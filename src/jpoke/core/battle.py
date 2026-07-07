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
import time
from random import Random
from copy import deepcopy

from jpoke.types import BattlePhase, Stat, StatChangeReason, GlobalFieldName, \
    HPChangeReason, AbilityDisabledReason, AbilityName, MoveName, CriticalMode, DamageRollMode
from jpoke.enums import Event, Command, LogCode
from jpoke.exceptions import InvalidCommandError, InvalidPhaseError
from jpoke.utils import fast_copy
from jpoke.utils.math import round_half_down

from jpoke.model import Pokemon, Move, Field

from .player_state import PlayerState
from .event_manager import EventManager
from .context import EventContext
from .player import Player
from .event_logger import EventLogger, Payload
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
        players: 参加プレイヤーのリスト（通常2人）
        seed: 乱数シード値
        turn: 現在のターン数
        winner: 勝者のPlayerインスタンス（勝負がついていない場合はNone）
        events: イベント管理システム
        logger: バトルログ記録システム
        random: 乱数生成器
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
                 players: tuple[Player, ...],
                 n_selected: int = 3,
                 seed: int | None = None,
                 mega_evolution: bool = True,
                 terastal: bool = True,
                 critical_mode: CriticalMode = "通常",
                 damage_roll: DamageRollMode = "通常",
                 accuracy_fix_threshold: int | None = None,
                 effect_chance_threshold: float | None = None) -> None:
        """Battleインスタンスを初期化する。

        Args:
            players: 参加プレイヤーのタプル（通常2人）
            n_selected: 選出可能なポケモンの数（デフォルトは3）
            seed: 乱数シード値（Noneの場合は現在時刻を使用）
            mega_evolution: メガシンカを許可するか（デフォルトTrue）
            terastal: テラスタルを許可するか（デフォルトTrue）
            critical_mode: 急所判定モード（"通常" / "確定のみ"、デフォルト"通常"）
            damage_roll: ダメージ乱数モード（"通常" / "平均" / "最大" / "最小"、デフォルト"通常"）
            accuracy_fix_threshold: この値以上の命中率を100%固定にする（Noneなら無効）
            effect_chance_threshold: この値未満の追加効果確率を0%にする（Noneなら無効）
        """

        self.players: tuple[Player, ...] = players
        self.n_selected: int = n_selected
        self.seed: int = seed if seed is not None else int(time.time())

        self.random = Random(self.seed)

        self.copy_depth: int = 0
        self._reseed_count: int = 0
        self.observer: Player | None = None

        self.turn: int = -1
        self.phase: BattlePhase = ""
        self.winner: Player | None = None
        self.last_used_move_name: MoveName | Literal[""] = ""

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
        )
        self.test_option: TestOption = TestOption()

    # update_reference を持たないが deepcopy が必要な可変状態。
    # マネージャー類は _deepcopy_keys() が自動検出するため、ここに列挙するのは
    # 「マネージャーでない可変オブジェクト」のみ。
    _EXTRA_DEEPCOPY_KEYS: tuple[str, ...] = (
        "random",
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

        # ポケモンが持つ他ポケモンへの参照（contact_hitter 等）を複製後の個体に付け替える
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
                    moves: Move | tuple[Move, int] | list[Move | tuple[Move, int]],
                    critical: bool = False,
                    secondary: bool = False,
                    max_attack: int = 10) -> list[LethalResult]:
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

    def resolve_speed_order(self) -> list[Pokemon]:
        """素早さ順序を解決（SpeedCalculatorへの委譲）。

        Returns:
            素早さの速い順にソートされたポケモンのリスト
        """
        return self.speed_calculator.resolve_speed_order()

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
                    raise InvalidCommandError(f"Invalid command type for {player.name}: {command}.")

        if not commands:
            raise InvalidCommandError("No commands provided for step().")

        # リプレイ再現用に行動コマンドを記録する。外部から commands を直接渡す経路と
        # resolve_command() に解決させる経路の両方をここで一元的に捕捉する。
        # turn は _begin_turn() でインクリメントされる前なので +1 補正が必要。
        record_turn = self.turn + (1 if self.is_new_turn() else 0)
        for player, command in commands.items():
            self.command_log.append(RecordedCommand(
                turn=record_turn,
                player_idx=self.players.index(player),
                phase="action",
                command=command,
            ))

        self.turn_controller.step(commands)

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
            case "平均":
                return round_half_down(sum(damages) / len(damages))
            case "最大":
                return max(damages)
            case "最小":
                return min(damages)
            case _:
                return self.random.choice(damages)

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
        else:
            idx = self._get_player_index(source)
        self.event_logger.add(self.turn, idx, log, payload)

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

    def get_log_lines(self, turn: int | None = None) -> list[str]:
        """指定したターンのログを整形した文字列のリストとして返す。

        出力先（print / logging / GUI 等）を呼び出し側に委ねるための API。
        `print_logs` はこのメソッドの結果を print するだけの薄いラッパー。

        Args:
            turn: ターン番号（Noneの場合は現在のターン）

        Returns:
            list[str]: 整形済みログ行のリスト
        """
        if turn is None:
            turn = self.turn

        event_logs = [log for log in self.event_logger.logs if log.turn == turn]
        lines = []
        for log in event_logs:
            player = self.players[log.idx]
            pokemon = getattr(log.payload, "pokemon", "") if log.payload else ""
            lines.append(f"Turn {turn} : {player.name} : {pokemon} : {log.render()}")
        return lines

    def print_logs(self, turn: int | None = None):
        """指定したターンのログを整形して出力する（`get_log_lines` の互換ラッパー）。

        Args:
            turn: ターン番号（Noneの場合は現在のターン）
        """
        for line in self.get_log_lines(turn):
            print(line)

    def remove_all_volatiles(self, mon: Pokemon):
        """対象のポケモンからすべての揮発性状態を解除する（VolatileManagerへの委譲）。"""
        self.volatile_manager.remove_all(mon)
