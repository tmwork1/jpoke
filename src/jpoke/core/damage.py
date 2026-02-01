"""ダメージ計算ロジックを提供するモジュール。

ポケモンの技のダメージ計算を行います。
ランク補正、特性、持ち物、天候などの諸要素を考慮した詳細なダメージ計算を実装します。
"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.model import Pokemon, Ability, Move

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_DOWN

from jpoke.utils.type_defs import Stat
from jpoke.utils.enums import DamageFlag
from jpoke.utils import fast_copy

from .event import EventManager, Event, EventContext


def rank_modifier(v: float) -> float:
    """ランク補正値を計算する。

    Args:
        v: ランク値（-6～+6）

    Returns:
        float: 補正倍率
    """
    return (2+v)/2 if v >= 0 else 2/(2-v)


def round_half_down(v: float) -> int:
    """五捨五超入で丸める。

    0.5は切り捨て、0.5より大きい値は切り上げます。

    Args:
        v: 対象の値

    Returns:
        int: 丸められた整数値
    """
    return int(Decimal(str(v)).quantize(Decimal('0'), rounding=ROUND_HALF_DOWN))


@dataclass
class DamageContext:
    """ダメージ計算のコンテキスト情報。

    ダメージ計算中の状態や補正、フラグを保持します。

    Attributes:
        critical: 急所に当たるかどうか
        self_harm: 自分自身へのダメージかどうか
        power_multiplier: 技威力の倍率
        is_lethal_calc: 致死率計算中かどうか
        _flags: ダメージ計算に関するフラグのリスト
    """
    critical: bool = False
    self_harm: bool = False
    power_multiplier: float = 1
    is_lethal_calc: bool = False
    _flags: list[DamageFlag] = field(default_factory=list)

    def add_flag(self, flag: DamageFlag):
        """ダメージ計算フラグを追加する。

        Args:
            flag: 追加するフラグ
        """
        self._flags.append(flag)


class DamageCalculator:
    """ダメージ計算を行うクラス。

    技のダメージ計算、威力・攻撃・防御の最終値計算を提供します。

    Attributes:
        lethal_num: 致死回数
        lethal_prob: 致死確率
        hp_dstr: HP分布
        damage_dstr: ダメージ分布
        damage_ratio_dstr: ダメージ割合分布
    """

    def __init__(self):
        """DamageCalculatorを初期化する。"""
        self.lethal_num: int = 0
        self.lethal_prob: float = 0.
        self.hp_dstr: dict = {}
        self.damage_dstr: dict = {}
        self.damage_ratio_dstr: dict = {}

    def __deepcopy__(self, memo):
        """ディープコピーを作成する。

        Args:
            memo: コピー済みオブジェクトのメモ辞書

        Returns:
            DamageCalculator: コピーされたインスタンス
        """
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
                           dmg_ctx: DamageContext | None = None) -> tuple[list[int], DamageContext | None]:
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

        # -- ここで乱数が適用される(計算はループ内で実行) --

        # 攻撃タイプ補正
        r_atk_type = events.emit(
            Event.ON_CALC_ATK_TYPE_MODIFIER,
            EventContext(attacker=attacker, defender=defender, move=move),
            4096
        )

        # 防御タイプ補正
        r_def_type = events.emit(
            Event.ON_CALC_DEF_TYPE_MODIFIER,
            EventContext(attacker=attacker, defender=defender, move=move),
            4096
        )

        # やけど補正（タイプ相性の後、ダメージ補正の前）
        r_burn = events.emit(
            Event.ON_CALC_BURN_MODIFIER,
            EventContext(attacker=attacker, defender=defender, move=move),
            4096
        )

        # ダメージ補正
        r_dmg = events.emit(
            Event.ON_CALC_DAMAGE_MODIFIER,
            EventContext(attacker=attacker, defender=defender, move=move),
            4096
        )

        # まもる貫通系補正（Z技、ダイマックス技等）
        r_protect = events.emit(
            Event.ON_CALC_PROTECT_MODIFIER,
            EventContext(attacker=attacker, defender=defender, move=move),
            4096
        )

        dmgs = [0]*16
        for i in range(16):
            # 乱数 85~100%
            dmgs[i] = int(max_dmg * (0.85+0.01*i))

            # タイプ補正
            dmgs[i] = round_half_down(dmgs[i] * r_atk_type / 4096)
            dmgs[i] = round_half_down(dmgs[i] * r_def_type / 4096)

            # やけど補正
            dmgs[i] = round_half_down(dmgs[i] * r_burn / 4096)

            # ダメージ補正
            dmgs[i] = round_half_down(dmgs[i] * r_dmg / 4096)

            # まもる貫通系補正
            dmgs[i] = round_half_down(dmgs[i] * r_protect / 4096)

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
        """最終威力を計算する。

        Args:
            events: イベントマネージャー
            attacker: 攻撃側のポケモン
            defender: 防御側のポケモン
            move: 技
            dmg_ctx: ダメージコンテキスト

        Returns:
            int: 補正後の最終威力
        """
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
        """最終攻撃力を計算する。

        ランク補正、特性、持ち物などの補正を適用します。

        Args:
            events: イベントマネージャー
            attacker: 攻撃側のポケモン
            defender: 防御側のポケモン
            move: 技
            dmg_ctx: ダメージコンテキスト

        Returns:
            int: 補正後の最終攻撃力
        """
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
        """最終防御力を計算する。

        ランク補正、特性、持ち物などの補正を適用します。

        Args:
            events: イベントマネージャー
            attacker: 攻撃側のポケモン
            defender: 防御側のポケモン
            move: 技
            dmg_ctx: ダメージコンテキスト

        Returns:
            int: 補正後の最終防御力
        """
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
