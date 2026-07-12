"""jpoke で学べること: battle.calc_lethal() を使った確定数・乱数ダメージの計算。

対戦を進行させずに「この技を何回当てれば倒せるか」「乱数でダメージ幅はどのくらいか」
を計算する。ダメージ計算ツール開発ユースケースの入口。
"""
from __future__ import annotations

from jpoke import Battle, Player


def main() -> None:
    move_name = "ドラゴンテール"

    attacker_player = Player("Attacker")
    attacker_player.add_pokemon("ガブリアス", move_names=[move_name])

    defender_player = Player("Defender")
    defender_player.add_pokemon("カイリュー", item_name="オボンのみ")

    # calc_lethal は対戦を進行させないため、バトルは1体選出で start() しただけでよい
    battle = Battle(attacker_player, defender_player, seed=1)
    battle.start()

    attacker = battle.get_active(attacker_player)
    defender = battle.get_active(defender_player)

    # こうげき努力値をChampions形式（0〜32、poke-envの0〜252スケールとは異なる）で
    # 最大まで振る。実数値のこうげきが上がるため、下記の確定数・致死率も
    # 無振りの場合より高く（＝倒しやすく）なる
    attacker.set_evs([0, 32, 0, 0, 0, 0])

    # moves には技名の文字列 / Move 単体 / (Move, ヒット数) / それらのリストを渡せる
    results = battle.calc_lethal(
        attacker=attacker,
        moves=move_name,
        max_attack=5,  # 最大5回攻撃するまで計算する（確定数が出た時点で打ち切り）
    )

    print(f"攻撃側: {attacker.name}（{move_name}, こうげき実数値 {attacker.stats['atk']}）")
    print(f"防御側: {defender.name}（HP {defender.max_hp}, オボンのみ）")
    print("-" * 50)

    # TODO: 致死判定はresults[-1]に格納されている。resultsの各要素はヒットごとのHP分布が格納されている。ということがわかるようにする。
    for result in results:
        print(
            f"{result.n_attack}発目: ダメージ {result.min_damage}~{result.max_damage} "
            f"/ 致死率 {result.lethal_probability:.2%}"
        )

    final = results[-1]
    print("-" * 50)
    print(f"{final.n_attack}回攻撃した時点での致死率: {final.lethal_probability:.2%}")

    # calc_lethal は防御側に状態異常・天候が設定されていれば、技のダメージに加えて
    # 毎ターンの状態異常・天候ダメージも自動的に合算して致死率を計算する
    # （どく/もうどく/やけど・すなあらし等のダメージが1攻撃ごとに積み重なる）。
    # 上の攻撃側（努力値振り済み）とは条件を揃えるため、努力値無振りの
    # 別ペアで「どく無し」と「どくあり」を同じ発数で比較する
    print("-" * 50)
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

    # set_ailment() で防御側を直接どく状態にする（技を当てずにシナリオを組み立てられる）
    plain_battle.set_ailment(plain_defender, "どく")
    poisoned_final = plain_battle.calc_lethal(
        attacker=plain_attacker, moves=move_name, max_attack=2,
    )[-1]

    print(
        f"{move_name}を{no_ailment_final.n_attack}発当てた時点の致死率: "
        f"どく無し {no_ailment_final.lethal_probability:.2%} / "
        f"どくあり {poisoned_final.lethal_probability:.2%}"
    )
    # 技そのもののダメージは変わらないが、攻撃の合間に入る毎ターンのどくダメージが
    # 加算される分だけ致死率が底上げされ、結果としてより少ない発数で確定しやすくなる

    # 試してみよう: move_name を別の技に変えたり、defender_player のアイテムを
    # 変えたりすると、確定数や致死率がどう変わるか比較できる


if __name__ == "__main__":
    main()
