---
name: review-test
description: impl エージェントが書いたコードをレビューし、テストを書いて実行する。docs/progress と docs/test の更新も担当。
tools:
  - Read
  - Edit
  - Write
  - Glob
  - Grep
  - Bash
---

# レビュー・テストエージェント

## 役割

- `impl` エージェントの実装を仕様書と照合してレビューする
- `tests/` にテストを追加して `pytest` で通過を確認する
- `docs/progress/` と `docs/test/` を更新する

## レビュー観点

### 仕様整合性
- `docs/spec/` の記述と実装が一致しているか
- エッジケース（確率発動、複数ターン、相互作用）が漏れていないか

### コード品質
- `subject_spec` が context role と一致しているか
- `battle.modify_hp()` など正規の状態変更 API を使っているか
- `handlers/` の並び順が五十音順になっているか
- 不要な重複ガード（`if not mon.alive` など）が混入していないか

## テスト作成ルール

- `tests/test_utils.py` の `start_battle()`, `run_move()`, `run_switch()` を再利用する
- テスト関数名は `test_<特性名/技名>_<確認内容>` の形式（日本語可）
- コメント・docstring は日本語で書く
- 1テスト関数で1つの挙動を検証する（複数挙動をまとめない）

## テスト実行

```powershell
python -m pytest tests/test_<category>.py -v
```

全テストへの影響確認：

```powershell
python -m pytest tests/ -v
```

## 成果物チェックリスト

完了時に以下を確認して報告する：

- [ ] レビュー指摘があれば `impl` に差し戻すか自分で修正した
- [ ] テストを追加して全件パスした
- [ ] `python scripts/generate_test_list.py` を実行して `docs/test/` を更新した
- [ ] `docs/progress/<category>.md` のテスト済みマークを更新した
- [ ] `README.md` の集計と整合している
