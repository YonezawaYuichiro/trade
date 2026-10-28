# 手法: 経験から育つルールブック(プレイブック)の設計

> 調査日: 2026-10-13 / 観点: self-improving-rulebooks / 状態: 一次調査(未検証)

調査メモ(作法の遵守状況)
- WebSearch は 18 回(英語 17、日本語 1)実行した時点で、セッション共有の検索上限に達して停止した(追加 2 回は未実行)。以降は既知 URL への WebFetch のみで確認している。日本語圏の探索が薄い点は「未追跡の手がかり」に記した。
- 実際に開いて中身を確認したソースは 45 件超(論文 HTML/抄録、GitHub の README・ソース・プロンプトファイル、仕様書、書籍サンプル PDF)。
- GitHub API は途中からレート制限(403)。それ以降のリポジトリは HTML ページでスター数・ライセンスのみ確認し、最終 push 日は「未確認」と明記した。
- 「提案値」と書いた数値は本ノート筆者の設計案であり、出典で検証された値ではない。出典由来の数値には出典を併記した。
- 本ノートは調査であり投資助言ではない。ここで扱う研究の多くは「LLM エージェントの汎用タスク」での結果で、株価予測での有効性を直接示すものではない。

## 結論(5〜10 行)

1. 最も直接の設計図は ACE(Agentic Context Engineering、arXiv 2510.04618、公式実装 ace-agent/ace は Apache-2.0)。ルールを「ID + helpful/harmful カウンタ + 本文」の箇条書き 1 件として持ち、Generator(予測)→ Reflector(振り返り)→ Curator(差分提案)の 3 役で回し、マージは LLM ではなく決定的なコードで行う。行フォーマットは `[str-00001] helpful=5 harmful=0 :: 本文`。
2. 絶対にやってはいけないのは「LLM にルールブック全体を書き直させる」こと。ACE 論文は、全文書き直しで文脈が 18,282 トークン→122 トークンに潰れ、精度が 66.7→57.1(無適応の 63.7 未満)に落ちた例(context collapse)を示している。更新は差分(delta)だけにする。
3. 振り返りの質は「正解ラベルの有無」で大きく変わる。ACE の金融ベンチ(オンライン)は正解ラベルなしだと平均 +3.8 にとどまり、FiNER 単体では −3.4 と悪化した。本プロジェクトは毎日引け後に確定値という正解が手に入るので、採点はプログラムが確定値で行い、LLM の自己判定を証拠にしない設計にすべき。
4. 票決プロトコルは ExpeL が最も具体的: 新規ルールは重み 2 で追加、賛成で +1、反対で −1、0 で削除、1 回の更新で最大 4 操作、満杯時は REMOVE 優先。ルール上限は論文設定で 8〜10 件。
5. ルール 1 件のスキーマは AutoManual の 4 属性(Rule Type / Rule Content / Example / Validation Logs)と、Sigma ルール仕様のライフサイクル(experimental → test → stable → deprecated / unsupported、ID は不変、ロジックを変えたら新 ID、`related` で系譜を残す、`falsepositives` を必須級で書く)を合成するのが最良。
6. ただし LLM 研究のカウンタ方式(3 回害があれば削除、等)をそのまま株に使うとノイズに過学習する。相場の 1 回の当たり外れはほぼコイン投げなので、昇格・降格は統計基準で縛る必要がある: 的中率は Wilson 下限(60/100 でようやく下限 0.502)、発掘型のルールは t 値 3 以上(Harvey-Liu-Zhu)、試した候補の総数 N を必ず記録(Deflated Sharpe Ratio)、効果は時間とともに縮む前提(McLean-Pontiff: 標本外 −26%、公表後 −58%)。
7. 人間側の型は SMB Capital の PlayBook(書籍サンプルで 7 項目を確認)+ decision journal(fs.blog の 8 項目、事前に確率を書く)+ Good Judgment Project の知見(基準率から入る、Brier スコアで採点)。
8. 表現形式は「1 ルール = 1 Markdown ファイル、先頭に YAML front matter(機械が読む条件・状態・カウンタ)、本文は固定見出し(人と LLM が読む因果の説明)」。先行例は Agent Skills の SKILL.md、Cursor の .mdc、MADR、Sigma。Python からは python-frontmatter(MIT)で読める。カウンタは人も LLM も手で書かず、追記専用の台帳からプログラムが再計算する。
9. LLM 売買エージェントの成績報告は割り引いて読む。FINSABER(KDD 2026)は長期間・多銘柄で評価すると既報の優位が大きく劣化すると報告し、StockBench は大半の LLM が buy-and-hold に勝てないと報告している。過去日を LLM に「予測」させる検証は先読みバイアスの疑いが残るため、昇格の証拠は前向き記録だけにする。

## 丸パクリ候補(優先度順の表)

| # | 名前 | URL | 種別 | ライセンス | 鮮度(最終更新・発表年) | 何をどう写すか | 確認 |
|---|---|---|---|---|---|---|---|
| 1 | ACE: Agentic Context Engineering(論文) | https://arxiv.org/abs/2510.04618 | paper | arXiv | 2025-10 投稿、v2 あり。ICLR 2026 掲載(iclr.cc 一覧は検索結果で確認) | 3 役構成(Generator / Reflector / Curator)、bullet 単位の delta 更新、grow-and-refine(追記+既存 bullet のカウンタ更新+埋め込みで重複除去)、context collapse の回避原則。ハイパラ: Reflector 最大 5 ラウンド、オフライン最大 5 エポック、バッチサイズ 1 | ✅ |
| 2 | ace-agent/ace(公式実装) | https://github.com/ace-agent/ace | repo | Apache-2.0 | スター 1,360、最終 push 2026-08-24、非アーカイブ | `playbook_utils.py` の行フォーマットと正規表現 `\[([^\]]+)\]\s*helpful=(\d+)\s*harmful=(\d+)\s*::\s*(.*)`、`update_bullet_counts()`(helpful/harmful/neutral タグで +1)、`get_playbook_stats()` の閾値(high_performing: helpful>5 かつ harmful<2、problematic: harmful>=helpful かつ harmful>0、unused: 両方 0)、`ace/prompts/reflector.py` と `ace/prompts/curator.py` の JSON キー、`ace/core/bulletpoint_analyzer.py` の重複統合(all-mpnet-base-v2、cos 類似 0.90) | ✅ |
| 3 | ExpeL(論文+実装) | https://arxiv.org/abs/2308.10144 / https://github.com/LeapLabTHU/ExpeL | paper + repo | Apache-2.0 | AAAI 2024。repo はスター 245、コミット 11 件、最終 push 日は未確認(更新は止まっている可能性) | 票決プロトコル。`prompts/templates/human.py` の操作書式 `AGREE <番号>: <ルール>` / `REMOVE …` / `EDIT …` / `ADD …`、1 応答 4 操作まで、1 ルールに 1 操作まで、満杯時は REMOVE 優先。論文側: 新規は重み 2、UPVOTE/EDIT で +1、DOWNVOTE で −1、0 で削除。設定 `agent.max_num_rules`(10/8/10)、`agent.success_critique_num`(8/4/8) | ✅ |
| 4 | AutoManual | https://arxiv.org/abs/2405.16247 / https://github.com/minghchen/automanual | paper + repo | repo のライセンス未確認 | NeurIPS 2024。repo はスター 55、コミット 5 件 | ルール 4 属性(Rule Type / Rule Content / Example / Validation Logs)、6 種のルール型、Builder の関数 `write_rule` / `update_rule` / `stop_generating`、Consolidator(上限 N_max=12 超で統合・削除)、case-conditioned prompting(失敗原因を Imperfect Rules と Imperfect Agent に先に分類) | ✅(論文 HTML)/ ❓(repo 内部) |
| 5 | Sigma Rules Specification | https://github.com/SigmaHQ/sigma-specification | spec | 仕様リポジトリのライセンス未確認 | v2.1.0(2025-08-02) | `status` の 5 値(stable / test / experimental / deprecated / unsupported)、`id` は UUID(v4)で、ロジックの大幅変更・派生・統合では新 ID を振る、`related.type`(derived / obsolete / merged / renamed / similar)、`falsepositives`、`level`、`date` / `modified` の更新規則 | ✅ |
| 6 | TradingAgents の永続メモリ | https://github.com/TauricResearch/TradingAgents | repo | Apache-2.0 | スター約 11.1 万、v0.6.0(2026-10) | 「判断を Markdown ログに追記 → 保有期間経過後に実現リターン(生値と対ベンチマーク超過)を取得 → 1 段落の反省を書く → 次回は同一銘柄の直近判断と他銘柄の教訓を読む」という 2 段階(pending → settled)ログ。既定パス `~/.tradingagents/memory/trading_memory.md`、`ta.settle_all_pending()`、バックテストは別ログに書く設計 | ✅(README)/ ❓(ソースのパスとログ書式) |
| 7 | kayba-ai/agentic-context-engine | https://github.com/kayba-ai/agentic-context-engine | repo | Apache-2.0 | スター 2,592、最終 push 2026-09-24。`uv add ace-framework` | `ace/core/skillbook.py` の Skill データクラス(id, section, keywords, issue, insight, occurrences, active, used_count, helpful_count, harmful_count, neutral_count, created_at, updated_at)、操作 ADD / UPDATE / TAG / REMOVE、soft delete(`active=False`)、JSON 保存(`schema_version`, `skills`, `sections`, `next_id`, `similarity_decisions`)、重複統合の判断を記録する `similarity_decisions` | ✅ |
| 8 | SMB PlayBook テンプレート(Bellafiore) | https://ptgmedia.pearsoncmg.com/images/9780132937641/samplepages/0132937646.pdf / https://www.smbtraining.com/blog/the-smb-playbook-compiling-our-best-trades | book + article | 書籍は著作権あり(構成のみ参考) | ブログ 2011-05-10、書籍 The PlayBook(刊年は本調査で未確認) | 7 見出し(The Big Picture / Intraday Fundamentals / Technical Analysis / Reading the Tape / Trade Management / Trade Strategy / Trade Review)と、毎セッション後に「最も腑に落ちたセットアップを 1 つだけ」保存し、第三者がレビュー注記を付ける運用 | ✅ |
| 9 | Decision Journal(Farnam Street) | https://fs.blog/decision-journal/ | article | 記事 | 更新日未確認 | 事前に書く 8 項目(状況、問題の枠組み、支配変数、複雑さ、検討した代替案と却下理由、結果の幅、期待する結果と確率、時刻と心身状態)。事後に書き換えられないようにする目的(後知恵バイアス対策) | ✅ |
| 10 | Dynamic Cheatsheet | https://arxiv.org/abs/2504.07952 / https://github.com/suzgunmirac/dynamic-cheatsheet | paper + repo | MIT | arXiv 2025-04、EACL 2026。repo はスター 277、最終 push 2026-03-12 | `prompts/curator_prompt_for_dc_cumulative.txt` のチートシート構造(`<cheatsheet>` 内に Version 行、`<memory_item>` に `<description>` と `<example>`、直後に `** Count: N`)、全体 2,000〜2,500 語。反面教師として「全文書き直し方式は潰れる」こと | ✅ |
| 11 | microsoft/RD-Agent と R&D-Agent-Quant | https://github.com/microsoft/RD-Agent / https://arxiv.org/abs/2505.15155 | repo + paper | MIT | スター 14,911、最終 push 2026-10-11。論文は NeurIPS 2025 | `rdagent/core/proposal.py` の Hypothesis(hypothesis, reason, concise_reason, concise_observation, concise_justification, concise_knowledge)と HypothesisFeedback(observations, hypothesis_evaluation, new_hypothesis, reason, decision, acceptable)、`rdagent/scenarios/qlib/prompts.yaml` のフィードバック JSON キー(Observations / Feedback for Hypothesis / New Hypothesis / Reasoning / Replace Best Result)、重複因子の除去基準(既存 SOTA 因子との IC 最大値 0.99 以上で冗長)、「単純な仮説から始め、数ラウンド負けたら方向転換」の方針。注意: README は Linux のみ対応・Docker 必須と明記(Windows 11 では WSL2 が要る) | ✅ |
| 12 | AlphaAgent | https://arxiv.org/abs/2502.16789 | paper | arXiv。repo(RndmVariableQ/AlphaAgent、スター 419)はライセンス表記なし、公式かどうか未確認 | arXiv 2025-02。KDD 2025 掲載は引用元の記載で確認(一次は未確認) | 仮説の 5 要素(knowledge, market observations, justification, hypothesis, specification)、3 つの正則化(既存因子との AST 類似で独自性、仮説と式の整合を LLM 採点、複雑さ制限)。「似たルールばかり増えると混雑して早く効かなくなる」という設計思想 | ✅(論文)/ ❓(repo) |
| 13 | AlphaSchema | https://arxiv.org/abs/2607.26642 | paper | arXiv | 2026-07-29 投稿(新しい)。コード未公開 | ルールの意味を実装前に 5 要素(Event / Context / Qualities / Direction / Output)で固定する「schema plan」。同じ plan なら LLM を替えても予測品質が近い、という報告 → ルールの条件記述を構造化する根拠 | ✅(抄録のみ) |
| 14 | ReasoningBank | https://arxiv.org/abs/2509.25140 / https://github.com/google-research/reasoning-bank | paper + repo | Apache-2.0 | arXiv 2025-09、ICLR 2026。repo はスター 613 | メモリ項目の 3 欄(title / description / content)、1 軌跡から最大 3 項目、成功からは「なぜ効いたか」、失敗からは「原因と予防策」を抽出、単純追記 | ✅ |
| 15 | MADR 4.0.0 | https://adr.github.io/madr/ | template | MIT OR CC0-1.0 | 4.0.0(2024-09-17) | YAML front matter(status, date, decision-makers, consulted, informed)、status の書き方(proposed / rejected / accepted / deprecated / superseded by ADR-NNNN)、ファイル名 `NNNN-title-with-dashes.md`、置き場 `docs/decisions`。ルールブックの「運用方針の決定」を記録する用途に使う | ✅ |
| 16 | Agent Skills 仕様(SKILL.md) | https://agentskills.io/specification | spec | 仕様サイト | 現行 | YAML front matter + Markdown 本文、段階的開示(メタデータ約 100 トークン、本文 5,000 トークン未満推奨、SKILL.md は 500 行未満、詳細は references/ へ)。ルールブックの「索引は常時読み、個別ルールは必要時に読む」設計の根拠 | ✅ |
| 17 | Cursor Rules(.mdc) | https://cursor.com/docs/context/rules | docs | 製品ドキュメント | 現行 | front matter の `description` / `globs` / `alwaysApply` による「常時適用・条件付き適用・LLM 判断・手動」の 4 分類、1 ルール 500 行未満、同じ失敗が繰り返されたときだけルールを足す方針 | ✅ |
| 18 | python-frontmatter | https://github.com/eyeseast/python-frontmatter | library | MIT | スター 435、最終リリース日未確認 | `frontmatter.load(path)` → `post.metadata`(dict)と `post.content`(本文)。`frontmatter.dumps(post)` で書き戻し。ルールファイルの読み書きにそのまま使う | ✅ |
| 19 | Wilson スコア下限(Evan Miller) | https://www.evanmiller.org/how-not-to-sort-by-average-rating.html | article | 記事 | 古い記事だが数式は不変 | 賛否カウンタの順位付けは「差」でも「比率」でもなく Wilson 信頼区間の下限で。式: (p̂ + z²/2n − z·√((p̂(1−p̂) + z²/4n)/n)) / (1 + z²/n)、95% なら z=1.96 | ✅ |
| 20 | The Deflated Sharpe Ratio | https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf | paper | 論文 | Bailey & López de Prado、Journal of Portfolio Management 2014 | 試行回数 N を記録する義務、N 回試した最良の見かけ SR の期待値(式 1)、DSR(式 2)。数値例: 年率 SR 2.5、N=100 で DSR 約 0.90(95% 基準で不採用)、N=46 なら 0.9505 | ✅(PDF 本文を抽出して確認。数式の記号は一部欠落) |
| 21 | 多重検定と公表後減衰の基礎研究 | https://www.nber.org/papers/w20592 / https://www.nber.org/papers/w28432 | paper | 論文 | Harvey-Liu-Zhu(RFS 2016)、Jensen-Kelly-Pedersen(JF 2023)、McLean-Pontiff(JF 2016) | 新規ルールの t 値ハードル 3.0、ルールを 13 テーマのような「系統」で束ねて評価する発想、標本外 −26% / 公表後 −58% の割引 | ✅(HLZ, JKP の NBER 抄録)/ ❓(McLean-Pontiff は検索結果の抄録のみ、一次ページは 403) |
| 22 | Good Judgment Project の知見(AI Impacts まとめ) | https://aiimpacts.org/evidence-on-good-forecasting-practices-from-the-good-judgment-project/ | article(二次) | 記事 | まとめ記事。元研究は 2011〜2015 年頃 | 基準率(comparison class)から入る、確率を細かく刻む、小さな更新を多く、Brier スコアで採点、1 時間の訓練でも効果が 1 年以上持続、という運用原則 | ✅ |
| 23 | Brier スコア | https://en.wikipedia.org/wiki/Brier_score | reference | CC BY-SA | — | BS = (1/N)Σ(f−o)²、常に 50% 予測なら 0.25、分解 BS = REL − RES + UNC、BSS = 1 − BS/BS_ref | ✅ |
| 24 | onlineFDR | https://dsrobertson.github.io/onlineFDR/ | library(R) | GPL-3 | Robertson ら(Bioinformatics 2019) | 仮説が 1 件ずつ流れてくる状況で偽発見率を制御する手法群(alpha-investing、SAFFRON、ADDIS)。「増え続けるルール候補」への多重検定対策の後期導入候補 | ✅(概要のみ) |
| 25 | GEPA | https://arxiv.org/abs/2507.19457 / https://github.com/gepa-ai/gepa | paper + repo | repo のライセンス未確認 | ICLR 2026(oral) | 採点つき軌跡を自然言語で反省してプロンプトを改訂し、候補を 1 本に絞らずパレート前線で保持する方式。予測手順書そのものを最適化する段階で使う | ✅(抄録) |
| 26 | TradeZella のジャーナル項目 | https://www.tradezella.com/blog/how-to-build-a-trade-journal | article(業者ブログ) | 記事 | 2026-05-12 | 日次 5 分・週次 30 分・月次 60 分の 3 段レビュー、セットアップ別に 20〜30 件、比較には 50 件という実務目安、品質タグ(A+ / B / C / Off-plan) | ✅(根拠は経験則レベル) |
| 27 | Zettelkasten の原則 | https://zettelkasten.de/introduction/ | article | 記事 | — | 1 ノート 1 アイデア(原子性)、不変の一意 ID、リンクには理由を書く、構造ノート(索引)を別に持つ、ID・本文・参照の 3 部構成 | ✅ |
| 28 | Effective context engineering for AI agents(Anthropic) | https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents | article | 記事 | 2025-09-29 | 文脈は有限資源(context rot)、必要時取得、構造化メモ、最小の指示から始め失敗が出た所だけ足す | ✅ |
| 29 | QuantAgent / Alpha-GPT / FinCon | https://arxiv.org/abs/2402.03755 / https://arxiv.org/abs/2308.00016 / https://arxiv.org/abs/2407.06567 | paper | arXiv | 2024 / 2023(EMNLP 2025 demo)/ 2024 | QuantAgent: 知識ベース 1 件 = 取引アイデア + 実装 + 成績 + レビュー、内側ループ(writer と judge)と外側ループ(実環境の結果で KB 更新)。FinCon: 定期的な自己批評で「投資信念」を更新し必要な担当にだけ配る。いずれも数値やコードは本調査で未確認 | ✅(抄録・ar5iv)/ ❓(数値) |
| 30 | Reflexion / Voyager / Agent Workflow Memory | https://arxiv.org/abs/2303.11366 / https://arxiv.org/abs/2305.16291 / https://arxiv.org/abs/2409.07429 | paper + repo | MIT / MIT / Apache-2.0 | 2023 / 2023 / 2024。スター 3.3k / 7.3k / 478 | Reflexion: 失敗後の言語的反省を短期メモリに置く最小形。Voyager: 検証済みの実行可能コードをスキルとして蓄積。AWM: 個別値を変数に抽象化した手順(workflow)を蓄積。ルール条件を「具体例」でなく「変数つきの型」で書く根拠 | ✅(抄録・repo ページ)/ ❓(細部) |

## 詳細(項目ごとに、中身・数値・使い方・限界)

### 1. ACE(Agentic Context Engineering)

出典: Zhang ら(Stanford / SambaNova Systems / UC Berkeley)、arXiv 2510.04618。公式実装 ace-agent/ace(Apache-2.0)。

中身
- 既存手法の 2 つの失敗を名指しする。brevity bias(短い一般論に要約されて具体知識が落ちる)と context collapse(LLM による反復的な書き直しで細部が削れる)。
- 文脈を「プレイブック」として扱い、箇条書き(bullet)の集合にする。各 bullet はメタデータ(一意 ID、helpful と harmful のカウンタ)と内容(再利用できる戦略、ドメイン概念、典型的な失敗)からなる。
- 3 役:
  - Generator: 現在のプレイブックを使って解く。使った bullet のうちどれが役立ち、どれが誤誘導だったかを示す。
  - Reflector: 軌跡を批評して教訓を抽出する。複数ラウンドで磨ける。
  - Curator: 教訓を小さな delta(追加候補)にする。既存文脈への統合は LLM でなく決定的なロジックが行う。
- grow-and-refine: 新しい bullet は新 ID で追記、既存 bullet はその場で更新(カウンタ加算)、重複は意味埋め込みの比較で除去。除去は毎回(proactive)でも、文脈上限を超えたときだけ(lazy)でもよい。

数値(論文 HTML で確認)
- context collapse の例(AppWorld、Dynamic Cheatsheet 方式): ステップ 60 で 18,282 トークン・精度 66.7 → 次ステップで 122 トークン・精度 57.1。無適応ベースラインは 63.7。
- AppWorld(ベース DeepSeek-V3.1、ReAct 平均 42.4): オフライン ACE 正解ラベルあり 59.4(+17.0)、ラベルなし 57.2(+14.8)、オンライン ACE ラベルなし 59.5(+17.1)。比較: ICL 46.0、GEPA 46.4、オンライン DC(CU)51.9。
- 金融ベンチ(FiNER と Formula。ベース平均 69.1): オフライン ACE ラベルあり FiNER 78.3 / Formula 85.5 / 平均 81.9(+12.8)、ラベルなし平均 77.1(+8.0)、オンライン ラベルあり 76.6(+7.5)、オンライン ラベルなし 72.9(+3.8)で FiNER 単体は 67.3(−3.4)。
- 抄録の要約値: エージェントで +10.6%、金融で +8.6%。
- ハイパラ: Reflector 最大 5 ラウンド、オフライン最大 5 エポック、バッチサイズ 1。

公式実装で確認した具体(そのまま写せる部分)
- リポジトリ構成: `ace/ace.py`、`ace/ace_batch.py`、`ace/core/{generator,reflector,curator,bulletpoint_analyzer}.py`、`ace/prompts/{generator,reflector,curator}.py`、`playbook_utils.py`、`utils.py`、`llm.py`、`eval/finance/run.py`、`eval/finance/data/sample_config.json`、`EXTENDING_ACE.md`。
- 行フォーマット: `[{id}] helpful={n} harmful={n} :: {content}`。新規は helpful=0 harmful=0。ID は `{セクションのスラグ}-{連番5桁}`。
- README のセクション例: `## STRATEGIES & INSIGHTS`(接頭辞 str)、`## FORMULAS & CALCULATIONS`(cal)、`## COMMON MISTAKES TO AVOID`(mis)。未知のセクションは `## OTHERS` に入る。
- `update_bullet_counts()`: タグは `{id, tag}` の配列。tag が helpful なら helpful を +1、harmful なら harmful を +1、neutral は変更なし。1 回の呼び出しで同じ bullet は 1 度だけ更新。
- `apply_curator_operations()`: 実装されている操作は ADD のみ。UPDATE / MERGE / DELETE / CREATE_META はコメントアウトと TODO。つまり公式コードは「削除しない・書き換えない」運用で、整理は別モジュールの重複統合に任せている。
- `get_playbook_stats()` の分類閾値: high_performing は helpful>5 かつ harmful<2、problematic は harmful>=helpful かつ harmful>0、unused は両方 0。これは集計用で、自動削除はしない。
- Reflector の出力 JSON キー(順に): `reasoning`, `error_identification`, `root_cause_analysis`, `correct_approach`, `key_insight`, `bullet_tags`(各要素 `id` と `tag`)。正解ラベルなし版(`REFLECTOR_PROMPT_NO_GT`)は入力から正解を除いただけで出力は同じ。
- Curator の出力 JSON キー: `reasoning`, `operations`(各要素 `type`="ADD", `section`, `content`)。入力は token_budget、current_step、total_samples、playbook_stats、recent_reflection、current_playbook、question_context。指示の骨子は「既存にない洞察だけ足す、プレイブック全体を作り直さない、新規がなければ空配列を返す、ID は書かない」。並列で出た ADD 案を統合する集約プロンプト(`CURATOR_OPERATIONS_AGGREGATION_PROMPT`)もある。
- 重複統合(`bulletpoint_analyzer.py`): 埋め込みは `all-mpnet-base-v2`(sentence-transformers)、L2 正規化して内積 = コサイン類似、閾値 0.90、貪欲グルーピング、グループごとに LLM(temperature 0.3)で 1 本に統合し先頭 ID を残す。既定では無効(`use_bulletpoint_analyzer=False`)。
- README の既定設定: `num_epochs` 1、`max_num_rounds` 3、`curator_frequency` 1、`playbook_token_budget` 80000、`bulletpoint_analyzer_threshold` 0.9、`no_ground_truth` False、モデルは 3 役とも DeepSeek-V3.1。論文のハイパラ(5 ラウンド・5 エポック)と README 既定(3 ラウンド・1 エポック)は異なる点に注意。
- 実行例: `uv run python -m eval.finance.run --task_name finer --mode offline --save_path results`(モードは offline / online / eval_only)。

使い方(本プロジェクトへの写像)
- Generator = 毎朝の予測(LLM が docs を読んで予測票を書く。使ったルール ID を必ず列挙)。
- 採点 = 引け後にプログラムが確定値で行う(ACE の「実行フィードバック・正解ラベル」に当たる)。
- Reflector = 外れた予測と当たった予測について、ルールごとに helpful / harmful / neutral を付け、原因を 4 キー(error_identification 等)で書く。
- Curator = 追加候補(ADD)だけを JSON で出す。反映はプログラム。

限界
- ACE の「金融」ベンチは FiNER(XBRL タグ付け)と Formula(数値推論)であり、株価の予測ではない。効果量を相場予測に持ち込めない。
- 著者自身の限界記述: Reflector が弱いとプレイブックが雑音化する。信頼できるフィードバックがない領域では悪化しうる。簡潔な指針で足りる課題では長い文脈の利点が薄い。
- 公式コードは削除・降格をしない。相場では「昔効いたが今は効かない」ルールが必ず出るので、退役の仕組みは自前で足す必要がある。
- helpful / harmful のタグは LLM の判定。相場では「ルールは正しいが今回はノイズで外れた」が頻発するため、タグ=結果の符号、にすると 1 回ごとの偶然を数えるだけになる。

### 2. ExpeL

出典: Zhao ら(清華大 LeapLab)、arXiv 2308.10144、AAAI 2024。実装 LeapLabTHU/ExpeL(Apache-2.0)。

中身と数値
- 経験収集 → 洞察(ルール)抽出 → 推論時に洞察と成功例を想起、の 3 段。重みは更新しない。
- 洞察リストの編集操作は ADD / EDIT / UPVOTE / DOWNVOTE(論文の呼称)。実装では `AGREE` / `REMOVE` / `EDIT` / `ADD`。
- 新規洞察の重要度は 2 から開始。UPVOTE と EDIT で +1、DOWNVOTE で −1、0 になったら削除。著者は、成功軌跡でも最適とは限らないので、この方式が頑健性を与えると述べる。
- 入力は「同一タスクの失敗と成功のペア」または「成功 L 件の束」(L は HotpotQA 8、WebShop 4、ALFWorld 8)。抽出モデルは gpt-4-0613(gpt-3.5 より指示遵守がよく幻覚が少ないと報告)。
- 実装のプロンプト規則(`prompts/templates/human.py`): 1 応答で最大 4 操作、既存ルール 1 件につき 1 操作まで、触れなかったルールはそのまま残る、満杯時は REMOVE を優先し ADD は「明確に別物で非常に有益な場合」に限る、ルールは個別試行に言及せず一般的に書く。
- 設定: `agent.max_num_rules`(ALFWorld 10 / WebShop 8 / HotpotQA 10)、`agent.success_critique_num`(8 / 4 / 8)。
- 成績: HotpotQA 28.0→39.0、ALFWorld 40.0→59.0、WebShop 報酬 0.666→0.701、FEVER への転移 63→70。
- アブレーション(HotpotQA): 人手の洞察 32.0、反省文を混ぜて抽出 29.0、gpt-3.5 で抽出 32.0、フル 39.0。

使い方
- 「新規は重み 2、賛成 +1、反対 −1、0 で削除」は候補段階(candidate)のふるいとして使える。ただし相場ではノイズが大きいので、候補段階の賛否は「メカニズムの説明が今日の値動きと整合したか」の定性的票に限定し、昇格は統計基準で別に判定する(後述プロトコル)。
- 「1 回の更新で最大 4 操作」「満杯なら REMOVE 優先」は、そのまま更新量の上限として写す。

限界
- 対象は QA・家事シミュレーション・EC サイト操作で、確率的な結果を持つ領域ではない。
- 0 で即削除は、相場のような雑音環境では過敏。

### 3. AutoManual

出典: Chen ら、arXiv 2405.16247、NeurIPS 2024。

中身(論文 HTML で確認)
- 各ルールは 4 属性: Rule Type(6 種のいずれか)、Rule Content(適用場面の範囲から書き始める説明)、Example(軌跡からの例。間違えやすい細部の注記を含められる)、Validation Logs(適用と更新の記録。エピソード ID とルール ID を含む)。
- 6 種のルール型: Special Phenomenon、Special Mechanism、Useful Helper Method、Success Process、Corrected Error、Unsolved Error。
- Builder の関数: `write_rule(**rule_attributes)`、`update_rule(rule_id, **rule_attributes)`、`stop_generating()`。
- case-conditioned prompting: エピソードを Direct Success / Indirect Success / Failure に分類。Builder はまず主因が Imperfect Rules(ルールが不完全)か Imperfect Agent(ルールはあったが従わなかった・実行が悪い)かを判定し、ケース別の指示を受ける。長い軌跡からのルール抽出で起きる幻覚(失敗軌跡から成功ルールを作る等)を抑える狙い。
- Consolidator: ルール数が N_max(構築時 12)を超えたら、関連ルールの統合と冗長ルールの削除を行う。細部と例は保つ。
- 成績: ALFWorld で GPT-4-turbo 97.4%、GPT-3.5-turbo 86.2%(デモ 1 件のみ)。case-conditioned prompting のアブレーションは 93.8% → 97.4%。

使い方
- 「Rule Type」を相場用に置き換える(提案): mechanism(因果ルール)、phenomenon(観測された癖、因果未解明)、process(手順)、guardrail(やってはいけない)、corrected-error(直した誤り)、open-question(未解決)。
- 「まずルールの欠陥か、適用の欠陥か、どちらでもない(ノイズ)かを分類してから更新する」を振り返りの第 1 問にする。相場では第 3 の分類「ルールも適用も妥当だが偶然外れた」が最頻になるはずで、これを数えられることが重要。
- Validation Logs は、手書きではなく台帳から自動生成する。

### 4. Dynamic Cheatsheet(反面教師として重要)

出典: Suzgun ら、arXiv 2504.07952、EACL 2026。実装 suzgunmirac/dynamic-cheatsheet(MIT)。

- 2 方式: DC-Cu(解いてからメモリ更新)と DC-RS(類似過去問 top-3 を text-embedding-3-small で取得し、解く前にメモリを整える)。Curator は正解ラベルを見ず、モデル自身が正誤を判断する。
- チートシート書式(`prompts/curator_prompt_for_dc_cumulative.txt`): `<cheatsheet>` ブロック内に Version 行、項目は `<memory_item>` に `<description>` と `<example>`、閉じタグの後に `** Count: N`(成功利用のたび増やし優先度に使う)。全体は 2,000〜2,500 語程度。前版の内容は明示的に写さないと失われる、という方式。
- 成績: Game of 24 で GPT-4o 10%→99%(DC-RS)、AIME 2024 で Claude 3.5 Sonnet 23.3%→50.0%、GPQA-Diamond 59.6%→68.7%、Math Equation Balancer 44.8%→97.8%。一方で Claude の Game of 24 は 12%→14%、GPT-4o の GPQA-Diamond は 57.1%→58.1% と効果は課題とモデルで大きくばらつく。
- 限界(著者記述): 小型モデルでは効果が小さいか悪化、誤ったヒューリスティックも同じように増幅される、長い文脈の再生成でモデルが記憶を省略して中身が劣化する、検索ノイズで混乱する、トークン消費が増える(AIME 2024 で平均 370→1,831)。
- 教訓: 利用回数カウンタと「説明+例」の 2 欄は写す価値がある。全文再生成方式は写さない(ACE が示した崩壊の発生源)。

### 5. ReasoningBank

出典: Ouyang ら(Google Cloud AI Research ほか)、arXiv 2509.25140、ICLR 2026。

- メモリ項目は title(戦略の短い識別名)、description(1 文の要約)、content(推論手順・根拠・運用上の洞察)。
- 成否は LLM-as-a-Judge が判定(正解ラベルなし、temperature 0.0)。成功軌跡からは「なぜ効いたか」、失敗軌跡からは「失敗原因と予防策」を抽出。1 軌跡あたり最大 3 項目。検索は gemini-embedding-001 のコサイン類似で top-1。統合は単純追記。
- 成績: WebArena で無メモリ比 +8.3 / +7.2 / +4.6 ポイント(3 種のバックボーン)、SWE-Bench-Verified で 34.2→38.8(Gemini-2.5-flash)、54.0→57.4(Gemini-2.5-pro)。
- 失敗由来メモリの効果(WebArena-Shopping): Synapse 40.6→41.7、AWM 44.4→42.2(悪化)、ReasoningBank 46.5→49.7。失敗を足せば必ず良くなるわけではなく、抽出の仕方に依存する。
- 判定器の精度は Shopping で 72.7%。判定精度 70〜90% の範囲では成績が近く、完全ラベルが最良。

使い方: 日次の振り返りで新規ルール候補は最大 3 件まで、という上限の根拠に使える。title / description / content の 3 欄は、索引(INDEX)に載せる短い 2 欄と本文の分離にそのまま対応する。

### 6. R&D-Agent-Quant(RD-Agent(Q))と LLM アルファマイニング系

RD-Agent(Q)(arXiv 2505.15155、NeurIPS 2025、microsoft/RD-Agent、MIT)
- 5 ユニット: Specification(前提・データ IF・出力形式・実行環境の定義)、Synthesis(過去実験から仮説生成)、Implementation(Co-STEER がコード生成。タスク・コード・フィードバックの三つ組を成功失敗とも知識ベースに保存し類似解を検索、デバッグ内側ループは 1 タスク最大 10 回)、Validation(冗長因子の除去後にバックテスト)、Analysis(評価、SOTA 集合の更新、次に因子とモデルのどちらを攻めるか決定)。
- 冗長判定: 新因子と各 SOTA 因子の IC を時点ごとに計算して平均し、その最大値が 0.99 以上なら冗長として捨てる。
- スケジューラ: 因子とモデルの 2 腕の文脈つき Thompson sampling。状態は 8 次元(IC, ICIR, Rank IC, Rank ICIR, ARR, IR, −MDD, SR)。報酬の重みの数値は本文で未確認。
- 成績(論文の主張): CSI 300(学習 2008–2014、検証 2015–2016、テスト 2017〜2020-08)で IC 0.0532、ICIR 0.4278、ARR 14.21%、IR 1.74、MDD −7.42%(o3-mini)。Alpha 158 は IC 0.0341、ARR 5.70%、IR 0.85。CSI 500 と NASDAQ 100 は学習 2008–2021、検証 2022–2023、テスト 2024〜2025-06。総コスト 10 ドル未満。取引コストの仮定は付録で、本調査では未確認。
- 実装で写せるもの: `rdagent/core/proposal.py` の Hypothesis と HypothesisFeedback のフィールド、`rdagent/scenarios/qlib/prompts.yaml` のキー構成(`hypothesis_and_feedback`, `factor_hypothesis_specification`, `factor_feedback_generation`, `action_gen` など)。フィードバックの方針は「年率リターンが改善したら SOTA を置き換える。初回は ICIR が 0 を超える程度で成功扱い」「単純な因子から始め、検証できてから複雑化。数ラウンド SOTA を超えなければ方向転換」。
- コマンド: `rdagent fin_quant`(因子とモデルの共進化)、`rdagent fin_factor`、`rdagent fin_model`、`rdagent fin_factor_report --report-folder=<path>`(レポートからの因子抽出)。
- 制約: README は Linux のみ対応、Docker 必須と明記。Windows 11 では WSL2 + Docker が前提。対象データは Qlib(中国株・米株)で、日本株データの整備は別途必要。
- 注意: SOTA 置換基準が「年率リターンが少しでも改善したら」なので、検証期間への過適合が起きやすい構造。試行回数の補正(DSR 等)は確認した範囲では組み込まれていない。

AlphaAgent(arXiv 2502.16789)
- 仮説は 5 要素(knowledge, market observations, justification, hypothesis, specification)。3 エージェント(Idea / Factor / Eval)。
- 正則化: 独自性(既存アルファ群との AST の最大共通部分木サイズ)、仮説整合(仮説と説明、説明と式の整合を LLM が 0〜1 で採点)、複雑さ(記号長・パラメータ数・使用特徴量数)。重みや閾値の数値は論文に記載なし。
- 成績(2021–2024、学習 2015–2019、検証 2020): CSI 500 で IC 0.0212、年率 11.00%、IR 1.488、MDD −9.36%。S&P 500 で IC 0.0056、年率 8.74%、IR 1.05、MDD −9.10%。取引コストは CSI 500 買い 0.0005・売り 0.0015、S&P 500 売りのみ 0.0005。アブレーションで有効因子のヒット率 0.29 対 0.16。
- 同論文での RD-Agent の再評価値は CSI 500 で IC 0.0113、年率 0.78%、MDD −20.85%。ただし使用 LLM が異なり(AlphaAgent は GPT-3.5-turbo、RD-Agent は GPT-4-turbo)、競合側による評価である。「論文の主張値は別の期間・別の評価者では大きく変わる」実例として読むのが妥当。
- 減衰の図: CSI 500 で Alpha158・GP・RSI 系の IC が 5 年で 0.02〜0.04 程度からほぼ 0 に低下(図からの読み取り値)。

AlphaSchema(arXiv 2607.26642、2026-07)
- 因子の意味を実装前に 5 要素(Event / Context / Qualities / Direction / Output)の schema plan で指定し、探索をコードではなく意味空間で行う。異なる LLM でも同じ plan なら予測品質が近いと報告。数値は抄録に無し、コードリンク無し。
- 本プロジェクトへの示唆: ルールの IF 部を「何が起きたか(Event)・どんな地合いで(Context)・どの程度(Qualities)」、THEN 部を「方向(Direction)・何を出力するか(Output)」に分けて書けば、人・LLM・プログラムで解釈がぶれにくい。

QuantAgent(arXiv 2402.03755): 知識ベースの 1 件は「取引アイデア・実装・成績指標・レビュー」。内側ループ(writer が KB を引いて書き、judge が採点、閾値か上限回数で停止)と外側ループ(実環境で評価し、成功も失敗も KB に追記)。数値は図のみ、コード公開は確認できず。

サーベイ(arXiv 2608.31041、2026-08-31): 抄録レベルで「予測能力の高さがライブ市場での売買成績に安定して結びつかない」と総括している。本文の分類表は未読。

### 7. TradingAgents の「保留 → 決済 → 反省」ログ

- README で確認: 各実行の判断を Markdown ログ(既定 `~/.tradingagents/memory/trading_memory.md`、環境変数 `TRADINGAGENTS_MEMORY_LOG_PATH` で変更可)に追記。後日の実行時に、保有期間を過ぎた判断について実現リターン(生値と、その銘柄の地域ベンチマーク対比の超過)を取得し、1 段落の反省を書く。Portfolio Manager は同一銘柄の直近判断と他銘柄の最近の教訓を読む。決済に失敗しても実行は続き、レポートにその旨を書く。`ta.settle_all_pending()` で分析なしに決済だけ実行可能。バックテスト(`run_backtest`)は別ログに書き、本番ログを汚さない。
- 写す点: 「予測記録(pending)と答え合わせ(settled)を同じ台帳の 2 状態にする」「絶対リターンとベンチマーク超過の両方を残す」「バックテストと前向き記録の台帳を分ける」。
- 未確認: ログ 1 件の書式、保有期間の長さ、v0.5.1 で再編された後のメモリ実装ファイルのパス。
- 免責(README): 研究目的であり投資助言ではない、同じ銘柄・同じ日でも LLM のサンプリングで結果が変わりうる、と明記されている。

### 8. kayba-ai/agentic-context-engine(ACE の実用派生)

- `ace/core/skillbook.py` で確認した Skill のフィールド: `id`(str)、`section`("context" か "harness")、`keywords`(list)、`issue`(str)、`insight`(str か None)、`occurrences`(出所のリスト)、`active`(bool、既定 True)、`used_count`、`helpful_count`、`harmful_count`、`neutral_count`、`embedding`、`created_at`、`updated_at`(UTC ISO)。
- 操作: ADD / UPDATE / TAG / REMOVE。TAG の delta は +1 / −1 / 0 で helpful / harmful / neutral を加算。REMOVE は既定で soft(`active=False`)で、プロンプト出力(`as_prompt()`)から外れるだけで保存は残る。
- 保存形式: JSON(`schema_version`="2"、`skills`、`sections`、`next_id`、`similarity_decisions`)。埋め込みは別ファイル(`.embeddings.npz`)。重複判定の結果(統合する・別物として残す)を `similarity_decisions` に記録し、同じ組を再判定しない。
- 設計ドキュメント(`docs/design/ACE_REFERENCE.md`)の記載: 重複・曖昧・`harmful_count ≥ 3` のスキルは削除対象。重複統合は既定 10 サンプルごと、例示の類似閾値は 0.85。
- 写す点: `issue`(どんな状況で)と `insight`(どうする)を分ける 2 欄構成、`used_count` と helpful / harmful / neutral の 4 カウンタ、soft delete、重複判定の記録。
- 写さない点: harmful 3 回で削除。相場では勝率 55% の有効ルールでも 3 連敗は約 9% の確率で起きる(0.45³、自前計算)。

### 9. 人間側: PlayBook、日誌、超予測、チェックリスト、知識ベース

SMB Capital の PlayBook(Mike Bellafiore)
- 書籍サンプル PDF(Pearson 配布)で確認した運用: 毎セッション後、その日いちばん腑に落ちたセットアップを 1 つ、テンプレート形式で保存し、デスクで共有する。各トレードは次の見出しで分解される: The Big Picture / Intraday Fundamentals / Technical Analysis / Reading the Tape / Trade Management / Trade Strategy / Trade Review。第 1 章の目次では判断の変数として Big Picture、Intraday Fundamentals、Technical Analysis、Reading the Tape、Intuition が並ぶ。
- 2011-05-10 のブログ記事で確認: テンプレートは Name of The Play、Intraday Fundamentals、Technical Analysis、Reading the Tape、Trade Management。トレーダーが 1 日の最良トレードを書き、Bellafiore がレビュー注記を付けて共有する。例は Sysco(SYY)の決算後ギャップアップで、特定価格に居座る買い手を読む内容。
- 著者の強調点は「中身は各自でよいが、PlayBook の存在自体は必須」。経験者でも成績不振の人は、得意セットアップを即答できず保存の方法論もなかった、という観察が書かれている(逸話であり統計ではない)。
- 写す点: 1 日 1 件に絞る(量より定着)、名前を付ける、他者(または別 LLM)の注記欄を設ける。発注しない本プロジェクトでは Trade Management と Reading the Tape は省略または「値動きの経過」に置き換える。

Decision Journal(fs.blog で確認)
- 事前に書く 8 項目: 状況の文脈、問題の枠組み、状況を支配する変数、複雑さ、真剣に検討した代替案と却下理由、ありうる結果の幅、期待する結果とその根拠と各結果の確率、時刻と心身の状態。
- 目的は後知恵バイアスの遮断。良い結果の後は「分かっていた」と記憶が書き換わり、悪い結果の後は当時なかった疑念を作り出す。曖昧な書き方は言い逃れの余地になるので、明確に書く。
- Kahneman への帰属は記事本文には無かった(ページのメタデータにのみ名前)。「Kahneman 系」という呼び方は二次情報由来で、一次根拠は本調査で未確認。レビュー間隔の指定も本文には無い。

Good Judgment Project(AI Impacts の二次まとめで確認)
- GJP は対照群に 60% 超の差、機密情報を持つ情報機関アナリストの予測市場に 25〜30% の差をつけた。超予測者の約 70% が翌年も地位を維持、年次成績の相関は 0.65。
- 訓練は 1 時間で、効果は少なくとも 1 年持続。内容は確率的推論、外部視点(基準率)、バイアス回避など。
- 「comparison classes」タグ付き回答の平均 Brier は 0.17、次点のタグは 0.26。興味深いことに「post-mortem analysis」タグは不正確さと相関していた(因果ではなくタグの相関)。
- 超予測者の較正誤差は 0.01。確率を丸めると精度が落ちるという主張があるが、閾値の記述(0.05 か 0.1 か)に不整合があり未解決。
- Tetlock の「十戒」の見出し: トリアージ、分解、内外の視点の均衡、証拠への過小反応と過剰反応の均衡、衝突する因果の力を探す、疑いの度合いを細かく、過小確信と過剰確信の均衡、失敗の背後の誤りを探す、他者を活かす、練習と採点、戒めを絶対視しない。
- 写す点: 予測票の最初の欄を「基準率」にする、確率は 5% 刻みより細かく書いてよい、毎日 Brier で採点する。

チェックリスト(Gawande ら)
- projectcheck.org に「A Checklist for Checklists」(Atul Gawande、Brigham and Women's Hospital、Boeing の Dan Boorman 作成)が存在することは確認。中身は PDF で、本調査では未開封。一般に知られる原則(1 つの停止点につき項目は少数、READ-DO と DO-CONFIRM の区別、現場で試して改訂、日付を入れる)は書籍の一般知識として記すが、一次確認はしていない。

Bridgewater の Principles
- principles.com のトップは開いたが、5 ステップ・プロセス(目標 → 問題 → 診断 → 設計 → 実行)、「痛み + 内省 = 進歩」、issue log、原則のアルゴリズム化といった中身は本調査で一次確認できていない(記憶ベース)。採用するなら「失敗は必ず記録し、原因を診断し、原則(ルール)に落とす」という流れだけを借りる。

Zettelkasten(zettelkasten.de で確認)
- 1 ノート 1 アイデア、変わらない一意 ID、リンクには理由を書く、構造ノート(索引・目次)を別に持つ、ノートは ID・本文・参照の 3 部。自分の言葉で書く。
- 写す点: 1 ルール 1 ファイル、ID 不変、`related` には type(理由)を必ず付ける、INDEX.md を構造ノートとして持つ。

TradeZella のジャーナル記事(2026-05-12、業者ブログ)
- 取引ログ項目: 日時、銘柄、方向、エントリー価格、エグジット価格、サイズ、損益、セットアップタグ、感情・品質タグ。事前計画 5 問、事後レビュー 4 問。
- レビュー周期: 日次 約 5 分(タグ付けと短い振り返り。日次の結果は雑音が多いので分析しない)、週次 約 30 分、月次 約 60 分。
- 目安: 全体のベースラインに約 30 件、セットアップ別に 20〜30 件、戦略比較には約 50 件。根拠は示されておらず経験則。

### 10. 統計の歯止め(ノイズへの過学習を防ぐ道具)

Wilson スコア下限(Evan Miller の記事で式を確認、以下の表は自前計算)

| 当たり / 発火 | 的中率 | Wilson 95% 下限 |
|---|---|---|
| 7 / 10 | 0.700 | 0.397 |
| 14 / 20 | 0.700 | 0.481 |
| 20 / 30 | 0.667 | 0.488 |
| 30 / 50 | 0.600 | 0.462 |
| 33 / 50 | 0.660 | 0.522 |
| 55 / 100 | 0.550 | 0.452 |
| 60 / 100 | 0.600 | 0.502 |
| 115 / 200 | 0.575 | 0.506 |
| 275 / 500 | 0.550 | 0.506 |
| 540 / 1000 | 0.540 | 0.509 |

読み方: 10 回中 7 回当たっても、真の的中率が 50% 未満である可能性を排除できない。的中率 55% のルールを 95% 下限で 50% 超と言うには約 500 回の発火が要る。

必要サンプル数(片側 5%、検出力 80%、帰無仮説 50%、正規近似による自前計算)

| 真の的中率 | 必要な独立発火数 |
|---|---|
| 52% | 約 3,860 |
| 53% | 約 1,715 |
| 55% | 約 616 |
| 58% | 約 239 |
| 60% | 約 152 |
| 65% | 約 67 |
| 70% | 約 36 |

含意: 週 1 回しか発火しないルールで 55% の優位を確かめるには 10 年以上かかる。したがって (a) 方向の当たり外れだけでなく符号つきリターン(効果量)で評価する、(b) 同じ因果の系統(family)でルールを束ねて評価する、(c) 外部の査読研究という事前証拠を持つルールは前向き記録のハードルを下げる、の 3 つが実務上必須になる。

t 値で見る場合(自前計算): 1 発火あたりの情報比(平均 ÷ 標準偏差)が 0.1 なら、t=2 に 400 発火、t=3 に 900 発火。0.2 なら 100 と 225。0.3 なら 44 と 100。

Deflated Sharpe Ratio(Bailey & López de Prado 2014、PDF 本文を抽出して確認)
- 主張: バックテストに欠けている最重要情報は「何通り試したか」であり、それ抜きの成績は評価不能。
- 式 1(N 回の独立試行で最良となる見かけ SR の期待値、真の SR が 0 の場合): SR0 = √V[SR] × ((1 − γ)·Z⁻¹[1 − 1/N] + γ·Z⁻¹[1 − 1/(N·e)])。γ は Euler-Mascheroni 定数(約 0.5772)、Z は標準正規の累積分布、V[SR] は試行間の SR の分散。
- 式 2: DSR = Z[ (SR̂ − SR0)·√(T − 1) / √(1 − γ̂3·SR̂ + ((γ̂4 − 1)/4)·SR̂²) ]。T は標本長、γ̂3 は歪度、γ̂4 は尖度。SR は年率でなく 1 観測あたりの値で入れる。PDF 抽出で記号の一部が欠落したため、実装前に原論文の式 (1)(2) と照合すること。
- 数値例: 日次 5 年(T=1250)、年率 SR 2.5、N=100、V[SR]=1/2、歪度 −3、尖度 10 → DSR 約 0.90 で 95% 基準に届かない。N=46 なら 0.9505。正規分布の収益なら N=88 でも 0.95。
- 実装上の含意: 提案されたルールは却下分も含めすべて `trials.jsonl` に残し、系統ごとの試行数 N を数えられるようにする。

多重検定・減衰・再現性
- Harvey, Liu, Zhu(RFS 2016、NBER w20592): 何百もの因子が試された後では、新因子は t 値 3.0 超を要するという推定。金融経済学の「発見」の多くは偽だろうと主張。
- 反論側: Jensen, Kelly, Pedersen(JF 2023、NBER w28432)はベイズモデルで「過半は再現する」「因子は 13 テーマに集約され大半が有意」「93 か国の新データで標本外でも機能」と報告。Chen(2021 年頃)も t 値 3 前後のハードルは偽発見率 5% 以下に対応し、多くの発見は真だと論じる(検索結果の要約のみ確認)。つまり「大半は偽」か「大半は真」かは学界で決着していない。
- McLean & Pontiff(JF 2016): 97 の予測変数で、ポートフォリオ収益は標本外で 26% 低く、公表後は 58% 低い。差の 32% を公表による裁定取引の効果と解釈(検索結果の抄録で確認。一次ページは 403 で開けず)。米国株の結果であり、日本株での減衰幅は本調査で未確認。
- onlineFDR(R、GPL-3): 仮説が逐次到着する状況で FDR を制御するアルゴリズム群。alpha-investing は「棄却できたら検定予算が増える」方式で、育つルールブックと相性がよい。ただし p 値を出せる程度のサンプルが要るため後期の導入候補。

Brier スコア
- BS = (1/N)Σ(予測確率 − 結果)²。常に 50% なら 0.25。BS = 信頼性 − 分解能 + 不確実性。BSS = 1 − BS/BS_ref(基準は「常に基準率を言う」予測)。稀な事象の高スキル予測の評価には n>1000 が要るという指摘がある。
- 本プロジェクトでは BS_ref を「その銘柄群の寄り→引け上昇の過去基準率を毎日言う」予測に置き、BSS が 0 を超えるかを主指標にする。

### 11. LLM を相場ルールの抽出・検証に使うときの固有リスク

- 先読みバイアスと distraction effect(Glasserman & Lin、arXiv 2309.17322、2023): LLM の学習期間内のニュースで感情分析戦略を検証すると、モデルがその後の株価を「知っている」可能性がある。社名を匿名化した見出しのほうが標本内で好成績だったことから、著者らは一般知識による攪乱(distraction)の影響のほうが大きいと結論。学習期間後の標本外では先読みは問題にならないが攪乱は残りうる。
- FINSABER(arXiv 2505.07078、KDD 2026 Datasets & Benchmarks、oral): 20 年・100 銘柄超の系統的バックテストで、既報の LLM 戦略の優位は大きく劣化。上昇相場では保守的すぎてパッシブに負け、下落相場では攻めすぎて大きく損失。原因として生存者バイアスとデータスヌーピングを挙げる。数値は抄録に無し。
- StockBench(arXiv 2510.02209): 数か月の実市場を模した売買ベンチで、評価した LLM の大半が buy-and-hold を上回れない。静的な金融 QA の成績は売買の巧拙を予測しない。
- 含意: (1) LLM に過去日を再予測させた成績を昇格の証拠にしない。(2) ルールの条件判定はできる限りプログラム(決定的)にし、LLM の役割はメカニズムの説明・候補提案・振り返りの文章化に寄せる。(3) LLM のモデル更新日をまたぐと振る舞いが変わるので、予測票に使用モデル名とバージョンを記録する。

---

## 必須回答 (1): ルール 1 件の記述スキーマ(最良事例の合成)

先行例の対応表

| 欄 | 何を書くか | 由来 |
|---|---|---|
| id | 不変の一意 ID。ロジック変更・派生・統合では新 ID | Sigma(id は UUID、変更条件を明記)、Zettelkasten、ACE(`slug-00001`) |
| title | セットアップの名前 | SMB PlayBook(Name of the Play)、ReasoningBank(title) |
| type | mechanism / phenomenon / process / guardrail / corrected-error / open-question | AutoManual(Rule Type 6 種を相場向けに読み替え。提案) |
| status | candidate / probation / active / watch / retired / rejected / unsupported | Sigma(experimental / test / stable / deprecated / unsupported)、MADR(proposed / rejected / accepted / deprecated / superseded) |
| family | 因果の系統。重複管理と多重検定の単位 | JKP の 13 テーマ、AlphaAgent の独自性、RD-Agent(Q) の冗長除去 |
| condition(IF) | 判定時刻までに観測できる条件。構造化(機械用)と 1〜2 文(人用)の両方 | AlphaSchema(Event / Context / Qualities)、kayba Skill(issue)、AutoManual(Rule Content は適用範囲から書く) |
| prediction(THEN) | 対象・方向・大きさの目安・時間軸・確率 | AlphaSchema(Direction / Output)、decision journal(期待結果と確率) |
| mechanism | なぜそうなるか | AlphaAgent(justification)、RD-Agent(reason / concise_justification)、Tetlock(衝突する因果の力) |
| evidence | 出典 URL、対象市場、期間、効果量、コスト考慮、確度 A/B/C | Sigma(references)、Zettelkasten(参照欄)、QuantAgent(成績指標とレビュー) |
| invalidation | 効かなくなる条件・除外条件 | Sigma(falsepositives)、ACE(COMMON MISTAKES TO AVOID) |
| data_required | 必要データと入手時刻 | RD-Agent(Q)(Specification ユニット) |
| example | 発火した実例(日付・銘柄・経過) | AutoManual(Example)、Dynamic Cheatsheet(`<example>`)、SMB(毎日の 1 件) |
| counters | fires / helpful / harmful / neutral、的中率、Wilson 下限、平均符号つきリターン、t 値、最終発火日 | ACE(helpful / harmful)、kayba(used_count と 3 カウンタ)、DC(Count)、ExpeL(重要度) |
| related | 他ルールとの関係と種類 | Sigma(derived / obsolete / merged / renamed / similar)、MADR(superseded by) |
| status_history / validation log | 状態遷移と理由、適用記録 | AutoManual(Validation Logs)、Sigma(date / modified)、kayba(occurrences) |

設計上の要点
- counters とバリデーションログは「派生データ」。人も LLM も手で書かず、追記専用台帳からプログラムが再計算して front matter に書き戻す。こうすると LLM がカウンタを書き間違える・都合よく直す事故が構造的に起きない(ACE が統合を非 LLM にした理由と同じ)。
- condition は「その時刻に本当に観測できたか」を `observable_by` で明示する。先読み混入の最大の入口はここ。
- prediction には必ず確率を書く。方向だけだと Brier 採点も較正もできない。
- 編集で ID を保てるのは、誤字・説明の明確化・出典の追加・除外条件の追記(範囲を狭める方向)まで。条件の閾値や予測方向を変えたら新 ID にしてカウンタを 0 から始め、旧ルールは `related: derived` でつなぐ。事後に条件をいじって成績を良く見せる行為(ゴールポストの移動)を防ぐため。

## 必須回答 (2): ルール更新プロトコル

以下の閾値はすべて提案値(未検証)。根拠にした先行例と統計を併記する。運用しながら MADR 形式の決定記録で改訂すること。

状態と意味

| 状態 | 意味 | 予測への使われ方 |
|---|---|---|
| candidate | 提案されたばかり。メカニズムの説明はあるが前向き実績なし | 影の予測のみ(公式予測には使わない。発火と結果だけ記録) |
| probation | 前向きで最低限の実績が出た | 公式予測に使うが重みは縮小 |
| active | 統計基準を通過 | 公式予測に通常の重みで使う |
| watch | 直近の成績が悪化 | 重みを半減、新規の派生を止める |
| retired | 退役。ファイルは `retired/` に移すが削除しない | 使わない。影の記録を続けてもよい |
| rejected | candidate のまま基準を満たさず終了 | 使わない。試行数 N のために記録は残す |
| unsupported | 必要データが取れなくなった等で判定不能 | 使わない |

遷移の証拠基準(提案値)

| 遷移 | 条件 | 根拠・先行例 |
|---|---|---|
| (新規)→ candidate | メカニズムを 1〜3 文で書ける。かつ、外部出典が 1 件以上ある、または別々の営業日 3 日以上の観測がある。1 回の更新で追加は最大 3 件、全操作は最大 4 件。既存ルールと意味が重複しないこと | ReasoningBank(1 軌跡 3 項目まで)、ExpeL(4 操作まで)、ACE(既存に無い洞察だけ追加)、Cursor(同じ失敗が繰り返されたら足す) |
| candidate → probation | 独立な発火日 n ≥ 20、平均符号つきリターン > 0、的中率 ≥ 55%。データ欠損や判定不能が発火の 10% 未満 | TradeZella(セットアップ別 20〜30 件)、RD-Agent(Q)(初回は「明確に悪くなければ可」) |
| probation → active | 独立な発火日 n ≥ 50、かつ(Wilson 95% 下限 > 0.50、または日次クラスタで計算した平均リターンの t ≥ 2.0)。外部の査読根拠(確度 A/B)が無い純粋な発掘型ルールは t ≥ 3.0 を要求 | Evan Miller(Wilson 下限)、Harvey-Liu-Zhu(t>3)、TradeZella(比較に 50 件) |
| active → watch | 直近 30 発火の的中率 < 45%、または直近 30 発火の平均リターンが昇格時点の平均の 50% 未満、または累積で harmful ≥ helpful | McLean-Pontiff(標本外で −26%、公表後で −58% は普通に起きる)、ACE(problematic の定義) |
| watch → active | watch 入り後の 20 発火で的中率 ≥ 55% かつ平均リターン > 0 | 提案 |
| watch → retired | watch 入り後の 20 発火でも回復しない、または全期間の Wilson 95% 上限 < 0.50 | 提案 |
| 任意 → retired(即時) | メカニズムの前提が制度変更・データ仕様変更などで消えた。理由と日付を必ず書く | Sigma(deprecated は置き換え先を related で示す) |
| candidate → rejected | 登録から 60 営業日で発火が 5 回未満(検証不能)、または n ≥ 20 で平均リターン ≤ 0 | ExpeL(重要度 0 で削除)、ACE(unused の分類) |
| 任意 → unsupported | 必要データが 10 営業日連続で取得不能 | Sigma(unsupported) |

ノイズへの過学習を防ぐ仕掛け(重要な順)

1. 全文書き直しの禁止。LLM が出せるのは delta(ADD 案・EDIT 案・タグ)だけ。反映は決定的なコードが行い、全変更を `deltas.jsonl` に残す(ACE、context collapse 対策)。
2. カウンタは台帳から再計算。LLM にも人にも front matter の counters を編集させない。
3. 採点は確定値でプログラムが行う。LLM の自己判定は使わない(ACE: ラベルなしで金融は悪化、ReasoningBank: 判定器の精度は 72.7%)。
4. 影のモード。candidate は公式予測に影響させず、発火と結果だけ貯める。これで「新ルールを入れた途端に予測が振り回される」ことを防ぐ(RD-Agent(Q) の SOTA 集合と候補の分離に相当)。
5. 更新の周期を分ける。日次はタグ付けと台帳追記だけ。週次で ADD / EDIT 案を審査。月次で昇格・降格・退役を判定。日次の当たり外れで状態を動かさない(TradeZella: 日次は雑音、週次・月次で判断)。
6. 独立性の単位は「日」。同じ日に 30 銘柄で発火しても、地合いが共通なので独立な証拠は 30 個ではない。n、的中率、t 値はまず日次平均に集約してから数える(一般的な統計上の注意。日次クラスタ)。
7. 外れの原因を 4 分類してからタグを付ける: rule_wrong(ルールの因果が違った)、misapplied(条件を満たしていないのに適用した・データ誤り)、noise(ルールも適用も妥当だが偶然外れた)、regime(前提の地合いが違った)。harmful を付けるのは rule_wrong と、繰り返す regime のみ。noise は neutral。ただし統計(的中率・リターン)は分類に関係なく全発火で計算する(AutoManual の Imperfect Rules と Imperfect Agent の区別を拡張)。
8. 事後の条件変更は新 ID。カウンタを引き継がない(Sigma の ID 規則)。
9. 試行数の記録。提案された全ルール(却下含む)を `trials.jsonl` に残し、系統ごとの N を数える。N が増えたら昇格ハードルを上げる(DSR、Harvey-Liu-Zhu)。
10. 重複の統合。新規案は既存ルールと意味が近くないか確認する。目安は埋め込みコサイン類似 0.90 以上で統合候補(ACE 既定値。kayba の例示は 0.85)。統合の判断(統合した・別物として残した)は記録して再判定しない(kayba の similarity_decisions)。ルール数が少ないうちは人の目で十分。
11. 総量の上限。予測時に LLM に読ませる active + probation は最大 30 件程度に抑え、超えたら REMOVE(退役・統合)を優先(ExpeL: 満杯時は REMOVE 優先、AutoManual: N_max=12、Agent Skills: 本文 5,000 トークン未満)。全ルールの本文は保持してよいが、常時読むのは索引だけにする(段階的開示)。
12. 縮小推定。ルールの確率は生の的中率でなく、基準率 p0 への縮小値 p = (当たり + k·p0) / (n + k) を使う(k=20 を初期値とする提案。ベータ事前分布に相当)。少数サンプルの過信を機械的に抑える。
13. 割引。外部研究の効果量を事前値に使うときは、標本外 −26%・公表後 −58% を目安に割り引いて書く(McLean-Pontiff。日本株で同じ幅かは未確認)。
14. 人の承認ゲート。ADD と状態遷移は、プログラムが条件充足を示し、人が承認して初めて反映する(MVP 期)。Bellafiore のレビュー注記に相当。

## 必須回答 (3): 人間・LLM・プログラムが同じ docs を読める表現形式の先行例

| 先行例 | 機械可読部 | 人・LLM 可読部 | 写す点 |
|---|---|---|---|
| Agent Skills(SKILL.md) | YAML front matter(name, description, metadata など) | Markdown 本文、別ファイル参照 | 索引用の短いメタデータと本文の分離。段階的開示 |
| Cursor Rules(.mdc) | front matter(description, globs, alwaysApply) | Markdown 本文 | 「いつ読むか」をメタデータで決める 4 分類。常時読むルールと条件付きルールの区別 |
| MADR 4.0.0 | 任意の YAML front matter(status, date, decision-makers…) | 固定見出しの本文 | 状態を front matter に、理由を本文に。連番ファイル名 |
| Sigma | ルール全体が YAML | description, falsepositives は自然文 | ライフサイクル、ID 規則、related。検出条件を構造化して書く考え方 |
| ACE playbook | 1 行 1 ルール(ID・カウンタ・本文)を正規表現で解析 | 同じ行を LLM がそのまま読む | 最小構成。ルールが短文で済むなら 1 ファイルに並べる形式も可 |
| kayba Skillbook | JSON が正、Markdown は書き出し | `ExportSkillbookMarkdownStep` で人が読む版を生成 | 正本をどちらに置くかの判断材料。本プロジェクトは「docs が正本」という要望なので逆(Markdown が正、JSON は派生) |
| Dynamic Cheatsheet | XML 風タグと Count 行 | 同じテキスト | 説明と例の 2 欄、利用回数 |
| TradingAgents | Markdown ログを追記し、後で決済情報を追記 | 同じログを LLM が読む | 予測と答え合わせを同じファイルに 2 段階で書く |

結論(提案)
- 正本は Markdown(1 ルール 1 ファイル、YAML front matter + 固定見出しの本文)。
- プログラムは python-frontmatter で読み、front matter をスキーマ検証する(pydantic 等。ライブラリ選定は別観点)。検証に落ちたルールは予測に使わない。
- カウンタと INDEX.md は生成物。台帳(JSONL)が事実の正本、ルールファイルが知識の正本。
- LLM には INDEX.md(ID・題名・状態・条件 1 行・確率)を常に読ませ、発火したルールだけ本文を読ませる。

## 必須回答 (4): そのまま写せるテンプレート

以下は本調査で確認した先行例の構造を合成した自作テンプレート(原文の転載ではない)。山括弧は埋める場所。

### 4-1. ディレクトリ構成

```
docs/
  playbook/
    README.md              # 予測手順(READ-DO)。人も LLM も最初に読む
    protocol.md            # 更新プロトコル(本ノートの「必須回答 (2)」を移植)
    INDEX.md               # 自動生成: ID / 題名 / 状態 / 条件 1 行 / 確率 / n / Wilson 下限
    rules/
      R-0001-<slug>.md     # 1 ルール 1 ファイル
    retired/               # 退役・却下ルール(削除しない)
  decisions/
    0001-<title>.md        # MADR 形式: 運用方針の決定記録(閾値の変更など)
  journal/
    2026/2026-10-14.md     # 日次の予測票 + 答え合わせ
  ledger/
    fires.jsonl            # 追記専用: ルール発火と採点
    deltas.jsonl           # 追記専用: ルールブックへの全変更
    trials.jsonl           # 追記専用: 提案された全ルール(却下含む)
```

### 4-2. ルールファイル `docs/playbook/rules/R-0001-<slug>.md`

```markdown
---
id: R-0001                      # 不変。条件や予測を変えたら新 ID を発行
title: <セットアップの短い名前>
type: mechanism                 # mechanism | phenomenon | process | guardrail | corrected-error | open-question
status: candidate               # candidate | probation | active | watch | retired | rejected | unsupported
family: <因果の系統名>           # 例: overnight-us-spillover(系統名は自由だが再利用する)
scope:
  market: TSE
  universe: <対象銘柄群の定義>
  horizon: open_to_close        # 予測の時間軸
condition:                      # IF: observable_by までに観測できるものだけ
  observable_by: "<HH:MM JST>"
  event: <何が起きたか>
  context: <どんな地合い・前提で>
  all:
    - {feature: <特徴量名>, op: ">=", value: <数値>}
  none:
    - {feature: <除外に使う特徴量名>, op: "==", value: <値>}
prediction:                     # THEN
  target: <例: 当日の寄り→引けリターン(対指数超過)>
  direction: <up | down>
  magnitude: {typical: <例: +0.3%>, low: <..>, high: <..>}
  probability: <0.50〜1.00>     # 方向が当たる確率の見積り(縮小推定後)
mechanism: >
  <なぜそうなるかを 1〜3 文で。誰が、なぜ、売買するのか>
evidence:
  grade: <A | B | C>            # A: 複数の査読研究で再現 / B: 単独研究や実務統計 / C: 経験則・未検証
  sources:
    - url: <出典 URL>
      market: <対象市場>
      period: <対象期間>
      effect: <効果量。数値で>
      cost_considered: <true | false>
      verified: <opened | snippet | unverified>
  haircut_note: <外部効果量をどれだけ割り引いたか>
invalidation:                   # 効かなくなる条件・適用除外
  - <例: 当日が決算発表日の銘柄は除外>
data_required:
  - {name: <データ名>, source: <入手元>, available_at: "<HH:MM JST>"}
counters:                       # 自動生成。手で編集しない
  fires: 0
  fire_days: 0
  helpful: 0
  harmful: 0
  neutral: 0
  hit_rate: null
  wilson_lb95: null
  mean_signed_return: null
  t_stat_daily: null
  last_fired: null
related: []                     # 例: [{id: R-0003, type: derived}]  type: derived | obsolete | merged | similar
created: <YYYY-MM-DD>
modified: <YYYY-MM-DD>
status_history:
  - {date: <YYYY-MM-DD>, to: candidate, reason: <登録理由>, approved_by: <human>}
---

## いつ使うか(IF)
<条件を人の言葉で 1〜2 文。判定に迷う境界例も書く>

## 予測(THEN)
<方向・目安の大きさ・時間軸・確率>

## なぜそうなるか
<メカニズム。逆向きに働く力があればそれも書く>

## 根拠
<出典ごとに、対象市場・期間・効果量・コスト考慮の有無・その後の再現や反証>

## 実例
<発火した日の実例を 1〜3 件。日付、銘柄、条件の値、結果。外れた例も 1 件入れる>

## 効かない条件・よくある誤適用
<除外条件、似ているが別のパターン、過去に誤適用した例>

## レビュー注記
<人または別の LLM による注記。日付つき>
```

### 4-3. 日次の予測票と答え合わせ `docs/journal/YYYY/YYYY-MM-DD.md`

```markdown
---
date: <YYYY-MM-DD>
frozen_at: "<寄り付き前の時刻 JST>"   # これ以降、予測欄は編集禁止
forecaster: <human | llm:<モデル名とバージョン> | program:<版>>
playbook_version: <deltas.jsonl の最終行番号またはハッシュ>
settled: false
---

## 1. 全体観(The Big Picture)
- 前夜〜今朝の材料: <箇条書き>
- 基準率: <対象銘柄群の「寄り→引け上昇」の過去比率と期間>
- 今日の地合い判断と、その確信度: <..>
- 自分の状態(人の場合): <睡眠、体調、焦りの有無>

## 2. 予測(寄り付き前に確定)
| # | 銘柄 | 発火ルール ID | 方向 | 確率 | 目安の大きさ | 根拠 1 行 | 反対の材料 |
|---|---|---|---|---|---|---|---|
| 1 | <コード> | R-0001, R-0007 | up | 0.58 | +0.3% | <..> | <..> |

- 見送った候補と理由: <..>
- 影の予測(candidate ルールの発火): <ルール ID と銘柄。公式予測には使わない>

## 3. 答え合わせ(引け後。プログラムが記入)
| # | 実績(寄り→引け) | 対指数超過 | 当否 | Brier 寄与 |
|---|---|---|---|---|
| 1 | <..> | <..> | <hit | miss> | <(確率−結果)²> |

- 当日 Brier: <..> / 基準率予測の Brier: <..> / BSS: <..>

## 4. 振り返り(引け後。LLM または人)
- ルール別タグ: R-0001: <helpful | harmful | neutral>(原因: <rule_wrong | misapplied | noise | regime>)
- 何が違ったか(error_identification): <..>
- なぜ違ったか(root_cause_analysis): <..>
- どうすべきだったか(correct_approach): <..>
- 覚えておくこと(key_insight): <1 文>
- 今日の 1 件(最も腑に落ちたセットアップ): <ルール ID または新パターンの名前と経過>
- ルールブックへの提案(最大 3 件、週次審査に回す): <ADD / EDIT 案。なければ「なし」>
```

### 4-4. 台帳の 1 行(JSONL)

```json
{"date":"2026-10-14","rule_id":"R-0001","ticker":"<コード>","phase":"pending","direction":"up","prob":0.58,"mode":"official","frozen_at":"2026-10-14T08:50:00+09:00"}
{"date":"2026-10-14","rule_id":"R-0001","ticker":"<コード>","phase":"settled","ret_open_close":0.0042,"excess_ret":0.0031,"hit":true,"tag":"helpful","cause":null,"settled_at":"2026-10-14T16:05:00+09:00"}
```

- `mode` は official(公式予測に使った)か shadow(candidate の影の発火)。
- pending 行は寄り付き前に追記し、以後変更しない。settled 行は引け後に追記する(上書きしない)。TradingAgents の 2 段階ログと同じ考え方。

### 4-5. ルールブック変更操作(`deltas.jsonl`)

```json
{"ts":"<ISO8601>","op":"ADD","rule_id":"R-0012","by":"llm-curator","approved_by":"human","reason":"<1 文>","evidence":["journal/2026/2026-10-14.md"]}
{"ts":"<ISO8601>","op":"TAG","rule_id":"R-0001","tag":"helpful","date":"2026-10-14","by":"program"}
{"ts":"<ISO8601>","op":"EDIT","rule_id":"R-0007","field":"invalidation","before":"<..>","after":"<..>","id_preserved":true,"reason":"<..>"}
{"ts":"<ISO8601>","op":"FORK","from":"R-0007","to":"R-0013","relation":"derived","reason":"条件の閾値を変更したため新 ID"}
{"ts":"<ISO8601>","op":"PROMOTE","rule_id":"R-0007","from":"probation","to":"active","stats":{"fire_days":52,"hits":34,"wilson_lb95":0.52,"t_stat_daily":2.4},"approved_by":"human"}
{"ts":"<ISO8601>","op":"DEMOTE","rule_id":"R-0003","from":"active","to":"watch","stats":{"last30_hit_rate":0.43}}
{"ts":"<ISO8601>","op":"RETIRE","rule_id":"R-0003","reason":"<..>","superseded_by":null}
{"ts":"<ISO8601>","op":"MERGE","from":["R-0004","R-0009"],"to":"R-0014","similarity":0.93,"reason":"<..>"}
```

- 許可する操作は ADD / TAG / EDIT / FORK / PROMOTE / DEMOTE / RETIRE / MERGE / REJECT のみ。全文置換に当たる操作は定義しない。
- EDIT で `id_preserved: true` にできる field は title、mechanism、evidence、invalidation、本文の説明のみ。condition と prediction の変更は FORK。

### 4-6. Reflector(振り返り役)への指示の骨子(自作。ACE の JSON キー構成を踏襲)

```
あなたは予測の振り返り役です。入力は (1) 今日の予測票、(2) プログラムが記入した確定結果、(3) 予測で使われたルールの本文です。
結果の数値は確定値です。あなたが正誤を判定し直してはいけません。
次の順で考えてください。
 1. 各予測について、外れ(または当たり)の主因を 1 つ選ぶ: rule_wrong / misapplied / noise / regime。
    迷ったら noise を選ぶ。1 日の結果だけで rule_wrong と断定しない。
 2. 使われた各ルールにタグを付ける: helpful / harmful / neutral。
    harmful は「ルールの因果説明そのものが今日の値動きと矛盾した」場合に限る。
 3. 既存ルールで説明できない、再現しそうなパターンがあれば key_insight に 1 文で書く。なければ空文字。
出力は次の JSON のみ:
{"reasoning": "...", "error_identification": "...", "root_cause_analysis": "...",
 "correct_approach": "...", "key_insight": "...",
 "bullet_tags": [{"id": "R-0001", "tag": "neutral", "cause": "noise"}]}
```

### 4-7. Curator(編集役)への指示の骨子(自作。ACE と ExpeL の制約を踏襲)

```
あなたはルールブックの編集役です。入力は (1) INDEX.md、(2) 直近 1 週間の振り返り JSON、(3) ルール別の統計(プログラム算出)です。
制約:
 - ルールブックを書き直してはいけない。出力できるのは操作のリストだけ。
 - 操作は最大 4 件。うち ADD は最大 3 件。既存ルール 1 件につき操作は 1 つまで。
 - ADD は、既存ルールに無い因果で、別々の営業日 3 日以上の観測または外部出典があるものに限る。
 - active + probation が上限に達している場合、ADD より先に統合・退役の提案を出す。
 - 条件や予測を変える提案は EDIT ではなく FORK として出す。
 - カウンタや状態は書かない(プログラムが決める)。提案が無ければ operations を空にする。
出力は次の JSON のみ:
{"reasoning": "...",
 "operations": [{"type": "ADD", "family": "...", "title": "...", "condition": "...", "prediction": "...",
                 "mechanism": "...", "evidence": ["journal/..."], "invalidation": ["..."]}]}
```

### 4-8. docs だけで予測する手順(READ-DO。`docs/playbook/README.md` に置く)

```
1. 今日の日付と frozen_at を予測票に書く。
2. 基準率を書く(対象銘柄群の過去の上昇比率)。ここが出発点。
3. INDEX.md を上から読み、condition の observable_by が現在時刻より前で、条件を満たすルールを列挙する。
   条件の値はデータから読む。推測で満たしたことにしない。
4. 発火したルールの本文を開き、invalidation に当たらないか確認する。当たれば外す。
5. status が candidate のルールは「影の予測」欄にだけ書く。
6. 公式予測の確率は、基準率から始め、発火した active / probation ルールの確率で動かす。
   probation と watch は動かす幅を半分にする。同じ family のルールが複数発火しても 1 つ分として扱う。
   向きが逆のルールが同時に発火したら、確率は基準率に近づけ、「反対の材料」欄に書く。
7. 確率は 0.35〜0.65 の範囲に収める(運用初期の上限。較正が確認できたら決定記録で広げる)。
8. 予測票を確定し、台帳に pending 行を書く。以後、予測欄は編集しない。
```

手順 6・7 の合成方法と数値は提案であり、先行例で検証されたものではない。

### 4-9. 週次・月次レビューのチェックリスト(DO-CONFIRM)

```
週次(30 分)
 [ ] 今週の Brier と BSS を記録した
 [ ] 振り返りの「提案」を集め、重複を除き、ADD は 3 件以内に絞った
 [ ] 各 ADD 案にメカニズム・除外条件・必要データが書かれている
 [ ] 却下した案も trials.jsonl に記録した
 [ ] 「今日の 1 件」から来週も注目するセットアップを 1 つ選んだ
月次(60 分)
 [ ] ルール別統計(発火日数、的中率、Wilson 下限、t 値)をプログラムで再計算した
 [ ] 昇格・降格・退役・却下の条件を満たすルールを一覧にし、承認した
 [ ] family ごとの試行数 N を確認し、N が多い系統の昇格を慎重にした
 [ ] active + probation の総数が上限以内
 [ ] 較正表(予測確率の帯ごとの実現頻度)を更新した
 [ ] 閾値や手順を変えた場合、docs/decisions/ に決定記録を書いた
```

## 因果ルール候補(該当する場合)

本観点はルールブックの設計なので、市場の値動きに関する因果ルールは他観点のノートに委ねる。ここでは「ルールブック運用そのものの因果」(メタルール)を記す。これらは `docs/playbook/protocol.md` の根拠として使う。

### M-01 全文書き直しは崩壊を招く
- IF LLM にルールブック全体を毎回書き直させる → THEN 数十回の更新のどこかで内容が急激に短くなり、予測品質が無適応の水準を下回りうる(時間軸: 数十ステップ以内)。
- なぜ: LLM は長文の再生成で要約・省略に流れる。一度落ちた細部は次の入力に存在しないので戻らない。
- 根拠: ACE(https://arxiv.org/html/2510.04618v2)。AppWorld で 18,282 トークン・精度 66.7 → 122 トークン・精度 57.1(ベースライン 63.7)。Dynamic Cheatsheet 論文(https://arxiv.org/html/2504.07952v1)も、モデルが記憶を省略して劣化する現象を限界として記載。
- 効かなくなる条件: ルールブックが十分短く、毎回の全文を人が差分確認する運用。
- 判定に必要なデータと入手時刻: ルールブックのトークン数・行数の推移(更新のたび)。
- 確度: B(単独研究の実測 + 別研究の定性的記述。相場領域での検証なし)

### M-02 正解ラベルなしの振り返りは改善が小さいか逆効果
- IF 確定した結果を使わず LLM の自己判定で振り返りを回す → THEN プレイブックの改善幅が縮むか悪化する。
- なぜ: 誤った成功体験・失敗体験からもっともらしい教訓が抽出され、それが蓄積・増幅される。
- 根拠: ACE の金融ベンチ。オンラインで正解ラベルあり +7.5、ラベルなし +3.8、FiNER 単体は −3.4。オフラインでも 81.9 対 77.1。対照的に ReasoningBank(https://arxiv.org/html/2509.25140)は判定精度 70〜90% で成績が近いと報告しており、課題依存。
- 効かなくなる条件: 判定器が十分正確で、課題の成否が明確な場合。
- 判定に必要なデータと入手時刻: 引け後の確定値(当日)。
- 確度: B

### M-03 新ルールの効果は時間とともに縮む
- IF あるルールが標本内(発見時)で効果 X を示した → THEN 標本外では平均して約 26% 小さく、広く知られた後は約 58% 小さいと見込む(時間軸: 年単位)。
- なぜ: データマイニングによる過大評価分の剥落と、公表後の裁定取引による収益機会の消費。
- 根拠: McLean & Pontiff, Journal of Finance 2016、米国株、97 変数(検索結果の抄録で確認、一次ページ未開封)。AlphaAgent 論文の図でも CSI 500 で既存因子の IC が 5 年でほぼ 0 に低下。
- 効かなくなる条件: 制度・構造に根ざし裁定しにくい効果。日本株で同じ減衰幅になるかは未確認。
- 判定に必要なデータと入手時刻: ルール別の期間別成績(月次)。
- 確度: B(米国株の代表的な査読研究 1 本を抄録で確認。追試の一次確認は未了)/ 日本株への適用は C

### M-04 試した候補が多いほど最良候補の見かけ成績は膨らむ
- IF N 個の候補ルールから成績最良のものを選ぶ → THEN そのルールの見かけの成績は真の実力が 0 でも N とともに上がる。
- なぜ: 極値の期待値は試行数の増加関数(極値理論)。
- 根拠: Bailey & López de Prado 2014(https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf)。年率 SR 2.5 でも N=100、非正規収益だと DSR 約 0.90。
- 効かなくなる条件: 候補を事前に理論で絞り、N が小さい場合。
- 判定に必要なデータと入手時刻: 試行の全記録(`trials.jsonl`)。常時。
- 確度: A(数学的性質)

### M-05 発掘型のルールは t 値 2 では足りない
- IF 外部の理論的・実証的裏付けがなく自分のデータから見つけたルールで、t 値が 3 未満 → THEN 偽陽性とみなして昇格させない。
- なぜ: 多数の仮説を暗黙に試しているため、名目 5% の有意水準が実質的に緩くなる。
- 根拠: Harvey, Liu, Zhu, RFS 2016(https://www.nber.org/papers/w20592)。反論として Jensen, Kelly, Pedersen, JF 2023(https://www.nber.org/papers/w28432)は「過半は再現する」と報告。
- 効かなくなる条件: 事前登録された少数の仮説。査読研究で独立に再現済みの効果。
- 判定に必要なデータと入手時刻: 日次クラスタの t 値(月次)。
- 確度: B(学界で論争中)

### M-06 少数サンプルの的中率で昇格させると偶然を拾う
- IF 発火 30 回未満の的中率だけでルールを昇格させる → THEN 真の的中率が 50% 以下のルールを相当数昇格させる。
- なぜ: 二項分布の標本誤差。10 回中 7 回当たりの Wilson 95% 下限は 0.397、30 回中 20 回でも 0.488。
- 根拠: Wilson スコア区間(https://www.evanmiller.org/how-not-to-sort-by-average-rating.html)に基づく自前計算。
- 効かなくなる条件: 効果量が非常に大きい(真の的中率 70% なら約 36 回で検出可能)。
- 判定に必要なデータと入手時刻: 発火日数と当たり数(台帳、日次)。
- 確度: A(統計的性質。閾値の具体値は提案)

### M-07 常時読ませるルールが増えすぎると LLM の予測が不安定になる
- IF 予測時に読ませるルールを上限なく増やす → THEN 想起の正確さが落ち、重複・矛盾するルールに引っ張られる。
- なぜ: 文脈は有限資源で、長くなるほど個々の情報の利用精度が下がる。
- 根拠: Anthropic の記事(2025-09-29、定性的)。先行実装の上限値: ExpeL 8〜10 件、AutoManual 12 件、Agent Skills 本文 5,000 トークン未満、Cursor 1 ルール 500 行未満、Dynamic Cheatsheet 2,000〜2,500 語。反対の主張として ACE は「短い要約より詳細な長い文脈が良い」とし、トークン予算 80,000 を既定にしている。
- 効かなくなる条件: 索引だけ常時読み、本文は発火時に読む段階的開示を採る場合。
- 判定に必要なデータと入手時刻: 予測時に読ませたトークン数、同一入力での予測の再現性。
- 確度: C(相場予測での定量的検証なし)

### M-08 失敗からの教訓は、抽出の仕方次第で薬にも毒にもなる
- IF 外れた予測からも教訓を抽出する → THEN 構造化された抽出(原因と予防策に限定)なら改善、雑な抽出なら悪化。
- なぜ: 失敗軌跡には誤った推論が含まれ、そのまま記憶すると誤りを再生産する。
- 根拠: ReasoningBank の比較(失敗を加えると ReasoningBank 46.5→49.7、AWM 44.4→42.2)。ExpeL のアブレーション(反省文を混ぜると 39.0→29.0)。AutoManual(原因の事前分類で 93.8→97.4)。
- 効かなくなる条件: 不明。
- 判定に必要なデータと入手時刻: 振り返り JSON と、その後のルール成績。
- 確度: B(非金融タスク)

### M-09 基準率から入ると予測が良くなる
- IF 予測の最初に比較クラス(基準率)を明示する → THEN 確率予測の精度(Brier)が改善する。
- なぜ: 個別事情(内部視点)への過剰反応を、統計的な出発点が抑える。
- 根拠: Good Judgment Project。comparison classes タグ付き回答の平均 Brier 0.17、次点 0.26(タグとの相関であり無作為化実験ではない)。1 時間の訓練効果は 1 年以上持続(https://aiimpacts.org/evidence-on-good-forecasting-practices-from-the-good-judgment-project/)。
- 効かなくなる条件: 適切な比較クラスが無い新奇な事象。対象は地政学予測であり、日中の株価方向での効果は未検証。
- 判定に必要なデータと入手時刻: 銘柄群の過去の方向別頻度(前日まで)。
- 確度: B

### M-10 LLM による過去日の「予測」は証拠にならない
- IF LLM の学習期間内の過去日を LLM に予測させてルールを検証する → THEN 成績が歪む(過大にも過小にもなりうる)。
- なぜ: モデルがその後の値動きや企業の帰結を知っている可能性(先読み)と、企業に関する一般知識が判断を攪乱する効果。
- 根拠: Glasserman & Lin 2023(https://arxiv.org/abs/2309.17322)。関連して FINSABER(https://arxiv.org/abs/2505.07078、KDD 2026)は長期・多銘柄で LLM 戦略の優位が大きく劣化と報告、StockBench(https://arxiv.org/abs/2510.02209)は大半の LLM が buy-and-hold に勝てないと報告。
- 効かなくなる条件: 条件判定が完全にプログラム化され LLM を介さないルール(通常のバックテストの注意点だけが残る)。
- 判定に必要なデータと入手時刻: 使用モデルの学習カットオフ日、予測票の frozen_at。
- 確度: B

### M-11 似たルールの乱立は証拠を薄め、判断を遅らせる
- IF 同じ因果を別の言い回しで書いたルールが複数ある → THEN カウンタが分散して昇格判定が遅れ、同じ材料を二重に数えて確率を過大に動かす。
- なぜ: 独立でない証拠を独立として扱うことになる。
- 根拠: ACE の重複統合(コサイン類似 0.90)、RD-Agent(Q) の冗長因子除去(IC 0.99 以上)、AlphaAgent の独自性正則化と「同質な因子は混雑して減衰が早い」という主張。効果の定量は AlphaAgent のヒット率 0.29 対 0.16(正則化全体の効果で、重複除去単独ではない)。
- 効かなくなる条件: family 単位で集計し、同一 family の同時発火を 1 つとして扱う場合。
- 判定に必要なデータと入手時刻: ルール間の発火の重なり率(台帳から月次)。
- 確度: C

### M-12 外れの原因を分類してから更新すると誤更新が減る
- IF 振り返りで「ルールの欠陥か、適用の欠陥か、偶然か」を先に分類する → THEN 誤ったルール追加・削除が減る。
- なぜ: 分類なしだと、失敗軌跡から成功ルールを作るような取り違えが起きる。
- 根拠: AutoManual(https://arxiv.org/html/2405.16247)。case-conditioned prompting の有無で ALFWorld 93.8% → 97.4%。
- 効かなくなる条件: 不明。確率的な結果を持つ領域(相場)での検証は見当たらない。「偶然」の分類は本ノートの拡張で、出典には無い。
- 判定に必要なデータと入手時刻: 振り返り JSON の cause 欄。
- 確度: B(非金融)/ 相場への適用は C

## 落とし穴・反証・注意

- 領域の違い。ACE、ExpeL、AutoManual、ReasoningBank、Dynamic Cheatsheet の成績はすべて「正解が決定的に決まる課題」(Web 操作、QA、数学、家事シミュレーション)のもの。相場の日中方向は 1 回ごとの信号対雑音比が極めて低く、同じ仕組みで同程度の改善が得られる保証はない。本ノートが統計の歯止めを厚くしているのはこのため。
- ACE の「金融で +8.6%」は株価予測ではない。XBRL タグ付けと数式推論のベンチである。
- LLM アルファマイニング論文の成績は再現性に注意。RD-Agent(Q) の主張値(CSI 300 で ARR 14.21%)と、AlphaAgent 論文内での RD-Agent の再評価値(CSI 500、2021–2024 で年率 0.78%)は大きく違う。期間・市場・LLM・評価者が違えば結果は変わる。どちらも中国株・米国株で、日本株の結果は見当たらなかった。
- helpful / harmful カウンタは統計ではない。LLM のタグは説明の整合性の印であって、有効性の証明ではない。昇格判定に使うのは台帳から計算した数値だけにする。
- 「post-mortem」の逆説。GJP のデータでは post-mortem analysis のタグは不正確さと相関していた。因果は不明だが、振り返りの量を増やせば当たるようになるとは限らない。振り返りは短く、構造化し、週次・月次の統計判断と切り離す。
- 学界の未決着。「大半の発見は偽」(Harvey-Liu-Zhu)と「過半は再現する」(Jensen-Kelly-Pedersen、Chen)が並立している。t ≥ 3 は保守側の基準として採るが、絶対視しない。
- 提案閾値は未検証。n ≥ 20、n ≥ 50、的中率 55%、直近 30 発火などの数値は、TradeZella の経験則と統計計算から置いた初期値にすぎない。発火頻度の実態を見て、決定記録を残して調整する。
- 日次クラスタの見落とし。多銘柄を同日に予測すると見かけの n がすぐ増えるが、独立な証拠は日数分しかない。これを怠ると全ルールが早々に「有意」になる。
- ゴールポストの移動。成績を見てから条件の閾値を調整し、過去の発火を数え直すのは最も起こりやすい自己欺瞞。FORK(新 ID、カウンタ 0)を強制する。
- モデル更新。LLM の版が変わると同じ docs でも予測が変わる。予測票にモデル名・版を記録し、版をまたいだ比較は区別する。
- Windows の制約。RD-Agent は Linux 専用・Docker 必須。ACE 公式実装の重複統合は sentence-transformers と faiss に依存(Python 3.13・Windows での動作は本調査で未確認)。MVP は外部フレームワークを入れず、Markdown + YAML + 小さな Python スクリプトで自作するほうが確実。
- ライセンス。ACE(Apache-2.0)、ExpeL(Apache-2.0)、Dynamic Cheatsheet(MIT)、RD-Agent(MIT)、kayba ACE(Apache-2.0)、TradingAgents(Apache-2.0)はコードやプロンプトの流用が可能だが、著作権表示とライセンス文の保持が要る。AutoManual、GEPA、AlphaAgent の repo はライセンス未確認。SMB の書籍と fs.blog の記事は著作物なので、構成を参考にするにとどめ本文は写さない。
- 鮮度。SMB のブログ記事は 2011 年、Decision Journal の記事は更新日不明、GJP の研究は 2011〜2015 年頃のもの。原則は古びにくいが、数値を現在の相場に当てはめる根拠にはならない。

## このプロジェクトへの提案(MVP で採用するもの、後回しにするもの)

MVP で採用
1. 1 ルール 1 ファイルの Markdown + YAML front matter(テンプレート 4-2)。python-frontmatter で読み、スキーマ検証に落ちたルールは使わない。
2. 追記専用の台帳 3 本(fires / deltas / trials)。カウンタと INDEX.md は台帳から再生成。
3. 日次の予測票(テンプレート 4-3)。寄り付き前に確定し、引け後にプログラムが採点。Brier と BSS を毎日記録。
4. 状態は 7 種(candidate / probation / active / watch / retired / rejected / unsupported)。candidate は影のモード。
5. 更新周期の分離: 日次はタグと台帳だけ、週次で ADD / EDIT 審査、月次で状態遷移。
6. LLM の出力は delta の JSON だけ(テンプレート 4-6、4-7)。反映はプログラム、ADD と状態遷移は人が承認。
7. 統計は Wilson 下限と日次クラスタの t 値の 2 つに絞る。縮小推定(k=20)で確率を出す。
8. 外れ原因の 4 分類(rule_wrong / misapplied / noise / regime)。
9. 最初のルール群は「外部の査読根拠があるもの」を優先して少数(10 件前後)から始める。発掘型は candidate に置く。
10. 運用方針の変更は `docs/decisions/` に MADR 形式で残す。

後回し
- 埋め込みによる重複検出(all-mpnet-base-v2、0.90)。ルールが 50 件を超えてから。
- Deflated Sharpe Ratio と online FDR(alpha-investing)。試行数とサンプルが貯まってから。
- GEPA 型の予測手順書の最適化(パレート前線)。Brier の系列が数か月分貯まってから。
- RD-Agent(Q) / AlphaAgent 型の因子自動探索。WSL2 + Docker と日本株の Qlib 形式データが整ってから。機械学習側(予測の一本目)の話であり、docs ルール側とは台帳で接続する。
- Thompson sampling による「どの系統の候補を次に試すか」の配分。
- kayba ACE や ace-agent/ace をライブラリとして組み込むこと。構造は写すが、依存は増やさない。

採用しない
- LLM によるルールブック全文の再生成。
- harmful が 3 回で削除、重要度 0 で即削除といった、少数回の結果による自動削除。
- LLM に過去日を再予測させた成績を昇格の証拠にすること。

## 未追跡の手がかり

- 検索上限で実行できなかった 2 クエリ: 「LLM 売買エージェント × 自己進化するルールブック(2026 年の新着)」「GitHub 上の、日次予測を Brier で採点して教訓を蓄積する OSS」。日本語圏(Zenn、Qiita、note)での ACE・プレイブック運用の実践記事も未探索。
- ace-agent/ace の `ace/prompts/generator.py`(Generator が使った bullet ID をどう報告させるか)と `ace/ace.py`(適応ループ本体)。
- kayba-ai/agentic-context-engine の `ace/implementations/prompts.py` と `docs/design/ACE_DECISIONS.md`(harmful ≥ 3 削除の設計理由)。
- ExpeL 論文 Figure 2(洞察抽出プロンプトの全体図)と `prompts/hotpotQA.py` などタスク別プロンプト。
- AutoManual の付録プロンプトと repo のライセンス、ルール保存形式。
- ReasoningBank の `WebArena/prompt/` 以下の抽出プロンプト、付録 E(限界)。
- TradingAgents のメモリ実装ファイル(v0.5.1 の再編後のパス)、ログ 1 件の書式、保有期間の既定値、地域ベンチマークの対応表。
- AlphaAgent の公式リポジトリの特定とライセンス、後継とみられる AlphaAgentEvo、AlphaSchema のコード公開有無。
- サーベイ arXiv 2608.31041 の本文(adaptation の分類表、評価の落とし穴の節)。
- FinCon(arXiv 2407.06567)本文の信念更新の手順、FinMem(arXiv 2311.13743)の層状メモリ、FinAgent。
- McLean & Pontiff の一次本文、国際市場での公表後減衰の研究(日本を含むか)、日本株アノマリーの減衰に関する研究。
- Open Source Asset Pricing(Chen & Zimmermann、https://www.openassetpricing.com/、2025-10 リリース、CrossSection v1.4.0)の SignalDoc(各予測変数の出典・標本期間・t 値・予測可能性区分を持つ台帳)。ルール台帳のスキーマ先行例として有望だが、フィールド定義は未確認。
- WorldQuant BRAIN のアルファ提出基準、Numerai のモデル評価基準など、実務プラットフォームの昇格基準(未調査)。
- 「A Checklist for Checklists」の PDF 本文、Bridgewater Principles の一次記述、Brett Steenbarger の日誌論、Van Tharp の期待値と SQN、Annie Duke の結果と判断の分離。
- alpha-investing(Foster & Stine)、SAFFRON、逐次確率比検定(SPRT)、CUSUM による劣化検知の一次文献と Python 実装。
- LLM の時系列一貫性に関する研究(学習カットオフを揃えたモデル群など)。
- Mem0、Letta(MemGPT)、A-MEM などの汎用メモリ基盤、AGENTS.md の仕様(Cursor のドキュメント経由で存在のみ確認)。

## 参照 URL 一覧(✅ / ❓ つき)

AI 側(自己改善するプレイブック・メモリ)
- ✅ https://arxiv.org/html/2510.04618v2 — ACE 論文(HTML)
- ✅ https://github.com/ace-agent/ace — ACE 公式実装(README)
- ✅ https://api.github.com/repos/ace-agent/ace — スター 1,360、push 2026-08-24、Apache-2.0
- ✅ https://raw.githubusercontent.com/ace-agent/ace/main/playbook_utils.py
- ✅ https://raw.githubusercontent.com/ace-agent/ace/main/ace/prompts/curator.py
- ✅ https://raw.githubusercontent.com/ace-agent/ace/main/ace/prompts/reflector.py
- ✅ https://raw.githubusercontent.com/ace-agent/ace/main/ace/core/bulletpoint_analyzer.py
- ✅ https://api.github.com/repos/ace-agent/ace/git/trees/main?recursive=1 — ファイル一覧
- ❓ https://iclr.cc/virtual/2026/10018667 — ACE の ICLR 2026 掲載(検索結果で確認、未開封)
- ✅ https://github.com/kayba-ai/agentic-context-engine — README
- ✅ https://api.github.com/repos/kayba-ai/agentic-context-engine — スター 2,592、push 2026-09-24、Apache-2.0
- ✅ https://raw.githubusercontent.com/kayba-ai/agentic-context-engine/main/ace/core/skillbook.py
- ✅ https://raw.githubusercontent.com/kayba-ai/agentic-context-engine/main/docs/design/ACE_REFERENCE.md
- ✅ https://raw.githubusercontent.com/kayba-ai/agentic-context-engine/main/docs/design/ACE_ARCHITECTURE.md
- ✅ https://arxiv.org/html/2308.10144v3 — ExpeL 論文
- ✅ https://github.com/LeapLabTHU/ExpeL — README(スター 245、Apache-2.0。最終 push 日は未確認)
- ✅ https://raw.githubusercontent.com/LeapLabTHU/ExpeL/main/prompts/templates/human.py
- ✅ https://arxiv.org/html/2504.07952v1 — Dynamic Cheatsheet 論文
- ✅ https://github.com/suzgunmirac/dynamic-cheatsheet — README
- ✅ https://api.github.com/repos/suzgunmirac/dynamic-cheatsheet — スター 277、push 2026-03-12、MIT
- ✅ https://raw.githubusercontent.com/suzgunmirac/dynamic-cheatsheet/main/prompts/curator_prompt_for_dc_cumulative.txt
- ✅ https://arxiv.org/html/2405.16247 — AutoManual 論文(HTML、前半 10 万字)
- ✅ https://github.com/minghchen/automanual — スター 55(ライセンス未確認)
- ✅ https://arxiv.org/html/2509.25140 — ReasoningBank 論文(HTML、前半 10 万字)
- ✅ https://github.com/google-research/reasoning-bank — スター 613、Apache-2.0
- ❓ https://research.google/blog/reasoningbank-enabling-agents-to-learn-from-experience/ — 検索結果のみ
- ✅ https://arxiv.org/abs/2303.11366 — Reflexion(抄録)
- ✅ https://github.com/noahshinn/reflexion — スター 3.3k、MIT
- ✅ https://arxiv.org/abs/2305.16291 — Voyager(抄録)
- ✅ https://github.com/MineDojo/Voyager — スター 7.3k、MIT(「検証通過後にのみスキル追加」は未確認)
- ✅ https://arxiv.org/abs/2409.07429 — Agent Workflow Memory(抄録)
- ✅ https://github.com/zorazrw/agent-workflow-memory — スター 478、Apache-2.0
- ✅ https://arxiv.org/abs/2507.19457 — GEPA(抄録)
- ❓ https://github.com/gepa-ai/gepa — 未開封(API は 403)
- ✅ https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents — 2025-09-29

金融 × LLM
- ✅ https://arxiv.org/html/2505.15155v2 — R&D-Agent-Quant 論文(HTML、前半 10 万字。付録の取引コスト仮定は未読)
- ✅ https://github.com/microsoft/RD-Agent — README(Linux のみ、Docker 必須、MIT)
- ✅ https://api.github.com/repos/microsoft/RD-Agent — スター 14,911、push 2026-10-11
- ✅ https://raw.githubusercontent.com/microsoft/RD-Agent/main/rdagent/core/proposal.py
- ✅ https://raw.githubusercontent.com/microsoft/RD-Agent/main/rdagent/scenarios/qlib/prompts.yaml
- ✅ https://arxiv.org/html/2502.16789v1 — AlphaAgent 論文
- ✅ https://github.com/RndmVariableQ/AlphaAgent — スター 419(公式かどうか・ライセンスとも未確認)
- ✅ https://arxiv.org/abs/2607.26642 — AlphaSchema(抄録のみ)
- ✅ https://ar5iv.labs.arxiv.org/html/2402.03755 — QuantAgent
- ✅ https://arxiv.org/abs/2308.00016 — Alpha-GPT(抄録)
- ✅ https://arxiv.org/abs/2407.06567 — FinCon(抄録。査読掲載先は未確認)
- ❓ https://arxiv.org/abs/2311.13743 — FinMem(検索結果のみ)
- ✅ https://github.com/TauricResearch/TradingAgents — README(スター約 11.1 万、Apache-2.0、v0.6.0)
- ✅ https://raw.githubusercontent.com/TauricResearch/TradingAgents/main/README.md — 永続メモリの節
- ✅ https://arxiv.org/abs/2608.31041 — Agentic Quantitative Trading サーベイ(抄録のみ)
- ✅ https://arxiv.org/abs/2505.07078 — FINSABER(抄録。KDD 2026)
- ✅ https://arxiv.org/abs/2510.02209 — StockBench(抄録)
- ✅ https://arxiv.org/abs/2309.17322 — Glasserman & Lin(抄録)

人間側・知識ベース・形式
- ✅ https://ptgmedia.pearsoncmg.com/images/9780132937641/samplepages/0132937646.pdf — The PlayBook 書籍サンプル(PDF を抽出して確認)
- ✅ https://www.smbtraining.com/blog/the-smb-playbook-compiling-our-best-trades — 2011-05-10
- ❓ https://www.slideshare.net/slideshow/singapore-ifest-2013/25178389 — 410 Gone(現在は閲覧不可)
- ✅ https://fs.blog/decision-journal/
- ✅ https://aiimpacts.org/evidence-on-good-forecasting-practices-from-the-good-judgment-project/
- ❓ https://goodjudgment.com/wp-content/uploads/2021/10/Superforecasters-A-Decade-of-Stochastic-Dominance.pdf — 検索結果のみ
- ✅ https://www.projectcheck.org/checklist-for-checklists.html — ページのみ(PDF 本文は未開封)
- ✅ https://www.principles.com/ — トップのみ(5 ステップ等の中身は未確認)
- ✅ https://zettelkasten.de/introduction/
- ✅ https://www.tradezella.com/blog/how-to-build-a-trade-journal — 2026-05-12
- ✅ https://raw.githubusercontent.com/SigmaHQ/sigma-specification/main/specification/sigma-rules-specification.md — v2.1.0
- ✅ https://adr.github.io/madr/ — MADR 4.0.0
- ✅ https://agentskills.io/specification
- ✅ https://cursor.com/docs/context/rules
- ✅ https://github.com/eyeseast/python-frontmatter

統計・再現性
- ✅ https://www.evanmiller.org/how-not-to-sort-by-average-rating.html
- ✅ https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf — PDF を抽出して確認(数式記号は一部欠落)
- ❓ https://papers.ssrn.com/abstract=2326253 — The Probability of Backtest Overfitting(検索結果のみ)
- ✅ https://www.nber.org/papers/w20592 — Harvey, Liu, Zhu
- ✅ https://www.nber.org/papers/w28432 — Jensen, Kelly, Pedersen
- ❓ https://onlinelibrary.wiley.com/doi/10.1111/jofi.12365 — McLean & Pontiff(403。数値は検索結果の抄録で確認)
- ❓ https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2156623 — 同上(403)
- ❓ https://arxiv.org/pdf/2209.13623 — Publication Bias in Asset Pricing Research(検索結果のみ)
- ✅ https://www.openassetpricing.com/ — トップのみ(SignalDoc の項目は未確認)
- ✅ https://dsrobertson.github.io/onlineFDR/
- ✅ https://en.wikipedia.org/wiki/Brier_score
