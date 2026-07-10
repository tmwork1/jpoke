"""バトルログの記録と管理を行うモジュール。

バトル中の各種イベント、コマンド、ダメージ情報を記録します。
ログは後で再生やデバッグ、戦略分析に使用できます。
"""
from dataclasses import dataclass, asdict

from jpoke.enums import LogCode
from jpoke.core.log_payload import (
    Payload, FailureLogPayload, HPChangePayload, StatChangePayload,
    AilmentPayload, VolatilePayload, AbilityPayload, ItemPayload,
    SwitchPayload, FieldPayload, MoveActionPayload, TerastalPayload,
    TextPayload,
)


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
            JSON-serializable なログデータを含む辞書
        """
        return {
            "turn": self.turn,
            "idx": self.idx,
            "log": self.log.name,
            "payload": asdict(self.payload) if self.payload is not None else None,
        }

    def render(self) -> str:
        """ログエントリをテキスト表現に変換。

        LogCode と Payload から人間が読める文字列を生成します。
        display_reasonがある場合は"[基本記述]:[display_reason]"形式で統一します。

        Returns:
            ログのテキスト表現
        """
        text = self._get_base_text()
        if self.payload and self.payload.display_reason:
            text += f" [{self.payload.display_reason}]"
        return text

    def _get_base_text(self) -> str:
        """LogCodeに対応する基本的なテキストを生成。

        Returns:
            基本的なテキスト表現
        """
        payload = self.payload

        # LogCode に応じた適切なテキスト変換
        match self.log:
            case LogCode.GAME_STARTED:
                return "バトル開始"

            case LogCode.GAME_WON:
                return "勝利"

            case LogCode.GAME_LOST:
                return "敗北"

            case LogCode.SWITCHED_IN:
                pokemon = payload.pokemon if isinstance(payload, SwitchPayload) else "ポケモン"
                return f"{pokemon} 入場"

            case LogCode.SWITCHED_OUT:
                pokemon = payload.pokemon if isinstance(payload, SwitchPayload) else "ポケモン"
                return f"{pokemon} 退場"

            case LogCode.TEXT_LOG:
                return payload.text if isinstance(payload, TextPayload) else ""

            case LogCode.MOVE_FAILED:
                return "技は失敗した"

            case LogCode.MOVE_REFLECTED:
                return "技ははね返された"

            case LogCode.MOVE_MISSED:
                return "技が外れた"

            case LogCode.ABILITY_TRIGGERED:
                ability = payload.ability if isinstance(payload, AbilityPayload) else "特性"
                return f"{ability}が発動した"

            case LogCode.ITEM_TRIGGERED:
                item = payload.item if isinstance(payload, ItemPayload) else "道具"
                return f"{item}が発動した"

            case LogCode.ITEM_GAINED:
                item = payload.item if isinstance(payload, ItemPayload) else "アイテム"
                return f"{item}を得た"

            case LogCode.ITEM_LOST:
                item = payload.item if isinstance(payload, ItemPayload) else "アイテム"
                return f"{item}を失った"

            case LogCode.AILMENT_APPLIED:
                ailment = payload.ailment if isinstance(payload, AilmentPayload) else "状態異常"
                return f"{ailment}が付与された"

            case LogCode.AILMENT_REMOVED:
                ailment = payload.ailment if isinstance(payload, AilmentPayload) else "状態異常"
                return f"{ailment}が回復した"

            case LogCode.AILMENT_PREVENTED:
                ailment = payload.ailment if isinstance(payload, AilmentPayload) else "状態異常"
                return f"{ailment}の付与が無効化された"

            case LogCode.VOLATILE_IMMUNE:
                volatile = payload.volatile if isinstance(payload, VolatilePayload) else "揮発状態"
                return f"{volatile}は効かなかった"

            case LogCode.VOLATILE_APPLIED:
                volatile = payload.volatile if isinstance(payload, VolatilePayload) else "揮発状態"
                return f"{volatile}が付与された"

            case LogCode.VOLATILE_REMOVED:
                volatile = payload.volatile if isinstance(payload, VolatilePayload) else "揮発状態"
                return f"{volatile}が解除された"

            case LogCode.VOLATILE_DISPLAY:
                volatile = payload.volatile if isinstance(payload, VolatilePayload) else "揮発状態"
                return f"{volatile}の状態"

            case LogCode.VOLATILE_PREVENTED:
                volatile = payload.volatile if isinstance(payload, VolatilePayload) else "揮発状態"
                return f"{volatile}の付与が無効化された"

            case LogCode.STAT_CHANGED:
                stats = payload.stats if isinstance(payload, StatChangePayload) else {}
                texts = []
                for stat, value in stats.items():
                    texts.append(f"{stat}{'+' if value > 0 else ''}{value}")
                return " ".join(texts) if texts else "能力値が変化した"

            case LogCode.STAT_CHANGE_BLOCKED:
                return "能力値は変化しなかった"

            case LogCode.HP_CHANGED:
                value = payload.value if isinstance(payload, HPChangePayload) else 0
                hp = payload.hp if isinstance(payload, HPChangePayload) else "?"
                max_hp = payload.max_hp if isinstance(payload, HPChangePayload) else "?"
                return f"HP {'+' if value > 0 else ''}{value} ({hp}/{max_hp})"

            case LogCode.HEAL_BLOCKED:
                return "回復できない"

            case LogCode.ACTION_BLOCKED:
                return "動けない"

            case LogCode.PP_CONSUMED:
                move = payload.move if isinstance(payload, MoveActionPayload) else "技"
                pp_value = payload.value if isinstance(payload, MoveActionPayload) else "?"
                return f"{move} PP -{pp_value}"

            case LogCode.SUBSTITUTE_HIT:
                return "みがわりにヒット"

            case LogCode.PROTECT_SUCCEEDED:
                return "攻撃を防いだ"

            case LogCode.PROTECT_FAILED:
                return "まもるは失敗した"

            case LogCode.MOVE_IMMUNED:
                move = payload.move if isinstance(payload, FailureLogPayload) else "技"
                return f"{move} を無効化した"

            case LogCode.FIELD_STARTED:
                field_ = payload.field if isinstance(payload, FieldPayload) else "場の状態"
                return f"{field_} が始まった"

            case LogCode.FIELD_ENDED:
                field_ = payload.field if isinstance(payload, FieldPayload) else "場の状態"
                return f"{field_} が終わった"

            case LogCode.TERASALLIZED:
                type_ = payload.type if isinstance(payload, TerastalPayload) else None
                text = "テラスタル化した"
                if type_:
                    return text + f"（タイプ: {type_}）"
                return text

            case LogCode.MEGA_EVOLVED:
                return "メガシンカした"

            case LogCode.CRITICAL_HIT:
                return "急所に当たった！"

            case _:
                raise ValueError(f"Unsupported LogCode in EventLog._get_base_text: {self.log}")


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
