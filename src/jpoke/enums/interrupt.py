"""割り込み処理関連のEnum定義"""
from enum import Enum, auto


class Interrupt(Enum):
    """バトル中の割り込み処理の種類

    アイテム消費やポケモンの強制交代などの
    特殊な割り込み処理を管理する。
    """
    NONE = auto()
    PIVOT = auto()
    EMERGENCY = auto()
    FAINTED = auto()
    REQUESTED = auto()
    EJECTBUTTON = auto()
    EJECTPACK_ON_AFTER_SWITCH = auto()
    EJECTPACK_ON_START = auto()
    EJECTPACK_ON_SWITCH_0 = auto()
    EJECTPACK_ON_SWITCH_1 = auto()
    EJECTPACK_ON_AFTER_MOVE_0 = auto()
    EJECTPACK_ON_AFTER_MOVE_1 = auto()
    EJECTPACK_ON_TURN_END = auto()

    def requires_item_consumption(self) -> bool:
        """この割り込みがアイテムの消費を伴うかどうかを返す。"""
        return self in {
            Interrupt.EJECTBUTTON,
            Interrupt.EJECTPACK_ON_AFTER_SWITCH,
            Interrupt.EJECTPACK_ON_START,
            Interrupt.EJECTPACK_ON_SWITCH_0,
            Interrupt.EJECTPACK_ON_SWITCH_1,
            Interrupt.EJECTPACK_ON_AFTER_MOVE_0,
            Interrupt.EJECTPACK_ON_AFTER_MOVE_1,
            Interrupt.EJECTPACK_ON_TURN_END,
        }

    @classmethod
    def ejectpack_on_switch(cls, idx: int):
        """交代時のだっしゅつパック発動を取得

        Args:
            idx: ポケモンのインデックス (0 or 1)
        """
        return cls[f"EJECTPACK_ON_SWITCH_{idx}"]

    @classmethod
    def ejectpack_on_after_move(cls, idx: int):
        """技使用後のだっしゅつパック発動を取得

        Args:
            idx: ポケモンのインデックス (0 or 1)
        """
        return cls[f"EJECTPACK_ON_AFTER_MOVE_{idx}"]
