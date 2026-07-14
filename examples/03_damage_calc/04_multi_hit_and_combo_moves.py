"""jpoke で学べること: 連続技の期待ヒット数、複数技を1ラウンドとして扱うコンボ技の計算。

連続技は Move.expected_hits で期待ヒット数を確認できる。2〜5回技はヒット数の
分布が35:35:15:15なので、期待値は単純平均(3.5)ではなく3.1になる。calc_lethal() の
moves にはリストも渡せ、複数技を渡すとその順番通りに1ラウンドとして使用する
（例: ["でんこうせっか", "かみなり"] は1発目にでんこうせっか、2発目にかみなりを撃つ）。
max_attack>1にすると、このラウンド自体を繰り返す。
"""
from __future__ import annotations

from jpoke import Battle, Move, Player


def main() -> None:
    multi_hit_move = Move("タネマシンガン")
    print(
        f"{multi_hit_move.name}: {multi_hit_move.min_hits}〜{multi_hit_move.max_hits}回技、"
        f"期待ヒット数 {multi_hit_move.expected_hits:.1f}"
    )

    print("-" * 50)
    combo_player = Player("ComboAttacker")
    combo_player.add_pokemon("ピカチュウ", move_names=["でんこうせっか", "かみなり"])
    combo_defender_player = Player("ComboDefender")
    combo_defender_player.add_pokemon("カビゴン")

    combo_battle = Battle(combo_player, combo_defender_player, seed=1)
    combo_battle.start()
    combo_attacker = combo_battle.get_active(combo_player)
    combo_results = combo_battle.calc_lethal(
        attacker=combo_attacker, moves=["でんこうせっか", "かみなり"], max_attack=1,
    )
    for result in combo_results:
        print(f"{result.move.name}: ダメージ {result.min_damage}~{result.max_damage}")

    # 試してみよう: moves のリストの順番を入れ替えたり、max_attack を2以上にして
    # ラウンドを繰り返したりすると、致死率がどう変わるか比較できる


if __name__ == "__main__":
    main()
