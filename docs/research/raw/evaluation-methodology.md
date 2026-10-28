# 手法: 予測の採点・統計的検定・過学習防止・改ざん不能な記録

> 調査日: 2026-10-13 / 観点: evaluation-methodology / 状態: 一次調査(未検証)

> 注意: これは調査メモであり投資助言ではない。数値は出典つきの報告値か、本ノート内で明示した自前計算(Python 3.13.5 + numpy/scipy で実行確認済み)のどちらか。「設計案」と書いた閾値は文献の引用ではなく、検定力計算から導いた本ノートの提案。
> 調査上の制約: WebSearch は 21 回実行した時点でセッション共有の上限に達した(日本語クエリは 1 回のみ成功)。以降は既知 URL への WebFetch(約 60 件)で一次ソースを確認した。日本語圏の先行事例(Qiita/Zenn/note の実装記事など)の探索は不十分で、「未追跡の手がかり」に残した。

## 結論(5〜10 行)

1. **採点は「適切なスコア規則 + ベースライン比 + 日単位の集計」に固定する。** 主指標は Brier score と log loss、補助に的中率・RPS(五分位)・日次ランク IC・紙上スプレッドリターン。基準はコイン(p=0.5、Brier 0.25)と基準率。M6 コンペでは「全五分位に 0.2 を置くだけ」のベンチマーク(RPS 0.16)に勝てたチームは 23.3%(163 中 38)、改善幅も 2.5% 未満だった。**ベースラインに勝つこと自体が難しい**という前提で設計する。
2. **独立な標本単位は「予測 1 件」ではなく「営業日」。** 同じ日の銘柄間には相関があり、実効サンプルは n_eff = n / (1 + (n−1)ρ)。自前シミュレーションでは、日内相関 ρ=0.05 のとき予測 1 件単位の逐次検定は帰無仮説下で 20.9% 誤って昇格させた(名目 5%)。日単位の賭け型 e-process は 2.8〜4.1% に収まった。
3. **昇格の最小サンプルは「60 営業日かつ 300 件以上」、判定式は日単位 e-process E ≥ 20(α=0.05)。** 的中率 55% の予測器は 1 日 20 銘柄で中央値 55〜67 営業日、53% は 101〜155 営業日で昇格に届く(自前シミュレーション)。固定標本なら 55% の検出に 654 件、53% に 1,773 件、52% に 3,945 件必要(片側 5%、検出力 80%、厳密二項)。
4. **1 日 20〜30 銘柄を「ユニバース中央値に対する相対方向」で予測する**のが標本効率の最適点。絶対方向(上がる/下がる)は地合いで相関するので、何銘柄増やしても n_eff は 1/ρ(ρ=0.3 なら約 3 件/日)で頭打ちになる。
5. **多重検定を放置すると必ず「偽の当たりルール」が出る。** 20 本のルールを各 250 件で比べると、全部が無能でも最良の 1 本の期待的中率は 56.0% になる(E[max z]=1.90)。試したルール変種はすべて台帳に残し、e-BH(FDR 10%)か Deflated Sharpe Ratio で割り引く。
6. **改ざん防止は 3 層で足りる。** (L0) ハッシュチェーン付き追記専用 JSONL、(L1) 毎朝のローカル git コミット、(L2) 先頭ハッシュの外部アンカー(RFC 3161 の FreeTSA が即時・秒精度、OpenTimestamps は数時間後に Bitcoin で確定)。git のコミット日時は環境変数で自由に書けるので、L1 だけでは証明にならない。
7. **写せるライブラリは揃っている。** purgedcv(MIT、PurgedKFold/CPCV/DSR/PBO)、skfolio(BSD-3)、arch(SPA/StepM/MCS)、scikit-learn(Brier/較正曲線)、scipy/statsmodels(BH 法)、dieboldmariano。mlfinlab は「all rights reserved」になっており写せない。pypbo は AGPL、expectation は GPL-3.0、confseq は Windows 用 wheel が無い。
8. **LLM に docs を読ませる (b) 系の予測は、過去日付でのバックテストを証拠にしない。** 学習データに答えが入っている可能性があるため、モデルの知識カットオフ以降の前向き記録だけを採点対象にする(Glasserman & Lin 2023、Halawi et al. 2024、ForecastBench の設計)。
9. **事前確率は低く置く。** 台湾の全デイトレーダーのうち手数料後に安定して勝てるのは 1% 未満(Barber et al. 2014)、ブラジルで 300 日以上続けた人の 97% が損失(Chague et al. 2020)。このシステムの価値は「勝てること」より先に「勝てていないことを早く正しく知ること」にある。

## 丸パクリ候補(優先度順の表)

| # | 名前 | URL | 種別 | ライセンス | 鮮度 | 何をどう写すか | 確認 |
|---|---|---|---|---|---|---|---|
| 1 | 本ノートの `ledger.py` / `scoring.py`(下の「詳細」に全文) | (本ファイル) | 自前コード | (自作) | 2026-10-13 実行確認 | そのまま `src/` に置く。stdlib + numpy + scipy のみ。ハッシュチェーン、Brier/logloss/RPS/Murphy 分解/PT 検定/日ブロック bootstrap/日内置換検定/e-process(日単位・予測単位)/e-BH/SPRT/ベータ事後/ICC/PSR/DSR/MinTRL | ✅ 実行確認 |
| 2 | M6 competition の採点仕様 | https://arxiv.org/abs/2310.13357 | 論文 | arXiv | 2023-10 投稿 | 五分位確率の RPS 式、同順位の按分、一様ベンチマーク 0.16、IR = 年率対数リターン / 年率日次標準偏差、4 週ごと 12 回提出、100 資産。日次版に縮小して使う | ✅ |
| 3 | purgedcv (eslazarev/purged-cross-validation) | https://github.com/eslazarev/purged-cross-validation | repo / PyPI | MIT | v0.1.10 (2026-10-01)、初版 2026-05-16、55 stars、Python ≥3.10(バッジは 3.13/3.14 対応) | `pip install purgedcv`。`PurgedKFold(n_splits, prediction_times, evaluation_times, purge_horizon, embargo)`、`CombinatorialPurgedCV(n_splits=6, n_test_groups=2, ...).backtest_paths(est, X, y)`、`WalkForwardSplit(window="expanding")`、`probabilistic_sharpe_ratio`、`min_track_record_length(observed_sharpe, target_sharpe, alpha, skew, kurtosis)`、`deflated_sharpe_ratio`、`probability_of_backtest_overfitting`、`effective_n_trials`、`optuna_integration.TrialSharpeRecorder` | ✅(新しいライブラリなので自前実装と突き合わせる) |
| 4 | skfolio | https://github.com/skfolio/skfolio | repo | BSD-3-Clause | 2,490 stars、push 2026-10-12 | `CombinatorialPurgedCV(n_folds=10, n_test_folds=8, purged_size=0, embargo_size=0)`、`WalkForward(test_size, train_size, expand_train, purged_size)`。purged_size は 1 以上(執行遅延の楽観バイアス回避)と公式に注記あり | ✅ |
| 5 | arch (bashtage) `arch.bootstrap` | https://arch.readthedocs.io/en/latest/multiple-comparison/generated/arch.bootstrap.SPA.html | ライブラリ | NCSA | PyPI 最新 8.0.0、Python ≥3.10 | `SPA(benchmark, models, block_size=None, reps=1000, bootstrap='stationary', studentize=True)`(入力は**損失**)。`.compute()`→`.pvalues`(lower/consistent/upper)。同モジュールに `StepM`、`MCS(losses, size=0.05, method='R')`、`RealityCheck`。日次平均 Brier を損失列にして複数モデルを一括比較 | ✅(例コードは公式ページに無し) |
| 6 | scikit-learn | https://scikit-learn.org/stable/modules/generated/sklearn.metrics.brier_score_loss.html | ライブラリ | BSD-3 | docs 1.9.1 | `brier_score_loss(y_true, y_proba, scale_by_half='auto')`、`calibration_curve(y_true, y_prob, n_bins=5, strategy='uniform'|'quantile')`、`TimeSeriesSplit(n_splits, test_size, gap)` | ✅ |
| 7 | FreeTSA (RFC 3161) | https://freetsa.org/index_en.php | 無料サービス | (利用規約の明文なし) | 証明書 2026-03-16 更新、タイムスタンプ有効期限 2040-02 | `openssl ts -query -data F -no_nonce -sha512 -cert -out F.tsq` → `curl -H "Content-Type: application/timestamp-query" --data-binary '@F.tsq' https://freetsa.org/tsr > F.tsr` → `openssl ts -verify -in F.tsr -queryfile F.tsq -CAfile cacert.pem -untrusted tsa.crt`。この PC の Git Bash に openssl 3.2.4 と curl あり | ✅ ページ確認(実送信は未実行) |
| 8 | OpenTimestamps (JS クライアント) | https://github.com/opentimestamps/javascript-opentimestamps | repo / npm | LGPL-3.0 | 149 stars、550 commits(最終日付は未確認) | `npm install -g opentimestamps` → `ots-cli.js stamp -d <sha256>`(ファイルでなくハッシュを直接刻める)→ 数時間後 `upgrade` → `verify`。**ローカル Bitcoin ノードが無くてもブロックエクスプローラで検証できる** | ✅ |
| 9 | OpenTimestamps (Python クライアント) | https://github.com/opentimestamps/opentimestamps-client | repo / PyPI | GitHub 表示は "Other"(種別未確認) | 425 stars、push 2026-02-07 | `pip3 install opentimestamps-client` → `ots stamp F` / `ots upgrade F.ots` / `ots verify F.ots`。**検証にはローカルの Bitcoin Core ノード(pruned 可)が必要**。git 連携は `git config --global gpg.program <ots-git-gpg-wrapper.sh>` で署名コミットに自動付与。Windows での動作は未確認 | ✅(Windows 動作 ❓) |
| 10 | scipy / statsmodels の多重検定補正 | https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.false_discovery_control.html | ライブラリ | BSD-3 | statsmodels docs 0.15.0 | `scipy.stats.false_discovery_control(ps, method='bh'|'by')`、`statsmodels.stats.multitest.multipletests(pvals, alpha, method='holm'|'fdr_bh'|'fdr_by')`。相関のある検定には 'by' | ✅ |
| 11 | Deflated Sharpe Ratio(論文の式と数値例) | https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf | 論文 | - | 2014 | E[max SR] ≈ √V·[(1−γ)Φ⁻¹(1−1/N) + γΦ⁻¹(1−1/(Ne))]、DSR = PSR(SR₀)。数値例(年率 SR 2.5、N=100、V=1/2、T=1250、歪度 −3、尖度 10 → SR₀=0.1132、DSR=0.9004)を自前コードで再現済み。単体テストの期待値に使う | ✅ PDF 本文 + 再計算 |
| 12 | PBO / CSCV(論文のアルゴリズム) | https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf | 論文 | - | 2015 頃 | T×N の成績行列を S 個(例 16)に等分 → 半分を IS、残りを OOS にする全組合せで「IS 最良の OOS 相対順位」のロジットを集め、ロジット ≤ 0 の割合が PBO。論文は PBO > 0.05 で棄却を「慣例的」として挙げる | ✅ PDF 本文 |
| 13 | zoonek/2025-sharpe-ratio | https://github.com/zoonek/2025-sharpe-ratio | repo | 表示なし(未確認) | 103 stars、71 commits | López de Prado, Lipton, Zoonekynd "How to Use the Sharpe Ratio" の公式コード。`functions.py` に共通関数とテスト、Exhibit 別ノートブック(PSR / FWER / FDR / SFDR / クラスタ数)。ライセンス不明なので式だけ写す | ✅ ページ確認(関数名 ❓) |
| 14 | quantskills/skill-backtest-overfit | https://github.com/quantskills/skill-backtest-overfit | repo(エージェント用スキル) | GPL-3.0 | 40 stars、push 2026-07-16 | `SKILL.md` + `scripts/overfit_report.py --returns selected.csv --trials trials.csv --n-trials 200 --out report.json`、`references/methodology.md`、`references/anti-patterns.md`。判定は DSR ≥ 0.95 で PASS。README の合成例: 200 本のノイズ戦略の最良は年率 SR 1.65 でも DSR 0.63(FAIL)、PBO 0.34、ヘアカット −61%。docs の「過学習チェック手順」の雛形として構成を真似る(GPL なのでコードの転載は避ける) | ✅ |
| 15 | Harvey & Liu "Backtesting" のヘアカット Sharpe | https://people.duke.edu/~charvey/Research/Published_Papers/P120_Backtesting.PDF | 論文 | - | 2015 (JPM) | SR→t 値→p 値→多重検定補正(Bonferroni / Holm / BHY)→補正 p から逆算した SR がヘアカット SR。例: 月次 240 か月、年率 SR 0.75 は単独なら p=0.0008、試行 200 なら補正 p=0.15、補正 SR 0.32(約 60% 減)。一律 50% 引きは誤りで、弱い SR ほど強く削られる | ✅ PDF 本文 |
| 16 | dieboldmariano | https://pypi.org/project/dieboldmariano/ | PyPI | MIT | v1.1.0 (2025-01-09) | `dm_test(V, P1, P2, loss=..., h=1, one_sided=False, harvey_correction=True)`。2 つの予測器の日次平均損失差の検定 | ✅ PyPI JSON |
| 17 | JPX Tokyo Stock Exchange Prediction の評価指標 | https://zenn.dev/gamella/articles/eaf7fe5a96bdf0 | 記事(設計者本人) | - | 2022 コンペ | 約 2,000 銘柄を順位づけ、上位 200 と下位 200 に順位に応じた線形ウェイト(2〜1)を掛けた日次スプレッドリターン R_day = S_up − S_down、スコア = mean(R_day)/std(R_day)。目的変数は翌日終値→翌々日終値。自分の版は「上位 k − 下位 k」に縮小 | ✅(ウェイトの向きは記事内で表記揺れ、公式ルール ❓) |
| 18 | Numerai CORR | https://docs.numer.ai/numerai-tournament/scoring/correlation-corr | docs | - | 2026 時点で公開 | 予測を順位化→正規分位に変換→符号付き 1.5 乗、目的変数は中心化→1.5 乗、両者の Pearson 相関。裾を重く見るランク相関。CORR20V2 / CORR60 などの変種あり | ✅(MMC の式 ❓) |
| 19 | expectation (jakorostami) | https://github.com/jakorostami/expectation | repo / PyPI | GPL-3.0 | v0.6.1、90 stars | `SequentialTesting(test_type="proportion"|"mean", null_value, alternative)`、`.update(batch)` → `e_value` / `reject_null`、`e_bh()` / `e_bonferroni()`。API は 1.0 前で変わりうる。GPL なので依存として使うだけに留める | ✅ |
| 20 | Choe & Ramdas "Comparing Sequential Forecasters" + comparecast | https://github.com/yjchoe/ComparingForecasters | 論文 + repo | MIT | comparecast 1.0.0 (2023-10-24)、11 stars | `cc.compare_forecasts(data, "A", "B", scoring_rule="brier", alpha=0.05, compute_cs=True, compute_e=True)` → 信頼列(lcb/ucb)と e 値。**依存の confseq 0.0.11 は Windows 用 wheel が無い**(macOS/Linux のみ、C++14 + Boost 要)。Windows では考え方だけ写して自前実装(本ノートの `e_process_daily`)を使う | ✅ |
| 21 | ForecastBench の運用設計 | https://www.forecastbench.org/ | ベンチマーク | サイトは CC BY-SA 4.0 | 2026 年も更新中 | 「締切時点で答えが存在しない問いだけを出す」「質問セットは締切 10 日前に凍結」「締切 23:59:59 UTC」「順位が安定するまで約 50 日」「難易度調整 Brier」。自分の締切(08:50 JST)と凍結ルールの書き方を真似る | ✅(難易度調整式 ❓) |
| 22 | agent-backtest-lab (bettyguo) | https://github.com/bettyguo/agent-backtest-lab | repo | Apache-2.0 | 7 stars、23 commits | LLM 売買エージェントの監査層。`as_of` より後のデータを拒否するファイアウォール、yfinance の Adj Close 拒否、DSR/PSR/BH/BY/Holm/Romano-Wolf/SPA、PBO、ECE、6 種のベースライン常時表示。`pip install agent-backtest-lab` → `abl evaluate buy_and_hold --window 2020-01-06..2024-12-31 --out out/`。小規模なので設計(チェック項目の一覧)を写す | ✅ |
| 23 | rfc3161-client (Trail of Bits) | https://pypi.org/project/rfc3161-client/ | PyPI | Apache-2.0 | 最新 1.0.9、Python ≥3.9 | openssl コマンドを Python に置き換えたい場合の RFC 3161 実装。win_amd64 の abi3 wheel は 1.0.2 まで確認 | ✅(1.0.9 の wheel 一覧は未確認) |
| 24 | pypbo (esvhd) | https://github.com/esvhd/pypbo | repo | **AGPL-3.0** | 143 stars、push 2026-07-06 | `pbo.pbo(rtns_df, S=16, metric_func=..., threshold=1, n_jobs=4, plot=True)`。PSR / MinTRL / MinBTL / DSR も同梱。statsmodels 0.8.0 固定という古い依存。AGPL なので読むだけにして purgedcv か自前実装を使う | ✅ |
| 25 | Baron et al. の extremizing 変換 | https://faculty.wharton.upenn.edu/wp-content/uploads/2015/07/2015---two-reasons-to-make-aggregated-probability-forecasts_1.pdf | 論文 | - | 2014 (Decision Analysis 11(2)) | t(p) = p^a / (p^a + (1−p)^a)。図の例は a=2.5。a>1 で極端化、a<1 で縮小。地政学予測の平均では a>1 が最適だったが、著者自身が「a<1 が最適な場合もある」と書いている。金融は M6 の結果から a<1(縮小)側を初期値にする | ✅ PDF 本文 |
| - | (写せない)mlfinlab | https://github.com/hudson-and-thames/mlfinlab | repo | all rights reserved | 4,939 stars、最終 push 2023-10-02 | 公開リポジトリは issue 受付用。Business / Enterprise ライセンス制。**コードを写さない** | ✅ |

## 詳細

### 1. 採点仕様の具体案(必答 1)

#### 1.1 予測レコード(1 行 = 1 予測)

| 項目 | 例 | 意味 |
|---|---|---|
| target_date | 2026-10-14 | 採点対象の営業日 |
| ticker | 7203.T | 銘柄 |
| predictor | `rule:gap_fade@<docsのgit blobハッシュ>` / `ml:lgbm_v3@<モデルハッシュ>` / `base:coin` | 予測器 ID。ルール文書やモデルの版を必ず含める |
| target | `oc_rel_median` | 目的変数の定義 ID(下記 T1〜T3) |
| p_up | 0.56 | 確率。0.02〜0.98 に制限(log loss の発散防止) |
| q5 | [0.15,0.2,0.2,0.2,0.25] | 任意。五分位確率(T3) |
| data_cutoff | 2026-10-14T08:30+09:00 | 使ったデータの最終時刻 |
| llm | モデル ID、プロンプトのハッシュ、temperature | LLM 予測のみ。出力全文は別ファイルに保存しハッシュを記録 |
| abstain | false | 見送りも 1 行として記録する |

締切は寄り付き前(設計案: 08:50 JST)。締切後に追記された行は自動で「late」とし採点対象外にする。

#### 1.2 目的変数(解決基準を事前に固定する)

- **T1(主)相対方向**: 当日の (終値/始値 − 1) が、事前登録したユニバースの同日中央値を上回れば 1。基準率が構造的に 0.5 になり、地合いの影響が消える。
- **T2(副)絶対方向**: 終値 > 始値なら 1、同値は 0.5 点扱い。基準率が 0.5 からずれるので基準率ベースラインが必須。
- **T3(任意)五分位**: ユニバース内の寄り→引けリターン順位の五分位。M6 と同じ RPS で採点。
- 例外規定(設計案): 始値 = 当日立会の最初の約定値。終日約定なしは void。void は削除せず `void` レコードを追記し、件数をダッシュボードに出す。株式分割は同日内リターンに影響しないので調整不要。

#### 1.3 指標

| 指標 | 式 | 基準値 |
|---|---|---|
| Brier score (BS) | mean (p − y)² | コイン 0.25 |
| Brier skill score (BSS) | 1 − BS / BS_ref | 0 より上が基準超え |
| log loss | −mean[y ln p + (1−y) ln(1−p)] | コイン ln 2 = 0.6931 |
| 的中率 | mean 1{(p>0.5) = y} | 0.5 |
| RPS(M6 式) | 資産ごとに (1/5) Σ_j (Σ_{k≤j} q_k − Σ_{k≤j} f_k)²、資産平均 | 一様 0.16 |
| Murphy 分解 | BS = REL − RES + UNC | REL 小・RES 大が良い |
| 日次ランク IC | その日の p と実現リターンの Spearman 相関 | 0 |
| 紙上スプレッド | 上位 k の平均リターン − 下位 k の平均リターン(bp/日)、mean/std | 0 |
| PSR / DSR | 下記 3.2 | 0.95 |

的中率 55% で p=0.55/0.45 と正直に申告した場合の BS は 0.2475(BSS = 1.0%)。**BSS が 1% 動くだけで大きな差**という尺度感を持つこと(自前計算)。

M6 の RPS 定義(論文で確認): 実現リターンを 1〜5 の五分位に順位づけ(各 20 資産)。境界の同順位は平均順位で按分(例: 18 位に 4 資産が並ぶと順位 4.75、q = (0,0,0,0.25,0.75))。IR は年率化した対数リターン ÷ 年率化した日次標準偏差で、ベンチマークは 100 資産の等ウェイト(Global IR 0.453)。

#### 1.4 ベースライン(同じ台帳に予測器として毎日記録する)

| ID | 中身 | 目的 |
|---|---|---|
| base:coin | p = 0.5 | BS 0.25 / RPS 0.16 の基準。M6 でほとんどのチームが負けた相手 |
| base:rate | p = 直近 250 営業日の上昇割合(T2 用) | 基準率を知っているだけの人 |
| base:persist | 前日の寄り→引けが上なら p=0.55、下なら 0.45 | 持続 |
| base:reverse | persist の逆 | 反転 |
| base:always_up | 全銘柄 p=0.55 | 「常に上」。T2 でのみ意味がある |
| base:shuffle | 自分の予測を日内で銘柄間シャッフル | 自分の確率分布を保った無能な自分。日内置換検定の帰無分布 |

#### 1.5 集計単位

- 保存は予測 1 件単位。**推論(検定・信頼区間)は日単位**: d_t = その日の平均 (BS_ref − BS_model)。
- 窓: 直近 20 / 60 / 250 営業日と通算。
- 軸: 予測器別、ルール別、確信度バケット別(0.50–0.55 / 0.55–0.60 / 0.60 以上と対称側)、地合い別(TOPIX の寄り→引けの符号、ボラ高低)、イベント日別(決算、SQ、権利落ち)、セクター・流動性別。
- 切り口を増やすほど多重検定になる。切り口別の数字は「診断用」と明記し、昇格判定には使わない。

#### 1.6 ダッシュボード項目

1. 完全性: 今日の予測件数、締切遵守(ts < 08:50)、チェーン検証 OK、アンカー状態(git コミット、TSA トークン検証、OTS upgrade 済み)、late / void 件数。
2. カバレッジ: 予測件数 / ユニバース、見送り率。
3. スコア表: 予測器 × {BS, BSS(対コイン、対基準率), log loss, 的中率(Wilson 区間), RPS, 平均 IC, 紙上スプレッド bp/日, PSR}。ベースライン行を必ず並べる。
4. 差の区間: 日次平均スコア差の 90% ブロック bootstrap 区間。
5. 較正: 信頼性曲線、ECE、REL / RES / UNC、確率のヒストグラム。
6. 逐次の証拠: 予測器・ルールごとの e 値(log10 表示、閾値 20)、SPRT の状態、縮小後の的中率と P(p>0.5)。
7. 標本会計: n、営業日数 D、推定 ρ、n_eff、「53% / 55% 検出に必要な件数」に対する進捗。
8. 多重検定: 生存ルール数 m、登録済み試行数 N、現在の n における「無能でも出る最良的中率」、e-BH の棄却リスト。
9. ドリフト: 直近 60 日の的中率と通算の差、昇格・降格の履歴。

### 2. 昇格・降格の最小サンプルと判定式(必答 2)

#### 2.1 固定標本の必要件数(自前計算、厳密二項、片側、H0: p=0.5)

| 真の的中率 | 51% | 52% | 53% | 54% | 55% | 56% | 58% | 60% |
|---|---|---|---|---|---|---|---|---|
| α=0.05、検出力 0.8 | 15,605 | 3,945 | 1,773 | 1,008 | 654 | 457 | 258 | 169 |
| α=0.05、検出力 0.9 | 21,557 | 5,435 | 2,435 | 1,381 | 891 | 623 | 348 | 224 |
| α=0.01、検出力 0.8 | 25,233 | 6,351 | 2,848 | 1,607 | 1,028 | 720 | 411 | 261 |
| α=0.0025(20 本 Bonferroni)、検出力 0.8 | 33,445 | 8,401 | 3,758 | 2,121 | 1,359 | 948 | 539 | 346 |

件数は**独立な予測**の数。同日多銘柄なら n_eff に読み替える。

#### 2.2 棄却に必要な的中数(自前計算、片側)

| n | α=0.05 | α=0.01 | α=0.0025 |
|---|---|---|---|
| 100 | 59 (59.0%) | 63 (63.0%) | 65 (65.0%) |
| 200 | 113 (56.5%) | 117 (58.5%) | 121 (60.5%) |
| 300 | 165 (55.0%) | 171 (57.0%) | 175 (58.3%) |
| 500 | 269 (53.8%) | 277 (55.4%) | 282 (56.4%) |
| 1,000 | 527 (52.7%) | 538 (53.8%) | 545 (54.5%) |
| 2,000 | 1,038 (51.9%) | 1,053 (52.6%) | 1,064 (53.2%) |
| 3,000 | 1,546 (51.5%) | 1,565 (52.2%) | 1,578 (52.6%) |

300 件未満では 55% 出ていても有意にならない。これが「最小 300 件」の根拠。

#### 2.3 多重比較で「無能でも出る最良成績」(自前計算、Bailey & López de Prado の E[max] 式)

| 比べた本数 N | E[max z] | 各 100 件 | 各 250 件 | 各 500 件 | 各 1,000 件 |
|---|---|---|---|---|---|
| 5 | 1.19 | 56.0% | 53.8% | 52.7% | 51.9% |
| 10 | 1.57 | 57.9% | 55.0% | 53.5% | 52.5% |
| 20 | 1.90 | 59.5% | 56.0% | 54.3% | 53.0% |
| 50 | 2.28 | 61.4% | 57.2% | 55.1% | 53.6% |
| 100 | 2.53 | 62.7% | 58.0% | 55.7% | 54.0% |
| 1,000 | 3.26 | 66.3% | 60.3% | 57.3% | 55.2% |

表の % は「全ルールが的中率 50% でも、最良 1 本に期待される的中率」。月間ランキング 1 位のルールを信じてはいけない理由。

#### 2.4 逐次検定(毎日見てよい検定)

**(a) 日単位の賭け型 e-process(主判定、設計案)**
x_t = その日の的中割合 − 0.5(範囲 [−0.5, 0.5])。E_D = mean_λ Π_{t≤D} (1 + λ x_t)、λ ∈ {0.25, 0.5, 1.0, 1.5, 1.9}。H0「過去を条件に E[x_t] ≤ 0」の下で非負の優マルチンゲールになり、Ville の不等式から **E_D ≥ 1/α = 20 に一度でも達したら α=0.05 で棄却**。日内の相関がどうであっても有効(1 日 = 1 回の賭けだから)。理論の出典は Ramdas, Grünwald, Vovk, Shafer (2022) と Waudby-Smith & Ramdas(未開封)、予測器比較への応用は Choe & Ramdas (Operations Research)、Henzi & Ziegel (2021)。

自前シミュレーション(1 日 20 銘柄、750 営業日、2,000 回、ベータ二項で日内相関を付与):

| 真の的中率 | 日内相関 ρ | 日単位 e-process: 棄却率 / 中央値 | 予測単位の素朴な e-process: 棄却率 / 中央値 |
|---|---|---|---|
| 50% | 0 | 2.8% / - | 3.7% / - |
| 50% | 0.05 | 2.8% / - | **20.9%** / - |
| 50% | 0.2 | 4.1% / - | **54.2%** / 294 日 |
| 55% | 0 | 100% / 55 日 | 100% / 29 日 |
| 55% | 0.05 | 100% / 67 日 | 100% / 22 日 |
| 55% | 0.2 | 99.8% / 145 日 | (無効) |
| 53% | 0 | 100% / 101 日 | 100% / 83 日 |
| 53% | 0.05 | 99.8% / 155 日 | (無効) |
| 55%(30 銘柄/日) | 0.05 | 100% / 62 日 | (無効) |
| 53%(30 銘柄/日) | 0.02 | 100% / 100 日 | (無効) |

予測単位の検定は速く見えるが、相関があると偽陽性が 4〜10 倍になる。**日単位を主判定にする。**

**(b) Wald の SPRT(早期打ち切りの目安、独立な予測に対して)** H0: p=0.5 対 H1: p=p1、α=0.05、β=0.20。上側閾値 ln((1−β)/α)=2.773、下側 ln(β/(1−α))=−1.558。的中で +ln(p1/0.5)、外れで +ln((1−p1)/0.5) を足す。

| p1 | 的中の加点 | 外れの減点 | 平均必要件数(H1 が真) | 同(H0 が真) |
|---|---|---|---|---|
| 0.53 | +0.0583 | −0.0619 | 1,058 | 744 |
| 0.55 | +0.0953 | −0.1054 | 381 | 267 |
| 0.58 | +0.1484 | −0.1744 | 148 | 103 |
| 0.60 | +0.1823 | −0.2231 | 95 | 66 |

注意: β=0.20 は「本当に 55% のルールを 20% の確率で捨てる」設定(400 回の検算で昇格 79.5% / 打ち切り 20.5%)。降格に使うなら β=0.10(下側 −2.251、平均 396〜474 件)にする。

**(c) ベータ二項の事後分布(重みづけと表示用、設計案)** 懐疑的な事前分布 Beta(100,100)(的中率の 95% が 0.43〜0.57 に入る想定)。縮小推定値 = (100+k)/(200+n)。例: 300 件中 165(55%)→ 0.530、P(p>0.5)=0.910。500 件中 275 → 0.536、0.971。1,000 件中 540 → 0.533、0.990。2,000 件中 1,060 → 0.527、0.995。

#### 2.5 状態遷移と判定式(設計案)

`登録 → shadow(記録のみ) → candidate → active → probation → retired`

| 遷移 | 条件(すべて満たす) |
|---|---|
| 登録 → shadow | ルール文書(IF / THEN / 根拠 / 無効条件)がコミット済みで、試行台帳に 1 行追加済み |
| shadow → candidate | 40 営業日以上かつ 200 件以上。チェーン欠損なし。較正の粗検査: 使用バケット(100 件以上)で |平均 p − 実現頻度| ≤ 0.03 |
| candidate → active | (1) **60 営業日以上かつ 300 件以上**、(2) 日単位 e-process **E ≥ 20**。複数を同時審査するなら e-BH: e 値を降順に並べ、e_(k) ≥ m/(0.10·k) を満たす最大の k までを昇格(FDR 10%)、(3) 日次平均 (BS_coin − BS) の 90% ブロック bootstrap 区間の下限 > 0、(4) 損益に使うなら紙上スプレッド(想定コスト控除後)の PSR ≥ 0.90、試行数で割り引いた DSR ≥ 0.95 |
| active → probation | 直近 60 営業日の的中率 ≤ 49%、または同期間の日次平均 BSS < 0。probation 中はアンサンブルの重み 0 で記録は継続 |
| probation → retired | probation 入りから 120 営業日たっても日次 x_t の累積平均が 0 以下、または直近 500 件(n_eff 換算)で一様事前の P(p>0.5) < 0.05(500 件なら的中 231 以下 = 46.2%) |
| probation → active | probation 入り後のデータだけで E ≥ 20 を再達成 |

補足:
- 発火頻度が低いルール(1 日 5 件未満)は単独で 300 件に届くまで半年以上かかる。ルール族でまとめて審査し、個別ルールは縮小推定で重みづけする。
- 的中率が 44% のような「逆に当たる」ルールは自動で反転させない。反転版を**新しい試行**として登録し、ゼロから数える。
- 一様事前での降格の目安(自前計算): 直近 200 件で的中 94 以下(47.0%)なら P(p>0.5) < 0.2、88 以下(44.0%)なら < 0.05。300 件なら 142 以下 / 135 以下。500 件なら 240 以下 / 231 以下。

### 3. 過学習防止の道具

#### 3.1 パージ付き CV・エンバーゴ・CPCV(ML モデルの選定用)

- パージ: テスト区間のラベルと時間が重なる学習標本を除く。エンバーゴ: テスト直後の学習標本を除く(系列相関対策)。
- 寄り→引けの同日ラベルは日をまたいで重ならないので、パージは 1 日で足りる。特徴量に長い移動窓を使うならエンバーゴを 5 営業日程度置く(設計案)。
- CPCV: N 群から k 群をテストに取る全組合せ。purgedcv の README 例では N=6、k=2 で 15 分割・5 本のバックテスト経路(サンプル 120 件、出力形状 (5, 120))。経路ごとの成績の分布(中央値と下位 5%)で判断する。
- ウォークフォワードは経路が 1 本しかないが実運用に最も近い。Arian, Norouzi, Seco (2024) は合成環境で CPCV が過学習抑制に優れると報告した、という二次情報あり(原論文は未開封)。
- skfolio の公式注記: `WalkForward(purged_size=0)` だと学習末尾とテスト先頭が同じ期になり楽観的になるので、執行に遅延があるなら 1 以上にする。

#### 3.2 PSR / DSR / MinTRL / MinBTL

- PSR(SR*) = Φ[ (SR − SR*)·√(T−1) / √(1 − γ₃·SR + (γ₄−1)/4·SR²) ]。SR は 1 期間あたり(年率でない)、γ₄ は超過でない尖度。
- DSR = PSR(SR₀)、SR₀ = √V·[(1−γ)Φ⁻¹(1−1/N) + γΦ⁻¹(1−1/(Ne))]。N は独立な試行数、V は試行間の SR の分散、γ=0.5772。相関のある M 試行は平均相関から「実効的な独立試行数」に直す(論文付録 A.3)。
- 論文の数値例を再計算: SR₀=0.1132、DSR=0.9004。N=46 なら 0.9505。正規リターンなら N=88 まで 0.95 を保つ。すべて論文の記述と一致。
- MinTRL = 1 + [1 − γ₃·SR + (γ₄−1)/4·SR²]·(z_α / (SR − SR*))²。自前計算(年 245 営業日、SR*=0、α=0.05):

| 年率 SR | 正規 | 歪度 −1、尖度 6 |
|---|---|---|
| 0.5 | 2,654 日 | 2,741 日 |
| 1.0 | 666 日 | 710 日 |
| 1.5 | 297 日 | 328 日 |
| 2.0 | 169 日 | 192 日 |
| 3.0 | 77 日 | 93 日 |

- MinBTL: N 通り試して最良を選ぶと、真の SR が 0 でも IS の年率 SR 1 が出る。それを避けるのに必要な年数は E[max]² 年。N=45 でちょうど 5.0 年(自前計算。「5 年分のデータなら独立な試行は 45 まで」という Bailey らの経験則と一致)。N=10 で 2.5 年、N=100 で 6.4 年。

#### 3.3 PBO / CSCV

手順(論文 Algorithm 2.3): (1) T×N の成績行列 M(列 = 試した設定)、(2) 行を偶数 S 個に等分、(3) S/2 個を選ぶ全組合せ(S=16 なら C(16,8) = 12,870 通り。論文本文は 12,780 と印字)、(4) 各組合せで IS 最良の設定を選び、その OOS での相対順位 ω を出してロジット ln(ω/(1−ω)) を取る、(5) ロジット ≤ 0 の割合が PBO。論文が挙げる用途: PBO > 0.05 で棄却、事前確率として使う、(1−PBO) で重みづける。論文自身が「PBO を最適化の目的関数にしてはいけない」と注意している。

#### 3.4 多重検定

- Harvey, Liu, Zhu(NBER w20592、RFS 2016 29(1):5-68): 新しいファクターには t > 3.0 を要求すべき。
- Harvey & Liu "Backtesting": 上の表 15 番。
- White の Reality Check(Econometrica 2000)と Hansen の SPA(JBES 2005): 「ベンチマークより良いモデルが 1 つでもあるか」のブートストラップ検定。arch の `SPA` が実装。
- FDR: BH 法(独立または正の依存)、BY 法(任意の依存)。e 値版の e-BH は任意の依存で FDR を制御する(Wang & Ramdas。原論文は未開封、式は記憶に基づく。expectation ライブラリに `e_bh()` あり)。
- López de Prado, Lipton, Zoonekynd "How to Use the Sharpe Ratio"(SSRN 5520741、2025-10 掲載。JPM 2026 掲載という情報は検索要約のみ): 5 つの落とし穴(正規性の仮定、標本長の無視、検出力の無視、p 値を「戦略が本物である確率」と取り違える、多重検定の無補正)と、PSR / MinTRL / DSR / ベイズ FDR をまとめた枠組み。

#### 3.5 バックテストは実運用をほとんど予測しない

Wiecki, Campbell, Lent, Stauth (2016、Quantopian): 888 本のアルゴリズム(各 6 か月以上の OOS)で、バックテストの Sharpe が OOS 成績を説明する R² は 0.025 未満。バックテスト回数が多い戦略ほど IS と OOS の落差が大きい。複数特徴量の非線形分類器なら R²=0.17(Quantpedia の要約で確認、原論文は未開封)。

### 4. 1 日あたり何銘柄を予測すべきか(必答 3)

実効サンプル n_eff/日 = n / (1 + (n−1)ρ)。ρ は同日の予測結果どうしの級内相関。

| ρ | n=5 | 10 | 20 | 30 | 50 | 100 | 200 |
|---|---|---|---|---|---|---|---|
| 0 | 5.0 | 10.0 | 20.0 | 30.0 | 50.0 | 100.0 | 200.0 |
| 0.02 | 4.6 | 8.5 | 14.5 | 19.0 | 25.3 | 33.6 | 40.2 |
| 0.05 | 4.2 | 6.9 | 10.3 | 12.2 | 14.5 | 16.8 | 18.3 |
| 0.1 | 3.6 | 5.3 | 6.9 | 7.7 | 8.5 | 9.2 | 9.6 |
| 0.3 | 2.3 | 2.7 | 3.0 | 3.1 | 3.2 | 3.3 | 3.3 |

固定標本(α=0.05、検出力 0.8)に届くまでの営業日数:

| 設計 | n_eff/日 | 55%(654 件) | 53%(1,773 件) |
|---|---|---|---|
| 絶対方向 5 銘柄、ρ=0.3 | 2.3 | 285 日 | 771 日 |
| 絶対方向 20 銘柄、ρ=0.3 | 3.0 | 218 日 | 591 日 |
| 相対方向 20 銘柄、ρ=0.05 | 10.3 | 64 日 | 172 日 |
| 相対方向 30 銘柄、ρ=0.05 | 12.2 | 54 日 | 145 日 |
| 相対方向 30 銘柄、ρ=0.02 | 19.0 | 35 日 | 93 日 |
| 相対方向 50 銘柄、ρ=0.02 | 25.3 | 26 日 | 70 日 |
| 相対方向 100 銘柄、ρ=0.02 | 33.6 | 20 日 | 53 日 |

提案:
- **ルールベース(人 / LLM が docs を読む)は 1 日 20〜30 銘柄、目的変数は T1(相対方向)。** 30 を超えると読む手間に対して n_eff の伸びが鈍る。
- **ML は事前登録したユニバース全体(例: 売買代金上位 300〜500)** を毎日採点し、日次ランク IC とスプレッドリターンで評価する(1 日 = 1 標本)。
- ρ の値(0.02〜0.3)は**仮定**。日本株の寄り→引けでの実測値は未確認なので、40〜100 営業日たったら `icc_from_daily` で自分の台帳から推定し、この表を引き直す。
- どの銘柄を予測するかの選択も予測の一部。ユニバースは事前登録し、選ばなかった銘柄は見送りとして残す。

### 5. 改ざんできない記録方式(必答 4)

#### 5.1 3 層構成

| 層 | 仕組み | 何を防ぐか | 弱点 |
|---|---|---|---|
| L0 | 追記専用 JSONL。各行に prev_hash と hash(SHA-256、正規化 JSON) | 途中の行の書き換え・削除・並べ替え | 末尾の切り捨てと全体の作り直しは検出できない |
| L1 | 毎朝 08:45 にローカル git コミット | 作業履歴の保全 | `--date`、`GIT_AUTHOR_DATE`、`GIT_COMMITTER_DATE` で日時を自由に設定できる(git 公式ドキュメントで確認) |
| L2a | 先頭ハッシュを RFC 3161 TSA(FreeTSA)で署名 | 「この時刻より前に存在した」を秒精度で第三者署名 | TSA を信頼する必要がある |
| L2b | 先頭ハッシュを OpenTimestamps で刻印 | Bitcoin ブロックで裏づけ。運営者を信頼しなくてよい | 確定まで数時間。「9:00 より前」の分単位の証明には向かない |
| L2c | GitHub へ push | サーバー側に履歴が残る | Events API の保持は 30 日・最大 300 件、遅延 30 秒〜6 時間(GitHub Docs で確認)。長期証拠には別の手段が要る |

前日までにアンカーした先頭ハッシュが今日のチェーンの途中に現れることを毎日検証すれば、切り捨てと作り直しも検出できる。

#### 5.2 `ledger.py`(実行確認済み、stdlib のみ)

```python
"""ledger.py - append-only, hash-chained prediction log (stdlib only)."""
import hashlib, json, os, sys
from datetime import datetime, timezone

GENESIS = "0" * 64

def _canon(obj) -> bytes:
    # canonical JSON: sorted keys, no spaces, UTF-8 -> same bytes on every machine
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def _last_hash(path):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return GENESIS, 0
    with open(path, "rb") as f:
        lines = f.read().splitlines()
    return json.loads(lines[-1])["hash"], len(lines)

def append(path, payload: dict) -> dict:
    prev, n = _last_hash(path)
    rec = {"seq": n, "ts_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "prev_hash": prev, "payload": payload}
    rec["hash"] = hashlib.sha256(_canon(rec)).hexdigest()
    with open(path, "ab") as f:            # append-only; never rewrite
        f.write(_canon(rec) + b"\n"); f.flush(); os.fsync(f.fileno())
    return rec

def verify(path) -> str:
    prev = GENESIS
    with open(path, "rb") as f:
        for i, line in enumerate(f.read().splitlines()):
            rec = json.loads(line); h = rec.pop("hash")
            if rec["seq"] != i or rec["prev_hash"] != prev: raise ValueError(f"chain broken at line {i}")
            if hashlib.sha256(_canon(rec)).hexdigest() != h: raise ValueError(f"hash mismatch at line {i}")
            prev = h
    return prev   # head hash -> anchor this externally (git push / RFC3161 / OpenTimestamps)

if __name__ == "__main__":
    print(verify(sys.argv[1]))
```

確認した挙動: 3 行追記 → `verify` が先頭ハッシュを返す。2 行目の p_up を 0.55 から 0.9 に書き換えると `hash mismatch at line 1` で失敗する。

#### 5.3 毎朝の手順(Git Bash、タスクスケジューラで 08:45 JST に起動する想定)

```bash
D=$(date +%F)
python ledger.py data/predictions.jsonl > data/anchors/$D.head          # 検証 + 先頭ハッシュ
git add data/predictions.jsonl data/anchors && git commit -m "pred $D" && git push
openssl ts -query -data data/anchors/$D.head -no_nonce -sha512 -cert -out data/anchors/$D.tsq
curl -s -H "Content-Type: application/timestamp-query" --data-binary "@data/anchors/$D.tsq" \
     https://freetsa.org/tsr > data/anchors/$D.tsr
openssl ts -verify -in data/anchors/$D.tsr -queryfile data/anchors/$D.tsq \
     -CAfile cacert.pem -untrusted tsa.crt                               # "Verification: OK"
# 任意: ots-cli.js stamp data/anchors/$D.head   (数時間後に ots-cli.js upgrade data/anchors/$D.head.ots)
```

- openssl / curl の 3 コマンドは FreeTSA 公式ページの記載どおり(`-cert` を付けると検証時の `-untrusted` は不要とも書かれている)。**実際の送信は未実行**。
- `cacert.pem` と `tsa.crt` は https://freetsa.org/files/ から取得。ページ掲載の SHA-256 は tsa.crt が `8bfb0305…a13467`、cacert.pem が `2151b611…044438`。
- `.tsr` は翌日のコミットに含める。
- 採点結果は別ファイル `outcomes.jsonl` に追記する。予測ファイルは二度と編集しない。
- ルール文書の版(git blob ハッシュ)を predictor ID に入れるので、ルールを後から書き換えると ID が変わり、別の試行として数えられる。
- 試したルール変種・パラメータはすべて `trials.jsonl`(同じ方式)に 1 行ずつ残す。これが DSR / e-BH の N と m になる。

#### 5.4 限界

- タイムスタンプが証明するのは「存在」であって「唯一性」ではない。予測を何通りも作って全部刻印し、後で当たった版だけ見せることは技術的に可能。対外的な証明が要るなら、1 本の公開リポジトリに線形履歴で積む。自分を騙さない目的なら、自動ジョブが 1 系統しか書かない構成で足りる。
- OpenTimestamps の Python クライアントは検証にローカル Bitcoin ノードを要求する。JS クライアントはエクスプローラで代替できるが、README 自身が「自前ノードより安全性は落ちる」と書いている。
- OpenTimestamps の無料カレンダー(Alice / Bob / Finney / Catallaxy)は寄付運営で、可用性の保証は無い。

### 6. `scoring.py`(実行確認済み、numpy + scipy のみ)

```python
"""scoring.py - proper scores, baselines, tests (numpy + scipy only)."""
import numpy as np
from math import log, sqrt, e
from scipy.stats import norm, beta

def brier(p, y):            return float(np.mean((np.asarray(p) - np.asarray(y)) ** 2))
def logloss(p, y, eps=0.01):
    p = np.clip(np.asarray(p, float), eps, 1 - eps); y = np.asarray(y, float)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))
def skill(score, ref):      return 1.0 - score / ref          # BSS etc. (>0 = better than ref)

def rps_m6(F, Q):
    """M6 RPS. F,Q: (n_assets, 5) forecast probs / realized quintile one-hot. Uniform F -> 0.16."""
    d = np.cumsum(np.asarray(Q, float), 1) - np.cumsum(np.asarray(F, float), 1)
    return float(np.mean(np.mean(d ** 2, axis=1)))

def murphy(p, y, edges=(0, .4, .45, .5, .55, .6, 1.0000001)):
    """Brier = REL - RES + UNC (exact when forecasts are constant within a bin)."""
    p, y = np.asarray(p, float), np.asarray(y, float); n = len(p); ybar = y.mean()
    rel = res = 0.0; rows = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (p >= lo) & (p < hi)
        if m.sum() == 0: continue
        pk, ok = p[m].mean(), y[m].mean()
        rel += m.sum() * (pk - ok) ** 2 / n; res += m.sum() * (ok - ybar) ** 2 / n
        rows.append((lo, hi, int(m.sum()), round(float(pk), 4), round(float(ok), 4)))
    return {"REL": rel, "RES": res, "UNC": ybar * (1 - ybar), "bins": rows}

def pesaran_timmermann(pred_up, actual_up):
    """PT(1992) market-timing test; H0: prediction and outcome independent. Returns (z, one-sided p)."""
    x, y = np.asarray(pred_up, float), np.asarray(actual_up, float); n = len(x)
    px, py, phat = x.mean(), y.mean(), np.mean(x == y)
    pstar = py * px + (1 - py) * (1 - px)
    v_hat = pstar * (1 - pstar) / n
    v_star = ((2 * py - 1) ** 2 * px * (1 - px) + (2 * px - 1) ** 2 * py * (1 - py)) / n \
             + 4 * py * px * (1 - py) * (1 - px) / n ** 2
    z = (phat - pstar) / sqrt(v_hat - v_star)
    return float(z), float(norm.sf(z))

def day_block_bootstrap(daily_diff, reps=10000, block=5, seed=0):
    """CI/p for mean daily score differential (ref - model > 0 = model better). Circular block bootstrap."""
    d = np.asarray(daily_diff, float); D = len(d); rng = np.random.default_rng(seed)
    nb = int(np.ceil(D / block)); starts = rng.integers(0, D, size=(reps, nb))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]) % D
    means = d[idx.reshape(reps, -1)[:, :D]].mean(axis=1)
    lo, hi = np.percentile(means, [5, 95])
    return {"mean": float(d.mean()), "ci90": (float(lo), float(hi)), "p_le0": float(np.mean(means <= 0))}

def within_day_permutation(p, y, day, reps=2000, seed=0):
    """Shuffle outcomes across tickers inside each day -> null that keeps market-wide moves fixed."""
    p, y, day = map(np.asarray, (p, y, day)); rng = np.random.default_rng(seed)
    obs = -brier(p, y); cnt = 0
    groups = [np.nonzero(day == d)[0] for d in np.unique(day)]
    for _ in range(reps):
        yp = y.copy()
        for g in groups: yp[g] = y[rng.permutation(g)]
        cnt += (-brier(p, yp) >= obs)
    return (cnt + 1) / (reps + 1)

LAM = np.array([0.25, 0.5, 1.0, 1.5, 1.9])
def e_process_daily(x, lam=LAM):
    """PRIMARY promotion test. x_t = daily hit fraction - 0.5 in [-0.5, 0.5].
    H0: E[x_t | past days] <= 0. Valid under any within-day dependence. Reject when E >= 1/alpha."""
    x = np.asarray(x, float)[:, None]
    ll = np.cumsum(np.log1p(lam[None, :] * x), axis=0)
    m = ll.max(axis=1, keepdims=True)
    return np.exp(m[:, 0] + np.log(np.exp(ll - m).mean(axis=1)))

GRID = np.array([0.52, 0.54, 0.56, 0.58, 0.60])
def e_process(hits, p0=0.5, grid=GRID):
    """Per-prediction likelihood-ratio mixture. ONLY valid for independent predictions."""
    h = np.asarray(hits, float)[:, None]
    ll = np.cumsum(h * np.log(grid / p0) + (1 - h) * np.log((1 - grid) / (1 - p0)), axis=0)
    m = ll.max(axis=1, keepdims=True)
    return np.exp(m[:, 0] + np.log(np.exp(ll - m).mean(axis=1)))

def e_bh(evalues, alpha=0.10):
    """e-BH (FDR control under arbitrary dependence): reject the k* largest e-values."""
    ev = np.asarray(evalues, float); m = len(ev); order = np.argsort(-ev)
    k = np.arange(1, m + 1); ok = np.nonzero(ev[order] >= m / (alpha * k))[0]
    rej = np.zeros(m, bool)
    if len(ok): rej[order[: ok.max() + 1]] = True
    return rej

def sprt(hits, p0=0.5, p1=0.55, alpha=0.05, beta_=0.20):
    """Wald SPRT. Returns ('promote'|'drop'|'continue', n_used)."""
    A, B = log((1 - beta_) / alpha), log(beta_ / (1 - alpha)); s = 0.0
    for i, h in enumerate(hits, 1):
        s += log(p1 / p0) if h else log((1 - p1) / (1 - p0))
        if s >= A: return "promote", i
        if s <= B: return "drop", i
    return "continue", len(hits)

def beta_posterior(k, n, a=100, b=100, thr=0.5):
    """Skeptical prior Beta(100,100): returns (shrunk hit rate, P(p > thr | data))."""
    return (a + k) / (a + b + n), float(beta.sf(thr, a + k, b + n - k))

def icc_from_daily(hit_rate_by_day, n_per_day):
    """Design effect -> intraclass corr rho and n_eff/day (equal n per day)."""
    hr = np.asarray(hit_rate_by_day, float); p = hr.mean(); n = n_per_day
    deff = hr.var(ddof=1) / (p * (1 - p) / n); rho = max(0.0, (deff - 1) / (n - 1))
    return float(rho), float(n / (1 + (n - 1) * rho))

_G = 0.5772156649015329
def expected_max_z(N): return (1 - _G) * norm.ppf(1 - 1 / N) + _G * norm.ppf(1 - 1 / (N * e))
def psr(sr, T, skew=0.0, kurt=3.0, sr_star=0.0):          # per-period SR, kurt = non-excess
    return float(norm.cdf((sr - sr_star) * sqrt(T - 1) / sqrt(1 - skew * sr + (kurt - 1) / 4 * sr * sr)))
def dsr(sr, T, n_trials, var_trials_sr, skew=0.0, kurt=3.0):
    return psr(sr, T, skew, kurt, sr_star=sqrt(var_trials_sr) * expected_max_z(n_trials))
def min_trl(sr, sr_star=0.0, alpha=0.05, skew=0.0, kurt=3.0):
    return 1 + (1 - skew * sr + (kurt - 1) / 4 * sr * sr) * (norm.ppf(1 - alpha) / (sr - sr_star)) ** 2
```

実行確認の内容: 合成データ(250 日 × 20 銘柄)で全関数が動作。`rps_m6` は一様予測で約 0.16。`murphy` は REL − RES + UNC が Brier と一致。`dsr(2.5/√250, 1250, 100, 0.5/250, -3, 10)` = 0.9004(論文値と一致)。`e_process` は帰無仮説下 400 回で誤棄却 5.0%、的中率 55% で中央値 511 件。`sprt` は的中率 55% で昇格 79.5%、帰無仮説下で誤昇格 4.75%。Pesaran–Timmermann の式と e-BH の式は原論文を開けておらず記憶に基づく実装なので、採用前に原典と突き合わせること。

### 7. 予測の集約(複数ルール・複数モデルの統合)

- M6 の結果: 上位チームの予測を単純平均すると最良の単独チームを上回り、常にベンチマークにも勝った。約半数のチームを混ぜても最良に近い精度を保った。
- 平均は確率を 0.5 側に圧縮する。Baron et al. (2014) は t(p) = p^a/(p^a+(1−p)^a) で補正する(地政学予測では a>1)。Satopää et al. (2014) は対数オッズの平均を極端化する形(最適な係数が 1.161〜3.921 という数字は二次要約のみで未確認)。
- 金融では逆方向の証拠がある。M6 では参加者の確率が極端すぎた(過信)。Makridakis, Spiliotis, Michailidis (2025, IJF 41(4):1395-1403) は対称な五分位に近い確率を置くと精度も運用効率も上がると報告。
- 設計案: 統合確率 = 対数オッズの重み付き平均。重みは Beta(100,100) で縮小した的中率 − 0.5(負なら 0)。その後 a を過去データのみで Brier 最小化して当てはめる(範囲 [0.3, 3]、初期値 1)。a を後知恵で決めると過学習になる。

### 8. LLM 予測に固有の評価問題

- Glasserman & Lin (2023, arXiv:2309.17322): LLM の学習期間と重なるバックテストは先読みバイアスを受ける。別に「distraction effect」(企業名から一般知識が混入して見出しの評価が歪む)もある。企業名を匿名化すると学習期間内ではむしろ成績が上がり、後者の影響が大きいと示唆。学習期間外なら先読みは問題にならない。
- He, Lv, Manela, Wu (2025, arXiv:2502.21206 v3): 各時点までの文書だけで学習した ChronoBERT / ChronoGPT。ニュースから翌日リターンを予測する用途では、大型の Llama と同程度の Sharpe で、先読みバイアスは「modest」と結論(数値は要旨に無く未確認)。
- Halawi et al. (2024, arXiv:2402.18563): テスト問題をモデルの知識カットオフ以降に公開されたものに限定して漏洩を避けた。
- ForecastBench (Karger et al., arXiv:2409.19839 v5): 提出時点で答えが存在しない問いを自動生成して漏洩を防ぐ。500 問(LLM)/ 200 問(人間)を 2 週ごと。初期の論文では専門家が最良の LLM を上回った(p<0.001)。2026 年の順位(超予測者が 1 位を維持、複数モデルが信頼区間内)は検索要約のみで未確認。
- このプロジェクトへの含意: (b) 系は前向き記録だけを証拠にする。モデル ID、プロンプトのハッシュ、temperature、出力全文を残す。モデルを替えたら predictor ID を変えてゼロから数える。

### 9. デイトレーダーの実績研究(事前確率の根拠)

| 研究 | 市場・期間 | 主な数値 | 確認 |
|---|---|---|---|
| Barber, Lee, Liu, Odean (2014) "The cross-section of speculator skill: Evidence from day trading", J. Financial Markets 18(1) | 台湾、1992–2006 | 前年成績上位 500 人は翌年も日次 +61.3bp(手数料前)/ +37.9bp(手数料後)。下位は −11.5bp / −28.9bp。手数料後に予測可能な形で勝てるのは全体の 1% 未満 | ✅ PDF 本文(2011 年稿は 49.5 / 28.1bp) |
| Chague, De-Losso, Giovannetti (2020) "Day trading for a living?", FGV EESP TD 525 | ブラジル株価指数先物、2013–2015 開始で 300 日以上継続 | 97% が損失。銀行窓口係(日 54 ドル)を上回ったのは 0.4%。最上位は日 310 ドルだが標準偏差 2,560 ドル。経験による上達の証拠なし | ✅ IDEAS |
| SEBI(PR No. 13/2024、2024-07-24) | インド株式現物の日計り、FY2022-23 | 個人の 7 割超が損失。参加者は FY2018-19 比で 300% 超増 | ✅ 二次(Taxmann)。71%、年 500 回超で 80%、若年層 76%、平均損失 5,371 ルピーは報道要約のみ ❓ |
| SEBI(PR No. 22/2024、2024-09-23) | インド株式デリバティブ、FY22–FY24 | 個人約 1,000 万人の 93% が損失、平均約 20 万ルピー、総額 1.8 兆ルピー超 | ❓ 報道要約のみ |
| 金融先物取引業協会「預託金増減口座数割合情報」 | 日本の店頭 FX、四半期 | 2018Q1〜2020Q4 の預託金減少口座は 43.1%〜72.2% | ✅ 二次(外為どっとコムの解説記事)。原データ XLS は未開封 |
| 日本株の個人デイトレーダーの損益分布 | - | 公的統計を見つけられなかった | ❓ 未確認 |

### 10. M6 コンペの設計と教訓(確認済みの数値)

- 226 チーム(318 人)、Global 順位表は 163 チーム。資産 100(S&P500 構成 50 + 国際 ETF 50)。試行 1 か月の後、4 週間隔で 12 回提出。
- 予測でベンチマーク超え 38 チーム(23.3%)、投資で 47 チーム(28.8%)、両方 11 チーム(6.7%)。
- 予測成績(RPS)と投資成績(IR)の相関は全体で r=0.04。**当てる力と儲ける力は別物として両方測る。**
- 予測ベンチマークに 12 か月すべてで勝ったのは 3 チーム。投資で全月勝ったチームは無し。
- 主催者の提言: 運と実力を分けるには 1 年では短く 2〜5 年が望ましい。コードの提出による再現性確保。

## 因果ルール候補(該当する場合)

この観点は市場の値動きではなく「予測の評価」を扱うので、以下は**評価メタルール**(予測器やルールの成績がどう振る舞うか)である。docs のルール運用規程にそのまま入れられる形で書く。

### M-01 選抜バイアス
- IF N 本のルール / パラメータの中から過去成績で最良を選んだ → THEN その成績は割り引く。全部が無能でも最良の z 値は E[max] ≈ (1−γ)Φ⁻¹(1−1/N) + γΦ⁻¹(1−1/(Ne))(N=20 で 1.90、各 250 件なら的中率 56.0% 相当)。時間軸: 選抜直後から。
- なぜ: 最大値を取る操作そのものが上振れを作る。
- 根拠: Bailey & López de Prado 2014(数値例を再計算で確認)。Harvey & Liu 2015(SR 0.75 が試行 200 で 0.32 に)。Wiecki et al. 2016(バックテスト回数が多いほど IS–OOS 落差が大きい、米国株 888 戦略、OOS は 2015-06〜2016-02)。
- 効かなくなる条件: 選抜後に取った新しい前向きデータだけで評価する場合。
- 必要データと入手時刻: 試行台帳(全変種)、各試行の成績系列。随時。
- 確度: A

### M-02 標本不足
- IF あるルールの実績が 300 件未満または 60 営業日未満 → THEN 的中率の数字で昇格・降格を決めない(300 件での有意水準 5% の境界は 55.0%)。
- なぜ: 二項分布の標準誤差が 0.5/√n で、300 件でも ±2.9%。
- 根拠: 自前の厳密二項計算(上の表)。
- 効かなくなる条件: なし(数学的事実)。効果が極端に大きい(60% 超)なら 169 件で足りる。
- 必要データ: 予測台帳。毎日引け後。
- 確度: A

### M-03 日内相関
- IF 同じ日に n 銘柄を予測し、結果どうしの級内相関が ρ → THEN 独立標本は n/(1+(n−1)ρ) 件しかない。予測 1 件を独立とみなす検定は偽陽性が増える(ρ=0.05 で 5% → 20.9%)。
- なぜ: 地合い・セクター要因が同日の結果を同じ方向に動かす。
- 根拠: 設計効果の公式と自前シミュレーション。日本株での ρ の実測値は未確認。
- 効かなくなる条件: 中央値相対・セクター中立の目的変数にすると ρ が下がる(下がり幅は要実測)。
- 必要データ: 日別の的中率。40〜100 営業日後に推定。
- 確度: A(式)/ C(ρ の具体値)

### M-04 確率の過信
- IF 株の相対リターン順位に 0.2 から大きく離れた五分位確率(または 0.5 から大きく離れた上昇確率)を付ける → THEN スコアは一様予測より悪化しやすい。時間軸: 4 週間予測での結果。日中予測への転用は未検証。
- なぜ: 予測可能な成分が小さく、極端な確率は外れたときの罰が大きい。価格変動の大きさが主因と報告されている。
- 根拠: M6(2022–2023、100 資産、163 チーム中ベンチマーク超え 23.3%、改善 2.5% 未満)。Makridakis, Spiliotis, Michailidis 2025。
- 効かなくなる条件: 決算など情報量の大きいイベント直後は別の可能性(未検証)。
- 必要データ: 確信度バケット別の較正表。
- 確度: B

### M-05 平均の優位
- IF 複数の予測器の確率を単純平均する → THEN 単独最良に近いか上回る。
- なぜ: 個別の誤差が打ち消し合う。
- 根拠: M6(上位チームの平均が最良単独を上回り、常にベンチマーク超え)。Baron et al. 2014 / Satopää et al. 2014(地政学予測)。
- 効かなくなる条件: 予測器どうしが同じ情報・同じ誤りを共有する場合。無能な予測器を大量に混ぜる場合。
- 必要データ: 予測器別の台帳。
- 確度: B(金融では単一コンペ)

### M-06 LLM の先読み
- IF LLM に学習期間内の過去日付を予測させて成績を測った → THEN その成績は証拠にしない(先読みと、企業名による一般知識の混入の両方で歪む)。
- なぜ: モデルが結果を既に見ている可能性がある。
- 根拠: Glasserman & Lin 2023。Halawi et al. 2024 と ForecastBench はカットオフ後の問いに限定する設計。He et al. 2025 は翌日リターン予測では影響が小さいと報告しており、大きさは用途依存。
- 効かなくなる条件: 知識カットオフ以降の前向き記録。時点整合モデル(ChronoGPT など)の使用。
- 必要データ: モデル ID とカットオフ日、予測の刻印時刻。
- 確度: B

### M-07 バックテストと実運用の落差
- IF バックテストの Sharpe が高い → THEN 実運用の成績はほとんど予測できない(R² < 0.025)。ボラティリティや最大ドローダウンなどリスク指標の方が持続する。
- なぜ: 過学習と環境変化。
- 根拠: Wiecki et al. 2016(Quantpedia 要約で確認)。McLean & Pontiff 2016(JF 71(1):5-32。「サンプル外で 26%、公表後で 58% 低下」という数値は記憶によるもので今回未確認)。
- 効かなくなる条件: 試行数が少なく、経済的な理由が事前に書かれている戦略(定量的な裏づけは未確認)。
- 必要データ: 試行台帳、前向き成績。
- 確度: B

### M-08 当たることと儲かることの乖離
- IF 予測スコア(RPS / Brier)が改善した → THEN 紙上損益が改善するとは限らない。別指標として追う。
- なぜ: 損益は外れたときの大きさ、ポジションの相関、リスク管理に依存する。
- 根拠: M6(全チームで IR と RPS の相関 r=0.04。予測上位 10 チームの提出ポートフォリオの IR 中央値 0.37)。
- 効かなくなる条件: 予測をそのまま機械的にリスクモデルへ流す場合は連動が強まる(M6 の再最適化では予測上位の IR 中央値 0.50)。
- 必要データ: 予測台帳と紙上ポートフォリオの日次損益。
- 確度: B

### M-09 個人デイトレードの基準率
- IF 個人が日計りで継続的に売買する → THEN 手数料後に安定して勝つ確率は 1〜3% 程度。
- なぜ: コストと逆選択。経験による上達の証拠も無い(ブラジル)。
- 根拠: 上の表 9(台湾 1% 未満、ブラジル 97% 損失、インド現物 7 割超損失)。
- 効かなくなる条件: 上位層には持続性がある(台湾の上位 500 人は翌年も手数料後 +37.9bp/日)。つまり「全員が負ける」ではなく「ごく少数だけが勝ち続ける」。
- 必要データ: なし(事前分布として使う)。
- 確度: A(海外)/ 日本株は未確認

### M-10 バックテスト長の下限
- IF 手元のデータが Y 年分 → THEN 独立に試してよい設定数は E[max_N]² ≤ Y を満たす N まで(5 年で 45、2.5 年で 10)。
- なぜ: それ以上試すと、真の SR が 0 でも IS の年率 SR 1 が出る。
- 根拠: Bailey, Borwein, López de Prado, Zhu の MinBTL(式を自前で再計算。原論文 AMS Notices 版は 403 で未開封)。
- 効かなくなる条件: 試行間の相関が高い場合は実効的な N が小さくなる。
- 必要データ: 試行台帳。
- 確度: B

## 落とし穴・反証・注意

1. **後から目的変数を変える**のが最大の抜け道。T1〜T3 の定義、価格ソース、同値・売買停止・終日値付かずの扱いを先に文書化し、定義 ID を予測レコードに入れる。
2. **毎日成績を見て「有意になった日」に止める**と通常の p 値は壊れる。e-process か SPRT を使う。
3. **切り口の後づけ**(「火曜だけ」「高ボラ日だけ」)は多重検定。切り口は診断用に限定し、良さそうなら新ルールとして登録して前向きに数え直す。
4. **的中率は適切なスコア規則ではない。** 0.51 でも 0.99 でも同じ 1 点なので過信を罰しない。Brier / log loss を主にする。
5. **log loss は p=0 や 1 で発散する。** 0.02〜0.98 に制限する。
6. **非定常性。** CPCV や PBO は期間を入れ替えても意味があることを暗に仮定する。1 年かけて検出した優位性が検出時点で消えていることもあり得るので、昇格後も probation 判定を回し続ける。
7. **e-process の λ 格子や混合格子は事前に固定する。** データを見て選ぶと有効性が崩れる。
8. **日単位 e-process は保守的。** 55% の検出が予測単位の約 2 倍(29 日 → 55 日)かかる。速さを取って予測単位にすると M-03 の偽陽性を踏む。
9. **ベータ二項の事前分布 Beta(100,100)** と降格閾値(60 日で 49% 以下など)は本ノートの設計値で、文献の裏づけは無い。運用しながら誤警報率を実測して調整する。
10. **ρ の値は仮定。** 表 4 の日数は ρ 次第で数倍変わる。
11. **ライセンス。** mlfinlab(all rights reserved)は写さない。pypbo(AGPL)、expectation と quantskills(GPL-3.0)はコードを自分のリポジトリに転載しない。式とアルゴリズムは論文から実装する。
12. **purgedcv は 2026-05 初版の若いライブラリ**(v0.1.x、55 stars)。DSR は本ノートの `dsr` と数値を突き合わせてから使う。
13. **confseq は Windows 用 wheel が無い**(0.0.11、2023-01)。comparecast も巻き添えで入れにくい。
14. **紙上と実弾の差**(この節は出典未確認の経験則、確度 C): 寄り成行は板寄せの始値で約定する想定が置けるが、特別気配で寄らない、ストップ高買い気配で買えない、空売りできない銘柄がある、自分の注文が価格を動かす、といった要因は紙上では現れない。紙上の成績は上限とみなす。
15. **タイムスタンプは唯一性を証明しない**(5.4 参照)。
16. **Metaculus の採点式**(Baseline score = 100·log₂(p/0.5)、Peer score など)は公式 FAQ が 403 で開けず、二次要約しか確認できていない。
17. **JPX Kaggle の順位ウェイトの向き**は Zenn 記事内で表記が揺れている。公式ルール未確認。

## このプロジェクトへの提案

### MVP で採用するもの
1. `ledger.py` による予測・採点・試行の 3 台帳(すべて追記専用 + ハッシュチェーン)。
2. 毎朝 08:45 の自動ジョブ: 検証 → git commit / push → FreeTSA 刻印。
3. 目的変数 T1(中央値相対の寄り→引け方向)を主、T2 を副。ユニバースは事前登録(まず 100 銘柄程度)。
4. ルールベースは 1 日 20〜30 銘柄、ML はユニバース全銘柄。
5. 指標: Brier、BSS(対コイン)、log loss、的中率、Murphy 分解、信頼性曲線。ベースライン 6 種を同じ台帳に記録。
6. 推論は日単位: 日ブロック bootstrap 区間と `e_process_daily`。
7. 昇格 = 60 営業日 + 300 件 + E ≥ 20 + bootstrap 下限 > 0。降格 = 直近 60 日の的中率 ≤ 49% で probation。
8. 40〜100 営業日後に ρ を実測し、銘柄数と必要日数の表を引き直す。
9. LLM 予測はモデル ID・プロンプトハッシュ・出力全文を保存し、前向き記録のみ採点。
10. docs に「評価メタルール M-01〜M-10」を運用規程として収録。

### 後回しにするもの
- T3(五分位 RPS、M6 日次版)と Numerai 式 CORR、JPX 式スプレッド Sharpe。
- ML モデル選定用の CPCV / PBO / DSR(purgedcv または skfolio)。過去データで ML を作り始める段階で導入。
- 3 モデル以上の一括比較(arch の SPA / MCS)、2 モデル比較の DM 検定。
- 予測の集約(縮小重み + a の当てはめ)。予測器が 3 つ以上 active になってから。
- OpenTimestamps(FreeTSA の補強)。
- 紙上損益の PSR / DSR、コストモデル。

## 未追跡の手がかり

- 日本語圏の先行実装(Qiita / Zenn / note / GitHub の「株価予測 記録 採点」「J-Quants 検証」系)。検索上限で未着手。
- 金融先物取引業協会の原データ XLS(https://www.ffaj.or.jp/wp-content/uploads/2026/08/otc_fx_account_percentage_j.xls、2021 年以降を含むはず)。
- 日本株の個人デイトレーダーの損益統計(日証協、JPX、証券会社の開示)。
- SEBI の原報告書 2 本(PR 13/2024、PR 22/2024)。
- 日本株の寄り→引けリターンにおける日内級内相関 ρ の実測(自分のデータで計算可能)。
- Arian, Norouzi, Seco (2024) "Backtest overfitting in the machine learning era" の本文と数値。
- López de Prado, Lipton, Zoonekynd (2025) の本文と `functions.py` の関数一覧・ライセンス。
- Wang & Ramdas の e-BH 原論文、Waudby-Smith & Ramdas "Estimating means of bounded random variables by betting"(arXiv:2010.09686)。
- Pesaran & Timmermann (1992, JBES 10(4):461-465) と Anatolyev & Gerko (2005, JBES 23(4):455-461) の原式。
- Satopää et al. (2014, IJF 30:344-356) の本文と係数。
- Metaculus Scores FAQ(403)、ForecastBench の難易度調整 Brier の式(arXiv:2409.19839 本文)。
- Kaggle JPX コンペの公式 Evaluation ページと、上位解法が private 期間後も持続したか。
- Numerai MMC の正確な式と、Numerai Signals の日本株カバレッジ。
- opentimestamps-client(Python)の Windows での動作、ライセンス種別。
- GitHub 上でサーバー時刻が長期に残る場所(Actions のログ保持期間、Release / Issue コメントの created_at)の仕様。
- McLean & Pontiff (2016) の数値(26% / 58%)の原典確認。
- scoringrules の関数名(Brier / RPS / log の API)。
- Fatebook の API(予測の外部記録先として使えるか。about ページでは API とエクスポートの存在のみ確認)。

## 参照 URL 一覧

### 開いて確認(✅)
- ✅ https://arxiv.org/abs/2310.13357 (M6 論文。本文は https://ar5iv.labs.arxiv.org/html/2310.13357 で確認)
- ✅ https://ideas.repec.org/a/eee/intfor/v41y2025i4p1395-1403.html (M6 overconfidence)
- ✅ https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf (DSR、PDF をテキスト抽出)
- ✅ https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf (PBO / CSCV、同上)
- ✅ https://people.duke.edu/~charvey/Research/Published_Papers/P120_Backtesting.PDF (Harvey & Liu)
- ✅ https://www.nber.org/papers/w20592 (Harvey, Liu, Zhu)
- ✅ https://www.adialab.ae/research-series/how-to-use-the-sharpe-ratio
- ✅ https://github.com/zoonek/2025-sharpe-ratio
- ✅ https://github.com/eslazarev/purged-cross-validation / https://pypi.org/pypi/purgedcv/json / https://raw.githubusercontent.com/eslazarev/purged-cross-validation/main/README.md / https://eslazarev.github.io/purged-cross-validation/
- ✅ https://api.github.com/repos/skfolio/skfolio / https://skfolio.org/generated/skfolio.model_selection.CombinatorialPurgedCV.html / https://skfolio.org/generated/skfolio.model_selection.WalkForward.html
- ✅ https://arch.readthedocs.io/en/latest/multiple-comparison/generated/arch.bootstrap.SPA.html / https://arch.readthedocs.io/en/latest/multiple-comparison/multiple-comparisons.html / https://pypi.org/pypi/arch/json
- ✅ https://scikit-learn.org/stable/modules/generated/sklearn.metrics.brier_score_loss.html / https://scikit-learn.org/stable/modules/generated/sklearn.calibration.calibration_curve.html / https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html
- ✅ https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.false_discovery_control.html
- ✅ https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html
- ✅ https://github.com/frazane/scoringrules / https://scoringrules.readthedocs.io/en/latest/
- ✅ https://github.com/esvhd/pypbo
- ✅ https://github.com/quantskills/skill-backtest-overfit
- ✅ https://github.com/bettyguo/agent-backtest-lab
- ✅ https://github.com/hudson-and-thames/mlfinlab / https://api.github.com/repos/hudson-and-thames/mlfinlab
- ✅ https://api.github.com/search/repositories?q=deflated+sharpe+ratio&sort=stars / https://api.github.com/search/repositories?q=probability+of+backtest+overfitting&sort=stars
- ✅ https://arxiv.org/abs/2110.00115 (Choe & Ramdas) / https://github.com/yjchoe/ComparingForecasters / https://pypi.org/pypi/comparecast/json / https://pypi.org/pypi/confseq/json
- ✅ https://arxiv.org/abs/2103.08402 (Henzi & Ziegel)
- ✅ https://arxiv.org/abs/2210.01948 (Ramdas, Grünwald, Vovk, Shafer)
- ✅ https://github.com/jakorostami/expectation / https://2025.pycon.de/talks/ZKNTGN
- ✅ https://pypi.org/pypi/dieboldmariano/json
- ✅ https://www.rdocumentation.org/packages/rugarch/versions/1.4-4/topics/DACTest (PT 検定・AG 検定の出典)
- ✅ https://api.github.com/repos/opentimestamps/opentimestamps-client / https://github.com/opentimestamps/opentimestamps-client / https://github.com/opentimestamps/opentimestamps-client/blob/master/doc/git-integration.md
- ✅ https://github.com/opentimestamps/javascript-opentimestamps / https://opentimestamps.org/
- ✅ https://freetsa.org/index_en.php
- ✅ https://pypi.org/pypi/rfc3161-client/json
- ✅ https://git-scm.com/docs/git-commit / https://docs.github.com/en/rest/activity/events
- ✅ https://zenn.dev/gamella/articles/eaf7fe5a96bdf0 (JPX Kaggle コンペ設計)
- ✅ https://docs.numer.ai/numerai-tournament/scoring/correlation-corr
- ✅ https://faculty.wharton.upenn.edu/wp-content/uploads/2015/07/2015---two-reasons-to-make-aggregated-probability-forecasts_1.pdf (Baron et al.)
- ✅ https://www.escholarship.org/content/qt7k75v0qx/qt7k75v0qx.pdf / https://faculty.haas.berkeley.edu/odean/papers/day%20traders/Day%20Trading%20Skill%20110523.pdf (Barber et al.)
- ✅ https://ideas.repec.org/p/fgv/eesptd/525.html (Chague et al.)
- ✅ https://taxmann.com/post/blog/sebi-study-finds-that-7-out-of-10-individual-intraday-traders-in-equity-cash-segment-made-losses
- ✅ https://www.gaitame.com/beginner/start/fail.html / https://www.ffaj.or.jp/library/performance/quarter_total/quarterly_data/ (XLS へのリンクのみ)
- ✅ https://quantpedia.com/quantopians-academic-paper-about-in-vs-out-of-sample-performance-of-trading-alg/
- ✅ https://arxiv.org/abs/2309.17322 (Glasserman & Lin) / https://arxiv.org/abs/2502.21206 (He et al.) / https://arxiv.org/abs/2402.18563 (Halawi et al.)
- ✅ https://www.forecastbench.org/ / https://www.forecastbench.org/docs/ / https://github.com/forecastingresearch/forecastbench/wiki/How-does-ForecastBench-work%3F / https://arxiv.org/abs/2409.19839
- ✅ https://fatebook.io/about
- ✅ https://ideas.repec.org/a/bla/jfinan/v71y2016i1p5-32.html (McLean & Pontiff。書誌のみ、要旨なし)

### 未確認(❓)
- ❓ https://www.metaculus.com/help/scores-faq/ (403)
- ❓ https://papers.ssrn.com/abstract=2460551 (DSR の SSRN ページ、403)
- ❓ https://papers.ssrn.com/abstract=5520741 (How to Use the Sharpe Ratio、検索要約のみ)
- ❓ https://www.ams.org/notices/201405/rnoti-p458.pdf (Pseudo-Mathematics and Financial Charlatanism、403)
- ❓ https://www.business-standard.com/markets/news/over-70-intra-day-traders-incur-losses-during-fy23-reveals-sebi-study-124072401110_1.html (403)
- ❓ https://www.ffaj.or.jp/wp-content/uploads/2026/08/otc_fx_account_percentage_j.xls (未開封)
- ❓ https://api.github.com/repos/yjchoe/ComparingForecasters / https://api.github.com/repos/zoonek/2025-sharpe-ratio (403。HTML ページ側で確認)
- ❓ https://scoringrules.readthedocs.io/en/latest/api/categorical.html (404)
- ❓ https://en.wikipedia.org/wiki/Purged_cross-validation (404)
- ❓ Arian, Norouzi, Seco (2024) SSRN、Satopää et al. (2014) IJF、Wang & Ramdas (e-BH)、Waudby-Smith & Ramdas (arXiv:2010.09686)、Wiecki et al. (SSRN 2745220) の各原文
