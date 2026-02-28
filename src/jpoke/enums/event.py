"""
イベントのEnum定義
イベントの処理順の詳細は docs/spec/turn_flow.md を参照
"""

from enum import Enum, auto


class DomainEvent(Enum):
    ON_CALC_SPEED = auto()
    ON_CHECK_SPEED_REVERSE = auto()
    ON_MODIFY_MOVE_PRIORITY = auto()


class Event(Enum):
    """バトルイベントの種類

    イベントは大きく3つのカテゴリに分類される：
    - アクション系: ON_BEFORE_ACTION, ON_SWITCH_IN など
    - チェック系: ON_CHECK_PP_CONSUMED, ON_CHECK_FLOATING など
    - 計算系: ON_CALC_ACCURACY など

    行動順に関与するものは enums/domain.py に分離されている。
    """
    # アクション系イベント（emit/handlerの主な参照先）
    ON_SWITCH_IN = auto()
    ON_SWITCH_OUT = auto()

    ON_MODIFY_COMMAND_OPTIONS = auto()
    ON_BEFORE_ACTION = auto()
    ON_BEFORE_MOVE = auto()
    ON_MODIFY_MOVE = auto()
    ON_PREPARE_MOVE = auto()

    ON_TRY_ACTION = auto()
    ON_CONSUME_PP = auto()
    ON_TRY_MOVE = auto()
    ON_TRY_IMMUNE = auto()
    ON_CHECK_SUBSTITUTE = auto()
    ON_CHECK_PROTECT = auto()
    ON_PROTECT_SUCCESS = auto()
    ON_CHECK_INVULNERABLE = auto()
    ON_CHECK_REFLECT = auto()
    ON_HIT = auto()
    ON_PAY_HP = auto()
    ON_MODIFY_DAMAGE = auto()
    ON_BEFORE_DAMAGE_APPLY = auto()
    ON_MOVE_SECONDARY = auto()
    ON_DAMAGE = auto()

    # ターン終了イベント
    ON_TURN_END_1 = auto()
    ON_TURN_END_2 = auto()
    ON_TURN_END_3 = auto()
    ON_TURN_END_4 = auto()
    ON_TURN_END_5 = auto()
    ON_TURN_END_6 = auto()

    ON_MODIFY_STAT = auto()
    ON_END = auto()  # 未使用

    # 状態異常・能力変化前イベント
    ON_BEFORE_HEAL = auto()
    ON_BEFORE_APPLY_AILMENT = auto()
    ON_BEFORE_APPLY_VOLATILE = auto()
    ON_BEFORE_MODIFY_STAT = auto()

    # チェック系イベント
    ON_CHECK_PP_CONSUMED = auto()
    ON_CHECK_DURATION = auto()
    ON_CHECK_FLOATING = auto()
    ON_CHECK_TRAPPED = auto()
    ON_CHECK_NERVOUS = auto()
    ON_CHECK_MOVE_TYPE = auto()
    ON_CHECK_MOVE_CATEGORY = auto()
    ON_CHECK_HIT_SUBSTITUTE = auto()
    ON_CHECK_CONTACT = auto()

    # 計算系イベント
    ON_MODIFY_ACCURACY = auto()
    ON_MODIFY_BIND_DAMAGE_RATIO = auto()
    ON_CALC_CRITICAL_RANK = auto()
    ON_CALC_POWER_MODIFIER = auto()
    ON_CALC_ATK_MODIFIER = auto()
    ON_CALC_DEF_MODIFIER = auto()
    ON_CALC_ATK_TYPE_MODIFIER = auto()
    ON_CALC_DEF_TYPE_MODIFIER = auto()
    ON_CALC_BURN_MODIFIER = auto()
    ON_CALC_DAMAGE_MODIFIER = auto()
    ON_CALC_PROTECT_MODIFIER = auto()
    ON_CALC_FINAL_DAMAGE_MODIFIER = auto()
    ON_CHECK_DEF_ABILITY = auto()
    ON_CALC_DRAIN = auto()
