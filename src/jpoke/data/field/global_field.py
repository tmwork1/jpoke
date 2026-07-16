from jpoke.enums import DomainEvent, Event
from jpoke.handlers import field as h
from ..models import FieldData

GLOBAL_FIELD: dict[str, FieldData] = {
    "じゅうりょく": FieldData(
        handlers={
            Event.ON_FIELD_ACTIVATE: h.FieldHandler(
                h.じゅうりょく_remove_volatiles,
                subject_spec="source:self",
            ),
            Event.ON_MODIFY_ACCURACY: h.FieldHandler(
                h.じゅうりょく_modify_accuracy,
                subject_spec="attacker:self",
            ),
            Event.ON_CHECK_FLOATING: h.FieldHandler(
                h.じゅうりょく_grounded,
                subject_spec="source:self",
            ),
            Event.ON_TURN_END: h.FieldHandler(
                h.じゅうりょく_tick,
                subject_spec="source:self",
                priority=140,
                allow_fainted_subject=True,  # フィールドcountdownはsource(occupant)の生死に関わらず毎ターン進行させる
            ),
        },
    ),
    "トリックルーム": FieldData(
        handlers={
            DomainEvent.ON_CHECK_SPEED_REVERSE: h.FieldHandler(
                h.トリックルーム_reverse_spe,
                subject_spec="source:self",
            ),
            Event.ON_TURN_END: h.FieldHandler(
                h.トリックルーム_tick,
                subject_spec="source:self",
                priority=140,
                allow_fainted_subject=True,  # フィールドcountdownはsource(occupant)の生死に関わらず毎ターン進行させる
            ),
        },
    ),
    "フェアリーロック": FieldData(
        handlers={
            Event.ON_CHECK_TRAPPED: h.FieldHandler(
                h.フェアリーロック_check_trapped,
                subject_spec="source:self",
            ),
            Event.ON_TURN_END: h.FieldHandler(
                h.フェアリーロック_tick,
                subject_spec="source:self",
                priority=140,
                allow_fainted_subject=True,  # フィールドcountdownはsource(occupant)の生死に関わらず毎ターン進行させる
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
                h.マジックルーム_tick,
                subject_spec="source:self",
                priority=140,
                allow_fainted_subject=True,  # フィールドcountdownはsource(occupant)の生死に関わらず毎ターン進行させる
            ),
        },
    ),
    "ワンダールーム": FieldData(
        handlers={
            Event.ON_CALC_DEF_MODIFIER: h.FieldHandler(
                h.ワンダールーム_def_modifier,
                subject_spec="defender:self",
            ),
            Event.ON_TURN_END: h.FieldHandler(
                h.ワンダールーム_tick,
                subject_spec="source:self",
                priority=140,
                allow_fainted_subject=True,  # フィールドcountdownはsource(occupant)の生死に関わらず毎ターン進行させる
            ),
        },
    ),
}
