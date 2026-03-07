"""バトルログの記録と管理を行うモジュール。

バトル中の各種イベント、コマンド、ダメージ情報を記録します。
ログは後で再生やデバッグ、戦略分析に使用できます。
"""
from typing import TypedDict
from dataclasses import dataclass

from jpoke.utils.type_defs import Stat
from jpoke.enums import LogCode
from jpoke.utils import fast_copy


class Payload(TypedDict, total=False):
    """イベントの詳細情報を表す型定義。

    イベントログに付随する追加情報を格納するための辞書構造。
    例えば、技の名前、ダメージ量、状態異常の種類などが含まれる。
    """
    # 汎用フィールド
    text: str | None = None
    success: bool | None = None

    # 特定のソース
    pokemon: str | None = None
    ability: str | None = None
    item: str | None = None
    move: str | None = None
    volatile: str | None = None
    ailment: str | None = None

    # その他
    stat: Stat | None = None
    value: int | None = None
    reason: str | None = None


@dataclass(frozen=True)
class EventLog:
    """バトル中のイベント

    技の使用、特性の発動、状態異常の付与など、ターン中に発生した
    すべてのイベントを記録する。

    Attributes:
        turn: ログが記録されたターン番号
        idx: プレイヤーのインデックス (0 or 1)
        log: イベントの内容を表すLogCode列挙値
        payload: イベントの詳細情報（必要に応じて）
    """
    turn: int
    idx: int
    log: LogCode
    payload: Payload | None = None

    def to_dict(self) -> dict:
        """ログエントリを辞書形式に変換。

        Returns:
            ログデータを含む辞書
        """
        return vars(self).copy()

    def render(self) -> str:
        """ログエントリをテキスト表現に変換。

        LogCode と Payload から人間が読める文字列を生成します。

        Returns:
            ログのテキスト表現
        """
        if not self.payload:
            return self.log.name

        # LogCode に応じた適切なテキスト変換
        match self.log:
            case LogCode.TEXT_LOG:
                return self.payload.get("text", "")

            case LogCode.ABILITY_TRIGGERED:
                ability = self.payload.get("ability", "特性")
                success = self.payload.get("success", True)
                text = ability
                if not success:
                    text += "失敗"
                return text

            case LogCode.CONSUME_ITEM:
                item = self.payload.get("item", "持ち物")
                success = self.payload.get("success", True)
                text = item
                if not success:
                    text += "失敗"
                return text

            case LogCode.VOLATILE_APPLIED:
                volatile = self.payload.get("volatile", "揮発状態")
                return f"{volatile}が付与された"

            case LogCode.VOLATILE_REMOVED:
                volatile = self.payload.get("volatile", "揮発状態")
                return f"{volatile}が解除された"

            case LogCode.APPLY_AILMENT:
                ailment = self.payload.get("ailment", "状態異常")
                return f"{ailment}になった"

            case LogCode.CURE_AILMENT:
                ailment = self.payload.get("ailment", "状態異常")
                return f"{ailment}が回復した"

            case LogCode.MODIFY_STAT:
                stat = self.payload.get("stat", "能力値")
                change = self.payload.get("value", 0)
                direction = "上がった" if change > 0 else "下がった"
                return f"{stat}が{direction}"

            case LogCode.HEAL:
                value = self.payload.get("value", 0)
                return f"{value}回復"

            case LogCode.DAMAGE:
                value = self.payload.get("value", 0)
                return f"{value}ダメージ"

            case LogCode.ACTION_BLOCKED:
                reason = self.payload.get("reason", "")
                return f"{reason}で動けない" if reason else "動けない"

            case _:
                return self.log.name


class EventLogger:
    """バトル中のログを管理するクラス。

    バトル中に発生するイベント、コマンド、ダメージを記録し、
    ターンごと、プレイヤーごとに取得可能にする。

    Attributes:
        logs: ログのリスト
    """

    def __init__(self):
        self.logs: list[EventLog] = []

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        return fast_copy(self, new)

    def clear(self):
        """すべてのログをクリアする。"""
        self.logs.clear()

    def add(self, turn: int, idx: int, log: LogCode, payload: Payload | None = None):
        """イベントログを追加。

        Args:
            turn: ターン番号
            idx: プレイヤーインデックス (0 or 1)
            log: イベントの内容を表すLogCode列挙値
            payload: イベントの詳細情報（必要に応じて）
        """
        self.logs.append(EventLog(turn, idx, log, payload))

    def get(self, turn: int, idx: int) -> list[EventLog]:
        """指定したターンとプレイヤーのイベントログを取得。

        Args:
            turn: ターン番号
            idx: プレイヤーインデックス (0 or 1)

        Returns:
            EventLog オブジェクトのリスト
        """
        return [log for log in self.logs if
                log.turn == turn and log.idx == idx]
