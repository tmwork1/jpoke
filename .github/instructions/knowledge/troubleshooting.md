# トラブルシューティング

よくある問題と解決策。

## イベント・Handler関連

### 問題: Handlerが発動しない

**症状**: 実装したHandlerが呼ばれない

**チェック項目**:
1. **イベントは正しいか**
   ```python
   # ❌ NG: 技命中時なのに ON_SWITCH_IN
   Event.ON_SWITCH_IN: Handler(...)
   
   # ✅ OK
   Event.ON_HIT: Handler(...)
   ```

2. **RoleSpecは正しいか**
   ```python
   # ❌ NG: ダメージ計算で source 使用
   Handler(func, subject_spec="source:self")
   
   # ✅ OK: attacker/defender使用
   Handler(func, subject_spec="attacker:self")
   ```

3. **ハンドラ登録されているか**
   ```python
   # ポケモンが場に出たときに登録
   pokemon.register_handlers(battle.event_manager)
   
   # 引っ込むときに解除
   pokemon.unregister_handlers(battle.event_manager)
   ```

4. **条件チェックが厳しすぎないか**
   ```python
   # 条件を満たさない場合、HandlerReturn(False)で処理されない
   if not meets_condition():
       return HandlerReturn(False)
   ```

**デバッグ方法**:
- `log="always"` に設定してHandlerが呼ばれているか確認
- loggerでデバッグ出力
  ```python
  logger.debug(f"Handler called: {condition}")
  ```

---

### 問題: Handlerが重複発動

**症状**: 同じHandlerが複数回呼ばれる

**原因**: ハンドラの二重登録

**解決策**:
1. `switch_out()` 時に必ず `unregister_handlers()`
2. `switch_in()` 前に未登録を確認
3. 登録状態フラグを管理

```python
def switch_in(self, battle):
    """場に出る"""
    if self._handlers_registered:
        return
    
    self.register_handlers(battle.event_manager)
    self._handlers_registered = True

def switch_out(self, battle):
    """引っ込む"""
    if not self._handlers_registered:
        return
    
    self.unregister_handlers(battle.event_manager)
    self._handlers_registered = False
```

---

### 問題: HandlerReturnの返り値が効かない

**症状**: `HandlerReturn(True, value)` を返しても値が反映されない

**チェック項目**:
1. **イベントの種類**
   - `ON_CALC_POWER_MODIFIER`: valueを返すと補正される
   - `ON_HIT`: valueは通常使わない
   - `ON_TRY_ACTION`: control で BLOCK/INTERRUPT

2. **返り値の意味**
   ```python
   HandlerReturn(
       success=True,      # Handler が処理を実行したか
       value=新しい値,     # 補正後の値（イベントによる）
       control=BLOCK,     # 処理の制御（BLOCK/INTERRUPT）
   )
   ```

---

## ダメージ計算関連

### 問題: ダメージが期待値と違う

**チェック項目**:
1. **乱数要素**
   - 0.85～1.0のランダム補正
   - 急所ヒット（1/24確率）

2. **タイプ相性**
   ```python
   effectiveness = get_type_effectiveness(move_type, [defender.type1, defender.type2])
   ```

3. **ランク補正**
   ```python
   # ランク+1 = 1.5倍、-1 = 2/3倍
   effective_attack = base_attack * rank_multiplier(attack_rank)
   ```

4. **補正の重複**
   ```python
   # 複数の補正は掛け算で累積
   power = base_power
   power = (power * modifier1) // 4096
   power = (power * modifier2) // 4096
   ```

5. **整数演算の丸め**
   ```python
   # 小数点切り捨てで誤差が出る
   damage = (damage * modifier) // 4096
   ```

**デバッグ方法**:
- 各段階でのダメージをログ出力
  ```python
  logger.debug(f"Base damage: {base_damage}")
  logger.debug(f"After type: {after_type}")
  logger.debug(f"Final damage: {final_damage}")
  ```

---

### 問題: 補正が効かない

**チェック項目**:
1. **正しいイベント使用**
   - `ON_CALC_POWER`: 威力そのものを計算
   - `ON_CALC_POWER_MODIFIER`: 威力に補正をかける

2. **RoleSpec**
   ```python
   # ダメージ計算は attacker/defender
   Handler(func, subject_spec="attacker:self")
   ```

3. **条件チェック**
   ```python
   # 条件を満たさないと補正されない
   if ctx.move.type != "ほのお":
       return HandlerReturn(False)
   ```

4. **HandlerReturnの返り値**
   ```python
   # value に補正後の値を返す
   return HandlerReturn(True, modified_value)
   ```

---

## テスト関連

### 問題: テストが失敗する

**チェック項目**:
1. **初期化**
   ```python
   # test_utils.start_battle を使用
   battle = start_battle(
       ally=[Pokemon(...)],
       foe=[Pokemon(...)],
   )
   ```

2. **フィールド効果の指定**
   ```python
   # タプル形式: (名前, カウント)
   weather=("はれ", 5)
   terrain=("エレキフィールド", 5)
   ```

3. **浮動小数点比較**
   ```python
   # ❌ NG: 完全一致
   assert value == expected
   
   # ✅ OK: 許容誤差
   assert abs(value - expected) < 0.01
   ```

4. **状態確認**
   ```python
   # フィールド確認
   assert_field_active(battle, "はれ")
   
   # カウント確認
   assert get_field_count(battle, "エレキフィールド") == 2
   ```

---

### 問題: テストが依存関係でる

**原因**: テストケース間の状態共有

**解決策**:
1. 各テストで独立したbattleインスタンス作成
2. グローバル変数を使わない
3. テスト順序に依存しない設計

```python
# ✅ OK: 各テストで独立
def test_case_1():
    battle = start_battle(...)
    # テスト

def test_case_2():
    battle = start_battle(...)
    # テスト
```

---

## 型・構造関連

### 問題: 型エラー

**症状**: Pydanticのバリデーションエラー

**原因**: フィールドの型が合わない

**解決策**:
```python
# ❌ NG: 型が違う
MoveData(power="90")  # str

# ✅ OK
MoveData(power=90)  # int
```

---

### 問題: AttributeError

**症状**: `'NoneType' object has no attribute 'xxx'`

**原因**: オブジェクトがNone

**解決策**:
```python
# ❌ NG: Noneチェックなし
defender.ailment.name

# ✅ OK: Noneチェック
if defender.ailment:
    name = defender.ailment.name
```

---

## パフォーマンス関連

### 問題: 処理が遅い

**チェック項目**:
1. **不要なログ出力**
   ```python
   # ❌ NG: 補正計算で毎回ログ
   log="always"
   
   # ✅ OK
   log="never"
   ```

2. **無駄な計算**
   ```python
   # ❌ NG: 毎回計算
   for i in range(100):
       value = expensive_calculation()
   
   # ✅ OK: キャッシュ
   cached_value = expensive_calculation()
   for i in range(100):
       value = cached_value
   ```

3. **deepcopyの多用**
   ```python
   # ❌ NG: 全体コピー
   battle_copy = deepcopy(battle)
   
   # ✅ OK: 必要な部分だけ
   battle_copy = fast_copy(battle, keys_to_deepcopy=["players"])
   ```

---

## よくあるコーディングミス

### 1. RoleSpecの間違い

```python
# ❌ NG: ダメージ計算でsource
Event.ON_CALC_POWER_MODIFIER: Handler(func, subject_spec="source:self")

# ✅ OK
Event.ON_CALC_POWER_MODIFIER: Handler(func, subject_spec="attacker:self")
```

---

### 2. HandlerReturn忘れ

```python
# ❌ NG: 返り値なし
def handler(battle, ctx, value):
    apply_effect()

# ✅ OK
def handler(battle, ctx, value):
    apply_effect()
    return HandlerReturn(True)
```

---

### 3. 補正計算の誤り

```python
# ❌ NG: 浮動小数点
modifier = value * 1.5

# ✅ OK: 4096基準
modifier = (value * 6144) // 4096
```

---

### 4. ログの過剰出力

```python
# ❌ NG: 補正で毎回
log="always"

# ✅ OK
log="never"
```

---

### 5. 型ヒントなし

```python
# ❌ NG
def handler(battle, ctx, value):
    pass

# ✅ OK
def handler(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    pass
```

---

## デバッグ Tips

### 1. logger活用

```python
from jpoke.core.logger import get_logger

logger = get_logger(__name__)

def handler(battle, ctx, value):
    logger.debug(f"Input: {value}")
    result = process(value)
    logger.debug(f"Output: {result}")
    return HandlerReturn(True, result)
```

---

### 2. イベントログ確認

```python
# イベント発火をログで追跡
battle.logger.log_debug(f"Event: {event}, Handlers: {len(handlers)}")
```

---

### 3. ブレークポイント

```python
# デバッガでブレークポイント設定
def handler(battle, ctx, value):
    breakpoint()  # ここで停止
    return HandlerReturn(True, value)
```

---

### 4. テスト駆動開発

```python
# 先にテストを書く
def test_feature():
    battle = start_battle(...)
    execute_move(battle, "技名")
    assert battle.foe.active.ailment.name == "まひ"

# 実装
def 技_effect(battle, ctx, value):
    # ...
```

---

## 最新トラブルシューティング（随時追記）

<!-- 新しい問題と解決策はここに追記 -->
