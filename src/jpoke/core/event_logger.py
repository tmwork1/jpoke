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
    reason: str | None = None

    # 特定のソース
    pokemon: str | None = None
    ability: str | None = None
    item: str | None = None
    move: str | None = None
    action_order: str | None = None
    ailment: str | None = None
    volatile: str | None = None
    text: str | None = None

    # その他
    stat: Stat | None = None
    value: int | None = None
    percent: int | None = None


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
        reasonがある場合は"[基本記述]:[reason]"形式で統一します。

        Returns:
            ログのテキスト表現
        """
        if not self.payload:
            return self.log.name

        # reasonを統一フォーマットで付与
        reason = self.payload.get("reason")
        base_text = self._get_base_text()

        if reason:
            return f"{base_text} [{reason}]"
        return base_text

    def _get_base_text(self) -> str:
        """LogCodeに対応する基本的なテキストを生成。

        Returns:
            基本的なテキスト表現
        """
        if not self.payload:
            return self.log.name

        # LogCode に応じた適切なテキスト変換
        match self.log:
            case LogCode.TEXT_LOG:
                return self.payload.get("text", "")

            case LogCode.ABILITY_TRIGGERED:
                return self.payload.get("ability", "特性")

            case LogCode.CONSUME_ITEM:
                item = self.payload.get("item", "持ち物")
                return item

            case LogCode.VOLATILE_APPLIED:
                volatile = self.payload["volatile"]
                return f"{volatile}が付与された"

            case LogCode.VOLATILE_REMOVED:
                volatile = self.payload["volatile"]
                return f"{volatile}が解除された"

            case LogCode.VOLATILE_STATUS:
                return self.payload["volatile"]

            case LogCode.APPLY_AILMENT:
                ailment = self.payload.get("ailment", "状態異常")
                return f"{ailment}が付与された"

            case LogCode.CURE_AILMENT:
                ailment = self.payload.get("ailment", "状態異常")
                return f"{ailment}が回復した"

            case LogCode.MODIFY_STAT:
                stat = self.payload.get("stat", "能力値")
                change = self.payload.get("value", 0)
                direction = "上がった" if change > 0 else "下がった"
                return f"{stat}が{direction}"

            case LogCode.HP_CHANGED:
                pokemon = self.payload.get("pokemon", "ポケモン")
                value = self.payload.get("value", 0)
                percent = self.payload.get("percent", 0)
                s = f"{pokemon}  HP "
                if value > 0:
                    s += "+"
                s += f"{value} (残り {percent}%)"
                return s

            case LogCode.ACTION_BLOCKED:
                return "動けない"

            case LogCode.ACTION_START:
                pokemon = self.payload.get("pokemon", "ポケモン")
                action_order = self.payload.get("action_order", "行動")
                return f"{pokemon} {action_order}"

            case LogCode.CONSUME_PP:
                move = self.payload.get("move", "技")
                value = self.payload.get("value")
                if value is None:
                    return f"{move} PP消費"
                return f"{move} PP-{value}"

            case LogCode.HIT_SUBSTITUTE:
                return "みがわりにヒット"

            case LogCode.PROTECT_SUCCESS:
                return "攻撃を防いだ"

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
        """EventLoggerを初期化する。"""
        self.logs: list[EventLog] = []

    def __deepcopy__(self, memo):
        """EventLoggerのディープコピーを作成する。"""
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
