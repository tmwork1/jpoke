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
            Event.ON_CALC_POWER_MODIFIER: Handler(
                h.はれ_power_modifier,
                subject_spec="attacker:self",
            ),
            Event.ON_BEFORE_APPLY_AILMENT: Handler(
                h.はれ_prevent_freeze,
                subject_spec="target:self",
            ),
            Event.ON_TURN_END_1: Handler(
                h.tick_weather,
                priority=10,
                subject_spec="source:self",
            ),
        },
    ),
    "あめ": FieldData(
        turn_extension_item="しめったいわ",
        handlers={
            Event.ON_CALC_POWER_MODIFIER: Handler(
                h.あめ_power_modifier,
                subject_spec="attacker:self",
            ),
            Event.ON_TURN_END_1: Handler(
                h.tick_weather,
                priority=10,
                subject_spec="source:self",
            ),
        },
    ),
    "すなあらし": FieldData(
        turn_extension_item="さらさらいわ",
        handlers={
            Event.ON_TURN_END_1: Handler(
                h.すなあらし_turn_end,
                priority=10,
                subject_spec="source:self",
            ),
            Event.ON_CALC_DEF_MODIFIER: Handler(
                h.すなあらし_spdef_boost,
                subject_spec="defender:self",
            ),
        },
    ),
    "ゆき": FieldData(
        turn_extension_item="つめたいいわ",
        handlers={
            Event.ON_CALC_DEF_MODIFIER: Handler(
                h.ゆき_def_boost,
                subject_spec="defender:self",
            ),
            Event.ON_TURN_END_1: Handler(
                h.tick_weather,
                priority=10,
                subject_spec="source:self",
            ), },
    ),
    # ===== 地形 (Terrain) =====
    "エレキフィールド": FieldData(
        turn_extension_item="グランドコート",
        handlers={
            Event.ON_CALC_POWER_MODIFIER: Handler(
                h.エレキフィールド_power_modifier,
                subject_spec="attacker:self",
            ),
            Event.ON_BEFORE_APPLY_AILMENT: Handler(
                h.エレキフィールド_prevent_sleep,
                subject_spec="target:self",
            ),
            Event.ON_BEFORE_APPLY_VOLATILE: Handler(
                h.エレキフィールド_prevent_nemuke,
                subject_spec="target:self",
            ),
            Event.ON_TURN_END_4: Handler(
                h.tick_terrain,
                priority=20,
                subject_spec="source:self",
            ),
        },
    ),
    "グラスフィールド": FieldData(
        turn_extension_item="グランドコート",
        handlers={
            Event.ON_CALC_POWER_MODIFIER: Handler(
                h.グラスフィールド_power_modifier,
                subject_spec="attacker:self",
            ),
            Event.ON_TURN_END_2: Handler(
                h.グラスフィールド_heal,
                subject_spec="source:self",
            ),
            Event.ON_TURN_END_4: Handler(
                h.tick_terrain,
                priority=20,
                subject_spec="source:self",
            ),
        },
    ),
    "サイコフィールド": FieldData(
        turn_extension_item="グランドコート",
        handlers={
            Event.ON_CALC_POWER_MODIFIER: Handler(
                h.サイコフィールド_power_modifier,
                subject_spec="attacker:self",
            ),
            Event.ON_CHECK_MOVE: Handler(
                h.サイコフィールド_block_priority,
                priority=100,
                subject_spec="defender:self",
            ),
            Event.ON_TURN_END_4: Handler(
                h.tick_terrain,
                priority=20,
                subject_spec="source:self",
            ),
        },
    ),
    "ミストフィールド": FieldData(
        turn_extension_item="グランドコート",
        handlers={
            Event.ON_CALC_POWER_MODIFIER: Handler(
                h.ミストフィールド_power_modifier,
                subject_spec="defender:self",
            ),
            Event.ON_BEFORE_APPLY_AILMENT: Handler(
                h.ミストフィールド_prevent_ailment,
                subject_spec="target:self",
            ),
            Event.ON_BEFORE_APPLY_VOLATILE: Handler(
                h.ミストフィールド_prevent_volatile,
                subject_spec="target:self",
            ),
            Event.ON_TURN_END_4: Handler(
                h.tick_terrain,
                priority=20,
                subject_spec="source:self",
            ),
        },
    ),
    # ===== グローバルフィールド (GlobalField) =====
    "じゅうりょく": FieldData(
        handlers={
            Event.ON_MODIFY_ACCURACY: Handler(
                h.じゅうりょく_accuracy,
                subject_spec="source:self",
            ),
            Event.ON_CHECK_FLOATING: Handler(
                h.じゅうりょく_grounded,
                subject_spec="source:self",
            ),
            Event.ON_TURN_END_4: Handler(
                partial(h.tick_global_field, name="じゅうりょく"),
                priority=20,
                subject_spec="source:self",
            ),
        },
    ),
    "トリックルーム": FieldData(
        handlers={
            DomainEvent.ON_CHECK_SPEED_REVERSE: Handler(
                h.トリックルーム_reverse_speed,
                subject_spec="source:self",
            ),
            Event.ON_TURN_END_4: Handler(
                partial(h.tick_global_field, name="トリックルーム"),
                priority=20,
                subject_spec="source:self",
            ),
        },
    ),

    # ===== サイドフィールド (SideField) =====
    "リフレクター": FieldData(
        turn_extension_item="ひかりのねんど",
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: Handler(
                h.リフレクター_reduce_damage,
                subject_spec="defender:self",
            ),
            Event.ON_TURN_END_4: Handler(
                partial(h.tick_side_field, name="リフレクター"),
                priority=10,
                subject_spec="source:self",
            ),
        },
    ),
    "ひかりのかべ": FieldData(
        turn_extension_item="ひかりのねんど",
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: Handler(
                h.ひかりのかべ_reduce_damage,
                subject_spec="defender:self",
            ),
            Event.ON_TURN_END_4: Handler(
                partial(h.tick_side_field, name="ひかりのかべ"),
                priority=10,
                subject_spec="source:self",
            ),
        },
    ),
    "オーロラベール": FieldData(
        turn_extension_item="ひかりのねんど",
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: Handler(
                h.オーロラベール_reduce_damage,
                subject_spec="defender:self",
            ),
            Event.ON_TURN_END_4: Handler(
                partial(h.tick_side_field, name="オーロラベール"),
                priority=10,
                subject_spec="source:self",
            ),
        },
    ),
    "しんぴのまもり": FieldData(
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: Handler(
                h.しんぴのまもり_prevent_ailment,
                subject_spec="target:self",
            ),
            Event.ON_BEFORE_APPLY_VOLATILE: Handler(
                h.しんぴのまもり_prevent_volatile,
                subject_spec="target:self",
            ),
            Event.ON_TURN_END_4: Handler(
                partial(h.tick_side_field, name="しんぴのまもり"),
                priority=10,
                subject_spec="source:self",
            ),
        },
    ),
    "しろいきり": FieldData(
        handlers={
            Event.ON_BEFORE_MODIFY_STAT: Handler(
                h.しろいきり_prevent_stat_drop,
                subject_spec="target:self",
            ),
            Event.ON_TURN_END_4: Handler(
                partial(h.tick_side_field, name="しろいきり"),
                priority=10,
                subject_spec="source:self",
            ),
        },
    ),
    "おいかぜ": FieldData(
        handlers={
            DomainEvent.ON_CALC_SPEED: Handler(
                h.おいかぜ_speed_boost,
                subject_spec="source:self",
            ),
            Event.ON_TURN_END_4: Handler(
                partial(h.tick_side_field, name="おいかぜ"),
                priority=10,
                subject_spec="source:self",
            ),
        },
    ),
    "ねがいごと": FieldData(
        handlers={
            Event.ON_TURN_END_2: Handler(
                h.ねがいごと_heal,
                priority=20,
                subject_spec="target:self",
            ),
        },
    ),
    "まきびし": FieldData(
        handlers={
            Event.ON_SWITCH_IN: Handler(
                h.まきびし_damage,
                subject_spec="source:self",
            ),
        },
    ),
    "どくびし": FieldData(
        handlers={
            Event.ON_SWITCH_IN: Handler(
                h.どくびし_poison,
                subject_spec="source:self",
            ),
        },
    ),
    "ステルスロック": FieldData(
        handlers={
            Event.ON_SWITCH_IN: Handler(
                h.ステルスロック_damage,
                subject_spec="source:self",
            ),
        },
    ),
    "ねばねばネット": FieldData(
        handlers={
            Event.ON_SWITCH_IN: Handler(
                h.ねばねばネット_speed_drop,
                subject_spec="source:self",
            ),
        },
    ),
}


common_setup()
