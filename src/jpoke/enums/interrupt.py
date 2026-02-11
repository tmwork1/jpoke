"""割り込み処理関連のEnum定義"""
from enum import Enum, auto


class Interrupt(Enum):
    """バトル中の割り込み処理の種類

    アイテム消費やポケモンの強制交代などの
    特殊な割り込み処理を管理する。
    """
    NONE = auto()
    EJECTBUTTON = auto()
    PIVOT = auto()
    EMERGENCY = auto()
    FAINTED = auto()
    REQUESTED = auto()
    EJECTPACK_ON_AFTER_SWITCH = auto()
    EJECTPACK_ON_START = auto()
    EJECTPACK_ON_SWITCH_0 = auto()
    EJECTPACK_ON_SWITCH_1 = auto()
    EJECTPACK_ON_AFTER_MOVE_0 = auto()
    EJECTPACK_ON_AFTER_MOVE_1 = auto()
    EJECTPACK_ON_TURN_END = auto()

    def consume_item(self) -> bool:
        """このInterruptがアイテム消費を伴うかどうか"""
        return "EJECT" in self.name

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
