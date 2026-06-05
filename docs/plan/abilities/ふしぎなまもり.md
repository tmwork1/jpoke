# 実装計画: ふしぎなまもり

作成日: 2026-06-04

## 効果
効果抜群でない攻撃技のダメージを無効化する。変化技・かたやぶり系は防げない。

## イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_TRY_MOVE_1` | 110（`turn.md`） | `defender:self` | `ふしぎなまもり_block_non_effective` |

## flags

```python
"mold_breaker_ignorable"  # かたやぶり系で無視される
```

## 実装

```python
def ふしぎなまもり_block_non_effective(battle, ctx, value):
    """ふしぎなまもり特性: 効果抜群でない攻撃技を無効化する。"""
    if not ctx.move.is_attack:
        return HandlerReturn(value=value)  # 変化技は通す
    if common.is_super_effective(battle, ctx):
        return HandlerReturn(value=value)  # 効果抜群は通す
    return HandlerReturn(value=False, stop_event=True)  # 無効化
```

## data/ability.py 登録

```python
"ふしぎなまもり": AbilityData(
    flags=["mold_breaker_ignorable"],
    handlers={
        Event.ON_TRY_MOVE_1: h.AbilityHandler(
            h.ふしぎなまもり_block_non_effective,
            subject_spec="defender:self",
            priority=110,
        ),
    }
),
```

## テストケース
- 等倍技 → 無効（ダメージ 0）
- 今ひとつ技 → 無効
- 効果抜群技 → 通る（ダメージあり）
- 変化技（でんじは等）→ 通る
- かたやぶり持ちの攻撃 → 無視して通る
- タイプ無効（免疫）の技 → 相性判定より前なので ON_TRY_MOVE_1 で先に無効化
