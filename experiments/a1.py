"""実験A1: 時系列で分けて学習し、テストの正解率を測る。"""
import numpy as np
from sklearn.linear_model import LogisticRegression

from common import SEED, random_walk_returns

N_DAYS = 2000
TRAIN_FRACTION = 0.7

r = random_walk_returns(N_DAYS)

# 行 t: 特徴量 = 翌日の収益率、ラベル = 翌日に値上がりしたか
x = r[1:].reshape(-1, 1)
y = (r[1:] > 0).astype(int)

cut = int(len(y) * TRAIN_FRACTION)
x_train, y_train = x[:cut], y[:cut]
x_test, y_test = x[cut:], y[cut:]

model = LogisticRegression(random_state=SEED).fit(x_train, y_train)
accuracy = float(np.mean(model.predict(x_test) == y_test))

print(f"学習 {len(y_train)} 行（過去） / テスト {len(y_test)} 行（未来）")
print(f"テストの正解率: {accuracy:.4f}")
