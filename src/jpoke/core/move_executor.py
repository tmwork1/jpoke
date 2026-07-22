"""技実行を管理するモジュール。

技の発動、命中判定、ダメージ適用などの処理を担当。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, cast
if TYPE_CHECKING:
    from jpoke.core import Battle, EventManager

from jpoke.types import Type, MoveCategory, MoveName
from jpoke.utils.math import clamp_stats, clamp_critic
from jpoke.model.pokemon import Pokemon
from jpoke.model.move import Move
from jpoke.enums import LogCode

from .event_manager import Event
from .context import AttackContext
from .log_payload import FailureLogPayload, MoveActionPayload
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

        # デバッグ用（action_success/move_success/move_applied/move_missedは
        # やけっぱち・じだんだの成否判定にも使用する）
        self.accuracy: int | None = None
        self.action_success: bool | None = None
        self.move_success: bool | None = None
        self.move_applied: bool | None = None
        self.move_missed: bool = False
        self.move_type: Type | None = None
        self.move_category: MoveCategory | None = None
        self.move_power: int | None = None
        self.critical_rank: int | None = None
        self.critical: bool | None = None

        # run_moveのネスト呼び出し深度（ねごと・さいはい等のサブ技実行を検出するため）。
        # 深度が1（トップレベル実行）のときのみ selected_move を更新する。
        self._run_move_depth: int = 0

    def reset_monitoring_flags(self):
        """技実行のモニタリング用フラグをリセットする。"""
        self.accuracy = None
        self.action_success = None
        self.move_success = None
        self.move_applied = None
        self.move_missed = False
        self.move_type = None
        self.move_category = None
        self.move_power = None
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

    @property
    def is_nested_move_execution(self) -> bool:
        """まねっこ・ねごと・ゆびをふる・さいはい等のサブ技実行として
        ネストされたrun_move呼び出しの内側かどうかを判定する。

        トップレベルのrun_move呼び出しがEvent.ON_MODIFY_MOVEを発火する時点
        （_run_move_depthの加算前）では、この判定は「外側に既に進行中の
        run_move呼び出しが存在するか」を表す。値がTrueの場合、この
        run_move呼び出しは他の技の効果によって内部的に起動されたサブ技実行
        であることを意味する（アンコール等、使用者自身の技選択を強制的に
        固定する効果を、サブ技実行には適用しないよう判定するために使う。
        適用してしまうと、まねっこ等がコピーした技が固定技と異なる場合に
        強制的に固定技へ差し戻され、battle.run_moveが際限なく再帰する）。
        """
        return self._run_move_depth > 0

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
            return move.base_power

        power_sequence = move.data.multi_hit.get("power_sequence", ())
        if power_sequence:
            idx = min(hit_index - 1, len(power_sequence) - 1)
            return power_sequence[idx]
        return move.base_power

    def _check_hit(self, ctx: AttackContext) -> bool:
        """技の命中判定。

        Args:
            ctx: バトルコンテキスト

        Returns:
            命中した場合True
        """
        # テストオプションによる命中率の上書き
        if self.battle.test_option.accuracy is not None:
            self.accuracy = self.battle.test_option.accuracy
            return 100 * self.battle.random.random() < self.accuracy

        assert ctx.defender is not None
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
            "accuracy": attacker.boosts["accuracy"],
            "evasion": defender.boosts["evasion"]
        }
        modified_rank = self._events.emit(Event.ON_GET_STAT_RANK, ctx, ranks)
        rank_modifier = hit_rank_modifier(modified_rank["accuracy"], modified_rank["evasion"])
        accuracy = int(accuracy * rank_modifier)

        self.accuracy = accuracy  # デバッグ用に保存

        threshold = self.battle.option.accuracy_fix_threshold
        if threshold is not None and accuracy >= threshold:
            return True

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
        if self.battle.option.critical_mode == "always":
            critical_rank = clamp_critic(ctx.move.crit_ratio)
            self.critical_rank = critical_rank  # デバッグ用に保存
            return self.battle.random.random() < CRIT_RATES[critical_rank]

        # 急所ランクの計算
        critical_rank = self._events.emit(
            Event.ON_CALC_CRITICAL_RANK,
            ctx,
            ctx.move.crit_ratio
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
        if ctx.move.has_flag("bypass_substitute"):
            return False
        # 音技はみがわりを貫通する（第六世代以降の仕様）。
        # 特定の技ではなく sound フラグから導出される汎用ルールのため、
        # 個別技へのハンドラ登録ではなく意図的にコア側で判定する。
        if ctx.move.has_flag("sound"):
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
        ctx = AttackContext(attacker=attacker, defender=defender, move=move)

        # 技の変更 (アンコールなど)
        move = self._events.emit(Event.ON_MODIFY_MOVE, ctx, move)
        if move is None:
            return

        # PPが0の技はわるあがきに置き換える
        # （ねごとのサブ実行中は対象外。ねごとはPP0の技も選択でき、そのまま成功する）
        if move.pp == 0 and not attacker.sleep_talk_active:
            move = Move("わるあがき")

        ctx.move = move

        # 技のハンドラを登録
        ctx.move.register_handlers(self._events, ctx.attacker)

        # run_moveのネスト呼び出し深度を記録する（ねごと・さいはい等のサブ技実行検出用）
        self._run_move_depth += 1
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

                # 選択した技の確定: トップレベル実行（深度1）のときのみ更新する。
                # ねごと・さいはい等によるサブ技実行（深度2以上）では選択技は変化しない
                # （いちゃもん等「選択した技」を参照すべき効果のため）。PP消費と同時点
                # （タイプ相性判定・ON_TRY_MOVE_2・くさタイプ粉技無効判定等より前）で
                # 確定させることで、それらの判定により技自体が不発になった場合でも
                # 「選択した技」として正しく記録される（PPは既に消費済みのため。
                # .internal/spec/volatiles/いちゃもん.md 参照）。
                if self._run_move_depth == 1:
                    ctx.attacker.selected_move = ctx.move

                # かたやぶりを適用する
                self._events.emit(Event.ON_BEGIN_MOVE, ctx)

                # 技の実行
                self._execute_move(ctx)

        finally:
            self._run_move_depth -= 1

            # 技の状態をリセットする（タイプや威力の変更を元に戻す）
            ctx.move.reset()

            # 今回の行動が総合的に成功したかを記録する（やけっぱち・じだんだ用）
            # マジックコート等でctx.attackerが入れ替わる場合があるため、
            # 実際に行動したポケモン（引数のattacker）に対して記録する
            overall_success = (
                self.action_success is not False
                and self.move_success is not False
                and self.move_applied is not False
                and not self.move_missed
            )
            attacker.failed_or_immobile_last_turn = not overall_success

            # 場に出てから一度でも行動したことを記録する（であいがしら用）
            # であいがしら自身の成否判定（ON_TRY_MOVE_1）はこの行動の途中で行われるため、
            # 今回の行動を「行動済み」として反映するのはここ（行動完了後）でよい。
            attacker.acted_since_switch_in = True

            # ユーザーがbattle.step()実行後に技の成否を確認できるようプレイヤー状態へ記録する
            player = self.battle.get_player(attacker)
            self.battle.player_states[player].last_move_succeeded = overall_success

            # かたやぶりを解除する
            self._events.emit(Event.ON_END_MOVE, ctx)

            # 技のハンドラを解除
            # マジックコート・マジックミラー等でctx.attackerが入れ替わる場合があるため、
            # register_handlers時と同じ主体（引数のattacker）を指定して解除する
            # （324行目付近の同種コメント参照）。ctx.attackerのまま解除すると
            # 登録時と異なる主体でoff()を呼ぶことになり、登録済みハンドラが
            # 削除されずに残り続けて後続ターンで誤発動する不具合が生じる。
            ctx.move.unregister_handlers(self._events, attacker)

    def _check_hit_by_type(self, ctx: AttackContext) -> bool:
        """タイプ相性によって技が有効かを判定する。"""
        type_modifier = self.battle.damage_calculator.calc_def_type_modifier(ctx)

        if type_modifier == 0:
            self.battle.add_event_log(
                ctx.attacker,
                LogCode.MOVE_IMMUNED,
                payload=FailureLogPayload(move=ctx.move.name, display_reason="タイプ無効")
            )
            return False
        return True

    def _check_grass_type_powder_immunity(self, ctx: AttackContext) -> bool:
        """くさタイプへの粉技無効化チェック (ON_TRY_MOVE_2, priority=120)。

        くさタイプの防御側に powder ラベルを持つ技を使うと無効化される。
        特定の技ではなく powder フラグから導出される汎用ルールのため、
        個別技へのハンドラ登録ではなく意図的にコア側で判定する。
        特性そうしょくを持つ場合は、くさタイプによる無効化よりそうしょくの
        効果（Event.ON_BEFORE_APPLY_MOVE）が優先されるため、ここでは無効化しない。
        """
        assert ctx.defender is not None
        if (
            ctx.move.has_flag("powder")
            and ctx.defender.has_type("くさ")
            and ctx.defender.ability.name != "そうしょく"
        ):
            self.battle.add_event_log(
                ctx.attacker,
                LogCode.MOVE_IMMUNED,
                payload=FailureLogPayload(move=ctx.move.name, display_reason="くさタイプ粉技無効")
            )
            return False
        return True

    def _check_target_fainted(self, ctx: AttackContext) -> bool:
        """対象がすでに瀕死かどうかをチェックする (ON_TRY_MOVE_1, priority=90相当のコアルール)。

        シングルバトル専用のため、相手単体を対象とする技（ctx.move.target == "foe"）
        でのみ判定する。自分自身・味方・場全体を対象とする技には適用しない。

        瀕死交代はターン終了時（turn_controller._run_end_phase 内の
        switch_manager.run_faint_switch()）にしか行われないため、同一ターン内で
        自分より先に行動した側の攻撃や、相手自身のHPコスト（いのちのたまの反動等）に
        よって相手が既に瀕死になっている場合、瀕死交代前の場に残ったままの瀕死ポケモンが
        対象になり得る。この場合、技は不発として扱う（おきみやげ・かかとおとし等の仕様書
        「対象がすでに全員ひんしで技自体が不発になった場合」を参照）。
        """
        assert ctx.defender is not None
        if ctx.move.target == "foe" and ctx.defender.fainted:
            self.battle.add_event_log(
                ctx.attacker,
                LogCode.MOVE_FAILED,
                payload=FailureLogPayload(move=ctx.move.name, display_reason="相手がいない")
            )
            return False
        return True

    def _execute_move(self, ctx: AttackContext) -> None:
        """技実行の内部フローを処理する。

        行動可否チェックから PP 消費、命中判定、連続ヒット処理までを担当する。

        Args:
            ctx: 技実行中のバトルコンテキスト
        """
        assert ctx.defender is not None
        # 溜め技の準備
        if not self._events.emit(Event.ON_MOVE_CHARGE, ctx, True):
            return

        # 発動成功判定(1)
        self.move_success = self._events.emit(Event.ON_TRY_MOVE_1, ctx, True)
        if not self.move_success:
            # ここに到達する時点でPPは既に消費済み（_consume_ppはrun_move側で
            # ON_MOVE_CHARGEより前に無条件で呼ばれる）。実機ではPP消費後の
            # 不発でもこだわり系アイテム等のロックはかかるため、ON_MOVE_ENDを
            # 発火してこだわり_lock_move等の後処理を確実に実行させる。
            if ctx.blocked_by_protect:
                # まもる・ワイドガード等のprotect系による不発は、しめりけによる
                # 不発とは異なり使用者が必ずひんしになる
                # （.internal/spec/moves/だいばくはつ.md「まもる: 防がれる
                # （防がれてもひんしになる）」）。protect系のブロック判定は
                # しめりけ（HPコスト支払い前に失敗すべき）と同じEvent.ON_TRY_MOVE_1
                # で発火するため、通常はON_PAY_HPより前に不発が確定してしまう。
                # ここでctx.blocked_by_protectを見て、protectブロック時のみ
                # ON_PAY_HPを発火させHPコスト支払いを保証する
                # （じばく・だいばくはつ・ミストバースト対応。しめりけの場合は
                # blocked_by_protectがFalseのままなので従来どおりHP消費は発生しない）。
                self.battle.begin_deferred_winner_log()
                try:
                    self._events.emit(Event.ON_PAY_HP, ctx)
                    self._events.emit(Event.ON_MOVE_END, ctx)
                finally:
                    self.battle.end_deferred_winner_log()
                return
            if ctx.missed_hidden_target:
                # そらをとぶ・あなをほる等で姿を隠している相手に対応していない技で
                # 外れた場合も、通常の命中率判定による「外れ」と同様に扱う
                # （.internal/spec/moves/とびひざげり.md）。LogCode.MOVE_MISSEDは
                # can_hit_hidden_target側で既に記録済みのためここでは記録せず、
                # move_missedフラグの設定とEvent.ON_MISSの発火のみ行う。
                self.move_missed = True
                self._events.emit(Event.ON_MISS, ctx)
                self._events.emit(Event.ON_MOVE_END, ctx)
                return
            self._events.emit(Event.ON_MOVE_END, ctx)
            return

        # HPコストの支払い (Event.ON_PAY_HP)
        # じばく・だいばくはつ・てっていこうせん・ミストバースト等はここでHPを消費する。
        # .internal/spec/moves/じばく.md「命中判定・タイプ相性・まもるなどにより攻撃が不発になった
        # 場合であっても、使用者は必ずひんしになる」「しめりけによる失敗判定はON_PAY_HPより前に
        # 行われるため、失敗時は現在HPの消費も発生しない」を満たすため、ON_TRY_MOVE_1
        # （しめりけ等の失敗経路）の直後・対象瀕死チェック/タイプ相性判定/ON_TRY_MOVE_2/
        # くさ粉技無効判定より前に発火する。これらのチェックによる不発は「攻撃が不発になった
        # 場合」に含まれるため、HPコスト支払い後も通常どおり判定を続行する。
        #
        # てっていこうせん等、HPコストの支払いにより使用者が瀕死になった場合でも
        # 以降の判定・ヒット処理（命中判定・ダメージ適用・ON_MOVE_KO等の撃破時効果）は
        # 通常どおり進行する（.internal/spec/moves/てっていこうせん.md「HP消費の順序」
        # 「HP0でのひんし・全滅判定」を参照）。
        # そのため、HPコスト支払いの時点で使用者が瀕死になり勝敗が確定しても、
        # 以降の処理が完了するまではGAME_WON/GAME_LOSTログの記録を遅延させる。
        # そうしないと、相手へのダメージ適用や撃破時特性の発動より前に
        # 勝敗確定ログが記録されてしまい、ログ上「勝敗が決した後に戦闘が続いた」
        # ような不整合が生じる（勝者判定自体はmodify_hp内で即座に行われ、
        # ここで遅延するのはログ記録タイミングのみ）。
        self.battle.begin_deferred_winner_log()
        try:
            self._events.emit(Event.ON_PAY_HP, ctx)

            # 対象がすでに瀕死: 技失敗 (ON_TRY_MOVE_1, priority=90相当のコアルール)
            if not self._check_target_fainted(ctx):
                self.move_success = False
                self._events.emit(Event.ON_MOVE_END, ctx)
                return

            # 攻撃技のタイプ相性判定
            if ctx.move.is_attack and not self._check_hit_by_type(ctx):
                # タイプ相性による無効化も「技が失敗した」ことになる（やけっぱち・じだんだ用）
                self.move_success = False
                self._events.emit(Event.ON_MOVE_END, ctx)
                return

            # 発動成功判定(2): priority=110 のハンドラ群（ぼうじんゴーグル等）
            self.move_success = self._events.emit(Event.ON_TRY_MOVE_2, ctx, True)
            if not self.move_success:
                self._events.emit(Event.ON_MOVE_END, ctx)
                return

            # くさタイプ: 粉技無効 (priority=120 相当のコアルール)
            if not self._check_grass_type_powder_immunity(ctx):
                self.move_success = False
                self._events.emit(Event.ON_MOVE_END, ctx)
                return

            # 発動した技の確定
            ctx.attacker.last_move = ctx.move
            # selected_move はPP消費時点（本メソッド前段）で確定済みのためここでは更新しない。
            # non_negotoでない技のみバトル全体の最後使用技として記録する
            if not ctx.move.has_flag("non_negoto"):
                self.battle.last_used_move_name = cast(MoveName, ctx.move.name)

            # 反射判定
            if self._events.emit(Event.ON_CHECK_REFLECT, ctx, False):
                self.battle.add_event_log(
                    ctx.defender, LogCode.MOVE_REFLECTED,
                    payload=MoveActionPayload(move=ctx.move.name)
                )
                ctx.attacker, ctx.defender = ctx.defender, ctx.attacker

            # 連続技のヒット回数を決定
            hit_count = self._resolve_hit_count(ctx)
            ctx.hit_count = hit_count

            # 開始時点で既にねむり状態か（ねごとで眠ったまま行動する場合等）を記録しておく。
            # ほうし等でヒット中に新たにねむり状態になった場合のみ中断対象とするため。
            was_asleep_before_hits = ctx.attacker.has_ailment("ねむり")

            # ヒットごとに命中判定を行うかどうか（いかさまダイス等で上書き可能）
            check_hit_each_time = self._events.emit(
                Event.ON_MODIFY_HIT_CHECK_EACH_TIME,
                ctx,
                ctx.move.has_flag("check_hit_each_time"),
            )

            # 命中判定が必要な技の場合、ヒットごとに命中判定を行うかどうかを決定
            for hit_index in range(1, hit_count + 1):
                ctx.hit_index = hit_index

                # ヒットごとの技の威力を設定
                ctx.move.base_power = self._resolve_hit_power(ctx.move, hit_index)
                self.move_power = ctx.move.base_power

                # 命中判定: 通常技は初回ヒットのみ、ヒットごと判定技は毎ヒットで判定
                need_hit_check = (
                    ctx.move.accuracy is not None
                    and (hit_index == 1 or check_hit_each_time)
                )

                if need_hit_check and not self._check_hit(ctx):
                    self.move_missed = True
                    self.battle.add_event_log(
                        ctx.attacker, LogCode.MOVE_MISSED,
                        payload=FailureLogPayload(move=ctx.move.name)
                    )
                    self._events.emit(Event.ON_MISS, ctx)
                    break

                # 無効化されたら中断
                self.move_applied = self._events.emit(Event.ON_BEFORE_APPLY_MOVE, ctx, True)
                if not self.move_applied:
                    # TODO: ON_BEFORE_APPLY_MOVE失敗経路（みがわりでの変化技ブロック等）でも
                    # ON_MOVE_ENDが発火しないため、こだわり系アイテム/ごりむちゅうのロックが
                    # かからない（例: みがわり状態の相手にどくどくを使うとPPは消費されるが
                    # こだわりロックはかからない）。ON_TRY_MOVE_1/2・タイプ相性・くさ粉技無効化の
                    # 4経路については move_executor.py の対応する分岐で ON_MOVE_END を発火する
                    # 修正済みだが、このヒットループ内の分岐は影響範囲調査（のどスプレー等
                    # move_applied を見ずに move_success のみで判定しているON_MOVE_ENDハンドラの
                    # 洗い出しを含む）が必要なため意図的に未対応としている。
                    return

                # 技が当たったときの処理を実行
                self._execute_hit(ctx)

                # ひんしになったら中断
                if ctx.defender.fainted or ctx.attacker.fainted:
                    break

                # 連続攻撃技の途中で新たにねむり状態になった場合（ほうし等）は直ちに中断。
                # 開始時点で既にねむり状態だった場合（ねごとで眠ったまま行動する場合）は対象外。
                if not was_asleep_before_hits and ctx.attacker.has_ailment("ねむり"):
                    break

            # 技実行完了後の処理（状態管理・撤去など）
            self._events.emit(Event.ON_MOVE_END, ctx)
        finally:
            self.battle.end_deferred_winner_log()

    def _execute_hit(self, ctx: AttackContext) -> None:
        """1 ヒット分の処理を実行する。

        Args:
            ctx: 技実行中のバトルコンテキスト
        """
        assert ctx.defender is not None
        # 変化技の処理はダメージ処理とは別に行う
        if ctx.move.category == "status":
            self._execute_status_hit(ctx)
            return

        # 固定ダメージ技（いのちがけ・ちきゅうなげ等）は攻撃・防御・威力・急所・
        # 乱数補正を一切使用しない（.internal/spec/moves/_fixed_damage.md 7.1・7.3）。
        # 実際のダメージ値はEvent.ON_MODIFY_MOVE_DAMAGEで後から上書きされるため
        # ここでの急所判定自体は数値に影響しないが、判定・ログを行うと「急所に
        # 当たった」という誤ったログが記録され、いかりのつぼ等の急所被弾を
        # トリガーにする効果にも誤って波及しうる（fuzzログ seed=1914で発見）。
        if ctx.move.has_flag("fixed_damage"):
            self.critical = False
        else:
            self.critical = self._check_critical(ctx)
            if self.critical:
                self.battle.add_event_log(
                    ctx.attacker, LogCode.CRITICAL_HIT,
                    payload=MoveActionPayload(move=ctx.move.name)
                )
        damage = self.battle.roll_damage(
            ctx.attacker, ctx.defender, ctx.move, critical=self.critical
        )

        damage = self._events.emit(Event.ON_MODIFY_MOVE_DAMAGE, ctx, damage)

        # GAME_WON/GAME_LOSTログの記録は、この技ヒットに付随する後続イベント
        # （ON_HIT・ON_DAMAGE_HIT・ON_MOVE_KO、およびそれらに付随して発生する
        # さめはだ等の反撃ダメージ・自己ランク低下・状態異常付与等）が
        # すべて完了した後に行いたい（＝この1ヒットの処理全体を1つの区間として
        # 扱う）。ここで即座に記録すると、Vジェネレート等の自己ランク低下や
        # 撃破時特性（しろのいななき等）・さめはだ等の反撃ダメージのログが
        # 勝敗確定ログより後に記録されてしまうため。なお勝者判定自体
        # （battle.winner の確定）は modify_hp 内で即座に行われる。
        self.battle.begin_deferred_winner_log()
        try:
            actual_damage = -self.battle.modify_hp(
                ctx.defender, -damage, source=ctx.attacker, reason="move_damage",
            )

            self._events.emit(Event.ON_HIT, ctx, actual_damage)

            # ダメージを与えた後の処理（actual_damage は正値=ダメージ量）
            if actual_damage <= 0:
                # ばけのかわ等、フォルムチェンジの消費ダメージで既にひんしになっている場合がある。
                # この場合も、相手を倒したことをトリガーとする効果（じしんかじょう等の特性）は発動する。
                if ctx.defender.fainted:
                    self._events.emit(Event.ON_MOVE_KO, ctx, actual_damage)
                return

            ctx.defender.hits_taken += 1
            # カウンター・ミラーコートは「最後に受けた1回分」のダメージを参照するため、
            # 連続技で複数回ヒットした場合も合算せず直近のヒット量で上書きする。
            # 技のカテゴリは run_move 実行時に既に確定済み（ctx.move.category）のため、
            # ここで再度 resolve_move_category（battle.foe(attacker) を参照）を呼ばない。
            # ON_HIT イベント（レッドカード等）で attacker が既に交代済みの場合、
            # battle.foe(attacker) が例外を送出するため。
            category = "physical" if (ctx.move.category == "physical" or ctx.move.has_flag("physical_damage")) else "special"
            ctx.defender.last_damage_taken = {"damage": actual_damage, "category": category}

            self._events.emit(Event.ON_DAMAGE_HIT, ctx, actual_damage)

            if ctx.defender.fainted:
                self._events.emit(Event.ON_MOVE_KO, ctx, actual_damage)

            # ステラ補正の消費記録: ダメージを与えた技タイプを記録する
            if ctx.attacker.active_tera_type == 'ステラ':
                ctx.attacker.stellar_boosted_types.add(ctx.move.type)
        finally:
            self.battle.end_deferred_winner_log()

    def _execute_status_hit(self, ctx: AttackContext) -> None:
        """状態変化技の命中処理を実行する。

        Args:
            ctx: 技実行中のバトルコンテキスト
        """
        # 状態変化技の命中処理は、通常のダメージ処理とは別にON_STATUS_HITイベントで行う。
        # これにより、ダメージを与えない状態変化技（でんじはなど）も同様のフローで処理できる。
        logs = self.battle.event_logger.logs
        log_count_before = len(logs)
        result = self._events.emit(Event.ON_STATUS_HIT, ctx, True)
        if not result:
            self.move_success = False
            # ひっくりかえす・ねむる・ねごと・いやしのねがい等、ON_STATUS_HITに
            # 登録されたハンドラ自身が理由付きのMOVE_FAILEDログを記録して失敗する
            # ケースがある。その場合は汎用フォールバックログを重ねて出さないよう、
            # このemit呼び出し中に新たにMOVE_FAILEDログが追加されたかどうかで判定する。
            already_logged = (
                len(logs) > log_count_before
                and logs[-1].log == LogCode.MOVE_FAILED
            )
            if not already_logged:
                self.battle.add_event_log(
                    ctx.attacker,
                    LogCode.MOVE_FAILED,
                    payload=FailureLogPayload(move=ctx.move.name)
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
            AttackContext(attacker=attacker, defender=self.battle.foe(attacker), move=move),
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
            AttackContext(attacker=attacker, defender=self.battle.foe(attacker), move=move),
            value=move.category
        )

    def _consume_pp(self, ctx: AttackContext):
        """技を開示してPPを消費する。

        技を使用した際にPPを減らします。

        Args:
            ctx: EventContextインスタンス
        """
        move = ctx.move
        move.revealed = True
        # あばれる・さわぐ等、Command.FORCEDによる強制続行ターンは使い捨てMove
        # インスタンス（実際の技スロットのPPには影響しない）で実行されるため、
        # PPは消費しない（.internal/spec/moves/さわぐ.md「PP消費は最初の使用時の1回のみ」。
        # fuzzログ seed=1823で、続行ターンでも「PP -1」が表示され続ける
        # ログ不整合を発見。実データ（技スロットのPP）自体は元々影響を受けていない）。
        if move.is_forced_continuation:
            v = 0
        else:
            v = self._events.emit(Event.ON_MODIFY_PP_CONSUMED, ctx, 1)
        move.pp = max(0, move.pp - v)
        if v > 0:
            # 実際にPPを消費した技として記録する（とっておき用）
            ctx.attacker.pp_consumed_moves.add(cast(MoveName, move.name))
            # 最後にPPを消費した技として記録する（かなしばり・うらみ・さいはい等の参照先）。
            # ねごとのサブ技は ねごと_suppress_pp により v=0 となるためここには記録されない。
            ctx.attacker.pp_consumed_move = move
        self.battle.add_event_log(
            ctx.attacker,
            LogCode.PP_CONSUMED,
            payload=MoveActionPayload(move=move.name, value=v)
        )
        # PP消費後のフック（ヒメリのみ: PPが0になったとき回復する）
        self._events.emit(Event.ON_PP_CONSUMED, ctx, move.pp)
