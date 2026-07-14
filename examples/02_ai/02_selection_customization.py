"""choose_selection() をオーバーライドして選出順をカスタマイズする方法を示す。

choose_command とは別に choose_selection(battle) をオーバーライドすると、
対戦開始前の選出番号（n_selected件）を自分で決められる。デフォルト実装は
「先頭からn_selected件」という単純な選出のため、手持ちの並び順と選出結果が
直結してしまう。
"""
from __future__ import annotations

from jpoke import Battle, Player


class FastestLeadPlayer(Player):
    """素早さ実数値が高い順に選出する（先発が速いほうが有利、という単純な発想）。"""

    def choose_selection(self, battle: Battle) -> list[int]:
        order = sorted(range(len(self.team)), key=lambda i: self.team[i].stats["spe"], reverse=True)
        return order[:battle.n_selected]


def main() -> None:
    lead_player = FastestLeadPlayer("FastestLeadPlayer")
    lead_player.add_pokemon("カビゴン", move_names=["たいあたり"])
    lead_player.add_pokemon("ピカチュウ", move_names=["でんこうせっか"])
    lead_player.add_pokemon("ヤドン", move_names=["みずでっぽう"])
    lead_player.add_pokemon("ペルシアン", move_names=["ひっかく"])
    print("手持ちの素早さ:", [(mon.name, mon.stats["spe"]) for mon in lead_player.team])

    opponent = Player("Opponent")
    opponent.add_pokemon("ゼニガメ", move_names=["たいあたり"])
    opponent.add_pokemon("コラッタ")  # n_selectedを両陣営2に揃えるためのダミー

    battle = Battle(lead_player, opponent, n_selected=2, seed=1)
    battle.start()
    lead = battle.get_active(lead_player)
    print(f"選出2体の先発: {lead.name}（最も素早い個体が選ばれている）")

    # 試してみよう: 手持ちの並び順を変えても、常に最も素早いポケモンが
    # 先発になることを確認できる


if __name__ == "__main__":
    main()
