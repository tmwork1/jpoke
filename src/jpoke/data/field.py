from jpoke.core.event import Event, Handler, HandlerReturn
from .models import FieldData
from jpoke.handlers import common, field as h


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
            Event.ON_TURN_END_2: Handler(
                h.すなあらし_apply_damage,
                subject_spec="target:self",
                log_text="すなあらしダメージ",
            ),
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
        },
    ),
    "サイコフィールド": FieldData(
        turn_extension_item="グランドコート",
        handlers={
        },
    ),
    "ミストフィールド": FieldData(
        turn_extension_item="グランドコート",
        handlers={
        },
    ),
    "じゅうりょく": FieldData(
        handlers={
        },
    ),
    "トリックルーム": FieldData(
        handlers={
        },
    ),

    # Side fields
    "リフレクター": FieldData(
        handlers={
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
