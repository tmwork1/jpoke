from jpoke.enums import DomainEvent, Event
from jpoke.handlers import field as h
from .models import FieldData

WEATHER_PRIORITY = {
    "": 0,
    "はれ": 0,
    "あめ": 0,
    "ゆき": 0,
    "すなあらし": 0,
    "おおひでり": 1,
    "おおあめ": 1,
    "らんきりゅう": 2,
}


def common_setup():
    """共通のセットアップ処理"""
    for name in FIELDS:
        FIELDS[name].name = name


FIELDS: dict[str, FieldData] = {
    "": FieldData(),
    # ===== 天候 (Weather) =====
    "はれ": FieldData(
        turn_extension_item="あついいわ",
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.FieldHandler(
                h.はれ_power_modifier,
                subject_spec="attacker:self",
            ),
            Event.ON_BEFORE_APPLY_AILMENT: h.FieldHandler(
                h.はれ_prevent_freeze,
                subject_spec="target:self",
            ),
            Event.ON_TURN_END: h.FieldHandler(
                h.tick_weather,
                subject_spec="source:self",
                priority=10,
            ),
        },
    ),
    "あめ": FieldData(
        turn_extension_item="しめったいわ",
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.FieldHandler(
                h.あめ_power_modifier,
                subject_spec="attacker:self",
            ),
            Event.ON_TURN_END: h.FieldHandler(
                h.tick_weather,
                subject_spec="source:self",
                priority=10,
            ),
        },
    ),
    "すなあらし": FieldData(
        turn_extension_item="さらさらいわ",
        handlers={
            Event.ON_CALC_DEF_MODIFIER: h.FieldHandler(
                h.すなあらし_D_boost,
                subject_spec="defender:self",
            ),
            Event.ON_TURN_END: h.FieldHandler(
                h.すなあらし_turn_end,
                subject_spec="source:self",
                priority=10,
            ),
        },
    ),
    "ゆき": FieldData(
        turn_extension_item="つめたいいわ",
        handlers={
            Event.ON_CALC_DEF_MODIFIER: h.FieldHandler(
                h.ゆき_B_boost,
                subject_spec="defender:self",
            ),
            Event.ON_TURN_END: h.FieldHandler(
                h.tick_weather,
                subject_spec="source:self",
                priority=10,
            ),
        },
    ),
    # ===== 強天候 (Strong Weather) =====
    "おおひでり": FieldData(
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.FieldHandler(
                h.はれ_power_modifier,
                subject_spec="attacker:self",
            ),
            Event.ON_BEFORE_APPLY_AILMENT: h.FieldHandler(
                h.はれ_prevent_freeze,
                subject_spec="target:self",
            ),
            Event.ON_TRY_MOVE_1: h.FieldHandler(
                h.おおひでり_block_move,
                priority=10,
                subject_spec="attacker:self",
            ),
        },
    ),
    "おおあめ": FieldData(
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.FieldHandler(
                h.あめ_power_modifier,
                subject_spec="attacker:self",
            ),
            Event.ON_TRY_MOVE_1: h.FieldHandler(
                h.おおあめ_block_move,
                priority=10,
                subject_spec="attacker:self",
            ),
        },
    ),
    "らんきりゅう": FieldData(
        handlers={
            Event.ON_CALC_DEF_TYPE_MODIFIER: h.FieldHandler(
                h.らんきりゅう_type_modifier,
                subject_spec="defender:self",
            ),
        },
    ),
    # ===== 地形 (Terrain) =====
    "エレキフィールド": FieldData(
        turn_extension_item="グランドコート",
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.FieldHandler(
                h.エレキフィールド_power_modifier,
                subject_spec="attacker:self",
            ),
            Event.ON_BEFORE_APPLY_AILMENT: h.FieldHandler(
                h.エレキフィールド_prevent_sleep,
                subject_spec="target:self",
            ),
            Event.ON_BEFORE_APPLY_VOLATILE: h.FieldHandler(
                h.エレキフィールド_prevent_nemuke,
                subject_spec="target:self",
            ),
            Event.ON_TURN_END: h.FieldHandler(
                h.tick_terrain,
                subject_spec="source:self",
                priority=140,
            ),
        },
    ),
    "グラスフィールド": FieldData(
        turn_extension_item="グランドコート",
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.FieldHandler(
                h.グラスフィールド_power_modifier,
                subject_spec="attacker:self",
            ),
            Event.ON_TURN_END: [
                h.FieldHandler(
                    h.グラスフィールド_heal,
                    subject_spec="source:self",
                    priority=60,
                ),
                h.FieldHandler(
                    h.tick_terrain,
                    subject_spec="source:self",
                    priority=140,
                ),
            ]
        },
    ),
    "サイコフィールド": FieldData(
        turn_extension_item="グランドコート",
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.FieldHandler(
                h.サイコフィールド_power_modifier,
                subject_spec="attacker:self",
            ),
            Event.ON_TRY_MOVE_1: h.FieldHandler(
                h.サイコフィールド_block_priority_move,
                priority=100,
                subject_spec="defender:self",
            ),
            Event.ON_TURN_END: h.FieldHandler(
                h.tick_terrain,
                subject_spec="source:self",
                priority=140,
            ),
        },
    ),
    "ミストフィールド": FieldData(
        turn_extension_item="グランドコート",
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.FieldHandler(
                h.ミストフィールド_power_modifier,
                subject_spec="defender:self",
            ),
            Event.ON_BEFORE_APPLY_AILMENT: h.FieldHandler(
                h.ミストフィールド_prevent_ailment,
                subject_spec="target:self",
            ),
            Event.ON_BEFORE_APPLY_VOLATILE: h.FieldHandler(
                h.ミストフィールド_prevent_confusion,
                subject_spec="target:self",
            ),
            Event.ON_TURN_END: h.FieldHandler(
                h.tick_terrain,
                subject_spec="source:self",
                priority=140,
            ),
        },
    ),
    # ===== グローバルフィールド (GlobalField) =====
    "じゅうりょく": FieldData(
        handlers={
            Event.ON_MODIFY_ACCURACY: h.FieldHandler(
                h.じゅうりょく_modify_accuracy,
                subject_spec="attacker:self",
            ),
            Event.ON_CHECK_FLOATING: h.FieldHandler(
                h.じゅうりょく_grounded,
                subject_spec="source:self",
            ),
            Event.ON_TURN_END: h.FieldHandler(
                h.じゅうりょく_tick_global_field,
                subject_spec="source:self",
                priority=140,
            ),
        },
    ),
    "トリックルーム": FieldData(
        handlers={
            DomainEvent.ON_CHECK_SPEED_REVERSE: h.FieldHandler(
                h.トリックルーム_reverse_speed,
                subject_spec="source:self",
            ),
            Event.ON_TURN_END: h.FieldHandler(
                h.トリックルーム_tick_global_field,
                subject_spec="source:self",
                priority=140,
            ),
        },
    ),
    "マジックルーム": FieldData(
        handlers={
            Event.ON_FIELD_ACTIVATE: h.FieldHandler(
                h.マジックルーム_apply,
                subject_spec="source:self",
            ),
            Event.ON_SWITCH_IN: h.FieldHandler(
                h.マジックルーム_apply,
                subject_spec="source:self",
            ),
            Event.ON_FIELD_DEACTIVATE: h.FieldHandler(
                h.マジックルーム_remove,
                subject_spec="source:self",
            ),
            Event.ON_TURN_END: h.FieldHandler(
                h.マジックルーム_tick_global_field,
                subject_spec="source:self",
                priority=140,
            ),
        },
    ),
    "ワンダールーム": FieldData(
        handlers={
            Event.ON_CALC_DEF_RANK_MODIFIER: h.FieldHandler(
                h.ワンダールーム_def_rank_modifier,
                subject_spec="defender:self",
            ),
            Event.ON_CALC_DEF_MODIFIER: h.FieldHandler(
                h.ワンダールーム_def_modifier,
                subject_spec="defender:self",
            ),
            Event.ON_TURN_END: h.FieldHandler(
                h.ワンダールーム_tick_global_field,
                subject_spec="source:self",
                priority=140,
            ),
        },
    ),

    # ===== サイドフィールド (SideField) =====
    "リフレクター": FieldData(
        turn_extension_item="ひかりのねんど",
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.FieldHandler(
                h.リフレクター_reduce_damage,
                subject_spec="defender:self",
            ),
            Event.ON_TURN_END: h.FieldHandler(
                h.リフレクター_tick_side_field,
                subject_spec="source:self",
                priority=130,
            ),
        },
    ),
    "ひかりのかべ": FieldData(
        turn_extension_item="ひかりのねんど",
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.FieldHandler(
                h.ひかりのかべ_reduce_damage,
                subject_spec="defender:self",
            ),
            Event.ON_TURN_END: h.FieldHandler(
                h.ひかりのかべ_tick_side_field,
                subject_spec="source:self",
                priority=130,
            ),
        },
    ),
    "オーロラベール": FieldData(
        turn_extension_item="ひかりのねんど",
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.FieldHandler(
                h.オーロラベール_reduce_damage,
                subject_spec="defender:self",
            ),
            Event.ON_TURN_END: h.FieldHandler(
                h.オーロラベール_tick_side_field,
                subject_spec="source:self",
                priority=130,
            ),
        },
    ),
    "しんぴのまもり": FieldData(
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.FieldHandler(
                h.しんぴのまもり_prevent_ailment,
                subject_spec="target:self",
            ),
            Event.ON_BEFORE_APPLY_VOLATILE: h.FieldHandler(
                h.しんぴのまもり_prevent_confusion,
                subject_spec="target:self",
            ),
            Event.ON_TURN_END: h.FieldHandler(
                h.しんぴのまもり_tick_side_field,
                subject_spec="source:self",
                priority=10,
            ),
        },
    ),
    "しろいきり": FieldData(
        handlers={
            Event.ON_BEFORE_MODIFY_STAT: h.FieldHandler(
                h.しろいきり_prevent_stat_drop,
                subject_spec="target:self",
            ),
            Event.ON_TURN_END: h.FieldHandler(
                h.しろいきり_tick_side_field,
                subject_spec="source:self",
                priority=130,
            ),
        },
    ),
    "おいかぜ": FieldData(
        handlers={
            DomainEvent.ON_CALC_SPEED: h.FieldHandler(
                h.おいかぜ_speed_boost,
                subject_spec="source:self",
            ),
            Event.ON_TURN_END: h.FieldHandler(
                h.おいかぜ_tick_side_field,
                subject_spec="source:self",
                priority=130,
            ),
        },
    ),
    "ねがいごと": FieldData(
        handlers={
            Event.ON_TURN_END: h.FieldHandler(
                h.ねがいごと_tick_side_field,
                subject_spec="source:self",
                priority=50,
            ),
            Event.ON_FIELD_DEACTIVATE: h.FieldHandler(
                h.ねがいごと_heal,
                subject_spec="source:self",
            ),
        },
    ),
    "まきびし": FieldData(
        handlers={
            Event.ON_SWITCH_IN: h.FieldHandler(
                h.まきびし_damage,
                subject_spec="source:self",
            ),
        },
    ),
    "どくびし": FieldData(
        handlers={
            Event.ON_SWITCH_IN: h.FieldHandler(
                h.どくびし_poison,
                subject_spec="source:self",
            ),
        },
    ),
    "ステルスロック": FieldData(
        handlers={
            Event.ON_SWITCH_IN: h.FieldHandler(
                h.ステルスロック_damage,
                subject_spec="source:self",
            ),
        },
    ),
    "ねばねばネット": FieldData(
        handlers={
            Event.ON_SWITCH_IN: h.FieldHandler(
                h.ねばねばネット_speed_drop,
                subject_spec="source:self",
            ),
        },
    ),
}


common_setup()
