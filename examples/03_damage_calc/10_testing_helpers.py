"""jpoke.testing のヘルパーを使い、これまでのサンプルで繰り返し書いてきた
Battle(...).start() + Player.add_pokemon() の定型処理を1呼び出しにまとめる方法を示す。

jpoke.testing は tests/test_utils.py にあった内部テスト専用ヘルパーが本体パッケージへ
昇格したもので、`pip install jpoke` だけで（リポジトリを clone せずに）使える。
状態異常・天候・命中率固定などをキーワード引数で指定して一発でバトルを組み立てられるため、
「状態を変えて比較する」シナリオ検証コードが短く書ける。
"""
from __future__ import annotations

from jpoke import Pokemon
from jpoke.testing import apply_ailment, calc_lethal, run_move, start_battle


def main() -> None:
    move_name = "ドラゴンテール"

    # start_battle() は Player の生成・add_pokemon()・Battle(...).start() をまとめて行う。
    # accuracy=100 で命中率を固定し、乱数による命中判定のばらつきを排除する
    battle = start_battle(
        team0=[Pokemon("ガブリアス", move_names=[move_name])],
        team1=[Pokemon("カイリュー", item_name="オボンのみ")],
        accuracy=100,
    )
    # start_battle() は Player インスタンスを返さないため、battle.players から取得する
    player0, player1 = battle.players
    defender = battle.get_active(player1)

    # calc_lethal() は player_idx（アクティブのインデックス）を渡すだけで済む
    # battle.calc_lethal() のショートカット
    plain_final = calc_lethal(battle, player_idx=0, moves=move_name, max_attack=2)[-1]

    # apply_ailment() は player_idx 指定で set_ailment() 相当のことができる
    apply_ailment(battle, player_idx=1, ailment_name="どく")
    print(f"防御側の状態異常: {defender.status}")

    poisoned_final = calc_lethal(battle, player_idx=0, moves=move_name, max_attack=2)[-1]
    print(
        f"{move_name}を{plain_final.n_attack}発当てた時点の致死率: "
        f"どく無し {plain_final.lethal_probability:.2%} / "
        f"どくあり {poisoned_final.lethal_probability:.2%}"
    )

    # run_move() は「player_idx番目のアクティブがmove_idx番目の技を使う」を1行にまとめ、
    # 使用後のログもまとめて出力する（battle.run_move() + battle.print_logs() のショートカット）
    print("-" * 50)
    hp_before = defender.hp
    run_move(battle, player_idx=0, move_idx=0)
    print(f"{move_name}を実際に撃ち込んだ後、{defender.name}のHP: {hp_before} → {defender.hp}")

    # 試してみよう: apply_ailment() の ailment_name を別の状態異常に変えたり、
    # start_battle() の weather / terrain / side0 / side1 引数で場の状態を
    # 追加してから calc_lethal() を呼ぶと、致死率がどう変わるか比較できる


if __name__ == "__main__":
    main()
