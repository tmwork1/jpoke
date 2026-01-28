from enum import Enum, auto


class EventControl(Enum):
    STOP_HANDLER = auto()
    STOP_EVENT = auto()


class DamageFlag(Enum):
    CRITICAL = "急所"
    IGNORE_ATK_RANK_BY_TENNEN = "てんねん 攻撃ランク無視"
    IGNORE_ATK_DOWN_DURING_CRITICAL = "急所 攻撃ランク無視"
    IGNORE_DEF_RANK_BY_MOVE = "技 防御ランク無視"
    IGNORE_DEF_RANK_BY_TENNEN = "てんねん 防御ランク無視"
    IGNORE_DEF_UP_DURING_CRITICAL = "急所 防御ランク無視"


class Event(Enum):
    ON_BEFORE_ACTION = auto()
    ON_SWITCH_IN = auto()
    ON_SWITCH_OUT = auto()
    ON_BEFORE_MOVE = auto()
    ON_TRY_ACTION = auto()
    ON_DECLARE_MOVE = auto()
    ON_CONSUME_PP = auto()
    ON_TRY_MOVE = auto()
    ON_TRY_IMMUNE = auto()
    ON_HIT = auto()
    ON_PAY_HP = auto()
    ON_MODIFY_DAMAGE = auto()
    ON_MOVE_SECONDARY = auto()
    ON_DAMAGE = auto()
    ON_AFTER_PIVOT = auto()
    ON_TURN_END_1 = auto()
    ON_TURN_END_2 = auto()
    ON_TURN_END_3 = auto()
    ON_TURN_END_4 = auto()
    ON_TURN_END_5 = auto()
    ON_TURN_END_6 = auto()
    ON_MODIFY_STAT = auto()
    ON_END = auto()

    ON_CHECK_PP_CONSUMED = auto()
    ON_CHECK_DURATION = auto()
    ON_CHECK_FLOATING = auto()
    ON_CHECK_TRAPPED = auto()
    ON_CHECK_NERVOUS = auto()
    ON_CHECK_MOVE_TYPE = auto()
    ON_CHECK_MOVE_CATEGORY = auto()

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


class Interrupt(Enum):
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
        return "EJECT" in self.name

    @classmethod
    def ejectpack_on_switch(cls, idx: int):
        return cls[f"EJECTPACK_ON_SWITCH_{idx}"]

    @classmethod
    def ejectpack_on_after_move(cls, idx: int):
        return cls[f"EJECTPACK_ON_AFTER_MOVE_{idx}"]


class Condition(Enum):
    AQUA_RING = ("アクアリング", 1, True, False)
    AME_MAMIRE = ("あめまみれ", 3, False, True)
    ENCORE = ("アンコール", 3, False, True)
    GROUNDED = ("うちおとす", 1, False, False)
    HEAL_BLOCK = ("かいふくふうじ", 5, True, True)
    KANASHIBARI = ("かなしばり", 3, False, True)
    CRITICAL = ("急所ランク", 3, True, False)
    CONFUSION = ("こんらん", 5, True, True)
    SHIOZUKE = ("しおづけ", 1, False, False)
    JIGOKUZUKI = ("じごくづき", 2, False, True)
    CHARGE = ("じゅうでん", 1, False, False)
    STOCK = ("たくわえる", 3, False, False)
    CHOHATSU = ("ちょうはつ", 3, False, True)
    MAGNET_RISE = ("でんじふゆう", 5, True, True)
    SWITCH_BLOCK = ("にげられない", 1, False, False)
    NEMUKE = ("ねむけ", 2, False, True)
    NEOHARU = ("ねをはる", 1, False, False)
    NOROI = ("のろい", 1, True, False)
    BIND = ("バインド", 5, False, True)
    HOROBI = ("ほろびのうた", 3, True, True)
    MICHIZURE = ("みちづれ", 1, False, False)
    MEROMERO = ("メロメロ", 1, False, False)
    BAD_POISON = ("もうどく", 15, False, False)
    YADORIGI = ("やどりぎのタネ", 1, True, False)

    @property
    def max_count(self) -> int:
        return self.value[1]

    @property
    def inheritable(self) -> bool:
        return self.value[2]

    @property
    def expirable(self) -> bool:
        return self.value[3]


class Time(Enum):
    """時間 [s]"""
    GAME = 20*60                # 試合
    SELECTION = 90              # 選出
    COMMAND = 45                # コマンド入力
    CAPTURE = 0.1               # キャプチャ遅延
    TRANSITION_CAPTURE = 0.3    # 画面遷移を伴うキャプチャ遅延
    TIMEOUT = 60                # 実機対戦でのタイムアウト


class Command(Enum):
    NONE = auto()
    STRUGGLE = auto()
    FORCED = auto()
    SKIP = auto()
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
        return [x.name for x in cls]

    def __str__(self):
        return self.name

    def is_none(self) -> bool:
        return self.value is None

    @property
    def idx(self) -> int:
        return int(self.name[-1])

    def is_select(self) -> bool:
        return self.name[:-2] == "SELECT"

    def is_switch(self) -> bool:
        return self.name[:-2] == "SWITCH"

    def is_move(self) -> bool:
        return self.name[:-2] == "MOVE"

    def is_terastal(self) -> bool:
        return self.name[:-2] == "TERASTAL"

    def is_megaevol(self) -> bool:
        return self.name[:-2] == "MEGAEVOL"

    def is_gigamax(self) -> bool:
        return self.name[:-2] == "GIGAMAX"

    def is_zmove(self) -> bool:
        return self.name[:-2] == "ZMOVE"

    def is_action(self) -> bool:
        return self.is_move() or self.is_terastal() or \
            self.is_megaevol() or self.is_gigamax() or self.is_zmove()

    @classmethod
    def selection_commands(cls):
        return [x for x in cls if x.is_select()]

    @classmethod
    def switch_commands(cls):
        return [x for x in cls if x.is_switch()]

    @classmethod
    def action_commands(cls):
        return [x for x in cls if x.is_action()]

    @classmethod
    def move_commands(cls):
        return [x for x in cls if x.is_move()]

    @classmethod
    def terastal_commands(cls):
        return [x for x in cls if x.is_terastal()]

    @classmethod
    def megaevol_commands(cls):
        return [x for x in cls if x.is_megaevol()]

    @classmethod
    def gigamax_commands(cls):
        return [x for x in cls if x.is_gigamax()]

    @classmethod
    def zmove_commands(cls):
        return [x for x in cls if x.is_zmove()]
