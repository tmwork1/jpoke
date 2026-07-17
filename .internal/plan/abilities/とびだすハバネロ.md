# 実装計画: とびだすハバネロ

作成日: 2026-06-04

## 効果
攻撃技のダメージを受けたとき、攻撃者を確率 100% でやけど状態にする。
直接攻撃に限定されず、あらゆる攻撃技が対象。

## イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_DAMAGE_HIT` | 100 | `defender:self` | `とびだすハバネロ_on_damage` |

## 実装

ON_DAMAGE_HIT 発火時点では damage > 0 が担保されているため、move_damage のガード不要。

```python
def とびだすハバネロ_on_damage(battle, ctx, value):
    """とびだすハバネロ特性: 攻撃技を受けたとき攻撃者をやけど状態にする。"""
    attacker = ctx.attacker
    if attacker is None:
        return HandlerReturn(value=value)
    battle.ailment_manager.apply(attacker, "やけど", source=ctx.defender, ctx=ctx)
    return HandlerReturn(value=value)
```

**注意**: やけど耐性（ほのおタイプ、すいほう、きよめのしお等）は `ailment_manager.apply` 内の `ON_BEFORE_APPLY_AILMENT` ハンドラで処理される。

## data/ability.py 登録

```python
"とびだすハバネロ": AbilityData(
    handlers={
        Event.ON_DAMAGE_HIT: h.AbilityHandler(
            h.とびだすハバネロ_on_damage,
            subject_spec="defender:self",
        ),
    }
),
```

## テストケース
- 攻撃技でダメージ後 → 攻撃者がやけど
- ほのおタイプの攻撃者 → やけど無効
- すいほう持ちの攻撃者 → やけど無効
- みがわりに当たった場合 → ON_DAMAGE_HIT は発火しないため自動的に不発動
- 攻撃でKOされた場合も発動する
- 直接攻撃でない技（れいとうビーム等）でも発動する
