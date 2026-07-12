"""jpoke で学べること: battle.calc_lethal() を使った確定数・乱数ダメージの計算。

対戦を進行させずに「この技を何回当てれば倒せるか」「乱数でダメージ幅はどのくらいか」
を計算する。ダメージ計算ツール開発ユースケースの入口。
"""
from __future__ import annotations

from jpoke import Battle, Move, Player


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

    # Pokemon.show()（render_info() の文字列をそのまま表示するだけの薄いラッパー）で、
    # HP・性格・特性・持ち物・テラスタイプ・努力値・技構成をまとめて確認できる。
    # 上のset_evs()でこうげき努力値を振った結果を実数値込みで見たいときに便利
    attacker.show()

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
    # 付与できたかは mon.status（poke-env互換のailment.nameのエイリアス）や
    # has_ailment() で読み取れる
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
    # 技そのもののダメージは変わらないが、攻撃の合間に入る毎ターンのどくダメージが
    # 加算される分だけ致死率が底上げされ、結果としてより少ない発数で確定しやすくなる

    # calc_lethal は確定数・致死率に集約した結果を返すが、その内部で使われている
    # 生のダメージロール（通常16通り）そのものを見たい場合は calc_damages() /
    # 乱数で1つ選んだ値だけでよければ roll_damage() を直接呼べる
    print("-" * 50)
    raw_damages = battle.calc_damages(attacker, defender, move_name)
    print(f"{move_name}の生ダメージロール（{len(raw_damages)}通り）: {raw_damages}")
    print(f"roll_damage()で乱数を1つ引いた結果: {battle.roll_damage(attacker, defender, move_name)}")

    # Battle(..., damage_roll='最大', critical_mode='確定のみ') を指定すると、
    # ダメージ計算そのものを「常に最大乱数・急所レートは基礎値のみ」に固定できる。
    # calc_lethal と並ぶ、最大保証ダメージを一発で知りたいときの代替手段
    fixed_attacker_player = Player("FixedRollAttacker")
    fixed_attacker_player.add_pokemon("ガブリアス", move_names=[move_name])
    fixed_defender_player = Player("FixedRollDefender")
    fixed_defender_player.add_pokemon("カイリュー", item_name="オボンのみ")

    fixed_battle = Battle(
        fixed_attacker_player, fixed_defender_player, seed=1,
        damage_roll="最大", critical_mode="確定のみ",
    )
    fixed_battle.start()
    fixed_attacker = fixed_battle.get_active(fixed_attacker_player)
    fixed_defender = fixed_battle.get_active(fixed_defender_player)
    # 元のattackerと条件を揃えるため、同じこうげき努力値を振っておく
    fixed_attacker.set_evs([0, 32, 0, 0, 0, 0])
    print(
        f"damage_roll='最大'指定時のダメージ: "
        f"{fixed_battle.roll_damage(fixed_attacker, fixed_defender, move_name)}"
        f"（通常ロールの最大値 {max(raw_damages)} と一致）"
    )

    # 連続技は Move.expected_hits で期待ヒット数を確認できる。2〜5回技は
    # ヒット数の分布が35:35:15:15なので、期待値は単純平均(3.5)ではなく3.1になる
    print("-" * 50)
    multi_hit_move = Move("タネマシンガン")
    print(
        f"{multi_hit_move.name}: {multi_hit_move.min_hits}〜{multi_hit_move.max_hits}回技、"
        f"期待ヒット数 {multi_hit_move.expected_hits:.1f}"
    )

    # 試してみよう: move_name を別の技に変えたり、defender_player のアイテムを
    # 変えたりすると、確定数や致死率がどう変わるか比較できる


if __name__ == "__main__":
    main()
