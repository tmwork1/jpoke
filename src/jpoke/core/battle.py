"""ポケモンバトルのメインロジックを管理するモジュール。

バトル全体の状態管理、ターン進行、イベント処理、ログ記録などを統括します。
プレイヤー、ポケモン、技、場の状態などを一元管理し、バトルの進行を制御します。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Literal
if TYPE_CHECKING:
    from .lethal import LethalResult

from dataclasses import dataclass
from contextlib import contextmanager
import secrets
from random import Random
from copy import deepcopy

from jpoke.types import BattlePhase, Stat, StatChangeReason, GlobalFieldName, \
    HPChangeReason, AbilityDisabledReason, AbilityName, MoveName, CriticalMode, DamageRollMode, \
    AilmentName, WeatherName, TerrainName, VolatileName, SideFieldName, ItemName
from jpoke.enums import Event, Command, LogCode
from jpoke.exceptions import InvalidCommandError, InvalidPhaseError
from jpoke.utils import fast_copy
from jpoke.utils.math import round_half_down

from jpoke.model.pokemon import Pokemon
from jpoke.model.move import Move
from jpoke.model.field import Field

from .player_state import PlayerState
from .event_manager import EventManager
from .context import EventContext
from .player import Player
from .event_logger import EventLogger
from .log_payload import Payload
from .replay import RecordedCommand, BattleReplayData
from .damage import DamageCalculator
from .field_manager import WeatherManager, TerrainManager, GlobalFieldManager, SideFieldManager
from .move_executor import MoveExecutor
from .switch_manager import SwitchManager
from .turn_controller import TurnController
from .speed_calculator import SpeedCalculator
from .item_manager import ItemManager
from .command_manager import CommandManager
from .ability_manager import AbilityManager
from .ailment_manager import AilmentManager
from .volatile_manager import VolatileManager
from .status_manager import StatusManager
from .query import PokemonQuery
from . import lethal, observation_builder


@dataclass
class TestOption:
    """テスト用オプション設定クラス。

    Attributes:
        accuracy: 命中率の固定値（Noneの場合は通常計算）
        trigger_ailment: 状態異常の確率的発動の固定値（Noneの場合は通常の乱数判定）
            例: True = 必ず発動, False = 必ず発動しない
        trigger_volatile: 変動状態の確率的発動の固定値（Noneの場合は通常の乱数判定）
            例: True = 必ず発動, False = 必ず発動しない
        secondary_chance: 追加効果確率の固定値（Noneの場合は通常計算）
            例: 1.0 = 必ず発動, 0.0 = 必ず発動しない
    """
    accuracy: int | None = None
    trigger_ailment: bool | None = None
    trigger_volatile: bool | None = None
    secondary_chance: float | None = None


@dataclass
class BattleOption:
    """対戦全体のルールオプション設定クラス。

    Attributes:
        mega_evolution: メガシンカを許可するか
        terastal: テラスタルを許可するか
        critical_mode: 急所判定モード（"normal" / "always"）
        damage_roll: ダメージ乱数モード（"normal" / "average" / "max" / "min"）
        accuracy_fix_threshold: この値以上の命中率を100%固定にする（Noneなら無効）
        effect_chance_threshold: この値未満の追加効果確率を0%（発生しない）にする（Noneなら無効）
        double_battle: ダブルバトル向けのダメージ計算補正
            （複数対象になり得る技のダメージ0.75倍・壁の軽減率2/3倍）を有効にするか
    """
    mega_evolution: bool = True
    terastal: bool = True
    critical_mode: CriticalMode = "normal"
    damage_roll: DamageRollMode = "normal"
    accuracy_fix_threshold: int | None = None
    effect_chance_threshold: float | None = None
    double_battle: bool = False


class Battle:
    """ポケモンバトルの状態と処理を管理するメインクラス。

    バトル全体の状態、ターン管理、イベントシステム、ログ記録、
    各種マネージャークラスを統括します。

    API 方針:
        外部からの利用（テスト・bot・探索コード）は Battle の公開メソッドを入口とする。
        マネージャーの直接呼び出し（battle.move_executor.run_move() 等）は
        jpoke 内部実装（core/ handlers/）に限る。
        run_move や modify_stats などの委譲メソッドはこの方針のための公式 API である。

    Attributes:
        players: 参加プレイヤーのタプル（通常2人）
        seed: 乱数シード値
        turn: 現在のターン数
        winner: 勝者のPlayerインスタンス（勝負がついていない場合はNone）
        events: イベント管理システム
        logger: バトルログ記録システム
        random: ゲーム進行用の乱数生成器（ダメージロール・命中判定・急所判定など）
        decision_random: 行動選択（choose_command）専用の乱数生成器。observation_builder.build()
            の観測用コピーはこちらだけを本体と共有するため、方策がこれを消費しても
            ゲーム進行用の乱数系列（random）を先取りすることはない
        damage_calculator: ダメージ計算機
        move_executor: 技実行管理
        switch_manager: 交代管理
        turn_controller: ターン進行制御
        speed_calculator: 素早さ計算機
        weather_manager: 天候管理
        terrain_manager: 地形管理
        global_manager: グローバル場の状態管理
        side_managers: 各プレイヤー側の場の状態管理
        option: 対戦全体のルールオプション設定
        test_option: テスト用オプション設定
    """

    def __init__(self,
                 *players: Player,
                 n_selected: int | None = None,
                 seed: int | None = None,
                 mega_evolution: bool = True,
                 terastal: bool = True,
                 critical_mode: CriticalMode = "normal",
                 damage_roll: DamageRollMode = "normal",
                 accuracy_fix_threshold: int | None = None,
                 effect_chance_threshold: float | None = None,
                 double_battle: bool = False) -> None:
        """Battleインスタンスを初期化する。

        Args:
            players: 参加プレイヤー（可変長引数、通常2人）。`Battle(player1, player2)` のように
                個別の位置引数で渡す（`Battle((player1, player2))` のようなタプル渡しは不可）
            n_selected: 選出可能なポケモンの数（Noneの場合は `min(3, 各プレイヤーの手持ち数)`
                を自動設定する。手持ち数がプレイヤー間で異なる場合も両者に同じ値が
                適用されるため、片方の手持ちが少ないと両者とも選出数が絞られる点に注意）
            seed: 乱数シード値（Noneの場合はOSの乱数源から高エントロピーな値を生成する。
                同一プロセス内で短時間に複数の `Battle` を作る場合でも衝突しない）
            mega_evolution: メガシンカを許可するか（デフォルトTrue）
            terastal: テラスタルを許可するか（デフォルトTrue）
            critical_mode: 急所判定モード（"normal" / "always"、デフォルト"normal"）
            damage_roll: ダメージ乱数モード（"normal" / "average" / "max" / "min"、デフォルト"normal"）
            accuracy_fix_threshold: この値以上の命中率を100%固定にする（Noneなら無効）
            effect_chance_threshold: この値未満の追加効果確率を0%にする（Noneなら無効）
            double_battle: ダブルバトル向けのダメージ計算補正
                （複数対象になり得る技のダメージ0.75倍・壁の軽減率2/3倍）を有効にするか（デフォルトFalse）
        """

        self.players: tuple[Player, ...] = players
        self.n_selected: int = (
            n_selected if n_selected is not None
            else min(3, min(len(ply.team) for ply in players))
        )
        self.seed: int = seed if seed is not None else secrets.randbits(32)

        self.random = Random(self.seed)
        # 行動選択（choose_command）専用の乱数生成器。ゲーム進行用の self.random とは
        # 完全に独立させる。observation_builder.build() の観測用コピーはこちらだけを
        # 本体と同一参照で共有するため、方策がこれを消費してもダメージロール・命中判定・
        # 急所判定など未来の乱数を先取りしてしまうことがない。同じ seed なら毎回同じ
        # 初期状態になるよう seed から決定的に派生させる。
        self.decision_random = Random(hash((self.seed, "decision")) & 0xFFFFFFFF)

        self.copy_depth: int = 0
        self._reseed_count: int = 0
        self.observer: Player | None = None

        self.turn: int = -1
        self.phase: BattlePhase = ""
        self.winner: Player | None = None
        self.last_used_move_name: MoveName | Literal[""] = ""
        self.round_used_turn: int | None = None  # りんしょう: 直近に使われたターン番号
        self.echoed_voice_power: int = 40  # エコーボイス: 現在の威力段階
        self.echoed_voice_last_turn: int | None = None  # エコーボイス: 直近に成立したターン番号
        self.fusion_bolt_used_turn: int | None = None  # クロスサンダー: 直近に命中したターン番号（クロスフレイムとの威力2倍判定用）
        self.fusion_flare_used_turn: int | None = None  # クロスフレイム: 直近に命中したターン番号（クロスサンダーとの威力2倍判定用）

        self._player_states: list[PlayerState] = [PlayerState(ply) for ply in players]
        self._player_states_map: dict[Player, PlayerState] = dict(zip(players, self._player_states))

        # リプレイ再現用の対戦開始前チームスナップショット（PlayerState 構築直後、
        # 対戦の影響を一切受けていない状態で取得する）
        self._team_snapshot: list[list[dict]] = [
            [mon.to_dict() for mon in state.team] for state in self._player_states
        ]
        self.command_log: list[RecordedCommand] = []

        self.events = EventManager(self)
        self.event_logger = EventLogger()
        self.turn_controller: TurnController = TurnController(self)
        self.speed_calculator: SpeedCalculator = SpeedCalculator(self)
        self.switch_manager: SwitchManager = SwitchManager(self)
        self.move_executor: MoveExecutor = MoveExecutor(self)
        self.damage_calculator: DamageCalculator = DamageCalculator(self)
        self.ailment_manager: AilmentManager = AilmentManager(self)
        self.volatile_manager: VolatileManager = VolatileManager(self)
        self.query: PokemonQuery = PokemonQuery(self)
        self.status_manager: StatusManager = StatusManager(self)
        self.command_manager: CommandManager = CommandManager(self)
        self.ability_manager: AbilityManager = AbilityManager(self)
        self.item_manager: ItemManager = ItemManager(self)
        self.weather_manager: WeatherManager = WeatherManager(self)
        self.terrain_manager: TerrainManager = TerrainManager(self)
        self.global_manager: GlobalFieldManager = GlobalFieldManager(self)
        self.side_managers: list[SideFieldManager] = [
            SideFieldManager(self, ply) for ply in self.players
        ]

        self.option: BattleOption = BattleOption(
            mega_evolution=mega_evolution,
            terastal=terastal,
            critical_mode=critical_mode,
            damage_roll=damage_roll,
            accuracy_fix_threshold=accuracy_fix_threshold,
            effect_chance_threshold=effect_chance_threshold,
            double_battle=double_battle,
        )
        self.test_option: TestOption = TestOption()

    # update_reference を持たないが deepcopy が必要な可変状態。
    # マネージャー類は _deepcopy_keys() が自動検出するため、ここに列挙するのは
    # 「マネージャーでない可変オブジェクト」のみ。
    _EXTRA_DEEPCOPY_KEYS: tuple[str, ...] = (
        "random",
        "decision_random",
        "_player_states",
        "event_logger",
        "option",
        "test_option",
        "command_log",
    )

    def _deepcopy_keys(self) -> list[str]:
        """deepcopy 対象の属性キーを列挙する。

        `update_reference` を持つ属性（マネージャー）とそのリストを自動検出するため、
        新しいマネージャーを追加してもここを更新する必要はない。
        """
        keys = list(self._EXTRA_DEEPCOPY_KEYS)
        for key, value in vars(self).items():
            if hasattr(value, "update_reference"):
                keys.append(key)
            elif (
                isinstance(value, list)
                and value
                and all(hasattr(item, "update_reference") for item in value)
            ):
                keys.append(key)
        return keys

    def __deepcopy__(self, memo):
        """Battleインスタンスのディープコピーを作成する。

        Args:
            memo: コピー済みオブジェクトのメモ辞書

        Returns:
            Battle: コピーされたBattleインスタンス
        """
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new

        fast_copy(self, new, keys_to_deepcopy=self._deepcopy_keys())

        # player_states のキャッシュを複製後の PlayerState で再構築する
        new._player_states_map = dict(zip(new.players, new._player_states))

        # ポケモンが持つ他ポケモンへの参照を複製後の個体に付け替える
        mon_map = {
            id(old_mon): new_mon
            for old_state, new_state in zip(self._player_states, new._player_states)
            for old_mon, new_mon in zip(old_state.team, new_state.team)
        }
        for state in new._player_states:
            for mon in state.team:
                for key, val in vars(mon).items():
                    if isinstance(val, Pokemon):
                        setattr(mon, key, mon_map.get(id(val), val))

        # 複製したBattleインスタンスへの参照を各マネージャークラスに更新
        new._update_reference()

        # 深さを更新
        new.copy_depth += 1

        return new

    def _update_reference(self):
        """ディープコピー後のBattleインスタンスへの参照を各マネージャークラスに更新する。

        `update_reference` を持つ属性（マネージャー）とそのリスト要素を自動検出して呼び出す。
        EventManager はハンドラ主体の再解決に旧 Battle への参照を使うため、
        属性定義順（events が先頭）のまま処理される必要がある。
        """
        for value in vars(self).values():
            if hasattr(value, "update_reference"):
                value.update_reference(self)
            elif isinstance(value, list):
                for item in value:
                    if hasattr(item, "update_reference"):
                        item.update_reference(self)

    def copy(self, reseed: bool = False) -> Battle:
        """Battleの複製を作成する。

        Args:
            reseed: Trueの場合、複製側の乱数生成器を派生シードで初期化する。
                木探索で複数の枝が同一の乱数系列を引いて相関するのを避けたいときに使う。
                派生シードは元のシードと派生回数から決定的に生成されるため、
                元の乱数系列は消費されず再現性も保たれる。
        """
        new = deepcopy(self)
        if reseed:
            self._reseed_count += 1
            new.seed = hash((self.seed, self._reseed_count)) & 0xFFFFFFFF
            new.random = Random(new.seed)
            new.decision_random = Random(hash((new.seed, "decision")) & 0xFFFFFFFF)
        return new

    @contextmanager
    def phase_context(self, phase: BattlePhase):
        old_phase = self.phase
        self.phase = phase
        try:
            yield
        finally:
            self.phase = old_phase

    def build_observation(self, observer: Player) -> Battle:
        """指定したプレイヤー視点で情報を隠蔽した Battle インスタンスのコピーを作成。

        すでに観測状態の場合はそのままコピーを返す。

        Args:
            observer: 観測対象のプレイヤー。Noneの場合は全ての情報をコピー。

        Returns:
            Battle インスタンスのコピー
        """
        if self.is_observation():
            return self.copy()
        return observation_builder.build(self, observer)

    def is_observation(self) -> bool:
        """Battle インスタンスが観測用かどうかを判定する。

        Returns:
            bool: 観測用の場合は True、通常の Battle インスタンスの場合は False
        """
        return self.observer is not None

    def calc_lethal(self,
                    attacker: Pokemon,
                    moves: MoveName | Move | tuple[MoveName | Move, int]
                        | list[MoveName | Move | tuple[MoveName | Move, int]],
                    critical: bool = False,
                    secondary: bool = False,
                    max_attack: int = 10) -> list[LethalResult]:
        """指定した技（列）を最大 max_attack 回撃ち込んだ場合の致死率を計算する（LethalCalculatorへの委譲）。

        `moves` には技名の文字列（`MoveName`）・`Move` インスタンス・
        `(技, ヒット数)` のタプル、およびそれらのリストを渡せる。文字列は
        内部で `Move(name)` に正規化される。リストで複数の技を渡した場合は
        その順番通りに1回ずつ使用する（例: `["でんこうせっか", "かみなり"]` は
        1発目にでんこうせっか、2発目にかみなりを撃つ）。

        Args:
            attacker: 攻撃側のポケモン
            moves: 使用する技。単体 / (技, ヒット数) / それらのリスト
            critical: 急所として計算するか
            secondary: 追加効果ハンドラ（火傷・怯みなど）を適用するか
            max_attack: 最大攻撃回数（確定数が出た時点で打ち切り）

        Returns:
            list[LethalResult]: 各ヒット後の致死率計算結果のリスト。
                リストの1要素が1ヒットに対応し、`hp_dist` はそのヒットを
                適用した後の防御側HP分布を表す。多段技はヒットごとに
                要素が分かれる。最終的な致死率（max_attack回、または
                多段技も含め全ヒット終了時点のもの）は `results[-1].lethal_probability`
                で読み取れる
        """
        return lethal.calc_lethal(
            self, attacker, moves, critical=critical,
            move_secondary=secondary, max_attack=max_attack
        )

    @property
    def player_states(self) -> dict[Player, PlayerState]:
        """プレイヤーごとの状態を管理する辞書を返す。"""
        return self._player_states_map

    @property
    def actives(self) -> list[Pokemon]:
        """現在場に出ているポケモンのリストを取得。

        Returns:
            list[Pokemon]: 各プレイヤーの場のポケモン
        """
        return [state.active for state in self.player_states.values() if state.active is not None]

    def get_active(self, player: Player) -> Pokemon | None:
        """指定したプレイヤーの現在場に出ているポケモンを取得。

        Args:
            player: プレイヤー

        Returns:
            Pokemon | None: 指定したプレイヤーの場のポケモン。
                交代中などで場が空いている場合は None
        """
        if player in self.player_states:
            return self.player_states[player].active
        raise ValueError(f"Player {player} not found in battle.")

    def get_team(self, player: Player) -> list[Pokemon]:
        """指定したプレイヤーの対戦中のチームを取得。

        `player.team` はコンストラクタ時点のスナップショットで対戦中は更新されないため、
        瀕死・HP変化などバトル開始後の状態を見るには本メソッドを使う。

        Args:
            player: プレイヤー

        Returns:
            list[Pokemon]: 対戦中のポケモンのリスト（選出漏れの控えも含む）
        """
        if player in self.player_states:
            return self.player_states[player].team
        raise ValueError(f"Player {player} not found in battle.")

    def is_active(self, mon: Pokemon) -> bool:
        """指定したポケモンが現在場に出ているか確認。"""
        return mon in self.actives

    @property
    def raw_weather(self) -> Field:
        """現在セットされている天候を取得。"""
        return self.weather_manager.current

    @property
    def weather(self) -> Field:
        """有効な天候オブジェクトを返す。判定ロジックは WeatherManager に委譲する。"""
        return self.weather_manager.active

    def weather_for(self, mon: Pokemon) -> Field:
        """指定したポケモンに対して有効な天候を返す。

        ON_CHECK_WEATHER_IMMUNE ハンドラ（ばんのうがさ等）が True を返した場合は
        「なし」天候を返す。エアロック・ノーてんきで天候が無効の場合も「なし」天候を返す。

        Args:
            mon: 対象のポケモン

        Returns:
            Field: 対象ポケモンに有効な天候
        """
        if self.events.emit(Event.ON_CHECK_WEATHER_IMMUNE, EventContext(source=mon), False):
            return self.weather_manager.inactive
        return self.weather

    @property
    def terrain(self) -> Field:
        """現在のフィールド状態を取得。

        Returns:
            Field: 現在のフィールド
        """
        return self.terrain_manager.current

    def get_global_field(self, name: GlobalFieldName) -> Field:
        """グローバルフィールド効果を取得。"""
        return self.global_manager.fields[name]

    def get_side(self, source: Player | Pokemon) -> SideFieldManager:
        """プレイヤーまたはポケモンからサイドフィールドマネージャーを取得。

        Args:
            source: Player または Pokemon インスタンス

        Returns:
            SideFieldManager: 対応するサイドフィールドマネージャー
        """
        index = self._get_player_index(source)
        return self.side_managers[index]

    def get_player(self, mon: Pokemon) -> Player:
        """ポケモンが所属するプレイヤーを検索する。

        Args:
            mon: 検索対象のポケモン

        Returns:
            Player: ポケモンを所有するプレイヤー

        Raises:
            Exception: ポケモンが見つからない場合
        """
        index = self._get_player_index(mon)
        return self.players[index]

    def _get_player_index(self, source: Player | Pokemon) -> int:
        """プレイヤーまたはポケモンからプレイヤーインデックスを取得。

        Args:
            source: Player または Pokemon インスタンス

        Returns:
            プレイヤーインデックス (0 or 1)
        """
        if isinstance(source, Player):
            return self.players.index(source)
        else:
            for player, state in self.player_states.items():
                if source in state.team:
                    return self.players.index(player)
        raise ValueError(f"Source {source} not found in battle.")

    def opponent(self, player: Player) -> Player:
        """相手のプレイヤーを取得する。

        Args:
            player: プレイヤー

        Returns:
            Player: 対戦相手のプレイヤー
        """
        return self.players[1 - self.players.index(player)]

    def foe(self, active: Pokemon) -> Pokemon:
        """相手の場のポケモンを取得する。

        Args:
            active: 場に出ているポケモン

        Returns:
            Pokemon: 対戦相手のポケモン

        Raises:
            ValueError: 引数のポケモンが場に出ていない場合
        """
        actives = self.actives
        if active not in actives:
            raise ValueError(f"{active.name} は場に出ていないため、相手のポケモンを特定できません。")
        return actives[1 - actives.index(active)]

    def get_available_commands(self, player: Player) -> list[Command]:
        """指定したプレイヤーが現在使用可能なコマンドのリストを取得する。

        Args:
            player: プレイヤー

        Returns:
            list[Command]: 使用可能なコマンドのリスト
        """
        # 相手の観測状態でコマンドを取得する場合は、最後に利用可能だったコマンドを返す
        if self.observer == self.opponent(player):
            return self.player_states[player].last_available_commands

        match self.phase:
            case "action":
                return self.command_manager.get_available_action_commands(player)
            case "switch":
                return self.command_manager.get_available_switch_commands(player)

        raise InvalidPhaseError(f"Invalid phase: {self.phase}")

    def can_switch(self, player: Player) -> bool:
        """指定したプレイヤーが交代可能かどうかを判定する（PokemonQueryへの委譲）。

        場のポケモンがとらわれ状態にある場合、または控えが全滅している場合はFalse。

        Args:
            player: 判定するプレイヤー

        Returns:
            bool: 交代可能な場合True
        """
        return self.query.can_switch(player)

    def resolve_speed_order(self) -> list[Pokemon]:
        """素早さ順序を解決（SpeedCalculatorへの委譲）。

        Returns:
            素早さの速い順にソートされたポケモンのリスト
        """
        return self.speed_calculator.resolve_speed_order()

    def resolve_action_order(self) -> list[Pokemon]:
        """技の行動順序を解決する（SpeedCalculatorへの委譲）。

        優先度と実効素早さを考慮した行動順を返す。各プレイヤーに予約済みコマンド
        （`player_states[player].reserved_commands`）が必要（`step()` 内部や
        シナリオ検証で `phase_context` 経由でコマンドを予約した後に呼ぶ）。

        Returns:
            list[Pokemon]: 行動順にソートされたポケモンのリスト
        """
        return self.speed_calculator.resolve_action_order()

    def calc_move_priority(self, attacker: Pokemon, move: Move) -> int:
        """技を発動したときの優先度を計算する（SpeedCalculatorへの委譲）。

        技本来の優先度に加え、ON_MODIFY_MOVE_PRIORITYイベント（さきどり等）による
        補正後の優先度を返す。

        Args:
            attacker: 技を使用するポケモン
            move: 使用する技

        Returns:
            int: 補正後の優先度
        """
        return self.speed_calculator.calc_move_priority(attacker, move)

    def judge_winner(self) -> Player | None:
        """勝者を判定（TurnControllerへの委譲）。

        Returns:
            勝者のPlayerインスタンス、勝負がついていない場合はNone
        """
        return self.turn_controller.judge_winner()

    def resolve_command(self, phase: BattlePhase, player: Player | None = None) -> dict[Player, Command]:
        """コマンドを解決する（CommandManagerへの委譲）。"""
        return self.command_manager.resolve_command(phase, player)

    def build_replay_data(self) -> BattleReplayData:
        """対戦を再現するためのリプレイデータを組み立てる。

        対戦の途中でも呼べる（選出とコマンド列はその時点までのものになる）。
        """
        from dataclasses import asdict
        return BattleReplayData(
            seed=self.seed,
            n_selected=self.n_selected,
            battle_option=asdict(self.option),
            teams=(self._team_snapshot[0], self._team_snapshot[1]),
            selections=(
                self.player_states[self.players[0]].selected_indexes,
                self.player_states[self.players[1]].selected_indexes,
            ),
            commands=list(self.command_log),
        )

    def start(self):
        """バトル開始処理を実行する（TurnControllerへの委譲）。

        選出と初期繰り出しを完了し、以降の `step` を可能にする。
        """
        self.turn_controller.start_battle()

    def step(self, commands: dict[Player, Command] | None = None):
        """ターンを1つ進める（TurnControllerへの委譲）。

        Args:
            commands: 各プレイヤーのコマンド辞書。Noneの場合はプレイヤーの方策関数に従う。
        """
        if self.is_new_turn() and commands is None:
            # is_new_turn()だけで判定すると、行動コマンド選択時の木探索でresolve_action_commands()が再帰的に呼ばれてしまうため、command is Noneのガードが必要。
            commands = self.resolve_command("action")
        else:
            if commands is None:
                raise InvalidCommandError("No commands provided for step().")
            for player in self.players:
                command = commands.get(player)
                if not self.command_manager.validate_command(player, command):
                    raise InvalidCommandError(f"Invalid command type for {player.username}: {command}.")

        if not commands:
            raise InvalidCommandError("No commands provided for step().")

        # リプレイ再現用に行動コマンドを記録する。外部から commands を直接渡す経路と
        # resolve_command() に解決させる経路の両方をここで一元的に捕捉する。
        # turn は _begin_turn() でインクリメントされる前なので +1 補正が必要。
        record_turn = self.turn + (1 if self.is_new_turn() else 0)
        for player, command in commands.items():
            self.command_log.append(RecordedCommand(
                turn=record_turn,
                player_index=self.players.index(player),
                phase="action",
                command=command,
            ))

        self.turn_controller.step(commands)

    def play_out(self, max_turns: int = 100) -> Player | None:
        """決着がつくかターン上限に達するまで自動的に進める。

        `battle.start()` の後に呼ぶ。01/03/05等の examples で繰り返されていた
        `while not battle.finished and battle.turn < N: battle.step()` という
        定型ループを1メソッドにまとめたもの。手動で `step()` を呼ぶ過程自体を
        観察したい場合はこのメソッドを使わず、従来通りループを書けばよい。

        Args:
            max_turns: 最大ターン数

        Returns:
            勝者のPlayerインスタンス。ターン上限で決着がつかなかった場合はNone
        """
        while not self.finished and self.turn < max_turns:
            self.step()
        return self.winner

    def run_move(self, attacker: Pokemon, move: Move):
        """技を実行（MoveExecutorへの委譲）。

        Args:
            attacker: 攻撃側のポケモン
            move: 使用する技
        """
        self.move_executor.run_move(attacker, move)

    def change_ability(self, mon: Pokemon, ability: AbilityName) -> None:
        """ポケモンの特性を更新する（AbilityManagerへの委譲）。"""
        self.ability_manager.change_ability(mon, ability)

    def command_to_move(self, player: Player, command: Command) -> Move:
        """コマンドから技オブジェクトを取得。

        方策実装（`choose_command`）でコマンドから技を引きたいときに使う。

        Args:
            player: プレイヤー
            command: 実行するコマンド

        Returns:
            技オブジェクト
        """
        return self.command_manager.resolve_move_from_command(player, command)

    def modify_hp(self,
                  target: Pokemon,
                  v: int = 0,
                  r: float = 0,
                  source: Pokemon | None = None,
                  reason: HPChangeReason = "") -> int:
        """ポケモンのHPを変更する（StatusManagerへの委譲）。

        Args:
            target: 対象のポケモン
            v: 変更する固定HP量
            r: 最大HPに対する割合（-1.0～1.0）。v との同時指定は不可
            source: ダメージ源のポケモン
            reason: 変更の理由

        Returns:
            実際に変化したHP量（正=回復、負=ダメージ）

        Raises:
            ValueError: v と r を同時に指定した場合、または r が範囲外の場合
        """
        if v and r:
            raise ValueError("modify_hp では v と r を同時に指定できません。")
        if r and not -1.0 <= r <= 1.0:
            raise ValueError(f"modify_hp の r は -1.0～1.0 で指定してください: {r}")
        if r:
            raw = int(target.max_hp * r)
            if r > 0:
                v = max(1, raw)
            else:
                v = min(-1, raw)
        return self.status_manager.modify_hp(target, v=v, reason=reason, source=source)

    def faint(self,
              target: Pokemon,
              source: Pokemon | None = None,
              reason: HPChangeReason = "") -> None:
        """ポケモンをひんしにする（HPを0にする）。"""
        self.modify_hp(target, v=-target.max_hp, source=source, reason=reason)

    def modify_stats(self,
                     target: Pokemon,
                     stats: dict[Stat, int],
                     source: Pokemon | None = None,
                     reason: StatChangeReason = "") -> dict[Stat, int]:
        """ポケモンの複数の能力ランクを同時に変更する（StatusManagerへの委譲）。"""
        return self.status_manager.modify_stats(target, stats, source=source, reason=reason)

    def set_ailment(self,
                    target: Pokemon,
                    name: AilmentName,
                    count: int | None = None,
                    source: Pokemon | None = None,
                    overwrite: bool = True) -> bool:
        """状態異常を直接付与する（シナリオ構築・ダメージ計算検証用）。

        既定では既存の状態異常があれば上書きする。特性・タイプ等による無効化判定は行わない
        （examples/スクリプトから素直に状態を作るための薄いラッパーのため）。

        Args:
            target: 対象のポケモン
            name: 状態異常名
            count: 継続ターン数（ねむりは省略時にChampions仕様で自動決定）
            source: 状態異常の原因となったポケモン（シンクロ等、原因ポケモンを
                参照するハンドラの検証に使う）
            overwrite: False の場合、既に状態異常があれば付与に失敗する
                （デフォルトTrueで既存の状態異常を上書き）

        Returns:
            bool: 付与に成功した場合True
        """
        return self.ailment_manager.apply(target, name, count=count, source=source, overwrite=overwrite)

    def set_volatile(self,
                     target: Pokemon,
                     name: VolatileName,
                     count: int | None = None,
                     source: Pokemon | None = None) -> bool:
        """揮発性状態を直接付与する（シナリオ構築・ダメージ計算検証用）。

        Args:
            target: 対象のポケモン
            name: 揮発性状態名
            count: 継続ターン数
            source: 揮発性状態の原因となったポケモン

        Returns:
            bool: 付与に成功した場合True（既に同じ揮発性状態がある場合は失敗）
        """
        return self.volatile_manager.apply(target, name, count=count, source=source)

    def set_weather(self, name: WeatherName, count: int = 5) -> bool:
        """天候を直接発動する（シナリオ構築・ダメージ計算検証用）。

        Args:
            name: 天候名
            count: 持続ターン数

        Returns:
            bool: 発動に成功した場合True
        """
        return self.weather_manager.apply(name, count)

    def set_terrain(self, name: TerrainName, count: int = 5) -> bool:
        """地形を直接発動する（シナリオ構築・ダメージ計算検証用）。

        Args:
            name: 地形名
            count: 持続ターン数

        Returns:
            bool: 発動に成功した場合True
        """
        return self.terrain_manager.apply(name, count)

    def activate_global_field(self, name: GlobalFieldName, count: int) -> bool:
        """グローバルフィールド効果を直接発動する（シナリオ構築・ダメージ計算検証用）。

        Args:
            name: グローバルフィールド効果名
            count: 持続ターン数

        Returns:
            bool: 発動に成功した場合True
        """
        return self.global_manager.activate(name, count)

    def activate_side_field(self, player: Player, name: SideFieldName, count: int) -> bool:
        """指定プレイヤーのサイドフィールド効果を直接発動する（シナリオ構築・ダメージ計算検証用）。

        Args:
            player: 発動対象のサイドを持つプレイヤー
            name: サイドフィールド効果名
            count: 層数・持続ターン数（効果による）

        Returns:
            bool: 発動に成功した場合True
        """
        return self.get_side(player).activate(name, count)

    def set_item(self, target: Pokemon, name: ItemName, source: Pokemon | None = None) -> bool:
        """ポケモンの持ち物を直接設定する（シナリオ構築・ダメージ計算検証用）。

        Args:
            target: 持ち物を設定するポケモン
            name: 設定後の持ち物名（空文字列の場合は持ち物を外す）
            source: 変更の原因となったポケモン（例: 交換元のポケモン、技の使用者など）

        Returns:
            bool: 設定に成功した場合True
        """
        return self.item_manager.set_item(target, name, source=source)

    def roll_damage(self,
                    attacker: Pokemon,
                    defender: Pokemon,
                    move: Move | MoveName,
                    critical: bool = False) -> int:
        """ダメージを計算してランダムに1つ選択する。

        Args:
            attacker: 攻撃側のポケモン
            defender: 防御側のポケモン
            move: 使用する技（MoveオブジェクトまたはID文字列）
            critical: 急所に当たるかどうか

        Returns:
            int: 計算されたダメージ値
        """
        damages = self.calc_damages(attacker, defender, move, critical)
        match self.option.damage_roll:
            case "average":
                return round_half_down(sum(damages) / len(damages))
            case "max":
                return max(damages)
            case "min":
                return min(damages)
            case _:
                # random.choice() は getrandbits() 経由でPRNG内部状態に依存するため、
                # random() のみを固定するテストヘルパー（fix_random）では制御できない。
                # random() ベースの選択にすることで、乱数シードが異なる2つの Battle
                # 間でも fix_random() だけでダメージロールを再現できるようにする。
                # random() は理論上 [0, 1) だが、fix_random() で 1.0 を代入する
                # テストが存在するため、境界超過による IndexError を防ぐ
                index = min(int(self.random.random() * len(damages)), len(damages) - 1)
                return damages[index]

    def calc_damages(self,
                     attacker: Pokemon,
                     defender: Pokemon,
                     move: Move | MoveName,
                     critical: bool = False) -> list[int]:
        """可能なダメージ値のリストを計算する。

        乱数によるダメージ幅を考慮した全ての可能なダメージ値を返します。

        Args:
            attacker: 攻撃側のポケモン
            defender: 防御側のポケモン
            move: 使用する技（MoveオブジェクトまたはID文字列）
            critical: 急所に当たるかどうか

        Returns:
            list[int]: 可能なダメージ値のリスト
        """
        if isinstance(move, str):
            move = Move(move)
        return self.damage_calculator.calc_damages(
            attacker, defender, move, critical=critical
        )

    def has_interrupt(self) -> bool:
        """割り込みフラグが設定されているか確認。

        Returns:
            いずれかのプレイヤーに割り込みフラグがある場合True
        """
        return any(state.has_interrupt() for state in self.player_states.values())

    def is_new_turn(self) -> bool:
        """新しいターンの開始かどうかを判定する。

        Returns:
            現在のターンが開始されたばかりで、まだ行動が実行されていない場合True
        """
        return not self.has_interrupt()

    def run_switch(self, player: Player, new: Pokemon, emit: bool = True):
        """ポケモンを交代（SwitchManagerへの委譲）。

        Args:
            player: 交代を行うプレイヤー
            new: 場に出す新しいポケモン
            emit: ON_SWITCH_INイベントを発火する場合True
        """
        self.switch_manager.run_switch(player, new, emit)

    def end_turn(self) -> None:
        """ターン終了処理（ON_TURN_ENDイベント）のみを発火する（シナリオ構築・検証用）。

        通常のターン進行は `step()` が内部でこのイベントも含めて実行するため、
        対戦を進めながら使う分にはこのメソッドは不要。技を使わず状態異常・天候・
        揮発性状態などのターン終了時効果（毒ダメージ・やけど回復阻害・天候ダメージ等）
        だけを単体で検証したい場合に使う。
        """
        self.events.emit(Event.ON_TURN_END)

    def add_event_log(self,
                      source: Player | Pokemon | int,
                      log: LogCode,
                      payload: Payload | None = None):
        """イベントログを追加。

        Args:
            source: Player または Pokemon インスタンス、またはプレイヤーインデックス
            log: イベントの内容を表すLogCode列挙値
            payload: イベントの詳細情報（必要に応じて）
        """
        if isinstance(source, int):
            idx = source
            pokemon = None
        else:
            idx = self._get_player_index(source)
            pokemon = source.name if isinstance(source, Pokemon) else None
        self.event_logger.add(self.turn, idx, log, payload, pokemon)

    def get_event_logs(self, turn: int | None = None) -> dict[Player, list]:
        """指定したターンの全プレイヤーのイベントログを取得。

        Args:
            turn: ターン番号（Noneの場合は現在のターン）

        Returns:
            Playerをキーとしたイベントログ(EventLog)のリストの辞書
        """
        if turn is None:
            turn = self.turn
        return {player: self.event_logger.get(turn, i)
                for i, player in enumerate(self.players)}

    def add_ability_disabled_reason(self, mon: Pokemon, reason: AbilityDisabledReason) -> bool:
        """特性の無効化理由を追加する（AbilityManagerへの委譲）。"""
        return self.ability_manager.add_disabled_reason(mon, reason)

    def remove_ability_disabled_reason(self, mon: Pokemon, reason: AbilityDisabledReason) -> bool:
        """特性の無効化理由を削除する（AbilityManagerへの委譲）。"""
        return self.ability_manager.remove_disabled_reason(mon, reason)

    def resolve_secondary_chance(self, ctx: EventContext, chance: float) -> float:
        """追加効果補正後の実効確率を返す。"""
        if self.test_option.secondary_chance is not None:
            return self.test_option.secondary_chance
        chance = self.events.emit(Event.ON_MODIFY_SECONDARY_CHANCE, ctx, chance)
        threshold = self.option.effect_chance_threshold
        if threshold is not None and chance < threshold:
            return 0.0
        return chance

    def get_log_lines(self, turn: int | None | Literal["all"] = None) -> list[str]:
        """指定したターンのログを整形した文字列のリストとして返す。

        出力先（print / logging / GUI 等）を呼び出し側に委ねるための API。
        `print_logs` はこのメソッドの結果を print するだけの薄いラッパー。

        Args:
            turn: ターン番号。Noneの場合は現在のターンのみ、`"all"` の場合は
                1ターン目から現在のターンまでの全ログを返す

        Returns:
            list[str]: 整形済みログ行のリスト
        """
        if turn == "all":
            target_turns = None
        else:
            target_turns = self.turn if turn is None else turn

        lines = []
        for log in self.event_logger.logs:
            if target_turns is not None and log.turn != target_turns:
                continue
            player = self.players[log.idx]
            lines.append(f"Turn {log.turn} : {player.username} : {log.pokemon or ''} : {log.render()}")
        return lines

    def print_logs(self, turn: int | None | Literal["all"] = None):
        """指定したターンのログを整形して出力する（`get_log_lines` の互換ラッパー）。

        Args:
            turn: ターン番号。Noneの場合は現在のターンのみ、`"all"` の場合は
                1ターン目から現在のターンまでの全ログを出力する
        """
        for line in self.get_log_lines(turn):
            print(line)

    def remove_all_volatiles(self, mon: Pokemon):
        """対象のポケモンからすべての揮発性状態を解除する（VolatileManagerへの委譲）。"""
        self.volatile_manager.remove_all(mon)

    # ── poke-env 互換 ───────────────────────────────────────────

    @property
    def finished(self) -> bool:
        """poke-env 互換: 対戦が終了しているかどうか。

        `self.winner` は `judge_winner()` を呼んだ時点で初めて遅延判定・
        キャッシュされるため、`judge_winner()` を一度も呼ばずに `self.winner`
        だけを参照すると、TODスコアで実際には決着している対戦でも
        `None` のままになる。そのため単純な `self.winner is not None` ではなく、
        `judge_winner()` を経由して判定する。
        """
        return self.judge_winner() is not None

    def won(self, player: Player) -> bool:
        """poke-env 互換: 指定したプレイヤーが勝利したかどうか。

        poke-env の `won` は引数なしのプロパティで、未終了時は None を返す
        （`bool | None`）。jpoke は完全情報でプレイヤー視点が固定されないため、
        Player を引数に取るメソッドとして提供する（意図的な差異）。
        未終了時に False を返す点も poke-env（None）と異なる。

        Args:
            player: 判定対象のプレイヤー
        """
        return self.winner is player

    def lost(self, player: Player) -> bool:
        """poke-env 互換: 指定したプレイヤーが敗北したかどうか。

        `won` と同様、poke-env とはシグネチャ・未終了時の戻り値が異なる（意図的な差異）。

        Args:
            player: 判定対象のプレイヤー
        """
        return self.winner is not None and self.winner is not player

    @property
    def active_pokemon(self) -> Pokemon | None:
        """poke-env 互換: observer 視点の場のポケモン。

        observer が設定されていない場合は先頭のポケモン（`actives[0]`）を返す。
        """
        if self.observer:
            return self.get_active(self.observer)
        return self.actives[0] if self.actives else None

    @property
    def opponent_active_pokemon(self) -> Pokemon | None:
        """poke-env 互換: observer から見た相手側の場のポケモン。

        observer が設定されていない場合は2番目のポケモン（`actives[1]`）を返す。
        """
        if self.observer:
            rival = self.opponent(self.observer)
            return self.get_active(rival)
        return self.actives[1] if len(self.actives) > 1 else None

    @property
    def side_conditions(self) -> dict:
        """poke-env 互換: observer 側のサイドフィールド状態（`side_managers[i].fields` のエイリアス）。"""
        if self.observer:
            idx = self.players.index(self.observer)
            return self.side_managers[idx].fields
        return {}

    @property
    def team(self) -> list[Pokemon]:
        """poke-env 互換: observer 側のチーム。

        poke-env は `Dict[str, Pokemon]` を返すが、jpoke は list のまま返す（ユーザー判断）。
        """
        if self.observer:
            return self.player_states[self.observer].team
        return []

    @property
    def available_moves(self) -> list[Move]:
        """poke-env 互換: observer が選択可能な技のリスト。

        `get_available_commands` の通常技コマンド（MOVE_i）を `command_to_move` で
        Move に変換する。テラスタル・メガシンカ等、同じ技のバリアントコマンドは
        重複を避けるため含めない。技コマンドが1つもない場合（わるあがきのみ）は
        わるあがきを1件返す。
        """
        if self.observer is None:
            return []
        commands = self.get_available_commands(self.observer)
        moves = [
            self.command_to_move(self.observer, cmd)
            for cmd in commands
            if cmd.is_regular_move
        ]
        if not moves and Command.STRUGGLE in commands:
            moves = [self.command_to_move(self.observer, Command.STRUGGLE)]
        return moves

    @property
    def available_switches(self) -> list[Pokemon]:
        """poke-env 互換: observer が交代可能なポケモンのリスト。

        `get_available_commands` の交代コマンド（SWITCH_i）からチームの該当ポケモンを抽出する。
        """
        if self.observer is None:
            return []
        commands = self.get_available_commands(self.observer)
        team = self.player_states[self.observer].team
        return [team[cmd.index] for cmd in commands if cmd.is_switch()]
