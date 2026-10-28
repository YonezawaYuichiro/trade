"""先読みの検査。末尾を切っても過去が変わらないこと、開始点をずらしても一定期間後に一致すること。

考え方の参照: https://www.freqtrade.io/en/stable/lookahead-analysis/
"""
from typing import Callable, Iterable

import numpy as np
import pandas as pd

Feature = Callable[[pd.Series], pd.Series]

# 移動窓の計算は開始点で最後の桁がずれることがあるので、その分だけ許す
_RTOL, _ATOL = 1e-9, 1e-12


class LookaheadError(AssertionError):
    pass


def _same(a: pd.Series, b: pd.Series) -> bool:
    if not a.index.equals(b.index):
        return False
    return bool(np.allclose(a.to_numpy(float), b.to_numpy(float), rtol=_RTOL, atol=_ATOL, equal_nan=True))


def truncation_violations(feature: Feature, series: pd.Series, cuts: Iterable[int]) -> list[int]:
    """末尾を cut 行目で切って再計算したとき、過去の値が変わった cut の一覧。"""
    full = feature(series)
    return [cut for cut in cuts if not _same(feature(series.iloc[:cut]), full.iloc[:cut])]


def start_shift_violations(feature: Feature, series: pd.Series, shifts: Iterable[int], warmup: int) -> list[int]:
    """開始を shift 行ずらして再計算したとき、warmup 行より後で値が一致しなかった shift の一覧。"""
    full = feature(series)
    bad = []
    for shift in shifts:
        part = feature(series.iloc[shift:])
        if not _same(part.iloc[warmup:], full.iloc[shift + warmup :]):
            bad.append(shift)
    return bad


def assert_no_lookahead(feature: Feature, series: pd.Series, warmup: int) -> None:
    """どちらかの検査に1つでも違反があれば LookaheadError。値が出ない特徴量は検査できないので ValueError。"""
    n = len(series)
    if n <= 3 * warmup:
        raise ValueError("系列が短すぎて検査できない")
    full = feature(series)
    if full.iloc[warmup:].isna().all():
        raise ValueError("warmup の後に値が1つもないので検査できない")
    cuts = sorted({warmup + 1, n // 4, n // 2, 3 * n // 4, n - 1})
    shifts = sorted({1, 7, n // 4})
    trunc = truncation_violations(feature, series, cuts)
    shift = start_shift_violations(feature, series, shifts, warmup)
    if trunc or shift:
        raise LookaheadError(f"先読みの疑い: 末尾の切り詰め {trunc}、開始点のずらし {shift}")
