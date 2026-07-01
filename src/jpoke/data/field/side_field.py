from jpoke.enums import DomainEvent, Event
from jpoke.handlers import field as h
from ..models import FieldData

SIDE_FIELD: dict[str, FieldData] = {
    "リフレクター": FieldData(
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
    "いやしのねがい": FieldData(
        handlers={
            Event.ON_SWITCH_IN: h.FieldHandler(
                h.いやしのねがい_heal_on_switch_in,
                subject_spec="source:self",
                priority=100,
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
        max_count=3,
        handlers={
            Event.ON_SWITCH_IN: h.FieldHandler(
                h.まきびし_damage,
                subject_spec="source:self",
            ),
        },
    ),
    "どくびし": FieldData(
        max_count=2,
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
