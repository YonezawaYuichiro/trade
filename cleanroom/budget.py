"""Minimum Backtest Length。

Bailey, Borwein, López de Prado, Zhu, "Pseudo-Mathematics and Financial Charlatanism",
Notices of the AMS 61(5), 2014, pp.458-471. https://doi.org/10.1090/noti1105
式 (4)〜(6)。数値例との照合は tests/test_budget.py。
"""
import math
from statistics import NormalDist

EULER_GAMMA = 0.5772156649015329
_Z_INV = NormalDist().inv_cdf


def expected_max_sharpe(n_trials: int, years: float = 1.0) -> float:
    """N 本の独立な、真のシャープが0の戦略から選んだ最良の、年率シャープの期待値（式 (4)、(5)）。"""
    if n_trials < 2:
        raise ValueError("式 (4) は N ≫ 1 の近似。N は 2 以上で使う")
    if years <= 0:
        raise ValueError("years は正")
    n = n_trials
    e_max = (1 - EULER_GAMMA) * _Z_INV(1 - 1 / n) + EULER_GAMMA * _Z_INV(1 - 1 / (n * math.e))
    return e_max / math.sqrt(years)


def min_backtest_length(n_trials: int, target_sharpe: float) -> float:
    """最良の IS シャープの期待値が target_sharpe になるのに要る年数（式 (6)）。"""
    if target_sharpe <= 0:
        raise ValueError("target_sharpe は正")
    return (expected_max_sharpe(n_trials) / target_sharpe) ** 2


def max_trials(years: float, target_sharpe: float) -> int:
    """MinBTL が years 以下に収まる、独立な試行回数の最大値。1本なら選択がないので常に1以上。"""
    n = 1
    while min_backtest_length(n + 1, target_sharpe) <= years:
        n += 1
    return n
