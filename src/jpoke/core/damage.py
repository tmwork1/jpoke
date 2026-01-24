from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.model import Pokemon, Ability, Move

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_DOWN

from jpoke.utils.types import Stat
from jpoke.utils.enums import DamageFlag
from jpoke.utils import fast_copy

from .event import EventManager, Event, EventContext


def rank_modifier(v: float) -> float:
    return (2+v)/2 if v >= 0 else 2/(2-v)


def round_half_down(v: float) -> int:
    """五捨五超入"""
    return int(Decimal(str(v)).quantize(Decimal('0'), rounding=ROUND_HALF_DOWN))


@dataclass
class DamageContext:
    critical: bool = False
    self_harm: bool = False
    power_multiplier: float = 1
    is_lethal_calc: bool = False
    _flags: list[DamageFlag] = field(default_factory=list)

    def add_flag(self, flag: DamageFlag):
        self._flags.append(flag)


class DamageCalculator:
    def __init__(self):
        self.lethal_num: int = 0
        self.lethal_prob: float = 0.
        self.hp_dstr: dict = {}
        self.damage_dstr: dict = {}
        self.damage_ratio_dstr: dict = {}

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        fast_copy(self, new)
        return new

    def single_hit_damages(self,
                           events: EventManager,
                           attacker: Pokemon,
                           defender: Pokemon,
                           move: Move,
                           dmg_ctx: DamageContext | None = None) -> tuple[list[int], DamageContext]:
        """
        1回の攻撃で与えるダメージを計算する

        Args:
            events: イベントマネージャー
            attacker: 攻撃側
            defender: 防御側
            move: 技
            dmg_ctx: ダメージコンテキスト

        Returns:
            ダメージのリスト
            ダメージコンテキスト
        """
        if not move.data.power:
            return [0], dmg_ctx

        if not dmg_ctx:
            dmg_ctx = DamageContext()

        move_category = attacker.effective_move_category(move, events)

        # 最終威力・攻撃・防御
        final_pow = self.calc_final_power(events, attacker, defender, move, dmg_ctx)
        final_atk = self.calc_final_attack(events, attacker, defender, move, dmg_ctx)
        final_def = self.calc_final_defense(events, attacker, defender, move, dmg_ctx)

        # 最大乱数ダメージ
        max_dmg = int(int(int(attacker.level*0.4+2)*final_pow*final_atk/final_def)/50+2)

        # 急所
        if dmg_ctx.critical:
            max_dmg = round_half_down(max_dmg * 1.5)
            dmg_ctx.add_flag(DamageFlag.CRITICAL)

        # その他の補正
        r_atk_type = events.emit(Event.ON_CALC_ATK_TYPE_MODIFIER, EventContext(attacker=attacker, defender=defender, move=move), 4096)
        r_def_type = events.emit(Event.ON_CALC_DEF_TYPE_MODIFIER, EventContext(attacker=attacker, defender=defender, move=move), 1)
        r_dmg = events.emit(Event.ON_CALC_DAMAGE_MODIFIER, EventContext(attacker=attacker, defender=defender, move=move), 1)

        dmgs = [0]*16
        for i in range(16):
            # 乱数 85~100%
            dmgs[i] = int(max_dmg * (0.85+0.01*i))

            # 補正
            dmgs[i] = round_half_down(dmgs[i] * r_atk_type)
            dmgs[i] = int(dmgs[i] * r_def_type)
            dmgs[i] = round_half_down(dmgs[i] * r_dmg/4096)

            # 最低ダメージ補償
            if dmgs[i] == 0 and r_def_type * r_dmg > 0:
                dmgs[i] = 1

        return dmgs, dmg_ctx

    def calc_final_power(self,
                         events: EventManager,
                         attacker: Pokemon,
                         defender: Pokemon,
                         move: Move,
                         dmg_ctx: DamageContext | None = None) -> int:
        if not dmg_ctx:
            dmg_ctx = DamageContext()

        move_category = attacker.effective_move_category(move, events)

        # 技威力
        final_pow = move.data.power * dmg_ctx.power_multiplier

        # その他の補正
        r_pow = events.emit(
            Event.ON_CALC_POWER_MODIFIER,
            EventContext(attacker=attacker, defender=defender, move=move),
            4096
        )
        final_pow = round_half_down(final_pow * r_pow/4096)
        final_pow = max(1, final_pow)

        return final_pow

    def calc_final_attack(self,
                          events: EventManager,
                          attacker: Pokemon,
                          defender: Pokemon,
                          move: Move,
                          dmg_ctx: DamageContext | None = None) -> int:
        if not dmg_ctx:
            dmg_ctx = DamageContext()

        move_category = attacker.effective_move_category(move, events)

        # ステータス
        if move == 'イカサマ':
            final_atk = defender.stats["A"]
            r_rank = rank_modifier(defender.rank["A"])
        else:
            if move == 'ボディプレス':
                stat = "B"
            elif move_category == "物理":
                stat = "A"
            else:
                stat = "C"
            final_atk = attacker.stats[stat]
            r_rank = rank_modifier(attacker.rank[stat])

        # ランク補正の修正
        def_ability: Ability = events.emit(
            Event.ON_CHECK_DEF_ABILITY,
            EventContext(attacker=attacker, defender=defender, move=move),
            defender.ability
        )

        if def_ability == 'てんねん' and r_rank != 1:
            r_rank = 1
            dmg_ctx.add_flag(DamageFlag.IGNORE_ATK_RANK_BY_TENNEN)

        if dmg_ctx.critical and r_rank < 1:
            r_rank = 1
            dmg_ctx.add_flag(DamageFlag.IGNORE_ATK_DOWN_DURING_CRITICAL)

        # ランク補正
        final_atk = int(final_atk * r_rank)

        # その他の補正
        r_atk = events.emit(
            Event.ON_CALC_ATK_MODIFIER,
            EventContext(attacker=attacker, defender=defender, move=move),
            4096
        )
        final_atk = round_half_down(final_atk * r_atk/4096)
        final_atk = max(1, final_atk)

        return final_atk

    def calc_final_defense(self,
                           events: EventManager,
                           attacker: Pokemon,
                           defender: Pokemon,
                           move: Move,
                           dmg_ctx: DamageContext | None = None) -> int:
        if not dmg_ctx:
            dmg_ctx = DamageContext()

        move_category = attacker.effective_move_category(move, events)

        # ステータス
        if move_category == "物理" or "physical" in move.data.flags:
            stat = "B"
        else:
            stat = "D"

        final_def = defender.stats[stat]
        r_rank = rank_modifier(defender.rank[stat])

        # ランク補正の修正
        if "ignore_rank" in move.data.flags and r_rank != 1:
            r_rank = 1
            dmg_ctx.add_flag(DamageFlag.IGNORE_DEF_RANK_BY_MOVE)

        if attacker.ability == 'てんねん' and r_rank != 1:
            r_rank = 1
            dmg_ctx.add_flag(DamageFlag.IGNORE_DEF_RANK_BY_TENNEN)

        if dmg_ctx.critical and r_rank > 1:
            r_rank = 1
            dmg_ctx.add_flag(DamageFlag.IGNORE_DEF_UP_DURING_CRITICAL)

        # ランク補正
        final_def = int(final_def * r_rank)

        # その他の補正
        r_def = events.emit(
            Event.ON_CALC_DEF_MODIFIER,
            EventContext(attacker=attacker, defender=defender, move=move),
            4096
        )
        final_def = round_half_down(final_def * r_def/4096)
        final_def = max(1, final_def)

        return final_def
