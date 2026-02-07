# 実装パターン集

実装時によく使うパターンのクイックリファレンス。

## Handler基本パターン

### 1. 単純な条件発動

```python
def 特性_condition_check(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """条件チェック型の特性
    
    条件を満たす場合のみ効果を発動する基本パターン
    """
    # 条件チェック
    if not meets_condition(ctx.source):
        return HandlerReturn(False)
    
    # 効果適用
    result = apply_effect(value)
    
    return HandlerReturn(True, result)
```

### 2. 補正値計算

```python
def 特性_modifier(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """補正値を返すパターン（威力・ダメージ・素早さ等）
    
    4096基準: 1.5倍 = 6144, 0.5倍 = 2048
    """
    # 条件チェック
    if not should_apply(ctx):
        return HandlerReturn(False)
    
    # 補正計算（4096基準）
    modifier = 6144  # 1.5倍
    modified_value = (value * modifier) // 4096
    
    return HandlerReturn(True, modified_value)
```

### 3. 状態付与

```python
def 技_ailment(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """状態異常付与パターン"""
    target = ctx.defender
    
    # 既存状態異常チェック
    if target.ailment:
        return HandlerReturn(False)
    
    # 付与
    target.set_ailment("まひ")
    battle.logger.log_message(f"{target.name}はまひした！")
    
    return HandlerReturn(True)
```

### 4. フィールド効果発動

```python
from functools import partial
from jpoke.handlers.common import activate_weather

# 天候変更
Handler(
    partial(activate_weather, weather="はれ", duration=5),
    subject_spec="source:self",
    log="on_success",
)

# 地形変更
Handler(
    partial(activate_terrain, terrain="エレキフィールド", duration=5),
    subject_spec="source:self",
    log="on_success",
)
```

### 5. 複数効果の組み合わせ

```python
# MoveData.handlers にリスト登録
"技名": MoveData(
    handlers={
        Event.ON_HIT: [
            MoveHandler(ダメージ処理, subject_spec="attacker:self"),
            MoveHandler(状態異常付与, subject_spec="attacker:self"),
        ]
    }
)
```

## RoleSpec使い分け

### ダメージ計算イベント

```python
# ON_CALC_POWER_MODIFIER, ON_CALC_DAMAGE_MODIFIER 等
Handler(func, subject_spec="attacker:self")  # 攻撃側
Handler(func, subject_spec="defender:self")  # 防御側
```

### その他イベント

```python
# ON_SWITCH_IN, ON_TURN_END, ON_HIT 等
Handler(func, subject_spec="source:self")   # 発動源
Handler(func, subject_spec="target:self")   # 対象
Handler(func, subject_spec="source:foe")    # 発動源の相手
Handler(func, subject_spec="target:foe")    # 対象の相手
```

## よく使う共通関数

### handlers/common.py

```python
from jpoke.handlers.common import (
    activate_weather,      # 天候変更
    activate_terrain,      # 地形変更
    get_modifier,          # 補正値取得
    apply_modifier,        # 補正値適用
)

# 使用例
partial(activate_weather, weather="はれ", duration=5)
```

### logger活用

```python
from jpoke.core.logger import get_logger

logger = get_logger(__name__)

# デバッグ
logger.debug(f"計算: {value}")

# 情報
logger.info(f"{pokemon.name}の特性発動")

# ユーザー向けメッセージ
battle.logger.log_message(f"{pokemon.name}のこうげきが上がった！")
```

## データ定義パターン

### 特性

```python
"特性名": AbilityData(
    name="特性名",
    description="説明",
    handlers={
        Event.ON_SWITCH_IN: AbilityHandler(
            発動関数,
            subject_spec="source:self",
            log="on_success",
        ),
        Event.ON_CALC_POWER_MODIFIER: AbilityHandler(
            補正関数,
            subject_spec="attacker:self",
            log="never",  # 補正は大量発火するのでログなし
        ),
    }
)
```

### 技

```python
"技名": MoveData(
    name="技名",
    type="ほのお",
    category="physical",
    power=90,
    accuracy=100,
    pp=15,
    priority=0,
    target="normal",
    contact=True,
    description="説明",
    handlers={
        Event.ON_HIT: MoveHandler(
            効果関数,
            subject_spec="attacker:self",
        ),
    }
)
```

### アイテム

```python
"アイテム名": ItemData(
    name="アイテム名",
    description="説明",
    handlers={
        Event.ON_CALC_POWER_MODIFIER: ItemHandler(
            補正関数,
            subject_spec="attacker:self",
            log="never",
        ),
    }
)
```

## テストパターン

### 基本テスト

```python
from tests.test_utils import start_battle

def test_特性発動():
    """特性の基本動作"""
    battle = start_battle(
        ally=[Pokemon("ピカチュウ", ability="せいでんき")],
        foe=[Pokemon("フシギダネ")],
    )
    
    # 行動実行
    execute_move(battle, "つるのムチ")
    
    # 結果確認
    assert battle.foe.active.ailment.name == "まひ"
```

### フィールド初期化

```python
def test_天候効果():
    """天候の効果確認"""
    battle = start_battle(
        ally=[Pokemon("リザードン")],
        foe=[Pokemon("カメックス")],
        weather=("はれ", 5),  # (天候名, 残りターン)
        terrain=("エレキフィールド", 5),  # (地形名, 残りターン)
    )
    
    # 天候確認
    assert_field_active(battle, "はれ")
```

### 複合効果

```python
def test_複合効果():
    """複数効果の相互作用"""
    battle = start_battle(
        ally=[Pokemon("フシギバナ", ability="ようりょくそ", item="きあいのタスキ")],
        foe=[Pokemon("リザードン")],
        weather=("はれ", 5),
        ally_volatile={"みがわり": (None, 50)},  # (カウント, 値)
    )
    
    # 効果確認
    assert battle.ally.active.effective_speed == original_speed * 2
```

## エラーハンドリングパターン

### 推奨パターン

```python
def handler_function(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """エラーハンドリング付きハンドラ"""
    try:
        # 処理
        result = process(value)
        return HandlerReturn(True, result)
    
    except ValueError as e:
        # 予期されるエラー
        battle.logger.log_critical(f"Invalid value: {e}")
        return HandlerReturn(False)
    
    except Exception as e:
        # 予期しないエラー
        battle.logger.log_critical(f"Unexpected error in handler: {e}")
        raise  # 再送出してデバッグ容易に
```

## よくある落とし穴

### 1. RoleSpecの間違い

```python
# ❌ NG: ダメージ計算でsource使用
Event.ON_CALC_POWER_MODIFIER: Handler(func, subject_spec="source:self")

# ✅ OK: ダメージ計算はattacker/defender
Event.ON_CALC_POWER_MODIFIER: Handler(func, subject_spec="attacker:self")
```

### 2. HandlerReturn忘れ

```python
# ❌ NG: 返り値なし
def handler(battle, ctx, value):
    apply_effect()

# ✅ OK: 必ずHandlerReturn
def handler(battle, ctx, value):
    apply_effect()
    return HandlerReturn(True)
```

### 3. 補正計算の誤り

```python
# ❌ NG: 浮動小数点
modifier = value * 1.5

# ✅ OK: 4096基準の整数演算
modifier = (value * 6144) // 4096
```

### 4. ログの過剰出力

```python
# ❌ NG: 補正計算で毎回ログ
Event.ON_CALC_POWER_MODIFIER: Handler(func, log="always")

# ✅ OK: 補正はログなし
Event.ON_CALC_POWER_MODIFIER: Handler(func, log="never")
```

## 最新パターン（随時追記）

<!-- 新しいパターンはここに追記 -->
