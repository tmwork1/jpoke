from jpoke.core.event import Event, Handler, HandlerReturn
from .models import FieldData
from jpoke.handlers import common, field as h


FIELDS: dict[str, FieldData] = {
    "": FieldData(),
    # ===== 天候 (Weather) =====
    "はれ": FieldData(
        turn_extension_item="あついいわ",
        handlers={
            Event.ON_CALC_POWER_MODIFIER: Handler(
                h.はれ_power_modifier,
                subject_spec="attacker:self",
                log="never",
            ),
            Event.ON_CALC_ACCURACY: Handler(
                h.はれ_accuracy,
                subject_spec="attacker:self",
                log="never",
            ),
        },
    ),
    "あめ": FieldData(
        turn_extension_item="しめったいわ",
        handlers={
            Event.ON_CALC_POWER_MODIFIER: Handler(
                h.あめ_power_modifier,
                subject_spec="attacker:self",
                log="never",
            ),
            Event.ON_CALC_ACCURACY: Handler(
                h.あめ_accuracy,
                subject_spec="attacker:self",
                log="never",
            ),
        },
    ),
    "すなあらし": FieldData(
        turn_extension_item="さらさらいわ",
        handlers={
            Event.ON_TURN_END_2: Handler(
                h.すなあらし_apply_damage,
                subject_spec="target:self",
                log_text="すなあらしダメージ",
            ),
            Event.ON_CALC_DEF_TYPE_MODIFIER: Handler(
                h.すなあらし_spdef_boost,
                subject_spec="defender:self",
                log="never",
            ),
        },
    ),
    "ゆき": FieldData(
        turn_extension_item="つめたいいわ",
        handlers={
            Event.ON_CALC_DEF_TYPE_MODIFIER: Handler(
                h.ゆき_def_boost,
                subject_spec="defender:self",
                log="never",
            ),
            Event.ON_CALC_ACCURACY: Handler(
                h.ゆき_accuracy,
                subject_spec="attacker:self",
                log="never",
            ),
        },
    ),
    # ===== 地形 (Terrain) =====
    "エレキフィールド": FieldData(
        turn_extension_item="グランドコート",
        handlers={
            Event.ON_CALC_POWER_MODIFIER: Handler(
                h.エレキフィールド_power_modifier,
                subject_spec="attacker:self",
                log="never",
            ),
            Event.ON_BEFORE_APPLY_AILMENT: Handler(
                h.エレキフィールド_prevent_sleep,
                subject_spec="target:self",
                log="on_success",
            ),
            Event.ON_SWITCH_IN: Handler(
                h.エレキフィールド_cure_sleep,
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
                log="never",
            ),
            Event.ON_TURN_END_2: Handler(
                h.グラスフィールド_heal,
                subject_spec="target:self",
                log_text="グラスフィールド回復",
            ),
        },
    ),
    "サイコフィールド": FieldData(
        turn_extension_item="グランドコート",
        handlers={
            Event.ON_CALC_POWER_MODIFIER: Handler(
                h.サイコフィールド_power_modifier,
                subject_spec="attacker:self",
                log="never",
            ),
            Event.ON_CHECK_PRIORITY_VALID: Handler(
                h.サイコフィールド_block_priority,
                subject_spec="target:self",
                log="never",
            ),
        },
    ),
    "ミストフィールド": FieldData(
        turn_extension_item="グランドコート",
        handlers={
            Event.ON_CALC_POWER_MODIFIER: Handler(
                h.ミストフィールド_power_modifier,
                subject_spec="defender:self",
                log="never",
            ),
            Event.ON_BEFORE_APPLY_AILMENT: Handler(
                h.ミストフィールド_prevent_ailment,
                subject_spec="target:self",
                log="on_success",
            ),
        },
    ),
    # ===== グローバルフィールド (GlobalField) =====
    "じゅうりょく": FieldData(
        handlers={
            Event.ON_CALC_ACCURACY: Handler(
                h.じゅうりょく_accuracy,
                subject_spec="source:self",
                log="never",
            ),
            Event.ON_CHECK_FLOATING: Handler(
                h.じゅうりょく_grounded,
                subject_spec="source:self",
                log="never",
            ),
        },
    ),
    "トリックルーム": FieldData(
        handlers={
            Event.ON_CALC_ACTION_SPEED: Handler(
                h.トリックルーム_reverse_speed,
                subject_spec="source:self",
                log="never",
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
                log="never",
            ),
        },
    ),
    "ひかりのかべ": FieldData(
        turn_extension_item="ひかりのねんど",
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: Handler(
                h.ひかりのかべ_reduce_damage,
                subject_spec="defender:self",
                log="never",
            ),
        },
    ),
    "しんぴのまもり": FieldData(
        turn_extension_item="ひかりのねんど",
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: Handler(
                h.しんぴのまもり_prevent_ailment,
                subject_spec="target:self",
                log="on_success",
            ),
        },
    ),
    "おいかぜ": FieldData(
        handlers={
            Event.ON_CALC_SPEED: Handler(
                h.おいかぜ_speed_boost,
                subject_spec="source:self",
                log="never",
            ),
        },
    ),
    "まきびし": FieldData(
        handlers={
            Event.ON_SWITCH_IN: Handler(
                h.まきびし_damage,
                subject_spec="target:self",
                log_text="まきびしダメージ",
            ),
        },
    ),
    "どくびし": FieldData(
        handlers={
            Event.ON_SWITCH_IN: Handler(
                h.どくびし_poison,
                subject_spec="target:self",
                log_text="どくびし",
            ),
        },
    ),
    "ステルスロック": FieldData(
        handlers={
            Event.ON_SWITCH_IN: Handler(
                h.ステルスロック_damage,
                subject_spec="target:self",
                log_text="ステルスロック",
            ),
        },
    ),
    "ねばねばネット": FieldData(
        handlers={
            Event.ON_SWITCH_IN: Handler(
                h.ねばねばネット_speed_drop,
                subject_spec="target:self",
                log_text="ねばねばネット",
            ),
        },
    ),
}
