# TODO : lambda式は使わず、名前付き関数をhandlers/volatile.pyに定義する

"""揮発状態データ定義モジュール。

Note:
    このモジュール内の揮発状態定義はVOLATILES辞書内で五十音順に配置されています。
"""
from functools import partial

from jpoke.enums import Event, Command
from jpoke.core import HandlerReturn
from jpoke.handlers import common, volatile as h
from .models import VolatileData


def common_setup() -> None:
    """
    各VOLATILEのハンドラにログ用のテキスト（名前）を設定する。

    この関数は、VOLATILESディクショナリ内の全てのVolatileDataに対して、
    これにより、ハンドラ実行時のログ出力で状態名を表示できます。

    呼び出しタイミング: モジュール初期化時（ファイル末尾）
    """
    for name, data in VOLATILES.items():
        VOLATILES[name].name = name


VOLATILES: dict[str, VolatileData] = {
    "": VolatileData(),
    "アクアリング": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                partial(common.modify_hp, target_spec="source:self", r=1/16),
                subject_spec="source:self",
                priority=10,
            ),
        }
    ),
    "あばれる": VolatileData(
        forced=True,
        handlers={
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                lambda *args: HandlerReturn(value=[Command.FORCED], stop_event=True),
                subject_spec="source:self",
            ),
            Event.ON_DAMAGE: h.VolatileHandler(
                h.あばれる_tick,
                subject_spec="attacker:self",
                priority=180
            ),
        }
    ),
    "あめまみれ": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                h.あめまみれ,
                subject_spec="source:self",
            ),
        }
    ),
    "アンコール": VolatileData(
        handlers={
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                partial(h.restrict_commands, name="アンコール"),
                subject_spec="source:self",
            ),
            Event.ON_MODIFY_MOVE: h.VolatileHandler(
                h.アンコール_modify_move,
                subject_spec="attacker:self",
                priority=200
            ),
            Event.ON_TURN_END_3: h.VolatileHandler(
                partial(h.tick_volatile, name="アンコール"),
                subject_spec="source:self",
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
                lambda *args: HandlerReturn(value=False, stop_event=True),
                subject_spec="source:self",
            ),
        }
    ),
    "おんねん": VolatileData(
        handlers={
            Event.ON_CHECK_ACTION: h.VolatileHandler(
                partial(h.remove_volatile, name="おんねん"),
                subject_spec="attacker:self",
                priority=10
            ),
            Event.ON_FAINTED: h.VolatileHandler(
                h.おんねん,
                subject_spec="target:self",
                priority=10
            ),
        }
    ),
    "かいふくふうじ": VolatileData(
        handlers={
            Event.ON_BEFORE_HEAL: h.VolatileHandler(
                h.かいふくふうじ,
                subject_spec="target:self",
            ),
            Event.ON_TURN_END_3: h.VolatileHandler(
                partial(h.tick_volatile, name="かいふくふうじ"),
                subject_spec="source:self",
                priority=100
            ),
        }
    ),
    "かなしばり": VolatileData(
        handlers={
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                h.かなしばり_modify_command_options,
                subject_spec="source:self",
            ),
            Event.ON_CHECK_ACTION: h.VolatileHandler(
                h.かなしばり_check_action,
                subject_spec="attacker:self",
                priority=100
            ),
            Event.ON_TURN_END_3: h.VolatileHandler(
                partial(h.tick_volatile, name="かなしばり"),
                subject_spec="source:self",
                priority=100
            ),
        }
    ),
    "きゅうしょアップ": VolatileData(
        handlers={
            Event.ON_CALC_CRITICAL_RANK: h.VolatileHandler(
                h.きゅうしょアップ,
                subject_spec="attacker:self",
            ),
        }
    ),
    "こだわり": VolatileData(
        handlers={
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                partial(h.restrict_commands, name="こだわり"),
                subject_spec="source:self",
            )
        }
    ),
    "こんらん": VolatileData(
        handlers={
            Event.ON_CHECK_ACTION: h.VolatileHandler(
                h.こんらん_action,
                subject_spec="attacker:self",
                priority=110
            ),
        }
    ),
    "さわぐ": VolatileData(
        handlers={
            Event.ON_APPLY_VOLATILE: h.VolatileHandler(
                h.さわぐ_on_apply,
                subject_spec="source:self",
            ),
            Event.ON_VOLATILE_END: h.VolatileHandler(
                h.さわぐ_on_end,
                subject_spec="source:self",
            ),
            Event.ON_TURN_END_3: h.VolatileHandler(
                partial(h.tick_volatile, name="さわぐ"),
                subject_spec="source:self",
            ),
            Event.ON_MODIFY_MOVE: h.VolatileHandler(
                h.さわぐ_modify_move,
                subject_spec="attacker:self",
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
    "しおづけ": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                h.しおづけ,
                subject_spec="source:self",
                priority=90,
            ),
        }
    ),
    "じごくづき": VolatileData(
        handlers={
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                h.じごくづき_restrict_commands,
                subject_spec="source:self",
            ),
            Event.ON_CHECK_ACTION: h.VolatileHandler(
                h.じごくづき_check_action,
                subject_spec="attacker:self",
            ),
            Event.ON_TURN_END_3: h.VolatileHandler(
                partial(h.tick_volatile, name="じごくづき"),
                subject_spec="source:self",
            ),
        }
    ),
    "じゅうでん": VolatileData(
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.VolatileHandler(
                h.じゅうでん_boost,
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
                h.タールショット_damage_modifier,
                subject_spec="defender:self",
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
                h.ちいさくなる_power_modifier,
                subject_spec="defender:self",
            ),
        }
    ),
    "ちょうはつ": VolatileData(
        handlers={
            Event.ON_CHECK_ACTION: h.VolatileHandler(
                h.ちょうはつ_check_action,
                subject_spec="attacker:self",
                priority=200
            ),
            Event.ON_TURN_END_3: h.VolatileHandler(
                partial(h.tick_volatile, name="ちょうはつ"),
                subject_spec="source:self",
                priority=100
            ),
        }
    ),
    "でんじふゆう": VolatileData(
        handlers={
            Event.ON_CHECK_FLOATING: h.VolatileHandler(
                lambda *args: HandlerReturn(value=True),
                subject_spec="source:self",
            ),
            Event.ON_TURN_END_3: h.VolatileHandler(
                partial(h.tick_volatile, name="でんじふゆう"),
                subject_spec="source:self",
            ),
        }
    ),
    "とくせいなし": VolatileData(
        handlers={
            Event.ON_APPLY_VOLATILE: h.VolatileHandler(
                h.とくせいなし_on_volatile_apply,
                subject_spec="source:self",
            ),
            Event.ON_VOLATILE_END: h.VolatileHandler(
                h.とくせいなし_on_volatile_end,
                subject_spec="source:self",
            ),
            Event.ON_CHECK_ABILITY_ENABLED: h.VolatileHandler(
                h.とくせいなし_check_ability_enabled,
                subject_spec="source:self",
            ),
        }
    ),
    "にげられない": VolatileData(
        handlers={
            Event.ON_CHECK_TRAPPED: h.VolatileHandler(
                lambda *args: HandlerReturn(value=True),
                subject_spec="source:self",
            ),
        }
    ),
    "ねむけ": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                partial(h.tick_volatile, name="ねむけ"),
                subject_spec="source:self",
                priority=100,
            ),
            Event.ON_VOLATILE_END: h.VolatileHandler(
                h.ねむけ_on_volatile_end,
                subject_spec="source:self",
            ),
        }
    ),
    "ねをはる": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                partial(common.modify_hp, target_spec="source:self", r=1/16),
                subject_spec="source:self",
                priority=10
            ),
            Event.ON_CHECK_TRAPPED: h.VolatileHandler(
                lambda *args: HandlerReturn(value=True),
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
            Event.ON_TURN_END_3: h.VolatileHandler(
                h.のろい_damage,
                subject_spec="source:self",
                priority=70,
            ),
        }
    ),
    "バインド": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                h.バインド_damage,
                subject_spec="source:self",
                priority=70
            ),
            Event.ON_CHECK_TRAPPED: h.VolatileHandler(
                lambda *args: HandlerReturn(value=True),
                subject_spec="source:self",
            ),
            Event.ON_SWITCH_OUT: h.VolatileHandler(
                h.バインド_swith_out,
                subject_spec="source:foe",
            ),
        }
    ),
    "ひるみ": VolatileData(
        handlers={
            Event.ON_CHECK_ACTION: h.VolatileHandler(
                h.ひるみ_block_action,
                subject_spec="attacker:self",
                priority=40,
            ),
        }
    ),
    "ふういん": VolatileData(
        handlers={
            Event.ON_CHECK_ACTION: h.VolatileHandler(
                h.ふういん,
                subject_spec="defender:self",
                priority=100,
            ),
        }
    ),
    "ほろびのうた": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                partial(h.tick_volatile, name="ほろびのうた"),
                subject_spec="source:self",
                priority=110
            ),
            Event.ON_VOLATILE_END: h.VolatileHandler(
                h.ほろびのうた_faint,
                subject_spec="source:self",
            )
        }
    ),
    "マジックコート": VolatileData(
        handlers={
            Event.ON_QUERY_REFLECT: h.VolatileHandler(
                h.マジックコート_reflect,
                subject_spec="defender:self",
                priority=200
            ),
        }
    ),
    "まるくなる": VolatileData(
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.VolatileHandler(
                h.まるくなる_power_modifier,
                subject_spec="attacker:self",
            ),
        }
    ),
    "みがわり": VolatileData(
        handlers={
            Event.ON_CHECK_MOVE_IMMUNE: h.VolatileHandler(
                h.みがわり_immune,
                subject_spec="defender:self",
                priority=30,
            ),
            Event.ON_MODIFY_DAMAGE: h.VolatileHandler(
                h.みがわり_modify_damage,
                subject_spec="defender:self",
                priority=20,
            ),
        }
    ),
    "みちづれ": VolatileData(
        handlers={
            Event.ON_FAINTED: h.VolatileHandler(
                h.みちづれ,
                subject_spec="target:self",
                priority=30
            ),
        }
    ),
    "メロメロ": VolatileData(
        handlers={
            Event.ON_CHECK_ACTION: h.VolatileHandler(
                h.メロメロ_action,
                subject_spec="attacker:self",
                priority=130
            ),
        }
    ),
    "やどりぎのタネ": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                partial(common.drain_hp, from_="source:self", r=1/8),
                subject_spec="source:self",
                priority=20,
            ),
        }
    ),
    "ロックオン": VolatileData(
        handlers={
            Event.ON_MODIFY_ACCURACY: h.VolatileHandler(
                h.ロックオン_modify_accuracy,
                subject_spec="attacker:self",
            ),
        }
    ),
    "まもる": VolatileData(
        handlers={
            Event.ON_CHECK_MOVE: h.VolatileHandler(
                h.まもる_protect,
                subject_spec="defender:self",
                priority=100,
            ),
            Event.ON_TURN_END_1: h.VolatileHandler(
                partial(h.remove_volatile, name="まもる"),
                subject_spec="source:self",
            ),
        }
    ),
    "かえんのまもり": VolatileData(
        handlers={
            Event.ON_CHECK_MOVE: h.VolatileHandler(
                h.かえんのまもり_protect,
                subject_spec="defender:self",
                priority=100,
            ),
            Event.ON_TURN_END_1: h.VolatileHandler(
                partial(h.remove_volatile, name="かえんのまもり"),
                subject_spec="source:self",
            ),
        }
    ),
    "キングシールド": VolatileData(
        handlers={
            Event.ON_CHECK_MOVE: h.VolatileHandler(
                h.キングシールド_protect,
                subject_spec="defender:self",
                priority=100,
            ),
            Event.ON_TURN_END_1: h.VolatileHandler(
                partial(h.remove_volatile, name="キングシールド"),
                subject_spec="source:self",
            ),
        }
    ),
    "スレッドトラップ": VolatileData(
        handlers={
            Event.ON_CHECK_MOVE: h.VolatileHandler(
                h.スレッドトラップ_protect,
                subject_spec="defender:self",
                priority=100,
            ),
            Event.ON_TURN_END_1: h.VolatileHandler(
                partial(h.remove_volatile, name="スレッドトラップ"),
                subject_spec="source:self",
            ),
        }
    ),
    "トーチカ": VolatileData(
        handlers={
            Event.ON_CHECK_MOVE: h.VolatileHandler(
                h.トーチカ_protect,
                subject_spec="defender:self",
                priority=100,
            ),
            Event.ON_TURN_END_1: h.VolatileHandler(
                partial(h.remove_volatile, name="トーチカ"),
                subject_spec="source:self",
            ),
        }
    ),
    "かくれる": VolatileData(
        forced=True,
        handlers={
            Event.ON_CHECK_TRAPPED: h.VolatileHandler(
                lambda *args: HandlerReturn(value=True),
                subject_spec="source:self",
            ),
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                lambda *args: HandlerReturn(value=[Command.FORCED], stop_event=True),
                subject_spec="source:self",
            ),
            Event.ON_CHECK_MOVE: h.VolatileHandler(
                h.check_hidden_move,
                subject_spec="defender:self",
                priority=50
            ),
            Event.ON_HIT: h.VolatileHandler(
                partial(h.remove_volatile, name="かくれる"),
                subject_spec="attacker:self",
            ),
        }
    ),
}


common_setup()
