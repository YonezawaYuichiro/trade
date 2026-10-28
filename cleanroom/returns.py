"""終値から終値への価格リターン（調整前の終値）。企業行為をまたぐ日と四本値が Null の日は欠損にする。

企業行為の判定は J-Quants の AdjFactor（権利落ち日に1以外が入る）で行う。調整済みの値は小数第1位に
丸められているので、調整済みと調整前のリターンの比較では判定しない（DATA.md）。

営業日の一覧（sessions）を受け取り、前の行が直前の営業日でなければ欠損にする。行が丸ごと欠けた日
（例えば権利落ち日の行が無い）を、またいでリターンをつながないため。
配当は調整に入っていないので、これは配当込みのリターンではない。
"""
from decimal import Decimal

import pandas as pd


def close_to_close_returns(df: pd.DataFrame, sessions) -> pd.Series:
    """AdjFactor が1でない日、AdjFactor が無い日、前の行が直前の営業日でない日は None。

    前日が Null なら、それより前の終値を繰り越さず None。各銘柄の最初の行も None。
    sessions にない日付の行があれば ValueError。
    """
    sessions = list(sessions)
    pos = {ts: i for i, ts in enumerate(sessions)}
    if len(pos) != len(sessions) or sessions != sorted(sessions):
        raise ValueError("sessions は重複のない昇順")
    out = pd.Series([None] * len(df), index=df.index, dtype=object)
    prev_close: dict[str, Decimal | None] = {}
    prev_pos: dict[str, int] = {}
    for i in df.sort_values(["code", "ts"], kind="stable").index:
        code, ts = df.at[i, "code"], df.at[i, "ts"]
        if ts not in pos:
            raise ValueError(f"営業日の一覧にない日付: {code} {ts}")
        here = pos[ts]
        if code in prev_pos and here <= prev_pos[code]:
            raise ValueError(f"{code} の時刻が重複している: {ts}")
        close, factor = df.at[i, "close"], df.at[i, "adj_factor"]
        p = prev_close.get(code) if prev_pos.get(code) == here - 1 else None
        if p is not None and close is not None and factor is not None:
            if factor == 1:
                out[i] = close / p - 1
        prev_close[code], prev_pos[code] = close, here
    return out
