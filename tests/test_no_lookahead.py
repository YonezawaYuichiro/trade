from decimal import Decimal

import numpy as np
import pandas as pd
import pytest

from cleanroom.features import past_return, trailing_zscore
from cleanroom.lookahead import (
    LookaheadError,
    assert_no_lookahead,
    start_shift_violations,
    truncation_violations,
)
from cleanroom.returns import close_to_close_returns
from conftest import make_sessions

WARMUP = 30


def future_return(s: pd.Series) -> pd.Series:
    return s.shift(-1) / s - 1


def full_period_standardize(s: pd.Series) -> pd.Series:
    return (s - s.mean()) / s.std()


def centered_mean(s: pd.Series) -> pd.Series:
    return s.rolling(5, center=True).mean()


def start_dependent(s: pd.Series) -> pd.Series:
    return s - s.expanding().mean()


@pytest.mark.parametrize("bad", [future_return, full_period_standardize, centered_mean])
def test_lookahead_features_fail(bad, closes):
    with pytest.raises(LookaheadError):
        assert_no_lookahead(bad, closes, warmup=WARMUP)


@pytest.mark.parametrize("good", [past_return(1), past_return(5), trailing_zscore(20)])
def test_past_only_features_pass(good, closes):
    assert_no_lookahead(good, closes, warmup=WARMUP)


def test_start_dependent_feature_fails(closes):
    # 末尾の切り詰めでは捕まらず、開始点のずらしでだけ捕まる特徴量
    assert truncation_violations(start_dependent, closes, cuts=[100, 200]) == []
    with pytest.raises(LookaheadError):
        assert_no_lookahead(start_dependent, closes, warmup=WARMUP)


def test_truncation_catches_future_return(closes):
    assert truncation_violations(future_return, closes, cuts=[100]) == [100]


def test_truncation_catches_centered_window(closes):
    assert truncation_violations(centered_mean, closes, cuts=[100]) == [100]


def test_start_shift_catches_full_period_standardize(closes):
    assert start_shift_violations(full_period_standardize, closes, shifts=[10], warmup=WARMUP) == [10]


def test_past_return_values(closes):
    expected = closes.iloc[10] / closes.iloc[5] - 1
    assert past_return(5)(closes).iloc[10] == pytest.approx(expected)
    assert np.isnan(past_return(5)(closes).iloc[4])


def test_feature_without_values_cannot_be_checked(closes):
    with pytest.raises(ValueError):
        assert_no_lookahead(lambda s: s * np.nan, closes, warmup=WARMUP)


def _bars(raw, factors=None, adj=None, codes=None):
    n = len(raw)

    def dec(values):
        return [None if v is None else Decimal(v) for v in values]

    return pd.DataFrame(
        {
            "code": codes or ["1301"] * n,
            "ts": make_sessions(n),
            "close": dec(raw),
            "adj_close": dec(adj or raw),
            "adj_factor": dec(factors or ["1"] * n),
        }
    )


def _r(bars: pd.DataFrame) -> pd.Series:
    return close_to_close_returns(bars, make_sessions(len(bars)))


def test_return_across_split_is_missing():
    # 5日目が 1:2 の分割の権利落ち日。公式の仕様どおり AdjFactor に 0.5 が入る
    raw = ["1000", "1010", "1020", "1030", "1040", "525", "530"]
    factors = ["1", "1", "1", "1", "1", "0.5", "1"]
    r = _r(_bars(raw, factors))
    assert r.iloc[5] is None
    assert r.iloc[6] == Decimal("530") / Decimal("525") - 1
    assert r.iloc[1] == Decimal("1010") / Decimal("1000") - 1
    assert all(isinstance(v, Decimal) for v in r.iloc[[1, 2, 3, 4, 6]])


def test_return_across_reverse_split_is_missing():
    raw = ["100", "101", "1010", "1020"]
    r = _r(_bars(raw, ["1", "1", "10", "1"]))
    assert r.iloc[2] is None
    assert r.iloc[3] == Decimal("1020") / Decimal("1010") - 1


def test_rounded_adjusted_prices_do_not_drop_returns():
    # 後の分割で、過去の調整済み値が小数第1位に丸められている。AdjFactor が1の日のリターンは残す
    raw = ["1001", "1003", "1007"]
    adj = ["333.7", "334.3", "335.7"]
    r = _r(_bars(raw, adj=adj))
    assert r.iloc[1] == Decimal("1003") / Decimal("1001") - 1
    assert r.iloc[2] == Decimal("1007") / Decimal("1003") - 1


def test_missing_adj_factor_gives_no_return():
    r = _r(_bars(["1000", "1010", "1020"], ["1", None, "1"]))
    assert r.iloc[1] is None
    assert r.iloc[2] == Decimal("1020") / Decimal("1010") - 1


def test_null_day_has_no_return_and_is_not_carried():
    raw = ["1000", "1010", None, "1030", "1040"]
    r = _r(_bars(raw))
    assert r.iloc[2] is None
    assert r.iloc[3] is None  # 前日が Null。2日前の終値を繰り越さない
    assert r.iloc[4] == Decimal("1040") / Decimal("1030") - 1


def test_first_row_of_each_code_has_no_return():
    raw = ["1000", "1010", "2000", "2020"]
    r = _r(_bars(raw, codes=["1301", "1301", "7203", "7203"]))
    assert r.iloc[0] is None
    assert r.iloc[2] is None
    assert r.iloc[3] == Decimal("2020") / Decimal("2000") - 1


def test_missing_ex_date_row_does_not_bridge_the_split():
    # 権利落ち日の行そのものが無い。前日から翌日へリターンをつながない
    bars = _bars(["1000", "1010", "505", "510"], ["1", "1", "0.5", "1"]).drop(index=2)
    r = close_to_close_returns(bars, make_sessions(4))
    assert r.loc[3] is None
    assert r.loc[1] == Decimal("1010") / Decimal("1000") - 1


def test_one_missing_row_breaks_only_that_code():
    raw = ["1000", "1010", "1020", "2000", "2010", "2020"]
    codes = ["1301"] * 3 + ["7203"] * 3
    bars = _bars(raw, codes=codes)
    bars["ts"] = list(make_sessions(3)) * 2
    r = close_to_close_returns(bars.drop(index=1), make_sessions(3))
    assert r.loc[2] is None
    assert r.loc[5] == Decimal("2020") / Decimal("2010") - 1


def test_date_outside_calendar_is_an_error():
    with pytest.raises(ValueError):
        close_to_close_returns(_bars(["1000", "1010", "1020"]), make_sessions(2))


def test_duplicate_row_for_same_code_and_day_is_an_error():
    bars = _bars(["1000", "1010", "1020"])
    with pytest.raises(ValueError):
        close_to_close_returns(pd.concat([bars, bars.iloc[[1]]], ignore_index=True), make_sessions(3))


@pytest.mark.parametrize("order", ["unsorted", "duplicated"])
def test_bad_sessions_are_an_error(order):
    # 行は2日だけ。行の側の順番は正しいので、重複の検査ではなく sessions の検査で止まる
    s = list(make_sessions(3))
    sessions = [s[0], s[2], s[1]] if order == "unsorted" else [s[0], s[1], s[1], s[2]]
    with pytest.raises(ValueError):
        close_to_close_returns(_bars(["1000", "1010"]), sessions)
