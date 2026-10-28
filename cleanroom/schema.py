"""日足の形式。価格は Decimal、時刻は Asia/Tokyo。

ts は「その営業日の 0:00 JST」で、日付を表すだけ。終値が確定した時刻でも、データが使えるようになった時刻でもない
（公式は利用可能になった日時を提供していない。DATA.md）。約定や特徴量の時点は、ts の時刻ではなく営業日の順で決める。
"""
from decimal import Decimal
from zoneinfo import ZoneInfo

import pandas as pd

TZ = ZoneInfo("Asia/Tokyo")
PRICE_COLUMNS = ("open", "high", "low", "close", "adj_close")
POSITIVE_COLUMNS = (*PRICE_COLUMNS, "adj_factor")
DECIMAL_COLUMNS = (*POSITIVE_COLUMNS, "volume")
REQUIRED_COLUMNS = ("code", "ts", *DECIMAL_COLUMNS)


class SchemaError(ValueError):
    pass


def validate_bars(df: pd.DataFrame) -> pd.DataFrame:
    """形式が正しければ df をそのまま返す。

    Null の日は None だけ。float、Decimal の NaN と無限大は通さない。価格と調整係数は正、出来高は0以上。
    """
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise SchemaError(f"列がない: {missing}")
    ts_dtype = df["ts"].dtype
    if not isinstance(ts_dtype, pd.DatetimeTZDtype) or str(ts_dtype.tz) != str(TZ):
        raise SchemaError(f"ts のタイムゾーンが {TZ} でない: {ts_dtype}")
    for col in DECIMAL_COLUMNS:
        for v in df[col]:
            if v is None:
                continue
            if not isinstance(v, Decimal):
                raise SchemaError(f"{col} に Decimal でない値がある: {v!r}")
            if not v.is_finite():
                raise SchemaError(f"{col} に NaN か無限大がある: {v!r}")
            if col in POSITIVE_COLUMNS and v <= 0:
                raise SchemaError(f"{col} に正でない値がある: {v!r}")
            if col == "volume" and v < 0:
                raise SchemaError(f"volume に負の値がある: {v!r}")
    if df.duplicated(["code", "ts"]).any():
        raise SchemaError("同じ銘柄・同じ時刻の行が重複している")
    return df
