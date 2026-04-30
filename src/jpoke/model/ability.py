from jpoke.utils import fast_copy
from jpoke.data import ABILITIES

from .effect import GameEffect


class Ability(GameEffect):
    """ポケモンの特性を表すクラス。

    特性は戦闘中に自動的に発動する効果を持ち、
    特定のイベントに対してハンドラを登録します。

    Attributes:
        count: 特性の発動回数などを記録するカウンター
    """

    def __init__(self, name: str = "") -> None:
        """特性を初期化する。

        Args:
            name: 特性名。空文字列の場合は特性なしとして扱う
        """
        super().__init__(ABILITIES[name])
        self.count: int = 0
        self.is_hangry: bool = False
        self.activated_since_switch_in: bool = False

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
        self.is_hangry = False
        self.activated_since_switch_in = False

    def __deepcopy__(self, memo):
        """特性オブジェクトのディープコピーを作成する。"""
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        return fast_copy(self, new)
