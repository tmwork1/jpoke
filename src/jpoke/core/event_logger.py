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
    pokemon: str | None = None
    ability: str | None = None
    item: str | None = None
    move: str | None = None
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

    def get(self, turn: int, idx: int) -> list[str]:
        """指定したターンとプレイヤーのイベントログを取得。

        Args:
            turn: ターン番号
            idx: プレイヤーインデックス (0 or 1)

        Returns:
            イベントテキストのリスト
        """
        return [log.text for log in self.logs if
                log.turn == turn and log.idx == idx]
