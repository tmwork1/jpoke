# グループ計画: 複雑系特性

作成日: 2026-06-05

対象: ほうし / ほろびのボディ / いかりのつぼ / こぼれダネ / どくくぐつ / どくげしょう / ゆうばく / ヘヴィメタル / ライトメタル / じんばいったい

---

## ほうし

### 効果
直接攻撃を受けたとき、30%の確率でどく・まひ・ねむりのいずれかにする。
確率: どく9% / まひ10% / ねむり11%（合計30%）。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_DAMAGE_HIT` | 100 | `defender:self` | `ほうし_on_damage` |

### 実装

```python
def ほうし_on_damage(battle, ctx, value):
    """ほうし: 接触技を受けたとき30%でどく/まひ/ねむりのいずれかを付与。"""
    if not battle.query.is_contact(ctx):
        return HandlerReturn(value=value)
    r = battle.random.random()
    if r < 0.09:
        ailment = "どく"
    elif r < 0.19:
        ailment = "まひ"
    elif r < 0.30:
        ailment = "ねむり"
    else:
        return HandlerReturn(value=value)
    battle.ailment_manager.apply(
        ctx.attacker, ailment,
        source=ctx.defender, ctx=ctx,
    )
    return HandlerReturn(value=value)
```

**注意**:
- ちからずくの効果は `resolve_secondary_chance` ではなく直接乱数判定のため、ちからずくの無効化は適用されない（仕様）。
- くさタイプ・ぼうじん・ぼうじんゴーグルには無効（ailment_manager が拒否する）。

### data/ability.py 登録

```python
"ほうし": AbilityData(
    handlers={
        Event.ON_DAMAGE_HIT: h.AbilityHandler(
            h.ほうし_on_damage,
            subject_spec="defender:self",
        ),
    }
),
```

### テストケース
- 接触技受けて 30% 以内 → 状態異常付与（確率は乱数シードで制御）
- 非接触技 → 発動しない
- どく無効特性の相手にはどく付与失敗（ailment_manager が拒否）

---

## ほろびのボディ

### 効果
直接攻撃を受けると、自分と攻撃者の両方がほろびのうた状態になり、3ターン後にひんしになる。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_DAMAGE_HIT` | 20 | `defender:self` | `ほろびのボディ_on_damage` |

**priority**: `turn.md` ON_DAMAGE priority 20「のろわれボディ等: 攻撃技を受けた」に準拠。

### 実装

```python
def ほろびのボディ_on_damage(battle, ctx, value):
    """ほろびのボディ: 直接攻撃でほろびのうた状態を双方に付与。"""
    if not battle.query.is_contact(ctx):
        return HandlerReturn(value=value)
    attacker = ctx.attacker
    defender = ctx.defender
    if attacker is None or attacker.fainted:
        return HandlerReturn(value=value)
    triggered = False
    for mon in (defender, attacker):
        if not mon.check_volatile("ほろびのうた"):
            battle.volatile_manager.apply(mon, "ほろびのうた", source=defender)
            triggered = True
    if triggered:
        announce_ability_triggered(battle, ctx, value, mon=defender)
    return HandlerReturn(value=value)
```

### data/ability.py 登録

```python
"ほろびのボディ": AbilityData(
    handlers={
        Event.ON_DAMAGE_HIT: h.AbilityHandler(
            h.ほろびのボディ_on_damage,
            subject_spec="defender:self",
            priority=20,
        ),
    }
),
```

### テストケース
- 直接攻撃受けると双方ほろびのうた
- 非接触技では発動しない
- すでにほろびのうた状態の場合は追加しない
- 攻撃者がひんしなら発動しない（じばく等）

---

## いかりのつぼ

### 効果
攻撃を急所に受けたとき、こうげきが最大ランク（+6）まで上がる。

**priority**: `turn.md` ON_DAMAGE priority 20「いかりのつぼ: 急所に当たった」。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_DAMAGE_HIT` | 20 | `defender:self` | `いかりのつぼ_on_damage` |

### 実装

```python
def いかりのつぼ_on_damage(battle, ctx, value):
    """いかりのつぼ: 急所に被弾したときこうげきを最大まで上げる。"""
    if not ctx.critical:
        return HandlerReturn(value=value)
    mon = ctx.defender
    if battle.modify_stats(mon, {"A": +12}, source=ctx.attacker):
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)
```

**注意**: A最大(+6)にするには現在のランクに関わらず +12 ではなく、「+6にセット」する方が正確。`battle.modify_stats` に絶対値設定APIがあるか確認。なければ `{"A": 6 - mon.rank["A"]}` で差分を計算。

### data/ability.py 登録

```python
"いかりのつぼ": AbilityData(
    handlers={
        Event.ON_DAMAGE_HIT: h.AbilityHandler(
            h.いかりのつぼ_on_damage,
            subject_spec="defender:self",
            priority=20,
        ),
    }
),
```

### テストケース
- 急所に被弾 → Aが最大ランク(+6)になる
- 急所でない被弾 → 発動しない
- A最大のときに急所 → メッセージなし（modify_stats が False）

---

## こぼれダネ

### 効果
攻撃技でダメージを受けたとき、グラスフィールドを展開する（5ターン）。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_DAMAGE_HIT` | 100 | `defender:self` | `こぼれダネ_on_damage` |

### 実装

```python
def こぼれダネ_on_damage(battle, ctx, value):
    """こぼれダネ: 被弾時グラスフィールドを展開する。"""
    mon = ctx.defender
    if battle.terrain.apply("グラスフィールド", 5, source=mon):
        announce_ability_triggered(battle, ctx, value, mon=mon)
    return HandlerReturn(value=value)
```

**注意**: すでにグラスフィールドが展開されている場合は発動しない（terrain.apply が False を返す）。グランドコートを持っている場合は 8 ターン（terrain.apply の拡張アイテム機能で対応）。

### data/ability.py 登録

```python
"こぼれダネ": AbilityData(
    handlers={
        Event.ON_DAMAGE_HIT: h.AbilityHandler(
            h.こぼれダネ_on_damage,
            subject_spec="defender:self",
        ),
    }
),
```

### テストケース
- 攻撃受けてグラスフィールド展開（5ターン）
- すでにグラスフィールド中は発動しない

---

## どくくぐつ

### 効果
相手を「どく」状態にしたとき、同時に「こんらん」状態にする。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_APPLY_AILMENT` | 100 | `source:self` | `どくくぐつ_on_apply_ailment` |

**subject_spec**: `source:self` = 状態異常を与えた側が自分のとき発動。

### 実装

```python
def どくくぐつ_on_apply_ailment(battle, ctx, value):
    """どくくぐつ: どく/もうどく付与時に相手をこんらんにする。"""
    ailment = getattr(value, "name", value)
    if ailment not in ("どく", "もうどく"):
        return HandlerReturn(value=value)
    target = ctx.target
    if target is None:
        return HandlerReturn(value=value)
    battle.volatile_manager.apply(target, "こんらん", source=ctx.source)
    announce_ability_triggered(battle, ctx, value, mon=ctx.source)
    return HandlerReturn(value=value)
```

**注意**:
- `ON_APPLY_AILMENT` の value が状態異常オブジェクトか名前文字列かは実装時に確認。
- `subject_spec="source:self"` は「どくを付与した側が自分」を意味する。

### data/ability.py 登録

```python
"どくくぐつ": AbilityData(
    flags=["uncopyable"],
    handlers={
        Event.ON_APPLY_AILMENT: h.AbilityHandler(
            h.どくくぐつ_on_apply_ailment,
            subject_spec="source:self",
        ),
    }
),
```

### テストケース
- どくを付与した直後にこんらんも付与される
- もうどく付与でもこんらん
- まひ等他の状態異常ではこんらん付与されない

---

## どくげしょう

### 効果
物理技を受けると、相手の場に「どくびし」を1層設置する。

**仕様**: 仕様書には「物理技を受けると、相手の場にどくびしを設置する」とある（`ability_list.md`）。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_DAMAGE_HIT` | 20 | `defender:self` | `どくげしょう_on_damage` |

### 実装

```python
def どくげしょう_on_damage(battle, ctx, value):
    """どくげしょう: 物理技被弾時に攻撃者の場にどくびしを設置する。"""
    if battle.resolve_move_category(ctx.attacker, ctx.move) != "物理":
        return HandlerReturn(value=value)
    attacker = ctx.attacker
    if attacker is None:
        return HandlerReturn(value=value)
    foe_side = battle.get_side(attacker)
    poison_spikes = foe_side.get("どくびし")
    if poison_spikes.count < 2:  # 最大2層
        foe_side._activate_field("どくびし", 1)  # どくびしを1層追加
        announce_ability_triggered(battle, ctx, value, mon=ctx.defender)
    return HandlerReturn(value=value)
```

**注意**: `どくびし` の設置方法は `SideFieldManager._activate_field` または既存のどくびし設置APIを使う。どくびしはカウントベース（1層/2層）なので layer 追加の正確な実装は既存コードを参照。

### data/ability.py 登録

```python
"どくげしょう": AbilityData(
    handlers={
        Event.ON_DAMAGE_HIT: h.AbilityHandler(
            h.どくげしょう_on_damage,
            subject_spec="defender:self",
            priority=20,
        ),
    }
),
```

### テストケース
- 物理技受けると攻撃者側にどくびし1層設置
- 特殊技では発動しない
- すでに2層の場合は設置されない

---

## ゆうばく

### 効果
直接攻撃でひんしになったとき、攻撃してきた相手に最大HPの1/4ダメージを与える。

**仕様**: `とびだすなかみ` と類似。ON_MOVE_KO を使用。

### イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_MOVE_KO` | 100 | `defender:self` | `ゆうばく_on_ko` |

### 実装

```python
def ゆうばく_on_ko(battle, ctx, value):
    """ゆうばく: 直接攻撃でKOされたとき攻撃者に1/4ダメージ。"""
    if not battle.query.is_contact(ctx):
        return HandlerReturn(value=value)
    attacker = ctx.attacker
    if attacker is None or attacker.fainted:
        return HandlerReturn(value=value)
    defender = ctx.defender
    damage = max(1, attacker.max_hp // 4)
    battle.modify_hp(attacker, -damage, reason="ability")
    announce_ability_triggered(battle, ctx, value, mon=defender)
    return HandlerReturn(value=value)
```

### data/ability.py 登録

```python
"ゆうばく": AbilityData(
    handlers={
        Event.ON_MOVE_KO: h.AbilityHandler(
            h.ゆうばく_on_ko,
            subject_spec="defender:self",
        ),
    }
),
```

### テストケース
- 直接攻撃でKO → 攻撃者に最大HP1/4ダメージ
- 非接触技でKO → 発動しない
- 攻撃者が既にひんし（じばく等）→ 発動しない
- マジックガード持ち攻撃者 → ダメージなし

---

## ヘヴィメタル / ライトメタル

### 効果
- **ヘヴィメタル**: 自分の重さが2倍になる
- **ライトメタル**: 自分の重さが半分になる

### 現状

両特性とも `src/jpoke/model/pokemon.py` の `Pokemon.weight` プロパティで既に実装済み：

```python
@property
def weight(self) -> float:
    w = self.data.weight
    match self.ability.name:
        case 'ライトメタル':
            w = int(w*0.5*10)/10
        case 'ヘヴィメタル':
            w = w * 2
    ...
```

`data/ability.py` の登録 (`flags=["mold_breaker_ignorable"]`) も正しい。
**追加の実装作業は不要。テストの追加のみ行う。**

### テストケース（追加すべきテスト）
- ヘヴィメタル: `pokemon.weight` が基本値の2倍
- ライトメタル: `pokemon.weight` が基本値の半分
- かたやぶり系技に対してヘヴィメタル/ライトメタルが無効化されることの確認

---

## じんばいったい

### 効果
きんちょうかんとしろのいななき（またはくろのいななき）の効果を持つ。ダブルバトル専用特性。

### シングルバトルでの扱い

シングルバトルでは「味方がいない」ため実質的に無効。仕様書にも「シングルバトルでの影響なし」と解釈される。

**実装方針**: シングルバトルに影響するのはきんちょうかん効果（相手のきのみ使用を防ぐ）のみ。`flags=["uncopyable", "protected"]` は既に設定済み。

追加対応:
- `ON_SWITCH_IN` でアナウンスのみ（きんちょうかんと同様）
- `ON_CHECK_NERVOUS` でリンゴ制限

```python
"じんばいったい": AbilityData(
    flags=["uncopyable", "protected"],
    handlers={
        Event.ON_SWITCH_IN: h.AbilityHandler(
            h.announce_ability_triggered,
            subject_spec="source:self",
        ),
        Event.ON_CHECK_NERVOUS: h.AbilityHandler(
            h.きんちょうかん_check_nervous,  # 共有
            subject_spec="source:foe",
        ),
    }
),
```

### テストケース
- 入場時にアナウンスが出る
- 相手がきのみを使えない
