"""コマンド関連のEnum定義"""
from enum import Enum, auto


class Command(Enum):
    """バトル中のコマンド

    ポケモンの選出、技選択、交代などの
    プレイヤーの行動を表す。

    命名規則:
    - {TYPE}_{INDEX}: コマンドタイプとインデックス (0-9)
    - SELECT: ポケモン選出
    - SWITCH: ポケモン交代
    - MOVE: 技使用
    - TERASTAL: テラスタル + 技使用
    - MEGAEVOL: メガシンカ + 技使用
    - GIGAMAX: ダイマックス + 技使用
    - ZMOVE: Zワザ使用
    """
    # 特殊コマンド
    NONE = auto()
    STRUGGLE = auto()
    FORCED = auto()
    SKIP = auto()

    # 選出コマンド (0-9)
    SELECT_0 = auto()
    SELECT_1 = auto()
    SELECT_2 = auto()
    SELECT_3 = auto()
    SELECT_4 = auto()
    SELECT_5 = auto()
    SELECT_6 = auto()
    SELECT_7 = auto()
    SELECT_8 = auto()
    SELECT_9 = auto()

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

    def is_none(self) -> bool:
        """NONEコマンドかどうか"""
        return self.value is None

    @property
    def idx(self) -> int:
        """コマンドのインデックス (0-9)"""
        return int(self.name[-1])

    def is_select(self) -> bool:
        """選出コマンドかどうか"""
        return self.name[:-2] == "SELECT"

    def is_switch(self) -> bool:
        """交代コマンドかどうか"""
        return self.name[:-2] == "SWITCH"

    def is_move(self) -> bool:
        """技コマンドかどうか"""
        return self.name[:-2] == "MOVE"

    def is_terastal(self) -> bool:
        """テラスタルコマンドかどうか"""
        return self.name[:-2] == "TERASTAL"

    def is_megaevol(self) -> bool:
        """メガシンカコマンドかどうか"""
        return self.name[:-2] == "MEGAEVOL"

    def is_gigamax(self) -> bool:
        """ダイマックスコマンドかどうか"""
        return self.name[:-2] == "GIGAMAX"

    def is_zmove(self) -> bool:
        """Zワザコマンドかどうか"""
        return self.name[:-2] == "ZMOVE"

    def is_action(self) -> bool:
        """アクションコマンドかどうか（技系全般）"""
        return self.is_move() or self.is_terastal() or \
            self.is_megaevol() or self.is_gigamax() or self.is_zmove()

    @classmethod
    def selection_commands(cls):
        """全ての選出コマンドを取得"""
        return [x for x in cls if x.is_select()]

    @classmethod
    def switch_commands(cls):
        """全ての交代コマンドを取得"""
        return [x for x in cls if x.is_switch()]

    @classmethod
    def action_commands(cls):
        """全てのアクションコマンドを取得"""
        return [x for x in cls if x.is_action()]

    @classmethod
    def move_commands(cls):
        """全ての技コマンドを取得"""
        return [x for x in cls if x.is_move()]

    @classmethod
    def terastal_commands(cls):
        """全てのテラスタルコマンドを取得"""
        return [x for x in cls if x.is_terastal()]

    @classmethod
    def megaevol_commands(cls):
        """全てのメガシンカコマンドを取得"""
        return [x for x in cls if x.is_megaevol()]

    @classmethod
    def gigamax_commands(cls):
        """全てのダイマックスコマンドを取得"""
        return [x for x in cls if x.is_gigamax()]

    @classmethod
    def zmove_commands(cls):
        """全てのZワザコマンドを取得"""
        return [x for x in cls if x.is_zmove()]
