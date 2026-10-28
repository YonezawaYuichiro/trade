"""実験B: 優位性のない戦略を50本作り、平均÷標準偏差×√252 の最大値を出す。"""
import numpy as np

from common import DAYS_PER_YEAR, SEED, random_walk_returns

N_DAYS = 504
N_STRATEGIES = 50

r = random_walk_returns(N_DAYS)
rng = np.random.default_rng(SEED + 1)

values = []
for _ in range(N_STRATEGIES):
    position = rng.integers(0, 2, size=N_DAYS)  # 各日、無作為に 0（持たない）か 1（持つ）
    strategy = position * r
    values.append(strategy.mean() / strategy.std(ddof=1) * np.sqrt(DAYS_PER_YEAR))

print(f"合成の収益率 {N_DAYS} 営業日、戦略 {N_STRATEGIES} 本")
print(f"50本の最大値: {max(values):.4f}")
