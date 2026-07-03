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
                h.リフレクター_tick,
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
                h.ひかりのかべ_tick,
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
                h.オーロラベール_tick,
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
                h.しんぴのまもり_tick,
                subject_spec="source:self",
                priority=130,
            ),
        },
    ),
    "しろいきり": FieldData(
        handlers={
            Event.ON_BEFORE_MODIFY_STAT: h.FieldHandler(
                h.しろいきり_prevent_stat_drop,
                subject_spec="target:self",
                priority=130,
            ),
            Event.ON_TURN_END: h.FieldHandler(
                h.しろいきり_tick,
                subject_spec="source:self",
                priority=130,
            ),
        },
    ),
    "いやしのねがい": FieldData(
        handlers={
            Event.ON_SWITCH_IN: h.FieldHandler(
                h.いやしのねがい_heal,
                subject_spec="source:self",
                priority=100,
            ),
        },
    ),
    "おいかぜ": FieldData(
        handlers={
            DomainEvent.ON_CALC_SPEED: h.FieldHandler(
                h.おいかぜ_boost_spe,
                subject_spec="source:self",
            ),
            Event.ON_TURN_END: h.FieldHandler(
                h.おいかぜ_tick,
                subject_spec="source:self",
                priority=130,
            ),
        },
    ),
    "ねがいごと": FieldData(
        handlers={
            Event.ON_TURN_END: h.FieldHandler(
                h.ねがいごと_tick,
                subject_spec="source:self",
                priority=50,
            ),
            Event.ON_FIELD_DEACTIVATE: h.FieldHandler(
                h.ねがいごと_heal,
                subject_spec="source:self",
            ),
        },
    ),
    "みらいよち": FieldData(
        handlers={
            Event.ON_TURN_END: h.FieldHandler(
                h.みらいよち_tick,
                subject_spec="source:self",
                priority=40,
            ),
            Event.ON_FIELD_DEACTIVATE: h.FieldHandler(
                h.みらいよち_damage,
                subject_spec="source:self",
            ),
        },
    ),
    "はめつのねがい": FieldData(
        handlers={
            Event.ON_TURN_END: h.FieldHandler(
                h.はめつのねがい_tick,
                subject_spec="source:self",
                priority=40,
            ),
            Event.ON_FIELD_DEACTIVATE: h.FieldHandler(
                h.はめつのねがい_damage,
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
                h.どくびし_apply_poison,
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
                h.ねばねばネット_reduce_spe,
                subject_spec="source:self",
            ),
        },
    ),
}
