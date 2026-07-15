"""対戦を進行させず、ポケモンの持ち物を直接操作する方法を扱う。

02（状態異常・HP・能力ランクの直接操作）と同じ「シナリオを直接作り込む」用途で、
持ち物だけは gain_item() / remove_item() / set_item() / take_item() /
consume_item() / swap_items() という6つの専用APIに分かれている。
それぞれ単体で・技を介さずに動かして、成功/失敗の条件の違いを確認する。
"""
from __future__ import annotations

from jpoke import Battle, Player


def main() -> None:
    player = Player("Attacker")
    player.add_pokemon("ガブリアス", item_name="こだわりスカーフ", move_names=["じしん"])
    target_player = Player("Target")
    target_player.add_pokemon("カイリュー")

    battle = Battle(player, target_player, seed=1)
    battle.start()
    attacker = battle.get_active(player)
    target = battle.get_active(target_player)

    print("battle.gain_item(): 持ち物を持たないポケモンに新規で持たせる")
    print(f"  変更前の{target.name}の持ち物: {target.item.name!r}")
    ok = battle.gain_item(target, "たべのこし")
    print(f"  gain_item(target, 'たべのこし') -> {ok}、持ち物: {target.item.name}")

    print("-" * 50)
    print("battle.gain_item(): 既に持ち物を持っている場合は失敗する")
    ok = battle.gain_item(target, "オボンのみ")
    print(f"  gain_item(target, 'オボンのみ') -> {ok}（持ち物は{target.item.name}のまま）")

    print("-" * 50)
    print("battle.set_item(): 現在の持ち物に関わらず任意の持ち物に直接差し替える")
    ok = battle.set_item(target, "きあいのタスキ")
    print(f"  set_item(target, 'きあいのタスキ') -> {ok}、持ち物: {target.item.name}")

    print("-" * 50)
    print("battle.remove_item(): 持ち物を取り外す")
    ok = battle.remove_item(target)
    print(f"  remove_item(target) -> {ok}、持ち物: {target.item.name!r}")
    print(f"  last_lost_item_name: {target.last_lost_item_name!r}（リサイクル等の復元対象）")

    print("-" * 50)
    print("battle.consume_item(): きのみを消費する（食べたフラグを立ててからremove_item）")
    battle.gain_item(target, "オボンのみ")
    ok = battle.consume_item(target)
    print(f"  consume_item(target) -> {ok}、持ち物: {target.item.name!r}、ate_berry: {target.ate_berry}")

    print("-" * 50)
    print("battle.take_item(): targetは「持ち物を奪われる側」。相手（foe）が持ち物なしの時のみ成功する")
    battle.remove_item(attacker)  # 奪う側(attacker)を持ち物なしにしておく
    battle.gain_item(target, "こだわりスカーフ")
    print(
        f"  奪う前: {attacker.name}={attacker.item.name!r}, "
        f"{target.name}={target.item.name!r}"
    )
    ok = battle.take_item(target)
    print(f"  take_item(target) -> {ok}（{target.name}の持ち物を{attacker.name}が奪う）")
    print(
        f"  奪った後: {attacker.name}={attacker.item.name!r}, "
        f"{target.name}={target.item.name!r}"
    )

    print("-" * 50)
    print("battle.swap_items(): take_item()と異なり、双方が持ち物を持っていても入れ替えられる")
    battle.gain_item(target, "たべのこし")
    ok = battle.swap_items()
    print(f"  swap_items() -> {ok}")
    print(
        f"  入れ替え後: {attacker.name}={attacker.item.name!r}, "
        f"{target.name}={target.item.name!r}"
    )

    # 試してみよう: gain_item()を持ち物ありのポケモンに使って失敗を確認したり、
    # take_item()を双方が持ち物を持っている状態で呼んで失敗することを確認できる
    # （take_item()は「奪う側(相手)が持ち物なし」が前提。持ち物を交換したいだけならswap_items()を使う）


if __name__ == "__main__":
    main()
