# ループ ディスパッチャー

1. **まず `.claude/loop/_common.md`（全フロー共通規約）を Read する。**
2. フローに対応する状態ファイルを Read する。
3. フローの指示書を Read し、`_common.md` の §共通N 参照を解決しながら内容に従う。

| フロー | 方式 | 状態ファイル | 指示書 |
|---|---|---|---|
| impl | 統合ブランチ | `.loop/impl_state.json` | `.claude/loop/impl.md` |
| review | 統合ブランチ | `.loop/review_state.json` | `.claude/loop/review.md` |
| todo | 単一ブランチ | `.loop/todo_state.json` | `.claude/loop/todo.md` |
| impl_lethal | 単一ブランチ | `.loop/impl_lethal_state.json` | `.claude/loop/impl_lethal.md`（バックログ消化用・移行期。新規は impl が担当） |
| fuzz | 単一ブランチ | `.loop/fuzz_state.json` | `.claude/loop/fuzz.md`（random / tree_search を `active_mode` で切替） |
| replay_fuzz | 単一ブランチ | `.loop/replay_fuzz_state.json` | `.claude/loop/replay_fuzz.md`（リプレイ再現の一致検証） |
| fuzz_log | 単一ブランチ | `.loop/fuzz_log_state.json` | `.claude/loop/fuzz_log.md`（イベントログの整合性をsub agentにレビューさせる。道中クラッシュも即座に自動修正） |
| flaky | 単一ブランチ | `.loop/flaky_state.json` | `.claude/loop/flaky.md`（全テストの反復実行によるflaky test検出・修正） |
| api | 単一ブランチ | `.loop/api_state.json` | `.claude/loop/api.md`（開発者/初心者/AI開発者の3エージェントによるAPI・examplesレビューと改善の自律ループ） |

フローの指定がない場合は `impl` とみなす。
