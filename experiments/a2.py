"""実験A2: テストのラベル期間が、学習のラベル期間と重なる割合を数える。"""
import numpy as np
from sklearn.model_selection import train_test_split

from common import SEED

N_DAYS = 2000
HORIZON = 5
TEST_FRACTION = 0.3

# 行 t のラベル = 翌日から HORIZON 営業日の収益率の和、つまり日 t+1 .. t+HORIZON を見る
n_rows = N_DAYS - HORIZON
rows = np.arange(n_rows)


def overlap_fraction(train_rows: np.ndarray, test_rows: np.ndarray) -> float:
    """ラベル期間が学習のどれか1行と1日でも重なるテスト行の割合。"""
    is_train = np.zeros(n_rows, dtype=bool)
    is_train[train_rows] = True
    overlapped = 0
    for t in test_rows:
        lo, hi = max(0, t - HORIZON + 1), min(n_rows, t + HORIZON)
        if is_train[lo:hi].any():
            overlapped += 1
    return overlapped / len(test_rows)


train_shuffled, test_shuffled = train_test_split(
    rows, test_size=TEST_FRACTION, shuffle=True, random_state=SEED
)

cut = int(n_rows * (1 - TEST_FRACTION))
train_time = rows[: cut - HORIZON]
test_time = rows[cut + HORIZON :]

print(f"シャッフルで分けた場合: 学習 {len(train_shuffled)} 行 / テスト {len(test_shuffled)} 行")
print(f"  重なる割合: {overlap_fraction(train_shuffled, test_shuffled):.4f}")
print(f"時間で分け、境界の {HORIZON} 営業日を両方から除いた場合: 学習 {len(train_time)} 行 / テスト {len(test_time)} 行")
print(f"  重なる割合: {overlap_fraction(train_time, test_time):.4f}")
