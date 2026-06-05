# 実装計画: ふうりょくでんき

作成日: 2026-06-04

## 効果
- 風ラベルを持つ攻撃技でダメージを受けたとき → じゅうでん状態になる
- 味方の場においかぜ状態が発生したとき → じゅうでん状態になる

## イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_DAMAGE` | 20（`turn.md`: 「ふうりょくでんき: 風技を受けた」） | `defender:self` | `ふうりょくでんき_on_damage` |
| `ON_FIELD_ACTIVATE` | 100（`かぜのり` 参照） | `source:self` | `ふうりょくでんき_on_field_activate` |

## 実装

風技は `move.has_label("wind")` で識別する（ラベル一覧リストは不要）。

```python
def ふうりょくでんき_on_damage(battle, ctx, value):
    """ふうりょくでんき特性: 風技のダメージを受けたときじゅうでん状態になる。"""
    if ctx.move_damage == 0:  # みがわりに当たった
        return HandlerReturn(value=value)
    if not ctx.move.has_label("wind"):
        return HandlerReturn(value=value)
    mon = ctx.defender
    battle.volatile_manager.apply(mon, "じゅうでん")
    announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)


def ふうりょくでんき_on_field_activate(battle, ctx, value):
    """ふうりょくでんき特性: 味方のおいかぜ発生時にじゅうでん状態になる。"""
    # かぜのり の ON_FIELD_ACTIVATE 実装を参照して field.name と side を確認する
    mon = ctx.source
    field = ctx.field
    if field is None or field.name != "おいかぜ":
        return HandlerReturn(value=value)
    # 味方の場のおいかぜのみ対象
    if field.side != mon.side:
        return HandlerReturn(value=value)
    battle.volatile_manager.apply(mon, "じゅうでん")
    announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)
```

**補足**:
- 既にじゅうでん状態の場合、`volatile_manager.apply` は重複付与を失敗として扱い、ゲーム上の効果はない（仕様: 既に状態でも「発動する」が実効は無し）
- ON_FIELD_ACTIVATE の ctx.field のアクセス方法は `かぜのり_on_field_activate` の実装を参照

## data/ability.py 登録

```python
"ふうりょくでんき": AbilityData(
    handlers={
        Event.ON_DAMAGE: h.AbilityHandler(
            h.ふうりょくでんき_on_damage,
            subject_spec="defender:self",
            priority=20,
        ),
        Event.ON_FIELD_ACTIVATE: h.AbilityHandler(
            h.ふうりょくでんき_on_field_activate,
            subject_spec="source:self",
        ),
    }
),
```

## テストケース
- ぼうふう等の wind ラベル技で被弾 → じゅうでん状態になる
- wind ラベルのない技で被弾 → 発動しない
- みがわりに wind 技が当たった → 発動しない
- おいかぜ展開時 → じゅうでん状態になる
- 相手のおいかぜ展開 → 発動しない
