from decimal import Decimal

import pandas as pd
import pytest

from cleanroom.schema import SchemaError, validate_bars
from conftest import make_bars


def test_valid_bars_pass():
    bars = make_bars(5)
    assert validate_bars(bars) is bars


def test_null_price_is_allowed():
    bars = make_bars(5)
    bars.loc[2, ["open", "high", "low", "close", "adj_close", "volume"]] = None
    assert validate_bars(bars) is bars


def test_float_price_is_rejected():
    bars = make_bars(5)
    bars["close"] = bars["close"].astype(float)
    with pytest.raises(SchemaError):
        validate_bars(bars)


def test_single_float_price_is_rejected():
    bars = make_bars(5)
    bars["open"] = bars["open"].astype(object)
    bars.at[3, "open"] = 1000.0
    with pytest.raises(SchemaError):
        validate_bars(bars)


@pytest.mark.parametrize("value", ["NaN", "sNaN", "Infinity", "-Infinity", "0", "-5"])
def test_non_finite_or_non_positive_price_is_rejected(value):
    bars = make_bars(5)
    bars.at[2, "close"] = Decimal(value)
    with pytest.raises(SchemaError):
        validate_bars(bars)


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-1"])
def test_non_finite_or_negative_volume_is_rejected(value):
    bars = make_bars(5)
    bars.at[2, "volume"] = Decimal(value)
    with pytest.raises(SchemaError):
        validate_bars(bars)


def test_naive_timestamp_is_rejected():
    bars = make_bars(5)
    bars["ts"] = bars["ts"].dt.tz_localize(None)
    with pytest.raises(SchemaError):
        validate_bars(bars)


@pytest.mark.parametrize("tz", ["UTC", "America/New_York"])
def test_timezone_other_than_tokyo_is_rejected(tz):
    bars = make_bars(5)
    bars["ts"] = bars["ts"].dt.tz_convert(tz)
    with pytest.raises(SchemaError):
        validate_bars(bars)


def test_missing_column_is_rejected():
    with pytest.raises(SchemaError):
        validate_bars(make_bars(5).drop(columns=["adj_close"]))


def test_duplicate_code_and_time_is_rejected():
    bars = make_bars(5)
    with pytest.raises(SchemaError):
        validate_bars(pd.concat([bars, bars.iloc[[0]]], ignore_index=True))


def test_decimal_volume_is_allowed():
    bars = make_bars(5)
    assert isinstance(bars.at[0, "volume"], Decimal)
    assert validate_bars(bars) is bars


@pytest.mark.parametrize("value", ["0", "-0.5", "NaN"])
def test_bad_adj_factor_is_rejected(value):
    bars = make_bars(5)
    bars.at[2, "adj_factor"] = Decimal(value)
    with pytest.raises(SchemaError):
        validate_bars(bars)


def test_adj_factor_is_required():
    with pytest.raises(SchemaError):
        validate_bars(make_bars(5).drop(columns=["adj_factor"]))
