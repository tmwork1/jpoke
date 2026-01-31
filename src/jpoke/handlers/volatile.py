from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle, EventContext

from jpoke.utils.type_defs import RoleSpec, LogPolicy
from jpoke.utils.enums import Event
from jpoke.core.event import Handler, HandlerReturn
from . import common


class VolatileHandler(Handler):
    def __init__(self,
                 func: Callable,
                 subject_spec: RoleSpec = "source:self",
                 log: LogPolicy = "on_success",
                 log_text: str | None = None,
                 priority: int = 100):
        super().__init__(func, subject_spec, "volatile", log, log_text, priority)
