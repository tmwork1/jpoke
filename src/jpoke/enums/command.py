"""コマンド関連のEnum定義"""
from __future__ import annotations
from enum import Enum, auto

from jpoke.types import CommandType


class Command(Enum):
    """バトル中のコマンド

    技選択、交代などのプレイヤーの行動を表す。

    命名規則:
    - {TYPE}_{INDEX}: コマンドタイプとインデックス (0-9)
    - SWITCH: ポケモン交代
    - MOVE: 技使用
    - TERASTAL: テラスタル + 技使用
    - MEGAEVOL: メガシンカ + 技使用
    - GIGAMAX: ダイマックス + 技使用
    - ZMOVE: Zワザ使用
    """
    # 特殊コマンド
    STRUGGLE = auto()  # わるあがき
    FORCED = auto()  # 強制再行動

    # 交代コマンド (0-9)
    SWITCH_0 = auto()
    SWITCH_1 = auto()
    SWITCH_2 = auto()
    SWITCH_3 = auto()
    SWITCH_4 = auto()
    SWITCH_5 = auto()
    SWITCH_6 = auto()
    SWITCH_7 = auto()
    SWITCH_8 = auto()
    SWITCH_9 = auto()

    # 技コマンド (0-9)
    MOVE_0 = auto()
    MOVE_1 = auto()
    MOVE_2 = auto()
    MOVE_3 = auto()
    MOVE_4 = auto()
    MOVE_5 = auto()
    MOVE_6 = auto()
    MOVE_7 = auto()
    MOVE_8 = auto()
    MOVE_9 = auto()

    # テラスタルコマンド (0-9)
    TERASTAL_0 = auto()
    TERASTAL_1 = auto()
    TERASTAL_2 = auto()
    TERASTAL_3 = auto()
    TERASTAL_4 = auto()
    TERASTAL_5 = auto()
    TERASTAL_6 = auto()
    TERASTAL_7 = auto()
    TERASTAL_8 = auto()
    TERASTAL_9 = auto()

    # メガシンカコマンド (0-9)
    MEGAEVOL_0 = auto()
    MEGAEVOL_1 = auto()
    MEGAEVOL_2 = auto()
    MEGAEVOL_3 = auto()
    MEGAEVOL_4 = auto()
    MEGAEVOL_5 = auto()
    MEGAEVOL_6 = auto()
    MEGAEVOL_7 = auto()
    MEGAEVOL_8 = auto()
    MEGAEVOL_9 = auto()

    # ダイマックスコマンド (0-9)
    GIGAMAX_0 = auto()
    GIGAMAX_1 = auto()
    GIGAMAX_2 = auto()
    GIGAMAX_3 = auto()
    GIGAMAX_4 = auto()
    GIGAMAX_5 = auto()
    GIGAMAX_6 = auto()
    GIGAMAX_7 = auto()
    GIGAMAX_8 = auto()
    GIGAMAX_9 = auto()

    # Zワザコマンド (0-9)
    ZMOVE_0 = auto()
    ZMOVE_1 = auto()
    ZMOVE_2 = auto()
    ZMOVE_3 = auto()
    ZMOVE_4 = auto()
    ZMOVE_5 = auto()
    ZMOVE_6 = auto()
    ZMOVE_7 = auto()
    ZMOVE_8 = auto()
    ZMOVE_9 = auto()

    @classmethod
    def names(cls) -> list[str]:
        """全てのコマンド名を取得"""
        return [x.name for x in cls]

    def __str__(self):
        return self.name

    @property
    def index(self) -> int:
        """コマンドのインデックス (0-9)
        特殊コマンドは0を返す。
        """
        if "_" in self.name:
            return int(self.name.split("_")[-1])
        return 0

    def change_index(self, new_index: int) -> Command:
        """コマンドのインデックスを変更して新しいコマンドを返す。

        Args:
            new_index: 新しいインデックス (0-9)

        Returns:
            新しいコマンド
        """
        if "_" in self.name:
            prefix = self.name.split("_")[0]
            new_name = f"{prefix}_{new_index}"
            return Command[new_name]
        return self

    def is_type(self, command_type: CommandType | None) -> bool:
        """指定したコマンドタイプかどうか"""
        match command_type:
            case None:
                return False
            case "any":
                return True
            case "move":
                return self.name[:-2] not in {"SELECT", "SWITCH"}
            case "switch":
                return self.name[:-2] == "SWITCH"
        raise ValueError(f"Invalid command type: {command_type}")

    @property
    def is_move(self) -> bool:
        """技系コマンドかどうか"""
        return self.is_type("move")

    @property
    def is_switch(self) -> bool:
        """交代コマンドかどうか"""
        return self.is_type("switch")

    @property
    def is_regular_move(self) -> bool:
        """技コマンドかどうか"""
        return self.name[:-2] == "MOVE"

    @property
    def is_terastal(self) -> bool:
        """テラスタルコマンドかどうか"""
        return self.name[:-2] == "TERASTAL"

    @property
    def is_megaevol(self) -> bool:
        """メガシンカコマンドかどうか"""
        return self.name[:-2] == "MEGAEVOL"

    @property
    def is_gigamax(self) -> bool:
        """ダイマックスコマンドかどうか"""
        return self.name[:-2] == "GIGAMAX"

    @property
    def is_zmove(self) -> bool:
        """Zワザコマンドかどうか"""
        return self.name[:-2] == "ZMOVE"

    @classmethod
    def get_switch_command(cls, index: int) -> Command:
        """対応する交代コマンドを取得"""
        return cls[f"SWITCH_{index}"]

    @classmethod
    def get_move_command(cls, index: int) -> Command:
        """対応する技コマンドを取得"""
        return cls[f"MOVE_{index}"]

    @classmethod
    def get_terastal_command(cls, index: int) -> Command:
        """対応するテラスタルコマンドを取得"""
        return cls[f"TERASTAL_{index}"]

    @classmethod
    def get_megaevol_command(cls, index: int) -> Command:
        """指定インデックスのメガシンカコマンドを取得"""
        return cls[f"MEGAEVOL_{index}"]

    @classmethod
    def get_gigamax_command(cls, index: int) -> Command:
        """指定インデックスのダイマックスコマンドを取得"""
        return cls[f"GIGAMAX_{index}"]

    @classmethod
    def get_zmove_command(cls, index: int) -> Command:
        """指定インデックスのZワザコマンドを取得"""
        return cls[f"ZMOVE_{index}"]

    @classmethod
    def switch_commands(cls) -> list[Command]:
        """全ての交代コマンドを取得"""
        return [x for x in cls if x.is_switch]

    @classmethod
    def all_move_commands(cls) -> list[Command]:
        """全ての技系コマンドを取得"""
        return [x for x in cls if x.is_move]

    @classmethod
    def regular_move_commands(cls) -> list[Command]:
        """全ての技コマンドを取得"""
        return [x for x in cls if x.is_regular_move]

    @classmethod
    def terastal_commands(cls) -> list[Command]:
        """全てのテラスタルコマンドを取得"""
        return [x for x in cls if x.is_terastal]

    @classmethod
    def megaevol_commands(cls) -> list[Command]:
        """全てのメガシンカコマンドを取得"""
        return [x for x in cls if x.is_megaevol]

    @classmethod
    def gigamax_commands(cls) -> list[Command]:
        """全てのダイマックスコマンドを取得"""
        return [x for x in cls if x.is_gigamax]

    @classmethod
    def zmove_commands(cls) -> list[Command]:
        """全てのZワザコマンドを取得"""
        return [x for x in cls if x.is_zmove]
