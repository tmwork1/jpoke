# 大量実装 自律ループ 指示書

**作業ディレクトリ**: `c:\Users\tmtmp\Documents\pokemon\jpoke`

---

## ループの役割

エントリを一件ずつ自律的に実装・テストする。
状態ファイル（`.claude/loop/state.json`）で現在位置とカテゴリ設定を管理し、
一件処理したら次ウェイクアップを予約する。

---

## 状態ファイルのスキーマ

```json
{
  "config": {
    "category":       "変化技",              // 人間向けラベル（ログ・報告に使う）
    "plan_dir":       "docs/plan/moves",     // 計画書ディレクトリ
    "spec_hint":      "docs/spec/ を参照",   // Plan エージェントへのヒント（自由記述）
    "progress_file":  "docs/progress/move.md",
    "test_files":     ["tests/test_move.py"],
    "impl_extra":     "",                    // impl エージェントへの追加指示（任意）
    "review_extra":   ""                     // review-test エージェントへの追加指示（任意）
  },
  "impl_queue":       ["..."],   // 計画書あり、実装待ち
  "plan_queue":       ["..."],   // 計画書なし、計画待ち（パイプライン用）
  "current_planning": null,      // Plan エージェントで処理中のエントリ名
  "completed":        ["..."],
  "failed":           ["..."]
}
```

---

## 毎回のウェイクアップ手順

### ステップ 1 — 状態ファイルを読む

`.claude/loop/state.json` を Read ツールで読み、`config` を変数として保持する。

### ステップ 2 — 終了チェック

`impl_queue`・`plan_queue`・`current_planning` がすべて空なら
→ 「{config.category} 全件完了: {completed のリスト}」と報告してループを終了（ScheduleWakeup を呼ばない）。

### ステップ 3 — plan_queue の処理（パイプライン）

`plan_queue` に件があり `current_planning` が null の場合のみ実行：

- `plan_queue` から先頭のエントリを取り出す（→ `entry`）
- `Plan` エージェントを foreground で起動し `{config.plan_dir}/{entry}.md` を作成させる
  - 指示:
    ```
    jpoke {config.category} 計画書作成タスク: {entry}

    作業ディレクトリ: c:\Users\tmtmp\Documents\pokemon\jpoke

    {config.spec_hint}
    ハンドラ構成・subject_spec・priority（docs/spec/turn.md 参照）・実装コードを含む計画書を
    {config.plan_dir}/{entry}.md に作成すること。
    CLAUDE.md のハンドラ約束事に厳守。
    ```
- Plan 完了後: `impl_queue` の末尾に追加、`current_planning` を null に
- `.claude/loop/state.json` を更新

### ステップ 4 — impl_queue の処理

`impl_queue` から先頭のエントリを取り出す（→ `entry`）。

#### 4-a. impl エージェント（foreground）

```
jpoke {config.category} 実装タスク: {entry}

作業ディレクトリ: c:\Users\tmtmp\Documents\pokemon\jpoke

計画書: {config.plan_dir}/{entry}.md

手順:
1. 計画書を読み込む（CLAUDE.md の実装時参照順に従い関連ファイルも確認）
2. CLAUDE.md のハンドラ約束事に従い、handlers/ と data/ に実装する
3. テストは書かない（review-test エージェントが担当）
{config.impl_extra}
```

impl が失敗した場合: `failed` に追加して次の件へ（ループ継続）。

#### 4-b. パイプライン起動（impl 実行前に並行）

impl foreground 呼び出しの直前に、`plan_queue` に次の件があれば
Plan エージェントを background で起動する（ステップ 3 の条件と同じ）。

#### 4-c. review-test エージェント（foreground）

impl 成功後：

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

review-test 成功後: `completed` に追加。失敗した場合: `failed` に追加（ループ継続）。

### ステップ 5 — 状態ファイルを更新

Write ツールで `.claude/loop/state.json` を上書き保存する。

### ステップ 6 — 次のウェイクアップを予約

```
ScheduleWakeup(
    delaySeconds=120,
    prompt="<<autonomous-loop-dynamic>>",
    reason="{config.category} 実装ループ: 次の件へ"
)
```

---

## エラーハンドリング

- impl か review-test が例外・失敗した場合: `failed` に追加してループ継続
- 同じ件が `failed` に 2 回以上入った場合: スキップして次へ

---

## 状態例（変化技、進行中）

```json
{
  "config": {
    "category":      "変化技",
    "plan_dir":      "docs/plan/moves",
    "spec_hint":     "docs/spec/ の対応仕様書を参照",
    "progress_file": "docs/progress/move.md",
    "test_files":    ["tests/test_move.py"],
    "impl_extra":    "4. data/move.py の MoveData に技が未登録なら追加する",
    "review_extra":  ""
  },
  "impl_queue":       ["あくまのキッス", "おにび", "かいでんぱ"],
  "plan_queue":       [],
  "current_planning": null,
  "completed":        ["あくび"],
  "failed":           []
}
```

## 状態例（特性、新規開始）

```json
{
  "config": {
    "category":      "特性",
    "plan_dir":      "docs/plan/abilities",
    "spec_hint":     "docs/spec/ability/ の対応仕様書を参照",
    "progress_file": "docs/progress/ability.md",
    "test_files":    ["tests/test_ability.py"],
    "impl_extra":    "",
    "review_extra":  ""
  },
  "impl_queue":       [],
  "plan_queue":       ["いかく", "うるおいボディ", "おみとおし"],
  "current_planning": null,
  "completed":        [],
  "failed":           []
}
```
