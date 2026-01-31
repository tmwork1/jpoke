"""技実行を管理するモジュール。

技の発動、命中判定、ダメージ適用などの処理を担当。
"""

from typing import TYPE_CHECKING

from jpoke.model import Pokemon, Move
from jpoke.utils.enums import Command
from .event import Event, EventContext

if TYPE_CHECKING:
    from .battle import Battle


class MoveExecutor:
    """技実行を管理するクラス。

    技の発動、命中判定、ダメージ適用などの処理を担当。
    Battleクラスから技関連の処理を分離し、単一責任原則を実現。

    Attributes:
        battle: 親となるBattleインスタンス
    """

    def __init__(self, battle: 'Battle'):
        """MoveExecutorを初期化。

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

    def command_to_move(self, player, command: Command) -> Move:
        """コマンドから技オブジェクトを取得。

        Args:
            player: プレイヤー
            command: 実行するコマンド

        Returns:
            技オブジェクト
        """
        if command == Command.STRUGGLE:
            return Move("わるあがき")
        elif command.is_zmove():
            return Move("わるあがき")
        else:
            return player.active.moves[command.idx]

    def check_hit(self, attacker: Pokemon, move: Move) -> bool:
        """技の命中判定。

        Args:
            attacker: 攻撃側のポケモン
            move: 使用する技

        Returns:
            命中した場合True
        """
        if self.battle.test_option.accuracy is not None:
            accuracy = self.battle.test_option.accuracy
        else:
            if not move.data.accuracy:
                return True
            accuracy = self.battle.events.emit(
                Event.ON_CALC_ACCURACY,
                EventContext(attacker=attacker, move=move),
                move.data.accuracy
            )
        return 100 * self.battle.random.random() < accuracy

    def run_move(self, attacker: Pokemon, move: Move):
        """技を実行。

        技のハンドラ登録、イベント発火、ダメージ計算・適用までの
        一連の処理を実行する。

        Args:
            attacker: 攻撃側のポケモン
            move: 使用する技
        """
        ctx = EventContext(
            attacker=attacker,
            defender=self.battle.foe(attacker),
            move=move
        )

        # 技のハンドラを登録
        move.register_handlers(self.battle.events, attacker)

        # 行動成功判定
        self.battle.events.emit(Event.ON_TRY_ACTION, ctx)

        # 技の宣言、PP消費
        self.battle.events.emit(Event.ON_CONSUME_PP, ctx)

        # 発動成功判定
        self.battle.events.emit(Event.ON_TRY_MOVE, ctx)

        # 発動した技の確定
        attacker.executed_move = move

        # 命中判定
        if not self.check_hit(attacker, move):
            return

        # 無効判定
        self.battle.events.emit(Event.ON_TRY_IMMUNE, ctx)

        # ダメージ計算
        damage = self.battle.calc_damage(attacker, move)

        # HPコストの支払い
        self.battle.events.emit(Event.ON_PAY_HP, ctx)

        # ダメージ修正
        damage = self.battle.events.emit(Event.ON_MODIFY_DAMAGE, ctx, damage)

        # ダメージの適用
        if damage:
            self.battle.modify_hp(ctx.defender, -damage)

        # 技を当てたときの処理
        self.battle.events.emit(Event.ON_HIT, ctx)

        # ダメージを与えたときの処理
        if damage:
            self.battle.events.emit(Event.ON_DAMAGE_1, ctx)

        # TODO: 勝敗判定

        if damage:
            self.battle.events.emit(Event.ON_DAMAGE_2, ctx)

        # 技のハンドラを解除
        move.unregister_handlers(self.battle.events, attacker)
