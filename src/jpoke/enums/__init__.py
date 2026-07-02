"""Enum定義パッケージ

バトルシステムで使用される各種Enumを提供する。
各Enumは責務ごとに分割されたモジュールに配置されている。
"""

from .event import DomainEvent, Event, LethalEvent
from .interrupt import Interrupt
from .command import Command
from .logcode import LogCode

__all__ = [
    "DomainEvent",
    "Event",
    "Interrupt",
    "Command",
    "LogCode",
]
