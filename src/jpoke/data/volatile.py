from functools import partial

from jpoke.utils.enums import Event
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
                partial(common.heal_hp, from_="source:self", r=1/16),
                subject_spec="source:self",
                priority=10,
            ),
        }
    ),
    "あめまみれ": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                h.あめまみれ_turn_end,
                subject_spec="source:self",
                log="on_success",
                priority=100
            ),
        }
    ),
    "アンコール": VolatileData(
        handlers={
            Event.ON_BEFORE_MOVE: h.VolatileHandler(
                h.アンコール_before_move,
                subject_spec="target:self",
                log="on_success",
                priority=200
            ),
            Event.ON_TURN_END_3: h.VolatileHandler(
                h.アンコール_turn_end,
                subject_spec="source:self",
                log="on_success",
                priority=100
            ),
        }
    ),
    "うちおとす": VolatileData(
        handlers={
            Event.ON_CHECK_FLOATING: h.VolatileHandler(
                h.うちおとす_check_floating,
                subject_spec="source:self",
                log="never",
                priority=50,
            ),
        }
    ),
    "かいふくふうじ": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                h.かいふくふうじ_turn_end,
                subject_spec="source:self",
                log="on_success",
                priority=100
            ),
        }
    ),
    "かなしばり": VolatileData(
        handlers={
            Event.ON_BEFORE_MOVE: h.VolatileHandler(
                h.かなしばり_before_move,
                subject_spec="target:self",
                log="on_success",
                priority=200
            ),
            Event.ON_TURN_END_3: h.VolatileHandler(
                h.かなしばり_turn_end,
                subject_spec="source:self",
                log="on_success",
                priority=100
            ),
        }
    ),
    "急所ランク": VolatileData(
        handlers={
            Event.ON_CALC_CRITICAL: h.VolatileHandler(
                h.急所ランク_calc_critical,
                subject_spec="attacker:self",
                log="never",
                priority=50,
            ),
        }
    ),
    "こんらん": VolatileData(
        handlers={
            Event.ON_TRY_ACTION: h.VolatileHandler(
                h.こんらん_action,
                subject_spec="target:self",
                log="on_success",
                priority=110
            ),
        }
    ),
    "ひるみ": VolatileData(
        handlers={
            Event.ON_TRY_ACTION: h.VolatileHandler(
                h.ひるみ_action,
                subject_spec="target:self",
                log="never",
                priority=40
            ),
            Event.ON_TURN_END_1: h.VolatileHandler(
                h.ひるみ_turn_end,
                subject_spec="source:self",
                log="never",
                priority=10
            ),
        }
    ),
    "しおづけ": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                partial(common.drain_hp, from_="source:self", r=1/8),
                subject_spec="source:self",
                priority=90,
            ),
        }
    ),
    "じごくずき": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                h.じごくずき_turn_end,
                subject_spec="source:self",
                log="on_success",
                priority=100
            ),
        }
    ),
    "じゅうでん": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                h.じゅうでん_turn_end,
                subject_spec="source:self",
                log="on_success",
                priority=100
            ),
        }
    ),
    "たくわえる": VolatileData(
        handlers={
            # TODO: たくわえるのハンドラを実装
            # 蓄積数（最大3）を管理し、はきだす・のみこむで使用
            # 使用時に防御・特防ランク+1、はきだす・のみこむで蓄積数リセット＆ランク解除
        }
    ),
    "ちょうはつ": VolatileData(
        handlers={
            Event.ON_BEFORE_MOVE: h.VolatileHandler(
                h.ちょうはつ_before_move,
                subject_spec="target:self",
                log="on_success",
                priority=200
            ),
            Event.ON_TURN_END_3: h.VolatileHandler(
                h.ちょうはつ_turn_end,
                subject_spec="source:self",
                log="on_success",
                priority=100
            ),
        }
    ),
    "でんじふゆう": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                h.でんじふゆう_turn_end,
                subject_spec="source:self",
                log="on_success",
                priority=100
            ),
        }
    ),
    "にげられない": VolatileData(
        handlers={
            Event.ON_CHECK_TRAPPED: h.VolatileHandler(
                h.にげられない_check_trapped,
                subject_spec="source:self",
                log="on_success",
                priority=200
            ),
        }
    ),
    "ねむけ": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                h.ねむけ_turn_end,
                subject_spec="source:self",
                log="on_success",
                priority=100
            ),
        }
    ),
    "ねをはる": VolatileData(
        handlers={
            Event.ON_CHECK_TRAPPED: h.VolatileHandler(
                h.ねをはる_check_trapped,
                subject_spec="source:self",
                log="on_success",
                priority=200
            ),
        }
    ),
    "のろい": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                partial(common.drain_hp, from_="source:self", r=1/4),
                subject_spec="source:self",
                priority=70,
            ),
        }
    ),
    "バインド": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                h.バインド_turn_end,
                subject_spec="source:self",
                log="on_success",
                priority=70
            ),
            Event.ON_CHECK_TRAPPED: h.VolatileHandler(
                h.バインド_before_switch,
                subject_spec="source:self",
                log="on_success",
                priority=200
            ),
        }
    ),
    "ほろびのうた": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                h.ほろびのうた_turn_end,
                subject_spec="source:self",
                log="on_success",
                priority=110
            ),
        }
    ),
    "みがわり": VolatileData(
        handlers={
            Event.ON_TRY_IMMUNE: h.VolatileHandler(
                h.みがわり_check_substitute,
                subject_spec="defender:self",
                log="never",
                priority=30,  # ON_TRY_IMMUNE Priority 30: みがわりによる無効化
            ),
            Event.ON_BEFORE_DAMAGE_APPLY: h.VolatileHandler(
                h.みがわり_before_damage_apply,
                subject_spec="defender:self",
                log="never",
                priority=50,
            ),
        }
    ),
    "みちづれ": VolatileData(
        handlers={
            Event.ON_FAINT: h.VolatileHandler(
                h.みちづれ_on_faint,
                subject_spec="defender:self",
                log="on_success",
                priority=100
            ),
        }
    ),
    "メロメロ": VolatileData(
        handlers={
            Event.ON_TRY_ACTION: h.VolatileHandler(
                h.メロメロ_action,
                subject_spec="target:self",
                log="on_success",
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
    "あくむ": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                h.あくむ_turn_end,
                subject_spec="source:self",
                priority=75,
            ),
        }
    ),
    "さしおさえ": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                h.さしおさえ_turn_end,
                subject_spec="source:self",
                log="on_success",
                priority=100
            ),
        }
    ),
    "たこがため": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                h.たこがため_turn_end,
                subject_spec="source:self",
                priority=80,
            ),
        }
    ),
    "タールショット": VolatileData(
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.VolatileHandler(
                h.タールショット_damage_modifier,
                subject_spec="defender:self",
                log="never",
                priority=80,
            ),
        }
    ),
    "テレキネシス": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                h.テレキネシス_turn_end,
                subject_spec="source:self",
                log="on_success",
                priority=100
            ),
        }
    ),
    "そうでん": VolatileData(
        handlers={
            Event.ON_CHECK_MOVE_TYPE: h.VolatileHandler(
                h.そうでん_move_type,
                subject_spec="source:self",
                log="never",
                priority=50,
            ),
            Event.ON_TURN_END_1: h.VolatileHandler(
                h.そうでん_turn_end,
                subject_spec="source:self",
                log="never",
                priority=200
            ),
        }
    ),
    "まるくなる": VolatileData(
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.VolatileHandler(
                h.まるくなる_power_modifier,
                subject_spec="attacker:self",
                log="never",
                priority=80,
            ),
        }
    ),
    "ちいさくなる": VolatileData(
        handlers={
            Event.ON_CALC_ACCURACY: h.VolatileHandler(
                h.ちいさくなる_accuracy_modifier,
                subject_spec="defender:self",
                log="never",
                priority=50,
            ),
            Event.ON_CALC_POWER_MODIFIER: h.VolatileHandler(
                h.ちいさくなる_power_modifier,
                subject_spec="defender:self",
                log="never",
                priority=80,
            ),
        }
    ),
    "ロックオン": VolatileData(
        handlers={
            Event.ON_CALC_ACCURACY: h.VolatileHandler(
                h.ロックオン_accuracy,
                subject_spec="defender:self",
                log="never",
                priority=50,
            ),
            Event.ON_HIT: h.VolatileHandler(
                h.ロックオン_on_hit,
                subject_spec="defender:self",
                log="never",
                priority=50,
            ),
            Event.ON_TURN_END_3: h.VolatileHandler(
                h.ロックオン_turn_end,
                subject_spec="source:self",
                log="never",
                priority=100,
            ),
        }
    ),
    "特性なし": VolatileData(
        handlers={
            # 特性無効化は別途特性判定時に参照
        }
    ),
    "いちゃもん": VolatileData(
        handlers={
            Event.ON_BEFORE_MOVE: h.VolatileHandler(
                h.いちゃもん_before_move,
                subject_spec="target:self",
                log="on_success",
                priority=200
            ),
            Event.ON_TRY_MOVE: h.VolatileHandler(
                h.いちゃもん_record_move,
                subject_spec="attacker:self",
                log="never",
                priority=200
            ),
        }
    ),
    "あばれる": VolatileData(
        handlers={
            Event.ON_BEFORE_MOVE: h.VolatileHandler(
                h.あばれる_before_move,
                subject_spec="target:self",
                log="never",
                priority=200
            ),
            Event.ON_TURN_END_3: h.VolatileHandler(
                h.あばれる_turn_end,
                subject_spec="source:self",
                log="on_success",
                priority=100
            ),
        }
    ),
    "さわぐ": VolatileData(
        handlers={
            Event.ON_BEFORE_MOVE: h.VolatileHandler(
                h.さわぐ_before_move,
                subject_spec="target:self",
                log="never",
                priority=200
            ),
            Event.ON_BEFORE_APPLY_AILMENT: h.VolatileHandler(
                h.さわぐ_prevent_sleep,
                subject_spec="target:self",
                log="never",
                priority=50
            ),
            Event.ON_BEFORE_APPLY_AILMENT: h.VolatileHandler(
                h.さわぐ_prevent_sleep,
                subject_spec="target:foe",
                log="never",
                priority=50
            ),
            Event.ON_TURN_END_3: h.VolatileHandler(
                h.さわぐ_turn_end,
                subject_spec="source:self",
                log="on_success",
                priority=100
            ),
        }
    ),
    "おんねん": VolatileData(
        handlers={
            Event.ON_FAINT: h.VolatileHandler(
                h.おんねん_on_faint,
                subject_spec="defender:self",
                log="on_success",
                priority=100
            ),
        }
    ),
    "ふういん": VolatileData(
        handlers={
            Event.ON_BEFORE_MOVE: h.VolatileHandler(
                h.ふういん_before_move,
                subject_spec="source:foe",
                log="on_success",
                priority=200
            ),
        }
    ),
    "マジックコート": VolatileData(
        handlers={
            Event.ON_CHECK_REFLECT: h.VolatileHandler(
                h.マジックコート_before_damage,
                subject_spec="defender:self",
                log="on_success",
                priority=200
            ),
        }
    ),
    "まもる": VolatileData(
        handlers={
            Event.ON_CHECK_PROTECT: h.VolatileHandler(
                h.まもる_check_protect,
                subject_spec="defender:self",
                log="never",
                priority=100  # ON_TRY_MOVE Priority 100: 無効化判定
            ),
            Event.ON_TURN_END_1: h.VolatileHandler(
                h.まもる_turn_end,
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
                h.キングシールド_turn_end,
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
                h.トーチカ_turn_end,
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
                h.かえんのまもり_turn_end,
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
                h.スレッドトラップ_turn_end,
                subject_spec="source:self",
                log="never",
                priority=200
            ),
        }
    ),
    "あなをほる": VolatileData(
        handlers={
            Event.ON_CHECK_INVULNERABLE: h.VolatileHandler(
                partial(h.姿消し_check_invulnerable, allowed_moves=["じしん", "マグニチュード"]),
                subject_spec="defender:self",
                log="never",
                priority=50
            ),
            Event.ON_TURN_END_3: h.VolatileHandler(
                h.姿消し_turn_end,
                subject_spec="source:self",
                log="never",
                priority=100
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
            Event.ON_TURN_END_3: h.VolatileHandler(
                h.姿消し_turn_end,
                subject_spec="source:self",
                log="never",
                priority=100
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
            Event.ON_TURN_END_3: h.VolatileHandler(
                h.姿消し_turn_end,
                subject_spec="source:self",
                log="never",
                priority=100
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
            Event.ON_TURN_END_3: h.VolatileHandler(
                h.姿消し_turn_end,
                subject_spec="source:self",
                log="never",
                priority=100
            ),
        }
    ),
}


common_setup()
