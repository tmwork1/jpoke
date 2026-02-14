"""揮発状態データ定義モジュール。

Note:
    このモジュール内の揮発状態定義はVOLATILES辞書内で五十音順に配置されています。
"""
from functools import partial

from jpoke.enums import Event
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
                partial(common.modify_hp, target_role="source:self", r=1/16),
                subject_spec="source:self",
                priority=10,
            ),
        }
    ),
    "あばれる": VolatileData(
        handlers={
            Event.ON_CHECK_MOVE: h.VolatileHandler(
                h.あばれる_before_move,
                subject_spec="attacker:self",
                log="never",
                priority=200
            ),
            Event.ON_DAMAGE_2: h.VolatileHandler(
                h.あばれる_on_damage,
                subject_spec="source:self",
                log="on_success",
                priority=180
            ),
        }
    ),
    "あめまみれ": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                h.あめまみれ_turn_end,
                subject_spec="source:self",
                log="on_success",
            ),
        }
    ),
    "アンコール": VolatileData(
        handlers={
            Event.ON_CHECK_MOVE: h.VolatileHandler(
                h.アンコール_check_move,
                subject_spec="attacker:self",
                log="on_success",
                priority=200
            ),
            Event.ON_TURN_END_3: h.VolatileHandler(
                partial(h.tick_volatile, name="アンコール"),
                subject_spec="source:self",
                log="on_success",
                priority=100
            ),
        }
    ),
    "いちゃもん": VolatileData(
        handlers={
            Event.ON_CHECK_MOVE: h.VolatileHandler(
                h.いちゃもん_before_move,
                subject_spec="attacker:self",
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
    "かいふくふうじ": VolatileData(
        handlers={
            Event.ON_TURN_END_3: h.VolatileHandler(
                partial(h.tick_volatile, name="かいふくふうじ"),
                subject_spec="source:self",
                log="on_success",
                priority=100
            ),
        }
    ),
    "かなしばり": VolatileData(
        handlers={
            Event.ON_CHECK_MOVE: h.VolatileHandler(
                h.かなしばり_before_move,
                subject_spec="attacker:self",
                log="on_success",
                priority=200
            ),
            Event.ON_TURN_END_3: h.VolatileHandler(
                partial(h.tick_volatile, name="かなしばり"),
                subject_spec="source:self",
                log="on_success",
                priority=100
            ),
        }
    ),
    "きゅうしょアップ": VolatileData(
        handlers={
            Event.ON_MODIFY_CRITICAL_RANK: h.VolatileHandler(
                h.きゅうしょランク_calc_critical,
                subject_spec="attacker:self",
                log="never",
                priority=50,
            ),
        }
    ),
    "こだわり": VolatileData(
        handlers={
        }
    ),
    "こんらん": VolatileData(
        handlers={
            Event.ON_TRY_ACTION: h.VolatileHandler(
                h.こんらん_action,
                subject_spec="attacker:self",
                log="on_success",
                priority=110
            ),
        }
    ),
    "さわぐ": VolatileData(
        handlers={
            Event.ON_CHECK_MOVE: h.VolatileHandler(
                h.さわぐ_before_move,
                subject_spec="attacker:self",
                log="never",
                priority=200
            ),
            Event.ON_BEFORE_APPLY_AILMENT: h.VolatileHandler(
                h.さわぐ_prevent_sleep,
                subject_spec="attacker:self",
                log="never",
                priority=50
            ),
            # TODO: 複数ハンドラ登録を可能にする
            # Event.ON_BEFORE_APPLY_AILMENT: h.VolatileHandler(
            #     h.さわぐ_prevent_sleep,
            #     subject_spec="attacker:foe",
            #     log="never",
            #     priority=50
            #  ),
            Event.ON_TURN_END_3: h.VolatileHandler(
                partial(h.tick_volatile, name="さわぐ"),
                subject_spec="source:self",
                log="on_success",
                priority=100
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
                partial(h.tick_volatile, name="じごくずき"),
                subject_spec="source:self",
                log="on_success",
                priority=100
            ),
        }
    ),
    "じゅうでん": VolatileData(
        handlers={
        }
    ),
    "たくわえる": VolatileData(
        # Volatileではカウントの管理のみ行い、実際の効果は技のハンドラ側で処理
        handlers={}
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
    "ちいさくなる": VolatileData(
        handlers={
            Event.ON_MODIFY_ACCURACY: h.VolatileHandler(
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
    "ちょうはつ": VolatileData(
        handlers={
            Event.ON_CHECK_MOVE: h.VolatileHandler(
                h.ちょうはつ_before_move,
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
            Event.ON_TURN_END_3: h.VolatileHandler(
                partial(h.tick_volatile, name="でんじふゆう"),
                subject_spec="source:self",
                log="on_success",
                priority=100
            ),
        }
    ),
    "とくせいなし": VolatileData(
        handlers={
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
            Event.ON_TURN_END_3: h.VolatileHandler(
                partial(common.modify_hp, target_spec="source:self", r=1/16),
                subject_spec="source:self",
                log="on_success",
                priority=10
            ),
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
                h.バインド_check_trapped,
                subject_spec="source:self",
                log="on_success",
                priority=200
            ),
        }
    ),
    "ひるみ": VolatileData(
        handlers={
            Event.ON_TRY_ACTION: h.VolatileHandler(
                h.ひるみ_action,
                subject_spec="attacker:self",
                log="never",
                priority=40,
                once=True,
            ),
        }
    ),
    "ふういん": VolatileData(
        handlers={
            Event.ON_CHECK_MOVE: h.VolatileHandler(
                h.ふういん_before_move,
                subject_spec="source:foe",
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
                subject_spec="attacker:self",
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
    "ロックオン": VolatileData(
        handlers={
            Event.ON_MODIFY_ACCURACY: h.VolatileHandler(
                h.ロックオン_accuracy,
                subject_spec="defender:self",
                log="never",
                priority=50,
            ),
            Event.ON_HIT: h.VolatileHandler(
                partial(h.remove_volatile, name="ロックオン"),
                subject_spec="defender:self",
                log="never",
                priority=50,
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
