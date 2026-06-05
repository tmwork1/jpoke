# 実装計画: へんしょく

作成日: 2026-06-04

## 効果
攻撃技のダメージを受けた後、その技と同じタイプになる。
以下の場合は発動しない:
- ひんしになったとき
- みがわりに当たった（move_damage == 0）
- わるあがき（move.type == ""）
- すでにそのタイプを持つ
- ちからずくの効果が発動した技（要確認）

## イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_DAMAGE` | 100（`turn.md`: 「へんしょく等（防御側特性）」） | `defender:self` | `へんしょく_on_damage` |

## 実装

```python
def へんしょく_on_damage(battle, ctx, value):
    """へんしょく特性: 攻撃技を受けた後、その技のタイプになる。"""
    mon = ctx.defender
    # ひんし・みがわり被弾は不発動
    if ctx.fainted or ctx.move_damage == 0:
        return HandlerReturn(value=value)
    # 連続攻撃は最終ヒット後にのみタイプ変化（第五世代以降仕様）
    if ctx.hit_index != ctx.hit_count:
        return HandlerReturn(value=value)
    move_type = ctx.move.type
    # わるあがきは move.type == "" なので not move_type で除外
    if not move_type:
        return HandlerReturn(value=value)
    if move_type in mon.types:
        return HandlerReturn(value=value)  # すでにそのタイプ
    mon.ability_override_type = move_type
    announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)
```

**補足**: `ctx.move.type` はスキン系や `ON_MODIFY_MOVE_TYPE` 後の最終タイプを反映している前提（既存の `へんげんじざい` と同様）。

## data/ability.py 登録

```python
"へんしょく": AbilityData(
    handlers={
        Event.ON_DAMAGE: h.AbilityHandler(
            h.へんしょく_on_damage,
            subject_spec="defender:self",
        ),
    }
),
```

## テストケース
- 攻撃技を受けた後 → タイプが技のタイプに変化
- すでにそのタイプを持つ → 発動しない
- ひんし時 → 発動しない
- わるあがき → 発動しない（move.type == ""）
- 連続攻撃技（例: ダブルキック）→ 最終ヒット後のみタイプ変化
- スキン変換後の技（例: フェアリースキン適用のハイパーボイス）→ 最終タイプに変化
