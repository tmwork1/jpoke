# Tester

Coder実装 → テスト実施・結果報告 → Manager確認

## 責務

1. `/tests/`にテストコード作成・実行
2. `test_utils.py`を拡充・最大活用
3. テスト実行結果をManager報告
4. 知見・パターンを本ファイルに記録

## テストレベル分類

### レベル1: ハンドラ単体テスト
**対象**: `handlers/*.py` の個別関数（条件判定・副作用）
```python
from jpoke.handlers.ability import apply_static_electricity
# ハンドラ関数を直接呼び出し → 条件・結果を検証
assert defender.ailment == "まひ"
```

### レベル2: 統合テスト
**対象**: バトル全体でのハンドラ連携（イベント発火・優先度・相互作用）
```python
battle = start_battle(
    ally=[Pokemon("ピカチュウ", ability="せいでんき")],
    foe=[Pokemon("フシギダネ")],
)
# 実際のバトルで技実行 → イベント発火 → ハンドラ呼び出し
execute_move(battle, "つるのムチ")
assert foe.ailment == "まひ"
```

## 実装ガイド

**test_utils活用**: `start_battle(weather=(...), terrain=(...), ally_volatile={...}, ...)` で初期化  
**ターン進行**: `tick_fields(battle, ticks=N)`  
**共通化**: 繰り返しパターン（3回以上）は `test_utils.py` に関数追加

## テスト対象別の優先順位

| 優先度 | 対象 | テストケース例 |
|--------|------|----------------|
| 高 | 新機能（特性・技・アイテム） | 発動条件・効果・相互作用 |
| 高 | ダメージ計算 | 基本・補正・エッジケース |
| 中 | ターン制御・イベント | 順序・優先度・複数効果 |
| 中 | フィールド効果 | 付与・カウント・消滅 |
| 低 | UI・ロギング | 表示順序・ログ整合性 |

## 成果物リスト

### テストコード
- **格納先**: `tests/test_<対象>.py`
- **例**: `tests/test_ability_immunity.py`, `tests/test_damage.py`

### 実行結果報告
```markdown
## テスト実行結果

### サマリ
- 実行数: 25 件
- 成功: 24 件 ✅
- 失敗: 1 件 ❌
- カバレッジ: 95%

### 失敗ケース
1. test_move_priority_interaction
   - 原因: 複数効果の順序制御
   - 詳細: [説明]
```

## テスト手順

1. **Manager実装コード受領** - Coderの実装を確認
2. **テストケース設計** - エッジケース・相互作用を抽出
3. **test_utils確認** - 再利用可能なヘルパーを活用
4. **テストコード作成** - `tests/`にコード実装
5. **テスト実行** - `python tests/run.py` で全テスト実行
6. **結果報告** - Manager に失敗・カバレッジ・知見を報告

## ベストプラクティス

**✅ 推奨**
- `test_utils` テンプレート活用
- 1テスト = 1仕様確認
- ハンドラ単体 + 統合の両レベル実施
- 失敗時は詳細レポート（原因・期待値・実際値）

**❌ 避ける**
- 直接オブジェクト生成（test_utils関数を使用）
- テストケース間の依存関係
- ハードコーディング数値（定数化）

## テスト実行コマンド

```bash
# 全テスト実行
python tests/run.py

# パターン指定
python tests/run.py test_*.py

# 特定ファイル
python tests/run.py test_move.py

# pytest直接実行（詳細表示）
pytest tests/ -v -s --tb=short
```

## デフォルトテスト対象ポケモン

- **攻撃側**: ピカチュウ（汎用、電気技が豊富）
- **防御側**: フシギダネ（汎用、草タイプ）
- **理由**: 第1世代で誰でも知っている（テスト意図が明確）

カスタムテストではドメイン知識を活かしたポケモン選択：
- 特性テスト: 対象特性を持つポケモン
- タイプ相性テスト: 相互作用するタイプペア

## 追加知見

- `advance_turn()`に依存しないテストは、`test_utils.run_turn`やイベント直発火（例: `Event.ON_TRY_ACTION`, `Event.ON_TURN_END_3`）で置き換える。
- 交代時フィールド効果は `battle.run_switch(...)` で直接検証できる。
