"""ポケモンバトルのメインロジックを管理するモジュール。

バトル全体の状態管理、ターン進行、イベント処理、ログ記録などを統括します。
プレイヤー、ポケモン、技、場の状態などを一元管理し、バトルの進行を制御します。
"""
from typing import Self
from dataclasses import dataclass

import time
import json
from random import Random
from copy import deepcopy

from jpoke.utils.type_defs import Stat, GlobalField, SideField, ItemLostCause, HPChangeReason
from jpoke.enums import Event, Command, Interrupt, LogCode
from jpoke.utils import fast_copy

from jpoke.model import Pokemon, Move, Field, Item

from .event_manager import EventManager
from .context import BattleContext
from .player import Player
from .event_logger import EventLogger
from .command_logger import CommandLogger
from .damage import DamageCalculator, DamageContext
from .field_manager import WeatherManager, TerrainManager, GlobalFieldManager, SideFieldManager
from .move_executor import MoveExecutor
from .switch import SwitchManager
from .turn import TurnController
from .speed import SpeedCalculator
from .item_manager import ItemManager
from .command_manager import CommandManager
from .ability_manager import AbilityManager
from .pokemon_state import AilmentManager, VolatileManager, PokemonQuery, StatusManager


@dataclass
class TestOption:
    """テスト用オプション設定クラス。

    Attributes:
        accuracy: 命中率の固定値（Noneの場合は通常計算）
        trigger_ailment: 状態異常の確率的発動の固定値（Noneの場合は通常の乱数判定）
            例: True = 必ず発動, False = 必ず発動しない
        trigger_volatile: 変動状態の確率的発動の固定値（Noneの場合は通常の乱数判定）
            例: True = 必ず発動, False = 必ず発動しない
    """
    accuracy: int | None = None
    trigger_ailment: bool | None = None
    trigger_volatile: bool | None = None


class Battle:
    """ポケモンバトルの状態と処理を管理するメインクラス。

    バトル全体の状態、ターン管理、イベントシステム、ログ記録、
    各種マネージャークラスを統括します。

    Attributes:
        players: 参加プレイヤーのリスト（通常2人）
        seed: 乱数シード値
        turn: 現在のターン数
        winner_idx: 勝者のインデックス（勝負がついていない場合はNone）
        events: イベント管理システム
        logger: バトルログ記録システム
        random: 乱数生成器
        damage_calculator: ダメージ計算機
        move_executor: 技実行管理
        switch_manager: 交代管理
        turn_controller: ターン進行制御
        speed_calculator: 素早さ計算機
        weather_manager: 天候管理
        terrain_manager: フィールド管理
        field_manager: グローバル場の状態管理
        side_manager: 各プレイヤー側の場の状態管理
        test_option: テスト用オプション設定
    """

    def __init__(self,
                 players: list[Player],
                 seed: int | None = None) -> None:
        """Battleインスタンスを初期化する。

        Args:
            players: 参加プレイヤーのリスト（通常2人）
            seed: 乱数シード値（Noneの場合は現在時刻を使用）
        """

        if seed is None:
            seed = int(time.time())

        self.players: list[Player] = players
        self.seed: int = seed

        self.turn: int = -1
        self.winner_idx: int | None = None

        self.random = Random(self.seed)
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
        self.query_manager: PokemonQuery = PokemonQuery(self)
        self.status_manager: StatusManager = StatusManager(self)
        self.item_manager: ItemManager = ItemManager(self)
        self.command_manager: CommandManager = CommandManager(self)
        self.ability_manager: AbilityManager = AbilityManager(self)

        self.weather_manager: WeatherManager = WeatherManager(self)
        self.terrain_manager: TerrainManager = TerrainManager(self)
        self.field_manager: GlobalFieldManager = GlobalFieldManager(self)
        self.side_manager: list[SideFieldManager] = [
            SideFieldManager(self, player) for player in self.players
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
        fast_copy(self, new, keys_to_deepcopy=[
            "players", "events", "event_logger", "command_logger", "random",
            "turn_controller", "speed_calculator", "switch_manager",
            "move_executor", "damage_calculator",
            "ailment_manager", "volatile_manager", "query_manager",
            "status_manager", "item_manager",
            "command_manager", "ability_manager",
            "weather_manager", "terrain_manager", "field_manager", "side_manager",
        ])

        # 複製したBattleインスタンスへの参照を各マネージャークラスに更新
        new._update_reference()

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
        self.query_manager.update_reference(self)
        self.status_manager.update_reference(self)
        self.item_manager.update_reference(self)
        self.command_manager.update_reference(self)
        self.ability_manager.update_reference(self)

        self.weather_manager.update_reference(self)
        self.terrain_manager.update_reference(self)
        self.field_manager.update_reference(self)
        for i, side in enumerate(self.side_manager):
            side.update_reference(self, self.players[i])

    def init_game(self):
        """ゲーム初期化。
        """
        # 管理クラスの初期化
        self.events = EventManager(self)
        self.event_logger = EventLogger()
        self.command_logger = CommandLogger()
        self.random = Random(self.seed)

        self.turn_controller = TurnController(self)
        self.speed_calculator = SpeedCalculator(self)
        self.switch_manager = SwitchManager(self)
        self.move_executor = MoveExecutor(self)
        self.damage_calculator = DamageCalculator(self)
        self.ailment_manager = AilmentManager(self)
        self.volatile_manager = VolatileManager(self)
        self.query_manager = PokemonQuery(self)
        self.status_manager = StatusManager(self)
        self.item_manager = ItemManager(self)
        self.command_manager = CommandManager(self)
        self.ability_manager = AbilityManager(self)

        self.weather_manager = WeatherManager(self)
        self.terrain_manager = TerrainManager(self)
        self.field_manager = GlobalFieldManager(self)
        self.side_manager = [SideFieldManager(self, player) for player in self.players]

        # 各プレイヤーとポケモンの初期化
        for player in self.players:
            player.init_game()

    def init_turn(self):
        """ターン初期化（TurnControllerへの委譲）。"""
        self.turn_controller.init_turn()

    @property
    def actives(self) -> list[Pokemon]:
        """現在場に出ているポケモンのリストを取得。

        Returns:
            list[Pokemon]: 各プレイヤーの場のポケモン
        """
        return [player.active for player in self.players]

    @property
    def raw_weather(self) -> Field:
        """現在セットされている天候を取得。

        Returns:
            Field: 現在セットされている天候フィールド
        """
        return self.weather_manager.current

    @property
    def weather(self) -> Field:
        """有効な天候オブジェクトを返す。判定ロジックは WeatherManager に委譲する。"""
        return self.weather_manager.active

    @property
    def terrain(self) -> Field:
        """現在のフィールド状態を取得。

        Returns:
            Field: 現在のフィールド
        """
        return self.terrain_manager.current

    def get_global_field(self, name: GlobalField) -> Field:
        """グローバルフィールド効果を取得。"""
        return self.field_manager.fields[name]

    def get_side(self, source: Player | Pokemon) -> SideFieldManager:
        """プレイヤーまたはポケモンからサイドフィールドマネージャーを取得。

        Args:
            source: Player または Pokemon インスタンス

        Returns:
            SideFieldManager: 対応するサイドフィールドマネージャー
        """
        return self.side_manager[self.get_player_index(source)]

    def get_side_field(self, source: Player | Pokemon, name: SideField) -> Field:
        """サイドフィールド効果を取得。

        Args:
            source: Player または Pokemon インスタンス
            name: フィールド効果の名前

        Returns:
            Field: 対応するサイドフィールド効果
        """
        return self.get_side(source).fields[name]

    def export_log(self, file):
        """バトルログをJSON形式でエクスポート。

        Args:
            file: 出力先ファイルパス
        """
        players_data = []
        for player in self.players:
            players_data.append({
                "name": player.name,
                "selection_indexes": player.selection_idxes,
                "team": [mon.to_dict() for mon in player.team],
            })

        self.event_logger.export(file, self.seed, players_data)

    def masked_copy(self, perspective: Player) -> Self:
        # TODO (copilotには任せない) implement more detailed masking
        """指定したプレイヤー視点で情報を隠蔽した Battle インスタンスのコピーを作成。
        Args:
            perspective: 情報を完全に保持するプレイヤー

        Returns:
            Battle インスタンスのコピー
        """
        new = deepcopy(self)

        # 乱数の隠蔽
        new.random.seed(int(time.time()))

        return new

    def find_player(self, mon: Pokemon) -> Player:
        """ポケモンが所属するプレイヤーを検索する。

        Args:
            mon: 検索対象のポケモン

        Returns:
            Player: ポケモンを所有するプレイヤー

        Raises:
            Exception: ポケモンが見つからない場合
        """
        return self.players[self.find_player_index(mon)]

    def find_player_index(self, mon: Pokemon) -> int:
        """ポケモンが所属するプレイヤーのインデックスを検索する。

        Args:
            mon: 検索対象のポケモン

        Returns:
            int: プレイヤーのインデックス（0または1）

        Raises:
            Exception: ポケモンが見つからない場合
        """
        for i, player in enumerate(self.players):
            if mon in player.team:
                return i
        raise Exception("Player not found.")

    def get_player_index(self, source: Player | Pokemon) -> int:
        """プレイヤーまたはポケモンからプレイヤーインデックスを取得。

        Args:
            source: Player または Pokemon インスタンス

        Returns:
            プレイヤーインデックス (0 or 1)
        """
        if isinstance(source, Player):
            return self.players.index(source)
        elif isinstance(source, Pokemon):
            return self.find_player_index(source)
        raise ValueError(f"Invalid source type: {type(source)}")

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

    def get_available_selection_commands(self, player: Player) -> list[Command]:
        """ポケモン選出時に使用可能なコマンドを取得する。

        Args:
            player: プレイヤー

        Returns:
            list[Command]: 選出可能なコマンドのリスト
        """
        return self.command_manager.get_available_selection_commands(player)

    def get_available_switch_commands(self, player: Player) -> list[Command]:
        """交代可能なコマンドのリストを取得する。

        Args:
            player: プレイヤー

        Returns:
            list[Command]: 交代可能なコマンドのリスト（交代不可の場合は空リスト）
        """
        return self.command_manager.get_available_switch_commands(player)

    def get_available_action_commands(self, player: Player) -> list[Command]:
        """行動時に使用可能なコマンドを取得する。

        技コマンド、テラスタルコマンド、交代コマンドを含みます。

        Args:
            player: プレイヤー

        Returns:
            list[Command]: 使用可能なコマンドのリスト
        """
        return self.command_manager.get_available_action_commands(player)

    def calc_effective_speed(self, mon: Pokemon) -> int:
        """実効素早さを計算（SpeedCalculatorへの委譲）。

        Args:
            mon: 対象のポケモン

        Returns:
            補正後の実効素早さ
        """
        return self.speed_calculator.calc_effective_speed(mon)

    def determine_speed_order(self) -> list[Pokemon]:
        """素早さ順序を計算（SpeedCalculatorへの委譲）。

        Returns:
            素早さの速い順にソートされたポケモンのリスト
        """
        return self.speed_calculator.calc_speed_order()

    def determine_action_order(self) -> list[Pokemon]:
        """行動順序を計算（SpeedCalculatorへの委譲）。

        Returns:
            行動順にソートされたポケモンのリスト
        """
        return self.speed_calculator.calc_action_order()

    def refresh_effect_enabled_states(self):
        """場の状況に応じて特性・アイテム効果の有効/無効状態を再計算する。
        特性とアイテムは相互に影響を与える可能性があるため、両方を再計算し、結果が安定するまで繰り返す。
        """
        prev_results = {}
        while True:
            results = {}
            results |= self.ability_manager.refresh_ability_enabled_states()
            results |= self.item_manager.refresh_item_enabled_states()
            if results == prev_results:
                break
            prev_results = results

    def determine_tod_score(self, player: Player, alpha: float = 1) -> float:
        """TODスコアを計算（TurnControllerへの委譲）。

        Args:
            player: スコアを計算するプレイヤー
            alpha: HP割合の重み係数

        Returns:
            TODスコア
        """
        return self.turn_controller.calc_tod_score(player, alpha)

    def judge_winner(self) -> Player | None:
        """勝者を判定（TurnControllerへの委譲）。

        Returns:
            勝者のPlayerインスタンス、勝負がついていない場合はNone
        """
        return self.turn_controller.judge_winner()

    def run_selection(self):
        """ポケモン選出処理（TurnControllerへの委譲）。"""
        self.turn_controller.run_selection()

    def start(self):
        """バトル開始処理を実行する（TurnControllerへの委譲）。

        選出と初期繰り出しを完了し、以降の `advance_turn` を可能にする。
        """
        self.turn_controller.start()

    def check_hit(self, attacker: Pokemon, move: Move) -> bool:
        """技の命中判定（MoveExecutorへの委譲）。

        Args:
            attacker: 攻撃側のポケモン
            move: 使用する技

        Returns:
            命中した場合True
        """
        return self.move_executor.check_hit(attacker, move)

    def run_move(self, attacker: Pokemon, move: Move):
        """技を実行（MoveExecutorへの委譲）。

        Args:
            attacker: 攻撃側のポケモン
            move: 使用する技
        """
        self.move_executor.run_move(attacker, move)

    def set_item(self, target: Pokemon, item: str | Item) -> None:
        """ポケモンの持ち物を更新する（ItemManagerへの委譲）。"""
        self.item_manager.set_item(target, item)

    def lose_item(self, target: Pokemon, cause: ItemLostCause = "remove") -> bool:
        """ポケモンの道具を喪失状態にする（ItemManagerへの委譲）。"""
        return self.item_manager.lose_item(target, cause=cause)

    def consume_item(self, target: Pokemon) -> bool:
        """ポケモンの道具を消費する（ItemManagerへの委譲）。"""
        # TODO : アイテム消費時のログ記入までItemManagerに任せるべきか検討
        return self.item_manager.consume_item(target)

    def set_ability(self,
                    target: Pokemon,
                    ability_name: str,
                    refresh_enabled_states: bool = True) -> None:
        """ポケモンの特性を更新する（AbilityManagerへの委譲）。"""
        self.ability_manager.set_ability(
            target,
            ability_name,
            refresh_enabled_states=refresh_enabled_states,
        )

    def can_change_item(self,
                        source: Pokemon,
                        target: Pokemon,
                        move: Move | None = None,
                        reason: str = "") -> bool:
        """持ち物変更可否を判定する（ItemManagerへの委譲）。"""
        return self.item_manager.can_change_item(source, target, move=move, reason=reason)

    def swap_items(self, source: Pokemon, target: Pokemon, move: Move | None = None) -> bool:
        """2体の持ち物を入れ替える（ItemManagerへの委譲）。"""
        return self.item_manager.swap_items(source, target, move=move)

    def take_item(self,
                  source: Pokemon,
                  target: Pokemon,
                  move: Move | None = None,
                  reason: ItemLostCause = "steal") -> bool:
        """対象の持ち物を source に移す（ItemManagerへの委譲）。"""
        return self.item_manager.take_item(source, target, move=move, reason=reason)

    def remove_item(self,
                    source: Pokemon,
                    target: Pokemon,
                    move: Move | None = None,
                    reason: ItemLostCause = "remove",
                    check_on_empty: bool = False) -> bool:
        """対象の持ち物を失わせる（ItemManagerへの委譲）。"""
        return self.item_manager.remove_item(
            source,
            target,
            move=move,
            reason=reason,
            check_on_empty=check_on_empty,
        )

    def command_to_move(self, player: Player, command: Command) -> Move:
        """コマンドから技オブジェクトを取得。

        Args:
            player: プレイヤー
            command: 実行するコマンド

        Returns:
            技オブジェクト
        """
        return self.command_manager.command_to_move(player, command)

    def modify_hp(
        self,
        target: Pokemon,
        v: int = 0,
        r: float = 0,
        reason: HPChangeReason = "other",
        source: Pokemon | None = None,
        move: Move | None = None,
    ) -> int:
        """ポケモンのHPを変更する（StatusManagerへの委譲）。"""
        return self.status_manager.modify_hp(target, v=v, r=r, reason=reason, source=source, move=move)

    def modify_stat(self,
                    target: Pokemon,
                    stat: Stat,
                    v: int,
                    source: Pokemon | None = None,
                    reason: str = "") -> dict[Stat, int]:
        """ポケモンの能力ランクを変更する（StatusManagerへの委譲）。"""
        return self.status_manager.modify_stat(target, stat, v, source=source, reason=reason)

    def modify_stats(self,
                     target: Pokemon,
                     stats: dict[Stat, int],
                     source: Pokemon | None = None,
                     reason: str = "") -> dict[Stat, int]:
        """ポケモンの複数の能力ランクを同時に変更する（StatusManagerへの委譲）。"""
        return self.status_manager.modify_stats(target, stats, source=source, reason=reason)

    def determine_damage(self,
                         attacker: Pokemon,
                         defender: Pokemon,
                         move: Move | str,
                         critical: bool = False) -> int:
        """ダメージを計算してランダムに1つ選択する。

        Args:
            attacker: 攻撃側のポケモン
            move: 使用する技（MoveオブジェクトまたはID文字列）
            critical: 急所に当たるかどうか
            self_harm: 自分自身へのダメージかどうか

        Returns:
            int: 計算されたダメージ値
        """
        damages = self.determine_damage_range(attacker, defender, move, critical)
        return self.random.choice(damages)

    def determine_damage_range(self,
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
        dmg_ctx = DamageContext(critical=critical)
        damages, dmg_ctx = self.damage_calculator.calc_damage_range(
            attacker, defender, move, dmg_ctx)
        return damages

    def has_interrupt(self) -> bool:
        """割り込みフラグが設定されているか確認（SwitchManagerへの委譲）。

        Returns:
            いずれかのプレイヤーに割り込みフラグがある場合True
        """
        return self.switch_manager.has_interrupt()

    def override_interrupt(self, flag: Interrupt, only_first: bool = True):
        """割り込みフラグを上書き（SwitchManagerへの委譲）。

        Args:
            flag: 設定する割り込みフラグ
            only_first: 最初の1体のみに設定する場合True
        """
        self.switch_manager.override_interrupt(flag, only_first)

    def run_switch(self, player: Player, new: Pokemon, emit: bool = True):
        """ポケモンを交代（SwitchManagerへの委譲）。

        Args:
            player: 交代を行うプレイヤー
            new: 場に出す新しいポケモン
            emit: ON_SWITCH_INイベントを発火する場合True
        """
        self.switch_manager.run_switch(player, new, emit)

    def run_initial_switch(self):
        """バトル開始時の初期交代（SwitchManagerへの委譲）。"""
        self.switch_manager.run_initial_switch()

    def run_interrupt_switch(self, flag: Interrupt, emit_on_each_switch: bool = True):
        """割り込み交代を実行（SwitchManagerへの委譲）。

        Args:
            flag: 対象とする割り込みフラグ
            emit_on_each_switch: 各交代ごとにON_SWITCH_INを発火する場合True
        """
        self.switch_manager.run_interrupt_switch(flag, emit_on_each_switch)

    def run_faint_switch(self):
        """瀕死による交代を実行（SwitchManagerへの委議）。"""
        self.switch_manager.run_faint_switch()

    def add_command_log(self, source: Player | Pokemon, command: Command):
        """コマンドログを追加。

        Args:
            source: Player または Pokemon インスタンス
            command: 選択されたコマンド
        """
        idx = self.get_player_index(source)
        self.command_logger.add(self.turn, idx, command)

    def add_event_log(self,
                      source: Player | Pokemon | int,
                      log: LogCode,
                      payload: dict | None = None):
        """イベントログを追加。

        Args:
            source: Player または Pokemon インスタンス、またはプレイヤーインデックス
            log: イベントの内容を表すLogCode列挙値 
            payload: イベントの詳細情報（必要に応じて）
        """
        if isinstance(source, int):
            idx = source
        else:
            idx = self.get_player_index(source)
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

    def advance_turn(self, commands: dict[Player, Command] | None = None):
        """ターンを進める（TurnControllerへの委譲）。

        Args:
            commands: 各プレイヤーのコマンド辞書。Noneの場合はプレイヤーの方策関数に従い、そうでなければ引数のコマンドを使用。
        """
        self.turn_controller.advance_turn(commands)
