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
    EJECTBUTTON = auto()

    EJECTPACK_REQUESTED = auto()
    EJECTPACK_ON_AFTER_SWITCH = auto()
    EJECTPACK_ON_START = auto()
    EJECTPACK_ON_SWITCH_0 = auto()
    EJECTPACK_ON_SWITCH_1 = auto()
    EJECTPACK_ON_AFTER_MEGAEVOLVE = auto()
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
            Interrupt.EJECTPACK_ON_AFTER_MEGAEVOLVE,
            Interrupt.EJECTPACK_ON_AFTER_MOVE_0,
            Interrupt.EJECTPACK_ON_AFTER_MOVE_1,
            Interrupt.EJECTPACK_ON_TURN_END,
        }

    def required_item_name(self) -> str:
        """この割り込みの発動に必要なアイテム名を返す（不要な場合は空文字列）。

        発動条件を満たした後、交代を実行するより前にマジシャン・わるいてぐせなどで
        アイテムを奪われた／失った場合、交代自体が発生しないようにするための判定に使う。
        """
        if self == Interrupt.EJECTBUTTON:
            return "だっしゅつボタン"
        if self.name.startswith("EJECTPACK"):
            return "だっしゅつパック"
        return ""

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
