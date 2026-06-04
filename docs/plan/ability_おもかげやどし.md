# 実装計画: おもかげやどし

作成日: 2026-06-04

## 効果
テラスタル後のオーガポン専用。場に出たとき（またはかがくへんかガス解除後）、フォルムに対応する能力が 1 段階上がる。

| フォルム | 対象能力 |
|---------|---------|
| オーガポン（みどりのめん） | S（素早さ） |
| オーガポン（いどのめん） | D（特防） |
| オーガポン（かまどのめん） | A（攻撃） |
| オーガポン（いしずえのめん） | B（防御） |

## flags

```python
"uncopyable", "protected"  # すでに設定済み
```

## イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_SWITCH_IN` | 100 | `source:self` | `おもかげやどし_activate` |
| `ON_ABILITY_ENABLED` | 100 | `source:self` | `おもかげやどし_activate` |

両イベントに同じ関数を登録する（かがくへんかガス解除後の再発動に対応）。

## 実装

```python
_OGERPON_STAT: dict[str, Stat] = {
    "オーガポン(みどりのめん)": "S",
    "オーガポン(いどのめん)": "D",
    "オーガポン(かまどのめん)": "A",
    "オーガポン(いしずえのめん)": "B",
}


def おもかげやどし_activate(battle, ctx, value):
    """おもかげやどし特性: 場に出たときフォルムに対応する能力が1段階上がる。"""
    mon = ctx.source
    stat = _OGERPON_STAT.get(mon.data.name)
    if stat is None:
        return HandlerReturn(value=value)
    # 場に出てから既に発動済みなら再発動しない
    if mon.ability.activated_since_switch_in:
        return HandlerReturn(value=value)
    mon.ability.activated_since_switch_in = True
    battle.modify_stat(mon, stat, +1, source=mon, reason="おもかげやどし")
    return HandlerReturn(value=value)
```

**補足**:
- `activated_since_switch_in` は `pokemon.reset_on_switch_in()` で `False` にリセットされる（`へんげんじざい` と同じフラグ）
- 能力がすでに +6 のとき、`modify_stat` は変化なし（メッセージ/バー非表示）→ フラグは立てるが `modify_stat` の戻り値で案内せず
- 仕様上「場に出てから 1 回のみ」→ `activated_since_switch_in` で管理

## data/ability.py 登録

```python
"おもかげやどし": AbilityData(
    flags=["uncopyable", "protected"],
    handlers={
        Event.ON_SWITCH_IN: h.AbilityHandler(
            h.おもかげやどし_activate,
            subject_spec="source:self",
        ),
        Event.ON_ABILITY_ENABLED: h.AbilityHandler(
            h.おもかげやどし_activate,
            subject_spec="source:self",
        ),
    }
),
```

## テストケース
- みどりのめん → S+1
- いどのめん → D+1
- かまどのめん → A+1
- いしずえのめん → B+1
- 同じポケモンが 2 回目に発動（交代して再登場後）→ 発動する（フラグリセット）
- かがくへんかガス中 → 発動しない、ガス解除後に発動する
- 対象能力がすでに +6 → バー/メッセージ非表示（発動済みフラグは立つ）
