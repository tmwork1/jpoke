"""バトルログの記録と管理を行うモジュール。

バトル中の各種イベント、コマンド、ダメージ情報を記録します。
ログは後で再生やデバッグ、戦略分析に使用できます。
"""
from dataclasses import dataclass
import json

from jpoke.enums import Command
from jpoke.utils import fast_copy


@dataclass(frozen=True)
class CommandLog:
    """プレイヤーが選択したコマンドを記録するログ。

    リプレイ再生や戦略分析に使用される。

    Attributes:
        turn: ログが記録されたターン番号
        idx: プレイヤーのインデックス (0 or 1)
        command: 選択されたコマンド (技選択、交代など)
    """
    turn: int
    idx: int
    command: Command

    def to_dict(self) -> dict:
        """ログエントリを辞書形式に変換。

        Returns:
            ログデータを含む辞書
        """
        return vars(self).copy()


class CommandLogger:
    """バトル中のコマンドログを管理するクラス。

    バトル中に発生するコマンドを記録し、
    ターンごと、プレイヤーごとに取得可能にする。

    Attributes:
        logs: コマンドログのリスト
    """

    def __init__(self):
        self.logs: list[CommandLog] = []

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        return fast_copy(self, new)

    def clear(self):
        """すべてのログをクリアする。"""
        self.logs.clear()

    def add(self, turn: int, idx: int, command: Command):
        """コマンドログを追加。

        Args:
            turn: ターン番号
            idx: プレイヤーインデックス (0 or 1)
            command: 選択されたコマンド
        """
        self.logs.append(CommandLog(turn, idx, command))

    def get(self, turn: int, idx: int) -> list[Command]:
        """指定したターンとプレイヤーのコマンドログを取得。

        Args:
            turn: ターン番号
            idx: プレイヤーインデックス (0 or 1)

        Returns:
            コマンドのリスト
        """
        return [log.command for log in self.logs if
                log.turn == turn and log.idx == idx]

    def export(self, file: str, seed: int, players_data: list[dict]):
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
        for log in self.logs:
            data["players"][log.idx]["commands"].setdefault(
                str(log.turn), []).append(log.command.name)

        # ファイルに書き込み
        with open(file, 'w', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=4))
