"""揮発状態データ定義モジュール。

Note:
    このモジュール内の揮発状態定義はVOLATILES辞書内で五十音順に配置されています。
"""
from jpoke.enums import Event
from jpoke.core import HandlerReturn
from jpoke.handlers import volatile as h
from .models import VolatileData


def common_setup() -> None:
    """
    各VOLATILEのハンドラにログ用のテキスト（名前）を設定する。

    この関数は、VOLATILESディクショナリ内の全てのVolatileDataに対して、
    これにより、ハンドラ実行時のログ出力で状態名を表示できます。

    呼び出しタイミング: モジュール初期化時（ファイル末尾）
    """
    for name, data in VOLATILES.items():
        data.name = name

# TODO : lambdaで定義しているハンドラは、名前付き関数に置き換える


VOLATILES: dict[str, VolatileData] = {
    "": VolatileData(),
    "アクアリング": VolatileData(
        handlers={
            Event.ON_TURN_END: h.VolatileHandler(
                h.アクアリング_self_heal,
                subject_spec="source:self",
                priority=70,
            ),
        }
    ),
    "あなをほる": VolatileData(
        forced=True,
        handlers={
            # TODO : あなをほる状態ではそもそも交代コマンドを選択できないため交代判定は不要。ほかの隠れる系状態も同様。
            Event.ON_CHECK_TRAPPED: h.VolatileHandler(
                h.check_trapped_not_ghost,
                subject_spec="source:self",
            ),
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                h.force_command,
                subject_spec="source:self",
            ),
            Event.ON_TRY_MOVE_1: h.VolatileHandler(
                lambda b, c, v: h.can_hit_hidden_target(b, c, v, "あなをほる"),
                subject_spec="defender:self",
                priority=50,
            ),
            Event.ON_HIT: h.VolatileHandler(
                lambda b, c, v: h.remove_volatile(b, c, v, volatile="あなをほる"),
                subject_spec="attacker:self",
            ),
        }
    ),
    "あばれる": VolatileData(
        forced=True,
        handlers={
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                h.force_command,
                subject_spec="source:self",
            ),
            Event.ON_DAMAGE_HIT: h.VolatileHandler(
                h.あばれる_tick,
                subject_spec="attacker:self",
                priority=180
            ),
        }
    ),
    "あめまみれ": VolatileData(
        handlers={
            Event.ON_TURN_END: h.VolatileHandler(
                h.あめまみれ_turn_end,
                subject_spec="source:self",
            ),
        }
    ),
    "アンコール": VolatileData(
        handlers={
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                h.アンコール_restrict_commands,
                subject_spec="source:self",
            ),
            Event.ON_MODIFY_MOVE: h.VolatileHandler(
                h.アンコール_modify_move,
                subject_spec="attacker:self",
                priority=200
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.アンコール_tick_volatile,
                subject_spec="source:self",
                priority=110
            ),
        }
    ),
    "いちゃもん": VolatileData(
        handlers={
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                h.いちゃもん_modify_command_options,
                subject_spec="source:self",
            )
        }
    ),
    "うちおとす": VolatileData(
        handlers={
            Event.ON_CHECK_FLOATING: h.VolatileHandler(
                h.うちおとす_check_floating,
                subject_spec="source:self",
            ),
        }
    ),
    "おんねん": VolatileData(
        handlers={
            Event.ON_TRY_ACTION: h.VolatileHandler(
                h.おんねん_remove_volatile,
                subject_spec="attacker:self",
                priority=10
            ),
            Event.ON_MOVE_KO: h.VolatileHandler(
                h.おんねん_deplete_attacking_move_pp,
                subject_spec="defender:self",
                priority=10
            ),
        }
    ),
    "かいふくふうじ": VolatileData(
        handlers={
            Event.ON_MODIFY_HEAL: h.VolatileHandler(
                h.かいふくふうじ_block_heal,
                subject_spec="target:self",
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.かいふくふうじ_tick_volatile,
                subject_spec="source:self",
                priority=110
            ),
        }
    ),
    "かなしばり": VolatileData(
        handlers={
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                h.かなしばり_modify_command_options,
                subject_spec="source:self",
            ),
            Event.ON_TRY_ACTION: h.VolatileHandler(
                h.かなしばり_try_action,
                subject_spec="attacker:self",
                priority=100
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.かなしばり_tick_volatile,
                subject_spec="source:self",
                priority=110
            ),
        }
    ),
    "きゅうしょアップ": VolatileData(
        handlers={
            Event.ON_CALC_CRITICAL_RANK: h.VolatileHandler(
                h.きゅうしょアップ_boost_critical_rank,
                subject_spec="attacker:self",
            ),
        }
    ),
    "こだわり": VolatileData(
        handlers={
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                h.こだわり_restrict_commands,
                subject_spec="source:self",
            )
        }
    ),
    "こらえる": VolatileData(
        handlers={
            Event.ON_MODIFY_MOVE_DAMAGE: h.VolatileHandler(
                h.こらえる_endure,
                subject_spec="defender:self",
                priority=60,
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.こらえる_remove_volatile,
                subject_spec="source:self",
            ),
        }
    ),
    "こんらん": VolatileData(
        handlers={
            Event.ON_TRY_ACTION: h.VolatileHandler(
                h.こんらん_try_action,
                subject_spec="attacker:self",
                priority=110
            ),
        }
    ),
    "さわぐ": VolatileData(
        handlers={
            Event.ON_VOLATILE_START: h.VolatileHandler(
                h.さわぐ_start,
                subject_spec="source:self",
            ),
            Event.ON_VOLATILE_END: h.VolatileHandler(
                h.さわぐ_remove_さわがしい,
                subject_spec="source:self",
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.さわぐ_tick_volatile,
                subject_spec="source:self",
                priority=150
            ),
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                h.force_command,
                subject_spec="source:self",
            ),
            Event.ON_BEFORE_APPLY_AILMENT: h.VolatileHandler(
                h.さわぐ_prevent_sleep,
                subject_spec="target:self",
            ),
            Event.ON_BEFORE_APPLY_VOLATILE: h.VolatileHandler(
                h.さわぐ_prevent_nemuke,
                subject_spec="target:self",
            ),
        }
    ),
    "さわがしい": VolatileData(
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.VolatileHandler(
                h.さわぐ_prevent_sleep,
                subject_spec="target:self",
            ),
            Event.ON_BEFORE_APPLY_VOLATILE: h.VolatileHandler(
                h.さわぐ_prevent_nemuke,
                subject_spec="target:self",
            ),
        }
    ),
    "シャドーダイブ": VolatileData(
        forced=True,
        handlers={
            Event.ON_CHECK_TRAPPED: h.VolatileHandler(
                h.check_trapped_not_ghost,
                subject_spec="source:self",
            ),
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                h.force_command,
                subject_spec="source:self",
            ),
            Event.ON_TRY_MOVE_1: h.VolatileHandler(
                lambda b, c, v: h.can_hit_hidden_target(b, c, v, "シャドーダイブ"),
                subject_spec="defender:self",
                priority=50,
            ),
            Event.ON_HIT: h.VolatileHandler(
                lambda b, c, v: h.remove_volatile(b, c, v, volatile="シャドーダイブ"),
                subject_spec="attacker:self",
            ),
        }
    ),
    "しおづけ": VolatileData(
        handlers={
            Event.ON_TURN_END: h.VolatileHandler(
                h.しおづけ_damage,
                subject_spec="source:self",
                priority=100,
            ),
        }
    ),
    "じごくづき": VolatileData(
        handlers={
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                h.じごくづき_restrict_commands,
                subject_spec="source:self",
            ),
            Event.ON_TRY_ACTION: h.VolatileHandler(
                h.じごくづき_try_action,
                subject_spec="attacker:self",
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.じごくづき_tick_volatile,
                subject_spec="source:self",
                priority=110
            ),
        }
    ),
    "じゅうでん": VolatileData(
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.VolatileHandler(
                h.じゅうでん_boost_electric,
                subject_spec="attacker:self",
            ),
        }
    ),
    "そらをとぶ": VolatileData(
        forced=True,
        handlers={
            Event.ON_CHECK_TRAPPED: h.VolatileHandler(
                h.check_trapped_not_ghost,
                subject_spec="source:self",
            ),
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                h.force_command,
                subject_spec="source:self",
            ),
            Event.ON_TRY_MOVE_1: h.VolatileHandler(
                lambda b, c, v: h.can_hit_hidden_target(b, c, v, "そらをとぶ"),
                subject_spec="defender:self",
                priority=50,
            ),
            Event.ON_HIT: h.VolatileHandler(
                lambda b, c, v: h.remove_volatile(b, c, v, volatile="そらをとぶ"),
                subject_spec="attacker:self",
            ),
        }
    ),
    "たくわえる": VolatileData(
        # Volatileではカウントの管理のみ行い、実際の効果は技のハンドラ側で処理
        handlers={}
    ),
    "タールショット": VolatileData(
        handlers={
            Event.ON_CALC_DEF_TYPE_MODIFIER: h.VolatileHandler(
                h.タールショット_boost_fire,
                subject_spec="defender:self",
            ),
        }
    ),
    "ダイビング": VolatileData(
        forced=True,
        handlers={
            Event.ON_CHECK_TRAPPED: h.VolatileHandler(
                h.check_trapped_not_ghost,
                subject_spec="source:self",
            ),
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                h.force_command,
                subject_spec="source:self",
            ),
            Event.ON_TRY_MOVE_1: h.VolatileHandler(
                lambda b, c, v: h.can_hit_hidden_target(b, c, v, "ダイビング"),
                subject_spec="defender:self",
                priority=50,
            ),
            Event.ON_HIT: h.VolatileHandler(
                lambda b, c, v: h.remove_volatile(b, c, v, volatile="ダイビング"),
                subject_spec="attacker:self",
            ),
        }
    ),
    "ちいさくなる": VolatileData(
        handlers={
            Event.ON_MODIFY_ACCURACY: h.VolatileHandler(
                h.ちいさくなる_guaranteed_hit,
                subject_spec="defender:self",
            ),
            Event.ON_CALC_POWER_MODIFIER: h.VolatileHandler(
                h.ちいさくなる_boost_power,
                subject_spec="defender:self",
            ),
        }
    ),
    "ちょうはつ": VolatileData(
        handlers={
            Event.ON_TRY_ACTION: h.VolatileHandler(
                h.ちょうはつ_try_action,
                subject_spec="attacker:self",
                priority=200
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.ちょうはつ_tick_volatile,
                subject_spec="source:self",
                priority=110
            ),
        }
    ),
    "でんじふゆう": VolatileData(
        handlers={
            Event.ON_CHECK_FLOATING: h.VolatileHandler(
                lambda *args: HandlerReturn(value=True),
                subject_spec="source:self",
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.でんじふゆう_tick_volatile,
                subject_spec="source:self",
                priority=110
            ),
        }
    ),
    "とくせいなし": VolatileData(
        handlers={
            Event.ON_VOLATILE_START: h.VolatileHandler(
                h.とくせいなし_disable_ability,
                subject_spec="source:self",
            ),
            Event.ON_VOLATILE_END: h.VolatileHandler(
                h.とくせいなし_enable_ability,
                subject_spec="source:self",
            ),
        }
    ),
    "にげられない": VolatileData(
        handlers={
            Event.ON_CHECK_TRAPPED: h.VolatileHandler(
                h.check_trapped_not_ghost,
                subject_spec="source:self",
            ),
        }
    ),
    "ねむけ": VolatileData(
        handlers={
            Event.ON_TURN_END: h.VolatileHandler(
                h.ねむけ_tick_volatile,
                subject_spec="source:self",
                priority=110,
            ),
            Event.ON_VOLATILE_END: h.VolatileHandler(
                h.ねむけ_remove_and_apply_sleep,
                subject_spec="source:self",
            ),
        }
    ),
    "ねをはる": VolatileData(
        handlers={
            Event.ON_TURN_END: h.VolatileHandler(
                h.ねをはる_self_heal,
                subject_spec="source:self",
                priority=70
            ),
            Event.ON_CHECK_TRAPPED: h.VolatileHandler(
                h.check_trapped_not_ghost,
                subject_spec="source:self",
            ),
            Event.ON_CHECK_FLOATING: h.VolatileHandler(
                lambda *args: HandlerReturn(value=False, stop_event=True),
                subject_spec="source:self",
            ),
        }
    ),
    "のろい": VolatileData(
        handlers={
            Event.ON_TURN_END: h.VolatileHandler(
                h.のろい_damage,
                subject_spec="source:self",
                priority=100,
            ),
        }
    ),
    "バインド": VolatileData(
        handlers={
            Event.ON_TURN_END: h.VolatileHandler(
                h.バインド_damage,
                subject_spec="source:self",
                priority=100
            ),
            Event.ON_CHECK_TRAPPED: h.VolatileHandler(
                h.check_trapped_not_ghost,
                subject_spec="source:self",
            ),
            Event.ON_SWITCH_OUT: h.VolatileHandler(
                h.バインド_remove,
                subject_spec="source:foe",
            ),
        }
    ),
    "ひるみ": VolatileData(
        handlers={
            Event.ON_TRY_ACTION: h.VolatileHandler(
                h.ひるみ_block_action,
                subject_spec="attacker:self",
                priority=40,
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.ひるみ_remove_volatile),
        }
    ),
    "ふういん": VolatileData(
        handlers={
            Event.ON_TRY_ACTION: h.VolatileHandler(
                h.ふういん_try_action,
                subject_spec="defender:self",
                priority=100,
            ),
        }
    ),
    "ほろびのうた": VolatileData(
        handlers={
            Event.ON_TURN_END: h.VolatileHandler(
                h.ほろびのうた_tick_volatile,
                subject_spec="source:self",
                priority=120
            ),
            Event.ON_VOLATILE_END: h.VolatileHandler(
                h.ほろびのうた_faint,
                subject_spec="source:self",
            )
        }
    ),
    "マジックコート": VolatileData(
        handlers={
            Event.ON_CHECK_REFLECT: h.VolatileHandler(
                h.マジックコート_reflect,
                subject_spec="defender:self",
                priority=200
            ),
        }
    ),
    "まるくなる": VolatileData(
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.VolatileHandler(
                h.まるくなる_boost_power,
                subject_spec="attacker:self",
            ),
        }
    ),
    "みがわり": VolatileData(
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.VolatileHandler(
                h.みがわり_immune,
                subject_spec="defender:self",
                priority=30,
            ),
            Event.ON_MODIFY_MOVE_DAMAGE: h.VolatileHandler(
                h.みがわり_block_damage,
                subject_spec="defender:self",
                priority=20,
            ),
        }
    ),
    "みちづれ": VolatileData(
        handlers={
            Event.ON_MOVE_KO: h.VolatileHandler(
                h.みちづれ_faint,
                subject_spec="defender:self",
                priority=30
            ),
        }
    ),
    "メロメロ": VolatileData(
        handlers={
            Event.ON_TRY_ACTION: h.VolatileHandler(
                h.メロメロ_try_action,
                subject_spec="attacker:self",
                priority=130
            ),
        }
    ),
    "やどりぎのタネ": VolatileData(
        handlers={
            Event.ON_TURN_END: h.VolatileHandler(
                h.やどりぎのタネ_drain_hp,
                subject_spec="source:self",
                priority=80,
            ),
        }
    ),
    "ロックオン": VolatileData(
        handlers={
            Event.ON_MODIFY_ACCURACY: h.VolatileHandler(
                h.ロックオン_guarantee_hit,
                subject_spec="attacker:self",
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.ロックオン_tick_volatile,
                subject_spec="source:self",
            ),
            Event.ON_SWITCH_OUT: h.VolatileHandler(
                h.ロックオン_remove_volatile,
                subject_spec="source:foe",
            ),
        }
    ),
    "まもる": VolatileData(
        handlers={
            Event.ON_TRY_MOVE_1: h.VolatileHandler(
                h.まもる_protect,
                subject_spec="defender:self",
                priority=100,
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.まもる_remove_volatile,
                subject_spec="source:self",
            ),
        }
    ),
    "かえんのまもり": VolatileData(
        handlers={
            Event.ON_TRY_MOVE_1: h.VolatileHandler(
                h.かえんのまもり_protect,
                subject_spec="defender:self",
                priority=100,
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.かえんのまもり_remove_volatile,
                subject_spec="source:self",
            ),
        }
    ),
    "キングシールド": VolatileData(
        handlers={
            Event.ON_TRY_MOVE_1: h.VolatileHandler(
                h.キングシールド_protect,
                subject_spec="defender:self",
                priority=100,
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.キングシールド_remove_volatile,
                subject_spec="source:self",
            ),
        }
    ),
    "スレッドトラップ": VolatileData(
        handlers={
            Event.ON_TRY_MOVE_1: h.VolatileHandler(
                h.スレッドトラップ_protect,
                subject_spec="defender:self",
                priority=100,
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.スレッドトラップ_remove_volatile,
                subject_spec="source:self",
            ),
        }
    ),
    "トーチカ": VolatileData(
        handlers={
            Event.ON_TRY_MOVE_1: h.VolatileHandler(
                h.トーチカ_protect,
                subject_spec="defender:self",
                priority=100,
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.トーチカ_remove_volatile,
                subject_spec="source:self",
            ),
        }
    ),
    "ハロウィン": VolatileData(
        handlers={
            Event.ON_VOLATILE_START: h.VolatileHandler(
                h.ハロウィン_add_type,
                subject_spec="source:self",
            ),
            Event.ON_VOLATILE_END: h.VolatileHandler(
                h.ハロウィン_remove_type,
                subject_spec="source:self",
            ),
        }
    ),
    "もりののろい": VolatileData(
        handlers={
            Event.ON_VOLATILE_START: h.VolatileHandler(
                h.もりののろい_add_type,
                subject_spec="source:self",
            ),
            Event.ON_VOLATILE_END: h.VolatileHandler(
                h.もりののろい_remove_type,
                subject_spec="source:self",
            ),
        }
    ),
}


common_setup()
