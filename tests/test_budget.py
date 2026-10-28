"""論文の数値例との照合。Bailey, Borwein, López de Prado, Zhu (2014), Notices of the AMS 61(5), pp.458-471。"""
import math

import pytest

from cleanroom.budget import expected_max_sharpe, max_trials, min_backtest_length


def test_paper_example_ten_trials_gives_sharpe_157():
    # 本文: N = 10 なら IS のシャープ 1.57 が見つかると期待される（Figure 1 の説明）
    assert round(expected_max_sharpe(10), 2) == 1.57


def test_paper_example_five_years_allows_45_trials():
    # 本文: 5年のデータなら、独立な設定は45個まで（E[max_N] = 1）
    assert max_trials(5.0, 1.0) == 45
    assert min_backtest_length(45, 1.0) <= 5.0 < min_backtest_length(46, 1.0)


def test_paper_example_seven_trials_for_two_years():
    # 本文: 7個の独立な設定で、2年のバックテストの IS 最大シャープの期待値が1
    assert max_trials(2.0, 1.0) == 7


@pytest.mark.parametrize("n", [10, 45, 100])
def test_paper_upper_bound(n):
    # 式 (6): MinBTL < 2 ln[N] / E[max_N]^2
    assert min_backtest_length(n, 1.0) < 2 * math.log(n) / 1.0**2


def test_years_rescale_by_inverse_square_root():
    # 式 (5): y^(-1/2) 倍
    assert expected_max_sharpe(10, years=4.0) == pytest.approx(expected_max_sharpe(10) / 2)


def test_formula_needs_more_than_one_trial():
    with pytest.raises(ValueError):
        expected_max_sharpe(1)


def test_one_trial_is_always_allowed():
    assert max_trials(0.1, 1.0) == 1
