"""技実行を管理するモジュール。

技の発動、命中判定、ダメージ適用などの処理を担当。
"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle, EventManager

from jpoke.utils.type_defs import Type, MoveCategory
from jpoke.utils.math import clamp_stats, clamp_critic
from jpoke.model import Pokemon, Move
from jpoke.enums import LogCode

from .event_manager import Event
from .context import AttackContext
from jpoke.utils import fast_copy

CRIT_RATES = [1/24, 1/8, 1/2, 1]
MULTI_HIT_DISTRIBUTION_2_TO_5 = (
    (0.375, 2),
    (0.75, 3),
    (0.875, 4),
    (1.0, 5),
)


def hit_rank_modifier(rank_acc: int, rank_eva: int) -> float:
    """命中ランク差に基づく命中率補正を計算する。"""
    diff = clamp_stats(rank_acc - rank_eva)
    if diff > 0:
        return (3+diff)/3
    else:
        return 3/(3-diff)


class MoveExecutor:
    """技実行を管理するクラス。

    技の発動、命中判定、ダメージ適用などの処理を担当。
    Battleクラスから技関連の処理を分離し、単一責任原則を実現。

    Attributes:
        battle: 親となるBattleインスタンス
    """

    def __init__(self, battle: Battle):
        self.battle = battle

        # デバッグ用
        self.accuracy: int | None = None
        self.action_success: bool | None = None
        self.move_success: bool | None = None
        self.move_applied: bool | None = None
        self.move_type: Type | None = None
        self.critical_rank: int | None = None
        self.critical: bool | None = None

    def reset_monitoring_flags(self):
        """技実行のモニタリング用フラグをリセットする。"""
        self.accuracy = None
        self.action_success = None
        self.move_success = None
        self.move_applied = None
        self.move_type = None
        self.critical_rank = None
        self.critical = None

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

    def _resolve_hit_count(self, ctx: AttackContext) -> int:
        """連続技の実ヒット回数を決定する。

        Args:
            ctx: バトルコンテキスト

        Returns:
            今回の実ヒット回数
        """
        move = ctx.move
        min_hits, max_hits = move.min_hits, move.max_hits

        if max_hits <= 1:
            base_hit_count = 1
        elif min_hits == max_hits:
            base_hit_count = max_hits
        elif (min_hits, max_hits) == (2, 5):
            base_hit_count = 5
            roll = self.battle.random.random()
            for threshold, hits in MULTI_HIT_DISTRIBUTION_2_TO_5:
                if roll < threshold:
                    base_hit_count = hits
                    break
        else:
            base_hit_count = self.battle.random.randint(min_hits, max_hits)

        return self._events.emit(Event.ON_MODIFY_HIT_COUNT, ctx, base_hit_count)

    def _resolve_hit_power(self, move: Move, hit_index: int) -> int | None:
        """現在ヒットの威力を取得する。

        Args:
            move: 使用する技
            hit_index: 1 始まりのヒット番号

        Returns:
            ヒットごとの威力。指定がなければ基礎威力を返す。
        """
        if move.data.multi_hit is None:
            return move.power

        power_sequence = move.data.multi_hit.get("power_sequence", ())
        if power_sequence:
            idx = min(hit_index - 1, len(power_sequence) - 1)
            return power_sequence[idx]
        return move.power

    def _check_hit(self, ctx: AttackContext) -> bool:
        """技の命中判定。

        Args:
            ctx: バトルコンテキスト

        Returns:
            命中した場合True
        """
        # テストオプションによる命中率の上書き
        if self.battle.test_option.accuracy is not None:
            print(f"Test option override: accuracy set to {self.battle.test_option.accuracy}")
            self.accuracy = self.battle.test_option.accuracy
            return 100 * self.battle.random.random() < self.accuracy

        attacker = ctx.attacker
        defender = ctx.defender
        move = ctx.move
        accuracy = move.accuracy

        # 命中率がNoneなら必中
        if accuracy is None:
            return True

        # 技の命中変更 + 命中補正
        accuracy = self._events.emit(Event.ON_MODIFY_ACCURACY, ctx, accuracy)

        # 必中処理：イベントハンドラがNoneを返した場合は必中
        if accuracy is None:
            self.accuracy = accuracy
            return True

        # ランク補正
        ranks = {
            "ACC": attacker.rank["ACC"],
            "EVA": defender.rank["EVA"]
        }
        modified_rank = self._events.emit(Event.ON_GET_STAT_RANK, ctx, ranks)
        rank_modifier = hit_rank_modifier(modified_rank["ACC"], modified_rank["EVA"])
        accuracy = int(accuracy * rank_modifier)

        self.accuracy = accuracy  # デバッグ用に保存

        return 100 * self.battle.random.random() < accuracy

    def _check_critical(self, ctx: AttackContext) -> bool:
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
        # 急所ランクの計算
        critical_rank = self._events.emit(
            Event.ON_CALC_CRITICAL_RANK,
            ctx,
            ctx.move.critical_rank
        )
        critical_rank = clamp_critic(critical_rank)

        # 急所確率の計算
        crit_rate = self._events.emit(
            Event.ON_MODIFY_CRITICAL_RATE,
            ctx,
            CRIT_RATES[critical_rank]
        )

        self.critical_rank = critical_rank  # デバッグ用に保存

        return self.battle.random.random() < crit_rate

    def check_hit_substitute(self, ctx: AttackContext) -> bool:
        """みがわりに技が当たるかどうかを判定する。

        Args:
            ctx: バトルコンテキスト

        Returns:
            bool: 技がみがわりに当たる場合True
        """
        if ctx.move.target != "foe":
            return False
        return self._events.emit(Event.ON_CHECK_HIT_SUBSTITUTE, ctx, True)

    def run_move(self, attacker: Pokemon, move: Move):
        """技を実行。

        技のハンドラ登録、イベント発火、ダメージ計算・適用までの
        一連の処理を実行する。

        Args:
            attacker: 攻撃側のポケモン
            move: 使用する技
        """
        self.reset_monitoring_flags()

        defender = self.battle.foe(attacker)
        ctx = AttackContext(attacker=attacker, defender=defender)

        # 技の変更 (アンコールなど)
        move = self._events.emit(Event.ON_MODIFY_MOVE, ctx, move)
        if move is None:
            return

        # PPが0の技はわるあがきに置き換える
        if move.pp == 0:
            move = Move("わるあがき")

        ctx.move = move

        # 技のハンドラを登録
        ctx.move.register_handlers(self._events, ctx.attacker)

        try:
            # 技タイプを評価する（可変技対応）
            ctx.move.type = self.resolve_move_type(ctx.attacker, ctx.move)
            self.move_type = ctx.move.type

            # 技カテゴリを評価する（可変技対応）
            ctx.move.category = self.resolve_move_category(ctx.attacker, ctx.move)
            self.move_category = ctx.move.category

            # 行動成功判定
            self.action_success = self._events.emit(Event.ON_TRY_ACTION, ctx, True)
            if self.action_success:
                # PP消費
                self._consume_pp(ctx)

                # かやたぶりを適用する
                self._events.emit(Event.ON_BEGIN_MOVE, ctx)

                # 技の実行
                self._execute_move(ctx)

        finally:
            # 技の状態をリセットする（タイプや威力の変更を元に戻す）
            ctx.move.reset()

            # かやたぶりを解除する
            self._events.emit(Event.ON_END_MOVE, ctx)

            # 技のハンドラを解除
            ctx.move.unregister_handlers(self._events, ctx.attacker)

    def _check_hit_by_type(self, ctx: AttackContext) -> bool:
        """タイプ相性によって技が有効かを判定する。"""
        type_modifier = self.battle.damage_calculator.calc_def_type_modifier(ctx)

        if type_modifier == 0:
            self.battle.add_event_log(
                ctx.attacker,
                LogCode.MOVE_IMMUNED,
                payload={"reason": "タイプ無効"}
            )
            return False
        return True

    def _execute_move(self, ctx: AttackContext) -> None:
        """技実行の内部フローを処理する。

        行動可否チェックから PP 消費、命中判定、連続ヒット処理までを担当する。

        Args:
            ctx: 技実行中のバトルコンテキスト
        """
        # 溜め技の準備
        if not self._events.emit(Event.ON_MOVE_CHARGE, ctx, True):
            return

        # 発動成功判定(1)
        self.move_success = self._events.emit(Event.ON_TRY_MOVE_1, ctx, True)
        if not self.move_success:
            return

        # 攻撃技のタイプ相性判定
        if ctx.move.is_attack and not self._check_hit_by_type(ctx):
            return

        # 発動成功判定(2)
        self.move_success = self._events.emit(Event.ON_TRY_MOVE_2, ctx, True)
        if not self.move_success:
            return

        # 発動した技の確定
        ctx.attacker.executed_move = ctx.move

        # HPコストの支払い
        self._events.emit(Event.ON_PAY_HP, ctx)

        # 反射判定
        if self._events.emit(Event.ON_CHECK_REFLECT, ctx, False):
            self.battle.add_event_log(ctx.defender, LogCode.MOVE_REFLECTED)
            ctx.attacker, ctx.defender = ctx.defender, ctx.attacker

        # 連続技のヒット回数を決定
        hit_count = self._resolve_hit_count(ctx)
        ctx.hit_count = hit_count

        # 命中判定が必要な技の場合、ヒットごとに命中判定を行うかどうかを決定
        for hit_index in range(1, hit_count + 1):
            ctx.hit_index = hit_index

            # ヒットごとの技の威力を設定
            ctx.move.power = self._resolve_hit_power(ctx.move, hit_index)
            self.move_power = ctx.move.power

            # 命中判定: 通常技は初回ヒットのみ、ヒットごと判定技は毎ヒットで判定
            need_hit_check = (
                ctx.move.accuracy is not None
                and (hit_index == 1 or ctx.move.has_label("check_hit_each_time"))
            )

            if need_hit_check and not self._check_hit(ctx):
                self.battle.add_event_log(ctx.attacker, LogCode.MOVE_MISSED)
                break

            # 無効化されたら中断
            self.move_applied = self._events.emit(Event.ON_BEFORE_APPLY_MOVE, ctx, True)
            if not self.move_applied:
                return

            # 技が当たったときの処理を実行
            self._execute_hit(ctx)

            # ひんしになったら中断
            if ctx.defender.fainted or ctx.attacker.fainted:
                break

        # 技実行完了後の処理（状態管理・撤去など）
        self._events.emit(Event.ON_MOVE_END, ctx)

    def _execute_hit(self, ctx: AttackContext) -> None:
        """1 ヒット分の処理を実行する。

        Args:
            ctx: 技実行中のバトルコンテキスト
        """
        # 変化技の処理はダメージ処理とは別に行う
        if ctx.move.category == "変化":
            self._execute_status_hit(ctx)
            return

        self.critical = self._check_critical(ctx)
        damage = self.battle.roll_damage(
            ctx.attacker, ctx.defender, ctx.move, critical=self.critical
        )

        damage = self._events.emit(Event.ON_MODIFY_MOVE_DAMAGE, ctx, damage)

        actual_damage = -self.battle.modify_hp(
            ctx.defender, -damage, source=ctx.attacker, move=ctx.move, reason="move_damage"
        )

        self._events.emit(Event.ON_HIT, ctx, actual_damage)

        # ダメージを与えた後の処理（actual_damage は正値=ダメージ量）
        if actual_damage <= 0:
            return

        ctx.defender.hits_taken += 1

        self._events.emit(Event.ON_DAMAGE_HIT, ctx, actual_damage)

        if ctx.defender.fainted:
            self._events.emit(Event.ON_MOVE_KO, ctx, actual_damage)

        # ステラ補正の消費記録: ダメージを与えた技タイプを記録する
        if ctx.attacker.active_tera_type == 'ステラ':
            ctx.attacker.stellar_boosted_types.add(ctx.move.type)

    def _execute_status_hit(self, ctx: AttackContext) -> None:
        """状態変化技の命中処理を実行する。

        Args:
            ctx: 技実行中のバトルコンテキスト
        """
        # 状態変化技の命中処理は、通常のダメージ処理とは別にON_STATUS_HITイベントで行う。
        # これにより、ダメージを与えない状態変化技（でんじはなど）も同様のフローで処理できる。
        result = self._events.emit(Event.ON_STATUS_HIT, ctx, True)
        if not result:
            self.battle.add_event_log(
                ctx.attacker,
                LogCode.MOVE_FAILED,
                payload={"move": ctx.move.name}
            )

    def resolve_move_type(self, attacker: Pokemon, move: Move) -> Type:
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
        return self._events.emit(
            Event.ON_MODIFY_MOVE_TYPE,
            AttackContext(attacker=attacker, move=move),
            value=move.data.type,
        )

    def resolve_move_category(self, attacker: Pokemon, move: Move) -> MoveCategory:
        """技の有効なカテゴリを判定する。

        Args:
            attacker: 技を使用するポケモン
            move: 技オブジェクト

        Returns:
            有効分類（物理、特殊、変化）

        Note:
            特性や効果による分類変化を考慮する。
        """
        return self._events.emit(
            Event.ON_MODIFY_MOVE_CATEGORY,
            AttackContext(attacker=attacker, move=move),
            value=move.category
        )

    def _consume_pp(self, ctx: AttackContext):
        """技のPPを消費する。

        技を使用した際にPPを減らします。

        Args:
            ctx: EventContextインスタンス
        """
        v = self._events.emit(Event.ON_MODIFY_PP_CONSUMED, ctx, 1)
        ctx.move.pp = max(0, ctx.move.pp - v)
        self.battle.add_event_log(
            ctx.attacker,
            LogCode.PP_CONSUMED,
            payload={"move": ctx.move.name, "value": v}
        )
