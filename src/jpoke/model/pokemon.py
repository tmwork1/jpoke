from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core.event import EventManager

from jpoke.utils.types import Type, Stat, MoveCategory, Gender, BoostSource, stats, AilmentName
from jpoke.utils.constants import NATURE_MODIFIER
from jpoke.utils import fast_copy

from jpoke.core.event import Event, EventContext
from jpoke.data import pokedex

from .ability import Ability
from .item import Item
from .move import Move
from .ailment import Ailment


def calc_hp(level, base, indiv, effort):
    return ((base*2 + indiv + effort//4) * level) // 100 + level + 10


def calc_stat(level, base, indiv, effort, nc):
    return int((((base*2 + indiv + effort//4) * level) // 100 + 5) * nc)


class Pokemon:
    def __init__(self,
                 name: str,
                 ability: str | Ability = "",
                 item: str | Item = "",
                 moves: list[str | Move] = ["はねる"]):
        self.data = pokedex[name]

        self.observed: bool
        self.gender: Gender = ""
        self._level: int = 50
        self._nature: str = "まじめ"
        self._ability: Ability = Ability()
        self._item: Item = Item()
        self._moves: list[Move] = []
        self._indiv: list[int] = [31]*6
        self._effort: list[int] = [0]*6
        self._stats: list[int] = [100]*6
        self._terastal: str = ""
        self.terastallized: bool = False

        self.sleep_count: int
        self.ailment: Ailment = Ailment()
        # self.field_status: FieldStatus = FieldStatus()

        self.ability = ability
        self.item = item
        self.moves = moves

        self.update_stats()
        self.hp: int = self.max_hp

        self.bench_reset()

    def bench_reset(self):
        """ベンチに戻ったときのリセット処理"""
        self.choice_locked: bool = False
        self.hidden: bool = False
        self.lockon: bool = False
        self.active_turn: int = 0
        self.forced_turn: int = 0
        self.sub_hp: int = 0
        self.bind_damage_denom: int = 0
        self.hits_taken: int = 0
        self.boosted_stat: Stat | None = None
        self.boost_source: BoostSource = ""
        self.rank: dict[Stat, int] = {k: 0 for k in stats()}
        self.added_types: list[str] = []
        self.lost_types: list[str] = []
        self.executed_move: Move | None = None
        self.pp_consumed_moves: list[Move] = []

    @classmethod
    def reconstruct_from_log(cls, data: dict) -> Pokemon:
        mon = cls(data["name"])
        mon.gender = data["gender"]
        mon.level = data["level"]
        mon.nature = data["nature"]
        # mon.ability = cls.create_ability(data["ability"])
        # mon.item = cls.create_item(data["item"])
        # mon.moves = [cls.create_move(s) for s in data["moves"]]
        mon.indiv = data["indiv"]
        mon.effort = data["effort"]
        mon.terastal = data["terastal"]
        return mon

    def __str__(self):
        sep = '\n\t'
        s = f"{self.name}{sep}"
        s += f"HP {self.hp}/{self.max_hp} ({self.hp_ratio*100:.0f}%){sep}"
        s += f"{self._nature}{sep}"
        s += f"{self.ability.name}{sep}"
        s += f"{self.item.name or 'No item'}{sep}"
        if self._terastal:
            s += f"{self._terastal}T{sep}"
        else:
            s += f"No terastal{sep}"
        for st, ef in zip(self._stats, self._effort):
            s += f"{st}({ef})-" if ef else f"{st}-"
        s = s[:-1] + sep
        s += "/".join(move.name for move in self.moves)
        return s

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        fast_copy(self, new, keys_to_deepcopy=['ability', 'item', 'moves', 'field_status', 'executed_move', 'expended_moves'])
        return new

    def dump(self) -> dict:
        return {
            "name": self.orig_name,
            "gender": self.gender,
            "level": self._level,
            "nature": self._nature,
            "ability": self.ability.name,
            "item": self.item.name,
            "moves": [move.name for move in self.moves],
            "indiv": self._indiv,
            "effort": self._effort,
            "terastal": self._terastal,
        }

    def switch_in(self, events: EventManager):
        self.observed = True
        if self.ability.effect_enabled:
            self.ability.register_handlers(events, self)
        if self.item.effect_enabled:
            self.item.register_handlers(events, self)
        if self.ailment.effect_enabled:
            self.ailment.register_handlers(events, self)

    def switch_out(self, events: EventManager):
        self.bench_reset()
        self.ability.unregister_handlers(events, self)
        self.item.unregister_handlers(events, self)
        self.ailment.unregister_handlers(events, self)

    @property
    def name(self) -> str:
        return self.data.name

    @property
    def ability(self) -> Ability:
        return self._ability

    @ability.setter
    def ability(self, obj: str | Ability):
        if isinstance(obj, str):
            obj = Ability(obj)
        self._ability = obj

    @property
    def item(self) -> Item:
        return self._item

    @item.setter
    def item(self, obj: str | Item):
        if isinstance(obj, str):
            obj = Item(obj)
        self._item = obj

    @property
    def moves(self) -> list[Move]:
        return self._moves

    @moves.setter
    def moves(self, objs: list[str | Move]):
        self._moves = [Move(obj) if isinstance(obj, str) else obj
                       for obj in objs]

    @property
    def types(self) -> list[str]:
        if self.terastal:
            if self.terastal == 'ステラ':
                return self.data.types
            else:
                return [self.terastal]
        else:
            if self.name == 'アルセウス':
                # TODO アルセウスのタイプ変化
                return ["ノーマル"]
            else:
                return [t for t in self.data.types if t not in
                        self.lost_types + self.added_types] + self.added_types

    @property
    def max_hp(self) -> int:
        return self.stats["H"]

    @property
    def hp_ratio(self) -> float:
        return self.hp / self.max_hp

    @hp_ratio.setter
    def hp_ratio(self, v: float):
        self.hp = int(self.max_hp * v)

    @property
    def level(self) -> int:
        return self._level

    @level.setter
    def level(self, level: int):
        self._level = level
        self.update_stats()

    @property
    def weight(self) -> float:
        w = self.data.weight
        match self.ability.name:
            case 'ライトメタル':
                w = int(w*0.5*10)/10
            case 'ヘヴィメタル':
                w *= 2
        if self.item.name == 'かるいし':
            w = int(w*0.5*10)/10
        return w

    @property
    def nature(self) -> str:
        return self._nature

    @nature.setter
    def nature(self, nature: str):
        self._nature = nature
        self.update_stats()

    @property
    def terastal(self) -> str | None:
        return self._terastal if self.terastallized else None

    @terastal.setter
    def terastal(self, type: str):
        self._terastal = type

    def can_terastallize(self) -> bool:
        return not self.terastallized and self._terastal is not None

    def terastallize(self) -> bool:
        self.terastallized = self.can_terastallize()
        return self.terastallized

    @property
    def stats(self) -> dict[Stat, int]:
        labels = stats()[:6]
        return {s: v for s, v in zip(labels, self._stats)}

    @stats.setter
    def stats(self, stats: dict[Stat, int]):
        stat_values = list(stats.values())
        nc = NATURE_MODIFIER[self._nature]
        efforts_50 = [0] + [4+8*i for i in range(32)]

        for i in range(6):
            for eff in efforts_50:
                if i == 0:
                    v = calc_hp(self._level, self.data.base[i], self._indiv[i], self._effort[i])
                else:
                    v = calc_stat(self._level, self.data.base[i], self._indiv[i], self._effort[i], nc)
                if v == stat_values[i]:
                    self._effort[i] = eff
                    self._stats[i] = v
                    break

    @property
    def base(self) -> list[int]:
        return self.data.base

    @base.setter
    def base(self, base: list[int]):
        self.data.base = base
        self.update_stats()

    @property
    def indiv(self) -> list[int]:
        return self._indiv

    @indiv.setter
    def indiv(self, indiv: list[int]):
        self._indiv = indiv
        self.update_stats()

    @property
    def effort(self) -> list[int]:
        return self._effort

    @effort.setter
    def effort(self, effort: list[int]):
        self._effort = effort
        self.update_stats()

    def has_type(self, type_: Type) -> bool:
        return type_ in self.types

    def has_move(self, move: Move | str) -> bool:
        return self.find_move(move) is not None

    def update_stats(self, keep_damage: bool = False):
        if keep_damage:
            damage = self._stats[0] - self.hp

        self._stats[0] = calc_hp(self._level, self.data.base[0], self._indiv[0], self._effort[0])
        for i in range(1, 6):
            self._stats[i] = calc_stat(self._level, self.data.base[i], self._indiv[i], self._effort[i], NATURE_MODIFIER[self._nature][i])

        if keep_damage:
            self.hp = self.hp - damage

    def set_stats(self, idx: int, value: int) -> bool:
        nc = NATURE_MODIFIER[self._nature]
        efforts_50 = [0] + [4+8*i for i in range(32)]

        for eff in efforts_50:
            if idx == 0:
                v = calc_hp(self._level, self.data.base[0], self._indiv[0], eff)
            else:
                v = calc_stat(self._level, self.data.base[idx], self._indiv[idx], eff, nc[idx])
            if v == value:
                self._effort[idx] = eff
                self._stats[idx] = v
                return True

        return False

    def set_effort(self, idx: int, value: int):
        self._effort[idx] = value
        self.update_stats()

    def modify_hp(self, v: int) -> int:
        old = self.hp
        self.hp = max(0, min(self.max_hp, old + v))
        return self.hp - old

    def modify_stat(self, stat: Stat, v: int) -> int:
        old = self.rank[stat]
        self.rank[stat] = max(-6, min(6, old + v))
        return self.rank[stat] - old

    def find_move(self, move: Move | str) -> Move | None:
        for mv in self.moves:
            if move in [mv, mv.name]:
                return mv

    def is_floating(self, events: EventManager) -> bool:
        floating = "ひこう" in self.types
        floating &= events.emit(
            Event.ON_CHECK_FLOATING,
            EventContext(source=self),
            floating
        )
        return floating

    def is_trapped(self, events: EventManager) -> bool:
        trapped = events.emit(
            Event.ON_CHECK_TRAPPED,
            EventContext(source=self),
            False
        )
        trapped &= "ゴースト" not in self.types
        return trapped

    def is_nervous(self, events: EventManager) -> bool:
        return events.emit(
            Event.ON_CHECK_NERVOUS,
            EventContext(source=self),
            False
        )

    def effective_move_type(self, move: Move, events: EventManager) -> str:
        events.emit(
            Event.ON_CHECK_MOVE_TYPE,
            EventContext(source=self, move=move)
        )
        return move._type

    def effective_move_category(self, move: Move, events: EventManager) -> MoveCategory:
        return events.emit(
            Event.ON_CHECK_MOVE_CATEGORY,
            EventContext(source=self, move=move),
            value=move.category
        )

    def apply_ailment(self, events: EventManager, name: AilmentName, source: Pokemon | None = None, force: bool = False) -> bool:
        # force=True でない限り上書き不可
        if self.ailment.is_active and not force:
            return False
        # 重ねがけ不可
        if name == self.ailment.name:
            return False
        # 既存のハンドラを削除
        if self.ailment.is_active:
            self.ailment.unregister_handlers(events, self)
        # 新しい状態異常を設定してハンドラ登録
        self.ailment = Ailment(name)
        self.ailment.register_handlers(events, self)
        return True

    def cure_ailment(self, events: EventManager, source: Pokemon | None = None) -> bool:
        """状態異常を解除する"""
        if not self.ailment.effect_enabled:
            return False
        # ハンドラ削除
        self.ailment.unregister_handlers(events, self)
        # 状態異常をクリア
        self.ailment = Ailment()
        return True
