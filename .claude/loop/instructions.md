# ループ ディスパッチャー

フローに対応する状態ファイルを Read したあと、指示書を Read して内容に従う。

| フロー | 状態ファイル | 指示書 |
|---|---|---|
| impl | `.loop/impl_state.json` | `.claude/loop/impl.md` |
| review | `.loop/review_state.json` | `.claude/loop/review.md` |
| todo | `.loop/todo_state.json` | `.claude/loop/todo.md` |
| lethal | `.loop/lethal_state.json` | `.claude/loop/lethal.md` |
| fuzz | `.loop/fuzz_state.json` | `.claude/loop/fuzz.md` |
| tsfuzz | `.loop/tsfuzz_state.json` | `.claude/loop/tsfuzz.md` |

フローの指定がない場合は `impl` とみなす。
