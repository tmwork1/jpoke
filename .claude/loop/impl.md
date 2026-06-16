# 大量実装 自律ループ 指示書

**作業ディレクトリ**: `c:\Users\tmtmp\Documents\pokemon\jpoke`

---

## 状態ファイルのスキーマ

```json
{
  "config": {
    "category":           "変化技",
    "plan_dir":           "docs/plan/moves",
    "spec_hint":          "docs/spec/ を参照",
    "progress_file":      "docs/progress/move.md",
    "test_files":         ["tests/test_move.py"],
    "impl_extra":         "",
    "review_extra":       "",
    "planning_slots_max": 2
  },
  "plan_queue":  ["..."],
  "impl_queue":  ["..."],
  "completed":   ["..."],
  "failed":      ["..."]
}
```

---

## ウェイクアップ手順

### 1. 状態ファイルを読む

`.loop/impl_state.json` を Read で読み込む。

### 2. 終了チェック

`plan_queue` と `impl_queue` が両方空なら
→「{config.category} 全件完了: {completed}」と報告してループ終了（ScheduleWakeup を呼ばない）。

### 3. 収穫（Harvest）

`plan_queue` を先頭から走査し、`{config.plan_dir}/{entry}.md` が存在するエントリを
`impl_queue` 末尾に移して `plan_queue` から除く。

### 4. 実装

`impl_queue` が空でなければ先頭エントリを取り出す（→ `entry`）。

**impl エージェント（foreground）**

```
jpoke {config.category} 実装タスク: {entry}

作業ディレクトリ: c:\Users\tmtmp\Documents\pokemon\jpoke

計画書: {config.plan_dir}/{entry}.md

手順:
1. 計画書を読み込む（CLAUDE.md の実装時参照順に従い関連ファイルも確認）
2. CLAUDE.md のハンドラ約束事に従い、handlers/ と data/ に実装する
3. テストは書かない（review-test エージェントが担当）
{config.impl_extra}
- 実装完了後: {config.progress_file} の {entry} 行の実装列を `x` に更新する
```

失敗した場合: `failed` に追加して次のステップへ（review-test はスキップ）。

**review-test エージェント（foreground）**

impl 成功後のみ実行：

```
jpoke {config.category} レビュー・テストタスク: {entry}

作業ディレクトリ: c:\Users\tmtmp\Documents\pokemon\jpoke

{entry} の実装が完了した。以下を順に実施すること:
1. handlers/ と data/ の実装をレビュー、問題があれば修正
2. {config.test_files} にテストを追加
3. python scripts/sort_tests.py {config.test_files をスペース区切り} でソート
4. python scripts/generate_test_list.py でテスト一覧更新
5. python -m pytest tests/ -v で全テストが通ることを確認
6. {config.progress_file} の {entry} 行を ✓ に更新
{config.review_extra}
```

成功: `completed` に追加。失敗: `failed` に追加。

### 5. 種まき（Sow）

`plan_queue` の先頭から最大 `planning_slots_max` 件を **background** で planner エージェントに渡す
（収穫後に plan_queue に残っているものはすべてファイル未生成）。

```
jpoke {config.category} 計画書作成タスク: {entry}

作業ディレクトリ: c:\Users\tmtmp\Documents\pokemon\jpoke

{config.spec_hint}
ハンドラ構成・subject_spec・priority（docs/spec/turn.md 参照）・実装コードを含む計画書を
{config.plan_dir}/{entry}.md に作成すること。
CLAUDE.md のハンドラ約束事を厳守。
```

### 6. 状態ファイルを保存

Write ツールで `.loop/impl_state.json` を上書き。

### 7. 次のウェイクアップを予約

```
ScheduleWakeup(delaySeconds=120, prompt="<<autonomous-loop-dynamic>>",
               reason="{config.category} 実装ループ: 次の件へ")
```

---

## エラーハンドリング

- impl / review-test 失敗 → `failed` に追加してループ継続
- 同じ件が `failed` に 2 回以上 → スキップして次へ

---

## 状態例

```json
{
  "config": {
    "category":           "変化技",
    "plan_dir":           "docs/plan/moves",
    "spec_hint":          "docs/spec/ の対応仕様書を参照（volatiles/, moves/, side_fields/, global_fields/ 以下も確認）",
    "progress_file":      "docs/progress/move.md",
    "test_files":         ["tests/test_move.py"],
    "impl_extra":         "4. data/move.py の MoveData に技が未登録なら追加する",
    "review_extra":       "",
    "planning_slots_max": 2
  },
  "plan_queue":  ["からをやぶる", "ガードシェア"],
  "impl_queue":  ["いばる"],
  "completed":   ["あくび", "あくまのキッス"],
  "failed":      []
}
```
