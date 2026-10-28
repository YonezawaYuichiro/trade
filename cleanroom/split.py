"""学習・検証・ホールドアウトの時系列分割と、ホールドアウトのロック。

ホールドアウトは別のファイルに分けて書き、通常の読み込み（load_bars）は読まない。
開くのは open_holdout で1回だけ。
"""
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from cleanroom.schema import DECIMAL_COLUMNS, TZ, validate_bars

OPEN_CONFIRM = "ホールドアウトを1回だけ開く"


class HoldoutLockedError(PermissionError):
    pass


@dataclass(frozen=True)
class SplitPlan:
    valid_start: pd.Timestamp
    holdout_start: pd.Timestamp
    label_horizon: int


def assign_segments(sessions: pd.DatetimeIndex, plan: SplitPlan) -> pd.Series:
    """各営業日を train / valid / holdout / purge に分ける。

    ラベルが次の区間と重なる行を除き（パージ）、その後ろにラベルの期間と同じ長さの余白を置く。
    """
    h = plan.label_horizon
    if h < 1:
        raise ValueError("label_horizon は 1 以上")
    if not (sessions.is_monotonic_increasing and sessions.is_unique):
        raise ValueError("sessions は重複のない昇順")
    if not plan.valid_start < plan.holdout_start:
        raise ValueError("valid_start は holdout_start より前")
    vs = sessions.searchsorted(plan.valid_start)
    hs = sessions.searchsorted(plan.holdout_start)
    i = np.arange(len(sessions))
    seg = np.full(len(sessions), "purge", dtype=object)
    seg[i <= vs - 2 * h - 1] = "train"
    seg[(i >= vs) & (i <= hs - 2 * h - 1)] = "valid"
    seg[i >= hs] = "holdout"
    return pd.Series(seg, index=sessions)


def _paths(store: Path) -> tuple[Path, Path, Path]:
    store = Path(store)
    return store / "main" / "bars.csv", store / "holdout" / "bars.csv", store / "plan.json"


def _is_missing(v) -> bool:
    """None と、文字列の列で pandas が None を置き換えた NaN・NA。Decimal の列は validate_bars が NaN を拒否済み。"""
    return v is None or v is pd.NA or (isinstance(v, float) and v != v)


def _write(df: pd.DataFrame, path: Path, columns: list[str]) -> None:
    """Decimal は文字列、None は空欄で書く。ファイルが既にあれば追記する。"""
    out = df[columns].copy()
    out["ts"] = [ts.isoformat() for ts in out["ts"]]
    for col in columns:
        if col != "ts":
            out[col] = ["" if _is_missing(v) else str(v) for v in out[col]]
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        out.to_csv(path, index=False, header=False, mode="a")
    else:
        out.to_csv(path, index=False)


def _read(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    df["ts"] = pd.to_datetime(df["ts"], format="ISO8601").dt.tz_convert(TZ)
    for col in df.columns:
        if col in DECIMAL_COLUMNS:
            df[col] = pd.Series([None if v == "" else Decimal(v) for v in df[col]], index=df.index, dtype=object)
        elif col not in ("code", "ts"):
            df[col] = pd.Series([None if v == "" else v for v in df[col]], index=df.index, dtype=object)
    return df


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lock_holdout(bars: pd.DataFrame, holdout_start: pd.Timestamp, store: Path) -> None:
    """holdout_start 以降の行を別ファイルに分けてロックする。既にあれば上書きしない。"""
    lock_holdout_frames([bars], holdout_start, store)


def lock_holdout_frames(frames: Iterable[pd.DataFrame], holdout_start: pd.Timestamp, store: Path) -> None:
    """日ごとなどに分かれた表を順に書き、holdout_start 以降の行を別ファイルに分けてロックする。"""
    main, hold, plan_path = _paths(store)
    if main.exists() or hold.exists() or plan_path.exists():
        raise FileExistsError(f"{store} には既にデータがある。ロックは作り直さない")
    columns: list[str] | None = None
    for bars in frames:
        validate_bars(bars)
        if columns is None:
            columns = list(bars.columns)
        elif list(bars.columns) != columns:
            raise ValueError("表ごとに列が揃っていない")
        is_hold = bars["ts"] >= holdout_start
        _write(bars[~is_hold], main, columns)
        _write(bars[is_hold], hold, columns)
    if columns is None:
        raise ValueError("書く表が1つもない")
    plan_path.write_text(
        json.dumps(
            {"holdout_start": holdout_start.isoformat(), "holdout_sha256": _sha256(hold)},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _holdout_start(store: Path) -> pd.Timestamp:
    _, _, plan_path = _paths(store)
    return pd.Timestamp(json.loads(plan_path.read_text(encoding="utf-8"))["holdout_start"])


def load_bars(store: Path) -> pd.DataFrame:
    """通常の読み込み。ホールドアウトは返さない。混ざっていたら止める。"""
    main, _, _ = _paths(store)
    df = _read(main)
    if (df["ts"] >= _holdout_start(store)).any():
        raise HoldoutLockedError("通常の読み込みにホールドアウトの行が混ざっている")
    return validate_bars(df)


def open_holdout(store: Path, confirm: str) -> pd.DataFrame:
    """ホールドアウトを1回だけ開く。開いた時刻を残し、2回目は拒否する。"""
    if confirm != OPEN_CONFIRM:
        raise HoldoutLockedError(f"確認の文字列が違う。開くなら confirm={OPEN_CONFIRM!r}")
    _, hold, plan_path = _paths(store)
    expected = json.loads(plan_path.read_text(encoding="utf-8"))["holdout_sha256"]
    if _sha256(hold) != expected:
        raise HoldoutLockedError("ホールドアウトのファイルがロック時から変わっている")
    hold_bars = validate_bars(_read(hold))  # 不正な行があれば、開封を消費する前に止める
    marker = hold.parent / "OPENED"
    try:
        with marker.open("x", encoding="utf-8") as f:
            f.write(datetime.now(TZ).isoformat())
    except FileExistsError:
        raise HoldoutLockedError(f"ホールドアウトは既に開かれた: {marker.read_text(encoding='utf-8')}") from None
    return hold_bars
