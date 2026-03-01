# ログ自動化システムから明示的ログシステムへの移行ガイド

## 概要

`HandlerReturn`の`success`フラグに基づいた自動ログ機能を廃止し、各ハンドラ関数で明示的にログを記入するシステムに変更しました。

## 主な変更点

### 1. HandlerReturn の変更

**旧:**
```python
HandlerReturn(success=True, value=result)
```

**新:**
```python
HandlerReturn(value=result)
```

`success` フラグは削除されました。

### 2. Handler クラスの変更

以下のパラメータと機能が削除されました：
- `log` パラメータ（LogPolicy）
- `log_text` パラメータ  
- `write_log()` メソッド
- `should_log()` メソッド

### 3. ハンドラ派生クラスの変更

各ハンドラ派生クラスのコンストラクタから `log` と `log_text` パラメータが削除されました：

**旧:**
```python
class AbilityHandler(Handler):
    def __init__(self, func, subject_spec, log="on_success", priority=100):
        super().__init__(func, subject_spec, "ability", log=log, priority=priority)
```

**新:**
```python
class AbilityHandler(Handler):
    def __init__(self, func, subject_spec, priority=100, once=False):
        super().__init__(func, subject_spec, "ability", priority=priority, once=once)
```

## ハンドラ関数での明示的ログ記入方法

### EventLogger のヘルパーメソッド

`EventLogger` に以下のヘルパーメソッドが追加されました：

#### テキストベースのログ
```python
def add_text_log(turn: int, idx: int, text: str) -> None
```

**使用例:**
```python
def my_handler(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    # ... 処理 ...
    idx = battle.get_player_index(ctx.source)
    battle.event_logger.add_text_log(battle.turn, idx, "特性が発動した！")
    return HandlerReturn()
```

#### 特性ログ
```python
def add_ability_log(turn: int, idx: int, ability_name: str, success: bool = True) -> None
```

**使用例:**
```python
def いかく(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    # ... 処理 ...
    idx = battle.get_player_index(ctx.source)
    battle.event_logger.add_ability_log(battle.turn, idx, "いかく", success=True)
    return HandlerReturn()
```

#### 持ち物ログ
```python
def add_item_log(turn: int, idx: int, item_name: str, success: bool = True) -> None
```

**使用例:**
```python
def フラッシュファイア(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    # ... 処理 ...
    idx = battle.get_player_index(ctx.source)
    battle.event_logger.add_item_log(battle.turn, idx, "フラッシュファイア")
    return HandlerReturn()
```

#### 揮発状態ログ
```python
def add_volatile_log(turn: int, idx: int, volatile_name: str, applied: bool = True) -> None
```

**使用例:**
```python
def りんしょう_apply(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    # ... 処理 ...
    idx = battle.get_player_index(ctx.source)
    battle.event_logger.add_volatile_log(battle.turn, idx, "りんしょう", applied=True)
    return HandlerReturn()
```

### 汎用の LogCode による直接ログ記入

より細かい制御が必要な場合は、`EventLogger.add()` を直接使用できます：

```python
from jpoke.enums import LogCode

def my_handler(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    # ... 処理 ...
    idx = battle.get_player_index(ctx.source)
    battle.event_logger.add(
        battle.turn,
        idx, 
        LogCode.ABILITY_TRIGGERED,
        payload={"ability": "特性名", "text": "カスタムテキスト"}
    )
    return HandlerReturn()
```

## LogCode の種類

以下の LogCode が利用可能です：

- `WIN` - バトル勝利
- `LOSE` - バトル敗北
- `ACTION_START` - 行動開始
- `ACTION_BLOCKED` - 行動ブロック
- `PROTECT_SUCCESS` - 守る成功
- `PROTECT_FAILED` - 守る失敗
- `MODIFY_HP` - HP変更
- `MODIFY_STAT` - 能力値変更
- `SWITCH_IN` - ポケモン登場
- `SWITCH_OUT` - ポケモン交代
- `CONSUME_ITEM` - 持ち物消費
- `CURE_AILMENT` - 状態異常回復
- `APPLY_AILMENT` - 状態異常適用
- `ABILITY_TRIGGERED` - 特性発動
- `MOVE_USED` - 技使用
- `VOLATILE_APPLIED` - 揮発状態適用
- `VOLATILE_REMOVED` - 揮発状態削除
- `TEXT_LOG` - テキストログ（汎用）

## 修正例

### 例1: 特性ハンドラ（めんえき）

**旧:**
```python
def めんえき(battle: Battle, ctx: BattleContext, value: str) -> HandlerReturn:
    if value in ["どく", "もうどく"]:
        return HandlerReturn(True, "", stop_event=True)
    return HandlerReturn(False, value)
```

**新:**
```python
def めんえき(battle: Battle, ctx: BattleContext, value: str) -> HandlerReturn:
    if value in ["どく", "もうどく"]:
        idx = battle.get_player_index(ctx.target)
        battle.event_logger.add_ability_log(battle.turn, idx, "めんえき", success=True)
        return HandlerReturn(value="", stop_event=True)
    return HandlerReturn(value=value)
```

### 例2: 揮発状態ハンドラ

**旧:**
```python
def remove_volatile(battle: Battle, ctx: BattleContext, value: Any, 
                   name: VolatileName, log: bool = True) -> HandlerReturn:
    mon = ctx.source
    if mon.remove_volatile(battle, name) and log:
        battle.add_event_log(mon, f"{name}解除")
    return HandlerReturn()
```

**新:**
```python
def remove_volatile(battle: Battle, ctx: BattleContext, value: Any, 
                   name: VolatileName, log: bool = True) -> HandlerReturn:
    mon = ctx.source
    if mon.remove_volatile(battle, name) and log:
        idx = battle.get_player_index(mon)
        battle.event_logger.add_volatile_log(battle.turn, idx, name, applied=False)
    return HandlerReturn()
```

## マイグレーション チェックリスト

- [ ] `HandlerReturn` から `success` フラグを削除
- [ ] ハンドラ派生クラスのコンストラクタから `log`, `log_text` パラメータを削除
- [ ] すべてのハンドラ関数にログ記入処理を追加
- [ ] `battle.get_player_index()` でプレイヤーインデックスを取得
- [ ] 適切な `LogCode` またはヘルパーメソッドでログを記入
- [ ] アビリティ、持ち物、揮発状態ハンドラから自動ログ記入パラメータを削除

## 利点

1. **構造的管理**: ログの種類と内容が明確に定義される
2. **柔軟性**: ハンドラ関数内でログの詳細を完全に制御可能
3. **保守性**: ハンドラ関数と対応するログが同じ場所にある
4. **テスト性**: ログロジックが独立して検証可能
