# REVIEW

状態: **新しい回は、検査係の2回目の判定で直すべき点なし（§8 末尾）。推奨 (a)〜(c) と (d) の `ts` の意味には対応した（§9、検査係の判定はまだ）。(d) の取引カレンダーとの照合は、公式ページの写し待ち**。前の回は、検査係の2回目の判定で直すべき点なし（§5）。結論は「未検証」。試行回数の上限が未確定なので、モデル探索には進まない（`BUDGET.md`）。

## 1. テストを先に書いた記録

実装の前に、関数の中身を `raise NotImplementedError` にしたまま `tests/` を実行し、全部落ちることを確かめた（2026-10-27）。

```
uv run pytest -q -p no:cacheprovider --continue-on-collection-errors
27 failed, 1 error
```

`error` は `tests/test_no_lookahead.py` の収集時の `NotImplementedError`。

## 2. 変異の一覧

`uv run python tools/mutate.py` で取った記録（2026-10-27、データ取得コードを足した後に取り直した）。一時フォルダに写したコードを1箇所ずつ壊して `tests/` を実行した。元のファイルは変えていない。M19〜M26 は、検査係の指摘と検査係が入れた変異を足したもの。M15 は、指摘 d の修正で壊す行の文字列が変わったので、新しい行に合わせた。M04・M05・M08・M23・M25 は、§7 の変更で壊す行が変わったので合わせた。M27〜M37 は §7 で足したコードの変異。M38〜M47 は §8 の指摘への対応の変異。M05・M33 は §8 の変更で壊す行が変わったので合わせた。M48〜M54 は §9 の推奨への対応の変異。M14 は §9 でタイムゾーンの検査を1行にまとめたので合わせた（2026-10-28 に取り直した）。

| ID | 壊し方 | ファイル | 結果 | 落ちたテスト |
|---|---|---|---|---|
| M01 | 先読みを混ぜる（過去リターンを1日先にずらす） | `cleanroom/features.py` | 落ちた | `test_past_only_features_pass[past_return_1]`<br>`test_past_only_features_pass[past_return_5]`<br>`test_past_return_values` |
| M02 | 全期間で標準化する | `cleanroom/features.py` | 落ちた | `test_past_only_features_pass[trailing_zscore_20]` |
| M03 | 中央寄せの窓にする | `cleanroom/features.py` | 落ちた | `test_past_only_features_pass[trailing_zscore_20]` |
| M04 | 企業行為の日のリターンを埋める（AdjFactor を見ない） | `cleanroom/returns.py` | 落ちた | `test_return_across_split_is_missing`<br>`test_return_across_reverse_split_is_missing` |
| M05 | Null の日に前の終値を繰り越す | `cleanroom/returns.py` | 落ちた | `test_null_day_has_no_return_and_is_not_carried` |
| M06 | ホールドアウトを通常の読み込みが返す | `cleanroom/split.py` | 落ちた | `test_build_store_locks_holdout_and_hashes_files`<br>`test_normal_loader_does_not_return_holdout`<br>`test_loader_rejects_nan_written_in_file`<br>`test_flag_column_null_survives_round_trip`<br>`test_lock_from_daily_frames_matches_single_frame` |
| M07 | 通常の読み込みの、ホールドアウト混入の検査を消す | `cleanroom/split.py` | 落ちた | `test_loader_rejects_holdout_rows_placed_in_main`<br>`test_loader_rejects_holdout_start_day_alone` |
| M08 | ロック時にホールドアウトも通常のファイルへ書く | `cleanroom/split.py` | 落ちた | `test_build_store_locks_holdout_and_hashes_files`<br>`test_normal_loader_does_not_return_holdout`<br>`test_holdout_rows_are_not_in_main_file`<br>`test_loader_rejects_nan_written_in_file`<br>`test_flag_column_null_survives_round_trip`<br>`test_lock_from_daily_frames_matches_single_frame` |
| M09 | ホールドアウトを2回開ける | `cleanroom/split.py` | 落ちた | `test_holdout_opens_once_with_confirmation` |
| M10 | 確認の文字列なしで開ける | `cleanroom/split.py` | 落ちた | `test_holdout_opens_once_with_confirmation` |
| M11 | パージと余白を消す | `cleanroom/split.py` | 落ちた | `test_segments_keep_label_windows_apart` |
| M12 | 断言を消す: 先読み検査の違反を見逃す | `cleanroom/lookahead.py` | 落ちた | `test_lookahead_features_fail[future_return]`<br>`test_lookahead_features_fail[full_period_standardize]`<br>`test_lookahead_features_fail[centered_mean]`<br>`test_start_dependent_feature_fails` |
| M13 | 先読み検査の許容差を大きくする | `cleanroom/lookahead.py` | 落ちた | `test_start_shift_catches_full_period_standardize` |
| M14 | 断言を消す: タイムゾーンなしの時刻を通す | `cleanroom/schema.py` | 落ちた | `test_naive_timestamp_is_rejected`<br>`test_timezone_other_than_tokyo_is_rejected[UTC]`<br>`test_timezone_other_than_tokyo_is_rejected[America/New_York]` |
| M15 | 断言を消す: float の価格を通す | `cleanroom/schema.py` | 落ちた | `test_float_price_is_rejected`<br>`test_single_float_price_is_rejected` |
| M16 | 式 (4) の第2項を 1 − e/N と読み違える | `cleanroom/budget.py` | 落ちた | `test_paper_example_ten_trials_gives_sharpe_157`<br>`test_paper_example_five_years_allows_45_trials`<br>`test_paper_example_seven_trials_for_two_years`<br>`test_one_trial_is_always_allowed` |
| M17 | コスト下限を呼値1つ分にする | `cleanroom/costs.py` | 落ちた | `test_cost_floor_is_two_ticks_over_price` |
| M18 | 端株を許す | `cleanroom/costs.py` | 落ちた | `test_quantity_is_whole_lots` |
| M19 | 先読み検査から開始点のずらしを外す（指摘 a、P2） | `cleanroom/lookahead.py` | 落ちた | `test_start_dependent_feature_fails` |
| M20 | ホールドアウトのハッシュ照合を外す（指摘 b、P4） | `cleanroom/split.py` | 落ちた | `test_holdout_changed_after_lock_is_refused` |
| M21 | 混入検査の境界を > にする（指摘 c、P7） | `cleanroom/split.py` | 落ちた | `test_loader_rejects_holdout_start_day_alone` |
| M22 | Decimal の NaN と無限大を通す（指摘 d） | `cleanroom/schema.py` | 落ちた | `test_non_finite_or_non_positive_price_is_rejected[NaN]`<br>`test_non_finite_or_non_positive_price_is_rejected[sNaN]`<br>`test_non_finite_or_non_positive_price_is_rejected[Infinity]`<br>`test_non_finite_or_negative_volume_is_rejected[NaN]`<br>`test_non_finite_or_negative_volume_is_rejected[Infinity]`<br>`test_bad_adj_factor_is_rejected[NaN]`<br>`test_loader_rejects_nan_written_in_file`<br>`test_lock_refuses_invalid_frame`<br>`test_invalid_holdout_is_refused_before_opening_is_used_up` |
| M23 | 正でない価格を通す（指摘 d） | `cleanroom/schema.py` | 落ちた | `test_non_finite_or_non_positive_price_is_rejected[0]`<br>`test_non_finite_or_non_positive_price_is_rejected[-5]`<br>`test_bad_adj_factor_is_rejected[0]`<br>`test_bad_adj_factor_is_rejected[-0.5]` |
| M24 | 負の出来高を通す（指摘 d） | `cleanroom/schema.py` | 落ちた | `test_non_finite_or_negative_volume_is_rejected[-1]` |
| M25 | ロックの境界を > にする（検査係の P3） | `cleanroom/split.py` | 落ちた | `test_build_store_locks_holdout_and_hashes_files`<br>`test_normal_loader_does_not_return_holdout`<br>`test_holdout_rows_are_not_in_main_file`<br>`test_holdout_opens_once_with_confirmation`<br>`test_loader_rejects_holdout_start_day_alone`<br>`test_loader_rejects_nan_written_in_file`<br>`test_flag_column_null_survives_round_trip`<br>`test_lock_from_daily_frames_matches_single_frame` |
| M26 | 先読み検査から末尾の切り詰めを外す（検査係の P1） | `cleanroom/lookahead.py` | 落ちた | `test_lookahead_features_fail[future_return]`<br>`test_lookahead_features_fail[centered_mean]` |
| M27 | 数値を float で読む | `cleanroom/jquants.py` | 落ちた | `test_numbers_are_parsed_as_decimal_not_float` |
| M28 | pagination_key を追わない | `cleanroom/jquants.py` | 落ちた | `test_pagination_is_followed_until_key_disappears`<br>`test_repeated_pagination_key_stops` |
| M29 | 呼び出しの間隔をあけない（5件/分を超える） | `cleanroom/jquants.py` | 落ちた | `test_calls_are_spaced_for_free_plan_limit` |
| M30 | 429・5xx で再試行しない | `cleanroom/jquants.py` | 落ちた | `test_retryable_errors_wait_then_succeed[429]`<br>`test_retryable_errors_wait_then_succeed[500]`<br>`test_retryable_errors_wait_then_succeed[503]`<br>`test_retryable_errors_wait_then_succeed[0]` |
| M31 | 例外の文に APIキーを入れる | `cleanroom/jquants.py` | 落ちた | `test_bad_request_raises_with_message_but_not_key` |
| M32 | float の価格を受け付ける | `cleanroom/jquants.py` | 落ちた | `test_to_bars_rejects_float` |
| M33 | ホールドアウトの日の記録を main に保存する | `cleanroom/fetch.py` | 落ちた | `test_fetch_days_separates_holdout_files_and_resumes`<br>`test_saved_files_on_wrong_side_of_holdout_are_an_error`<br>`test_build_store_locks_holdout_and_hashes_files`<br>`test_run_fetch_leaves_no_raw_holdout_outside_lock`<br>`test_run_fetch_after_lock_removes_leftover_raw_holdout` |
| M34 | 保存済みの日も取り直す | `cleanroom/fetch.py` | 落ちた | `test_fetch_days_separates_holdout_files_and_resumes`<br>`test_empty_day_is_an_error_and_is_not_saved` |
| M35 | ホールドアウトを5か月に縮める | `cleanroom/fetch.py` | 落ちた | `test_holdout_is_the_last_six_months` |
| M36 | 文字列の列の Null を 'nan' と書く | `cleanroom/split.py` | 落ちた | `test_flag_column_null_survives_round_trip` |
| M37 | 調整係数の正の値の検査を外す | `cleanroom/schema.py` | 落ちた | `test_bad_adj_factor_is_rejected[0]`<br>`test_bad_adj_factor_is_rejected[-0.5]`<br>`test_bad_adj_factor_is_rejected[NaN]`<br>`test_adj_factor_is_required` |
| M38 | 行が欠けた日をまたいでリターンをつなぐ（指摘1） | `cleanroom/returns.py` | 落ちた | `test_missing_ex_date_row_does_not_bridge_the_split`<br>`test_one_missing_row_breaks_only_that_code` |
| M39 | 空の応答の日を保存する（指摘1） | `cleanroom/fetch.py` | 落ちた | `test_empty_day_is_an_error_and_is_not_saved` |
| M40 | 記録の無い営業日があってもロックする（指摘1） | `cleanroom/fetch.py` | 落ちた | `test_build_store_refuses_missing_or_empty_day` |
| M41 | 空の記録のファイルがあってもロックする（指摘1） | `cleanroom/fetch.py` | 落ちた | `test_build_store_refuses_missing_or_empty_day` |
| M42 | 固定した計画を無視して毎回計算し直す（指摘3、Q6） | `cleanroom/fetch.py` | 落ちた | `test_plan_is_fixed_once_and_reused` |
| M43 | 保存済みファイルの側の照合を外す（指摘3） | `cleanroom/fetch.py` | 落ちた | `test_saved_files_on_wrong_side_of_holdout_are_an_error` |
| M44 | manifest のハッシュを中身と無関係にする（指摘4、Q4） | `cleanroom/fetch.py` | 落ちた | `test_build_store_locks_holdout_and_hashes_files` |
| M45 | ロックの外のホールドアウトの記録を消さない（指摘5） | `cleanroom/fetch.py` | 落ちた | `test_run_fetch_leaves_no_raw_holdout_outside_lock`<br>`test_run_fetch_after_lock_removes_leftover_raw_holdout` |
| M46 | ロック済みでも取得をやり直す（指摘5） | `cleanroom/fetch.py` | 落ちた | `test_run_fetch_does_not_refetch_after_lock`<br>`test_run_fetch_after_lock_removes_leftover_raw_holdout` |
| M47 | 同じ pagination_key が返り続けても止めない（指摘2） | `cleanroom/jquants.py` | 落ちた | `test_repeated_pagination_key_stops` |
| M48 | 同じ銘柄・同じ日の重複の検査を外す（推奨 a） | `cleanroom/returns.py` | 落ちた | `test_duplicate_row_for_same_code_and_day_is_an_error` |
| M49 | sessions の昇順の検査を外す（推奨 a） | `cleanroom/returns.py` | 落ちた | `test_bad_sessions_are_an_error[unsorted]` |
| M50 | sessions の重複の検査を外す（推奨 a） | `cleanroom/returns.py` | 落ちた | `test_bad_sessions_are_an_error[duplicated]` |
| M51 | ロック時の validate_bars を外す（推奨 b、Q7） | `cleanroom/split.py` | 落ちた | `test_lock_refuses_invalid_frame` |
| M52 | 開くときの検証を外す（推奨 b） | `cleanroom/split.py` | 落ちた | `test_invalid_holdout_is_refused_before_opening_is_used_up` |
| M53 | ロック済みのとき、残ったホールドアウトの記録を消さない（推奨 c） | `cleanroom/fetch.py` | 落ちた | `test_run_fetch_after_lock_removes_leftover_raw_holdout` |
| M54 | Asia/Tokyo 以外のタイムゾーンを通す | `cleanroom/schema.py` | 落ちた | `test_timezone_other_than_tokyo_is_rejected[UTC]`<br>`test_timezone_other_than_tokyo_is_rejected[America/New_York]` |

生き残った変異: 0 / 54

テストを書いている途中で、`test_holdout_rows_are_not_in_main_file` が書式違いで空振りしうることに気づいた。そこで「ホールドアウト直前の日付は書かれている」という確認を足して強くした。

「断言を消す」は、仕様書 §5 の例をこう読んだ: 実装の中の検査（`raise`）を消したとき、テストが落ちるか（M12、M14、M15）。テスト側の `assert` を消す変異は、この一覧に入っていない。

## 3. 実装係が把握している未実装・限界

- 取得コード（§7）は偽の通信でしかテストしていない。実際の API にはまだ送っていない（APIキーが無い）。
- `load_bars` は全期間を1つの表に読む。全銘柄2年分（数百万行の Decimal）では、メモリと時間が重い見込み。
- 調整の対象外の企業行為（公式: 現金配当、その他一部）は `AdjFactor` に出ないので検出できない。
- 営業日の一覧は銘柄 86970 の日付から作っている。Free の取引カレンダーとの突き合わせはまだしていない（取引カレンダーの API の仕様を、本人が公式ページから写すまで書かない）。
- 検査係1回目の推奨のうち、`mutate.py` の cp932 での文字化けは未対応（`PYTHONIOENCODING=utf-8` を付けて実行する）。`close_to_close_returns` の入力を `validate_bars` に通すことも未対応（Decimal NaN は InvalidOperation で止まる）。
- `lock_holdout_frames` が途中で止まると、`plan.json` の無い書きかけの `main/`・`holdout/` が残る。次のロックは FileExistsError で止まるので、黙って進みはしないが、手で消す必要がある。
- `GATES.md` の門 4〜12 の道具（DSR、PBO、SPA、StepM など）は未実装。閾値は空欄。
- `BUDGET.md` の上限は仮（取得期間の長さと目標シャープが未確定）。
- リポジトリ直下に、Mac から持ち込んだ `.Spotlight-V100/`、`.fseventsd/`、`._*` がある（`.gitignore` 済み、未削除）。

## 4. 検査係に渡すもの

`README.md`、`SPLIT.md`、`GATES.md`、`DATA.md`、`BUDGET.md`、`ledger.csv`、`cleanroom/`、`tests/`、`tools/mutate.py`、`pyproject.toml`、`uv.lock`、このファイルの §2（変異の一覧）。

貼る文は `docs/日本株機械学習.md` の `INSPECTOR_START` から `INSPECTOR_END` まで。実装係の思考の経過、「テストは通りました」という自己申告、APIキーは渡さない。

## 5. 検査係の判定表

### 1回目（2026-10-27、検査係: 「デイトレード検証システム構築」チャット）

本人が貼った判定を、そのまま写した。

| 項目 | 合格 / 不合格 | 証跡（実行したコマンドと、落ちたテスト名） |
|---|---|---|
| 1. 未来を混ぜた特徴量、全期間で適合した標準化、中央寄せの移動窓がテストで落ちるか | 合格 | uv run pytest -q -rA は 41 件すべて通過。悪い特徴量3つは test_lookahead_features_fail[future_return]、[full_period_standardize]、[centered_mean] で LookaheadError を期待しており、通過している。uv run python tools/mutate.py も再実行し、M01〜M03 は test_past_only_features_pass[past_return_1/5]、test_past_return_values、test_past_only_features_pass[trailing_zscore_20] で落ちた。自分で入れた P1（assert_no_lookahead から末尾切り詰めを外す）は test_lookahead_features_fail[future_return]、[centered_mean] で落ちた。P8（後ろ向き窓を expanding に変える）は test_past_only_features_pass[trailing_zscore_20] で落ちた |
| 2. 企業行為をまたぐ日のリターンが欠損になるか | 合格 | 手で入れた H1（REVIEW M04 と同じ壊し方で、if abs(raw_ret - adj_ret) <= tol: を if True: に）は test_return_across_split_is_missing で落ちた。P5（adj_ret = raw_ret にして調整済みを無視）も同じテストで落ちた。Null の日の繰り越しは M05 が test_null_day_has_no_return_and_is_not_carried で落ちることを確認した |
| 3. ホールドアウトを、通常の読み込みが返さないか | 合格 | 手で入れた H2（REVIEW M06 と同じ壊し方で、load_bars がホールドアウトのファイルも結合する）は test_normal_loader_does_not_return_holdout で落ちた。P3（lock_holdout の境界を > にし、開始日の行が main に入る）は test_normal_loader_does_not_return_holdout、test_holdout_rows_are_not_in_main_file、test_holdout_opens_once_with_confirmation で落ちた。M07〜M10 も mutate.py で落ちることを確認した |
| 4. REVIEW.md の変異を1つ自分で入れて、テストが落ちるか | 合格 | 作業用のコピー（scratchpad/inspect）にだけ、M04（H1）と M06（H2）を自分で入れた。どちらも上の名前のテストで落ちた。終了後、元のファイル 14 件を sha256sum -c で照合し、すべて変更なし。mutate.py の再実行結果は、生き残り 0 / 18、終了コード 0 |
| 5. 価格が Decimal で、時刻がタイムゾーン付きか | 合格 | test_float_price_is_rejected、test_single_float_price_is_rejected、test_naive_timestamp_is_rejected が通過。M14、M15 で落ちることを確認した。直接の入力では、float の nan と pd.NA は SchemaError で拒否された。_read は Decimal とタイムゾーンへの変換をしている |
| 指摘 | | (a) P2 が生き残った。 assert_no_lookahead の開始点ずらし（shift = start_shift_violations(...) を shift = [] に変える）を外しても、どのテストも落ちない（終了コード 0）。test_start_shift_catches_full_period_standardize は関数を直接呼んでいる。全期間の標準化は末尾の切り詰めでも捕まる。そのため、門2の関数から規則6の「開始点をずらす検査」を消しても検出されない。<br>(b) P4 が生き残った。 open_holdout のハッシュ照合（if _sha256(hold) != expected: を if False: に変える）を外しても、どのテストも落ちない。SPLIT.md の「ファイルがロック時から変わっていても拒否する」を守るテストがない。<br>(c) P7 が生き残った。 load_bars の混入検査を >= から > に変えても、どのテストも落ちない。test_loader_rejects_holdout_rows_placed_in_main は 50 行をまとめて混ぜるので、境界の日（ホールドアウト開始日の1行だけが main にある場合）を見ていない。<br>(d) validate_bars が Decimal("NaN")、Decimal("Infinity")、Decimal("0")、Decimal("-5") を通した。 docstring の「NaN や float は通さない」と食い違う。CSV に NaN と書かれていれば、_read はそれを Decimal NaN にする。下流の close_to_close_returns は InvalidOperation で止まるので、黙って通りはしない。それでも、規則11の Null を None 以外で表した値が検査を通る |
| 推奨（合否に含めない） | | ・validate_bars が UTC のタイムゾーンを通す。Asia/Tokyo に固定するなら、テストを足す。<br>・test_null_price_is_allowed、test_past_only_features_pass には assert 文がない。それぞれ P6（Null を拒否する）、M01〜M03 で落ちることを確認したので、空振りはしない。それでも、assert validate_bars(bars) is bars のように明示すると読みやすい。<br>・close_to_close_returns は「営業日ごとに1行ある」を前提にしているが、検査していない。行が丸ごと欠けた日をまたいでリターンを計算してしまう。<br>・tools/mutate.py の表は、cp932 のコンソールで文字化けする（判定には影響なし）。 |

### 2回目（2026-10-27、検査係: 「デイトレード検証システム構築」チャット）

検査係がこのセッションへ直接送った判定を、そのまま写した。本人の指示（「俺の手を煩わせないで」）により、中継は本人を通していない。

> 検査係（2回目）の判定表です。前回の指摘 (a)〜(d) は、すべて解消しました。直すべき点はありません。

| 項目 | 合格 / 不合格 | 証跡（実行したコマンドと、落ちたテスト名） |
|---|---|---|
| (a) P2：開始点ずらしを外すと落ちるか | 合格 | 作業用のコピー（scratchpad/inspect2）で `shift = []` に置き換え、pytest を実行した。`test_start_dependent_feature_fails` が落ちた。このテストは、末尾の切り詰めでは捕まらない（`truncation_violations(...) == []` を断言）特徴量が、`assert_no_lookahead` で落ちることを確かめている |
| (b) P4：ハッシュ照合を外すと落ちるか | 合格 | 同じコピーで `if _sha256(hold) != expected:` を `if False:` に置き換え、`test_holdout_changed_after_lock_is_refused` が落ちた。追加の Q4（照合を OPENED 作成の後に移す）でも、`test_holdout_opens_once_with_confirmation` と `test_holdout_changed_after_lock_is_refused` が落ちた |
| (c) P7：混入検査を `>` にすると落ちるか | 合格 | REVIEW §2 の M21 を自分の手で入れた（`>=` を `>` に）。`test_loader_rejects_holdout_start_day_alone` が落ちた。このテストは、ホールドアウト開始日の1行だけを main に混ぜている |
| (d) Decimal の NaN、無限大、0、負の値を通さないか | 合格 | 前回と同じ edge.py を実行した。`Decimal("NaN")`、`Decimal("Infinity")`、`Decimal("0")`、`Decimal("-5")`、float の nan、`pd.NA` は、すべて SchemaError で拒否された。弱めた変異は3つとも落ちた。Q1（`is_finite` を `is_nan` に）は `[Infinity]` の2件、Q2（`<= 0` を `< 0` に）は `test_non_finite_or_non_positive_price_is_rejected[0]`、Q3（有限の検査を価格列だけに）は `test_non_finite_or_negative_volume_is_rejected[NaN]` と `[Infinity]` で落ちた |
| 全体の再実行 | 合格 | `uv run pytest -q`：54 件通過。`uv run python tools/mutate.py`：生き残り 0 / 26、終了コード 0。終了後に、元のファイル（cleanroom/*.py、tests/*.py、tools/mutate.py）を `sha256sum -c` で照合し、すべて変更なし |
| 指摘 | なし | |
| 推奨（合否に含めない） | | ・`validate_bars` は UTC のタイムゾーンをまだ通す。Asia/Tokyo に固定するなら、テストを足す。<br>・`test_null_price_is_allowed`、`test_decimal_volume_is_allowed` は、本体の戻り値を断言していない。`assert validate_bars(bars) is bars` と明示すると読みやすい。<br>・`close_to_close_returns` は、入力を `validate_bars` に通していない。Decimal NaN が入ると InvalidOperation で止まるので、黙って通りはしない。<br>・`close_to_close_returns` は「営業日ごとに1行ある」を前提にしているが、検査していない |

## 6. 差し戻し1回目への対応（実装係）

| 指摘 | 足したテスト | 直したコード | そのテストを落とす変異 |
|---|---|---|---|
| (a) 開始点ずらしを外しても落ちない | `test_start_dependent_feature_fails`（末尾の切り詰めは通り、開始点のずらしでだけ捕まる特徴量 `s - s.expanding().mean()` が `assert_no_lookahead` で落ちる） | なし | M19 |
| (b) ハッシュ照合を外しても落ちない | `test_holdout_changed_after_lock_is_refused`（ロック後にホールドアウトの値を1つ書き換えると開けない。`OPENED` も作られない） | なし | M20 |
| (c) 混入検査を > にしても落ちない | `test_loader_rejects_holdout_start_day_alone`（ホールドアウト開始日の1行だけを通常のファイルに混ぜる） | なし | M21 |
| (d) Decimal の NaN、無限大、0、負の値が通る | `test_non_finite_or_non_positive_price_is_rejected`（6通り）、`test_non_finite_or_negative_volume_is_rejected`（3通り）、`test_loader_rejects_nan_written_in_file`（CSV に NaN と書かれた場合） | `cleanroom/schema.py` の `validate_bars`: 価格は有限かつ正、出来高は有限かつ0以上。docstring も合わせた | M22、M23、M24 |

(d) の新しいテストは、修正の前に実行して落ちることを確かめた（10 failed）。(a)〜(c) の新しいテストは、修正前のコードでも通る（コードは正しく、テストが欠けていた）。そのため、各指摘の変異で落ちることで確かめた（§2 の M19〜M21）。

## 7. 新しい回: 公式ページとの照合と、データ取得コード（実装係、2026-10-27）

本人が J-Quants の公式ページ5つの文言を写した。それに合わせて次を変えた。検査係の判定はまだ。

| 変更 | 理由 | テスト | 変異 |
|---|---|---|---|
| 企業行為の判定を、調整済みと調整前のリターンの比較から `AdjFactor` に変えた（`cleanroom/returns.py`、`tol` 引数を削除） | 公式: 調整済み値は小数第1位に丸められる。比較だと、企業行為のない日も丸めの分ずれる。公式は権利落ち日に `AdjFactor` を入れる | `test_return_across_split_is_missing`、`test_return_across_reverse_split_is_missing`、`test_rounded_adjusted_prices_do_not_drop_returns`、`test_missing_adj_factor_gives_no_return` | M04、M05 |
| `adj_factor` を必須の列にした（正の Decimal） | 上の判定に使う | `test_bad_adj_factor_is_rejected`、`test_adj_factor_is_required` | M37 |
| `lock_holdout` は `SplitPlan` ではなくホールドアウト開始日を受け取る。日ごとの表を順に書く `lock_holdout_frames` を足した。`plan.json` は開始日とハッシュだけ | ロックは取得の直後に行い、検証の開始日はまだ決めない。全銘柄2年分を一度にメモリに載せない | `test_lock_from_daily_frames_matches_single_frame` | M08、M25 |
| 文字列の列（`upper_limit` など）の Null を空欄で書き、`None` で読む | pandas 3 は文字列の列の `None` を NaN にし、`"nan"` と書いていた | `test_flag_column_null_survives_round_trip` | M36 |
| `cleanroom/jquants.py`（API クライアント、`to_bars`） | 公式の仕様: `x-api-key`、`pagination_key`、5件/分、400 は範囲外 | `tests/test_jquants.py`（15件） | M27〜M32 |
| `cleanroom/fetch.py`、`tools/fetch_daily.py`（取得の手順） | 末尾6か月を取得の前に固定し、ホールドアウトの日の記録を別のフォルダに保存する | `tests/test_fetch.py`（4件） | M33〜M35 |

新しいテストは実装の前に実行して、落ちることを確かめた（`10 failed, 41 passed, 3 errors`。3つの error は、まだ無い関数を import したことによる収集時のエラー）。

### 検査係の判定（新しい回の1回目、2026-10-27）

検査係がこのセッションへ直接送った判定を、そのまま写した。

> 検査係（J-Quants 照合・取得コード、新しい回の1回目）の判定表です。2項目が不合格（企業行為をまたぐ日、pagination_key）、直すべき点が5つあります。

| 項目 | 合格 / 不合格 | 証跡（実行したコマンドと、落ちたテスト名） |
|---|---|---|
| 照合: AdjFactor による判定 | 合格 | DATA.md の写しは「AdjFactor が1でない日（例: 1:2 の分割なら権利落ち日に 0.5）」。`close_to_close_returns` は、その行のリターンを None にしている。作業用のコピー（scratchpad/inspect3）で次を入れた。<br>・Q1（`factor == 1` を `>= 1` に）: `test_return_across_reverse_split_is_missing` で落ちた。<br>・Q2（`<= 1` に）: `test_return_across_split_is_missing` で落ちた。<br>丸めた調整済み値でリターンを落とさないことは、`test_rounded_adjusted_prices_do_not_drop_returns` が通過して確認した |
| 照合: Free の 5件/分 | 合格 | `FREE_MIN_INTERVAL = 13.0` で、ページ送りと再試行の呼び出しも同じ間隔になる。<br>・Q8（呼び出し時刻を記録しない）: `test_calls_are_spaced_for_free_plan_limit` で落ちた。<br>・Q3（429・5xx の後に待たない）: `test_retryable_errors_wait_then_succeed[429/500/503/0]` で落ちた |
| 照合: pagination_key | 不合格 | 応答側（「空か無くなるまで繰り返す」）は写しと一致した。手で入れた H2（REVIEW M28）は `test_pagination_is_followed_until_key_disappears` で落ちた。<br>一方、次の要求で pagination_key をクエリ引数として送ることは、DATA.md の写しに書かれていない。テストもこの前提を断言しているだけなので、照合は未確認。<br>同じキーが返り続けたときの止め方もない。probe3b.py で、同じキーを返す偽の通信に対して、50 回で打ち切るまで呼び続けた |
| 1. 先読みの検査（変わったコードで再確認） | 合格 | `uv run pytest -q`: 83 件通過。`uv run python tools/mutate.py`: 生き残り 0 / 37、終了コード 0（M01〜M03、M12、M13、M19、M26 を含む） |
| 2. 企業行為をまたぐ日のリターンが欠損になるか | 不合格 | probe3b.py の結果。権利落ち日（AdjFactor 0.5）の `date` 指定の応答が空の配列だった場合、次のようになった。<br>・`fetch_days` も `build_store` も例外を出さない。manifest にはその日が rows 0 で残る。<br>・`load_bars` → `close_to_close_returns` が、分割をまたぐ前日→翌日のリターン −0.4951… を出した（欠損であるべき）。<br>・再実行しても、その日は取り直さない（呼び出し 0 回）。<br>AdjFactor が行にあるときは欠損になる（H1、REVIEW M04 を手で入れ、`test_return_across_split_is_missing` と `test_return_across_reverse_split_is_missing` で落ちた） |
| 3. ホールドアウトを、通常の読み込みが返さないか | 合格 | M06、M07、M08、M21、M25、M33 は mutate.py で落ちた。`test_build_store_locks_holdout` は通過 |
| 4. REVIEW §2 の変異を1つ自分で入れて、テストが落ちるか | 合格 | 作業用のコピーで M04（H1）と M28（H2）を手で入れ、上のテストで落ちた。元のファイル（cleanroom/、tests/、tools/）は、`sha256sum -c` ですべて変更なし |
| 5. 価格が Decimal で、時刻がタイムゾーン付きか | 合格 | M27（float で読む）、M32（float を受け付ける）、M22〜M24、M37 は mutate.py で落ちた。`test_to_bars_maps_official_fields` は、ts が Asia/Tokyo であることを断言している |
| APIキーと実際の API | 合格 | キーはヘッダだけで送り、URL・repr・例外の文に入らない（M31 で落ちた）。テストの通信はすべて偽物で、tests/ に実通信はない。`.env` と `data/` は存在しない。`.env` は .gitignore に入っている |
| 指摘 | | **(1) 取得した日の行が空でも通る。** `fetch_days` と `build_store` は、営業日の応答が空の配列でも、エラーにも取り直しにもしない。`close_to_close_returns` は「営業日ごとに1行」の前提を検査しない。その結果、権利落ち日の行が欠けると、分割をまたぐリターン（−49.5%）が欠損にならない。ある日に1銘柄だけ行が欠けた場合も、同じ形になる。<br>**(2) pagination_key の送り方が未確認。** 本人が公式ページの該当する文言を DATA.md に写すまで、照合は未確認。<br>**(3) 生き残った変異 Q6。** `tools/fetch_daily.py` で、固定した計画（fetch_plan.json）を無視して毎回計算し直すように変えても（`if plan_path.exists():` を `if False:` に）、どのテストも落ちない。中断した後の再実行で、ホールドアウトの開始日が後ろにずれうる。そのとき、以前に holdout として保存した日が main に入る（規則4）。<br>**(4) 生き残った変異 Q4。** manifest の sha256 を、中身と無関係な値に変えても落ちない。テストが長さ64しか見ていない（規則25）。<br>**(5) 生のホールドアウトがロックの外にある。** `data/raw/holdout/*.json` に、ホールドアウトの記録がロックの外で平文のまま残る。`open_holdout` の「1回だけ開く」が、普通のファイル読み込みで迂回できる（規則4） |
| 推奨（合否に含めない） | | ・Q7: `lock_holdout_frames` の `validate_bars` を外しても落ちない。`open_holdout` は OPENED を書いた後に検証するので、不正な行があると1回きりの開封が消費される。<br>・`ts` は「その営業日の 0:00 JST」で、終値が確定した時刻ではない。その意味を docstring と DATA.md に書く。<br>・営業日の一覧は、銘柄 86970 の日付から作っている。Free に含まれる取引カレンダーとの突き合わせを足す。<br>・保存は「取ったままの記録」ではなく、数値を文字列にした JSON。そのため、ハッシュは API の生の応答のハッシュではない。そう明記する |

## 8. 新しい回の差し戻し1回目への対応（実装係、2026-10-27）

| 指摘 | 足したテスト | 直したコード | そのテストを落とす変異 |
|---|---|---|---|
| (1) 取得した日の行が空でも通る | `test_empty_day_is_an_error_and_is_not_saved`、`test_build_store_refuses_missing_or_empty_day`、`test_missing_ex_date_row_does_not_bridge_the_split`（権利落ち日の行が無い）、`test_one_missing_row_breaks_only_that_code`（1銘柄だけ行が無い）、`test_date_outside_calendar_is_an_error` | `fetch_days`: 応答が空の営業日は保存せずに止める。`build_store`: 営業日の一覧のどの日にも空でない記録のファイルがあることを確かめてからロックする。`close_to_close_returns(df, sessions)`: 営業日の一覧を受け取り、前の行が直前の営業日でなければ欠損にする。一覧にない日付は ValueError | M38、M39、M40、M41 |
| (2) pagination_key の送り方が未確認 | `test_repeated_pagination_key_stops` | 本人が写した日足の仕様（クエリパラメータの欄）とデータの FAQ の文言を、DATA.md に引用した。どちらも「クエリパラメータ」と書いている。同じキーが繰り返し返ったら `JQuantsError` で止める（実装の判断で、公式の記述ではないと DATA.md に明記） | M47 |
| (3) Q6: 固定した計画を無視しても落ちない | `test_plan_is_fixed_once_and_reused`（2回目は API を呼ばず、ファイルの開始日を使う）、`test_saved_files_on_wrong_side_of_holdout_are_an_error` | `fetch_days` の最初に、保存済みのファイルが固定した開始日と食い違う側にあれば止める | M42、M43 |
| (4) Q4: manifest のハッシュが中身と無関係でも落ちない | `test_build_store_locks_holdout_and_hashes_files`（各ファイルの中身を `hashlib.sha256` で計算し直して照合する） | なし | M44 |
| (5) 生のホールドアウトがロックの外にある | `test_run_fetch_leaves_no_raw_holdout_outside_lock`、`test_run_fetch_does_not_refetch_after_lock` | `run_fetch`: ロックした後、`data/raw/holdout/*.json` を消す（ハッシュは manifest に残る）。ロック済みなら何も取らずに止める | M45、M46 |

新しいテストは、修正の前に実行して落ちることを確かめた（`10 failed, 73 passed, 1 error`。1つの error は、まだ無い関数を import したことによる収集時のエラー）。

推奨への対応:

- 保存は API の生の応答ではなく、数値を文字列にした JSON で、ハッシュはその JSON のもの: DATA.md の取得の手順 4 に明記した。
- 取引カレンダーとの突き合わせ: まだしていない。DATA.md の取得の手順 1 に「まだしていない」と書いた。
- Q7（`lock_holdout_frames` の `validate_bars`、`open_holdout` の検証の順番）: 未対応。
- `ts` の意味（その営業日の 0:00 JST で、終値が確定した時刻ではない）: 未対応。

### 検査係の判定（新しい回の2回目、2026-10-27）

検査係がこのセッションへ直接送った判定を、そのまま写した。

| 項目 | 合格 / 不合格 | 証跡（実行したコマンドと、落ちたテスト名） |
|---|---|---|
| 前回指摘1 空の日・行の欠け | 合格 | `uv run pytest -q` 93 passed。scratchpad の写しに自分で変異を入れた: `prev_pos.get(code) == here - 1` を `code in prev_pos` に → test_missing_ex_date_row_does_not_bridge_the_split, test_one_missing_row_breaks_only_that_code が落ちた。fetch_days の `if not records:` を `if False:` に → test_empty_day_is_an_error_and_is_not_saved。build_store の `if missing:` を外す → test_build_store_refuses_missing_or_empty_day。空ファイル検査を外す → 同。自作の確認: 3日目が空の応答 → FetchError で止まり、前の2日だけ保存。build_store は欠けた日を挙げて拒否。権利落ち日の行が無い銘柄のリターン → [None, 0.01, None]（前回の −0.4951 は出ない） |
| 前回指摘2 pagination_key | 合格 | DATA.md 28行に、日足のクエリパラメータの欄と FAQ の引用あり。「同じキーで止める」は実装の判断と明記。`if next_key in seen:` を `if False:` に → test_repeated_pagination_key_stops が落ちた（呼び出し2回で止まることを断言） |
| 前回指摘3 計画の固定（Q6） | 合格 | load_or_fix_plan の `if plan_path.exists():` を `if False:` に → test_plan_is_fixed_once_and_reused。`_check_saved_sides` の呼び出しを外す → test_saved_files_on_wrong_side_of_holdout_are_an_error |
| 前回指摘4 manifest のハッシュ（Q4） | 合格 | `hashlib.sha256(data)` を `hashlib.sha256(b"")` に → test_build_store_locks_holdout_and_hashes_files（中身のハッシュと一致を断言） |
| 前回指摘5 ロックの外のホールドアウト | 合格 | run_fetch の `f.unlink()` を `pass` に → test_run_fetch_leaves_no_raw_holdout_outside_lock。ロック済みの検査を外す → test_run_fetch_does_not_refetch_after_lock |
| 1. 未来の特徴量・全期間標準化・中央寄せ窓 | 合格 | `PYTHONIOENCODING=utf-8 uv run python tools/mutate.py` 生き残り 0 / 47。M19 → test_start_dependent_feature_fails、M26 → test_lookahead_features_fail[future_return], [centered_mean] |
| 2. 企業行為をまたぐ日のリターンが欠損 | 合格 | 上の指摘1の行と同じ。M38 も落ちた |
| 3. ホールドアウトを通常の読み込みが返さない | 合格 | M21 → test_loader_rejects_holdout_start_day_alone、M25 → test_normal_loader_does_not_return_holdout ほか |
| 4. REVIEW.md §2 の変異を自分で入れる | 合格 | M38, M39, M40, M45, M47 を自分で入れた（上記）。すべて落ちた。元のファイルは `sha256sum -c`（154 ファイル）で変更なしを確認。data/ は無い。実 API には送っていない |
| 5. 価格が Decimal、時刻がタイムゾーン付き | 合格 | M27 → test_numbers_are_parsed_as_decimal_not_float、M32 → test_to_bars_rejects_float、M15 → test_float_price_is_rejected |

| 指摘 | 直すべき点だけ。推奨は分ける |
|---|---|
| 直すべき点 | なし |
| 推奨（合否に含めない） | (a) returns.py の同じ銘柄・同じ日の重複の検査（`if code in prev_pos and here <= prev_pos[code]:` を外す）と、sessions の昇順の検査を外しても、どのテストも落ちない。(b) Q7: lock_holdout_frames の validate_bars を外してもテストは落ちない（前回からの持ち越し）。open_holdout は検査の前に OPENED を書く。(c) build_store の後、raw/holdout を消す前に落ちると、ロックの外にホールドアウトの記録が残る。次の実行は plan.json があるので止まるが、消されない。(d) 営業日カレンダーとの照合、ts を日付の 0 時とする意味は未確認のまま |

結論: 未検証（実データでは何も確かめていない）。

## 9. 新しい回の2回目の推奨への対応（実装係、2026-10-28）

本人の指示（「推奨」）で、§8 末尾の推奨 (a)〜(d) と、検査係1回目・2回目の推奨の残りに対応した。検査係の判定はまだ。

| 推奨 | 足したテスト | 直したコード | そのテストを落とす変異 |
|---|---|---|---|
| (a) returns.py の重複の検査と、sessions の昇順の検査を外しても落ちない | `test_duplicate_row_for_same_code_and_day_is_an_error`、`test_bad_sessions_are_an_error[unsorted]`、`[duplicated]`（行の側の順番は正しく、sessions の検査でだけ止まる） | なし | M48、M49、M50 |
| (b) Q7: lock_holdout_frames の validate_bars を外しても落ちない。open_holdout は検証の前に OPENED を書く | `test_lock_refuses_invalid_frame`、`test_invalid_holdout_is_refused_before_opening_is_used_up`（ハッシュを合わせた不正なホールドアウトで、SchemaError になり OPENED が作られない） | `open_holdout`: 読んで `validate_bars` を通してから OPENED を書く | M51、M52 |
| (c) ロックの後、raw/holdout を消す前に落ちると、ロックの外に記録が残る | `test_run_fetch_after_lock_removes_leftover_raw_holdout` | `run_fetch`: ロック済みのとき、raw/holdout の残りを消してから止める（API は呼ばない） | M53（M45、M46 も、このテストで落ちる） |
| (d) ts を日付の 0 時とする意味 | なし（文書） | `cleanroom/schema.py`・`cleanroom/jquants.py` の docstring と DATA.md の「取得の決まり」に書いた: ts は日付を表すだけで、終値が確定した時刻でも利用可能になった時刻でもない。時点は営業日の順で決める | なし |
| (d) 営業日カレンダーとの照合 | なし | **未対応。** 取引カレンダーの API の仕様（エンドポイント、項目名、休業日の区分）を、本人が公式ページから写すまで書かない | なし |
| 1回目・2回目: validate_bars が UTC を通す | `test_timezone_other_than_tokyo_is_rejected[UTC]`、`[America/New_York]` | `validate_bars`: ts は Asia/Tokyo だけ（タイムゾーンなしの検査と1行にまとめた） | M54、M14 |
| 2回目: 2つのテストが戻り値を断言していない | `test_null_price_is_allowed`、`test_decimal_volume_is_allowed` に `assert validate_bars(bars) is bars` | なし | なし |

修正の前に新しいテストを実行し、`5 failed, 96 passed` を確かめた（そのうち1件はテストの書き方の誤りで、index の重複のせいだった。直した）。(a) の sessions と (b) のロックのテストは、修正前のコードでも通る（コードは正しく、テストが欠けていた）。そのため、変異で落ちることで確かめた。

変異の1回目の実行では、2つが生き残った。M14 は、新しい Asia/Tokyo の検査がタイムゾーンなしの時刻も捕まえていた。そのため、元の検査を外しても落ちなかった。2つの検査を1行にまとめて解消した。M49 は、並びの乱れたテストが重複の検査で止まり、昇順の検査を見ていなかった。テストを、行の側の順番が正しい形に変えて解消した。

取り直した結果: `uv run pytest -q` は 101 件通過。`PYTHONIOENCODING=utf-8 uv run python tools/mutate.py` は生き残り 0 / 54、終了コード 0。

結論: 未検証（実データでは何も確かめていない）。
