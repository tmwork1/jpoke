from enum import Enum, auto


class LogCode(Enum):
    WIN = auto()
    LOSE = auto()
    ACTION_START = auto()
    ACTION_BLOCKED = auto()
    PROTECT_SUCCESS = auto()
    PROTECT_FAILED = auto()
    MODIFY_HP = auto()
    MODIFY_STAT = auto()
    SWITCH_IN = auto()
    SWITCH_OUT = auto()
    CONSUME_ITEM = auto()
    CURE_AILMENT = auto()
    APPLY_AILMENT = auto()
