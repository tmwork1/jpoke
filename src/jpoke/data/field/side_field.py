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
                allow_fainted_subject=True,  # フィールドcountdownはsource(occupant)の生死に関わらず毎ターン進行させる
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
                allow_fainted_subject=True,  # フィールドcountdownはsource(occupant)の生死に関わらず毎ターン進行させる
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
                allow_fainted_subject=True,  # フィールドcountdownはsource(occupant)の生死に関わらず毎ターン進行させる
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
                allow_fainted_subject=True,  # フィールドcountdownはsource(occupant)の生死に関わらず毎ターン進行させる
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
                allow_fainted_subject=True,  # フィールドcountdownはsource(occupant)の生死に関わらず毎ターン進行させる
            ),
        },
    ),
    "いやしのねがい": FieldData(
        handlers={
            Event.ON_SWITCH_IN: h.FieldHandler(
                h.いやしのねがい_heal,
                subject_spec="source:self",
                # まきびし・ステルスロック等の設置技（デフォルトpriority=100）より必ず先に
                # 発動させるため90を明示する。同一priority同士のタイブレークはハンドラ
                # 登録順（＝設置が先だった技が先に発動）に依存するため、設置技より後に
                # 設置された場合でも回復が設置技のダメージより後回しになってしまっていた
                # （.internal/spec/fields/みかづきのまい.md「設置技との順序」参照。
                # fuzzログ seed=1879で発見）。
                priority=90,
            ),
        },
    ),
    "みかづきのまい": FieldData(
        handlers={
            Event.ON_SWITCH_IN: h.FieldHandler(
                h.みかづきのまい_heal,
                subject_spec="source:self",
                # いやしのねがいと同じ理由でpriority=90（設置技より先に発動させる）。
                priority=90,
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
                allow_fainted_subject=True,  # フィールドcountdownはsource(occupant)の生死に関わらず毎ターン進行させる
            ),
        },
    ),
    "ねがいごと": FieldData(
        handlers={
            Event.ON_TURN_END: h.FieldHandler(
                h.ねがいごと_tick,
                subject_spec="source:self",
                priority=50,
                allow_fainted_subject=True,  # フィールドcountdownはsource(occupant)の生死に関わらず毎ターン進行させる
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
                allow_fainted_subject=True,  # フィールドcountdownはsource(occupant)の生死に関わらず毎ターン進行させる
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
                allow_fainted_subject=True,  # フィールドcountdownはsource(occupant)の生死に関わらず毎ターン進行させる
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
