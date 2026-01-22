from jpoke.core.event import Event, Handler
from .models import FieldData
from jpoke.handlers import common, field as hdl


FIELDS: dict[str, FieldData] = {
    "": FieldData(),

    # Global fields
    "はれ": FieldData(
        turn_extension_item="あついいわ",
        handlers={
            Event.ON_TURN_END_1: Handler(
                lambda b, c, v: hdl.reduce_global_field_count(b, c, v, "weather"),
            ),
        },
    ),
    "あめ": FieldData(
        turn_extension_item="しめったいわ",
        handlers={
            Event.ON_TURN_END_1: Handler(
                lambda b, c, v: hdl.reduce_global_field_count(b, c, v, "weather"),
            ),
        },
    ),
    "すなあらし": FieldData(
        turn_extension_item="さらさらいわ",
        handlers={
            Event.ON_TURN_END_1: Handler(
                lambda b, c, v: hdl.reduce_global_field_count(b, c, v, "weather"),
            ),
            Event.ON_TURN_END_2: Handler(
                lambda b, c, v: common.modify_hp(b, c, "self", r=-1/16),
            )
        },
    ),
    "ゆき": FieldData(
        turn_extension_item="つめたいいわ",
        handlers={
            Event.ON_TURN_END_1: Handler(
                lambda b, c, v: hdl.reduce_global_field_count(b, c, v, "weather"),
            ),
        },
    ),
    "エレキフィールド": FieldData(
        turn_extension_item="グランドコート",
        handlers={
            Event.ON_TURN_END_5: Handler(
                lambda b, c, v: hdl.reduce_global_field_count(b, c, v, "terrain"),
            )
        },
    ),
    "グラスフィールド": FieldData(
        turn_extension_item="グランドコート",
        handlers={
            Event.ON_TURN_END_3: Handler(
                lambda b, c, v: common.modify_hp(b, c, "self", r=1/16)
            ),
            Event.ON_TURN_END_5: Handler(
                lambda b, c, v: hdl.reduce_global_field_count(b, c, v, "terrain"),
            )
        },
    ),
    "サイコフィールド": FieldData(
        turn_extension_item="グランドコート",
        handlers={
            Event.ON_TURN_END_5: Handler(
                lambda b, c, v: hdl.reduce_global_field_count(b, c, v, "terrain"),
            )
        },
    ),
    "ミストフィールド": FieldData(
        turn_extension_item="グランドコート",
        handlers={
            Event.ON_TURN_END_5: Handler(
                lambda b, c, v: hdl.reduce_global_field_count(b, c, v, "terrain"),
            )
        },
    ),
    "じゅうりょく": FieldData(
        handlers={
            Event.ON_TURN_END_5: Handler(
                lambda b, c, v: hdl.reduce_global_field_count(b, c, v, "gravity"),
            ),
        },
    ),
    "トリックルーム": FieldData(
        handlers={
            Event.ON_TURN_END_5: Handler(
                lambda b, c, v: hdl.reduce_global_field_count(b, c, v, "trickroom"),
            ),
        },
    ),

    # Side fields
    "リフレクター": FieldData(
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: Handler(hdl.リフレクター, triggered_by="foe"),
            Event.ON_TURN_END_5: Handler(
                lambda b, c, v: hdl.reduce_side_field_count(b, c, v, "reflector"),
            ),
        },
    ),
    "ひかりのかべ": FieldData(
        handlers={
        },
    ),
    "しんぴのまもり": FieldData(
        handlers={
        },
    ),
    "しろいきり": FieldData(
        handlers={
        },
    ),
    "おいかぜ": FieldData(
        handlers={
        },
    ),
    "ねがいごと": FieldData(
        handlers={
        },
    ),
    "まきびし": FieldData(
        handlers={
        },
    ),
    "どくびし": FieldData(
        handlers={
        },
    ),
    "ステルスロック": FieldData(
        handlers={
        },
    ),
    "ねばねばネット": FieldData(
        handlers={
        },
    ),
}
