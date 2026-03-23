"""ダメージ計算ロジックを提供するモジュール。

ポケモンの技のダメージ計算を行います。
ランク補正、特性、持ち物、天候などの諸要素を考慮した詳細なダメージ計算を実装します。
"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle, EventManager
    from jpoke.model import Pokemon, Ability, Move

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_DOWN

from jpoke.utils.type_defs import Stat
from jpoke.enums import Event, DamageFlag
from jpoke.utils import fast_copy
from jpoke.utils.constants import TYPE_MODIFIER

from .context import BattleContext


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
        power_multiplier: 技威力の倍率
        is_lethal_calc: 致死率計算中かどうか
        _flags: ダメージ計算に関するフラグのリスト
    """
    critical: bool = False
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

    def __init__(self, battle: Battle):
        self.battle: Battle = battle

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

    def update_reference(self, new_battle: Battle):
        """ディープコピー後の参照を更新する。

        Args:
            battle: 新しいBattleインスタンス
        """
        self.battle = new_battle

    @property
    def events(self) -> EventManager:
        """イベント管理システムへのショートカットプロパティ。"""
        return self.battle.events

    def calc_damage_range(self,
                          attacker: Pokemon,
                          defender: Pokemon,
                          move: Move,
                          dmg_ctx: DamageContext) -> tuple[list[int], DamageContext | None]:
        """
        1回の攻撃で与えるダメージを計算する

        Args:
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

        ctx = BattleContext(attacker=attacker, defender=defender, move=move)

        # 最終威力・攻撃・防御
        final_pow = self.calc_final_power(ctx, dmg_ctx)
        final_atk = self.calc_final_attack(ctx, dmg_ctx)
        final_def = self.calc_final_defense(ctx, dmg_ctx)

        # 最大乱数ダメージ
        max_dmg = int(int(int(attacker.level*0.4+2)*final_pow*final_atk/final_def)/50+2)

        # 急所
        if dmg_ctx.critical:
            max_dmg = round_half_down(max_dmg * 1.5)
            dmg_ctx.add_flag(DamageFlag.CRITICAL)

        # -- ここで乱数が適用される(計算はループ内で実行) --

        # タイプ一致補正
        r_atk_type = self.calc_atk_type_modifier(ctx)

        # タイプ相性補正
        r_def_type = self.calc_def_type_modifier(ctx)

        # やけど補正（タイプ相性の後、ダメージ補正の前）
        r_burn = self.events.emit(
            Event.ON_CALC_BURN_MODIFIER,
            ctx,
            4096
        ) / 4096

        # ダメージ補正
        r_dmg = self.events.emit(
            Event.ON_CALC_DAMAGE_MODIFIER,
            ctx,
            4096
        ) / 4096

        # まもる貫通系補正（Z技、ダイマックス技等）
        r_protect = self.events.emit(
            Event.ON_CALC_PROTECT_MODIFIER,
            ctx,
            4096
        ) / 4096

        dmgs = [0]*16
        for i in range(16):
            # 乱数 85~100%
            dmgs[i] = int(max_dmg * (0.85+0.01*i))

            # タイプ補正
            dmgs[i] = round_half_down(dmgs[i] * r_atk_type)
            dmgs[i] = round_half_down(dmgs[i] * r_def_type)

            # やけど補正
            dmgs[i] = round_half_down(dmgs[i] * r_burn)

            # ダメージ補正
            dmgs[i] = round_half_down(dmgs[i] * r_dmg)

            # まもる貫通系補正
            dmgs[i] = round_half_down(dmgs[i] * r_protect)

            # 最低ダメージ補償
            if dmgs[i] == 0 and r_def_type * r_dmg > 0:
                dmgs[i] = 1

        return dmgs, dmg_ctx

    def calc_atk_type_modifier(self, ctx: BattleContext) -> float:
        """タイプ一致補正（STAB）を計算する。

        テラスタルの有無を考慮してSTAB補正値を計算し、
        ON_CALC_ATK_TYPE_MODIFIER イベントを発火して返す。

        仕様は docs/spec/damage_calc.md の「タイプ一致補正の詳細」を参照。

        Args:
            ctx: 攻防・技の情報を持つバトルコンテキスト

        Returns:
            float: タイプ一致補正
        """
        attacker = ctx.attacker
        move_type = ctx.move.type

        base_modifier = 4096

        if attacker.is_terastallized:
            tera_type = attacker._terastal
            original_types = attacker.data.types
            tera_matches = tera_type == move_type
            original_matches = move_type in original_types

            if tera_matches and original_matches:
                # テラスタイプ・元タイプ両方が技タイプと一致 → 2.0倍
                base_modifier = 8192
            elif tera_matches:
                # テラスタイプのみ一致 → 1.5倍
                base_modifier = 6144
            elif original_matches:
                # 元タイプのみ一致（テラスタイプ異なる） → 1.5倍
                base_modifier = 6144
        else:
            if move_type in attacker.data.types:
                base_modifier = 6144

        v = self.events.emit(
            Event.ON_CALC_ATK_TYPE_MODIFIER,
            ctx,
            base_modifier
        )
        return v / 4096

    def calc_def_type_modifier(self,
                               ctx: BattleContext | None = None,
                               attacker=None,
                               defender=None,
                               move=None) -> float:
        """タイプ相性補正を計算する。

        攻撃技タイプと防御側タイプの相性を固定小数点で計算し、
        ON_CALC_DEF_TYPE_MODIFIER イベントを発火して倍率（float）で返す。

        Args:
            ctx: 攻防・技の情報を持つバトルコンテキスト（Noneの場合は以下の個別引数を使用）
            attacker: 攻撃側ポケモン
            defender: 防御側ポケモン
            move: 技オブジェクトまたは技名文字列

        Returns:
            float: タイプ相性倍率（1.0=等倍、2.0=効果ばつぐん等）
        """
        if ctx is None:
            from jpoke.model import Move as MoveModel
            ctx = BattleContext(
                attacker=attacker,
                defender=defender,
                move=MoveModel(move) if isinstance(move, str) else move,
            )

        base_modifier = 4096
        if ctx.move and ctx.defender:
            for defender_type in ctx.defender.types:
                type_chart = TYPE_MODIFIER.get(ctx.move.type, {})
                rate = type_chart.get(defender_type, 1.0)
                base_modifier = int(base_modifier * rate)

        v = self.events.emit(
            Event.ON_CALC_DEF_TYPE_MODIFIER,
            ctx,
            base_modifier
        )
        return v / 4096

    def calc_final_power(self,
                         ctx: BattleContext,
                         dmg_ctx: DamageContext | None = None) -> int:
        """最終威力を計算する。

        Args:
            ctx: 攻防・技の情報を持つバトルコンテキスト
            dmg_ctx: ダメージコンテキスト

        Returns:
            int: 補正後の最終威力
        """
        if not dmg_ctx:
            dmg_ctx = DamageContext()

        # 技威力
        final_pow = ctx.move.data.power * dmg_ctx.power_multiplier

        # その他の補正
        r_pow = self.events.emit(
            Event.ON_CALC_POWER_MODIFIER,
            ctx,
            4096
        )
        final_pow = round_half_down(final_pow * r_pow/4096)
        final_pow = max(1, final_pow)

        return final_pow

    def calc_final_attack(self,
                          ctx: BattleContext,
                          dmg_ctx: DamageContext | None = None) -> int:
        """最終攻撃力を計算する。

        ランク補正、特性、持ち物などの補正を適用します。

        Args:
            ctx: 攻防・技の情報を持つバトルコンテキスト
            dmg_ctx: ダメージコンテキスト

        Returns:
            int: 補正後の最終攻撃力
        """
        if not dmg_ctx:
            dmg_ctx = DamageContext()

        attacker = ctx.attacker
        defender = ctx.defender
        move = ctx.move

        move_category = self.battle.move_executor.get_effective_move_category(attacker, move)

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
        def_ability: Ability = self.events.emit(
            Event.ON_CHECK_DEF_ABILITY,
            ctx,
            defender.ability
        )

        # TODO (特性実装時でよい) 特性てんねんのハンドラとして実装する
        if def_ability == 'てんねん' and r_rank != 1:
            r_rank = 1
            dmg_ctx.add_flag(DamageFlag.IGNORE_ATK_RANK_BY_TENNEN)

        if dmg_ctx.critical and r_rank < 1:
            r_rank = 1
            dmg_ctx.add_flag(DamageFlag.IGNORE_ATK_DOWN_DURING_CRITICAL)

        # ランク補正
        final_atk = int(final_atk * r_rank)

        # その他の補正
        r_atk = self.events.emit(
            Event.ON_CALC_ATK_MODIFIER,
            ctx,
            4096
        )
        final_atk = round_half_down(final_atk * r_atk/4096)
        final_atk = max(1, final_atk)

        return final_atk

    def calc_final_defense(self,
                           ctx: BattleContext,
                           dmg_ctx: DamageContext | None = None) -> int:
        """最終防御力を計算する。

        ランク補正、特性、持ち物などの補正を適用します。

        Args:
            ctx: 攻防・技の情報を持つバトルコンテキスト
            dmg_ctx: ダメージコンテキスト

        Returns:
            int: 補正後の最終防御力
        """
        if not dmg_ctx:
            dmg_ctx = DamageContext()

        attacker = ctx.attacker
        defender = ctx.defender
        move = ctx.move

        move_category = self.battle.move_executor.get_effective_move_category(attacker, move)

        # ステータス
        if move_category == "物理" or move.has_label("physical"):
            stat = "B"
        else:
            stat = "D"

        final_def = defender.stats[stat]
        r_rank = rank_modifier(defender.rank[stat])

        # ランク補正の修正
        if move.has_label("ignore_rank") and r_rank != 1:
            r_rank = 1
            dmg_ctx.add_flag(DamageFlag.IGNORE_DEF_RANK_BY_MOVE)

        # TODO (特性実装時でよい) 特性てんねんのハンドラとして実装する
        if attacker.ability == 'てんねん' and r_rank != 1:
            r_rank = 1
            dmg_ctx.add_flag(DamageFlag.IGNORE_DEF_RANK_BY_TENNEN)

        if dmg_ctx.critical and r_rank > 1:
            r_rank = 1
            dmg_ctx.add_flag(DamageFlag.IGNORE_DEF_UP_DURING_CRITICAL)

        # ランク補正
        final_def = int(final_def * r_rank)

        # その他の補正
        r_def = self.events.emit(
            Event.ON_CALC_DEF_MODIFIER,
            ctx,
            4096
        )
        final_def = round_half_down(final_def * r_def/4096)
        final_def = max(1, final_def)

        return final_def
