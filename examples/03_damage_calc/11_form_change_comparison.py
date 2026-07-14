"""Pokemon.set_form() によるフォルム変化がダメージ計算に与える影響を確認する。

ロトムはフォルムごとにタイプ・種族値が異なる（例: ヒートロトムはでんき/ほのお、
スピンロトムはでんき/ひこう）。特定のフォルムを最初から使いたいだけなら
add_pokemon() でそのフォルムのエイリアスを直接指定すればよいが、ここでは
set_form() で対戦を進行させずにフォルムを直接切り替えられる点を活かし、
複数フォルムを1つの Battle・Pokemon インスタンスのまま順番に切り替えて
比較する（フォルムの数だけ Player・Battle を作り直さずに済む、比較・
スイープ用途に特化した使い方）。calc_lethal() と組み合わせて「同じ技でも
フォルムが変わるだけで結果がどう変わるか」を確認する。
"""
from __future__ import annotations

from jpoke import Battle, Player


def main() -> None:
    move_name = "じしん"  # じめんタイプの物理技。でんきタイプに効果抜群、ひこうタイプには無効

    attacker_player = Player("Attacker")
    attacker_player.add_pokemon("ガブリアス", move_names=[move_name])
    defender_player = Player("Defender")
    defender_player.add_pokemon("ロトム")  # でんき/ゴースト（ベースフォルム）

    battle = Battle(attacker_player, defender_player, seed=1)
    battle.start()
    attacker = battle.get_active(attacker_player)
    defender = battle.get_active(defender_player)

    # set_form(name, hp_policy="keep_absolute", set_default_ability=False) は
    # エイリアス指定でフォルムを切り替える。種族値・タイプ・特性候補が変更先のものに
    # 差し替わる（戻り値は実際に切り替わったかを示す bool）。
    # ロトムは全フォルムでH種族値が同じ(50)ため、既定の hp_policy="keep_absolute" でも
    # 現在HPは変化しない
    forms = [
        "ロトム",          # でんき/ゴースト: じめん2倍弱点
        "ヒートロトム",      # でんき/ほのお: じめん4倍弱点
        "ウォッシュロトム",   # でんき/みず: じめん2倍弱点
        "フロストロトム",     # でんき/こおり: じめん2倍弱点
        "スピンロトム",      # でんき/ひこう: じめん完全無効
        "カットロトム",      # でんき/くさ: じめん等倍
    ]

    print(f"{move_name}（じめんタイプ）を各フォルムのロトムに撃った場合の致死率:")
    for form in forms:
        defender.set_form(form)
        final = battle.calc_lethal(attacker=attacker, moves=move_name, max_attack=1)[-1]
        print(
            f"  {defender.name}（{'/'.join(defender.types)}）: "
            f"ダメージ {final.min_damage}~{final.max_damage} / 致死率 {final.lethal_probability:.2%}"
        )

    # set_form() は種族値も差し替えるため、耐久力そのものも比較すると分かりやすい
    print("-" * 50)
    print("フォルムごとのぼうぎょ実数値（種族値も切り替わっている）:")
    for form in forms:
        defender.set_form(form)
        print(f"  {defender.name}: ぼうぎょ実数値 {defender.stats['def']}")

    # 試してみよう: move_name を「なみのり」（みずタイプ）に変えると、
    # ウォッシュロトムだけ無効になるなど、また違うフォルム差が見られる


if __name__ == "__main__":
    main()
