# ダメージ計算式仕様書

## 概要
ポケモン対戦におけるダメージ計算式と、各種補正の適用順序についてまとめたドキュメント。

## 基本計算式

```
# ダメージ計算式仕様書

## 概要
ポケモン対戦におけるダメージ計算式と、各種補正の適用順序についてまとめたドキュメント。

## 基本計算式

```
ダメージ = 攻撃側のレベル×2÷5+2→切り捨て
　×最終威力×最終攻撃÷最終防御→切り捨て
　÷50+2→切り捨て
　×複数対象3072÷4096→五捨五超入
　×おやこあい(2発目)1024÷4096→五捨五超入
　×天気弱化 2048÷4096→五捨五超入
　×天気強化 6144÷4096→五捨五超入
　×きょけんとつげき 8192÷4096→五捨五超入
　×急所 6144÷4096→五捨五超入
　×乱数(0.85, 0.86, …… 0.99, 1.00 の何れか)→切り捨て
　×タイプ一致6144÷4096→五捨五超入
　または てきおうりょく8192÷4096→五捨五超入
　または てきおうりょく+テラスタル9216÷4096→五捨五超入
　×タイプ相性→切り捨て
　×やけど 2048÷4096→五捨五超入
　×ダメージの補正値÷4096→五捨五超入
　×Z技まもる1024÷4096→五捨五超入
　×ダイマックス技まもる1024÷4096→五捨五超入
　→タイプ相性が0ではないときダメージが1より小さければ1にする
```

**重要**: 各補正は記載順に適用され、補正ごとに切り捨てまたは五捨五超入を行います。

## 補正倍率の基準値: 4096

- **等倍（1.0倍）**: 4096
- **1.5倍**: 6144
- **2.0倍**: 8192
- **0.5倍**: 2048

## 計算の流れ（要約）

1. **基礎ダメージ計算**
2. **戦闘状況による補正**（複数対象・おやこあい・天候・きょけんとつげき）
3. **急所補正**
4. **乱数補正**
5. **タイプ一致補正（STAB）**
6. **タイプ相性補正**
7. **やけど補正**（物理技）
8. **ダメージ補正**（壁・特性・アイテム等）
9. **まもる貫通系補正**
10. **最小ダメージ保証**

## 重要な注意事項

### 1. 切り捨てのタイミング
- 各補正を適用するたびに小数点以下を切り捨てる
- 複数の補正をまとめて計算してから切り捨ててはいけない

### 2. 補正の順序
- 補正の適用順序を間違えると、最終的なダメージが変わる可能性がある
- 特に「急所→ランダム→STAB→タイプ相性→やけど→その他」の順序を厳守

### 3. 0ダメージの扱い
- タイプ相性が0倍の場合、それ以降の計算は不要
- 最小ダメージは1（一部の技を除く）

## 世代による違い

### 第6世代以降（現行）
- 急所補正: 1.5倍
- タイプ一致補正: 1.5倍（てきおうりょくで2.0倍）

### 第5世代以前
- 急所補正: 2.0倍（第2〜5世代）または3.0倍（第1世代）
- その他細かい計算式の違いあり
|-----|---------|---------|---------|---------|
| **軽減系（0.75倍）** |
| フィルター | 0.75倍 | 3072 | 効果ばつぐん（2倍以上）を軽減 | ❌ 未実装 |
| ハードロック | 0.75倍 | 3072 | 効果ばつぐん（2倍以上）を軽減 | ❌ 未実装 |
| プリズムアーマー | 0.75倍 | 3072 | 効果ばつぐん（2倍以上）を軽減 | ❌ 未実装 |
| **軽減系（0.5倍）** |
| たいねつ | 0.5倍 | 2048 | ほのお技のダメージ | ❌ 未実装 |
| あついしぼう | 0.5倍 | 2048 | ほのお・こおり技のダメージ | ❌ 未実装 |
| かんそうはだ | 0.5倍 | 2048 | みず技のダメージ（HP回復に変更） | ❌ 未実装 |
| ちょすい | 無効化 | 0 | みず技のダメージ（HP回復に変更） | ❌ 未実装 |
| よびみず | 無効化 | 0 | みず技を引き寄せて無効化、特攻+1 | ❌ 未実装 |
| **無効化系** |
| もらいび | 無効化 | 0 | ほのお技を無効化、ほのお技威力1.5倍 | ❌ 未実装 |
| でんきエンジン | 無効化 | 0 | でんき技を無効化、素早さ+1段階 | ❌ 未実装 |
| ひらいしん | 無効化 | 0 | でんき技を引き寄せて無効化、特攻+1 | ❌ 未実装 |
| そうしょく | 無効化 | 0 | くさ技を無効化、攻撃+1段階 | ❌ 未実装 |
| ぼうおん | 無効化 | 0 | 音技を無効化 | ❌ 未実装 |
| たいねつ（地面接地時） | 無効化 | 0 | じめん技を無効化（ふゆう等） | ❌ 未実装 |
| **増加系** |
| かんそうはだ | 1.25倍 | 5120 | ほのお技のダメージ増加 | ❌ 未実装 |
| もふもふ | 2.0倍 | 8192 | ほのお技のダメージ増加 | ❌ 未実装 |
| **その他特殊** |
| ふゆう | 無効化 | 0 | じめん技を無効化 | ❌ 未実装 |
| ワンダーガード | - | - | 効果ばつぐん以外無効（ヌケニン専用） | ❌ 未実装 |

#### アイテムによるタイプ補正
| アイテム | 補正倍率 | 4096基準 | 適用条件 | 実装状態 |
|---------|---------|---------|---------|---------|
| **軽減系（半減ベリー）** |
| オッカのみ | 0.5倍 | 2048 | 効果ばつぐんのほのお技（一度きり） | ❌ 未実装 |
| イトケのみ | 0.5倍 | 2048 | 効果ばつぐんのみず技（一度きり） | ❌ 未実装 |
| ソクノのみ | 0.5倍 | 2048 | 効果ばつぐんのでんき技（一度きり） | ❌ 未実装 |
| リンドのみ | 0.5倍 | 2048 | 効果ばつぐんのくさ技（一度きり） | ❌ 未実装 |
| ヤチェのみ | 0.5倍 | 2048 | 効果ばつぐんのこおり技（一度きり） | ❌ 未実装 |
| ヨプのみ | 0.5倍 | 2048 | 効果ばつぐんのかくとう技（一度きり） | ❌ 未実装 |
| ビアーのみ | 0.5倍 | 2048 | 効果ばつぐんのどく技（一度きり） | ❌ 未実装 |
| シュカのみ | 0.5倍 | 2048 | 効果ばつぐんのじめん技（一度きり） | ❌ 未実装 |
| バコウのみ | 0.5倍 | 2048 | 効果ばつぐんのひこう技（一度きり） | ❌ 未実装 |
| ウタンのみ | 0.5倍 | 2048 | 効果ばつぐんのエスパー技（一度きり） | ❌ 未実装 |
| タンガのみ | 0.5倍 | 2048 | 効果ばつぐんのむし技（一度きり） | ❌ 未実装 |
| ヨロギのみ | 0.5倍 | 2048 | 効果ばつぐんのいわ技（一度きり） | ❌ 未実装 |
| カシブのみ | 0.5倍 | 2048 | 効果ばつぐんのゴースト技（一度きり） | ❌ 未実装 |
| ハバンのみ | 0.5倍 | 2048 | 効果ばつぐんのドラゴン技（一度きり） | ❌ 未実装 |
| ナモのみ | 0.5倍 | 2048 | 効果ばつぐんのあく技（一度きり） | ❌ 未実装 |
| リリバのみ | 0.5倍 | 2048 | 効果ばつぐんのはがね技（一度きり） | ❌ 未実装 |
| ロゼルのみ | 0.5倍 | 2048 | 効果ばつぐんのフェアリー技（一度きり） | ❌ 未実装 |
| **軽減系（固定ダメージ半減）** |
| チイラのみ | 0.5倍 | 2048 | ノーマル技（一度きり） | ❌ 未実装 |

### ダメージ補正 (ON_CALC_DAMAGE_MODIFIER)

ダメージ補正は最終ダメージに対して適用され、イベント `ON_CALC_DAMAGE_MODIFIER` を通じて各効果が倍率を返します。

#### サイドフィールド効果
| 効果 | 補正倍率 | 4096基準 | 適用条件 | 実装状態 |
|-----|---------|---------|---------|---------|
| リフレクター | 0.5倍 | 2048 | 物理技、防御側の場（5ターン） | ✅ 実装済 |
| ひかりのかべ | 0.5倍 | 2048 | 特殊技、防御側の場（5ターン） | ✅ 実装済 |
| オーロラベール | 0.5倍 | 2048 | 物理・特殊技、防御側の場（5ターン、雪限定） | ❌ 未実装 |

**注意**: ダブルバトルでは壁の効果が 2/3倍（約2730/4096）になります。ひかりのねんどで8ターンに延長可能。

#### 特性による最終ダメージ補正（防御側）
| 特性 | 補正倍率 | 4096基準 | 適用条件 | 実装状態 |
|-----|---------|---------|---------|---------|
| **HP依存軽減** |
| マルチスケイル | 0.5倍 | 2048 | HP満タン時 | ❌ 未実装 |
| ファントムガード | 0.5倍 | 2048 | HP満タン時（ルナアーラ専用） | ❌ 未実装 |
| **タイプ系軽減** |
| もふもふ | 0.5倍 | 2048 | 接触技のダメージ | ❌ 未実装 |
| パンクロック | 0.5倍 | 2048 | 音技のダメージ | ❌ 未実装 |
| こおりのりんぷん | 0.5倍 | 2048 | 特殊技のダメージ | ❌ 未実装 |
| **その他軽減** |
| たいねつ | 0.5倍 | 2048 | ほのお技のダメージ | ❌ 未実装 |
| あついしぼう | 0.5倍 | 2048 | ほのお・こおり技のダメージ | ❌ 未実装 |
| **増加系** |
| もふもふ | 2.0倍 | 8192 | ほのお技のダメージ | ❌ 未実装 |
| かんそうはだ | 1.25倍 | 5120 | ほのお技のダメージ | ❌ 未実装 |

#### 特性による最終ダメージ補正（攻撃側）
| 特性 | 補正倍率 | 4096基準 | 適用条件 | 実装状態 |
|-----|---------|---------|---------|---------|
| スナイパー | 1.5倍 | 6144 | 急所時（1.5倍からさらに1.5倍で2.25倍） | ❌ 未実装 |
| パンクロック | 1.3倍 | 5324 | 音技の威力 | ❌ 未実装 |

#### アイテムによる最終ダメージ補正
| アイテム | 補正倍率 | 4096基準 | 適用条件 | 実装状態 |
|---------|---------|---------|---------|---------|
| たつじんのおび | 1.2倍 | 4915 | 効果ばつぐんの技 | ❌ 未実装 |

#### その他の最終ダメージ補正
| 効果 | 補正倍率 | 4096基準 | 適用条件 | 実装状態 |
|-----|---------|---------|---------|---------|
| 急所 | 1.5倍 | 6144 | 急所に当たった場合（第6世代以降） | ✅ 実装済 |
| ランダム補正 | 0.85～1.0倍 | 3482～4096 | 16段階のランダム値 | ✅ 実装済 |
| タイプ一致（STAB） | 1.5倍 | 6144 | 攻撃側のタイプと技タイプが一致 | ✅ 実装済 |
| タイプ一致（てきおうりょく） | 2.0倍 | 8192 | 特性てきおうりょくでタイプ一致 | ❌ 未実装 |
| タイプ相性 | 0～4.0倍 | 0～16384 | 防御側のタイプとの相性 | ✅ 実装済 |
| やけど（物理技） | 0.5倍 | 2048 | やけど状態で物理技使用 | ✅ 実装済 |
| 複数対象（ダブル） | 0.75倍 | 3072 | ダブルバトルで複数対象の技 | ❌ 未実装 |

## イベントシステムと補正の実装

### イベントの種類

コードでは以下のイベントを使用して補正を管理しています（[event.py](../src/jpoke/utils/enums/event.py) 参照）：

| イベント名 | 用途 | 適用タイミング | 基準値 |
|-----------|------|--------------|-------|
| `ON_CALC_POWER_MODIFIER` | 技威力の補正 | `calc_final_power()` 内 | 4096 |
| `ON_CALC_ATK_MODIFIER` | 攻撃力/特攻の補正 | `calc_final_attack()` 内 | 4096 |
| `ON_CALC_DEF_MODIFIER` | 防御力/特防の補正 | `calc_final_defense()` 内 | 4096 |
| `ON_CALC_ATK_TYPE_MODIFIER` | 攻撃側のタイプ相性補正 | `calc_damage()` 内 | 4096 |
| `ON_CALC_DEF_TYPE_MODIFIER` | 防御側のタイプ相性補正 | `calc_damage()` 内 | 4096 |
| `ON_CALC_BURN_MODIFIER` | やけど補正 | `calc_damage()` 内、タイプ相性の後 | 4096 |
| `ON_CALC_DAMAGE_MODIFIER` | ダメージ補正（壁、特性、アイテム等） | `calc_damage()` 内、やけどの後 | 4096 |
| `ON_CALC_PROTECT_MODIFIER` | まもる貫通系補正（Z技、ダイマックス技） | `calc_damage()` 内、最後 | 4096 |
| `ON_CALC_FINAL_DAMAGE_MODIFIER` | 最終ダメージへの順次補正（旧システム） | 使用非推奨 | ダメージ値 |

### ハンドラの登録方法

各特性・アイテム・フィールド効果は、ハンドラとして登録されます。

**例1**: エレキフィールドによる威力補正（[field.py](../src/jpoke/handlers/field.py)）
```python
def エレキフィールド_power_modifier(battle: Battle, ctx: イベントContext, value: Any) -> HandlerReturn:
    """エレキフィールドでの電気技威力1.3倍"""
    if ctx.move.type == "でんき" and not ctx.attacker.is_floating(battle.events):
        return HandlerReturn(True, value * 1.3)
    return HandlerReturn(False, value)
```

**例2**: やけど補正（`ON_CALC_BURN_MODIFIER`）

```python
def calc_burn_modifier(battle: Battle, ctx: イベントContext, value: int) -> HandlerReturn:
    """やけど状態での物理技ダメージ0.5倍"""
    # 攻撃側がやけど状態で物理技を使用している場合
    if ctx.attacker.ailment.name == "やけど" and ctx.move.category == "物理":
        # こんじょう、すいほう等の特性で無効化される
        if ctx.attacker.ability.name not in ["こんじょう", "すいほう"]:
            # 0.5倍 = 2048/4096
            return HandlerReturn(True, value * 2048 // 4096)
    return HandlerReturn(False, value)
```

**例3**: まもる貫通系補正（`ON_CALC_PROTECT_MODIFIER`）

```python
def calc_protect_modifier_z_move(battle: Battle, ctx: イベントContext, value: int) -> HandlerReturn:
    """Z技使用時、まもる状態の相手へのダメージ0.25倍"""
    # 防御側がまもる状態かつ、攻撃側がZ技を使用している場合
    if ctx.defender.is_protecting and ctx.move.is_z_move:
        # 0.25倍 = 1024/4096
        return HandlerReturn(True, value * 1024 // 4096)
    return HandlerReturn(False, value)

def calc_protect_modifier_dynamax(battle: Battle, ctx: イベントContext, value: int) -> HandlerReturn:
    """ダイマックス技使用時、まもる状態の相手へのダメージ0.25倍"""
    # 防御側がまもる状態かつ、攻撃側がダイマックス技を使用している場合
    if ctx.defender.is_protecting and ctx.move.is_dynamax_move:
        # 0.25倍 = 1024/4096
        return HandlerReturn(True, value * 1024 // 4096)
    return HandlerReturn(False, value)
```

**例2**: 最終ダメージへの順次補正（`ON_CALC_FINAL_DAMAGE_MODIFIER`）

`ON_CALC_FINAL_DAMAGE_MODIFIER`イベントは、基礎ダメージに対して各種補正を**優先度順**に適用するために使用します。
優先度（priority）の値が小さいほど先に実行されます。

```python
# タイプ一致補正（STAB）: priority=10
def calc_stab(battle: Battle, ctx: イベントContext, damage: int) -> HandlerReturn:
    """タイプ一致補正"""
    if ctx.attacker.has_type(ctx.move.type):
        # てきおうりょくの場合は2倍、通常は1.5倍
        if ctx.attacker.ability == "てきおうりょく":
            damage = damage * 2
        else:
            damage = damage * 3 // 2
    return HandlerReturn(True, damage)

# タイプ相性補正: priority=20
def calc_type_effectiveness(battle: Battle, ctx: イベントContext, damage: int) -> HandlerReturn:
    """タイプ相性補正"""
    effectiveness = battle.get_type_effectiveness(ctx.move.type, ctx.defender.types)
    if effectiveness == 0:
        return HandlerReturn(True, 0)
    elif effectiveness == 4.0:
        damage = damage * 4
    elif effectiveness == 2.0:
        damage = damage * 2
    elif effectiveness == 0.5:
        damage = damage // 2
    elif effectiveness == 0.25:
        damage = damage // 4
    return HandlerReturn(True, damage)

# やけど補正: priority=30
def calc_burn_modifier(battle: Battle, ctx: イベントContext, damage: int) -> HandlerReturn:
    """やけど状態での物理技ダメージ0.5倍"""
    if ctx.attacker.ailment.name == "やけど" and ctx.move.category == "物理":
        # こんじょう等の特性で無効化されることもある
        if ctx.attacker.ability not in ["こんじょう", "すいほう"]:
            damage = damage // 2
    return HandlerReturn(True, damage)

# 壁補正: priority=40
def calc_wall_modifier(battle: Battle, ctx: イベントContext, damage: int) -> HandlerReturn:
    """リフレクター/ひかりのかべによる軽減"""
    side = battle.get_side(ctx.defender)
    if ctx.move.category == "物理" and side.fields.get("リフレクター"):
        damage = damage // 2
    elif ctx.move.category == "特殊" and side.fields.get("ひかりのかべ"):
        damage = damage // 2
    return HandlerReturn(True, damage)
```

### 優先度による補正順序の管理

`ON_CALC_FINAL_DAMAGE_MODIFIER`イベントのハンドラは、以下の優先度で実行されます：

| 優先度 | 補正内容 | 説明 |
|-------|---------|------|
| 10 | タイプ一致（STAB） | 攻撃側のタイプと技タイプが一致 |
| 20 | タイプ相性 | 防御側のタイプとの相性 |
| 30 | やけど | 物理技のやけど補正 |
| 40 | 壁（リフレクター/ひかりのかべ） | サイドフィールド効果 |
| 50 | 特性補正（防御側） | マルチスケイル、フィルター等 |
| 60 | アイテム補正 | たつじんのおび等 |
| 100 | その他の補正 | デフォルト優先度 |

**重要**: 優先度が同じ場合、登録順に実行されます。補正の順序が結果に影響する場合は、適切な優先度を設定してください。

### 補正値の計算方法（4096基準）

実装では、精度を保つために全ての補正を **4096基準** で計算します。

#### 倍率から4096基準値への変換表

| 倍率 | 計算式 | 4096基準値 |
|-----|-------|----------|
| 2.0倍 | 4096 × 2.0 | 8192 |
| 1.5倍 | 4096 × 1.5 | 6144 |
| 1.3倍 | 4096 × 1.3 | 5324 |
| 1.25倍 | 4096 × 1.25 | 5120 |
| 1.2倍 | 4096 × 1.2 | 4915 |
| 1.1倍 | 4096 × 1.1 | 4505 |
| 1.0倍（等倍） | 4096 × 1.0 | 4096 |
| 0.75倍 | 4096 × 0.75 | 3072 |
| 0.5倍 | 4096 × 0.5 | 2048 |
| 0.25倍 | 4096 × 0.25 | 1024 |

#### コード実装例

**威力補正の実装**（`calc_final_power` より）
```python
# 基本威力
final_pow = move.data.power * dmg_ctx.power_multiplier

# イベントから補正値を取得（4096基準）
r_pow = events.emit(
    Event.ON_CALC_POWER_MODIFIER,
    イベントContext(attacker=attacker, defender=defender, move=move),
    4096  # 初期値（等倍）
)

# 補正を適用（五捨五超入で切り捨て）
final_pow = round_half_down(final_pow * r_pow / 4096)
final_pow = max(1, final_pow)  # 最低値は1
```

**攻撃補正の実装**（`calc_final_attack` より）
```python
# 基本攻撃力とランク補正
final_atk = attacker.stats[stat]
r_rank = rank_modifier(attacker.rank[stat])
final_atk = int(final_atk * r_rank)

# イベントから補正値を取得（4096基準）
r_atk = events.emit(
    Event.ON_CALC_ATK_MODIFIER,
    イベントContext(attacker=attacker, defender=defender, move=move),
    4096  # 初期値（等倍）
)

# 補正を適用
final_atk = round_half_down(final_atk * r_atk / 4096)
final_atk = max(1, final_atk)
```

**複数補正の連鎖例**
```python
# 特性「ちからもち」の実装例
def ちからもち_atk_modifier(battle: Battle, ctx: イベントContext, value: Any) -> HandlerReturn:
    """物理攻撃2倍"""
    if ctx.move.category == "物理":
        # 4096基準で2倍 = 8192
        # すでに他の補正が入っている可能性があるため、valueに乗算
        return HandlerReturn(True, value * 8192 // 4096)  # value * 2
    return HandlerReturn(False, value)

# アイテム「こだわりハチマキ」の実装例
def こだわりハチマキ_atk_modifier(battle: Battle, ctx: イベントContext, value: Any) -> HandlerReturn:
    """物理攻撃1.5倍"""
    if ctx.move.category == "物理":
        # 4096基準で1.5倍 = 6144
        return HandlerReturn(True, value * 6144 // 4096)  # value * 1.5
    return HandlerReturn(False, value)

# 両方が適用された場合: value → value * 2 → value * 2 * 1.5 = value * 3
```

### 五捨五超入（round_half_down）

ポケモンのダメージ計算では、0.5ちょうどの場合は切り捨てる「五捨五超入」を使用します。

```python
def round_half_down(v: float) -> int:
    """五捨五超入で丸める。
    
    0.5は切り捨て、0.5より大きい値は切り上げます。
    """
    return int(Decimal(str(v)).quantize(Decimal('0'), rounding=ROUND_HALF_DOWN))

# 使用例
round_half_down(10.5)   # → 10 (切り捨て)
round_half_down(10.51)  # → 11 (切り上げ)
round_half_down(10.4)   # → 10 (切り捨て)
```

## 補正適用の順序（重要）

ダメージ計算では、補正を適用する順序が非常に重要です。順序を間違えると最終ダメージが変わります。

### 1. 最終威力の計算 (`calc_final_power`)
```
最終威力 = 基本威力 × 威力補正(4096基準) ÷ 4096
```
- 天候補正（晴れ・雨）
- フィールド補正（エレキ・グラス・サイコ・ミスト）
- 特性補正（すてみ、ちからずく等）
- アイテム補正（タイプ強化アイテム等）

### 2. 最終攻撃力の計算 (`calc_final_attack`)
```
最終攻撃 = 実数値 × ランク補正 × 攻撃補正(4096基準) ÷ 4096
```
- ランク補正（-6～+6段階）
- てんねんによるランク無視
- 急所時のランク下降無視
- 特性補正（ちからもち、こんじょう等）
- アイテム補正（こだわりハチマキ等）
- やけど補正（物理技0.5倍）

### 3. 最終防御力の計算 (`calc_final_defense`)
```
最終防御 = 実数値 × ランク補正 × 防御補正(4096基準) ÷ 4096
```
- ランク補正（-6～+6段階）
- てんねんによるランク無視
- 急所時のランク上昇無視
- 技フラグによるランク無視
- 特性補正（ファーコート等）
- アイテム補正（しんかのきせき等）

### 4. 基礎ダメージの計算
```
基礎ダメージ = ((レベル × 2 ÷ 5 + 2) × 最終威力 × 最終攻撃 ÷ 最終防御 ÷ 50 + 2)
```

### 5. 最終ダメージへの補正適用 (`calc_damage`)

基礎ダメージ計算後、以下の順序で補正を適用します。

#### 実装コード例

```python
# 基礎ダメージ計算
base_damage = int(int(int(level * 2 // 5 + 2) * final_pow * final_atk // final_def) // 50 + 2)

# TODO: 複数対象、おやこあい、天気、きょけんとつげき補正
# これらは基礎ダメージに直接適用される（イベント化予定）

# 急所補正
if critical:
    base_damage = round_half_down(base_damage * 6144 / 4096)  # 1.5倍

# 各乱数パターンでダメージ計算
for i in range(16):  # 乱数16通り
    dmg = int(base_damage * (85 + i) / 100)  # ランダム補正（85～100%）切り捨て
    
    # TODO: タイプ一致補正（STABイベント化予定）
    # dmg = round_half_down(dmg * stab / 4096)
    
    # タイプ相性補正（攻撃側）
    dmg = round_half_down(dmg * r_atk_type / 4096)
    
    # タイプ相性補正（防御側）
    dmg = round_half_down(dmg * r_def_type / 4096)
    
    # やけど補正
    dmg = round_half_down(dmg * r_burn / 4096)
    
    # ダメージ補正（壁、特性、アイテム等）
    dmg = round_half_down(dmg * r_dmg / 4096)
    
    # まもる貫通系補正
    dmg = round_half_down(dmg * r_protect / 4096)
    
    # 最小ダメージ保証
    if dmg == 0 and r_def_type > 0:  # タイプ相性が0でない
        dmg = 1
    
    damages[i] = dmg
```

#### イベントから補正値を取得

```python
# タイプ相性補正（攻撃側）
r_atk_type = events.emit(
    Event.ON_CALC_ATK_TYPE_MODIFIER,
    イベントContext(attacker=attacker, defender=defender, move=move),
    4096  # 初期値（等倍）
)

# タイプ相性補正（防御側）
r_def_type = events.emit(
    Event.ON_CALC_DEF_TYPE_MODIFIER,
    イベントContext(attacker=attacker, defender=defender, move=move),
    4096
)

# やけど補正
r_burn = events.emit(
    Event.ON_CALC_BURN_MODIFIER,
    イベントContext(attacker=attacker, defender=defender, move=move),
    4096
)

# ダメージ補正
r_dmg = events.emit(
    Event.ON_CALC_DAMAGE_MODIFIER,
    イベントContext(attacker=attacker, defender=defender, move=move),
    4096
)

# まもる貫通系補正
r_protect = events.emit(
    Event.ON_CALC_PROTECT_MODIFIER,
    イベントContext(attacker=attacker, defender=defender, move=move),
    4096
)
```

## 参考資料

- [ポケモンwiki - ダメージ計算式](https://latest.pokewiki.net/%E3%83%80%E3%83%A1%E3%83%BC%E3%82%B8%E8%A8%88%E7%AE%97%E5%BC%8F)
- 実装コード: [damage.py](../src/jpoke/core/damage.py)
- イベント定義: [event.py](../src/jpoke/utils/enums/event.py)
- 最終更新: 2026年2月1日
