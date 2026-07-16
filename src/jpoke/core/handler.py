"""イベントハンドラ定義を扱うモジュール。

ハンドラ本体の型、戻り値、登録済みハンドラ情報を定義する。
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any, NamedTuple
if TYPE_CHECKING:
    from jpoke.core import Battle
    from jpoke.model import Pokemon

from typing import Callable
from dataclasses import dataclass, field

from jpoke.utils import fast_copy
from jpoke.types import HandlerSource, ContextRole, RoleSpec, Side
from jpoke.core.player import Player


class HandlerReturn(NamedTuple):
    """ハンドラ関数の戻り値。

    - value: 補正値などの連鎖計算に使う値（省略可）
    - stop_event: イベント処理を停止するかどうか（省略可）
    """
    value: Any = None
    stop_event: bool = False


@dataclass(frozen=True)
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
    skip_subject_check: bool = False  # ハンドラの主体の照合をスキップするか
    ignored_disable_reasons: frozenset[str] = field(default_factory=frozenset)  # 無効化理由のうち無視するもの（例: とくせいガードはぶきように影響されない）
    allow_fainted_subject: bool = False  # 主体（subject_spec解決先）が瀕死でも発動を許すか（例: ON_MOVE_KOで瀕死になった当人自身が発動する効果）
    role: ContextRole = field(init=False)
    side: Side = field(init=False)

    def __post_init__(self):
        parts = self.subject_spec.split(":")
        if (
            len(parts) != 2
            or parts[0] not in ("source", "target", "attacker", "defender")
            or parts[1] not in ("self", "foe")
        ):
            func_name = getattr(self.func, "__qualname__", repr(self.func))
            raise ValueError(
                f"不正な subject_spec '{self.subject_spec}' (handler: {func_name})。"
                "'role:side' 形式（例: 'source:self'）で指定してください。"
            )
        role, side = parts
        object.__setattr__(self, "role", role)
        object.__setattr__(self, "side", side)


@dataclass
class RegisteredHandler:
    """登録済みのイベントハンドラ情報。

    ハンドラとその主体（ポケモンまたはプレイヤー）の組み合わせを保持する。

    Attributes:
        handler: ハンドラ定義
        registered_subject: ハンドラの主体（ポケモンまたはプレイヤー）
    """
    handler: Handler
    registered_subject: Pokemon | Player

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        return fast_copy(self, new, keys_to_deepcopy=["handler"])

    def update_reference(self, old: Battle, new: Battle):
        """Battleの複製後に、対応する新しい主体ポケモンを参照するように更新する。

        Args:
            old: 複製前のBattle
            new: 複製後のBattle
        """
        if isinstance(self.registered_subject, Player):
            return

        player = old.get_player(self.registered_subject)  # 元のBattleからプレイヤーを特定
        old_state = old.player_states[player]
        team_index = old_state.team.index(self.registered_subject)
        self.registered_subject = new.player_states[player].team[team_index]

    def get_subject(self, battle: Battle) -> Pokemon | None:
        """ハンドラの主体となるポケモンを取得する。

        Playerの場合は現在場に出ているポケモンを返す。

        Returns:
            Pokemon | None: ハンドラの主体となるポケモン。
                主体がPlayerで場が空いている場合は None
        """
        if isinstance(self.registered_subject, Player):
            return battle.get_active(self.registered_subject)
        else:
            return self.registered_subject
