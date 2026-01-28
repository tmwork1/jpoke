from __future__ import annotations
from typing import TYPE_CHECKING, Self
if TYPE_CHECKING:
    from jpoke.core.event import EventManager
    from jpoke.core.player import Player
    from jpoke.model.pokemon import Pokemon


class BaseEffect:
    def __init__(self, data) -> None:
        self.data = data
        self.effect_enabled: bool = True
        self.revealed: bool = False

    @property
    def name(self) -> str:
        """名前。効果が無効化されている場合は空文字を返す"""
        return self.data.name if self.effect_enabled else ""

    @property
    def orig_name(self) -> str:
        """効果の無効化に関わらず、常に元の名前を返す"""
        return self.data.name

    def register_handlers(self,
                          events: EventManager,
                          subject: Pokemon | Player):
        for event, handler in self.data.handlers.items():
            events.on(event, handler, subject)

    def unregister_handlers(self,
                            events: EventManager,
                            subject: Pokemon | Player):
        for event, handler in self.data.handlers.items():
            events.off(event, handler, subject)

    def __eq__(self, value: Self | str) -> bool:
        if isinstance(value, str):
            return self.name == value
        else:
            return self is value

    def __nq__(self, value: Self | str) -> bool:
        if isinstance(value, str):
            return self.name != value
        else:
            return self is not value
