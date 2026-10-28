"""合成データだけを作る。実データは読まない。"""
from decimal import Decimal

import numpy as np
import pandas as pd
import pytest

from cleanroom.schema import TZ

SEED = 20261027


def make_sessions(n: int, start: str = "2024-01-04") -> pd.DatetimeIndex:
    return pd.date_range(start, periods=n, freq="B", tz=TZ)


def make_bars(n: int, code: str = "1301", seed: int = SEED, start: str = "2024-01-04") -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    closes = 1000 * np.exp(np.cumsum(rng.normal(0, 0.01, size=n)))
    prices = [Decimal(f"{c:.1f}") for c in closes]
    return pd.DataFrame(
        {
            "code": code,
            "ts": make_sessions(n, start),
            "open": prices,
            "high": prices,
            "low": prices,
            "close": prices,
            "adj_close": prices,
            "adj_factor": [Decimal(1)] * n,
            "volume": [Decimal(1000)] * n,
        }
    )


@pytest.fixture
def closes() -> pd.Series:
    """特徴量の検査用。合成の終値（float、株価ではない）。"""
    rng = np.random.default_rng(SEED)
    values = 1000 * np.exp(np.cumsum(rng.normal(0, 0.01, size=300)))
    return pd.Series(values, index=make_sessions(300))
