from functools import partial

from jpoke.enums import DomainEvent, Event
from jpoke.core import Handler, HandlerReturn
from jpoke.handlers import common, field as h
from .models import FieldData


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
            Event.ON_TURN_END_1: h.FieldHandler(
                h.tick_weather,
                priority=10,
                subject_spec="source:self",
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
            Event.ON_TURN_END_1: h.FieldHandler(
                h.tick_weather,
                priority=10,
                subject_spec="source:self",
            ),
        },
    ),
    "すなあらし": FieldData(
        turn_extension_item="さらさらいわ",
        handlers={
            Event.ON_TURN_END_1: h.FieldHandler(
                h.すなあらし_turn_end,
                priority=10,
                subject_spec="source:self",
            ),
            Event.ON_CALC_DEF_MODIFIER: h.FieldHandler(
                h.すなあらし_spdef_boost,
                subject_spec="defender:self",
            ),
        },
    ),
    "ゆき": FieldData(
        turn_extension_item="つめたいいわ",
        handlers={
            Event.ON_CALC_DEF_MODIFIER: h.FieldHandler(
                h.ゆき_def_boost,
                subject_spec="defender:self",
            ),
            Event.ON_TURN_END_1: h.FieldHandler(
                h.tick_weather,
                priority=10,
                subject_spec="source:self",
            ), },
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
            Event.ON_CHECK_MOVE: h.FieldHandler(
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
            Event.ON_CHECK_MOVE: h.FieldHandler(
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
            Event.ON_TURN_END_4: h.FieldHandler(
                h.tick_terrain,
                priority=20,
                subject_spec="source:self",
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
            Event.ON_TURN_END_2: h.FieldHandler(
                h.グラスフィールド_heal,
                subject_spec="source:self",
            ),
            Event.ON_TURN_END_4: h.FieldHandler(
                h.tick_terrain,
                priority=20,
                subject_spec="source:self",
            ),
        },
    ),
    "サイコフィールド": FieldData(
        turn_extension_item="グランドコート",
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.FieldHandler(
                h.サイコフィールド_power_modifier,
                subject_spec="attacker:self",
            ),
            Event.ON_CHECK_MOVE: h.FieldHandler(
                h.サイコフィールド_block_priority,
                priority=100,
                subject_spec="defender:self",
            ),
            Event.ON_TURN_END_4: h.FieldHandler(
                h.tick_terrain,
                priority=20,
                subject_spec="source:self",
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
                h.ミストフィールド_prevent_volatile,
                subject_spec="target:self",
            ),
            Event.ON_TURN_END_4: h.FieldHandler(
                h.tick_terrain,
                priority=20,
                subject_spec="source:self",
            ),
        },
    ),
    # ===== グローバルフィールド (GlobalField) =====
    "じゅうりょく": FieldData(
        handlers={
            Event.ON_MODIFY_ACCURACY: h.FieldHandler(
                h.じゅうりょく_accuracy,
                subject_spec="source:self",
            ),
            Event.ON_CHECK_FLOATING: h.FieldHandler(
                h.じゅうりょく_grounded,
                subject_spec="source:self",
            ),
            Event.ON_TURN_END_4: h.FieldHandler(
                partial(h.tick_global_field, name="じゅうりょく"),
                priority=20,
                subject_spec="source:self",
            ),
        },
    ),
    "トリックルーム": FieldData(
        handlers={
            DomainEvent.ON_CHECK_SPEED_REVERSE: h.FieldHandler(
                h.トリックルーム_reverse_speed,
                subject_spec="source:self",
            ),
            Event.ON_TURN_END_4: h.FieldHandler(
                partial(h.tick_global_field, name="トリックルーム"),
                priority=20,
                subject_spec="source:self",
            ),
        },
    ),
    "マジックルーム": FieldData(
        handlers={
            Event.ON_CHECK_ITEM_ENABLED: h.FieldHandler(
                h.マジックルーム_check_item_enabled,
                subject_spec="source:self",
            ),
            Event.ON_FIELD_DEACTIVATE: h.FieldHandler(
                h.マジックルーム_on_field_deactivate,
                subject_spec="source:self",
            ),
            Event.ON_TURN_END_4: h.FieldHandler(
                partial(h.tick_global_field, name="マジックルーム"),
                priority=20,
                subject_spec="source:self",
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
            Event.ON_TURN_END_4: h.FieldHandler(
                partial(h.tick_global_field, name="ワンダールーム"),
                priority=20,
                subject_spec="source:self",
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
            Event.ON_TURN_END_4: h.FieldHandler(
                partial(h.tick_side_field, name="リフレクター"),
                priority=10,
                subject_spec="source:self",
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
            Event.ON_TURN_END_4: h.FieldHandler(
                partial(h.tick_side_field, name="ひかりのかべ"),
                priority=10,
                subject_spec="source:self",
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
            Event.ON_TURN_END_4: h.FieldHandler(
                partial(h.tick_side_field, name="オーロラベール"),
                priority=10,
                subject_spec="source:self",
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
                h.しんぴのまもり_prevent_volatile,
                subject_spec="target:self",
            ),
            Event.ON_TURN_END_4: h.FieldHandler(
                partial(h.tick_side_field, name="しんぴのまもり"),
                priority=10,
                subject_spec="source:self",
            ),
        },
    ),
    "しろいきり": FieldData(
        handlers={
            Event.ON_BEFORE_MODIFY_STAT: h.FieldHandler(
                h.しろいきり_prevent_stat_drop,
                subject_spec="target:self",
            ),
            Event.ON_TURN_END_4: h.FieldHandler(
                partial(h.tick_side_field, name="しろいきり"),
                priority=10,
                subject_spec="source:self",
            ),
        },
    ),
    "おいかぜ": FieldData(
        handlers={
            DomainEvent.ON_CALC_SPEED: h.FieldHandler(
                h.おいかぜ_speed_boost,
                subject_spec="source:self",
            ),
            Event.ON_TURN_END_4: h.FieldHandler(
                partial(h.tick_side_field, name="おいかぜ"),
                priority=10,
                subject_spec="source:self",
            ),
        },
    ),
    "ねがいごと": FieldData(
        handlers={
            Event.ON_TURN_END_2: h.FieldHandler(
                h.ねがいごと_heal,
                priority=20,
                subject_spec="target:self",
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
