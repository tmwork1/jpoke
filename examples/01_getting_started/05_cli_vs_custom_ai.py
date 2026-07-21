"""CLIPlayer と自作AIを対戦させるスクリプト。

`python examples/01_getting_started/05_cli_vs_custom_ai.py` で実行し、標準入力から
コマンドを入力しながら自作AI（`CustomAI`）相手に対戦できる。標準入力を使う対話型の
サンプルのため、他の01_getting_started配下と異なりColab非対応（.ipynbではなく.py）。

`CustomAI` は 03_custom_player.ipynb と同じ実装（ダメージが最大になる技を選ぶだけの
方策）。`Player` を継承して choose_command()/choose_selection() を書き換えるだけで
自作AIを組み込める。
"""
from __future__ import annotations

from jpoke import Battle, Player
from jpoke.enums import Command
from jpoke.players import CLIPlayer


class CustomAI(Player):
    """自作AIのサンプル: 相手に与えるダメージが最大になる技を選ぶだけの方策。"""

    def choose_selection(self, battle: Battle) -> list[int]:
        """素早さの高い順に選出する。"""
        indexes = list(range(len(self.team)))
        speeds = [self.team[i].stats["spe"] for i in indexes]
        order = sorted(indexes, key=lambda i: speeds[i], reverse=True)
        return order[:battle.n_selected]

    def choose_command(self, battle: Battle) -> Command:
        """ダメージが最大になる技を選ぶ。"""
        commands = battle.available_commands(self)
        return max(commands, key=lambda command: self._damage(battle, command))

    def _damage(self, battle: Battle, command: Command) -> int:
        if not command.is_move:
            return -1

        move = battle.command_to_move(self, command)
        opponent = battle.opponent(self)
        damages = battle.calc_damages(
            attacker=battle.get_active(self),
            defender=battle.get_active(opponent),
            move=move,
            critical=move.guaranteed_crit,  # 確定急所を考慮する
        )
        return damages[0]  # 0: 最低ダメージ


def build_teams() -> tuple[CLIPlayer, CustomAI]:
    """デモ用の3vs3チームを構築する。"""
    human = CLIPlayer("あなた")
    human.add_pokemon("ピカチュウ", moves=["でんこうせっか", "かみなり", "でんじは"])
    human.add_pokemon("フシギダネ", moves=["たいあたり", "やどりぎのタネ"])
    human.add_pokemon("ゼニガメ", moves=["みずでっぽう", "からにこもる"])

    ai = CustomAI("自作AI")
    ai.add_pokemon("ヒトカゲ", moves=["ひのこ", "ひっかく"])
    ai.add_pokemon("コラッタ", moves=["たいあたり", "でんこうせっか"])
    ai.add_pokemon("ポッポ", moves=["つつく", "かぜおこし"])

    return human, ai


def main() -> None:
    human, ai = build_teams()
    battle = Battle(human, ai, n_selected=2, seed=1)
    battle.play_out(max_turns=100)

    print("=" * 50)
    if battle.winner is None:
        print("結果: 引き分け（ターン上限）")
    else:
        print(f"結果: {battle.winner.username} の勝利！")
    print("=" * 50)
    battle.print_logs("all")


if __name__ == "__main__":
    main()
