"""対戦を進行させず、ポケモンの状態異常・HP・能力ランクを直接操作する方法を扱う。

01（生ダメージロール）・03（calc_lethal）はどちらも「今の状態から技を撃ったら
どうなるか」を計算するが、その前提となる「今の状態」自体を作り込みたいことがある。
ここでは battle.set_ailment() / modify_hp() / modify_stats() / faint() という
4つの直接操作APIを、それぞれ単体で・技を介さずに動かして効果を確認する
（04でこれらをcalc_lethal()と組み合わせたシナリオ比較に使う）。
"""
from __future__ import annotations

from jpoke import Battle, Player


def main() -> None:
    player = Player("Attacker")
    player.add_pokemon("ガブリアス", move_names=["じしん"])
    target_player = Player("Target")
    target_player.add_pokemon("カイリュー")

    battle = Battle(player, target_player, seed=1)
    battle.start()
    target = battle.get_active(target_player)

    print("battle.set_ailment(): 技を当てずに状態異常を直接付与する")
    battle.set_ailment(target, "どく")
    print(
        f"  {target.name}の状態異常: {target.status}"
        f"（has_ailment('どく') = {target.has_ailment('どく')}）"
    )

    print("-" * 50)
    print("battle.modify_hp(): HPを直接増減する（v=固定量 / r=割合、同時指定は不可）")
    hp_before = target.hp
    battle.modify_hp(target, r=-0.5, reason="サンプル用にHPを半分減らす")
    print(f"  {target.name}のHP: {hp_before} → {target.hp}（最大HP {target.max_hp}）")

    print("-" * 50)
    print("battle.modify_stats(): 能力ランクを直接変更する（複数ステータスを同時指定できる）")
    def_rank_before = target.boosts["def"]
    battle.modify_stats(target, {"def": 2, "spd": -1})
    print(
        f"  {target.name}のぼうぎょランク: {def_rank_before} → {target.boosts['def']}、"
        f"すばやさランク: {target.boosts['spd']}"
    )

    print("-" * 50)
    print("battle.faint(): modify_hp(v=-max_hp) の薄いラッパーで、対象を即座にひんしにする")
    battle.faint(target)
    print(f"  {target.name}のfainted: {target.fainted}（HP {target.hp}/{target.max_hp}）")

    # 試してみよう: modify_hp() の r を v=固定量の指定に変えたり、
    # modify_stats() で変更するステータス・ランク幅を変えたりすると、
    # 反映結果がどう変わるか比較できる


if __name__ == "__main__":
    main()
