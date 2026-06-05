# グループ計画: KO反応・入場効果系

作成日: 2026-06-05

対象: ソウルハート / ビーストブースト / そうだいしょう / ふくつのたて / ふとうのけん / かんろなミツ / バリアフリー / しょうりのほし

---

## ソウルハート

### 効果
場のポケモンがひんしになるたびに、とくこうが1段階上がる。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_MOVE_KO` | 100 | `source:self` | `ソウルハート_on_ko` |

**注意**: 仕様書では「どのポケモンがどの形でひんしになっても発動」とあるが、`ON_MOVE_KO` は技によるひんし限定。状態異常等によるひんし（`ON_HP_CHANGED`）にも対応するため、両イベントで登録する。

実装の観点では、まず `ON_MOVE_KO` で基本動作を実装し、状態異常ひんし対応は別途検討する。

### 実装

```python
def ソウルハート_on_ko(battle, ctx, value):
    """ソウルハート特性: 誰かひんしになるたびとくこうが1段階上がる。"""
    mon = ctx.source  # subject_spec="source:self" なので自分
    if not battle.is_active(mon):
        return HandlerReturn(value=value)
    if battle.modify_stats(mon, {"C": +1}, source=mon):
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)
```

### data/ability.py 登録

```python
"ソウルハート": AbilityData(
    handlers={
        Event.ON_MOVE_KO: h.AbilityHandler(
            h.ソウルハート_on_ko,
            subject_spec="source:self",
        ),
    }
),
```

**補足**: `subject_spec="source:self"` では ON_MOVE_KO のソース（倒した側）にソウルハートがいる場合のみ発動。倒された側への反応も必要な場合は `defender:self` や `target:self` も追加する。仕様確認後に拡張する。

### テストケース
- 自分が技で相手を倒すとC↑1
- C最大なら発動しない

---

## ビーストブースト

### 効果
攻撃技で他のポケモンをひんしにさせたとき、自分の最も高い能力のランクが1段階上がる。同値の場合はこうげき→ぼうぎょ→とくこう→とくぼう→すばやさの優先順。

**仕様**: 上がる能力の判定はランク補正・持ち物・特性等を考慮しない実数値。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_MOVE_KO` | 100 | `attacker:self` | `ビーストブースト_on_ko` |

### 実装

```python
_BEAST_BOOST_ORDER: tuple[Stat, ...] = ("A", "B", "C", "D", "S")

def ビーストブースト_on_ko(battle, ctx, value):
    """ビーストブースト特性: 倒したとき最も高い実数値の能力が1段階上がる。"""
    mon = ctx.attacker
    best_stat = max(
        _BEAST_BOOST_ORDER,
        key=lambda s: mon.stats[s],
    )
    if battle.modify_stats(mon, {best_stat: +1}, source=mon):
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)
```

**注意**:
- `mon.stats[s]` は補正前の実数値（level/base stats由来）。ランク補正は含まない。
- `max` の `key` が同値の場合は Python の `max` がリストの先頭要素を返すため、`_BEAST_BOOST_ORDER` の順序が優先順に対応する。
- `mon.stats` の実際のキーが `"A","B","C","D","S"` かどうか確認が必要。

### data/ability.py 登録

```python
"ビーストブースト": AbilityData(
    handlers={
        Event.ON_MOVE_KO: h.AbilityHandler(
            h.ビーストブースト_on_ko,
            subject_spec="attacker:self",
        ),
    }
),
```

### テストケース
- 最高実数値がAのとき倒す→A↑1
- 最高実数値が複数同値のとき→優先順（A>B>C>D>S）で決まる
- 既に最高ランクの能力が最高実数値でも他は上がらない

---

## そうだいしょう

### 効果
場に出たとき、その戦闘でひんしになった味方の数×10%（最大50%）の威力補正が発動する。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_SWITCH_IN` | 100 | `source:self` | `そうだいしょう_on_switch_in` |
| `ON_CALC_POWER_MODIFIER` | 100 | `attacker:self` | `そうだいしょう_modify_power` |

### 実装

```python
def そうだいしょう_on_switch_in(battle, ctx, value):
    """そうだいしょう: 入場時にひんし味方数を記録し補正率を設定。"""
    mon = ctx.source
    player = battle.get_player(mon)
    fainted_count = sum(
        1 for p in player.party if p.fainted and p is not mon
    )
    if fainted_count == 0:
        return HandlerReturn(value=value)
    multiplier = min(fainted_count * 0.1, 0.5)
    mon.ability.state = multiplier
    announce_ability_triggered(battle, ctx, value, mon=mon)
    battle.add_event_log(
        mon, LogCode.TEXT_LOG,
        payload={"text": f"{mon.name}は倒された仲間から力をもらった！"}
    )
    return HandlerReturn(value=value)


def そうだいしょう_modify_power(battle, ctx, value):
    """そうだいしょう: 記録された補正率で威力を上げる。"""
    mon = ctx.attacker
    multiplier = mon.ability.state
    if not multiplier:
        return HandlerReturn(value=value)
    value = apply_fixed_modifier(value, int(4096 * (1 + multiplier)))
    return HandlerReturn(value=value)
```

**注意**:
- `ability.state` は float（0.0〜0.5）。
- 入場後に味方がひんしになっても補正は変わらない（仕様）。
- `player.party` の正確なAPIは実装時に確認。

### data/ability.py 登録

```python
"そうだいしょう": AbilityData(
    handlers={
        Event.ON_SWITCH_IN: h.AbilityHandler(
            h.そうだいしょう_on_switch_in,
            subject_spec="source:self",
        ),
        Event.ON_CALC_POWER_MODIFIER: h.AbilityHandler(
            h.そうだいしょう_modify_power,
            subject_spec="attacker:self",
        ),
    }
),
```

### テストケース
- 味方1体ひんし状態で入場 → 威力1.1倍
- 味方5体ひんしで入場 → 威力1.5倍（上限50%）
- 入場後に味方がひんしになっても補正は変わらない

---

## ふくつのたて

### 効果
バトル中一度だけ、場に出たときにぼうぎょが1段階上がる。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_SWITCH_IN` | 100 | `source:self` | `ふくつのたて_on_switch_in` |

**per_battle_once**: `ability.state` で使用済みフラグを管理。

### 実装

```python
def ふくつのたて_on_switch_in(battle, ctx, value):
    mon = ctx.source
    if mon.ability.state == "used":
        return HandlerReturn(value=value)
    mon.ability.state = "used"
    if battle.modify_stats(mon, {"B": +1}, source=mon):
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)
```

### data/ability.py 登録

```python
"ふくつのたて": AbilityData(
    flags=["per_battle_once"],
    handlers={
        Event.ON_SWITCH_IN: h.AbilityHandler(
            h.ふくつのたて_on_switch_in,
            subject_spec="source:self",
        ),
    }
),
```

### テストケース
- 初回入場 → B↑1
- 2回目以降の入場 → 発動しない

---

## ふとうのけん

### 効果
バトル中一度だけ、場に出たときにこうげきが1段階上がる。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_SWITCH_IN` | 100 | `source:self` | `ふとうのけん_on_switch_in` |

### 実装

```python
def ふとうのけん_on_switch_in(battle, ctx, value):
    mon = ctx.source
    if mon.ability.state == "used":
        return HandlerReturn(value=value)
    mon.ability.state = "used"
    if battle.modify_stats(mon, {"A": +1}, source=mon):
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)
```

### data/ability.py 登録

```python
"ふとうのけん": AbilityData(
    flags=["per_battle_once"],
    handlers={
        Event.ON_SWITCH_IN: h.AbilityHandler(
            h.ふとうのけん_on_switch_in,
            subject_spec="source:self",
        ),
    }
),
```

### テストケース
- 初回入場 → A↑1
- 2回目以降の入場 → 発動しない

---

## かんろなミツ

### 効果
バトル中一度だけ、場に出たとき、相手の回避率を1段階下げる。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_SWITCH_IN` | 100 | `source:self` | `かんろなミツ_on_switch_in` |

### 実装

```python
def かんろなミツ_on_switch_in(battle, ctx, value):
    mon = ctx.source
    if mon.ability.state == "used":
        return HandlerReturn(value=value)
    mon.ability.state = "used"
    foe = battle.foe(mon)
    if battle.modify_stats(foe, {"EVA": -1}, source=mon):
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)
```

### data/ability.py 登録

```python
"かんろなミツ": AbilityData(
    flags=["per_battle_once"],
    handlers={
        Event.ON_SWITCH_IN: h.AbilityHandler(
            h.かんろなミツ_on_switch_in,
            subject_spec="source:self",
        ),
    }
),
```

### テストケース
- 初回入場 → 相手EVA↓1
- 2回目以降の入場 → 発動しない
- クリアボディ等でEVA↓無効の相手には発動しない（modify_stats が False）

---

## バリアフリー

### 効果
場に出たとき、敵味方全体のリフレクター・ひかりのかべ・オーロラベールを消す。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_SWITCH_IN` | 100 | `source:self` | `バリアフリー_on_switch_in` |

### 実装

```python
_BARRIER_SCREENS = ("リフレクター", "ひかりのかべ", "オーロラベール")

def バリアフリー_on_switch_in(battle, ctx, value):
    """バリアフリー特性: 入場時に両サイドの壁を解除する。"""
    mon = ctx.source
    triggered = False
    for side in battle.side_managers:
        for screen in _BARRIER_SCREENS:
            field = side.get(screen)
            if field.is_active:
                side._deactivate_field(field)
                triggered = True
    if triggered:
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)
```

**注意**:
- `side._deactivate_field` はプライベートメソッド。公開APIとして `side.remove(name)` が追加された場合はそちらを使う。
- `battle.side_managers` は両プレイヤー分のリストなので両サイドを解除できる。

### data/ability.py 登録

```python
"バリアフリー": AbilityData(
    handlers={
        Event.ON_SWITCH_IN: h.AbilityHandler(
            h.バリアフリー_on_switch_in,
            subject_spec="source:self",
        ),
    }
),
```

### テストケース
- 相手側にリフレクターがあるとき → 入場で解除
- 自分側にひかりのかべがあるとき → 入場で解除
- 両サイドにオーロラベールがあるとき → 両方解除
- 壁が一切ない → アナウンスなし

---

## しょうりのほし

### 効果
場に出ている間、自分の使用する技の命中率が1.1倍になる（正確には4506/4096倍）。一撃必殺技は対象外。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_MODIFY_ACCURACY` | 100 | `attacker:self` | `しょうりのほし_modify_accuracy` |

### 実装

```python
def しょうりのほし_modify_accuracy(battle, ctx, value):
    """しょうりのほし特性: 命中率を4506/4096倍にする（一撃必殺除く）。"""
    if ctx.move.has_label("ohko"):
        return HandlerReturn(value=value)
    return HandlerReturn(value=apply_fixed_modifier(value, 4506))
```

### data/ability.py 登録

```python
"しょうりのほし": AbilityData(
    handlers={
        Event.ON_MODIFY_ACCURACY: h.AbilityHandler(
            h.しょうりのほし_modify_accuracy,
            subject_spec="attacker:self",
        ),
    }
),
```

### テストケース
- 技の命中率が 4506/4096 倍になる（例: 85%命中技 → 約93%）
- 一撃必殺技は命中率変化なし
- こうかくレンズとの累積効果
