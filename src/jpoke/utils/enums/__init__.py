"""Enum定義パッケージ

バトルシステムで使用される各種Enumを提供する。
各Enumは責務ごとに分割されたモジュールに配置されている。
"""

from .event import Event
from .interrupt import Interrupt
from .damage import DamageFlag
from .command import Command

__all__ = [
    "Event",
    "Interrupt",
    "DamageFlag",
    "Command",
]
