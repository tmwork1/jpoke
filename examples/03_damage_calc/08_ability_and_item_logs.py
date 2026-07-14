"""battle.step() を伴う進行で、特性・アイテムの発動ログを確認する。

calc_lethal()は対戦を進行させないため発動ログが出ない。battle.step()を伴う
対戦であれば、特性・アイテムの発動ログがprint_logs()にそのまま表示される。
"""
from __future__ import annotations

from jpoke import Battle, Player


def show_ability_log() -> None:
    print("特性の発動ログ: もらいび（ほのお技を無効化し、とくこうを上げる）")
    ability_attacker = Player("Attacker")
    ability_attacker.add_pokemon("ヒトカゲ", move_names=["かえんほうしゃ"], nature="ようき")
    ability_defender = Player("Defender")
    ability_defender.add_pokemon("ライチュウ", ability_name="もらいび", nature="ずぶとい")

    ability_battle = Battle(ability_attacker, ability_defender, seed=1, accuracy_fix_threshold=0)
    ability_battle.start()
    ability_battle.step()
    ability_battle.print_logs()


def show_item_log() -> None:
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


def main() -> None:
    show_ability_log()
    print("-" * 50)
    show_item_log()

    # 試してみよう: もらいびを別の技無効化特性（例: "ちょすい"）に変えると、
    # 発動ログの表示内容がどう変わるか比較できる


if __name__ == "__main__":
    main()
