from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle
    from jpoke.model import Move, Pokemon, Field

from jpoke.utils.type_defs import ContextRole, RoleSpec


class BattleContext:
    """ドメイン/イベント発火時のコンテキスト情報。

    ドメイン/イベントに関連するポケモン、技、場の状態などを保持します。
    ハンドラ実行時に必要な情報を提供します。

    内部的には source/target のみを保持しますが、
    attacker/defender での指定・アクセスも可能です（source/target のエイリアス）。

    Attributes:
        source: イベントの発生源となるポケモン（attacker のエイリアス）
        target: イベントの対象となるポケモン（defender のエイリアス）
        move: 使用された技
        field: 場の状態
        damage: 与えたダメージ値（ON_HIT 等で使用）
    """

    def __init__(self,
                 source: Pokemon | None = None,
                 target: Pokemon | None = None,
                 attacker: Pokemon | None = None,
                 defender: Pokemon | None = None,
                 move: Move | None = None,
                 field: Field | None = None,
                 damage: int = 0):
        """BattleContext を初期化する。

        Args:
            source: イベントの発生源となるポケモン
            target: イベントの対象となるポケモン
            attacker: 攻撃側のポケモン（source のエイリアス）
            defender: 防御側のポケモン（target のエイリアス）
            move: 使用された技
            field: 場の状態
            damage: 与えたダメージ値（デフォルト0）

        Note:
            attacker が指定された場合は source に、
            defender が指定された場合は target にマッピングされます。
        """
        # attacker/defender が指定された場合は source/target にマッピング
        self.source = attacker if attacker is not None else source
        self.target = defender if defender is not None else target
        self.move = move
        self.field = field
        self.damage = damage

    @property
    def attacker(self) -> Pokemon | None:
        """攻撃側のポケモン（source のエイリアス）。"""
        return self.source

    @property
    def defender(self) -> Pokemon | None:
        """防御側のポケモン（target のエイリアス）。"""
        return self.target

    def get(self, role: ContextRole) -> Pokemon | None:
        """指定されたロールのポケモンを取得する。

        Args:
            role: 取得するロール（"source", "target", "attacker", "defender"）

        Returns:
            Pokemon | None: 該当するポケモン。存在しない場合はNone
        """
        # attacker/defender を source/target にマッピング
        if role == "attacker":
            return self.source
        elif role == "defender":
            return self.target
        return getattr(self, role, None)

    def resolve_role(self,
                     battle: Battle,
                     spec: RoleSpec | None) -> Pokemon | None:
        """ロール指定からポケモンを解決する。
        Args:
            battle: バトルインスタンス
            spec: "role:side"形式のロール指定（例: "source:foe"）

        Returns:
            Pokemon | None: 解決されたポケモン。存在しない場合はNone
        """
        if spec is None:
            return None

        role, side = spec.split(":")
        mon = self.get(role)
        if mon and side == "foe":
            mon = battle.foe(mon)
        return mon
