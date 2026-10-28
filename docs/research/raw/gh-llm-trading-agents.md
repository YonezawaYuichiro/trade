# GitHub: LLM トレーディングエージェントとライブベンチマーク

> 調査日: 2026-10-13 / 観点: gh-llm-trading-agents / 状態: 一次調査(未検証)

**調査の制約(先に明記)**: WebSearch はワークフロー全体で共有の上限に達し、本観点では 7 回しか実行できなかった(指定の 15 回に未達)。上限到達後は検索エンジンの迂回利用はせず、既知 URL・GitHub リポジトリ本体・GitHub トピックページ・arXiv を WebFetch で直接開いて確認した(実際に開いたページは約 90)。GitHub API は途中からレート制限(403)になったため、後半のリポジトリは HTML ページで確認しており、**最終 push 日が取れていないものがある**(表に明記)。WebFetch は小型モデルによる要約を返すため、数値は原典での再確認を推奨する。

---

## 結論(5〜10 行)

1. **「毎日 docs を読んで予測 → 翌日採点して反省 → docs を直す」を全部やっている OSS は見つからなかった。** 部品はそろっており、(a) 予測の保留→決済→反省→次回プロンプトへの注入は `TauricResearch/TradingAgents` v0.4〜0.6 の memory log、(b) 自然言語ルール(YAML/Markdown)で LLM に毎日判定させて後日自動採点するのは `ZhuLinsen/daily_stock_analysis`、(c) 事後検証から「手順書の改善バックログ」を作るのは `tradermonty/claude-trading-skills` の signal-postmortem、(d) 手順書そのものを壊さずに差分更新する仕組みは `ace-agent/ace`(ACE, ICLR 2026)が最も近い。この 4 つを組み合わせるのが最短。
2. **ライブ(先読み不能)環境での LLM の実成績は「ベースラインに安定して勝てていない」が現時点の共通所見。** StockBench(2025-03〜06)は受動ベースライン +0.4% に対し上位でも +2.5%、下落局面ではどの LLM も勝てず。DeepFund(2025-03-17〜04-17)は 9 モデル中 8 が損失。Agent Market Arena(2025-08〜09)は TSLA で Buy&Hold +46.88% を超えたエージェントなし。Alpha Arena Season 1(暗号資産)は 6 モデル中 4 が大幅損失、Season 1.5(米国株)は 8 モデル中 1 だけ黒字(二次報道)。
3. **過去期間のバックテスト成績は信用しない。** Profit Mirage(arXiv 2510.07920)は学習期間内→期間外で Sharpe が 51〜62% 減衰、The Alpha Illusion(arXiv 2605.16895)は TradingAgents をコスト込みで再評価し Sharpe 0.43→0.22、5 銘柄中 4 で Buy&Hold 未満と報告。FINSABER(KDD 2026)は 20 年・多銘柄で FinMem/FinAgent が Buy&Hold に有意に負けると報告。
4. **先読み対策の決定版は「カットオフ後の期間だけで評価」か「本当のライブ記録」。** プロンプトで「未来を知らないふりをしろ」と指示しても、社名をマスクしても暗記は防げない(Lopez-Lira ら, arXiv 2504.14765)。本プロジェクトは毎朝の予測をタイムスタンプ付きで追記専用台帳に書くので、**前向き記録である限り構造的に先読み不能**。逆に LLM ルール予測の過去日バックテストは混入するので、過去検証は機械的ルール(プログラム)だけに限定する。
5. **モデルの賢さより、設計と規律が効く。** LiveTradeBench は LMArena スコアと運用成績の順位相関が 0.054(株)/ −0.38(Polymarket)。AMA は「バックボーンよりエージェント構成の差が大きい」と結論。LLM に売買サイズや執行を触らせず、見解(方向・確信度・根拠)だけ出させ、決定論的コードで採点・集計する設計(`virattt/ai-hedge-fund` の現行版)が主流になりつつある。
6. **日本株向けの LLM 予測→採点ループの OSS はほぼ空白。** データ接続(`shigechika/jquants-mcp`、`tdnet-disclosure-mcp`、`edinetdb/dexter-jp`)とファンダ調査スキル(`dexter-kabu-jp`、`ai-berkshire-jp`)はあるが、予測の記録と採点まで持つのは星 0 の個人リポジトリ(`shisakulab/ai-trade-check`、`Yurikada/jp-stock-screener`、`Tomato-1101/scalplab`)程度。TradingAgents は `7203.T` と `^N225` ベンチマークに公式対応済みなので、採点ロジックはそのまま流用できる。
7. **自己更新する手順書は、採点が確定した結果だけを材料にしないと劣化する。** ACE 論文は正解ラベルなしのオンライン更新で精度がベースを下回る例(FiNER 70.7→67.3)を示す。`signal-postmortem` は重み変更に最低 20 シグナルを要求。docs の改訂は「件数しきい値+人間の承認」を必須にする。

---

## 丸パクリ候補(優先度順の表)

| # | 名前 | URL | 種別 | ライセンス | 鮮度(最終更新・発表年) | 何をどう写すか | 確認 |
|---|---|---|---|---|---|---|---|
| 1 | TauricResearch/TradingAgents | https://github.com/TauricResearch/TradingAgents | repo | Apache-2.0 | v0.6.0 = 2026-10-03、push 2026-10-03、星 110,854(API 取得値) | **予測台帳と反省ループの本体**。`tradingagents/memory/log.py`(追記専用 Markdown 台帳、`[日付 \| 銘柄 \| 評価 \| pending]` → 決済後 `[... \| +x.x% \| +y.y% \| Nd \| resolved:日付]`、区切り `<!-- ENTRY_END -->`、同一銘柄 5 件+他銘柄 3 件を注入、`as_of` で時点フィルタ)、`memory/settlement.py`(`holding_period_days` 既定 5、`.T`→`^N225` で alpha 算出)、`memory/reflection.py`(2〜4 文の反省を生成)、`agents/schemas.py`(Pydantic 出力スキーマ)、`dataflows/date_window.py`(日付クランプ)、`backtest.py`(評価別 hit rate / mean alpha)。`holding_period_days=1` にして日中予測用に転用 | ✅ |
| 2 | ZhuLinsen/daily_stock_analysis | https://github.com/ZhuLinsen/daily_stock_analysis | repo | MIT | push 2026-10-11、星 66,244 | **毎日回す運用の型**。`.github/workflows/00-daily-analysis.yml`(cron `0 10 * * 1-5` UTC、非取引日スキップ、成果物 30 日保存)、`src/analyzer.py` の「決策ダッシュボード」JSON スキーマとスコア帯、`strategies/*.yaml`(自然言語ルールを YAML で持つスキーマ: `name/category/core_rules/required_tools/market_regimes/instructions`)、後日採点の定義(`BACKTEST_EVAL_WINDOW_DAYS=10`、`BACKTEST_NEUTRAL_BAND_PCT=2.0`、方向一致率と勝率の式)。日本株は `7203.T` 形式と `MARKET_REVIEW_REGION=jp` に対応 | ✅ |
| 3 | tradermonty/claude-trading-skills | https://github.com/tradermonty/claude-trading-skills | repo(Claude Skills) | MIT | 星 約 3.0k、最終更新日 未取得 | **docs 駆動+事後検証→手順書改善の型**。`skills/signal-postmortem/SKILL.md`(結果を TRUE_POSITIVE / FALSE_POSITIVE / MISSED_OPPORTUNITY / REGIME_MISMATCH に分類、5 日・20 日で採点、重み変更は 20 件以上、改善バックログ YAML を出力)、`skills/trader-memory-core/SKILL.md`(仮説 1 件 = YAML 1 ファイル、状態遷移は前進のみ、`state/` を git 管理)、`workflows/trade-memory-loop.yaml`(記録→事後検証→コーチ→再検証→教訓追記の 5 段) | ✅ |
| 4 | ace-agent/ace(ACE 論文) | https://github.com/ace-agent/ace / https://arxiv.org/abs/2510.04618 | repo + paper | Apache-2.0 | 論文 2025-10(v3 2026-03、ICLR 2026)、星 約 1.4k | **手順書(playbook)を壊さず育てる仕組み**。箇条書き 1 行 = `[section-00001] helpful=X harmful=Y :: 内容`、Generator(実行)→ Reflector(反省、最大 5 回)→ Curator(差分だけ追記・カウンタ更新、全文書き換え禁止)、重複は埋め込み類似度 0.9 で統合。docs の「因果ルール」各行にこの ID とカウンタを付ける | ✅ |
| 5 | virattt/ai-hedge-fund | https://github.com/virattt/ai-hedge-fund | repo | MIT | push 2026-10-02、星 63,963 | **改ざんできない紙上台帳と規律**。`hedge_fund/README.md` の原則(その日までに提出済みのデータだけ見せる/T の引けで決めて T+1 で約定/LLM は見解だけで売買に触れない/台帳は追記専用)、`~/.hedge-fund/paper/<name>/ledger/<session>.json`(ハッシュ連鎖)、`Signal`(conviction −1〜+1+reasoning)、`hedge_fund/event_study/`(市場モデル CAR) | ✅ |
| 6 | The Alpha Illusion(報告プロトコル P1〜P6) | https://arxiv.org/abs/2605.16895 | paper | — | 2026-05 | **自分の成績報告の書式**。P1 時点整合(モデル版・カットオフ・検索時刻の記録)、P3 反実仮想テスト(逆の証拠を入れたとき方向が変わるか)、P4 確信度の較正(ECE・信頼性曲線)、P5 グロス→ネットの段階表示、P6 単独エージェント比較。Sharpe の標準誤差式も写す | ✅ |
| 7 | shigechika/jquants-mcp | https://github.com/shigechika/jquants-mcp | repo(MCP) | MIT | 2026-10-12 更新(トピック一覧表示)、星 2 | **日本株データを Claude Code から引く口**。`claude mcp add jquants-mcp -- jquants-mcp`、55 ツール(日足・分足・財務・信用残・セクター騰落・52 週高安検出など)、SQLite キャッシュ、J-Quants Free 可(5 回/分) | ✅ |
| 8 | StockBench | https://github.com/ChenYXxxx/stockbench / https://arxiv.org/abs/2510.02209 | repo + paper | Apache-2.0 | 論文 2025-10、最終更新日 未取得、星 183 | **毎朝の入力仕様と 4 段ワークフロー**(全体俯瞰→選んだ銘柄だけ深掘り→判断→検証して差し戻し)。入力は「過去 7 日の自分の行動」「直近 48 時間のニュース最大 5 本」「寄り値」「選択銘柄のみファンダ」。受動ベースライン比較と 3 シード平均の評価方法 | ✅ |
| 9 | DeepFund | https://github.com/HKUSTDial/DeepFund / https://arxiv.org/abs/2505.11065 | repo + paper | MIT | NeurIPS 2025 D&B、星 299 | **日次予測に使うアナリストの絞り方**(Technical / Company News / Policy / Insider を使用、Fundamental と Macro は日次に不向きとして除外)、パラメータ(OHLCV 100 日、ニュース 10 本、直近行動 5 件、temperature 0.5、再試行 3)。プロンプトは `src/graph/` | ✅ |
| 10 | LiveTradeBench | https://github.com/ulab-uiuc/live-trade-bench / https://arxiv.org/abs/2511.03628 | repo + paper | **PolyForm Noncommercial 1.0.0**(非商用のみ) | 論文 2025-11、星 168 | プロンプト構成(銘柄ごとの直近 10 日の終値と前日比、直近 3 日のニュース、過去配分の履歴)と JSON 出力(`reasoning` と `allocations`、合計 1.0)。コードは非商用ライセンスなので構成だけ参考にする | ✅ |
| 11 | shisakulab/ai-trade-check | https://github.com/shisakulab/ai-trade-check | repo(日本株) | MIT | 結果表 2026-09-28 付、星 0 | **日本株で「AI 判断を紙上で検証」する最小構成**。`ai_engine.py` の `ask_ai(state)` → (action, confidence 0〜1, 生応答)、失敗時は hold、`store.py`(SQLite)、`compare.py`(複数実行の比較)、`run_daily.bat`(Windows)。日経 225 と ACWI(円)を対照にする | ✅ |
| 12 | waylonli/FINSABER | https://github.com/waylonli/FINSABER | repo | Apache-2.0 | FINSABER-2 = 2026-05、KDD 2026、星 149 | 検証エンジン。`pip install finsaber`、既定の `next_open` 約定(同日先読み防止)、`BaseStrategyIso.on_data(date, today_data, framework)` を継承、`finsaber.toolkit.llm_cost_monitor` で API 費用を取引コストに算入 | ✅ |
| 13 | ajtgjmdjp/tdnet-disclosure-mcp | https://github.com/ajtgjmdjp/tdnet-disclosure-mcp | repo(MCP) | Apache-2.0 | 2026-08-23 更新、星 6 | 適時開示を Claude Code から取得(`uvx tdnet-disclosure-mcp serve`、4 ツール)。データ元は非公式の Yanoshin Web API なので利用規約と可用性に注意 | ✅ |
| 14 | edinetdb/dexter-jp / raditrejp/dexter-kabu-jp / edinetdb/ai-berkshire-jp | https://github.com/edinetdb/dexter-jp ほか | repo(日本株調査エージェント) | MIT(dexter-jp はデータ別ライセンス) | 2026-10-08 / 2026-05-12 / 2026-07-11、星 312 / 26 / 8 | `.dexter/RULES.md` に自分の調査ルールを書くと自動で読み込まれる方式、`/check`(仮説を有報の記述と突き合わせる)。dexter-kabu-jp は需給(信用倍率・空売り比率)やしこり分析などのスキル雛形と「別コンテキストの評価役が 4 軸 1〜5 点で採点し平均 3.0 未満なら再分析」。予測採点は持たない | ✅ |
| 15 | Tomato-1101/scalplab / Yurikada/jp-stock-screener / polipoli0401/longterm-stock-lab | https://github.com/Tomato-1101/scalplab ほか | repo(日本株・個人) | MIT | 2026-10-01 / 2026-09-08 / 2026-08-19、星 0〜1 | scalplab: ティック記録→夜間の期間外評価→チャンピオン固定(自動差し替えなし)、ギャップ逆張り(`gap_sigma` 下位数 % を寄りで買い引けで売り)。jp-stock-screener: 平日 8:00 にスクリーニング、8:30 に +1/+3/+7/+14/+30 営業日の事後リターンを記録。longterm-stock-lab: GitHub Actions 平日 18:30 JST、採否を `models/decisions.jsonl` に理由つきで記録 | ✅ |
| 16 | FinStep-AI/ContestTrade | https://github.com/FinStep-AI/ContestTrade | repo | Apache-2.0 | 星 681、最終更新日 未取得 | `contest_trade/config/belief_list.json`(「取引信念」を 1 行 1 エージェントで持ち、内部コンテストで選抜)。ルール群を並走させて競わせる発想 | ✅ |
| 17 | HKUDS/AI-Trader(ベンチマーク論文) | https://github.com/HKUDS/AI-Trader / https://arxiv.org/abs/2512.10971 | repo + paper | API では license なし、ページには MIT バッジ(**不整合・要確認**) | push 2026-06-11、星 22,757 | 論文の結果表と「検索・価格ツールを模擬時刻で制限」という設計のみ参考。**リポジトリは現在エージェント向け取引プラットフォームに転換**しており、論文当時のベンチマーク用プロンプトは main に見当たらない | ✅(論文・現リポジトリ)/ ❓(旧コードの所在) |
| 18 | Alpha Arena(nof1.ai) | https://nof1.ai/ / https://alphaarena.ai/ | service | 非公開 | Season 1 = 2025-10-18〜11-03、Season 1.5 = 2025-11 下旬〜12 月初旬 | 出力に「無効化条件」「確信度」「根拠」を必須にする設計、複数プロンプト条件(記憶と自己学習あり/資本保全重視/順位を見せる/高レバ強制)を並走させる発想。**公式ページは 403/404 で開けず、成績は二次報道** | ❓(公式)/ ✅(報道 2 本) |
| 19 | Agent Market Arena | https://arxiv.org/abs/2510.11695 | paper | — | 2025-10 | 同じデータで 4 種のエージェント構成 × 5 モデルを比較する実験設計、温度 0.5・ウォームアップ 90 日・決定記憶 7 ステップ | ✅(論文)/ ❓(リーダーボード URL) |
| 20 | FinMem / FinCon / FinAgent / InvestorBench / FinGPT / FinRobot / QuantAgent / SEP | 各 URL は末尾 | repo / paper | MIT / Apache-2.0 など | 2023〜2025 年発表、多くは更新停滞 | 概念の参照のみ(層状メモリ、信念の言語的強化、反省)。いずれも過去期間バックテストの成績で、後続研究で減衰が報告されている | ✅(リポジトリ存在)/ ❓(論文内数値) |

---

## 詳細(項目ごとに、中身・数値・使い方・限界)

### 0. 必ず答えること(4 点の要約)

**(1) 「毎日、決まった手順書を読んで予測を出し、翌日反省して手順書を直す」に最も近い実装**

| 段階 | 最も近い実装 | 足りない部分 |
|---|---|---|
| 手順書(自然言語ルール)を読んで毎日判定 | daily_stock_analysis(`strategies/*.yaml` の `instructions` と `src/analyzer.py` の規律プロンプト、GitHub Actions で平日毎日) | ルールは人が書いた固定物。採点結果でルールは変わらない |
| 予測を保留で記録し、期間経過後に自動採点 | TradingAgents `memory/log.py` + `memory/settlement.py`(ベンチマーク比 alpha、時点フィルタつき) | 既定は 5 営業日。日中予測には `holding_period_days` 変更と始値基準への改造が要る |
| 採点結果から短い反省を書き、次回の判断に注入 | TradingAgents `memory/reflection.py`(2〜4 文、数値引用必須、教訓 1 つ) | 反省はメモリに溜まるだけで、プロンプト(手順書)自体は不変 |
| 事後検証から手順書の改善案を出す | claude-trading-skills `signal-postmortem`(改善バックログ YAML、重み提案は 20 件以上) | 手順書の書き換えは人間 |
| 手順書を自動で差分更新 | ACE(playbook の箇条書きに helpful/harmful カウンタ、Curator が差分のみ適用) | 取引特化ではない。信頼できる採点がないと劣化する |
| ライブで「記憶と自己学習」を持たせた競技 | Alpha Arena Season 1.5 の New Baseline 条件 | コード非公開 |

結論: **単体で最も近いのは TradingAgents(v0.4.0 以降)**。ただし「手順書を直す」部分は持たないので、ACE の playbook 形式と signal-postmortem の分類を足す。

**(2) 写すべきプロンプト・構成・出力スキーマ(ファイルパス)** → 下の §1〜§5 に列挙。

**(3) ライブ環境での LLM の実成績** → §6 の表。

**(4) 学習データ混入(先読み)への対処** → §7。

---

### 1. TauricResearch/TradingAgents(最優先)

- **状態**: Apache-2.0、星 110,854・フォーク 21,357(GitHub API、2026-10-13 取得)、アーカイブなし。v0.6.0 が 2026-10-03。なお別の二次情報は 2026 年 3 月時点で約 3.1 万星としており、急増している。
- **論文**: Xiao, Sun, Luo, Wang "TradingAgents: Multi-Agents LLM Financial Trading Framework" arXiv:2412.20138(v1 2024-12-28、v7 2025-06-03)。
- **構成**(README とソースで確認):
  - アナリスト 4 種(並列): `tradingagents/agents/analysts/market_analyst.py`(テクニカル)、`sentiment_analyst.py`、`news_analyst.py`、`fundamentals_analyst.py`
  - 強気/弱気リサーチャーの討論: `agents/researchers/bull_researcher.py`、`bear_researcher.py`
  - リサーチマネージャー(審判): `agents/managers/research_manager.py`
  - トレーダー: `agents/trader/trader.py`
  - リスク討論 3 者: `agents/risk_mgmt/aggressive_debator.py`、`conservative_debator.py`、`neutral_debator.py`
  - ポートフォリオマネージャー(最終判断): `agents/managers/portfolio_manager.py`
  - 速いモデルがアナリスト・討論・トレーダー、深いモデルが 2 人のマネージャーを担当。
- **写すべきプロンプトの要点**(原文は転載せず要約):
  - テクニカル(`market_analyst.py`): 12 指標のメニュー(`close_50_sma`、`close_200_sma`、`close_10_ema`、`macd`、`macds`、`macdh`、`rsi`(70/30)、`boll`、`boll_ub`、`boll_lb`、`atr`、`vwma`)から**重複しない最大 8 個**を選ばせ理由を書かせる。先に価格 CSV を取り、最後に「検証済みスナップショット」ツールを呼び、数値の食い違いは捏造せず明示させる。ツール出力に日付と価格の裏づけがない限り「過去に検証済み」「支持線で反発」「正確な % 変動」といった主張を禁止。末尾に Markdown 表。
  - 全アナリスト共通: 実行日 `trade_date` を「今日」として扱わせ、ツールの日付範囲もそれに合わせる。
  - ニュース(`news_analyst.py`): ツールは `get_news`、`get_global_news`、`get_macro_indicators`(FRED)、`get_prediction_markets`。マクロの記述は実データで裏づけ、売買判断は別エージェントに任せる。
  - 審判 2 人(`research_manager.py`、`portfolio_manager.py`): 5 段階(Buy / Overweight / Hold / Underweight / Sell)から 1 つ。**「意見が割れていること自体は Hold の理由にならない。強い側に寄せ、決め手の強さで大きさを決める。Hold は証拠が拮抗か不足のときだけ」**。話した順番で重みを変えない。
  - トレーダー(`trader.py`): エントリーと損切りは**絶対価格**で書かせ、% や範囲は禁止(書けないなら省略)。
- **出力スキーマ**(`tradingagents/agents/schemas.py`):
  - `ResearchPlan`: `recommendation`(5 段階)、`rationale`、`strategic_actions`
  - `TraderProposal`: `action`(Buy/Hold/Sell)、`reasoning`、`entry_price`(float|None)、`stop_loss`(float|None)、`position_sizing`(str|None)
  - `PortfolioDecision`: `rating`(5 段階)、`executive_summary`、`investment_thesis`、`price_target`(float|None)、`time_horizon`(str|None)
  - `SentimentReport`: `overall_band`(6 段階)、`overall_score`(0〜10)、`confidence`(low/medium/high。データ 5 件未満なら low)、`narrative`
  - `_coerce_optional_float`: 「N/A」や % 表記、範囲表記を None に落とす前処理。評価が読めない場合は Hold にせず `REVIEW` として別扱い(v0.4.0 #1170)。
- **memory log(予測台帳)**(`tradingagents/memory/log.py`):
  - 追記専用 Markdown、既定パス `~/.tradingagents/memory/trading_memory.md`(`TRADINGAGENTS_MEMORY_LOG_PATH` で変更)。
  - 保留: `[{trade_date} | {ticker} | {rating} | pending]` の次に `DECISION:` 本文。
  - 決済後: `[{trade_date} | {ticker} | {rating} | {raw_pct} | {alpha_pct} | {holding_days}d | resolved:{日付}]`、本文に `REFLECTION:` を追加。% は符号つき小数 1 桁。
  - 区切りは `\n\n<!-- ENTRY_END -->\n\n`(LLM の文章に出ない文字列を境界にする)。
  - 冪等: 同じ日付×銘柄があれば書かない。書き込みは一時ファイル→置換の原子的更新、決済はロックで直列化。
  - 注入: `get_past_context(ticker, n_same=5, n_cross=3, as_of=None)`。同一銘柄は全文 5 件、他銘柄は反省だけ 3 件。`as_of` 指定時は**その日までに決済済みの教訓だけ**見せる(#1251)。
  - `memory_log_max_entries` で決済済みの古い順に間引き(保留は消さない)。
- **決済**(`memory/settlement.py`): `raw = (close[h] − close[0]) / close[0]`、`alpha = raw − ベンチマーク同期間リターン`。`holding_period_days` 既定 5。保有期間がすべて取引済みになるまで保留のまま。ベンチマークは `benchmark_map` で接尾辞から決まり、**`.T` → `^N225`**、既定は `SPY`。価格は Yahoo。`settle_all_pending()` で分析を走らせずに決済だけ実行可能(スケジューラ向け、v0.6.0)。
- **反省**(`memory/reflection.py`): 入力は「N 日の生リターン」「ベンチマーク比 alpha」「最終判断本文」。出力は 2〜4 文の平文で、(i) alpha が方向判断について何を示すか(数値を引用。期間が短すぎて判断不能ならそう書く)、(ii) 仮説のどの部分が支持/否定されたか、(iii) 次の類似分析に使う具体的教訓 1 つ。短い窓で長期仮説を否定したことにしない、という注意が入っている。
- **バックテスト**(`tradingagents/backtest.py`、CLI `tradingagents backtest NVDA,AAPL --start 2026-06-01 --end 2026-08-01 --every 7`): ポートフォリオ模擬ではなく「判断の質」の集計。Buy/Overweight は +1、Underweight/Sell は −1 とし、**hit rate = alpha の符号が一致した割合**、Hold は方向主張なしで hit rate を出さない。評価別に件数・hit rate・平均 alpha。レポート自身が「1 セル 1 サンプルでテキストフィードは保存されないため、数値は参考であり再現可能ではない」と注記。
- **無人実行**: `tradingagents --ticker NVDA --date 2026-09-23 --analysts market,news,fundamentals --save --no-show`、設定は `TRADINGAGENTS_*` 環境変数。
- **主な設定**(`tradingagents/default_config.py`): `max_debate_rounds=1`、`max_risk_discuss_rounds=1`、`max_tool_rounds=20`、`news_article_limit=20`、`global_news_article_limit=10`、`global_news_lookback_days=7`、`holding_period_days=5`、`output_language="English"`(日本語出力可)、`temperature=None`、`checkpoint_enabled=False`。既定モデル名は取得時点で `gpt-6-sol` / `gpt-6-luna` と返ってきた(要再確認)。
- **日本株対応**: `7203.T` のような接尾辞つきティッカーをプロンプト・ツール間で保持(v0.2.2 #413)、`.T` のベンチマークは `^N225`(v0.2.5 #628)。非米国企業の財務は Yahoo 由来で、過去日実行では「提出日がない財務は伏せる」。
- **報告成績と反証**:
  - 原論文: 2024-01-01〜03-29(約 3 か月)。AAPL 累積 +26.62%・Sharpe 8.21・最大 DD 0.91%、GOOGL +24.36%・6.39、AMZN +23.21%・5.60。取引コストの記載なし。著者自身が Sharpe は想定範囲を超えていると認め、期間が短い理由を「1 予測あたり LLM 約 11 回+ツール 20 回超」と説明。
  - Profit Mirage: 学習期間内→期間外で TradingAgents の Sharpe 55.68% 減、総リターン 50.18% 減。
  - The Alpha Illusion: 2025-01〜2026-01、5 銘柄(TSLA, NVDA, KO, XOM, MSTR)等加重、$100K。Buy&Hold $104.8K に対し TradingAgents グロス $106.4K → ネット $102.3K、Sharpe 0.43→0.22。
  - Agent Market Arena(ライブ 2 か月): TradingAgents 由来の TradeAgent は GPT-4.1 で TSLA −38.72%、Gemini-2.0-flash で +21.91% とバックボーンで大きくばらつく。
- **限界**: 1 銘柄 1 実行のコストが高い(呼び出し回数が多い)。日中(寄り→引け)の予測を想定していない。README も「研究用の足場であり、固定で再現可能なリターンを持つ戦略ではない」と明記。

### 2. ZhuLinsen/daily_stock_analysis

- **状態**: MIT、星 66,244・フォーク 55,151(GitHub Actions で各自が回すためフォークが多い)、push 2026-10-11。
- **毎日の流れ**: データ取得 → テクニカル計算とニュース検索 → LLM 分析 → レポート生成 → 通知。`python main.py`(`--market-review` / `--no-market-review` / `--force-run` / `--schedule`)。
- **ワークフロー**(`.github/workflows/00-daily-analysis.yml`): cron `0 10 * * 1-5`(UTC、北京 18:00)、開始前に 0〜59 秒のランダム待機、ジョブ上限 30 分(`ANALYSIS_TIMEOUT_MINUTES`)、`concurrency: stock-analysis`(キャンセルせず順番待ち)、`reports/` と `logs/` を 30 日保存。銘柄リストは `STOCK_LIST` 変数。
- **決策ダッシュボード JSON**(`src/analyzer.py`): 最上位に `sentiment_score`(0〜100 整数)、`trend_prediction`、`operation_advice`、`decision_type`(buy/hold/sell)、`action`(buy/add/hold/reduce/sell/watch/avoid/alert)、`confidence_level`、`guardrail_reason`。`dashboard` 配下に `core_conclusion`(`one_sentence`、`signal_type`、`time_sensitivity`、`position_advice`)、`data_perspective`(`trend_status`、`price_position`、`volume_analysis`、`chip_structure`)、`intelligence`(`latest_news`、`risk_alerts`、`positive_catalysts`、`earnings_outlook`、`sentiment_summary`)、`battle_plan`(`sniper_points`: `ideal_buy`/`secondary_buy`/`stop_loss`/`take_profit`、`position_strategy`、`action_checklist` 6 項目を ✅/⚠️/❌)、`phase_decision`(`watch_conditions`、`next_check_time`、`confidence_reason`、`data_limitations`)、任意の `signal_attribution`(テクニカル/ニュース/ファンダ/地合いの寄与を各 0〜100、最強の強気材料と弱気材料)。
- **スコア帯**(プロンプト内): 80〜100 強い買い / 60〜79 買い / 40〜59 様子見 / 20〜39 減らす / 0〜19 売り。
- **コード側のガード**(LLM の出力を機械的に矯正): 支持線割れ = 価格 < 支持 × 0.985、支持線付近 = ≤ 支持 × 1.03、ブレイク = > 抵抗 × 1.01、抵抗付近 = ≥ 抵抗 × 0.97。抵抗付近で資金流入なしの買いは hold に格下げ。データが古い・欠損・推定のとき、および寄り前や非取引時間は確信度を「高」にできない。出来高の前日比が 10 倍超は異常値として重みを下げる。構造的リスク語(減持、退市、処罰、訴訟、違約など)をニュースから照合。**「1 日の値動きやスコアの閾値越えだけで買い↔売りを反転させない」**という安定化規則。
- **7 つの規律**(`strategies/README.md`): ①乖離率 5% 未満でのみ買い検討 ②MA5 > MA10 > MA20 ③出来高で確認 ④押し目(移動平均の支持)で買う ⑤悪材料は拒否権 ⑥価格と出来高の整合 ⑦強い主導株は基準を緩和(`BIAS_THRESHOLD=5.0`、強トレンドは 1.5 倍に緩和)。
- **自然言語ルールの YAML**(`strategies/`、15 本: `bottom_volume`、`box_oscillation`、`bull_trend`、`chan_theory`、`dragon_head`、`emotion_cycle`、`event_driven`、`expectation_repricing`、`growth_quality`、`hot_theme`、`ma_golden_cross`、`one_yang_three_yin`、`shrink_pullback`、`volume_breakout`、`wave_theory`)。スキーマ: `name`、`display_name`、`description`、`category`(trend/pattern/reversal/framework)、`core_rules`(1〜7 の番号)、`required_tools`、`aliases`、`default_active`、`default_router`、`default_priority`、`market_regimes`、`instructions`(Markdown の自由文。コード不要)。`AGENT_SKILL_DIR` で自作ルールを追加・上書き。例 `shrink_pullback.yaml`: MA5 > MA10 > MA20、MA5 から 1% 以内または MA10 から 2% 以内へ押し、押しの出来高が 5 日平均の 70% 未満、MA5 乖離 2% 未満が最良、含み益比率 50〜80%、損切りは MA20、条件成立で `sentiment_score` +10(MA10 かつ出来高 0.6 倍未満なら +8)。
- **後日採点**(`docs/full-guide.md`): `BACKTEST_ENABLED=true`(毎日の分析後に自動実行)、`BACKTEST_EVAL_WINDOW_DAYS=10`、`BACKTEST_MIN_AGE_DAYS=14`、`BACKTEST_NEUTRAL_BAND_PCT=2.0`、`BACKTEST_ENGINE_VERSION=v1`(ロジック変更時に結果を分ける)。buy は帯以上の上昇で勝ち、sell は帯以上の下落で勝ち、hold は大きく下げなければ勝ち、wait は帯の内側なら勝ち。`direction_accuracy_pct`(方向一致率)、`win_rate_pct` = 勝ち /(勝ち+負け)で中立は除外、`stop_loss_trigger_rate`、`take_profit_trigger_rate`、`avg_simulated_return_pct`。別系統の「決策シグナル事後評価」は 1/3/5/10 営業日の 4 窓、`watch` と `alert` は評価対象外、エンジン名 `decision-signal-v1`。
- **限界**: 精度の公表値はない。対象の中心は A 株で、規律は中国の個人投資家向け経験則。評価窓が 10 日で、寄り→引けの日中予測には読み替えが必要。

### 3. tradermonty/claude-trading-skills

- **状態**: MIT、星 約 3.0k、コミット 887。日本語 README(`README.ja.md`、`docs/ja/`)あり。売買シグナル配信でも自動売買でもなく、判断材料を出して人が決める設計。
- **構造**: `skills/<名前>/SKILL.md` + `references/` + `scripts/`、索引 `skills-index.yaml`、複数スキルの手順 `workflows/*.yaml`(12 本)。Claude Code では `~/.claude/skills/` かプロジェクトの `.claude/skills/` にコピー。
- **signal-postmortem**: 入力は `state/signals/` の JSON(`signal_id`、`ticker`、`signal_date`、`predicted_direction`、`source_skill`、任意で `entry_price`)。出力レコード: `schema_version`、`postmortem_id`、`signal_id`、`ticker`、`signal_date`、`source_skill`、`predicted_direction`、`entry_price`、`realized_returns`(`5d`、`20d`)、`exit_price`、`exit_date`、`holding_days`、`outcome_category`、`regime_at_signal`、`regime_at_exit`、`outcome_notes`、`recorded_at`。フィードバックは 2 種: 重み提案 JSON(`skill`、`current_weight`、`suggested_weight`、`reason`、`sample_size`、`min_sample_threshold`。**20 シグナル未満では重みを動かさない**)と、改善バックログ YAML(`skill`、`issue_type`、`severity`、`evidence`、`suggested_action`)。スクリプト `scripts/postmortem_recorder.py`(`--list-ready --min-days`、`--holding-periods 5,20`)、`scripts/postmortem_analyzer.py`(`--generate-weight-feedback`、`--generate-improvement-backlog`、`--summary --group-by skill,month`)。
- **trader-memory-core**: 仮説 1 件を `state/theses/<thesis_id>.yaml`(`schemas/thesis.schema.json` で検証)、索引 `_index.json`、事後検証レポート `state/journal/pm_<thesis_id>.md`。状態は IDEA → ENTRY_READY → ACTIVE → PARTIALLY_CLOSED → CLOSED / INVALIDATED の前進のみ。`review-due --as-of` で見直し期限の来た仮説を列挙。
- **trade-memory-loop**: ①結果記録 ②事後検証(原因を 仮説の質/執行/地合い/偶然 に分類)③コーチ(次回の運用ルール案を 採用/修正/保留/記録のみ で人が裁定)④バックテストで仮説を再検証 ⑤教訓を追記。
- **限界**: 価格取得は FMP API(米国株前提、無料枠 250 回/日)。日本株データ源は入っていない。

### 4. ACE(Agentic Context Engineering)

- **論文**: Zhang ら(Stanford / SambaNova ほか)arXiv:2510.04618、2025-10-06 提出、ICLR 2026。リポジトリ `ace-agent/ace`(Apache-2.0、星 約 1.4k)。
- **中身**: 文脈を「育つ手順書(playbook)」として扱う。全文を毎回書き直すと細部が失われる(context collapse)ことと、要約が短くなりすぎて専門知識が落ちる(brevity bias)ことを問題視。箇条書き単位で ID と helpful/harmful カウンタを持ち、Curator は差分(追記とカウンタ更新)だけを出し、マージは LLM でなく決定論的コードが行う。重複は埋め込み類似度で統合(既定しきい値 0.9)。Reflector の磨き直しは最大 5 回、オフライン学習は最大 5 エポック、バッチ 1。
- **金融ベンチマークの数値**(DeepSeek-V3.1、ベース平均 69.1): オフライン+正解あり 81.9(FiNER 78.3 / Formula 85.5)、オフライン+正解なし 77.1、オンライン+正解あり 76.6、オンライン+正解なし 72.9(ただし FiNER は 67.3 でベース 70.7 を下回る)。比較手法 Dynamic Cheatsheet は正解なしのオンラインで 65.4 とベース未満。
- **本プロジェクトへの読み替え**: docs の因果ルール 1 行 = playbook の箇条書き 1 行。予測時に「使ったルール ID」を出力させ、採点確定後に当たり=helpful、外れ=harmful を加算。ルールの追加・文言変更は週次で差分提案 → 人が承認。
- **限界**: 題材は固有表現抽出と数式計算で、株価予測ではない。株価は正解のノイズが大きいので、1 件の当たり外れでルールを書き換えるとノイズを学習する。

### 5. virattt/ai-hedge-fund(現行版)

- **状態**: MIT、星 63,963、push 2026-10-02。構成が `src/` から `hedge_fund/` に刷新され、CLI は `aihf`(`pipx install aihf`)。
- **設計原則**(`hedge_fund/README.md`): データ(時点整合)→ アルファモデル → ポートフォリオ → リスク → 執行 → 台帳。任意の模擬日には**その日までに提出済みのデータだけ**が見える(決算期ではなく提出日でフィルタ)。**T の引けで決めて T+1 の引けで約定**(バックテストも紙上取引も同じ)。LLM(Buffett / Munger / Graham / Lynch / Druckenmiller の人格)は見解と文章だけを出し、サイズ決定と発注は決定論的コード、リスク上限はハードゲート。台帳は追記専用。
- **紙上台帳**(`~/.hedge-fund/paper/<name>/`): `fund.yaml`、`broker.json`、`ledger/<session>.json`(ハッシュ連鎖)、`control.json`(停止スイッチ)、`events.jsonl`。`aihf paper tick <name>` で未記録の 1 セッションだけ進める。照合不一致は自動修復せずエラーで停止。
- **統計**: `event_study/`(市場モデルの異常リターン CAR)は実装済み、`validation/`(CPCV、PBO)は計画段階。
- **限界**: データは Financial Datasets(有料 API キー必須、米国株)。日本株は対象外。成績の公表なし。

### 6. ライブ(先読み不能)環境での実成績

| ベンチマーク | 期間・市場 | 設定 | 結果(ベースライン比) | 出典 |
|---|---|---|---|---|
| StockBench | 2025-03-03〜06-30(82 営業日)、ダウ上位 20 銘柄、$100K、毎朝寄りで判断 | 14 モデル、各 3 シード平均 | 等加重 Buy&Hold +0.4%(最大 DD −15.2%)。最高は Qwen3-235B-Think +2.5%、Kimi-K2 +1.9%(総合 1 位)、Claude-4-Sonnet +2.2%、GPT-5 +0.3%、GPT-OSS-20B −2.8%。**下落局面(2025-01〜04)ではどの LLM もベースラインに勝てず**、上昇局面(05〜08)では大半が勝った | arXiv 2510.02209 |
| DeepFund | 2025-03-17〜04-17(24 営業日、FOMC と関税ショックを含む)、米 5 銘柄、$100K | 9 モデル、日次 | **9 中 8 が損失**。Grok 3 mini +1.1%、Gemini 2.5 Flash −1.9%、Claude 3.7 Sonnet −3.7%、DeepSeek-V3 −5.7%、GPT-4.1 −5.9%、Doubao −8.1%。同期間の S&P 500 は −6.91%(損失が小さいモデルは現金比率が高くベータ 0.35〜0.94)。総費用 約 $100 | arXiv 2505.11065(NeurIPS 2025 D&B) |
| Agent Market Arena | 2025-08-01〜09-30、TSLA / BMRN / BTC / ETH、日次 | 4 構成 × 5 モデル+多数決 | Buy&Hold: TSLA +46.88%、BMRN −6.89%、BTC +0.66%、ETH +18.56%。**TSLA では全エージェントが Buy&Hold 未満**(最良 InvestorAgent+GPT-4.1 で +40.83%、Sharpe は 6.47 対 6.00 で上回る)。TradeAgent(TradingAgents 由来)は TSLA で −38.72%〜+21.91%。ETH で Buy&Hold を超えたのは HedgeFundAgent(+39.66%)のみ | arXiv 2510.11695 |
| LiveTradeBench | 2025-08-18〜10-24(50 営業日)、米 15 銘柄+現金、Polymarket 10 市場 | 21 モデル | 株は全モデルがプラス(+1.78%〜+6.25%、GPT-4.1 が最高)だが、取得した範囲では**指数ベースラインの記載なし**。Polymarket は 21 中 4 だけプラス(Claude-Sonnet-3.7 +20.54%、Grok-4 +7.38%)、最悪 −57.62%。LMArena スコアとの順位相関は株 0.054、Polymarket −0.38 | arXiv 2511.03628 |
| AI-Trader | 米国株 2025-10-01〜11-07(1 時間足)、A 株 同期間(日足)、暗号資産 2025-11-01〜11-14 | 6 モデル | 米国株: QQQ +1.87% に対し MiniMax-M2 +9.56%、DeepSeek-v3.1 +8.39%、Claude-3.7-Sonnet +3.11%、GPT-5 +1.56%、Qwen3-Max +0.39%、Gemini-2.5-Flash −0.06%。A 株: SSE-50 +1.65% を**超えたモデルなし**(最良 +1.31%)。暗号資産: CD5 −14.30% を上回ったのは DeepSeek(−12.18%)のみ | arXiv 2512.10971 |
| Alpha Arena Season 1 | 2025-10-18〜11-03(17 日)、Hyperliquid の暗号資産無期限先物、各 $10,000 実弾 | 6 モデル | Qwen3 Max $12,231(約 +22%)、DeepSeek $10,489、Claude Sonnet 4.5 $5,799、Gemini 2.5 Pro $5,445、Grok $4,208、GPT-5 $4,126(別報道では約 $3,733)。**6 中 4 が 4 割超の損失** | 二次報道(ForkLog、GNcrypto)。公式は未確認 |
| Alpha Arena Season 1.5 | 2025 年 11 月下旬〜12 月初旬(約 2 週間)、米国株、4 条件並走 | 8 モデル | 匿名参加モデル(後に Grok 4.20 と報道)が平均約 +12% で 4 条件すべて黒字。2 位 GPT-5.1、3 位 Gemini 3。報道時点で**黒字は 1 モデルのみ** | 二次報道(ForkLog)。公式は未確認 |

読み方の注意:
- 期間が 2 週間〜4 か月と短く、1 構成 1 回の実行が多い。Sharpe 6 のような値は期間の短さの産物。
- 「プラスだった」ことと「ベースラインに勝った」ことは別。上昇相場ではロングに偏った LLM は絶対リターンがプラスになりやすい。
- 寄り→引けの日中方向を当てる形式のライブベンチマークは、今回確認した範囲には無かった(いずれもポートフォリオ運用の損益で評価)。

### 7. 学習データ混入(先読み)への対処の類型

| 手法 | 採用例 | 評価 |
|---|---|---|
| モデルのカットオフ後の期間だけで評価 | StockBench(2025-03 以降)、DeepFund、LiveTradeBench | 有効。ただしモデルが更新されるたびに期間を後ろへずらす必要がある |
| 実時間のライブ運用 | Alpha Arena、Agent Market Arena、AI-Trader、DeepFund | 最も確実。結果が出るのに時間がかかる |
| ツール側で日付を強制 | TradingAgents `dataflows/date_window.py`(`as_of` は未来日を実行日に置換、`as_of_window` は窓を実行日で打ち切り、提出日のないプロフィール・インサイダー取引・財務は過去日実行で伏せる、FRED は当時のビンテージに固定 #1275)。テスト `tests/test_news_lookahead.py`、`test_social_lookahead.py`、`test_fundamentals_lookahead.py`、`test_memory_pointintime.py`、`test_tool_date_enforcement.py` | 入力データの漏れは防げるが、**モデル内部の暗記は防げない** |
| 記憶の時点フィルタ | TradingAgents `get_past_context(as_of=...)`(その日までに決済済みの教訓のみ) | 自作の反省メモ経由の漏れを防ぐ。必須 |
| 提出日ベースのデータ | ai-hedge-fund(決算期でなく提出日でフィルタ)、TradingAgents の SEC EDGAR | 財務データの先読み防止の基本 |
| 翌足約定 | FINSABER(既定 `next_open`)、ai-hedge-fund(T 決定→T+1 約定) | 同日先読み防止の基本 |
| 社名の匿名化 | Glasserman & Lin(arXiv 2309.17322) | 学習期間内では匿名化した見出しのほうが成績が良い(社名への先入観が判断を歪める)。ただし Lopez-Lira らは「マスクしても文脈から復元される」と報告しており、暗記対策としては不十分 |
| 「カットオフ以降を知らないふりをせよ」と指示 | — | **無効**(Lopez-Lira, Tang, Zhu, arXiv 2504.14765) |
| 反実仮想テスト | Profit Mirage の FactFin(ニュースの善し悪しを反転、直近 5 日のトレンドを反転、セクター動向を反転して判断が変わるかを見る)、Alpha Illusion の P3 | 暗記で答えているかの診断に使える。日次運用で常時やるには重い |
| 暗記の測定 | Profit Mirage の FinLake-Bench(2022-01〜2023-06 の 2,000 問。「その日相場は上がったか」などに GPT-4o 等が 85〜93% 正答) | 過去期間の検証が無意味であることの証拠 |

本プロジェクトでの結論: 毎朝の予測を寄り前のタイムスタンプ付きで追記専用台帳に書く限り、LLM 予測は前向き記録となり混入は起きない。過去日に対して LLM に「予測」させる検証は、その日がモデルのカットオフより前なら混入する。**使用モデル名・版・公表カットオフを全レコードに記録**し、モデルを替えたら成績系列を分ける。

### 8. 過去期間バックテスト型の先行研究(参照のみ)

| 名前 | 中身 | 状態 | 反証・減衰 |
|---|---|---|---|
| FinMem(arXiv 2311.13743) | プロファイル+層状メモリ+意思決定。`pipiku915/FinMem-LLM-StockTrading`、MIT、星 963。既定の試験期間 2022-06-30〜2022-10-11(TSLA) | 更新停滞(コミット 55) | FINSABER: 2004〜2024 で TSLA 以外は Buy&Hold に Sharpe で劣後(NFLX 0.293 対 0.622、AMZN 0.188 対 0.551、MSFT 0.203 対 0.461)、強気相場 Sharpe −0.19、弱気相場 −0.97。Profit Mirage: 総リターン 71.85% 減衰(最大) |
| FinAgent(arXiv 2402.18485) | 市場情報+低次/高次の反省+ツール。`DVampire/FinAgent`、MIT、星 75、コミット 7 | 更新停滞 | FINSABER: 複合条件で Buy&Hold との差が有意(p = 7.7e-4 など)、強気相場 Sharpe 0.12 |
| FinCon(arXiv 2407.06567) | マネージャー–アナリスト階層、エピソードごとに「投資信念」を言語で更新。公式コードは未確認 | — | Profit Mirage: Sharpe 62.23% 減衰(最大) |
| InvestorBench(arXiv 2412.18174、ACL 2025) | FinMem 系エージェントで株・暗号資産・ETF を評価。`felis33/INVESTOR-BENCH`、MIT、星 33。試験期間は 2020〜2023 年 | 更新停滞 | 期間が現行モデルのカットオフより前 |
| QuantAgent(Y-Research-SBU) | 指標・パターン・トレンド・判断の 4 エージェント、価格のみ(ニュースなし)、1 分〜日足。MIT、星 約 2.9k | 最終更新日 未取得 | Alpha Illusion: 2025-01〜2026-01 で $100K → ネット $77.9K、Sharpe −0.96 → −1.15 |
| FinGPT / FinRobot | FinGPT-Forecaster はダウ 30 を対象に翌週の方向を出す Llama2-7b の LoRA(学習データ 2023-05〜2024-05)。FinRobot は調査レポート生成が中心。MIT / Apache-2.0、星 21.4k / 8.2k | FinGPT の新着は 2023-11 が最後 | 他市場は再学習が必要と明記。日本株には直接使えない |
| SEP(WWW 2024) | 要約→説明→予測、自己反省つき。`koa-fin/sep`、星 172、**ライセンス表示なし**(コード転用不可) | コミット 2 | — |
| TradingAgents-CN | A 株向け派生、星 32.3k。**アプリ層は独自ライセンスで再配布・商用不可** | 活発 | 写す対象にしない |
| Trading-R1 | Tauric の取引特化モデル。リポジトリは README のみ(星 505) | 未公開 | — |

### 9. 日本株まわりの現状

- **データ接続**: `shigechika/jquants-mcp`(J-Quants API v2、MIT、PyPI で頻繁に更新)。J-Quants 公式組織には `jquants-api-client-python`(Apache-2.0、星 195、2026-09-30 更新)、`jquants-cli`(Rust)、`j-quants-doc-mcp`(中身未確認)がある。`dexter-kabu-jp` の `CLAUDE.md` によると J-Quants Free は直近 12 週のみ、4 桁コードは末尾 0 を付けて 5 桁、株式分割があるので調整済み項目(`AdjO` / `AdjH` / `AdjL` / `AdjC` / `AdjVo`)を必ず使う。
- **適時開示**: `ajtgjmdjp/tdnet-disclosure-mcp`(非公式 Yanoshin API 経由)。`shisakulab/ai-trade-check` も同 API を使用。
- **予測の採点まで持つ日本株リポジトリ**:
  - `shisakulab/ai-trade-check`: 2025-01〜2026-09、元本 100 万円。外部 AI が 30 銘柄選定(2 回平均)+38.0%(最大 DD 7.1%)、モメンタムのみ +52.1%、モメンタム+AI 拒否権 +41.4%、日経 225 +68.8%、ACWI(円)+36.1%。10 年(2016-01〜2026-09)ではモメンタム +24.5%(年率 +2.1%)対 ACWI +287.7%。AI の実行ごとのぶれは約 ±7%。作者自身が生存者バイアスと先読みの可能性を明記し、指数投資のほうが良いと結論。外部 AI の結果は公開コードでは再現不能。
  - `Tomato-1101/scalplab`: RCI × パラボリック SAR のデイトレ規則は、往復コスト+スプレッドを正しく入れると優位性が消えた。初期のギャップ研究に先読みバグがあり修正済み。成績数値は意図的に非公開。
  - `Yurikada/jp-stock-screener`: スコアは較正された確率ではないと明記。事後リターンによる閾値の自動調整は未実装。
- **TradingAgents を日本株に当てる日本語記事**(Zenn、2025-07-31)は動作確認のみで、定量評価なし。

---

## 因果ルール候補(該当する場合。1 件ずつ)

本観点は「相場の因果」よりも「LLM 予測器と検証手続きの因果」が中心。docs のルールベース予測を運用する側の規則として使う。

### R1. 学習期間内の検証成績は水増しされる
- IF: LLM に過去日(モデルのカットオフ以前)の予測をさせて成績を測る → THEN: 期間外では Sharpe が 5〜6 割、総リターンが 5〜7 割落ちる前提で読む(時間軸: 検証全体)
- なぜ: モデルが当時の値動きやニュースの帰結を暗記しており、予測ではなく想起で当てる
- 根拠: Profit Mirage(arXiv 2510.07920、NASDAQ-100、GPT-4o、期間内 2021 Q2〜Q3 対 期間外 2024 Q3〜Q4)で Sharpe 減衰 51.48〜62.23%、総リターン減衰 50.18〜71.85%。FinLake-Bench で過去の騰落を 85〜93% 正答。Lopez-Lira ら(arXiv 2504.14765)はカットオフ前の経済・金融データの正確な想起を確認し、カットオフ後は想起なしと報告
- 効かなくなる条件: 検証期間が使用モデルのカットオフより後、または実時間の前向き記録
- 判定に必要なデータと入手時刻: 使用モデルの版と公表カットオフ(予測時に記録)
- 確度: B(単独研究 2 本が同方向、査読状況は未確認)

### R2. 下落局面では LLM エージェントは受動ベースラインに勝ちにくい
- IF: 指数が下落トレンド(例: 直近数か月が下げ基調、年率 −20% 級) → THEN: LLM の買い判断の超過リターンは期待しない。受動比で劣後しやすい(時間軸: 数週間〜数か月)
- なぜ: LLM はロング寄りで、損失局面での縮小が遅い。FINSABER の表現では「報われる局面で慎重すぎ、罰せられる局面で積極的すぎる」
- 根拠: StockBench(2025-01〜04 の下落局面でどの LLM も受動ベースライン未満、05〜08 は大半が上回る)。FINSABER(米国株 2004〜2024、弱気年の Sharpe: Buy&Hold −0.28、FinAgent −0.38、FinMem −0.97、強気年: 0.61 / 0.12 / −0.19)。DeepFund(2025-03〜04 の急落期に 9 中 8 が損失)
- 効かなくなる条件: 現金比率を機械的に上げる規則を別に持つ場合(DeepFund の Grok は現金約 60% で唯一プラス、AI-Trader の DeepSeek は高い現金比率で暗号資産の下落を軽減)
- 判定に必要なデータと入手時刻: 指数の移動平均・ドローダウン(前日引け後に確定)
- 確度: B(独立した 3 研究が同方向。ただし各期間は短いか、対象モデルが古い)

### R3. 汎用ベンチマークの順位は予測成績を予言しない
- IF: 「より賢い」モデル(LMArena 上位、新しい世代)に替える → THEN: 予測成績の改善は期待しない。替えたら別系列として採点し直す
- なぜ: 言語・推論能力と、ノイズの多い時系列での意思決定は別の能力。数値時系列の扱いが弱いという主催者の所見もある
- 根拠: LiveTradeBench(21 モデル、2025-08-18〜10-24、順位相関 株 0.054、Polymarket −0.38)。Agent Market Arena(構成の差 > バックボーンの差)。Alpha Arena Season 1(GPT-5 が最下位)。AI-Trader(GPT-5 +1.56% 対 MiniMax-M2 +9.56%)
- 効かなくなる条件: 未確認(長期・多市場での検証はまだない)
- 判定に必要なデータと入手時刻: 自前の採点台帳(モデル版つき)
- 確度: B

### R4. 取引コストを入れると LLM エージェントの優位は半減以下になる
- IF: グロス成績だけで評価している → THEN: ネットでは Sharpe が半分程度まで落ちる可能性を織り込む。売買回数が多い構成ほど不利
- なぜ: LLM は毎回見解を変えやすく回転が高い。手数料・スプレッド・市場インパクト・API 費用が積み上がる
- 根拠: The Alpha Illusion(arXiv 2605.16895、2025-01〜2026-01、TradingAgents の Sharpe 0.43→0.22、$106.4K→$102.3K で Buy&Hold $104.8K 未満。先行 5 システムの摩擦 8 項目のうち 40 中 35 が未モデル化)。FINSABER(FinMem の手数料比率は FinAgent の 5〜9 倍)。scalplab(日本株デイトレ規則の優位が往復コスト+スプレッドで消滅、個人の報告)
- 効かなくなる条件: 売買しない予測採点だけの運用(本プロジェクト)。ただし「実際に張れたか」を主張するなら必要
- 判定に必要なデータと入手時刻: 予測ごとの想定売買と気配スプレッド
- 確度: B

### R5. ニュースとファンダを入力から抜くと成績が落ちる
- IF: LLM に価格だけを渡す → THEN: ニュース+ファンダも渡した場合より成績が下がる(目安: 4 か月の累積で 1〜2 ポイント)
- なぜ: 価格系列だけでは LLM の強み(文章の解釈)が使えない
- 根拠: StockBench の切除実験(2025-03〜06、Kimi-K2: 全入力 +1.9% → ニュースなし +1.4% → ニュース・ファンダなし +0.6%。GPT-OSS-120B: −1.2% → −1.2% → −3.4%)
- 効かなくなる条件: 2 モデル・1 期間のみで、差はばらつきの範囲内かもしれない(銘柄数 20 での標準偏差は 1.7〜3.9)
- 判定に必要なデータと入手時刻: 入力条件を変えた並走実験
- 確度: C

### R6. 機械的規則に LLM の拒否権を足すと、かえって成績を落とすことがある
- IF: モメンタムなどの機械的シグナルに LLM の拒否権(veto)を重ねる → THEN: 上昇相場では取りこぼしが増え、リターンが下がる可能性
- なぜ: LLM は理由を見つけて見送りがちで、強いトレンドの銘柄ほど「過熱」と判断しやすい(推測)
- 根拠: shisakulab/ai-trade-check(日本株、2025-01〜2026-09、モメンタムのみ +52.1% 対 拒否権つき +41.4%、2 回平均)
- 効かなくなる条件: 下落局面では拒否権が損失を減らす可能性(未検証)。外部 AI の中身が非公開で再現不能
- 判定に必要なデータと入手時刻: 拒否権あり/なしを両方記録する並走台帳
- 確度: C(個人プロジェクト、再現不能、生存者バイアスあり)

### R7. 同じ入力でも LLM の出力はぶれる
- IF: 1 回の実行結果だけで予測を確定する → THEN: 実行ごとに結論が変わりうる(累積成績で ±7% 程度の差の報告)。複数回サンプルして多数決か平均を取る
- なぜ: サンプリングの確率性と、取得時点で変わるライブデータ
- 根拠: ai-trade-check(同条件の反復で約 ±7%)。StockBench(3 シード平均を採用、銘柄 20 で標準偏差 1.7〜3.9)。TradingAgents の README とバックテスト出力の注記(1 セル 1 サンプルで再現不能)
- 効かなくなる条件: temperature を固定できるモデルでも、ツール結果が変われば再現しない
- 判定に必要なデータと入手時刻: 同一入力での反復実行ログ
- 確度: B

### R8. 信頼できる採点なしに手順書を自己更新すると劣化する
- IF: 結果が未確定、または 1 件の当たり外れだけを材料に docs のルールを書き換える → THEN: ルール集の精度がベースより下がりうる
- なぜ: ノイズや誤った教訓が文脈に溜まる。全文書き直しは細部を消す
- 根拠: ACE(arXiv 2510.04618、正解なしのオンライン更新で FiNER 67.3 対 ベース 70.7。Dynamic Cheatsheet は平均 65.4 対 69.1)。claude-trading-skills の signal-postmortem(重み変更は 20 シグナル以上)。scalplab(挑戦者は旗を立てるだけでチャンピオンを自動差し替えしない)
- 効かなくなる条件: 採点が確定した結果のみを使い、件数しきい値と人の承認を挟む場合
- 判定に必要なデータと入手時刻: ルール ID ごとの helpful / harmful カウンタ(引け後に更新)
- 確度: B

### R9. 短い記録では当たり外れを統計的に区別できない
- IF: 予測件数が数百件未満 → THEN: 的中率 50% 台前半の差は偶然と区別できない。結論を出さない
- なぜ: 標本誤差。的中率の 95% 信頼区間の半幅は約 1.96 × √(0.25 / n)。n = 100 で ±9.8 ポイント、250 で ±6.2、400 で ±4.9、1,000 で ±3.1、2,500 で ±2.0(本ノートでの計算。同日の複数銘柄は相関するので実効件数はさらに少ない)。年率 Sharpe の標準誤差は約 √((252 + SR²/2) / T)(T は日次観測数)で、1 年分・SR = 1 なら約 ±2.0 の 95% 区間
- 根拠: The Alpha Illusion が Lo(2002)の式を引用し、1 年の検証ではエージェントと Buy&Hold の差が区間内に収まると指摘。FinBen の GPT-4 取引 Sharpe は 1.51 ± 1.08
- 効かなくなる条件: なし(統計の性質)
- 判定に必要なデータと入手時刻: 採点台帳の件数
- 確度: A(統計学の標準結果)

### R10. 「意見が割れたら Hold」にすると予測が中立に潰れる
- IF: 強気と弱気の材料が両方あるときに無条件で Hold / 様子見を許す → THEN: 方向を出す予測が減り、採点できる件数が減る。強い側に寄せて確信度で濃淡をつけさせる
- なぜ: LLM は対立する情報があると中立に逃げやすい
- 根拠: TradingAgents の審判プロンプト(割れていること自体は Hold の理由にならない、Hold は拮抗か証拠不足のときだけ)と、読めない評価を Hold でなく REVIEW に分ける修正(v0.4.0 #1170)。バックテストでは Hold を hit rate の対象外にしている。効果量の公表はない
- 効かなくなる条件: 無理に方向を作らせると自信過剰になる(プロンプト自身が「決断的に見せるために方向を捏造するな」と注意)
- 判定に必要なデータと入手時刻: 評価別の件数分布
- 確度: C(設計上の経験則)

### R11. 乖離率が大きい銘柄を追いかけない(実務経験則)
- IF: 終値が 5 日移動平均から +5% 超 → THEN: 新規の買い判断は「様子見」に格下げ。+2% 未満が最良、MA5 > MA10 > MA20 が前提。強いトレンドの主導株は閾値を 1.5 倍(7.5%)に緩和(時間軸: 数日〜10 営業日)
- なぜ: 短期の過熱後は平均への押しが入りやすいという経験則
- 根拠: daily_stock_analysis の `strategies/README.md` と `src/analyzer.py`、`BIAS_THRESHOLD=5.0`(中国 A 株の個人投資家向け。統計的な効果量の提示なし)
- 効かなくなる条件: 値幅制限・呼値・投資家構成が違う日本株で同じ閾値が妥当かは不明。寄り→引けの日中方向とは時間軸が違う
- 判定に必要なデータと入手時刻: 日足終値と移動平均(前日引け後)
- 確度: C

### R12. 出来高の細った押し目は続伸の候補(実務経験則)
- IF: MA5 > MA10 > MA20 の上昇中に、価格が MA5 から 1% 以内(または MA10 から 2% 以内)まで押し、押しの出来高が 5 日平均の 70% 未満、かつ悪材料ニュースなし → THEN: 買い候補としてスコア +10(MA10 かつ出来高 0.6 倍未満なら +8)。損切りは MA20
- なぜ: 売り圧力が弱い押しはトレンド継続の中の一服とみなす
- 根拠: daily_stock_analysis `strategies/shrink_pullback.yaml`(統計の提示なし)
- 効かなくなる条件: 下落相場、決算や適時開示の直後
- 判定に必要なデータと入手時刻: 日足の価格・出来高(前日引け後)、ニュース(寄り前)
- 確度: C

### R13. 社名を伏せたほうがニュース感情の判定は歪みにくい
- IF: ニュース見出しの感情を LLM に採点させる → THEN: 社名を匿名化して渡すほうが、既知企業への先入観による歪みが減る
- なぜ: モデルが企業について持つ一般知識が見出しの読みを邪魔する
- 根拠: Glasserman & Lin(arXiv 2309.17322、米国株、学習期間内で匿名化見出しのほうが成績良好、大型株ほど顕著)
- 効かなくなる条件: 暗記対策としては不十分(Lopez-Lira らは文脈から復元されると報告)。期間外では先読みは問題にならないが先入観は残りうる
- 判定に必要なデータと入手時刻: 見出しテキスト(寄り前)
- 確度: B(単独研究)

---

## 落とし穴・反証・注意

1. **星の数は成績の証拠ではない。** 星が 6 万〜11 万の TradingAgents / daily_stock_analysis / ai-hedge-fund はいずれも実運用成績を公表していない。独立検証(Profit Mirage、Alpha Illusion、AMA)では優位が確認されていない。
2. **「ライブで勝った」報告は期間が短い。** Alpha Arena Season 1.5 の +12% は約 2 週間、AI-Trader の MiniMax-M2 +9.56% は 5 週間強。主催者の利害もある(Alpha Arena は nof1 の宣伝、AI-Trader は自社プラットフォーム)。
3. **論文表の数値に不整合がある。** AMA は累積リターンがマイナスなのに Sharpe がプラスの行があり、HedgeFundAgent は 5 モデルで結果が完全に同一。AI-Trader の CD5 の Sharpe −12.71 は誤記の疑い。Alpha Illusion の本文に「55 銘柄中 44」という 5 銘柄と合わない記述。DeepFund の本文と表でドローダウン値が食い違う。**引用前に原典 PDF を確認する。**
4. **リポジトリは変質する。** HKUDS/AI-Trader はベンチマークからエージェント向け取引プラットフォームに転換し、論文当時のコードは main にない。ai-hedge-fund は `src/` 構成から `hedge_fund/` に全面刷新。TradingAgents は v0.2.4 で BM25 メモリを廃止して決定ログに置換。古い解説記事(2025 年の Zenn など)の手順はそのままでは動かない。
5. **ライセンスの罠。** live-trade-bench は PolyForm Noncommercial(非商用のみ)。TradingAgents-CN のアプリ層は独自ライセンス。KabuForge と nofx は AGPL-3.0。koa-fin/sep はライセンス表示なし。HKUDS/AI-Trader は API とページで表示が食い違う。Apache-2.0 / MIT のものは著作権表示とライセンス文の同梱が条件。
6. **日本株で使えないデータ源。** ai-hedge-fund は Financial Datasets(米国株・有料)、claude-trading-skills は FMP / FINVIZ(米国株)、StockBench は Polygon / Finnhub。日本株は yfinance(`.T`、終値ベース・遅延)と J-Quants に差し替えが要る。tdnet 系 MCP は非公式 API 依存。
7. **TradingAgents の決済は終値→終値。** 寄り→引けの日中予測を採点するには、始値基準に改造し、ベンチマークも同じ区間で取る必要がある。`^N225` は Yahoo の指数系列で、配当込みではない。
8. **LLM の確信度は確率ではない。** Alpha Illusion が P4 で較正の報告を要求している通り、「confidence: high」と的中率の対応は自分で測るまで不明。
9. **多エージェント化の効果は未証明。** AMA では単一エージェント(InvestorAgent)が多エージェント(TradeAgent)より安定。Alpha Illusion の P6 は単独エージェントとの比較を必須としている。まず 1 回の LLM 呼び出しで始めるのが安い。
10. **本ノートの数値は WebFetch の要約経由。** 小型モデルが表を読み違えている可能性がある(例: DeepFund の「S&P 500 に全モデルが劣後」という要約は表の数値と合わず、本ノートでは表の数値を採った)。

---

## このプロジェクトへの提案(MVP で採用するもの、後回しにするもの)

### MVP で採用

1. **予測台帳は TradingAgents の memory log 方式を写す。** 追記専用、保留→決済の 2 状態、冪等、原子的書き込み、`<!-- ENTRY_END -->` 区切り。ai-hedge-fund に倣いレコードにハッシュ連鎖を付け、寄り前に書いたことを後から証明できるようにする(git コミットでも代用可)。
2. **予測の出力スキーマ(案。上記各ソースの要素を合成した本プロジェクト用の設計)**:
   - `pred_id`、`created_at`(JST、寄り前であること)、`trade_date`、`ticker`(`7203.T` 形式)、`horizon`(`open_to_close` 固定から開始)
   - `direction`(up / down / flat)、`prob_up`(0〜1)、`expected_move_pct`(任意)、`confidence`(low / medium / high)
   - `rule_ids`(使った docs ルールの ID 配列。ACE のカウンタ更新に使う)
   - `strongest_bull`、`strongest_bear`(daily_stock_analysis の `signal_attribution` に相当)
   - `invalidation`(この条件が起きたら予測の前提が崩れる、という一文)
   - `data_asof`(各入力の取得時刻)、`data_limitations`
   - `predictor`(`ml` / `docs_rule`)、`model`、`model_cutoff`、`docs_commit`(手順書の git ハッシュ)
3. **採点は TradingAgents `backtest.py` と daily_stock_analysis の定義を合成。** 方向一致率(flat は中立帯で判定、帯の幅は日中用に小さく設定して `ENGINE_VERSION` で管理)、指数比 alpha の符号による hit rate、Brier スコア(`prob_up` の較正)、ルール ID 別・確信度別・地合い別の集計。Hold / flat は hit rate から除外して件数だけ報告。
4. **対照を最初から並走させる。** 常に上、前日と同方向、前日と逆方向、ランダム、機械学習のみ、docs なしの LLM、docs ありの LLM。StockBench 流に受動ベースラインとの差で語る。
5. **引け後の反省は TradingAgents の Reflector 形式。** 2〜4 文、数値を引用、教訓は 1 つ、窓が短くて判断不能ならそう書く。加えて signal-postmortem の 4 分類(当たり / 外れ / 見送って機会損失 / 地合い不一致)を機械的に付ける。
6. **docs のルールは ACE 形式の 1 行 1 ルール。** `[rule-0001] helpful=0 harmful=0 :: IF … THEN …`。日次はカウンタ更新のみ。文言の追加・修正・削除は週次で差分案を作り、**該当ルールの採点済み件数が 20 以上**かつ人が承認したときだけ反映。全文書き直しは禁止。
7. **自然言語ルールのファイル形式は daily_stock_analysis の strategy YAML を写す。** `name`、`category`、`market_regimes`、`required_tools`、`instructions`。地合いタグで適用ルールを絞る。
8. **日付の強制は TradingAgents `date_window.py` を写す。** すべてのデータ取得関数に実行日を渡し、未来日は実行日に置換、提出日のないデータは過去日実行で伏せる。先読みテスト(`tests/test_*lookahead*.py` の考え方)を自前のデータ層にも書く。
9. **LLM は見解だけ、数値計算と採点はコード。** ai-hedge-fund の原則。StockBench の誤り分析でも LLM の主な失敗は算術と JSON 形式だった。
10. **データ接続**: J-Quants(`jquants-api-client-python` か `shigechika/jquants-mcp`)、yfinance(`.T`)、TDnet(`tdnet-disclosure-mcp` の利用規約を確認のうえ)。
11. **毎日の起動は Windows タスクスケジューラ+バッチ**(ai-trade-check の `run_daily.bat` 方式)。PC を常時起動できないなら daily_stock_analysis のワークフロー YAML を写して GitHub Actions(cron は UTC 指定、JST 寄り前に合わせて設定し直す)。
12. **成績報告の書式は Alpha Illusion の P1 / P4 / P5 を最低限満たす。** モデル版とカットオフ、較正曲線、信頼区間つきの的中率。件数が 400 未満のうちは結論を書かない。

### 後回し

- TradingAgents の全構成(4 アナリスト+討論+リスク討論)の丸ごと導入。1 銘柄 1 回のコストが高く、多エージェントの上積みは未証明。まず 1 回の呼び出しで始め、後で A/B。
- 反実仮想テスト(FactFin 方式)。前向き記録だけなら混入は起きないので優先度は低い。
- 紙上のポートフォリオ運用(約定・現金・コストの模擬)。FINSABER か ai-hedge-fund の台帳を後から接続。
- 社名匿名化(R13)。効果が単独研究のみなので、並走実験の一条件として後で試す。
- Alpha Arena 式の複数条件並走(順位を見せる、資本保全重視など)。

---

## 未追跡の手がかり

- Alpha Arena の公式ページ(`alphaarena.ai` は 403、`nof1.ai/blog/...` は 404)。Season 1 のハーネス(プロンプトに入れたデータ、出力項目、既知の失敗モード)と 2026 年の後続シーズンの有無。出力項目に「無効化条件・確信度・根拠」があるという点は記憶に基づくもので今回は未確認。
- `trade-bench.live`(LiveTradeBench のライブ順位表、接続拒否)。2026 年の継続結果と指数ベースラインの有無。論文付録の後半(アブレーション)も未読。
- Agent Market Arena のライブ順位表と公式リポジトリの URL(`The-FinAI/Agent-Market-Arena` は 404)。
- HKUDS/AI-Trader の論文当時のベンチマークコード(旧ブランチ・タグ・別リポジトリの有無)とライセンスの正確な表示。
- TradingAgents: 1 実行あたりの実コスト(呼び出し回数・トークン)、Python 3.13 / Windows での動作、`tests/test_memory_pointintime.py` などの中身、`cli/run.py` の無人実行の詳細、issue #1251 / #1445 の議論。
- daily_stock_analysis: `docs/` 配下の市場対応表(日本株で使えない機能の一覧)、`evals/agent_trajectory/`、`strategies/` の残りの YAML(`event_driven.yaml`、`expectation_repricing.yaml`、`emotion_cycle.yaml` は材料・期待修正・地合い循環のルールで因果ルールの種になりそう)、`src/analyzer.py` の後半(約 13 万字未読)。
- claude-trading-skills: `references/outcome-classification.md`、`references/feedback-integration.md`、`schemas/thesis.schema.json`、`trade-hypothesis-ideator`、`market-news-analyst`、`stockbee-*` ワークフロー(日次の値動き研究)。
- ACE リポジトリのプロンプトファイルのパス、playbook の実例(`final_playbook.txt`)。
- `J-Quants/j-quants-doc-mcp` の中身、`ajtgjmdjp/japanfinance-agent`(EDINET / TDnet / e-Stat / 日銀 / ニュース / 株価の 6 ソース統合 MCP)、`Siyuan-chat/KabuForge`(AGPL、J-Quants ベースの研究基盤)、`YutaroSugaya/stock-bot`(LLM を発注経路の外に置く日本株ボット)、`virattt/dexter`(dexter-jp の元)。
- `HKUDS/Vibe-Trading`(星 35.3k、MIT)、`ValueCell-ai/valuecell`(星 11k、日本市場は予定のみ)、`NoFxAiOS/nofx`(星 13k、AGPL)、`microsoft/RD-Agent`(星 14.9k、MIT、LLM によるファクター研究の自動化)の README 詳細。
- FinCon の公式コード、FinMem / InvestorBench / QuantAgent / SEP の論文内数値、Trading-R1(arXiv 2509.11420)。
- 予測の当たり外れを直接競うライブ型ベンチマーク(ForecastBench、Prophet Arena、FutureX など)の混入対策と採点方法。今回は検索枠切れで未着手。
- FINSABER の付録 G(LLM の API 費用分析、未読部分)と FINSABER-2 の変更点。
- 日本語圏のブログ・Qiita・Zenn・note での「LLM で日本株を毎日予測して答え合わせ」実践記録。検索枠切れで 1 件しか拾えていない。

---

## 参照 URL 一覧(✅ 開いて確認 / ❓ 未確認・取得失敗)

### リポジトリ
- ✅ https://github.com/TauricResearch/TradingAgents (API、README、CHANGELOG、ツリー、`memory/log.py`、`memory/reflection.py`、`memory/settlement.py`、`agents/schemas.py`、`default_config.py`、`backtest.py`、`graph/trading_graph.py`、`dataflows/date_window.py`、`agents/analysts/market_analyst.py`、`news_analyst.py`、`agents/managers/portfolio_manager.py`、`research_manager.py`、`agents/researchers/bull_researcher.py`、`agents/trader/trader.py` を raw で確認)
- ✅ https://github.com/ZhuLinsen/daily_stock_analysis (API、README、`.github/workflows/00-daily-analysis.yml`、`AGENTS.md`、`SKILL.md`、`src/analyzer.py` 前半、`docs/full-guide.md`、`strategies/README.md`、`strategies/shrink_pullback.yaml`)
- ✅ https://github.com/tradermonty/claude-trading-skills (README、`skills/signal-postmortem/SKILL.md`、`skills/trader-memory-core/SKILL.md`、`workflows/`、`workflows/trade-memory-loop.yaml`)
- ✅ https://github.com/ace-agent/ace
- ✅ https://github.com/virattt/ai-hedge-fund (API、README、`hedge_fund/`、`hedge_fund/README.md`)
- ✅ https://github.com/HKUDS/AI-Trader (API、README、`research/`)
- ✅ https://github.com/ulab-uiuc/live-trade-bench
- ✅ https://github.com/ChenYXxxx/stockbench
- ✅ https://github.com/HKUSTDial/DeepFund
- ✅ https://github.com/waylonli/FINSABER
- ✅ https://github.com/shigechika/jquants-mcp
- ✅ https://github.com/J-Quants (組織ページ)
- ✅ https://github.com/edinetdb/dexter-jp (README、`RULES.md.example`)
- ✅ https://github.com/raditrejp/dexter-kabu-jp (README、`CLAUDE.md`)
- ✅ https://github.com/edinetdb/ai-berkshire-jp
- ✅ https://github.com/Siyuan-chat/KabuForge
- ✅ https://github.com/shisakulab/ai-trade-check
- ✅ https://github.com/Tomato-1101/scalplab
- ✅ https://github.com/Yurikada/jp-stock-screener
- ✅ https://github.com/polipoli0401/longterm-stock-lab
- ✅ https://github.com/ajtgjmdjp/tdnet-disclosure-mcp
- ✅ https://github.com/hsliuping/TradingAgents-CN
- ✅ https://github.com/FinStep-AI/ContestTrade
- ✅ https://github.com/Y-Research-SBU/QuantAgent
- ✅ https://github.com/HKUDS/Vibe-Trading (ページ上部のみ。README 詳細は未取得)
- ✅ https://github.com/ValueCell-ai/valuecell
- ✅ https://github.com/NoFxAiOS/nofx
- ✅ https://github.com/alpacahq/alpaca-mcp-server
- ✅ https://github.com/narumiruna/yfinance-mcp (`.T` での動作は未確認)
- ✅ https://github.com/pipiku915/FinMem-LLM-StockTrading
- ✅ https://github.com/DVampire/FinAgent
- ✅ https://github.com/felis33/INVESTOR-BENCH
- ✅ https://github.com/AI4Finance-Foundation/FinGPT
- ✅ https://github.com/AI4Finance-Foundation/FinRobot
- ✅ https://github.com/koa-fin/sep
- ✅ https://github.com/TauricResearch/Trading-R1
- ✅ https://api.github.com/repos/microsoft/RD-Agent (API のみ)
- ✅ https://github.com/topics/jquants 、 https://github.com/topics/tdnet 、 https://github.com/topics/japanese-stocks
- ❓ https://github.com/The-FinAI/Agent-Market-Arena (404)
- ❓ https://github.com/topics/trading-agents 、 https://github.com/topics/llm-trading (404)
- ❓ https://github.com/ajtgjmdjp/japanfinance-agent 、 https://github.com/J-Quants/j-quants-doc-mcp 、 https://github.com/YutaroSugaya/stock-bot 、 https://github.com/virattt/dexter (一覧で存在のみ確認、本体は未開封)

### 論文
- ✅ https://arxiv.org/abs/2412.20138 / https://arxiv.org/html/2412.20138v7 (TradingAgents)
- ✅ https://arxiv.org/abs/2510.02209 / https://arxiv.org/html/2510.02209v1 (StockBench)
- ✅ https://arxiv.org/abs/2511.03628 / https://arxiv.org/html/2511.03628v1 (LiveTradeBench。付録後半は一部のみ)
- ✅ https://arxiv.org/abs/2510.11695 / https://arxiv.org/html/2510.11695v1 (Agent Market Arena)
- ✅ https://arxiv.org/abs/2512.10971 / https://arxiv.org/html/2512.10971v1 (AI-Trader)
- ✅ https://arxiv.org/abs/2505.11065 / https://arxiv.org/html/2505.11065v2 (DeepFund)
- ✅ https://arxiv.org/html/2505.07078v3 (FINSABER。末尾約 1.4 万字は未読)
- ✅ https://arxiv.org/html/2510.07920v1 (Profit Mirage)
- ✅ https://arxiv.org/html/2605.16895v1 / https://www.alphaxiv.org/ja/overview/2605.16895 (The Alpha Illusion)
- ✅ https://arxiv.org/abs/2510.04618 / https://arxiv.org/html/2510.04618v1 (ACE)
- ✅ https://arxiv.org/abs/2504.14765 (The Memorization Problem。要旨のみ)
- ✅ https://arxiv.org/abs/2309.17322 (Glasserman & Lin。要旨のみ)
- ✅ https://arxiv.org/abs/2407.06567 (FinCon。要旨のみ)
- ❓ arXiv 2311.13743(FinMem)、2402.18485(FinAgent)、2412.18174(InvestorBench)、2509.11420(Trading-R1) — 本文未開封

### 記事・サービス
- ✅ https://forklog.com/en/ai-model-grok-4-2-triumphs-in-trading-tournament/amp (Alpha Arena Season 1 / 1.5 の結果、二次報道)
- ✅ https://www.gncrypto.news/news/qwen-wins-alpha-arena-season-1-with-22-percent-returns/ (Alpha Arena Season 1、二次報道)
- ✅ https://nof1.ai/ (トップページのみ。成績・ルールの記載なし)
- ✅ https://zenn.dev/yh007/articles/34e6efee5bd2da (TradingAgents を試した記事、2025-07-31、古い)
- ❓ https://alphaarena.ai/ (403)
- ❓ https://nof1.ai/blog/TechPost1 、 https://nof1.ai/blog (404)
- ❓ https://trade-bench.live/ (接続拒否)
- ❓ https://deepfund.paradoox.ai/ (README に記載、未開封)
- ❓ https://powerdrill.ai/blog/alpha-arena-season (検索結果の抜粋のみ)
