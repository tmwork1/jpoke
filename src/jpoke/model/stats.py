"""ポケモンのステータス計算を担当するモジュール。

種族値、個体値、努力値、性格補正を基に実数値を計算する純粋関数を提供する。
"""


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
    # ヌケニン（種族値HP=1）は個体値・努力値・レベルに関わらずHP実数値が常に1固定
    # （fuzzログ seed=2040で発見: 通常式で計算されLv43で81になっていた）。
    if base == 1:
        return 1
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
