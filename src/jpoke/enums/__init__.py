"""Enum定義パッケージ

バトルシステムで使用される各種Enumを提供する。
各Enumは責務ごとに分割されたモジュールに配置されている。
"""

from .event import DomainEvent, Event
from .interrupt import Interrupt
from .damage import DamageFlag
from .command import Command
from .log import LogCode

__all__ = [
    "DomainEvent",
    "Event",
    "Interrupt",
    "DamageFlag",
    "Command",
    "LogCode",
]
