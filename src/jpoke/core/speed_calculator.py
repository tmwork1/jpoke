"""素早さ計算を管理するモジュール。

実効素早さ、素早さ順序、行動順序の計算を担当。
"""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle, EventManager
    from jpoke.model import Move

from jpoke.enums import DomainEvent
from jpoke.model.pokemon import Pokemon
from .context import EventContext, AttackContext
from jpoke.utils import fast_copy


class SpeedCalculator:
    """素早さ計算を管理するクラス。

    実効素早さの計算、素早さ順序の決定、行動順序の決定を担当。
    Battleクラスから素早さ関連の処理を分離し、単一責任原則を実現。

    Attributes:
        battle: 親となるBattleインスタンス
    """

    def __init__(self, battle: Battle):
        self.battle = battle
        # calc_effective_speed() の再入防止用。現在計算中のポケモンの集合。
        # すいすい等の天候依存の素早さ補正ハンドラが battle.weather_for() を
        # 呼び、それが ON_CHECK_WEATHER_IMMUNE を発火し、そのハンドラの
        # 素早さソート（_sort_handlers）が同じポケモンの実効素早さを再度
        # 要求する循環を断ち切るために使う（RecursionError対策）。
        self._computing_speed: set[Pokemon] = set()

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        fast_copy(self, new, keys_to_deepcopy=[])
        return new

    def update_reference(self, battle: Battle):
        """Battleインスタンスの参照を更新。

        Args:
            battle: 新しいBattleインスタンス
        """
        self.battle = battle

    @property
    def _events(self) -> EventManager:
        return self.battle.events

    def calc_effective_speed(self, mon: Pokemon) -> int:
        """ポケモンの実効素早さを計算。

        含まれる要素
        - 特性による補正
        - アイテムによる補正

        含まれない要素
        - トリックルームなどの行動順序補正
        - 技の優先度

        Args:
            mon: 対象のポケモン

        Returns:
            補正後の実効素早さ
        """
        # 再入ガード: 同じポケモンの実効素早さ計算が既に進行中の場合は、
        # 素早さ実数値をそのまま返して再帰を打ち切る。
        # （例: すいすい の ON_CALC_SPEED ハンドラが battle.weather_for()
        #  経由で ON_CHECK_WEATHER_IMMUNE を発火し、そのハンドラリストの
        #  素早さソートが同じポケモンの calc_effective_speed() を再度
        #  要求するケース。ON_CHECK_WEATHER_IMMUNE は subject_spec で
        #  対象ポケモンに一致するハンドラのみが実行されるため、ソート順が
        #  結果に影響しない＝フォールバック値を使っても安全）
        if mon in self._computing_speed:
            return mon.stats["spe"]

        self._computing_speed.add(mon)
        try:
            return self.battle.events.emit(
                DomainEvent.ON_CALC_SPEED,
                EventContext(source=mon),
                mon.stats["spe"]
            )
        finally:
            self._computing_speed.discard(mon)

    def calc_speed_order_key(self, mon: Pokemon) -> int:
        """ポケモンの行動速度を計算する。

        含まれる要素
        - 特性による補正
        - アイテムによる補正
        - トリックルームなどの行動順序補正

        含まれない要素
        - 技の優先度

        Args:
            mon: 対象のポケモン

        Returns:
            補正後の行動素早さ
        """
        # 基本の実効素早さを取得
        base_speed = self.calc_effective_speed(mon)

        # 素早さ反転の適用
        return self.battle.events.emit(
            DomainEvent.ON_CHECK_SPEED_REVERSE,
            EventContext(source=mon),
            base_speed
        )

    def calc_move_priority(self, attacker: Pokemon, move: Move) -> int:
        """技による優先度補正後の優先度を計算する。

        Args:
            attacker: 攻撃側のポケモン
            move: 使用する技

        Returns:
            修正後の優先度
        """
        # 技の優先度を取得（基本値）
        base_priority = move.priority if move else 0

        # ON_CALC_ACTION_SPEEDイベントで優先度を拡張可能にする
        return self.battle.events.emit(
            DomainEvent.ON_MODIFY_MOVE_PRIORITY,
            AttackContext(attacker=attacker, defender=self.battle.foe(attacker), move=move),
            base_priority
        )

    def resolve_speed_order(self) -> list[Pokemon]:
        """現在場に出ているポケモンの素早さ順序を計算。

        実効素早さが同じ場合はランダムに決定。

        Returns:
            素早さの速い順にソートされたポケモンのリスト
        """
        actives = self.battle.actives.copy()
        if len(actives) <= 1:
            return actives

        speeds = [self.calc_speed_order_key(p) for p in actives]
        if len(set(speeds)) == 1:
            # 同速の場合はランダムに順序を決定
            self.battle.random.shuffle(actives)
        else:
            # 素早さ順にソート
            paired = sorted(
                zip(speeds, actives),
                key=lambda pair: pair[0],
                reverse=True
            )
            actives = [mon for _, mon in paired]
        return actives

    def resolve_action_order(self) -> list[Pokemon]:
        """技の行動順序を解決する。

        優先度と実効素早さを考慮して行動順を決定。
        既に交代したポケモンは除外される。
        同優先度・同速度の場合はランダムに決定。

        Returns:
            行動順にソートされたポケモンのリスト
        """
        actives, speeds = [], []
        for player, state in self.battle.player_states.items():
            if state.has_switched:
                continue

            mon = state.active

            # 行動速度を計算
            speed_key = self.calc_speed_order_key(mon)

            # 技の優先度を取得
            command = state.next_command
            move = self.battle.command_to_move(player, command)
            move_priority = self.calc_move_priority(mon, move)

            # 後攻ティアを計算（0=通常, -1=あとだし等）
            ctx = AttackContext(attacker=mon, move=move)
            back_tier = self.battle.events.emit(DomainEvent.ON_CALC_BACK_TIER, ctx, 0)

            # 優先度・後攻ティア・素早さの3要素タプルで行動順を決定
            # タプル降順ソートで (高優先度, 高ティア, 高速) が先攻
            action_key = (move_priority, back_tier, speed_key)
            speeds.append(action_key)
            actives.append(mon)

        # Sort by action_key（優先度優先、同一優先度時は素早さで判断）
        if len(actives) > 1:
            paired = sorted(
                zip(speeds, actives),
                key=lambda pair: pair[0],
                reverse=True
            )

            # 同優先度・同速度のグループごとにシャッフルする
            result_actives = []
            i = 0
            while i < len(paired):
                current_key = paired[i][0]
                group = [paired[i][1]]

                # 同じキーのモンを集める
                j = i + 1
                while j < len(paired) and paired[j][0] == current_key:
                    group.append(paired[j][1])
                    j += 1

                # グループ内をシャッフル
                self.battle.random.shuffle(group)
                result_actives.extend(group)

                i = j

            actives = result_actives
        elif len(actives) == 1:
            # 1匹の場合はそのままソート処理をスキップ
            pass
        else:
            # 0匹の場合は空リストを返す
            pass

        return actives
