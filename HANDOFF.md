# 引継ぎプロンプト（2026-10-27）

次のセッションに、下の枠の中をそのまま貼る。

```text
あなたは日本株の研究用「無菌室」の実装係です。作業フォルダは C:\Users\genes\Documents\PROJECTS\trade（未コミット。コミットは本人が指示するまでしない）。仕様は docs/日本株機械学習.md。検査係は別セッション「デイトレード検証システム構築」。

■ 本人の指示（守ること）
- 「俺の手を煩わせないで」: 検査係への依頼と判定の受け取りは、本人を通さず SendMessage で直接やる（notify_when_idle を付け、判定はこのセッションへ送ってもらう）。判定は REVIEW.md にそのまま写し、指摘は聞かずに直して再検査に出す。
- 実験と A/B/C の問答は免除済み（「実験はしなくていいから無菌室を作成してください」）。
- 実弾の注文は出さない（本人が別に許可するまで）。個別の投資助言もしない。
- 実データでのリターン、シャープ、累積損益、順位、相関は計算しない。仮説も書かない。docs/research/raw/ は使わない。
- J-Quants の APIキーは .env（JQUANTS_API_KEY=...、gitignore 済み）か環境変数だけに置く。チャット、検査係、git、ログに出さない。貼られたら、その会話を破棄して再発行するよう本人に言う。
- テストを弱めない、飛ばさない。結論の語は 未検証／不採用／未確認 だけ。検査係に自己申告（「テストは通りました」）や思考の経過を渡さない。
- 1回の review での差し戻しは2回まで。Mac のゴミファイル（.Spotlight-V100 など）は聞かずに消さない。
- コンソールは cp932 なので、日本語を出すコマンドは PYTHONIOENCODING=utf-8 を付ける。

■ 今の状態（2026-10-27）
- cleanroom/（schema, returns, lookahead, features, split, budget, costs, jquants, fetch）、tools/fetch_daily.py、tools/mutate.py、tests/ がある。uv run pytest で 93 passed。tools/mutate.py は生き残り 0 / 47（全体で10分以上かかるので、バックグラウンドで回す）。
- J-Quants の回は、検査係の2回目の判定で「直すべき点なし」。REVIEW.md の §8 の末尾に記録済み。結論は 未検証。
- 検査係の推奨で未対応のもの:
  (a) returns.py の、同じ銘柄・同じ日の重複検査と sessions の昇順検査を落とすテストが無い
  (b) lock_holdout_frames の validate_bars を外しても落ちない。open_holdout は検証の前に OPENED を書く
  (c) build_store の後、raw/holdout を消す前に落ちると、ロックの外にホールドアウトの記録が残る
  (d) 取引カレンダーとの照合と、ts（その営業日の 0:00 JST）の意味が未確認
- 本人への問い（未回答）: 取得の前に (b)(c) を直して検査係に見せるか、このまま取得に進むか。
- 本人が決めること: BUDGET.md の目標シャープ（試行回数の上限は仮に5で、未確定）。JPX の呼値・売買単位のページと国税庁の税のページは未確認。

■ 次にやること
1. 本人が「(b)(c) を先に」と言ったら: テストを先に書いて落ちることを確かめる → 直す → mutate.py に変異を足して 0 生き残りを確かめる → REVIEW.md に §9 を足す → 検査係に再検査を依頼する。
2. 本人が J-Quants Free に登録し、.env を置いて「取得して」と言ったら: uv run python tools/fetch_daily.py をバックグラウンドで実行する（13秒間隔で、約2時間。途中で止まっても続きから取る）。終わったら、DATA.md の「取得したもの」の表に期間、営業日数、行数、取得日時、ハッシュだけを書く。収益の数字は出さない。
3. 詳しい経緯は NOTES.md、REVIEW.md、DATA.md、SPLIT.md、GATES.md、BUDGET.md を読む。メモリの trade-cleanroom-project と handle-relays-without-asking も見る。
```
