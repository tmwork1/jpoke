from jpoke.enums import Event
from jpoke.handlers import field as h
from ...handlers.models import FieldData

TERRAIN: dict[str, FieldData] = {
    "エレキフィールド": FieldData(
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
}
