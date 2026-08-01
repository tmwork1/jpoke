"""標準入出力でコマンドを入力しながら対戦できるプレイヤー。

`Player.choose_command()` / `choose_selection()` はBattle側から常に同期的に
呼び出されるため、`input()` でブロッキングするだけで対話操作が成立する
（非同期対応やイベントループは不要）。
"""
from __future__ import annotations

from jpoke import Battle, Player
from jpoke import text
from jpoke.enums import Command


class CLIPlayer(Player):
    """標準入出力（input()/print()）でコマンドを入力しながら対戦する人間プレイヤー。

    `choose_selection()` / `choose_command()` の呼び出しごとに現在の盤面
    （直前ターンのログ、自分・相手の場のポケモンのHP・状態異常・ランク補正・
    テラスタル状況、天候・フィールド・場の状態）を表示し、番号入力で
    コマンドを選ばせる。選択肢が1つしかない場合（わるあがき、交代先が
    1体のみ等）は表示のうえ入力を求めず自動的に確定する。
    """

    def choose_selection(self, battle: Battle) -> list[int]:
        """チームを表示し、選出するポケモンの番号を対話的に選ばせる。"""
        n = battle.n_selected
        print(f"\n=== {self.username}: 選出（{n}体選んでください） ===")
        for i, mon in enumerate(self.team):
            types = "/".join(t for t in mon.types if t)
            print(f"{i}: {mon.name} (タイプ:{types} 特性:{mon.ability.name} "
                  f"持ち物:{mon.item.name or 'なし'})")
            for move in mon.moves:
                print(f"      - {move.name} (タイプ:{move.type} 分類:{move.category} PP:{move.pp})")

        while True:
            raw = input(f"選出番号を空白区切りで{n}個入力: ").strip()
            try:
                indexes = [int(x) for x in raw.split()]
            except ValueError:
                print("数字を空白区切りで入力してください。")
                continue
            if len(indexes) != n or len(set(indexes)) != n:
                print(f"重複なしで{n}個の番号を入力してください。")
                continue
            if any(i < 0 or i >= len(self.team) for i in indexes):
                print(f"0〜{len(self.team) - 1}の範囲で入力してください。")
                continue
            return indexes

    def choose_command(self, battle: Battle) -> Command:
        """現在の盤面を表示し、行動コマンドを対話的に選ばせる。"""
        for line in text.render_battle_state(battle, self):
            print(line)

        commands = battle.available_commands(self)
        if len(commands) == 1:
            command = commands[0]
            print(f"選択肢が1つのため自動選択します: {text.describe_command(battle, self, command)}")
            return command

        print("--- 選択可能なコマンド ---")
        for i, command in enumerate(commands):
            print(f"{i}: {text.describe_command(battle, self, command)}")

        while True:
            raw = input("コマンド番号を入力: ").strip()
            try:
                choice = int(raw)
            except ValueError:
                print("数字を入力してください。")
                continue
            if choice < 0 or choice >= len(commands):
                print(f"0〜{len(commands) - 1}の範囲で入力してください。")
                continue
            return commands[choice]
