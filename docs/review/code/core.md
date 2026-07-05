# コードレビュー — core/

日付: 2026-07-05
対象: `src/jpoke/core/`
（`battle.py`, `turn_controller.py`, `move_executor.py`, `command_manager.py`,
`event_manager.py`, `handler.py`, `context.py`, `damage.py`, `event_logger.py`,
`field_manager.py`, `player.py`, `player_state.py`, `ability_manager.py`,
`ailment_manager.py`, `item_manager.py`, `status_manager.py`,
`switch_manager.py`, `volatile_manager.py`, `query.py`, `speed_calculator.py`,
`observation_builder.py`, `lethal.py`, `__init__.py`）
観点: 責務分離、内部実装の隠蔽、拡張性、過剰設計

---

## 総論

`core/` は `Battle` を Facade とし、`TurnController`/`MoveExecutor`/`DamageCalculator`/
`SwitchManager`/`SpeedCalculator`/`CommandManager`/`AbilityManager`/`ItemManager`/
`AilmentManager`/`VolatileManager`/`StatusManager`/`PokemonQuery`/
`WeatherManager`・`TerrainManager`・`GlobalFieldManager`・`SideFieldManager` という
15種のマネージャーに処理を委譲する構成になっている。`Handler`/`EventManager` による
統一的なイベント発火の仕組み、`GameEffect` 側の有効/無効管理と組み合わせた
`subject_spec` ベースのハンドラ照合など、CLAUDE.md が定めた設計規約は総じて守られている。

今回のレビューであらためて確認した限り、既存レビュー（`architecture_review.md`）の
core/ 関連の指摘（CRIT-1, CRIT-3, CRIT-4, ISSUE-2〜11, MINOR-2, MINOR-6, MINOR-7,
NOTE-1）は行番号のずれを除いてすべて現在のコードでも再現することを確認した
（詳細は各節を参照）。本レビューではその上で、依頼observation にある「過剰設計」の
観点を重点的に掘り下げ、以下の新規の指摘を追加した。

1. **内部実装の隠蔽**: `PokemonQuery` が `TurnController.action_order` という
   生のリスト属性を直接読みに行っている（`query.py:168,176`）。これは ISSUE-9
   （`TurnController` が Facade をバイパスして `SwitchManager` に直接触れる）と
   対になる、逆方向のバイパス経路である。
2. **過剰設計（新規・重点）**: `self.battle` しか保持しない「実体のない」7個の
   マネージャー（`AbilityManager`/`ItemManager`/`AilmentManager`/`VolatileManager`/
   `StatusManager`/`CommandManager`/`PokemonQuery`）全てに、`__deepcopy__` +
   `update_reference` という同一の儀式が課されている。一方で同じコードベースの
   `lethal.py`/`observation_builder.py` は全く同じ「状態を持たない処理のまとまり」を
   プレーンなモジュール関数として実装しており、儀式のコストがゼロで済んでいる。
   クラス化という選択が、その効果に見合わない画一的な間接化を生んでいる好例。
3. `_events` プロパティ（`self.battle.events` を返すだけ）が12ファイルに複製されて
   いるが、定義者自身の `SpeedCalculator` は一度も自分の `_events` を使っておらず
   デッドコード化している。`CommandManager` は定義すらせず直接 `self.battle.events`
   を使っており、この「抽象化」が一貫した価値を生んでいないことを示す実例。
4. `BaseContext.derive()` はコードベース全体で呼び出し箇所が1つ（`handlers/volatile.py:1229`）
   しかない汎用的な dataclass フィールド複製メソッドであり、premature generalization の疑いがある。

---

## 重大な指摘

### CRIT-1: `core/observation_builder.py:12` の `OBSERVED_MOVE_INDEXES` がモジュールグローバル辞書

```python
# observation_builder.py:12
OBSERVED_MOVE_INDEXES: dict[Pokemon, dict[int, int]] = {}

def _mask(battle: Battle, player: Player):
    global OBSERVED_MOVE_INDEXES
    OBSERVED_MOVE_INDEXES = {}
    ...
```

`_mask()` 開始時に `global` 文で丸ごと再代入してリセットする設計になっている
（`observation_builder.py:41-42`）。`_mask_move()`（同ファイル121-131行目）で
書き込み、`_mask_command()`（153行目）で読み出す、という「同一 `build()` 呼び出し内で
閉じた一時状態」を、わざわざモジュールグローバルとして持ち回している。

現状は `build()` の呼び出しが同期的に完結するため実害はないが、`Battle` 自体が
`copy_depth` を持つほど深いネストしたコピー・観測構築を行う設計であることを踏まえると、
将来「観測構築中にさらに観測構築を行う」ような再入や、並行処理が発生した場合に
一方の `_mask()` 呼び出しがもう一方の状態を破壊する。`_mask()`/`_mask_pokemon()`/
`_mask_command()` の引数として辞書を明示的に引き回す（ローカル変数化する）べき。

### CRIT-2: `Battle` クラスの docstring `Attributes` が実装と大きく食い違っている

**ファイル**: `src/jpoke/core/battle.py:70-88`（docstring）vs `102-139`（`__init__`実装）

docstring は17個の属性（`players`, `seed`, `turn`, `winner`, `events`, `logger`,
`random`, `damage_calculator`, `move_executor`, `switch_manager`, `turn_controller`,
`speed_calculator`, `weather_manager`, `terrain_manager`, `global_manager`,
`side_managers`, `test_option`）を列挙しているが、実際の `__init__` にはそこに
含まれない次の13個の属性が存在する。

```
n_selected, copy_depth, observer, phase, last_used_move_name, _player_states,
ailment_manager, volatile_manager, query, status_manager, command_manager,
ability_manager, item_manager
```

さらに docstring の `logger` は実装の属性名 `event_logger`（`battle.py:119`）と
一致しない。

```python
# docstring（battle.py:76）
logger: バトルログ記録システム
# 実装（battle.py:119）
self.event_logger = EventLogger()
```

`Battle` はコードベース全体で最も参照頻度が高いクラスであり、この docstring が
「属性一覧」として信頼されると誤解を招く。新しいマネージャー（`ailment_manager`
以降の7個）を `__init__` に追加した際に docstring 側の更新だけが漏れ続けてきたと
見られる。`__init__` の実属性に合わせて総ざらいで更新すべき。

### CRIT-3: `core/__init__.py` の import 順に依存した脆弱な循環 import パターン

**ファイル**: `src/jpoke/core/__init__.py:1-12`

```python
from .handler import Handler, HandlerReturn        # 1
from .lethal import StateDist, LethalHandler, LethalContext  # 2
from .context import BaseContext, EventContext, AttackContext  # 3 ← ここで EventContext が jpoke.core に束縛される
from .event_manager import EventManager              # 4
from .battle import Battle                           # 5 ← battle.py が turn_controller/field_manager/
                                                       #     ailment_manager/volatile_manager/status_manager/query
                                                       #     を module-level import する
from .player import Player                           # 6
from .player_state import PlayerState                # 7
from .ailment_manager import AilmentManager          # 8
from .volatile_manager import VolatileManager        # 9
from .field_manager import SideFieldManager          # 10
from .status_manager import StatusManager            # 11
from .query import PokemonQuery                      # 12
```

同じ `EventContext` を使うファイルのうち、以下の6ファイルはパッケージ経由の
`from jpoke.core import EventContext` を使っている。

```
ailment_manager.py:13, field_manager.py:17, query.py:13,
status_manager.py:13, turn_controller.py:12, volatile_manager.py:13
```

一方、次の8ファイルは定義元モジュールを直接 import している。

```
ability_manager.py:12, battle.py:26, command_manager.py:15, damage.py:17,
item_manager.py:14, move_executor.py:16, speed_calculator.py:14,
switch_manager.py:15
```
（実際に `grep` で全件確認済み）

前者が動作しているのは、`__init__.py` の3行目が実行された時点で `jpoke.core`
名前空間に `EventContext` が束縛され、その後5行目で `battle.py` 経由で
`turn_controller.py` 等が読み込まれるという**行順に依存した偶然の成立**に
過ぎない。`__init__.py` の import順（例: アルファベット順への並び替え、循環を
避けるための `battle` の先頭移動等）を変更すると
`ImportError: cannot import name 'EventContext' from partially initialized
module 'jpoke.core' (most likely due to a circular import)` で即座に破綻する。
全モジュールで `from .context import ...` の直接 import に統一すべき。

---

## 中程度の指摘

### ISSUE-1: `SwitchManager.run_switch` の docstring が実引数名と不一致

**ファイル**: `src/jpoke/core/switch_manager.py:53-65`

```python
def run_switch(self,
               player: Player,
               new: Pokemon,
               process_events_after_switch: bool = True):
    """ポケモンを交代。
    Args:
        ...
        process_switch_in_events: ON_SWITCH_INイベントを発火する場合True
    """
```

引数名は `process_events_after_switch` だが、docstring の `Args` は
`process_switch_in_events` という別名で説明している。パラメータ名変更時の
更新漏れと見られる。

### ISSUE-2: `Battle.run_switch` と `SwitchManager.run_switch` でパラメータ名が異なる

**ファイル**: `src/jpoke/core/battle.py:589-597`, `src/jpoke/core/switch_manager.py:53-65`

同じ「ON_SWITCH_IN発火の有無」を指すパラメータが、Facade 側では `emit`、
実処理側では `process_events_after_switch`（docstring 上はさらに別名
`process_switch_in_events` — ISSUE-1）と、境界を1つ跨ぐだけで名前が変わる。
位置引数で転送されるため実害はないが、`Battle.run_switch(emit=False)` で
コードベースを検索しても `SwitchManager` 側にヒットせず、調査を混乱させる。
Facade メソッドの引数名は委譲先と一致させるべき。

### ISSUE-3: コアマネージャー4クラスのモジュール docstring が使い回しでコピペされている

**ファイル**: `src/jpoke/core/ailment_manager.py:1-4`, `volatile_manager.py:1-4`,
`query.py:1-4`, `status_manager.py:1-4`

4ファイルとも冒頭が一字一句同じ文面になっている。

```python
"""ポケモンの状態管理（状態異常・揮発状態）を行うモジュール。

Pokemonクラスから状態管理ロジックを分離し、Battleクラスに集約する。
"""
```

`ailment_manager.py`/`volatile_manager.py` は文面通りだが、`query.py`
（読み取り専用クエリ集）と `status_manager.py`（HP・ランク変更）は実際の
役割と一致しておらず、コピー&ペーストで書かれたまま個別に書き換えられて
いないことがわかる。各ファイルの実際の責務に合わせて書き直すべき。

### ISSUE-4: 有効/無効切り替え・状態管理系のロジックがマネージャー間で並行実装されている

**ファイル**: `src/jpoke/core/ability_manager.py:128-167`,
`src/jpoke/core/item_manager.py:43-81`,
`src/jpoke/core/ailment_manager.py:49-181`,
`src/jpoke/core/volatile_manager.py:49-172`

`AbilityManager.add_disabled_reason`/`remove_disabled_reason` と
`ItemManager.add_disabled_reason`/`remove_disabled_reason` は、発火する
イベント名以外ほぼ同一の「`was_enabled`/`is_enabled` を比較して有効状態の
変化時のみイベント発火する」という実装になっている。また
`AilmentManager.apply/remove/tick` と `VolatileManager.apply/remove/tick`
も、`apply`＝「重複チェック→`ON_BEFORE_APPLY_*`発火→ハンドラ登録→
`ON_APPLY_*`/`ON_*_START`発火」、`tick`＝「`is_active`チェック→`tick()`→
`count==0`なら`remove()`」という構造がほぼ並行している（`uncurable`等の
細部ルールを除く）。各効果ごとに固有のルールがあるため無理な統合は避ける
べきだが、「有効/無効の反転検知 → イベント発火」「存在チェック→ハンドラ
登録→前後イベント発火」という共通パターンを小さなヘルパー関数として
`GameEffect` 側に切り出せる余地がある。

### ISSUE-5: `Handler` の docstring が存在しない引数 `target_spec` を説明している

**ファイル**: `src/jpoke/core/handler.py:34-43`

`Handler` の実フィールドは `func`/`source`/`subject_spec`/`priority`/`once`/
`skip_subject_check`/`ignored_disable_reasons` のみだが、docstring の
「いかく」の例では「`target_spec="source:foe"`: 効果の対象は...」という、
実装には存在しない引数 `target_spec` を説明している。`subject_spec` の
役割を説明する最重要 docstring が実装と矛盾しており、新規参加者が「効果対象を
指定する別引数がある」と誤解する。実装（`subject_spec` のみで発動条件と
効果対象の関係を説明する形）に合わせて修正すべき。

### ISSUE-6: `subject_spec` の role とコンテキスト型の不一致が検出されずサイレントに無視される

**ファイル**: `src/jpoke/core/event_manager.py:158-166, 187-209`,
`src/jpoke/core/context.py:43-59`, `src/jpoke/types/literals.py:24-32`

```python
# event_manager.py:158-166
def _build_context(self, rh: RegisteredHandler) -> BaseContext:
    mon = self._resolve_subject(rh)
    if rh.handler.side == "foe":
        mon = self.battle.foe(mon)
    role = rh.handler.role
    if role == "target":
        return EventContext(target=mon)
    return EventContext(source=mon)
```

`RoleSpec`（`types/literals.py:27-32`）は `attacker:self`/`defender:self` と
`source:self`/`target:self` を同じ `Literal` に混在させているが、「このイベントは
非攻撃フェーズ用だから `attacker:self` は指定できない」という制約はコード上
どこにも存在しない。非攻撃フェーズのハンドラに誤って `subject_spec="attacker:self"`
を指定するミスは実行時エラーにならず、`_build_context` が無条件で
`EventContext(source=mon)` を組み立てた後、`ctx.resolve_role`（`context.py:43-59`）の
`getattr(self, role, None)` が `EventContext` に存在しない `attacker` 属性を
探そうとして `None` を返し、`_check_handler_validity`（`event_manager.py:187-209`）が
常に不一致と判定して**ハンドラが例外を出さずに永久にスキップされる**という
発見しづらい不具合として現れる。`Handler.__post_init__` や登録時に、イベント
種別（攻撃フェーズか否か）と `role` の整合性を検証するガードの追加を推奨する。

### ISSUE-7: `AttackContext.critical` が主経路では常に `False` のまま残り、急所状態が三系統に分裂している

**ファイル**: `src/jpoke/core/move_executor.py:443-448`,
`src/jpoke/core/damage.py:72-98`, `src/jpoke/handlers/ability.py:491`

`MoveExecutor._execute_hit` は急所判定の結果を `self.critical`
（`MoveExecutor` 自身の属性、443行目）にのみ代入し、`run_move` が使い続ける
`ctx.critical` へは代入しない。`self.battle.roll_damage(...)` →
`self.battle.calc_damages(...)` → `DamageCalculator.calc_damages`
（`damage.py:72-98`）は渡された `critical` 引数で**新規に別の `AttackContext`
インスタンスを生成する**（`damage.py:93-98`）。結果として

- `DamageCalculator` ローカルの `ctx`（`critical` は正しい値）
- `ON_TRY_MOVE`/`ON_HIT`/`ON_MOVE_KO` 等で使われる `run_move` の `ctx`
  （`critical` は常に `False`）
- `MoveExecutor.critical`（インスタンス属性、テスト・一部ハンドラ用）

という3系統に急所情報が分裂している。現在 `ctx.critical` を読むハンドラ
（オーロラベール等）は `DamageCalculator` ローカルの `ctx` を使う
`ON_CALC_DAMAGE_MODIFIER` に登録されているため実害はないが、
`handlers/ability.py:491` は `ctx.critical` ではなく
`battle.move_executor.critical` を直接参照しており、この分裂の実例になって
いる（実際に `grep` で確認済み）。将来 `ON_HIT`/`ON_MOVE_KO` のハンドラが
素朴に `ctx.critical` を参照すると、急所ヒットでも常に `False` を返す
不具合を生む。`run_move` の `ctx` にも一貫して `critical` を設定するか、
フィールドの用途を docstring で明記すべき。

### ISSUE-8: `Battle` が「委譲だけの Facade」から外れ、実体のあるロジックを複数抱えている

**ファイル**: `src/jpoke/core/battle.py:296-315`（`weather_for`）,
`489-513`（`modify_hp`）, `599-618`（`add_event_log`）

`weather_for` は「ばんのうがさ」という特定アイテム名と天候名の集合を
ハードコードして天候無効化を判定しており、他のアイテム効果がすべて
`handlers/item.py` + `data/item.py` のハンドラとして実装されている設計
方針から明確に逸脱している。

```python
# battle.py:309-315
if (
    mon.item.enabled
    and mon.item.name == "ばんのうがさ"
    and self.weather.name in {"はれ", "あめ", "おおひでり", "おおあめ"}
):
    return self.weather_manager.inactive
return self.weather
```

`modify_hp` の割合→固定値変換（`battle.py:507-512`）、`add_event_log` の
`Pokemon` ソースからの payload 自動補完（`battle.py:614-617`）も同様に、
本来 `WeatherManager`/`StatusManager`/`EventLogger` 側に属するべきロジックが
`Battle` 自身に残留している例。他の大多数のメソッド（`run_move`, `run_switch`,
`change_ability` 等）が1行委譲で統一されている中で異質な存在になっている。

### ISSUE-9: `TurnController` が交代処理を「Battle facade 経由」と「SwitchManager 直接アクセス」の二重経路で呼び分けている

**ファイル**: `src/jpoke/core/turn_controller.py:50-52, 163-200, 294-326`

`Battle` は `run_switch` のみを facade メソッドとして公開しているが、
`run_interrupt_switch`/`override_ejectpack_interrupt`/`run_initial_switch`/
`run_faint_switch` には対応する facade メソッドが存在しない。そのため
`TurnController` は `_run_switch_phase` 内で通常交代は
`self.battle.run_switch(...)`（194行目）、割り込み交代は `self._switch`
（`battle.switch_manager` への直接参照プロパティ、50-52行目）経由という
2つの経路を混在させている。「マネージャー間通信は `Battle` を介する」と
いう前提を部分的に崩している。

### ISSUE-10: `PokemonQuery` が `TurnController.action_order` という生の内部属性に直接アクセスしている（ISSUE-9と対になる逆方向のバイパス）

**ファイル**: `src/jpoke/core/query.py:166-180`, `src/jpoke/core/turn_controller.py:29, 202-211`

```python
# query.py:166-172
def is_first_actor(self, player: Player) -> bool | None:
    """このターンで player が先攻かどうかを返す（1vs1想定）。"""
    order = self.battle.turn_controller.action_order
    if not order:
        return None
    index = self.battle.players.index(player)
    return order[0] == index
```

`TurnController.action_order`（`turn_controller.py:29`）は、交代フェーズ・
行動順解決フェーズをまたいで `TurnController` 自身が段階的に構築する
内部作業用リスト（`_run_switch_phase`/`_resolve_action_order` が
`self.action_order.append(...)` で書き込む）であり、公開 API として設計
されたものではない。`PokemonQuery.is_first_actor`/`is_second_actor` は
これを `battle.turn_controller.action_order` という経路で直接読みに
行っており、アクセサメソッド（例: `TurnController.first_actor_index()`）を
経由していない。ISSUE-9 が「`TurnController` が `Battle` を介さず
`SwitchManager` に触れる」という下り方向のバイパスだったのに対し、これは
「`PokemonQuery` が `Battle` を介さず `TurnController` の生データに触れる」
という上り方向のバイパスであり、`Battle` を境界にした「全マネージャー間
通信は `Battle` を介する」という設計方針の一貫性を両側から崩している。
`TurnController` の内部データ構造（現在は player index のリスト）が
将来変わった場合、`query.py` がサイレントに壊れる。

なお同じ `query.py` 内の `resolve_move_category`（152行目）と
`is_super_effective`/`is_not_very_effective`（192, 197行目）も
`self.battle.move_executor.xxx`/`self.battle.damage_calculator.xxx` を
直接呼んでいるが、こちらは公開メソッド呼び出しであり実装詳細の露出は
ないため問題ない。属性への直接アクセスとメソッド呼び出しは区別して扱うべき。

### ISSUE-11: `ON_MODIFY_DURATION` の emit・戻り値展開パターンが3箇所で重複している

**ファイル**: `src/jpoke/core/field_manager.py:173-183`（`ExclusiveFieldManager.apply`）,
`329-354`（`SideFieldManager.apply`）, `src/jpoke/core/query.py:234-250`
（`PokemonQuery.get_volatile_duration`）

```python
# field_manager.py:173-183 と 344-352 の双方に一字一句同じブロックがある
value = self._events.emit(
    Event.ON_MODIFY_DURATION,
    EventContext(source=source),
    [name, count]
)
_, modified_count = value
if modified_count <= 0:
    raise ValueError("フィールドの持続ターン数は1以上でなければなりません。")
```

`PokemonQuery.get_volatile_duration` も同じ「`[name, count]` を
`ON_MODIFY_DURATION` に渡して `_, modified_count` を取り出す」処理を
3つ目のバリエーションとして持つ（こちらはエラーチェックなし）。
「持続ターン数をイベント経由で補正する」という同一の関心事が3箇所に
分散しているため、`BaseFieldManager` あるいは共有ヘルパー関数
（`resolve_duration(events, ctx, name, count) -> int`）に集約すべき。

---

## 過剰設計の観点

### OVER-1: 実体のない7マネージャーに一律の deepcopy セレモニーを課している一方、同じコードベースにすでに軽量な代替パターンが存在する

**ファイル**: `src/jpoke/core/ability_manager.py:25-30`,
`item_manager.py:23-28`, `ailment_manager.py:30-35`,
`volatile_manager.py:30-35`, `status_manager.py:29-34`,
`command_manager.py:24-29`, `query.py:30-35`

以下の7クラスは、`self.battle` 以外に固有の状態を一切持たない
（`__init__` は `self.battle = battle` の1行のみ）。

```python
class AbilityManager:
    def __init__(self, battle: Battle):
        self.battle = battle
```

にもかかわらず、各クラスは次の6行の boilerplate を個別に実装している
（`AbilityManager`/`ItemManager`/`AilmentManager`/`VolatileManager`/
`StatusManager`/`CommandManager`/`PokemonQuery` の7ファイルで文言まで
一字一句同一）。

```python
def __deepcopy__(self, memo):
    cls = self.__class__
    new = cls.__new__(cls)
    memo[id(self)] = new
    fast_copy(self, new, keys_to_deepcopy=[])
    return new

def update_reference(self, battle: Battle):
    self.battle = battle
```

`Battle.__deepcopy__`（`battle.py:154-178`）はこの7クラスすべてを
`fast_copy` の `keys_to_deepcopy` に列挙し、`_update_reference`
（`battle.py:188-207`）でも7クラス全ての `update_reference` を個別に
呼び出している。つまり「新しい状態なしマネージャーを1つ追加する」だけで、
最低4箇所（マネージャー自身の`__deepcopy__`/`update_reference`、
`Battle.__deepcopy__`のリスト、`Battle._update_reference`の呼び出し）を
機械的に増やす必要がある。

一方で、同じコードベースの `core/lethal.py` と `core/observation_builder.py`
は、性質としてはこれらのマネージャーと同じ「`Battle` を受け取って処理する
だけで固有の状態を持たない処理のまとまり」でありながら、**クラスではなく
プレーンなモジュール関数** として実装されている（`calc_lethal(battle, ...)`,
`observation_builder.build(battle, ...)` 等）。この2ファイルには
`__deepcopy__` も `update_reference` も一切登場しない。「インスタンスを
作らずモジュール関数として実装する」という選択肢が同じコードベース内に
既に実例として存在するにもかかわらず、7マネージャーは「`Battle` の属性として
アクセスできる」という利便性のためだけにクラス化され、その代償として
本質的な価値のない deepcopy 儀式を反復している。

これは「クラスにするか関数群にするか」という設計判断そのものが誤って
いるという指摘ではなく、**クラス化を選んだことで発生する固定コスト
（deepcopy protocol 全体の維持）が、7クラス中いずれの場合も効果に
見合っていない**という過剰設計の指摘である。対して `WeatherManager`
等（`ExclusiveFieldManager`/`StackableFieldManager` を継承し `fields`
という実際にコピーすべき状態を持つ）や `SwitchManager`
（`switching_out_mon` という交代処理中のみ有効な一時状態を持つ）、
`TurnController`（`action_order` を持つ）は deepcopy 儀式が実際に
意味を持つ側の好対照例であり、今回の指摘はこれらには当てはまらない。

### OVER-2: `_events` プロパティが12ファイルに複製されているが、定義者自身が使っていないケースがある

**ファイル**: `src/jpoke/core/speed_calculator.py:46-48, 67, 94, 114, 170`,
`src/jpoke/core/command_manager.py`（未定義）

```python
# speed_calculator.py:46-48
@property
def _events(self) -> EventManager:
    return self.battle.events
```

`self.battle.events` を返すだけの1行プロパティが
`turn_controller.py`/`move_executor.py`/`query.py`/`ability_manager.py`/
`switch_manager.py`/`status_manager.py`/`volatile_manager.py`/
`speed_calculator.py`/`ailment_manager.py`/`item_manager.py`/`damage.py`/
`field_manager.py` の12ファイルに、実装内容が全く同一のまま複製されている
（`grep`で12件確認済み。共有 mixin や `Battle` 側のヘルパーとしては
まとめられていない）。

ところが `SpeedCalculator` 自身は、この `_events` プロパティを定義した
直後の全メソッド（`calc_effective_speed`/`calc_speed_order_key`/
`calc_move_priority`/`resolve_action_order`、67, 94, 114, 170行目）で
一貫して `self.battle.events.emit(...)` と直接記述しており、
**自分で定義した `self._events` を一度も使っていない**。`CommandManager`
に至っては `_events` プロパティ自体を定義せず、素直に
`self.battle.events.emit(...)`（`command_manager.py:92-94`）を使っている。

「`self.battle.events` へのショートカット」という、それ自体はよくある
軽量な間接化が、(a) 12箇所に一字一句コピーされる形で重複し、(b) その
うちの1箇所では定義したこと自体が無駄になっている（デッドコード）、
(c) 別の1箇所ではそもそも導入されていない、という状態は、「抽象化の
コストをかけた割に一貫した価値を生んでいない」過剰設計の典型例と言える。
共有base/mixinに集約するか、素直に `self.battle.events` を都度書くかの
どちらかに統一すべき。

### OVER-3: `BaseContext.derive()` は汎用的な dataclass フィールド複製メソッドだが、呼び出し箇所はコードベース全体で1つしかない

**ファイル**: `src/jpoke/core/context.py:27-37`

```python
def derive(self, **kwargs) -> BaseContext:
    """同型の新しいコンテキストを派生する。kwargs で指定したフィールドを上書きする。"""
    cls = type(self)
    cls_fields = {f.name for f in dataclasses.fields(cls)}
    base = {
        f.name: getattr(self, f.name)
        for f in dataclasses.fields(self)
        if f.name in cls_fields
    }
    base.update(kwargs)
    return cls(**base)
```

`type(self)` を使って動的にサブクラス（`EventContext`/`AttackContext`）を
判定し、`dataclasses.fields` で全フィールドを反射的に収集・再構築する
という、コンテキストの型を問わず汎用的に動作するよう作り込まれた実装だが、
実際に呼ばれている箇所はコードベース全体で `handlers/volatile.py:1229`
の1箇所のみ（`ctx.derive(source=to_mon)`、ドレイン系ハンドラで
ダメージの発生源を差し替えるために使用）。`dataclasses.fields` を2回
呼ぶ・辞書内包表記でフィルタするといった実装コストに対して、恩恵を
受けている呼び出し元が1つしかなく、premature generalization の疑いが
強い。今後複数箇所で使われるようになるまでは、呼び出し元で
`dataclasses.replace(ctx, source=to_mon)` を直接使うか、
`AttackContext` 専用の薄いヘルパーに置き換えて構わない。

### OVER-4（過剰設計ではなく、むしろ妥当な抽象化の例として言及）: `BaseFieldManager`/`ExclusiveFieldManager`/`StackableFieldManager` の2階層は適切な粒度

**ファイル**: `src/jpoke/core/field_manager.py:22-260`

OVER-1〜3 とは対照的に、`field_manager.py` の
`BaseFieldManager[T]`（`tick_down`/`_activate_field`/`_deactivate_field`/
deepcopy を共通化）→ `ExclusiveFieldManager`（天候・地形の排他上書き）/
`StackableFieldManager`（グローバル・サイドの重ね掛け）という2階層の
汎用化は、`WeatherManager`/`TerrainManager`/`GlobalFieldManager`/
`SideFieldManager` の4つの具象マネージャーが実際に
`_activate_field`/`_deactivate_field`/ログ出力/イベント発火のロジックを
共有しており、抽象化のコストに見合ったコード削減が実現できている。
OVER-1 で指摘した「7マネージャーへの一律 deepcopy 儀式」とは異なり、
ここでの `Generic[T]` の導入は妥当な設計判断であり、過剰設計ではない。

---

## 軽微な指摘

### MINOR-1: `SpeedCalculator.resolve_action_order` の末尾に無意味な分岐が残っている

**ファイル**: `src/jpoke/core/speed_calculator.py:206-211`

```python
elif len(actives) == 1:
    # 1匹の場合はそのままソート処理をスキップ
    pass
else:
    # 0匹の場合は空リストを返す
    pass

return actives
```

`if len(actives) > 1:` 分岐だけで完結する処理であり、`elif`/`else` は
何もしない（コメントの説明があるだけの）分岐。可読性のためにも削除して良い。

### MINOR-2: `ExclusiveFieldManager.apply` と `SideFieldManager.apply` の `ON_MODIFY_DURATION` 処理が丸ごと重複（ISSUE-11参照）

**ファイル**: `src/jpoke/core/field_manager.py:173-183, 344-354`

エラーメッセージまで一字一句同一の6行ブロックが2クラスに重複している。
（3箇所目の `PokemonQuery.get_volatile_duration` を含めた対応方針は
ISSUE-11 にまとめて記載。）

### MINOR-3: `PlayerState` にモジュール docstring が無い

**ファイル**: `src/jpoke/core/player_state.py:1`

他の core モジュールは冒頭にモジュール docstring を持つ規約だが、この
ファイルのみ `from __future__ import annotations` から始まり欠落している。
クラス自身の docstring（`"""対戦中のプレイヤー状態。"""`）はあるが、
モジュールレベルのものは存在しない。

### MINOR-4: `EventLog._get_base_text` に「ログデータモデル」と「日本語テキストレンダリング」の責務が混在

**ファイル**: `src/jpoke/core/event_logger.py:83-232`

`frozen dataclass` である `EventLog` の中に `LogCode` 全種を網羅する
140行超の `match` 文が実装され、日本語表示テキストへの変換ロジックが
同居している。`LogCode` 追加時に対応するcaseを書き忘れると
`case _: raise ValueError(...)`（232行目）で実行時に落ちる。「記録」と
「レンダリング」を別クラス（例: `LogRenderer`）に分離すべき。

### MINOR-5: `MoveExecutor.move_category`/`move_power` が書き込み専用のデッドコードになっている

**ファイル**: `src/jpoke/core/move_executor.py:47-70, 270, 403`

`accuracy`/`action_success`/`move_success`/`move_applied`/`move_missed`/
`move_type`/`critical_rank`/`critical` は `__init__`（52-59行目）で宣言され
`reset_monitoring_flags()`（61-70行目）でリセットされる「監視用フラグ」だが、
同じ目的で追加された `move_category`（270行目）と `move_power`（403行目）
だけは `__init__` 未宣言・`reset_monitoring_flags()` 対象外・代入以外の
参照がコードベース中に一件も無い。他の監視用フラグと扱いを揃えるか、
使われていないなら削除すべき。

---

## 総評

`core/` の全体アーキテクチャ（`Battle` Facade + 専門マネージャー群、
`Handler`/`EventManager` によるイベント駆動、`GameEffect` との連携）は
一貫性が高く、CLAUDE.md の設計規約にも沿っている。既存レビュー
（`architecture_review.md`）で core/ に関連して指摘されていた内容
（docstring/引数名のドリフト、id() キー辞書、import順依存の循環、
Facade バイパス、`critical` の三系統分裂等）は、今回すべて実装を
再確認した上で今も有効であることを確認した。

新規に踏み込んだ「過剰設計」の観点では、単発の premature generalization
（`BaseContext.derive()`）よりも、**「実体を持たないマネージャーにまで
画一的な deepcopy protocol を課している」構造的なパターン（OVER-1）**が
最も価値のある発見だった。これは同じコードベース内に「クラス化せず
モジュール関数で済ませる」という軽量な代替（`lethal.py`,
`observation_builder.py`）が既に存在することで対比が際立っており、
次にマネージャーを追加する際の判断基準（「固有の状態を持つか」を
クラス化の要否の基準にする）を明文化する価値がある。あわせて、
`_events` ショートカットプロパティの重複とその不使用（OVER-2）は、
「一貫していない小さな抽象化は無いほうがまし」という反面教師として
分かりやすい実例である。

内部実装の隠蔽の観点では、`TurnController`→`SwitchManager`（ISSUE-9、
既知）に加えて `PokemonQuery`→`TurnController.action_order`
（ISSUE-10、新規）という逆方向のバイパスも見つかり、「マネージャー間
通信は `Battle` を介する」という設計方針が両側から部分的に崩れている
ことが分かった。`TurnController` に `first_actor_index()` のような
アクセサを設け、`Battle` あるいは `TurnController` 自身を通じて
公開する形に揃えることを推奨する。
