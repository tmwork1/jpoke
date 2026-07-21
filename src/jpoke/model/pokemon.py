"""ポケモンモデルを定義するモジュール。

ポケモンの基本情報、ステータス、特性、アイテム、技、状態異常、
ランク変化など、バトル中のポケモンの全状態を管理します。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Literal
if TYPE_CHECKING:
    from jpoke.data.models import PokemonData

from jpoke.types import Nature, Type, Stat, Gender, HpPolicy, \
    AilmentName, VolatileName, BoostSource, PokemonName, AbilityName, MoveName, ItemName
from jpoke.utils.constants import STATS, STAT_RANK_MIN, STAT_RANK_MAX
from jpoke.utils import math as m
from jpoke.utils import fast_copy
from jpoke.data.pokedex import POKEDEX
from jpoke.data.megaevol import MEGA_STONES, MEGA_POKEMONS
from jpoke.data.nature import NATURE_MODIFIER

from .ability import Ability
from .item import Item
from .move import Move
from .ailment import Ailment
from .volatile import Volatile
from .stats import calc_hp, calc_stat, chmp_to_legacy_effort


class Pokemon:
    """ポケモンクラス。

    ポケモンの全状態と機能を管理するメインクラスです。
    種族値、個体値、努力値、性格からステータスを計算し、
    特性、アイテム、技、状態異常、ランク変化などを管理します。

    Attributes:
        data: ポケモン図鑑データ
        gender: 性別
        hp: 現在HP

            単なる属性であり代入自体はエラーなく成功するが、対戦シミュレーション中に
            直接代入するとON_HP_CHANGE系ハンドラの発火・瀕死判定がスキップされ内部状態が
            不整合になる。対戦を進行させる文脈では必ず `Battle.modify_hp()` を使うこと。
            ダメージ計算のみを行いハンドラ起動を意図的に避けたい場合はこの限りではない。
        max_hp: 最大HP
        ailment: 状態異常
        ability: 特性
        item: アイテム
        moves: 覚えている技のリスト
        boosts: 能力ランクの辞書
        volatiles: 揮発状態の辞書
        is_terastallized: テラスタル済みかどうか
    """

    # ── 初期化・コピー ──────────────────────────────────────────

    def __init__(self,
                 name: PokemonName,
                 gender: Gender = "",
                 nature: Nature = "まじめ",
                 level: int = 50,
                 ability_name: AbilityName = "",
                 item_name: ItemName = "",
                 move_names: list[MoveName] | None = None,
                 tera_type: Type | None = None) -> None:
        """ポケモンを初期化する。

        Args:
            name: ポケモン名
            gender: 性別（"male"/"female"/""）
            nature: 性格（デフォルト"まじめ"、ステータス補正なし）
            level: レベル（デフォルト50）
            ability_name: 特性（文字列、デフォルト""＝特性なし扱い）
            item_name: アイテム（文字列、デフォルト""＝アイテムなし）
            move_names: 技のリスト（文字列のリスト、省略時は["はねる"]の1技のみ
                になるため、実際に戦わせる場合は必ず指定する）
            tera_type: テラスタルタイプ（デフォルトNoneの場合、そのポケモンの
                第1タイプを引き継ぐ）

        Note:
            個体値・努力値はコンストラクタの引数ではなく、初期状態は
            個体値31・努力値0固定で生成される。変更する場合は生成後に
            `set_ivs()` / `set_evs()` を呼ぶ。
        """
        self.data: PokemonData = POKEDEX[name]
        self.gender: Gender = gender
        self._nature: Nature = nature
        self._level: int = level

        self.tera_type: Type = tera_type or self.base_types[0]

        self.ability: Ability = Ability(ability_name)
        self.base_ability: AbilityName = ability_name

        self.item = Item(item_name)

        self.set_moves(move_names if move_names is not None else ["はねる"])

        # ステータス（実数値・個体値・努力値）
        self._stats: list[int] = [100]*6
        self._ivs: list[int] = [31]*6
        self._evs: list[int] = [0]*6

        # 初期ステータス計算（hp は未定義のため update_stats() の hp 追従処理は経由しない）
        self._recalc_stats()

        # バトル中に利用する属性はコンストラクタで明示的に定義する。
        self.revealed: bool = False
        self.is_terastallized: bool = False
        self.hp: int = self.max_hp
        self.ailment: Ailment = Ailment()
        self.volatiles: dict[VolatileName, Volatile] = {}
        self.boosts: dict[Stat, int] = {k: 0 for k in STATS}
        self.last_move: Move | None = None
        # トップレベルで選択した技（ねごと等のネスト実行では更新されない、アンコール等用）。
        self.selected_move: Move | None = None
        # 最後にPPを消費した技（かなしばり・うらみ等用。複数形pp_consumed_movesとは別）。
        self.pp_consumed_move: Move | None = None

        # スコープ付きメモリ。技・特性個別のフラグはここに保存し、
        # リセットはスコープ単位（turn: ターン開始 / switch: 登場時・退場時 / battle: リセットなし）
        # で一括して行う。新しいフラグを追加してもリセット処理の追記は不要。
        # 代表的なフラグへのアクセスは下部のプロパティ（スコープ付きメモリ節）を参照。
        self.memory: dict[str, dict[str, Any]] = {
            "turn": {}, "switch": {}, "battle": {}
        }

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        fast_copy(self, new, keys_to_deepcopy=[
            'ability', 'item', 'moves', 'ailment', 'volatiles',
            'last_move', 'selected_move', 'pp_consumed_move', 'memory',
        ])
        return new

    # ── リセット ────────────────────────────────────────────────

    def reset_on_switch_in(self):
        self.revealed = True
        self.memory["switch"] = {}

    def reset_on_switch_out(self):
        # へんしん/かわりものによる変身の復元（技・性別を戻す。特性・実数値ステータス・
        # 能力ランクは以下の既存リセット処理がそのまま兼ねる）。
        if self.pre_transform_moves is not None:
            self.moves = self.pre_transform_moves
            self.gender = self.pre_transform_gender

        # switch スコープは登場時だけでなく退場時にも即座にクリアする
        # （タイプ上書き系・上記の変身関連フラグなど、退場直後に戻す必要があるフラグを収容するため）
        self.memory["switch"] = {}

        self.boosts = {k: 0 for k in STATS}
        # ガードシェア・パワーシェア・パワートリックなどによる実数値の書き換えを
        # 種族値ベースの値に再計算してリセットする（交代でリセットされる仕様）
        self.update_stats()
        self.last_move = None
        self.selected_move = None
        self.pp_consumed_move = None
        self.ability.activated_since_switch_in = False

        # 特性の状態をリセット
        # 特性が変わっている場合は特性自体をリセットする
        if self.ability.base_name != self.base_ability:
            self.ability = Ability(self.base_ability)
        else:
            self.ability.reset_on_switch_out()

        # アイテムの状態をリセット
        self.item.reset_on_switch_out()

        # 状態異常の経過ターンをリセット（もうどくは交代でカウントが1/16からやり直し）
        self.ailment.reset_on_switch_out()

    def reset_turn_state(self):
        """ターン初期化処理。"""
        self.memory["turn"] = {}

    # ── スコープ付きメモリ ──────────────────────────────────────
    # 技・特性個別のフラグへのアクセサ。実体は memory の各スコープに保存され、
    # reset_turn_state / reset_on_switch_in / reset_on_switch_out でスコープごと一括クリアされる。

    @property
    def stat_lowered_this_turn(self) -> bool:
        """このターン中にランクが下がったか（うっぷんばらし用）。"""
        return self.memory["turn"].get("stat_lowered", False)

    @stat_lowered_this_turn.setter
    def stat_lowered_this_turn(self, value: bool):
        self.memory["turn"]["stat_lowered"] = value

    @property
    def sleep_talk_active(self) -> bool:
        """ねごとによるサブ技実行中フラグ。呼び出し元のtry/finallyで必ずFalseに戻される。"""
        return self.memory["turn"].get("sleep_talk_active", False)

    @sleep_talk_active.setter
    def sleep_talk_active(self, value: bool):
        self.memory["turn"]["sleep_talk_active"] = value

    @property
    def metronome_active(self) -> bool:
        """ゆびをふるによるサブ技実行中フラグ。呼び出し元のtry/finallyで必ずFalseに戻される。"""
        return self.memory["turn"].get("metronome_active", False)

    @metronome_active.setter
    def metronome_active(self, value: bool):
        self.memory["turn"]["metronome_active"] = value

    @property
    def copycat_active(self) -> bool:
        """まねっこによるサブ技実行中フラグ。呼び出し元のtry/finallyで必ずFalseに戻される。"""
        return self.memory["turn"].get("copycat_active", False)

    @copycat_active.setter
    def copycat_active(self, value: bool):
        self.memory["turn"]["copycat_active"] = value

    @property
    def hits_taken(self) -> int:
        """このターン中に受けた攻撃回数（カウント等）。"""
        return self.memory["turn"].get("hits_taken", 0)

    @hits_taken.setter
    def hits_taken(self, value: int):
        self.memory["turn"]["hits_taken"] = value

    @property
    def last_damage_taken(self) -> dict[str, Any]:
        """今ターン最後に受けたダメージ情報（damage: 量, category: "physical"/"special"/None）。"""
        return self.memory["turn"].setdefault("last_damage_taken", {"damage": 0, "category": None})

    @last_damage_taken.setter
    def last_damage_taken(self, value: dict[str, Any]):
        self.memory["turn"]["last_damage_taken"] = value

    @property
    def last_damage_received(self) -> int:
        """今ターン最後に受けたダメージ量（種別問わず）。"""
        return self.last_damage_taken["damage"]

    @property
    def last_physical_damage_received(self) -> int:
        """今ターン最後に受けた物理ダメージ量（カウンター等の反射元）。"""
        info = self.last_damage_taken
        return info["damage"] if info["category"] == "physical" else 0

    @property
    def last_special_damage_received(self) -> int:
        """今ターン最後に受けた特殊ダメージ量（ミラーコート等の反射元）。"""
        info = self.last_damage_taken
        return info["damage"] if info["category"] == "special" else 0

    @property
    def stat_raised_this_turn(self) -> bool:
        """このターン中にランクが上がったか（みわくのボイス・しっとのほのお用）。"""
        return self.memory["turn"].get("stat_raised", False)

    @stat_raised_this_turn.setter
    def stat_raised_this_turn(self, value: bool):
        self.memory["turn"]["stat_raised"] = value

    @property
    def failed_or_immobile_last_turn(self) -> bool:
        """前のターンに行動不能または技が失敗したか（やけっぱち・じだんだ用）。"""
        return self.memory["switch"].get("failed_or_immobile", False)

    @failed_or_immobile_last_turn.setter
    def failed_or_immobile_last_turn(self, value: bool):
        self.memory["switch"]["failed_or_immobile"] = value

    @property
    def acted_since_switch_in(self) -> bool:
        """場に出てから一度でも行動したか（であいがしら用）。"""
        return self.memory["switch"].get("acted", False)

    @acted_since_switch_in.setter
    def acted_since_switch_in(self, value: bool):
        self.memory["switch"]["acted"] = value

    @property
    def pp_consumed_moves(self) -> set[MoveName]:
        """場に出てからPPを消費した技名の集合（とっておき用。単数形と別）。"""
        return self.memory["switch"].setdefault("pp_consumed_moves", set())

    @pp_consumed_moves.setter
    def pp_consumed_moves(self, value: set[MoveName]):
        self.memory["switch"]["pp_consumed_moves"] = value

    @property
    def ability_override_type(self) -> Type | None:
        """特性によるタイプ上書き（へんげんじざい等）。登場・退場時にリセットされる。"""
        return self.memory["switch"].get("ability_override_type")

    @ability_override_type.setter
    def ability_override_type(self, value: Type | None):
        self.memory["switch"]["ability_override_type"] = value

    @property
    def move_override_types(self) -> list[Type] | None:
        """技によるタイプ上書き（テクスチャー・ミラータイプ等）。登場・退場時にリセットされる。"""
        return self.memory["switch"].get("move_override_types")

    @move_override_types.setter
    def move_override_types(self, value: list[Type] | None):
        self.memory["switch"]["move_override_types"] = value

    @property
    def volatile_override_type(self) -> Type | None:
        """揮発性状態によるタイプ上書き（まほうのこな・みずびたし等）。登場・退場時にリセットされる。"""
        return self.memory["switch"].get("volatile_override_type")

    @volatile_override_type.setter
    def volatile_override_type(self, value: Type | None):
        self.memory["switch"]["volatile_override_type"] = value

    @property
    def added_types(self) -> list[Type]:
        """技・特性等で追加されたタイプ（ハロウィン・もりののろい等）。登場・退場時にリセットされる。"""
        return self.memory["switch"].setdefault("added_types", [])

    @added_types.setter
    def added_types(self, value: list[Type]):
        self.memory["switch"]["added_types"] = value

    @property
    def removed_types(self) -> list[Type]:
        """はねやすめ等によるタイプ除去。登場・退場時にリセットされる。"""
        return self.memory["switch"].setdefault("removed_types", [])

    @removed_types.setter
    def removed_types(self, value: list[Type]):
        self.memory["switch"]["removed_types"] = value

    @property
    def transform_types(self) -> list[Type] | None:
        """へんしん/かわりもので変身中のコピー元タイプ（種族データ自体は変更しない）。"""
        return self.memory["switch"].get("transform_types")

    @transform_types.setter
    def transform_types(self, value: list[Type] | None):
        self.memory["switch"]["transform_types"] = value

    @property
    def transform_weight(self) -> float | None:
        """へんしん/かわりもので変身中のコピー元体重（種族データ自体は変更しない）。"""
        return self.memory["switch"].get("transform_weight")

    @transform_weight.setter
    def transform_weight(self, value: float | None):
        self.memory["switch"]["transform_weight"] = value

    @property
    def pre_transform_moves(self) -> list[Move] | None:
        """変身前の技リストのスナップショット（変身中のみ非None）。reset_on_switch_outで復元。"""
        return self.memory["switch"].get("pre_transform_moves")

    @pre_transform_moves.setter
    def pre_transform_moves(self, value: list[Move] | None):
        self.memory["switch"]["pre_transform_moves"] = value

    @property
    def pre_transform_gender(self) -> Gender | None:
        """変身前の性別のスナップショット（変身中のみ非None）。reset_on_switch_outで復元。"""
        return self.memory["switch"].get("pre_transform_gender")

    @pre_transform_gender.setter
    def pre_transform_gender(self, value: Gender | None):
        self.memory["switch"]["pre_transform_gender"] = value

    @property
    def last_lost_item_name(self) -> ItemName:
        """直近で失った（消費・奪取された）アイテム名（ものひろい・しゅうかく用）。

        リサイクル・しゅうかく等は交代して控えに戻っても記憶を保持するため、
        switch スコープではなく battle スコープ（バトル中リセットなし）に保存する。
        """
        return self.memory["battle"].get("last_lost_item_name", "")

    @last_lost_item_name.setter
    def last_lost_item_name(self, value: ItemName):
        self.memory["battle"]["last_lost_item_name"] = value

    @property
    def last_lost_item_turn(self) -> int:
        """直近で `last_lost_item_name` が更新されたターン数（ものひろい用）。

        しゅうかく等はターンをまたいでも last_lost_item_name を参照するため、
        こちらは battle スコープで保持しつつ「そのターンに限定する」判定にのみ使う。
        """
        return self.memory["battle"].get("last_lost_item_turn", -1)

    @last_lost_item_turn.setter
    def last_lost_item_turn(self, value: int):
        self.memory["battle"]["last_lost_item_turn"] = value

    @property
    def paradox_boost_stat(self) -> Stat | None:
        """パラドックス特性で強化されているステータス。登場・退場時にリセットされる。"""
        return self.memory["switch"].get("paradox_boost_stat")

    @paradox_boost_stat.setter
    def paradox_boost_stat(self, value: Stat | None):
        self.memory["switch"]["paradox_boost_stat"] = value

    @property
    def paradox_boost_source(self) -> BoostSource:
        """パラドックス補正の発動要因。登場・退場時にリセットされる。"""
        return self.memory["switch"].get("paradox_boost_source", "")

    @paradox_boost_source.setter
    def paradox_boost_source(self, value: BoostSource):
        self.memory["switch"]["paradox_boost_source"] = value

    @property
    def ate_berry(self) -> bool:
        """今バトル中にきのみを食べたかどうか（ゲップの使用条件）。"""
        return self.memory["battle"].get("ate_berry", False)

    @ate_berry.setter
    def ate_berry(self, value: bool):
        self.memory["battle"]["ate_berry"] = value

    @property
    def stellar_boosted_types(self) -> set[Type]:
        """ステラテラスタルで威力補正が消費済みのタイプ集合（バトル中リセットされない）。"""
        return self.memory["battle"].setdefault("stellar_boosted_types", set())

    @property
    def last_move_type(self) -> Type | None:
        """直近で使用した技の実効タイプ（テクスチャー2用）。last_move から算出する。"""
        return self.last_move.type if self.last_move else None

    @property
    def last_move_name(self) -> MoveName | None:
        """直近で使用した技名（テクスチャー2用）。last_move から算出する。"""
        return self.last_move.name if self.last_move else None

    # ── 基本情報 ────────────────────────────────────────────────

    @property
    def name(self) -> PokemonName:
        """ポケモンの名前を取得する。

        Returns:
            ポケモンの種族名
        """
        return self.data.name

    @property
    def pre_evolution(self) -> PokemonName | Literal[""]:
        """1段階進化前のポケモン名を取得する。

        Returns:
            進化前ポケモン名。進化前がない場合は空文字列
        """
        return self.data.pre_evolution

    @property
    def level(self) -> int:
        """ポケモンのレベルを取得する。

        Returns:
            レベル
        """
        return self._level

    def set_level(self, level: int, hp_policy: HpPolicy = "keep_absolute"):
        """ポケモンのレベルを設定する。

        Args:
            level: レベル
            hp_policy: 最大HP変化時のhpの追従方法（HpPolicy参照）

        Note:
            レベル変更時にステータスを自動再計算する。
        """
        self._level = level
        self.update_stats(hp_policy)

    @property
    def nature(self) -> str:
        """ポケモンの性格を取得する。

        Returns:
            性格名
        """
        return self._nature

    def set_nature(self, nature: Nature, hp_policy: HpPolicy = "keep_absolute"):
        """ポケモンの性格を設定する。

        Args:
            nature: 性格名
            hp_policy: 最大HP変化時のhpの追従方法（HpPolicy参照）

        Note:
            性格変更時にステータスを自動再計算する。
        """
        self._nature = nature
        self.update_stats(hp_policy)

    @property
    def weight(self) -> float:
        """ポケモンの現在の体重を取得する。

        Returns:
            体重（kg）

        Note:
            特性（ライトメタル、ヘヴィメタル）や
            アイテム（かるいし）の効果を考慮した体重を返す。
            へんしん/かわりもので変身中は、コピー元の体重（transform_weight）を基準にする。
        """
        w = self.transform_weight if self.transform_weight is not None else self.data.weight
        match self.ability.name:
            case 'ライトメタル':
                w = int(w*0.5*10)/10
            case 'ヘヴィメタル':
                w *= 2
        if self.has_item('かるいし', consider_enabled=True):
            w = int(w*0.5*10)/10
        # おもさの最低値は0.1kg
        return max(w, 0.1)

    @property
    def base_types(self) -> list[Type]:
        """ポケモンの基本タイプを取得する。

        Returns:
            基本タイプのリスト
        """
        return self.data.types

    @property
    def types(self) -> list[Type]:
        """ポケモンの現在のタイプを取得する。

        Returns:
            タイプのリスト

        Note:
            テラスタル、タイプ追加/削除効果、added_types を考慮した現在のタイプを返す。
            added_types は ハロウィン・もりののろい などによって後付けされたタイプを保持する。
            へんしん/かわりもので変身中は、種族本来のタイプ（self.data.types）の代わりに
            コピー元のタイプ（transform_types）を基準にする。
        """
        base_types_ = self.transform_types if self.transform_types is not None else self.data.types
        if self.active_tera_type:
            if self.active_tera_type == 'ステラ':
                base = base_types_
            else:
                base = [self.active_tera_type]
        elif self.move_override_types is not None:
            base = self.move_override_types
        elif self.ability_override_type is not None:
            base = [self.ability_override_type]
        elif self.volatile_override_type is not None:
            base = [self.volatile_override_type]
        else:
            base = base_types_

        if not self.added_types:
            result = base
        else:
            # 既にベースタイプに含まれているものは除外して追加する
            extra = [t for t in self.added_types if t not in base]
            result = base + extra if extra else base
        # はねやすめ等によるタイプ除去を適用（テラスタル中は無視）
        if self.removed_types and not self.active_tera_type:
            result = [t for t in result if t not in self.removed_types]
        return result

    def has_type(self, type_: Type) -> bool:
        """指定されたタイプを持っているか判定する。

        Args:
            type_: タイプ名

        Returns:
            指定タイプを持っていればTrue
        """
        return type_ in self.types

    @property
    def learnset(self) -> frozenset[MoveName]:
        """覚えられる技名の集合を取得する。

        シングルバトルで戦闘に一切影響しない技（MoveFlag「no_effect_in_singles」参照）は
        あらかじめ除外する。data.moveの遅延インポートは、data.pokedex経由の循環インポートを
        避けるため（learnsetローダー自体はps-champ-ja由来の生データのみを保持する）。

        Returns:
            覚えられる技名の集合（ps-champ-ja由来のスナップショットから、対戦に影響しない技を除いたもの）
        """
        from jpoke.data.move import MOVES
        return frozenset(
            move for move in self.data.learnset
            if "no_effect_in_singles" not in MOVES[move].flags
        )

    def can_learn(self, move_name: MoveName) -> bool:
        """指定された技を覚えられるか判定する。

        Args:
            move_name: 技名

        Returns:
            覚えられる場合True
        """
        return move_name in self.learnset

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

    # ── フォルム変化・テラスタル・メガシンカ ────────────────────

    def set_form(self,
                 name: PokemonName,
                 hp_policy: HpPolicy = "keep_absolute",
                 set_default_ability: bool = False) -> bool:
        """ポケモンのフォルムをエイリアス指定で切り替える。

        Args:
            name: 変更先フォルムの図鑑エイリアス
            hp_policy: 最大HP変化時のhpの追従方法（HpPolicy参照）
            set_default_ability: Trueの場合、特性を変更先のデフォルト特性にリセットする
        """
        if self.name == name:
            return False

        self.data = POKEDEX[name]
        self.update_stats(hp_policy)

        if set_default_ability:
            ability_name = self.data.abilities[0]
            self.ability = Ability(ability_name)
            self.base_ability = self.ability.base_name

        return True

    @property
    def active_tera_type(self) -> Type:
        """テラスタルのタイプを取得する。

        Returns:
            テラスタル済みの場合はタイプ名、そうでなければNone
        """
        return self.tera_type if self.is_terastallized else ""

    def can_terastallize(self) -> bool:
        """テラスタル可能かどうかを判定する。

        Returns:
            テラスタル可能な場合True
        """
        return not self.is_terastallized and self.tera_type != ""

    def terastallize(self):
        """テラスタルする。

        `is_terastallized` を立てるだけの内部メソッドで、戻り値は常に `None`。
        `Event.ON_TERASTALLIZE` の発火や `can_terastallize()` の判定は行わないため、
        単体で呼び出さず `TurnController` がコマンド（`Command.get_terastal_command()`）を
        解決する経路（`Battle.step()` 等）から使うこと。
        """
        self.is_terastallized = True

    @property
    def megaevolved(self) -> bool:
        """メガシンカしているかどうかを判定する。"""
        return self.name in MEGA_POKEMONS

    def can_megaevolve(self) -> bool:
        """メガシンカ可能かどうかを判定する。"""
        forms = MEGA_STONES.get(self.item.name, None)
        if forms is None:
            return False
        return self.name in forms[:-1]  # 最後の要素はメガシンカ後のフォーム名

    def megaevolve(self):
        """メガシンカする。

        フォルムを切り替えるだけの内部メソッドで、戻り値は常に `None`。
        メガシンカ前後の特性ハンドラの付け替えや `Event.ON_ABILITY_ENABLED` の発火、
        `can_megaevolve()` の判定は行わないため、単体で呼び出さず `TurnController` が
        コマンド（`Command.get_megaevol_command()`）を解決する経路（`Battle.step()` 等）
        から使うこと。
        """
        mega_name = MEGA_STONES[self.item.name][-1]
        self.set_form(mega_name, set_default_ability=True)

    # ── ステータス ──────────────────────────────────────────────

    @property
    def base(self) -> list[int]:
        """種族値を取得する。

        Returns:
            種族値のリスト
        """
        return self.data.base

    def set_base(self, base: list[int], hp_policy: HpPolicy = "keep_absolute"):
        """種族値を設定する。

        Args:
            base: 種族値のリスト
            hp_policy: 最大HP変化時のhpの追従方法（HpPolicy参照）

        Note:
            種族値変更時にステータスを自動再計算する。
        """
        self.data.base = base
        self.update_stats(hp_policy)

    @property
    def ivs(self) -> list[int]:
        """個体値を取得する。

        Returns:
            個体値のリスト
        """
        return self._ivs

    def set_ivs(self, ivs: list[int] | dict[Stat, int], hp_policy: HpPolicy = "keep_absolute"):
        """個体値を設定する。

        Args:
            ivs: 個体値。`list[int]` の場合は6要素（HP, 攻撃, 防御, 特攻, 特防,
                素早さの順）で全体を置き換える。`dict[Stat, int]` の場合は
                指定したステータスのみ更新し、未指定のステータスは既存値を維持する
            hp_policy: 最大HP変化時のhpの追従方法（HpPolicy参照）

        Note:
            個体値変更時にステータスを自動再計算する。
        """
        if isinstance(ivs, dict):
            for stat, value in ivs.items():
                self._ivs[STATS.index(stat)] = value
        else:
            self._ivs = ivs
        self.update_stats(hp_policy)

    @property
    def evs(self) -> list[int]:
        """努力値をChampions形式（0〜32）で取得する。

        Note:
            poke-env の `evs`（各値0〜252）とは名前は同じだがスケールが異なる。
            poke-env形式からの変換は `types/poke_env.py` の `evs_from_poke_env` を使う。

        Returns:
            Champions形式の努力値のリスト
        """
        return self._evs

    def set_evs(self, evs: list[int] | dict[Stat, int], hp_policy: HpPolicy = "keep_absolute"):
        """努力値をChampions形式（0〜32）で設定する。

        Args:
            evs: Champions形式の努力値（各値0〜32）。`list[int]` の場合は6要素
                （HP, 攻撃, 防御, 特攻, 特防, 素早さの順）で全体を置き換える。
                `dict[Stat, int]` の場合は指定したステータスのみ更新し、
                未指定のステータスは既存値を維持する
            hp_policy: 最大HP変化時のhpの追従方法（HpPolicy参照）

        Note:
            努力値変更時にステータスを自動再計算する。
            poke-env の `evs`（各値0〜252）とはスケールが異なるため、
            poke-env形式の値をそのまま渡さないこと（`evs_from_poke_env` で変換する）。
        """
        if isinstance(evs, dict):
            for stat, value in evs.items():
                self._evs[STATS.index(stat)] = value
        else:
            self._evs = evs
        self.update_stats(hp_policy)

    @property
    def stats(self) -> dict[Stat, int]:
        """ステータスを辞書形式で取得する。

        Returns:
            ステータス名をキーとする実数値の辞書
        """
        labels = STATS[:6]
        return {s: v for s, v in zip(labels, self._stats)}

    def set_stats(self, stats: dict[Stat, int], hp_policy: HpPolicy = "keep_absolute"):
        """実数値から努力値を逆算して設定する。

        Args:
            stats: ステータス名をキー、実数値を値とする辞書
            hp_policy: 最大HP変化時のhpの追従方法（HpPolicy参照）

        Note:
            設定後、ステータスを自動再計算する。
        """
        for stat, value in stats.items():
            idx = STATS.index(stat)
            self._set_stat_from_value(idx, value)
        self.update_stats(hp_policy)

    def get_raw_stat(self, idx: int) -> int:
        """指定インデックスの実数値を取得する。

        Args:
            idx: ステータスのインデックス (0=HP, 1=攻撃, 2=防御, ...)
        """
        return self._stats[idx]

    def set_raw_stat(self, idx: int, value: int):
        """指定インデックスの実数値を努力値と無関係に直接書き換える。

        Note:
            ガードシェア・パワーシェア・パワートリック・スピードスワップなど、
            努力値の再計算を伴わずに実数値そのものを操作する専用効果でのみ使用する。
        """
        self._stats[idx] = value

    @property
    def ranked_stats(self) -> dict[Stat, int]:
        """能力ランク補正を反映したステータスを辞書形式で取得する。

        Returns:
            ステータス名をキーとする能力ランク補正を反映した実数値の辞書
        """
        return {s: int(v * self.rank_modifier(s)) for (s, v) in self.stats.items()}

    def rank_modifier(self, stat: Stat) -> float:
        """指定したステータスのランク補正を取得する。

        Args:
            stat: ステータス名

        Returns:
            ランク補正値
        """
        v = self.boosts[stat]
        return (2 + v) / 2 if v >= 0 else 2 / (2 - v)

    @property
    def max_hp(self) -> int:
        """最大HPを取得する。

        Returns:
            最大HP
        """
        return self._stats[0]

    @property
    def hp_fraction(self) -> float:
        """現在のHP割合を取得する。

        Returns:
            HP割合（0.0～1.0）
        """
        return self.hp / self.max_hp

    @property
    def paradox_boost_active(self) -> bool:
        """パラドックス補正が有効かどうかを取得する。"""
        return self.paradox_boost_stat is not None

    def _apply_hp_policy(self, old_max_hp: int, old_hp: int, hp_policy: HpPolicy):
        """新しい最大HPに対してhpを追従させる（HpPolicy参照）。"""
        if hp_policy == "reset":
            self.hp = self.max_hp
        elif hp_policy == "keep_ratio":
            ratio = old_hp / old_max_hp if old_max_hp else 0.0
            self.hp = max(0, min(self.max_hp, round(self.max_hp * ratio)))
        else:
            damage = old_max_hp - old_hp
            self.hp = max(0, min(self.max_hp, self.max_hp - damage))

    def _recalc_stats(self):
        """レベル・種族値・個体値・努力値・性格から実数値を再計算する。"""
        self._stats[0] = calc_hp(
            self._level, self.data.base[0],
            self._ivs[0], chmp_to_legacy_effort(self._evs[0])
        )

        nc = NATURE_MODIFIER[self._nature]
        for i in range(1, 6):
            self._stats[i] = calc_stat(
                self._level, self.data.base[i],
                self._ivs[i], chmp_to_legacy_effort(self._evs[i]), nc[i]
            )

    def _set_stat_from_value(self, idx: int, value: int) -> bool:
        """指定インデックスの実数値になるよう努力値を逆算して設定する。

        Note:
            Champions努力値（0〜32）に対応するSV等価値を前提とした逆算を行う。
            該当する努力値が見つからない場合は失敗する。
        """
        nc = NATURE_MODIFIER[self._nature]

        for chmp in range(33):
            eff = chmp_to_legacy_effort(chmp)
            if idx == 0:
                v = calc_hp(
                    self._level, self.data.base[idx], self._ivs[idx], eff)
            else:
                v = calc_stat(
                    self._level, self.data.base[idx], self._ivs[idx], eff, nc[idx])

            if v == value:
                self._evs[idx] = chmp
                self._stats[idx] = v
                return True

        return False

    def update_stats(self, hp_policy: HpPolicy = "keep_absolute"):
        """ステータスを再計算する。

        Args:
            hp_policy: 最大HP変化時のhpの追従方法（HpPolicy参照）

        Note:
            レベル、性格、種族値、個体値、努力値に基づいて
            全ステータスを再計算する。レベルアップや性格変更時に使用。
        """
        old_max_hp = self.max_hp
        old_hp = self.hp

        self._recalc_stats()

        self._apply_hp_policy(old_max_hp, old_hp, hp_policy)

    def set_stat(self, idx: int, value: int, hp_policy: HpPolicy = "keep_absolute") -> bool:
        """指定した実数値になるよう努力値を設定する。

        Args:
            idx: ステータスのインデックス(0=HP, 1=攻撃, 2=防御, ...)
            value: 目標の実数値
            hp_policy: 最大HP変化時のhpの追従方法（HpPolicy参照。idx=0の場合のみ関与する）

        Returns:
            設定に成功した場合True、失敗した場合False
        """
        old_max_hp = self.max_hp
        old_hp = self.hp

        ok = self._set_stat_from_value(idx, value)

        if ok and idx == 0:
            self._apply_hp_policy(old_max_hp, old_hp, hp_policy)

        return ok

    def set_evs_at(self, idx: int, value: int, hp_policy: HpPolicy = "keep_absolute"):
        """指定インデックスの努力値をChampions形式（0〜32）で設定する。

        Args:
            idx: ステータスのインデックス
            value: 設定するChampions形式の努力値（0〜32）
            hp_policy: 最大HP変化時のhpの追従方法（HpPolicy参照）

        Note:
            設定後、ステータスを自動再計算する。
        """
        self._evs[idx] = value
        self.update_stats(hp_policy)

    def _modify_hp_raw(self, v: int) -> int:
        """HPを増減させる（内部専用の低レベル実装）。

        Args:
            v: 増減量（正の値で回復、負の値でダメージ）

        Returns:
            実際に変化したHP量

        Warning:
            HPを0から最大HPの範囲にクランプするだけの内部専用メソッドであり、
            ON_HP_CHANGE系ハンドラの発火・瀕死判定・ログ記録を一切行わない。
            外部コード（テスト・bot・探索コード含む）から直接呼び出さないこと。
            通常は必ず `Battle.modify_hp()` を使用する。
        """
        hp_before = self.hp
        self.hp = max(0, min(self.max_hp, hp_before + v))
        assert 0 <= self.hp <= self.max_hp, f"HP範囲外: hp={self.hp} max_hp={self.max_hp}"
        return self.hp - hp_before

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
        old = self.boosts[stat]
        self.boosts[stat] = m.clamp_stats(old + v)
        assert STAT_RANK_MIN <= self.boosts[stat] <= STAT_RANK_MAX, \
            f"ランク範囲外: stat={stat} value={self.boosts[stat]}"
        return self.boosts[stat] - old

    @property
    def critical_rank(self) -> int:
        """急所ランクを取得する。

        Returns:
            急所ランク（volatileの急所ランク状態から取得）

        Note:
            volatile["きゅうしょアップ"]が存在しない場合は0を返す。
        """
        if self.has_volatile("きゅうしょアップ"):
            return self.volatiles["きゅうしょアップ"].count or 0
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

    # ── 技 ──────────────────────────────────────────────────────

    def set_moves(self, moves: list[MoveName]):
        """技のリストを設定する。

        Args:
            moves: 技名のリスト
        """
        self.moves = [Move(name) for name in moves]

    def get_move(self, move_name: MoveName) -> Move | None:
        """技を検索する。

        Args:
            move_name: 技名

        Returns:
            見つかった場合はMoveオブジェクト、見つからなければNone
        """
        for mv in self.moves:
            if mv.name == move_name:
                return mv
        return None

    def has_move(self, move: MoveName) -> bool:
        """指定された技を持っているか判定する。

        Args:
            move: 技名

        Returns:
            指定技を持っていればTrue
        """
        return self.get_move(move) is not None

    # ── アイテム ────────────────────────────────────────────────

    def has_item(self, name: ItemName | None = None, consider_enabled: bool = False) -> bool:
        """アイテムを持っているか判定する。

        Args:
            name: アイテム名（Noneの場合は何らかのアイテムを持っているかを判定）
            consider_enabled: True の場合はアイテムが有効なときのみ所持とみなす

        Returns:
            nameが指定された場合はそのアイテムを持っているか、
            Noneの場合は何らかのアイテムを持っている場合True
        """
        item_name = self.item.name if consider_enabled else self.item.base_name
        if name is None:
            return bool(item_name)
        return item_name == name

    # ── 状態異常・揮発性状態 ────────────────────────────────────

    def has_ailment(self, *ailment_names: AilmentName) -> bool:
        """指定された状態異常を持っているか判定する。

        Args:
            ailment_names: 状態異常名の可変長引数

        Returns:
            指定状態異常を持っていればTrue
        """
        return self.ailment.name in ailment_names

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

    def has_volatile(self, volatile_name: VolatileName) -> bool:
        """指定された揮発性状態を持っているか判定する。

        Args:
            volatile_name: 揮発性状態名

        Returns:
            指定揮発性状態を持っていればTrue
        """
        return volatile_name in self.volatiles

    def get_volatile(self, volatile_name: VolatileName) -> Volatile | None:
        """揮発性状態を取得する。

        Args:
            volatile_name: 揮発性状態名

        Returns:
            指定された揮発性状態があればそのVolatileオブジェクト、なければNone
        """
        return self.volatiles.get(volatile_name, None)

    # ── poke-env 互換 ───────────────────────────────────────────
    # poke-env との互換性のために追加したエイリアス property。
    # 実体は既存の property/属性であり、ここでは名前の変換のみを行う。

    @property
    def current_hp(self) -> int:
        """poke-env 互換: 現在HP（`hp` のエイリアス）。"""
        return self.hp

    @property
    def current_hp_fraction(self) -> float:
        """poke-env 互換: 現在のHP割合（`hp_fraction` のエイリアス）。"""
        return self.hp_fraction

    @property
    def status(self) -> AilmentName:
        """poke-env 互換: 状態異常名（`ailment.name` のエイリアス、型変換なし）。"""
        return self.ailment.name

    @property
    def effects(self) -> dict[VolatileName, Volatile]:
        """poke-env 互換: 揮発性状態の辞書（`volatiles` のエイリアス、型変換なし）。"""
        return self.volatiles

    @property
    def first_turn(self) -> bool:
        """poke-env 互換: 場に出てから最初の行動かどうか。

        `acted_since_switch_in`（場に出てから一度でも行動したか）の否定形で代替する。
        """
        return not self.acted_since_switch_in

    # ── ユーティリティ ──────────────────────────────────────────

    def render_info(self) -> str:
        """ポケモンの情報を整形した文字列として返す。

        出力先（print / logging 等）を呼び出し側に委ねるための API。
        `show` はこのメソッドの結果を print するだけの薄いラッパー。
        """
        sep = '\n\t'
        s = f"{self.name}{sep}"
        s += f"HP {self.hp}/{self.max_hp} ({self.hp_fraction*100:.0f}%){sep}"
        s += f"{self._nature}{sep}"
        s += f"{self.ability.name}{sep}"
        s += f"{self.item.name or 'アイテムなし'}{sep}"
        # __init__ で tera_type = tera_type or self.base_types[0] により常に非空値が
        # 設定されるため、現状の設計ではelse節（テラスタルなし）は到達しない。
        # 将来tera_typeが空になり得る経路が増えた場合の保険として残す。
        if self.tera_type:
            s += f"{self.tera_type}T{sep}"
        else:
            s += f"テラスタルなし{sep}"
        for st, ef in zip(self._stats, self._evs):
            s += f"{st}({ef})-" if ef else f"{st}-"
        s = s[:-1] + sep
        s += "/".join(move.name for move in self.moves)
        return s

    def show(self):
        """ポケモンの情報を文字列化して表示する（`render_info` の互換ラッパー）。"""
        print(self.render_info())

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
            "ivs": self._ivs,
            "evs": self._evs,
            "tera_type": self.tera_type,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Pokemon":
        """to_dict() が返す辞書からポケモンを再構築する。"""
        mon = cls(
            data["name"],
            gender=data["gender"],
            nature=data["nature"],
            level=data["level"],
            ability_name=data["ability"],
            item_name=data["item"],
            move_names=data["moves"],
            tera_type=data["tera_type"],
        )
        mon.set_ivs(list(data["ivs"]))
        # to_dict() は瀕死・被弾状態を保存しない（常に全回復状態の再構築を想定）ため reset を使う
        mon.set_evs(list(data["evs"]), hp_policy="reset")
        return mon
