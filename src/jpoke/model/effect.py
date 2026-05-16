from __future__ import annotations
from typing import TYPE_CHECKING, Protocol, Any
if TYPE_CHECKING:
    from jpoke.core import EventManager, Handler, Player
    from jpoke.data.models import Handlers
    from jpoke.model import Pokemon

from jpoke.enums import DomainEvent, Event
from jpoke.utils.type_defs import AbilityDisabledReason


class EffectData(Protocol):
    """効果データのプロトコル。

    各効果データクラス (AbilityData, ItemData, MoveData など) が
    実装すべきインターフェースを定義する。
    """
    name: str
    handlers: Handlers


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
        self._disabled_reasons: set[Any] = set()

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
        return not self._disabled_reasons

    @property
    def self_disabled(self) -> bool:
        """効果が自己無効化されているかを判定する。

        Returns:
            効果が自己無効化されている場合はTrue、そうでない場合はFalse
        """
        return "self" in self._disabled_reasons

    def add_disable_reason(self, reason: Any) -> None:
        """
        効果を無効にする理由を追加する。
        Args:
            reason: 無効化の理由を示すキー
        """
        self._disabled_reasons.add(reason)

    def remove_disable_reason(self, reason: Any) -> None:
        """効果を有効にする理由を削除する。

        Args:
            reason: 有効化の理由を示すキー
        """
        self._disabled_reasons.discard(reason)

    def set_disabled_reasons(self, reasons: set[Any]) -> None:
        """無効化の理由を置き換える。

        Args:
            reasons: 新しい無効化理由のセット
        """
        self._disabled_reasons = reasons

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
