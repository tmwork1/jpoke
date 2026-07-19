from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.data.ability import AbilityData

from jpoke.utils import fast_copy
from jpoke.data.ability import ABILITIES
from jpoke.types import AbilityState, AbilityName, ItemName, WeatherName

from .effect import GameEffect


class Ability(GameEffect):
    """ポケモンの特性を表すクラス。

    特性は戦闘中に自動的に発動する効果を持ち、
    特定のイベントに対してハンドラを登録します。

    Attributes:
        count: 特性の発動回数などを記録するカウンター
        state: 特性の状態を表す文字列。必要に応じて Literal を拡張する。
    """

    def __init__(self, name: AbilityName = "") -> None:
        """特性を初期化する。

        Args:
            name: 特性名。空文字列の場合は特性なしとして扱う
        """
        super().__init__(ABILITIES[name])
        self.count: int = 0
        self.state: AbilityState = ""

        self.is_hangry: bool = False
        self.activated_since_switch_in: bool = False
        self.mold_breaker_active: bool = False

        self.cud_chew_item: ItemName = ""
        """はんすう専用: 次のターン終了時に再度食べるきのみ名。"""
        self.cud_chew_turns: int = 0
        """はんすう専用: 再発動までの残りターン数（消費時点で2にセットし0で発動）。"""

        self.saved_weather_name: WeatherName = ""
        """メガソーラー専用: 天候を「はれ」に上書きする前の本来の天候名を一時保存する。"""
        self.saved_weather_count: int = 0
        """メガソーラー専用: 天候を上書きする前の「はれ」フィールドのカウントを一時保存する。"""
        self.weather_override_depth: int = 0
        """メガソーラー専用: ねごと・まねっこ等で技実行がネストした場合に対応する深度カウンター。
        最も外側の ON_BEGIN_MOVE でのみ本来の天候を保存し、深度が0に戻る
        ON_END_MOVE でのみ復元する。"""
        self.saved_weather_version: int = 0
        """メガソーラー専用: 天候を上書きした時点の WeatherManager.change_version を
        一時保存する。技使用中に相手のすなはき等で本物の天候変化が発生したかどうかを
        判定するために使う（一致していれば仮想上書きのみ、一致しなければ本物の
        天候変化が発生済みなので復元処理をスキップする。`メガソーラー_deactivate` 参照）。"""

        self.data: AbilityData  # 型ヒントのための属性。実際のデータはsuper().__init__で設定される

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        return fast_copy(self, new)

    def reset_on_switch_out(self):
        """ベンチに戻ったときのリセット処理。

        特性の状態をリセットし、カウンターを0に戻す。
        """
        self.count = 0
        self.state = ""
        self.activated_since_switch_in = False
        self.cud_chew_item = ""
        self.cud_chew_turns = 0
        self.saved_weather_name = ""
        self.saved_weather_count = 0
        self.weather_override_depth = 0
        self.saved_weather_version = 0
        self.reset_enable_state()

    def reset_enable_state(self):
        """
        特性の有効/無効状態をリセットする。

        特性の状態を初期状態に戻す。
        試合中一度しか発動しない特性は自己無効化フラグを維持する。
        """
        reasons = set()
        if self.has_flag("per_battle_once") and self.consumed:
            reasons.add("consumed")
        self.replace_disabled_reasons(reasons)

    def has_flag(self, flag: str) -> bool:
        """特性の状態フラグを判定する。

        Args:
            flag: 判定するフラグ名

        Returns:
            bool: フラグが立っているかどうか
        """
        return flag in self.data.flags
