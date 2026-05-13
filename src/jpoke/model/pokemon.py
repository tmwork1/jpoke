# TODO : メソッドの定義順を整理する（例: 基本情報関連、状態関連、ステータス関連、技関連など）

"""ポケモンモデルを定義するモジュール。

ポケモンの基本情報、ステータス、特性、持ち物、技、状態異常、
ランク変化など、バトル中のポケモンの全状態を管理します。
"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle, BattleContext
    from jpoke.data.models import PokemonData

from jpoke.utils.type_defs import Nature, Type, Stat, Gender, BoostSource, AilmentName, VolatileName
from jpoke.utils.constants import RANK_MIN, RANK_MAX, STATS
from jpoke.utils import fast_copy
from jpoke.data import pokedex

from .ability import Ability
from .item import Item
from .move import Move
from .ailment import Ailment
from .volatile import Volatile
from .stats import PokemonStats


class Pokemon:
    """ポケモンクラス。

    ポケモンの全状態と機能を管理するメインクラスです。
    種族値、個体値、努力値、性格からステータスを計算し、
    特性、持ち物、技、状態異常、ランク変化などを管理します。

    Attributes:
        data: ポケモン図鑑データ
        gender: 性別
        hp: 現在HP
        max_hp: 最大HP
        ailment: 状態異常
        ability: 特性
        item: 持ち物
        moves: 覚えている技のリスト
        rank: 能力ランクの辞書
        volatiles: 揮発状態の辞書
        terastallized: テラスタル済みかどうか
    """

    def __init__(self,
                 name: str,
                 gender: Gender = "",
                 nature: Nature = "まじめ",
                 level: int = 50,
                 ability: str = "",
                 item: str = "",
                 moves: list[str] = ["はねる"],
                 tera_type: Type = "ステラ") -> None:
        """ポケモンを初期化する。

        Args:
            name: ポケモン名
            gender: 性別（"オス"/"メス"/""）
            nature: 性格
            level: レベル（デフォルト50）
            ability: 特性（文字列）
            item: 持ち物（文字列）
            moves: 技のリスト（文字列のリスト）
            tera_type: テラスタルタイプ
        """
        self.data: PokemonData = pokedex[name]
        self.gender: Gender = gender
        self._nature: Nature = nature
        self._level: int = level
        self.tera_type: Type = tera_type

        self.ability = Ability(ability)
        self.item = Item(item)
        self.set_moves(moves)

        self.base_ability_name: str = self.ability.orig_name

        # ステータス計算マネージャー
        self._stats_manager = PokemonStats()

        # 初期ステータス計算
        self.update_stats()

        # パラドックス特性の状態はコンストラクタで属性を明示し、bench_resetで値を初期化する。
        # TODO : paradox_boost_active は paradox_boost_stat が None でないことと同値なので、paradox_boost_stat を主属性にして整理する。
        self.paradox_boost_active: bool = False
        self.paradox_boost_stat: Stat | None = None
        self.paradox_boost_source: BoostSource = ""

        # バトル中に利用する属性はコンストラクタで明示的に定義する。
        self.revealed: bool = False
        self.terastallized: bool = False
        self.hp: int = self.max_hp
        self.ailment: Ailment = Ailment()
        self.stellar_boosted_types: set = set()
        self.volatiles: dict[VolatileName, Volatile] = {}
        self.active_turn: int = 0
        self.hits_taken: int = 0
        self.rank: dict[Stat, int] = {k: 0 for k in STATS}
        self.executed_move: Move | None = None
        self.ability_override_type: Type | None = None

        self.init_game()

    def init_game(self):
        """ゲーム初期化処理。
        ポケモンのバトル状態を初期化する。
        """
        self.revealed = False
        self.terastallized = False
        self.hp = self.max_hp
        self.ailment = Ailment()
        # ステラ テラスタル補正を消費したタイプの集合
        self.stellar_boosted_types = set()

        # 場に出ているときの状態をリセット
        self.bench_reset()

    def bench_reset(self):
        """ベンチに戻ったときのリセット処理"""
        self.volatiles = {}
        self.active_turn = 0
        self.hits_taken = 0
        self.rank = {k: 0 for k in STATS}
        self.executed_move = None
        self.ability_override_type = None
        self.ability.activated_since_switch_in = False
        self.paradox_boost_active = False
        self.paradox_boost_stat = None
        self.paradox_boost_source = ""

        self.restore_ability()

    def restore_ability(self) -> bool:
        """特性をもとに戻す。"""
        if self.ability.orig_name != self.base_ability_name:
            self.ability = Ability(self.base_ability_name)
            return True
        return False

    def init_turn(self):
        """ターン初期化処理。"""
        self.hits_taken = 0

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        fast_copy(self, new, keys_to_deepcopy=[
            'ability', 'item', 'moves', 'ailment', 'volatiles',
            'executed_move', 'pp_consumed_moves',
            '_stats_manager',
        ])
        return new

    def show(self):
        """ポケモンの情報を文字列化して表示する。"""
        sep = '\n\t'
        s = f"{self.name}{sep}"
        s += f"HP {self.hp}/{self.max_hp} ({self.hp_ratio*100:.0f}%){sep}"
        s += f"{self._nature}{sep}"
        s += f"{self.ability.name}{sep}"
        s += f"{self.item.name or 'No item'}{sep}"
        if self.tera_type:
            s += f"{self.tera_type}T{sep}"
        else:
            s += f"No terastal{sep}"
        for st, ef in zip(self._stats_manager.stats, self._stats_manager.effort):
            s += f"{st}({ef})-" if ef else f"{st}-"
        s = s[:-1] + sep
        s += "/".join(move.name for move in self.moves)
        print(s)

    def to_dict(self) -> dict:
        """ポケモンの情報を辞書形式で返す。

        Returns:
            ポケモンの全情報を含む辞書
        """
        return {
            "name": self.name,
            "gender": self.gender,
            "level": self._level,
            "nature": self._nature,
            "ability": self.ability.name,
            "item": self.item.name,
            "moves": [move.name for move in self.moves],
            "indiv": self._stats_manager.indiv,
            "effort": self._stats_manager.effort,
            "tera_type": self.tera_type,
        }

    @property
    def name(self) -> str:
        """ポケモンの名前を取得する。

        Returns:
            ポケモンの種族名
        """
        return self.data.name

    @property
    def alias(self) -> str:
        """ポケモンの図鑑エイリアスを取得する。"""
        return self.data.alias

    def set_form(self, alias: str, keep_damage: bool = True) -> None:
        """ポケモンのフォルムをエイリアス指定で切り替える。

        Args:
            alias: 変更先フォルムの図鑑エイリアス
            keep_damage: Trueの場合、現在の被ダメージ量を維持する
        """
        if self.alias == alias:
            return

        self.data = pokedex[alias]
        self.update_stats(keep_damage=keep_damage)

    @property
    def alive(self) -> bool:
        """ポケモンが生存しているかどうかを取得する。

        Returns:
            HPが0より大きい場合True
        """
        return self.hp > 0

    @property
    def fainted(self) -> bool:
        """ポケモンが瀕死状態かどうかを取得する。

        Returns:
            HPが0の場合True
        """
        return self.hp == 0

    def set_moves(self, moves: list[str]):
        """技のリストを設定する。

        Args:
            moves: 技名のリスト
        """
        self.moves = [Move(name) for name in moves]

    @property
    def types(self) -> list[Type]:
        """ポケモンの現在のタイプを取得する。

        Returns:
            タイプのリスト

        Note:
            テラスタル、タイプ追加/削除効果を考慮した現在のタイプを返す。
            アルセウスのタイプ変化は未実装（TODO）。
        """
        if self.active_tera_type:
            if self.active_tera_type == 'ステラ':
                return self.data.types
            else:
                return [self.active_tera_type]
        elif self.ability_override_type is not None:
            return [self.ability_override_type]
        else:
            return self.data.types

    @property
    def max_hp(self) -> int:
        """最大HPを取得する。

        Returns:
            最大HP
        """
        return self._stats_manager.stats[0]

    @property
    def hp_ratio(self) -> float:
        """現在のHP割合を取得する。

        Returns:
            HP割合（0.0～1.0）
        """
        return self.hp / self.max_hp

    @property
    def level(self) -> int:
        """ポケモンのレベルを取得する。

        Returns:
            レベル
        """
        return self._level

    @level.setter
    def level(self, level: int):
        """ポケモンのレベルを設定する。

        Args:
            level: レベル

        Note:
            レベル変更時にステータスを自動再計算する。
        """
        self._level = level
        self.update_stats()

    @property
    def weight(self) -> float:
        """ポケモンの現在の体重を取得する。

        Returns:
            体重（kg）

        Note:
            特性（ライトメタル、ヘヴィメタル）や
            持ち物（かるいし）の効果を考慮した体重を返す。
        """
        # TODO : ON_MODIFY_WEIGHTイベントを作成してハンドラとして実装する
        w = self.data.weight
        match self.ability.name:
            case 'ライトメタル':
                w = int(w*0.5*10)/10
            case 'ヘヴィメタル':
                w *= 2
        if self.has_item('かるいし'):
            w = int(w*0.5*10)/10
        return w

    @property
    def nature(self) -> str:
        """ポケモンの性格を取得する。

        Returns:
            性格名
        """
        return self._nature

    @nature.setter
    def nature(self, nature: Nature):
        """ポケモンの性格を設定する。

        Args:
            nature: 性格名

        Note:
            性格変更時にステータスを自動再計算する。
        """
        self._nature = nature
        self.update_stats()

    @property
    def active_tera_type(self) -> Type:
        """テラスタルのタイプを取得する。

        Returns:
            テラスタル済みの場合はタイプ名、そうでなければNone
        """
        return self.tera_type if self.terastallized else ""

    def can_terastallize(self) -> bool:
        """テラスタル可能かどうかを判定する。

        Returns:
            テラスタル可能な場合True
        """
        return not self.terastallized and self.tera_type != ""

    def terastallize(self):
        """テラスタルする"""
        if self.can_terastallize():
            self.terastallized = True

    def has_item(self, name: str | None = None) -> bool:
        """持ち物を持っているか判定する。

        Args:
            name: 持ち物名（Noneの場合は何らかの持ち物を持っているかを判定）

        Returns:
            nameが指定された場合はその持ち物を持っているか、
            Noneの場合は何らかの持ち物を持っている場合True
        """
        return self.item.name == name

    @property
    def stats(self) -> dict[Stat, int]:
        """ステータスを辞書形式で取得する。

        Returns:
            ステータス名をキーとする実数値の辞書
        """
        return self._stats_manager.stats_dict

    @stats.setter
    def stats(self, stats: dict[Stat, int]):
        """実数値から努力値を逆算して設定する。

        Args:
            stats: ステータス名をキー、実数値を値とする辞書

        Note:
            設定後、ステータスを自動再計算する。
        """
        self._stats_manager.set_stats_from_dict(stats, self._level, self.data.base, self._nature)
        self.update_stats()

    @property
    def base(self) -> list[int]:
        """種族値を取得する。

        Returns:
            種族値のリスト
        """
        return self.data.base

    @base.setter
    def base(self, base: list[int]):
        """種族値を設定する。

        Args:
            base: 種族値のリスト

        Note:
            種族値変更時にステータスを自動再計算する。
        """
        self.data.base = base
        self.update_stats()

    @property
    def indiv(self) -> list[int]:
        """個体値を取得する。

        Returns:
            個体値のリスト
        """
        return self._stats_manager.indiv

    @indiv.setter
    def indiv(self, indiv: list[int]):
        """個体値を設定する。

        Args:
            indiv: 個体値のリスト

        Note:
            個体値変更時にステータスを自動再計算する。
        """
        self._stats_manager.indiv = indiv
        self.update_stats()

    @property
    def effort(self) -> list[int]:
        """努力値を取得する。

        Returns:
            努力値のリスト
        """
        return self._stats_manager.effort

    @effort.setter
    def effort(self, effort: list[int]):
        """努力値を設定する。

        Args:
            effort: 努力値のリスト

        Note:
            努力値変更時にステータスを自動再計算する。
        """
        self._stats_manager.effort = effort
        self.update_stats()

    def has_type(self, type_: Type) -> bool:
        """指定されたタイプを持っているか判定する。

        Args:
            type_: タイプ名

        Returns:
            指定タイプを持っていればTrue
        """
        return type_ in self.types

    def has_move(self, move: str) -> bool:
        """指定された技を持っているか判定する。

        Args:
            move: 技名

        Returns:
            指定技を持っていればTrue
        """
        return self.get_move(move) is not None

    @property
    def damage_taken(self) -> int:
        """現在までに受けたダメージ量を取得する。

        Returns:
            受けたダメージ量
        """
        return self.max_hp - self.hp

    def update_stats(self, keep_damage: bool = False):
        """ステータスを再計算する。

        Args:
            keep_damage: Trueの場合、現在の被ダメージ量を保持する

        Note:
            レベル、性格、種族値、個体値、努力値に基づいて
            全ステータスを再計算する。レベルアップや性格変更時に使用。
        """
        # 被ダメージ量を保持する場合
        damage = self.damage_taken if keep_damage else 0

        # ステータスを再計算
        self._stats_manager.update_stats(
            self._level, self.data.base, self._nature
        )

        # 被ダメージ量を復元
        if keep_damage:
            self.hp = self.max_hp - damage

    def set_stats(self, idx: int, value: int) -> bool:
        """指定した実数値になるよう努力値を設定する。

        Args:
            idx: ステータスのインデックス (0=HP, 1=攻撃, 2=防御, ...)
            value: 目標の実数値

        Returns:
            設定に成功した場合True、失敗した場合False

        Note:
            内部的に PokemonStats に委譲する。
        """
        return self._stats_manager.set_stats_from_value(
            idx, value, self._level, self.data.base, self._nature
        )

    def set_effort(self, idx: int, value: int):
        """指定インデックスの努力値を設定する。

        Args:
            idx: ステータスのインデックス
            value: 設定する努力値

        Note:
            設定後、ステータスを自動再計算する。
        """
        self._stats_manager.set_effort_at(idx, value)
        self.update_stats()

    def modify_hp(self, v: int) -> int:
        """HPを増減させる。

        Args:
            v: 増減量（正の値で回復、負の値でダメージ）

        Returns:
            実際に変化したHP量

        Note:
            HPは0から最大HPの範囲に制限される。
            このメソッドは内部用です。外部からはbattle.modify_hp()を使用してください。
        """
        old = self.hp
        self.hp = max(0, min(self.max_hp, old + v))
        return self.hp - old

    def modify_stat(self, stat: Stat, v: int) -> int:
        """ランク補正を変更する。

        Args:
            stat: ステータス名
            v: 変化量

        Returns:
            実際に変化したランク

        Note:
            ランクは-6から+6の範囲に制限される。
        """
        old = self.rank[stat]
        self.rank[stat] = max(RANK_MIN, min(RANK_MAX, old + v))
        return self.rank[stat] - old

    @property
    def critical_rank(self) -> int:
        """急所ランクを取得する。

        Returns:
            急所ランク（volatileの急所ランク状態から取得）

        Note:
            volatile["きゅうしょアップ"]が存在しない場合は0を返す。
        """
        if self.has_volatile("きゅうしょアップ"):
            return self.volatiles["きゅうしょアップ"].count
        return 0

    @critical_rank.setter
    def critical_rank(self, value: int):
        """急所ランクを設定する。

        Args:
            value: 設定する急所ランク値

        Note:
            内部的にvolatile["きゅうしょアップ"]を管理するため、
            テストやデバッグ用に使用される。
        """
        if value <= 0:
            # 急所ランクが0以下の場合は状態を削除
            if self.has_volatile("きゅうしょアップ"):
                del self.volatiles["きゅうしょアップ"]
        else:
            # 急所ランク状態を作成または更新
            if not self.has_volatile("きゅうしょアップ"):
                self.volatiles["きゅうしょアップ"] = Volatile("きゅうしょアップ", count=0)
            self.volatiles["きゅうしょアップ"].count = value

    @property
    def sub_hp(self) -> int:
        """みがわりの残りHPを取得する。

        Returns:
            みがわりの残りHP（volatileのみがわりから取得）

        Note:
            volatile["みがわり"]が存在しない場合は0を返す。
        """
        if self.has_volatile("みがわり"):
            return self.volatiles["みがわり"].hp
        return 0

    @sub_hp.setter
    def sub_hp(self, value: int):
        """みがわりの残りHPを設定する。

        Args:
            value: 設定するHP値

        Note:
            内部的にvolatile["みがわり"]を管理するため、
            テストやデバッグ用に使用される。
        """
        if value <= 0:
            # sub_hpが0以下の場合は状態を削除
            if self.has_volatile("みがわり"):
                del self.volatiles["みがわり"]
        else:
            # みがわり状態を作成または更新
            if not self.has_volatile("みがわり"):
                self.volatiles["みがわり"] = Volatile("みがわり", count=0)
            self.volatiles["みがわり"].hp = value

    def get_move(self, move: str) -> Move | None:
        """技を検索する。

        Args:
            move: 技名

        Returns:
            見つかった場合はMoveオブジェクト、見つからなければNone
        """
        for m in self.moves:
            if m.name == move:
                return m
        return None

    def has_ailment(self, name: AilmentName) -> bool:
        """指定された状態異常を持っているか判定する。

        Args:
            name: 状態異常名

        Returns:
            指定状態異常を持っていればTrue
        """
        return self.ailment.is_active and self.ailment.name == name

    def has_volatile(self, name: VolatileName) -> bool:
        """指定された揮発性状態を持っているか判定する。

        Args:
            name: 揮発性状態名

        Returns:
            指定揮発性状態を持っていればTrue
        """
        return name in self.volatiles

    def get_volatile(self, name: VolatileName) -> Volatile | None:
        """揮発性状態を取得する。

        Args:
            name: 揮発性状態名

        Returns:
            指定された揮発性状態があればそのVolatileオブジェクト、なければNone
        """
        return self.volatiles.get(name, None)
