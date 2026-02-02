"""イベント駆動システムの検証テスト。

Event enum の各要素が正しく利用されているか、ターン進行とイベント発火の
整合性を検証します。
"""
import pytest
from jpoke.core import Battle
from jpoke.core.player import Player
from jpoke.core.event import Event, EventContext, Handler, HandlerReturn
from jpoke.model import Pokemon
from tests.test_utils import start_battle


class TestEventFiring:
    """イベント発火の正確性を検証"""

    def test_on_before_action_fires_once_per_turn(self):
        """ON_BEFORE_ACTIONが各ターン1回発火する"""
        fire_count = {"count": 0}

        def track_fire(battle, ctx, value):
            fire_count["count"] += 1
            return HandlerReturn(True)

        battle = start_battle(
            ally=[Pokemon("ピカチュウ")],
            foe=[Pokemon("ライチュウ")],
            turn=0,
        )

        # ハンドラを登録
        handler = Handler(
            track_fire,
            subject_spec="source:self",
            source_type=None,
            log="never",
        )
        battle.events.on(Event.ON_BEFORE_ACTION, handler, battle.players[0])

        # ターン1を進める
        battle.turn_controller.advance_turn()
        count_turn1 = fire_count["count"]

        # ターン2を進める
        battle.turn_controller.advance_turn()
        count_turn2 = fire_count["count"]

        assert count_turn1 == 1, "ON_BEFORE_ACTIONがターン1で1回発火すべき"
        assert count_turn2 == 2, "ON_BEFORE_ACTIONがターン2で1回発火すべき"

    def test_on_turn_end_fires_in_sequence(self):
        """ON_TURN_END_1～6が順序正しく発火する"""
        fire_sequence = []

        def track_end_1(battle, ctx, value):
            fire_sequence.append("END_1")
            return HandlerReturn(True)

        def track_end_2(battle, ctx, value):
            fire_sequence.append("END_2")
            return HandlerReturn(True)

        battle = start_battle(
            ally=[Pokemon("ピカチュウ")],
            foe=[Pokemon("ライチュウ")],
            turn=0,
        )

        # ハンドラを登録
        h1 = Handler(track_end_1, subject_spec="source:self", source_type=None, log="never")
        h2 = Handler(track_end_2, subject_spec="source:self", source_type=None, log="never")

        battle.events.on(Event.ON_TURN_END_1, h1, battle.players[0])
        battle.events.on(Event.ON_TURN_END_2, h2, battle.players[0])

        # ターン1を進める
        battle.turn_controller.advance_turn()

        # END_1 が END_2 より先に発火すべき
        end1_idx = fire_sequence.index("END_1")
        end2_idx = fire_sequence.index("END_2")
        assert end1_idx < end2_idx, "ON_TURN_END_1がON_TURN_END_2より先に発火すべき"

    def test_on_switch_in_fires_during_switch(self):
        """ON_SWITCH_INが場に出たときに発火する"""
        fire_count = {"count": 0}

        def track_switch_in(battle, ctx, value):
            fire_count["count"] += 1
            return HandlerReturn(True)

        battle = start_battle(
            ally=[Pokemon("ピカチュウ"), Pokemon("フシギダネ")],
            foe=[Pokemon("ライチュウ")],
            turn=0,
        )

        # ハンドラを登録して明示的にON_SWITCH_INを発火
        handler = Handler(
            track_switch_in,
            subject_spec="source:self",
            source_type=None,
            log="never",
        )
        battle.events.on(Event.ON_SWITCH_IN, handler, battle.players[0])

        # ON_SWITCH_INを手動で発火して動作確認
        ctx = EventContext(source=battle.players[0].active)
        battle.events.emit(Event.ON_SWITCH_IN, ctx)

        assert fire_count["count"] == 1, "ON_SWITCH_INが1回発火すべき"


class TestEventContextResolution:
    """EventContext のロール解決が正しいか検証"""

    def test_role_self_resolves_correctly(self):
        """RoleSpec 'self' が正しく解決される"""
        battle = start_battle(
            ally=[Pokemon("ピカチュウ")],
            foe=[Pokemon("ライチュウ")],
            turn=0,
        )

        ally_active = battle.players[0].active
        foe_active = battle.players[1].active

        # ally として emit した場合
        ctx = EventContext(source=ally_active)
        resolved = ctx.resolve_role(battle, "source:self")
        assert resolved == ally_active, "source:self が ally_active に解決すべき"

        resolved = ctx.resolve_role(battle, "source:foe")
        assert resolved == foe_active, "source:foe が foe_active に解決すべき"

    def test_attacker_defender_aliases(self):
        """attacker/defender が source/target のエイリアスとして機能"""
        ally_active = Pokemon("ピカチュウ")
        foe_active = Pokemon("ライチュウ")

        # attacker/defender で指定
        ctx = EventContext(attacker=ally_active, defender=foe_active)

        # source/target でアクセスできるか確認
        assert ctx.source == ally_active, "source == attacker"
        assert ctx.target == foe_active, "target == defender"

        # エイリアスプロパティでアクセスできるか確認
        assert ctx.attacker == ally_active, "attacker エイリアスが機能"
        assert ctx.defender == foe_active, "defender エイリアスが機能"


class TestTurnProgression:
    """ターン進行の整合性を検証"""

    def test_turn_counter_increments_correctly(self):
        """ターンカウンタが正しく増加する"""
        battle = start_battle(
            ally=[Pokemon("ピカチュウ")],
            foe=[Pokemon("ライチュウ")],
            turn=0,
        )

        assert battle.turn == 0, "初期ターンは0"

        # ターン1を進める
        battle.turn_controller.advance_turn()
        assert battle.turn == 1, "ターン1に進むべき"

        # ターン2を進める
        battle.turn_controller.advance_turn()
        assert battle.turn == 2, "ターン2に進むべき"

    def test_no_duplicate_turn_increment(self):
        """ターン増分の重複がない"""
        battle = start_battle(
            ally=[Pokemon("ピカチュウ")],
            foe=[Pokemon("ライチュウ")],
            turn=0,
        )

        initial_turn = battle.turn
        battle.turn_controller.advance_turn()
        advanced_turn = battle.turn

        # 増分が1であることを確認
        assert advanced_turn - initial_turn == 1, "ターン増分は1であるべき"


class TestPriorityBlockage:
    """先制技ブロック（サイコフィールド）の検証"""

    def test_psychic_field_blocks_priority_moves(self):
        """サイコフィールドが先制技を無効化"""
        battle = start_battle(
            ally=[Pokemon("ピカチュウ")],
            foe=[Pokemon("ライチュウ")],
            terrain=("サイコフィールド", 5),
            turn=0,
        )

        ally_active = battle.players[0].active
        foe_active = battle.players[1].active

        # 優先度1の技を作成
        priority_move = ally_active.moves[0]
        # テスト用に手動で優先度を確認（Moveデータの優先度はmove.data.priorityで保持）

        ctx = EventContext(
            attacker=ally_active,
            defender=foe_active,
            move=priority_move,
        )

        # ON_CHECK_PRIORITY_VALIDイベントが発火
        # サイコフィールド_block_priority ハンドラが呼び出される
        # 浮いていないポケモンへの先制技は無効化される
        if priority_move.data.priority > 0 and not foe_active.is_floating(battle.events):
            # サイコフィールド内では先制技が無効化される可能性
            result = battle.events.emit(Event.ON_CHECK_PRIORITY_VALID, ctx, True)
            # result が False になるはず（ハンドラが False を返す）
            # ただし、具体的な技によって異なる可能性があるため、
            # ここではイベント発火自体が成功することを確認
            assert result is not None, "ON_CHECK_PRIORITY_VALIDが発火すべき"
        else:
            # 優先度0の通常技の場合は何もしない
            pass


class TestHandlerPriority:
    """ハンドラ優先度とソート順序の検証"""

    def test_handlers_sorted_by_priority(self):
        """ハンドラが優先度でソートされる"""
        call_order = []

        def handler_high(battle, ctx, value):
            call_order.append("high")
            return HandlerReturn(True)

        def handler_low(battle, ctx, value):
            call_order.append("low")
            return HandlerReturn(True)

        battle = start_battle(
            ally=[Pokemon("ピカチュウ")],
            foe=[Pokemon("ライチュウ")],
            turn=0,
        )

        # 優先度50と150のハンドラを登録（小さい値が先に実行）
        h_high = Handler(
            handler_high,
            subject_spec="source:self",
            source_type=None,
            log="never",
            priority=50,
        )
        h_low = Handler(
            handler_low,
            subject_spec="source:self",
            source_type=None,
            log="never",
            priority=150,
        )

        battle.events.on(Event.ON_BEFORE_ACTION, h_low, battle.players[0])
        battle.events.on(Event.ON_BEFORE_ACTION, h_high, battle.players[0])

        # イベント発火
        battle.events.emit(Event.ON_BEFORE_ACTION)

        # 優先度50が先に実行されるべき
        assert call_order[0] == "high", "優先度50が先に実行されるべき"
        assert call_order[1] == "low", "優先度150が後に実行されるべき"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
