# TODO: 致死率計算の前に、まずは生のダメージロールを確認する例を01で提示する。
"""生のダメージロールを直接確認する方法と、決定論的な固定ロールで計算する方法を扱う。

calc_lethal() は複数発の致死率をまとめて計算するAPIだが、1発のダメージロール
（通常16通り）そのものを見たい場合は calc_damages()、乱数で1つ選んだ値だけで
よければ roll_damage() を直接呼べる。damage_roll='max' / critical_mode='always' を
Battle に指定すると、そのバトル全体のダメージ計算を「常に最大乱数・急所は基礎値のみ」
に固定できる（最大保証ダメージを一発で知りたいときの代替手段）。
"""
from __future__ import annotations

from jpoke import Battle, Player


def main() -> None:
    move_name = "ドラゴンテール"

    attacker_player = Player("Attacker")
    attacker_player.add_pokemon("ガブリアス", move_names=[move_name])
    defender_player = Player("Defender")
    defender_player.add_pokemon("カイリュー", item_name="オボンのみ")

    battle = Battle(attacker_player, defender_player, seed=1)
    battle.start()
    attacker = battle.get_active(attacker_player)
    defender = battle.get_active(defender_player)
    attacker.set_evs([0, 32, 0, 0, 0, 0])

    raw_damages = battle.calc_damages(attacker, defender, move_name)
    print(f"{move_name}の生ダメージロール（{len(raw_damages)}通り）: {raw_damages}")
    print(f"roll_damage()で乱数を1つ引いた結果: {battle.roll_damage(attacker, defender, move_name)}")

    print("-" * 50)
    fixed_attacker_player = Player("FixedRollAttacker")
    fixed_attacker_player.add_pokemon("ガブリアス", move_names=[move_name])
    fixed_defender_player = Player("FixedRollDefender")
    fixed_defender_player.add_pokemon("カイリュー", item_name="オボンのみ")

    fixed_battle = Battle(
        fixed_attacker_player, fixed_defender_player, seed=1,
        damage_roll="max", critical_mode="always",
    )
    fixed_battle.start()
    fixed_attacker = fixed_battle.get_active(fixed_attacker_player)
    fixed_defender = fixed_battle.get_active(fixed_defender_player)
    # 元のattackerと条件を揃えるため、同じこうげき努力値を振っておく
    fixed_attacker.set_evs([0, 32, 0, 0, 0, 0])
    print(
        f"damage_roll='max'指定時のダメージ: "
        f"{fixed_battle.roll_damage(fixed_attacker, fixed_defender, move_name)}"
        f"（通常ロールの最大値 {max(raw_damages)} と一致）"
    )

    # 試してみよう: damage_roll='min' に変えると最小保証ダメージが分かる


if __name__ == "__main__":
    main()
