"""天候・地形の効果を確認する。

01（calc_lethal）は防御側の状態異常・天候ダメージも計算に含められるが、
天候・地形そのものの効果は別軸の話であり、ここでは battle.step() を伴う
最小構成の対戦で確認する。
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


def main() -> None:
    show_weather_effect()
    print("-" * 50)
    show_terrain_effect()

    # 試してみよう: すなあらしを別の天候（あめ・にほんばれ・ゆき）に、
    # エレキフィールドを別の地形に変えると、対象タイプ・威力補正がどう変わるか比較できる


if __name__ == "__main__":
    main()
