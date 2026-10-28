"""過去だけを使う特徴量。入力は1銘柄の時系列（時刻順）。標準化は後ろ向きの窓の中だけで行う。"""
import pandas as pd


def past_return(n: int):
    """n 行前から今の足までのリターン。"""

    def feature(s: pd.Series) -> pd.Series:
        return s / s.shift(n) - 1

    feature.__name__ = f"past_return_{n}"
    return feature


def trailing_zscore(window: int):
    """直近 window 行（今の足を含む）の平均と標準偏差で標準化した値。"""

    def feature(s: pd.Series) -> pd.Series:
        rolling = s.rolling(window)
        return (s - rolling.mean()) / rolling.std()

    feature.__name__ = f"trailing_zscore_{window}"
    return feature
