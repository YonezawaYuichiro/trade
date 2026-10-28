# GitHub: AIクオンツ基盤・ML パイプライン・特徴量ライブラリ

> 調査日: 2026-10-13 / 観点: gh-quant-platforms / 状態: 一次調査(未検証)

**調査方法の注記(正直な申告)**
- WebSearch はチーム共有の上限に達し、実行できたのは 2 回のみ(以降は拒否された)。指定の「検索 15 回以上」は満たせていない。代わりに GitHub 検索 API / GitHub サイト内検索(7 回)と、既知 URL の直接取得(GitHub 本体・raw ファイル・PyPI JSON・arXiv・Crossref・Semantic Scholar など約 110 ページ)で補った。
- GitHub API は途中からレート制限(403)になったため、一部リポジトリはスター数・最終 push 日を HTML ページから取得した(HTML では push 日が取れないものがあり、その場合は「日付未確認」と書いた)。
- ✅ = このセッションで実際に開いて中身を確認。❓ = 開けなかった/記憶ベース。数値は断りがない限りリポジトリ・論文の**自己申告**であり、第三者検証ではない。
- これは調査メモであり投資助言ではない。

---

## 結論(5〜10 行)

1. **MVP の土台として最有力なのは「Qlib 本体」ではなく「Qlib の定義を写した自前の薄いパイプライン」**。構成は J-Quants API V2 → Parquet → Alpha158 相当の特徴量(pandas/polars で再実装) → LightGBM → 日次 IC / Rank IC 採点。理由: (a) Qlib の PyPI 最新 0.9.7 は cp38〜cp312 の wheel のみで **Python 3.13 用が無い**、(b) Qlib に日本リージョンも日本株コレクタも無い、(c) 発注しない「予測→記録→採点」には Qlib の執行・バックテスト層が過剰、(d) Alpha158 の全 158 式・ラベル式・正規化・評価関数は MIT ライセンスで短く、そのまま写せる。
2. **Qlib 本体は「参照実装・モデル動物園」として Python 3.12 の別 venv で併用**するのが現実的(cp312 の win_amd64 wheel は存在)。自前実装の特徴量が Qlib と一致するかの突き合わせに使う。
3. **Qlib × 日本株の既存事例は 1 件だけ見つかった**: `iyoda/jquants-qlib`(MIT、スター 0、2026-10-12 push、macOS/Linux 専用、Python 3.10〜3.12)。microsoft/qlib の Issue を "japan" で検索しても 0 件。つまり先行事例はほぼ無く、手順は「CSV を作って `dump_bin.py` に通す」一択。
4. **写すべき特徴量は 4 系統**: Qlib Alpha158(全式確認済)、Alpha360(生 OHLCV 60 日分)、WorldQuant 101 Formulaic Alphas(論文 PDF から式を確認)、JPX Kaggle コンペ上位解法(2 位は 14 特徴、5 位は 8 特徴。日本株 2,000 銘柄で実績のある最小セット)。
5. **日本株で唯一、直接の実証がある知見**: JPX コンペ 5 位の解法では「2 日リターンの短期リバーサル」が最重要シグナル。ウォークフォワードの月次スコア平均は約 0.2(自己申告)。一方 1 位は線形回帰、3 位は OHLC だけの決定木、4 位はルールベースで本人が「運」と明言しており、**3 か月の順位は運の比重が大きい**。
6. **期待値の較正**: Qlib 公式ベンチマーク(中国 CSI300、テスト 2017〜2020)で LightGBM+Alpha158 の日次 IC は 0.0448、Rank IC 0.0469。最良でも IC 0.05 前後。日次予測で IC が 0.1 を超えたらリークを疑う。
7. **日次運用の雛形**は `touhoufan2024/qlibAssistant`(MIT、毎晩 GitHub Actions で学習→翌日予測→過去予測の答え合わせを Pages に公開)と Qlib `examples/online_srv/` が写せる。日本株では `id774/finance`(J-Quants V2 + TA-Lib の日次バッチ)が先行例だが GPL/LGPL。
8. **Windows + Python 3.13 でそのまま動くもの**: LightGBM 4.7.0、TA-Lib 0.8.2(Windows wheel 同梱)、pandas-ta-classic、ml4t-engineer / ml4t-diagnostic、alphalens-reloaded、quantstats、jquants-api-client。**動かない/要回避**: pyqlib(3.12 まで)、RD-Agent(Linux + Docker 専用)、ML4T 第 3 版リポジトリ(Windows は WSL2 のみ)、jquants-qlib(Windows 非対応)。
9. **元祖 pandas-ta(twopirllc/pandas-ta)は 404 で消滅**、mlfinlab は「all rights reserved」の有償ライブラリ化。古い記事の `pip install pandas-ta` / `mlfinlab` 前提のコードは写せない。

---

## 丸パクリ候補(優先度順の表)

| # | 名前 | URL | 種別 | ライセンス | 鮮度 | 何をどう写すか | 確認 |
|---|---|---|---|---|---|---|---|
| 1 | microsoft/qlib | https://github.com/microsoft/qlib | repo | MIT | 49,316★、push 2026-10-08、GitHub v0.9.8(2026-10-08、ソースのみ)、PyPI 0.9.7(2025-08-15) | `qlib/contrib/data/loader.py` の `Alpha158DL.get_feature_config`(158 式)と `Alpha360DL`、`handler.py` のラベル式 `Ref($close,-2)/Ref($close,-1)-1` と既定プロセッサ、`qlib/data/dataset/processor.py` の正規化、`qlib/contrib/eva/alpha.py` の `calc_ic` / `calc_long_short_return` / `calc_long_short_prec`、`examples/benchmarks/LightGBM/workflow_config_lightgbm_Alpha158.yaml` のハイパーパラメータ、`examples/online_srv/update_online_pred.py` の日次更新手順 | ✅ |
| 2 | J-Quants/JPXTokyoStockExchangePrediction | https://github.com/J-Quants/JPXTokyoStockExchangePrediction | repo(コンペ上位 10 解法) | Apache-2.0 | コンペは 2022-04-04 開始。日付未確認 | `winner-models/2nd`(LightGBM + 14 特徴)、`winner-models/5th`(LightGBM + 8 特徴、超過リターン目的変数、上下 250 銘柄だけで学習、月次拡張ウォークフォワード)をそのまま日本株 MVP の初期特徴・検証手順にする | ✅ |
| 3 | J-Quants/jquants-api-client-python | https://github.com/J-Quants/jquants-api-client-python | repo / API クライアント | Apache-2.0 | 195★、push 2026-09-30、V2 専用、Python 3.10+(3.13 でテスト) | `jquantsapi.ClientV2(api_key=...)` → `get_eq_bars_daily_range(start_dt, end_dt)`、`get_eq_master`、`get_mkt_calendar`、`get_fin_summary`。API キーは環境変数 `JQUANTS_API_KEY` | ✅ |
| 4 | iyoda/jquants-qlib | https://github.com/iyoda/jquants-qlib | repo(J-Quants→Qlib ETL) | MIT | 0★、push 2026-10-12、v0.1.x Beta、コミット 11 | 設計を写す: 生データを無調整 Parquet で保存 → 変換時に `$factor` を付けて Qlib 化、`run-daily`(最新営業日まで欠損補完)、`audit`(直近営業日の欠落検査)、`validate`、原子的 publish。CLI は `jqqlib run-all --config config.yaml --start ... --end ...` | ✅ |
| 5 | ml4t-engineer | https://github.com/ml4t/engineer / https://pypi.org/project/ml4t-engineer/ | repo / PyPI | MIT | 0.1.6(2026-09-25)、Python 3.12〜3.14、Windows 対応と明記、23★ | `compute_features(df, ["rsi","macd","atr"])`(polars)、`triple_barrier_labels(features, config=LabelingConfig.triple_barrier(upper_barrier=0.02, lower_barrier=0.01, max_holding_period=20))`、`create_dataset_builder(..., scaler="robust").train_test_split(train_size=0.8)`(学習区間だけでスケーラを fit) | ✅ |
| 6 | ml4t-diagnostic | https://github.com/ml4t/diagnostic / https://pypi.org/project/ml4t-diagnostic/ | repo / PyPI | MIT | 0.1.8(2026-09-24)、Python 3.12〜3.14、Windows 対応、34★ | `analyze_signal(factor=..., prices=..., periods=(1,5))` → `result.ic["1D"]`、`result.ic_t_stat["1D"]`(HAC 補正)、`result.spread["1D"]`。`WalkForwardCV` / `CombinatorialCV`、Deflated Sharpe Ratio、PBO、White's Reality Check | ✅ |
| 7 | numerai/example-scripts + numerai-tools | https://github.com/numerai/example-scripts / https://github.com/numerai/numerai-tools | repo | MIT | 1,189★、push 2026-10-12、データ v5.3 | `numerai_tools/scoring.py` の `numerai_corr`(順位→正規分布化→1.5 乗→Pearson)、`neutralize`(最小二乗残差)、`correlation_contribution`。`example_model.ipynb` の LightGBM 設定(n_estimators=2000, learning_rate=0.01, max_depth=5, num_leaves=31, colsample_bytree=0.1、era を 4 つおきに間引き) | ✅ |
| 8 | touhoufan2024/qlibAssistant | https://github.com/touhoufan2024/qlibAssistant | repo(日次予測の運用例) | MIT | 467★、push 2026-05-30、コミット 408 | 運用フロー丸ごと: 毎晩 20:00 に定時実行 → データ同期 → 4 アルゴリズム × 学習窓 1〜5 年のモデル群を学習 → IC / ICIR / Rank IC / Rank ICIR でモデル選別 → スコア単純平均 → 翌営業日 Top 銘柄と `pos_ratio`(上昇予測モデルの割合)を出力 → 過去予測の振り返りページ | ✅ |
| 9 | Kakushadze "101 Formulaic Alphas" | https://arxiv.org/abs/1601.00991 | paper | arXiv(式は事実として利用可) | 2016(データ 2010-01-04〜2013-12-31)。古い | 付録 A の 101 式と演算子定義(rank=クロスセクション順位、delay、delta、ts_rank、decay_linear など)。delay-0 は #42 #48 #53 #54 の 4 本のみ、他は delay-1 | ✅(PDF 本文を抽出して確認) |
| 10 | Menooker/KunQuant | https://github.com/Menooker/KunQuant | repo | Apache-2.0 | 325★、push 2026-10-09 | Alpha101 と Alpha158 の実装(Alpha158 は Qlib の出力と倍精度で照合テスト済と記載)。Alpha101 の Python 実装を写すなら無ライセンスの yli188 版ではなくこちらを参照。Windows は MSVC 必須 | ✅ |
| 11 | TA-Lib (ta-lib-python) | https://github.com/TA-Lib/ta-lib-python | repo / PyPI | BSD-2-Clause | 12,289★、push 2026-10-12、0.8.2、Python 3.9〜3.14 | `pip install TA-Lib` だけで Windows でも入る(wheel に C ライブラリ同梱)。`talib.RSI`、`talib.ATR`、`talib.MACD`、ローソク足パターン群 | ✅ |
| 12 | pandas-ta-classic | https://github.com/xgboosted/pandas-ta-classic | repo / PyPI | MIT | 453★、push 2026-10-10、0.8.32(2026-09-14)、Python 3.10+(分類子は 3.14 まで) | 消滅した元祖 pandas-ta の後継。224 指標 + ローソク足 62 種。TA-Lib 不要。`pip install pandas-ta-classic` | ✅ |
| 13 | alphalens-reloaded | https://github.com/stefan-jansen/alphalens-reloaded | repo / PyPI | Apache-2.0 | 669★、push 2026-10-13、0.4.6(2025-06-02)、Python 3.10〜3.13、pandas<3.0 | `alphalens.utils.get_clean_factor_and_forward_returns(factor, prices, quantiles=5)` → `alphalens.tears.create_full_tear_sheet(...)` で分位別リターン・IC の標準レポート | ✅ |
| 14 | quantstats | https://github.com/ranaroussi/quantstats | repo / PyPI | Apache-2.0 | 7,700★、push 2026-09-27、0.0.86、Python 3.10+ | 仮想損益系列の HTML レポート(Sharpe、最大 DD など)。予測記録を「上位 N 銘柄等金額」の仮想リターンに直して流す | ✅ |
| 15 | id774/finance | https://github.com/id774/finance | repo(日本株の個人用日次バッチ) | GPL-3 / LGPL-3 のデュアル | 69★、push 2026-09-23、コミット 479、Python 3.11+ | **コードは写さず設計だけ**: cron 平日 18:10 → J-Quants V2 日足取得 → TA-Lib で 42 指標 → 銘柄ごとに分類+回帰 2 モデルを毎晩再学習 → CSV/PNG 出力 → メール。`doc/DATA_CONTRACT.md` の列定義方式 | ✅ |
| 16 | stefan-jansen/machine-learning-for-trading(第 3 版) | https://github.com/stefan-jansen/machine-learning-for-trading | repo(書籍コード) | コード MIT / 本文は著作権保護 | 21,319★、push 2026-10-13、書籍 © 2026 | 章構成そのものが設計書: `07`〜`11`(学習タスク定義・特徴量・ML パイプライン)、`case_studies/nasdaq100_microstructure`(15 分足)、`case_studies/us_equities_panel`。Windows は WSL2 のみ対応 | ✅ |
| 17 | microsoft/RD-Agent | https://github.com/microsoft/RD-Agent | repo(LLM による因子・モデル自動探索) | MIT | 14,911★、push 2026-10-11 | `rdagent fin_factor` / `fin_model` / `fin_quant` / `fin_factor_report --report-folder=<path>`。Linux + Docker 必須、Python 3.10/3.11。後回し(WSL2 が要る) | ✅ |
| 18 | shiyu-coder/Kronos | https://github.com/shiyu-coder/Kronos | repo(K 線の基盤モデル) | MIT | 40.6k★、arXiv 2508.02739、AAAI 2026 採択と記載 | `KronosPredictor(model, tokenizer, max_context=512).predict(df, x_timestamp, y_timestamp, pred_len, T=1.0, top_p=0.9, sample_count=1)`。入力は OHLC(V)。ゼロショットの「機械予測の比較対象」として | ✅ |
| 19 | TauricResearch/TradingAgents | https://github.com/TauricResearch/TradingAgents | repo(LLM マルチエージェント) | Apache-2.0 | 110.9k★、v0.6.0(2026-10)、Python 3.11+ | 役割分担(アナリスト 4 種 → 強気/弱気の討論 → トレーダー → リスク → PM)を docs ルール予測の手順書の型として写す。`7203.T` など東証ティッカー対応と明記 | ✅ |
| 20 | wilsonfreitas/awesome-quant ほか | https://github.com/wilsonfreitas/awesome-quant | まとめリスト | 未設定 | 30,046★、push 2026-10-13 | 索引として使う。日本関連は EDINET / TDnet / e-Stat の MCP 系のみで、J-Quants や日本株 ML 基盤の掲載は無し | ✅ |
| 21 | ajtgjmdjp/awesome-japan-finance-data | https://github.com/ajtgjmdjp/awesome-japan-finance-data | まとめリスト | CC0-1.0 | 21★、push 2026-08-23 | 日本の金融データ源の索引(J-Quants、EDINET、TDnet、e-Stat、日銀、Stooq、yfinance)。ML/クオンツ基盤の欄は空 | ✅ |
| 22 | vnpy(vnpy.alpha) | https://github.com/vnpy/vnpy | repo | MIT | 45.8k★、v4.0 系、Python 3.10+(3.13 推奨)、Windows 11 対応 | `vnpy.alpha` に Alpha158 + Lasso / LightGBM / MLP + Lab の一式。Qlib 以外で Windows + 3.13 を公式に謳う Alpha158 実装として参照 | ✅ |
| 23 | mlfinpy / RiskLabAI.py / finmlkit / purged-cross-validation | https://github.com/baobach/mlfinpy 、https://github.com/RiskLabAI/RiskLabAI.py 、https://finmlkit.readthedocs.io/ 、https://github.com/eslazarev/purged-cross-validation | repo(mlfinlab の OSS 代替) | MIT / BSD-3 / MIT / MIT | mlfinpy 88★ push 2026-10-11、RiskLabAI 6★(Python 3.12〜3.14)、finmlkit 0.1.11、purged-cv 55★ push 2026-10-01 | トリプルバリア、メタラベリング、パージ付き K 分割、CPCV、PBO、DSR。MVP では ml4t-diagnostic で足りるので予備 | ✅ |
| 24 | OpenSourceAP/CrossSection | https://github.com/OpenSourceAP/CrossSection | repo(アノマリー約 300 本の定義) | GPL-2.0 | 1.1k★、コミット 1,268 | `SignalDoc.csv` を因果ルール辞書の種にする(定義・出典の一覧)。コードは GPL なので式と出典だけ参照 | ✅ |
| 25 | bkelly-lab/jkp-data + jkpfactors.com | https://github.com/bkelly-lab/jkp-data | repo / データ | コード MIT、データ CC BY-NC 4.0 | 80★、旧 ReplicationCrisis は保守終了 | Jensen-Kelly-Pedersen(JF 2023、93 か国・13 テーマ)の因子定義 PDF。生成には WRDS 契約が必要。国別因子リターンは jkpfactors.com から取得可と記載(日本の有無は未確認) | ✅(日本収録は❓) |
| 26 | FinRL / FinRL-X | https://github.com/AI4Finance-Foundation/FinRL 、https://github.com/AI4Finance-Foundation/FinRL-Trading | repo(強化学習) | MIT / Apache-2.0 | 16,632★ push 2026-10-12 / 3.8k★ | 採用しない。状態変数の指標リスト(macd, boll_ub, boll_lb, rsi_30, dx_30, close_30_sma, close_60_sma)だけ参考。日本データ源なし | ✅ |
| 27 | vectorbt | https://github.com/polakowo/vectorbt | repo | Apache 2.0 + Commons Clause | 9,348★、1.1.2(2026-10-09)、Python 3.11〜3.14 | 後回し。`pandas>=3.0.3` 必須で alphalens / pyfolio(`pandas<3.0`)と同居不可 | ✅ |
| 28 | tsfresh | https://github.com/blue-yonder/tsfresh | repo | MIT | 9,473★、0.21.2(2026-05-31)、分類子は 3.12 まで | 後回し。大量の汎用時系列特徴。3.13 での動作は未確認 | ✅(3.13 動作は❓) |
| 29 | OpenBB | https://github.com/OpenBB-finance/OpenBB | repo | README は Apache-2.0 表記(GitHub API は NOASSERTION) | 74,170★、push 2026-10-12、Python 3.10〜3.14 | 採用しない(日本株プロバイダの記載なし、ML パイプラインなし)。MCP サーバ機能は将来の参考 | ✅ |
| 30 | alphagen | https://github.com/RL-MLDM/alphagen | repo(式アルファの自動生成) | 未記載 | 1.3k★、KDD 2023 | 後回し。Qlib 依存。因子自動探索の比較対象 | ✅ |
| 31 | polars_ta | https://github.com/wukan1986/polars_ta | repo | MIT | 265★ | WorldQuant 風演算子(`ts_mean`、`ts_std_dev` など)の polars 実装。自前で Alpha101 を polars 化するときの部品 | ✅ |
| 32 | GTJA Alpha191 実装 | https://github.com/popbo/alphas 、https://github.com/Daic115/alpha191 | repo | 両方ライセンス未記載 | 593★(2023-04 push)/ 17★ | 優先度低。`alphas191.py` があるが検証記載なし・無ライセンス。原典(国泰君安の 2017 年レポート)は未確認 | ✅(原典❓) |
| 33 | SIGNATE JPX ファンダ 1 位解法 / UKI000 | https://github.com/masahiro-mochizuki/signate-fundamentals-challange-1st-place 、https://github.com/UKI000/JQuants-Forum | repo | MIT / 未記載 | 42★(2025-02 push)/ 107★(2021-07 push) | 20 営業日先の高値・安値レンジ予測という「値幅の予測」の先行例。中身(特徴量)は Speaker Deck / PDF 側にあり未読 | ✅(中身❓) |

---

## 詳細

### 1. microsoft/qlib(最重要の「写し元」)

**現況(✅)**
- 49,316★、MIT、アーカイブなし、push 2026-10-08。PyPI 最新は **0.9.7(2025-08-15)**。GitHub には **v0.9.8(2026-10-08)** があるが「ソースアーカイブのみ、PyPI は別途確認」と書かれている。
- v0.9.8 はセキュリティ強化リリース。レコーダ成果物(モデル・データセット)の読み込みに `trusted=True` の明示が必要になり、特徴量式は制限付きパーサで評価されるようになった。古いチュートリアルのコードがそのまま動かない可能性がある。
- README に「公式データセットは一時的に無効」とあり、代替として `chenditc/investment_data`(中国株のみ)が案内されている。
- `qlib/constant.py` のリージョン定数は `REG_CN="cn"`、`REG_US="us"`、`REG_TW="tw"` の 3 つだけ。`qlib/config.py` の既定は cn(売買単位 100、値幅 0.095)、us(1、None)、tw(1000、0.1)。**日本は無い**。
- `scripts/data_collector/yahoo/collector.py` の対応地域は CN / US / IN / BR。**JP クラスは無い**。
- microsoft/qlib の Issue を "japan" で検索すると 0 件。

**Alpha158 の全定義(`qlib/contrib/data/loader.py` の `Alpha158DL.get_feature_config`、✅)**

内訳: K 線 9 本 + 価格 4 本(OPEN0, HIGH0, LOW0, VWAP0)+ ローリング 29 種 × 窓 5 種(5, 10, 20, 30, 60)= 158。

K 線(当日 1 本のローソク足の形)

| 名前 | 式 |
|---|---|
| KMID | `($close-$open)/$open` |
| KLEN | `($high-$low)/$open` |
| KMID2 | `($close-$open)/($high-$low+1e-12)` |
| KUP | `($high-Greater($open,$close))/$open` |
| KUP2 | `($high-Greater($open,$close))/($high-$low+1e-12)` |
| KLOW | `(Less($open,$close)-$low)/$open` |
| KLOW2 | `(Less($open,$close)-$low)/($high-$low+1e-12)` |
| KSFT | `(2*$close-$high-$low)/$open` |
| KSFT2 | `(2*$close-$high-$low)/($high-$low+1e-12)` |

価格: `$open/$close`、`$high/$close`、`$low/$close`、`$vwap/$close`(名前は OPEN0 など)。

ローリング(d = 5, 10, 20, 30, 60)

| 名前 | 式 | 意味 |
|---|---|---|
| ROC{d} | `Ref($close,d)/$close` | d 日前終値 ÷ 当日終値。**値が大きい = 下がった**(符号に注意) |
| MA{d} | `Mean($close,d)/$close` | 移動平均乖離の逆数型 |
| STD{d} | `Std($close,d)/$close` | 価格の標準偏差 |
| BETA{d} | `Slope($close,d)/$close` | 回帰の傾き(トレンドの速さ) |
| RSQR{d} | `Rsquare($close,d)` | トレンドの直線性 |
| RESI{d} | `Resi($close,d)/$close` | 回帰残差 |
| MAX{d} | `Max($high,d)/$close` | 期間高値との距離 |
| MIN{d} | `Min($low,d)/$close` | 期間安値との距離(設定キーは "LOW") |
| QTLU{d} | `Quantile($close,d,0.8)/$close` | 80% 分位 |
| QTLD{d} | `Quantile($close,d,0.2)/$close` | 20% 分位 |
| RANK{d} | `Rank($close,d)` | 期間内での時系列パーセンタイル順位 |
| RSV{d} | `($close-Min($low,d))/(Max($high,d)-Min($low,d)+1e-12)` | ストキャスティクス %K 相当 |
| IMAX{d} | `IdxMax($high,d)/d` | 高値を付けた日の位置(Aroon 相当) |
| IMIN{d} | `IdxMin($low,d)/d` | 安値を付けた日の位置 |
| IMXD{d} | `(IdxMax($high,d)-IdxMin($low,d))/d` | 高値日と安値日の前後関係 |
| CORR{d} | `Corr($close, Log($volume+1), d)` | 価格と出来高の相関 |
| CORD{d} | `Corr($close/Ref($close,1), Log($volume/Ref($volume,1)+1), d)` | 価格変化と出来高変化の相関 |
| CNTP{d} | `Mean($close>Ref($close,1), d)` | 上昇日の割合 |
| CNTN{d} | `Mean($close<Ref($close,1), d)` | 下落日の割合 |
| CNTD{d} | CNTP − CNTN | 上昇日と下落日の差 |
| SUMP{d} | `Sum(Greater($close-Ref($close,1),0),d)/(Sum(Abs($close-Ref($close,1)),d)+1e-12)` | RSI 相当(上昇幅の比率) |
| SUMN{d} | `Sum(Greater(Ref($close,1)-$close,0),d)/(Sum(Abs($close-Ref($close,1)),d)+1e-12)` | 下落幅の比率 |
| SUMD{d} | SUMP − SUMN | 上昇幅と下落幅の差 |
| VMA{d} | `Mean($volume,d)/($volume+1e-12)` | 出来高移動平均比 |
| VSTD{d} | `Std($volume,d)/($volume+1e-12)` | 出来高の標準偏差 |
| WVMA{d} | `Std(Abs($close/Ref($close,1)-1)*$volume,d)/(Mean(Abs($close/Ref($close,1)-1)*$volume,d)+1e-12)` | 出来高加重の価格変動のばらつき |
| VSUMP{d} | `Sum(Greater($volume-Ref($volume,1),0),d)/(Sum(Abs($volume-Ref($volume,1)),d)+1e-12)` | 出来高版 RSI |
| VSUMN{d} | `Sum(Greater(Ref($volume,1)-$volume,0),d)/(Sum(Abs($volume-Ref($volume,1)),d)+1e-12)` | 同・減少側 |
| VSUMD{d} | VSUMP − VSUMN | 同・差 |

**Alpha360(`Alpha360DL`、✅)**: `Ref($close,i)/$close`、`Ref($open,i)/$close`、`Ref($high,i)/$close`、`Ref($low,i)/$close`、`Ref($vwap,i)/$close`、`Ref($volume,i)/($volume+1e-12)` を i = 59〜0 で並べた 6 × 60 = 360 本。系列モデル(GRU/LSTM など)向けの「生データ窓」。

**演算子の意味(`qlib/data/ops.py`、✅)— 自前実装で間違えやすい点**
- `Ref(x, N)`: N>0 は N 本前(過去)。**N<0 は未来**(ラベル専用)。
- ローリング系は pandas の `rolling(N, min_periods=1)`。窓が埋まる前でも値が出る点に注意(序盤の値は少数サンプル)。
- `Std` / `Var` は ddof=1。
- `Rank(x, N)` は**時系列**の窓内パーセンタイル順位(0〜1)。WorldQuant 101 の `rank` は**クロスセクション**順位で、別物。
- `IdxMax` / `IdxMin` は 1 始まり(1 = 窓内で最も古い、N = 最新)。
- `Mad` は平均絶対偏差(中央値絶対偏差ではない)。
- `Slope` / `Rsquare` / `Resi` は Cython 実装で、x 軸は 1, 2, 3, … と docstring にある(コードは未確認)。
- `Greater` / `Less` は `np.maximum` / `np.minimum`。
- `Corr` は片方のローリング標準偏差がほぼ 0 のとき NaN。

**ラベルと正規化(`qlib/contrib/data/handler.py`、✅)**
- Alpha158 / Alpha360 のラベル: `Ref($close, -2)/Ref($close, -1) - 1`。**翌日終値→翌々日終値**のリターン(当日引け後に予測し、翌日引けで建てる想定)。vwap 版は `Ref($vwap,-2)/Ref($vwap,-1)-1`。
- 学習用既定プロセッサ: `DropnaLabel` + `CSZScoreNorm(fields_group="label")`(ラベルを日ごとにクロスセクション z スコア化)。
- 推論用既定プロセッサ(Alpha360): `ProcessInf` → `ZScoreNorm` → `Fillna`。Alpha158 は推論側プロセッサ既定なし。
- `processor.py` の定義: `RobustZScoreNorm` は (x − 中央値) / ((MAD + EPS) × 1.4826) を [−3, 3] にクリップ(fit 期間で推定)。`CSRankNorm` は日ごとのパーセンタイル順位 r に対し (r − 0.5) × 3.46。`CSZFillna` は日ごとの平均で欠損補完。`TimeRangeFlt` は未来情報リークの可能性ありと明記。

**LightGBM ベンチマーク設定(`workflow_config_lightgbm_Alpha158.yaml`、✅)**
- 学習 2008-01-01〜2014-12-31、検証 2015-01-01〜2016-12-31、テスト 2017-01-01〜2020-08-01。市場 CSI300、ベンチマーク SH000300。
- モデル: loss=mse、learning_rate=0.2、max_depth=8、num_leaves=210、colsample_bytree=0.8879、subsample=0.8789、lambda_l1=205.6999、lambda_l2=580.9768、num_threads=20。
- 戦略: `TopkDropoutStrategy`(topk=50、n_drop=5)。資金 1 億、終値約定、値幅 9.5%、買いコスト 0.0005、売りコスト 0.0015、最低 5。
- 記録: `SignalRecord` → `SigAnaRecord`(ann_scaler 252)→ `PortAnaRecord`。

**公式ベンチマーク結果(`examples/benchmarks/README.md`、CSI300、20 シード平均、✅)**

| モデル(Alpha158) | IC | ICIR | Rank IC | 年率超過リターン | 情報比 | 最大 DD |
|---|---|---|---|---|---|---|
| Linear | 0.0397 | 0.3000 | 0.0472 | 0.0692 | 0.9209 | −0.1509 |
| LightGBM | 0.0448 | 0.3660 | 0.0469 | 0.0901 | 1.0164 | −0.1038 |
| XGBoost | 0.0498 | 0.3779 | 0.0505 | 0.0780 | 0.9070 | −0.1168 |
| CatBoost | 0.0481 | 0.3366 | 0.0454 | 0.0765 | 0.8032 | −0.1092 |
| DoubleEnsemble | 0.0521 | 0.4223 | 0.0502 | 0.1158 | 1.3432 | −0.0920 |
| MLP | 0.0376 | 0.2846 | 0.0429 | 0.0895 | 1.1408 | −0.1103 |
| Transformer | 0.0264 | 0.2053 | 0.0407 | 0.0273 | 0.3970 | −0.1101 |
| TRA | 0.0440 | 0.3535 | 0.0540 | 0.0718 | 1.0835 | −0.0760 |

- Alpha360 では LightGBM が IC 0.0400、最良は HIST の IC 0.0522 / 年率 0.0987。
- 読み取り: **木系 + 手作り特徴(Alpha158)が深層系列モデルと同等以上**。線形でも IC 0.04。MVP は LightGBM で十分。
- 限界: 中国 A 株・2017〜2020 年・単一期間。日本株への転用は未検証。CSI500 の表には DoubleEnsemble 行に Linear 行と同じ値が入っており転記ミスの疑いがある。

**評価関数(`qlib/contrib/eva/alpha.py`、✅)**
- `calc_ic(pred, label)`: 日ごとに Pearson(IC)と Spearman(Rank IC)。
- `calc_long_short_return(pred, label, quantile=0.2)`: 日ごとに上位 20% と下位 20% の平均ラベルを取り、`(r_long − r_short) / 2`。
- `calc_long_short_prec(pred, label, quantile=0.2, is_alpha=False)`: 上位群でラベル > 0 の割合、下位群でラベル < 0 の割合(**方向的中率の定義としてそのまま使える**)。
- `pred_autocorr(pred, lag=1)`: 予測の日次自己相関(入れ替わりの激しさ)。

**TopkDropoutStrategy(`qlib/contrib/strategy/signal_strategy.py`、✅)**: スコア上位 topk を保有し、1 日あたり最大 n_drop 銘柄だけ入れ替える。売りは保有銘柄のうち合成順位の下位 n_drop に落ちたもの。買いは等金額(現金 × risk_degree 0.95 ÷ 買い銘柄数)。発注しない本プロジェクトでは「仮想ポートフォリオの定義」として使える。

**オンライン運用(`docs/component/online.rst`、`examples/online_srv/update_online_pred.py`、✅)**
- 4 部品: Online Manager / Online Strategy / Online Tool / Updater。
- 最小例: `first_train()` で `task_train(...)` → `online_tool.reset_online_tag(rec)`。以後は 1 日 1 回 `online_tool.update_online_pred()`。
- ドキュメントに「翌営業日の予測更新は対応、**翌日の注文生成は公開データの制約で非対応**」と明記。データ更新は利用者の責任。

**高頻度(1 分足)特徴(`qlib/contrib/data/highfreq_handler.py`、✅)**
- 価格の正規化: `P / DayLast(Ref(FFillNan($close), 243))`(前日終値で割る。243 は 240 本/日の中国市場前提)。
- 出来高の正規化: `v / Ref(DayLast(Mean(v, 7200)), 240)`(過去 30 日 = 7200 分の平均で割る)。
- `HighFreqGeneralHandler(day_length=240)` は 1 日の本数をパラメータ化。東証で使うなら day_length を 1 日の分足本数に置き換える(東証の現行立会時間は本セッションで一次情報を開けず❓)。

### 2. Qlib を日本株で使う具体的手順(質問 2 への回答)

**既存事例**: `iyoda/jquants-qlib` のみ(✅)。
- J-Quants の日足を無調整のまま Parquet に保存し、Qlib 変換時に分割・併合・株主割当を調整して `$factor` を書く(規約は `raw = $close / $factor`)。**配当は調整しない**。
- 生成物に `calendars/day.txt` と `instruments/all.txt` を含む。
- Qlib に日本リージョンが無いので例では `region="cn"` を使用。
- Windows 非対応(symlink による publish と Keychain 依存のため)。Python 3.10〜3.12。Light プラン前提。
- モデル学習・バックテスト設定は含まない(データ ETL まで)。
- スター 0・コミット 11 の出来立てで、品質は未検証。

**自分でやる場合の手順(Qlib 公式ドキュメント `docs/component/data.rst` と Yahoo コレクタの構造から組み立てたもの。日本株での通し実行は未検証)**
1. Python 3.12 の venv を別に作り `pip install pyqlib==0.9.7`(cp312 win_amd64 wheel あり ✅)。
2. J-Quants V2 から日足を取得し、銘柄ごとの CSV(または 1 ファイルに symbol 列)を作る。列は最低 `date, symbol, open, high, low, close, volume, factor`。Alpha158 は `$vwap` を使うので `vwap = 売買代金 ÷ 出来高` も入れる(J-Quants V2 の正確な列名は `jquants schema eq.daily` で要確認❓)。
3. `factor = 調整後価格 ÷ 元の価格`。価格列は調整後、出来高は factor で割る(Yahoo コレクタの `adjusted_price` と同じ規約 ✅)。売買停止日は OHLCV と factor を NaN にする。
4. `python scripts/dump_bin.py dump_all --data_path <csv_dir> --qlib_dir <qlib_dir> --include_fields open,close,high,low,volume,vwap,factor --symbol_field_name symbol --date_field_name date --file_suffix .csv`
5. `python scripts/check_data_health.py check_data --qlib_dir <qlib_dir>` で欠損と異常値を確認。
6. 銘柄プール(例: TOPIX500)は `instruments/<name>.txt` を自作する(書式は公式ドキュメントに記載が無く、既存ファイルを見て合わせる必要あり❓)。ベンチマーク(TOPIX)は指数を 1 銘柄として同じ形式で投入する。
7. `qlib.init(provider_uri=<qlib_dir>, region="us")` を基本にし、売買単位だけ 100 に上書きする案(`qlib.init` は余剰キーワードを設定に書き込む実装 ✅。ただし日本株での動作は未検証)。`region="cn"` だと値幅 9.5% がバックテストに適用され、日本の値幅制限(価格帯別の円建て)と合わない。
8. Windows ではスクリプトを `if __name__ == "__main__":` で包む(マルチプロセス対策。jquants-qlib の README にも同じ注意 ✅)。`run_all_model.py` は Linux 専用と README に明記 ✅。
9. 日次更新は CSV を作り直して再ダンプ。Yahoo コレクタの `update_data_to_bin` は CN/US 専用なので使えない ✅。

**Yahoo コレクタに JP を足す場合の作業(collector.py の構造から ✅)**: `YahooCollectorJP1d`(`_timezone`、`get_instrument_list`、`normalize_symbol`、`download_index_data` を実装)と `YahooNormalizeJP1d`、`data_collector/utils` に `get_jp_stock_symbols` を追加。ただし Yahoo の日本株データ品質は Qlib 自身が「完璧ではない」と警告しており、J-Quants を使う方が筋が良い。

### 3. 日本株の先行実装: JPX Tokyo Stock Exchange Prediction(Kaggle、2022)

リポジトリ `winner-models/` に上位 10 解法が入っている(Apache-2.0 ✅)。Private LB スコア: 1 位 0.381、2 位 0.356、3 位 0.352、4 位 0.347、5 位 0.339、6 位 0.308、7 位 0.301、8 位 0.289、9 位 0.281、10 位 0.280。

課題の目的変数は「各銘柄の P(t+2)/P(t+1) − 1」(5 位 README で確認 ✅)。評価指標は「日次スプレッドリターンのシャープレシオ(上位 200 と下位 200、線形加重)」と記憶しているが、本セッションでは Kaggle ページを開けず❓。

| 順位 | モデル | 特徴量 | 特記 |
|---|---|---|---|
| 1 位 | scikit-learn `LinearRegression` | SecuritiesCode, Open, High, Low, Close, Volume, AdjustmentFactor, ExpectedDividend, SupervisionFlag + Daily_Range, Mean | 標準化のみ。学習 45.5 秒 |
| 2 位 | LightGBM 回帰(単体) | return_1month / 2month / 3month(20 / 40 / 60 営業日リターン)、volatility_1month / 2month / 3month、MA_gap_1month / 2month / 3month(終値と SMA の乖離)、Close, Open, Low, High, Volume の 14 本 | 60 日 MA 乖離が最重要。CV 約 0.25、Private 0.36。LGBMRanker と XGBoost は改善せず |
| 3 位 | `DecisionTreeRegressor` 単体 | Open, High, Low, Close の 4 本のみ | 特徴量エンジニアリングなし |
| 4 位 | ルールベース(ML なし) | return_1day の順位 + ExpectedDividend > 0 の銘柄を最下位へ | 本人が最重要の工夫を「Luck!」と回答 |
| 5 位 | LightGBM 回帰 | SecuritiesCode(カテゴリ)、Close_rank、mrsignal(2 日リターン)、momsignal(131 日リターン、25 日ラグ)、volsignal(過去 231 営業日の日次リターン標準偏差)、adv_rank(11 営業日平均出来高の順位)、ave_momsignal、ave_mrsignal の 8 本 | 下記 |

**5 位解法の要点(最も情報量が多い ✅)**
- 目的変数を「P(t+2)/P(t) − クロスセクション平均」に変更(市場中立の超過リターン)。ベータよりアルファの方が予測しやすいという判断。
- 短期リバーサル(2 日リターン)が最重要シグナル。モメンタム・ボラティリティ・出来高も寄与。
- 学習データを日次リターン上位 250・下位 250 銘柄だけに絞ると大きく改善(外れ値を刈るのではなく外れ値で学習)。
- 銘柄コードをカテゴリ変数にすると OOS が改善。
- ファンダ指標と市場全体のインプライドボラは OOS で改善せず。
- 検証は約 1 年から始めて 1 か月ずつ伸ばす拡張ウィンドウのウォークフォワード。3〜4 年の OOS で月次スコア平均が約 0.2。
- 生の価格は分割等が未調整に見えたため、調整済み目的変数から価格系列を再構築。

**読み取り**: 上位が極端に単純なモデルで占められ、4 位が運と明言している。**3 か月程度の採点期間では、凝ったモデルの優位は統計的に示せない**。本プロジェクトの採点設計(後述)はこの前提で組むべき。

### 4. WorldQuant 101 Formulaic Alphas(✅ PDF 本文を抽出)

- Kakushadze (2016)、arXiv:1601.00991。データ期間 2010-01-04〜2013-12-31(1,006 営業日)。
- 平均保有期間 0.6〜6.4 日。ペア相関の平均 15.9%(中央値 14.3%)。
- 年率シャープ(コスト控除前)は最小 1.24、中央値 2.22、平均 2.27、最大 4.16(Table 1)。**「取引コスト・マーケットインパクト等を含まない」と明記**。
- アルファの平均日次リターン R はアルファの日次ボラティリティ V と R ∝ V^0.76 の関係(回帰係数 0.761、標準誤差 0.046)。回転率への有意な依存なし。これは**戦略単位**の性質で、個別銘柄の値幅の話ではない。
- delay-0(計算に使う価格の時刻と売買時刻が同じ。引け際に売買する想定)は #42、#48、#53、#54 の 4 本。残りは delay-1(翌日に売買)。
- 論文中の説明例: 「−ln(当日始値 / 前日終値)」は delay-0 の平均回帰アルファ(寄りで逆張り)。「ln(前日終値 / 前日始値)」は delay-1 のモメンタムアルファ。

演算子(付録 A): `rank(x)`=クロスセクション順位、`delay(x,d)`=d 日前の値、`delta(x,d)`=当日 − d 日前、`correlation(x,y,d)` / `covariance(x,y,d)`=過去 d 日の時系列相関/共分散、`scale(x,a)`=絶対値和が a になるよう再スケール、`signedpower(x,a)`=x^a、`decay_linear(x,d)`=重み d, d−1, …, 1 の加重移動平均、`indneutralize(x,g)`=業種内で平均を引く、`ts_min` / `ts_max` / `ts_argmax` / `ts_argmin` / `ts_rank` / `sum` / `product` / `stddev`=過去 d 日の時系列演算。入力: returns(終値間日次リターン)、open、close、high、low、volume、vwap、cap、adv{d}(過去 d 日の平均売買代金)。

写しやすい式(原文どおり)
- Alpha#2: `(-1 * correlation(rank(delta(log(volume), 2)), rank(((close - open) / open)), 6))`
- Alpha#3: `(-1 * correlation(rank(open), rank(volume), 10))`
- Alpha#4: `(-1 * Ts_Rank(rank(low), 9))`
- Alpha#6: `(-1 * correlation(open, volume, 10))`
- Alpha#12: `(sign(delta(volume, 1)) * (-1 * delta(close, 1)))`
- Alpha#33: `rank((-1 * ((1 - (open / close))^1)))`
- Alpha#41: `(((high * low)^0.5) - vwap)`
- Alpha#42: `(rank((vwap - close)) / rank((vwap + close)))`
- Alpha#53: `(-1 * delta((((close - low) - (high - close)) / (close - low)), 9))`
- Alpha#54: `((-1 * ((low - close) * (open^5))) / ((low - high) * (close^5)))`
- Alpha#101: `((close - open) / ((high - low) + .001))`

実装リポジトリ(GitHub 検索 ✅)
- `yli188/WorldQuant_alpha101_code`: 878★、**ライセンスなし**、コミット 1 本(2019-03)。コードの転用は権利上グレー。
- `STHSF/alpha101`: 189★、MIT、2019-06。
- `Menooker/KunQuant`: Apache-2.0、Alpha101 と Alpha158。`rank` を含む因子は数値的に敏感と注記。
- `popbo/alphas`: 593★、ライセンス未記載、`alphas101.py` と `alphas191.py`。

### 5. ML4T 第 3 版と ml4t-* ライブラリ(2026 年の新顔)

- `stefan-jansen/machine-learning-for-trading`: 21,319★、push 2026-10-13。第 3 版は全面書き直しで 27 章。第 2 版は `second-edition` ブランチ。
- 9 つのケーススタディ: ETF(日次)、暗号資産パーペチュアル(8 時間)、**NASDAQ-100(15 分足、板・注文フロー)**、S&P500 株+オプション、米国企業特性(月次)、FX、CME 先物、S&P500 オプション、米国株パネル。**日本市場の事例は無い**。
- 環境: Linux と Apple Silicon が正式。**Windows は WSL2 のみ**(ネイティブ Windows Python は非対応と明記)。
- 付属 6 ライブラリ: ml4t-data / ml4t-engineer / ml4t-models / ml4t-diagnostic / ml4t-backtest / ml4t-live。データ層は Polars。
- **ml4t-engineer 0.1.6**(Python 3.12〜3.14、Windows 対応 ✅): 特徴 120 本を 11 分類で提供 — Momentum 31(RSI、MACD、Stochastic、CCI、ADX、MFI)、Microstructure 15(Kyle Lambda、VPIN、Amihud、Roll spread)、Volatility 15(ATR、Bollinger、Yang-Zhang、Parkinson)、Statistics 14、ML 14(分数階差分、エントロピー、ラグ)、Trend 10、Risk 6、Price Transform 5、Regime 4(Hurst、Choppiness)、Volume 3、Math 3。ラベルはトリプルバリア、ATR バリア、パーセンタイル、固定ホライズン、トレンドスキャン、メタラベル。バーはティック/出来高/ドル/不均衡/ラン。
- **ml4t-diagnostic 0.1.8**(同上 ✅): `analyze_signal`(HAC 補正 IC、分位プロファイル、回転率)、`WalkForwardCV` / `CombinatorialCV` / `ValidatedCrossValidation`、Deflated Sharpe Ratio、PBO、RAS、FDR 制御、White's Reality Check。
- 注意: どちらもスター 20〜30 台・バージョン 0.1.x の新しいパッケージ。0.1.0 は 3.15 のインストール失敗で yank 済み。API の安定性は未知数。

### 6. Numerai example-scripts / numerai-tools

- データ v5.3。特徴セット: small 42、faith 372、medium 780、quantum 807、all 3,555。ターゲットは `target`(将来リターンの指標)と `target_ender_20`。
- `example_model.ipynb` の LightGBM: `n_estimators=2000, learning_rate=0.01, max_depth=5, num_leaves=2**5-1, colsample_bytree=0.1`。コメントアウトされた「深い」設定は `n_estimators=30_000, learning_rate=0.001, max_depth=10, num_leaves=2**10, colsample_bytree=0.1, min_data_in_leaf=10000`。学習は era を 4 つおきに間引く(隣接 era のラベル重複を避ける)。
- `numerai_corr`: 予測を順位化 `(rank − 0.5) / n` → 正規分布の逆関数 → `sign(x)·|x|^1.5` → ターゲット(中心化し同じく 1.5 乗)との Pearson。裾(極端な予測)の当たり外れを重く評価する指標。
- `neutralize(df, neutralizers, proportion)`: 中和対象に切片列を足して最小二乗(`np.linalg.lstsq(..., rcond=1e-6)`)し、`proportion × 予測値` を引く。特徴量エクスポージャ(特定因子への偏り)を落とす。
- `correlation_contribution`(MMC): 予測をメタモデルに直交化してからターゲットとの内積 ÷ n。「既存の予測に何を上乗せできたか」の指標 — 本プロジェクトでは**ルール予測が機械予測に上乗せする価値**の測定に転用できる。

### 7. 指標ライブラリと分析ライブラリ(Windows + Python 3.13 適合)

| パッケージ | 版(公開日) | requires_python / 分類子 | 3.13 + Windows | メモ |
|---|---|---|---|---|
| pyqlib | 0.9.7(2025-08-15) | >=3.8、分類子 3.8〜3.12 | **不可**(cp313 wheel なし、sdist も PyPI に無し) | 3.12 venv なら win_amd64 wheel あり |
| lightgbm | 4.7.0 | >=3.10、分類子 3.14 まで | 可(wheel 一覧は未確認❓) | |
| TA-Lib | 0.8.2 | >=3.9、分類子 3.14 まで | 可 | Windows wheel に C ライブラリ同梱 |
| pandas-ta-classic | 0.8.32(2026-09-14) | >=3.10、分類子 3.14 まで | 可 | numpy>=2 必須 |
| ta | 0.11.0(2023-11-02) | 指定なし、分類子 3.6 / 3.7 | 未確認 | PyPI は 3 年更新なし(GitHub は 2026-03 push) |
| ml4t-engineer | 0.1.6(2026-09-25) | 3.12〜3.14 | 可 | numba、polars 依存 |
| ml4t-diagnostic | 0.1.8(2026-09-24) | 3.12〜3.14 | 可 | |
| alphalens-reloaded | 0.4.6(2025-06-02) | >=3.10、分類子 3.13 まで | 可 | pandas<3.0 |
| pyfolio-reloaded | 0.9.9(2025-06-02) | >=3.9、分類子 3.13 まで | 可 | pandas<3.0 |
| quantstats | 0.0.86(2026-09-27) | >=3.10、分類子 3.13 まで | 可 | yfinance に依存 |
| vectorbt | 1.1.2(2026-10-09) | 3.11〜3.14 | 可 | pandas>=3.0.3、numpy>=2.4.6、numba>=0.66 |
| tsfresh | 0.21.2(2026-05-31) | >=3.9、分類子 3.12 まで | 未確認 | |
| RiskLabAI | 3.1.0 | 3.12〜3.14 | 可(未実行) | numpy>=2.2 |
| jquants-api-client | (版未確認) | >=3.10、3.13 でテスト | 可 | pandas>=2.2 |
| RD-Agent | — | 3.10 / 3.11、Linux のみ | **不可** | Docker 必須 |
| Kronos | — | 3.10+ | 未確認 | PyTorch、GPU 推奨の記述 |

- **元祖 `twopirllc/pandas-ta` は GitHub で 404**(✅)。awesome-systematic-trading でも "no longer available" 表記。
- **`hudson-and-thames/mlfinlab`**: 4,939★ だが README に「all rights reserved licence」と有償(Business / Enterprise)の案内。最終 push 2023-10。OSS としては使えない(✅)。

### 8. LLM・自動化系(後回し候補だが把握しておく)

- **RD-Agent**(NeurIPS 2025 と arXiv コメントに記載、arXiv:2505.15155): 仮説生成 → コード生成(Co-STEER)→ バックテスト → フィードバックを回し、次の探索方向をバンディットで選ぶ。主張は「古典的因子ライブラリ比で年率リターン最大 2 倍、因子数 70% 減」。対象市場は要旨に記載なし。LLM は LiteLLM 経由(`CHAT_MODEL`、`EMBEDDING_MODEL` 環境変数)。
- **Kronos**: 45 以上の取引所の K 線で事前学習と記載(東証を含むかは未記載)。mini 4.1M / small 24.7M / base 102.3M パラメータ(large 499.2M は非公開)。README に数値の精度指標は無い。ファインチューニング手順は Qlib の中国株データ前提。
- **TradingAgents**: v0.6.0。SEC 以外の企業は過去日付での実行時に財務諸表を伏せる仕様(先読み防止)。出力は非決定的で、公表数値の再現は保証しないと明記。
- **FinRL-X**(arXiv:2603.21330): 自己申告で 2018-01〜2025-10 のバックテスト年率 25.85% / Sharpe 0.93、2025-10〜2026-03 のペーパートレードで Sharpe 1.96。米国株のみ、検証期間 5 か月。

---

## 因果ルール候補

本観点(基盤・特徴量ライブラリ)から直接裏づけが取れたものに絞る。確度は A=複数の査読研究で再現、B=単独研究または実務統計あり、C=経験則・未検証。日本株での定量検証はほぼ無いので、日本向けの確度は 1 段下げて読むこと。

### R1. 短期リバーサル(クロスセクション、1〜5 日)
- **IF** ある銘柄の直近 2 営業日リターンが、同日の全銘柄の中で下位(上位)にある → **THEN** 翌営業日以降の 1〜2 日の対市場相対リターンは高め(低め)。大きさの目安は未確定(5 位解法は式を公開しているが銘柄単位の効果量は未記載)。時間軸は 1〜2 日。
- **なぜ**: 一時的な需給の偏り(流動性提供への対価)と売買気配の跳ね返り。Heston-Korajczyk-Sadka (2010) は短期リバーサルを「1 時間未満で解消する一時的な流動性不均衡 + ビッド・アスク・バウンス」と説明。
- **根拠**: (a) JPX Kaggle 5 位解法 — 東証約 2,000 銘柄、3〜4 年のウォークフォワードで月次スコア平均約 0.2、「短期平均回帰が最重要」https://github.com/J-Quants/JPXTokyoStockExchangePrediction/tree/main/winner-models/5th (b) Kakushadze (2016) — 101 本の多くが平均回帰型、保有 0.6〜6.4 日、コスト控除前シャープ中央値 2.22(米国、2010〜2013)https://arxiv.org/abs/1601.00991 (c) Qlib Alpha158 の ROC5 / RSV5 / SUMD5 などが同じ情報を持つ。
- **効かなくなる条件**: 決算・材料で動いた銘柄(情報による価格変化は戻らない)。低流動性銘柄ではスプレッドで消える。コスト控除後は大幅に縮む(原論文もコスト抜き)。相場全体が一方向に走る局面。
- **必要データと入手時刻**: 調整済み終値(当日引け後。J-Quants の日足更新時刻は未確認❓)。
- **確度**: B(日本株ではコンペ 1 件の実証。寄り→引けでの有効性は未検証)。

### R2. 配当権利落ち日の機械的な下落
- **IF** 翌営業日が配当の権利落ち日 → **THEN** 前日終値→当日始値(および無調整の終値間リターン)は、1 株配当 ÷ 株価の分だけ機械的に下がる。寄り→引けのリターンには機械的影響なし。
- **なぜ**: 権利落ちで配当分だけ理論株価が下がる。分割・併合と違い、J-Quants の調整係数は配当を調整しない。
- **根拠**: (a) JPX Kaggle 4 位解法が「ExpectedDividend > 0 の銘柄を最下位に置く」ルールで Private 0.347。参照スレッド名に "Shorting dividend days = easy score boost" https://github.com/J-Quants/JPXTokyoStockExchangePrediction/tree/main/winner-models/4th (b) jquants-qlib の README が「配当は調整しない」と明記 https://github.com/iyoda/jquants-qlib
- **効かなくなる条件**: 配当込みで調整したリターンを使う場合は消える(見かけの効果)。配当額が小さい銘柄。
- **必要データと入手時刻**: 権利落ち日と予想配当(J-Quants の配当情報は Premium プラン。決算短信の予想配当は財務サマリーにある可能性 ❓)。前営業日までに判明。
- **確度**: A(算術的な効果)。ただし「予測の当たり」ではなく**データ処理上の落とし穴**として扱う。

### R3. 夜間リターンと日中リターンの持続と相互反転(tug of war)
- **IF** ある銘柄の過去 1 か月の日中(寄り→引け)リターンが相対的に高い → **THEN** その後も日中リターンは高めに出やすく、夜間(引け→寄り)リターンは低めに出やすい。逆に過去の夜間リターンが高い銘柄は、日中リターンが低めに出やすい。大きさの目安は要旨に数値なし。時間軸は翌日〜数か月。
- **なぜ**: 夜間に売買する投資家層と日中に売買する投資家層が異なり、それぞれの需要が持続するため。
- **根拠**: Lou, Polk, Skouras (2019) "A tug of war: Overnight versus intraday expected returns", Journal of Financial Economics。米国株。14 の戦略で利益が夜間か日中のどちらか一方に集中し符号が逆、と要旨に記載。DOI 10.1016/j.jfineco.2019.03.011(Semantic Scholar 経由で要旨確認、被引用 241)
- **効かなくなる条件**: 日本株での再現は未確認。寄り付きの板寄せ方式や昼休みの存在で構造が違う可能性。
- **必要データと入手時刻**: 調整済みの始値・終値(日足で足りる)。前日引け後に計算可能。
- **確度**: B(米国)/ C(日本)。寄り→引け予測に直結するので**最優先で自前検証**したい。

### R4. 市場全体の日中モメンタム(最初の 30 分 → 最後の 30 分)
- **IF** 指数(または指数 ETF・先物)の寄り付き後 30 分のリターンが正(負) → **THEN** 大引け前 30 分のリターンも正(負)になりやすい。
- **なぜ**: 情報を持つ投資家が朝と引け際に分けて売買する、引け前のヘッジ・リバランス需要など。
- **根拠**: Gao, Han, Li, Zhou (2018) "Market intraday momentum", Journal of Financial Economics。S&P500 ETF、1993〜2013 年。ボラティリティが高い日、出来高が多い日、景気後退期、重要マクロ指標の発表日に強い。他の 10 本の ETF と 2 本の海外株価指数先物でも成立と要旨に記載。DOI 10.1016/j.jfineco.2018.05.009(要旨確認、被引用 186)
- **効かなくなる条件**: 低ボラ・薄商いの日。日本の指数での再現は本セッションで未確認。個別銘柄では別の話(R5)。
- **必要データと入手時刻**: 指数または先物の分足(9:30 時点で判定)。J-Quants の分足はアドオン(月 5,500 円)。
- **確度**: B(米国)/ C(日本)。日中の途中で予測を更新する設計にする場合のみ使える。

### R5. 同時刻の周期性(個別銘柄)
- **IF** ある銘柄が過去数日〜40 営業日、特定の 30 分枠で他銘柄より高いリターンを出している → **THEN** 次の営業日の同じ 30 分枠でも相対的に高くなりやすい。
- **なぜ**: 機関投資家が毎日同じ時刻に分割発注する習慣(出来高・注文不均衡にも同じ周期があるが、それだけでは説明しきれないと著者は述べる)。
- **根拠**: Heston, Korajczyk, Sadka (2010) "Intraday Patterns in the Cross-Section of Stock Returns", Journal of Finance。米国株。少なくとも 40 営業日持続。DOI 10.1111/j.1540-6261.2010.01573.x(要旨確認、被引用 180)
- **効かなくなる条件**: 効果量は実効スプレッド程度と著者が示唆(=単独では取引コストに負ける)。日本株での再現は未確認。
- **必要データと入手時刻**: 個別銘柄の 30 分足を 40 営業日分。
- **確度**: B(米国)/ C(日本)。分足データを買うまでは保留。

### R6. 前日のローソク足実体の向き(翌日モメンタム)
- **IF** 前日の `(終値 − 始値) / (高値 − 安値 + 0.001)` が大きい(陽線の実体が値幅に対して大きい) → **THEN** 翌日は上方向(クロスセクションで相対的に)。
- **なぜ**: 日中の一方向の買いが翌日も続くという短期モメンタム仮説。
- **根拠**: Kakushadze (2016) の Alpha#101。著者自身が「delay-1 のモメンタムアルファ」と説明。米国、2010〜2013、個別アルファの成績は非開示。Qlib の KMID2 が同じ式。
- **効かなくなる条件**: R1(短期リバーサル)と逆方向なので、どちらが優勢かは市場・期間依存。コスト控除前の主張。
- **必要データと入手時刻**: 前日の四本値(前日引け後)。
- **確度**: C。R1 と競合するため、必ず両方を同じ期間で比べる。

### R7. 引け値と当日 VWAP の乖離(引け際の逆張り)
- **IF** 当日の終値が VWAP より高い(午後に買われた) → **THEN** 直後は反落しやすい(逆なら反発)。
- **なぜ**: 引けにかけての一時的な需給の偏りの解消。
- **根拠**: Kakushadze (2016) の Alpha#42 `rank(vwap − close) / rank(vwap + close)`。著者が「delay-0 の平均回帰アルファ、引け近くで逆張り」と説明。米国、2010〜2013。
- **効かなくなる条件**: delay-0 前提(引けで売買)なので、翌日寄りまで待つと効果が残るかは不明。日本株未検証。
- **必要データと入手時刻**: 当日の終値と VWAP(売買代金 ÷ 出来高。引け後)。
- **確度**: C。

### R8. 中期モメンタム・ボラティリティ・流動性は補助シグナル
- **IF** 131 営業日リターン(直近 25 日を除く)が高い / 231 営業日ボラティリティが高い・低い / 11 営業日平均出来高の順位が高い・低い → **THEN** 翌日以降の相対リターンに弱い説明力(方向は木モデル任せで、単純な符号は公開情報から確定できない)。
- **なぜ**: 中期モメンタム、低ボラティリティ効果、流動性プレミアムという既知の因子群。
- **根拠**: (a) JPX Kaggle 5 位解法が「モメンタム、ボラティリティ、出来高も寄与」と記載 (b) Gu, Kelly, Xiu (2020) "Empirical Asset Pricing via Machine Learning", Review of Financial Studies 33(5) — 米国株・月次で、どの手法も支配的な予測変数はモメンタム・流動性・ボラティリティの変種と要旨に記載。DOI 10.1093/rfs/hhaa009(Crossref で要旨確認)(c) Asness (2011) "Momentum in Japan: The Exception that Proves the Rule", Journal of Portfolio Management — 題名のとおり日本はモメンタムが弱い例外として知られる(要旨は取得できず、内容は❓)。
- **効かなくなる条件**: 日次・日中の時間軸では効果が小さい(根拠の多くは月次)。
- **必要データと入手時刻**: 過去 1 年分の調整済み日足。
- **確度**: B(因子群の存在)/ C(日本の日次予測での寄与の大きさ)。

---

## 落とし穴・反証・注意

**環境・依存**
- pyqlib は Python 3.13 に入らない(0.9.7 の wheel は cp38〜cp312、sdist なし)。v0.9.8 は 2026-10-08 時点で GitHub のソースのみ。
- Qlib v0.9.8 以降はレコーダ成果物の読み込みに `trusted=True` が要る。古い記事の `R.load_object(...)` 例は動かない可能性。
- vectorbt 1.1.2 は `pandas>=3.0.3`、alphalens-reloaded / pyfolio-reloaded は `pandas<3.0`。同じ venv に入れられない。
- 元祖 pandas-ta は消滅。mlfinlab は非 OSS。`ta` の PyPI 版は 2023-11 から更新なし。
- RD-Agent は Linux + Docker 専用。ML4T 第 3 版は Windows ネイティブ非対応。jquants-qlib は Windows 非対応。

**ライセンス**
- `yli188/WorldQuant_alpha101_code`、`popbo/alphas`、`Daic115/alpha191`、`UKI000/JQuants-Forum` はライセンス未記載。コードの複製は避け、論文の式(事実)から自前実装する。
- `id774/finance` は GPL-3 / LGPL-3、`OpenSourceAP/CrossSection` は GPL-2.0。コードを取り込むと派生物に同ライセンスが及ぶ。設計・式・出典の参照に留める。
- vectorbt と PyBroker は「Apache 2.0 + Commons Clause」(販売制限つき)。個人利用は可。
- JKP のデータは CC BY-NC 4.0(非営利)。

**データ(J-Quants、2026-10-13 に公式サイトで確認)**
- Free: 0 円、過去 2 年、**12 週間遅延**、5 回/分。→ 毎日の予測には使えない。
- Light: 月 1,650 円、過去 5 年、60 回/分。Standard: 3,300 円、10 年。Premium: 16,500 円、最大 20 年(前場四本値、配当、財務諸表はここから)。
- アドオン: 分足・ティック(過去 2 年)月 5,500 円、TDnet 開示(過去 5 年)月 11,000 円。Free には付けられない。
- 規約: データを閲覧可能な形で配布・共有することは禁止。**データに基づく分析結果を継続的に第三者へ提供することも禁止**。予測記録を公開する設計にする場合は規約の再確認が必須。
- V1 のリフレッシュトークン方式は 2026-06-01 に廃止(id774/finance の README 記載)。V2 は API キー方式。古い記事・古いコンペ解法の取得コードは動かない。

**統計・設計**
- Qlib のベンチマークは中国 A 株・単一テスト期間。年率超過 9% などの数字を日本株に持ち込まない。
- 日次 IC の現実的な水準は 0.03〜0.05。方向的中率に直すと 50% をわずかに超える程度。**的中率 60% などを目標に置くと、達成できたときはほぼリーク**。
- JPX コンペは上位が単純モデル + 4 位が「運」と明言。3 か月・約 60 営業日の採点では実力差は検出しにくい。
- Alpha101 の成績はコスト控除前・2010〜2013 年・社内データ。個別アルファの成績は非開示。
- Qlib の `Rank` は時系列、WorldQuant の `rank` はクロスセクション。混同すると別の特徴量になる。
- Qlib の `ROC{d}` は「過去 ÷ 現在」。一般的な ROC と符号が逆。
- ローリング演算は `min_periods=1`。上場直後や欠損明けの値は信頼できない。
- Qlib のラベルは「翌日終値→翌々日終値」。本プロジェクトの主対象(寄り→引け)とは別物なので、ラベル式は必ず書き換える。
- `RobustZScoreNorm` などは fit 期間の統計量を全期間に適用する。fit 期間にテスト期間を含めるとリーク。
- 権利落ち日(R2)。配当未調整の価格で特徴量を作ると、権利落ち日に偽の急落が入る。
- 生存バイアス。`instruments/all.txt` に上場廃止銘柄を残す設計にしないと過去成績が上振れる(J-Quants の銘柄マスタが廃止銘柄を返すかは未確認❓)。
- Yahoo Finance の日本株データは Qlib 自身が品質を警告。Qlib の Yahoo 正規化には「前日比 89〜111 倍の値を 100 で割る」という単位誤り補正が入っており、データ源依存の癖が多い。

---

## このプロジェクトへの提案(MVP で採用するもの、後回しにするもの)

### MVP で採用
1. **データ層**: `jquants-api-client`(V2、Apache-2.0)で日足を取得 → 無調整のまま Parquet に追記保存 → 調整は読み出し時に計算(jquants-qlib の設計を写す)。Light プラン(月 1,650 円)を前提にする。
2. **特徴量 v0(日足のみ、前日引け後に確定)**
   - Alpha158 の 158 本をそのまま pandas / polars で再実装(式は本ノートの表)。
   - JPX 2 位の 9 本(20 / 40 / 60 日のリターン・ボラ・MA 乖離)。
   - JPX 5 位の 8 本(2 日リターン、131 日リターン 25 日ラグ、231 日ボラ、11 日平均出来高順位、終値順位、クロスセクション平均 2 本、銘柄コードのカテゴリ)。
   - 夜間・日中分解(R3 用): `gap = 始値 / 前日終値 − 1`、`intraday = 終値 / 始値 − 1` の 5 / 20 / 60 日平均。
3. **ラベル(本プロジェクト用に書き換え。出典の式ではなく提案)**
   - 主: `y = 当日終値 / 当日始値 − 1`(寄り→引け)。予測は前日引け後の情報だけで出す。
   - 副: y からその日の全銘柄平均を引いた超過リターン(JPX 5 位の考え方)。
   - 比較用: Qlib 流の `Ref($close,-2)/Ref($close,-1)-1`。
4. **モデル**: LightGBM 回帰 1 本から始める。初期値は Numerai 流(n_estimators=2000、learning_rate=0.01、max_depth=5、num_leaves=31、colsample_bytree=0.1)と Qlib 流(learning_rate=0.2、max_depth=8、num_leaves=210、強い L1/L2)を両方試す。線形回帰をベースラインに置く(Qlib でも JPX でも線形が健闘)。
5. **検証**: 約 1 年から始めて 1 か月ずつ伸ばす拡張ウィンドウのウォークフォワード(JPX 5 位)。隣接期間のラベル重複がある場合は間引く(Numerai の era 間引き)。
6. **採点(毎営業日、引け後)**: Qlib `calc_ic` の IC と Rank IC、`calc_long_short_return`(上位 20% − 下位 20% の半分)、`calc_long_short_prec`(上位群の上昇率・下位群の下落率 = 方向的中率)、`pred_autocorr`。週次・月次で ICIR(IC 平均 ÷ IC 標準偏差)。機械予測と docs ルール予測を同じ関数で採点し、ルール予測の上乗せ価値は Numerai の `correlation_contribution` の考え方(機械予測に直交化してから相関)で測る。
7. **日次運用**: qlibAssistant の流れを写す(定時実行 → データ同期 → 予測 → 記録 → 過去予測の答え合わせページ)。Windows ではタスクスケジューラ。データ欠落検査は jquants-qlib の `audit` 相当を入れる。
8. **docs ルール予測の型**: 本ノートの R1〜R8 を初期ルール表に入れ、各ルールに「判定データ・入手時刻・確度」を持たせる。R2 は予測ルールではなく前処理規則として登録。

### 2 番目に着手
- Python 3.12 の別 venv に pyqlib 0.9.7 を入れ、自前 Alpha158 と Qlib 出力を突き合わせる(KunQuant が同じ照合をしている)。
- `ml4t-diagnostic` の `analyze_signal`(HAC 補正 t 値)と Deflated Sharpe Ratio を月次レビューに追加。
- `alphalens-reloaded` で特徴量ごとの分位リターンを見て、ルール表の確度を更新する。

### 後回し
- Qlib 本体でのバックテスト・オンライン運用(発注しないので不要)。
- RD-Agent(WSL2 + Docker + LLM 費用)。
- Kronos・TradingAgents(比較対象として面白いが、採点基盤ができてから)。
- 分足特徴(R4、R5、Qlib highfreq)。J-Quants アドオン月 5,500 円を払う判断は、日足 MVP の採点が 3 か月以上回ってから。
- FinRL(強化学習)、tsfresh、vectorbt、Alpha191。

---

## 未追跡の手がかり

- JPX コンペ 6〜10 位の解法 README とノートブックの中身(7 位は `LGBMHierarchModel`。特徴量は未読)。
- JPX コンペの公式評価式(Kaggle ページが開けず)。J-Quants 公式チュートリアルに再掲があるはず。
- `UKI000/JQuants-Forum` の `jquants_uki.pdf` と、SIGNATE ファンダ 1 位解法の Speaker Deck(日本株の値幅予測の特徴量)。
- `iyoda/jquants-qlib` の `docs/`(価格調整式、運用時刻、設定キー)と `pyproject.toml`(pyqlib の版固定)。
- J-Quants V2 日足の正確な列名、更新時刻、銘柄マスタが上場廃止銘柄を含むか。
- jkpfactors.com に日本の因子リターン(日次)があるか。因子定義 PDF(jkpfactors.s3.amazonaws.com/documents/Documentation.pdf)。
- ML4T 第 3 版 `case_studies/nasdaq100_microstructure` の特徴量・ラベル定義(15 分足の設計を日本株に移す材料)。
- 日本株での R3(夜間/日中)、R4(日中モメンタム)、R5(同時刻周期性)の再現研究。JPX ワーキングペーパーや証券アナリストジャーナルを当たる必要あり。
- Asness (2011) の本文、および日本株の短期リバーサルの査読研究。
- GTJA Alpha191 の原典レポート(国泰君安、2017 年)と検証済み実装。
- pyqlib を Python 3.13 でソースビルドできるか(Cython + MSVC)。
- `chenditc/investment_data` の構成(自前の日次データ更新リポジトリの雛形になりうる)。
- `QuantMind`(AGPL-3.0、Qlib + RD-Agent の多市場基盤、1,739★)、`Qbot`(MIT、18,623★)、`edinetdb/dexter-jp`(MIT、312★、日本株の LLM 調査エージェント)の中身。
- vnpy.alpha の Alpha158 実装が Windows + 3.13 で単体利用できるか。
- awesome-systematic-trading の残り(オフセット 200,000 以降)と awesome-quant の後半。

---

## 参照 URL 一覧(✅ / ❓ つき)

**Qlib 本体**
- ✅ https://api.github.com/repos/microsoft/qlib
- ✅ https://raw.githubusercontent.com/microsoft/qlib/main/README.md
- ✅ https://raw.githubusercontent.com/microsoft/qlib/main/pyproject.toml
- ✅ https://raw.githubusercontent.com/microsoft/qlib/main/qlib/contrib/data/loader.py
- ✅ https://raw.githubusercontent.com/microsoft/qlib/main/qlib/contrib/data/handler.py
- ✅ https://raw.githubusercontent.com/microsoft/qlib/main/qlib/contrib/data/highfreq_handler.py
- ✅ https://raw.githubusercontent.com/microsoft/qlib/main/qlib/data/ops.py
- ✅ https://raw.githubusercontent.com/microsoft/qlib/main/qlib/data/dataset/processor.py
- ✅ https://raw.githubusercontent.com/microsoft/qlib/main/qlib/contrib/eva/alpha.py
- ✅ https://raw.githubusercontent.com/microsoft/qlib/main/qlib/contrib/strategy/signal_strategy.py
- ✅ https://raw.githubusercontent.com/microsoft/qlib/main/qlib/constant.py
- ✅ https://raw.githubusercontent.com/microsoft/qlib/main/qlib/config.py
- ✅ https://raw.githubusercontent.com/microsoft/qlib/main/scripts/data_collector/yahoo/collector.py
- ✅ https://raw.githubusercontent.com/microsoft/qlib/main/scripts/data_collector/yahoo/README.md
- ✅ https://raw.githubusercontent.com/microsoft/qlib/main/docs/component/data.rst
- ✅ https://raw.githubusercontent.com/microsoft/qlib/main/docs/component/online.rst
- ✅ https://raw.githubusercontent.com/microsoft/qlib/main/examples/online_srv/update_online_pred.py
- ✅ https://raw.githubusercontent.com/microsoft/qlib/main/examples/benchmarks/README.md
- ✅ https://raw.githubusercontent.com/microsoft/qlib/main/examples/benchmarks/LightGBM/workflow_config_lightgbm_Alpha158.yaml
- ✅ https://github.com/microsoft/qlib/releases
- ✅ https://github.com/microsoft/qlib/issues?q=is%3Aissue+japan (0 件)
- ✅ https://pypi.org/pypi/pyqlib/0.9.7/json
- ❓ https://github.com/chenditc/investment_data (README からの言及のみ)
- ❓ https://github.com/microsoft/qlib-server (検索結果のみ: 400★、push 2025-12-18)

**日本株関連**
- ✅ https://github.com/iyoda/jquants-qlib / https://raw.githubusercontent.com/iyoda/jquants-qlib/dev/README.md
- ✅ https://github.com/J-Quants/jquants-api-client-python
- ✅ https://jpx-jquants.com/en (料金・プラン)
- ✅ https://jpx-jquants.com/en/spec/jquants-cli
- ✅ https://github.com/J-Quants/JPXTokyoStockExchangePrediction (+ `winner-models/1st`〜`5th`、`7th` の README)
- ❓ https://www.kaggle.com/competitions/jpx-tokyo-stock-exchange-prediction (本文取得できず)
- ✅ https://github.com/id774/finance
- ✅ https://github.com/ajtgjmdjp/awesome-japan-finance-data
- ✅ https://github.com/UKI000/JQuants-Forum (ファイル一覧のみ)
- ✅ https://github.com/masahiro-mochizuki/signate-fundamentals-challange-1st-place (README のみ)
- ❓ https://github.com/edinetdb/dexter-jp (検索結果のみ)
- ❓ https://www.jpx.co.jp/english/equities/trading/domestic/01.html (403。立会時間は未確認)

**基盤・書籍コード・LLM 系**
- ✅ https://github.com/microsoft/RD-Agent / https://arxiv.org/abs/2505.15155
- ✅ https://github.com/stefan-jansen/machine-learning-for-trading (+ `/tree/main`)
- ✅ https://github.com/ml4t/engineer / https://pypi.org/pypi/ml4t-engineer/json / https://www.ml4trading.io/docs/engineer/
- ✅ https://github.com/ml4t/diagnostic / https://pypi.org/pypi/ml4t-diagnostic/json
- ✅ https://github.com/numerai/example-scripts / `numerai/hello_numerai.ipynb`(冒頭のみ)/ `numerai/example_model.ipynb`
- ✅ https://raw.githubusercontent.com/numerai/numerai-tools/master/numerai_tools/scoring.py
- ✅ https://github.com/touhoufan2024/qlibAssistant
- ✅ https://github.com/AI4Finance-Foundation/FinRL / https://github.com/AI4Finance-Foundation/FinRL-Trading
- ✅ https://github.com/OpenBB-finance/OpenBB
- ✅ https://github.com/shiyu-coder/Kronos
- ✅ https://github.com/TauricResearch/TradingAgents
- ✅ https://github.com/RL-MLDM/alphagen
- ✅ https://github.com/vnpy/vnpy
- ✅ https://github.com/edtechre/pybroker
- ❓ https://github.com/UFund-Me/Qbot 、https://github.com/qusong0627/QuantMind (検索結果のみ)

**特徴量・指標・分析**
- ✅ https://arxiv.org/abs/1601.00991 / https://arxiv.org/pdf/1601.00991 (PDF 本文抽出)
- ✅ https://github.com/yli188/WorldQuant_alpha101_code
- ✅ https://github.com/Menooker/KunQuant
- ✅ https://github.com/popbo/alphas 、https://github.com/Daic115/alpha191
- ❓ https://github.com/STHSF/alpha101 (検索結果のみ: 189★、MIT)
- ✅ https://github.com/TA-Lib/ta-lib-python / https://pypi.org/pypi/TA-Lib/json
- ✅ https://github.com/xgboosted/pandas-ta-classic / https://pypi.org/pypi/pandas-ta-classic/json
- ✅ https://github.com/twopirllc/pandas-ta (404 を確認)
- ✅ https://api.github.com/repos/bukosabino/ta / https://pypi.org/pypi/ta/json
- ✅ https://api.github.com/repos/blue-yonder/tsfresh / https://pypi.org/pypi/tsfresh/json
- ✅ https://api.github.com/repos/polakowo/vectorbt / https://pypi.org/pypi/vectorbt/json
- ✅ https://github.com/stefan-jansen/alphalens-reloaded / https://pypi.org/pypi/alphalens-reloaded/json
- ✅ https://api.github.com/repos/stefan-jansen/pyfolio-reloaded / https://pypi.org/pypi/pyfolio-reloaded/json
- ✅ https://api.github.com/repos/ranaroussi/quantstats / https://pypi.org/pypi/quantstats/json
- ✅ https://pypi.org/pypi/lightgbm/json
- ✅ https://github.com/wukan1986/polars_ta
- ✅ https://github.com/hudson-and-thames/mlfinlab
- ✅ https://github.com/baobach/mlfinpy 、https://github.com/RiskLabAI/RiskLabAI.py 、https://finmlkit.readthedocs.io/en/latest/
- ❓ https://github.com/eslazarev/purged-cross-validation (検索結果と awesome-quant の記載のみ)

**因子定義・論文**
- ✅ https://github.com/OpenSourceAP/CrossSection
- ✅ https://github.com/bkelly-lab/ReplicationCrisis 、https://github.com/bkelly-lab/jkp-data
- ❓ https://jkpfactors.com (未訪問)
- ✅ Gao, Han, Li, Zhou (2018) DOI 10.1016/j.jfineco.2018.05.009 (Semantic Scholar API で要旨)
- ✅ Lou, Polk, Skouras (2019) DOI 10.1016/j.jfineco.2019.03.011 (同上)
- ✅ Heston, Korajczyk, Sadka (2010) DOI 10.1111/j.1540-6261.2010.01573.x (同上)
- ✅ Gu, Kelly, Xiu (2020) DOI 10.1093/rfs/hhaa009 (Crossref API で要旨)
- ✅ Jensen, Kelly, Pedersen (2023) DOI 10.1111/jofi.13249 (Crossref API で要旨)
- ❓ Asness (2011) DOI 10.3905/jpm.2011.37.4.067 (書誌のみ確認、要旨は取得できず)

**まとめリスト**
- ✅ https://raw.githubusercontent.com/wilsonfreitas/awesome-quant/master/README.md (先頭 10 万字)
- ✅ https://github.com/georgezouq/awesome-ai-in-finance
- ✅ https://github.com/paperswithbacktest/awesome-systematic-trading (0〜20 万字)

**検索(実施分)**
- ✅ WebSearch「Qlib 日本株 使い方 データ J-Quants dump_bin」
- ✅ WebSearch「qlib Japan stock market data collector region jp Nikkei TOPIX github」
- ✅ GitHub API 検索: `qlib japan OR jquants OR 日本株`、`jquants`、`pandas-ta`、`alpha101 OR "101 formulaic alphas" OR alpha191`、`mlfinlab OR mlfinpy OR "advances in financial machine learning"`、`qlib jquants`
- ✅ GitHub サイト内検索: `qlib (japan OR japanese OR nikkei OR topix OR tse OR 日本株)`(751 件、Japan を明示するものは jquants-qlib のみ)
- ❌ 以降の WebSearch は共有上限により実行不可
