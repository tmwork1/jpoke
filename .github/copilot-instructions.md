````instructions
# Copilot 指示

## 基本方針
- 第9世代（SV）仕様準拠、シングル対戦のみ実装
- イベント駆動アーキテクチャを遵守し、効果処理は帰属するオブジェクトのハンドラで実装
- コードの追加や修正があれば、ワークフローに従ってテストとレビューまで完遂
- ユーザへの確認はせず、不明点は推測して継続
- 既存コード・テストを最大限活用し、一貫性・可読性を重視

## 核心概念
- イベント駆動: `EventManager` (`src/jpoke/core/event.py`)
- Handler: 全効果をハンドラで実装 (`src/jpoke/handlers/`)
- RoleSpec: `"role:side"` 形式（`"source:self"`, `"target:foe"` 等）
  - ダメージ計算: `"attacker:self"`, `"defender:self"`
  - その他: `"source:self"`, `"target:self"`
- HandlerReturn: 常に `HandlerReturn(success, value, control)` を返す
- ダメージ計算: 4096基準（1.5倍 = 6144, 0.5倍 = 2048）

## ファイル構成
```
src/jpoke/
 core/       # event.py, battle.py, damage.py
 model/      # pokemon.py, stats.py
 data/       # ability.py, move.py, item.py
 handlers/   # 効果実装
 utils/      # 補助機能
tests/          # test_utils.py, field.py
```

## テスト規則
- ポケモン: 第1世代の有名種（ピカチュウ、フシギダネ等）を優先
- ヘルパー: `start_battle()`, `tick_fields()`, `assert_field_active()`, `get_field_count()`
- フィールド指定: `weather=(名前, カウント)`, `terrain=(名前, カウント)`, `ally_side_field={名前: レイヤー数}`
- 浮動小数点比較: `abs(actual - expected) < 0.01`

## ファイル管理
- ルート直下: README.md, pyproject.toml, setup.cfg, LICENSE のみ
- 中間スクリプト: `docs/spec/` または作業後削除
- テスト: `tests/` 内に配置

## タスク完了時
1. `python -m jpoke.utils.dashboard` 実行
2. README.md 更新
3. 知見を `.github/instructions/agents/*.md` に追記

## ワークフロー
`.github/instructions/_README.md`  `agents/workflow.md`  各エージェント指示を参照
詳細: `project_context.md`, `architecture.md`
````
