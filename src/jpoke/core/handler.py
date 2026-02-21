from __future__ import annotations
from typing import TYPE_CHECKING, Any, NamedTuple
if TYPE_CHECKING:
    from jpoke.core import Battle
    from jpoke.model import Pokemon, BattleContext

from typing import Callable
from dataclasses import dataclass

from jpoke.utils.type_defs import ContextRole, RoleSpec, LogPolicy, EffectSource, Side
from jpoke.core.player import Player


class HandlerReturn(NamedTuple):
    """ハンドラ関数の戻り値。

    - success: 処理が成功したか（または行われたか）どうか
    - value: 補正値などの連鎖計算に使う値（省略可）
    - stop_event: イベント処理を停止するかどうか（省略可）
    """
    success: bool = False
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
    subject_spec: RoleSpec
    source_type: EffectSource | None = None
    log: LogPolicy = "on_success"
    log_text: str | None = None
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

    def resolve_subject(self, battle: Battle, ctx: BattleContext) -> Pokemon | None:
        """subject_spec に基づいてハンドラの対象ポケモンを解決"""
        return ctx.resolve_role(battle, self.subject_spec)

    def should_log(self, success: bool) -> bool:
        return self.log == "always" or \
            (self.log == "on_success" and success) or \
            (self.log == "on_failure" and not success)

    def write_log(self, battle: Battle, ctx: BattleContext, success: bool) -> None:
        if not self.should_log(success):
            return

        subject = self.resolve_subject(battle, ctx)
        if not subject:
            return

        if self.log_text is not None:
            text = self.log_text
        else:
            text = ""
            match self.source_type:
                case "ability":
                    subject.ability.reveal()
                    text = subject.ability.orig_name
                case "item":
                    subject.item.reveal()
                    text = subject.item.orig_name
                case "move":
                    ctx.move.reveal()
                    text = ctx.move.orig_name
                case "ailment":
                    text = subject.ailment.name
                case "volatile":
                    # どの Volatile か特定できないため、自動ログはサポートしない
                    pass

            if not success:
                text += " 失敗"

        if text:
            battle.add_event_log(subject, text)


@dataclass
class RegisteredHandler:
    """登録済みのイベントハンドラ情報。

    ハンドラとその対象（ポケモンまたはプレイヤー）の組み合わせを保持する。

    Attributes:
        handler: ハンドラ定義
        _subject: ハンドラの対象（ポケモンまたはプレイヤー）
    """
    handler: Handler
    _subject: Pokemon | Player

    def update_reference(self, old: Battle, new: Battle):
        """Battleの複製後に、対応する新しい対象ポケモンを見つける。

        Args:
            old: 複製前のBattle
            new: 複製後のBattle

        Returns:
            Pokemon | Player: 対応する新しい対象
        """
        if isinstance(self._subject, Player):
            player_idx = old.players.index(self._subject)
            self._subject = new.players[player_idx]
        else:
            player = old.find_player(self._subject)
            player_idx = old.players.index(player)
            team_idx = player.team.index(self._subject)
            self._subject = new.players[player_idx].team[team_idx]

    @property
    def subject(self) -> Pokemon:
        """ハンドラの対象ポケモンを取得する。

        Playerの場合は現在場に出ているポケモンを返す。

        Returns:
            Pokemon: 対象のポケモン
        """
        if isinstance(self._subject, Player):
            return self._subject.active
        else:
            return self._subject
