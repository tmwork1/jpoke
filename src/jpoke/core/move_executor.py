"""技実行を管理するモジュール。

技の発動、命中判定、ダメージ適用などの処理を担当。
"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle, EventManager

from jpoke.model import Pokemon, Move
from jpoke.enums import LogCode

from .event_manager import Event
from .context import BattleContext


CRIT_RATES = [1/24, 1/8, 1/2, 1]


def hit_rank_modifier(rank_acc: int, rank_eva: int) -> float:
    """命中ランク差に基づく命中率補正を計算する。"""
    diff = max(-6, min(6, rank_acc - rank_eva))
    if diff > 0:
        return (3+diff)/3
    else:
        return 3/(3-abs(diff))


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

        # デバッグ用
        self.accuracy: int | None = None
        self.action_success: bool | None = None
        self.move_success: bool | None = None
        self.move_applied: bool | None = None
        self.crit_rank: int | None = None
        self.critical: bool | None = None

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

    def _resolve_hit_count(self, ctx: BattleContext) -> int:
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
            roll = self.battle.random.random()
            if roll < 0.375:
                base_hit_count = 2
            elif roll < 0.75:
                base_hit_count = 3
            elif roll < 0.875:
                base_hit_count = 4
            else:
                base_hit_count = 5
        else:
            base_hit_count = self.battle.random.randint(min_hits, max_hits)

        return self.events.emit(Event.ON_MODIFY_HIT_COUNT, ctx, base_hit_count)

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

    def _check_hit(self, ctx: BattleContext) -> bool:
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
        self.accuracy = move.accuracy

        # 命中率がNoneなら必中
        if self.accuracy is None:
            return True

        # 技の命中変更 + 命中補正
        self.accuracy = self.events.emit(Event.ON_MODIFY_ACCURACY, ctx, self.accuracy)

        # 必中処理：イベントハンドラがNoneを返した場合は必中
        if self.accuracy is None:
            return True

        # ランク補正
        rank_modifier = hit_rank_modifier(attacker.rank["ACC"], defender.rank["EVA"])
        self.accuracy = int(self.accuracy * rank_modifier)
        return 100 * self.battle.random.random() < self.accuracy

    def _check_critical(self, ctx: BattleContext) -> bool:
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
        self.crit_rank = self.events.emit(
            Event.ON_CALC_CRITICAL_RANK, ctx, ctx.move.critical_rank
        )
        self.crit_rank = max(0, min(3, self.crit_rank))

        # 急所確率の計算
        crit_rate = self.events.emit(
            Event.ON_MODIFY_CRITICAL_RATE, ctx, CRIT_RATES[self.crit_rank]
        )
        return self.battle.random.random() < crit_rate

    def check_hit_substitute(self, ctx: BattleContext) -> bool:
        """みがわりに技が当たるかどうかを判定する。

        Args:
            ctx: バトルコンテキスト

        Returns:
            bool: 技がみがわりに当たる場合True
        """
        if ctx.move.target != "foe":
            return False
        return self.battle.events.emit(Event.ON_CHECK_HIT_SUBSTITUTE, ctx, True)

    def run_move(self, attacker: Pokemon, move: Move):
        """技を実行。

        技のハンドラ登録、イベント発火、ダメージ計算・適用までの
        一連の処理を実行する。

        Args:
            attacker: 攻撃側のポケモン
            move: 使用する技
        """
        self.accuracy = None
        self.action_success = False
        self.move_success = False
        self.move_applied = False

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

        # 技タイプを評価する（可変技対応）
        ctx.move.set_type(
            self.resolve_move_type(ctx.attacker, ctx.move)
        )

        # 技カテゴリを評価する（可変技対応）
        ctx.move.set_category(
            self.resolve_move_category(ctx.attacker, ctx.move)
        )

        # 行動成功判定
        self.action_success = self.events.emit(Event.ON_TRY_ACTION, ctx, True)
        if not self.action_success:
            return

        # PP消費
        self._consume_pp(ctx)

        # かやたぶりを有効にする
        self.events.emit(Event.ON_ACTIVATE_MOLD_BREAKER, ctx)

        # 技の実行
        self._execute_move(ctx)

        # かやたぶりを無効にする
        self.events.emit(Event.ON_DEACTIVATE_MOLD_BREAKER, ctx)

        # 技のハンドラを解除
        ctx.move.unregister_handlers(self.events, ctx.attacker)

    def _check_hit_by_type(self, ctx: BattleContext) -> bool:
        """タイプ相性によって技が有効かを判定する。"""
        type_modifier = self.battle.damage_calculator.calc_def_type_modifier(ctx=ctx)

        if type_modifier == 0:
            self.battle.add_event_log(
                ctx.attacker,
                LogCode.MOVE_IMMUNED,
                payload={"reason": "タイプ無効"},
            )
            return False
        return True

    def _execute_move(self, ctx: BattleContext):
        """技実行の内部フローを処理する。

        行動可否チェックから PP 消費、命中判定、連続ヒット処理までを担当する。

        Args:
            ctx: 技実行中のバトルコンテキスト
        """
        # 溜め技の準備
        if not self.events.emit(Event.ON_MOVE_CHARGE, ctx, True):
            return

        # 発動成功判定(1)
        self.move_success = self.events.emit(Event.ON_TRY_MOVE_1, ctx, True)
        if not self.move_success:
            return

        # 攻撃技のタイプ相性判定
        if ctx.move.is_attack and not self._check_hit_by_type(ctx):
            return

        # 発動成功判定(2)
        self.move_success = self.events.emit(Event.ON_TRY_MOVE_2, ctx, True)
        if not self.move_success:
            return

        # 反射判定
        if self.events.emit(Event.ON_CHECK_REFLECT, ctx, False):
            ctx.attacker, ctx.defender = ctx.defender, ctx.attacker

        # 発動した技の確定
        ctx.attacker.executed_move = ctx.move

        # HPコストの支払い
        self.events.emit(Event.ON_PAY_HP, ctx)

        # 連続技のヒット回数を決定
        hit_count = self._resolve_hit_count(ctx)
        ctx.hit_count = hit_count

        # 命中判定が必要な技の場合、ヒットごとに命中判定を行うかどうかを決定
        for hit_index in range(1, hit_count + 1):
            ctx.hit_index = hit_index

            # ヒットごとの技の威力を設定
            ctx.move.set_power(self._resolve_hit_power(ctx.move, hit_index))

            # 命中判定: 通常技は初回ヒットのみ、ヒットごと判定技は毎ヒットで判定
            need_hit_check = (
                ctx.move.accuracy is not None
                and (ctx.move.has_label("check_hit_each_time") or hit_index == 1)
            )

            if need_hit_check and not self._check_hit(ctx):
                self.battle.add_event_log(ctx.attacker, LogCode.MOVE_MISSED)
                break

            # 無効化されたら中断
            self.move_applied = self.events.emit(Event.ON_APPLY_MOVE, ctx, True)
            if not self.move_applied:
                return False

            self._execute_hit(ctx)

            # ひんしになったら中断
            if ctx.defender.fainted or ctx.attacker.fainted:
                break

        # 技の威力を元に戻す（トリプルアクセルなどのため）
        ctx.move.set_power(ctx.move.data.power)

        # 技実行完了後の処理（状態管理・撤去など）
        self.events.emit(Event.ON_MOVE_END, ctx)

    def _execute_hit(self, ctx: BattleContext) -> None:
        """1 ヒット分の処理を実行する。

        Args:
            ctx: 技実行中のバトルコンテキスト
        """
        # 変化技はダメージ計算をせず、効果処理のみ行う
        if ctx.move.category == "変化":
            self.events.emit(Event.ON_STATUS_HIT, ctx)
            return

        self.critical = self._check_critical(ctx)
        damage = self.battle.roll_damage(
            ctx.attacker, ctx.defender, ctx.move, critical=self.critical
        )

        damage = self.events.emit(Event.ON_MODIFY_MOVE_DAMAGE, ctx, damage)

        hp_delta = self.battle.modify_hp(ctx.defender, -damage, source=ctx.attacker,
                                         move=ctx.move, reason="move_damage")
        if hp_delta < 0:
            ctx.defender.hits_taken += 1

        self.events.emit(Event.ON_HIT, ctx)

        # ダメージを与えた後の処理
        if hp_delta < 0:
            self.events.emit(Event.ON_MOVE_DAMAGE, ctx, abs(hp_delta))

            # ステラ補正の消費記録: ダメージを与えた技タイプを記録する
            if ctx.attacker.active_tera_type == 'ステラ':
                ctx.attacker.stellar_boosted_types.add(ctx.move.type)

    def is_contact(self, ctx: BattleContext) -> bool:
        """技が接触技かどうかを判定する。
        Args:
            ctx: BattleContextインスタンス

         Returns:
            技が接触技の場合True
        """
        return self.events.emit(
            Event.ON_CHECK_CONTACT,
            ctx,
            ctx.move.has_label("contact")
        )

    def resolve_move_type(self, attacker: Pokemon, move: Move) -> str:
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

    def resolve_move_category(self, attacker: Pokemon, move: Move) -> str:
        """技の有効なカテゴリを判定する。

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

    def deals_physical_damage(self, attacker: Pokemon, move: Move) -> bool:
        """技が物理ダメージを与えるかどうかを判定する。一部の特殊技も該当する。

        Returns:
            技が物理ダメージを与える場合True
        """
        return (
            move.has_label("physical_damage")
            or self.resolve_move_category(attacker, move) == "物理"
        )

    def _consume_pp(self, ctx: BattleContext):
        """技のPPを消費する。

        技を使用した際にPPを減らします。

        Args:
            ctx: BattleContextインスタンス
        """
        v = self.events.emit(Event.ON_MODIFY_PP_CONSUMED, ctx, 1)
        ctx.move.pp = max(0, ctx.move.pp - v)
        self.battle.add_event_log(ctx.attacker, LogCode.PP_CONSUMED,
                                  payload={"move": ctx.move.name, "value": v})
