"""jpoke で学べること: 技を実際に当てて状態異常を発生させる方法、揮発性状態を
直接付与する方法、追加効果の発動確率を固定して決定論的にする方法。
"""
from __future__ import annotations

from jpoke import Battle, Player


def show_ailment_via_actual_move() -> None:
    """状態異常はset_ailment()以外に、実際に技を当てて発生させることもできる。"""
    attacker_player = Player("Attacker")
    attacker_player.add_pokemon("ドクロッグ", move_names=["どくどく"])
    defender_player = Player("Defender")
    defender_player.add_pokemon("カビゴン")

    # accuracy_fix_threshold=0 で命中率を100%に固定し、命中判定の非決定性を排除する
    battle = Battle(attacker_player, defender_player, seed=1, accuracy_fix_threshold=0)
    battle.start()
    defender = battle.get_active(defender_player)
    battle.step()
    print(
        f"どくどく使用後の{defender.name}の状態異常: {defender.status}"
        f"（has_ailment('もうどく') = {defender.has_ailment('もうどく')}）"
    )
    battle.print_logs()


def show_volatile_via_set_volatile() -> None:
    """揮発性状態はset_ailment()と同様、set_volatile()で直接付与できる。

    やどりぎのタネ: ターン終了時に対象のHPを最大HPの1/8吸い取り、相手を回復させる。
    """
    attacker_player = Player("Attacker")
    attacker_player.add_pokemon("ピカチュウ", move_names=["なきごえ"])
    defender_player = Player("Defender")
    defender_player.add_pokemon("フシギダネ", move_names=["たいあたり"])

    battle = Battle(attacker_player, defender_player, seed=1)
    battle.start()
    defender = battle.get_active(defender_player)
    battle.set_volatile(defender, "やどりぎのタネ")
    print(f"揮発性状態の付与: has_volatile('やどりぎのタネ') = {defender.has_volatile('やどりぎのタネ')}")
    battle.step()
    battle.print_logs()


def show_effect_chance_threshold() -> None:
    """effect_chance_threshold: 指定値未満の追加効果発動確率を強制的に0%にする。

    accuracy_fix_threshold（命中率の固定）と組み合わせると、確率で発動する要素を
    すべて排除した完全に決定論的なシナリオを作れる（シナリオ検証・回帰テスト向け）。
    かえんほうしゃのやけど付与（10%）で確認する。
    """
    move_name = "かえんほうしゃ"

    def burned_after_one_hit(effect_chance_threshold: float | None, seed: int) -> bool:
        attacker_player = Player("Attacker")
        attacker_player.add_pokemon("ヒトカゲ", move_names=[move_name])
        defender_player = Player("Defender")
        defender_player.add_pokemon("フシギダネ")
        battle = Battle(
            attacker_player, defender_player, seed=seed,
            accuracy_fix_threshold=0, effect_chance_threshold=effect_chance_threshold,
        )
        battle.start()
        defender = battle.get_active(defender_player)
        battle.step()
        return defender.has_ailment("やけど")

    seeds = range(1, 21)
    # effect_chance_threshold未指定（既定）では、やけどの発動有無はseedごとに変わる（確率10%）
    n_burned_default = sum(burned_after_one_hit(None, s) for s in seeds)
    # 0.11未満の確率を0%にする指定なので、10%（0.1）のやけど付与は常に抑制される
    n_burned_suppressed = sum(burned_after_one_hit(0.11, s) for s in seeds)
    print(
        f"{move_name}のやけど付与（{len(seeds)}試行）: "
        f"既定 {n_burned_default}回発動 / effect_chance_threshold=0.11指定時 {n_burned_suppressed}回発動"
    )


def main() -> None:
    show_ailment_via_actual_move()
    print("-" * 50)
    show_volatile_via_set_volatile()
    print("-" * 50)
    show_effect_chance_threshold()

    # 試してみよう: effect_chance_threshold を 0.09 に下げると、10%のやけど付与が
    # 抑制されなくなることを確認できる


if __name__ == "__main__":
    main()
