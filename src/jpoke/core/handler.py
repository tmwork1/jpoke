"""イベントハンドラ定義を扱うモジュール。

ハンドラ本体の型、戻り値、登録済みハンドラ情報を定義する。
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any, NamedTuple
if TYPE_CHECKING:
    from jpoke.core import Battle
    from jpoke.model import Pokemon

from typing import Callable
from dataclasses import dataclass

from jpoke.utils.type_defs import HandlerSource, ContextRole, RoleSpec, Side
from jpoke.core.player import Player


class HandlerReturn(NamedTuple):
    """ハンドラ関数の戻り値。

    - value: 補正値などの連鎖計算に使う値（省略可）
    - stop_event: イベント処理を停止するかどうか（省略可）
    """
    value: Any = None
    stop_event: bool = False


@dataclass
class Handler:
    """ドメイン/イベントハンドラの定義。

    Handler は特定のポケモンまたはプレイヤー（subject）に紐づいて登録され、条件に合うドメイン/イベントが発火したときに実行される。

    - **subject**: ハンドラを所有・発動させるトリガーとなるポケモン（またはプレイヤー）
    - **subject_spec**: どの役割（role）のどちら側（side）に対して発動するかを "role:side" 形式で指定

    例: 「いかく」特性
    - subject: いかくを持つポケモン自身
    - subject_spec="source:self": トリガーの source（登場したポケモン）が自分自身の時に発動
    - target_spec="source:foe": 効果の対象は source から見て相手側のポケモン
    """
    func: Callable[..., HandlerReturn]
    source: HandlerSource
    subject_spec: RoleSpec
    priority: int = 100
    once: bool = False

    def __lt__(self, other):
        """priorityが小さいほど先に実行される"""
        return self.priority < other.priority

    @property
    def role(self) -> ContextRole:
        """subject_spec から role を抽出"""
        return self.subject_spec.split(":")[0]

    @property
    def side(self) -> Side:
        """subject_spec から side を抽出"""
        return self.subject_spec.split(":")[1]


@dataclass
class RegisteredHandler:
    """登録済みのイベントハンドラ情報。

    ハンドラとその主体（ポケモンまたはプレイヤー）の組み合わせを保持する。

    Attributes:
        handler: ハンドラ定義
        _subject: ハンドラの主体（ポケモンまたはプレイヤー）
    """
    handler: Handler
    _subject: Pokemon | Player

    def update_reference(self, old: Battle, new: Battle):
        """Battleの複製後に、対応する新しい主体ポケモンを見つける。

        Args:
            old: 複製前のBattle
            new: 複製後のBattle
        """
        if isinstance(self._subject, Player):
            player_idx = old.players.index(self._subject)
            self._subject = new.players[player_idx]
        else:
            player = old.get_player(self._subject)
            player_idx = old.players.index(player)
            team_idx = player.team.index(self._subject)
            self._subject = new.players[player_idx].team[team_idx]

    @property
    def subject(self) -> Pokemon | None:
        """ハンドラの主体ポケモンを取得する。

        Playerの場合は現在場に出ているポケモンを返す。

        Returns:
            Pokemon | None: 主体のポケモン
        """
        if isinstance(self._subject, Player):
            return self._subject.active_mon
        else:
            return self._subject
