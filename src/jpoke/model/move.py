
from jpoke.utils.type_defs import MoveCategory
from jpoke.utils import fast_copy
from jpoke.data import MOVES

from .effect import GameEffect


class Move(GameEffect):
    """ポケモンの技を表すクラス。

    技は戦闘中に使用される攻撃や補助効果を持ち、
    PP（パワーポイント）によって使用回数が制限される。

    Attributes:
        pp: 技の残りPP（使用可能回数）
        _type: 技のタイプ（一部の効果で変更される可能性がある）
    """

    def __init__(self, name: str, pp: int | None = None):
        """技を初期化する。

        Args:
            name: 技名
            pp: 初期PP。Noneの場合はデータから取得した最大PPを使用
        """
        super().__init__(MOVES[name])
        self._initial_pp: int = pp if pp else self.data.pp
        self.pp: int = self._initial_pp
        self._type: str = self.data.type

    def init_game(self):
        """ゲーム初期化処理。

        PPとタイプをゲーム開始時の状態にリセットする。
        """
        self.reset_effect()
        self.pp = self._initial_pp
        self._type = self.data.type

    def bench_reset(self):
        """ベンチに戻ったときのリセット処理。

        技のタイプを元の状態にリセットする。
        """
        self._type: str = self.data.type

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        return fast_copy(self, new)

    def to_dict(self):
        """技の情報を辞書形式で返す。

        Returns:
            技名とPPを含む辞書
        """
        return {"name": self.name, "pp": self.pp}

    def modify_pp(self, v: int):
        """技のPPを増減させる。

        Args:
            v: 増減量（正の値で増加、負の値で減少）

        Note:
            PPは0から最大PPの範囲に制限される。
        """
        self.pp = max(0, min(self.data.pp, self.pp + v))

    @property
    def type(self) -> str:
        """技の現在のタイプを取得する。

        Returns:
            技のタイプ（一部の効果で変更されている可能性がある）
        """
        return self._type

    @property
    def category(self) -> MoveCategory:
        """技の分類を取得する。

        Returns:
            技の分類（物理、特殊、変化）
        """
        return self.data.category
