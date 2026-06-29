"""ポケモンバトルのメインロジックを管理するモジュール。

バトル全体の状態管理、ターン進行、イベント処理、ログ記録などを統括します。
プレイヤー、ポケモン、技、場の状態などを一元管理し、バトルの進行を制御します。
"""
from __future__ import annotations
from dataclasses import dataclass
from contextlib import contextmanager
import time
from random import Random
from copy import deepcopy

from jpoke.utils.type_defs import BattlePhase, Stat, StatChangeReason, GlobalFieldName, \
    HPChangeReason, MoveCategory, AbilityDisabledReason, ItemDisabledReason
from jpoke.enums import Event, Command, Interrupt, LogCode
from jpoke.utils import fast_copy

from jpoke.model import Pokemon, Move, Field

from .player_state import PlayerState
from .event_manager import EventManager
from .context import EventContext, AttackContext
from .player import Player
from .event_logger import EventLogger, Payload
from .command_logger import CommandLogger
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
from . import lethal_calculator, observation_builder


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


class Battle:
    """ポケモンバトルの状態と処理を管理するメインクラス。

    バトル全体の状態、ターン管理、イベントシステム、ログ記録、
    各種マネージャークラスを統括します。

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
        test_option: テスト用オプション設定
    """

    def __init__(self,
                 players: tuple[Player, ...],
                 n_selected: int = 3,
                 seed: int | None = None) -> None:
        """Battleインスタンスを初期化する。

        Args:
            players: 参加プレイヤーのタプル（通常2人）
            n_selected: 選出可能なポケモンの数（デフォルトは3）
            seed: 乱数シード値（Noneの場合は現在時刻を使用）
        """

        self.players: tuple[Player, ...] = players
        self.n_selected: int = n_selected
        self.seed: int = seed or int(time.time())

        self.random = Random(self.seed)

        self.copy_depth: int = 0
        self.observer: Player | None = None

        self.turn: int = -1
        self.phase: BattlePhase = ""
        self.winner: Player | None = None

        self._player_states: list[PlayerState] = [PlayerState(ply) for ply in players]

        self.events = EventManager(self)
        self.event_logger = EventLogger()
        self.command_logger = CommandLogger()
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

        self.test_option: TestOption = TestOption()

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

        fast_copy(
            self, new,
            keys_to_deepcopy=[
                "random",
                "_player_states",
                "events",
                "event_logger",
                "command_logger",
                "turn_controller",
                "speed_calculator",
                "switch_manager",
                "move_executor",
                "damage_calculator",
                "ailment_manager",
                "volatile_manager",
                "query",
                "status_manager",
                "item_manager",
                "command_manager",
                "ability_manager",
                "weather_manager",
                "terrain_manager",
                "global_manager",
                "side_managers",
            ]
        )

        # 複製したBattleインスタンスへの参照を各マネージャークラスに更新
        new._update_reference()

        # 深さを更新
        new.copy_depth += 1

        return new

    def _update_reference(self):
        """ディープコピー後のBattleインスタンスへの参照を各マネージャークラスに更新する。"""
        self.events.update_reference(self)
        self.turn_controller.update_reference(self)
        self.speed_calculator.update_reference(self)
        self.switch_manager.update_reference(self)
        self.move_executor.update_reference(self)
        self.damage_calculator.update_reference(self)
        self.ailment_manager.update_reference(self)
        self.volatile_manager.update_reference(self)
        self.query.update_reference(self)
        self.status_manager.update_reference(self)
        self.command_manager.update_reference(self)
        self.ability_manager.update_reference(self)
        self.item_manager.update_reference(self)
        self.weather_manager.update_reference(self)
        self.terrain_manager.update_reference(self)
        self.global_manager.update_reference(self)
        for side in self.side_managers:
            side.update_reference(self)

    def copy(self) -> Battle:
        return deepcopy(self)

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
                    move: Move | list[Move],
                    critical: bool = False,
                    max_hit: int = 9):
        moves = [move] if isinstance(move, Move) else move
        lethal_calculator.calc_lethal(self, attacker, moves, critical=critical, max_hit=max_hit)

    @property
    def player_states(self) -> dict[Player, PlayerState]:
        """プレイヤーごとの状態を管理する辞書を返す。"""
        return {ply: state for ply, state in zip(self.players, self._player_states)}

    @property
    def actives(self) -> list[Pokemon]:
        """現在場に出ているポケモンのリストを取得。

        Returns:
            list[Pokemon]: 各プレイヤーの場のポケモン
        """
        return [state.active for state in self.player_states.values() if state.active is not None]

    def get_active(self, player: Player) -> Pokemon:
        """指定したプレイヤーの現在場に出ているポケモンを取得。

        Args:
            player: プレイヤー

        Returns:
            Pokemon: 指定したプレイヤーの場のポケモン
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

        ばんのうがさを持つポケモンにはにほんばれ・あめの影響を受けないため、
        天候が晴れ/雨系の場合は「なし」天候を返す。
        エアロック・ノーてんきで天候が無効の場合も「なし」天候を返す。

        Args:
            mon: 対象のポケモン

        Returns:
            Field: 対象ポケモンに有効な天候
        """
        if (
            mon.item.enabled
            and mon.item.name == "ばんのうがさ"
            and self.weather.name in {"はれ", "あめ", "おおひでり", "おおあめ"}
        ):
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

    def foe(self, active: Pokemon) -> Pokemon:
        """指定したポケモンの対戦相手を取得する。

        Args:
            active: 場に出ているポケモン

        Returns:
            Pokemon: 対戦相手のポケモン
        """
        return self.actives[1 - self.actives.index(active)]

    def rival(self, player: Player) -> Player:
        """指定したプレイヤーの対戦相手を取得する。

        Args:
            player: プレイヤー

        Returns:
            Player: 対戦相手のプレイヤー
        """
        return self.players[1 - self.players.index(player)]

    def get_available_commands(self, player: Player) -> list[Command]:
        """指定したプレイヤーが現在使用可能なコマンドのリストを取得する。

        Args:
            player: プレイヤー

        Returns:
            list[Command]: 使用可能なコマンドのリスト
        """
        # 相手の観測状態でコマンドを取得する場合は、最後に利用可能だったコマンドを返す
        if self.observer == self.rival(player):
            return self.player_states[player].last_available_commands

        match self.phase:
            case "action":
                return self.command_manager.get_available_action_commands(player)
            case "switch":
                return self.command_manager.get_available_switch_commands(player)

        raise ValueError(f"Invalid phase: {self.phase}")

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
        # TODO : command_managerに移譲したほうがよいかもしれない。
        """コマンドを解決する。"""
        players = [player] if player else self.players

        with self.phase_context(phase):
            # 方策関数を呼び出す前準備
            for ply in players:
                state = self.player_states[ply]
                # 利用できるコマンドを記録
                state.last_available_commands = self.get_available_commands(ply)
                # 木探索を行う際に補完すべきコマンドタイプを指定
                state.required_command_type = "any" if self.phase == "action" else "switch"

            # コマンドを選択
            commands = {}
            for ply in players:
                sim = self.build_observation(ply)
                commands[ply] = ply.choose_command(sim)
        return commands

    def start(self):
        """バトル開始処理を実行する（TurnControllerへの委譲）。

        選出と初期繰り出しを完了し、以降の `step` を可能にする。
        """
        self.turn_controller.start_battle()

    def step(self, commands: dict[Player, Command] | None = None):
        # turn_controller.step()より前の処理はcommand_managerに移譲したほうがよいかもしれない
        """ターンを1つ進める（TurnControllerへの委譲）。

        Args:
            commands: 各プレイヤーのコマンド辞書。Noneの場合はプレイヤーの方策関数に従う。
        """
        if self.is_new_turn() and commands is None:
            # is_new_turn()だけで判定すると、行動コマンド選択時の木探索でresolve_action_commands()が再帰的に呼ばれてしまうため、command is Noneのガードが必要。
            commands = self.resolve_command("action")
        else:
            for player in self.players:
                command = commands.get(player)
                if not self._validate_command(player, command):
                    raise ValueError(f"Invalid command type for {player.name}: {command}.")

        if not commands:
            raise ValueError("No commands provided for step().")

        self.turn_controller.step(commands)

    def _validate_command(self, player: Player, command: Command | None) -> bool:
        # TODO : command_managerに移譲したほうがよいかもしれない。
        """コマンドがコンテキストに合致しているか検証する。

        Args:
            state: プレイヤーの状態
            command: 実行するコマンド

        Returns:
            bool: コマンドの型が状態に適合する場合は True、そうでない場合は False
        """
        state = self.player_states[player]
        required_type = state.required_command_type
        return (
            command is None
            or required_type in {None, "any"}
            or command.is_type(required_type)
        )

    def run_move(self, attacker: Pokemon, move: Move):
        """技を実行（MoveExecutorへの委譲）。

        Args:
            attacker: 攻撃側のポケモン
            move: 使用する技
        """
        self.move_executor.run_move(attacker, move)

    def change_ability(self, mon: Pokemon, ability: str) -> None:
        """ポケモンの特性を更新する（AbilityManagerへの委譲）。"""
        self.ability_manager.change_ability(mon, ability)

    def gain_item(self, target: Pokemon, item_name: str) -> bool:
        """ポケモンがアイテムを得る（ItemManagerへの委譲）。"""
        return self.item_manager.gain_item(target, item_name)

    def remove_item(self,
                    target: Pokemon,
                    source: Pokemon | None = None) -> bool:
        """ポケモンの道具を喪失状態にする（ItemManagerへの委譲）。"""
        return self.item_manager.remove_item(target, source=source)

    def consume_item(self, mon: Pokemon) -> bool:
        # TODO : item_managerに実装を完全移譲する
        """ポケモンの道具を消費する（ItemManagerへの委譲）。"""
        if mon.item.is_berry():
            mon.ate_berry = True
        return self.item_manager.remove_item(mon, source=mon)

    def force_trigger_berry(self, mon: Pokemon) -> None:
        # TODO : item_managerに移譲してBattleクラスにはメソッドを残さない
        """きのみを強制発動してから消費する。

        ほおばる・おちゃかい等で「HP閾値やターン終了を待たずに即座に」
        きのみ効果を発動させるときに使う。

        発火順:
        1. ON_HP_CHANGED (value=max_hp): HP 閾値ベースのきのみ（オボンのみ等）を対象にする
        2. ON_FORCE_BERRY_TRIGGER: ON_HP_CHANGED に登録されていないきのみ（
           状態異常治療きのみ等）を発動する
        3. まだ消費されていなければ consume_item で明示的に消費する

        Args:
            mon: きのみを強制発動するポケモン
        """
        # HP 閾値ベースのきのみを発動（オボンのみ・フィラのみ等）
        hp_ctx = EventContext(target=mon, source=mon)
        self.events.emit(Event.ON_HP_CHANGED, hp_ctx, mon.max_hp)
        # HP 閾値チェックなしで発動するきのみ（状態異常治療きのみ等）
        if mon.item.is_berry():
            force_ctx = EventContext(source=mon)
            self.events.emit(Event.ON_FORCE_BERRY_TRIGGER, force_ctx)
        # いずれの発火でも消費されなかった場合は明示的に消費する
        if mon.item.is_berry():
            self.consume_item(mon)

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
            r: 最大HPに対する割合（-1.0～1.0）。v と同時指定時は r が優先される。r !=0 なら v も有限
            source: ダメージ源のポケモン
            reason: 変更の理由

        Returns:
            実際に変化したHP量（正=回復、負=ダメージ）
        """
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
                    move: Move | str,
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
        return self.random.choice(damages)

    def calc_damages(self,
                     attacker: Pokemon,
                     defender: Pokemon,
                     move: Move | str,
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
        if isinstance(source, Pokemon) and payload is not None and "pokemon" not in payload:
            payload = {"pokemon": source.name, **payload}
        elif isinstance(source, Pokemon) and payload is None:
            payload = {"pokemon": source.name}
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

    def resolve_move_category(self, attacker: Pokemon, move: Move) -> MoveCategory:
        # TODO : battle.queryに移譲してBattleクラスから削除すべきかもしれない
        """実際の技カテゴリを判定する（MoveExecutorへの委譲）。

        Args:
            move: 技オブジェクト
            attacker: 技を使用するポケモン

        Returns:
            有効な技のカテゴリ（"物理"、"特殊"、"変化"のいずれか）
        """
        return self.move_executor.resolve_move_category(attacker, move)

    def add_ability_disabled_reason(self, mon: Pokemon, reason: AbilityDisabledReason) -> bool:
        """特性の無効化理由を追加する（AbilityManagerへの委譲）。"""
        return self.ability_manager.add_disabled_reason(mon, reason)

    def remove_ability_disabled_reason(self, mon: Pokemon, reason: AbilityDisabledReason) -> bool:
        """特性の無効化理由を削除する（AbilityManagerへの委譲）。"""
        return self.ability_manager.remove_disabled_reason(mon, reason)

    def add_item_disabled_reason(self, mon: Pokemon, reason: ItemDisabledReason) -> bool:
        """道具の無効化理由を追加する（ItemManagerへの委譲）。"""
        return self.item_manager.add_disabled_reason(mon, reason)

    def remove_item_disabled_reason(self, mon: Pokemon, reason: ItemDisabledReason) -> bool:
        """道具の無効化理由を削除する（ItemManagerへの委譲）。"""
        return self.item_manager.remove_disabled_reason(mon, reason)

    def resolve_secondary_chance(self, ctx: EventContext, chance: float) -> float:
        """追加効果補正後の実効確率を返す。"""
        if self.test_option.secondary_chance is not None:
            return self.test_option.secondary_chance
        return self.events.emit(Event.ON_MODIFY_SECONDARY_CHANCE, ctx, chance)

    def can_switch(self, player: Player) -> bool:
        # TODO : 実装をswitch_managerからqueryに移譲して、Battleクラスのメソッドは廃止したほうがよいかもしれない。
        """プレイヤーが交代可能かどうかを判定する（SwitchManagerへの委譲）。"""
        state = self.player_states[player]
        return self.switch_manager.can_switch(state)

    def print_logs(self, turn: int | None = None):
        """指定したターンのログを整形して出力。

        Args:
            turn: ターン番号（Noneの場合は現在のターン）
        """
        if turn is None:
            turn = self.turn

        event_logs = [log for log in self.event_logger.logs if log.turn == turn]
        for log in event_logs:
            player = self.players[log.idx]
            pokemon = log.payload.get("pokemon", "") if log.payload else ""
            print(f"Turn {turn} : {player.name} : {pokemon} : {log.render()}")

    def remove_all_volatiles(self, mon: Pokemon):
        """対象のポケモンからすべての揮発性状態を解除する（VolatileManagerへの委譲）。"""
        self.volatile_manager.remove_all(mon)
