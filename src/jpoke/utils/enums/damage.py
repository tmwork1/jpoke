"""ダメージ計算関連のEnum定義"""
from enum import Enum


class DamageFlag(Enum):
    """ダメージ計算時の特殊フラグ

    急所やランク無視などの特殊なダメージ計算条件を表す。
    値は日本語の説明文を持つ。
    """
    CRITICAL = "急所"
    IGNORE_ATK_RANK_BY_TENNEN = "てんねん 攻撃ランク無視"
    IGNORE_ATK_DOWN_DURING_CRITICAL = "急所 攻撃ランク無視"
    IGNORE_DEF_RANK_BY_MOVE = "技 防御ランク無視"
    IGNORE_DEF_RANK_BY_TENNEN = "てんねん 防御ランク無視"
    IGNORE_DEF_UP_DURING_CRITICAL = "急所 防御ランク無視"
