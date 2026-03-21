from __future__ import annotations
from typing import TYPE_CHECKING, Protocol, Self
if TYPE_CHECKING:
    from jpoke.core import EventManager, Handler, Player
    from jpoke.model import Pokemon

from jpoke.enums import DomainEvent, Event


class EffectData(Protocol):
    """効果データのプロトコル。

    各効果データクラス (AbilityData, ItemData, MoveData など) が
    実装すべきインターフェースを定義する。
    """
    name: str
    handlers: dict[DomainEvent | Event, Handler]


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
        self.data: EffectData = data
        self.enabled: bool = True
        self.revealed: bool = False

    def reset_effect(self) -> None:
        """効果の状態をリセットする。

        効果の有効/無効状態と公開状態を初期状態に戻す。
        """
        self.enabled = True
        self.revealed = False

    @property
    def name(self) -> str:
        """効果の名前を取得する。

        効果が無効化されている場合は空文字を返す。
        有効な効果の名前のみが必要な場合に使用する。

        Returns:
            有効な場合は効果名、無効な場合は空文字
        """
        return self.data.name if self.enabled else ""

    @property
    def orig_name(self) -> str:
        """効果の元の名前を取得する。

        効果の有効/無効状態に関わらず、常に元の名前を返す。
        ログ記録やデバッグ時に使用する。

        Returns:
            効果の名前
        """
        return self.data.name

    def register_handlers(self,
                          events: EventManager,
                          subject: Pokemon | Player) -> None:
        """イベントハンドラを登録する。

        効果が無効化されている場合は登録を行わない。

        Args:
            events: イベントマネージャー
            subject: ハンドラの対象となるポケモンまたはプレイヤー
        """
        if not self.enabled:
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
