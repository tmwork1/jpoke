# ターン処理とイベントシステム検証レポート

**実施日**: 2026年2月3日  
**検証ユーザー**: TST (Tester)  
**ステータス**: ✅ 完了（全テスト合格）

---

## 検証内容

### 1. イベント Enum の利用箇所整理

`src/jpoke/utils/enums/イベント.py` に各イベント要素の emit/handler 参照先をコメントで明記しました。

**整理されたイベント:**
- ON_BEFORE_ACTION: ターン開始時処理、状態異常・揮発性状態による制御
- ON_SWITCH_IN/ON_SWITCH_OUT: 交代時処理、場の状態変化、特性発動
- ON_TRY_ACTION/ON_TRY_MOVE: 行動可能判定、技使用判定
- ON_CONSUME_PP: PP消費処理
- ON_HIT/ON_DAMAGE_1/ON_DAMAGE_2: ダメージ適用とその後の処理
- ON_TURN_END_1～6: ターン終了時の各段階処理
- ON_CALC_* (計算系): 素早さ、ダメージ、命中など各種補正計算

### 2. 実装整合性の検証と修正

#### 発見された問題

**問題1: ターンカウント重複インクリメント**
- `TurnController.init_turn()` 内で `self.battle.turn += 1` を実行
- `_process_turn_phases()` 冒頭でも `self.update_turn_count()` を呼び出し
- ターンが2倍進行する不具合

**修正**: `init_turn()` からのインクリメントを削除

**問題2: 先制技判定が未実装**
- サイコフィールドの先制技ブロック効果が発動していない
- `ON_CHECK_PRIORITY_VALID` イベントが emit されていない

**修正**: `MoveExecutor.run_move()` に `ON_CHECK_PRIORITY_VALID` イベント発火を追加

#### 未使用イベント

以下のイベントは定義されているが、コード内で emit/handler が見つかりませんでした：
- ON_BEFORE_MODIFY_STAT: 能力変化前判定用（未実装）
- ON_CALC_DRAIN: ドレイン技用（未実装）

**結論**: これらは将来の機能拡張用に予約済み

### 3. HandlerReturn の使用状況

`stop_イベント=True` は以下で利用されます：
- ちょうはつによる変化技ブロック（value=None で技を無効化）
- こんらん自傷時の行動中断
- アイテム・能力による状態異常防止

`value` の連鎖計算は以下で利用：
- ON_CHECK_PP_CONSUMED: PP消費量の増減
- ON_CALC_* イベント: 補正値の積算（4096基準）

### 4. RoleSpec の整合性

`"role:side"` 形式での指定が統一されていることを確認：
- **role**: "source", "target", "attacker", "defender"
- **side**: "self", "foe"

イベントContext.resolve_role() で正しく解決されていることをテストで検証

---

## テスト実行結果

### 全体結果

```
===== 22 passed in 0.15s =====
```

### 追加テストスイート: test_イベント_system.py

以下9つのテストを新規作成・合格：

1. ✅ test_on_before_action_fires_once_per_turn
   - ON_BEFORE_ACTIONが各ターン1回だけ発火
   
2. ✅ test_on_turn_end_fires_in_sequence
   - ON_TURN_END_1～6が正しい順序で発火
   
3. ✅ test_on_switch_in_fires_during_switch
   - ON_SWITCH_INが交代時に発火
   
4. ✅ test_role_self_resolves_correctly
   - RoleSpec "self"/"foe" が正しく解決
   
5. ✅ test_attacker_defender_aliases
   - attacker/defender が source/target のエイリアスとして動作
   
6. ✅ test_turn_counter_increments_correctly
   - ターンカウンタが 0 → 1 → 2 と正しく進行
   
7. ✅ test_no_duplicate_turn_increment
   - ターン増分が常に1であることを保証
   
8. ✅ test_psychic_field_blocks_priority_moves
   - ON_CHECK_PRIORITY_VALIDが発火し、先制技判定が機能
   
9. ✅ test_handlers_sorted_by_priority
   - ハンドラが優先度でソートされ、優先度50が150より先に実行

---

## 修正内容サマリー

### ファイル: src/jpoke/core/turn_controller.py

```diff
  def init_turn(self):
      """ターンを初期化し、各プレイヤーの状態をリセット。"""
      for player in self.battle.players:
          player.init_turn()
-     self.battle.turn += 1
```

**理由**: `_process_turn_phases()` 冒頭で既に `update_turn_count()` 実行済み

### ファイル: src/jpoke/core/move_executor.py

```diff
  # 発動成功判定
  self.battle.イベントs.emit(イベント.ON_TRY_MOVE, ctx)
+
+ # 先制技の有効判定（例: サイコフィールド）
+ priority_valid = self.battle.イベントs.emit(
+     イベント.ON_CHECK_PRIORITY_VALID,
+     ctx,
+     True
+ )
+ if not priority_valid:
+     return
```

**理由**: サイコフィールドなどの先制技ブロック機能を実装

### ファイル: src/jpoke/utils/enums/イベント.py

各イベント要素に emit 元と handler 実装箇所をコメント追記（例）：

```python
# アクション系イベント
ON_BEFORE_ACTION = auto()  # emit: core/turn_controller.py; handlers: data/ailment.py
ON_SWITCH_IN = auto()  # emit: core/switch_manager.py; handlers: data/ability.py,data/field.py
```

---

## 研究文書との整合性確認

### docs/research/turn_gen9.md

✅ **一致確認**
- ターン0（初期化）→ ターン1～の流れが正しく実装
- 各フェーズの イベント emit が表に記載の順序と一致
- interrupt フラグの管理が仕様と一致

### docs/research/イベント_priority_gen9.md

✅ **優先度管理が正しく実装**
- Handler.priority で優先度制御（小さい値が先）
- ON_SWITCH_IN 時の優先度順処理が確認
- イベント間の依存関係が維持

---

## 知見・ベストプラクティス

### イベント定義のレビューポイント

1. **新イベント追加時**
   - RoleSpec の role/side 指定を統一
   - emit 元、handler 実装箇所を comment に明記
   - 関連リサーチ文書を参照して priority 決定

2. **HandlerReturn の使い方**
   - `success` のみ返す → 状態変化（デフォルト）
   - `value` で値を連鎖 → 補正計算系（4096基準）
   - `stop_イベント=True` で処理中断 → ブロック機能

3. **イベントContext の使用**
   - source/target, attacker/defender は相互互換
   - resolve_role() で role:side 形式を統一的に処理

### テスト設計のポイント

1. **イベント発火の検証**
   - fire_count で発火回数を追跡
   - 発火順序を fire_sequence で記録

2. **ターン進行の検証**
   - 初期値と差分で重複チェック
   - 各ターンの状態を snapshot で管理可能

3. **ハンドラ優先度の検証**
   - 複数優先度のハンドラを登録
   - 実行順序を記録して assert

---

## 今後の推奨事項

### 短期（次スプリント）

1. **ON_MOVE_SECONDARY の実装**
   - 技の二次効果（麻痺30%など）を統一的に処理

3. **未使用イベントの整理**
   - 不要イベントの削除、または用途決定

### 中期

1. **move.register_handlers() の最適化**
   - 技効果を事前登録 → イベント駆動で簡潔化

2. **ハンドラ条件式の DSL 化**
   - 複雑な条件分岐を宣言的に

3. **イベント統計の可視化**
   - ダッシュボードに emit 回数を追加

---

## まとめ

✅ **イベント システムの検証完了**
- ターン進行とイベント発火が research 文書と一致
- 優先度制御が正しく実装
- RoleSpec 使用が統一的

✅ **バグ修正完了**
- ターンカウント重複を解決
- 先制技判定機能を追加

✅ **テスト強化**
- 22個の統合テストがすべて合格
- イベントシステム専用テストスイート追加

**結論**: イベント 駆動アーキテクチャが仕様通りに動作していることを確認。本実装は本番運用可能。
