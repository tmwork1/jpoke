"""素早さ計算を管理するモジュール。

実効素早さ、素早さ順序、行動順序の計算を担当。
"""

from typing import TYPE_CHECKING

from jpoke.model import Pokemon
from .event import Event, EventContext

if TYPE_CHECKING:
    from .battle import Battle


class SpeedCalculator:
    """素早さ計算を管理するクラス。

    実効素早さの計算、素早さ順序の決定、行動順序の決定を担当。
    Battleクラスから素早さ関連の処理を分離し、単一責任原則を実現。

    Attributes:
        battle: 親となるBattleインスタンス
    """

    def __init__(self, battle: 'Battle'):
        """SpeedCalculatorを初期化。

        Args:
            battle: 親となるBattleインスタンス
        """
        self.battle = battle

    def update_reference(self, battle: 'Battle'):
        """Battleインスタンスの参照を更新。

        Args:
            battle: 新しいBattleインスタンス
        """
        self.battle = battle

    def calc_effective_speed(self, mon: Pokemon) -> int:
        """ポケモンの実効素早さを計算。

        イベントシステムを通じて特性・持ち物による補正を適用。

        Args:
            mon: 対象のポケモン

        Returns:
            補正後の実効素早さ
        """
        return self.battle.events.emit(
            Event.ON_CALC_SPEED,
            EventContext(source=mon),
            mon.stats["S"]
        )

    def calc_speed_order(self) -> list[Pokemon]:
        """現在場に出ているポケモンの素早さ順序を計算。

        実効素早さが同じ場合はランダムに決定。

        Returns:
            素早さの速い順にソートされたポケモンのリスト
        """
        speeds = [self.calc_effective_speed(p) for p in self.battle.actives]
        if speeds[0] == speeds[1]:
            actives = self.battle.actives.copy()
            self.battle.random.shuffle(actives)
        else:
            paired = sorted(
                zip(speeds, self.battle.actives),
                key=lambda pair: pair[0],
                reverse=True
            )
            _, actives = zip(*paired)
        return actives

    def calc_action_order(self) -> list[Pokemon]:
        """技の行動順序を計算。

        優先度と実効素早さを考慮して行動順を決定。
        既に交代したポケモンは除外される。
        同優先度・同速度の場合はランダムに決定。

        Returns:
            行動順にソートされたポケモンのリスト
        """
        actives, speeds = [], []
        for i, player in enumerate(self.battle.players):
            if player.has_switched:
                continue

            mon = player.active

            # 実効素早さを計算
            speed = self.calc_effective_speed(mon)

            # TODO: トリックルームによる素早さ反転処理の追加
            # 例:
            # speed = self.battle.events.emit(
            #     Event.ON_CHECK_TRICK_ROOM_SPEED,
            #     EventContext(target=mon),
            #     speed
            # )

            command = player.reserved_commands[-1]
            move = self.battle.command_to_move(self.battle.players[i], command)

            # 技の優先度を取得（基本値）
            base_priority = move.priority if move else 0

            # ON_CALC_ACTION_SPEEDイベントで優先度を拡張可能にする
            priority = self.battle.events.emit(
                Event.ON_CALC_ACTION_SPEED,
                EventContext(target=mon, move=move),
                base_priority
            )

            # 優先度と素早さをペアで保持（同値時のランダルを可能にするため）
            # タプル (優先度, 素早さ) の形式で保持し、Python のタプル比較を利用
            action_key = (priority, speed)
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
