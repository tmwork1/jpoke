# TODO: Pokemon.hpへの直接代入を禁じているのは対戦シミュレーションの整合性を保つためであり、ダメージ計算のみを行う場合は、むしろ不必要にハンドラを起動しないためにも直接代入すべき。
# TODO: まずポケモンの状態を直接操作するだけのサンプルコードを作成し、02として見せるべき。すべての操作をわかりやすく列挙してほしい。

"""jpoke で学べること: 状態異常・HP・能力ランクを直接操作したシナリオでの致死率比較。

01（calc_lethal 基本）を踏まえ、battle.set_ailment() / modify_hp() / modify_stats() /
faint() で「対戦を進行させずに特定の状態から始まるシナリオ」を組み立て、
calc_lethal() の結果がどう変わるかを比較する。
"""
from __future__ import annotations

from jpoke import Battle, Player


def main() -> None:
    move_name = "ドラゴンテール"

    # calc_lethal は防御側の状態異常・天候ダメージ（どく・やけど・すなあらし等）も
    # 技のダメージに自動的に合算する。努力値無振りのペアで比較する
    print("努力値無振りの攻撃側で、どく無し/どくありを比較:")

    plain_attacker_player = Player("PlainAttacker")
    plain_attacker_player.add_pokemon("ガブリアス", move_names=[move_name])
    plain_defender_player = Player("PlainDefender")
    plain_defender_player.add_pokemon("カイリュー", item_name="オボンのみ")

    plain_battle = Battle(plain_attacker_player, plain_defender_player, seed=1)
    plain_battle.start()
    plain_attacker = plain_battle.get_active(plain_attacker_player)
    plain_defender = plain_battle.get_active(plain_defender_player)

    no_ailment_final = plain_battle.calc_lethal(
        attacker=plain_attacker, moves=move_name, max_attack=2,
    )[-1]

    # set_ailment() で防御側を直接どく状態にする（技を当てずにシナリオを組み立てられる）。
    # 付与できたかは mon.status（poke-env互換のailment.nameエイリアス）や has_ailment() で読み取れる
    plain_battle.set_ailment(plain_defender, "どく")
    print(
        f"防御側の状態異常: {plain_defender.status}"
        f"（has_ailment('どく') = {plain_defender.has_ailment('どく')}）"
    )
    poisoned_final = plain_battle.calc_lethal(
        attacker=plain_attacker, moves=move_name, max_attack=2,
    )[-1]

    print(
        f"{move_name}を{no_ailment_final.n_attack}発当てた時点の致死率: "
        f"どく無し {no_ailment_final.lethal_probability:.2%} / "
        f"どくあり {poisoned_final.lethal_probability:.2%}"
    )

    # modify_hp()/modify_stats() で「特定のHP・ランク状態から始まる」シナリオも
    # 直接組み立てられる（Pokemon.hp への直接代入は禁止されており、必ずこれらを通す）
    print("-" * 50)
    print("防御側のHP・ランク状態を変えて比較:")

    scenario_attacker_player = Player("ScenarioAttacker")
    scenario_attacker_player.add_pokemon("ガブリアス", move_names=[move_name])
    scenario_defender_player = Player("ScenarioDefender")
    scenario_defender_player.add_pokemon("カイリュー")

    scenario_battle = Battle(scenario_attacker_player, scenario_defender_player, seed=1)
    scenario_battle.start()
    scenario_attacker = scenario_battle.get_active(scenario_attacker_player)
    scenario_defender = scenario_battle.get_active(scenario_defender_player)

    # max_attack=1 に絞り、HP・ランク状態を変えた結果が1発の致死率にそのまま反映されるようにする
    full_hp_final = scenario_battle.calc_lethal(
        attacker=scenario_attacker, moves=move_name, max_attack=1,
    )[-1]

    # modify_hp(r=-0.6) で最大HPの60%分のダメージを与え、残りHP40%の状態を直接作る
    # （v で固定量、r で割合指定。同時指定は不可）
    scenario_battle.modify_hp(scenario_defender, r=-0.6, reason="シナリオ構築用")
    damaged_final = scenario_battle.calc_lethal(
        attacker=scenario_attacker, moves=move_name, max_attack=1,
    )[-1]
    print(
        f"{move_name}を1発当てた時点の致死率: "
        f"HP満タン {full_hp_final.lethal_probability:.2%} / "
        f"HP{scenario_defender.hp}/{scenario_defender.max_hp} "
        f"{damaged_final.lethal_probability:.2%}"
    )

    # modify_stats() は複数の能力ランクを同時に変更できる
    scenario_battle.modify_stats(scenario_defender, {"def": 1})
    raised_def_final = scenario_battle.calc_lethal(
        attacker=scenario_attacker, moves=move_name, max_attack=1,
    )[-1]
    print(f"上記の状態からさらにぼうぎょ+1した後の致死率: {raised_def_final.lethal_probability:.2%}")

    # faint() は modify_hp(v=-target.max_hp) の薄いラッパーで、対象を即座にひんしにする
    scenario_battle.faint(scenario_defender)
    print(f"faint()呼び出し後: fainted={scenario_defender.fainted}")

    # 試してみよう: modify_hp(r=-0.6) の割合や set_ailment() の状態異常を変えると、
    # 致死率がどう変わるか比較できる


if __name__ == "__main__":
    main()
