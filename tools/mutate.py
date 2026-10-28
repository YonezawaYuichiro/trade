"""変異の検査。大事な1行を1箇所ずつ壊し、テストが落ちるかを見る。

作業用の一時フォルダに cleanroom/、tests/、pyproject.toml を写して壊すので、元のファイルは変えない。
使い方: uv run python tools/mutate.py
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# (ID, 壊し方, ファイル, 元の文字列, 壊した文字列)
MUTATIONS = [
    ("M01", "先読みを混ぜる（過去リターンを1日先にずらす）", "cleanroom/features.py",
     "return s / s.shift(n) - 1", "return s.shift(-1) / s.shift(n - 1) - 1"),
    ("M02", "全期間で標準化する", "cleanroom/features.py",
     "return (s - rolling.mean()) / rolling.std()", "return (s - s.mean()) / s.std()"),
    ("M03", "中央寄せの窓にする", "cleanroom/features.py",
     "rolling = s.rolling(window)", "rolling = s.rolling(window, center=True)"),
    ("M04", "企業行為の日のリターンを埋める（AdjFactor を見ない）", "cleanroom/returns.py",
     "if factor == 1:", "if True:"),
    ("M05", "Null の日に前の終値を繰り越す", "cleanroom/returns.py",
     "prev_close[code], prev_pos[code] = close, here",
     "prev_close[code], prev_pos[code] = (close if close is not None else prev_close.get(code)), here"),
    ("M06", "ホールドアウトを通常の読み込みが返す", "cleanroom/split.py",
     "df = _read(main)\n", "df = pd.concat([_read(main), _read(_paths(store)[1])], ignore_index=True)\n"),
    ("M07", "通常の読み込みの、ホールドアウト混入の検査を消す", "cleanroom/split.py",
     'if (df["ts"] >= _holdout_start(store)).any():', "if False:"),
    ("M08", "ロック時にホールドアウトも通常のファイルへ書く", "cleanroom/split.py",
     "_write(bars[~is_hold], main, columns)", "_write(bars, main, columns)"),
    ("M09", "ホールドアウトを2回開ける", "cleanroom/split.py",
     'with marker.open("x", encoding="utf-8") as f:', 'with marker.open("w", encoding="utf-8") as f:'),
    ("M10", "確認の文字列なしで開ける", "cleanroom/split.py",
     "if confirm != OPEN_CONFIRM:", "if False:"),
    ("M11", "パージと余白を消す", "cleanroom/split.py",
     'seg[i <= vs - 2 * h - 1] = "train"', 'seg[i < vs] = "train"'),
    ("M12", "断言を消す: 先読み検査の違反を見逃す", "cleanroom/lookahead.py",
     "if trunc or shift:", "if False:"),
    ("M13", "先読み検査の許容差を大きくする", "cleanroom/lookahead.py",
     "_RTOL, _ATOL = 1e-9, 1e-12", "_RTOL, _ATOL = 1e-1, 1e-1"),
    ("M14", "断言を消す: タイムゾーンなしの時刻を通す", "cleanroom/schema.py",
     "if not isinstance(ts_dtype, pd.DatetimeTZDtype) or str(ts_dtype.tz) != str(TZ):", "if False:"),
    ("M15", "断言を消す: float の価格を通す", "cleanroom/schema.py",
     "if not isinstance(v, Decimal):", "if False:"),
    ("M16", "式 (4) の第2項を 1 − e/N と読み違える", "cleanroom/budget.py",
     "_Z_INV(1 - 1 / (n * math.e))", "_Z_INV(1 - math.e / n)"),
    ("M17", "コスト下限を呼値1つ分にする", "cleanroom/costs.py",
     "return 2 * tick / price", "return tick / price"),
    ("M18", "端株を許す", "cleanroom/costs.py",
     "return quantity // lot * lot", "return quantity"),
    # 検査係1回目の指摘と、検査係が入れた変異
    ("M19", "先読み検査から開始点のずらしを外す（指摘 a、P2）", "cleanroom/lookahead.py",
     "shift = start_shift_violations(feature, series, shifts, warmup)", "shift = []"),
    ("M20", "ホールドアウトのハッシュ照合を外す（指摘 b、P4）", "cleanroom/split.py",
     "if _sha256(hold) != expected:", "if False:"),
    ("M21", "混入検査の境界を > にする（指摘 c、P7）", "cleanroom/split.py",
     'if (df["ts"] >= _holdout_start(store)).any():', 'if (df["ts"] > _holdout_start(store)).any():'),
    ("M22", "Decimal の NaN と無限大を通す（指摘 d）", "cleanroom/schema.py",
     "if not v.is_finite():", "if False:"),
    ("M23", "正でない価格を通す（指摘 d）", "cleanroom/schema.py",
     "if col in POSITIVE_COLUMNS and v <= 0:", "if False:"),
    ("M24", "負の出来高を通す（指摘 d）", "cleanroom/schema.py",
     'if col == "volume" and v < 0:', "if False:"),
    ("M25", "ロックの境界を > にする（検査係の P3）", "cleanroom/split.py",
     'is_hold = bars["ts"] >= holdout_start', 'is_hold = bars["ts"] > holdout_start'),
    ("M26", "先読み検査から末尾の切り詰めを外す（検査係の P1）", "cleanroom/lookahead.py",
     "trunc = truncation_violations(feature, series, cuts)", "trunc = []"),
    # J-Quants の取得（DATA.md、公式の仕様）
    ("M27", "数値を float で読む", "cleanroom/jquants.py",
     "return json.loads(raw, parse_float=Decimal, parse_int=Decimal)", "return json.loads(raw)"),
    ("M28", "pagination_key を追わない", "cleanroom/jquants.py",
     "if not next_key:", "if True:"),
    ("M29", "呼び出しの間隔をあけない（5件/分を超える）", "cleanroom/jquants.py",
     "if wait > 0:", "if False:"),
    ("M30", "429・5xx で再試行しない", "cleanroom/jquants.py",
     "if status == 0 or status == 429 or status >= 500:", "if False:"),
    ("M31", "例外の文に APIキーを入れる", "cleanroom/jquants.py",
     'を返した: {text}")', 'を返した: {text} {self._key}")'),
    ("M32", "float の価格を受け付ける", "cleanroom/jquants.py",
     "if isinstance(value, str):", "if isinstance(value, (str, float)):"),
    ("M33", "ホールドアウトの日の記録を main に保存する", "cleanroom/fetch.py",
     'return "holdout" if day >= holdout_start else "main"', 'return "main"'),
    ("M34", "保存済みの日も取り直す", "cleanroom/fetch.py",
     "if path.exists():", "if False:"),
    ("M35", "ホールドアウトを5か月に縮める", "cleanroom/fetch.py",
     "cutoff = sessions[-1] - pd.DateOffset(months=months)", "cutoff = sessions[-1] - pd.DateOffset(months=months - 1)"),
    ("M36", "文字列の列の Null を 'nan' と書く", "cleanroom/split.py",
     "return v is None or v is pd.NA or (isinstance(v, float) and v != v)", "return v is None"),
    ("M37", "調整係数の正の値の検査を外す", "cleanroom/schema.py",
     'POSITIVE_COLUMNS = (*PRICE_COLUMNS, "adj_factor")', "POSITIVE_COLUMNS = PRICE_COLUMNS"),
    # 新しい回の1回目の指摘（REVIEW.md §7）
    ("M38", "行が欠けた日をまたいでリターンをつなぐ（指摘1）", "cleanroom/returns.py",
     "p = prev_close.get(code) if prev_pos.get(code) == here - 1 else None", "p = prev_close.get(code)"),
    ("M39", "空の応答の日を保存する（指摘1）", "cleanroom/fetch.py",
     'raise FetchError(f"{day} の応答が空だった。保存せずに止める")', "pass"),
    ("M40", "記録の無い営業日があってもロックする（指摘1）", "cleanroom/fetch.py",
     "if missing:", "if False:"),
    ("M41", "空の記録のファイルがあってもロックする（指摘1）", "cleanroom/fetch.py",
     'raise FetchError(f"{f} が空")', "pass"),
    ("M42", "固定した計画を無視して毎回計算し直す（指摘3、Q6）", "cleanroom/fetch.py",
     "if plan_path.exists():", "if False:"),
    ("M43", "保存済みファイルの側の照合を外す（指摘3）", "cleanroom/fetch.py",
     "    _check_saved_sides(raw_dir, holdout_start)\n", ""),
    ("M44", "manifest のハッシュを中身と無関係にする（指摘4、Q4）", "cleanroom/fetch.py",
     '"sha256": hashlib.sha256(data).hexdigest(),', '"sha256": hashlib.sha256(b"x").hexdigest(),'),
    ("M45", "ロックの外のホールドアウトの記録を消さない（指摘5）", "cleanroom/fetch.py",
     "        f.unlink()", "        pass"),
    ("M46", "ロック済みでも取得をやり直す（指摘5）", "cleanroom/fetch.py",
     'if (store / "plan.json").exists():', "if False:"),
    ("M47", "同じ pagination_key が返り続けても止めない（指摘2）", "cleanroom/jquants.py",
     "if next_key in seen:", "if False:"),
    # 新しい回の2回目の推奨（REVIEW.md §9）
    ("M48", "同じ銘柄・同じ日の重複の検査を外す（推奨 a）", "cleanroom/returns.py",
     "if code in prev_pos and here <= prev_pos[code]:", "if False:"),
    ("M49", "sessions の昇順の検査を外す（推奨 a）", "cleanroom/returns.py",
     "if len(pos) != len(sessions) or sessions != sorted(sessions):", "if len(pos) != len(sessions):"),
    ("M50", "sessions の重複の検査を外す（推奨 a）", "cleanroom/returns.py",
     "if len(pos) != len(sessions) or sessions != sorted(sessions):", "if sessions != sorted(sessions):"),
    ("M51", "ロック時の validate_bars を外す（推奨 b、Q7）", "cleanroom/split.py",
     "        validate_bars(bars)\n", ""),
    ("M52", "開くときの検証を外す（推奨 b）", "cleanroom/split.py",
     "hold_bars = validate_bars(_read(hold))", "hold_bars = _read(hold)"),
    ("M53", "ロック済みのとき、残ったホールドアウトの記録を消さない（推奨 c）", "cleanroom/fetch.py",
     "        _remove_raw_holdout(data_dir / \"raw\")\n        raise", "        raise"),
    ("M54", "Asia/Tokyo 以外のタイムゾーンを通す", "cleanroom/schema.py",
     "if not isinstance(ts_dtype, pd.DatetimeTZDtype) or str(ts_dtype.tz) != str(TZ):",
     "if not isinstance(ts_dtype, pd.DatetimeTZDtype):"),
]


def run(workdir: Path) -> tuple[int, list[str]]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rfE"],
        cwd=workdir, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    failed = re.findall(r"^(?:FAILED|ERROR) (\S+)", proc.stdout, flags=re.M)
    return proc.returncode, failed


def main() -> int:
    survived = 0
    print("| ID | 壊し方 | ファイル | 結果 | 落ちたテスト |")
    print("|---|---|---|---|---|")
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "base"
        for name in ("cleanroom", "tests"):
            shutil.copytree(ROOT / name, base / name, ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copy(ROOT / "pyproject.toml", base / "pyproject.toml")
        code, failed = run(base)
        if code != 0:
            print(f"壊す前のテストが通らない: {failed}")
            return 1
        for mid, desc, rel, old, new in MUTATIONS:
            work = Path(tmp) / mid
            shutil.copytree(base, work)
            src = (work / rel).read_text(encoding="utf-8")
            if src.count(old) != 1:
                print(f"| {mid} | {desc} | `{rel}` | 置き換え先が1箇所でない（{src.count(old)}） | |")
                survived += 1
                continue
            (work / rel).write_text(src.replace(old, new), encoding="utf-8")
            code, failed = run(work)
            if code == 0:
                survived += 1
                print(f"| {mid} | {desc} | `{rel}` | **落ちなかった** | |")
            else:
                names = "<br>".join(f"`{f}`" for f in failed) or f"終了コード {code}"
                print(f"| {mid} | {desc} | `{rel}` | 落ちた | {names} |")
    print(f"\n生き残った変異: {survived} / {len(MUTATIONS)}")
    return 1 if survived else 0


if __name__ == "__main__":
    sys.exit(main())
