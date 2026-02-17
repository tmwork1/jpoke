"""技実行を管理するモジュール。

技の発動、命中判定、ダメージ適用などの処理を担当。
"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle, EventManager

from jpoke.model import Pokemon, Move
from jpoke.enums import Command
from jpoke.utils.constants import HIT_RANK_MODIFIERS

from .event import Event
from .context import BattleContext


class MoveExecutor:
    """技実行を管理するクラス。

    技の発動、命中判定、ダメージ適用などの処理を担当。
    Battleクラスから技関連の処理を分離し、単一責任原則を実現。

    Attributes:
        battle: 親となるBattleインスタンス
    """

    def __init__(self, battle: Battle):
        """MoveExecutorを初期化。

        Args:
            battle: 親となるBattleインスタンス
        """
        self.battle = battle

    def update_reference(self, battle: Battle):
        """Battleインスタンスの参照を更新。

        Args:
            battle: 新しいBattleインスタンス
        """
        self.battle = battle

    @property
    def events(self) -> EventManager:
        """イベント管理システムへのショートカットプロパティ。"""
        return self.battle.events

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
        accuracy = self.events.emit(
            Event.ON_MODIFY_ACCURACY,
            BattleContext(attacker=attacker, defender=self.battle.foe(attacker), move=move),
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

    def check_critical(self, ctx: BattleContext) -> bool:
        """急所判定を行う。

        急所ランクに基づいて急所確率を計算します：
        - ランク0: 1/24（約4.2%）
        - ランク1: 1/8（12.5%）
        - ランク2: 1/2（50%）
        - ランク3以上: 1/1（100%、上限）

        Args:
            ctx: バトルコンテキスト

        Returns:
            bool: 急所に当たるかどうか
        """
        rank = self.events.emit(
            Event.ON_CALC_CRITICAL_RANK,
            ctx,
            ctx.move.critical_rank
        )
        rank = max(0, min(3, rank))
        critical_rates = [1/24, 1/8, 1/2, 1]
        return self.battle.random.random() < critical_rates[rank]

    def run_move(self, attacker: Pokemon, move: Move):
        """技を実行。

        技のハンドラ登録、イベント発火、ダメージ計算・適用までの
        一連の処理を実行する。

        Args:
            attacker: 攻撃側のポケモン
            move: 使用する技
        """
        defender = self.battle.foe(attacker)
        ctx = BattleContext(attacker=attacker, defender=defender)

        # 技の変更 (アンコールなど)
        move = self.events.emit(Event.ON_MODIFY_MOVE, ctx, move)
        if move is None:
            return

        # PPが0の技はわるあがきに置き換える
        if move.pp == 0:
            move = Move("わるあがき")

        ctx.move = move

        # 技のハンドラを登録
        ctx.move.register_handlers(self.events, ctx.attacker)

        # 技の実行
        self._execute_move(ctx)

        # 技のハンドラを解除
        ctx.move.unregister_handlers(self.events, ctx.attacker)

    def _execute_move(self, ctx: BattleContext):
        """技を実行する内部メソッド。
        """
        # 技の準備行動
        self.events.emit(Event.ON_PREPARE_MOVE, ctx)

        # 行動成功判定（行動者自身を対象にする）
        if not self.events.emit(Event.ON_TRY_ACTION, ctx, True):
            return

        # 技の宣言、PP消費
        self.events.emit(Event.ON_CONSUME_PP, ctx)

        # 発動成功判定
        if not self.events.emit(Event.ON_TRY_MOVE, ctx, True):
            pass

        # まもる系判定（ON_TRY_MOVE Priority 100: 無効化判定）
        if self.events.emit(Event.ON_CHECK_PROTECT, ctx, False):
            return

        # 姿消し・無敵判定（ON_TRY_MOVE Priority 100: 無効化判定）
        if self.events.emit(Event.ON_CHECK_INVULNERABLE, ctx, False):
            return

        # 反射判定（ON_TRY_MOVE Priority 100: マジックコート等による反射）
        if self.events.emit(Event.ON_CHECK_REFLECT, ctx, False):
            return

        # 発動した技の確定
        ctx.attacker.executed_move = ctx.move

        # 命中判定（仕様書: ON_TRY_MOVE終了後のInterrupt）
        if not self.check_hit(ctx.attacker, ctx.move):
            return

        # 無効判定（ON_TRY_IMMUNE: Priority 10-100）
        # Priority 30: みがわり、Priority 100: その他の判定
        is_immune = self.events.emit(Event.ON_TRY_IMMUNE, ctx, False)
        if is_immune:
            return

        # 急所判定
        critical = self.check_critical(ctx)

        # ダメージ計算
        damage = self.battle.determine_damage(
            ctx.attacker, ctx.defender, ctx.move, critical=critical
        )

        # HPコストの支払い
        self.events.emit(Event.ON_PAY_HP, ctx)

        # ダメージ修正
        damage = self.events.emit(Event.ON_MODIFY_DAMAGE, ctx, damage)

        # ダメージ適用前処理
        damage = self.events.emit(Event.ON_BEFORE_DAMAGE_APPLY, ctx, damage)

        # ダメージの適用
        if damage:
            self.battle.modify_hp(ctx.defender, -damage)

            # ひんし時の処理
            if ctx.defender.hp == 0:
                ctx.fainted = True

        # 技を当てたときの処理（ダメージ情報を含める）
        ctx.damage = damage
        self.events.emit(Event.ON_HIT, ctx)

        # ダメージを与えたときの処理
        if damage:
            self.events.emit(Event.ON_DAMAGE, ctx)
