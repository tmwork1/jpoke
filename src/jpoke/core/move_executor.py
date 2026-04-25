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

    def _resolve_hit_count(self, attacker: Pokemon, move: Move) -> int:
        """連続技の実ヒット回数を決定する。

        Args:
            attacker: 技を使用するポケモン
            move: 使用する技

        Returns:
            今回の実ヒット回数
        """
        min_hits = move.data.min_hits
        max_hits = move.data.max_hits

        if max_hits <= 1:
            return 1
        if min_hits == max_hits:
            return max_hits

        # TODO - スキルリンクの処理をイベントハンドラに移す
        if attacker.ability.name == "スキルリンク":
            return max_hits

        # TODO - いかさまダイスの処理をイベントハンドラに移す
        if attacker.has_item("いかさまダイス") and (min_hits, max_hits) == (2, 5):
            return 4 if self.battle.random.random() < 0.5 else 5

        if (min_hits, max_hits) == (2, 5):
            roll = self.battle.random.random()
            if roll < 0.375:
                return 2
            if roll < 0.75:
                return 3
            if roll < 0.875:
                return 4
            return 5

        return self.battle.random.randint(min_hits, max_hits)

    def _resolve_hit_power(self, move: Move, hit_index: int) -> int | None:
        """現在ヒットの威力を取得する。

        Args:
            move: 使用する技
            hit_index: 1 始まりのヒット番号

        Returns:
            ヒットごとの威力。指定がなければ基礎威力を返す。
        """
        if move.data.power_sequence:
            idx = min(hit_index - 1, len(move.data.power_sequence) - 1)
            return move.data.power_sequence[idx]
        return move.data.power

    def _execute_hit(self, ctx: BattleContext) -> bool:
        """1 ヒット分の処理を実行する。

        Args:
            ctx: 技実行中のバトルコンテキスト

        Returns:
            処理を継続できる場合はTrue。無効化などで終了する場合はFalse。
        """
        if self.events.emit(Event.ON_CHECK_IMMUNE, ctx, False):
            return False

        if not ctx.move.is_attack:
            self.events.emit(Event.ON_STATUS_HIT, ctx)
            return True

        critical = self.check_critical(ctx)
        damage = self.battle.determine_damage(
            ctx.attacker, ctx.defender, ctx.move, critical=critical
        )

        ctx.damage = self.events.emit(Event.ON_MODIFY_DAMAGE, ctx, damage)

        if ctx.damage:
            hp_delta = self.battle.modify_hp(ctx.defender, -ctx.damage)
            if hp_delta < 0:
                ctx.defender.hits_taken += 1

            if ctx.defender.fainted:
                ctx.fainted = True

        self.events.emit(Event.ON_HIT, ctx)

        if ctx.damage:
            self.events.emit(Event.ON_DAMAGE, ctx)
            # ステラ補正の消費記録: ダメージを与えた技タイプを記録する
            if ctx.attacker.is_terastallized and ctx.attacker._terastal == 'ステラ':
                ctx.attacker.stellar_boosted_types.add(ctx.move.type)

        return True

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

    def hit_substitute(self, ctx: BattleContext) -> bool:
        """みがわりに技が当たるかどうかを判定する。

        Args:
            ctx: バトルコンテキスト

        Returns:
            bool: 技がみがわりに当たる場合True
        """
        move_labels = [
            "bypass_substitute",
            "sound",
        ]
        hit = ctx.move.is_attack or not ctx.move.has_label(move_labels)
        hit = self.battle.events.emit(
            Event.ON_CHECK_HIT_SUBSTITUTE,
            ctx,
            hit
        )
        return hit

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
        # if move.pp == 0:
        #    move = Move("わるあがき")

        ctx.move = move

        # 技のハンドラを登録
        ctx.move.register_handlers(self.events, ctx.attacker)

        # 技タイプを実行直前に再評価する。
        # （テラバーストなどの可変タイプ技対応）
        move_type = self.get_effective_move_type(ctx.attacker, ctx.move)
        ctx.move.set_type(move_type)

        # 技の実行
        self._execute_move(ctx)

        # 技のハンドラを解除
        ctx.move.unregister_handlers(self.events, ctx.attacker)

    def _execute_move(self, ctx: BattleContext):
        """技実行の内部フローを処理する。

        行動可否チェックから PP 消費、命中判定、連続ヒット処理までを担当する。

        Args:
            ctx: 技実行中のバトルコンテキスト
        """
        # 行動成功判定
        if not self.events.emit(Event.ON_CHECK_ACTION, ctx, True):
            return

        # 技の宣言、PP消費
        self.events.emit(Event.ON_CONSUME_PP, ctx)

        # 溜め技の準備処理
        if not self.events.emit(Event.ON_MOVE_CHARGE, ctx, True):
            return

        # 発動成功判定
        if not self.events.emit(Event.ON_CHECK_MOVE, ctx, True):
            return

        # 反射判定
        if self.events.emit(Event.ON_CHECK_REFLECT, ctx, False):
            ctx.attacker, ctx.defender = ctx.defender, ctx.attacker

        # 発動した技の確定
        ctx.attacker.executed_move = ctx.move

        # HPコストの支払い
        self.events.emit(Event.ON_PAY_HP, ctx)

        # 連続技のヒット回数を決定
        hit_count = self._resolve_hit_count(ctx.attacker, ctx.move)
        ctx.hit_count = hit_count

        # 命中判定が必要な技の場合、ヒットごとに命中判定を行うかどうかを決定
        should_check_hit = ctx.move.accuracy is not None and not ctx.move.self_targeting

        for hit_index in range(1, hit_count + 1):
            ctx.hit_index = hit_index
            ctx.fainted = False
            ctx.move.set_power(self._resolve_hit_power(ctx.move, hit_index))

            # 命中判定: 通常技は初回ヒットのみ、ヒットごと判定技は毎ヒットで判定
            need_hit_check = should_check_hit and \
                (ctx.move.data.check_hit_each_time or hit_index == 1)

            if need_hit_check and not self.check_hit(ctx.attacker, ctx.move):
                break

            # 無効化されたら中断
            if not self._execute_hit(ctx):
                break

            # ひんしになったら中断
            if ctx.fainted:
                break

        # 技の威力を元に戻す（トリプルアクセルなどのため）
        ctx.move.set_power(ctx.move.data.power)

    def generate_context(self, attacker: Pokemon, move: Move) -> BattleContext:
        """BattleContextを生成する。

        Args:
            attacker: 技を使用するポケモン
            move: 使用する技（技コマンドの場合は必須）

        Returns:
            BattleContext: 技の使用に関するコンテキスト情報
        """
        return BattleContext(
            attacker=attacker,
            defender=self.battle.foe(attacker),
            move=move
        )

    def is_contact(self, ctx: BattleContext) -> bool:
        """技が接触技かどうかを判定する。
        Args:
            ctx: BattleContextインスタンス

         Returns:
            技が接触技の場合True
        """
        is_contact = ctx.move.has_label("contact")
        is_contact = self.events.emit(
            Event.ON_CHECK_CONTACT,
            ctx,
            is_contact
        )
        return is_contact

    def get_effective_move_type(self, attacker: Pokemon, move: Move) -> str:
        """技の有効タイプを取得する。

        Args:
            attacker: 技を使用するポケモン
            move: 技オブジェクト

        Returns:
            有効タイプ

        Note:
            特性や効果によるタイプ変化を考慮する。
        """
        # move自身は変更せず、イベント結果の有効タイプを返す。
        return self.events.emit(
            Event.ON_MODIFY_MOVE_TYPE,
            BattleContext(source=attacker, move=move),
            value=move.data.type,
        )

    def get_effective_move_category(self, attacker: Pokemon, move: Move) -> str:
        """技の有効分類を取得する。

        Args:
            attacker: 技を使用するポケモン
            move: 技オブジェクト

        Returns:
            有効分類（物理、特殊、変化）

        Note:
            特性や効果による分類変化を考慮する。
        """
        return self.events.emit(
            Event.ON_MODIFY_MOVE_CATEGORY,
            BattleContext(source=attacker, move=move),
            value=move.category
        )
