# リーサル計算ハンドラ 実装ループ 指示書

**前提**: `_common.md` を読んでいること（`{flow}` = `lethal`、方式は単一ブランチ）。
**実装作業ディレクトリ**: `{config.worktree}`（永続 worktree、ブランチ `loop/lethal`）。

> **位置づけ（移行期・削除予定）**: リーサルの新規実装は `impl` フローが担当するようになった
> （impl.md 手順3・新規 entry は `-` を残さない）。この lethal フローは、それ以前に実装された
> **`リーサル実装 = -` のバックログを総ざらいで消化するための一時的な後追いフロー**。
> バックログを消化しきったら（下記コマンドで `-` が 0 件になったら）このフローと状態ファイルは削除してよい。
> 残バックログ確認: `awk -F'\t' 'NR>1 && $6=="-"' docs/progress/*.md`

`impl.md` を簡略化したシングルエージェント実装ループ（計画書なし）。進捗ファイルのリーサル列を
読んで実装対象を決定し、`loop/lethal` 上で 1 件ずつ実装・テスト・進捗更新・コミットを行う。

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

### 1.5. worktree を準備する

§共通4 パターンA を適用する（`{config.worktree}`・ブランチ `loop/lethal`）。

### 2. 次の実装対象を決定する

`config.progress_files`（`{config.worktree}` 配下のパスとして解決）を順に Read して走査する。
「リーサル実装 = `-`」かつ「実装 = `x`」の行を探す（`n/a`・`保留`・`x` はスキップ）。
`completed` と `failed` に含まれる名前もスキップ。

- 対象が見つからなければ → 「リーサルハンドラ 全件完了」と報告してループ終了。
- 見つかった場合 → その名前・ファイル種別・効果列の説明を記録する。

### 3. 実装（impl エージェント、foreground）

```
jpoke リーサル計算ハンドラ実装タスク: {name}（{type}）

作業ディレクトリ: {config.worktree}

効果: {効果列の説明}

手順:
1. docs/spec/ に仕様書があれば読む。なければ現状の実装（handlers/lethal.py・core/lethal.py）を調査する
2. handlers/lethal.py の既存パターン（_heal, _heal_at_pinch など）を参照してハンドラ関数を実装する
   - シグネチャ: (battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist
3. type に対応する data ファイルの lethal_handlers にエントリを追加する
   - item → data/item.py, ability → data/ability.py, ailment → data/ailment.py,
     volatile → data/volatile.py, global_field → data/field.py, move → data/move.py
   - イベントは LethalEvent.ON_BEFORE_HIT / ON_HIT / ON_TURN_END / ON_EVERY_EVENT から選ぶ
   - subject は "attacker" / "defender" / None から選ぶ
4. ソートを実行する:
   python scripts/sort_handlers.py src/jpoke/handlers/lethal.py
   （data ファイルを変更した場合は scripts/sort_data/sort_abilities.py / sort_items.py / sort_moves.py も実行）
5. tests/test_lethal.py にテストを追加する（t.calc_lethal を使用）
6. python scripts/sort_tests.py tests/test_lethal.py を実行する
7. python scripts/generate_test_list.py を実行する
8. python -m pytest tests/ -v を実行し全テストが通ることを確認する
9. 変更をすべてコミットする（作業は `loop/lethal` ブランチ上で行う）:
   git add src/ tests/ docs/
   git commit -m "impl: lethal/{name}"

{config.spec_hint}
```

> 注: このフローは単一ブランチ・単一エージェントのため、ソートはエージェント側で実行する
> （統合ブランチ方式の §共通5「マージ後一括整形」は適用しない）。

### 4. 進捗ファイルを更新する

実装・テストが成功した場合のみ。対象行の「リーサル実装」「リーサルテスト」列を `-` → `x` に更新し、
worktree 内でコミットする:

```bash
# {config.worktree} 配下の progress_file を Edit で修正後:
git -C "{config.worktree}" commit -am "docs: lethal/{name} progress"
```

### 5. 状態保存・次ウェイクアップ

成功: `completed` に `{"name": "{name}", "type": "{type}"}` を追加。失敗: `failed` に追加。
§共通7 に従う（保存後 `delaySeconds=120` で予約。reason「リーサルハンドラ 実装ループ: 次の件へ」）。

---

## main への反映

§共通6 を適用する（`{branch}` = `loop/lethal`）。

## エラーハンドリング

§共通8 に従う（実装失敗 → `failed` に追加してループ継続）。
