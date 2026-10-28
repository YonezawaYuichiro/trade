# BUDGET — 試行回数の上限

**結論: 上限は未確定。探索しない。** 理由は下の「未確定の理由」。

## 道具

Minimum Backtest Length（`cleanroom/budget.py`）。

出典: Bailey, Borwein, López de Prado, and Zhu, "Pseudo-Mathematics and Financial Charlatanism: The Effects of Backtest Overfitting on Out-of-Sample Performance," Notices of the AMS 61(5), 2014, pp.458-471. https://doi.org/10.1090/noti1105

式は本文の (4)、(5)、(6) を、2026-10-27 に ams.org の PDF から読んで写した。

- (4) E[max_N] ≈ (1−γ) Z⁻¹[1 − 1/N] + γ Z⁻¹[1 − 1/(N e)]、γ ≈ 0.5772156649（オイラー・マスケローニ定数）
- (5) y 年なら、上の値に y^(−1/2) を掛ける
- (6) MinBTL ≈ (E[max_N] の式 / 目標の E[max_N])² < 2 ln[N] / E[max_N]²

## 論文の数値例との照合（`uv run pytest tests/test_budget.py`）

| 論文の記述 | 実装の値 | テスト |
|---|---|---|
| N = 10 なら IS のシャープ 1.57 が見つかると期待される | 1.5746 | `test_paper_example_ten_trials_gives_sharpe_157` |
| 5年のデータなら、独立な設定は45個まで（E[max_N] = 1） | MinBTL(45) = 4.998 年、MinBTL(46) = 5.036 年 → 上限45 | `test_paper_example_five_years_allows_45_trials` |
| 7個の独立な設定で、2年のバックテストの E[max_N] が1 | MinBTL(7) = 1.923 年、MinBTL(8) = 2.129 年 → 上限7 | `test_paper_example_seven_trials_for_two_years` |
| MinBTL < 2 ln[N] / E[max_N]² | N = 10, 45, 100 で成り立つ | `test_paper_upper_bound` |

照合: **一致**（3つの数値例とも）。

## 上限（仮の計算）

| 前提 | 値 | 状態 |
|---|---|---|
| ホールドアウトを除いた取得期間 | 1.5 年（2年 − 末尾6か月） | **仮。** 仕様書に書かれた無料プランの範囲から出した。APIが実際に返した日付ではない |
| 目標の E[max_N]（年率シャープ） | 1.0 | **仮。** 論文の例と同じ値を置いただけ。本人が決める |
| 上限 | **5**（MinBTL(5) = 1.422 年、MinBTL(6) = 1.690 年） | 仮 |

## 未確定の理由

1. 取得期間の長さが、APIの返した日付ではなく、仕様書の記述からの推定である。
2. 目標のシャープ（E[max_N]）を本人がまだ決めていない。
3. 検証区間とパージで、学習に使える長さはさらに短くなる。どの長さで数えるかが未定。

## 数え方

- N は独立な試行の数。似た設定どうしでも、独立とみなして数える（保守側）。
- 捨てた設定、近くのパラメータ、特徴量を足した回数、銘柄や期間の選び直し、乱数の種の選び直し、検証期間を見て閾値を変えた回数も、1回ずつ数える。銘柄を横断して選ぶときは、銘柄数×規則数。
- 上限が1未満、または未確定なら、モデル探索に進まない。
