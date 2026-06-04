# 実装計画: とびだすなかみ

作成日: 2026-06-04

## 効果
攻撃技でひんしになったとき、技を受ける**直前**のHPの分だけ攻撃者にダメージを与える。

連続攻撃技の場合は「最初のヒット前のHP」を使う。

## イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_BEGIN_MOVE` | 100 | `defender:self` | `とびだすなかみ_save_hp` |
| `ON_MOVE_KO` | 100 | `defender:self` | `とびだすなかみ_on_ko` |

## HP 追跡の方針

ON_BEGIN_MOVE は技実行前（ダメージ計算前）に発火するため、この時点の `ctx.defender.hp` が「技を受ける直前のHP」に相当する。
累積ダメージを記録する仕組みがないため、ON_DAMAGE_HIT ではなく ON_BEGIN_MOVE で保存するのが正確。

```python
_とびだすなかみ_hp_before: dict[int, int] = {}  # id(defender) → HP before move
```

## 実装

```python
def とびだすなかみ_save_hp(battle, ctx, value):
    """とびだすなかみ補助: 技開始時に防御側の初期HPを保存する。"""
    _とびだすなかみ_hp_before[id(ctx.defender)] = ctx.defender.hp
    return HandlerReturn(value=value)


def とびだすなかみ_on_ko(battle, ctx, value):
    """とびだすなかみ特性: 攻撃技でひんしになったとき攻撃者に反撃ダメージを与える。"""
    attacker = ctx.attacker
    defender = ctx.defender
    if attacker is None or attacker.fainted:
        return HandlerReturn(value=value)
    hp_before = _とびだすなかみ_hp_before.pop(id(defender), abs(value))
    if hp_before <= 0:
        return HandlerReturn(value=value)
    battle.modify_hp(attacker, -hp_before, reason="move_damage")
    announce_ability_triggered(battle, ctx, value, mon=defender)
    return HandlerReturn(value=value)
```

**補足**:
- ON_BEGIN_MOVE 時点ではまだダメージが入っていないため `ctx.defender.hp` が正確な初期HP
- 多段技でも最初のヒット前のHPを使えるため ON_DAMAGE_HIT より正確
- `_とびだすなかみ_hp_before.pop(id, default)` で辞書を自動クリーンアップ
- 攻撃者がすでにひんし（じばく等）なら発動しない

## data/ability.py 登録

```python
"とびだすなかみ": AbilityData(
    handlers={
        Event.ON_BEGIN_MOVE: h.AbilityHandler(
            h.とびだすなかみ_save_hp,
            subject_spec="defender:self",
        ),
        Event.ON_MOVE_KO: h.AbilityHandler(
            h.とびだすなかみ_on_ko,
            subject_spec="defender:self",
        ),
    }
),
```

## テストケース
- 単発攻撃でKO → 残りHP分のダメージ
- 連続攻撃（例: ダブルキック）でKO → 最初のヒット前のHP分のダメージ
- 天候・状態異常ダメージでのひんし → 発動しない（ON_MOVE_KO は技によるひんし限定）
- 攻撃者がじばくで先にひんし → 発動しない（`attacker.fainted` チェック）
- みがわりを無視してダメージを与える（仕様確認要）
