"""ダメージ計算ロジックを提供するモジュール。

ポケモンの技のダメージ計算を行います。
ランク補正、特性、アイテム、天候などの諸要素を考慮した詳細なダメージ計算を実装します。
"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle, EventManager
    from jpoke.model import Pokemon, Move

from jpoke.enums import Event
from jpoke.types import Stat
from jpoke.utils import fast_copy
from jpoke.data.type_chart import TYPE_MODIFIER
from jpoke.utils.math import round_half_down

from .context import AttackContext


class DamageCalculator:
    """ダメージ計算を行うクラス。"""

    def __init__(self, battle: Battle):
        self.battle: Battle = battle

        # ダメージ計算の結果を保存するための属性（テスト・デバッグ用）
        self.final_power: int | None = None
        self.final_attack: int | None = None
        self.final_defense: int | None = None
        self.power_modifier: int | None = None
        self.atk_modifier: int | None = None
        self.def_modifier: int | None = None
        self.atk_type_modifier: int | None = None
        self.def_type_modifier: int | None = None
        self.damage_modifier: int | None = None
        self.burn_modifier: int | None = None
        self.protect_modifier: int | None = None

    def reset_monitor_attributes(self):
        """ダメージ計算のモニタリング用属性をリセットする。"""
        self.final_power = None
        self.final_attack = None
        self.final_defense = None
        self.power_modifier = None
        self.atk_modifier = None
        self.def_modifier = None
        self.atk_type_modifier = None
        self.def_type_modifier = None
        self.damage_modifier = None
        self.burn_modifier = None
        self.protect_modifier = None

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        fast_copy(self, new, keys_to_deepcopy=[])
        return new

    def update_reference(self, new_battle: Battle):
        """ディープコピー後の参照を更新する。

        Args:
            new_battle: 新しいBattleインスタンス
        """
        self.battle = new_battle

    @property
    def _events(self) -> EventManager:
        return self.battle.events

    def calc_damages(self,
                     attacker: Pokemon,
                     defender: Pokemon,
                     move: Move,
                     critical: bool = False) -> list[int]:
        """1回の攻撃で与えるダメージ乱数列を計算する。

        Args:
            attacker: 攻撃側
            defender: 防御側
            move: 技
            critical: 急所に当たるかどうか

        Returns:
            list[int]: 16段階乱数に対応するダメージリスト
        """
        self.reset_monitor_attributes()

        if not move.base_power:
            return [0]

        ctx = AttackContext(
            attacker=attacker,
            defender=defender,
            move=move,
            critical=critical,
        )

        # 最終威力・攻撃・防御
        final_power = self._calc_final_power(ctx)
        final_attack = self._calc_final_attack(ctx)
        final_defense = self._calc_final_defense(ctx)

        # 最大乱数ダメージ
        level_factor = int(attacker.level * 0.4 + 2)
        base_damage = int(
            level_factor
            * final_power
            * final_attack
            / final_defense
        )
        max_damage = int(base_damage / 50 + 2)

        # 急所
        if ctx.critical:
            max_damage = round_half_down(max_damage * 1.5)

        # -- ここで乱数が適用される(計算はループ内で実行) --

        # タイプ一致補正
        self.atk_type_modifier = self._calc_atk_type_modifier(ctx)
        r_atk_type = self.atk_type_modifier / 4096

        # タイプ相性補正
        self.def_type_modifier = self.calc_def_type_modifier(ctx)
        r_def_type = self.def_type_modifier / 4096

        # やけど補正（タイプ相性の後、ダメージ補正の前）
        self.burn_modifier = self._events.emit(Event.ON_CALC_BURN_MODIFIER, ctx, 4096)
        r_burn = self.burn_modifier / 4096

        # ダメージ補正
        self.damage_modifier = self._events.emit(Event.ON_CALC_DAMAGE_MODIFIER, ctx, 4096)
        r_damage = self.damage_modifier / 4096

        # まもる貫通系補正（Z技、ダイマックス技等）
        self.protect_modifier = self._events.emit(Event.ON_CALC_PROTECT_MODIFIER, ctx, 4096)
        r_protect = self.protect_modifier / 4096

        damages = [0]*16
        for i in range(16):
            # 乱数 85~100%
            damages[i] = int(max_damage * (0.85+0.01*i))

            # タイプ補正
            damages[i] = round_half_down(damages[i] * r_atk_type)
            damages[i] = round_half_down(damages[i] * r_def_type)

            # やけど補正
            damages[i] = round_half_down(damages[i] * r_burn)

            # ダメージ補正
            damages[i] = round_half_down(damages[i] * r_damage)

            # まもる貫通系補正
            damages[i] = round_half_down(damages[i] * r_protect)

            # 最低ダメージ補償
            if r_def_type * r_damage > 0:
                damages[i] = max(1, damages[i])

        return damages

    def _calc_atk_type_modifier(self, ctx: AttackContext) -> int:
        """タイプ一致補正（STAB）を計算する。

        テラスタルの有無を考慮してSTAB補正値を計算し、
        ON_CALC_ATK_TYPE_MODIFIER イベントを発火して返す。

        仕様は .internal/spec/damage_calc.md の「タイプ一致補正の詳細」を参照。

        Args:
            ctx: 攻防・技の情報を持つバトルコンテキスト

        Returns:
            int: タイプ一致補正（4096が1.0倍、6144が1.5倍、8192が2.0倍など）
        """
        attacker = ctx.attacker
        move_type = ctx.move.type
        original_matches = move_type in attacker.data.types
        tera_type = attacker.active_tera_type

        base = 4096

        if not tera_type:
            if original_matches:
                base = 6144
        else:
            if tera_type == 'ステラ':
                # ステラ補正: タイプ一致補正の代替
                already_boosted = move_type in attacker.stellar_boosted_types

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

        return self._events.emit(Event.ON_CALC_ATK_TYPE_MODIFIER, ctx, base)

    def calc_def_type_modifier(self, ctx: AttackContext) -> int:
        """タイプ相性補正を計算する。

        攻撃技タイプと防御側タイプの相性を固定小数点で計算し、
        ON_CALC_DEF_TYPE_MODIFIER イベントを発火して倍率（float）で返す。

        Args:
            ctx: 攻防・技の情報を持つバトルコンテキスト

        Returns:
            int: タイプ相性補正（4096が1.0倍、2048が0.5倍、8192が2.0倍など）
        """
        assert ctx.defender is not None
        move_type = ctx.move.type

        # テラスタル状態の相手にステラ技が効果抜群になる
        if (
            move_type == "ステラ"
            and ctx.defender.is_terastallized
        ):
            return self._events.emit(Event.ON_CALC_DEF_TYPE_MODIFIER, ctx, 8192)

        base = 4096
        type_chart = TYPE_MODIFIER.get(move_type, {})

        if move_type == "じめん":
            foe_is_floating = self.battle.query.is_floating(ctx.defender)

            if foe_is_floating:
                # 浮いている相手にはじめん技が無効
                base = 0
            else:
                # 浮いていないひこうタイプにじめん技は等倍
                type_chart = type_chart.copy()
                type_chart["ひこう"] = 1.0

        # タイプ相性表に基づいて補正を計算
        for def_type in ctx.defender.types:
            rate = type_chart.get(def_type, 1.0)
            base = int(base * rate)

        return self._events.emit(Event.ON_CALC_DEF_TYPE_MODIFIER, ctx, base)

    def _calc_final_power(self, ctx: AttackContext) -> int:
        """最終威力を計算する。

        Args:
            ctx: 攻防・技の情報を持つバトルコンテキスト

        Returns:
            int: 補正後の最終威力
        """
        # 技威力
        power = ctx.move.base_power

        # その他の補正
        power_modifier = self._events.emit(Event.ON_CALC_POWER_MODIFIER, ctx, 4096)
        power = round_half_down(power*power_modifier/4096)

        # テラスタル時の威力60底上げ補正
        # 対象: テラスタイプ一致かつ非連続技かつ優先度+1未満
        if self._can_apply_terastal_power_floor(ctx):
            power = max(power, 60)

        self.final_power = max(1, power)

        self.power_modifier = power_modifier  # デバッグ用に保存

        return self.final_power

    def _can_apply_terastal_power_floor(self, ctx: AttackContext) -> bool:
        """テラスタル時の威力60底上げ補正が適用可能か判定する。"""
        attacker = ctx.attacker
        move = ctx.move

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

    def _calc_final_attack(self, ctx: AttackContext) -> int:
        """最終攻撃力を計算する。

        ランク補正、特性、アイテムなどの補正を適用します。

        Args:
            ctx: 攻防・技の情報を持つバトルコンテキスト

        Returns:
            int: 補正後の最終攻撃力
        """
        assert ctx.defender is not None
        attacker = ctx.attacker
        defender = ctx.defender
        move = ctx.move

        # ステータス
        if move.name == 'イカサマ':
            final_attack = defender.stats["atk"]
            r_rank = defender.rank_modifier("atk")
        else:
            stat: Stat
            if move.name == 'ボディプレス':
                stat = "def"
            elif move.category == "physical":
                stat = "atk"
            else:
                stat = "spa"
            final_attack = attacker.stats[stat]
            r_rank = attacker.rank_modifier(stat)

        r_rank = self._events.emit(Event.ON_CALC_ATK_RANK_MODIFIER, ctx, r_rank)

        if ctx.critical:
            r_rank = max(r_rank, 1)

        # ランク補正
        final_attack = int(final_attack * r_rank)

        # その他の補正
        atk_modifier = self._events.emit(Event.ON_CALC_ATK_MODIFIER, ctx, 4096)

        final_attack = round_half_down(final_attack * atk_modifier/4096)
        final_attack = max(1, final_attack)

        self.atk_modifier = atk_modifier  # デバッグ用に保存
        self.final_attack = final_attack  # デバッグ用に保存

        return final_attack

    def _calc_final_defense(self, ctx: AttackContext) -> int:
        """最終防御力を計算する。

        ランク補正、特性、アイテムなどの補正を適用します。

        Args:
            ctx: 攻防・技の情報を持つバトルコンテキスト

        Returns:
            int: 補正後の最終防御力
        """
        assert ctx.defender is not None
        attacker = ctx.attacker
        defender = ctx.defender
        move = ctx.move

        # ステータス
        stat: Stat
        if self.battle.query.deals_physical_damage(attacker, move):
            stat = "def"
        else:
            stat = "spd"

        final_defense = defender.stats[stat]
        r_rank = defender.rank_modifier(stat)

        # ランク補正の修正
        r_rank = self._events.emit(Event.ON_CALC_DEF_RANK_MODIFIER, ctx, r_rank)

        if ctx.critical:
            r_rank = min(r_rank, 1)

        # ランク補正
        final_defense = int(final_defense * r_rank)

        # その他の補正
        def_modifier = self._events.emit(Event.ON_CALC_DEF_MODIFIER, ctx, 4096)
        final_defense = round_half_down(final_defense * def_modifier/4096)
        final_defense = max(1, final_defense)

        self.def_modifier = def_modifier  # デバッグ用に保存
        self.final_defense = final_defense  # デバッグ用に保存

        return final_defense
