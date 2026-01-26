from jpoke.core.event import Event, Handler
from .models import FieldData
from jpoke.handlers import common, field as hdl


FIELDS: dict[str, FieldData] = {
    "": FieldData(),
    "はれ": FieldData(
        turn_extension_item="あついいわ",
        handlers={
        },
    ),
    "あめ": FieldData(
        turn_extension_item="しめったいわ",
        handlers={
        },
    ),
    "すなあらし": FieldData(
        turn_extension_item="さらさらいわ",
        handlers={
            Event.ON_TURN_END_1: Handler(
                lambda btl, ctx, v: btl.weather.tick()
            ),
            Event.ON_TURN_END_2: Handler(hdl.apply_sandstorm_damage)
        },
    ),
    "ゆき": FieldData(
        turn_extension_item="つめたいいわ",
        handlers={
        },
    ),
    "エレキフィールド": FieldData(
        turn_extension_item="グランドコート",
        handlers={
        },
    ),
    "グラスフィールド": FieldData(
        turn_extension_item="グランドコート",
        handlers={
            Event.ON_TURN_END_3: Handler(
                lambda btl, ctx, v: common.modify_hp(btl, ctx.source, r=1/16),
                role="source"
            ),
            Event.ON_TURN_END_5: Handler(
            )
        },
    ),
    "サイコフィールド": FieldData(
        turn_extension_item="グランドコート",
        handlers={
            Event.ON_TURN_END_5: Handler(
            )
        },
    ),
    "ミストフィールド": FieldData(
        turn_extension_item="グランドコート",
        handlers={
            Event.ON_TURN_END_5: Handler(
            )
        },
    ),
    "じゅうりょく": FieldData(
        handlers={
            Event.ON_TURN_END_5: Handler(
            ),
        },
    ),
    "トリックルーム": FieldData(
        handlers={
            Event.ON_TURN_END_5: Handler(
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
