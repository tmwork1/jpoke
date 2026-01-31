"""イベント関連のEnum定義"""
from enum import Enum, auto


class EventControl(Enum):
    """イベントハンドラの制御フラグ"""
    STOP_HANDLER = auto()
    STOP_EVENT = auto()


class Event(Enum):
    """バトルイベントの種類

    イベントは大きく3つのカテゴリに分類される：
    - アクション系: ON_BEFORE_ACTION, ON_SWITCH_IN など
    - チェック系: ON_CHECK_PP_CONSUMED, ON_CHECK_FLOATING など
    - 計算系: ON_CALC_SPEED, ON_CALC_ACCURACY など
    """
    # アクション系イベント
    ON_BEFORE_ACTION = auto()
    ON_SWITCH_IN = auto()
    ON_SWITCH_OUT = auto()
    ON_BEFORE_MOVE = auto()
    ON_TRY_ACTION = auto()
    ON_CONSUME_PP = auto()
    ON_TRY_MOVE = auto()
    ON_TRY_IMMUNE = auto()
    ON_HIT = auto()
    ON_PAY_HP = auto()
    ON_MODIFY_DAMAGE = auto()
    ON_MOVE_SECONDARY = auto()
    ON_DAMAGE = auto()
    ON_AFTER_PIVOT = auto()

    # ターン終了イベント
    ON_TURN_END_1 = auto()
    ON_TURN_END_2 = auto()
    ON_TURN_END_3 = auto()
    ON_TURN_END_4 = auto()
    ON_TURN_END_5 = auto()
    ON_TURN_END_6 = auto()

    ON_MODIFY_STAT = auto()
    ON_END = auto()

    # チェック系イベント
    ON_CHECK_PP_CONSUMED = auto()
    ON_CHECK_DURATION = auto()
    ON_CHECK_FLOATING = auto()
    ON_CHECK_TRAPPED = auto()
    ON_CHECK_NERVOUS = auto()
    ON_CHECK_MOVE_TYPE = auto()
    ON_CHECK_MOVE_CATEGORY = auto()

    # 計算系イベント
    ON_CALC_SPEED = auto()
    ON_CALC_ACTION_SPEED = auto()
    ON_CALC_ACCURACY = auto()
    ON_CALC_POWER_MODIFIER = auto()
    ON_CALC_ATK_MODIFIER = auto()
    ON_CALC_DEF_MODIFIER = auto()
    ON_CALC_ATK_TYPE_MODIFIER = auto()
    ON_CALC_DEF_TYPE_MODIFIER = auto()
    ON_CALC_DAMAGE_MODIFIER = auto()
    ON_CHECK_DEF_ABILITY = auto()
    ON_CALC_DRAIN = auto()
