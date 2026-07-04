# リーサル計算ハンドラ 実装ループ 指示書

**作業ディレクトリ**: `c:\Users\tmtmp\Documents\pokemon\jpoke`

---

## フロー概要

`impl.md` を簡略化したシングルエージェント実装ループ。
計画書・worktree なし。進捗ファイルのリーサル列を読んで実装対象を決定し、
1件ずつ実装・テスト・進捗更新・コミットを完遂する。

---

## 状態ファイルのスキーマ

```json
{
  "config": {
    "category":       "リーサル計算ハンドラ",
    "spec_hint":      "docs/spec/ 以下の仕様書を参照",
    "test_files":     ["tests/test_lethal.py"],
    "progress_files": ["docs/progress/item.md", "docs/progress/ability.md", "..."]
  },
  "completed": [{"name": "...", "type": "item|ability|ailment|volatile|global_field|move"}],
  "failed":    [{"name": "...", "type": "..."}]
}
```

---

## ウェイクアップ手順

### 1. 状態ファイルを読む

`.loop/lethal_state.json` を Read で読み込む。

### 2. 次の実装対象を決定する

`config.progress_files` を順に Read して走査する。
「リーサル実装 = `-`」かつ「実装 = `x`」の行を探す（`n/a`・`保留`・`x` はスキップ）。
`completed` と `failed` に含まれる名前もスキップ。

- 対象が見つからなければ → 「リーサルハンドラ 全件完了」と報告してループ終了（ScheduleWakeup を呼ばない）
- 対象が見つかった場合 → その名前・ファイル種別・効果列の説明を記録する

### 3. 実装（foreground）

**impl エージェント（foreground）** に以下のプロンプトで起動する:

```
jpoke リーサル計算ハンドラ実装タスク: {name}（{type}）

作業ディレクトリ: c:\Users\tmtmp\Documents\pokemon\jpoke

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
9. 変更をすべてコミットする:
   git add src/ tests/ docs/
   git commit -m "impl: lethal/{name}"

{config.spec_hint}
```

### 4. 進捗ファイルを更新する

実装・テストが成功した場合のみ実施する。

対象行の「リーサル実装」と「リーサルテスト」列を `-` → `x` に更新する。
（対応する progress_file を Edit ツールで直接修正する）

### 5. 状態ファイルを保存

成功した場合: `completed` に `{"name": "{name}", "type": "{type}"}` を追加。
失敗した場合: `failed` に追加。

Write ツールで `.loop/lethal_state.json` を上書き。

### 6. 次のウェイクアップを予約

```
ScheduleWakeup(delaySeconds=120, prompt="<<autonomous-loop-dynamic>>",
               reason="リーサルハンドラ 実装ループ: 次の件へ")
```

---

## エラーハンドリング

- 実装失敗 → `failed` に追加してループ継続
- 同じ件が `failed` に 2 回以上 → スキップして次へ
