from jpoke.enums import Event
from jpoke.handlers import field as h
from ..models import FieldData

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


WEATHER: dict[str, FieldData] = {
    "はれ": FieldData(
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
        handlers={
            Event.ON_CALC_DEF_MODIFIER: h.FieldHandler(
                h.すなあらし_D_boost,
                subject_spec="defender:self",
            ),
            Event.ON_TURN_END: [
                h.FieldHandler(
                    h.tick_weather,
                    subject_spec="source:self",
                    priority=10,
                ),
                h.FieldHandler(
                    h.すなあらし_turn_end,
                    subject_spec="source:self",
                    priority=20,
                ),
            ],
        },
    ),
    "ゆき": FieldData(
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
}
