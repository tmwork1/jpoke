from __future__ import annotations
from typing import TYPE_CHECKING, Protocol
if TYPE_CHECKING:
    from jpoke.core import EventManager, Handler, Player
    from jpoke.model import Pokemon

from jpoke.enums import DomainEvent, Event
from jpoke.utils.type_defs import EnableKey


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
        self.revealed: bool = False
        self._enabled: dict[EnableKey, bool] = {"self": True}

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

    @property
    def enabled(self) -> bool:
        """効果が有効かどうかを判定する。

        Returns:
            効果が有効な場合はTrue、無効な場合はFalse
        """
        return all(self._enabled.values())

    def get_enabled(self, key: EnableKey) -> bool:
        """特定のキーによる有効/無効状態を取得する。

        Args:
            key: 取得したい有効/無効状態のキー
        """
        return self._enabled.get(key, True)

    def set_enabled(self, key: EnableKey, enabled: bool) -> None:
        """効果の有効/無効状態を設定する。

        Args:
            key: 有効/無効状態のキー
            enabled: 有効にする場合はTrue、無効にする場合はFalse
        """
        self._enabled[key] = enabled

    def replace_enabled(self, states: dict[EnableKey, bool]) -> None:
        """有効/無効状態を新しい状態に置き換える。

        Args:
            new_states: 置き換える新しい有効/無効状態の辞書
        """
        self._enabled = states

    def reset_enabled(self, initial: bool = True) -> None:
        """有効/無効状態をリセットする。"""
        self._enabled = {"self": initial}

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
            if isinstance(handler, list):
                for h in handler:
                    events.off(event, h, subject)
            else:
                events.off(event, handler, subject)
