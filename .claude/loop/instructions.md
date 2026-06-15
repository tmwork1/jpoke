# ループ ディスパッチャー

`.loop/state.json` を Read したあと、プロンプトで指定されたフローの指示書を Read して内容に従う。

- impl フロー → `.claude/loop/impl.md`
- review フロー → `.claude/loop/review.md`

フローの指定がない場合は `impl` とみなす。
