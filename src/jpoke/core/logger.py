"""バトルログの記録と管理を行うモジュール。

バトル中の各種イベント、コマンド、ダメージ情報を記録します。
ログは後で再生やデバッグ、戦略分析に使用できます。
"""
from dataclasses import dataclass
import json

from jpoke.utils.enums import Command
from jpoke.utils import fast_copy


@dataclass(frozen=True)
class BaseLog:
    """ログエントリの基底クラス。

    Attributes:
        turn: ログが記録されたターン番号
        idx: プレイヤーのインデックス (0 or 1)
    """
    turn: int
    idx: int

    def to_dict(self) -> dict:
        """ログエントリを辞書形式に変換。

        Returns:
            ログデータを含む辞書
        """
        return vars(self).copy()


@dataclass(frozen=True)
class EventLog(BaseLog):
    """バトル中のイベント・アクション・メッセージを記録するログ。

    技の使用、特性の発動、状態異常の付与など、ターン中に発生した
    すべてのイベントを記録する。

    Attributes:
        text: イベントの内容を表すテキスト
    """
    text: str


@dataclass(frozen=True)
class CommandLog(BaseLog):
    """プレイヤーが選択したコマンドを記録するログ。

    リプレイ再生や戦略分析に使用される。

    Attributes:
        command: 選択されたコマンド (技選択、交代など)
    """
    command: Command


@dataclass(frozen=True)
class DamageLog(BaseLog):
    """ダメージ発生時の状況を記録するログ(実装は後回し)
    """
    text: str


class Logger:
    """バトル中のログを管理するクラス。

    バトル中に発生するイベント、コマンド、ダメージを記録し、
    ターンごと、プレイヤーごとに取得可能にする。

    Attributes:
        event_logs: イベントログのリスト
        command_logs: コマンドログのリスト
        damage_logs: ダメージログのリスト
    """

    def __init__(self):
        self.event_logs: list[EventLog] = []
        self.command_logs: list[CommandLog] = []
        self.damage_logs: list[DamageLog] = []

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        return fast_copy(self, new)

    def clear(self):
        """すべてのログをクリアする。"""
        self.event_logs.clear()
        self.command_logs.clear()
        self.damage_logs.clear()

    def get_event_logs(self, turn: int, idx: int) -> list[str]:
        """指定したターンとプレイヤーのイベントログを取得。

        Args:
            turn: ターン番号
            idx: プレイヤーインデックス (0 or 1)

        Returns:
            イベントテキストのリスト
        """
        return [log.text for log in self.event_logs if
                log.turn == turn and log.idx == idx]

    def get_command_logs(self, turn: int, idx: int) -> list[Command]:
        """指定したターンとプレイヤーのコマンドログを取得。

        Args:
            turn: ターン番号
            idx: プレイヤーインデックス (0 or 1)

        Returns:
            コマンドのリスト
        """
        return [log.command for log in self.command_logs if
                log.turn == turn and log.idx == idx]

    def get_damage_logs(self, turn: int, idx: int) -> list[str]:
        """指定したターンとプレイヤーのダメージログを取得。

        Args:
            turn: ターン番号
            idx: プレイヤーインデックス (0 or 1)

        Returns:
            ダメージテキストのリスト
        """
        return [log.text for log in self.damage_logs if
                log.turn == turn and log.idx == idx]

    def add_event_log(self, turn: int, idx: int, text: str):
        """イベントログを追加。

        Args:
            turn: ターン番号
            idx: プレイヤーインデックス (0 or 1)
            text: イベントの内容
        """
        self.event_logs.append(EventLog(turn, idx, text))

    def add_command_log(self, turn: int, idx: int, command: Command):
        """コマンドログを追加。

        Args:
            turn: ターン番号
            idx: プレイヤーインデックス (0 or 1)
            command: 選択されたコマンド
        """
        self.command_logs.append(CommandLog(turn, idx, command))

    def add_damage_log(self, turn: int, idx: int, text: str):
        """ダメージログを追加。

        Args:
            turn: ターン番号
            idx: プレイヤーインデックス (0 or 1)
            text: ダメージの詳細情報
        """
        self.damage_logs.append(DamageLog(turn, idx, text))

    def export_log(self, file: str, seed: int, players_data: list[dict]):
        """バトルログをJSON形式でエクスポート。

        Args:
            file: 出力先ファイルパス
            seed: バトルのシード値
            players_data: プレイヤーごとのデータ（name, selection_indexes, team）
        """
        data = {
            "seed": seed,
            "players": [],
        }

        # プレイヤーデータをコピー
        for player_data in players_data:
            data["players"].append({
                "name": player_data["name"],
                "selection_indexes": player_data["selection_indexes"],
                "commands": {},
                "team": player_data["team"],
            })

        # コマンドログを追加
        for log in self.command_logs:
            data["players"][log.idx]["commands"].setdefault(
                str(log.turn), []).append(log.command.name)

        # ファイルに書き込み
        with open(file, 'w', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=4))
