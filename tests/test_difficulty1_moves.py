"""難易度1の技（単純な能力ランク変化）のテスト"""
from jpoke import Pokemon
import test_utils as t


def test():
    print("--- ニトロチャージ：自分のS+1 ---")
    battle = t.start_battle(
        ally=[Pokemon("リザードン", moves=["ニトロチャージ"])],
        turn=1
    )
    assert battle.actives[0].rank["S"] == 1

    print("--- がんせきふうじ：相手のS-1 ---")
    battle = t.start_battle(
        ally=[Pokemon("イワーク", moves=["がんせきふうじ"])],
        foe=[Pokemon("ピジョン")],
        turn=1
    )
    assert battle.actives[1].rank["S"] == -1

    print("--- じならし：相手のS-1 ---")
    battle = t.start_battle(
        ally=[Pokemon("サンドパン", moves=["じならし"])],
        foe=[Pokemon("ゲンガー")],
        turn=1
    )
    assert battle.actives[1].rank["S"] == -1

    print("--- ドラムアタック：相手のS-1 ---")
    battle = t.start_battle(
        ally=[Pokemon("フシギバナ", moves=["ドラムアタック"])],
        foe=[Pokemon("ピカチュウ")],
        turn=1
    )
    assert battle.actives[1].rank["S"] == -1

    print("--- ソウルクラッシュ：相手のC-1 ---")
    battle = t.start_battle(
        ally=[Pokemon("プリン", moves=["ソウルクラッシュ"])],
        foe=[Pokemon("フーディン")],
        turn=1
    )
    assert battle.actives[1].rank["C"] == -1

    print("--- トロピカルキック：相手のA-1 ---")
    battle = t.start_battle(
        ally=[Pokemon("モンジャラ", moves=["トロピカルキック"])],
        foe=[Pokemon("カイリキー")],
        turn=1
    )
    assert battle.actives[1].rank["A"] == -1

    print("--- オーバーヒート：自分のC-2 ---")
    battle = t.start_battle(
        ally=[Pokemon("キュウコン", moves=["オーバーヒート"])],
        foe=[Pokemon("ニドキング")],
        turn=1
    )
    assert battle.actives[0].rank["C"] == -2

    print("--- インファイト：自分のBD-1 ---")
    battle = t.start_battle(
        ally=[Pokemon("サワムラー", moves=["インファイト"])],
        foe=[Pokemon("ゴローニャ")],
        turn=1
    )
    assert battle.actives[0].rank["B"] == -1
    assert battle.actives[0].rank["D"] == -1

    print("--- かたくなる：自分のB+1 ---")
    battle = t.start_battle(
        ally=[Pokemon("パルシェン", moves=["かたくなる"])],
        turn=1
    )
    assert battle.actives[0].rank["B"] == 1

    print("--- こうそくいどう：自分のS+2 ---")
    battle = t.start_battle(
        ally=[Pokemon("ペルシアン", moves=["こうそくいどう"])],
        turn=1
    )
    assert battle.actives[0].rank["S"] == 2

    print("--- なきごえ：相手のA-1 ---")
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["なきごえ"])],
        foe=[Pokemon("カイリキー")],
        turn=1
    )
    assert battle.actives[1].rank["A"] == -1

    print("--- こわいかお：相手のS-2 ---")
    battle = t.start_battle(
        ally=[Pokemon("ギャラドス", moves=["こわいかお"])],
        foe=[Pokemon("ゲンガー")],
        turn=1
    )
    assert battle.actives[1].rank["S"] == -2

    print("--- ばかぢから：自分のAB-1 ---")
    battle = t.start_battle(
        ally=[Pokemon("カイリキー", moves=["ばかぢから"])],
        foe=[Pokemon("ゴローニャ")],
        turn=1
    )
    assert battle.actives[0].rank["A"] == -1
    assert battle.actives[0].rank["B"] == -1

    print("\n✅ すべてのテストが成功しました！")


if __name__ == "__main__":
    test()
