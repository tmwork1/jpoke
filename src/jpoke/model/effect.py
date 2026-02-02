from __future__ import annotations
from typing import TYPE_CHECKING, Protocol, Self
if TYPE_CHECKING:
    from jpoke.core.event import EventManager, Event, Handler
    from jpoke.core.player import Player
    from jpoke.model.pokemon import Pokemon


class EffectData(Protocol):
    """効果データのプロトコル。

    各効果データクラス (AbilityData, ItemData, MoveData など) が
    実装すべきインターフェースを定義する。
    """
    name: str
    handlers: dict[Event, Handler]


class GameEffect:
    """ゲーム内効果の基底クラス。

    特性、道具、技、状態異常、フィールドなど、ハンドラを持ち
    有効/無効化や公開状態を管理する効果オブジェクトの共通基盤。

    Attributes:
        data: 効果のデータ (名前、ハンドラなど)
    """

    def __init__(self, data: EffectData) -> None:
        """GameEffect を初期化する。

        Args:
            data: 効果データ (AbilityData, ItemData など)
        """
        self.data = data
        self.reset_effect()

    def reset_effect(self) -> None:
        """効果の状態をリセットする。

        効果の有効/無効状態と公開状態を初期状態に戻す。
        """
        self._enabled = True
        self._revealed = False

    @property
    def effect_enabled(self) -> bool:
        """効果が有効化されているかどうか。

        Returns:
            効果が有効な場合 True、無効な場合 False
        """
        return self._enabled

    @property
    def revealed(self) -> bool:
        """効果が公開されているかどうか。

        効果が発動したり使用されたりして、相手プレイヤーに
        判明した状態かどうかを示す。

        Returns:
            公開されている場合 True、非公開の場合 False
        """
        return self._revealed

    @property
    def name(self) -> str:
        """効果の名前を取得する。

        効果が無効化されている場合は空文字を返す。
        有効な効果の名前のみが必要な場合に使用する。

        Returns:
            有効な場合は効果名、無効な場合は空文字
        """
        return self.data.name if self._enabled else ""

    @property
    def orig_name(self) -> str:
        """効果の元の名前を取得する。

        効果の有効/無効状態に関わらず、常に元の名前を返す。
        ログ記録やデバッグ時に使用する。

        Returns:
            効果の名前
        """
        return self.data.name

    def reveal(self) -> None:
        """効果を公開状態にする。

        効果が発動したり使用されたりして、相手プレイヤーに
        判明した際に呼び出す。
        """
        self._revealed = True

    def enable(self) -> None:
        """効果を有効化する。

        無効化されていた効果を再び有効にする。
        """
        self._enabled = True

    def disable(self) -> None:
        """効果を無効化する。

        効果を一時的または恒久的に無効にする。
        無効化された効果はハンドラが登録されず、name プロパティは空文字を返す。
        """
        self._enabled = False

    def register_handlers(self,
                          events: EventManager,
                          subject: Pokemon | Player) -> None:
        """イベントハンドラを登録する。

        効果が無効化されている場合は登録を行わない。

        Args:
            events: イベントマネージャー
            subject: ハンドラの対象となるポケモンまたはプレイヤー
        """
        if not self._enabled:
            return
        for event, handler in self.data.handlers.items():
            # handlerがリストの場合は各要素を登録
            if isinstance(handler, list):
                for h in handler:
                    events.on(event, h, subject)
            else:
                events.on(event, handler, subject)

    def unregister_handlers(self,
                            events: EventManager,
                            subject: Pokemon | Player) -> None:
        """イベントハンドラを解除する。

        Args:
            events: イベントマネージャー
            subject: ハンドラの対象となるポケモンまたはプレイヤー
        """
        for event, handler in self.data.handlers.items():
            # handlerがリストの場合は各要素を解除
            if isinstance(handler, list):
                for h in handler:
                    events.off(event, h, subject)
            else:
                events.off(event, handler, subject)

    def __eq__(self, value: Self | str) -> bool:
        """等価性の比較を行う。

        文字列との比較では名前を比較し、
        オブジェクトとの比較では同一性 (is) を確認する。

        Args:
            value: 比較対象 (GameEffect インスタンスまたは文字列)

        Returns:
            等しい場合 True、異なる場合 False
        """
        if isinstance(value, str):
            return self.name == value
        else:
            return self is value

    def __ne__(self, value: Self | str) -> bool:
        """非等価性の比較を行う。

        Args:
            value: 比較対象 (GameEffect インスタンスまたは文字列)

        Returns:
            異なる場合 True、等しい場合 False
        """
        if isinstance(value, str):
            return self.name != value
        else:
            return self is not value
