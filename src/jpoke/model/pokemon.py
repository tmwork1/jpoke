"""ポケモンモデルを定義するモジュール。

ポケモンの基本情報、ステータス、特性、持ち物、技、状態異常、
ランク変化など、バトル中のポケモンの全状態を管理します。
"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core.event import EventManager

from jpoke.utils.type_defs import Nature, PokeType, Stat, MoveCategory, Gender, BoostSource, AilmentName, VolatileName
from jpoke.utils.constants import RANK_MIN, RANK_MAX, STATS
from jpoke.utils import fast_copy

from jpoke.core.event import Event, EventContext
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
        is_terastallized: テラスタル済みかどうか
    """

    def __init__(self,
                 name: str,
                 gender: Gender = "",
                 nature: Nature = "まじめ",
                 level: int = 50,
                 ability: str | Ability = "",
                 item: str | Item = "",
                 moves: list[str | Move] = ["はねる"],
                 terastal: PokeType = "ステラ") -> None:
        """ポケモンを初期化する。

        Args:
            name: ポケモン名
            gender: 性別（"オス"/"メス"/""）
            nature: 性格
            level: レベル（デフォルト50）
            ability: 特性（文字列またはAbilityインスタンス）
            item: 持ち物（文字列またはItemインスタンス）
            moves: 技のリスト（文字列またはMoveインスタンスのリスト）
            terastal: テラスタルタイプ
        """
        self.data = pokedex[name]
        self.gender: Gender = gender
        self._nature: Nature = nature
        self._level: int = level
        self._terastal: PokeType = terastal

        # 内部変数の初期化
        self._ability: Ability = Ability()
        self._item: Item = Item()
        self._moves: list[Move] = []

        # プロパティ経由で設定
        self.ability = ability
        self.item = item
        self.moves = moves

        # ステータス計算マネージャー
        self._stats_manager = PokemonStats()

        # 初期ステータス計算
        self.update_stats()

        self.init_game()

    def init_game(self):
        """ゲーム初期化処理。
        ポケモンのバトル状態を初期化する。
        """
        self.revealed = False
        self.is_terastallized: bool = False
        self._hp: int = self.max_hp
        self.ailment: Ailment = Ailment()

        # 場に出ているときの状態をリセット
        self.bench_reset()

    def bench_reset(self):
        """ベンチに戻ったときのリセット処理"""
        self.volatiles: dict[str, Volatile] = {}
        self.active_turn: int = 0
        self.hits_taken: int = 0
        self.rank: dict[Stat, int] = {k: 0 for k in STATS}
        self.executed_move: Move | None = None

    @classmethod
    def reconstruct_from_log(cls, data: dict) -> Pokemon:
        """ログデータからポケモンを復元する。

        Args:
            data: ポケモンのログデータ（辞書形式）

        Returns:
            復元されたPokemonインスタンス

        Note:
            特性、持ち物、技の復元は未実装
            これらのデータはログに含まれていない、または
            復元ロジックが複雑なため保留中
        """
        # TODO: (保留) ability, item, movesの復元
        # データ形式の設計とcreate_*メソッドの実装が必要
        # - mon.ability = cls.create_ability(data["ability"])
        # - mon.item = cls.create_item(data["item"])
        # - mon.moves = [cls.create_move(s) for s in data["moves"]]
        mon = cls(data["name"])
        mon.gender = data["gender"]
        mon.level = data["level"]
        mon.nature = data["nature"]
        mon.indiv = data["indiv"]
        mon.effort = data["effort"]
        mon.terastal = data["terastal"]
        return mon

    def __deepcopy__(self, memo):
        """ディープコピーを作成する。

        Args:
            memo: コピー済みオブジェクトのメモ辞書

        Returns:
            Pokemon: コピーされたインスタンス
        """
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        fast_copy(self, new, keys_to_deepcopy=[
            'ability', 'item', 'moves', 'ailment', 'volatiles',
            'executed_move', 'pp_consumed_moves',
            '_stats_manager',
        ])
        return new

    def __str__(self):
        """ポケモンの情報を文字列化する。

        Returns:
            str: ポケモンの詳細情報
        """
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
        for st, ef in zip(self._stats_manager.stats, self._stats_manager.effort):
            s += f"{st}({ef})-" if ef else f"{st}-"
        s = s[:-1] + sep
        s += "/".join(move.name for move in self.moves)
        return s

    def to_dict(self) -> dict:
        """ポケモンの情報を辞書形式で返す。

        Returns:
            ポケモンの全情報を含む辞書
        """
        return {
            "name": self.orig_name,
            "gender": self.gender,
            "level": self._level,
            "nature": self._nature,
            "ability": self.ability.name,
            "item": self.item.name,
            "moves": [move.name for move in self.moves],
            "indiv": self._stats_manager.indiv,
            "effort": self._stats_manager.effort,
            "terastal": self._terastal,
        }

    def switch_in(self, events: EventManager):
        """ポケモンを場に出す。

        Args:
            events: イベントマネージャー

        Note:
            特性、持ち物、状態異常、揮発性状態のハンドラを登録し、
            observedフラグをTrueにする。
        """
        self.revealed = True
        self.ability.register_handlers(events, self)
        self.item.register_handlers(events, self)
        self.ailment.register_handlers(events, self)
        for volatile in self.volatiles.values():
            volatile.register_handlers(events, self)

    def switch_out(self, events: EventManager):
        """ポケモンを引っ込める。

        Args:
            events: イベントマネージャー

        Note:
            バトル状態をリセットし、全てのハンドラを解除する。
        """
        self.bench_reset()
        self.ability.unregister_handlers(events, self)
        self.item.unregister_handlers(events, self)
        self.ailment.unregister_handlers(events, self)
        for volatile in self.volatiles.values():
            volatile.unregister_handlers(events, self)

    @property
    def name(self) -> str:
        """ポケモンの名前を取得する。

        Returns:
            ポケモンの種族名
        """
        return self.data.name

    @property
    def alive(self) -> bool:
        """ポケモンが生存しているかどうかを取得する。

        Returns:
            HPが0より大きい場合True
        """
        return self.hp > 0

    @property
    def faited(self) -> bool:
        """ポケモンが瀕死状態かどうかを取得する。

        Returns:
            HPが0の場合True
        """
        return self.hp == 0

    @property
    def hp(self) -> int:
        """ポケモンの現在HPを取得する。

        Returns:
            現在のHP
        """
        return self._hp

    @hp.setter
    def hp(self, value: int):
        """HPの直接代入を防止する。

        HPを変更する場合は、battle.modify_hp()を使用してください。
        これにより、HP=0時の勝敗判定が漏れなくなります。

        Raises:
            AttributeError: 直接代入しようとした場合
        """
        raise AttributeError(
            "HPを直接代入することはできません。"
            "battle.modify_hp(pokemon, v)を使用してください。"
        )

    @property
    def ability(self) -> Ability:
        """特性を取得する。

        Returns:
            特性オブジェクト
        """
        return self._ability

    @ability.setter
    def ability(self, obj: str | Ability):
        """特性を設定する。

        Args:
            obj: 特性名またはAbilityオブジェクト
        """
        if isinstance(obj, str):
            obj = Ability(obj)
        self._ability = obj

    @property
    def item(self) -> Item:
        """持ち物を取得する。

        Returns:
            持ち物オブジェクト
        """
        return self._item

    @item.setter
    def item(self, obj: str | Item):
        """持ち物を設定する。

        Args:
            obj: 持ち物名またはItemオブジェクト
        """
        if isinstance(obj, str):
            obj = Item(obj)
        self._item = obj

    @property
    def moves(self) -> list[Move]:
        """技のリストを取得する。

        Returns:
            技オブジェクトのリスト
        """
        return self._moves

    @moves.setter
    def moves(self, objs: list[str | Move]):
        """技のリストを設定する。

        Args:
            objs: 技名またはMoveオブジェクトのリスト
        """
        self._moves = [Move(obj) if isinstance(obj, str) else obj
                       for obj in objs]

    @property
    def types(self) -> list[str]:
        """ポケモンの現在のタイプを取得する。

        Returns:
            タイプのリスト

        Note:
            テラスタル、タイプ追加/削除効果を考慮した現在のタイプを返す。
            アルセウスのタイプ変化は未実装（TODO）。
        """
        if self.terastal:
            if self.terastal == 'ステラ':
                return self.data.types
            else:
                return [self.terastal]
        else:
            if self.name == 'アルセウス':
                # TODO: アルセウスのタイプ変化
                return ["ノーマル"]
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

    @hp_ratio.setter
    def hp_ratio(self, v: float):
        """現在のHPを割合で設定する。

        Args:
            v: HP割合（0.0～1.0）
        """
        self._hp = int(self.max_hp * v)

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
        """ポケモンの性格を取得する。

        Returns:
            性格名
        """
        return self._nature

    @nature.setter
    def nature(self, nature: str):
        """ポケモンの性格を設定する。

        Args:
            nature: 性格名

        Note:
            性格変更時にステータスを自動再計算する。
        """
        self._nature = nature
        self.update_stats()

    @property
    def terastal(self) -> str | None:
        """テラスタルのタイプを取得する。

        Returns:
            テラスタル済みの場合はタイプ名、そうでなければNone
        """
        return self._terastal if self.is_terastallized else None

    @terastal.setter
    def terastal(self, type: str):
        """テラスタルのタイプを設定する。

        Args:
            type: テラスタルのタイプ
        """
        self._terastal = type

    def can_terastallize(self) -> bool:
        """テラスタル可能かどうかを判定する。

        Returns:
            テラスタル可能な場合True
        """
        return not self.is_terastallized and self._terastal is not None

    def terastallize(self) -> bool:
        """テラスタルを実行する。

        Returns:
            テラスタルに成功した場合True
        """
        self.is_terastallized = self.can_terastallize()
        return self.is_terastallized

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

    def has_type(self, type_: PokeType) -> bool:
        """指定されたタイプを持っているか判定する。

        Args:
            type_: タイプ名

        Returns:
            指定タイプを持っていればTrue
        """
        return type_ in self.types

    def has_move(self, move: Move | str) -> bool:
        """指定された技を持っているか判定する。

        Args:
            move: 技名またはMoveオブジェクト

        Returns:
            指定技を持っていればTrue
        """
        return self.find_move(move) is not None

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
            self._hp = self.max_hp - damage

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
        old = self._hp
        self._hp = max(0, min(self.max_hp, old + v))
        return self._hp - old

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
            volatile["急所ランク"]が存在しない場合は0を返す。
        """
        if self.check_volatile("急所ランク"):
            return self.volatiles["急所ランク"].count
        return 0

    @critical_rank.setter
    def critical_rank(self, value: int):
        """急所ランクを設定する。

        Args:
            value: 設定する急所ランク値

        Note:
            内部的にvolatile["急所ランク"]を管理するため、
            テストやデバッグ用に使用される。
        """
        if value <= 0:
            # 急所ランクが0以下の場合は状態を削除
            if self.check_volatile("急所ランク"):
                del self.volatiles["急所ランク"]
        else:
            # 急所ランク状態を作成または更新
            if not self.check_volatile("急所ランク"):
                self.volatiles["急所ランク"] = Volatile("急所ランク", count=0)
            self.volatiles["急所ランク"].count = value

    @property
    def sub_hp(self) -> int:
        """みがわりの残りHPを取得する。

        Returns:
            みがわりの残りHP（volatileのみがわりから取得）

        Note:
            volatile["みがわり"]が存在しない場合は0を返す。
        """
        if self.check_volatile("みがわり"):
            return self.volatiles["みがわり"].sub_hp
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
            if self.check_volatile("みがわり"):
                del self.volatiles["みがわり"]
        else:
            # みがわり状態を作成または更新
            if not self.check_volatile("みがわり"):
                self.volatiles["みがわり"] = Volatile("みがわり", count=0)
            self.volatiles["みがわり"].sub_hp = value

    def find_move(self, move: Move | str) -> Move | None:
        """技を検索する。

        Args:
            move: 技名またはMoveオブジェクト

        Returns:
            見つかった場合はMoveオブジェクト、見つからなければNone
        """
        for mv in self.moves:
            if move in [mv, mv.name]:
                return mv

    def is_floating(self, events: EventManager) -> bool:
        """浮いている状態か判定する。

        Args:
            events: イベントマネージャー

        Returns:
            浮いていればTrue

        Note:
            タイプや特性、技の効果を考慮して判定する。
        """
        floating = "ひこう" in self.types
        floating &= events.emit(
            Event.ON_CHECK_FLOATING,
            EventContext(source=self),
            floating
        )
        return floating

    def is_trapped(self, events: EventManager) -> bool:
        """逃げられない状態か判定する。

        Args:
            events: イベントマネージャー

        Returns:
            逃げられない場合True

        Note:
            ゴーストタイプは逃げられる。
        """
        trapped = events.emit(
            Event.ON_CHECK_TRAPPED,
            EventContext(source=self),
            False
        )
        trapped &= "ゴースト" not in self.types
        return trapped

    def is_nervous(self, events: EventManager) -> bool:
        """びんじょう状態か判定する。

        Args:
            events: イベントマネージャー

        Returns:
            びんじょう状態の場合True
        """
        return events.emit(
            Event.ON_CHECK_NERVOUS,
            EventContext(source=self),
            False
        )

    def effective_move_type(self, move: Move, events: EventManager) -> str:
        """技の有効タイプを取得する。

        Args:
            move: 技オブジェクト
            events: イベントマネージャー

        Returns:
            有効タイプ

        Note:
            特性や効果によるタイプ変化を考慮する。
        """
        events.emit(
            Event.ON_CHECK_MOVE_TYPE,
            EventContext(source=self, move=move)
        )
        return move._type

    def effective_move_category(self, move: Move, events: EventManager) -> MoveCategory:
        """技の有効分類を取得する。

        Args:
            move: 技オブジェクト
            events: イベントマネージャー

        Returns:
            有効分類（物理、特殊、変化）

        Note:
            特性や効果による分類変化を考慮する。
        """
        return events.emit(
            Event.ON_CHECK_MOVE_CATEGORY,
            EventContext(source=self, move=move),
            value=move.category
        )

    def apply_ailment(self,
                      events: EventManager,
                      name: AilmentName,
                      source: Pokemon | None = None,
                      force: bool = False) -> bool:
        """状態異常を付与する。

        Args:
            events: イベントマネージャー
            name: 状態異常名
            source: 状態異常の原因となったポケモン
            force: Trueの場合、既存の状態異常を上書き

        Returns:
            付与に成功したTrue

        Note:
            - force=Falseの場合、既に状態異常があれば失敗
            - 同じ状態異常の重ね掛けは不可
        """
        # force=True でない限り上書き不可
        if self.ailment.is_active and not force:
            return False
        # 重ねがけ不可
        if name == self.ailment.name:
            return False

        # ON_BEFORE_APPLY_AILMENT イベントを発火して特性などによる無効化をチェック
        # ハンドラーがvalueを空文字列に変更した場合は状態異常を防ぐ
        if not events.emit(
            Event.ON_BEFORE_APPLY_AILMENT,
            EventContext(target=self, source=source),
            name
        ):
            return False

        # 既存のハンドラを削除
        if self.ailment.is_active:
            self.ailment.unregister_handlers(events, self)
        # 新しい状態異常を設定してハンドラ登録
        self.ailment = Ailment(name)
        self.ailment.register_handlers(events, self)
        return True

    def cure_ailment(self, events: EventManager, source: Pokemon | None = None) -> bool:
        """状態異常を治療する。

        Args:
            events: イベントマネージャー
            source: 治療の原因となったポケモン

        Returns:
            治療に成功したらTrue
        """
        if not self.ailment.is_active:
            return False
        self.ailment.unregister_handlers(events, self)
        self.ailment = Ailment("")
        return True

    def check_volatile(self, name: VolatileName) -> bool:
        """指定された揮発性状態を持っているか判定する。

        Args:
            name: 揮発性状態名

        Returns:
            指定揮発性状態を持っていればTrue
        """
        return name in self.volatiles and self.volatiles[name].is_active

    def apply_volatile(self,
                       events: EventManager,
                       name: VolatileName,
                       count: int = 1,
                       source: Pokemon | None = None) -> bool:
        """揮発性状態を付与する。

        Args:
            events: イベントマネージャー
            name: 揮発性状態名
            source: 揮発性状態の原因となったポケモン

        Returns:
            付与に成功したTrue

        Note:
            - force=Falseの場合、既に同じ揮発性状態があれば失敗
        """
        # 既に同じ揮発性状態がある場合は失敗
        if self.check_volatile(name):
            return False

        # ON_BEFORE_APPLY_VOLATILE イベントを発火して特性やフィールドによる無効化をチェック
        # ハンドラーがvalueを空文字列に変更した場合は揮発状態を防ぐ
        if not events.emit(
            Event.ON_BEFORE_APPLY_VOLATILE,
            EventContext(target=self, move=None, attacker=source, defender=None),
            name
        ):
            return False

        volatile = Volatile(name, count=count)
        volatile.source_pokemon = source
        volatile.register_handlers(events, self)
        self.volatiles[name] = volatile
        return True

    def remove_volatile(self,
                        events: EventManager,
                        name: VolatileName,
                        source: Pokemon | None = None) -> bool:
        """揮発性状態を解除する。

        Args:
            events: イベントマネージャー
            name: 揮発性状態名
            source: 解除の原因となったポケモン

        Returns:
            解除に成功したTrue

        Note:
            指定された揮発性状態がない場合は失敗する。
        """
        if not self.check_volatile(name):
            return False
        self.volatiles.pop(name).unregister_handlers(events, self)
        return True
