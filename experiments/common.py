import numpy as np

SEED = 20261027
DAYS_PER_YEAR = 252


def random_walk_returns(n_days: int, seed: int = SEED, daily_sd: float = 0.01) -> np.ndarray:
    """平均0のランダムウォークの日次収益率（合成）。"""
    rng = np.random.default_rng(seed)
    return rng.normal(0.0, daily_sd, size=n_days)
