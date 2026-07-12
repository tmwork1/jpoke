# 計画書: Battle対戦オプション（メガシンカ/テラスタル可否・急所モード・ダメージ乱数モード・命中率固定・効果確率フィルタ）

## 目的

`Battle` のコンストラクタで、対戦全体に関わるオプションを指定できるようにする。

- メガシンカの使用可否
- テラスタルの使用可否
- 急所判定モード（通常 / 確定急所技のみ）
- ダメージ乱数モード（通常 / 平均 / 最大 / 最小）
- 命中率固定（閾値以上の命中率を100%固定にする。閾値未満は通常通り）
- 効果確率フィルタ（閾値以上の追加効果確率は通常通り抽選し、閾値未満は発生しない(0%)扱いにする）

既存の `TestOption`（`src/jpoke/core/battle.py`）は命中率・状態異常発動・追加効果確率など
「乱数判定を都度上書きする」ためのテスト用フックであり、今回の対戦オプションとは目的が異なる。
既存の `TestOption` はそのまま維持し、新設の `BattleOption` を並存させる。

## 現状分析

### メガシンカ / テラスタル可否

`src/jpoke/core/command_manager.py`

- `_can_use_megaevol(state)` (L182-194): 選出済み全員が未メガシンカ かつ `state.active.can_megaevolve()` で判定
- `_can_use_terastal(state)` (L196-208): 選出済み全員が未テラスタル かつ `state.active.can_terastallize()` で判定
- どちらも `get_available_action_commands` (L70-104) 内でコマンド一覧に追加するかどうかの判定にのみ使われる

→ 対戦オプションで「不可」に設定した場合、これらのコマンドをそもそも選択肢に出さないようにすればよい。

### 急所判定

`src/jpoke/core/move_executor.py`

- `CRIT_RATES = [1/24, 1/8, 1/2, 1]` (L19)
- `_check_critical(ctx)` (L182-214):
  1. `Event.ON_CALC_CRITICAL_RANK` を発火して技の `critical_rank` にランク補正を加える（特性・アイテム等の補正が入る）
  2. `clamp_critic` でランクを0-3にクランプ
  3. `Event.ON_MODIFY_CRITICAL_RATE` で確率補正
  4. `self.battle.random.random() < crit_rate` で判定

`src/jpoke/model/move.py` の `Move.critical_rank` (L92-95) は技データ定義値そのもの（ランク補正前）。
「あんこくきょうだ」等の確定急所技は `critical_rank=3` を持ち、`CRIT_RATES[3] == 1` で必ず急所になる。

→ 「確定急所技のみ」モードでは、`ON_CALC_CRITICAL_RANK` によるランク補正（とくせい・どうぐ等）を経由せず、
技定義の `critical_rank` のみをクランプして判定する。これにより特性・ランク変化由来の急所は発生しなくなり、
技自体が確定急所効果を持つ場合のみ急所になる。

### ダメージ乱数

`src/jpoke/core/battle.py`

- `roll_damage` (L530-547): `calc_damages` で16段階のダメージリストを取得し、`self.random.choice(damages)` でランダムに1つ選択

→ ダメージ乱数モードによってこの選択方法を切り替える。
  - 通常: 現状通り `self.random.choice(damages)`
  - 平均: `round_half_down(sum(damages) / len(damages))`（`jpoke.utils.math.round_half_down` を使用。既に `damage.py` でインポート済みの関数と同じ丸め方に揃える）
  - 最大: `max(damages)`
  - 最小: `min(damages)`

### 命中率固定

`src/jpoke/core/move_executor.py`

- `_check_hit(ctx)` (L138-180):
  1. `test_option.accuracy` が設定されていればそれを優先（既存、変更なし）
  2. 技の `accuracy` が `None` なら必中
  3. `Event.ON_MODIFY_ACCURACY` で命中率補正 → `None` なら必中
  4. ランク補正（命中ランク・回避ランク）を適用し、最終的な `accuracy`（int、100超もあり得る）を確定
  5. `self.accuracy = accuracy` で保存後、`100 * self.battle.random.random() < accuracy` で判定

→ 手順4で確定した最終 `accuracy` が閾値以上なら必中として扱い、閾値未満なら手順5の通常判定を行う。
`test_option.accuracy` による上書きより後（＝通常計算パスの最終判定直前）に適用する。

### 効果確率フィルタ

`src/jpoke/core/battle.py`

- `resolve_secondary_chance(ctx, chance)` (L642-646): `test_option.secondary_chance` が設定されていればそれを優先。
  そうでなければ `Event.ON_MODIFY_SECONDARY_CHANCE` で補正した `chance` を返す。呼び出し側
  （`handlers/move.py`, `handlers/move_attack.py`, `handlers/ability.py`, `handlers/item.py` 等）が
  この戻り値を使って `battle.random.random() < chance` 等で抽選する。

→ `Event.ON_MODIFY_SECONDARY_CHANCE` 適用後の `chance` が閾値未満なら `0.0` を返して発生しないようにし、
閾値以上ならそのまま返して通常通り抽選させる。`test_option.secondary_chance` による上書きより後に適用する。

### コピー処理

`fast_copy`（`src/jpoke/utils/copy_utils.py`）は `keys_to_deepcopy` に指定しない属性をシャローコピー（参照共有）する。
既存の `test_option` も `Battle.__deepcopy__` の `keys_to_deepcopy` リストに含まれておらず、参照共有されている。
`BattleOption` も対戦全体で不変な設定値なので同様に扱い、`keys_to_deepcopy` への追加は不要。

## 設計

### 1. Literal型追加（`src/jpoke/types/literals.py`）

```python
CriticalMode = Literal["通常", "確定のみ"]
DamageRollMode = Literal["通常", "平均", "最大", "最小"]
```

`src/jpoke/types/__init__.py` にも re-export を追加する。

### 2. `BattleOption` dataclass 追加（`src/jpoke/core/battle.py`）

`TestOption` の直後に定義する。

```python
@dataclass
class BattleOption:
    """対戦全体のルールオプション設定クラス。

    Attributes:
        mega_evolution: メガシンカを許可するか
        terastal: テラスタルを許可するか
        critical_mode: 急所判定モード（"通常" / "確定のみ"）
        damage_roll: ダメージ乱数モード（"通常" / "平均" / "最大" / "最小"）
        accuracy_fix_threshold: この値以上の命中率を100%固定にする（Noneなら無効）
        effect_chance_threshold: この値未満の追加効果確率を0%（発生しない）にする（Noneなら無効）
    """
    mega_evolution: bool = True
    terastal: bool = True
    critical_mode: CriticalMode = "通常"
    damage_roll: DamageRollMode = "通常"
    accuracy_fix_threshold: int | None = None
    effect_chance_threshold: float | None = None
```

`from jpoke.types import CriticalMode, DamageRollMode` を追加。

### 3. `Battle.__init__` に対戦オプションを1つずつ引数として追加

`BattleOption` をまとめて渡す形にはせず、利用者が使いやすいように各設定値を個別のキーワード引数として渡せるようにする。
内部では従来通り `BattleOption` にまとめて保持し、既存コード（`command_manager.py` 等）からは
`self.battle.option.mega_evolution` のように参照する。

```python
def __init__(self,
             players: tuple[Player, ...],
             n_selected: int = 3,
             seed: int | None = None,
             mega_evolution: bool = True,
             terastal: bool = True,
             critical_mode: CriticalMode = "通常",
             damage_roll: DamageRollMode = "通常",
             accuracy_fix_threshold: int | None = None,
             effect_chance_threshold: float | None = None) -> None:
    ...
    self.option: BattleOption = BattleOption(
        mega_evolution=mega_evolution,
        terastal=terastal,
        critical_mode=critical_mode,
        damage_roll=damage_roll,
        accuracy_fix_threshold=accuracy_fix_threshold,
        effect_chance_threshold=effect_chance_threshold,
    )
    self.test_option: TestOption = TestOption()
```

`Attributes` docstring と `Args` docstring に各引数の説明を追記する。

### 4. メガシンカ / テラスタル可否の反映（`src/jpoke/core/command_manager.py`）

```python
def _can_use_megaevol(self, state: PlayerState) -> bool:
    selection = state.selection
    return (
        self.battle.option.mega_evolution
        and all(not mon.megaevolved for mon in selection)
        and state.active.can_megaevolve()
    )

def _can_use_terastal(self, state: PlayerState) -> bool:
    selection = state.selection
    return (
        self.battle.option.terastal
        and all(not mon.terastallized for mon in selection)
        and state.active.can_terastallize()
    )
```

### 5. 急所判定モードの反映（`src/jpoke/core/move_executor.py`）

```python
def _check_critical(self, ctx: AttackContext) -> bool:
    if self.battle.option.critical_mode == "確定のみ":
        critical_rank = clamp_critic(ctx.move.critical_rank)
        self.critical_rank = critical_rank
        return self.battle.random.random() < CRIT_RATES[critical_rank]

    # 急所ランクの計算（既存ロジック）
    critical_rank = self._events.emit(
        Event.ON_CALC_CRITICAL_RANK,
        ctx,
        ctx.move.critical_rank
    )
    critical_rank = clamp_critic(critical_rank)

    crit_rate = self._events.emit(
        Event.ON_MODIFY_CRITICAL_RATE,
        ctx,
        CRIT_RATES[critical_rank]
    )

    self.critical_rank = critical_rank

    return self.battle.random.random() < crit_rate
```

「確定のみ」モードでも `self.battle.random.random()` による通常の乱数判定は維持する
（`critical_rank < 3` なら `CRIT_RATES[critical_rank] < 1` なので通常通り外れうる。
技側のランクが3以上の技だけが確定急所として成立する）。

### 6. ダメージ乱数モードの反映（`src/jpoke/core/battle.py`）

```python
def roll_damage(self,
                attacker: Pokemon,
                defender: Pokemon,
                move: Move | MoveName,
                critical: bool = False) -> int:
    damages = self.calc_damages(attacker, defender, move, critical)
    match self.option.damage_roll:
        case "平均":
            return round_half_down(sum(damages) / len(damages))
        case "最大":
            return max(damages)
        case "最小":
            return min(damages)
        case _:
            return self.random.choice(damages)
```

`from jpoke.utils.math import round_half_down` を `battle.py` に追加する。

### 7. 命中率固定の反映（`src/jpoke/core/move_executor.py`）

```python
def _check_hit(self, ctx: AttackContext) -> bool:
    # テストオプションによる命中率の上書き
    if self.battle.test_option.accuracy is not None:
        self.accuracy = self.battle.test_option.accuracy
        return 100 * self.battle.random.random() < self.accuracy

    ...（既存の accuracy 計算・ランク補正はそのまま）

    self.accuracy = accuracy  # デバッグ用に保存

    threshold = self.battle.option.accuracy_fix_threshold
    if threshold is not None and accuracy >= threshold:
        return True

    return 100 * self.battle.random.random() < accuracy
```

### 8. 効果確率フィルタの反映（`src/jpoke/core/battle.py`）

```python
def resolve_secondary_chance(self, ctx: EventContext, chance: float) -> float:
    """追加効果補正後の実効確率を返す。"""
    if self.test_option.secondary_chance is not None:
        return self.test_option.secondary_chance
    chance = self.events.emit(Event.ON_MODIFY_SECONDARY_CHANCE, ctx, chance)
    threshold = self.option.effect_chance_threshold
    if threshold is not None and chance < threshold:
        return 0.0
    return chance
```

## 実装順序

1. `src/jpoke/types/literals.py` に `CriticalMode` / `DamageRollMode` を追加し、`types/__init__.py` で re-export
2. `src/jpoke/core/battle.py`: `BattleOption` 追加、`__init__` にoption引数追加、`roll_damage` 修正、`resolve_secondary_chance` 修正
3. `src/jpoke/core/command_manager.py`: `_can_use_megaevol` / `_can_use_terastal` 修正
4. `src/jpoke/core/move_executor.py`: `_check_critical` 修正、`_check_hit` 修正
5. `python -m pytest tests/ -v` で既存テストが通ることを確認（デフォルト値は全て現行動作と同一のため、既存テストへの影響はないはず）

## テスト観点（新規テストを書く場合）

- `BattleOption(mega_evolution=False)` でメガシンカコマンドが選択肢に出ないこと
- `BattleOption(terastal=False)` でテラスタルコマンドが選択肢に出ないこと
- `BattleOption(critical_mode="確定のみ")` で `critical_rank < 3` の技は急所にならず（`fix_random` で乱数を0に固定しても外れる）、`critical_rank >= 3` の技（例: あんこくきょうだ）は急所になること
- `BattleOption(critical_mode="確定のみ")` 下では、とくせい・ランク変化由来の急所ランク補正（例: きゅうしょアップ）が急所成立に影響しないこと
- `BattleOption(damage_roll="最大"/"最小"/"平均")` で `roll_damage` が期待通りの値を返すこと（`calc_damages` の16通りに対して）
- `BattleOption(accuracy_fix_threshold=90)` で命中率90以上の技が乱数に関わらず必中になり、90未満の技は通常通り外れうること
- `BattleOption(effect_chance_threshold=0.5)` で追加効果確率0.5未満の効果が `fix_random` で乱数を0に固定しても発生しないこと、0.5以上の効果は通常通り抽選されること

## 備考

- `tests/test_utils.py` の `start_battle` にオプション引数を追加するかは実装時に判断する。追加する場合も `Battle.__init__` と同様に `mega_evolution` / `terastal` / `critical_mode` / `damage_roll` / `accuracy_fix_threshold` / `effect_chance_threshold` を個別のキーワード引数として受け取り、`Battle(players, mega_evolution=mega_evolution, ...)` のようにそのまま渡す。既存の `accuracy` / `secondary_chance` の扱いとは独立に扱う。
- `docs/spec/turn.md` のイベントpriority確認は対象外（新規イベントは追加せず、既存イベント発火の有無を分岐するのみのため）。
