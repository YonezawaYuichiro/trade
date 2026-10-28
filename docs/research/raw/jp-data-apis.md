# 日本株のデータ源・API・ライブラリ

> 調査日: 2026-10-13 / 観点: jp-data-apis / 状態: 一次調査(未検証)

凡例: ✅ = この調査中に実際に開いて(または実際にエンドポイントを叩いて)確認 / ❓ = 開けなかった・記憶ベース・二次情報のみ。
「実測」と書いた数値は 2026-10-13 11:30〜12:00 JST に手元から 1 回叩いた結果であり、恒常的な仕様の保証ではない。

調査の制約(正直な申告):
- WebSearch は 11 回成功した時点でセッション共有の検索予算が尽きた(12 回目は拒否)。指示の「最低 15 回」には届いていない。以降は検索エンジンを使わず、既知 URL の直接取得(WebFetch / curl)と、GitHub 公式 CLI(`gh api`, `gh search repos`)によるリポジトリ確認で補った。
- 直接開いて中身を確認したソースは 50 件超(下の参照 URL 一覧の ✅)。
- 株探・Yahoo!ファイナンス(日本)の利用規約本文は 403 / JavaScript 必須で取得できず、❓ のまま。

---

## 結論(5〜10 行)

1. **無料だけで MVP は組める。** 日足・分足・先物・為替・米国株は Yahoo Finance(`yfinance` 1.7.0、Apache-2.0)、適時開示は「やのしん TDnet WEB-API」(非公式・無料・2015 年分まで遡れることを実測)、法定開示は EDINET API v2(無料キー)、需給は JPX 統計ファイルと日証金 CSV、ニュースは RSS で揃う。
2. **J-Quants の Free プランは「12 週間遅延」なので当日の答え合わせには使えない。** 公式データで当日採点したいなら Light(月 1,650 円・税込、当日 16:30 頃更新、過去 5 年)が最小の有料ステップ。
3. **分足の無料蓄積は Yahoo の 1 分足が現実解。** 実測で「1 リクエスト最大 8 日・直近 30 日以内のみ」。毎日(少なくとも週 1 回)取りに行って Parquet に貯める以外に、無料で長期の分足を持つ方法はない。公式に買うなら J-Quants「分足・ティック」アドオン(月 5,500 円、過去 2 年、Light 以上が前提=合計 7,150 円/月)。
4. **Stooq は自動取得先として死んだ。** 2026 年 3 月から API キー必須になり、実測では CSV エンドポイントが JavaScript のブラウザ検証ページを返す。`pandas-datareader` の stooq リーダーも壊れたまま(issue #1012 未解決)。
5. **証券会社 API は「寄り前気配(板)」を取る唯一の無料ルートだが、どれも癖がある。** kabuステーション API は Professional プラン(信用 or 先物 OP 口座 + 約定 1 回以上)が必要で「実弾ゼロ」と衝突。立花証券 e支店 API は無料で日足約 20 年分も出るが、規約で「蓄積・編集・加工は禁止」と明記。楽天 MS2 RSS は無料だが Excel 経由。
6. **2026 年 9 月下旬に信用残の公表が変わった。** JPX の「銘柄別信用取引残高」は毎営業日 16:00 目安の日次掲載になっている(従来は週次)。古いブログ・古いスクレイパーは前提が崩れている。投資部門別売買状況のファイル形式も 2026-09-29 掲載分から変更。
7. **規約面の地雷は 3 つ。** (a) J-Quants は私的利用限定で、解約・ダウングレード時は取得データの削除義務あり。生成 AI に入力するには 4 条件を満たす必要がある。(b) JPX サイトは二次利用・再配信不可、高頻度の自動取得は遠慮要請。(c) Yahoo は非公式利用で、いつ止まってもおかしくない。
8. **朝 8 時台に確定している情報**は、米国株終値・CME 日経先物・ドル円・ADR・前日 15:30 以降の適時開示・前日夕方公表の需給統計・PTS 夜間値。寄前気配(8:00〜)だけは証券口座のツール/API が必要。
9. 予測システムの再現性のため、**「予測時点で見えていたデータ」を生レスポンスごと時刻付きで保存**すること(Yahoo の調整済み株価や J-Quants の Adj 系は後から遡及修正される)。

---

## 丸パクリ候補(優先度順の表)

| # | 名前 | URL | 種別 | ライセンス | 鮮度(最終更新・発表年) | 何をどう写すか | 確認 |
|---|---|---|---|---|---|---|---|
| 1 | yfinance | https://github.com/ranaroussi/yfinance | repo / PyPI | Apache-2.0 | v1.7.0(2026-08-26)、最終 push 2026-10-12、★25,503 | `pip install yfinance`。日足: `yf.download(["7203.T",...], period="5d", interval="1d", auto_adjust=False)`。分足: `yf.Ticker("7203.T").history(period="8d", interval="1m")` を毎日実行し Parquet に追記。ティッカー対応表は下の「詳細 2」をそのまま使う | ✅ |
| 2 | Yahoo chart エンドポイント(生) | `https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=8d` | 非公式 API | 規約上は個人利用想定 | 2026-10-13 実測で稼働 | yfinance が壊れた時の代替。`chart.result[0].timestamp` と `indicators.quote[0].{open,high,low,close,volume}`、`meta.currentTradingPeriod` を読む。制限値は実測済み(1m=8 日/30 日以内、5m=60 日、1h=730 日) | ✅ |
| 3 | J-Quants API V2 + 公式クライアント | https://jpx-jquants.com/ / https://github.com/J-Quants/jquants-api-client-python | 公式 API / repo | クライアントは Apache-2.0(データは私的利用限定) | クライアント v2.8.0(2026-09-30)、★195。V2 は 2025-12 開始、V1 は 2026-06-01 廃止 | `jquantsapi.ClientV2(api_key=...)`、`get_eq_bars_daily_range(start_dt, end_dt)`。ベース URL `https://api.jquants.com/v2`、ヘッダ `x-api-key`。エンドポイント表・フィールド略称(O/H/L/C/Vo/Va/AdjC…)は「詳細 1」を写す | ✅ |
| 4 | やのしん TDnet WEB-API | https://webapi.yanoshin.jp/tdnet/ (仕様: https://webapi.yanoshin.jp/llms.txt) | 非公式 API | 明示ライセンスなし(情報収集・分析向けと記載) | 2026-02-09 更新(llms.txt 公開、英数字コード対応)。2026-10-13 稼働実測 | `GET /webapi/tdnet/list/{today|recent|YYYYmmdd|YYYYmmdd-YYYYmmdd|コード}.json?limit=300`。`items[].Tdnet.{pubdate,company_code,title,document_url,url_xbrl}` を保存。`company_code` は 5 桁なので先頭 4 文字を使う | ✅ |
| 5 | TDnet 適時開示情報閲覧サービス(公式) | `https://www.release.tdnet.info/inbs/I_list_001_YYYYMMDD.html` | 公式 HTML | JPX/東証の著作物 | 2026-10-13 稼働実測 | やのしんが落ちた時のフォールバック。`I_list_{ページ3桁}_{日付}.html` を低頻度で取得し、時刻・コード・会社名・表題・PDF リンクを表から抜く。保持は約 1 か月 | ✅ |
| 6 | EDINET API v2 | https://api.edinet-fsa.go.jp/api/v2/documents.json | 公式 API | 無料(アカウント作成→API キー) | 仕様書 Version 2、2026-06-03 更新 | `?date=YYYY-MM-DD&type=2&Subscription-Key=...` で当日の提出書類一覧(8:30 過ぎから原則 1 分毎更新)。大量保有・臨時報告書の検知に使う | ✅ |
| 7 | JPX 統計ファイル群 | https://www.jpx.co.jp/markets/statistics-equities/index.html | 公式ファイル(PDF/Excel) | 二次利用・再配信不可、自動取得は低頻度で | 2026-10 時点で稼働。形式変更あり(下記) | 公表時刻表(詳細 6)をそのまま cron に写す。投資部門別(木 15:30)、空売り集計(日次)、銘柄別信用残(日次 16:00)、空売り残高(17:00)、裁定(16:00・前々営業日分) | ✅ |
| 8 | 日証金 貸借取引情報 CSV | https://www.taisyaku.jp/download/ | 公式 CSV | 私的利用の範囲、再配布不可 | 2026-10-13 稼働実測(2026/10/09 申込分の確報を確認) | `/data/zandaka.csv`(銘柄別残高、36 列)、`/data/shina.csv`(品貸料率)、`/data/seigenichiran.csv`(制限措置)、`/data/meigara.csv`。エンコードは cp932 | ✅ |
| 9 | 日経平均プロフィル 日次 CSV | `https://indexes.nikkei.co.jp/nkave/historical/nikkei_stock_average_daily_jp.csv` / `..._vi_daily_jp.csv` | 公式 CSV | 日経の著作物(無断複製・転載不可) | 2026/10/09 分まで収録を実測 | 日経平均と日経 VI の日次四本値。cp932、末尾 1 行は著作権注記なので読み飛ばす。2023-01-04 以降のみ | ✅ |
| 10 | ForexFactory 週次カレンダー JSON | https://nfs.faireconomy.media/ff_calendar_thisweek.json | 非公式フィード | 規約未確認 | 2026-10-13 稼働実測(今週 108 件) | `title,country,date,impact,forecast,previous` を保存。`country=="JPY"` と `"USD"`、`impact=="High"` を当日フラグにする | ✅(規約 ❓) |
| 11 | ニュース RSS 群 | 詳細 11 の表 | RSS | 各社規約 | 2026-10-13 に生死を実測 | Yahoo!ニュース経済、東洋経済、PR TIMES、日銀、JPX マーケットニュース、(非公式)wor.jp の日経マーケット。見出し・時刻・リンクだけ保存 | ✅ |
| 12 | kabuステーション API サンプル | https://github.com/kabucom/kabusapi (`sample/Python/kabusapi_board.py`, `kabusapi_register.py`, `kabusapi_ranking.py` ほか) | 公式 repo | MIT | 最終 push 2026-10-03、★438、OpenAPI v1.5 | 寄前気配の取得に `GET http://localhost:18080/kabusapi/board/{symbol}@1`。`MarketOrderSellQty/BuyQty`、`OverSellQty`、`UnderBuyQty`、気配フラグ(0107 寄前気配 等)を 8:00〜9:00 に記録 | ✅ |
| 13 | 楽天 マーケットスピード II RSS | https://marketspeed.jp/ms2_rss/ (関数一覧 PDF: https://marketspeed.jp/guide/manual/ms2rss_function.pdf) | 証券会社ツール(Excel アドイン) | 利用規約による | 関数一覧 2026/9/19 版 | `=RssChart(ヘッダー行,銘柄コード,"1M",3000)` で 1 分足最大 3000 本、`=RssTickList(ヘッダー行,"コード",300)` で歩み値。Python からは win32com で Excel を読む | ✅ |
| 14 | 立花証券 e支店 API サンプル | https://www.e-shiten.jp/e_api/ / https://github.com/e-shiten-jp | 証券会社 API / repo | サンプルは MIT | v4r10(2026-08-29 リリース、v4r9 は 2026-09-27 廃止) | `e_api_get_histrical_price_daily.py`(日足)、`e_api_websocket_receive_pubkey.py`(時価 PUSH)、`e_api_get_news_pubkey.py`。ただし規約で蓄積禁止(詳細 8) | ✅ |
| 15 | awesome-japan-finance-data | https://github.com/ajtgjmdjp/awesome-japan-finance-data | キュレーション | CC0 | 最終 push 2026-08-23、★21 | データ源の索引としてそのまま参照。ただし Stooq の記述は古い(実際は死んでいる)、NHK RSS も更新停止気味 | ✅ |
| 16 | tdnet-disclosure-mcp | https://github.com/ajtgjmdjp/tdnet-disclosure-mcp | repo / PyPI / MCP | Apache-2.0 | v0.2.1(2026-08-23)、★6 | やのしん API のラッパー。開示タイトルの自動分類(earnings / dividend / forecast_revision / buyback / offering / governance / other)のカテゴリ設計を写す | ✅ |
| 17 | edinet-tools | https://github.com/matthelmer/edinet-tools | repo / PyPI | MIT | v0.9.0(2026-10-06)、★55 | EDINET 書類 42 種を型付きで読むライブラリ。大量保有報告書などのパースを自作しない | ✅(README 本文は未読) |
| 18 | J-Quants CLI / 公式 MCP | https://github.com/J-Quants/jquants-cli / https://github.com/J-Quants/j-quants-doc-mcp | repo | MIT / MIT | CLI 最終 push 2026-09-30(★50、Rust)、MCP 2026-03-12(★15) | `jquants --output parquet --save daily.parquet eq daily --code 86970`。エージェント用 Skill は `npx skills add J-Quants/jquants-cli`。MCP は `uv tool install git+https://github.com/J-Quants/j-quants-doc-mcp.git` | ✅ |
| 19 | 日銀 時系列統計 API | `https://www.stat-search.boj.or.jp/api/v1/getDataCode?...` (マニュアル: https://www.stat-search.boj.or.jp/info/api_manual.pdf) | 公式 API | 誰でも利用可、キー不要 | マニュアル 2026-02-18 付 | `format=json&lang=jp&db=...&startDate=YYYYMM&endDate=YYYYMM&code=...`。高頻度アクセスは遮断の可能性と明記 | ✅ |
| 20 | KabuForge | https://github.com/Siyuan-chat/KabuForge | repo | **AGPL-3.0**(コード流用は感染に注意) | v0.1.1(2026-10-04)、★17 | J-Quants → 因子/ML → バックテスト → ペーパーの構成と「decision-time visibility gates」という設計思想を参考に。コードは写さず構成だけ | ✅(README のみ) |
| 21 | dexter-jp | https://github.com/edinetdb/dexter-jp | repo | MIT | 最終 push 2026-10-08、★312 | 日本株リサーチ AI エージェント(EDINET DB + J-Quants)。LLM にデータを渡すツール設計の参考 | ✅(メタデータのみ、README 未読) |
| 22 | pandas-datareader / Stooq | https://github.com/pydata/pandas-datareader | repo | BSD-3 | v0.11.1(2026-06-24)、★3,275 | **不採用。** stooq リーダーは 2026-03 以降 ParserError(issue #1012、2026-04-13 起票、未解決) | ✅ |
| 23 | yahooquery | https://github.com/dpguthrie/yahooquery | repo | MIT | v2.4.1(2025-05-15)、★919 | yfinance の予備。1 年以上更新なしなので主軸にしない | ✅(メタのみ) |
| 24 | japandas / investpy | https://github.com/sinhrks/japandas / https://github.com/alvarobartt/investpy | repo | BSD-3 / MIT | japandas 最終 push 2020-07、investpy PyPI 最終 2022-01 | **不採用(事実上メンテ停止)** | ✅(メタのみ) |

---

## 詳細

### 1. J-Quants API V2(JPX 総研・公式)

**プランと料金(公式サイト、2026-10-13 確認、月額・税込)** ✅

| | Free | Light | Standard | Premium |
|---|---|---|---|---|
| 料金 | 0 円 | 1,650 円 | 3,300 円 | 16,500 円 |
| 収録期間 | 2 年(**12 週間遅延**) | 5 年 | 10 年 | 最大 20 年 |
| レート制限 | 5 回/分 | 60 回/分 | 120 回/分 | 500 回/分 |
| CSV 一括 | 不可(取引カレンダーのみ可) | 可 | 可 | 可 |

**アドオン(Light 以上が前提)** ✅

| アドオン | 月額(税込) | 期間 | 取得方法 | レート制限 |
|---|---|---|---|---|
| 株価 分足・ティック | 5,500 円 | 2 年 | 分足=API/CSV、ティック=CSV のみ | 60 回/分(プラン枠と別) |
| TDnet/適時開示 | 11,000 円 | 5 年 | API/CSV | 100 回/分 |

- 分足・ティックは 2026-01-19 追加、TDnet アドオンは 2026-05-18 開始(JPX リリースで確認)。TDnet アドオンは個人投資家向けで法人・学術は不可。
- 分足は**現物株のみ**(先物の分足は無い)、**日次更新(16:30 頃)でリアルタイムではない**。

**プラン別データ**(○=取得可) ✅

| データ | Free | Light | Standard | Premium |
|---|---|---|---|---|
| 上場銘柄一覧、株価四本値(日通し)、バリュエーション、財務情報(サマリー)、決算発表予定日、取引カレンダー | ○ | ○ | ○ | ○ |
| 投資部門別情報、TOPIX 四本値 | | ○ | ○ | ○ |
| 指数四本値、日経 225 オプション、信用取引残高、日々公表信用残、業種別空売り比率、空売り残高報告、EDINET 大株主・政策保有・大量保有 | | | ○ | ○ |
| 前場四本値、前場/後場別の四本値フィールド、売買内訳、配当金、先物・オプション四本値、財務諸表(BS/PL/CF) | | | | ○ |

**V2 の技術仕様** ✅
- ベース URL: `https://api.jquants.com/v2`。認証は `x-api-key` ヘッダ(ダッシュボードで発行、有効期限なし)。V1 のリフレッシュトークン方式は廃止。
- 2025-12-22 以降の登録者は V2 のみ。V1 は 2026-06-01 に廃止済み。**V1 前提のブログ記事・サンプル(`/v1/prices/daily_quotes` など)は動かない。**
- レスポンスは `{"data":[...], "pagination_key": "..."}`。
- 429 には `Retry-After` が付かない。1 分スライディングウィンドウ。大幅超過を続けると約 5 分ブロック。制限はアカウント単位(キーを増やしても増えない)。`/v2/fins/summary` と `/v2/fins/details` はプランに関わらず 60 回/分。

**エンドポイント対応表(V1 → V2)** ✅

| データ | V2 パス |
|---|---|
| 株価四本値 | `/v2/equities/bars/daily` |
| 前場四本値 | `/v2/equities/bars/daily/am` |
| 株価分足(アドオン) | `/v2/equities/bars/minute` |
| 上場銘柄一覧 | `/v2/equities/master` |
| 決算発表予定 | `/v2/equities/earnings-calendar` |
| 投資部門別 | `/v2/equities/investor-types` |
| 財務情報(サマリー) | `/v2/fins/summary` |
| 財務諸表 | `/v2/fins/details` |
| 配当 | `/v2/fins/dividend` |
| 取引カレンダー | `/v2/markets/calendar` |
| 信用取引残高 | `/v2/markets/margin-interest` |
| 日々公表信用残 | `/v2/markets/margin-alert` |
| 業種別空売り比率 | `/v2/markets/short-ratio` |
| 空売り残高報告 | `/v2/markets/short-sale-report` |
| 売買内訳 | `/v2/markets/breakdown` |
| 指数四本値 / TOPIX | `/v2/indices/bars/daily` / `/v2/indices/bars/daily/topix` |
| 先物 / オプション / 日経 225 オプション | `/v2/derivatives/bars/daily/futures` / `.../options` / `.../options/225` |

**日足のフィールド**(`/v2/equities/bars/daily`) ✅
- 全プラン: `Date, Code, O, H, L, C, UL, LL, Vo, Va, AdjFactor, AdjO, AdjH, AdjL, AdjC, AdjVo, MktCap(廃止予定), ExRT`
- Premium のみ: 前場 `MO, MH, ML, MC, MUL, MLL, MVo, MVa, MAdj*`、後場 `AO, AH, AL, AC, AUL, ALL, AVo, AVa, AAdj*`(他プランではキー自体が返らない)
- `code` か `date` のどちらか必須。`date` だけ指定すると**その日の全上場銘柄**が返る(=毎日 1 リクエストで全銘柄の日足が取れる)。
- 調整値は分割・併合・株主割当のみ(配当は未調整)で、**新しいコーポレートアクションが起きると遡及再計算される**。公式も「時点再現には未調整値を使え」と明記。
- 出来高ゼロの日は OHLC・Vo・Va が Null(0 ではない)。売買停止と区別できない。
- 立会内のみ(ToSTNeT 等の立会外は含まない)。東証のみ(地方単独上場・PTS は対象外)。

**分足のフィールド**(`/v2/equities/bars/minute`) ✅
- `Date, Time(HH:mm、JST、1 分の開始時刻), Code, O, H, L, C, Vo, Va`(未調整)。`date` のみ指定で当日全銘柄。

**更新時刻(JST、公式の更新一覧表)** ✅

| データ | 時刻 |
|---|---|
| 株価四本値 / 指数 / TOPIX / 分足 / ティック / 日々公表信用残 / 業種別空売り比率 | 16:30 頃 |
| 前場四本値 | 12:00 頃(Premium) |
| 信用取引残高 | 16:00 頃(毎営業日、前営業日申込分。**2026-09-24 以前は週末時点のみ収録**) |
| 空売り残高報告 / 上場銘柄一覧 | 17:30 頃(銘柄一覧は翌営業日 8:00 頃にも更新が入ることがある) |
| 売買内訳 | 18:00 頃 |
| 財務情報 | 18:00 頃(速報)/ 24:30 頃(確報)。API の随時反映は Premium のみ |
| 決算発表予定日 | 10:05 頃(3・9 月期のみの別データは 19:00 頃・不定期) |
| 投資部門別 | 週次・第 4 営業日 16:30 頃 |
| 先物・オプション四本値 | 27:00 頃(翌 3:00 頃) |
| TDnet インデックス(アドオン) | 随時 |

**公式クライアント**(`jquants-api-client` v2.8.0) ✅
```python
# 出典: J-Quants/jquants-api-client-python README(Apache-2.0)。本調査では未実行
from datetime import datetime
from dateutil import tz
import jquantsapi

cli = jquantsapi.ClientV2(api_key="*****")   # 環境変数 JQUANTS_API_KEY でも可
df = cli.get_eq_bars_daily_range(
    start_dt=datetime(2022, 7, 25, tzinfo=tz.gettz("Asia/Tokyo")),
    end_dt=datetime(2022, 7, 26, tzinfo=tz.gettz("Asia/Tokyo")),
)
```
- 主なメソッド: `get_eq_master, get_eq_bars_daily, get_eq_bars_daily_am, get_eq_earnings_cal, get_eq_investor_types, get_idx_bars_daily_topix, get_mkt_calendar, get_mkt_short_ratio, get_mkt_short_sale_report, get_mkt_margin_interest, get_mkt_margin_alert, get_mkt_breakdown, get_drv_bars_daily_fut, get_fin_summary, get_fin_dividend, get_fin_earnings_date, get_bulk_list, get_bulk, get_eq_bars_minute, get_eq_bars_5minute, get_eq_bars_15minute, get_td_list, get_td_files, get_td_bulk`
- Python 3.10 以上、pandas 2.2 以上。Python 3.13 でテストされている。

**利用規約の要点(公式 FAQ「利用目的およびデータの利用について」)** ✅
- 私的利用限定。法人利用・第三者配信・データを使ったアプリ提供は営利/非営利を問わず不可。
- 取得データそのものの共有は禁止。分析結果(チャート等)の共有は可だが、継続的・反復的な公開は私的利用と認められない。
- 本人だけが見られる状態ならクラウド保存可。
- **解約・退会後は取得データと、元データを復元できる派生物を削除。プランを下げた場合も上位プランで取ったデータは使えず同様に削除。** 学習済みモデルの重みなど復元不能な派生物は、公開しない限り削除不要。
- **生成 AI への入力は 4 条件すべてを満たす場合のみ私的利用の範囲**: (1) 自身の分析目的、(2) 入力データが AI の学習に二次利用されない設定、(3) 入力データを第三者が閲覧できない、(4) 生成結果を配信・公開しない。

### 2. Yahoo Finance(yfinance / chart エンドポイント)

**基本情報** ✅
- `yfinance` v1.7.0(2026-08-26)、Apache-2.0、★25,503、最終 push 2026-10-12。依存に `curl_cffi>=0.15`(Chrome 偽装セッションが標準)、`websockets>=13`(ライブ配信用 `WebSocket`/`AsyncWebSocket` あり)。
- README は「Yahoo の公開 API を使う研究・教育目的のツール」「Yahoo! finance API は個人利用のみ」と記載。Yahoo とは無関係。

**2026-10-13 の実測結果(chart エンドポイントを直接叩いた)** ✅

| 項目 | 結果 |
|---|---|
| `7203.T` 1 分足 `range=1d` | 09:00 から取得可。11:32:38 JST 時点で最終バー 11:17 → **約 15〜20 分遅延**と推定 |
| 1 分足の上限 | `range=8d` は成功(2,864 本)。`range=1mo` はエラー「Only 8 days worth of 1m granularity data are allowed to be fetched per request」 |
| 1 分足の遡り | 28 日前起点の 6 日間は成功。35 日前起点はエラー「The requested range must be within the last 30 days」 |
| 2 分・5 分・15 分足 | `range=60d` で成功(5 分足 4,630 本、2026-07-14 から) |
| 1 時間足 | `range=730d` で成功(2023-10-13 から) |
| 取引時間メタ | `currentTradingPeriod.regular` の終了は 15:30 JST |
| 寄り付きバー | 09:00 の 1 分足バーの volume が 0 だった(寄り付き出来高がバーに乗らない可能性。要検証) |
| 当日の日足 | 場中でも当日行が返る(暫定値) |

**ティッカー対応表(実測)** ✅

| 対象 | シンボル | 備考 |
|---|---|---|
| 東証個別株・ETF | `7203.T`, `8306.T`, `1306.T`(TOPIX 連動 ETF), `1570.T`(日経レバ) | 1 分足可 |
| 日経平均 | `^N225` | 1 分足可 |
| TOPIX 指数 | **取得不可**(`^TPX`、`998405.T` とも Not Found) | `1306.T` で代用するか J-Quants Light |
| 日経 VI | **取得不可**(`^JNIV` Not Found) | 日経の公式 CSV を使う |
| CME 日経先物(円建て/ドル建て) | `NIY=F` / `NKD=F` | 5 分足可、約 10 分遅延、ほぼ 24 時間 |
| S&P500 先物 | `ES=F` | 5 分足可 |
| ドル円 | `JPY=X` | 1 分足可、ほぼリアルタイム(08:00 から) |
| 米国指数 | `^GSPC`(未実測), `^VIX`, `^SOX`, `^TNX` | 日足を確認 |
| 原油 | `CL=F` | |
| ADR | `TM`, `MUFG` | 日足を確認 |

**コード断片**(仕様から作成、ライブラリ呼び出しは本調査では未実行)
```python
import yfinance as yf
# 日足(答え合わせ用)。auto_adjust=False で未調整の OHLC と Adj Close を両方残す
d = yf.download(["7203.T", "8306.T"], period="5d", interval="1d",
                auto_adjust=False, group_by="ticker", threads=False)
# 分足(蓄積用)。直近 30 日以内・1 回 8 日まで
m = yf.Ticker("7203.T").history(period="8d", interval="1m")
```
```text
# 生エンドポイント(実測済み)
GET https://query1.finance.yahoo.com/v8/finance/chart/7203.T?interval=1m&range=8d
GET https://query1.finance.yahoo.com/v8/finance/chart/7203.T?interval=1m&period1={unix}&period2={unix}
```

**限界**
- 非公式。2025 年に `YFRateLimitError`(429)が頻発した報告が GitHub issue #2422・#2480・discussion #2431 にある(検索結果で把握、本文は未読 ❓)。「100 リクエスト程度で 30 秒休む」という利用者報告あり(2025 年、現状は未確認 ❓)。
- `history()` の既定は `auto_adjust=True`。分割・配当で過去値が書き換わるので、保存は未調整で。
- Yahoo 開発者 API 規約(REV 3-2022)は、収益化・再配布・過剰なリクエストを禁じ、レート制限は Yahoo の裁量としている ✅。Yahoo!ファイナンス(日本)側の規約本文は取得できず ❓。

### 3. Stooq — 不採用

- `https://stooq.com/q/d/l/?s=7203.jp&i=d` は 2026-10-13 実測で **CSV ではなく JavaScript のブラウザ検証(proof-of-work)ページ**を返す。`/q/l/` の気配 CSV は「ページが存在しない」。 ✅
- `pandas-datareader` issue #1012(2026-04-13 起票、未解決): 「2026 年 3 月から Stooq は API キー必須、HTML が返って ParserError」。キー取得は CAPTCHA 経由。 ✅
- ボット検知の回避は本プロジェクトのやるべきことではないので、候補から外す。`awesome-japan-finance-data` など古いリストの Stooq 記述は信用しない。

### 4. 適時開示(TDnet)

| ルート | 料金 | 期間 | 遅延 | 備考 | 確認 |
|---|---|---|---|---|---|
| やのしん TDnet WEB-API | 無料 | 2015-05-15 のデータが返ることを実測(それ以前は未確認) | TDnet と数分間隔で同期 | 非公式・個人運営・SLA なし | ✅ |
| TDnet 公式閲覧サービス(HTML) | 無料 | 約 1 か月(日付プルダウンで確認) | ほぼ即時 | 100 件/ページ。`I_list_001_YYYYMMDD.html` | ✅ |
| J-Quants TDnet アドオン | Light 1,650 円 + 11,000 円/月 | 5 年 | 随時 | 個人のみ。PDF/XBRL ファイル取得可 | ✅ |
| JPX 総研 TDnet API サービス | 未確認 | 5 年 | — | 約款同意の契約制。主に法人向けと推測 | ❓ |

**やのしん API の実測仕様** ✅
- `GET https://webapi.yanoshin.jp/webapi/tdnet/list/{key}.{format}`
- key: `recent` / `today` / `yesterday` / 4 文字コード(`130A` 可)/ `7203-9984` の複数指定 / `YYYYmmdd` / `YYYYmmdd-YYYYmmdd`
- format: `json`, `json2`(ネスト無し), `xml`, `xml2`, `rss`, `atom`, `html`
- パラメータ: `limit`(既定 300), `hasXBRL`(0/1), `keyword`, `stock_code`, `start_datetime`, `end_datetime`, `since_id`, `by_id`
- 実レスポンスのキーは **`"Tdnet"`**(llms.txt の例は `"TDnet"` だが実物は `"Tdnet"`)。フィールド: `id, pubdate, company_code(5 桁), company_name, title, document_url, url_report_type_summary, url_report_type_fs_consolidated, url_report_type_fs_non_consolidated, url_report_type_earnings_forecast, url_report_type_expected_dividends, url_xbrl, markets_string, update_history`
- `document_url` は `https://webapi.yanoshin.jp/rd.php?https://www.release.tdnet.info/inbs/....pdf` のリダイレクト形式。古い日付の PDF 実体は TDnet 側に残っていない可能性が高い(未確認)。
- `since_id` を使えば差分ポーリングができる(数分おきに 1 回で十分)。

```python
# 実レスポンスの形に合わせて作成(curl で同 URL の JSON を確認済み、Python では未実行)
import requests
j = requests.get("https://webapi.yanoshin.jp/webapi/tdnet/list/20261009.json",
                 params={"limit": 300}, timeout=30).json()
rows = [it["Tdnet"] for it in j["items"]]
for r in rows:
    code4 = r["company_code"][:4]
```

### 5. EDINET API v2(金融庁)

- 仕様書「EDINET API 仕様書(Version 2)」は 2026-06-03 更新(97 ページ)。 ✅
- 書類一覧: `https://api.edinet-fsa.go.jp/api/v2/documents.json?date=YYYY-MM-DD&type=2&Subscription-Key=...`(`type=1` はメタデータのみ、`type=2` は一覧込み)。 ✅
- 指定できる日付は過去 10 年以内。土日祝も指定可。 ✅
- **当日分は 8:30 過ぎから原則 1 分毎に更新**。 ✅
- API キーは EDINET 閲覧サイトでアカウント作成(多要素認証あり)→ 発行。初回発行キーを継続利用可。 ✅
- 書類取得 API の `type=5` で CSV 変換済みデータ、という点は二次情報のみ ❓。公式のレート制限値は明記なし(第三者の実測で「3〜5 秒間隔」との記述あり ❓)。
- デイトレ予測での用途は限定的(大量保有報告書・臨時報告書・訂正の検知)。決算短信は TDnet 側。

### 6. JPX 統計(需給)

**公表スケジュール(JPX サイトの各ページ記載、2026-10-13 確認)** ✅

| データ | 頻度 | 時刻(目安) | ファイル | URL |
|---|---|---|---|---|
| 投資部門別売買状況(株式・週間) | 毎週第 4 営業日(通常木曜) | 15:30 | `stock_1_w_YYYYMMDD_YYYYMMDD.xlsx/.pdf` | /markets/statistics-equities/investor-type/index.html |
| 空売り集計(日次)・業種別集計 | 毎営業日 | 時刻記載なし(J-Quants 側は 16:30 頃) | `YYMMDD-m.pdf`, `YYMMDD-g.pdf` | /markets/statistics-equities/short-selling/index.html |
| 銘柄別信用取引残高 | **毎営業日** | 16:00 | (申込分ごと) | /markets/statistics-equities/margin/01.html |
| 日々公表銘柄等信用取引残高 | 毎営業日 | 16:00 | `YYYYMMDD_mtdaily.xlsx/.pdf` | /markets/statistics-equities/margin/index.html |
| 品貸料 | 毎営業日 | 16:00 | | /markets/statistics-equities/margin/02.html |
| 信用取引売買比率 | 毎営業日 | 16:30 | | /markets/statistics-equities/margin/03.html |
| 信用取引現在高(市場全体) | 毎週第 2 営業日(火曜) | 16:00 | | /markets/statistics-equities/margin/04.html |
| 空売り残高(0.5% 以上の報告分) | 毎営業日 | 17:00 | `YYYYMMDD_Short_Positions.xls` | /markets/public/short-selling/index.html |
| 裁定取引の状況(日別) | 毎営業日 | 16:00(**前々営業日分**) | | /markets/statistics-equities/program/index.html |
| 東証上場銘柄一覧 | 毎月第 3 営業日 9:00 以降 | — | `data_j.xlsx`(拡張子が .xls から変わっている) | /markets/statistics-equities/misc/01.html |
| 決算発表予定(翌営業日分) | 毎営業日 | 17:00 頃 | `kessanMM_MMDD.xlsx` | /listing/event-schedules/financial-announcement/index.html |

**直近の制度・形式変更(重要)** ✅
- 投資部門別(株式)は **2026-09-29 掲載分から**、株数・金額の 2 ファイルを 1 ファイルに集約、Excel は 1 シートに全市場、ファイル名も `stock_1_w_...` に変更。
- 信用残: JPX の margin/01 は「銘柄別信用取引残高は日々 16:00 目安」と表示(10/2・10/5・10/6・10/7・10/8 申込分が並ぶ)。margin/04・05 には「2026 年 9 月 18 日申込現在までは旧フォーマット」とある。J-Quants の更新表は「2026-09-24 以前は週末時点のみ収録」、立花証券 API の告知は「仕様変更後のデータ配信は 9 月 29 日 16:00 以降の予定」。3 点が整合するので、**2026 年 9 月下旬に銘柄別信用残が週次から日次に変わった**と読める(JPX の正式リリース文そのものは未確認 ❓)。
- 呼値: 2026-10-30 から TOPIX500 入替に伴い細かい呼値の適用銘柄が変わる(JPX マーケットニュース 2026-10-09)。 ✅

**JPX サイトの利用条件(「サイトのご利用上の注意と免責事項」)** ✅
- 許諾なしの二次利用・再配信は用途を問わず不可(商用目的のデータ収集を含む)。
- 生成 AI での学習・解析・生成に使う場合も、権利侵害や運営方針に反する利用は禁止。
- 「高頻度・高負荷に繋がる可能性のある自動取得等はご遠慮」。
- → 個人が 1 日 1 回、公表時刻の後に各ファイルを 1 回ずつ取る程度に留める。より安全なのは J-Quants Standard(3,300 円)で同じデータを API 取得すること。

### 7. 日証金(貸借残・逆日歩)

- 速報: 証券会社からの申込みを 16:00〜18:30 目途に受付、**18:30 過ぎに集計**して「銘柄別融資・貸株残高(速報)」を主に証券会社・品貸入札参加者向けに公表。 ✅
- 確報: 翌営業日 8:30〜10:00 に翌朝訂正を受付、**11:00 頃**に確報を公表。訂正が大きいと速報と大きく異なる。超過が解消されると「満額」(逆日歩は発生せず、CSV では `*****`)。 ✅
- 品貸料率は申込日の翌営業日の入札で決定。**決算期が接近すると名義確保のため入札が減り、品貸料率が上昇する傾向**と日証金自身が説明。最高料率は投資単位で決まり、注意喚起・申込停止・基準日前などで 2 倍/4 倍、臨時措置で 4 倍/10 倍の倍率適用がある。 ✅
- CSV(cp932): ✅
  - `https://www.taisyaku.jp/data/zandaka.csv` — 列: 申込日, 決済日, 銘柄コード, 銘柄名, 取引所区分名, 上場区分, 速報/確報, 融資新規/返済/残高株数, 貸株新規/返済/残高株数, 差引残高株数, 各金額, 制度信用・買残高株数, 制度信用・売残高株数, 回転日数 など 36 列。実測で 2026/10/09 申込分の確報を収録。
  - `https://www.taisyaku.jp/data/shina.csv` — 先頭 3 行は注記。列: 貸借申込日, 決済日, コード, 銘柄名, 取引所区分, 決算事由, 決算等, 貸借値段, 貸株超過株数, 最高料率, 当日品貸料率, 当日品貸日数, 前日品貸料率, 備考, 制限, 応札倍率ランク。
  - `/data/seigenichiran.csv`(制限措置等一覧)、`/data/meigara.csv`(貸借銘柄一覧。1=貸借、2=貸借融資、0=非制度信用)。
- サイトの個別銘柄画面は最大 7 営業日分。過去分は自分で毎日貯める必要がある。
- サイトポリシー: 私的利用の範囲を超える利用不可、複製・再配布は権利者の許可が必要。スクレイピングへの直接の言及は無し。 ✅
- 速報が taisyaku.jp に何時に載るかは未確認 ❓(証券会社のヘルプでは 19〜21 時頃という二次情報)。

```python
# CSV 冒頭を curl で確認した上で作成(pandas では未実行)
import pandas as pd
z = pd.read_csv("https://www.taisyaku.jp/data/zandaka.csv", encoding="cp932")
s = pd.read_csv("https://www.taisyaku.jp/data/shina.csv", encoding="cp932", skiprows=3)
```

### 8. 証券会社 API(寄前気配・リアルタイム)

| | kabuステーション API(三菱 UFJ e スマート証券) | 立花証券 e支店 API | 楽天 マーケットスピード II RSS |
|---|---|---|---|
| 料金 | 無料(Professional プラン以上) | 無料 | 無料(利用申請) |
| 適用条件 | 信用取引口座 or 先物 OP 口座を開設済み **かつ** 前々々月〜直近で約定 1 回以上。初回ログイン時は翌々月第 1 営業日まで適用 | 口座開設、API 利用設定、公開鍵登録 | 口座、Windows + Excel(Office 2021/2024/365) |
| 方式 | ローカル REST `http://localhost:18080/kabusapi`(検証 18081)+ PUSH(WebSocket)。kabuステーション常駐必須、同一 PC から | インターネット越し HTTPS(JSON、Shift_JIS)+ EVENT I/F(Chunk / WebSocket) | Excel 関数(`RssMarket`, `RssChart`, `RssTickList` 等) |
| 制限 | 登録銘柄 最大 50(REST/PUSH 合算)。情報系は秒間 10 件ほど(FAQ では発注 5 件/秒、情報 10 件/秒)。PUSH 間引き 400ms。利用可能 6:30〜翌 6:15 | 流量制限 秒 10 件。時価照会は 1 要求 最大 120 銘柄。過負荷と判断されると口座利用停止の可能性 | `RssChart` 表示本数 1〜3000、`RssTickList` 1〜300、複数入力の上限 10 件 |
| 過去データ | **ヒストリカル(足)エンドポイントなし**。`/board`, `/symbol`, `/ranking`, `/regulations`, `/margin/marginpremium`, `/timeandsales/{symbol}` など | 日足など過去約 20 年分、4 本値、板、ニュース、証金残・信用残・逆日歩 | 足種 T(ティック)/1M/2M/3M/4M/5M/10M/15M/30M/60M/2H/4H…、`RssChartPast` で日・週・月足 |
| 寄前気配 | `/board` に `MarketOrderSellQty/BuyQty`、`OverSellQty`、`UnderBuyQty`、売買 10 本気配、気配フラグ(0107 寄前気配、0116/0117 寄前気配約定成立ポイントなし/あり)。**Bid/Ask の名前が意味と逆**という公式の注意あり | リアルタイム株価ボード・時価 | `RssMarket` で気配取得 |
| 規約上の注意 | 開発者ポータル規定に API データの蓄積・再配信に関する明文は見当たらず(口座約款側は未確認 ❓) | **「当社提供情報は、蓄積、編集および加工等は禁止」と明記** | RSS を組み込んだ外部プログラムはサポート対象外 |
| 確認 | ✅(OpenAPI v1.5、FAQ、プラン条件ページ) | ✅(API 専用ページ v4.10-000 at 2026.09.27) | ✅(関数一覧 2026/9/19 版、紹介ページ) |

- **「実弾を使わない」との関係**: kabuステーション API は約 3 か月に 1 回の約定実績が必要。立花と楽天は約定条件なしで情報取得可能(口座開設は必要)。
- 立花は無料・条件が軽く・データも厚いが、蓄積禁止条項があるので「毎朝の寄前気配をその場で特徴量化して予測に使い、原データは保存しない」運用が規約に沿うかは**立花の規定を読んで確認が必要**(未確認 ❓)。
- 立花のデモ環境は過去に提供されていた(2021〜2023 年のリリース履歴に記載)が、現行 v4r10 での提供状況は未確認 ❓。

### 9. 先物・夜間・PTS・日経 VI・為替

- **大阪取引所の指数先物(日経 225 先物など)の立会時間**: 日中 8:45〜15:40(クロージング 15:45)、ナイト・セッション 17:00〜翌 5:55(クロージング 6:00)。 ✅ 祝日取引もある(2026-10-12 は祝日取引実施の告知)。 ✅
- **無料で先物を見る方法**: Yahoo の `NIY=F`(CME 円建て)を 5 分足で取得。大阪取引所そのものの夜間四本値は J-Quants Premium(先物四本値、翌 3:00 頃更新)。
- **日経 VI**: 日経平均プロフィルの日次 CSV(`nikkei_stock_average_vi_daily_jp.csv`)。リアルタイム算出は 15 秒間隔だが、無料で取れるのは日次。 ✅
- **PTS(ジャパンネクスト)**: 公式サイトは「特定投資家向け」と明記、統計は日次サマリー・売買代金上位・週次/月次 PDF、市場サマリーは最大 10 分遅延。個別銘柄の夜間値を無料 CSV で配る公式手段は見つからず。 ✅ Yahoo!ファイナンス(日本)の銘柄ページには「夜間 PTS」の値が表示される(7203 で 23:59 時点の値を確認)。 ✅ 株探の PTS ランキングページ(`/warning/pts_night_price_increase`)は HTTP 200。 ✅ ただしどちらも自動取得の可否は規約未確認 ❓。夜間 PTS の時間帯(17:00〜翌 6:00)は検索スニペット経由の情報 ❓。
- **為替**: `JPY=X`(1 分足、ほぼリアルタイム)。FRED の `DEXJPUS` は最新が 2026-10-02(10-05 更新)で 1 週間以上遅れるので使えない。 ✅
- **日経平均(日次)**: FRED `NIKKEI225` は 2026-10-09 の値(69,030.92)を当日 7:02 CDT に更新。日経の著作物で第三者への再配布は許可が必要。 ✅

### 10. マクロ・経済指標カレンダー

| ソース | 中身 | 条件 | 確認 |
|---|---|---|---|
| FRED API | `fred/series/observations`, `fred/releases/dates` | API キー必須(fredaccount でログインして発行)。料金・レート制限はページに記載なし | ✅ |
| 日銀 時系列統計 API | `getDataCode` / 階層 API / メタデータ API、JSON・CSV | キー不要。高頻度アクセスは遮断の可能性 | ✅ |
| 日銀 新着 RSS | `https://www.boj.or.jp/rss/whatsnew.xml` | 8:50 公表物(企業物価指数など)が載る | ✅ |
| ForexFactory 週次 JSON | 今週の指標(国・時刻・重要度・予想・前回) | 非公式、規約未確認 | ✅ / ❓ |
| e-Stat API | 政府統計 | 無料 appId(二次情報) | ❓ |
| FXMacroData | JPY マクロ発表・日銀イベントカレンダー | 一部キー不要(二次情報) | ❓ |

### 11. ニュース

**RSS の生死(2026-10-13 実測)** ✅

| フィード | URL | 状態 |
|---|---|---|
| Yahoo!ニュース 経済 | https://news.yahoo.co.jp/rss/topics/business.xml | 稼働(8 件、当日分) |
| 東洋経済オンライン | https://toyokeizai.net/list/feed/rss | 稼働(20 件) |
| PR TIMES | https://prtimes.jp/index.rdf | 稼働(200 件、企業リリース全般でノイズ多い) |
| 日銀 新着 | https://www.boj.or.jp/rss/whatsnew.xml | 稼働(72 件) |
| JPX マーケットニュース | https://www.jpx.co.jp/rss/markets_news.xml | 稼働(11 件) |
| 日経 マーケット(非公式生成) | https://assets.wor.jp/rss/rdf/nikkei/markets.rdf | 稼働(30 件。「日経平均、続落で始まる 米半導体株安で」09:10 など寄り付き直後の見出しが載る)。第三者による非公式 RSS、規約未確認 ❓ |
| NHK 経済 | https://www3.nhk.or.jp/rss/news/cat5.xml | **最新が 2026-08-08 で止まっている**(更新停止の疑い) |
| ロイター(wor.jp 経由) | https://assets.wor.jp/rss/rdf/reuters/business.rdf | **空(243 バイト)** |
| Bloomberg(wor.jp 経由) | https://assets.wor.jp/rss/rdf/bloomberg/markets.rdf | **空** |
| 株探ニュース | https://kabutan.jp/news/rss/ | RSS ではない(HTML が返る) |

- **GDELT DOC 2.0 API**(`https://api.gdeltproject.org/api/v2/doc/doc?query=...&mode=artlist&format=json`): 2 回叩いて 2 回とも「5 秒に 1 回までに制限せよ」というレート制限メッセージが返った。稼働はしているが、記事 JSON の取得は未確認 ❓。共有 IP の影響の可能性あり。
- 株探: `robots.txt` は `Crawl-delay: 3`、`/search*` を Disallow。利用規約ページ(`info.kabutan.jp/terms-all/`)は 403 で読めず ❓。
- 日経電子版・Bloomberg は公式 RSS/API なし(awesome リストの記載、二次情報 ❓)。

### 12. 先行リポジトリ(データ取得まわり)

| リポジトリ | ★ | 最終 push | ライセンス | 一言 |
|---|---|---|---|---|
| ranaroussi/yfinance | 25,503 | 2026-10-12 | Apache-2.0 | 主力 |
| pydata/pandas-datareader | 3,275 | 2026-07-21 | BSD-3 | 復活したが Stooq は不可 |
| alvarobartt/investpy | 1,857 | 2026-04-13(PyPI は 2022-01) | MIT | Investing.com 依存、実質停止 |
| dpguthrie/yahooquery | 919 | 2025-05-15 | MIT | 予備 |
| kabucom/kabusapi | 438 | 2026-10-03 | MIT | 公式サンプル(Python/C#/JS/Excel) |
| edinetdb/dexter-jp | 312 | 2026-10-08 | MIT | 日本株リサーチ AI エージェント |
| J-Quants/jquants-api-client-python | 195 | 2026-09-30 | Apache-2.0 | 公式クライアント |
| BuffettCode/edinet_xbrl | 140 | 2020-10-30 | Apache-2.0 | 古い |
| UKI000/JQuants-Forum | 107 | 2021-07-19 | なし | 旧 J-Quants コンペの知見(V1 時代) |
| AlpacaDB/jquants-api-sample | 77 | 2024-04-07(アーカイブ済) | なし | V1 時代 |
| J-Quants/JPXTokyoStockExchangePrediction | 58 | 2023-01-12 | Apache-2.0 | Kaggle コンペのデータ・評価 |
| matthelmer/edinet-tools | 55 | 2026-10-06 | MIT | EDINET パーサ |
| J-Quants/jquants-cli | 50 | 2026-09-30 | MIT | 公式 CLI(Rust) |
| ajtgjmdjp/awesome-japan-finance-data | 21 | 2026-08-23 | CC0 | 索引 |
| ajtgjmdjp/edinet-mcp | 18 | 2026-10-12 | Apache-2.0 | EDINET XBRL + MCP |
| Siyuan-chat/KabuForge | 17 | 2026-10-06 | AGPL-3.0 | J-Quants ベースの研究スタック |
| shirasublue/python-kabusapi | 17 | 2021-02-03 | MIT | 古い |
| J-Quants/j-quants-doc-mcp | 15 | 2026-03-12 | MIT | 公式 MCP(仕様参照用) |
| e-shiten-jp/e_api_get_histrical_price_daily.py | 11 | 2026-09-11 | MIT | 立花の日足取得サンプル |
| ajtgjmdjp/tdnet-disclosure-mcp | 6 | 2026-08-23 | Apache-2.0 | やのしん API ラッパー |
| YutaroSugaya/stock-bot | 0 | 2026-10-09 | MIT | Go・立花 API の自動売買 bot。「LLM を発注経路の外に置く」設計(説明文のみ確認) |

(すべて `gh api` でメタデータを確認 ✅。README まで読んだのは awesome-japan-finance-data、tdnet-disclosure-mcp、KabuForge、jquants-api-client-python、yfinance)

### 13. 必ず答えること

#### (1) 無料だけで組む MVP データスタック

| 用途 | ソース | 取得時刻(JST) | コード断片の出典 |
|---|---|---|---|
| 当日の寄り値・引け値(答え合わせ) | yfinance `7203.T` 日足。15〜20 分遅延なので 16:00 以降に取得 | 16:00〜 | 詳細 2 / yfinance README |
| 日足の過去分 | yfinance(1999 年以降の月足まで確認、日足の最長は未実測)。J-Quants Free は 12 週遅れだが 2 年分の公式値で突合に使える | 随時 | 詳細 1・2 |
| 前日米国(S&P500, NASDAQ, SOX, VIX, 米 10 年債) | yfinance `^GSPC`, `^IXIC`, `^SOX`, `^VIX`, `^TNX` | 6:30〜 | 詳細 2 |
| 先物 | yfinance `NIY=F`(CME 日経先物・円建て)、`ES=F` | 8:00、8:45 | 詳細 2 |
| 為替 | yfinance `JPY=X` | 8:00、8:55 | 詳細 2 |
| 開示 | やのしん TDnet API(`since_id` で差分)+ 公式 HTML をフォールバック | 15:30〜翌 8:55 を数分おき | 詳細 4 / https://webapi.yanoshin.jp/llms.txt |
| 法定開示 | EDINET API v2 | 8:30〜 | 詳細 5 / 仕様書 PDF |
| 需給 | JPX 統計(16:00〜17:30 の各ファイル)、日証金 CSV(11:00 以降に確報) | 17:30、翌 11:30 | 詳細 6・7 |
| ボラ指標 | 日経 VI 日次 CSV、`^VIX` | 夕方 | 詳細 9 |
| ニュース | RSS 6 本(詳細 11) | 5〜15 分おき | 詳細 11 |
| 経済指標予定 | ForexFactory 週次 JSON、日銀 RSS | 朝 1 回 | 詳細 10 |
| 営業日判定 | J-Quants `/v2/markets/calendar`(Free でも可)または JPX 営業日ページ | 月 1 回 | 詳細 1 |
| 銘柄マスタ | JPX `data_j.xlsx`(月次)、J-Quants `/v2/equities/master` | 月 1 回 | 詳細 6 |

- 保存は Parquet(日付パーティション)か DuckDB。**生レスポンスを取得時刻つきで別に残す**。
- 対象銘柄は最初は 30〜100 銘柄(日経 225 の売買代金上位など)に絞る。Yahoo への負荷と 429 を避けるため。

#### (2) 朝 8 時台に手に入る「寄り前情報」

| 情報 | いつ確定 | どこから | 無料 | 確認 |
|---|---|---|---|---|
| 米国株終値(指数・SOX・VIX・金利) | 米国引け(夏時間 5:00 / 冬時間 6:00 JST) | yfinance | ○ | ✅(ティッカー実測) |
| CME 日経先物の現在値、大阪夜間の終値(6:00) | 継続 / 6:00 | yfinance `NIY=F`(大阪の公式値は J-Quants Premium) | ○ | ✅ |
| ドル円 | 継続 | yfinance `JPY=X` | ○ | ✅ |
| 日本株 ADR 終値 | 米国引け | yfinance `TM`, `MUFG` など | ○ | ✅ |
| 前日 15:30 以降〜当日朝の適時開示(決算・修正・自社株買い・増資) | 開示の都度 | やのしん API / TDnet 公式 | ○ | ✅ |
| 当日提出の法定開示 | 8:30 過ぎから 1 分毎 | EDINET API v2 | ○ | ✅ |
| 前日夕方公表の需給(銘柄別信用残、日々公表、空売り比率、空売り残高) | 前日 16:00〜17:30 | JPX / J-Quants Standard | ○(JPX) | ✅ |
| 日証金 速報(前日申込分) | 前日 18:30 過ぎに集計 | taisyaku.jp(掲載時刻未確認)。確報は当日 11:00 頃で寄りには間に合わない | ○ | ✅ / ❓ |
| 信用規制・増担保・日々公表指定 | 前日引け後 | JPX margin-daily / margin-reg、日証金 seigenichiran.csv | ○ | ✅ |
| 夜間 PTS の値 | 前日 17:00〜 | Yahoo!ファイナンス(日本)の銘柄ページ、株探 PTS ランキング | 閲覧は○、自動取得は規約未確認 | ✅ / ❓ |
| 当日の経済指標・イベント予定 | 週初に確定 | ForexFactory JSON、日銀 RSS | ○ | ✅ |
| 当日の決算発表予定 | 前営業日 17:00 頃 | JPX 決算発表予定 Excel、J-Quants earnings-calendar | ○ | ✅ |
| 朝のニュース見出し | 継続 | RSS | ○ | ✅ |
| **寄前気配(板、成行売買数量)** | 8:00〜9:00 | kabuステーション API `/board`、立花 API、楽天 RSS | 口座が必要 | ✅ |
| 先物の寄り(8:45) | 8:45 | `NIY=F` で代用、または証券会社 API | ○ | ✅ |

#### (3) 分足を無料で蓄積する方法

1. **Yahoo 1 分足を毎営業日 16:00 以降に取得して追記**(第一候補)。制限は実測で「1 回 8 日・直近 30 日以内」。毎日 `period="2d"` 程度で取り、週 1 回 `period="8d"` で欠損を埋める。5 分足なら 60 日、1 時間足なら 730 日まで遡れるので、初回のバックフィルはそれで行う。
2. **楽天 MS2 RSS の `RssChart(…,"1M",3000)`** を Excel に並べ、Python(win32com)で定期的に読み出して保存。3000 本 ≒ 約 9 営業日分(1 日 330 分で計算)。Windows 11 + Excel が前提で、今の環境に合う。
3. **kabuステーション API の PUSH**(50 銘柄まで)を自前で 1 分足に集計。約定条件(3 か月に 1 回)が必要。
4. 立花 API は蓄積禁止条項があるため、蓄積用途には使わない。
5. 有料なら J-Quants 分足アドオン(過去 2 年・全銘柄・日次 16:30 更新)が最も手堅い。

注意: Yahoo の分足は 15〜20 分遅延で、寄り付きバーの出来高が 0 になる例を確認した。出来高を特徴量に使うなら日足や別ソースと突合すること。

#### (4) スクレイピング可否・再配布制限

| ソース | 自動取得 | 蓄積 | 再配布・公開 | 根拠 | 確認 |
|---|---|---|---|---|---|
| J-Quants API | ○(API) | ○(本人のみ閲覧) | 生データ不可、分析結果の継続的公開は不可、解約・ダウングレード時は削除 | 公式 FAQ | ✅ |
| Yahoo Finance(米) / yfinance | 非公式。個人利用想定、過剰アクセス不可 | 明文なし(ユーザーデータは 24 時間ルール) | 不可 | yfinance README、Yahoo Developer API Terms | ✅ |
| Yahoo!ファイナンス(日本) | 規約本文を取得できず。スクレイピング禁止との記憶があるが未確認 | ❓ | ❓ | — | ❓ |
| Stooq | ボット検知で事実上不可 | — | — | 実測 | ✅ |
| やのしん TDnet API | ○(公開 API、情報収集・分析向け) | 明文なし | 明文なし(原典確認を推奨) | 公式ページ | ✅ |
| TDnet 公式 HTML | JPX サイトと同様に低頻度で | 私的範囲 | 不可 | JPX 利用上の注意(tdnet.info 側の個別規約は未確認) | ✅ / ❓ |
| EDINET API | ○(API) | ○ | 出典明示で可(PDL1.0、二次情報) | 仕様書 / awesome リスト | ✅ / ❓ |
| JPX サイト統計 | 高頻度・高負荷の自動取得は遠慮要請 | 私的範囲 | 二次利用・再配信不可 | サイト利用上の注意 | ✅ |
| 日証金 | 明文なし | 私的利用の範囲 | 不可(許可が必要) | サイトポリシー | ✅ |
| 日経平均プロフィル CSV | 明文は未確認 | 私的範囲 | 無断複製・転載・流布不可 | CSV 末尾の注記 | ✅ |
| kabuステーション API | ○(API、秒間 10 件) | 明文未確認 | 未確認 | ポータル規定 | ✅ / ❓ |
| 立花 e支店 API | ○(API、秒 10 件) | **禁止(蓄積・編集・加工)** | 不可 | API 専用ページ「ご利用にあたって」7 | ✅ |
| 楽天 MS2 RSS | Excel 関数経由 | 未確認 | 未確認 | — | ❓ |
| 株探 | robots.txt は Crawl-delay 3、/search* 不可。規約本文は 403 | ❓ | ❓ | robots.txt のみ | ✅ / ❓ |
| 日銀 API | ○(高頻度は遮断の可能性) | ○ | 留意点 PDF(`api_notice.pdf`)未読 | API マニュアル | ✅ / ❓ |
| GDELT | 5 秒に 1 回まで | — | — | API の応答メッセージ | ✅ |

#### (5) 有料に上げるならどこから、月いくら

| 段階 | 追加するもの | 月額(税込) | 得られるもの |
|---|---|---|---|
| 0 | 無料スタック | 0 円 | 上の (1) |
| 1 | **J-Quants Light** | 1,650 円 | 当日 16:30 の公式日足(全銘柄を 1 リクエスト)、5 年分、TOPIX、投資部門別、CSV 一括。Yahoo 依存を外せる |
| 2 | J-Quants Standard | 3,300 円 | 日次の銘柄別信用残、日々公表信用残、業種別空売り比率、空売り残高報告、指数、日経 225 オプション、10 年分 |
| 3 | + 分足・ティック アドオン | +5,500 円(Light なら計 7,150 円、Standard なら計 8,800 円) | 全銘柄 1 分足・過去 2 年、ティック CSV |
| 4 | J-Quants Premium | 16,500 円 | 前場/後場別の四本値、前場四本値(12:00)、先物・オプション四本値、売買内訳、財務の随時反映、20 年分 |
| 5 | + TDnet アドオン | +11,000 円 | 適時開示インデックスと書類ファイル、5 年分(無料のやのしんで足りるなら不要) |

- 最初の課金は Light(1,650 円)で十分。Standard の価値は「日次信用残」が 2026 年 9 月下旬から出るようになった点にある。
- 途中でプランを下げると上位プランで取得したデータの削除義務が生じる点に注意。
- J-Quants 以外の有料候補(KABU+、Twelve Data、EODHD、IBKR の東証マーケットデータ)は料金・日本株カバレッジを確認できず ❓。moomoo OpenAPI は日本株・日本先物の相場を「Unsupported」と明記 ✅。

---

## 因果ルール候補

この観点はデータ源が主担当なので、ここに書くのは「このデータが取れるから検証できる」ルールの下書きである。**効果量はどれも本調査では未確認**で、確度は原則 C。数値の裏付けは他の観点(先行研究担当)の結果と突き合わせること。

### R1. CME 日経先物の朝の水準 → 寄り付きギャップ
- IF: 8:45 時点の `NIY=F` が前営業日の日経平均終値(15:30)より X% 高い/低い → THEN: 日経平均と指数寄与の大きい大型株は同方向にほぼ同程度ギャップして寄り付く(時間軸: 9:00 の寄り)。寄り後の方向はこのルールからは言えない。
- なぜ: 先物と現物の裁定。夜間に入った海外材料は先物に先に織り込まれる。
- 根拠: メカニズムのみ。出典となる研究は本調査で開いていない。
- 効かなくなる条件: 配当落ち日・SQ 週(先物と現物のベーシスが動く)、寄り前の突発ニュース、限月交代期。
- 判定に必要なデータと入手時刻: `NIY=F` 5 分足(8:45、約 10 分遅延に注意)、前日終値(yfinance / 日経 CSV)。
- 確度: C(裁定メカニズムは強いが、数値は自前バックテスト前)

### R2. 前日の米国半導体株(SOX) → 東証の半導体関連の寄り
- IF: 前日の `^SOX` が大幅安/高 → THEN: 東証の半導体関連(値がさ株)は同方向にギャップして寄る。日経平均の寄りも同方向に傾く。
- なぜ: 同業種の収益見通しが連動し、海外投資家のバスケット売買が波及する。
- 根拠: 逸話 1 件のみ(2026-10-13 09:10 の日経見出し「日経平均、続落で始まる 米半導体株安で」を RSS で確認)。統計的裏付けは未確認。
- 効かなくなる条件: 個別の決算・開示が出た銘柄、為替が逆方向に大きく動いた日。
- 判定に必要なデータと入手時刻: `^SOX` 終値(6:30)、セクター対応表。
- 確度: C

### R3. 引け後の決算・業績修正・自社株買いの開示 → 翌営業日の寄りギャップ
- IF: 15:30 以降に TDnet で上方修正/下方修正/自社株買い/増資が開示 → THEN: 翌営業日の寄りは開示内容の方向にギャップ。寄り後に継続するか反転するかは別途検証が必要。
- なぜ: 開示は引け後に集中し、次に価格がつくのが翌朝の板寄せになる。
- 根拠: メカニズムのみ。効果量は未確認。
- 効かなくなる条件: 事前の観測報道で織り込み済み、PTS で既に大きく動いた後、決算集中日(注目が分散)。
- 判定に必要なデータと入手時刻: やのしん API の `pubdate`・`title`(開示の数分後)、タイトル分類(tdnet-disclosure-mcp のカテゴリ)、PTS 値。
- 確度: C(他観点の研究結果で格上げ余地あり)

### R4. 逆日歩(品貸料)の発生・最高料率の倍率適用 → 売り方の買い戻し
- IF: 日証金で貸株超過が続き、品貸料率が上昇/最高料率に張り付く/倍率適用(2 倍・4 倍・10 倍)になる → THEN: 売り方のコスト増で買い戻しが入りやすく、短期的に下がりにくい(時間軸: 数日)。
- なぜ: 制度信用の売り方全員が品貸料を負担する。決算期が近づくと入札参加者が減り料率が上がりやすい、と日証金自身が説明している。
- 根拠: 料率が上がる仕組みと「決算期接近で上昇する傾向」は日証金の解説ページ(一次ソース)。株価への効果量は未確認。
- 効かなくなる条件: 翌朝訂正で「満額」になった場合(速報と確報が大きく違うことがある)、権利落ち後、貸借銘柄でない銘柄。
- 判定に必要なデータと入手時刻: `shina.csv`、`zandaka.csv`(確報は 11:00 頃。寄り前には前日速報しか無い)。
- 確度: C(料率の傾向そのものは B 相当)

### R5. 日々公表銘柄の指定・増担保規制 → 過熱銘柄の失速
- IF: 急騰銘柄が日々公表銘柄に指定、または増担保規制が入る → THEN: 信用買いの余力が減り、翌日以降の上昇が鈍る/下押しされやすい(時間軸: 翌日〜数日)。
- なぜ: 規制で必要委託保証金が上がり、新規の信用買いが細る。
- 根拠: 経験則。JPX は「日々公表銘柄は規制措置ではなく注意喚起」と明記しており、指定だけでは効果が弱い可能性がある。
- 効かなくなる条件: 現物主導の上昇、規制解除の観測。
- 判定に必要なデータと入手時刻: JPX margin-daily / margin-reg(引け後)、日証金 `seigenichiran.csv`。
- 確度: C

### R6. 夜間 PTS の乖離 → 翌朝の寄りの方向
- IF: 夜間 PTS の値が東証終値から大きく乖離(材料あり・出来高あり) → THEN: 翌朝の寄りは同方向。乖離幅どおりに寄るとは限らない。
- なぜ: 引け後の開示を最初に織り込む場が PTS。
- 根拠: メカニズムのみ。
- 効かなくなる条件: PTS の出来高が極小(数百株)の場合、朝の先物・為替が逆行した場合。
- 判定に必要なデータと入手時刻: PTS 値(自動取得の可否は規約未確認)。
- 確度: C

### R7. 寄前気配の成行数量の偏り → 寄り値の方向
- IF: 8:55 時点の板で成行買い数量が成行売りを大きく上回る(`MarketOrderBuyQty` ≫ `MarketOrderSellQty`)、寄前気配が前日比プラス → THEN: 寄り値は前日比プラス方向。
- なぜ: 板寄せの約定値は寄り前の注文の需給で決まる。
- 根拠: 板寄せの仕組みから。数値は未確認。
- 効かなくなる条件: 8:59 台の大口取消(見せ板)、特別気配、先物の急変。
- 判定に必要なデータと入手時刻: 証券会社 API の板(8:00〜9:00)。
- 確度: C

### R8. 投資部門別売買(海外投資家)の大幅な買い越し/売り越し → 翌週の指数
- IF: 木曜 15:30 公表の週間データで海外投資家が大幅に買い越し/売り越し → THEN: 翌週の指数が同方向、という言説がある。
- なぜ: 海外投資家の売買シェアが大きく、フローに持続性があるとされる。
- 根拠: 言説のみ。公表は対象週の翌週木曜で、すでに 4 営業日以上遅れている。デイトレ予測への寄与は小さいと見るのが妥当。
- 効かなくなる条件: 月末・四半期末のリバランス、先物主導の週。
- 判定に必要なデータと入手時刻: JPX `stock_1_w_*.xlsx`(木 15:30)。
- 確度: C(弱い。採用優先度は低)

---

## 落とし穴・反証・注意

- **J-Quants Free は 12 週間遅延。**「無料で公式の当日データ」は存在しない。
- **J-Quants のダウングレード・解約でデータ削除義務。** 「1 か月だけ Premium にして 20 年分を抜いて解約」は規約違反。
- **J-Quants データを LLM に読ませる場合は 4 条件**(学習に使われない設定、第三者非公開、結果を公開しない、自身の分析目的)。docs ルール予測で LLM を使う設計なら、API 経由で学習オプトアウトされた経路だけを使う。
- **V1 の記事は全滅。** `refreshtoken`、`/v1/prices/daily_quotes`、`AdjustmentClose` などが出てくる記事は 2026-06-01 以降動かない。列名は `AdjC` などに短縮された。
- **Yahoo は非公式で、遅延 15〜20 分、TOPIX 指数と日経 VI は取れない。** 2025 年に大規模な 429 障害があった。yfinance の更新が月 2 回ペースで出ているので、バージョン固定と定期的な更新確認が必要。
- **調整済み株価は後から変わる。** 予測時点の特徴量は未調整値 + 調整係数で持つ。
- **Stooq は使えない。** 古い入門記事・古い awesome リストに注意。
- **NHK の経済 RSS は 2026-08-08 で止まっている。wor.jp のロイター/Bloomberg は空。**
- **立花証券 API は蓄積禁止。** 無料で 20 年分の日足が出るが、保存する設計は規約に抵触する可能性が高い。
- **kabuステーション API は約定実績が必要、登録 50 銘柄、Windows 常駐、Bid/Ask の名前が逆。**
- **JPX の統計ファイルは 2026 年 9 月に形式が変わった**(投資部門別、信用残)。パーサは新形式で書く。URL のディレクトリ名(`t13vrt...-att`)は毎回変わるので、一覧ページからリンクを拾う。
- **日証金の速報と確報は大きく違うことがある。** 寄り前に見られるのは前日の速報だけ。
- **裁定取引の状況は前々営業日分。** 当日の予測には古い。
- **投資部門別は週次で 4 営業日以上遅れ。**
- **東証の現物は 15:30 引け**(Yahoo のメタデータで確認)。古い資料の「15:00 引け」前提のコードは引け値の時刻を間違える。大阪の先物は 15:45 引け・夜間 17:00〜翌 6:00。
- **祝日でも先物は動く**(祝日取引)。祝日明けの寄りは先物と CME の両方を見る。
- **呼値の単位が 2026-10-30 に一部銘柄で変わる。** 値幅・スプレッド系の特徴量に段差が出る。
- **GitHub API は未認証だと 60 回/時**で、今回は途中で枯渇した。`gh` の認証済みトークンを使う。
- **GDELT は 5 秒に 1 回の制限**で、共有 IP だとすぐ弾かれる。
- 反証的な視点: 無料データだけで作ると、寄り付きの板情報と正確な出来高が欠ける。寄り→引けの予測で効きそうな情報ほど有料/口座必須側にある、という構造になっている。

---

## このプロジェクトへの提案

**MVP で採用するもの**
1. yfinance(日足・1 分足・先物・為替・米国株)。バージョンは 1.7.0 に固定し、生エンドポイント直叩きのフォールバックを 1 関数だけ用意する。
2. やのしん TDnet API(差分ポーリング)+ TDnet 公式 HTML のフォールバック。開示タイトル分類は tdnet-disclosure-mcp のカテゴリを出発点にする。
3. JPX 統計と日証金 CSV を 1 日 1 回ずつ(17:30 と翌 11:30)。
4. 日経平均・日経 VI の日次 CSV。
5. RSS 6 本と ForexFactory 週次 JSON。
6. 「予測スナップショット」: 毎朝 8:50 に、その時点で取れた全入力を生のまま 1 フォルダに固める(後で答え合わせするときの先読み防止)。
7. J-Quants は Free で登録だけして、銘柄マスタ・取引カレンダー・12 週遅れの公式日足で Yahoo の値を突合する。

**早めに判断するもの(少額課金)**
- J-Quants Light(1,650 円/月)。Yahoo の欠損・429 が実運用で気になり始めたら即切り替え。
- 楽天証券 or 立花証券の口座開設(無料)。寄前気配をルールに入れるなら必要。立花は蓄積禁止の解釈を先に確認。

**後回しにするもの**
- J-Quants Standard(日次信用残・空売り)と分足アドオン: 日足ベースの予測と採点が回り始めてから。
- kabuステーション API: 約定条件があるので、実弾ゼロ方針のうちは見送り。
- EDINET の本格パース、GDELT、e-Stat、日銀 API: デイトレの寄り→引け予測への寄与が小さい。
- PTS の自動取得: 規約確認が済むまで手動確認に留める。
- KabuForge / dexter-jp の流用: 設計の参考に留める(KabuForge は AGPL)。

**docs に書くべきデータ仕様の雛形**
- 各データに「公表時刻」「予測に使える最早時刻」「遅延」「遡及修正の有無」「規約上の扱い」を 1 行ずつ持たせる(本ノートの表をそのまま転記できる)。

---

## 未追跡の手がかり

- Yahoo!ファイナンス(日本)の利用規約・スクレイピング禁止条項の本文(ヘルプは JavaScript 必須で取得できず)。
- 株探の利用規約本文(403)、株探プレミアムの料金、決算速報・PTS ページの自動取得可否。
- みんかぶ、TRADERS WEB の規約と RSS の有無。
- JPX の「銘柄別信用取引残高の日次化」の正式リリース文と開始日。
- JPX 総研の公式 TDnet API サービスの料金と個人契約の可否。
- taisyaku.jp に速報が載る正確な時刻。
- ジャパンネクスト PTS の公式な取引時間ページ、SBI・楽天経由での PTS 値の取得手段。
- yfinance の 2026 年時点のレート制限の実態(何リクエストで 429 になるか)、issue #2422・#2480 の結末。
- Yahoo 1 分足の寄り付きバー出来高 0 が恒常的かどうか。日足の最長取得期間。
- J-Quants の `/v2/bulk/*` の仕様、年払い割引の有無、Free プランでの `date` 単独指定の可否。
- 立花証券の「当社規定」の該当条文(蓄積禁止の範囲)、現行のデモ環境の有無。
- 楽天 MS2 RSS の利用規約(蓄積・第三者提供)、同時に登録できる関数数の上限。
- KABU+ の料金、Twelve Data・EODHD・IBKR の日本株カバレッジと料金。
- GDELT DOC API の実際の日本語記事 JSON、日本語ソースの網羅度。
- 日銀 API の「利用時の留意点」PDF、e-Stat API、FXMacroData。
- wor.jp(非公式 RSS 生成)の規約と安定性。
- 大阪取引所の先物夜間四本値を無料で取れる公式ページの有無(JPX の日報・清算値段ページ)。
- dexter-jp・edinet-tools・edinet-mcp・stock-bot の README とデータ取得コードの中身。
- UKI000/JQuants-Forum(旧コンペ上位者の特徴量設計)、JPXTokyoStockExchangePrediction(Kaggle)のデータ定義。
- 因果ルール R1〜R8 の効果量を裏付ける研究(オーバーナイト/日中リターンの分解、決算後ドリフト、空売り・信用残と将来リターンなど)。本観点では 1 本も開いていない。

---

## 参照 URL 一覧(✅ / ❓ つき)

**J-Quants**
- ✅ https://jpx-jquants.com/en (料金・プラン・アドオン)
- ✅ https://jpx-jquants.com/en/spec.md (V1 廃止日)
- ✅ https://jpx-jquants.com/en/spec/quickstart
- ✅ https://jpx-jquants.com/en/spec/migration-v1-v2
- ✅ https://jpx-jquants.com/en/spec/rate-limits
- ✅ https://jpx-jquants.com/spec/data-update (更新時刻表)
- ✅ https://jpx-jquants.com/ja/spec/data-spec (プラン別収録期間)
- ✅ https://jpx-jquants.com/en/spec/eq-bars-daily
- ✅ https://jpx-jquants.com/en/spec/eq-bars-minute
- ✅ https://jpx-jquants.com/en/spec/jquants-cli
- ✅ https://jpx-jquants.com/en/spec/mcp-server
- ✅ https://jpx-jquants.com/en/help/data
- ✅ https://jpx-jquants.com/ja/help/usage (利用目的・データ利用 FAQ)
- ✅ https://www.jpx.co.jp/corporate/news/news-releases/6020/20260119.html (CSV・分足/Tick 追加)
- ✅ https://www.jpx.co.jp/corporate/news/news-releases/6020/20260518-01.html (TDnet アドオン)
- ✅ https://github.com/J-Quants/jquants-api-client-python
- ✅ https://github.com/J-Quants/jquants-cli
- ✅ https://github.com/J-Quants/j-quants-doc-mcp (メタデータのみ)

**Yahoo / yfinance / Stooq**
- ✅ https://github.com/ranaroussi/yfinance
- ✅ https://pypi.org/pypi/yfinance/json
- ✅ https://raw.githubusercontent.com/ranaroussi/yfinance/main/yfinance/scrapers/history.py
- ✅ https://query1.finance.yahoo.com/v8/finance/chart/7203.T (各種パラメータで実測)
- ✅ https://legal.yahoo.com/us/en/yahoo/terms/product-atos/apiforydn/index.html
- ✅ https://finance.yahoo.co.jp/quote/7203.T (夜間 PTS 表示の確認)
- ❓ https://support.yahoo-net.jp/PccFinance/ (ヘルプ。JavaScript 必須で読めず)
- ❓ https://github.com/ranaroussi/yfinance/issues/2422 / issues/2480 / discussions/2431 (検索結果のみ)
- ✅ https://stooq.com/q/d/l/?s=7203.jp&i=d (ブラウザ検証ページが返ることを実測)
- ✅ https://github.com/pydata/pandas-datareader/issues/1012

**開示**
- ✅ https://webapi.yanoshin.jp/tdnet/
- ✅ https://webapi.yanoshin.jp/llms.txt
- ✅ https://webapi.yanoshin.jp/webapi/tdnet/list/today.json (ほか日付指定で実測)
- ✅ https://www.release.tdnet.info/inbs/I_main_00.html
- ✅ https://www.release.tdnet.info/inbs/I_list_001_20261013.html
- ❓ https://www.jpx.co.jp/markets/paid-info-listing/tdnet/index.html (公式 TDnet API。403)
- ✅ https://disclosure2dl.edinet-fsa.go.jp/guide/static/disclosure/WZEK0110.html
- ✅ https://disclosure2dl.edinet-fsa.go.jp/guide/static/disclosure/download/ESE140206.pdf (EDINET API 仕様書 v2)
- ✅ https://github.com/ajtgjmdjp/tdnet-disclosure-mcp
- ✅ https://github.com/matthelmer/edinet-tools (メタデータのみ)

**JPX 統計・制度**
- ✅ https://www.jpx.co.jp/markets/statistics-equities/index.html
- ✅ https://www.jpx.co.jp/markets/statistics-equities/investor-type/index.html
- ✅ https://www.jpx.co.jp/markets/statistics-equities/short-selling/index.html
- ✅ https://www.jpx.co.jp/markets/statistics-equities/margin/index.html (01〜05.html も)
- ✅ https://www.jpx.co.jp/markets/statistics-equities/program/index.html
- ✅ https://www.jpx.co.jp/markets/statistics-equities/misc/01.html
- ✅ https://www.jpx.co.jp/markets/public/short-selling/index.html
- ✅ https://www.jpx.co.jp/markets/equities/margin-daily/index.html
- ✅ https://www.jpx.co.jp/markets/equities/margin-reg/index.html
- ✅ https://www.jpx.co.jp/listing/event-schedules/financial-announcement/index.html
- ✅ https://www.jpx.co.jp/derivatives/rules/trading-hours/index.html
- ✅ https://www.jpx.co.jp/term-of-use/index.html
- ✅ https://www.jpx.co.jp/rss/markets_news.xml
- ✅ https://www.jpx.co.jp/news/1030/20281009-01.html (10 月 30 日以降の呼値の単位。URL は RSS 記載のまま)

**日証金・日経・PTS**
- ✅ https://www.taisyaku.jp/
- ✅ https://www.taisyaku.jp/download/
- ✅ https://www.taisyaku.jp/about/report/
- ✅ https://www.taisyaku.jp/about/backwardation/
- ✅ https://www.taisyaku.jp/site-policy/
- ✅ https://www.taisyaku.jp/data/zandaka.csv / shina.csv (冒頭のみ)
- ✅ https://indexes.nikkei.co.jp/nkave/index/profile?idx=nk225vi
- ✅ https://indexes.nikkei.co.jp/nkave/historical/nikkei_stock_average_daily_jp.csv
- ✅ https://indexes.nikkei.co.jp/nkave/historical/nikkei_stock_average_vi_daily_jp.csv
- ✅ https://www.japannext.co.jp/ (/en/trading, /en/statistics)

**証券会社 API**
- ✅ https://kabucom.github.io/kabusapi/ptal/index.html
- ✅ https://kabucom.github.io/kabusapi/ptal/howto.html
- ✅ https://kabucom.github.io/kabusapi/ptal/faq.html
- ✅ https://kabucom.github.io/kabusapi/ptal/guide.html
- ✅ https://kabucom.github.io/kabusapi/reference/kabu_STATION_API.yaml
- ✅ https://kabu.com/item/kabustation_api/default.html
- ✅ https://kabu.com/kabustation/services.html (プラン条件)
- ✅ https://github.com/kabucom/kabusapi
- ✅ https://www.e-shiten.jp/e_api/
- ✅ https://github.com/e-shiten-jp
- ✅ https://marketspeed.jp/ms2_rss/
- ✅ https://marketspeed.jp/guide/manual/ms2rss_function.pdf
- ✅ https://www.rakuten-sec.co.jp/web/support/cs/ms2_rss.html (一部のみ表示)
- ✅ https://openapi.moomoo.com/moomoo-api-doc/en/intro/authority.html (日本株は非対応)

**マクロ・ニュース**
- ✅ https://fred.stlouisfed.org/docs/api/fred/
- ✅ https://fred.stlouisfed.org/docs/api/api_key.html
- ✅ https://fred.stlouisfed.org/series/DEXJPUS
- ✅ https://fred.stlouisfed.org/series/NIKKEI225
- ✅ https://www.stat-search.boj.or.jp/info/api_manual.pdf
- ❓ https://www.stat-search.boj.or.jp/info/api_notice.pdf (未読)
- ✅ https://www.boj.or.jp/rss/whatsnew.xml
- ✅ https://nfs.faireconomy.media/ff_calendar_thisweek.json
- ✅ https://news.yahoo.co.jp/rss/topics/business.xml
- ✅ https://toyokeizai.net/list/feed/rss
- ✅ https://prtimes.jp/index.rdf
- ✅ https://assets.wor.jp/rss/rdf/nikkei/markets.rdf
- ✅ https://www3.nhk.or.jp/rss/news/cat5.xml (更新停止気味)
- ✅ https://assets.wor.jp/rss/rdf/reuters/business.rdf (空)
- ✅ https://api.gdeltproject.org/api/v2/doc/doc (レート制限メッセージのみ)
- ✅ https://kabutan.jp/robots.txt
- ❓ https://info.kabutan.jp/terms-all/ (403)

**リポジトリ・その他**
- ✅ https://github.com/ajtgjmdjp/awesome-japan-finance-data
- ✅ https://github.com/Siyuan-chat/KabuForge
- ✅ https://github.com/edinetdb/dexter-jp (メタデータのみ)
- ✅ https://github.com/dpguthrie/yahooquery (メタデータのみ)
- ✅ https://github.com/pydata/pandas-datareader (メタデータのみ)
- ✅ https://github.com/sinhrks/japandas (メタデータのみ)
- ✅ https://github.com/alvarobartt/investpy (メタデータのみ)
- ✅ https://github.com/J-Quants/JPXTokyoStockExchangePrediction (メタデータのみ)
- ✅ https://github.com/UKI000/JQuants-Forum (メタデータのみ)
- ✅ https://kabu.plus/ (料金は記載なし)
- ✅ https://twelvedata.com/pricing (日本株の記載なし)
- ✅ https://eodhd.com/pricing (東証の記載なし)
