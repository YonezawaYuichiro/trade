"""日足の取得の手順。営業日の一覧 → ホールドアウト開始日の固定 → 日ごとの取得 → ロック。

収益率は計算しない。日ごとの記録（数値を文字列にした JSON）を保存し、途中で止まっても続きから取る。
ロックした後は、ロックの外にホールドアウトの記録を残さない（ハッシュは manifest.csv に残す）。
"""
import hashlib
import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pandas as pd

from cleanroom.jquants import to_bars
from cleanroom.schema import TZ
from cleanroom.split import lock_holdout_frames

DAILY = "/equities/bars/daily"


class FetchError(RuntimeError):
    pass


def session_dates(client, code: str) -> list[pd.Timestamp]:
    """1銘柄を code だけで取り（範囲はプランに合わせて自動）、返った日付だけを使う。価格は捨てる。"""
    records = client.get(DAILY, {"code": code})
    return sorted({pd.Timestamp(r["Date"]).tz_localize(TZ) for r in records})


def holdout_start_for(sessions: list[pd.Timestamp], months: int = 6) -> pd.Timestamp:
    """最後の営業日から months か月前より後の、最初の営業日。"""
    cutoff = sessions[-1] - pd.DateOffset(months=months)
    return next(s for s in sessions if s > cutoff)


def load_or_fix_plan(client, plan_path: Path, calendar_code: str, months: int) -> tuple[list[pd.Timestamp], pd.Timestamp]:
    """営業日の一覧とホールドアウト開始日を、最初の1回だけ決めてファイルに固定する。2回目からはファイルを使う。"""
    plan_path = Path(plan_path)
    if plan_path.exists():
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        return [pd.Timestamp(s) for s in plan["sessions"]], pd.Timestamp(plan["holdout_start"])
    sessions = session_dates(client, calendar_code)
    holdout_start = holdout_start_for(sessions, months=months)
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        json.dumps(
            {
                "fixed_at": datetime.now(TZ).isoformat(),
                "calendar_code": calendar_code,
                "holdout_months": months,
                "holdout_start": holdout_start.isoformat(),
                "sessions": [s.isoformat() for s in sessions],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return sessions, holdout_start


def _json_default(value):
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f"保存できない型: {type(value).__name__}")


def _side(day: pd.Timestamp, holdout_start: pd.Timestamp) -> str:
    return "holdout" if day >= holdout_start else "main"


def _check_saved_sides(raw_dir: Path, holdout_start: pd.Timestamp) -> None:
    for side in ("main", "holdout"):
        for f in (raw_dir / side).glob("*.json"):
            if _side(pd.Timestamp(f.stem).tz_localize(TZ), holdout_start) != side:
                raise FetchError(f"{f} はホールドアウト開始日 {holdout_start.date()} と食い違う側に保存されている")


def fetch_days(client, sessions, holdout_start: pd.Timestamp, raw_dir: Path, progress=None) -> None:
    """営業日ごとに全銘柄を取り、raw_dir/main か raw_dir/holdout に保存する。保存済みの日は取らない。

    応答が空の営業日は保存せずに止める（次の実行で取り直す）。
    """
    raw_dir = Path(raw_dir)
    _check_saved_sides(raw_dir, holdout_start)
    for s in sessions:
        day = s.date().isoformat()
        path = raw_dir / _side(s, holdout_start) / f"{day}.json"
        if path.exists():
            continue
        records = client.get(DAILY, {"date": day})
        if not records:
            raise FetchError(f"{day} の応答が空だった。保存せずに止める")
        path.parent.mkdir(parents=True, exist_ok=True)
        part = path.with_suffix(".part")
        part.write_text(json.dumps(records, default=_json_default, ensure_ascii=False), encoding="utf-8")
        part.replace(path)
        if progress:
            progress(day, len(records))


def build_store(raw_dir: Path, holdout_start: pd.Timestamp, store: Path, sessions) -> dict:
    """保存した記録を読み、ホールドアウトを分けてロックする。各ファイルのハッシュを manifest.csv に残す。

    営業日の一覧のどの日にも、空でない記録のファイルが1つあることを先に確かめる。
    """
    raw_dir, store = Path(raw_dir), Path(store)
    expected = {s.date().isoformat(): raw_dir / _side(s, holdout_start) / f"{s.date().isoformat()}.json" for s in sessions}
    missing = [day for day, f in expected.items() if not f.exists()]
    if missing:
        raise FetchError(f"記録の無い営業日がある: {missing[:5]} ほか {len(missing)} 日")
    files = [expected[day] for day in sorted(expected)]
    manifest = []

    def frames():
        for f in files:
            data = f.read_bytes()
            records = json.loads(data)
            if not records:
                raise FetchError(f"{f} が空")
            manifest.append(
                {
                    "file": f.relative_to(raw_dir).as_posix(),
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "rows": len(records),
                }
            )
            yield to_bars(records)

    lock_holdout_frames(frames(), holdout_start, store)
    pd.DataFrame(manifest).to_csv(store / "manifest.csv", index=False)
    return {
        "first": min(expected),
        "last": max(expected),
        "n_sessions": len(expected),
        "holdout_start": holdout_start.date().isoformat(),
        "rows_main": sum(m["rows"] for m in manifest if m["file"].startswith("main/")),
        "rows_holdout": sum(m["rows"] for m in manifest if m["file"].startswith("holdout/")),
    }


def _remove_raw_holdout(raw_dir: Path) -> None:
    for f in (raw_dir / "holdout").glob("*.json"):
        f.unlink()


def run_fetch(client, data_dir: Path, calendar_code: str, months: int, progress=None) -> dict:
    """取得の全手順。ロック済みなら何も取らずに止める。ロックした後、ロックの外のホールドアウトの記録は消す。

    ロックの後、消す前に止まった場合も、次の実行で消してから止める。
    """
    data_dir = Path(data_dir)
    store = data_dir / "store"
    if (store / "plan.json").exists():
        _remove_raw_holdout(data_dir / "raw")
        raise FileExistsError(f"{store} は既にロックされている。取り直さない")
    sessions, holdout_start = load_or_fix_plan(client, data_dir / "fetch_plan.json", calendar_code, months)
    fetch_days(client, sessions, holdout_start, data_dir / "raw", progress=progress)
    summary = build_store(data_dir / "raw", holdout_start, store, sessions)
    _remove_raw_holdout(data_dir / "raw")
    summary["fetched_at"] = datetime.now(TZ).isoformat()
    (store / "fetch_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary
