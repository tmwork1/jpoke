from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.data import AbilityData

from jpoke.utils import fast_copy
from jpoke.data import ABILITIES
from jpoke.utils.type_defs import AbilityState

from .effect import GameEffect


class Ability(GameEffect):
    """ポケモンの特性を表すクラス。

    特性は戦闘中に自動的に発動する効果を持ち、
    特定のイベントに対してハンドラを登録します。

    Attributes:
        count: 特性の発動回数などを記録するカウンター
        state: 特性の状態を表す文字列。必要に応じて Literal を拡張する。
    """

    def __init__(self, name: str = "") -> None:
        """特性を初期化する。

        Args:
            name: 特性名。空文字列の場合は特性なしとして扱う
        """
        super().__init__(ABILITIES[name])
        self.count: int = 0
        self.state: AbilityState = ""
        self.is_hangry: bool = False
        self.activated_since_switch_in: bool = False

        self.data: AbilityData  # 型ヒントのための属性。実際のデータはsuper().__init__で設定される

    def __deepcopy__(self, memo):
        """特性オブジェクトのディープコピーを作成する。"""
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        return fast_copy(self, new)

    def init_game(self):
        """ゲーム初期化処理。

        カウンターをリセットし、ゲーム開始時の状態にする。
        """
        self.bench_reset()

    def bench_reset(self):
        """ベンチに戻ったときのリセット処理。

        特性の状態をリセットし、カウンターを0に戻す。
        """
        self.count = 0
        self.state = ""
        self.is_hangry = False
        self.activated_since_switch_in = False
        self.reset_enabled()

    def reset_enabled(self):
        """
        特性の有効/無効状態をリセットする。

        特性の状態を初期状態に戻す。
        試合中一度しか発動しない特性は、未発動であれば有効にする。
        """
        initial = (
            not self.has_flag("per_battle_once")
            or self.get_enabled("self")
        )
        super().reset_enabled(initial=initial)

    def has_flag(self, flag: str) -> bool:
        """特性の状態フラグを判定する。

        Args:
            flag: 判定するフラグ名

        Returns:
            bool: フラグが立っているかどうか
        """
        return flag in self.data.flags
