"""jpoke で学べること: 天候・地形の効果、技を実際に当てて状態異常を発生させる方法、
揮発性状態（やどりぎのタネ等）を直接付与する方法、battle.step() を伴う進行での
アイテム・特性の発動ログ確認、追加効果の発動確率を固定して決定論的にする方法。

01（calc_lethal）は防御側の状態異常・天候ダメージも計算に含められるが、
天候・地形そのものの効果や、対戦を実際に進めたときのアイテム・特性の発動ログ
（calc_lethal()は対戦を進行させないため出ない）は別軸の話であり、ここでは
battle.step()を伴う最小構成の対戦で確認する。
"""
from __future__ import annotations

from jpoke import Battle, Player


def show_weather_effect() -> None:
    """すなあらし: 岩・はがね・じめんタイプ以外は毎ターン終了時にダメージを受ける。"""
    attacker_player = Player("Attacker")
    attacker_player.add_pokemon("ピカチュウ", move_names=["なきごえ"])
    defender_player = Player("Defender")
    defender_player.add_pokemon("フシギダネ", move_names=["たいあたり"])

    battle = Battle(attacker_player, defender_player, seed=1)
    battle.start()
    # set_weather() は技を介さず天候を直接発動する（あめふらし等の特性を経由しない検証用API）
    battle.set_weather("すなあらし")
    defender = battle.get_active(defender_player)
    hp_before = defender.hp
    battle.step()
    print(f"すなあらし発動中のターン終了時、{defender.name}のHP: {hp_before} → {defender.hp}")


def show_terrain_effect() -> None:
    """エレキフィールド: 地面にいるポケモンのでんきタイプの技の威力が1.3倍になる。"""
    move_name = "かみなり"
    attacker_player = Player("Attacker")
    attacker_player.add_pokemon("ピカチュウ", move_names=[move_name])
    defender_player = Player("Defender")
    defender_player.add_pokemon("カビゴン")

    battle = Battle(attacker_player, defender_player, seed=1)
    battle.start()
    attacker = battle.get_active(attacker_player)
    defender = battle.get_active(defender_player)

    before = battle.calc_damages(attacker, defender, move_name)
    battle.set_terrain("エレキフィールド")
    after = battle.calc_damages(attacker, defender, move_name)
    print(f"{move_name}のダメージ: エレキフィールド無し {before} → あり {after}")


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


def show_ability_and_item_logs() -> None:
    """calc_lethal()は対戦を進行させないため発動ログが出ない。battle.step()を伴う
    対戦であれば、特性・アイテムの発動ログがprint_logs()にそのまま表示される。
    """
    print("-" * 50)
    print("特性の発動ログ: もらいび（ほのお技を無効化し、とくこうを上げる）")
    ability_attacker = Player("Attacker")
    ability_attacker.add_pokemon("ヒトカゲ", move_names=["かえんほうしゃ"], nature="ようき")
    ability_defender = Player("Defender")
    ability_defender.add_pokemon("ライチュウ", ability_name="もらいび", nature="ずぶとい")

    ability_battle = Battle(ability_attacker, ability_defender, seed=1, accuracy_fix_threshold=0)
    ability_battle.start()
    ability_battle.step()
    ability_battle.print_logs()

    print("-" * 50)
    print("アイテムの発動ログ: きあいのタスキ（瀕死になるはずの一撃を耐えHP1で残る）")
    item_attacker = Player("Attacker")
    item_attacker.add_pokemon("ガブリアス", move_names=["じしん"], nature="ようき")
    item_defender = Player("Defender")
    item_defender.add_pokemon("ピチュー", item_name="きあいのタスキ")

    # damage_roll="max", critical_mode="always" で確実にOHKO相当の一撃にし、
    # きあいのタスキの発動条件（瀕死になるはずの一撃）を安定して再現する
    item_battle = Battle(
        item_attacker, item_defender, seed=1,
        accuracy_fix_threshold=0, damage_roll="max", critical_mode="always",
    )
    item_battle.start()
    item_battle.step()
    item_battle.print_logs()


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
    show_weather_effect()
    print("-" * 50)
    show_terrain_effect()
    print("-" * 50)
    show_ailment_via_actual_move()
    print("-" * 50)
    show_volatile_via_set_volatile()
    show_ability_and_item_logs()
    print("-" * 50)
    show_effect_chance_threshold()

    # 試してみよう: すなあらしを別の天候（あめ・にほんばれ・ゆき）に、
    # エレキフィールドを別の地形に変えると、対象タイプ・威力補正がどう変わるか比較できる


if __name__ == "__main__":
    main()
