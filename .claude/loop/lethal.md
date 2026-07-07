# リーサル計算ハンドラ 実装ループ 指示書

**ディスパッチャー作業ディレクトリ**: `c:\Users\tmtmp\Documents\pokemon\jpoke`
（Claude セッションの CWD。状態ファイル `.loop/` の読み書きと worktree 起動のみ。
**`jpoke/` の作業ツリーには一切コミット・マージしない**）
**実装作業ディレクトリ**: `{config.worktree}`（永続 worktree、ブランチ `loop/lethal`）

---

## フロー概要

`impl.md` を簡略化したシングルエージェント実装ループ。計画書なし。
進捗ファイルのリーサル列を読んで実装対象を決定し、永続 worktree 上のブランチ `loop/lethal` で
1件ずつ実装・テスト・進捗更新・コミットを行う。

> **統合ブランチ方式**: 成果は `loop/lethal` に蓄積し、**main へは自動マージしない**。
> ユーザーの `jpoke/`(main) には一切触れないため、ループ稼働中でも待ち・競合が発生しない。
> 完了分を main に取り込むのはユーザーが任意のタイミングで行う（末尾「main への反映」）。
> `.loop/` は git 管理外のローカルスクラッチ（`.gitignore` 済み・コミット不要）。

---

## 状態ファイルのスキーマ

```json
{
  "config": {
    "category":       "リーサル計算ハンドラ",
    "spec_hint":      "docs/spec/ 以下の仕様書を参照",
    "test_files":     ["tests/test_lethal.py"],
    "progress_files": ["docs/progress/item.md", "docs/progress/ability.md", "..."],
    "worktree":       "C:\\Users\\tmtmp\\Documents\\pokemon\\jpoke-loop\\lethal"
  },
  "completed": [{"name": "...", "type": "item|ability|ailment|volatile|global_field|move"}],
  "failed":    [{"name": "...", "type": "..."}]
}
```

---

## ウェイクアップ手順

### 1. 状態ファイルを読む

`.loop/lethal_state.json` を Read で読み込む。

### 1.5. worktree を準備する（冪等）

（ディスパッチャー作業ディレクトリ jpoke/ で実行）

`{config.worktree}` が存在しなければ作成する:
```bash
git worktree add -b loop/lethal "{config.worktree}" main
```
既に存在する場合は main の最新変更を取り込む:
```bash
git -C "{config.worktree}" checkout loop/lethal
git -C "{config.worktree}" merge main
```

### 2. 次の実装対象を決定する

`config.progress_files`（`{config.worktree}` 配下のパスとして解決する）を順に Read して走査する。
「リーサル実装 = `-`」かつ「実装 = `x`」の行を探す（`n/a`・`保留`・`x` はスキップ）。
`completed` と `failed` に含まれる名前もスキップ。

- 対象が見つからなければ → 「リーサルハンドラ 全件完了」と報告してループ終了（ScheduleWakeup を呼ばない）
- 対象が見つかった場合 → その名前・ファイル種別・効果列の説明を記録する

### 3. 実装（foreground）

**impl エージェント（foreground）** に以下のプロンプトで起動する:

```
jpoke リーサル計算ハンドラ実装タスク: {name}（{type}）

作業ディレクトリ: {config.worktree}

効果: {効果列の説明}

手順:
1. docs/spec/ に仕様書があれば読む。なければ現状の実装（handlers/lethal.py・core/lethal.py）を調査する
2. handlers/lethal.py の既存パターン（_heal, _heal_at_pinch など）を参照してハンドラ関数を実装する
   - シグネチャ: (battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist
3. type に対応する data ファイルの lethal_handlers にエントリを追加する
   - item      → data/item.py
   - ability   → data/ability.py
   - ailment   → data/ailment.py
   - volatile  → data/volatile.py
   - global_field → data/field.py
   - move      → data/move.py
   - イベントは LethalEvent.ON_BEFORE_HIT / ON_HIT / ON_TURN_END / ON_EVERY_EVENT から選ぶ
   - subject は "attacker" / "defender" / None から選ぶ
4. ソートを実行する:
   python scripts/sort_handlers.py src/jpoke/handlers/lethal.py
   （data ファイルを変更した場合は scripts/sort_data/sort_abilities.py / scripts/sort_data/sort_items.py / scripts/sort_data/sort_moves.py も実行）
5. tests/test_lethal.py にテストを追加する（t.calc_lethal を使用）
6. python scripts/sort_tests.py tests/test_lethal.py を実行する
7. python scripts/generate_test_list.py を実行する
8. python -m pytest tests/ -v を実行し全テストが通ることを確認する
9. 変更をすべてコミットする（作業は `loop/lethal` ブランチ上で行う）:
   git add src/ tests/ docs/
   git commit -m "impl: lethal/{name}"

{config.spec_hint}
```

### 4. 進捗ファイルを更新する

実装・テストが成功した場合のみ実施する。

対象行の「リーサル実装」と「リーサルテスト」列を `-` → `x` に更新する。
（`{config.worktree}` 配下の対応する progress_file を Edit ツールで直接修正し、
worktree 内でコミットする: `git -C "{config.worktree}" commit -am "docs: lethal/{name} progress"`）

> **main へのマージは行わない**。コミットは `loop/lethal` に積むだけでよい。

### 5. 状態ファイルを保存

成功した場合: `completed` に `{"name": "{name}", "type": "{type}"}` を追加。
失敗した場合: `failed` に追加。

Write ツールで `.loop/lethal_state.json` を上書きする。**`.loop/` は git 管理外なのでコミット不要**。

### 6. 次のウェイクアップを予約

```
ScheduleWakeup(delaySeconds=120, prompt="<<autonomous-loop-dynamic>>",
               reason="リーサルハンドラ 実装ループ: 次の件へ")
```

---

## main への反映（ユーザーが任意のタイミングで実行）

```bash
# jpoke/ で:
git switch main
git merge --ff-only loop/lethal
# FF 不可のときのみ:
git merge --no-ff loop/lethal -m "Merge loop/lethal"
```

---

## エラーハンドリング

- 実装失敗 → `failed` に追加してループ継続
- 同じ件が `failed` に 2 回以上 → スキップして次へ
