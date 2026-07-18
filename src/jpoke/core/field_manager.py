"""場の状態管理を行うマネージャークラス群。

天候、フィールド（地形）、グローバルフィールド効果、サイドフィールド効果など、
バトル中の場の状態を管理します。排他的な効果とスタック可能な効果を適切に処理します。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, get_args, Generic, Iterable, TypeVar, cast
if TYPE_CHECKING:
    from jpoke.core import Battle, Player, EventManager
    from jpoke.model import Pokemon

from jpoke.utils import fast_copy
from jpoke.types import GlobalFieldName, SideFieldName, WeatherName, TerrainName
from jpoke.data.field import WEATHER_PRIORITY
from jpoke.enums import Event, LogCode
from jpoke.model.field import Field
from .context import EventContext
from .log_payload import FieldPayload

T = TypeVar("T")


class BaseFieldManager(Generic[T]):
    """フィールド効果管理の基底クラス。
    フィールド効果（天候、地形、グローバルフィールド、サイドフィールドなど）を
    管理するための共通基盤。

    Notes:
        このクラスは直接インスタンス化せず、専用の管理クラスを使用すること。
    """

    def __init__(self, battle: Battle, owners: tuple[Player, ...], fields: dict[T, Field]):
        """BaseFieldManagerを初期化する。

        Args:
            battle: 親となるBattleインスタンス
            owners: フィールド効果の所有者リスト
            fields: フィールド名とFieldオブジェクトの辞書
        """
        self.battle: Battle = battle
        self.owners: tuple[Player, ...] = owners
        self.fields: dict[T, Field] = fields

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        fast_copy(self, new, keys_to_deepcopy=["fields"])
        return new

    def update_reference(self, new_battle: Battle):
        """ディープコピー後の参照を更新する。

        Args:
            new_battle: 新しいBattleインスタンス
        """
        self.battle = new_battle

    @property
    def _events(self) -> EventManager:
        return self.battle.events

    def get(self, name: T) -> Field:
        """フィールドオブジェクトを取得する。

        Args:
            name: フィールド名

        Returns:
            Field: 対応するフィールドオブジェクト
        """
        return self.fields[name]

    def tick_down(self, name: T):
        """フィールド効果のカウントを1減らす。

        カウントが0になった場合、効果を解除します。

        Args:
            name: フィールド名
        """
        field = self.get(name)
        if not field.is_active:
            return

        field.count -= 1
        if not field.count:
            self._deactivate_field(field)

    def _activate_field(self, name: T, count: int):
        """フィールドを有効化する。"""
        if count <= 0:
            raise ValueError("フィールドの持続ターン数は1以上でなければなりません。")
        field = self.get(name)
        field.count = count
        for player in field.owners:
            field.register_handlers(self._events, player)
        self.battle.add_event_log(
            field.owners[0], LogCode.FIELD_STARTED,
            payload=FieldPayload(field=field.name, count=count)
        )
        self._events.emit(Event.ON_FIELD_ACTIVATE, value=field)

    def _deactivate_field(self, field: Field):
        """解除イベントを発火してからフィールドを無効化する。"""
        field_name = field.data.name
        field.count = 0
        self.battle.add_event_log(
            field.owners[0], LogCode.FIELD_ENDED,
            payload=FieldPayload(field=field_name)
        )
        self._events.emit(Event.ON_FIELD_DEACTIVATE, value=field)
        for player in field.owners:
            field.unregister_handlers(self._events, player)

    def _has_turn_end_tick(self, field: Field) -> bool:
        """このフィールドがEvent.ON_TURN_ENDで自動的にカウントダウンされる種類かどうかを判定する。

        強天候（おおひでり・おおあめ・らんきりゅう）やまきびし等の設置技のように
        Event.ON_TURN_END のハンドラを持たない（=ターン経過でカウントダウンされない）
        フィールドは対象外（`late_field_activation` によるカウントダウン補填の対象を
        判定するために使う。`ExclusiveFieldManager.apply()` /
        `StackableFieldManager.activate()` / `SideFieldManager.apply()` 参照）。
        """
        return Event.ON_TURN_END in field.data.handlers


class ExclusiveFieldManager(BaseFieldManager[T]):
    """排他的なフィールド効果を管理するクラス。

    同時に1つの効果のみが有効になります（例：天候、フィールド）。
    新しい効果を発動すると、既存の効果は上書きされます。

    Attributes:
        current: 現在有効なフィールド
        change_version: current_name が実際に変化した回数を数えるカウンター。
            メガソーラー等、一時的に current_name を仮想的に上書きする効果が、
            その最中に本物の変化（apply/remove/tick_down_current 経由）が
            発生したかどうかを検知するために使う（直接の代入である
            `current_name = ...` はカウントされない。`メガソーラー_deactivate`
            参照）。
    """

    def __init__(self, battle: Battle, owners: tuple[Player, ...], kind: Any):
        """ExclusiveFieldManagerを初期化する。

        Args:
            battle: Battleインスタンス
            owners: フィールド効果の所有者リスト
            kind: フィールドタイプ（Weather, Terrainなど）。
                実体はクラスではなく `Literal[...]` の型エイリアスで、
                get_args() で列挙値を取り出すためだけに使う（type[T] は型として不正確なため Any にしている）
        """
        names = get_args(kind)
        if "" not in names:
            raise ValueError("ExclusiveFieldManagerのフィールドタイプには空文字が含まれている必要があります。")

        fields = {name: Field(name, owners) for name in names}
        super().__init__(battle, owners, fields)

        self.inactive_name: T = cast(T, "")  # 非アクティブ状態を表すフィールド名
        self.current_name: T = self.inactive_name
        self.change_version: int = 0

    @property
    def current(self) -> Field:
        """現在有効なフィールドオブジェクトを返す。"""
        return self.fields[self.current_name]

    @property
    def inactive(self) -> Field:
        """非発動状態のフィールドオブジェクトを返す。"""
        return self.fields[self.inactive_name]

    def apply(self, name: T, count: int, source: Pokemon | None = None) -> bool:
        """フィールド効果を発動する。

        既存の効果がある場合は解除してから新しい効果を発動します。

        Args:
            name: 発動するフィールド名
            count: 効果の持続ターン数
            source: 効果の発生源となるポケモン

        Returns:
            bool: 効果が発動された場合True（既に同じ効果が有効な場合はFalse）
        """
        if self.current_name == name:
            return False

        if self.current.is_active:
            self._deactivate_field(self.current)

        # ON_MODIFY_DURATIONイベントを発火して、ターン数の変更を可能にする
        value = self._events.emit(
            Event.ON_MODIFY_DURATION,
            EventContext(source=source),
            [name, count]
        )
        _, modified_count = value
        if modified_count <= 0:
            raise ValueError("フィールドの持続ターン数は1以上でなければなりません。")

        self._activate_field(name, modified_count)
        self.current_name = name
        self.change_version += 1
        self._events.emit(Event.ON_FIELD_CHANGE)

        # 瀕死交代・緊急交代など、このターンのON_TURN_END通過後に新規発動した場合は
        # そのターンのカウントダウン機会を逃しているため、即座に1回分を補填する
        # （`late_field_activation_context()` docstring参照）。
        if self.battle.late_field_activation and self._has_turn_end_tick(self.current):
            self.tick_down_current()
        return True

    def remove(self) -> bool:
        """現在のフィールド効果を解除する。

        Returns:
            bool: 効果が解除された場合True
        """
        if not self.current.is_active:
            return False
        self._deactivate_field(self.current)
        self.current_name = self.inactive_name
        self.change_version += 1
        self._events.emit(Event.ON_FIELD_CHANGE)
        return True

    def tick_down_current(self) -> None:
        """現在のフィールド効果のカウントを1減らす。

        カウントが0になった場合は remove() と同様に current_name をリセットし
        ON_FIELD_CHANGE を発火する。これにより、はれ/エレキフィールドなどが
        自然消滅したときにも、こだいかっせい/クォークチャージ/ぎたい/てんきやなど
        ON_FIELD_CHANGE を契機に再判定する特性が確実に反応する
        （.internal/spec/abilities/こだいかっせい.md「にほんばれ状態の効果が切れると
        『こだいかっせいの効果が切れた!』とメッセージが出て補正が消える」
        「にほんばれ状態が消滅すると一旦特性の効果が消えるが、即座に
        ブーストエナジーを消費して特性を再発動させる」を参照）。

        Notes:
            基底の tick_down(name) とは引数の有無が異なるため、
            LSP 違反（mypy override エラー）を避けるために別名にしている。
        """
        field = self.current
        if not field.is_active:
            return
        field.count -= 1
        if not field.count:
            self._deactivate_field(field)
            self.current_name = self.inactive_name
            self.change_version += 1
            self._events.emit(Event.ON_FIELD_CHANGE)


class StackableFieldManager(BaseFieldManager[T]):
    """複数同時に有効化可能なフィールド効果を管理するクラス。

    複数の効果が同時に有効になれます（例：リフレクター、ひかりのかべ、まきびしなど）。
    """

    def __init__(self, battle: Battle, owners: tuple[Player, ...], kind: Any):
        """StackableFieldManagerを初期化する。

        Args:
            battle: Battleインスタンス
            owners: フィールド効果の所有者リスト
            kind: フィールドタイプ（GlobalField, SideFieldなど）。
                実体はクラスではなく `Literal[...]` の型エイリアスで、
                get_args() で列挙値を取り出すためだけに使う（type[T] は型として不正確なため Any にしている）
        """
        names = get_args(kind)
        fields = {name: Field(name, owners) for name in names}
        super().__init__(battle, owners, fields)

    def activate(self, name: T, count: int) -> bool:
        """フィールド効果を発動する。

        max_count が 1 より大きいフィールド（まきびし・どくびし等）は、
        すでに有効な場合でも max_count 未満であれば count を 1 増やす。

        Args:
            name: 発動するフィールド名
            count: 新規発動時の持続ターン数（重ね掛けは常に +1）

        Returns:
            bool: 効果が発動または増加した場合True、最大層に達している場合False
        """
        field = self.get(name)
        if not field.is_active:
            self._activate_field(name, count)
            # 瀕死交代・緊急交代など、このターンのON_TURN_END通過後に新規発動した
            # 場合はそのターンのカウントダウン機会を逃しているため、即座に1回分を
            # 補填する（ON_TURN_ENDでカウントダウンされないまきびし等の設置技は
            # `_has_turn_end_tick` がFalseを返すため対象外。
            # `late_field_activation_context()` docstring参照）。
            if self.battle.late_field_activation and self._has_turn_end_tick(field):
                self.tick_down(name)
            return True
        max_count = field.data.max_count
        if max_count <= 1 or field.count >= max_count:
            return False
        field.count += 1
        self.battle.add_event_log(
            field.owners[0], LogCode.FIELD_STACKED,
            payload=FieldPayload(field=field.name, count=field.count)
        )
        return True

    def deactivate(self, name: T) -> bool:
        """指定したフィールド効果を解除する。

        Args:
            name: 解除するフィールド名

        Returns:
            bool: 効果が解除された場合True
        """
        field = self.get(name)
        if not field.is_active:
            return False
        self._deactivate_field(field)
        return True


class WeatherManager(ExclusiveFieldManager[WeatherName]):
    """天候を管理するクラス。

    晴れ、雨、砂嵐、霰などの天候状態を管理します。
    強天候（おおひでり・おおあめ・らんきりゅう）は通常天候で上書きできません。
    """

    def __init__(self, battle: Battle):
        super().__init__(battle, battle.players, WeatherName)

    @property
    def active(self) -> Field:
        """現在有効な天候オブジェクトを返す。"""
        if self.current_name != self.inactive_name:
            enabled = self._events.emit(Event.ON_CHECK_WEATHER_ENABLED, value=True)
            if not enabled:
                return self.inactive
        return self.current

    def apply(self, name: WeatherName, count: int, source: Pokemon | None = None) -> bool:
        """天候を発動する。
        天候の上書きは、現在の天候と新しい天候の優先度を比較して決める。
        """
        current_priority = WEATHER_PRIORITY[self.current_name]
        new_priority = WEATHER_PRIORITY[name]
        if new_priority >= current_priority:
            return super().apply(name, count, source=source)
        return False


class TerrainManager(ExclusiveFieldManager[TerrainName]):
    """フィールド（地形）を管理するクラス。

    エレキフィールド、グラスフィールド、ミストフィールド、サイコフィールドなどを管理します。
    """

    def __init__(self, battle: Battle):
        super().__init__(battle, battle.players, TerrainName)


class GlobalFieldManager(StackableFieldManager[GlobalFieldName]):
    """グローバルフィールド効果を管理するクラス。

    じゅうりょく、トリックルームなど、場全体に影響する効果を管理します。
    """

    def __init__(self, battle: Battle):
        super().__init__(battle, battle.players, GlobalFieldName)


class SideFieldManager(StackableFieldManager[SideFieldName]):
    """サイドフィールド効果を管理するクラス。

    リフレクター、ひかりのかべ、まきびし、ステルスロックなど、
    片方のプレイヤー側の場にのみ影響する効果を管理します。
    """

    def __init__(self, battle: Battle, owner: Player):
        """SideFieldManagerを初期化する。

        Args:
            battle: Battleインスタンス
            owner: 効果を管理するプレイヤー
        """
        super().__init__(battle, (owner,), SideFieldName)

    def apply(self, name: SideFieldName, count: int, source: Pokemon | None = None) -> bool:
        """サイドフィールド効果を発動する。ON_MODIFY_DURATION を発火してから activate する。

        Args:
            name: 発動するフィールド名
            count: 効果の持続ターン数
            source: 効果の発生源となるポケモン

        Returns:
            bool: 効果が発動された場合True（既に有効な場合はFalse）
        """
        field = self.get(name)
        if field.is_active:
            return False

        # ON_MODIFY_DURATION イベントを発火して、ひかりのねんど等による持続ターン延長を可能にする
        value = self._events.emit(
            Event.ON_MODIFY_DURATION,
            EventContext(source=source),
            [name, count]
        )
        _, modified_count = value
        if modified_count <= 0:
            raise ValueError("フィールドの持続ターン数は1以上でなければなりません。")

        self._activate_field(name, modified_count)

        # 瀕死交代・緊急交代など、このターンのON_TURN_END通過後に新規発動した場合は
        # そのターンのカウントダウン機会を逃しているため、即座に1回分を補填する
        # （`late_field_activation_context()` docstring参照）。
        if self.battle.late_field_activation and self._has_turn_end_tick(field):
            self.tick_down(name)
        return True

    def swap_fields(self, other: "SideFieldManager", names: Iterable[SideFieldName]) -> bool:
        """指定したサイドフィールドの状態を他方のマネージャーと入れ替える（コートチェンジ用）。

        継続ターン数（まきびし等の層数を含む）をそのまま交換する。有効/無効が
        入れ替わったフィールドについてはハンドラの登録・解除のみ行い、
        ON_FIELD_ACTIVATE / ON_FIELD_DEACTIVATE イベントは発火しない
        （かぜのり・ふうりょくでんき等、フィールド「開始」を検知する特性が
        誤発動しないようにするため）。FIELD_STARTED / FIELD_ENDED のバトルログも
        出力しない（技の成功ログのみで表現する設計とする）。

        Args:
            other: 入れ替え相手のサイドフィールドマネージャー
            names: 入れ替え対象のフィールド名一覧
                （呼び出し側で「単体対象の状態」等の対象外フィールドを
                あらかじめ除外したリストを渡すこと）

        Returns:
            bool: 1つ以上のフィールドが実際に入れ替わった場合True
        """
        changed = False
        for name in names:
            field_self = self.get(name)
            field_other = other.get(name)
            active_self = field_self.is_active
            active_other = field_other.is_active
            if not active_self and not active_other:
                continue
            changed = True

            if active_self:
                for player in field_self.owners:
                    field_self.unregister_handlers(self._events, player)
            if active_other:
                for player in field_other.owners:
                    field_other.unregister_handlers(other._events, player)

            field_self.count, field_other.count = field_other.count, field_self.count

            if field_self.is_active:
                for player in field_self.owners:
                    field_self.register_handlers(self._events, player)
            if field_other.is_active:
                for player in field_other.owners:
                    field_other.register_handlers(other._events, player)
        return changed
