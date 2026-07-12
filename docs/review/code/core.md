# コードレビュー — core/

日付: 2026-07-12（初版2026-07-05、本改訂で全面再検証・命名観点を追加）
対象: `src/jpoke/core/` 全25ファイル（`__pycache__` を除く、約6,900行）
（`__init__.py`, `battle.py`, `turn_controller.py`, `move_executor.py`,
`command_manager.py`, `event_manager.py`, `handler.py`, `context.py`, `damage.py`,
`event_logger.py`, `log_payload.py`, `field_manager.py`, `player.py`, `player_state.py`,
`replay.py`, `ability_manager.py`, `ailment_manager.py`, `item_manager.py`,
`status_manager.py`, `switch_manager.py`, `volatile_manager.py`, `query.py`,
`speed_calculator.py`, `observation_builder.py`, `lethal.py`)
観点: (1) 前回レビュー（2026-07-05）指摘の再検証、(2) 変数・関数・クラス・メソッド名の
一貫性と妥当性（新規重点観点）

`git log --since=2026-07-05 -- src/jpoke/core` で確認した通り、前回レビュー以降
`battle.py`/`player.py`/`lethal.py`/`observation_builder.py` を中心に活発な変更が入り、
`log_payload.py`・`replay.py` の2ファイルが新規追加された（`event_logger.py` からの
Payload分離、コマンド記録によるリプレイ再現機能の追加）。今回はこの2ファイルを含む
全25ファイルを実際に全文読み直した。

---

## 総論

`core/` は `Battle` を Facade とし、`TurnController`/`MoveExecutor`/`DamageCalculator`/
`SwitchManager`/`SpeedCalculator`/`CommandManager`/`AbilityManager`/`ItemManager`/
`AilmentManager`/`VolatileManager`/`StatusManager`/`PokemonQuery`/
`WeatherManager`・`TerrainManager`・`GlobalFieldManager`・`SideFieldManager` という
15種のマネージャーに処理を委譲する構成は前回から変わっていない。前回指摘した
アーキテクチャの一貫性・設計規約の遵守という評価は今回も概ね維持される。

今回の再検証で最も大きな進展は **CRIT-3（`__init__.py` の import 順依存の循環
import）が実質的に解消されていたこと** である。全ファイルの `EventContext`/
`AttackContext`/`Battle` 等の実行時 import が `from .context import ...` の
ような直接サブモジュール import に統一されており、`jpoke.core` パッケージ経由の
import は `TYPE_CHECKING` ブロック内（型チェック専用）にしか残っていないことを
`grep` で全件確認した。一方で `MINOR-5`（`move_category`/`move_power` の
監視フラグ扱い漏れ）も `MoveExecutor.__init__`/`reset_monitoring_flags()` の
更新により解消されている。詳細は「解消済み・部分的に解消した指摘」を参照。

今回新たに、既存観点の枠内で2件の実害あるバグ相当の指摘を発見した。

1. **`AilmentManager.apply()` の `ctx` 引数が完全な no-op**（CRIT-4、新規）。
   `handlers/` 側の15箇所以上が意図的に `ctx=ctx`（実際の `AttackContext`）を
   渡しているにもかかわらず、`apply()` 内部の分岐は渡された `ctx` の値を
   一切使わず、常に同一の `EventContext(source=..., target=...)` を組み立てる。
2. **`Battle.set_ailment()` の docstring が実装と矛盾する**（CRIT-5、新規）。
   「特性・タイプ等による無効化判定は行わない」と明記しているが、内部で呼ぶ
   `AilmentManager.apply(..., overwrite=True)` は実際にはタイプ免疫チェックと
   `ON_BEFORE_APPLY_AILMENT`（特性による無効化）を素通りせず適用してしまう。

命名観点では、以下の3点が特に価値のある発見だった。

1. **「対象ポケモン」を指す引数名が `mon` と `target` の2系統に割れており、
   `ItemManager` 単体の中でさえ混在している**（命名-1）。
2. **「基礎値を出してイベントで補正する」という同一パターンの関数群が、
   ファイルによって `calc_` と `resolve_` の異なる接頭辞を使っている**
   （命名-2）。`ON_MODIFY_*` 系イベントを発火するのに `calc_` を使う関数と
   `resolve_` を使う関数が両方存在し、接頭辞とイベント種別の対応関係がない。
3. **`Battle` Facade のマネージャーごとのカバレッジが非対称**（命名-7、
   中程度の指摘としても ISSUE-12 に計上）。`AbilityManager` の
   `add_disabled_reason`/`remove_disabled_reason` は
   `Battle.add_ability_disabled_reason` 等として公開されているが、
   全く同型の `ItemManager.add_disabled_reason`/`remove_disabled_reason`
   および `gain_item`/`remove_item`/`take_item`/`swap_items` には対応する
   Facade メソッドが1つも存在しない。CLAUDE.md 自身が定める「外部APIは
   `Battle` の公開メソッドを入口にする」という方針をアイテム操作だけが
   満たしていない。

---

## 解消済み・部分的に解消した指摘

- **CRIT-3（解消済み）**: `core/__init__.py` の import 順依存の循環 import。
  全ファイルが `.context` 等への直接サブモジュール import に統一され、
  `jpoke.core` パッケージ経由の import は `TYPE_CHECKING` 内のみになった。
  詳細は下記「CRIT-3」の節を参照（記録として残す）。
- **MINOR-5（解消済み）**: `MoveExecutor.move_category`/`move_power` が
  他の監視用フラグと同様に `__init__` で宣言され `reset_monitoring_flags()`
  でリセットされるようになった（`move_executor.py:60-61, 77-78`）。
- **OVER-1（部分的に解消）**: `Battle._deepcopy_keys()`/`_update_reference()`
  が `hasattr(value, "update_reference")` による自動検出方式に変わり
  （`battle.py:245-261, 301-314`）、新しい「実体のない」マネージャーを
  追加した際に `Battle` 側を手動更新する必要はなくなった。ただし
  マネージャー自身が `__deepcopy__`/`update_reference` の6行を個別に
  実装し続ける構造は変わっていない。詳細は OVER-1 の節を参照。
- **MINOR-4（部分的に解消）**: `Payload` 系 dataclass 群が `log_payload.py`
  に分離され、「ログデータモデル」の責務は `event_logger.py` から抜けた。
  ただし `EventLog._get_base_text()`（140行超の `match` 文）は
  引き続き `event_logger.py` の `frozen dataclass` 内に残っており、
  「日本語テキストレンダリング」の責務混在そのものは解消していない。

---

## 重大な指摘

### CRIT-1（既存）: `core/observation_builder.py:13` の `OBSERVED_MOVE_INDEXES` がモジュールグローバル辞書

```python
# observation_builder.py:13
OBSERVED_MOVE_INDEXES: dict[Pokemon, dict[int, int]] = {}

def _mask(battle: Battle, player: Player):
    global OBSERVED_MOVE_INDEXES
    OBSERVED_MOVE_INDEXES = {}
    ...
```

`_mask()` 開始時に `global` 文で丸ごと再代入してリセットする設計は前回から
変わっていない（`observation_builder.py:55-56`）。`_mask_move()`
（127-147行目）で書き込み、`_mask_command()`（150-199行目）で読み出す、
という「同一 `build()` 呼び出し内で閉じた一時状態」を、わざわざモジュール
グローバルとして持ち回している。

`build()` の呼び出しが同期的に完結する限り実害はないが、`Battle.copy_depth`
が示す通りネストしたコピー・観測構築を行う設計であるため、将来「観測構築中に
さらに観測構築を行う」再入が発生した場合に一方の `_mask()` 呼び出しが
もう一方の状態を破壊する。`_mask()`/`_mask_pokemon()`/`_mask_command()` の
引数として辞書を明示的に引き回す（ローカル変数化する）べき。

### CRIT-2（既存、悪化）: `Battle` クラスの docstring `Attributes` が実装とさらに乖離している

**ファイル**: `src/jpoke/core/battle.py:106-127`（docstring）vs
`130-230`（`__init__`実装）

前回指摘時点より `__init__` の属性数がさらに増えており、docstring との
乖離幅は拡大している。docstring は19個の属性（`players`, `seed`, `turn`,
`winner`, `events`, `logger`, `random`, `decision_random`,
`damage_calculator`, `move_executor`, `switch_manager`, `turn_controller`,
`speed_calculator`, `weather_manager`, `terrain_manager`, `global_manager`,
`side_managers`, `option`, `test_option`）を列挙しているが、実際の
`__init__` にはそこに含まれない次の公開/準公開属性が存在する（`_`始まりの
純内部キャッシュを除く）。

```
n_selected, copy_depth, observer, phase, last_used_move_name,
round_used_turn, echoed_voice_power, echoed_voice_last_turn,
fusion_bolt_used_turn, fusion_flare_used_turn, command_log,
ailment_manager, volatile_manager, query, status_manager,
command_manager, ability_manager, item_manager
```

さらに docstring の `logger` は実装の属性名 `event_logger`
（`battle.py:201`）と依然として一致しない。

```python
# docstring（battle.py:112）
logger: バトルログ記録システム
# 実装（battle.py:201）
self.event_logger = EventLogger()
```

`decision_random` は前回から docstring に追加され改善しているが、それ以外の
7マネージャー（`ailment_manager` 以降）と `copy_depth`/`observer`/`phase` 等の
挙動フラグ群は依然として未記載。`Battle` はコードベース全体で最も参照頻度が
高いクラスであり、`__init__` の実属性に合わせて総ざらいで更新すべき。

### CRIT-3（既存 → 解消済み・記録として維持）: `core/__init__.py` の import 順依存パターンは解消された

**ファイル**: `src/jpoke/core/__init__.py:1-12`

前回は次の6ファイルが `from jpoke.core import EventContext` というパッケージ
経由の実行時 import を使っており、`__init__.py` の行順を変えると
`ImportError` で破綻する状態だった。

```
ailment_manager.py, field_manager.py, query.py,
status_manager.py, turn_controller.py, volatile_manager.py
```

今回全ファイルを `grep` で確認した結果、これら6ファイルを含む `core/` 内
全ファイルが `.context` 等への直接サブモジュール import
（例: `turn_controller.py:11 from .context import EventContext`）に
統一されており、`from jpoke.core import ...` の形での import は
以下のように **全て `if TYPE_CHECKING:` ブロック内** に限定されていた。

```python
# 例: move_executor.py:6-8
from typing import TYPE_CHECKING, cast
if TYPE_CHECKING:
    from jpoke.core import Battle, EventManager
```

`TYPE_CHECKING` ブロックは実行時に評価されないため、`__init__.py` の
import順（アルファベット順への並び替え等）を変更しても実行時エラーには
ならない。前回指摘した「行順に依存した偶然の成立」というリスクは解消されて
いる。今後リグレッションを防ぐため、`core/` 新規ファイルでも同じ規約
（実行時は直接サブモジュール import、型ヒントのみ `jpoke.core` 経由）を
維持することを推奨する。

### CRIT-4（新規）: `AilmentManager.apply()` の `ctx` 引数が完全に no-op になっている

**ファイル**: `src/jpoke/core/ailment_manager.py:51-104`

```python
def apply(self,
          target: Pokemon,
          name: AilmentName,
          count: int | None = None,
          source: Pokemon | None = None,
          overwrite: bool = False,
          ctx: BaseContext | None = None) -> bool:
    ...
    # ON_BEFORE_APPLY_AILMENT イベントを発火して特性などによる無効化をチェック
    if ctx is not None:
        apply_ctx = EventContext(source=source, target=target)
    else:
        apply_ctx = EventContext(target=target, source=source)

    resolved_name = self._events.emit(Event.ON_BEFORE_APPLY_AILMENT, apply_ctx, name)
```

`if ctx is not None:` と `else:` の両分岐が **キーワード引数の順序が違うだけの
全く同じ `EventContext(source=source, target=target)` を生成している**。
つまり呼び出し元が渡した `ctx`（`AttackContext` 等、`move`/`critical`/
`hit_index` といった攻撃フェーズ固有の情報を持つ実際のコンテキスト）は
一度も `apply_ctx` に反映されず、`ON_BEFORE_APPLY_AILMENT` ハンドラは常に
`source`/`target` だけを持つ最小限の `EventContext` しか受け取らない。

`grep` で確認した限り、`handlers/ability.py`・`handlers/move_attack.py`・
`handlers/move_status.py`・`handlers/volatile.py` など少なくとも15箇所が
`ctx=ctx` を明示的に渡している（例:
`handlers/move_attack.py:2107 battle.ailment_manager.apply(ctx.defender, "まひ", source=ctx.attacker, ctx=ctx)`）。
これらの呼び出し元は `ctx` を渡すことで攻撃コンテキストの情報が
`ON_BEFORE_APPLY_AILMENT` ハンドラに伝わることを期待していると考えられるが、
実際には一切伝わらない。`ctx` パラメータを実際に使う実装（例えば
`apply_ctx = ctx.derive(...)` のような形、あるいは少なくとも
`EventContext(source=source, target=target, hp_change_reason=ctx.hp_change_reason)`
のように `ctx` から何らかの値を引き継ぐ形）に修正するか、現時点で
無意味であることが確定しているなら `ctx` パラメータ自体を削除し、
呼び出し元15箇所の `ctx=ctx` も削除すべき。どちらであるかは
`handlers/` 側の `ON_BEFORE_APPLY_AILMENT` ハンドラが `AttackContext` 固有の
フィールドを要求しているかどうかで判断する必要があり、次回 `handlers/`
レビュー時に合わせて確認することを推奨する。

### CRIT-5（新規）: `Battle.set_ailment()` の docstring が実装と矛盾する

**ファイル**: `src/jpoke/core/battle.py:752-766`,
`src/jpoke/core/ailment_manager.py:80-104`

```python
# battle.py:752-766
def set_ailment(self, target: Pokemon, name: AilmentName, count: int | None = None) -> bool:
    """状態異常を直接付与する（シナリオ構築・ダメージ計算検証用）。

    既存の状態異常があれば上書きする。特性・タイプ等による無効化判定は行わない
    （examples/スクリプトから素直に状態を作るための薄いラッパーのため）。
    ...
    """
    return self.ailment_manager.apply(target, name, count=count, overwrite=True)
```

docstring は「特性・タイプ等による無効化判定は行わない」と明言しているが、
実際に呼んでいる `AilmentManager.apply()`（`ailment_manager.py:80-104`）は
`overwrite=True` を渡しても以下の判定を素通りしない。

```python
# ailment_manager.py:91-104
if not self._can_apply_by_type(name, target, source):   # タイプ免疫チェック
    return False
...
resolved_name = self._events.emit(Event.ON_BEFORE_APPLY_AILMENT, apply_ctx, name)  # 特性等の無効化ハンドラ
if not resolved_name:
    return False
```

`_can_apply_by_type`（同ファイル122-141行目）はほのおタイプへの「やけど」
付与などを実際にブロックし、`ON_BEFORE_APPLY_AILMENT` は活性化中の特性
ハンドラ（不眠等）が登録されていれば実際に発火してブロックしうる。つまり
`battle.set_ailment(ほのおタイプのポケモン, "やけど")` は docstring の
約束に反して **黙って `False` を返し、状態異常が付与されない**。

このメソッドは「examples/スクリプトから素直に状態を作るための薄いラッパー」
という位置付けで、テスト・シナリオ構築時に呼び出し側が「必ず付与される」と
信じて後続コードを書く可能性が高い。ドキュメント通りの動作
（無条件で状態異常を設定する）に実装を合わせるか、ドキュメントを実装
（特性・タイプ判定は依然として行う）に合わせるかのいずれかで整合を取る
べき。`set_weather`/`set_terrain`（767-790行目）には同様の「判定を行わない」
という記載はなく、この矛盾は `set_ailment` のみに存在する。

---

## 中程度の指摘

### ISSUE-1（既存）: `SwitchManager.run_switch` の docstring が実引数名と不一致

**ファイル**: `src/jpoke/core/switch_manager.py:54-66`

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
`process_switch_in_events` という別名で説明している。前回から変化なし。

### ISSUE-2（既存）: `Battle.run_switch` と `SwitchManager.run_switch` でパラメータ名が異なる

**ファイル**: `src/jpoke/core/battle.py:866-874`,
`src/jpoke/core/switch_manager.py:54-66`

同じ「ON_SWITCH_IN発火の有無」を指すパラメータが、Facade 側では `emit`
（`battle.py:866`）、実処理側では `process_events_after_switch`
（docstring 上はさらに別名 `process_switch_in_events` — ISSUE-1）と、
境界を1つ跨ぐだけで名前が変わる構造は変化なし。

### ISSUE-3（既存）: コアマネージャー4クラスのモジュール docstring が使い回しでコピペされている

**ファイル**: `src/jpoke/core/ailment_manager.py:1-4`, `volatile_manager.py:1-4`,
`query.py:1-4`, `status_manager.py:1-4`

4ファイルとも冒頭が一字一句同じ文面のまま変化していない。

```python
"""ポケモンの状態管理（状態異常・揮発状態）を行うモジュール。

Pokemonクラスから状態管理ロジックを分離し、Battleクラスに集約する。
"""
```

`ailment_manager.py`/`volatile_manager.py` は文面通りだが、`query.py`
（読み取り専用クエリ集）と `status_manager.py`（HP・ランク変更）は実際の
役割と一致していない。特に `query.py` は **クラス自身の docstring**
（`query.py:19-25`「ポケモン個体に関する読み取り専用クエリをまとめた
クラス。状態を変更せず、イベントを通じて現在の判定結果を返す。」）が
正しく役割を説明しているのに、その4行上のモジュール docstring だけが
コピペのまま取り残されているという対比が今回あらためて確認できた。
各ファイルの実際の責務に合わせて書き直すべき。

### ISSUE-4（既存）: 有効/無効切り替え・状態管理系のロジックがマネージャー間で並行実装されている

**ファイル**: `src/jpoke/core/ability_manager.py:128-167`,
`src/jpoke/core/item_manager.py:45-83`,
`src/jpoke/core/ailment_manager.py:51-183`,
`src/jpoke/core/volatile_manager.py:51-174`

`AbilityManager.add_disabled_reason`/`remove_disabled_reason` と
`ItemManager.add_disabled_reason`/`remove_disabled_reason` は、発火する
イベント名以外ほぼ同一の「`was_enabled`/`is_enabled` を比較して有効状態の
変化時のみイベント発火する」という実装のまま。`AilmentManager.apply/remove/tick`
と `VolatileManager.apply/remove/tick` も同様の並行構造を維持している。
各効果ごとに固有のルールがあるため無理な統合は避けるべきだが、「有効/無効の
反転検知 → イベント発火」「存在チェック→ハンドラ登録→前後イベント発火」と
いう共通パターンを小さなヘルパー関数として切り出せる余地は変わらず残る。

### ISSUE-5（既存）: `Handler` の docstring が存在しない引数 `target_spec` を説明している

**ファイル**: `src/jpoke/core/handler.py:34-43`

`Handler` の実フィールドは `func`/`source`/`subject_spec`/`priority`/`once`/
`skip_subject_check`/`ignored_disable_reasons` のみだが、docstring の
「いかく」の例では実装に存在しない引数 `target_spec="source:foe"` を
説明したままになっている（`handler.py:42`）。

### ISSUE-6（既存）: `subject_spec` の role とコンテキスト型の不一致が検出されずサイレントに無視される

**ファイル**: `src/jpoke/core/event_manager.py:156-165, 187-212`,
`src/jpoke/core/context.py:43-63`, `src/jpoke/types/literals.py`

`Handler.__post_init__`（`handler.py:54-68`）は `subject_spec` の
`role:side` 形式と役割名（source/target/attacker/defender）の妥当性しか
検証せず、「このイベントは非攻撃フェーズ用だから `attacker:self` は
指定できない」という、イベント種別との整合性チェックは今回確認した
時点でも存在しない。`context.py:58-60` の
`getattr(self, role, None)` が `EventContext` に無い `attacker` 属性を
探して `None` を返し、`_check_handler_validity` が常に不一致と判定して
ハンドラが例外なく永久にスキップされる問題は変わらず有効。

### ISSUE-7（既存）: `AttackContext.critical` が主経路では常に `False` のまま残り、急所状態が三系統に分裂している

**ファイル**: `src/jpoke/core/move_executor.py:479-499`,
`src/jpoke/core/damage.py:73-99`, `src/jpoke/handlers/ability.py:544`

`MoveExecutor._execute_hit`（`move_executor.py:491`）は急所判定の結果を
`self.critical`（`MoveExecutor` 自身の属性）にのみ代入し、`run_move` が
使い続ける `ctx.critical`（`AttackContext.critical`、`context.py:102`）へは
代入しない。`DamageCalculator.calc_damages`（`damage.py:94-99`）は渡された
`critical` 引数で**新規に別の `AttackContext` インスタンスを生成する**。
結果として (1) `DamageCalculator` ローカルの `ctx`、(2) `run_move` の
`ctx`（常に `False`）、(3) `MoveExecutor.critical` インスタンス属性、という
3系統の分裂は変わらず存在する。`handlers/ability.py:544`
（`if not battle.move_executor.critical:`）は依然としてこの分裂を前提に
`MoveExecutor.critical` を直接参照しており、実例として残っている。

### ISSUE-8（既存）: `Battle` が「委譲だけの Facade」から外れ、実体のあるロジックを複数抱えている

**ファイル**: `src/jpoke/core/battle.py:458-472`（`weather_for`）,
`704-735`（`modify_hp`）, `876-893`（`add_event_log`）

`weather_for` は「ばんのうがさ」という特定アイテム名と天候名の集合を
ハードコードして天候無効化を判定しており（`battle.py:470`
`mon.item.name == "ばんのうがさ"`）、他のアイテム効果がすべて
`handlers/item.py` + `data/item.py` のハンドラとして実装されている設計
方針から明確に逸脱したままになっている。`modify_hp` の割合→固定値変換、
`add_event_log` の `Pokemon` ソースからの payload 自動補完も同様に
`Battle` 自身に残留している。

### ISSUE-9（既存）: `TurnController` が交代処理を「Battle facade 経由」と「SwitchManager 直接アクセス」の二重経路で呼び分けている

**ファイル**: `src/jpoke/core/turn_controller.py:50-52, 166-203, 320-337`

`Battle` は `run_switch` のみを facade メソッドとして公開しているが、
`run_interrupt_switch`/`override_ejectpack_interrupt`/`run_initial_switch`/
`run_faint_switch` には対応する facade メソッドが存在しない。そのため
`TurnController` は通常交代は `self.battle.run_switch(...)`
（`turn_controller.py:197`）、割り込み交代は `self._switch`
（`battle.switch_manager` への直接参照プロパティ、`turn_controller.py:50-52`）
経由という2つの経路を混在させたままになっている。

### ISSUE-10（既存）: `PokemonQuery` が `TurnController.action_order` という生の内部属性に直接アクセスしている

**ファイル**: `src/jpoke/core/query.py:180-194`,
`src/jpoke/core/turn_controller.py:29`

```python
# query.py:180-186
def is_first_actor(self, player: Player) -> bool | None:
    """このターンで player が先攻かどうかを返す（1vs1想定）。"""
    order = self.battle.turn_controller.action_order
    if not order:
        return None
    index = self.battle.players.index(player)
    return order[0] == index
```

`is_second_actor`（`query.py:188-194`）も同様に
`self.battle.turn_controller.action_order` を直接読みに行く構造は変わって
いない。ISSUE-9（下り方向のバイパス）と対になる、上り方向のバイパスとして
今も存在する。

### ISSUE-11（既存）: `ON_MODIFY_DURATION` の emit・戻り値展開パターンが3箇所で重複している

**ファイル**: `src/jpoke/core/field_manager.py:176-186`
（`ExclusiveFieldManager.apply`）, `354-362`（`SideFieldManager.apply`）,
`src/jpoke/core/query.py:248-264`（`PokemonQuery.get_volatile_duration`）

```python
value = self._events.emit(
    Event.ON_MODIFY_DURATION,
    EventContext(source=source),
    [name, count]
)
_, modified_count = value
if modified_count <= 0:
    raise ValueError("フィールドの持続ターン数は1以上でなければなりません。")
```

`field_manager.py` の2箇所と `query.py` の1箇所（エラーチェックなし）で
同一パターンが重複している状態は変わらず残っている。

### ISSUE-12（新規）: `Battle` Facade のマネージャー別カバレッジが非対称で、`ItemManager` の変更系メソッドに対応する公開APIが1つも無い

**ファイル**: `src/jpoke/core/battle.py:909-915`（`AbilityManager` 側の
Facade メソッド）, `src/jpoke/core/item_manager.py:45-84, 166-266`

`Battle` は `AbilityManager` の `add_disabled_reason`/`remove_disabled_reason`
を次のように facade 化している。

```python
# battle.py:909-915
def add_ability_disabled_reason(self, mon: Pokemon, reason: AbilityDisabledReason) -> bool:
    """特性の無効化理由を追加する（AbilityManagerへの委譲）。"""
    return self.ability_manager.add_disabled_reason(mon, reason)

def remove_ability_disabled_reason(self, mon: Pokemon, reason: AbilityDisabledReason) -> bool:
    """特性の無効化理由を削除する（AbilityManagerへの委譲）。"""
    return self.ability_manager.remove_disabled_reason(mon, reason)
```

`ItemManager` にも全く同型の `add_disabled_reason`/`remove_disabled_reason`
（`item_manager.py:45-83`）に加えて、外部コードが素直に使いたくなる
`gain_item`/`remove_item`/`take_item`/`swap_items`/`consume_item`
（`item_manager.py:166-266`）が存在するが、`battle.py` 全体を `grep` した
限り、これらいずれに対しても `Battle` 側の公開メソッドが存在しない
（`weather_manager`/`ailment_manager`/`status_manager` 等は
`set_weather`/`set_ailment`/`modify_hp` 等で必ず1つ以上のFacadeメソッドを
持つのに対し、`item_manager` だけが0件）。CLAUDE.md
は「外部 API（テスト・bot・探索コード）は `Battle` の公開メソッドを入口に
する。`battle.<manager>.<method>()` の直呼びは `src/jpoke` 内部実装に
限る」と明記しており、アイテムを付与・剥奪・交換したいテスト/scripts
コードは現状この方針に従うと `battle.item_manager.gain_item(...)` を
直接呼ぶ以外の手段がなく、規約と実態が食い違っている。少なくとも
`gain_item`/`remove_item` 相当のFacadeメソッドの追加を推奨する。

---

## 過剰設計の観点

### OVER-1（既存、部分的に改善）: 実体のない7マネージャーへの deepcopy セレモニーは自動検出化されたが、各マネージャー側の6行ボイラープレートは残存

**ファイル**: `src/jpoke/core/battle.py:232-261, 301-314`（自動検出ロジック）,
`ability_manager.py:25-30`, `item_manager.py:25-30`, `ailment_manager.py:32-37`,
`volatile_manager.py:32-37`, `status_manager.py:30-35`,
`command_manager.py:25-30`, `query.py:30-35`

前回指摘した「新しいマネージャーを1つ追加するたびに `Battle.__deepcopy__` の
リストと `Battle._update_reference` の呼び出しを機械的に増やす必要がある」
という問題は解消された。`Battle._deepcopy_keys()`（`battle.py:245-261`）が
`hasattr(value, "update_reference")` で `update_reference` を持つ属性を
自動検出するようになり、`_update_reference()`（`battle.py:301-314`）も
同様に `vars(self).values()` を走査する形に変わっている。

```python
# battle.py:232-234 のコメントがこの設計意図を明記している
# update_reference を持たないが deepcopy が必要な可変状態。
# マネージャー類は _deepcopy_keys() が自動検出するため、ここに列挙するのは
# 「マネージャーでない可変オブジェクト」のみ。
```

一方で、以下7クラスが `self.battle` 以外に固有の状態を持たないまま
`__deepcopy__`/`update_reference` の6行ボイラープレートを個別に実装し
続けている点は変わっていない。

```python
class AbilityManager:
    def __init__(self, battle: Battle):
        self.battle = battle

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        fast_copy(self, new, keys_to_deepcopy=[])
        return new

    def update_reference(self, battle: Battle):
        self.battle = battle
```

`core/lethal.py` と `core/observation_builder.py` が同じ性質の処理を
プレーンなモジュール関数として実装し、この儀式を一切必要としていない
という対比も前回と変わらず有効。`Battle` 側の負担は解消されたが、
7クラスそれぞれが6行の実質無内容なコードを持つという指摘自体は残る
（`Battle` へのマネージャー追加コストは下がったが、マネージャー自身を
クラス化するコストは変わっていない）。

### OVER-2（既存）: `_events` プロパティが12ファイルに複製されているが、定義者自身が使っていないケースがある

**ファイル**: `src/jpoke/core/speed_calculator.py:46-48, 67-71, 94-98, 114-118, 173`,
`src/jpoke/core/command_manager.py`（未定義）

`self.battle.events` を返すだけの1行プロパティが `turn_controller.py`/
`move_executor.py`/`query.py`/`ability_manager.py`/`switch_manager.py`/
`status_manager.py`/`volatile_manager.py`/`speed_calculator.py`/
`ailment_manager.py`/`item_manager.py`/`damage.py`/`field_manager.py`
の12ファイルに複製されたまま。`SpeedCalculator` 自身は今回確認した
全メソッド（`calc_effective_speed`/`calc_speed_order_key`/
`calc_move_priority`/`resolve_action_order`）で一貫して
`self.battle.events.emit(...)` と直接記述しており、自分で定義した
`self._events` を今も一度も使っていない。`CommandManager` も
`_events` プロパティ自体を定義せず `self.battle.events.emit(...)`
（`command_manager.py:109-111`）を直接使っている。

### OVER-3（既存）: `BaseContext.derive()` は汎用的な dataclass フィールド複製メソッドだが、呼び出し箇所はコードベース全体で1つしかない

**ファイル**: `src/jpoke/core/context.py:27-37`

呼び出し箇所は今回 `grep` で再確認した結果 `handlers/volatile.py:1386`
（`ctx.derive(source=to_mon)`）の1箇所のみで、前回から変わらず
premature generalization の疑いが強い。

### OVER-4（過剰設計ではなく、むしろ妥当な抽象化の例として言及・既存）: `BaseFieldManager`/`ExclusiveFieldManager`/`StackableFieldManager` の2階層は適切な粒度

**ファイル**: `src/jpoke/core/field_manager.py:23-262`

`WeatherManager`/`TerrainManager`/`GlobalFieldManager`/`SideFieldManager`
の4つの具象マネージャーが `_activate_field`/`_deactivate_field`/
ログ出力/イベント発火のロジックを実際に共有しており、抽象化のコストに
見合ったコード削減が実現できているという評価は変わらない。

---

## 軽微な指摘

### MINOR-1（既存）: `SpeedCalculator.resolve_action_order` の末尾に無意味な分岐が残っている

**ファイル**: `src/jpoke/core/speed_calculator.py:209-214`

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
何もしない分岐のまま残っている。

### MINOR-2（既存）: `ExclusiveFieldManager.apply` と `SideFieldManager.apply` の `ON_MODIFY_DURATION` 処理が丸ごと重複（ISSUE-11参照）

**ファイル**: `src/jpoke/core/field_manager.py:176-186, 354-362`

エラーメッセージまで一字一句同一の重複が残っている。対応方針は ISSUE-11
にまとめて記載。

### MINOR-3（既存）: `PlayerState` にモジュール docstring が無い

**ファイル**: `src/jpoke/core/player_state.py:1`

他の core モジュールは冒頭にモジュール docstring を持つ規約だが、この
ファイルのみ `from __future__ import annotations` から始まり欠落した
ままになっている。クラス自身の docstring（`"""対戦中のプレイヤー状態。"""`）
はある。

### MINOR-4（既存、部分的に解消）: `EventLog._get_base_text` に「ログデータモデル」と「日本語テキストレンダリング」の責務が混在

**ファイル**: `src/jpoke/core/event_logger.py:82-238`

`Payload` 系 dataclass 群が `log_payload.py` に分離されたことで
「データモデル」側の責務は `event_logger.py` から抜けたが、`frozen dataclass`
である `EventLog` の中に `LogCode` 全種を網羅する150行超の `match` 文
（`event_logger.py:91-238`）が実装され、日本語表示テキストへの変換ロジックが
同居する構造自体は変わっていない。`LogCode` 追加時に対応する case を
書き忘れると `case _: raise ValueError(...)`（238行目）で実行時に落ちる
リスクも残る。「記録」と「レンダリング」を別クラス（例: `LogRenderer`）に
分離する余地は今も残っている。

### MINOR-5（既存 → 解消済み）: `MoveExecutor.move_category`/`move_power` の監視フラグ扱い漏れ

**ファイル**: `src/jpoke/core/move_executor.py:52-80`

前回は `move_category`/`move_power` が他の監視用フラグ
（`accuracy`/`action_success`/`move_success`/`move_applied`/`move_missed`/
`move_type`/`critical_rank`/`critical`）と異なり `__init__` 未宣言・
`reset_monitoring_flags()` 対象外だったが、現在は次の通り両方とも
宣言・リセットの対象に含まれている。

```python
# move_executor.py:60-61（__init__）
self.move_category: MoveCategory | None = None
self.move_power: int | None = None
# move_executor.py:77-78（reset_monitoring_flags）
self.move_category = None
self.move_power = None
```

指摘は解消済み。

### MINOR-6（新規）: `AttackContext.fainted` フィールドが宣言されているだけで一度も読み書きされていない

**ファイル**: `src/jpoke/core/context.py:103`

```python
@dataclass(eq=False, kw_only=True)
class AttackContext(BaseContext):
    ...
    fainted: bool = False
```

`grep "ctx\.fainted"`（`src/jpoke` 全体）で1件もヒットせず、`fainted` は
デフォルト値のまま一度も代入も参照もされていないデッドフィールドである。
似た役割は `ctx.defender.fainted`（`Pokemon` 側のプロパティ）で実際に
判定されており（`move_executor.py:473, 513, 525`）、`AttackContext.fainted`
自体が使われる想定だったのか、それとも設計変更で不要になったのかが
コードから読み取れない。削除するか、使う予定があるならコメントで意図を
明記すべき。

### MINOR-7（新規）: `Battle.play_out()` と `replay.py:replay_battle()` が「決着まで進める」ループをそれぞれ独自の完了条件で実装している

**ファイル**: `src/jpoke/core/battle.py:659-675`（`play_out`）,
`src/jpoke/core/replay.py:105-127`（`replay_battle`）

```python
# battle.py:673-674
while not self.finished and self.turn < max_turns:
    self.step()
```

```python
# replay.py:124-125
while battle.judge_winner() is None and battle.turn < max_turns:
    battle.step()
```

どちらも「決着がつくかターン上限に達するまで `step()` を繰り返す」という
同一の関心事だが、完了判定に `self.finished` プロパティ（内部で
`judge_winner()` を呼ぶだけ、`battle.py:970-979`）と `judge_winner()`
の直接呼び出しという異なる書き方を使っている。実質的に等価だが、
将来 `finished` の判定ロジックだけが変更された場合に `replay_battle` 側の
判定が追従せず乖離するリスクがある。`replay_battle` 側も
`battle.finished` を使うか、共通のヘルパーに揃えるべき。

---

## 命名の一貫性・妥当性

今回のレビューで新規に追加した観点。`core/` 全25ファイルを横断して
identifier（変数名・引数名・関数名・クラス名・メソッド名）の一貫性を調べた。

### 命名-1（新規）: 「対象ポケモン」を指す引数名が `mon` と `target` の2系統に割れており、`ItemManager` 単体でも混在している

**ファイル**: `src/jpoke/core/ability_manager.py`（全体）,
`src/jpoke/core/item_manager.py`（全体）,
`src/jpoke/core/ailment_manager.py`（全体）,
`src/jpoke/core/volatile_manager.py`（全体）,
`src/jpoke/core/status_manager.py`（全体）

「効果の影響を受けるポケモン」という同一の役割を表す第一引数の名前が、
マネージャーによって次のように割れている。

- `mon` を使う: `AbilityManager.change_ability(mon, ability)`,
  `AbilityManager.swap_ability(mon1, mon2)`,
  `AbilityManager.add_disabled_reason(mon, reason)`,
  `AbilityManager.remove_disabled_reason(mon, reason)`,
  `AbilityManager.is_change_blocked(mon)`
- `target` を使う: `AilmentManager.apply(target, name, ...)`,
  `AilmentManager.remove(target)`, `AilmentManager.tick(target)`,
  `VolatileManager.apply(target, name, ...)`,
  `VolatileManager.remove(target, name)`,
  `StatusManager.modify_hp(target, v, ...)`,
  `StatusManager.modify_stats(target, stats, ...)`

さらに `ItemManager` は **同一クラス内で両方を使い分けている**。

```python
# item_manager.py:45（mon）
def add_disabled_reason(self, mon: Pokemon, reason: ItemDisabledReason) -> bool:
# item_manager.py:65（mon）
def remove_disabled_reason(self, mon: Pokemon, reason: ItemDisabledReason) -> bool:
# item_manager.py:119（mon、プライベートヘルパー）
def _change_item(self, mon: Pokemon, name: ItemName, *, track_loss: bool = True) -> None:
# item_manager.py:166（target）
def gain_item(self, target: Pokemon, name: ItemName) -> bool:
# item_manager.py:182（target）
def remove_item(self, target: Pokemon, source: Pokemon | None = None, *, track_loss: bool = True) -> bool:
# item_manager.py:244（target）
def take_item(self, target: Pokemon, *, ignore_sticky_hold: bool = False) -> bool:
# item_manager.py:268（mon）
def consume_item(self, mon: Pokemon, *, track_loss: bool = True) -> bool:
# item_manager.py:286（mon）
def force_trigger_berry(self, mon: Pokemon, *, track_loss: bool = True) -> None:
```

`add_disabled_reason`/`remove_disabled_reason`/`consume_item`/
`force_trigger_berry`/`_change_item` は `mon`、`gain_item`/`remove_item`/
`take_item` は `target` と、同じファイル内で交互に切り替わっている。
どちらの語を「主語となるポケモン」の標準名にするか（`AbilityManager` は
`mon` に統一済みなのでそちらに寄せるのが自然）を決めてプロジェクト全体で
揃えるべき。

### 命名-2（新規）: 「基礎値を出してイベントで補正する」パターンの関数群で `calc_` と `resolve_` の接頭辞が入り乱れている

**ファイル**: `src/jpoke/core/speed_calculator.py:50-118`,
`src/jpoke/core/move_executor.py:549-587`,
`src/jpoke/core/damage.py:73-395`,
`src/jpoke/core/query.py:156-166`

「ベースとなる値を求めた上で `events.emit(ON_MODIFY_*/ON_CALC_*, ...)` を
呼んで補正後の値を返す」という同一構造の関数が、ファイルによって異なる
接頭辞を使っている。特に次の2つは接頭辞とイベント種別の対応関係が
逆転しており直接比較できる好例になっている。

```python
# speed_calculator.py:100-118: ON_MODIFY_* イベントなのに calc_ 接頭辞
def calc_move_priority(self, attacker: Pokemon, move: Move) -> int:
    base_priority = move.priority if move else 0
    return self.battle.events.emit(
        DomainEvent.ON_MODIFY_MOVE_PRIORITY, ..., base_priority
    )

# move_executor.py:549-567: 同じ ON_MODIFY_* イベントだが resolve_ 接頭辞
def resolve_move_type(self, attacker: Pokemon, move: Move) -> Type:
    return self._events.emit(
        Event.ON_MODIFY_MOVE_TYPE, ..., value=move.data.type,
    )
```

`calc_` 系: `SpeedCalculator.calc_effective_speed`/`calc_speed_order_key`/
`calc_move_priority`、`DamageCalculator.calc_damages`/
`_calc_final_power`/`_calc_final_attack`/`_calc_final_defense`/
`calc_def_type_modifier`、`Battle.calc_damages`/`calc_lethal`。

`resolve_` 系: `MoveExecutor.resolve_move_type`/`resolve_move_category`、
`PokemonQuery.resolve_move_category`（`MoveExecutor` への1行委譲）、
`SpeedCalculator.resolve_speed_order`/`resolve_action_order`、
`CommandManager.resolve_command`/`resolve_move_from_command`、
`Battle.resolve_secondary_chance`/`resolve_command`/`resolve_speed_order`、
`Handler.context.resolve_role`。

両者は「イベント発火を経て最終値を確定する」という共通の意味構造を持つが、
使い分けの基準がコードから読み取れない。少なくとも新規追加時にどちらを
使うべきかの指針（例: 「単なる数値計算の補正 = `calc_`」「複数の候補・
選択肢から1つに決定する処理 = `resolve_`」）を決め、既存の逆転ケース
（`calc_move_priority` と `resolve_move_type`）のどちらかに寄せることを
推奨する。

### 命名-3（新規）: デバッグ/監視用フラグのリセットメソッド名が2系統存在する

**ファイル**: `src/jpoke/core/move_executor.py:69-80`,
`src/jpoke/core/damage.py:40-52`

「計算開始前にデバッグ用の属性群を `None` に戻す」という同一目的の
メソッドが、クラスによって異なる名前になっている。

```python
# move_executor.py:69
def reset_monitoring_flags(self):
    """技実行のモニタリング用フラグをリセットする。"""

# damage.py:40
def reset_monitor_attributes(self):
    """ダメージ計算のモニタリング用属性をリセットする。"""
```

「flags」と「attributes」という語の違いに実質的な意味はなく（両方とも
`int | None`/`bool | None` 型の属性が混在している）、単なる命名の揺れ。
どちらかに統一すべき。

### 命名-4（新規）: フィールド効果の開始/終了を表す動詞が管理者によって `apply`/`remove` と `activate`/`deactivate` の2系統に分かれている

**ファイル**: `src/jpoke/core/field_manager.py:90-115, 157-256`

`BaseFieldManager` が共通実装として持つプライベートヘルパーは
`_activate_field`/`_deactivate_field`（`field_manager.py:90, 104`）という
命名だが、これを呼び出す public メソッドの動詞はサブクラスによって
食い違う。

```python
# ExclusiveFieldManager（天候・地形）: apply / remove
def apply(self, name: T, count: int, source: Pokemon | None = None) -> bool:  # field_manager.py:157
def remove(self) -> bool:                                                     # field_manager.py:191

# StackableFieldManager（グローバル・サイド）: activate / deactivate
def activate(self, name: T, count: int) -> bool:    # field_manager.py:234
def deactivate(self, name: T) -> bool:               # field_manager.py:257
```

`StackableFieldManager` は内部ヘルパーと同じ語（activate/deactivate）を
public API 名としても使っているのに対し、`ExclusiveFieldManager` は
異なる語（apply/remove）を選んでおり、内部実装と外部APIの命名が
一致するクラスと一致しないクラスが同じ基底クラスの兄弟として同居している。
また `AilmentManager.apply`/`remove`、`VolatileManager.apply`/`remove`
（別ファイル）とは語が一致するため、`ExclusiveFieldManager` 系だけが
プロジェクト全体の「効果を与える/消す」ボキャブラリと合っており、
`StackableFieldManager` 系がそこから外れている、とも整理できる。

### 命名-5（新規）: 「critical」の略語表記が同一ファイル内で `critical` と `crit` に割れている

**ファイル**: `src/jpoke/core/move_executor.py:11, 21, 197-234`

```python
# move_executor.py:11
from jpoke.utils.math import clamp_stats, clamp_critic
# move_executor.py:21
CRIT_RATES = [1/24, 1/8, 1/2, 1]
# move_executor.py:213, 223 （同じファイル内で "critical" は省略しない）
critical_rank = clamp_critic(ctx.move.crit_ratio)
```

同じ `move_executor.py` の中で、`critical_rank`/`critical_mode`/
`AttackContext.critical`（`context.py:102`）/`ON_CALC_CRITICAL_RANK` は
省略しない `critical` を使う一方、インポートしている util 関数名
`clamp_critic` と定数名 `CRIT_RATES` だけが `crit` と省略されている。
`ctx.move.crit_ratio`（`model/move.py` 側のフィールド、core外だが
同じ流れで参照される）も省略形であり、プロジェクト全体で「critical」の
略語運用が統一されていないことが `core/` からも確認できる。

### 命名-6（新規）: コメント中の「ハンドラー」表記が2箇所だけ長音符付きになっている

**ファイル**: `src/jpoke/core/ailment_manager.py:101`,
`src/jpoke/core/volatile_manager.py:78`

```python
# ailment_manager.py:101
# ハンドラーが空値を返した場合は状態異常を付与しない
# volatile_manager.py:78
# ハンドラーが空値を返した場合は無効化させる
```

`core/` 全体では「ハンドラ」（長音符なし）表記が大多数（`handler.py`
というファイル名自体を含め数十箇所）を占めており、この2箇所のコメントだけ
「ハンドラー」と長音符付きになっている。プロジェクト全体の用語統一の
観点で軽微だが修正対象。

### 命名-7（新規、ISSUE-12と対応）: `Battle` Facade のメソッド命名がマネージャーの実メソッド名と一致する場合／ドメイン名を接頭辞として付加する場合／存在しない場合の3パターンに分かれている

**ファイル**: `src/jpoke/core/battle.py`（全体）

`Battle` の委譲メソッドは大半がマネージャー側と同名で1:1委譲する
（`run_move`→`MoveExecutor.run_move`、`modify_hp`→`StatusManager.modify_hp`、
`change_ability`→`AbilityManager.change_ability`、
`resolve_command`→`CommandManager.resolve_command` など）。一方
`add_ability_disabled_reason`/`remove_ability_disabled_reason`
（`battle.py:909-915`）は `AbilityManager.add_disabled_reason`/
`remove_disabled_reason` にドメイン名 `ability` を接頭辞として追加した
別名になっている（`Battle` は複数マネージャーが同名メソッドを持ちうる
フラットな名前空間のため、これ自体は妥当な設計判断）。ところが同じ
「`add_disabled_reason`/`remove_disabled_reason` を持つマネージャー」である
`ItemManager` にはこのパターンが一切適用されず、`Battle` 側に
`add_item_disabled_reason` 相当のメソッドが存在しない（ISSUE-12）。
また `set_ailment`/`set_weather`/`set_terrain`（`battle.py:752-790`）は
委譲先メソッド名 `apply` を `set_` にリネームしており、「委譲先と同名を
保つ」「ドメイン名を前置する」「動詞自体を変える」の3パターンが
使い分けの理由なく併存している。

### 命名-8（新規、参考）: `LethalContext`（lethal.py）と `AttackContext`（context.py）はフィールド構成が酷似しているが独立した型である

**ファイル**: `src/jpoke/core/lethal.py:50-64`,
`src/jpoke/core/context.py:94-113`

```python
# lethal.py:50-58
@dataclass
class LethalContext:
    attacker: Pokemon
    defender: Pokemon
    move: Move
    critical: bool = False
    move_secondary: bool = False
    n_attack: int = 1
    hit: int = 1

# context.py:94-104
@dataclass(eq=False, kw_only=True)
class AttackContext(BaseContext):
    attacker: Pokemon
    defender: Pokemon | None = None
    move: Move
    hit_index: int = 1
    hit_count: int = 1
    critical: bool = False
```

`attacker`/`defender`/`move`/`critical` というフィールド名・型が一致して
いるため一見 `AttackContext` の派生や姉妹型に見えるが、`LethalContext`
は `BaseContext` を継承しない独立した `dataclass` である。これは
`lethal.py` 冒頭の docstring（「通常の Handler とは独立した仕組み」）で
意図的な設計であると明記されており誤りではないが、`hit_index`/`hit_count`
（`AttackContext`）と `hit`/`n_attack`（`LethalContext`）のように、同じ
概念（何ヒット目か／何回目の攻撃か）を指す語が両クラス間で対応せず
異なる名前になっている点は、両システムを行き来する開発者にとって
紛らわしい可能性がある。統合は不要だが、フィールド名だけでも
`AttackContext` 側の語彙（`hit_index`）に合わせる余地はある。

---

## 総評

`core/` の全体アーキテクチャ（`Battle` Facade + 専門マネージャー群、
`Handler`/`EventManager` によるイベント駆動、`GameEffect` との連携）は
今回も一貫性が高く保たれていた。前回レビューで最大の懸念だった
「`__init__.py` の import 順依存の循環 import」（CRIT-3）が実質的に
解消されていたことは明確な改善であり、`move_category`/`move_power` の
監視フラグ扱い漏れ（MINOR-5）の解消と合わせて、地道な保守が続いている
ことがうかがえる。一方で `docstring`/引数名のドリフト系の指摘
（CRIT-2, ISSUE-1〜3, 5, 11）はほぼ全て未着手のまま残っており、
`Battle.__init__` の属性増加ペースに docstring の更新が追いついていない
傾向はむしろ悪化している。

今回新たに発見した2件（CRIT-4: `AilmentManager.apply()` の `ctx` 引数
no-op、CRIT-5: `Battle.set_ailment()` のdocstring矛盾）は、いずれも
「呼び出し側は動くと信じているが実際には機能していない」という、
テストでは検出されにくい種類の不具合である。特に CRIT-4 は
`handlers/` 側の15箇所以上が意図的に `ctx=ctx` を渡している以上、
本来何らかの意味を持たせるつもりだった設計の実装漏れである可能性が高く、
次回 `handlers/` レビュー時にあわせて実害の有無を確認することを推奨する。

命名観点では、`core/` 全体としてクラス構造・イベント駆動の骨格には
高い規律がある一方、**個々の関数・引数レベルの命名は「その場その場の
妥当な判断」が積み重なった結果、同じ概念に複数の呼び方が並立している**
という傾向が明確に見えた。特に「対象ポケモンの引数名（mon/target）」と
「イベント補正を伴う値計算の動詞（calc_/resolve_）」の2つは、それぞれ
15箇所以上・10箇所以上にまたがる大きな不統一であり、新規実装時の
参照先次第でどちらのパターンが選ばれるかが決まってしまっている状態に
近い。いずれも大規模な破壊的変更なしに、今後の新規コードから片方の
語彙に寄せていくことは可能であり、`CLAUDE.md` にプロジェクト標準の
語彙表（例: 「対象ポケモンは `mon`」「イベント補正付き計算は `resolve_`」）
を追記することが最も費用対効果の高い対策になる。
