"""変化技ハンドラの単体テスト（ま行）。"""

import pytest

from jpoke import Pokemon
from jpoke.data.move import MOVES
from .. import test_utils as t


@pytest.mark.parametrize("initial_count,expected_count", [
    (0, 1),  # 未設置 → 1層目
    (1, 2),  # 1層 → 2層
    (2, 3),  # 2層 → 3層（最大）
    (3, 3),  # 最大層では変化なし（失敗）
])
def test_まきびし_カウント累積(initial_count: int, expected_count: int):
    """まきびし: count=0~3の各状態から使用したときのカウント変化を検証する"""
    if initial_count == 0:
        battle = t.start_battle(
            team0=[Pokemon("ピカチュウ", move_names=["まきびし"])],
            team1=[Pokemon("カビゴン")],
        )
    else:
        battle = t.start_battle(
            team0=[Pokemon("ピカチュウ", move_names=["まきびし"])],
            team1=[Pokemon("カビゴン")],
            side1={"まきびし": initial_count},
        )
    side = battle.get_side(battle.actives[1])
    t.run_move(battle, 0)
    assert side.fields["まきびし"].count == expected_count


def test_まきびし_相手陣営に設置される():
    """まきびし: 使用すると相手陣営にまきびしが設置される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まきびし"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)

    side = battle.get_side(battle.actives[1])
    assert side.fields["まきびし"].is_active


def test_マジックルーム_PPは12():
    """マジックルーム: チャンピオンズでのPPは12（docs/champions/move_list.txt準拠）。"""
    assert MOVES["マジックルーム"].pp == 12


def test_マジックルーム_マジックコートで跳ね返されない():
    """マジックルーム: 全体の場を対象とする技のため、相手のマジックコートで跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["マジックルーム"])],
        team1=[Pokemon("ピカチュウ")],
        volatile1={"マジックコート": 1},
    )
    t.run_move(battle, 0)
    assert battle.get_global_field("マジックルーム").is_active


def test_マジックルーム_まもるで防がれない():
    """マジックルーム: 全体の場を対象とする技のため、相手のまもるで防がれない"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["マジックルーム"])],
        team1=[Pokemon("ピカチュウ")],
        volatile1={"まもる": 1},
    )
    t.run_move(battle, 0)
    assert battle.get_global_field("マジックルーム").is_active


def test_マジックルーム_場が発動する():
    """マジックルーム: 使用すると場が『マジックルーム』状態になり、5ターン継続する。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["マジックルーム"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    field = battle.get_global_field("マジックルーム")
    assert field.is_active
    assert field.count == 5


def test_マジックルーム_発動すると使用者のもちものも無効化される():
    """マジックルーム: 使用した瞬間から自分自身のもちものも無効化される。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["マジックルーム"], item_name="たべのこし")],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    mon = battle.actives[0]
    mon.hp = 1
    t.end_turn(battle)
    assert mon.hp == 1


def test_マジックルーム_発動中に再使用すると解除される():
    """マジックルーム: 発動中に再度使用すると即座にフィールドが解除される（トグル動作）。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["マジックルーム"])],
        team1=[Pokemon("ピカチュウ")],
        field={"マジックルーム": 5},
    )
    t.run_move(battle, 0)
    assert not battle.get_global_field("マジックルーム").is_active


def test_まねっこ_PPはまねっこ自身のみ消費されコピー技は消費されない():
    """まねっこ: コピーした技のPPは消費されず、まねっこ自身のPPのみ1消費される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まねっこ"])],
        team1=[Pokemon("コラッタ", move_names=["でんこうせっか"])],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]

    t.run_move(battle, 1)  # コラッタ: でんこうせっか（自身のPPを1消費）
    defender_move_pp_after_own_use = defender.moves[0].pp

    manekko_pp_before = attacker.moves[0].pp
    t.run_move(battle, 0)  # ピカチュウ: まねっこ（でんこうせっかをコピー）

    assert attacker.moves[0].pp == manekko_pp_before - 1
    assert defender.moves[0].pp == defender_move_pp_after_own_use


def test_まねっこ_おいわいはコピーできない():
    """まねっこ: 直前の技がおいわい（non_copycatフラグ持ち）の場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まねっこ"])],
        team1=[Pokemon("カビゴン", move_names=["おいわい"])],
        accuracy=100,
    )
    t.run_move(battle, 1)  # カビゴン: おいわい
    t.run_move(battle, 0)  # ピカチュウ: まねっこ → 失敗するはず

    assert not battle.move_executor.move_applied


def test_まねっこ_カウンターはコピーできない():
    """まねっこ: 直前の技がカウンター（non_copycatフラグ持ち）の場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ひっかく", "まねっこ"])],
        team1=[Pokemon("カビゴン", move_names=["カウンター"])],
        accuracy=100,
    )
    t.run_move(battle, 0, move_idx=0)  # ピカチュウ: ひっかく（カビゴンに物理ダメージ）
    t.run_move(battle, 1, move_idx=0)  # カビゴン: カウンター（成功して最後の使用技になる）
    t.run_move(battle, 0, move_idx=1)  # ピカチュウ: まねっこ → 失敗するはず

    assert not battle.move_executor.move_applied


def test_まねっこ_きょじゅうだんはコピーできない():
    """まねっこ: 直前の技がきょじゅうだん（non_copycatフラグ持ち）の場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まねっこ"])],
        team1=[Pokemon("カビゴン", move_names=["きょじゅうだん"])],
        accuracy=100,
    )
    t.run_move(battle, 1)  # カビゴン: きょじゅうだん
    t.run_move(battle, 0)  # ピカチュウ: まねっこ → 失敗するはず

    assert not battle.move_executor.move_applied


def test_まねっこ_ゲップはコピーできない():
    """まねっこ: 直前の技がゲップ（non_copycatフラグ持ち）の場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まねっこ"])],
        team1=[Pokemon("カビゴン", item_name="オレンのみ", move_names=["ゲップ"])],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.item_manager.consume_item(defender)  # きのみを食べてゲップの使用条件を満たす
    t.run_move(battle, 1)  # カビゴン: ゲップ（成功して最後の使用技になる）
    assert battle.move_executor.move_success is True
    t.run_move(battle, 0)  # ピカチュウ: まねっこ → 失敗するはず

    assert not battle.move_executor.move_applied


def test_まねっこ_スケッチはコピーできない():
    """まねっこ: 直前の技がスケッチ（non_copycatフラグ持ち）の場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まねっこ"])],
        team1=[Pokemon("ドーブル", move_names=["スケッチ"])],
        accuracy=100,
    )
    t.run_move(battle, 1)  # ドーブル: スケッチ（実装保留のため空振りだが技自体は使用される）
    t.run_move(battle, 0)  # ピカチュウ: まねっこ → 失敗するはず

    assert not battle.move_executor.move_applied


def test_まねっこ_スターモービル専用技はコピーできない():
    """まねっこ: 直前の技がスターモービル専用技（アクセル技）の場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まねっこ"])],
        team1=[Pokemon("コラッタ", move_names=["バーンアクセル"])],
        accuracy=100,
    )
    t.run_move(battle, 1)  # コラッタ: バーンアクセル
    t.run_move(battle, 0)  # ピカチュウ: まねっこ → 失敗するはず

    assert not battle.move_executor.move_applied


def test_まねっこ_すりかえはコピーできない():
    """まねっこ: 直前の技がすりかえ（non_copycatフラグ持ち）の場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まねっこ"])],
        team1=[Pokemon("カビゴン", move_names=["すりかえ"])],
        accuracy=100,
    )
    t.run_move(battle, 1)  # カビゴン: すりかえ
    t.run_move(battle, 0)  # ピカチュウ: まねっこ → 失敗するはず

    assert not battle.move_executor.move_applied


def test_まねっこ_ダイマックスほうはコピーできない():
    """まねっこ: 直前の技がダイマックスほう（non_copycatフラグ持ち）の場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まねっこ"])],
        team1=[Pokemon("カビゴン", move_names=["ダイマックスほう"])],
        accuracy=100,
    )
    t.run_move(battle, 1)  # カビゴン: ダイマックスほう
    t.run_move(battle, 0)  # ピカチュウ: まねっこ → 失敗するはず

    assert not battle.move_executor.move_applied


def test_まねっこ_テラクラスターはコピーできない():
    """まねっこ: 直前の技がテラクラスター（non_copycatフラグ持ち）の場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まねっこ"])],
        team1=[Pokemon("カビゴン", tera_type="ステラ", move_names=["テラクラスター"])],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.terastallize()
    t.run_move(battle, 1)  # カビゴン: テラクラスター
    t.run_move(battle, 0)  # ピカチュウ: まねっこ → 失敗するはず

    assert not battle.move_executor.move_applied


def test_まねっこ_トリックはコピーできない():
    """まねっこ: 直前の技がトリック（non_copycatフラグ持ち）の場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まねっこ"])],
        team1=[Pokemon("カビゴン", move_names=["トリック"], item_name="いのちのたま")],
        accuracy=100,
    )
    t.run_move(battle, 1)  # カビゴン: トリック
    t.run_move(battle, 0)  # ピカチュウ: まねっこ → 失敗するはず

    assert not battle.move_executor.move_applied


def test_まねっこ_ハッピータイムはコピーできる():
    """まねっこ: 直前の技がハッピータイム（non_copycatフラグなし）の場合はコピーに成功する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まねっこ"])],
        team1=[Pokemon("カビゴン", move_names=["ハッピータイム"])],
        accuracy=100,
    )
    t.run_move(battle, 1)  # カビゴン: ハッピータイム
    t.run_move(battle, 0)  # ピカチュウ: まねっこ → ハッピータイムをコピーして成功するはず

    assert battle.move_executor.move_applied


def test_まねっこ_フェイントはコピーできない():
    """まねっこ: 直前の技がフェイント（non_copycatフラグ持ち）の場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まねっこ"])],
        team1=[Pokemon("カビゴン", move_names=["フェイント"])],
        accuracy=100,
    )
    t.run_move(battle, 1)  # カビゴン: フェイント
    t.run_move(battle, 0)  # ピカチュウ: まねっこ → 失敗するはず

    assert not battle.move_executor.move_applied


def test_まねっこ_まもるはコピーできない():
    """まねっこ: 直前の技がまもる（protectフラグ持ち）の場合は失敗する

    「守る」系統の技は個別に non_copycat フラグを付与せず、既存の protect フラグを
    まねっこ_can_use 側で確認することでコピー不可にしている。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まねっこ"])],
        team1=[Pokemon("カビゴン", move_names=["まもる"])],
        accuracy=100,
    )
    t.run_move(battle, 1)  # カビゴン: まもる
    t.run_move(battle, 0)  # ピカチュウ: まねっこ → 失敗するはず

    assert not battle.move_executor.move_applied


def test_まねっこ_ものまねはコピーできない():
    """まねっこ: 直前の技がものまね（non_copycatフラグ持ち）の場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まねっこ"])],
        team1=[Pokemon("カビゴン", move_names=["ものまね"])],
        accuracy=100,
    )
    t.run_move(battle, 1)  # カビゴン: ものまね（実装保留のため空振りだが技自体は使用される）
    t.run_move(battle, 0)  # ピカチュウ: まねっこ → 失敗するはず

    assert not battle.move_executor.move_applied


def test_まねっこ_使用技がまだない場合は失敗する():
    """まねっこ: バトル開始以降、誰も技を使っていない場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まねっこ"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)

    assert not battle.move_executor.move_applied


def test_まねっこ_変化技をコピーしても無限再帰にならない():
    """まねっこ: コピー対象が変化技（status技）の場合でも RecursionError 等を起こさず正常に実行される

    まねっこ自身のON_STATUS_HITハンドラを解除せずにコピー技を実行すると、
    ネストしたrun_move内で再度ON_STATUS_HITが発火した際にまねっこ_executeが
    多重発火し無限再帰してしまう回帰を防ぐテスト。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まねっこ"])],
        team1=[Pokemon("コラッタ", move_names=["なきごえ"])],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]

    t.run_move(battle, 1)  # コラッタ: なきごえ（ピカチュウのこうげきを下げる）
    assert attacker.boosts["atk"] == -1

    t.run_move(battle, 0)  # ピカチュウ: まねっこ（なきごえをコピーしコラッタへ）

    assert battle.move_executor.move_applied
    assert defender.boosts["atk"] == -1  # コピーしたなきごえがコラッタのこうげきを下げる


def test_まねっこ_相手が最後に使用した技をコピーして実行する():
    """まねっこ: 相手が最後に使用した技をコピーして相手に与える"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まねっこ"])],
        team1=[Pokemon("コラッタ", move_names=["でんこうせっか"])],
        accuracy=100,
    )
    defender = battle.actives[1]

    t.run_move(battle, 1)  # コラッタ: でんこうせっか（ピカチュウにダメージ）
    hp_before_copy = defender.hp

    t.run_move(battle, 0)  # ピカチュウ: まねっこ（でんこうせっかをコピーしコラッタへ）

    assert defender.hp < hp_before_copy


def test_まねっこ_自分が使った技もコピー対象になる():
    """まねっこ: 直前に自分自身が使用した技もコピー対象になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんこうせっか", "まねっこ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]

    t.run_move(battle, 0, 0)  # でんこうせっか
    hp_after_first_hit = defender.hp

    t.run_move(battle, 0, 1)  # まねっこ（でんこうせっかをコピー）

    assert defender.hp < hp_after_first_hit


def test_まほうのこな_アルセウスには無効():
    """まほうのこな: アルセウスには持ち物の有無に関わらず無効"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まほうのこな"])],
        team1=[Pokemon("アルセウス")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert not defender.has_volatile("まほうのこな")
    assert defender.types == ["ノーマル"]


def test_まほうのこな_エスパー単タイプに変える():
    """まほうのこな: 使用後に defender がエスパータイプのみになること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まほうのこな"])],
        team1=[Pokemon("ボルケニオン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    assert "みず" in defender.types
    assert "ほのお" in defender.types
    t.run_move(battle, 0)

    assert defender.types == ["エスパー"]
    assert defender.has_volatile("まほうのこな")


def test_まほうのこな_くさタイプの相手には粉技として無効():
    """まほうのこな: くさタイプの相手には粉技無効化ルールで無効になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まほうのこな"])],
        team1=[Pokemon("フシギダネ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert not defender.has_volatile("まほうのこな")


def test_まほうのこな_シルヴァディには無効():
    """まほうのこな: シルヴァディには持ち物の有無に関わらず無効"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まほうのこな"])],
        team1=[Pokemon("シルヴァディ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert not defender.has_volatile("まほうのこな")
    assert defender.types == ["ノーマル"]


def test_まほうのこな_すでにエスパー単タイプなら失敗():
    """まほうのこな: 相手がすでにエスパー単タイプのみなら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まほうのこな"])],
        team1=[Pokemon("ケーシィ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    assert defender.types == ["エスパー"]
    t.run_move(battle, 0)

    assert not defender.has_volatile("まほうのこな")


def test_まほうのこな_テラスタル中の相手には失敗する():
    """まほうのこな: テラスタルしている相手には失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まほうのこな"])],
        team1=[Pokemon("カビゴン", tera_type="ほのお")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.is_terastallized = True
    assert defender.active_tera_type == "ほのお"
    t.run_move(battle, 0)

    assert not defender.has_volatile("まほうのこな")
    assert defender.types == ["ほのお"]


def test_まほうのこな_ハロウィン後の相手に使うとaddedTypesがクリアされエスパーのみになる():
    """まほうのこな: ハロウィン後の相手に使うと added_types がクリアされてエスパータイプのみになること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まほうのこな"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"ハロウィン": 0},
        accuracy=100,
    )
    defender = battle.actives[1]
    # ハロウィン付与後はゴーストタイプが追加されている
    assert defender.has_type("ゴースト")
    t.run_move(battle, 0)

    # まほうのこな後は added_types がクリアされてエスパーのみになること
    assert defender.types == ["エスパー"]
    assert not defender.has_type("ゴースト")


def test_まほうのこな_もりののろいでくさタイプになった相手には効かない():
    """まほうのこな: もりののろいでくさタイプが追加された相手には粉技無効化ルールで無効になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まほうのこな"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"もりののろい": 0},
        accuracy=100,
    )
    defender = battle.actives[1]
    assert defender.has_type("くさ")
    t.run_move(battle, 0)

    assert not defender.has_volatile("まほうのこな")
    assert defender.has_type("くさ")


def test_まほうのこな_交代すると元のタイプに戻る():
    """まほうのこな: 交代後に volatile_override_type がリセットされること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まほうのこな"])],
        team1=[Pokemon("カビゴン"), Pokemon("ヤドラン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.types == ["エスパー"]

    # 交代後は元のタイプに戻ること
    t.run_switch(battle, 1, 1)
    assert not defender.has_volatile("まほうのこな")
    assert defender.volatile_override_type is None
    # カビゴンはノーマルタイプ
    assert defender.types == ["ノーマル"]


def test_まほうのこな_特性ぼうじんを持つ相手には無効():
    """まほうのこな: 特性ぼうじんを持つ相手には粉技無効化ルールで無効になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まほうのこな"])],
        team1=[Pokemon("カビゴン", ability_name="ぼうじん")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert not defender.has_volatile("まほうのこな")


def test_まほうのこな_道具ぼうじんゴーグルを持つ相手には無効():
    """まほうのこな: ぼうじんゴーグルを持つ相手には粉技無効化ルールで無効になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まほうのこな"])],
        team1=[Pokemon("カビゴン", item_name="ぼうじんゴーグル")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert not defender.has_volatile("まほうのこな")


def test_まもる_まねっこでコピーできない():
    """まもる: non_copycatフラグを持つため、まねっこでコピーできない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まねっこ"])],
        team1=[Pokemon("カビゴン", move_names=["まもる"])],
        accuracy=100,
    )
    t.run_move(battle, 1)  # カビゴン: まもる
    t.run_move(battle, 0)  # ピカチュウ: まねっこ → 失敗するはず

    assert not battle.move_executor.move_applied


def test_まもる_使用した同ターンに相手の攻撃技をブロックする():
    """まもる: 技を実行して付与したまもる状態が、同ターン内の相手の攻撃を無効化する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まもる"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    protected_mon = battle.actives[0]  # まもるを使うピカチュウ（たいあたりの対象）
    hp_before = protected_mon.hp

    t.run_move(battle, 0)  # ピカチュウ: まもる成功
    assert battle.move_executor.move_success

    t.run_move(battle, 1)  # カビゴン: たいあたり → まもるでブロックされる
    assert not battle.move_executor.move_success
    assert protected_mon.hp == hp_before


def test_まもる系_2ターン目は失敗する():
    """まもる: 2ターン連続で使用すると2ターン目は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まもる"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]

    # 1ターン目: まもる成功
    t.run_move(battle, 0)
    assert battle.move_executor.move_success
    assert attacker.has_volatile("まもる")

    # ターン終了でまもるvolatileが解除されるが last_move は残る
    t.end_turn(battle)
    assert not attacker.has_volatile("まもる")

    # 2ターン目: まもる失敗（連続使用）
    t.run_move(battle, 0)
    assert not battle.move_executor.move_success
    assert not attacker.has_volatile("まもる")


def test_まもる系_2ターン目失敗後3ターン目は再使用できる():
    """まもる: 2ターン目に失敗した後、3ターン目は再び成功する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まもる"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]

    # 1ターン目: まもる成功
    t.run_move(battle, 0)
    assert battle.move_executor.move_success
    t.end_turn(battle)

    # 2ターン目: まもる失敗（連続使用）→ last_move が None にリセットされる
    t.run_move(battle, 0)
    assert not battle.move_executor.move_success
    t.end_turn(battle)

    # 3ターン目: まもる再び成功
    t.run_move(battle, 0)
    assert battle.move_executor.move_success
    assert attacker.has_volatile("まもる")


def test_まもる系_キングシールドとニードルガードでも相互に失敗する():
    """キングシールド→ニードルガード: 守る系は種類が違っても連続使用で2ターン目は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["キングシールド", "ニードルガード"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]

    # 1ターン目: キングシールド成功
    t.run_move(battle, 0, 0)
    assert battle.move_executor.move_success
    assert attacker.has_volatile("キングシールド")
    t.end_turn(battle)

    # 2ターン目: ニードルガード失敗（直前にprotectフラグ技を使ったため）
    t.run_move(battle, 0, 1)
    assert not battle.move_executor.move_success
    assert not attacker.has_volatile("ニードルガード")


def test_まもる系_別技をはさむと再使用できる():
    """まもる: 間に別技を使うと次のターンに守る系を再び使える"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まもる", "でんきショック"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]

    # 1ターン目: まもる成功
    t.run_move(battle, 0, 0)
    assert battle.move_executor.move_success
    t.end_turn(battle)

    # 2ターン目: でんきショックを使う（protect フラグなし）
    t.run_move(battle, 0, 1)
    t.end_turn(battle)

    # 3ターン目: まもる再び成功（last_move が守る系でないため）
    t.run_move(battle, 0, 0)
    assert battle.move_executor.move_success
    assert attacker.has_volatile("まもる")


def test_まもる系_異種の守る系技でも2ターン目は失敗する():
    """まもる→みきり: 異なる守る系技でも2ターン目は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まもる", "みきり"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]

    # 1ターン目: まもる成功
    t.run_move(battle, 0, 0)
    assert battle.move_executor.move_success
    t.end_turn(battle)

    # 2ターン目: みきり失敗（直前にprotectフラグ技を使ったため）
    t.run_move(battle, 0, 1)
    assert not battle.move_executor.move_success
    assert not attacker.has_volatile("まもる")


def test_まるくなる_ぼうぎょが1段階上がりまるくなる状態を付与する():
    """まるくなる: 自分のぼうぎょが1段階上がり、まるくなる状態になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まるくなる"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.boosts["def"] == 1
    assert attacker.has_volatile("まるくなる")


def test_まるくなる_マジックコートで跳ね返されない():
    """まるくなる: 自分を対象とする技のため、相手のマジックコートで跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まるくなる"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)

    assert attacker.boosts["def"] == 1
    assert attacker.has_volatile("まるくなる")
    assert defender.boosts["def"] == 0
    assert not defender.has_volatile("まるくなる")


def test_まるくなる_まもるで防がれない():
    """まるくなる: 自分を対象とする技のため、相手のまもるで防がれない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まるくなる"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.boosts["def"] == 1
    assert attacker.has_volatile("まるくなる")


def test_みかづきのいのり_HPが4分の1回復する():
    """みかづきのいのり: 最大HPの1/4を回復する(小数点以下切り捨て)"""
    battle = t.start_battle(
        team0=[Pokemon("クレセリア", move_names=["みかづきのいのり"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)

    assert attacker.hp == 1 + int(attacker.max_hp * 1 / 4)


def test_みかづきのいのり_HP満タンかつ無状態異常だと失敗する():
    """みかづきのいのり: HPが満タンかつ状態異常もない場合は技が失敗する

    公式Wiki「技の仕様」節によると、タイプとPPを除けば基本的に `ジャングルヒール` と
    同様の効果を持ち、`ジャングルヒール` はHPが満タンかつ状態異常でもないポケモンしか
    回復対象がいない場合に失敗する（docs/spec/turn.md 「ジャングルヒール: HP満タン・状態異常無」）。
    """
    battle = t.start_battle(
        team0=[Pokemon("クレセリア", move_names=["みかづきのいのり"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    assert attacker.hp == attacker.max_hp
    assert not attacker.ailment.is_active
    t.run_move(battle, 0)

    assert battle.move_executor.move_success is False


def test_みかづきのいのり_HP満タンでも状態異常があれば成功する():
    """みかづきのいのり: HPが満タンでも状態異常があれば技は成功し、状態異常のみ治す"""
    battle = t.start_battle(
        team0=[Pokemon("クレセリア", move_names=["みかづきのいのり"])],
        team1=[Pokemon("カビゴン")],
        ailment0=("まひ", None),
    )
    attacker = battle.actives[0]
    assert attacker.hp == attacker.max_hp
    assert attacker.ailment.is_active
    battle.test_option.trigger_ailment = False
    t.run_move(battle, 0)

    assert battle.move_executor.move_success is True
    assert not attacker.ailment.is_active
    assert attacker.hp == attacker.max_hp


@pytest.mark.parametrize("ailment_name", ["どく", "まひ", "やけど"])
def test_みかづきのいのり_状態異常を治す(ailment_name):
    """みかづきのいのり: 使用者の状態異常を治す"""
    battle = t.start_battle(
        team0=[Pokemon("クレセリア", move_names=["みかづきのいのり"])],
        team1=[Pokemon("カビゴン")],
        ailment0=(ailment_name, None),
    )
    attacker = battle.actives[0]
    assert attacker.ailment.is_active
    battle.test_option.trigger_ailment = False
    t.run_move(battle, 0)

    assert not attacker.ailment.is_active


def test_みかづきのまい_使用者がひんしになりサイドフィールドが設置される():
    """みかづきのまい: 使用後に使用者がひんし状態になり、自陣営にサイドフィールドが設置される"""
    battle = t.start_battle(
        team0=[Pokemon("クレセリア", move_names=["みかづきのまい"]), Pokemon("カビゴン")],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.fainted
    side = battle.get_side(attacker)
    assert side.get("みかづきのまい").is_active


def test_みかづきのまい_控えのポケモンがいない場合は失敗する():
    """みかづきのまい: 控えのポケモンがいない場合は失敗し、使用者はひんしにならない"""
    battle = t.start_battle(
        team0=[Pokemon("クレセリア", move_names=["みかづきのまい"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert not attacker.fainted
    assert not battle.move_executor.move_applied
    side = battle.get_side(attacker)
    assert not side.get("みかづきのまい").is_active


def test_みかづきのまい_死に出しポケモンのHPと状態異常とPPが全回復する():
    """みかづきのまい: 死に出しのポケモンのHPと状態異常が全回復し、全ての技のPPも全回復する"""
    battle = t.start_battle(
        team0=[Pokemon("クレセリア", move_names=["みかづきのまい"]), Pokemon("カビゴン", move_names=["たいあたり", "はらだいこ"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)

    bench = battle.player_states[battle.players[0]].team[1]
    bench.hp = 1
    battle.ailment_manager.apply(bench, "まひ")
    bench.moves[0].pp = 0
    bench.moves[1].pp = 1
    assert bench.ailment.is_active

    battle.switch_manager.run_faint_switch()

    assert bench.hp == bench.max_hp
    assert not bench.ailment.is_active
    assert bench.moves[0].pp == bench.moves[0].data.pp
    assert bench.moves[1].pp == bench.moves[1].data.pp
    side = battle.get_side(bench)
    assert not side.get("みかづきのまい").is_active


def test_みがわり_HPを消費してみがわり状態になる():
    """みがわり: 最大HPの1/4（切り捨て）を消費し、同量のHPを持つみがわり状態になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みがわり"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    max_hp = attacker.max_hp
    migawari_hp = max_hp // 4

    t.run_move(battle, 0)

    assert attacker.hp == max_hp - migawari_hp
    assert attacker.has_volatile("みがわり")
    assert attacker.volatiles["みがわり"].hp == migawari_hp
    assert battle.move_executor.move_applied is True


def test_みがわり_すでにみがわり状態なら失敗する():
    """みがわり: すでにみがわり状態のときは失敗し、HPもみがわりHPも変化しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みがわり"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    battle.volatile_manager.apply(attacker, "みがわり", hp=1)
    hp_before = attacker.hp

    t.run_move(battle, 0)

    assert attacker.hp == hp_before
    assert attacker.volatiles["みがわり"].hp == 1
    assert battle.move_executor.move_applied is False


def test_みがわり_成功時に自分のバインド状態を解除する():
    """みがわり: 技が成功すると自分のバインド状態を解除する（第三世代以降の仕様）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みがわり"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    battle.volatile_manager.apply(attacker, "バインド", count=3, source=battle.actives[1], bind_damage_ratio=1 / 8)

    t.run_move(battle, 0)

    assert not attacker.has_volatile("バインド")
    assert attacker.has_volatile("みがわり")


def test_みがわり_残りHPが最大HPの4分の1以下なら失敗する():
    """みがわり: 残りHPが最大HPの1/4以下（ちょうど1/4を含む）のときは失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みがわり"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.hp = attacker.max_hp // 4

    t.run_move(battle, 0)

    assert attacker.hp == attacker.max_hp // 4
    assert not attacker.has_volatile("みがわり")
    assert battle.move_executor.move_applied is False


def test_みがわり_相手のまもるを無視して成功する():
    """みがわり: 自分対象の変化技のため、相手がまもる状態でも無視して成功する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みがわり"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "まもる", count=1)

    t.run_move(battle, 0)

    assert attacker.has_volatile("みがわり")
    assert battle.move_executor.move_applied is True


def test_みきり_2ターン連続で使用すると2ターン目は失敗する():
    """みきり: まもると同じくPP8・優先度+4で先制でき、2ターン連続で使用すると2ターン目は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みきり"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    assert attacker.moves[0].data.pp == 8
    assert attacker.moves[0].data.priority == 4

    # 1ターン目: みきり成功
    t.run_move(battle, 0)
    assert battle.move_executor.move_success
    assert attacker.has_volatile("まもる")
    t.end_turn(battle)

    # 2ターン目: みきり失敗（連続使用）
    t.run_move(battle, 0)
    assert not battle.move_executor.move_success
    assert not attacker.has_volatile("まもる")


def test_ミストフィールド_すでに同じ地形なら失敗():
    """ミストフィールド: すでにミストフィールドが有効なら失敗（再設置されない）"""
    battle = t.start_battle(
        team0=[Pokemon("ピクシー", move_names=["ミストフィールド"])],
        team1=[Pokemon("カビゴン")],
        terrain=("ミストフィールド", 3),
    )
    t.run_move(battle, 0)

    # カウントは変わらない
    assert battle.terrain.name == "ミストフィールド"
    assert battle.terrain.count == 3


def test_ミストフィールド_地形がミストフィールドになる():
    """ミストフィールド: 使用後に地形がミストフィールドになり5ターン継続する"""
    battle = t.start_battle(
        team0=[Pokemon("ピクシー", move_names=["ミストフィールド"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)
    assert battle.terrain.name == "ミストフィールド"
    assert battle.terrain.count == 5


def test_みずびたし_アルセウスには無効():
    """みずびたし: アルセウスには持ち物の有無に関わらず無効"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みずびたし"])],
        team1=[Pokemon("アルセウス")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert not defender.has_volatile("みずびたし")
    assert defender.types == ["ノーマル"]


def test_みずびたし_シルヴァディには無効():
    """みずびたし: シルヴァディには持ち物の有無に関わらず無効"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みずびたし"])],
        team1=[Pokemon("シルヴァディ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert not defender.has_volatile("みずびたし")
    assert defender.types == ["ノーマル"]


def test_みずびたし_すでにみずタイプのみなら失敗():
    """みずびたし: 相手がすでにみずタイプのみなら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みずびたし"])],
        team1=[Pokemon("ゼニガメ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    assert defender.types == ["みず"]
    t.run_move(battle, 0)

    # volatile が付与されないこと
    assert not defender.has_volatile("みずびたし")


def test_みずびたし_テラスタル中の相手には失敗する():
    """みずびたし: テラスタルしている相手には失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みずびたし"])],
        team1=[Pokemon("カビゴン", tera_type="ほのお")],
        accuracy=100,
    )
    defender = battle.actives[1]
    # テラスタル状態にする
    defender.is_terastallized = True
    assert defender.active_tera_type == "ほのお"
    t.run_move(battle, 0)

    # 技自体が失敗し、volatile は付与されない
    assert not defender.has_volatile("みずびたし")
    assert defender.types == ["ほのお"]


def test_みずびたし_ハロウィン後の相手に使うとaddedTypesがクリアされみずのみになる():
    """みずびたし: ハロウィン後の相手に使うと added_types がクリアされてみずタイプのみになること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みずびたし"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"ハロウィン": 0},
        accuracy=100,
    )
    defender = battle.actives[1]
    # ハロウィン付与後はゴーストタイプが追加されている
    assert defender.has_type("ゴースト")
    t.run_move(battle, 0)

    # みずびたし後は added_types がクリアされてみずのみになること
    assert defender.types == ["みず"]
    assert not defender.has_type("ゴースト")


def test_みずびたし_みずタイプに変える():
    """みずびたし: 使用後に defender がみずタイプのみになること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みずびたし"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    assert not defender.has_type("みず")
    t.run_move(battle, 0)

    assert defender.types == ["みず"]
    assert defender.has_volatile("みずびたし")


def test_みずびたし_交代すると元のタイプに戻る():
    """みずびたし: 交代後に volatile_override_type がリセットされること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みずびたし"])],
        team1=[Pokemon("カビゴン"), Pokemon("ヤドラン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.types == ["みず"]

    # 交代後は元のタイプに戻ること
    t.run_switch(battle, 1, 1)
    assert not defender.has_volatile("みずびたし")
    assert defender.volatile_override_type is None
    # カビゴンはノーマルタイプ
    assert defender.types == ["ノーマル"]


def test_みずびたし_複合タイプに使うと成功しみずのみになる():
    """みずびたし: みず+ほのおの複合タイプを持つ相手にもみずのみになること"""
    # シャワーズはみずタイプのみなので、カメックス（みず）ではなく
    # ボルケニオン（みず+ほのお）を使う
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みずびたし"])],
        team1=[Pokemon("ボルケニオン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    assert "みず" in defender.types
    assert "ほのお" in defender.types
    t.run_move(battle, 0)

    # みずタイプのみになること
    assert defender.types == ["みず"]
    assert defender.has_volatile("みずびたし")


def test_みちづれ_2ターン目失敗後3ターン目は再使用できる():
    """みちづれ: 連続使用に失敗した直後にもう一度使った場合は成功する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みちづれ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]

    t.run_move(battle, 0)
    assert battle.move_executor.move_success
    t.end_turn(battle)

    # 2ターン目: 連続使用で失敗
    t.run_move(battle, 0)
    assert not battle.move_executor.move_success
    t.end_turn(battle)

    # 3ターン目: 直前が失敗（last_moveがリセット済み）のため再び成功する
    t.run_move(battle, 0)
    assert battle.move_executor.move_success
    assert attacker.has_volatile("みちづれ")


def test_みちづれ_2ターン連続で使用すると2ターン目は失敗する():
    """みちづれ: 第七世代以降の仕様により、成功直後にもう一度使うと必ず失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みちづれ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]

    # 1ターン目: みちづれ成功（付与直後なのでみちづれ状態は残っている）
    t.run_move(battle, 0)
    assert battle.move_executor.move_success
    assert attacker.has_volatile("みちづれ")
    t.end_turn(battle)

    # 2ターン目: 自身の行動開始時（ON_TRY_ACTION）にみちづれ状態は解除されるが、
    # 直前の last_move が「みちづれ」のままなので技自体は失敗する（連続使用）
    t.run_move(battle, 0)
    assert not battle.move_executor.move_success
    assert not attacker.has_volatile("みちづれ")


def test_みちづれ_使用すると自分にみちづれ状態を付与する():
    """みちづれ: 使用すると自分に「みちづれ」揮発性状態が付与される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みちづれ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert battle.move_executor.move_success
    assert attacker.has_volatile("みちづれ")


def test_みちづれ_別の技をはさむと再使用できる():
    """みちづれ: 間に別の技を使うと次のターンにみちづれを再び使える"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みちづれ", "でんきショック"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]

    # 1ターン目: みちづれ成功
    t.run_move(battle, 0, 0)
    assert battle.move_executor.move_success
    t.end_turn(battle)

    # 2ターン目: でんきショックを使う（みちづれではない）
    t.run_move(battle, 0, 1)
    t.end_turn(battle)

    # 3ターン目: みちづれ再び成功（last_moveがみちづれでないため）
    t.run_move(battle, 0, 0)
    assert battle.move_executor.move_success
    assert attacker.has_volatile("みちづれ")


def test_ミラータイプ_PPは16():
    """ミラータイプ: PPは16（champions基準）"""
    move_data = MOVES["ミラータイプ"]
    assert move_data.pp == 16


def test_ミラータイプ_コピー後元のタイプが消える():
    """ミラータイプ: タイプコピー後にゴースト追加前のタイプがリセットされること"""
    # ハロウィンでゴーストが追加されたピカチュウがミラータイプを使った場合
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ミラータイプ"])],
        team1=[Pokemon("エンテイ")],
        volatile0={"ハロウィン": 0},
        accuracy=100,
    )
    attacker = battle.actives[0]
    assert "ゴースト" in attacker.types
    t.run_move(battle, 0)

    # エンテイ（ほのお）のタイプのみになること
    assert attacker.types == ["ほのお"]


def test_ミラータイプ_ステラテラスタル中は元のタイプをコピーする():
    """ミラータイプ: 相手がステラテラスタル中なら data.types をコピーする"""
    # ゲッコウガがステラテラスタルしている場合は元のタイプ（みず・あく）をコピー
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ミラータイプ"])],
        team1=[Pokemon("ゲッコウガ", tera_type="ステラ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    defender.is_terastallized = True
    assert defender.active_tera_type == "ステラ"
    t.run_move(battle, 0)

    # data.types をコピー（みず・あく）
    assert "みず" in attacker.types
    assert "あく" in attacker.types


def test_ミラータイプ_タイプが同じなら失敗する():
    """ミラータイプ: 使用者のタイプが対象のタイプと同じなら失敗する"""
    # ピカチュウ（でんき）→ ピカチュウ（でんき）なら失敗
    # ただし使用者はすでにミラータイプ後でないとタイプが同じにならないので
    # カビゴン（ノーマル）対カビゴン（ノーマル）で試す
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ミラータイプ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    assert attacker.types == ["ノーマル"]
    t.run_move(battle, 0)

    # 失敗するためタイプ変化なし
    assert attacker.types == ["ノーマル"]


def test_ミラータイプ_テラスタル中の使用者は失敗する():
    """ミラータイプ: 自分がテラスタルしているときは失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ミラータイプ"], tera_type="ほのお")],
        team1=[Pokemon("ゲッコウガ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.is_terastallized = True
    t.run_move(battle, 0)

    # 失敗するためテラタイプのまま
    assert attacker.types == ["ほのお"]


def test_ミラータイプ_テラスタル中はテラタイプをコピーする():
    """ミラータイプ: 相手がテラスタル中（ステラ以外）ならテラタイプのみをコピーする"""
    # ゲッコウガ（みず・あく）がほのおテラスタルしている場合はほのおをコピー
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ミラータイプ"])],
        team1=[Pokemon("ゲッコウガ", tera_type="ほのお")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    defender.is_terastallized = True
    assert defender.active_tera_type == "ほのお"
    t.run_move(battle, 0)

    # テラタイプのみをコピー
    assert attacker.types == ["ほのお"]


def test_ミラータイプ_マジックコートで跳ね返されない():
    """ミラータイプ: unreflectableフラグを持つため、相手のマジックコート状態でも跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ミラータイプ"])],
        team1=[Pokemon("ゲッコウガ")],
        volatile1={"マジックコート": 1},
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert "みず" in attacker.types
    assert "あく" in attacker.types


def test_ミラータイプ_まもるで防がれる():
    """ミラータイプ: 相手のまもる状態には防がれる（対象がfoeのため）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ミラータイプ"])],
        team1=[Pokemon("ゲッコウガ")],
        volatile1={"まもる": 1},
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    # まもるで防がれるためタイプ変化なし
    assert attacker.types == ["でんき"]


def test_ミラータイプ_みがわりを貫通して成功する():
    """ミラータイプ: bypass_substituteフラグを持つため、みがわり状態の相手にも成功する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ミラータイプ"])],
        team1=[Pokemon("ゲッコウガ")],
        volatile1={"みがわり": 1},
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_volatile("みがわり")
    assert "みず" in attacker.types
    assert "あく" in attacker.types


def test_ミラータイプ_交代するとタイプがリセットされる():
    """ミラータイプ: 交代後にコピーされたタイプがリセットされること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ミラータイプ"]), Pokemon("カビゴン")],
        team1=[Pokemon("ゲッコウガ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.types == ["みず", "あく"]

    # 交代後はリセットされること
    t.run_switch(battle, 0, 1)
    # ピカチュウのタイプは元に戻る
    assert attacker.types == ["でんき"]


def test_ミラータイプ_相手がひこう単タイプではねやすめでタイプを消している場合はノーマルをコピーする():
    """ミラータイプ: 相手がひこう単タイプではねやすめ状態のときはノーマルタイプとして扱う"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ミラータイプ"])],
        team1=[Pokemon("トルネロス(けしん)")],
        volatile1={"はねやすめ": 0},
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    assert defender.types == []
    t.run_move(battle, 0)

    assert attacker.types == ["ノーマル"]


def test_ミラータイプ_相手のタイプをコピーする():
    """ミラータイプ: 使用後に attacker のタイプが defender のタイプと同じになること"""
    # ピカチュウ（でんき）→ ゲッコウガ（みず・あく）のタイプをコピー
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ミラータイプ"])],
        team1=[Pokemon("ゲッコウガ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    assert attacker.types == ["でんき"]
    t.run_move(battle, 0)

    assert "みず" in attacker.types
    assert "あく" in attacker.types


def test_ミラータイプ_相手のもりののろいで追加されたタイプもコピーする():
    """ミラータイプ: 相手がもりののろい状態のときは、追加されたくさタイプも含めてコピーする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ミラータイプ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"もりののろい": 0},
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    assert defender.types == ["ノーマル", "くさ"]
    t.run_move(battle, 0)

    assert attacker.types == ["ノーマル", "くさ"]


def test_ミルクのみ_HPが満タンのとき失敗する():
    """ミルクのみ: HPが満タンのとき失敗してHP変化なし。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ミルクのみ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    assert attacker.hp == attacker.max_hp
    t.run_move(battle, 0)
    assert attacker.hp == attacker.max_hp
    assert battle.move_executor.move_success is False


def test_ミルクのみ_HP不満のとき最大HPの半分回復する():
    """ミルクのみ: HPが満タンでないとき最大HPの1/2を回復する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ミルクのみ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)
    assert attacker.hp == 1 + int(attacker.max_hp * 1 / 2)


def test_ミルクのみ_マジックコートで跳ね返されない():
    """ミルクのみ: 自分を対象とする技のため、相手のマジックコートで跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ミルクのみ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
    )
    attacker, defender = battle.actives
    attacker.hp = 1
    defender_hp = defender.hp
    t.run_move(battle, 0)
    assert attacker.hp > 1
    assert defender.hp == defender_hp


def test_ミルクのみ_まもるで防がれない():
    """ミルクのみ: 自分を対象とする技のため、相手のまもるで防がれない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ミルクのみ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)
    assert attacker.hp > 1


def test_みをけずる_3ランクすべて上限なら技が失敗しHPも減らない():
    """みをけずる: こうげき・とくこう・すばやさが全て既に+6の場合、ランクは変化せず
    技自体が失敗する。HPも消費されない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みをけずる"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.boosts["atk"] = 6
    attacker.boosts["spa"] = 6
    attacker.boosts["spe"] = 6
    max_hp = attacker.max_hp
    t.run_move(battle, 0)

    assert attacker.boosts["atk"] == 6
    assert attacker.boosts["spa"] == 6
    assert attacker.boosts["spe"] == 6
    assert attacker.hp == max_hp
    assert battle.move_executor.move_success is False


def test_みをけずる_HPがちょうど半分なら失敗する():
    """みをけずる: HPがちょうど最大HPの半分のとき失敗し、能力・HPともに変化しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みをけずる"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.hp = attacker.max_hp // 2
    hp_before = attacker.hp
    t.run_move(battle, 0)

    assert attacker.boosts["atk"] == 0
    assert attacker.boosts["spa"] == 0
    assert attacker.boosts["spe"] == 0
    assert attacker.hp == hp_before
    assert battle.move_executor.move_applied is False


def test_みをけずる_HPが半分未満なら失敗する():
    """みをけずる: HPが最大HPの半分未満のとき失敗し、能力・HPともに変化しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みをけずる"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)

    assert attacker.boosts["atk"] == 0
    assert attacker.boosts["spa"] == 0
    assert attacker.boosts["spe"] == 0
    assert attacker.hp == 1
    assert battle.move_executor.move_applied is False


def test_みをけずる_HP半分超なら能力上昇しHPが半分減る():
    """みをけずる: HPが最大HPの半分を超えているとき、こうげき・とくこう・すばやさが+2され、
    最大HPの半分（切り捨て）が消費される。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みをけずる"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    max_hp = attacker.max_hp
    t.run_move(battle, 0)

    assert attacker.boosts["atk"] == 2
    assert attacker.boosts["spa"] == 2
    assert attacker.boosts["spe"] == 2
    assert attacker.hp == max_hp - (max_hp // 2)
    assert battle.move_executor.move_applied is True


def test_みをけずる_一部のランクのみ上限なら残りが上昇しHPが減る():
    """みをけずる: 一部のランクのみ+6でも、他のランクが変化可能であればそのランクが上昇し、
    HPは通常通り消費される。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みをけずる"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.boosts["atk"] = 6
    max_hp = attacker.max_hp
    t.run_move(battle, 0)

    assert attacker.boosts["atk"] == 6
    assert attacker.boosts["spa"] == 2
    assert attacker.boosts["spe"] == 2
    assert attacker.hp == max_hp - (max_hp // 2)
    assert battle.move_executor.move_applied is True


@pytest.mark.parametrize(
    "spa_init,spd_init,spa_exp,spd_exp",
    [
        # 通常: C+1、D+1
        (0, 0, 1, 1),
        # とくこう上限: Cはキャップ、Dは+1
        (6, 0, 6, 1),
        # とくぼう上限: Dはキャップ、Cは+1
        (0, 6, 1, 6),
        # 両方上限: どちらも変化できないので失敗（変化なし）
        (6, 6, 6, 6),
        # 両方上限まで1段階: どちらも上限ぴったりになる
        (5, 5, 6, 6),
        # 最低ランクから上昇
        (-6, -6, -5, -5),
    ],
)
def test_めいそう_発動前後のランク変化(spa_init, spd_init, spa_exp, spd_exp):
    """めいそう: 発動前後のとくこう・とくぼうランクの変化を網羅的に確認する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["めいそう"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.boosts["spa"] = spa_init
    attacker.boosts["spd"] = spd_init
    t.run_move(battle, 0)

    assert attacker.boosts["spa"] == spa_exp
    assert attacker.boosts["spd"] == spd_exp


def test_メロメロ_すでにメロメロ状態なら失敗():
    """メロメロ: 相手がすでにメロメロ状態なら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["メロメロ"], gender="male")],
        team1=[Pokemon("カビゴン", gender="female")],
        volatile1={"メロメロ": 1},
        accuracy=100,
    )
    defender = battle.actives[1]
    old_count = defender.volatiles["メロメロ"].count
    t.run_move(battle, 0)

    assert defender.has_volatile("メロメロ")
    assert defender.volatiles["メロメロ"].count == old_count


def test_メロメロ_みがわり状態の相手にも効果が発動する():
    """メロメロ: bypass_substituteフラグを持つため、みがわり状態の相手にも効果が発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["メロメロ"], gender="male")],
        team1=[Pokemon("カビゴン", gender="female")],
        volatile1={"みがわり": 1},
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_volatile("みがわり")
    assert defender.has_volatile("メロメロ")


@pytest.mark.parametrize("a_gender,d_gender,expected", [
    ("male", "female", True),   # 異性→成功
    ("female", "male", True),   # 異性→成功
    ("male", "male", False),  # 同性→失敗
    ("female", "female", False),  # 同性→失敗
    ("male", "",    False),  # 相手が無性→失敗
    ("",    "female", False),  # 使用者が無性→失敗
])
def test_メロメロ_性別の組み合わせ(a_gender, d_gender, expected):
    """メロメロ: 異性なら付与、同性・無性なら失敗"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["メロメロ"], gender=a_gender)],
        team1=[Pokemon("カビゴン", gender=d_gender)],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_volatile("メロメロ") == expected


def test_もえあがるいかり_ひるみが発動する():
    """もえあがるいかり: 20%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ゾロアーク", move_names=["もえあがるいかり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_もりののろい_くさタイプが付与される():
    """もりののろい: 使用後に defender が「くさ」タイプになること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["もりののろい"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    assert not defender.has_type("くさ")
    t.run_move(battle, 0)

    assert defender.has_type("くさ")


def test_もりののろい_すでにくさタイプなら失敗():
    """もりののろい: 相手がすでにくさタイプなら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["もりののろい"])],
        team1=[Pokemon("フシギバナ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    # くさタイプには付与されない
    assert not defender.has_volatile("もりののろい")


def test_もりののろい_テラスタル中の相手には失敗する():
    """もりののろい: テラスタルしている相手には失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["もりののろい"])],
        team1=[Pokemon("カビゴン", tera_type="ほのお")],
        accuracy=100,
    )
    defender = battle.actives[1]
    # テラスタル状態にする
    defender.is_terastallized = True
    assert defender.active_tera_type == "ほのお"
    t.run_move(battle, 0)

    # 技自体が失敗し、volatile は付与されない
    assert not defender.has_volatile("もりののろい")
    assert defender.types == ["ほのお"]


def test_もりののろい_もりののろい状態を付与する():
    """もりののろい: 相手にもりののろい状態を付与する（くさタイプが追加される）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["もりののろい"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_volatile("もりののろい")


def test_もりののろい_交代後にくさタイプがリセットされる():
    """もりののろい: 交代後に added_types がリセットされること"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["もりののろい"])],
        team1=[Pokemon("カビゴン"), Pokemon("ヤドラン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.has_type("くさ")

    # 交代後はくさタイプが消えること
    t.run_switch(battle, 1, 1)
    assert not defender.has_type("くさ")
    assert not defender.has_volatile("もりののろい")
