"""バトルログの記録と管理を行うモジュール。

バトル中の各種イベント、コマンド、ダメージ情報を記録します。
ログは後で再生やデバッグ、戦略分析に使用できます。
"""
from typing import TypedDict
from dataclasses import dataclass

from jpoke.utils.type_defs import Stat, Type
from jpoke.enums import LogCode
from jpoke.utils import fast_copy


class Payload(TypedDict, total=False):
    """イベントの詳細情報を表す型定義。

    イベントログに付随する追加情報を格納するための辞書構造。
    例えば、技の名前、ダメージ量、状態異常の種類などが含まれる。
    """
    reason: str | None
    pokemon: str | None
    ability: str | None
    item: str | None
    move: str | None
    action_order: str | None
    ailment: str | None
    volatile: str | None
    stats: dict[Stat, int] | None
    type: Type | None
    value: int | float | None
    hp: int | None
    max_hp: int | None
    field: str | None
    count: int | None
    text: str | None


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
        text = self._get_base_text()
        if reason:
            text += f" [{reason}]"
        return text

    def _get_base_text(self) -> str:
        # TODO : LogCodeを網羅する
        """LogCodeに対応する基本的なテキストを生成。

        Returns:
            基本的なテキスト表現
        """
        if not self.payload:
            return self.log.name

        # LogCode に応じた適切なテキスト変換
        match self.log:
            case LogCode.TEXT_LOG:
                return self.payload.get("text") or ""

            case LogCode.MOVE_MISSED:
                return "技が外れた"

            case LogCode.ABILITY_TRIGGERED:
                ability = self.payload.get("ability", "特性")
                return f"{ability}が発動した"

            case LogCode.ITEM_TRIGGERED:
                item = self.payload.get("item", "道具")
                return f"{item}が発動した"

            case LogCode.ITEM_GAINED:
                item = self.payload.get("item", "アイテム")
                return f"{item}を得た"

            case LogCode.ITEM_LOST:
                item = self.payload.get("item", "アイテム")
                return f"{item}を失った"

            case LogCode.AILMENT_APPLIED:
                ailment = self.payload.get("ailment", "状態異常")
                return f"{ailment}が付与された"

            case LogCode.AILMENT_REMOVED:
                ailment = self.payload.get("ailment", "状態異常")
                return f"{ailment}が回復した"

            case LogCode.AILMENT_PREVENTED:
                ailment = self.payload.get("ailment", "状態異常")
                return f"{ailment}の付与が無効化された"

            case LogCode.VOLATILE_APPLIED:
                volatile = self.payload.get("volatile", "揮発状態")
                return f"{volatile}が付与された"

            case LogCode.VOLATILE_REMOVED:
                volatile = self.payload.get("volatile", "揮発状態")
                return f"{volatile}が解除された"

            case LogCode.VOLATILE_DISPLAY:
                volatile = self.payload.get("volatile", "揮発状態")
                return f"{volatile}の状態"

            case LogCode.VOLATILE_PREVENTED:
                volatile = self.payload.get("volatile", "揮発状態")
                return f"{volatile}の付与が無効化された"

            case LogCode.STAT_CHANGED:
                stats = self.payload.get("stats", {})
                texts = []
                for stat, value in stats.items():
                    texts.append(f"{stat}{'+' if value > 0 else ''}{value}")
                return " ".join(texts)

            case LogCode.HP_CHANGED:
                value = self.payload.get("value", 0)
                hp = self.payload.get("hp", "?")
                max_hp = self.payload.get("max_hp", "?")
                return f"HP {'+' if value > 0 else ''}{value} ({hp}/{max_hp})"

            case LogCode.ACTION_BLOCKED:
                return "動けない"

            case LogCode.PP_CONSUMED:
                move = self.payload.get("move", "技")
                value = self.payload.get("value", "?")
                return f"{move} PP -{value}"

            case LogCode.SUBSTITUTE_HIT:
                return "みがわりにヒット"

            case LogCode.PROTECT_SUCCEEDED:
                return "攻撃を防いだ"

            case LogCode.MOVE_IMMUNED:
                move = self.payload.get("move", "技")
                return f"{move} を無効化した"

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
