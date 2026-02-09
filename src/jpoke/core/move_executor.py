"""技実行を管理するモジュール。

技の発動、命中判定、ダメージ適用などの処理を担当。
"""

from typing import TYPE_CHECKING

from jpoke.model import Pokemon, Move
from jpoke.utils.enums import Command
from jpoke.utils.constants import HIT_RANK_MODIFIERS
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
        # テストオプションによる命中率の上書き
        if self.battle.test_option.accuracy is not None:
            accuracy = self.battle.test_option.accuracy
            return 100 * self.battle.random.random() < accuracy

        # 命中率がNoneなら必中
        if move.accuracy is None:
            return True

        # 技の命中変更 + 命中補正
        accuracy = self.battle.events.emit(
            Event.ON_MODIFY_ACCURACY,
            EventContext(attacker=attacker, defender=self.battle.foe(attacker), move=move),
            move.accuracy
        )

        # 必中処理：イベントハンドラがNoneを返した場合は必中
        if accuracy is None:
            return True

        # ランク補正
        defender = self.battle.foe(attacker)
        rank_diff = attacker.rank["acc"] - defender.rank["eva"]
        rank_diff = max(-6, min(6, rank_diff))
        accuracy = int(accuracy * HIT_RANK_MODIFIERS[rank_diff])

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

        # 行動成功判定（行動者自身を対象にする）
        if not self.battle.events.emit(Event.ON_TRY_ACTION, ctx, True):
            return

        # 技の宣言、PP消費
        self.battle.events.emit(Event.ON_CONSUME_PP, ctx)

        # 発動成功判定
        if not self.battle.events.emit(Event.ON_TRY_MOVE, ctx, True):
            pass

        # まもる系判定（ON_TRY_MOVE Priority 100: 無効化判定）
        if self.battle.events.emit(Event.ON_CHECK_PROTECT, ctx, False):
            return

        # 姿消し・無敵判定（ON_TRY_MOVE Priority 100: 無効化判定）
        if self.battle.events.emit(Event.ON_CHECK_INVULNERABLE, ctx, False):
            return

        # 反射判定（ON_TRY_MOVE Priority 100: マジックコート等による反射）
        if self.battle.events.emit(Event.ON_CHECK_REFLECT, ctx, False):
            return

        # 先制技の有効判定（例: サイコフィールド）
        priority_valid = self.battle.events.emit(
            Event.ON_CHECK_PRIORITY_VALID,
            ctx,
            True
        )
        if not priority_valid:
            return

        # 発動した技の確定
        attacker.executed_move = move

        # 命中判定（仕様書: ON_TRY_MOVE終了後のInterrupt）
        if not self.check_hit(attacker, move):
            return

        # 無効判定（ON_TRY_IMMUNE: Priority 10-100）
        # Priority 30: みがわり、Priority 100: その他の判定
        is_immune = self.battle.events.emit(Event.ON_TRY_IMMUNE, ctx, False)
        if is_immune:
            return

        # ダメージ計算
        damage = self.battle.calc_damage(attacker, move)

        # HPコストの支払い
        self.battle.events.emit(Event.ON_PAY_HP, ctx)

        # ダメージ修正
        damage = self.battle.events.emit(Event.ON_MODIFY_DAMAGE, ctx, damage)

        # ダメージ適用前処理
        damage = self.battle.events.emit(Event.ON_BEFORE_DAMAGE_APPLY, ctx, damage)

        # ダメージの適用
        if damage:
            self.battle.modify_hp(ctx.defender, -damage)

        # ひんし時の処理
        if damage and ctx.defender and ctx.defender.hp == 0:
            self.battle.events.emit(Event.ON_FAINT, ctx)

        # 技を当てたときの処理（ダメージ情報を含める）
        ctx.damage = damage
        self.battle.events.emit(Event.ON_HIT, ctx)

        # ダメージを与えたときの処理
        if damage:
            self.battle.events.emit(Event.ON_DAMAGE_1, ctx)

        if damage:
            self.battle.events.emit(Event.ON_DAMAGE_2, ctx)

        # 技のハンドラを解除
        move.unregister_handlers(self.battle.events, attacker)
