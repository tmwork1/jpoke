"""ポケモンのステータス計算を担当するモジュール。

種族値、個体値、努力値、性格補正を基に実数値を計算する。
"""

from jpoke.types import Nature, Stat
from jpoke.utils.constants import STATS
from jpoke.data import NATURE_MODIFIER


def calc_hp(level: int, base: int, indiv: int, effort: int) -> int:
    """HPの実数値を計算する。

    Args:
        level: レベル
        base: 種族値
        indiv: 個体値
        effort: 努力値

    Returns:
        HPの実数値
    """
    return ((base*2 + indiv + effort//4) * level) // 100 + level + 10


def calc_stat(level: int, base: int, indiv: int, effort: int, nc: float) -> int:
    """HP以外のステータスの実数値を計算する。

    Args:
        level: レベル
        base: 種族値
        indiv: 個体値
        effort: 努力値
        nc: 性格補正

    Returns:
        ステータスの実数値
    """
    return int((((base*2 + indiv + effort//4) * level) // 100 + 5) * nc)


def chmp_to_legacy_effort(effort_chmp: int) -> int:
    """Champions努力値（0〜32）をレガシー努力値（0〜252）に変換する。

    Args:
        effort_chmp: Champions形式の努力値（0〜32）

    Returns:
        レガシー努力値（0, 4, 12, ..., 252）
    """
    return 0 if effort_chmp == 0 else 8*effort_chmp - 4


class PokemonStats:
    """ポケモンのステータス計算を管理するクラス。

    個体値、努力値、レベル、性格から実数値を計算し、
    実数値から逆算して努力値を設定する機能を提供する。

    Attributes:
        _stats: 実数値のリスト [HP, 攻撃, 防御, 特攻, 特防, 素早さ]
        indiv: 個体値のリスト
        effort: 努力値のリスト（Champions形式、0〜32）
    """

    def __init__(self):
        """ステータス計算マネージャーを初期化する。"""
        self._stats: list[int] = [100]*6
        self.indiv: list[int] = [31]*6
        self.effort: list[int] = [0]*6

    @property
    def stats(self) -> list[int]:
        """実数値のリストを取得する。

        Returns:
            [HP, 攻撃, 防御, 特攻, 特防, 素早さ]
        """
        return self._stats

    @property
    def stats_dict(self) -> dict[Stat, int]:
        """ステータスを辞書形式で取得する。

        Returns:
            ステータス名をキーとする実数値の辞書
        """
        labels = STATS[:6]
        return {s: v for s, v in zip(labels, self._stats)}

    def update_stats(self, level: int, base: list[int], nature: Nature):
        """ステータスを再計算する。

        Args:
            level: ポケモンのレベル
            base: 種族値のリスト
            nature: 性格

        Note:
            レベル、性格、種族値、個体値、努力値に基づいて
            全ステータスを再計算する。レベルアップや性格変更時に使用。
        """
        # HP計算
        self._stats[0] = calc_hp(
            level, base[0],
            self.indiv[0], chmp_to_legacy_effort(self.effort[0])
        )

        # その他のステータス計算
        nc = NATURE_MODIFIER[nature]
        for i in range(1, 6):
            self._stats[i] = calc_stat(
                level, base[i],
                self.indiv[i], chmp_to_legacy_effort(self.effort[i]), nc[i]
            )

    def set_stats_from_value(self, idx: int, value: int, level: int, base: list[int], nature: Nature) -> bool:
        """指定した実数値になるよう努力値を設定する。

        Args:
            idx: ステータスのインデックス (0=HP, 1=攻撃, 2=防御, ...)
            value: 目標の実数値
            level: ポケモンのレベル
            base: 種族値のリスト
            nature: 性格

        Returns:
            設定に成功した場合True、失敗した場合False
        """
        return self._calculate_effort_from_stat(idx, value, level, base, nature)

    def set_stats_from_dict(self, stats: dict[Stat, int], level: int, base: list[int], nature: Nature):
        """実数値から努力値を逆算して設定する。

        Args:
            stats: ステータス名をキー、実数値を値とする辞書
            level: ポケモンのレベル
            base: 種族値のリスト
            nature: 性格
        """
        stat_values = list(stats.values())
        for i in range(6):
            self._calculate_effort_from_stat(i, stat_values[i], level, base, nature)

    def _calculate_effort_from_stat(self, idx: int, value: int, level: int, base: list[int], nature: Nature) -> bool:
        """指定された実数値から努力値を逆算する。

        Args:
            idx: ステータスのインデックス (0=HP, 1=攻撃, 2=防御, ...)
            value: 目標とする実数値
            level: ポケモンのレベル
            base: 種族値のリスト
            nature: 性格

        Returns:
            逆算に成功した場合True、失敗した場合False

        Note:
            Champions努力値（0〜32）に対応するSV等価値を前提とした逆算を行う。
            該当する努力値が見つからない場合は失敗する。
        """
        nc = NATURE_MODIFIER[nature]

        for chmp in range(33):
            eff = chmp_to_legacy_effort(chmp)
            if idx == 0:
                v = calc_hp(level, base[idx], self.indiv[idx], eff)
            else:
                v = calc_stat(level, base[idx], self.indiv[idx], eff, nc[idx])

            if v == value:
                self.effort[idx] = chmp
                self._stats[idx] = v
                return True

        return False
