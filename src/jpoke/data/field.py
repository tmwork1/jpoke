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
                lambda btl, ctx, v: hdl.reduce_global_field_count(btl, ctx, v, "weather"),
            ),
        },
    ),
    "あめ": FieldData(
        turn_extension_item="しめったいわ",
        handlers={
            Event.ON_TURN_END_1: Handler(
                lambda btl, ctx, v: hdl.reduce_global_field_count(btl, ctx, v, "weather"),
            ),
        },
    ),
    "すなあらし": FieldData(
        turn_extension_item="さらさらいわ",
        handlers={
            Event.ON_TURN_END_1: Handler(
                lambda btl, ctx, v: hdl.reduce_global_field_count(btl, ctx, v, "weather"),
            ),
            Event.ON_TURN_END_2: Handler(hdl.すなあらし_ダメージ)
        },
    ),
    "ゆき": FieldData(
        turn_extension_item="つめたいいわ",
        handlers={
            Event.ON_TURN_END_1: Handler(
                lambda btl, ctx, v: hdl.reduce_global_field_count(btl, ctx, v, "weather"),
            ),
        },
    ),
    "エレキフィールド": FieldData(
        turn_extension_item="グランドコート",
        handlers={
            Event.ON_TURN_END_5: Handler(
                lambda btl, ctx, v: hdl.reduce_global_field_count(btl, ctx, v, "terrain"),
            )
        },
    ),
    "グラスフィールド": FieldData(
        turn_extension_item="グランドコート",
        handlers={
            Event.ON_TURN_END_3: Handler(
                lambda btl, ctx, v: common.modify_hp(btl, ctx.target, r=1/16)
            ),
            Event.ON_TURN_END_5: Handler(
                lambda btl, ctx, v: hdl.reduce_global_field_count(btl, ctx, v, "terrain"),
            )
        },
    ),
    "サイコフィールド": FieldData(
        turn_extension_item="グランドコート",
        handlers={
            Event.ON_TURN_END_5: Handler(
                lambda btl, ctx, v: hdl.reduce_global_field_count(btl, ctx, v, "terrain"),
            )
        },
    ),
    "ミストフィールド": FieldData(
        turn_extension_item="グランドコート",
        handlers={
            Event.ON_TURN_END_5: Handler(
                lambda btl, ctx, v: hdl.reduce_global_field_count(btl, ctx, v, "terrain"),
            )
        },
    ),
    "じゅうりょく": FieldData(
        handlers={
            Event.ON_TURN_END_5: Handler(
                lambda btl, ctx, v: hdl.reduce_global_field_count(btl, ctx, v, "gravity"),
            ),
        },
    ),
    "トリックルーム": FieldData(
        handlers={
            Event.ON_TURN_END_5: Handler(
                lambda btl, ctx, v: hdl.reduce_global_field_count(btl, ctx, v, "trickroom"),
            ),
        },
    ),

    # Side fields
    "リフレクター": FieldData(
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: Handler(
                hdl.リフレクター,
                role="defender",
            ),
            Event.ON_TURN_END_5: Handler(
                lambda btl, ctx, v: hdl.reduce_side_field_count(btl, ctx, v, "reflector"),
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
