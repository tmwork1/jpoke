from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.types import Type, MoveCategory, MoveFlag, MoveTarget, MoveName

from jpoke.utils import fast_copy
from jpoke.data.move import MOVES
from jpoke.data.models import MoveData
from .effect import GameEffect


class Move(GameEffect):
    """ポケモンの技を表すクラス。

    技は戦闘中に使用される攻撃や補助効果を持ち、
    PP（パワーポイント）によって使用回数が制限される。

    Attributes:
        pp: 技の残りPP（使用可能回数）
        _type: 技のタイプ（一部の効果で変更される可能性がある）
        is_forced_continuation: あばれる・さわぐ等、Command.FORCEDによる強制続行
            ターンで使い捨て生成されたインスタンスかどうか
    """

    def __init__(self, name: MoveName, is_forced_continuation: bool = False):
        """技を初期化する。

        Args:
            name: 技名
            is_forced_continuation: Command.FORCEDによる強制続行ターンで
                生成された使い捨てインスタンスの場合True。CommandManager
                （`resolve_move_from_command`）が明示的に指定する
        """
        super().__init__(MOVES[name])
        self.pp: int = self.data.pp

        self.type: Type = self.data.type
        self.base_power: int | None = self.data.power
        self.category: MoveCategory = self.data.category
        self.is_forced_continuation: bool = is_forced_continuation

        self.data: MoveData  # type hint

    def reset(self, reset_pp: bool = False):
        """技の状態をリセットする。"""
        self.type = self.data.type
        self.base_power = self.data.power
        self.category = self.data.category
        if reset_pp:
            self.pp = self.data.pp

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        return fast_copy(self, new)

    def to_dict(self) -> dict:
        """技の情報を辞書形式で返す。

        Returns:
            dict: 技名とPPを含む辞書
        """
        return {"name": self.name, "pp": self.pp}

    def has_flag(self, flag: MoveFlag | list[MoveFlag]) -> bool:
        """技が特定のフラグを持っているかを判定する。

        Args:
            flag: 判定するフラグ（単一のフラグまたは複数のフラグのリスト）。
                複数のフラグが指定された場合、いずれかのフラグを持っていればTrueを返す

        Returns:
            技が指定されたフラグを持っている場合True
        """
        if isinstance(flag, list):
            return any(s in self.data.flags for s in flag)
        return flag in self.data.flags

    def modify_pp(self, v: int):
        """技のPPを増減させる。PPは0から最大PPの範囲に制限される。

        Args:
            v: 増減量（正の値で増加、負の値で減少）
        """
        self.pp = max(0, min(self.data.pp, self.pp + v))

    @property
    def priority(self) -> int:
        """技の優先度を取得する。"""
        return self.data.priority

    @property
    def accuracy(self) -> int | None:
        """技の命中率を取得する。Noneの場合は必中。"""
        return self.data.accuracy

    @property
    def crit_ratio(self) -> int:
        """急所ランク補正値を取得する。"""
        return self.data.crit_ratio

    @property
    def guaranteed_crit(self) -> bool:
        """技が必ず急所に当たるかどうかを判定する。"""
        return self.data.crit_ratio >= 3

    @property
    def target(self) -> MoveTarget:
        """技の対象を取得する。"""
        return self.data.target

    @property
    def min_hits(self) -> int:
        """技の最小ヒット数を取得する。"""
        if self.data.multi_hit is None:
            return 1
        return self.data.multi_hit["min"]

    @property
    def max_hits(self) -> int:
        """技の最大ヒット数を取得する。"""
        if self.data.multi_hit is None:
            return 1
        return self.data.multi_hit["max"]

    @property
    def is_attack(self) -> bool:
        """技が攻撃技かどうかを判定する。

        Returns:
            技が物理または特殊技の場合True
        """
        return self.category in ["physical", "special"]

    @property
    def is_blocked_by_protect(self) -> bool:
        """技がまもるで防がれるかどうかを判定する。

        Returns:
            技がまもるで防がれる場合True
        """
        return (
            self.target == "foe"
            and not self.has_flag("unprotectable")
        )

    @property
    def is_blocked_by_wide_guard(self) -> bool:
        """技がワイドガードで防がれるかどうかを判定する。

        本プロジェクトはシングルバトル専用で `target` にダブル・トリプルバトルの
        「相手全体」「自分以外全体」区分（スプレッド技かどうか）を持たないため、
        `"spread"` フラグ（技データ上、実機でダブル時に複数対象になる技へ個別付与）で判定する。
        `unprotectable` フラグを持つ技はスプレッド技であってもワイドガードで防げない
        （まもる等と同じ除外ルール。ドラゴンアローはそもそも `"spread"` フラグを
        持たないため、この判定に依らず自然に対象外になる）。

        Returns:
            技がワイドガードで防がれる場合True
        """
        return (
            self.has_flag("spread")
            and not self.has_flag("unprotectable")
        )

    @property
    def is_reflectable(self) -> bool:
        """技がマジックコート・マジックミラーで跳ね返されるかどうかを判定する。

        Returns:
            技が跳ね返される場合True
        """
        return (
            self.category == "status"
            and self.target in ("foe", "foe_side")
            and not self.has_flag("unreflectable")
        )

    # ── poke-env 互換 ───────────────────────────────────────────

    @property
    def current_pp(self) -> int:
        """poke-env 互換: 技の残りPP（`pp` のエイリアス）。"""
        return self.pp

    @property
    def max_pp(self) -> int:
        """poke-env 互換: 技の最大PP（`data.pp` のエイリアス）。"""
        return self.data.pp

    @property
    def expected_hits(self) -> float:
        """poke-env 互換: 期待ヒット数（poke-env の実装に合わせる）。"""
        if self.min_hits == self.max_hits:
            return float(self.min_hits)
        # 2〜5回技のヒット数分布 2:3:4:5 = 35:35:15:15 の期待値 3.1（poke-env と同値）。
        return (2 + 3) * 0.35 + (4 + 5) * 0.15
