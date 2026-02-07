# コード品質改善の詳細ガイド

**作成日**: 2026年2月7日  
**対象**: jpoke プロジェクト

---

## 1. ハンドラ関数のDocstring改善ガイド

### 現状分析

`handlers/ability.py` の関数は以下の問題を抱えている：

```python
def ありじごく(battle: Battle, ctx: EventContext, value: Any):
    # ON_CHECK_TRAPPED
    result = not ctx.source.is_floating(battle.events)
    return HandlerReturn(True, result)
```

**問題点**:
- docstring がない ❌
- 型ヒントが不完全（`Any` が使われている）❌
- コメントが簡潔すぎて意図が不明確 ❌

---

### 改善方針（5つのレベル）

#### レベル1: 基本的なdocstring追加（最低限）

```python
def ありじごく(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ありじごく特性。
    
    浮いていないポケモンの交代を制限する。
    """
    result = not ctx.source.is_floating(battle.events)
    return HandlerReturn(True, result)
```

#### レベル2: Args/Returns を追加（推奨）

```python
def ありじごく(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ありじごく特性。
    
    浮いていないポケモンの交代を制限する。
    
    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト (source=交代対象)
        value: イベント値（ON_CHECK_TRAPPED では使用未使用）
    
    Returns:
        HandlerReturn: (True, 交代が制限されるかどうか)
    """
    result = not ctx.source.is_floating(battle.events)
    return HandlerReturn(True, result)
```

#### レベル3: 例と注意文を追加（充実）

```python
def ありじごく(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ありじごく特性。
    
    浮きポケモンを除き、すべてのポケモンの交代を制限する。
    
    仕様の詳細:
    - ふゆう、でんじふゆう、テレキネシス中のポケモンは対象外
    - ポケモンを地面に接地していない場合、この特性は機能しない
    
    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト
            - source: 交代を試みるポケモン
        value: イベント値（未使用）
    
    Returns:
        HandlerReturn: 処理成功フラグと制限の有無を返す
            - (True, True): 交代が制限される
            - (True, False): 交代制限なし
    
    Examples:
        >>> # ピジョットが場に出ている場合、地面タイプでないポケモンは交代不可
        >>> # ただし、ふゆう持ちは交代可能
    """
    result = not ctx.source.is_floating(battle.events)
    return HandlerReturn(True, result)
```

#### レベル4: 型ヒント強化（最高品質）

```python
def ありじごく(battle: "Battle", ctx: EventContext, value: None) -> HandlerReturn:
    """ありじごく特性。
    
    浮きポケモンを除き、すべてのポケモンの交代を制限する。
    
    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト (ON_CHECK_TRAPPED)
        value: イベント値（ON_CHECK_TRAPPED では `None`）
    
    Returns:
        HandlerReturn: 常に (True, 制限判定) を返す
    """
    result = not ctx.source.is_floating(battle.events)
    return HandlerReturn(True, result)
```

#### レベル5: インラインコメント追加（参考実装）

```python
def ありじごく(battle: "Battle", ctx: EventContext, value: None) -> HandlerReturn:
    """ありじごく特性。
    
    浮きポケモンを除き、すべてのポケモンの交代を制限する。
    
    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト (ON_CHECK_TRAPPED)
        value: イベント値（ON_CHECK_TRAPPED では `None`）
    
    Returns:
        HandlerReturn: 常に (True, 制限判定) を返す
    """
    # ポケモンが浮いているかどうかを判定
    # 浮いている = ふゆう、でんじふゆう、テレキネシス等
    is_floating = ctx.source.is_floating(battle.events)
    
    # 浮いていない場合、交代を制限する
    # is_floating=False → result=True → 交代制限
    result = not is_floating
    
    return HandlerReturn(True, result)
```

---

### 実装パターン集

#### パターン A: 状態異常予防型

```python
def めんえき(battle: "Battle", ctx: EventContext, value: str) -> HandlerReturn:
    """めんえき特性: どく状態を防ぐ。
    
    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト (ON_BEFORE_APPLY_AILMENT)
        value: 付与しようとする状態異常名
    
    Returns:
        HandlerReturn: (処理実行, 状態異常名)
            - どく/もうどくを防ぎEVENT停止の場合: (True, "", stop_event=True)
            - 防がない場合: (False, value)
    """
    if value in ["どく", "もうどく"]:
        return HandlerReturn(True, "", stop_event=True)
    return HandlerReturn(False, value)
```

#### パターン B: 能力ランク補正型

```python
def すなかき(battle: "Battle", ctx: EventContext, value: int) -> HandlerReturn:
    """すなかき特性: すなあらし中に素早さが2倍になる。
    
    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト (ON_CALC_SPEED)
        value: 元の素早さ値
    
    Returns:
        HandlerReturn: (処理実行, 補正後の素早さ)
    """
    multiplier = 2 if battle.weather == "すなあらし" else 1
    result_speed = value * multiplier
    return HandlerReturn(True, result_speed)
```

#### パターン C: ダメージ軽減型

```python
def ハードロック(battle: "Battle", ctx: EventContext, value: int) -> HandlerReturn:
    """ハードロック特性: 効果ばつぐん(2倍以上)を0.75倍に軽減。
    
    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト (ON_CALC_DAMAGE_MODIFIER)
        value: ダメージ補正倍率（4096基準）
    
    Returns:
        HandlerReturn: (処理実行, 軽減後の補正倍率)
            - 効果ばつぐんの場合: (True, value * 0.75)
            - そうでない場合: (False, value)
    """
    # 2倍以上の受けダメージをチェック
    if value >= 8192:  # 8192 = 2.0倍（4096基準）
        # 0.75倍軽減 = 3072/4096
        reduced = round_half_down(value * 3072 / 4096)
        return HandlerReturn(True, reduced)
    return HandlerReturn(False, value)
```

---

## 2. 型ヒント強化の具体例

### 現状の問題

```python
def describe_event(ctx: EventContext, value: Any) -> HandlerReturn:
    # valueの型が `Any` で、何が渡されるか不明
    # 呼び出し側でも何を期待するか不明確
    pass
```

### 改善方法

#### 方法1: Union 型を使用

```python
from typing import Union

def describe_event(
    ctx: EventContext, 
    value: Union[int, str, dict[str, int]]
) -> HandlerReturn:
    """
    Args:
        value: イベント値
            - ON_CALC_SPEED: int (素早さ値)
            - ON_BEFORE_APPLY_AILMENT: str (状態異常名)
            - ON_MODIFY_STAT: dict[str, int] (能力変更)
    """
    pass
```

#### 方法2: Literal型を使用（より具体的）

```python
from typing import Literal

def on_calc_accuracy(
    battle: Battle,
    ctx: EventContext,
    value: int  # 命中率（0～100）
) -> HandlerReturn:
    """命中率を計算する。
    
    Args:
        value: 元の命中率（0～100の整数）
    
    Returns:
        HandlerReturn: (処理実行, 補正後の命中率)
    """
    pass

def on_before_apply_ailment(
    battle: Battle,
    ctx: EventContext,
    value: str  # 状態異常名
) -> HandlerReturn:
    """状態異常を付与する前の処理。
    
    Args:
        value: 付与しようとする状態異常名
    
    Returns:
        HandlerReturn: (処理実行フラグ, 付与する状態異常名)
    """
    pass
```

#### 方法3: カスタム型エイリアスを定義

```python
# utils/type_defs.py に追加
EventValue = Union[int, str, dict[str, int], float, bool]

# または、より具体的に
AilmentName = Literal[
    "まひ", "やけど", "ねむり", "こおり", "どく", "もうどく"
]
StatChange = dict[Literal["H", "A", "B", "C", "D", "S"], int]

# ハンドラで使用
def めんえき(
    battle: Battle,
    ctx: EventContext,
    value: AilmentName
) -> HandlerReturn:
    # valueが文字列で、かつ状態異常名に限定される
    if value in ["どく", "もうどく"]:
        return HandlerReturn(True, "", stop_event=True)
    return HandlerReturn(False, value)
```

---

## 3. コメント品質の改善例

### 現状の問題

```python
def かちき(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    has_negative = any(v < 0 for v in value.values())
    result = has_negative and ctx.source != ctx.target and ...
    return HandlerReturn(result)
    # なぜ「source != target」の判定が必要か、何を防いでいるか不明確
```

### 改善例

#### レベル1: 簡潔なコメント

```python
def かちき(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    # 能力が低下したかチェック
    has_negative = any(v < 0 for v in value.values())
    
    # 相手の能力低下時のみ、自分の特攻を上げる
    # (自分が攻撃した場合のみ。反射ダメージ等は除外)
    result = has_negative and ctx.source != ctx.target
    
    return HandlerReturn(result)
```

#### レベル2: 詳細なコメント（参考資料付き）

```python
def かちき(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    # かちき特性: 相手の能力が低下した場合、自分の特攻を+2段階上げる
    # 仕様: https://wiki.xn--rckteqa2e.com/wiki/%E3%81%8B%E3%81%A1%E3%81%8D
    
    # value = {stat: change_amount, ...} の辞書
    # 例: {"C": -2, "D": 0} = 特攻-2, 特防不変
    ability_lowered = any(v < 0 for v in value.values())
    
    # ctx.source: 自分（かちき持ち）
    # ctx.target: 相手（能力を低下させた側）
    # もし ctx.source == ctx.target なら、自分の能力が低下した状況
    # （例：からぶりほけんで自分の攻撃が下げられた）
    # この場合、かちきは発動しない
    no_self_abuse = ctx.source != ctx.target
    
    result = ability_lowered and no_self_abuse and \
        common.modify_stat(battle, ctx, {"C": 2}, ...)
    
    return HandlerReturn(result)
```

#### レベル3: Docstring + コメント（最高品質）

```python
def かちき(battle: Battle, ctx: EventContext, value: dict[str, int]) -> HandlerReturn:
    """かちき特性: 能力が低下すると特攻が上がる。
    
    相手の能力が低下した場合、自分の特攻を2段階上昇させる。
    ただし、自分が低下の対象でない場合のみ有効。
    
    仕様詳細:
    - ON_MODIFY_STAT イベントに応答
    - 相手のいずれかの能力が低下する必要がある（-1以下）
    - 自分の能力が低下する状況（反射ダメージ等）では非発動
    
    Args:
        battle: バトルインスタンス
        ctx: イベントコンテキスト
            - source: 自分（かちき持ちのポケモン）
            - target: 相手（能力が低下する側）
        value: 能力変化量の辞書
            形式: {"H": 0, "A": -1, "B": 0, "C": 0, "D": 0, "S": 2}
    
    Returns:
        HandlerReturn: (処理実行, 自分の能力変化)
    
    References:
        - https://wiki.xn--rckteqa2e.com/wiki/%E3%81%8B%E3%81%A1%E3%81%8D
    """
    # 相手の能力が低下しているかチェック
    ability_lowered = any(v < 0 for v in value.values())
    
    if not ability_lowered:
        return HandlerReturn(False)
    
    # 自分が対象でないことを確認（反射ダメージ対策）
    is_attacker = ctx.source != ctx.target
    
    if not is_attacker:
        return HandlerReturn(False)
    
    # 特攻を+2上昇させる
    result = common.modify_stat(
        battle, ctx, {"C": 2}, 
        target_spec="target:self",
        source_spec="target:self"
    )
    
    return HandlerReturn(result)
```

---

## 4. __deepcopy__ 重複排除の実装例

### 現状（重複あり）

```python
# model/pokemon.py
class Pokemon(GameEffect):
    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        return fast_copy(self, new)

# model/move.py
class Move(GameEffect):
    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        return fast_copy(self, new)

# model/ability.py
class Ability(GameEffect):
    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        return fast_copy(self, new)
```

### 改善案（重複排除）

ユーザーコメント:
__deepcopy__ではクラスごとにdeepcopyする対象が異なるため、そのまま継承するような実装はできない。
別のよい統合方法があれば修正してもよい。

#### 案1: 基底クラスに実装を統合

```python
# model/effect.py
from copy import deepcopy
from jpoke.utils import fast_copy

class GameEffect:
    """ゲーム効果の基底クラス。
    
    deepcopy時の処理を共通実装します。
    """
    
    def __deepcopy__(self, memo):
        """浅いコピーを効率的に実行する。
        
        すべての継承クラスで同じ処理を実行するため、
        基底クラスで実装します。
        """
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        return fast_copy(self, new)

# 継承クラスでは __deepcopy__ を削除可能
class Pokemon(GameEffect):
    # __deepcopy__ を削除
    pass

class Move(GameEffect):
    # __deepcopy__ を削除
    pass

class Ability(GameEffect):
    # __deepcopy__ を削除
    pass
```

#### 案2: Mixin クラスで共通化

```python
# model/mixins.py
class CopyMixin:
    """効率的なコピー処理を提供するMixin。"""
    
    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        return fast_copy(self, new)

# model/effect.py
class GameEffect(CopyMixin):
    """ゲーム効果の基底クラス。"""
    pass

# これで全継承クラスで __deepcopy__ が使用可能
class Pokemon(GameEffect):
    pass
```

---

## 5. ダメージ補正ループの関数化
ユーザーコメント:案1でよい

### 現状（ループが繰り返される）

```python
# core/damage.py Line 244～252
for i in range(16):
    dmgs[i] = int(max_dmg * (0.85+0.01*i))

    # タイプ補正
    dmgs[i] = round_half_down(dmgs[i] * r_atk_type / 4096)
    dmgs[i] = round_half_down(dmgs[i] * r_def_type / 4096)

    # やけど補正
    dmgs[i] = round_half_down(dmgs[i] * r_burn / 4096)

    # ダメージ補正
    dmgs[i] = round_half_down(dmgs[i] * r_dmg / 4096)

    # まもる貫通系補正
    dmgs[i] = round_half_down(dmgs[i] * r_protect / 4096)

    # 最低ダメージ補償
    if dmgs[i] == 0 and r_def_type * r_dmg > 0:
        dmgs[i] = 1
```

### 改善案1: ヘルパー関数化

```python
def apply_damage_modifiers(
    dmg: int,
    modifiers: list[int],
    base_type_mult: int,
    base_dmg_mult: int
) -> int:
    """一連のダメージ補正を適用する。
    
    Args:
        dmg: 基礎ダメージ
        modifiers: 補正倍率のリスト（4096基準）
        base_type_mult: タイプ相性の乗数積（除外判定用）
        base_dmg_mult: ダメージ補正倍率の乗数積（除外判定用）
    
    Returns:
        int: 補正後のダメージ（最小1以上）
    """
    for modifier in modifiers:
        dmg = round_half_down(dmg * modifier / 4096)
    
    # 最低ダメージ補償：タイプ相性とダメージ補正が有効な場合は1以上
    if dmg == 0 and base_type_mult * base_dmg_mult > 0:
        dmg = 1
    
    return dmg

# 使用例
for i in range(16):
    dmgs[i] = int(max_dmg * (0.85 + 0.01 * i))
    
    # 一括で補正を適用
    modifiers = [r_atk_type, r_def_type, r_burn, r_dmg, r_protect]
    dmgs[i] = apply_damage_modifiers(
        dmgs[i],
        modifiers,
        r_atk_type * r_def_type,
        r_dmg
    )
```

### 改善案2: 補正計算を構造化

```python
@dataclass
class DamageModifiers:
    """ダメージ補正値をまとめて管理する。"""
    attack_type: int = 4096   # 攻撃側タイプ補正
    defense_type: int = 4096  # 防御側タイプ補正
    burn: int = 4096          # やけど補正
    damage: int = 4096        # ダメージ補正
    protect: int = 4096       # まもる貫通補正
    
    def calculate_single_damage(self, base_dmg: int) -> int:
        """単一ダメージを計算する。"""
        result = base_dmg
        for modifier in [self.attack_type, self.defense_type, 
                        self.burn, self.damage, self.protect]:
            result = round_half_down(result * modifier / 4096)
        
        # 最低ダメージ補償
        if result == 0 and self.defense_type * self.damage > 0:
            result = 1
        
        return result
    
    def calculate_distribution(self, max_dmg: int) -> list[int]:
        """16パターンの乱数ダメージを計算する。"""
        return [
            self.calculate_single_damage(int(max_dmg * (0.85 + 0.01 * i)))
            for i in range(16)
        ]

# 使用例
modifiers = DamageModifiers(
    attack_type=r_atk_type,
    defense_type=r_def_type,
    burn=r_burn,
    damage=r_dmg,
    protect=r_protect
)
dmgs = modifiers.calculate_distribution(max_dmg)
```

---

## 6. チェックリスト：プルリクエスト前に確認

新規機能を追加する際、以下のチェックリストを使用：

- [ ] **Docstring**: 関数・クラスに適切なdocstringが追加されている
  - [ ] 1行要約がある
  - [ ] 詳細説明がある
  - [ ] Args/Returns が記載されている
  
- [ ] **型ヒント**: 完全な型ヒントが記載されている
  - [ ] 関数の入出力に型がある
  - [ ] `Any` ではなく具体的な型が使用されている
  
- [ ] **コメント**: 複雑なロジックが説明されている
  - [ ] 判定条件の理由が分かる
  - [ ] なぜその処理が必要か説明がある
  
- [ ] **テスト**: 機能が適切にテストされている
  - [ ] ユニットテストが存在する
  - [ ] エッジケースがカバーされている
  
- [ ] **ドキュメント**: 仕様書が更新されている
  - [ ] docs/spec/ に関連ドキュメントがある
  - [ ] 既存ドキュメントと矛盾がない

---

**このガイドは開発チーム全体で共有してください**
