# 研究/コンペ: 機械学習による短期リターン予測で実際に効くもの

> 調査日: 2026-10-13 / 観点: ml-forecasting-evidence / 状態: 一次調査(未検証)

**調査の制約(先に明記)**: WebSearch はセッション共有の上限に達し、成功した検索は 12 回で打ち切られた(指示の「最低 15 回」は未達)。以降は既知 URL への WebFetch(約 90 回、うち失敗約 10 回)と、論文 PDF 4 本(Krauss-Do-Huck 2017、Fischer-Krauss 2017、Gu-Kelly-Xiu 2020、Rahimikia-Ni-Wang 2025)をローカルでテキスト化して本文を直接確認した。Kaggle のディスカッション本文は JavaScript 描画のため取得できず、Optiver 1 位解法などは二次情報どまり(該当箇所に ❓ を付けた)。本ノートは調査であり投資助言ではない。

## 結論(5〜10 行)

1. **到達可能な精度は小さい。** 日次・クロスセクションのリターン予測で公表されている水準は、IC(予測と実現の相関)0.03〜0.06、方向的中率 51〜52%(全銘柄)、確信度上位だけに絞っても 54% 前後、R² はほぼゼロ(月次で 0.3〜0.4%、日次は 0 近辺〜負)。これを大きく超える数字が手元で出たら、まずリークを疑う。
2. **効くのは GBDT と少数の価格系特徴量。** LightGBM / CatBoost / XGBoost に、短期リバーサル(1〜5 日リターン)、移動平均乖離、ボラティリティ、出来高・流動性を入れた構成が、論文でもコンペでも一貫して最上位か僅差。LSTM / Transformer / TabNet は安定して GBDT を上回らない。
3. **単純ベースラインが非常に強い。** JPX Tokyo Stock Exchange Prediction(Kaggle 2022、日本株 2,000 銘柄)の上位は、1 位が素の線形回帰、3 位が決定木 1 本、4 位と 9 位は学習なしの並べ替えルール。Chronos の統計裁定は「過去数日の単純リバーサル」と同等以下。MVP は必ずこれらと並べて採点する。
4. **取引コストで消える。** 日次ロングショートのシャープは 0 bps で約 6.4、20 bps で約 −3.6(Rahimikia 2025)。Krauss 2017 は 2010 年以降コスト後マイナス。本プロジェクトは発注しないので「予測精度の採点」には使えるが、「儲かる」とは言えない。
5. **非定常性は実在する。** S&P 500 では同じ手法のシャープが 1992〜2001 年の 6.7 から 2010〜2015 年の −0.9 に落ちた。再学習(オンライン学習)は上位解法で一貫して効いている。固定モデルを放置しない設計が必須。
6. **時系列基盤モデル(TSFM)は主軸にしない。** 汎用 TSFM のゼロショットは日次リターンで GBDT に負ける(R² −1.37%〜−2.80%)。金融データで事前学習したもの(Kronos、FinText)は比較対象として 1 本入れる価値がある程度。独立した再現報告は見つからなかった。
7. **リークの典型は 5 つ。** 配当落ち、株式分割の調整係数、同日集計のシフト忘れ、シャッフル KFold、公開リーダーボードや評価期間でのパラメータ選択。
8. **MVP の推奨**: 流動性上位 500〜1,000 銘柄、目的変数は「寄り→引けリターンの当日クロスセクション順位」、特徴量 30 個前後、LightGBM、ウォークフォワード(エンバーゴ 20 営業日)、評価は日次 RankIC の平均と ICIR、ベースライン 5 種との差分。

## 丸パクリ候補(優先度順の表)

| # | 名前 | URL | 種別 | ライセンス | 鮮度 | 何をどう写すか | 確認 |
|---|---|---|---|---|---|---|---|
| 1 | J-Quants/JPXTokyoStockExchangePrediction(Kaggle JPX 2022 上位 10 解法) | https://github.com/J-Quants/JPXTokyoStockExchangePrediction | repo | Apache-2.0 | 2022 年コンペ。スター 58。最終 push 日は未確認(API が 403) | `winner-models/2nd/2nd-place-solution.ipynb` の `add_features`(20/40/60 日のリターン・ボラ・移動平均乖離)、`calc_spread_return_per_day` / `calc_spread_return_sharpe`(評価関数)、LightGBM 設定。`winner-models/5th/JPX_5th_place_code.py` の 8 特徴量と「市場平均控除 2 日リターン」目的変数、`LGBMRegressor(max_depth=2, learning_rate=0.2, n_estimators=2000)`。1 位(線形回帰)・3 位(決定木)・4 位・9 位(ルール)はベースラインとしてそのまま実装 | ✅ |
| 2 | microsoft/qlib の Alpha158 と LightGBM ベンチマーク | https://github.com/microsoft/qlib | repo | MIT | スター 49.3k。Python 3.8〜3.12 対応(3.13 は表に無い) | `qlib/contrib/data/loader.py` の Alpha158 計算式(K 線 9 個+ローリング 29 演算子 × 窓 5/10/20/30/60)を pandas で再実装。`examples/benchmarks/LightGBM/workflow_config_lightgbm_Alpha158.yaml` のハイパーパラメータと学習・検証・テスト分割。`examples/benchmarks/README.md` の IC 表を「相場」として使う | ✅ |
| 3 | Rahimikia, Ni, Wang "Re(Visiting) Time Series Foundation Models in Finance" | https://arxiv.org/abs/2511.18578 | paper | arXiv | 2025-11-23 | 評価設計を丸ごと写す: 入力は過去リターン窓 5/21/252/512、拡張窓で毎年再学習、指標は R²oos・方向的中率・十分位ロングショート、コスト 0/20/40 bps 感応度。付録 Table C.1 の探索グリッド(LightGBM: num_leaves {32,64,128,256,512}、学習率 {0.01,0.05,0.1})。数値は「GBDT が基準線」の根拠 | ✅(PDF 本文) |
| 4 | Krauss, Do, Huck 2017 "Deep neural networks, gradient-boosted trees, random forests: Statistical arbitrage on the S&P 500" | https://www.iwf.rw.fau.de/files/2016/03/03-2016.pdf | paper | 作業論文(EJOR 259(2):689–702) | 2017 | 特徴量 31 個(R(m), m∈{1..20}∪{40,60,…,240})、目的変数(翌日リターンが当日クロスセクション中央値を上回るか)、学習 750 日/評価 250 日のスライド、上位・下位 k 銘柄評価、GBT(100 本・深さ 3・学習率 0.1)、RF(1000 本・深さ 20) | ✅(PDF 本文) |
| 5 | Fischer, Krauss "Deep learning with long short-term memory networks for financial market predictions" | https://www.econstor.eu/handle/10419/157808 | paper | 作業論文(FAU DP 11/2017。後に EJOR 掲載というのは記憶ベースで未確認) | 2017〜2018 | 単純ルールのベースライン: 「直近 5 日累積リターンが最も低い k 銘柄を上位、最も高い k 銘柄を下位」。LSTM の入力仕様(標準化した日次リターン 240 本の系列)は後回し | ✅(PDF 本文) |
| 6 | skfolio `CombinatorialPurgedCV` / `WalkForward` | https://skfolio.org/generated/skfolio.model_selection.CombinatorialPurgedCV.html | library | BSD | 2026 年版ドキュメント | `CombinatorialPurgedCV(n_folds=10, n_test_folds=8, purged_size=0, embargo_size=0)` を、purged_size と embargo_size を指定して使う。Python 3.13 対応は未確認 | ✅ |
| 7 | Valeyre, Aboura "LLMs for Time Series: an Application for Single Stocks and Statistical Arbitrage" | https://arxiv.org/abs/2412.09394 | paper | arXiv | v2 2025-11-03 | 「TSFM と単純リバーサル(STR)を同じ土俵で比べる」評価表の形を写す。3 bps のコストでシャープ 3.17→−1.49 という感応度検査も写す | ✅ |
| 8 | shiyu-coder/Kronos(金融 K 線の基盤モデル) | https://github.com/shiyu-coder/Kronos | repo / model | MIT | スター 40,618、最終 push 2026-04-13、アーカイブなし | `KronosPredictor(model, tokenizer, max_context=512)`、`predict(df, x_timestamp, y_timestamp, pred_len, T, top_p, sample_count)`、`predict_batch`。重みは `NeoQuasar/Kronos-small`(24.7M)、`NeoQuasar/Kronos-mini`(4.1M、文脈 2048)。予測系タスクは T≈0.6 が良いと論文付録。比較対象として 1 本だけ採点に載せる | ✅ |
| 9 | FinText の金融事前学習 TSFM と読み込みコード | https://huggingface.co/FinText / https://github.com/DeepIntoStreams/TSFM_Finance | model / repo | コード Apache-2.0、重みのライセンスは未記載 | 2025-11 更新、スター 31 | `FinText/Chronos_Small_2022_Global` などを、過去 21 日の超過リターンを入力に `prediction_length=1` で呼ぶ。年別モデル(2000〜2023)なので、評価日より前の年のモデルを使えば先読みを避けられる | ✅ |
| 10 | Optiver - Trading at the Close 9 位の XGBoost ノート | https://github.com/ChunhanLi/9th-kaggle-optiver-trading-close | repo | 記載なし(コードの複製は避け、式だけ写す) | 2023〜2024、スター 72 | 板・オークション特徴量の式(不均衡比 (X−Y)/(X+Y)、銘柄中央値での規格化、時点ごとの加重市場平均 `global_*`、公開済みターゲットのラグ)、XGBoost 設定(`reg:absoluteerror`、learning_rate 0.01、max_depth 10 ほか)、「時系列ホールドアウトで本数決定→全データで再学習」の手順。日本株の引け前予測をやる段階で使う | ✅ |
| 11 | cweill/jane-street-causal-forecasting(Jane Street 2024 2 位手法の再構成) | https://github.com/cweill/jane-street-causal-forecasting | repo | 記載なし | 2025〜2026 | オンライン学習の手順(前日ラベルが出たら Adam 3 ステップ、学習率 1e-4)、日付単位の分割表、`scripts/check_leakage_mutations`。固定モデルとオンライン更新の差を測る実験設計を写す | ✅ |
| 12 | Wy66wy/Jane-Street-Real-Time-Market-Data-Forecasting | https://github.com/Wy66wy/Jane-Street-Real-Time-Market-Data-Forecasting | repo | MIT | 2025 年頃、スター 0 | リーク検査の作法: ラグ特徴は銘柄ごとに 1 日シフト、学習時と推論時の特徴量一致を相関 0.999 以上で検査、`PurgedTimeSeriesSplit` の gap は既定 5 日・推奨 20 日 | ✅ |
| 13 | stefan-jansen/alphalens-reloaded | https://github.com/stefan-jansen/alphalens-reloaded | library | Apache-2.0 | スター 669 | `get_clean_factor_and_forward_returns` → `create_full_tear_sheet` で IC・分位リターン・回転率を一括出力。特徴量 1 本ずつの事前スクリーニングに使う | ✅ |
| 14 | RiskLabAI.py(トリプルバリア、パージ付き CV、PBO/DSR) | https://github.com/RiskLabAI/RiskLabAI.py | library | BSD-3-Clause | スター 6、コミット 411 | トリプルバリアラベル、メタラベル、`CROSS_VALIDATORS.create("purgedkfold", ...)`、PSR/DSR/PBO。関数名は README に無く、ソース確認が必要 | ✅(README のみ) |
| 15 | JapanExchangeGroup/J-Quants-Tutorial | https://japanexchangegroup.github.io/J-Quants-Tutorial/ | 教材 | CC BY-NC-ND 4.0(改変物の再配布不可・非営利) | 2021 年の SIGNATE コンペ教材、スター 186 | 日本株固有の注意点を写す: 累積調整係数は未来情報を含む、学習・検証・テストの間に 1 か月空ける、特徴量は 20/40/60 営業日のリターン・ボラ・移動平均乖離。コードは複製せず式だけ使う | ✅(前半 20 万字) |
| 16 | nishimoto「マーケット予測コンペの問題設計と取り組み方」 | https://www.docswell.com/s/8980249862/KR2YD1-KantoKaggler3rd_MarketCompetition | スライド | 記載なし | 2025-02-15 | 「特徴量と目的変数のスピアマン相関の最大値が 0.05 程度なら難問」という見極め基準、守りの原則 2 つ(異常値除外、特定特徴量に依存しない) | ✅ |
| 17 | numerai/example-scripts | https://github.com/numerai/example-scripts | repo | MIT | 継続更新 | `numerai/` の Feature Neutralization ノート(特徴量中和)、Target Ensemble。後回し | ✅(README のみ) |
| 18 | stefan-jansen/machine-learning-for-trading(第 3 版) | https://github.com/stefan-jansen/machine-learning-for-trading | repo / book | コード MIT、本文は著作権あり | 2026 年、スター 21.3k | `08_financial_features`、`12_gradient_boosting`、`18_transaction_costs`、`utils/` の CV コード。体系的な参照用 | ✅(README のみ) |
| 19 | Gu, Kelly, Xiu "Empirical Asset Pricing via Machine Learning" | https://dachxiu.chicagobooth.edu/download/ML.pdf | paper | RFS 33(5), 2020 | 2020 | 特徴量を毎期クロスセクション順位にして [−1,1] に写す前処理、交差検証せず時間順の学習・検証・テスト、年 1 回の再学習。重要変数の一覧 | ✅(PDF 本文) |
| 20 | Optiver - Trading at the Close 1 位解法 | https://www.kaggle.com/competitions/optiver-trading-at-the-close/discussion/487446 | 解法 | — | 2023-12 | CatBoost 0.5 / GRU 0.3 / Transformer 0.2 の加重平均、CatBoost 重要度上位 300 特徴量、オンライン再学習、予測から加重平均を引く後処理 | ❓(本文取得不可。検索結果の要約のみ) |
| 21 | 時系列基盤モデル各種(Chronos / TimesFM / Moirai / Lag-Llama / TimeGPT) | 詳細節の表を参照 | model | 各種 | 各種 | MVP では使わない。比較枠で 1 本だけ | ✅ |
| 22 | PriorLabs/TabPFN | https://github.com/PriorLabs/TabPFN | model | コード Apache-2.0、2.5 以降の重みは非商用 | 既定は TabPFN-3.5(重み 2026-09-09) | CPU では 5,000 サンプル上限かつ低速。75 万行規模の MVP には不向き。後回し | ✅ |
| 23 | hudson-and-thames/mlfinlab | https://github.com/hudson-and-thames/mlfinlab | library | all rights reserved(有償) | — | **使わない**。代替は #6 と #14 | ✅ |

## 詳細(項目ごとに、中身・数値・使い方・限界)

### 1. JPX Tokyo Stock Exchange Prediction(Kaggle、2022、日本株)

日本株で最も直接的な先行例。上位 10 解法の説明とコードが JPX 系の公式リポジトリで公開されている。

**課題設定**(2 位ノートの関数から確認)
- 目的変数 `Target` は翌営業日終値から翌々営業日終値への変化率(5 位 README の記述: P(t+2)/P(t+1) − 1)。
- 提出は約 2,000 銘柄の順位 `Rank`(0 が最上位)。
- 評価は日次スプレッドリターンのシャープレシオ。`calc_spread_return_per_day(df, portfolio_size=200, toprank_weight_ratio=2)` は、`weights = np.linspace(2, 1, 200)` を作り、順位上位 200 銘柄の Target に重みを掛けて合計し `weights.mean()` で割ったもの(買い)から、下位 200 銘柄の同じ計算(売り)を引く。スコアは日次値の `mean() / std()`(年率化なし)。

**上位解法の中身**(各順位の README とコードを確認)

| 順位 | Private スコア | 中身 |
|---|---|---|
| 1 位 | 0.381 | scikit-learn の `LinearRegression`。入力は SecuritiesCode、OHLC、Volume、AdjustmentFactor、ExpectedDividend、SupervisionFlag と自作の Daily_Range、Mean。標準化あり。作者は株の知識が無いと明記。検証方法の記述なし |
| 2 位 | 0.356 | LightGBM 回帰、特徴量 14 個、アンサンブルなし。CV は約 0.25、Private は 0.36 で「予想より高い」と本人が記載 |
| 3 位 | 0.352 | `DecisionTreeRegressor` 1 本。特徴量は Open/High/Low/Close の 4 つだけ |
| 4 位 | 0.347 | 学習なし。`return_1day` で並べ、`ExpectedDividend > 0` の銘柄を最下位へ移すルール。作者は「運が最重要」と記載 |
| 5 位 | 0.339 | LightGBM 回帰、特徴量 8 個、目的変数を作り直し。拡張窓ウォークフォワードで月次スコアは長期的に 0.2 前後 |
| 6 位 | 0.308 | LightGBM、特徴量を 1 個(前日終値との差)まで削減 |
| 7 位 | 0.301 | `LGBMHierarchModel`(階層型 LightGBM)。詳細は README に無し |
| 8 位 | 0.289 | LightGBM、Optuna、5 分割ウォークフォワード(学習と検証の間に小さな gap)。銘柄コードが最重要、次がリターンの移動平均 |
| 9 位 | 0.281 | 学習なし。当日の日中リターン (C−O)/O で並べるだけ(昇順か降順かは README から判別できず) |
| 10 位 | 0.280 | README 取得不可(404) |

**2 位のコード詳細**(`winner-models/2nd/2nd-place-solution.ipynb`)
- 特徴量: `return_Nmonth = Close.pct_change(W)`、`volatility_Nmonth = np.log(Close).diff().rolling(W).std()`、`MA_gap_Nmonth = Close / Close.rolling(W).mean()`、W = 20, 40, 60。これに High, Low, Open, Close, Volume を足して 14 個。最重要は `MA_gap_3month`。
- LightGBM: `learning_rate 0.005`、`objective 'regression'`、`boosting 'gbdt'`、`metric 'None'`、評価関数は自作のピアソン相関、`num_boost_round 3000`、`early_stopping 300`、最良 606 本。
- 検証の相関は 0.0149(学習側は 0.0942)。**この水準の相関で Private 2 位になる課題**だという点が重要。
- 分割は時系列ではなく銘柄で 2 群(Target の最大−最小が小さい 1,000 銘柄で学習、残りで検証)。提出時は前者の予測を当日中央値に置き換えてから順位付け、つまり値動きの大きい銘柄だけを上位・下位に送る。
- 限界: `add_features` が銘柄ごとの groupby なしで全体に適用されており、銘柄境界をまたぐ計算になっている可能性がある。コードをそのまま写さず、銘柄ごとに計算し直すこと。

**5 位のコード詳細**(`winner-models/5th/JPX_5th_place_code.py`)
- 特徴量 8 個: `mrsignal = P(t)/P(t−2)`(2 日リターン、作者によれば最重要の駆動要因で強い平均回帰)、`momsignal = P(t−25)/P(t−131)`、`volsignal =` 過去 231 日の絶対リターン合計、`adv_rank =` 11 日平均出来高の当日順位、`Close_rank =` 株価水準の当日順位、`ave_mrsignal` と `ave_momsignal`(当日の全銘柄平均)、`SecuritiesCode`(カテゴリ)。
- 目的変数: `alt_Target = P(t+2)/P(t) − 1` から当日の全銘柄平均を引いたもの。
- 学習行の選別: 各日の Target 順位が上位 250 と下位 250 の行だけで学習(ウィンザー化より良かったと記載)。
- モデル: `lgb.LGBMRegressor(boosting_type='gbdt', max_depth=2, learning_rate=0.2, n_estimators=2000, seed=42)`、カテゴリは `SecuritiesCode`。
- 効かなかったもの: 財務比率、TabNet、DNN、アンサンブル。インプライドボラは小さな改善のみで不採用。
- 限界: 推論側と学習側で特徴量の定義が一致していない箇所がある(推論は生の Close、学習は調整済み価格系列)。

**読み取れること**
- 上位が線形回帰・決定木・ルールで占められ、2 位本人も CV 0.25 と Private 0.36 の乖離を認めている。評価期間が短く(約 3 か月というのは記憶ベースで、今回は一次確認できていない)、運の寄与が大きい。4 位本人も「運が最重要」と書いている。順位そのものより「日次スプレッドのシャープ 0.2〜0.4(年率化前)が上限の目安」という相場観として使う。
- 複数の上位解法に共通するのは、短期リターン(1〜2 日)、移動平均乖離、ボラ、銘柄コード、市場平均である。

### 2. Optiver - Trading at the Close(Kaggle、2023、Nasdaq 引け前 10 分)

- 課題: 引け前 10 分間、60 秒先の WAP リターンから合成指数のリターンを引いた値(bp 単位)を予測。指標は MAE。約 4,000 チーム(検索結果の要約)。
- 目的変数の式(fan2goa1 のブログで確認): `(StockWAP(t+60)/StockWAP(t) − IndexWAP(t+60)/IndexWAP(t)) × 10000`。
- 1 位(❓ 二次情報): CatBoost 0.5、GRU 0.3、Transformer 0.2 の加重平均、3 モデル共通の 300 特徴量(CatBoost 重要度で選抜)、CV 5.8117 / Private 5.4030。オンライン再学習なし 5.4438 → 1 回 5.4157 → 5 回 5.4030。後処理は「予測から銘柄ウェイト加重平均を引く」。GRU は 55 時点 × 特徴量、4 層。
- nishimoto スライド(✅)では、1 位は「各種指標の市場平均・時間平均との比」を使い、Public と Private の入れ替わりがほぼ無かった良問とされる。
- 9 位ノート(✅): 157 特徴量、XGBoost(`objective reg:absoluteerror`、`learning_rate 0.01`、`max_depth 10`、`min_child_weight 8.86`、`subsample 0.771`、`colsample_bytree 0.535`、`reg_alpha 0.129`、`reg_lambda 0.393`、`gamma 0.244`)。検証は `date_id >= 390` のホールドアウト、最良 2,978 本で MAE 5.8705(学習率 0.01 の 0 本目、つまりほぼ定数予測の時点で 6.029)。**上位解法でも定数予測からの改善は約 2.6%**。本番用は 2,978 本固定で全データ再学習。
- fan2goa1(✅): パージ付き KFold(480 日を 5 分割、境界の前後 2 日を除去)で Public 5.3341、通常 KFold に替えると 5.3389 に悪化。
- 日本株への転用: 東証の引け前板情報を持たない MVP では直接使えない。写す価値があるのは「銘柄中央値で規格化」「同一時点の市場加重平均との比」「公開済みターゲットのラグ」「定期再学習」という設計パターン。

### 3. Jane Street(2021 / 2024)

- 2024(Real-Time Market Data Forecasting): 指標は重み付きゼロ平均 R²。全ゼロ予測で 0。公開 LB 上位は 0.005〜0.01 程度(Wy66wy README)、2 位 Patrick Yam の報告値は 0.02059(cweill README)。nishimoto スライドによれば特徴量と目的変数のスピアマン相関は最大でも 0.05 程度。
- cweill の再構成(本人コードではなく未検証の再現): 固定モデル R² 0.01433 → オンライン更新あり 0.02078(差 +0.00645、約 45% 改善)。設定はオフライン学習率 5e-4、オンライン 1e-4、毎日 Adam 3 ステップ(betas 0.8, 0.95)、9 エポック、17 シード。
- 2021(Market Prediction): scaomath チーム(241/4,245 位)の検証は 3 分割、各 100 日、学習と検証の間に 10 日の gap。ローカル CV と LB が食い違う例を多数報告。ノイズ除去した目的変数は CV で良く LB で悪かった。
- 2024 の 1 位解法は未確認。

### 4. Krauss-Do-Huck 2017 と Fischer-Krauss(収益の経年減衰)

**Krauss, Do, Huck(EJOR 259(2), 2017)**: S&P 500 構成銘柄(生存者バイアス除去)、1990〜2015 年、評価は 1992-12〜2015-10。
- k=10(上位 10 買い・下位 10 売り)の日次リターン(コスト前): DNN 0.33%、GBT 0.37%、RF 0.43%、3 モデル等加重 0.45%。コスト(片道 0.05%)後は 0.25%/日、年率シャープ 1.81。
- サブ期間(等加重、コスト後のシャープ): 1992-12〜2001-03 が 6.69、2001-04〜2008-08 が 0.51、2008-09〜2009-12 が 4.46、2010-01〜2015-10 が −0.88(年率 −14〜−25%)。最後の期間もコスト前はプラス(シャープ 1.2〜2.2)。
- 変数重要度: 木系では直近 4〜5 日のリターンが最上位。次が 20〜240 日の月次解像度リターン、11〜20 日は最下位群。
- 木の本数を倍にしても 0.37→0.38%、0.43→0.44% とほぼ変わらない。

**Fischer, Krauss(FAU DP 11/2017)**: 同じデータで LSTM(入力は標準化した日次リターン 240 本、特徴量 1 個)。
- k=10 でコスト前 0.46%/日(シャープ 5.8)、コスト後 0.26%。的中率 54.3%。RF はコスト前 0.43%・コスト後 0.23%、DNN はコスト後 0.12%、ロジスティック回帰は 0.06%(有意でない)。
- 2010〜2015 年は RF が損失、LSTM はコスト後ほぼ横ばい。
- LSTM が選ぶ銘柄の共通点: 高ボラ、平均以下のモメンタム、直近数日の極端な動き(リバーサル)、高ベータ。
- 単純ルール(直近 5 日累積リターンの最下位 k 銘柄を買い、最上位 k 銘柄を売り)はコスト前 0.23%/日、コスト後 3 bps。これだけで LSTM の買い側リターン分散の 52.1%、売り側の 53.6% を説明する(作業論文は "bps" と表記しているが文脈上 % の誤記と読める)。

### 5. Gu-Kelly-Xiu 2020(月次、米国)

- 約 30,000 銘柄、1957〜2016 年、94 特性(マクロ交互作用と業種ダミー込みで 920 変数)。学習 1957〜1974、検証 1975〜1986、テスト 1987〜2016。年 1 回再学習、学習窓は拡張、検証窓は 12 年でローリング。時間順を保つため交差検証は使わない。
- 月次 R²oos: 全変数 OLS −3.46%、3 変数 OLS 0.16%、Elastic Net 0.11%、PLS 0.27%、PCR 0.26%、GLM 0.19%、RF 0.33%、GBRT 0.34%、NN1 0.33%、NN3 0.40%(最高)。大型株では木系と NN が 0.52〜0.70%。
- 重要変数は 4 群: 価格トレンド(短期リバーサル mom1m、mom12m、chmom、indmom、maxret、mom36m)、流動性(turn、SD_turn、mvel1、dolvol、ill、zerotrade、baspread)、リスク(retvol、idiovol、beta、betasq)、バリュエーション(ep、sp、agr)。
- NN4 の十分位ロングショート: 時価加重シャープ 1.35、等加重 2.45。回転率は月 110〜130%(短期リバーサルは 172.6%)。本文に取引コスト控除後の成績は見当たらなかった。
- 後続の Avramov, Cheng, Metzker(Management Science 69(5), 2023, 2587–2619。要旨のみ確認): 深層学習シグナルの利益は裁定しにくい銘柄と局面に集中し、マイクロキャップ・財務困難銘柄・高ボラ局面を除くと大きく縮み、妥当な取引コストでさらに悪化する。

### 6. 日次リターンでの GBDT と TSFM の直接比較(Rahimikia, Ni, Wang 2025)

- データ: 94 か国の日次超過リターン、1990〜2023 年。評価は 2001〜2023 年、拡張窓。米国テストは 1,800 万件超。入力は過去リターンのみ(窓 5/21/252/512)。
- ベンチマーク: CatBoost(窓 512)で R²oos −0.03%、方向的中率 51.16%、F1 0.49。CatBoost の窓平均は R² −0.10%、OLS は −0.47%。小型株(時価総額下位 25%)は R² 0.51%・的中率 52.29%、大型株(上位 25%)は −0.37%・50.76%。
- CatBoost の十分位ロングショート(等加重、日次リバランス、コストなし)は年率 46.50%、シャープ 6.79(窓 252)。
- ゼロショット TSFM: Chronos large(窓 512)R² −1.37%、的中率 51% 強、年率 20.17%。TimesFM 500M は R² −2.80%、的中率 50% 未満、年率 −1.47%。ファインチューニングは大半で悪化。
- 金融データでゼロから事前学習: Chronos small(窓 512)R² −0.59%、年率 36.84%、シャープ 5.42。グローバルデータ+JKP ファクター+合成データで的中率 51.74%(CatBoost 51.16%)、シャープ 6.78(CatBoost 6.46)、年率は 41.89% 対 47.25%。
- **コスト**: ベンチマークの平均シャープは 0 bps で 6.44、20 bps で −3.62、40 bps で −13.59。全モデルが 20 bps でマイナス。小型 21.3 bps・大型 11.2 bps の混合コストでもベンチマークは −3.0〜−3.7。
- 経年: どのモデルも時間とともにシャープが低下する(脚注 37)。

### 7. Qlib ベンチマーク(中国 A 株 CSI300、日次)

Alpha158 特徴量での公式表(20 シード平均):

| モデル | IC | ICIR | Rank IC | 年率超過 | IR |
|---|---|---|---|---|---|
| LightGBM | 0.0448 | 0.366 | 0.0469 | 9.01% | 1.02 |
| XGBoost | 0.0498 | 0.378 | 0.0505 | 7.80% | 0.91 |
| CatBoost | 0.0481 | 0.337 | 0.0454 | 7.65% | 0.80 |
| Linear | 0.0397 | 0.300 | 0.0472 | 6.92% | 0.92 |
| MLP | 0.0376 | 0.285 | 0.0429 | 8.95% | 1.14 |
| LSTM | 0.0318 | 0.237 | 0.0435 | 3.81% | 0.56 |
| Transformer | 0.0264 | 0.205 | 0.0407 | 2.73% | 0.40 |
| TabNet | 0.0204 | 0.155 | 0.0333 | 2.27% | 0.37 |
| DoubleEnsemble | 0.0521 | 0.422 | 0.0502 | 11.58% | 1.34 |

- 線形モデルの Rank IC(0.0472)は LightGBM(0.0469)と同水準。生の時系列を入れる Alpha360 では GRU(IC 0.0493)や HIST(0.0522)が LightGBM(0.0400)を上回るが、Transformer(0.0114)と TabNet(0.0099)は最下位。
- LightGBM 設定(`workflow_config_lightgbm_Alpha158.yaml`): `loss mse`、`colsample_bytree 0.8879`、`learning_rate 0.2`、`subsample 0.8789`、`lambda_l1 205.6999`、`lambda_l2 580.9768`、`max_depth 8`、`num_leaves 210`。学習 2008〜2014、検証 2015〜2016、テスト 2017-01〜2020-08。戦略は `TopkDropoutStrategy(topk=50, n_drop=5)`、コストは買い 0.05%・売り 0.15%。
- ラベルの定義は取得ページに無く未確認(❓ 記憶では翌日終値から翌々日終値のリターン)。
- 限界: 中国 A 株、2017〜2020 年、値幅制限と空売り制約のある市場。日本株にそのまま当てはまる保証は無い。公式データセットは一時停止中と README に記載。

### 8. 板(LOB)深層学習: DeepLOB とその後

- DeepLOB(Zhang, Zohren, Roberts、IEEE Trans. Signal Processing 67(11), 2019、arXiv:1808.03668): 畳み込み+LSTM。ベンチマーク LOB データとロンドン証券取引所 1 年分で既存手法を上回り、学習に無い銘柄にも転移すると主張(要旨)。
- LOBCAST(Prata ほか 2023、arXiv:2308.01915): 15 個の LOB 深層学習モデルを再評価し、全モデルが新しいデータで大きく性能低下。
- Briola, Bartolucci, Aste 2024(arXiv:2403.09267、LOBFrame): Nasdaq 銘柄で、高い予測力が実行可能な売買シグナルに対応するとは限らないと結論。銘柄の微細構造特性で効き方が変わる。
- 3 本とも要旨のみ確認。板データが無料で手に入らない本プロジェクトでは後回しでよい。

### 9. 時系列基盤モデル(TSFM)

| モデル | 入手先 | ライセンス・状態 | リターン予測の証拠 |
|---|---|---|---|
| Kronos | github.com/shiyu-coder/Kronos | MIT。mini 4.1M / small 24.7M / base 102.3M 公開、large 499.2M 非公開。45 取引所・120 億本超の K 線で事前学習(2024-06 まで)、評価は 2024-07 以降 | 著者論文(arXiv:2508.02739、検索結果では AAAI 2026 採択)。日本取引所(XJPX)のリターン予測: Kronos-L IC 0.0668 / RankIC 0.0687。一方、同じ表でゼロショット Moirai-L は RankIC 0.0793、PatchTST は IC 0.0655、DLinear は IC 0.0621 で、**日本株での優位は IC では僅差、RankIC では Moirai に負けている**。CSI300/CSI800 のバックテスト(コスト 0.15%、10 日先予測、topk/dropn)では Kronos-L が年率超過 21.9% / 19.7% で最良。独立した再現は見つからず |
| FinText(金融事前学習 Chronos / TimesFM) | huggingface.co/FinText | 重みのライセンス未記載。613 モデル(年別 2000〜2023、US / Global / Augmented) | 上記 6 節。GBDT と同等〜やや上、コスト後は全滅 |
| Chronos / Chronos-Bolt / Chronos-2 | github.com/amazon-science/chronos-forecasting | Apache-2.0、スター 6.1k。Chronos-2(120M、2025-10-20)は共変量対応 | ゼロショットは日次リターンで R² −1.37%(Rahimikia)。Valeyre-Aboura では残差リターンの粗シャープ 1.2〜3.2(α=0.2〜0.4)だが単純リバーサル(2.2〜4.3)以下、3 bps のコストで 3.17 → −1.49。Kronos 論文の CSI バックテストでは Chronos-L が年率 −6.6% |
| TimesFM | github.com/google-research/timesfm | コードと 2.5 までの重みは Apache-2.0。3.0(2026-08 公開)の重みは非商用ライセンス。スター 34.4k | ゼロショット 500M で R² −2.80%、的中率 50% 未満(Rahimikia)。XJPX リターン予測 IC 0.0498(Kronos 論文) |
| Moirai(uni2ts) | github.com/SalesforceAIResearch/uni2ts | コード Apache-2.0、「研究目的のみ」の注記。最新は Moirai-2.0-R-small(2025-08) | Kronos 論文の XJPX 表で RankIC 0.079。Noguer i Alonso-Franklin(arXiv:2606.27100)では Moirai-2.0 と TimesFM-2.5 が平均順位最良だが、ランダムウォークに対する改善は小さく散発的 |
| Lag-Llama | github.com/time-series-foundation-models/lag-llama | Apache-2.0、スター 1.6k。更新は 2024-06 で止まっている | 金融リターンでの証拠は未確認 |
| TimeGPT | github.com/Nixtla/nixtla | モデルは非公開、API キー必須。SDK は Apache-2.0 | Noguer i Alonso-Franklin の比較対象に含まれるが個別の優位は示されず |

**判断**: 使う価値は「比較対象として 1 本」まで。根拠は 3 点。汎用 TSFM のゼロショットは日次リターンで GBDT に負ける。金融特化の事前学習でも GBDT との差は的中率 0.6 ポイント程度で、コスト後はどちらもマイナス。Kronos は著者以外の再現が見つからず、リポジトリ自身が「デモであり本番向けではない、生のシグナルである」と注記している(Issue #299「予測はコイン投げと変わらない」、#133、#35 など懐疑的な議論もある。題名のみ確認)。

### 10. 表形式モデルとラベル設計

- GBDT が基準線である根拠: Rahimikia(日次、94 か国)、Qlib(CSI300)、JPX 上位解法(2・5・6・7・8 位が LightGBM)、Optiver 1 位の主力が CatBoost、Grinsztajn ほか 2022(arXiv:2207.08815、中規模表データでは木系が最先端)。
- TabPFN: 既定の TabPFN-3.5 は 100 万行まで対応とされるが、CPU では 5,000 サンプル上限かつ低速。2.5 以降の重みは非商用。MVP の主軸には向かない。
- LightGBM のランキング目的(LGBMRanker): JPX 2 位は「CV が改善しなかった」と記載。回帰で十分。
- ラベル設計で実際に使われているもの:
  - クロスセクション中央値超えの 2 値(Krauss、Fischer-Krauss)
  - 市場平均控除リターン(JPX 5 位、Optiver の対指数リターン)
  - クロスセクション順位(GKX は特徴量側、JPX は提出形式)
  - 学習行を上位・下位の裾に限定(JPX 5 位)
  - トリプルバリアとメタラベル(López de Prado の書籍。実装は RiskLabAI.py)。**短期株リターンでトリプルバリアが単純な固定期間ラベルより良いという数値証拠は今回見つけられなかった**(未確認)。

## 写せる MVP レシピ(必ず答えること 1)

出典のある部品を組み合わせた提案であり、この組み合わせ自体の成績は未検証。出典の無い値には「提案値」と明記する。

**ユニバース**
- 東証プライムのうち過去 60 営業日の平均売買代金上位 500〜1,000 銘柄(提案値)。毎月末に入れ替え、判定は入れ替え日より前のデータだけで行う。
- 上場廃止銘柄を含む時点情報で組むこと。現在の銘柄一覧から遡ると生存者バイアスが入る(Krauss は過去の構成銘柄で除去)。

**目的変数**
- 主: `y_raw = Close_t / Open_t − 1`(当日の寄り→引け)。
- 学習用ラベル: `y = y_raw − 当日ユニバース平均` を当日クロスセクション順位に変換し [−0.5, 0.5] に写す(JPX 5 位の平均控除と GKX の順位変換の組み合わせ)。
- 併走させる副ラベル: 「当日中央値超え」の 2 値(Krauss 型)。
- 寄り→引けにする利点: 配当落ちは前日終値→当日始値のギャップに出るため、ラベルが配当落ちの機械的下落に汚染されない(JPX では終値ベースのラベルで配当落ち銘柄を最下位に置くだけでスコアが上がった)。

**予測時刻と特徴量の締め切り**
- 版 A(MVP): 当日 8:50 までに予測を確定。使えるのは前営業日の引けまでの情報だけ。
- 版 B(後回し): 寄り付き後に当日ギャップ `Open_t / Close_{t−1} − 1` を使う。予測時刻とラベルの起点を別途定義し直す必要がある。

**特徴量リスト(版 A、すべて t−1 引け時点で計算)**

| 群 | 名前 | 計算式 | 出典 |
|---|---|---|---|
| 短期リターン | `ret_1, ret_2, ret_3, ret_5, ret_10, ret_20` | `C[t−1]/C[t−1−m] − 1` | Krauss(m=1..20)、JPX 5 位(m=2 が最重要) |
| 中長期リターン | `ret_40, ret_60, ret_120, ret_240` | 同上 | Krauss、JPX 2 位(20/40/60) |
| ラグ付きモメンタム | `mom_131_25` | `C[t−26]/C[t−132] − 1` | JPX 5 位 |
| ボラティリティ | `vol_20, vol_40, vol_60` | `std(diff(log C), W)` | JPX 2 位、J-Quants チュートリアル |
| 長期絶対変動 | `absret_231` | `sum(abs(ret_1), 231)` | JPX 5 位 |
| 移動平均乖離 | `ma_gap_20, ma_gap_40, ma_gap_60` | `C / mean(C, W)` | JPX 2 位(60 が最重要) |
| 前日ローソク足 | `KMID, KLEN, KUP, KLOW, KSFT` | `(C−O)/O`、`(H−L)/O`、`(H−max(O,C))/O`、`(min(O,C)−L)/O`、`(2C−H−L)/O` | Qlib Alpha158 |
| 日中と夜間の分解 | `intraday_1, overnight_1`、各 5 日・20 日合計 | `(C−O)/O`、`O[t−1]/C[t−2] − 1` | JPX 9 位(日中リターン) |
| レンジ位置 | `RSV_20, MAX_20, MIN_20` | `(C−min(L,20))/(max(H,20)−min(L,20))`、`max(H,20)/C`、`min(L,20)/C` | Qlib Alpha158 |
| 出来高・流動性 | `adv_11_rank, vma_5, vstd_20, amihud_20` | 11 日平均出来高の当日順位、`mean(V,5)/V`、`std(V,20)/V`、`mean(abs(ret_1)/売買代金, 20)` | JPX 5 位、Qlib、GKX(ill) |
| 価格水準・規模 | `close_rank, mcap_rank` | 当日クロスセクション順位 | JPX 5 位、GKX(mvel1) |
| 市場文脈 | `mkt_ret_1, mkt_ret_2, mkt_mom` | `ret_1`・`ret_2`・`mom_131_25` の当日全銘柄平均 | JPX 5 位(ave_mrsignal、ave_momsignal) |
| 業種相対 | `ret_5_sec, ret_20_sec` | 自銘柄 − 33 業種平均 | GKX(indmom)に準じた提案 |
| カレンダー | `dow, month_end` | 曜日、月末フラグ | 提案値 |

- 前処理: 銘柄固有の特徴量は当日クロスセクション順位にして [−1, 1] に写す(GKX)。欠損は 0(順位変換後の中央)で埋める。
- 価格は「予測日時点で知り得た調整」だけを使う。全期間の累積調整係数を過去へ適用しない(J-Quants チュートリアルの警告)。
- 銘柄コードをカテゴリとして入れるかは要検証。JPX 5 位と 8 位では最重要だったが、評価期間が短い課題での結果で、銘柄固有の過去傾向を覚えるだけの恐れがある。MVP では入れない版を基準にする(提案)。

**CV(パージとエンバーゴ)**
- 基本形: 拡張窓ウォークフォワード。初回学習 750 営業日、評価 250 営業日、250 日ずつ前進(Krauss)。データが短ければ初回 1 年・1 か月刻み(JPX 5 位)。
- 学習末尾と評価先頭の間に 20 営業日のエンバーゴを置く。根拠: 最長の特徴量窓・EWM 半減期を覆う 20 日(Wy66wy の推奨)、10 日(scaomath)、1 か月(J-Quants チュートリアル)。ラベルが当日内で完結するので重複ラベルのパージは 1 日で足りるが、特徴量の自己相関のために 20 日取る。
- ハイパーパラメータ選択は各学習窓の末尾 250 日を検証に使う(GKX 型)。シャッフル KFold は使わない。
- 頑健性確認(後回し): `skfolio.model_selection.CombinatorialPurgedCV(n_folds=10, n_test_folds=2, purged_size=1, embargo_size=20)` で複数経路の分布を見る(引数値は提案値)。

**モデルとハイパーパラメータ**

出典のある設定(そのまま試せる):

| 出典 | 設定 |
|---|---|
| JPX 5 位 | `LGBMRegressor(max_depth=2, learning_rate=0.2, n_estimators=2000, seed=42)` |
| JPX 2 位 | `learning_rate=0.005, objective='regression', num_boost_round=3000, early_stopping=300`(最良 606 本)、評価はピアソン相関 |
| Qlib | `learning_rate=0.2, max_depth=8, num_leaves=210, colsample_bytree=0.8879, subsample=0.8789, lambda_l1=205.6999, lambda_l2=580.9768` |
| Krauss の GBT | 100 本、深さ 3、学習率 0.1、分割ごとに特徴量の半分 |
| Rahimikia の探索範囲 | LightGBM: `num_leaves {32,64,128,256,512}`、学習率 `{0.01,0.05,0.1}`。CatBoost: 深さ `{2,3,4,5,6,8,10,12,14,16}`、学習率 `{0.01,0.05,0.1}`。初年度だけ調整して以後固定 |

MVP の初期値(提案値、未検証): `objective='regression'`、`learning_rate=0.03`、`num_leaves=31`、`max_depth=5`、`min_data_in_leaf=300`、`feature_fraction=0.7`、`bagging_fraction=0.7`、`bagging_freq=1`、`lambda_l2=50`、検証 RankIC で早期停止(上限 2,000 本、patience 200)、シード 5 本の平均。浅い木と強い正則化は JPX 5 位(深さ 2)と Qlib(L1 206、L2 581)の方向に合わせた。

- 再学習: 月 1 回、拡張窓(オンライン学習の効果は Jane Street 再構成で +45%、Optiver 1 位で MAE 5.4438→5.4030 ❓)。
- 規模の見積もり: 1,000 銘柄 × 750 日 = 75 万行 × 約 45 列。LightGBM なら CPU で数分以内に収まる見込み(未計測)。

**評価**
- 主指標: 日次 RankIC(予測と実現ラベルのスピアマン相関)の平均、標準偏差、ICIR(平均/標準偏差)、t 値(ICIR × √日数)。
- 副指標: 平均控除後リターンの方向的中率、上位十分位 − 下位十分位の日次スプレッド(コスト 0 / 片道 10 / 20 bps の 3 通り)、JPX 式スプレッドシャープ(上位・下位 200 を銘柄数に合わせて縮小)。
- 判定の目安: RankIC 平均 0.02〜0.05 で先行例並み。全銘柄的中率 51〜52% で先行例並み。**RankIC が 0.1 超、的中率が 55% 超ならリークを先に調べる**(Wy66wy は 1 日シフト忘れで R² が 0.5 を超えた例を挙げ、高得点は技量ではなくリークの兆候として扱えとしている)。
- 必ず同じ表にベースラインを並べる(次節)。

## 単純ベースラインの強さ(必ず答えること 2)

| ベースライン | 定義 | 強さの証拠 |
|---|---|---|
| B0 ゼロ予測 | 全銘柄同値 | Jane Street 2024 では全ゼロで R² = 0、上位でも 0.005〜0.02。GKX の全変数 OLS はゼロ予測に負ける(R² −3.46%) |
| B1 短期リバーサル | `−ret_5` と `−ret_2` で順位付け | Fischer-Krauss: 5 日リバーサルだけで LSTM のリターン分散の 52〜54% を説明、コスト前 0.23%/日。Valeyre-Aboura: STR の粗シャープ 2.2〜4.3 が Chronos(1.2〜3.2)以上。JPX 5 位: 2 日平均回帰が最重要 |
| B2 線形回帰 | 標準化した生 OHLCV か特徴量の Ridge | JPX 1 位が `LinearRegression`。Qlib で Linear の Rank IC 0.0472 は LightGBM 0.0469 と同等。GKX で 3 変数 OLS は R² 0.16%(NN3 の 0.40% の 4 割) |
| B3 決定木 1 本 | OHLC のみ | JPX 3 位(0.352) |
| B4 移動平均乖離 | `ma_gap_60` 単独で順位付け | JPX 2 位の最重要特徴量。向き(順張りか逆張りか)は README から読めず、要実測 |
| B5 前日日中リターン | `(C−O)/O` で順位付け | JPX 9 位(0.281)。向きは未確認 |
| B6 配当落ちルール | 配当落ち銘柄を最下位へ | JPX 4 位(0.347)。ただし終値ベースのラベルに限った機械的効果 |

モデルの寄与は「B1〜B2 に対する上積み」で測る。上積みが無ければ ML は不要という結論もあり得る。Krauss でも木の本数を倍にして 0.01 ポイントしか変わらず、モデルの複雑さより特徴量と評価設計が支配的である。

## リーク・非定常性の典型的失敗(必ず答えること 3)

**リーク**
1. **配当落ち**: 終値ベースのリターンは権利落ち日に機械的に下がる。JPX では配当落ち銘柄を最下位に置くだけで得点が上がった。対策は寄り→引けラベルにするか、配当調整済みリターンを使う。
2. **株式分割の調整係数**: 累積調整係数は過去時点で知り得ない情報を含む(J-Quants チュートリアル)。予測日より後に決まった分割で過去価格を直さない。
3. **同日集計のシフト忘れ**: 当日を含む集計値を当日の特徴量に使う。Wy66wy は 1 日シフト漏れで R² が 0.5 超になる例を示す。
4. **シャッフル KFold**: 時間順を壊すと隣接日の相関で検証が甘くなる。fan2goa1 ではパージ付きの方が LB で良かった(5.3341 対 5.3389)。
5. **全期間統計での規格化**: 銘柄ごとの中央値や標準化の平均・分散を全期間で計算すると未来が混ざる。学習期間だけで当てはめて固定する(cweill)。
6. **学習時と推論時の特徴量不一致**: JPX 5 位のコードは両者の定義が異なる。Wy66wy は両者の相関 0.999 以上を提出前の検査条件にしている。
7. **評価期間でのパラメータ選択**: Valeyre-Aboura は「ゼロショットなので過学習リスクなし」と主張しつつ、EMA 係数を評価期間内で比較している。JPX 3 位は公開 LB で特徴量を選択。
8. **公開 LB の再現**: JPX は公開データで Public の正解をほぼ再現できた(note 記事)。Public スコアは無意味。
9. **生存者バイアス**: 現在の上場銘柄だけで過去を再構成すると上振れする。
10. **銘柄境界をまたぐローリング計算**: JPX 2 位の `add_features` は groupby なし。必ず銘柄ごとに計算する。
11. **銘柄単位の学習・検証分割**: 同じ日の銘柄同士は強く相関するため、銘柄で分けても時間リークは防げない(JPX 2 位の分割)。

**非定常性**
1. **経年減衰**: Krauss のコスト後シャープは 6.69(1992〜2001)→ 0.51 → 4.46(金融危機)→ −0.88(2010〜2015)。Rahimikia でも全モデルが時間とともに低下。
2. **局面依存**: 高ボラ・危機局面でリバーサル系が極端に効く(Krauss: 2008 年 10 月だけで月間 100% 超)。逆に JPX 5 位は最終月の高ボラで成績が落ちたと記載しており、方向は一定でない。
3. **特徴量の寿命**: 効く特徴量は時間とともに弱くなる。特定の特徴量に依存せず多数を薄く入れる(nishimoto)。
4. **短い評価期間の運**: JPX は短い評価期間(約 3 か月、記憶ベース)で、CV 0.25 が Private 0.36 になり、線形回帰が 1 位。日次 RankIC の平均を 0.03、標準偏差を 0.15 と仮定すると(Qlib の LightGBM は IC 0.045・ICIR 0.37 なので標準偏差は約 0.12)、t 値 2 に必要な日数は約 100 日、t 値 3 なら約 225 日(日次独立を仮定した単純計算)。数週間の採点で優劣を決めない。
5. **CV と本番の不一致**: scaomath は CV で良い変更が LB で悪化する例を複数報告。
6. **対策として効いているもの**: 定期再学習・オンライン更新(Jane Street、Optiver)、拡張窓、エンバーゴ、複数シード平均、クロスセクション順位変換。

## 因果ルール候補

本観点は ML の証拠が主題なので、ここに書くのは「モデルが一貫して拾っている規則性」を人間が読める形にしたもの。効果量はすべてコスト前で、対象市場は主に米国である点に注意。

### R1. 短期リバーサル(5 日)
- IF: ある銘柄の直近 5 営業日累積リターンが当日ユニバースの下位 10% → THEN: 翌営業日の対市場相対リターンはプラス寄り。上位 10% はマイナス寄り。大きさの目安は極端な 10 銘柄ずつで合計 0.2%/日前後(コスト前、1992〜2015 年の米国平均)。時間軸は 1 日。
- なぜ: 流動性供給への対価と過剰反応の修正。高ボラ・高ベータ銘柄で顕著。
- 根拠: Fischer-Krauss(https://www.econstor.eu/handle/10419/157808、S&P 500、1992〜2015、k=10 で 0.23%/日、LSTM の分散の 52〜54% を説明)。Krauss-Do-Huck(直近 4〜5 日リターンが重要度最上位)。Valeyre-Aboura(https://arxiv.org/abs/2412.09394、残差リターン、2002〜2016、粗シャープ 2.2〜4.3)。GKX(mom1m が最上位群、月次)。
- 効かなくなる条件: 2010 年以降の米国ではコスト後マイナス。決算・材料による正当な再評価。低ボラの大型株。
- データと入手時刻: 前営業日までの調整済み終値(当日寄り前に確定)。
- 確度: A(存在は複数の査読研究で再現)。ただしコスト後の収益性は否定的で、日本株・寄り→引けでの大きさは未検証。

### R2. 超短期リバーサル(2 日、日本株)
- IF: 2 日リターン `P(t)/P(t−2)` が高い → THEN: その後 2 日間の市場平均控除リターンは低い(逆も同様)。大きさは未公表。時間軸は 1〜2 日。
- なぜ: R1 と同じ。作者は「行動バイアスの方が財務指標より予測的」と述べる。
- 根拠: JPX 5 位(https://github.com/J-Quants/JPXTokyoStockExchangePrediction の `winner-models/5th`、日本株約 2,000 銘柄、2017〜2022 年頃、拡張窓の月次スコア約 0.2)。
- 効かなくなる条件: 最終月の高ボラ局面で悪化と本人が記載。
- データと入手時刻: 前営業日までの終値。
- 確度: B(単独のコンペ解法。効果量は非公表)。

### R3. 60 日移動平均乖離
- IF: `Close / SMA60` が極端 → THEN: 翌日以降の相対リターンに影響。**方向は未確認**(平均回帰を想定するが実測が必要)。
- なぜ: 中期の行き過ぎの修正、またはトレンド継続。
- 根拠: JPX 2 位(`MA_gap_3month` が最重要特徴量。検証相関 0.0149、CV スコア 0.25)。J-Quants チュートリアルも同じ特徴量を採用。
- 効かなくなる条件: 不明。
- データと入手時刻: 前営業日までの終値 60 本。
- 確度: C(重要度のみで方向・効果量なし)。

### R4. 値動きの大きさはボラティリティに比例する
- IF: 過去 20〜240 日のボラティリティとベータが高い → THEN: 翌日の絶対リターンが大きく、上位にも下位にも入りやすい。方向は決まらない。
- なぜ: ボラティリティの持続性。
- 根拠: Fischer-Krauss(LSTM の上位・下位銘柄はともに高ボラ・高ベータ)。JPX 2 位(Target の振れ幅が小さい銘柄を中央値に寄せる処理)。GKX(retvol、idiovol、beta が重要変数)。Kronos 論文のボラ予測 R² 0.249(方向より格段に当てやすい)。
- 効かなくなる条件: 材料出尽くし後のボラ急低下。
- データと入手時刻: 前営業日までの日次リターン。
- 確度: A(ボラの持続性自体は広く再現)。方向予測には使えない。

### R5. 小型株ほど予測しやすい(日次)
- IF: 時価総額下位 25% → THEN: 同じモデルでも的中率が約 1.5 ポイント高い(52.29% 対 50.76%)、R² は 0.51% 対 −0.37%。
- なぜ: 情報の織り込みが遅く、裁定が難しい。
- 根拠: Rahimikia-Ni-Wang(https://arxiv.org/abs/2511.18578、米国、2001〜2023、CatBoost)。Avramov ほか 2023(裁定困難銘柄に利益が集中)。
- 効かなくなる条件: 月次では逆の報告もある(GKX は大型株で R² 0.52〜0.70%)。小型株はコストが高い(21.3 bps 対 11.2 bps)。
- データと入手時刻: 時価総額(前営業日)。
- 確度: B(日次は単独の大規模研究。月次とは整合しない)。

### R6. 配当落ち日の機械的下落
- IF: 当日が権利落ち日 → THEN: 前日終値→当日終値のリターンは配当利回り分だけ機械的に低く出る(大きさは配当利回りが目安。出典に数値なし)。寄り→引けリターンには原則影響しない。
- なぜ: 配当の権利が価格から外れる。
- 根拠: JPX 4 位(`ExpectedDividend > 0` を最下位に置くルールで 0.347)と、同コンペの議論「Shorting dividend days = easy score boost」(題名のみ確認)。
- 効かなくなる条件: 配当調整済みリターンを使う場合は消える。
- データと入手時刻: 配当予定(事前に公表)。
- 確度: B(機械的効果。予測というよりラベル設計の罠)。

### R7. 市場が荒れるとクロスセクションの歪みが大きくなる
- IF: 市場全体のボラが急騰(危機局面) → THEN: リバーサル系シグナルの効果量が平常時の数倍になる。時間軸は数週間〜数か月。
- なぜ: 投資家の注意が個別銘柄から市場全体へ移り相対価格が歪む。同時に裁定の制約が強まる。
- 根拠: Krauss-Do-Huck(2008-09〜2009-12 のコスト後シャープ 4.46、2008 年 10 月は月間 100% 超、2011 年 10 月は +35%)。
- 効かなくなる条件: 空売り規制、流動性枯渇。JPX 5 位は高ボラ月に悪化しており、日本株で同じ向きになる保証は無い。
- データと入手時刻: 指数の実現ボラや VI(前営業日)。
- 確度: B。

### R8. 公表された価格系シグナルは年々弱くなる(メタルール)
- IF: あるルールの根拠が 10 年以上前のデータ → THEN: 現在の効果量は半分以下と仮定し、直近 2〜3 年で再検証するまで確度を 1 段下げる。
- なぜ: 手法の普及と計算資源の低価格化で裁定される。
- 根拠: Krauss-Do-Huck(シャープ 6.69 → −0.88)、Fischer-Krauss(1990 年代が突出、2010 年以降は横ばい〜損失)、Rahimikia(全モデルが経年低下)、nishimoto(効く特徴量は時間とともに弱くなる)。
- 確度: A。

### R9. 市場全体の短期リターン平均が個別の反転を条件付ける
- IF: 当日ユニバース全体の 2 日リターン平均が極端 → THEN: 個別のリバーサルの効き方が変わる(方向と大きさは未公表)。
- 根拠: JPX 5 位(`ave_mrsignal`、`ave_momsignal` が重要度上位)。Optiver 1 位と Ubiquant 1 位が市場平均系特徴量を使用(nishimoto スライドの記述)。
- 確度: C(特徴量として有効という報告のみ)。

### R10. 前日の日中リターンが翌日以降の相対リターンを予測する
- IF: 前日の `(C−O)/O` が極端 → THEN: 翌日以降の相対リターンに差が出る。**方向は未確認**。
- 根拠: JPX 9 位(日中リターンだけで順位付けして 0.281)。
- 確度: C。

### R11. 引け前オークションの不均衡は直後の価格を動かす
- IF: 引け前 10 分間の買い不均衡が大きい → THEN: 60 秒先の対指数リターンはプラス寄り。大きさは定数予測からの MAE 改善で約 2.6%(9 位ノートのホールドアウト)。
- 根拠: Optiver - Trading at the Close(Nasdaq、2023)。9 位ノートで MAE 6.029 → 5.8705。
- 効かなくなる条件: 東証の引けは制度が異なる。板データが必要。
- 確度: B(米国では多数の解法で再現。日本株は未検証で、MVP のデータでは判定不能)。

## 落とし穴・反証・注意

- **コスト前の数字に意味は薄い**: Krauss の 0.45%/日、Rahimikia のシャープ 6〜7、Valeyre の 3〜4 はすべてコスト前。20 bps でマイナスに反転する。本プロジェクトは発注しないが、ルール文書に効果量を書くときは「コスト前」と必ず添える。
- **Kronos の数字の読み方**: 「RankIC 93% 向上」は相対値。日本取引所の表では、価格系列予測の IC は Kronos-L 0.036 に対し NSTransformer 0.028、Time-MoE 0.028 で差は小さい。リターン予測では RankIC でゼロショット Moirai に負けている。比較対象に単純なリバーサルやモメンタムのルールは無い。予測期間や頻度の定義は表ごとに異なり、他の IC と直接比較できない。スター 4 万超は有効性の証拠ではない。
- **Noguer i Alonso-Franklin 2026 の「TSFM が 10 課題中 8 勝」**: 米国 5 銘柄だけの比較で、相手は学習型ニューラルネット。ランダムウォークに対する有意な改善は 2 例のみ。著者自身が「アルファ生成の万能エンジンではない」と結論。
- **GKX の R² 0.40%**: 月次・米国・94 特性の話。日次・価格のみの MVP には当てはまらない。等加重のシャープ 2.45 はマイクロキャップと高回転率に依存する。
- **Qlib の IC 0.045**: 中国 A 株 2017〜2020 年。README の数値はシード違いの平均で、期間は 1 つだけ。
- **JPX 上位解法**: 評価期間が短く運の寄与が大きい。「線形回帰が 1 位」は「線形回帰が最良」を意味しない。上位解法コードには不具合の疑いがある箇所(groupby なし、学習と推論の不一致)があり、そのまま写すと再現しない恐れがある。
- **オンライン学習の効果**: Jane Street の +45% は第三者による再構成で、評価窓は開発中に参照済み(README が明記)。Optiver 1 位の数値は二次情報。
- **ライセンス**: J-Quants-Tutorial は CC BY-NC-ND(改変物の再配布不可)。TimesFM 3.0 と TabPFN 2.5 以降の重みは非商用。Moirai は研究目的のみ。mlfinlab は有償。FinText の重みはライセンス未記載。9 位 Optiver、cweill のリポジトリはライセンス表記なし。式や数値(事実)は写せるが、コード本文の複製・再配布は避ける。
- **環境**: Qlib の対応 Python は 3.8〜3.12 と記載され、3.13 は対象外の可能性が高い。インストールせず式を再実装するのが安全。Kronos と TabPFN は Python 3.10 以上が要件で、3.13 での動作は未確認。
- **確認できなかったもの**: Optiver 1 位、Optiver Realized Volatility 1 位(題名「Nearest Neighbors」のみ確認)、Ubiquant、G-Research、Two Sigma、Jane Street 2024 1 位の本文。これらは nishimoto スライド経由の概要のみ。
- **寄り→引けを目的変数にした日本株 ML の先行研究は今回見つけられていない**。MVP の目的変数は先行例(翌日終値→翌々日終値、翌日クロスセクション中央値超え)からの類推である。

## このプロジェクトへの提案(MVP で採用するもの、後回しにするもの)

**MVP で採用**
1. ベースライン B0〜B5 を最初に実装し、毎日の採点表に常設する。ML はその上積みで評価する。
2. LightGBM 1 本(特徴量約 45 個、順位変換、月次再学習、エンバーゴ 20 日)。設定は JPX 5 位、Qlib、提案値の 3 通りを並走。
3. ラベルは寄り→引けの市場平均控除順位を主、中央値超え 2 値を副。
4. 評価は日次 RankIC、ICIR、的中率、十分位スプレッド(0/10/20 bps)。t 値 2 を超えるまで(目安 100 営業日以上)優劣を断定しない。
5. リーク検査を自動化: 特徴量を 1 日ずらして成績が急落するか、学習時と推論時の特徴量が一致するか(相関 0.999 以上)、RankIC 0.1 超で警告。
6. docs のルール予測(b)には R1(5 日リバーサル)、R4(ボラ比例)、R6(配当落ち)、R8(減衰メタルール)を初期ルールとして採用。R2、R3、R10 は方向を自前データで実測してから採否を決める。
7. ルール予測と ML 予測を同じ RankIC で採点し、ML が拾っている規則性をルール側に還元する(変数重要度と部分依存を月次で docs に転記)。

**後回し**
1. Kronos-small と FinText Chronos-Small を比較枠として 1 本ずつ(GPU なしでの推論時間を先に計測)。
2. CatBoost と XGBoost の追加、シード・モデル平均。
3. `CombinatorialPurgedCV` による経路分布、PBO、Deflated Sharpe。
4. トリプルバリアとメタラベル(固定期間ラベルに対する優位の証拠を先に探す)。
5. 特徴量中和(Numerai)、業種・ベータ中立化。
6. 寄り付き後の版 B(当日ギャップ利用)、引け前板情報(Optiver 型)。
7. LSTM / GRU / Transformer。Qlib と JPX の結果から優先度は低い。
8. TabPFN(CPU 5,000 行制限のため、直近数日だけで学習する小規模実験なら可能)。

## 未追跡の手がかり

- Optiver - Trading at the Close 1 位の原文(Kaggle discussion 487446)と公開コード。知乎の解説 2 本(https://zhuanlan.zhihu.com/p/689864294、https://zhuanlan.zhihu.com/p/699910063)は 403 で開けず。
- Optiver Realized Volatility 1 位「Nearest Neighbors」(discussion 274970)の本文。
- Ubiquant Market Prediction、G-Research Crypto Forecasting、Two Sigma 2 コンペの上位解法(nishimoto スライドの参考資料欄に日本語解説へのリンクがある)。
- Jane Street 2024 の 1 位解法と、Kaggle 公式の Patrick Yam 解説動画(https://www.youtube.com/watch?v=lfzzPZZyzjE)。
- 寄り→引け、夜間と日中の分解を目的変数にした研究(日中モメンタム、夜間リターンと日中リバーサル、日本株での検証)。今回は検索上限で未着手。
- Kronos の第三者検証: Issue #78(ファインチューニング結果、コメント 71)、#114(検証・テスト結果)、#299、#133 の本文。日本株でのファインチューニング事例。
- Chronos-2(共変量対応)と TimesFM 3.0 の金融リターンでの評価。
- Leippold, Wang, Zhou 2022(中国株の ML)、Blitz ほか 2023(予測期間を延ばすと 25 bps コスト後も残るという報告)。Rahimikia と検索結果で言及されていたが未読。
- Kelly, Malamud, Zhou「The Virtue of Complexity」とその批判、McLean-Pontiff の公表後減衰。
- Kelly, Xiu「Financial Machine Learning」(NBER w31502、要旨のみ確認)の本文。
- Abe, Nakayama 2018(arXiv:1801.01777、日本株・月次、PAKDD 2018)と Imajo ほか 2020(arXiv:2012.07245、日米株、残差ファクター)の本文と数値。
- J-Quants-Tutorial の後半(モデル学習・SHAP・スコア、`winners` フォルダの入賞者解法)。
- JPX 2021 年の SIGNATE コンペ(ファンダメンタルズ分析・ニュース分析チャレンジ)入賞解法。
- LOBCAST と LOBFrame の公開コードと数値。
- Rahimikia 論文の米国外(日本を含むか)の結果。評価対象 7 市場に日本は入っていなかったが、事前学習 94 市場には JPN が含まれる。
- 日本語圏の個人による日本株 ML 検証記事(UKI 氏など)。URL を確認できていない。

## 参照 URL 一覧(✅ / ❓ つき)

**日本株・コンペ**
- ✅ https://github.com/J-Quants/JPXTokyoStockExchangePrediction(README、`winner-models/1st`〜`9th` の README、2 位ノート、5 位スクリプト)
- ❓ `winner-models/10th/README.md`(404)
- ✅ https://japanexchangegroup.github.io/J-Quants-Tutorial/(前半 20 万字)
- ✅ https://github.com/JapanExchangeGroup/J-Quants-Tutorial
- ✅ https://www.docswell.com/s/8980249862/KR2YD1-KantoKaggler3rd_MarketCompetition
- ✅ https://note.com/sirteabear/n/nc4466135a619
- ❓ https://www.inf.shizuoka.ac.jp/english/news/detail.html?CN=154751(JPX 1 位が静岡大の学生という報道。検索結果の要約のみで本文は開いていない)
- ✅ https://github.com/ChunhanLi/9th-kaggle-optiver-trading-close(README と `xgboost-training.ipynb`)
- ✅ https://fan2goa1.github.io/mkdocs-material/blog/2023/12/24/kaggle-optiver---trading-at-the-close/
- ✅ https://github.com/osyuksel/kaggle-optiver-2024(15 位、MIT。README に詳細なし)
- ✅ https://github.com/nimashahbazi/optiver-trading-close(LSTM / ConvNet、Public 5.3508 / 5.3439)
- ✅ https://github.com/GrigoriiTarasov/Optiver-Trading-at-the-Close-retrain-monitoring
- ❓ https://www.kaggle.com/competitions/optiver-trading-at-the-close/discussion/487446(題名のみ)
- ❓ https://www.kaggle.com/competitions/optiver-realized-volatility-prediction/discussion/274970(題名のみ)
- ❓ https://zhuanlan.zhihu.com/p/689864294(403)
- ❓ https://blog.csdn.net/qq_51175703/article/details/137109118(521)
- ❓ https://medium.com/@joehbridges/gauging-the-market-optivers-trading-at-the-close-kaggle-competition-27b73f7789c0(403)
- ✅ https://github.com/cweill/jane-street-causal-forecasting
- ✅ https://github.com/Wy66wy/Jane-Street-Real-Time-Market-Data-Forecasting
- ✅ https://github.com/scaomath/kaggle-jane-street

**論文**
- ✅ https://www.iwf.rw.fau.de/files/2016/03/03-2016.pdf(Krauss, Do, Huck。PDF 本文)
- ✅ https://www.econstor.eu/handle/10419/157808 と https://www.econstor.eu/bitstream/10419/157808/1/886576210.pdf(Fischer, Krauss。PDF 本文)
- ✅ https://dachxiu.chicagobooth.edu/download/ML.pdf(Gu, Kelly, Xiu。PDF 本文)
- ✅ https://arxiv.org/abs/2511.18578(Rahimikia, Ni, Wang。HTML と PDF 本文)
- ✅ https://arxiv.org/abs/2412.09394(Valeyre, Aboura。HTML v2)
- ✅ https://arxiv.org/abs/2508.02739(Kronos。HTML v1、付録表まで)
- ✅ https://arxiv.org/abs/2606.27100(Noguer i Alonso, Franklin。要旨)
- ✅ https://cris.huji.ac.il/en/publications/machine-learning-vs-economic-restrictions-evidence-from-stock-ret/(Avramov, Cheng, Metzker。要旨)
- ❓ https://papers.ssrn.com/abstract=3450322(403)
- ✅ https://arxiv.org/abs/1808.03668(DeepLOB。要旨)
- ✅ https://arxiv.org/abs/2308.01915(LOBCAST。要旨)
- ✅ https://arxiv.org/abs/2403.09267(Deep Limit Order Book Forecasting。要旨)
- ✅ https://arxiv.org/abs/2207.08815(Grinsztajn ほか。要旨)
- ✅ https://arxiv.org/abs/1801.01777(Abe, Nakayama。要旨)
- ✅ https://arxiv.org/abs/2012.07245(Imajo ほか。要旨)
- ✅ https://www.nber.org/papers/w31502(Kelly, Xiu。要旨)
- ❓ https://www.esann.org/sites/default/files/proceedings/2024/ES2024-159.pdf(名前解決失敗)

**リポジトリ・モデル・ライブラリ**
- ✅ https://github.com/microsoft/qlib、`examples/benchmarks/README.md`、`examples/benchmarks/LightGBM/workflow_config_lightgbm_Alpha158.yaml`、`qlib/contrib/data/loader.py`
- ✅ https://github.com/shiyu-coder/Kronos(API、README、Issue 一覧の題名)
- ✅ https://huggingface.co/FinText
- ✅ https://github.com/DeepIntoStreams/TSFM_Finance
- ✅ https://github.com/amazon-science/chronos-forecasting
- ✅ https://github.com/google-research/timesfm
- ✅ https://github.com/SalesforceAIResearch/uni2ts
- ✅ https://github.com/time-series-foundation-models/lag-llama
- ✅ https://github.com/Nixtla/nixtla
- ✅ https://github.com/PriorLabs/TabPFN
- ✅ https://skfolio.org/generated/skfolio.model_selection.CombinatorialPurgedCV.html
- ✅ https://github.com/RiskLabAI/RiskLabAI.py
- ✅ https://github.com/hudson-and-thames/mlfinlab
- ✅ https://github.com/stefan-jansen/alphalens-reloaded
- ✅ https://github.com/stefan-jansen/machine-learning-for-trading
- ✅ https://github.com/numerai/example-scripts
