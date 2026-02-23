"""揮発状態データ定義モジュール。

Note:
    このモジュール内の揮発状態定義はVOLATILES辞書内で五十音順に配置されています。
"""
from functools import partial

from jpoke.enums import Event
from jpoke.core import HandlerReturn
from jpoke.handlers import common, volatile as h
from .models import VolatileData


def common_setup() -> None:
    """
    各VOLATILEのハンドラにログ用のテキスト（名前）を設定する。

    この関数は、VOLATILESディクショナリ内の全てのVolatileDataに対して、
    各イベントハンドラにlog_text属性として状態名を設定します。
    これにより、ハンドラ実行時のログ出力で状態名を表示できます。

    呼び出しタイミング: モジュール初期化時（ファイル末尾）
    """
    for name, data in VOLATILES.items():
        VOLATILES[name].name = name
        for event in data.handlers:
            data.handlers[event].log_text = name


VOLATILES: dict[str, VolatileData] = {
    "": VolatileData(),
    "アクアリング": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                partial(common.modify_hp, target_spec="source:self", r=1/16),
                subject_spec="source:self",
                log="on_success",
                priority=10,
            ),
        }
    ),
    "あばれる": VolatileData(
        handlers={
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                h.あばれる_modify_command_options,
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
                lambda *args: HandlerReturn(value=False),
                subject_spec="source:self",
            ),
        }
    ),
    "おんねん": VolatileData(
        handlers={
            Event.ON_TRY_ACTION: h.VolatileHandler(
                partial(h.remove_volatile, name="おんねん"),
                subject_spec="attacker:self",
                priority=10
            ),
            Event.ON_DAMAGE: h.VolatileHandler(
                h.おんねん,
                subject_spec="defender:self",
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
            Event.ON_TRY_ACTION: h.VolatileHandler(
                h.かなしばり_try_action,
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
            Event.ON_TRY_ACTION: h.VolatileHandler(
                h.こんらん_action,
                subject_spec="attacker:self",
                priority=110
            ),
        }
    ),
    "さわぐ": VolatileData(
        handlers={
            # TODO: 実装(低優先度)
        }
    ),
    "しおづけ": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                h.しおづけ,
                subject_spec="source:self",
                priority=90,
                log="on_success",
            ),
        }
    ),
    "じごくずき": VolatileData(
        handlers={
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                h.じごくずき_restrict_commands,
                subject_spec="source:self",
            ),
            Event.ON_TRY_ACTION: h.VolatileHandler(
                h.じごくづき_try_action,
                subject_spec="attacker:self",
            ),
            Event.ON_TURN_END_3: h.VolatileHandler(
                partial(h.tick_volatile, name="じごくずき"),
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
                log="never",
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
            Event.ON_TRY_ACTION: h.VolatileHandler(
                h.ちょうはつ_try_action,
                subject_spec="attacker:self",
                log="on_success",
                priority=200
            ),
            Event.ON_TURN_END_3: h.VolatileHandler(
                partial(h.tick_volatile, name="ちょうはつ"),
                subject_spec="source:self",
                log="on_success",
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
            Event.ON_CHECK_DEF_ABILITY: h.VolatileHandler(
                lambda *args: HandlerReturn(value=None),
                subject_spec="defender:self",
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
                h.ねむけ_tick,
                subject_spec="source:self",
                log="on_success",
                priority=100
            ),
        }
    ),
    "ねをはる": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                partial(common.modify_hp, target_spec="source:self", r=1/16),
                subject_spec="source:self",
                log="on_success",
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
                log="on_success",
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
            Event.ON_TRY_ACTION: h.VolatileHandler(
                h.ひるみ_action,
                subject_spec="attacker:self",
                priority=40,
            ),
        }
    ),
    "ふういん": VolatileData(
        handlers={
        }
    ),
    "ほろびのうた": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                h.ほろびのうた_tick,
                subject_spec="source:self",
                priority=110
            ),
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
        handlers={}
    ),
    "みがわり": VolatileData(
        handlers={
            Event.ON_TRY_IMMUNE: h.VolatileHandler(
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
            Event.ON_DAMAGE: h.VolatileHandler(
                h.みちづれ,
                subject_spec="defender:self",
                priority=30
            ),
        }
    ),
    "メロメロ": VolatileData(
        handlers={
            Event.ON_TRY_ACTION: h.VolatileHandler(
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
                log="on_success",
                log_text="やどりぎのタネ",
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
    # まもる系
    "まもる": VolatileData(
        handlers={
            Event.ON_CHECK_PROTECT: h.VolatileHandler(
                h.まもる_check_protect,
                subject_spec="defender:self",
                log="never",
                priority=100  # ON_TRY_MOVE Priority 100: 無効化判定
            ),
            Event.ON_TURN_END_1: h.VolatileHandler(
                partial(h.remove_volatile, name="まもる"),
                subject_spec="source:self",
                log="never",
                priority=200
            ),
        }
    ),
    "トーチカ": VolatileData(
        handlers={
            Event.ON_CHECK_PROTECT: h.VolatileHandler(
                h.トーチカ_check_protect,
                subject_spec="defender:self",
                log="never",
                priority=100  # ON_TRY_MOVE Priority 100: 無効化判定
            ),
            Event.ON_TURN_END_1: h.VolatileHandler(
                partial(h.remove_volatile, name="トーチカ"),
                subject_spec="source:self",
                log="never",
                priority=200
            ),
        }
    ),
    "キングシールド": VolatileData(
        handlers={
            Event.ON_CHECK_PROTECT: h.VolatileHandler(
                h.キングシールド_check_protect,
                subject_spec="defender:self",
                log="never",
                priority=100  # ON_TRY_MOVE Priority 100: 無効化判定
            ),
            Event.ON_TURN_END_1: h.VolatileHandler(
                partial(h.remove_volatile, name="キングシールド"),
                subject_spec="source:self",
                log="never",
                priority=200
            ),
        }
    ),
    "スレッドトラップ": VolatileData(
        handlers={
            Event.ON_CHECK_PROTECT: h.VolatileHandler(
                h.スレッドトラップ_check_protect,
                subject_spec="defender:self",
                log="never",
                priority=100  # ON_TRY_MOVE Priority 100: 無効化判定
            ),
            Event.ON_TURN_END_1: h.VolatileHandler(
                partial(h.remove_volatile, name="スレッドトラップ"),
                subject_spec="source:self",
                log="never",
                priority=200
            ),
        }
    ),
    "かえんのまもり": VolatileData(
        handlers={
            Event.ON_CHECK_PROTECT: h.VolatileHandler(
                h.かえんのまもり_check_protect,
                subject_spec="defender:self",
                log="never",
                priority=100  # ON_TRY_MOVE Priority 100: 無効化判定
            ),
            Event.ON_TURN_END_1: h.VolatileHandler(
                partial(h.remove_volatile, name="かえんのまもり"),
                subject_spec="source:self",
                log="never",
                priority=200
            ),
        }
    ),

    # 隠れる系
    "あなをほる": VolatileData(
        handlers={
            Event.ON_CHECK_INVULNERABLE: h.VolatileHandler(
                partial(h.姿消し_check_invulnerable, allowed_moves=["じしん", "マグニチュード"]),
                subject_spec="defender:self",
                log="never",
                priority=50
            ),
        }
    ),
    "そらをとぶ": VolatileData(
        handlers={
            Event.ON_CHECK_INVULNERABLE: h.VolatileHandler(
                partial(h.姿消し_check_invulnerable, allowed_moves=["かぜおこし", "たつまき", "かみなり"]),
                subject_spec="defender:self",
                log="never",
                priority=50
            ),
        }
    ),
    "ダイビング": VolatileData(
        handlers={
            Event.ON_CHECK_INVULNERABLE: h.VolatileHandler(
                partial(h.姿消し_check_invulnerable, allowed_moves=["なみのり", "うずしお"]),
                subject_spec="defender:self",
                log="never",
                priority=50
            ),
        }
    ),
    "シャドーダイブ": VolatileData(
        handlers={
            Event.ON_CHECK_INVULNERABLE: h.VolatileHandler(
                partial(h.姿消し_check_invulnerable, allowed_moves=[]),
                subject_spec="defender:self",
                log="never",
                priority=50
            ),
        }
    ),
}


common_setup()
