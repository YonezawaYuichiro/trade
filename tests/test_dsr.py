"""論文の数値例との照合。Bailey and López de Prado, "The Deflated Sharpe Ratio",
Journal of Portfolio Management 40(5), 2014。数値は SSRN 2460551（2014-07-31 版）の pp.9-10。"""
import math

import pytest

from cleanroom.dsr import deflated_sharpe, probabilistic_sharpe, rejection_threshold

# 本文の例: 5年の日次、年率の SR の分散 1/2、N = 100、T = 1250、歪度 −3、尖度 10。年250日で非年率にする
V = 1 / (2 * 250)
SR = 2.5 / math.sqrt(250)
T, SKEW, KURT = 1250, -3, 10


def test_paper_example_threshold_is_01132():
    assert round(rejection_threshold(100, V), 4) == 0.1132


def test_paper_example_dsr_is_09004():
    assert round(deflated_sharpe(SR, 100, V, T, SKEW, KURT), 4) == 0.9004


def test_paper_example_46_trials_pass_95_percent():
    # 本文: N = 46 なら DSR は 0.9505 で、95% を超える
    assert round(deflated_sharpe(SR, 46, V, T, SKEW, KURT), 4) == 0.9505
    assert deflated_sharpe(SR, 47, V, T, SKEW, KURT) < 0.95


def test_paper_example_normal_returns_allow_88_trials():
    # 本文: 正規分布（歪度0、尖度3）なら、N = 88 で DSR は 0.9505
    assert round(deflated_sharpe(SR, 88, V, T, 0, 3), 4) == 0.9505
    assert deflated_sharpe(SR, 89, V, T, 0, 3) < 0.95


def test_dsr_is_psr_at_the_threshold():
    # 式 (2): DSR = PSR(SR_0)
    sr0 = rejection_threshold(100, V)
    assert deflated_sharpe(SR, 100, V, T, SKEW, KURT) == probabilistic_sharpe(SR, sr0, T, SKEW, KURT)


def test_more_trials_lower_the_dsr():
    values = [deflated_sharpe(SR, n, V, T, SKEW, KURT) for n in (10, 100, 1000)]
    assert values == sorted(values, reverse=True)


@pytest.mark.parametrize("kwargs", [{"n_trials": 1}, {"var_sr": 0}, {"t": 1}])
def test_bad_inputs_are_rejected(kwargs):
    args = {"sr": SR, "n_trials": 100, "var_sr": V, "t": T, "skew": SKEW, "kurt": KURT} | kwargs
    with pytest.raises(ValueError):
        deflated_sharpe(**args)
