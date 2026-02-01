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

from jpoke.utils.type_defs import Stat
from jpoke.utils.enums import Command, Interrupt
from jpoke.utils import fast_copy

from jpoke.model import Pokemon, Move, Field

from .event import Event, EventManager, EventContext
from .player import Player
from .logger import Logger
from .damage import DamageCalculator, DamageContext
from .field_manager import WeatherManager, TerrainManager, GlobalFieldManager, SideFieldManager
from .move_executor import MoveExecutor
from .switch_manager import SwitchManager
from .turn_controller import TurnController
from .speed_calculator import SpeedCalculator


@dataclass
class TestOption:
    """テスト用オプション設定クラス。

    Attributes:
        accuracy: 命中率の固定値（Noneの場合は通常計算）
        ailment_trigger_rate: 状態異常の確率的発動の固定値（Noneの場合は通常の乱数判定）
            例: 1.0 = 必ず発動, 0.0 = 必ず発動しない
    """
    accuracy: int | None = None
    ailment_trigger_rate: float | None = None


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
        weather_mgr: 天候管理
        terrain_mgr: フィールド管理
        field_mgr: グローバル場の状態管理
        side_mgrs: 各プレイヤー側の場の状態管理
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

        self.events = EventManager(self)
        self.logger = Logger()
        self.random = Random(self.seed)
        self.damage_calculator: DamageCalculator = DamageCalculator()
        self.move_executor: MoveExecutor = MoveExecutor(self)
        self.switch_manager: SwitchManager = SwitchManager(self)
        self.turn_controller: TurnController = TurnController(self)
        self.speed_calculator: SpeedCalculator = SpeedCalculator(self)

        self.weather_mgr: WeatherManager = WeatherManager(self.events, self.players)
        self.terrain_mgr: TerrainManager = TerrainManager(self.events, self.players)
        self.field_mgr: GlobalFieldManager = GlobalFieldManager(self.events, self.players)
        self.side_mgrs: list[SideFieldManager] = [SideFieldManager(self.events, pl) for pl in self.players]

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
            "players", "events", "logger", "random", "damage_calculator",
            "move_executor", "switch_manager", "turn_controller", "speed_calculator",
            "field_mgr", "side_mgrs"
        ])

        # 複製したインスタンスが複製後を参照するように再代入する
        new._update_reference()

        return new

    def _update_reference(self):
        """Battle インスタンスの参照を各マネージャークラスに更新する。"""
        self.events.update_reference(self)
        self.move_executor.update_reference(self)
        self.switch_manager.update_reference(self)
        self.turn_controller.update_reference(self)
        self.speed_calculator.update_reference(self)
        self.field_mgr.update_reference(self.events, self.players)
        for i, side in enumerate(self.side_mgrs):
            side.update_reference(self.events, self.players[i])

    def init_game(self):
        """ゲーム初期化。
        """
        # 管理クラスの初期化
        self.events = EventManager(self)
        self.logger = Logger()
        self.random = Random(self.seed)
        self.damage_calculator = DamageCalculator()
        self.move_executor = MoveExecutor(self)
        self.switch_manager = SwitchManager(self)
        self.turn_controller = TurnController(self)
        self.speed_calculator = SpeedCalculator(self)

        self.weather_mgr = WeatherManager(self.events, self.players)
        self.terrain_mgr = TerrainManager(self.events, self.players)
        self.field_mgr = GlobalFieldManager(self.events, self.players)
        self.side_mgrs = [SideFieldManager(self.events, pl) for pl in self.players]

        # 各プレイヤーとポケモンの初期化
        for player in self.players:
            player.init_game()

    def init_turn(self):
        """ターン初期化（TurnControllerへの委譲）。"""
        self.turn_controller.init_turn()

    def get_side(self, source: Player | Pokemon) -> SideFieldManager:
        """プレイヤーまたはポケモンからサイドフィールドマネージャーを取得。

        Args:
            source: Player または Pokemon インスタンス

        Returns:
            SideFieldManager: 対応するサイドフィールドマネージャー
        """
        return self.side_mgrs[self.get_player_index(source)]

    @property
    def actives(self) -> list[Pokemon]:
        """現在場に出ているポケモンのリストを取得。

        Returns:
            list[Pokemon]: 各プレイヤーの場のポケモン
        """
        return [pl.active for pl in self.players]

    @property
    def weather(self) -> Field:
        """現在の天候を取得。

        Returns:
            Field: 現在の天候フィールド
        """
        return self.weather_mgr.current

    @property
    def terrain(self) -> Field:
        """現在のフィールド状態を取得。

        Returns:
            Field: 現在のフィールド
        """
        return self.terrain_mgr.current

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

        self.logger.export_log(file, self.seed, players_data)

    @classmethod
    def reconstruct_from_log(cls, file) -> Self:
        """ログファイルからBattleインスタンスを再構築する。

        Args:
            file: ログファイルのパス

        Returns:
            Self: 再構築されたBattleインスタンス
        """
        with open(file, encoding="utf-8") as f:
            data = json.load(f)

        new = cls(
            [Player(), Player()],
            seed=data["seed"],
        )

        for i, player in enumerate(new.players):
            player_data = data["players"][i]
            player.name = player_data["name"]
            player.selection_idxes = player_data["selection_indexes"]

            for p in player_data["team"]:
                mon = Pokemon.reconstruct_from_log(p)
                player.team.append(mon)

            for t, command_names in player_data["commands"].items():
                for s in command_names:
                    command = Command[s]
                    player.reserve_command(command)

        return new

    def masked_copy(self, perspective: Player) -> Self:
        # TODO: implement more detailed masking
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
        for player in self.players:
            if mon in player.team:
                return player
        raise Exception("Player not found.")

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
        return self.actives[not self.actives.index(active)]

    def rival(self, player: Player) -> Player:
        """指定したプレイヤーの対戦相手を取得する。

        Args:
            player: プレイヤー

        Returns:
            Player: 対戦相手のプレイヤー
        """
        return self.players[not self.players.index(player)]

    def get_available_selection_commands(self, player: Player) -> list[Command]:
        """ポケモン選出時に使用可能なコマンドを取得する。

        Args:
            player: プレイヤー

        Returns:
            list[Command]: 選出可能なコマンドのリスト
        """
        return Command.selection_commands()[:len(player.team)]

    def get_available_switch_commands(self, player: Player) -> list[Command]:
        """交代可能なコマンドのリストを取得する。

        Args:
            player: プレイヤー

        Returns:
            list[Command]: 交代可能なコマンドのリスト（交代不可の場合は空リスト）
        """
        if player.active.is_trapped(self.events):
            return []
        return [cmd for mon, cmd in zip(player.team, Command.switch_commands())
                if mon in player.selection and mon is not player.active]

    def get_available_action_commands(self, player: Player) -> list[Command]:
        """行動時に使用可能なコマンドを取得する。

        技コマンド、テラスタルコマンド、交代コマンドを含みます。

        Args:
            player: プレイヤー

        Returns:
            list[Command]: 使用可能なコマンドのリスト
        """
        n = len(player.active.moves)

        # 通常技
        commands = Command.move_commands()[:n]

        # テラスタル
        if player.can_use_terastal():
            commands += Command.terastal_commands()[:n]

        # わるあがき
        if not commands:
            commands = [Command.STRUGGLE]

        # 交代コマンド
        commands += self.get_available_switch_commands(player)

        return commands

    def calc_effective_speed(self, mon: Pokemon) -> int:
        """実効素早さを計算（SpeedCalculatorへの委譲）。

        Args:
            mon: 対象のポケモン

        Returns:
            補正後の実効素早さ
        """
        return self.speed_calculator.calc_effective_speed(mon)

    def calc_speed_order(self) -> list[Pokemon]:
        """素早さ順序を計算（SpeedCalculatorへの委譲）。

        Returns:
            素早さの速い順にソートされたポケモンのリスト
        """
        return self.speed_calculator.calc_speed_order()

    def calc_action_order(self) -> list[Pokemon]:
        """行動順序を計算（SpeedCalculatorへの委譲）。

        Returns:
            行動順にソートされたポケモンのリスト
        """
        return self.speed_calculator.calc_action_order()

    def calc_tod_score(self, player: Player, alpha: float = 1) -> float:
        """TODスコアを計算（TurnControllerへの委譲）。

        Args:
            player: スコアを計算するプレイヤー
            alpha: HP割合の重み係数

        Returns:
            TODスコア
        """
        return self.turn_controller.calc_tod_score(player, alpha)

    def winner(self) -> Player | None:
        """勝者を判定（TurnControllerへの委譲）。

        Returns:
            勝者のPlayerインスタンス、勝負がついていない場合はNone
        """
        return self.turn_controller.judge_winner()

    def run_selection(self):
        """ポケモン選出処理（TurnControllerへの委譲）。"""
        self.turn_controller.run_selection()

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

    def command_to_move(self, player: Player, command: Command) -> Move:
        """コマンドから技オブジェクトを取得（MoveExecutorへの委譲）。

        Args:
            player: プレイヤー
            command: 実行するコマンド

        Returns:
            技オブジェクト
        """
        return self.move_executor.command_to_move(player, command)

    def modify_hp(self, target: Pokemon, v: int = 0, r: float = 0) -> bool:
        """ポケモンのHPを変更する。

        Args:
            target: 対象のポケモン
            v: 変更する固定HP量
            r: 最大HPに対する割合（0.0～1.0）

        Returns:
            bool: HP変更が成功した場合True
        """
        if r:
            v = int(target.max_hp * r)
        if v and (v := target.modify_hp(v)):
            self.add_event_log(self.find_player(target),
                               f"HP {'+' if v >= 0 else ''}{v} >> {target.hp}")
        return bool(v)

    def drain_hp(self, from_: Pokemon, to_: Pokemon, v: int = 0, r: float = 0) -> tuple[bool, bool]:
        """HPを吸収。
        Args:
            from_: HPを吸収されるポケモン
            to_: HPを吸収するポケモン
            v: 固定値で吸収するHP量
            r: 最大HP割合で吸収するHP量

        Returns:
            成功したかどうかのタプル（吸収される側、吸収する側）
        """
        if r:
            v = int(from_.max_hp * r)
        success = self.modify_hp(from_, -v)
        if success:
            return success, self.modify_hp(to_, v)
        return success, False

    def modify_stat(self,
                    target: Pokemon,
                    stat: Stat,
                    v: int,
                    source: Pokemon | None = None) -> bool:
        """ポケモンの能力ランクを変更する。

        Args:
            target: 対象のポケモン
            stat: 変更する能力値（"A", "B", "C", "D", "S"）
            v: 変更するランク数
            source: 変更の原因となったポケモン（Noneの場合もある）

        Returns:
            bool: ランク変更が成功した場合True
        """
        if v and (v := target.modify_stat(stat, v)):
            self.add_event_log(self.find_player(target),
                               f"{stat}{'+' if v >= 0 else ''}{v}")
            self.events.emit(
                Event.ON_MODIFY_STAT,
                EventContext(target=target, source=source),
                v
            )
            return True
        return False

    def calc_damage(self,
                    attacker: Pokemon,
                    move: Move | str,
                    critical: bool = False,
                    self_harm: bool = False) -> int:
        """ダメージを計算してランダムに1つ選択する。

        Args:
            attacker: 攻撃側のポケモン
            move: 使用する技（MoveオブジェクトまたはID文字列）
            critical: 急所に当たるかどうか
            self_harm: 自分自身へのダメージかどうか

        Returns:
            int: 計算されたダメージ値
        """
        damages = self.calc_damages(attacker, move, critical, self_harm)
        return self.random.choice(damages)

    def calc_damages(self,
                     attacker: Pokemon,
                     move: Move | str,
                     critical: bool = False,
                     self_harm: bool = False) -> list[int]:
        """可能なダメージ値のリストを計算する。

        乱数によるダメージ幅を考慮した全ての可能なダメージ値を返します。

        Args:
            attacker: 攻撃側のポケモン
            move: 使用する技（MoveオブジェクトまたはID文字列）
            critical: 急所に当たるかどうか
            self_harm: 自分自身へのダメージかどうか

        Returns:
            list[int]: 可能なダメージ値のリスト
        """
        if isinstance(move, str):
            move = Move(move)
        defender = attacker if self_harm else self.foe(attacker)
        ctx = DamageContext(critical, self_harm)
        damages, ctx = self.damage_calculator.single_hit_damages(self.events, attacker, defender, move, ctx)
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
        self.logger.add_command_log(self.turn, idx, command)

    def add_event_log(self, source: Player | Pokemon, text: str):
        """イベントログを追加。

        Args:
            source: Player または Pokemon インスタンス
            text: イベントの内容
        """
        idx = self.get_player_index(source)
        self.logger.add_event_log(self.turn, idx, text)

    def add_damage_log(self, source: Player | Pokemon, text: str):
        """ダメージログを追加。

        Args:
            source: Player または Pokemon インスタンス
            text: ダメージの詳細情報
        """
        idx = self.get_player_index(source)
        self.logger.add_damage_log(self.turn, idx, text)

    def get_event_logs(self, turn: int | None = None) -> dict[Player, list[str]]:
        """指定したターンの全プレイヤーのイベントログを取得。

        Args:
            turn: ターン番号（Noneの場合は現在のターン）

        Returns:
            Playerをキーとしたイベントテキストのリストの辞書
        """
        if turn is None:
            turn = self.turn
        return {player: self.logger.get_event_logs(turn, i)
                for i, player in enumerate(self.players)}

    def get_damage_logs(self, turn: int | None = None) -> dict[Player, list[str]]:
        """指定したターンの全プレイヤーのダメージログを取得。

        Args:
            turn: ターン番号（Noneの場合は現在のターン）

        Returns:
            Playerをキーとしたダメージテキストのリストの辞書
        """
        if turn is None:
            turn = self.turn
        return {player: self.logger.get_damage_logs(turn, i)
                for i, player in enumerate(self.players)}

    def print_logs(self, turn: int | None = None):
        """指定したターンのログを整形して出力。

        Args:
            turn: ターン番号（Noneの場合は現在のターン）
        """
        if turn is None:
            turn = self.turn

        print(f"Turn {turn}")
        for i, player in enumerate(self.players):
            event_logs = self.logger.get_event_logs(turn, i)
            damage_logs = self.logger.get_damage_logs(turn, i)
            print(f"\t{player.name}\t{event_logs} {damage_logs}")

    def advance_turn(self, commands: dict[Player, Command] | None = None):
        """ターンを進める（TurnControllerへの委譲）。

        Args:
            commands: 各プレイヤーのコマンド辞書（Noneの場合は予約済みコマンドを使用）
        """
        self.turn_controller.advance_turn(commands)

    def _advance_turn(self):
        """内部的なターン進行処理（TurnControllerへの委譲）。"""
        self.turn_controller._process_turn_phases()
