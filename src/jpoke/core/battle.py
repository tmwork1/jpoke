from typing import Self
from dataclasses import dataclass

import time
from random import Random
from copy import deepcopy
import json

from jpoke.utils.types import Stat, Weather, Terrain
from jpoke.utils.enums import Command, Interrupt
from jpoke.utils import fast_copy

from jpoke.model import Pokemon, Move, Field

from .event import Event, EventManager, EventContext
from .player import Player
from .logger import Logger
from .damage import DamageCalculator, DamageContext
from .field import WeatherManager, TerrainManager, GlobalFieldManager, SideFieldManager


@dataclass
class TestOption:
    accuracy: int | None = None


class Battle:
    def __init__(self,
                 players: list[Player],
                 seed: int | None = None) -> None:

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

        self.weather_manager: WeatherManager = WeatherManager(self.events, self.players)
        self.terrain_manager: TerrainManager = TerrainManager(self.events, self.players)
        self.field: GlobalFieldManager = GlobalFieldManager(self.events, self.players)
        self.sides: list[SideFieldManager] = [SideFieldManager(self.events, pl) for pl in self.players]

        self.test_option: TestOption = TestOption()

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        fast_copy(self, new, keys_to_deepcopy=[
            "players", "events", "logger", "random", "damage_calculator",
            "states", "field", "sides"
        ])

        # 複製したインスタンスが複製後を参照するように再代入する
        new.events.update_reference(new)
        new.field.update_reference(new.events, new.players)
        for i, side in enumerate(new.sides):
            side.update_reference(new.events, new.players[i])

        # 乱数の隠蔽
        new.random.seed(int(time.time()))

        return new

    @property
    def side(self) -> dict[Player, SideFieldManager]:
        return dict(zip(self.players, self.sides))

    @property
    def actives(self) -> list[Pokemon]:
        return [pl.active for pl in self.players]

    @property
    def weather(self) -> Field:
        return self.weather_manager.current

    @property
    def terrain(self) -> Field:
        return self.terrain_manager.current

    def export_log(self, file):
        data = {
            "seed": self.seed,
            "players": [],
        }

        for player in self.players:
            data["players"].append({
                "name": player.name,
                "selection_indexes": player.selection_idxes,
                "commands": {},
                "team": [mon.dump() for mon in player.team],
            })

        for log in self.logger.command_logs:
            data["players"][log.player_idx]["commands"].setdefault(
                str(log.turn), []).append(log.command.name)

        with open(file, 'w', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=4))

    @classmethod
    def reconstruct_from_log(cls, file) -> Self:
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

    def masked(self, perspective: Player) -> tuple[Self, Player]:
        # TODO mask
        new = deepcopy(self)
        new_player = new.players[self.players.index(perspective)]
        return new, new_player

    def init_turn(self):
        for player in self.players:
            player.reset_turn()
        self.turn += 1

    def find_player(self, mon: Pokemon) -> Player:
        for player in self.players:
            if mon in player.team:
                return player
        raise Exception("Player not found.")

    def find_rival(self, mon: Pokemon) -> Player:
        player = self.find_player(mon)
        idx = self.players.index(player)
        return self.players[not idx]

    def find_player_index(self, mon: Pokemon) -> int:
        for i, player in enumerate(self.players):
            if mon in player.team:
                return i
        raise Exception("Player not found.")

    def team_idx(self, mon: Pokemon) -> int:
        player = self.find_player(mon)
        return player.team.index(mon)

    def foe(self, active: Pokemon) -> Pokemon:
        return self.actives[not self.actives.index(active)]

    def rival(self, player: Player) -> Player:
        return self.players[not self.players.index(player)]

    def get_available_selection_commands(self, player: Player) -> list[Command]:
        return Command.selection_commands()[:len(player.team)]

    def get_available_switch_commands(self, player: Player) -> list[Command]:
        if player.active.trapped(self.events):
            return []
        return [cmd for mon, cmd in zip(player.team, Command.switch_commands())
                if mon in player.selection and mon is not player.active]

    def get_available_action_commands(self, player: Player) -> list[Command]:
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

    def to_player_idxes(self, source: Player | list[Player] | Pokemon | None) -> list[int]:
        if isinstance(source, Player):
            return [self.players.index(source)]
        if isinstance(source, list):
            return [self.players.index(pl) for pl in source]
        if isinstance(source, Pokemon):
            return [self.players.index(self.find_player(source))]
        if source is None:
            return list(range(len(self.players)))
        return []

    def calc_effective_speed(self, mon: Pokemon) -> int:
        return self.events.emit(Event.ON_CALC_SPEED, EventContext(target=mon), mon.stats["S"])

    def calc_speed_order(self) -> list[Pokemon]:
        speeds = [self.calc_effective_speed(p) for p in self.actives]
        if speeds[0] == speeds[1]:
            actives = self.actives.copy()
            self.random.shuffle(actives)
        else:
            paired = sorted(zip(speeds, self.actives),
                            key=lambda pair: pair[0],
                            reverse=True)
            _, actives = zip(*paired)
        return actives

    def calc_action_order(self) -> list[Pokemon]:
        actives, speeds = [], []
        for i, player in enumerate(self.players):
            if player.has_switched:
                continue

            mon = player.active
            speed = self.calc_effective_speed(mon)

            command = player.reserved_commands[-1]
            move = self.command_to_move(self.players[i], command)
            action_speed = self.events.emit(
                Event.ON_CALC_ACTION_SPEED,
                EventContext(target=mon, move=move),
                0
            )
            total_speed = action_speed + speed*1e-5
            speeds.append(total_speed)
            actives.append(mon)

        # Sort by speed
        if len(actives) > 1:
            paired = sorted(zip(speeds, actives),
                            key=lambda pair: pair[0],
                            reverse=True)
            _, actives = zip(*paired)

        return actives

    def TOD_score(self, player: Player, alpha: float = 1):
        n_alive, total_max_hp, total_hp = 0, 0, 0
        for mon in player.selection:
            total_max_hp += mon.max_hp
            total_hp += mon.hp
            if mon.hp:
                n_alive += 1
        return n_alive + alpha * total_hp / total_max_hp

    def winner(self) -> Player | None:
        if self.winner_idx is not None:
            return self.players[self.winner_idx]

        TOD_scores = [self.TOD_score(pl) for pl in self.players]
        if 0 in TOD_scores:
            loser_idx = TOD_scores.index(0)
            self.winner_idx = int(not loser_idx)
            self.add_turn_log(self.players[self.winner_idx], "勝ち")
            self.add_turn_log(self.players[loser_idx], "負け")
            return self.players[self.winner_idx]

        return None

    def run_selection(self):
        for pl in self.players:
            if not pl.selection_idxes:
                commands = pl.choose_selection_commands(self)
                pl.selection_idxes = [c.idx for c in commands]

    def check_hit(self, attacker: Pokemon, move: Move) -> bool:
        if self.test_option.accuracy is not None:
            accuracy = self.test_option.accuracy
        else:
            if not move.data.accuracy:
                return True
            accuracy = self.events.emit(
                Event.ON_CALC_ACCURACY,
                EventContext(attacker=attacker, move=move),
                move.data.accuracy
            )
        return 100*self.random.random() < accuracy

    def run_move(self, attacker: Pokemon, move: Move):
        ctx = EventContext(attacker=attacker, defender=self.foe(attacker), move=move)

        # 技のハンドラを登録
        move.register_handlers(self.events, attacker)

        # 行動成功判定
        self.events.emit(Event.ON_TRY_ACTION, ctx)

        # 技の宣言、PP消費
        self.events.emit(Event.ON_DECLARE_MOVE, ctx)
        self.events.emit(Event.ON_CONSUME_PP, ctx)

        # 発動成功判定
        self.events.emit(Event.ON_TRY_MOVE, ctx)

        # 発動した技の確定
        attacker.executed_move = move
        self.add_turn_log(attacker, move.name)

        # TODO 命中判定
        if not self.check_hit(attacker, move):
            return

        # 無効判定
        self.events.emit(Event.ON_TRY_IMMUNE, ctx)

        # ダメージ計算
        damage = self.calc_damage(attacker, move)

        # HPコストの支払い
        self.events.emit(Event.ON_PAY_HP, ctx)

        # ダメージ修正
        damage = self.events.emit(Event.ON_MODIFY_DAMAGE, ctx, damage)

        # ダメージの適用
        if damage:
            self.modify_hp(ctx.defender, -damage)

        # 技を当てたときの処理
        self.events.emit(Event.ON_HIT, ctx)

        # ダメージを与えたときの処理
        if damage:
            self.events.emit(Event.ON_DAMAGE, ctx)

        # 技のハンドラを解除
        move.unregister_handlers(self.events, attacker)

    def command_to_move(self, player: Player, command: Command) -> Move:
        if command == Command.STRUGGLE:
            return Move("わるあがき")
        elif command.is_zmove():
            return Move("わるあがき")
        else:
            return player.active.moves[command.idx]

    def modify_hp(self, target: Pokemon, v: int = 0, r: float = 0) -> bool:
        if r:
            v = int(target.max_hp * r)
        if v and (v := target.modify_hp(v)):
            self.add_turn_log(self.find_player(target),
                              f"HP {'+' if v >= 0 else ''}{v} >> {target.hp}")
        return bool(v)

    def modify_stat(self,
                    target: Pokemon,
                    stat: Stat,
                    v: int,
                    source: Pokemon = None) -> bool:
        if v and (v := target.modify_stat(stat, v)):
            self.add_turn_log(self.find_player(target),
                              f"{stat}{'+' if v >= 0 else ''}{v}")
            print(f"{target.name} {stat} {v} {source.name if source else ''}")
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
        damages = self.calc_damages(attacker, move, critical, self_harm)
        return self.random.choice(damages)

    def calc_damages(self,
                     attacker: Pokemon,
                     move: Move | str,
                     critical: bool = False,
                     self_harm: bool = False) -> list[int]:
        if isinstance(move, str):
            move = Move(move)
        defender = attacker if self_harm else self.foe(attacker)
        ctx = DamageContext(critical, self_harm)
        damages, ctx = self.damage_calculator.single_hit_damages(self.events, attacker, defender, move, ctx)
        return damages

    def has_interrupt(self) -> bool:
        return any(pl.interrupt != Interrupt.NONE for pl in self.players)

    def override_interrupt(self, flag: Interrupt, only_first: bool = True):
        for mon in self.calc_speed_order():
            player = self.find_player(mon)
            if player.interrupt == Interrupt.REQUESTED:
                player.interrupt = flag
                if only_first:
                    return

    def run_switch(self, player: Player, new: Pokemon, emit: bool = True):
        # 割り込みフラグを破棄
        player.interrupt = Interrupt.NONE

        # 退場
        old = player.active
        if old is not None:
            self.events.emit(Event.ON_SWITCH_OUT, EventContext(source=old))
            old.switch_out(self.events)
            self.add_turn_log(player, f"{old.name} {'交代' if old.hp else '瀕死'}")

        # 入場
        player.active_idx = player.team.index(new)
        new.switch_in(self.events)
        self.add_turn_log(player, f"{new.name} 着地")

        # ポケモンが場に出た時の処理
        if emit:
            self.events.emit(Event.ON_SWITCH_IN, EventContext(source=new))

            # リクエストがなくなるまで再帰的に交代する
            while self.has_interrupt():
                flag = Interrupt.EJECTPACK_ON_AFTER_SWITCH
                self.override_interrupt(flag)
                self.run_interrupt_switch(flag)

        # その他の処理
        player.has_switched = True

    def run_initial_switch(self):
        # ポケモンを場に出す
        for pl in self.players:
            new = pl.selection[0]
            self.run_switch(pl, new, emit=False)

        # ポケモンが場に出たときの処理は、両者の交代が完了した後に行う
        self.events.emit(Event.ON_SWITCH_IN)

        # だっしゅつパックによる割り込みフラグを更新
        self.override_interrupt(Interrupt.EJECTPACK_ON_START)

    def run_interrupt_switch(self, flag: Interrupt, emit_on_each_switch=True):
        switched_players = []

        for player in self.players:
            if player.interrupt != flag:
                continue

            # 交代を引き起こしたアイテムを消費させる
            if flag.consume_item():
                self.add_turn_log(player, f"{player.active.item.name}消費")
                player.active.item.consume()

            # コマンドが予約されていなければ、プレイヤーの方策関数に従う
            if not player.reserved_commands:
                command = player.reserve_command(player.choose_switch_command(self))
                self.add_command_log(player, command)

            # 交代コマンドを取得
            command = player.reserved_commands.pop(0)

            self.run_switch(player, player.team[command.idx], emit=emit_on_each_switch)
            switched_players.append(player)

        # 全員の着地処理を同時に実行
        if not emit_on_each_switch:
            for mon in self.calc_speed_order():
                player = self.find_player(mon)
                if player in switched_players:
                    self.events.emit(Event.ON_SWITCH_IN, EventContext(source=mon))

    def run_faint_switch(self):
        '''
        while self.winner() is None:
            target_players = []
            if not self.has_interrupt():
                for player in self.players:
                    if player.active.hp == 0:
                        player.interrupt = Interrupt.FAINTED
                        target_players.append(player)

            # 交代を行うプレイヤーがいなければ終了
            if not target_players:
                return

            self.run_interrupt_switch(Interrupt.FAINTED, False)
        '''
        if self.winner():
            return

        # 交代フラグを設定
        if not self.has_interrupt():
            for player in self.players:
                if player.active.hp == 0:
                    player.interrupt = Interrupt.FAINTED

        # 交代を行うプレイヤー
        switch_players = [pl for pl in self.players if pl.interrupt == Interrupt.FAINTED]

        # 対象プレイヤーがいなければ終了
        if not switch_players:
            return

        # 交代
        self.run_interrupt_switch(Interrupt.FAINTED, False)

        # すべての死に出しが完了するまで再帰的に実行
        self.run_faint_switch()

    def add_command_log(self, source: Player | Pokemon | None, command: Command):
        idx = self.to_player_idxes(source)[0]
        self.logger.add_command_log(self.turn, idx, command)

    def add_turn_log(self, source: Player | list[Player] | Pokemon | None, text: str):
        for idx in self.to_player_idxes(source):
            self.logger.add_turn_log(self.turn, idx, text)

    def add_damage_log(self, source: Player | Pokemon | None, text: str):
        idx = self.to_player_idxes(source)[0]
        self.logger.add_damage_log(self.turn, idx, text)

    def get_turn_logs(self, turn: int | None = None) -> dict[Player, list[str]]:
        if turn is None:
            turn = self.turn
        return {pl: self.logger.get_turn_logs(turn, i) for i, pl in enumerate(self.players)}

    def get_damage_logs(self, turn: int | None = None) -> dict[Player, list[str]]:
        if turn is None:
            turn = self.turn
        return {pl: self.logger.get_damage_logs(turn, i) for i, pl in enumerate(self.players)}

    def print_turn_log(self, turn: int | None = None):
        if turn is None:
            turn = self.turn
        turn_logs = self.get_turn_logs(turn)
        damage_logs = self.get_damage_logs(turn)
        print(f"Turn {turn}")
        for player in self.players:
            print(f"\t{player.name}\t{turn_logs[player]} {damage_logs[player]}")

    def advance_turn(self,
                     commands: dict[Player, Command] | None = None,
                     print_log: bool = False):
        # 引数のコマンドをスケジュールに追加する
        if commands:
            for player, command in commands.items():
                player.reserve_command(command)
                self.add_command_log(player, command)

        self._advance_turn()

        if print_log:
            self.print_turn_log()

    def _advance_turn(self):
        if not self.has_interrupt():
            self.init_turn()

        if self.turn == 0:
            if not self.has_interrupt():
                # ポケモンを選出
                self.run_selection()
                # ポケモンを場に出す
                self.run_initial_switch()

            # だっしゅつパックによる交代
            self.run_interrupt_switch(Interrupt.EJECTPACK_ON_START)

            return

        if not self.has_interrupt():
            # 予約されているコマンドがなければ、方策関数に従ってコマンドを予約する
            for player in self.players:
                if not player.reserved_commands:
                    command = player.reserve_command(player.choose_action_command(self))
                    self.add_command_log(player, command)

            # 行動前の処理
            self.events.emit(Event.ON_BEFORE_ACTION)

        # ターン開始時の交代処理
        for mon in self.calc_speed_order():
            # 交代フラグ
            idx = self.actives.index(mon)
            interrupt = Interrupt.ejectpack_on_switch(idx)
            # 交代
            if not self.has_interrupt():
                player = self.players[idx]
                if player.reserved_commands[0].is_switch():
                    command = player.reserved_commands.pop(0)
                    player = self.find_player(mon)
                    new = player.team[command.idx]
                    self.run_switch(player, new)

                # だっしゅつパックによる割り込みフラグを更新
                self.override_interrupt(interrupt)

            # だっしゅつパックによる交代
            self.run_interrupt_switch(interrupt)

        # 行動前の処理
        self.events.emit(Event.ON_BEFORE_MOVE)

        # 技の処理
        for mon in self.calc_action_order():
            player = self.find_player(mon)
            self.add_turn_log(player, player.active.name)

            if not self.has_interrupt():
                # 技の発動
                command = player.reserved_commands.pop(0)
                move = self.command_to_move(player, command)
                self.run_move(mon, move)

            # だっしゅつボタンによる交代
            self.run_interrupt_switch(Interrupt.EJECTBUTTON)

            # ききかいひによる交代
            self.run_interrupt_switch(Interrupt.EMERGENCY)

            # 交代技による交代
            self.run_interrupt_switch(Interrupt.PIVOT)

            interrupt = Interrupt.ejectpack_on_after_move(
                self.players.index(player))

            if not self.has_interrupt():
                # 交代技の後の処理
                self.events.emit(
                    Event.ON_AFTER_PIVOT,
                    EventContext(target=player.active)
                )

                # だっしゅつパックによる割り込みフラグを更新
                self.override_interrupt(interrupt)

            # だっしゅつパックによる交代
            self.run_interrupt_switch(interrupt)

        # ターン終了時の処理 (1)
        if not self.has_interrupt():
            self.events.emit(Event.ON_TURN_END_1)

        # ターン終了時の処理 (2)
        if not self.has_interrupt():
            self.events.emit(Event.ON_TURN_END_2)

        # ききかいひによる交代
        self.run_interrupt_switch(Interrupt.EMERGENCY)

        # ターン終了時の処理 (3)
        if not self.has_interrupt():
            self.events.emit(Event.ON_TURN_END_3)

        # ききかいひによる交代
        self.run_interrupt_switch(Interrupt.EMERGENCY)

        # ターン終了時の処理 (4)
        if not self.has_interrupt():
            self.events.emit(Event.ON_TURN_END_4)

        # ききかいひによる交代
        self.run_interrupt_switch(Interrupt.EMERGENCY)

        # ターン終了時の処理 (5)
        if not self.has_interrupt():
            self.events.emit(Event.ON_TURN_END_5)

            # だっしゅつパックによる割り込みフラグを更新
            self.override_interrupt(Interrupt.EJECTPACK_ON_TURN_END)

        # だっしゅつパックによる交代
        self.run_interrupt_switch(Interrupt.EJECTPACK_ON_TURN_END)

        # ターン終了時の処理 (5)
        if not self.has_interrupt():
            self.events.emit(Event.ON_TURN_END_6)

        self.run_interrupt_switch(Interrupt.EJECTPACK_ON_TURN_END)

        # 瀕死による交代
        self.run_faint_switch()
