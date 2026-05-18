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

from jpoke.utils.type_defs import Stat
from jpoke.enums import Event, DamageFlag
from jpoke.utils import fast_copy
from jpoke.utils.constants import TYPE_MODIFIER
from jpoke.utils.battle_math import round_half_down

from .context import BattleContext


@dataclass
class DamageContext:
    """ダメージ計算のコンテキスト情報。

    ダメージ計算中の状態や補正、フラグを保持します。

    Attributes:
        critical: 急所に当たるかどうか
        power_multiplier: 技威力の倍率
        damage_flags: ダメージ計算に関するフラグのリスト
    """
    critical: bool = False
    power_multiplier: float = 1
    _damage_flags: list[DamageFlag] = field(default_factory=list)

    def add_flag(self, flag: DamageFlag):
        """ダメージ計算フラグを追加する。

        Args:
            flag: 追加するフラグ
        """
        self._damage_flags.append(flag)


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
        """ダメージ計算機を初期化する。

        Args:
            battle: 現在進行中のバトルインスタンス
        """
        self.battle: Battle = battle

        # ダメージ計算の結果を保存するための属性（デバッグ用）
        self.damages: list[int] = []
        self.final_power: int = 0
        self.final_attack: int = 0
        self.final_defense: int = 0
        self.power_modifier: int = 4096
        self.atk_modifier: int = 4096
        self.def_modifier: int = 4096
        self.atk_type_modifier: int = 4096
        self.def_type_modifier: int = 4096
        self.damage_modifier: int = 4096
        self.burn_modifier: int = 4096
        self.protect_modifier: int = 4096

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
            new_battle: 新しいBattleインスタンス
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
        """1回の攻撃で与えるダメージ乱数列を計算する。

        Args:
            attacker: 攻撃側
            defender: 防御側
            move: 技
            dmg_ctx: ダメージコンテキスト

        Returns:
            tuple[list[int], DamageContext | None]:
                - 16段階乱数に対応するダメージリスト
                - 計算後のダメージコンテキスト
        """
        if not move.power:
            return [0], dmg_ctx

        ctx = BattleContext(attacker=attacker, defender=defender, move=move)
        # ダメージ補正ハンドラ（壁など）で参照できるよう急所情報を共有する。
        ctx.critical = dmg_ctx.critical

        # 最終威力・攻撃・防御
        final_power = self._calc_final_power(ctx, dmg_ctx)
        final_attack = self._calc_final_attack(ctx, dmg_ctx)
        final_defence = self._calc_final_defense(ctx, dmg_ctx)

        # 最大乱数ダメージ
        max_dmg = int(int(int(attacker.level*0.4+2)*final_power*final_attack/final_defence)/50+2)

        # 急所
        if dmg_ctx.critical:
            max_dmg = round_half_down(max_dmg * 1.5)
            dmg_ctx.add_flag(DamageFlag.CRITICAL)

        # -- ここで乱数が適用される(計算はループ内で実行) --

        # タイプ一致補正
        self.atk_type_modifier = self._calc_atk_type_modifier(ctx)
        r_atk_type = self.atk_type_modifier / 4096

        # タイプ相性補正
        self.def_type_modifier = self._calc_def_type_modifier(ctx)
        r_def_type = self.def_type_modifier / 4096

        # やけど補正（タイプ相性の後、ダメージ補正の前）
        self.burn_modifier = self.events.emit(Event.ON_CALC_BURN_MODIFIER, ctx, 4096)
        r_burn = self.burn_modifier / 4096

        # ダメージ補正
        self.damage_modifier = self.events.emit(Event.ON_CALC_DAMAGE_MODIFIER, ctx, 4096)
        r_dmg = self.damage_modifier / 4096

        # まもる貫通系補正（Z技、ダイマックス技等）
        self.protect_modifier = self.events.emit(Event.ON_CALC_PROTECT_MODIFIER, ctx, 4096)
        r_protect = self.protect_modifier / 4096

        self.damages = [0]*16
        for i in range(16):
            # 乱数 85~100%
            self.damages[i] = int(max_dmg * (0.85+0.01*i))

            # タイプ補正
            self.damages[i] = round_half_down(self.damages[i] * r_atk_type)
            self.damages[i] = round_half_down(self.damages[i] * r_def_type)

            # やけど補正
            self.damages[i] = round_half_down(self.damages[i] * r_burn)

            # ダメージ補正
            self.damages[i] = round_half_down(self.damages[i] * r_dmg)

            # まもる貫通系補正
            self.damages[i] = round_half_down(self.damages[i] * r_protect)

            # 最低ダメージ補償
            if self.damages[i] == 0 and r_def_type * r_dmg > 0:
                self.damages[i] = 1

        return self.damages, dmg_ctx

    def _calc_atk_type_modifier(self, ctx: BattleContext) -> int:
        """タイプ一致補正（STAB）を計算する。

        テラスタルの有無を考慮してSTAB補正値を計算し、
        ON_CALC_ATK_TYPE_MODIFIER イベントを発火して返す。

        仕様は docs/spec/damage_calc.md の「タイプ一致補正の詳細」を参照。

        Args:
            ctx: 攻防・技の情報を持つバトルコンテキスト

        Returns:
            int: タイプ一致補正（4096が1.0倍、6144が1.5倍、8192が2.0倍など）
        """
        base = 4096

        attacker = ctx.attacker
        move_type = ctx.move.type
        original_matches = move_type in attacker.data.types

        if not attacker.terastallized:
            if original_matches:
                base = 6144
        else:
            tera_type = attacker.tera_type

            if tera_type == 'ステラ':
                # ステラ補正: タイプ一致補正の代替
                already_boosted = move_type in getattr(attacker, 'stellar_boosted_types', set())

                if original_matches:
                    # 元タイプ一致技: 初回2.0倍、以降1.5倍
                    base = 6144 if already_boosted else 8192
                else:
                    # 不一致技: 初回1.2倍、以降1.0倍
                    base = 4096 if already_boosted else 4915
            else:
                tera_matches = tera_type == move_type
                if tera_matches and original_matches:
                    # テラスタイプ・元タイプ両方が技タイプと一致 → 2.0倍
                    base = 8192
                elif tera_matches or original_matches:
                    # テラスタイプ一致、または元タイプ一致 → 1.5倍
                    base = 6144

        return self.events.emit(Event.ON_CALC_ATK_TYPE_MODIFIER, ctx, base)

    def _calc_def_type_modifier(self, ctx: BattleContext) -> int:
        """タイプ相性補正を計算する。

        攻撃技タイプと防御側タイプの相性を固定小数点で計算し、
        ON_CALC_DEF_TYPE_MODIFIER イベントを発火して倍率（float）で返す。

        Args:
            ctx: 攻防・技の情報を持つバトルコンテキスト

        Returns:
            int: タイプ相性補正（4096が1.0倍、2048が0.5倍、8192が2.0倍など）
        """
        base = 4096

        if (
            ctx.move.type == "ステラ"
            and ctx.defender.terastallized
        ):
            # テラスタル状態の相手にステラ技が効果抜群になる
            base *= 2
        elif (
            ctx.move.type == "じめん"
            and self.battle.query_manager.is_floating(ctx.defender)
        ):
            # 浮いている相手にはじめん技が無効
            base = 0
        else:
            # タイプ相性表に基づいて補正を計算
            for def_type in ctx.defender.types:
                type_chart = TYPE_MODIFIER.get(ctx.move.type, {})
                rate = type_chart.get(def_type, 1.0)
                base = int(base * rate)

        return self.events.emit(Event.ON_CALC_DEF_TYPE_MODIFIER, ctx, base)

    def _calc_final_power(self,
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
        power = ctx.move.power * dmg_ctx.power_multiplier

        # その他の補正
        self.power_modifier = self.events.emit(Event.ON_CALC_POWER_MODIFIER, ctx, 4096)
        power = round_half_down(power*self.power_modifier/4096)

        # テラスタル時の威力60底上げ補正
        # 対象: テラスタイプ一致かつ非連続技かつ優先度+1未満
        if self._can_apply_terastal_power_floor(ctx):
            power = max(power, 60)

        self.final_power = max(1, power)
        return self.final_power

    def _can_apply_terastal_power_floor(self, ctx: BattleContext) -> bool:
        """テラスタル時の威力60底上げ補正が適用可能か判定する。"""
        attacker = ctx.attacker
        move = ctx.move

        if not attacker.terastallized:
            return False
        if not attacker.active_tera_type:
            return False
        if move.type != attacker.active_tera_type:
            return False

        # 連続攻撃技は対象外
        if move.max_hits > 1:
            return False

        # 優先度+1以上の技は対象外
        if move.priority >= 1:
            return False

        return True

    def _calc_final_attack(self,
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

        move_category = self.battle.move_executor.resolve_move_category(attacker, move)

        # ステータス
        if move.name == 'イカサマ':
            final_attack = defender.stats["A"]
            r_rank = defender.rank_modifier("A")
        else:
            if move.name == 'ボディプレス':
                stat = "B"
            elif move_category == "物理":
                stat = "A"
            else:
                stat = "C"
            final_attack = attacker.stats[stat]
            r_rank = attacker.rank_modifier(stat)

        r_rank = self.events.emit(
            Event.ON_CALC_ATK_RANK_MODIFIER,
            ctx,
            r_rank,
        )

        if dmg_ctx.critical and r_rank < 1:
            r_rank = 1
            dmg_ctx.add_flag(DamageFlag.IGNORE_ATK_DOWN_DURING_CRITICAL)

        # ランク補正
        final_attack = int(final_attack * r_rank)

        # その他の補正
        self.atk_modifier = self.events.emit(Event.ON_CALC_ATK_MODIFIER, ctx, 4096)
        final_attack = round_half_down(final_attack * self.atk_modifier/4096)
        final_attack = max(1, final_attack)

        self.final_attack = final_attack  # デバッグ用に保存
        return final_attack

    def _calc_final_defense(self,
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

        # ステータス
        if self.battle.move_executor.deals_physical_damage(attacker, move):
            stat = "B"
        else:
            stat = "D"

        final_defence = defender.stats[stat]
        r_rank = defender.rank_modifier(stat)

        # ランク補正の修正
        r_rank = self.events.emit(Event.ON_CALC_DEF_RANK_MODIFIER, ctx, r_rank)

        if dmg_ctx.critical and r_rank > 1:
            r_rank = 1
            dmg_ctx.add_flag(DamageFlag.IGNORE_DEF_UP_DURING_CRITICAL)

        # ランク補正
        final_defence = int(final_defence * r_rank)

        # その他の補正
        self.def_modifier = self.events.emit(Event.ON_CALC_DEF_MODIFIER, ctx, 4096)
        final_defence = round_half_down(final_defence * self.def_modifier/4096)
        final_defence = max(1, final_defence)

        self.final_defense = final_defence  # デバッグ用に保存
        return final_defence
