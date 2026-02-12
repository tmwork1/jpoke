"""場の状態管理を行うマネージャークラス群。

天候、フィールド（地形）、グローバルフィールド効果、サイドフィールド効果など、
バトル中の場の状態を管理します。排他的な効果とスタック可能な効果を適切に処理します。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, get_args, Generic, TypeVar
if TYPE_CHECKING:
    from jpoke.core import Battle, Player, EventManager
    from jpoke.model import Pokemon

from jpoke.utils import fast_copy
from jpoke.utils.type_defs import GlobalField, SideField, Weather, Terrain
from jpoke.enums import Event
from jpoke.model import Field
from jpoke.core import BattleContext

T = TypeVar("T")


class BaseFieldManager(Generic[T]):
    """フィールド効果管理の基底クラス。
    フィールド効果（天候、地形、グローバルフィールド、サイドフィールドなど）を
    管理するための共通基盤。

    Notes:
        このクラスは直接インスタンス化せず、専用の管理クラスを使用すること。
        init_game()実装不要。ゲームの初期化ではインスタンスを再生成するため。
    """

    def __init__(self, battle: Battle, owners: list[Player], fields: dict[T, Field]):
        """BaseFieldManagerを初期化する。

        Args:
            battle: 親となるBattleインスタンス
            owners: フィールド効果の所有者リスト
            fields: フィールド名とFieldオブジェクトの辞書
        """
        self.battle = battle
        self.owners = owners
        self.fields = fields

    def __deepcopy__(self, memo):
        """ディープコピーを作成する。

        Args:
            memo: コピー済みオブジェクトのメモ辞書

        Returns:
            BaseFieldManager: コピーされたインスタンス
        """
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        fast_copy(self, new, keys_to_deepcopy=["fields"])
        return new

    def update_reference(self, new_battle: Battle, new_owners: list[Player]):
        """ディープコピー後の参照を更新する。

        Args:
            battle: 新しいBattleインスタンス
            owners: 新しい所有者リスト
        """
        self.battle = new_battle
        self.owners = new_owners
        for field in self.fields.values():
            field.update_reference(new_owners)
            if not field.is_active:
                continue
            # アクティブなフィールドのハンドラーを再登録
            for owner in new_owners:
                field.register_handlers(self.events, owner)

    @property
    def events(self) -> EventManager:
        """イベント管理システムへのショートカットプロパティ。"""
        return self.battle.events

    def tick_down(self, name: T):
        """フィールド効果のカウントを1減らす。

        カウントが0になった場合、効果を解除します。

        Args:
            name: フィールド名

        Returns:
            bool: カウントダウンが実行された場合True
        """
        field = self.fields[name]
        field.count -= 1
        if not field.count:
            field.deactivate(self.battle)


class ExclusiveFieldManager(BaseFieldManager[T]):
    """排他的なフィールド効果を管理するクラス。

    同時に1つの効果のみが有効になります（例：天候、フィールド）。
    新しい効果を発動すると、既存の効果は上書きされます。

    Attributes:
        current: 現在有効なフィールド
    """

    def __init__(self, battle: Battle, owners: list[Player], kind: type[T]):
        """ExclusiveFieldManagerを初期化する。

        Args:
            battle: Battleインスタンス
            owners: フィールド効果の所有者リスト
            kind: フィールドタイプ（Weather, Terrainなど）
        """
        names = get_args(kind)
        fields = {name: Field(name, owners) for name in names}
        super().__init__(battle, owners, fields)
        self._default = fields[names[0]]
        self.current = self._default

    def activate(self, name: T, count: int, source: Pokemon | None = None) -> bool:
        """フィールド効果を発動する。

        既存の効果がある場合は解除してから新しい効果を発動します。

        Args:
            name: 発動するフィールド名
            count: 効果の持続ターン数
            source: 効果の発生源となるポケモン

        Returns:
            bool: 効果が発動された場合True（既に同じ効果が有効な場合はFalse）
        """
        field = self.fields[name]
        if self.current is field:
            return False
        if self.current.is_active:
            self.current.deactivate(self.battle)

        count = self.events.emit(
            Event.ON_CHECK_DURATION,
            BattleContext(source=source, field=field),
            count
        )
        field.activate(self.battle, count)
        self.current = field
        return True

    def deactivate(self) -> bool:
        """現在のフィールド効果を解除する。

        Returns:
            bool: 効果が解除された場合True
        """
        if not self.current.is_active:
            return False
        self.current.deactivate(self.battle)
        self.current = self._default
        return True

    def tick_down(self) -> None:
        """現在のフィールド効果のカウントを1減らす。

        Returns:
            bool: カウントダウンが実行された場合True
        """
        super().tick_down(self.current.name)


class StackableFieldManager(BaseFieldManager[T]):
    """複数同時に有効化可能なフィールド効果を管理するクラス。

    複数の効果が同時に有効になれます（例：リフレクター、ひかりのかべ、まきびしなど）。
    """

    def activate(self, name: T, count: int) -> bool:
        """フィールド効果を発動する。

        Args:
            name: 発動するフィールド名
            count: 効果の持続ターン数

        Returns:
            bool: 効果が発動された場合True（既に有効な場合はFalse）
        """
        field = self.fields[name]
        if field.is_active:
            return False
        field.activate(self.battle, count)
        return True

    def deactivate(self, name: T) -> bool:
        """指定したフィールド効果を解除する。

        Args:
            name: 解除するフィールド名

        Returns:
            bool: 効果が解除された場合True
        """
        field = self.fields[name]
        if not field.is_active:
            return False
        field.deactivate(self.battle)
        return True


class WeatherManager(ExclusiveFieldManager[Weather]):
    """天候を管理するクラス。

    晴れ、雨、砂嵐、霰などの天候状態を管理します。
    """

    def __init__(self, battle: Battle):
        """WeatherManagerを初期化する。

        Args:
            battle: Battleインスタンス
        """
        super().__init__(battle, battle.players, Weather)

    def update_reference(self, new_battle: Battle):
        """ディープコピー後の参照を更新する。

        Args:
            battle: 新しいBattleインスタンス
        """
        return super().update_reference(new_battle, new_battle.players)


class TerrainManager(ExclusiveFieldManager[Terrain]):
    """フィールド（地形）を管理するクラス。

    エレキフィールド、グラスフィールド、ミストフィールド、サイコフィールドなどを管理します。
    """

    def __init__(self, battle: Battle):
        """TerrainManagerを初期化する。

        Args:
            battle: Battleインスタンス
        """
        super().__init__(battle, battle.players, Terrain)

    def update_reference(self, new_battle: Battle):
        """ディープコピー後の参照を更新する。

        Args:
            battle: 新しいBattleインスタンス
        """
        return super().update_reference(new_battle, new_battle.players)


class GlobalFieldManager(StackableFieldManager[GlobalField]):
    """グローバルフィールド効果を管理するクラス。

    じゅうりょく、トリックルームなど、場全体に影響する効果を管理します。
    """

    def __init__(self, battle: Battle):
        """GlobalFieldManagerを初期化する。

        Args:
            battle: Battleインスタンス
        """
        super().__init__(
            battle,
            battle.players,
            {
                "じゅうりょく": Field("じゅうりょく", battle.players),
                "トリックルーム": Field("トリックルーム", battle.players),
            }
        )

    def update_reference(self, new_battle: Battle):
        """ディープコピー後の参照を更新する。

        Args:
            battle: 新しいBattleインスタンス
        """
        return super().update_reference(new_battle, new_battle.players)


class SideFieldManager(StackableFieldManager[SideField]):
    """サイドフィールド効果を管理するクラス。

    リフレクター、ひかりのかべ、まきびし、ステルスロックなど、
    片方のプレイヤー側の場にのみ影響する効果を管理します。
    """

    def __init__(self, battle: Battle, player: Player):
        """SideFieldManagerを初期化する。

        Args:
            battle: Battleインスタンス
            player: 効果を管理するプレイヤー
        """
        super().__init__(
            battle,
            [player],
            {
                "リフレクター": Field("リフレクター", [player]),
                "ひかりのかべ": Field("ひかりのかべ", [player]),
                "オーロラベール": Field("オーロラベール", [player]),
                "しんぴのまもり": Field("しんぴのまもり", [player]),
                "しろいきり": Field("しろいきり", [player]),
                "おいかぜ": Field("おいかぜ", [player]),
                "ねがいごと": Field("ねがいごと", [player]),
                "まきびし": Field("まきびし", [player]),
                "どくびし": Field("どくびし", [player]),
                "ステルスロック": Field("ステルスロック", [player]),
                "ねばねばネット": Field("ねばねばネット", [player]),
            }
        )

    def update_reference(self, new_battle: Battle, new_owner: Player):
        """ディープコピー後の参照を更新する。

        Args:
            battle: 新しいBattleインスタンス
            player: 新しいプレイヤー
        """
        super().update_reference(new_battle, [new_owner])
