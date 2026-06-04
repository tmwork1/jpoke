# 実装計画: おみとおし

作成日: 2026-06-04

## 効果
場に出たとき、相手のアイテムが分かる。アイテム無しなら発動しない。

## イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_SWITCH_IN` | 100（`turn.md`） | `source:self` | `おみとおし_on_switch_in` |

## 実装

```python
def おみとおし_on_switch_in(battle, ctx, value):
    mon = ctx.source
    foe = battle.foe(mon)
    if not foe.item.base_name:  # アイテム無し
        return HandlerReturn(value=value)
    foe.item.revealed = True
    announce_ability_triggered(battle, ctx, value, mon=mon)
    battle.add_event_log(
        mon, LogCode.TEXT_LOG,
        payload={"text": f"{mon.name}は{foe.name}の{foe.item.base_name}をお見通しだ！"}
    )
    return HandlerReturn(value=value)
```

**注意**: `foe.item.base_name` を使う（`item.name` は無効化時に空文字を返す）。

## data/ability.py 登録

```python
"おみとおし": AbilityData(
    handlers={
        Event.ON_SWITCH_IN: h.AbilityHandler(
            h.おみとおし_on_switch_in,
            subject_spec="source:self",
        ),
    }
),
```

## テストケース
- 相手がアイテムを持っている → `item.revealed = True`、ログ出力
- 相手がアイテムを持っていない → 発動しない（ログ無し）
- ぶきようでアイテム無効化中でも `base_name` があれば公開される
