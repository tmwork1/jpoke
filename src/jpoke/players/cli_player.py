"""標準入出力でコマンドを入力しながら対戦できるプレイヤー。

`Player.choose_command()` / `choose_selection()` はBattle側から常に同期的に
呼び出されるため、`input()` でブロッキングするだけで対話操作が成立する
（非同期対応やイベントループは不要）。
"""
from __future__ import annotations

from jpoke import Battle, Player
from jpoke.enums import Command
from jpoke.model import Pokemon


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
        self._print_state(battle)

        commands = battle.available_commands(self)
        if len(commands) == 1:
            command = commands[0]
            print(f"選択肢が1つのため自動選択します: {self._describe_command(battle, command)}")
            return command

        print("--- 選択可能なコマンド ---")
        for i, command in enumerate(commands):
            print(f"{i}: {self._describe_command(battle, command)}")

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

    def _print_state(self, battle: Battle) -> None:
        """直前までのログと盤面（HP・状態・場の状態）を表示する。"""
        print(f"\n=== ターン{battle.turn} : {self.username} ===")
        battle.print_logs()

        opponent = battle.opponent(self)
        print(f"[自分] {self._describe_mon(battle.get_active(self))}")
        print(f"[相手] {self._describe_mon(battle.get_active(opponent))}")

        weather, terrain = battle.weather, battle.terrain
        if weather.is_active:
            print(f"天候: {weather.name}")
        if terrain.is_active:
            print(f"フィールド: {terrain.name}")

        for label, side_player in ((self.username, self), (opponent.username, opponent)):
            active_fields = [f.name for f in battle.get_side(side_player).fields.values() if f.is_active]
            if active_fields:
                print(f"{label}側の場の状態: {', '.join(active_fields)}")

    def _describe_mon(self, mon: Pokemon | None) -> str:
        """ポケモン1体のHP・状態異常・ランク補正・テラスタル状況を1行で表す。"""
        if mon is None:
            return "(場に出ていない)"

        hp = f"HP {mon.hp}/{mon.max_hp}"
        ailment = f" 状態異常:{mon.ailment.name}" if mon.ailment.is_active else ""
        boosts = ", ".join(f"{stat}{v:+d}" for stat, v in mon.boosts.items() if v != 0)
        boost_str = f" ランク:[{boosts}]" if boosts else ""
        tera = f" (テラス:{mon.tera_type})" if mon.is_terastallized else ""
        return f"{mon.name}{tera} {hp}{ailment}{boost_str}"

    def _describe_command(self, battle: Battle, command: Command) -> str:
        """コマンド1件を人間可読な説明文にする。"""
        if command in (Command.STRUGGLE, Command.FORCED):
            return "わるあがき" if command == Command.STRUGGLE else "強制続行"

        if command.is_switch:
            mon = battle.get_team(self)[command.index]
            return f"交代 → {mon.name} (HP {mon.hp}/{mon.max_hp})"

        move = battle.command_to_move(self, command)
        prefix = ""
        if command.is_terastal:
            prefix = "テラスタル+"
        elif command.is_megaevol:
            prefix = "メガシンカ+"
        elif command.is_gigamax:
            prefix = "ダイマックス+"
        elif command.is_zmove:
            prefix = "Z+"
        power = move.base_power if move.base_power is not None else "-"
        return (f"{prefix}{move.name} (タイプ:{move.type} 分類:{move.category} "
                f"威力:{power} PP:{move.pp}/{move.data.pp})")
