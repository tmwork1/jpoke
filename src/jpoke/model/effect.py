from __future__ import annotations
from typing import TYPE_CHECKING, Self
if TYPE_CHECKING:
    from jpoke.core.event import EventManager
    from jpoke.core.player import Player
    from jpoke.model.pokemon import Pokemon


class BaseEffect:
    def __init__(self, data) -> None:
        self.data = data
        self.active: bool = True
        self.revealed: bool = False

    @property
    def name(self) -> str:
        return self.data.name if self.active else ""

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
