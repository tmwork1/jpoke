"""変化技ハンドラの単体テスト（あ行）。"""

import pytest
from jpoke import Pokemon
from .. import test_utils as t


def test_アイアンヘッド_ひるみが発動しない():
    """アイアンヘッド: 確率外（70%以上）ではひるみを付与しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ドサイドン", move_names=["アイアンヘッド"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.5)
    t.run_move(battle, 0)
    assert not battle.actives[1].has_volatile("ひるみ")


def test_アイアンヘッド_ひるみが発動する():
    """アイアンヘッド: 30%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ドサイドン", move_names=["アイアンヘッド"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_アクアリング_揮発性状態が付与される():
    """アクアリング: 使用するとアクアリング揮発性状態が付与される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["アクアリング"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.has_volatile("アクアリング")


def test_あくのはどう_ひるみが発動する():
    """あくのはどう: 20%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["あくのはどう"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_あくび_すでにねむけ状態なら失敗():
    """あくび: 対象がすでにねむけ状態なら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あくび"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"ねむけ": 1},
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)

    # ねむけは継続したまま（2つ目のねむけは付かない）
    assert defender.has_volatile("ねむけ")


def test_あくび_すでに状態異常なら失敗():
    """あくび: 対象がすでに状態異常を持っているなら失敗する。
    状態異常による揮発状態のブロックなので追加検証している。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あくび"])],
        team1=[Pokemon("カビゴン")],
        ailment1=("まひ", None),
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)

    assert not defender.has_volatile("ねむけ")
    assert defender.has_ailment("まひ")


def test_あくび_ねむけ付与():
    """あくび: 相手をねむけ状態にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あくび"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)

    assert defender.has_volatile("ねむけ")
    assert not defender.has_ailment("ねむり")


def test_あくび_使用後2回のターン終了でねむり状態になる():
    """あくび: 使用したターンではねむらず、次のターン終了時にねむり状態になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あくび"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)

    assert defender.has_volatile("ねむけ")
    assert not defender.has_ailment("ねむり")

    # 使用したターンの終了ではまだねむらない
    t.end_turn(battle)
    assert defender.has_volatile("ねむけ")
    assert not defender.has_ailment("ねむり")

    # 次のターンの終了でねむり状態になる
    t.end_turn(battle)
    assert not defender.has_volatile("ねむけ")
    assert defender.has_ailment("ねむり")


def test_あくまのキッス_ねむり付与():
    """あくまのキッス: 相手をねむり状態に直接する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あくまのキッス"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)

    assert defender.has_ailment("ねむり")


def test_あさのひざし_マジックコートで跳ね返されない():
    """あさのひざし: 自分を対象とする技のため、相手のマジックコートで跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あさのひざし"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
    )
    attacker, defender = battle.actives
    attacker.hp = 1
    defender_hp = defender.hp
    t.run_move(battle, 0)
    assert attacker.hp > 1
    assert defender.hp == defender_hp


def test_あさのひざし_まもるで防がれない():
    """あさのひざし: 自分を対象とする技のため、相手のまもるで防がれない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あさのひざし"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)
    assert attacker.hp > 1


def test_あさのひざし_まんたんなら失敗():
    """あさのひざし: HPが最大値のときは失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あさのひざし"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    assert attacker.hp == attacker.max_hp
    t.run_move(battle, 0)
    assert attacker.hp == attacker.max_hp


@pytest.mark.parametrize("weather_arg,numerator,denominator", [
    (None,              1, 2),  # 通常天候: 1/2 回復
    (("あめ",      5), 1, 4),  # あめ: 1/4 回復
    (("おおあめ", 99), 1, 4),  # おおあめ: 1/4 回復
    (("おおひでり", 99), 2, 3),  # おおひでり: 2/3 回復
    (("すなあらし", 99), 1, 4),  # すなあらし: 1/4 回復
    (("はれ",      5), 2, 3),  # はれ: 2/3 回復
    (("ゆき",      5), 1, 4),  # ゆき: 1/4 回復
])
def test_あさのひざし_天候別回復量(weather_arg, numerator, denominator):
    """あさのひざし: 天候ごとに回復量が変わる（通常1/2, はれ/おおひでり2/3, それ以外1/4）"""
    kwargs = {}
    if weather_arg is not None:
        kwargs["weather"] = weather_arg
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あさのひざし"])],
        team1=[Pokemon("カビゴン")],
        **kwargs,
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)
    assert attacker.hp == 1 + int(attacker.max_hp * numerator / denominator)


def test_あまいかおり_defenderの回避率が2段階下がる():
    """あまいかおり: 相手（defender）の回避率が2段階下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あまいかおり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.boosts["evasion"] == -2


def test_あまえる_defenderのこうげきが2段階下がる():
    """あまえる: 相手（defender）のこうげきが2段階下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あまえる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.boosts["atk"] == -2


def test_あまごい_天気があめになる():
    """あまごい: 使用後に天気があめになる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あまごい"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)
    assert battle.weather.name == "あめ"
    assert battle.weather.count == 5


def test_あやしいひかり_こんらん付与():
    """あやしいひかり: 相手をこんらん状態にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あやしいひかり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_volatile("こんらん")


def test_アロマセラピー_まもるで防がれない():
    """アロマセラピー: 味方全体を対象とする技のため、相手のまもるで防がれない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["アロマセラピー"])],
        team1=[Pokemon("ピカチュウ")],
        ailment0=("どく", None),
        volatile1={"まもる": 1},
    )
    attacker = battle.actives[0]
    assert attacker.ailment.is_active
    battle.test_option.trigger_ailment = False
    t.run_move(battle, 0)

    assert not attacker.ailment.is_active


@pytest.mark.parametrize("ailment_name", ["やけど", "まひ", "どく"])
def test_アロマセラピー_使用者の状態異常が回復される(ailment_name):
    """アロマセラピー: 使用者がやけど・まひ・どく等の状態異常のとき、使用後に回復される。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["アロマセラピー"])],
        team1=[Pokemon("ピカチュウ")],
        ailment0=(ailment_name, None),
    )
    attacker = battle.actives[0]
    assert attacker.ailment.is_active
    battle.test_option.trigger_ailment = False
    t.run_move(battle, 0)

    assert not attacker.ailment.is_active


def test_アロマセラピー_控えの状態異常も回復される():
    """アロマセラピー: 控えのポケモンが状態異常でも、使用後に回復される。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["アロマセラピー"]), Pokemon("イーブイ")],
        team1=[Pokemon("ピカチュウ")],
    )
    bench = battle.player_states[battle.players[0]].team[1]
    battle.ailment_manager.apply(bench, "まひ")
    assert bench.ailment.is_active
    t.run_move(battle, 0)

    assert not bench.ailment.is_active


def test_アロマセラピー_状態異常なしなら失敗():
    """アロマセラピー: チームに状態異常がいない場合は技が失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["アロマセラピー"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    assert not attacker.ailment.is_active
    t.run_move(battle, 0)

    # 状態異常なし → 技が失敗 → 状態に変化なし
    assert not attacker.ailment.is_active


def test_アンコール_PP消費後に失敗した技が対象になる():
    """アンコール: PPを消費した後に失敗した技も「最後にPPを消費した技」として
    判定の対象になる。

    ねむり状態でないポケモンがねごとを使うと、PPは消費されるが ON_TRY_MOVE_1 で
    失敗する。この場合も最後にPPを消費した技はねごと（non_encore ラベル持ち）で
    あるため、直後のアンコールは失敗する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ねごと", "たいあたり"])],
        team1=[Pokemon("カビゴン", move_names=["アンコール"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    negoto = mon.moves[0]

    t.run_move(battle, 0, 0)  # ピカチュウ: ねごと（ねむり状態でないため失敗する）
    assert negoto.pp == 11, "失敗してもねごとのPPは消費される"
    assert mon.pp_consumed_move.name == "ねごと"

    t.run_move(battle, 1, 0)  # カビゴン: アンコール（ねごとは non_encore のため失敗する）
    assert not mon.has_volatile("アンコール")


def test_アンコール_すでにアンコール状態の相手には失敗する():
    """アンコール: 相手がすでにアンコール状態の場合は失敗する（重複付与不可）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["アンコール"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 1)
    # 1回目: 成功
    t.run_move(battle, 0)
    assert defender.has_volatile("アンコール")
    old_count = defender.volatiles["アンコール"].count

    # 2回目: すでにアンコール状態なので失敗（count は変わらない）
    t.run_move(battle, 0)
    assert defender.volatiles["アンコール"].count == old_count


def test_アンコール_ねごとで実行された技には失敗する():
    """アンコール: 相手がねごとでサブ技を実行しても、最後にPPを消費した技は
    ねごと自身（non_encore ラベル持ち）として扱われるため失敗する。

    ねごとの実行中に last_move がサブ技（たいあたり）で上書きされても、
    サブ技はPPを消費しないため pp_consumed_move はねごと自身のままである
    ことを利用して判定する回帰テスト。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ねごと", "たいあたり"])],
        team1=[Pokemon("カビゴン", move_names=["アンコール"])],
        ailment0=("ねむり", 3),
        accuracy=100,
    )
    mon = battle.actives[0]

    t.run_move(battle, 0, 0)  # ピカチュウ: ねごと（候補はたいあたりのみ）
    assert mon.selected_move.name == "ねごと"
    assert mon.last_move.name == "たいあたり"
    assert mon.pp_consumed_move.name == "ねごと"

    t.run_move(battle, 1, 0)  # カビゴン: アンコール（ねごとは non_encore のため失敗する）
    assert not mon.has_volatile("アンコール")


def test_アンコール_成功してアンコール揮発状態が付与される():
    """アンコール: 相手が技を使った後に使うとアンコール揮発状態が付与される。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["アンコール"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 1)
    assert defender.last_move.name == "たいあたり"

    t.run_move(battle, 0)
    assert defender.has_volatile("アンコール")
    assert defender.volatiles["アンコール"].count == 3


def test_いえき_protectedフラグ持ちに失敗():
    """いえき: アイスフェイス（protectedフラグ持ち）の相手には失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いえき"])],
        team1=[Pokemon("カビゴン", ability_name="アイスフェイス")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert not defender.has_volatile("とくせいなし")


def test_いえき_うのミサイルには失敗():
    """いえき: うのミサイル（上書きできない特性のためprotectedフラグ持ち）の相手には失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いえき"])],
        team1=[Pokemon("カビゴン", ability_name="うのミサイル")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert not defender.has_volatile("とくせいなし")


def test_いえき_すでにとくせいなし状態の相手には失敗():
    """いえき: すでに「とくせいなし」状態の相手には失敗する（volatile_manager内部で処理）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いえき"])],
        team1=[Pokemon("カビゴン", ability_name="めんえき")],
        volatile1={"とくせいなし": 5},
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_volatile("とくせいなし")
    assert not defender.ability.enabled


def test_いえき_通常特性を持つ相手に成功():
    """いえき: 通常特性（せいでんき等）の相手に使うと「とくせいなし」揮発状態が付与される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いえき"])],
        team1=[Pokemon("カビゴン", ability_name="めんえき")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_volatile("とくせいなし")
    assert not defender.ability.enabled


def test_いたみわけ_HPを均等にする():
    """いたみわけ: 自分と相手のHPを足して2で割った値に均等化する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いたみわけ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    battle.modify_hp(attacker, -(attacker.max_hp - 10))
    defender_hp = defender.hp  # 満タン
    expected_hp = (10 + defender_hp) // 2
    t.run_move(battle, 0)

    assert attacker.hp == expected_hp
    assert defender.hp == expected_hp


def test_いたみわけ_最大HPを超えて回復しない():
    """いたみわけ: 均等化後の値が最大HPを超える場合は最大HPで頭打ちになる"""
    battle = t.start_battle(
        team0=[Pokemon("ピチュー", move_names=["いたみわけ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    assert (attacker.hp + defender.hp) // 2 > attacker.max_hp
    t.run_move(battle, 0)

    assert attacker.hp == attacker.max_hp


def test_いたみわけ_端数は切り捨てられる():
    """いたみわけ: HPの合計を2で割った際の端数は切り捨てられる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いたみわけ"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    battle.modify_hp(attacker, -(attacker.max_hp - 11))
    defender_hp = defender.hp  # 満タン
    expected_hp = (11 + defender_hp) // 2
    t.run_move(battle, 0)

    assert attacker.hp == expected_hp
    assert defender.hp == expected_hp


def test_いちゃもん_すでにいちゃもん状態の相手には失敗する():
    """いちゃもん: 相手がすでにいちゃもん状態の場合は失敗し、move_nameは変化しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いちゃもん"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり", "なきごえ"])],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 1)
    t.run_move(battle, 0)
    assert defender.has_volatile("いちゃもん")
    assert defender.volatiles["いちゃもん"].move_name == "たいあたり"

    # なきごえを選択して使用する（たいあたりはいちゃもんで禁止されているため）
    t.run_move(battle, 1, 1)
    # 2回目のいちゃもんは失敗するため、move_nameは最初のまま
    t.run_move(battle, 0)
    assert defender.volatiles["いちゃもん"].move_name == "たいあたり"


def test_いちゃもん_まもる連続使用失敗直後でも直前の選択技をロックする():
    """いちゃもん: 相手がまもるを連続使用して2回目が失敗した直後でも、
    selected_move は連続使用失敗によって書き換えられないため、
    正しく直前に選択した「まもる」をロックできることを確認する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いちゃもん"])],
        team1=[Pokemon("カビゴン", move_names=["まもる", "たいあたり"])],
        accuracy=100,
    )
    defender = battle.actives[1]

    # 1ターン目: まもる成功
    t.run_move(battle, 1, 0)
    assert battle.move_executor.move_success
    t.end_turn(battle)

    # 2ターン目: まもる失敗（連続使用）。selected_move は「まもる」のまま保持される
    t.run_move(battle, 1, 0)
    assert not battle.move_executor.move_success
    assert defender.selected_move is not None
    assert defender.selected_move.name == "まもる"

    # 攻撃側がいちゃもんを使用 → 直前に選択した「まもる」が正しくロックされる
    t.run_move(battle, 0)
    assert defender.has_volatile("いちゃもん")
    assert defender.volatiles["いちゃもん"].move_name == "まもる"


def test_いちゃもん_使用で相手にいちゃもん状態が付与される():
    """いちゃもん: 相手が技を使った後に使うといちゃもん状態が付与され、直前に使用した技が記録される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いちゃもん"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 1)
    assert defender.last_move.name == "たいあたり"

    t.run_move(battle, 0)
    assert defender.has_volatile("いちゃもん")
    assert defender.volatiles["いちゃもん"].move_name == "たいあたり"


def test_いちゃもん_未行動の相手にも成功する():
    """いちゃもん: 相手がまだ技を使っていない（last_move が None）場合でも付与に成功する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いちゃもん"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    assert defender.last_move is None

    t.run_move(battle, 0)
    assert defender.has_volatile("いちゃもん")
    assert defender.volatiles["いちゃもん"].move_name == ""


def test_いちゃもん_直前に使用した技が選択肢から除外される():
    """いちゃもん: 付与後、相手は直前に使用した技をコマンドとして選択できなくなる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いちゃもん"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり", "なきごえ"])],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 1)
    t.run_move(battle, 0)
    assert defender.has_volatile("いちゃもん")

    with battle.phase_context("action"):
        commands = battle.get_available_commands(battle.players[1])
    move_indices = {cmd.index for cmd in commands if cmd.is_type("move")}
    assert move_indices == {1}


def test_いとをはく_すばやさ2段階下がる():
    """いとをはく: 相手のすばやさランクが2段階下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いとをはく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.boosts["spe"] == -2


def test_いのちのしずく_HPが4分の1回復する():
    """いのちのしずく: HPが減っているとき最大HPの1/4（四捨五入）を回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いのちのしずく"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)

    # ピカチュウの最大HPは110のため、110/4=27.5を四捨五入して28回復する
    assert attacker.max_hp == 110
    assert attacker.hp == 1 + 28


def test_いのちのしずく_HP満タンなら失敗する():
    """いのちのしずく: HPが満タンのとき技が失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いのちのしずく"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    assert attacker.hp == attacker.max_hp
    t.run_move(battle, 0)

    assert attacker.hp == attacker.max_hp


def test_いのちのしずく_かいふくふうじ中は回復が無効化される():
    """いのちのしずく: かいふくふうじ状態のとき回復が無効化される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いのちのしずく"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"かいふくふうじ": 3},
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)

    assert attacker.hp == 1


def test_いのちのしずく_回復量の端数は四捨五入で切り上げになる():
    """いのちのしずく: 端数は四捨五入で丸める。

    公式Wiki「技の仕様」節によると、同じ1/4回復技でも `ジャングルヒール` `みかづきのいのり`
    は切り捨てだが、本技のみ四捨五入になる。ピカチュウの最大HPは110のため、
    110/4=27.5となり、切り捨てなら27回復だが、四捨五入では28回復になる
    （単純な切り捨て(int())なら27になってしまうバグを検出する）。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いのちのしずく"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    assert attacker.max_hp == 110
    attacker.hp = 1
    t.run_move(battle, 0)

    assert attacker.hp == 1 + 28


def test_いのちのしずく_相手のまもるで防がれない():
    """いのちのしずく: 自分を対象とする技のため、相手のまもるで防がれない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いのちのしずく"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)

    assert attacker.hp > 1


def test_いのちのしずく_相手のよびみずに引き寄せられず回復できる():
    """いのちのしずく: みずタイプ技だが自分を対象とする技のため、
    相手がよびみずを持っていても特性に引き寄せられることなく回復できる。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いのちのしずく"])],
        team1=[Pokemon("ラプラス", ability_name="よびみず")],
    )
    attacker = battle.actives[0]
    attacker.hp = 1
    t.run_move(battle, 0)

    assert attacker.hp > 1


def test_いばる_こうげき2段階上がりこんらん付与():
    """いばる: 相手のこうげきが2段階上がり、こんらん状態になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いばる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.boosts["atk"] == 2
    assert defender.has_volatile("こんらん")
    assert battle.move_executor.move_applied is True


def test_いばる_こうげき最大でもこんらん未付与なら成功():
    """いばる: こうげきが+6でもこんらん状態でなければ技は成功しこんらんを付与する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いばる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.modify_stats(defender, {"atk": 6}, source=battle.actives[0])
    t.run_move(battle, 0)

    assert defender.boosts["atk"] == 6
    assert defender.has_volatile("こんらん")
    assert battle.move_executor.move_applied is True


def test_いばる_こんらん済みでもこうげき最大未満なら成功():
    """いばる: こんらん済みでもこうげきが+6未満であればこうげきアップのみ適用され技は成功する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いばる"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"こんらん": 3},
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.boosts["atk"] == 2
    assert battle.move_executor.move_applied is True


def test_いばる_すでにこんらんかつこうげき最大なら失敗():
    """いばる: こうげきが+6かつこんらん済みなら技が失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いばる"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"こんらん": 3},
        accuracy=100,
    )
    defender = battle.actives[1]
    # こうげきを+6にする
    battle.modify_stats(defender, {"atk": 6}, source=battle.actives[0])
    t.run_move(battle, 0)

    # こうげきは変化せず、こんらんも新たに付与されない
    assert defender.boosts["atk"] == 6
    assert battle.move_executor.move_applied is False


def test_いびき_ひるみが発動する():
    """いびき: 30%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["いびき"])],
        team1=[Pokemon("ピカチュウ")],
        ailment0=("ねむり", 3),
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_いやしのすず_まもるで防がれない():
    """いやしのすず: 味方全体を対象とする技のため、相手のまもるで防がれない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["いやしのすず"])],
        team1=[Pokemon("ピカチュウ")],
        ailment0=("どく", None),
        volatile1={"まもる": 1},
    )
    attacker = battle.actives[0]
    assert attacker.ailment.is_active
    t.run_move(battle, 0)

    assert not attacker.ailment.is_active


def test_いやしのすず_控えの状態異常も回復する():
    """いやしのすず: 選出チームの控えポケモンの状態異常も回復する"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["いやしのすず"]), Pokemon("コラッタ")],
        team1=[Pokemon("ピカチュウ")],
    )
    bench = battle.player_states[battle.players[0]].team[1]
    battle.ailment_manager.apply(bench, "まひ")
    assert bench.ailment.is_active
    t.run_move(battle, 0)

    assert not bench.ailment.is_active


def test_いやしのすず_状態異常なしなら失敗():
    """いやしのすず: チームに状態異常がいない場合は技が失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["いやしのすず"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    assert not attacker.ailment.is_active
    t.run_move(battle, 0)

    # 状態異常なし → 技が失敗 → 状態に変化なし
    assert not attacker.ailment.is_active


@pytest.mark.parametrize("ailment_name", ["どく", "まひ", "やけど"])
def test_いやしのすず_状態異常を回復する(ailment_name):
    """いやしのすず: 使用者が状態異常のとき回復される"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["いやしのすず"])],
        team1=[Pokemon("ピカチュウ")],
        ailment0=(ailment_name, None),
    )
    attacker = battle.actives[0]
    assert attacker.ailment.is_active
    battle.test_option.trigger_ailment = False
    t.run_move(battle, 0)

    assert not attacker.ailment.is_active


def test_いやしのすず_相手のぼうおんの影響を受けない():
    """いやしのすず: 相手を対象とする技ではないため、相手のぼうおんは無関係"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["いやしのすず"])],
        team1=[Pokemon("ピカチュウ", ability_name="ぼうおん")],
        ailment0=("どく", None),
    )
    attacker = battle.actives[0]
    assert attacker.ailment.is_active
    t.run_move(battle, 0)

    assert not attacker.ailment.is_active


def test_いやしのねがい_HP満タンかつ状態異常なしなら発動しない():
    """いやしのねがい: 死に出しポケモンのHPが満タンで状態異常もない場合、
    サイドフィールドは消えず（保留されたまま）ポケモンの状態に変化がない（第八世代以降仕様）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いやしのねがい"]), Pokemon("カビゴン")],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)

    # HP満タン・状態異常なしのベンチポケモンを死に出し
    bench = battle.player_states[battle.players[0]].team[1]
    assert bench.hp == bench.max_hp
    assert not bench.ailment.is_active
    battle.switch_manager.run_faint_switch()

    # フィールドは保留されたまま（解除されない）
    side = battle.get_side(bench)
    assert side.get("いやしのねがい").is_active
    # HPも変化なし
    assert bench.hp == bench.max_hp


def test_いやしのねがい_HP満タンでも状態異常が回復される():
    """いやしのねがい: HP が満タンのポケモンに死に出ししたとき、HP は変化せず状態異常だけ回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いやしのねがい"]), Pokemon("カビゴン")],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)

    bench = battle.player_states[battle.players[0]].team[1]
    battle.ailment_manager.apply(bench, "まひ")
    assert bench.ailment.is_active
    assert bench.hp == bench.max_hp

    battle.switch_manager.run_faint_switch()

    assert bench.hp == bench.max_hp
    assert not bench.ailment.is_active
    side = battle.get_side(bench)
    assert not side.get("いやしのねがい").is_active


def test_いやしのねがい_使用者がひんしになりサイドフィールドが設置される():
    """いやしのねがい: 使用後に使用者がひんし状態になり、自陣営にサイドフィールドが設置される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いやしのねがい"]), Pokemon("カビゴン")],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.fainted
    side = battle.get_side(attacker)
    assert side.get("いやしのねがい").is_active


def test_いやしのねがい_控えがいないと失敗し使用者はひんしにならない():
    """いやしのねがい: 控えのポケモンがいない場合は失敗し、使用者はひんしにならない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いやしのねがい"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert not attacker.fainted
    side = battle.get_side(attacker)
    assert not side.get("いやしのねがい").is_active


def test_いやしのねがい_死に出しポケモンのHPが全回復かつ状態異常が解除される():
    """いやしのねがい: 死に出しのポケモンのHPが全回復され、まひ状態異常も解除される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いやしのねがい"]), Pokemon("カビゴン")],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)

    # battle 内部の PlayerState のチームからベンチポケモンを取得する
    bench = battle.player_states[battle.players[0]].team[1]
    bench.hp = 1
    battle.ailment_manager.apply(bench, "まひ")
    assert bench.ailment.is_active
    battle.switch_manager.run_faint_switch()

    assert bench.hp == bench.max_hp
    assert not bench.ailment.is_active
    side = battle.get_side(bench)
    assert not side.get("いやしのねがい").is_active


def test_いやしのねがい_自分対象のためまもるで防がれない():
    """いやしのねがい: 自分を対象とする技のため、相手のまもるがあっても効果は発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いやしのねがい"]), Pokemon("カビゴン")],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.fainted
    side = battle.get_side(attacker)
    assert side.get("いやしのねがい").is_active


def test_いやしのはどう_HPが半分回復する():
    """いやしのはどう: 相手のHPが減っているとき相手の最大HPの1/2を回復する（端数は切り上げ）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いやしのはどう"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    defender.hp = 1
    t.run_move(battle, 0)

    assert defender.hp == 1 + (defender.max_hp + 1) // 2


def test_いやしのはどう_HP満タンなら失敗する():
    """いやしのはどう: 相手のHPが満タンのとき技が失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いやしのはどう"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    assert defender.hp == defender.max_hp
    t.run_move(battle, 0)

    assert defender.hp == defender.max_hp


def test_いやしのはどう_かいふくふうじ中は回復が無効化される():
    """いやしのはどう: かいふくふうじ状態の相手には回復が無効化される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いやしのはどう"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"かいふくふうじ": 3},
    )
    defender = battle.actives[1]
    defender.hp = 1
    t.run_move(battle, 0)

    assert defender.hp == 1


def test_いやしのはどう_メガランチャーで回復量が3_4になる():
    """いやしのはどう: 使用者がメガランチャーを持つ場合、回復量が最大HPの3/4になる"""
    from jpoke.utils.math import round_half_down

    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="メガランチャー", move_names=["いやしのはどう"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    defender.hp = 1
    t.run_move(battle, 0)

    assert defender.hp == 1 + round_half_down(defender.max_hp * 3 / 4)


def test_いやなおと_defenderのぼうぎょが2段階下がる():
    """いやなおと: 相手（defender）のぼうぎょが2段階下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いやなおと"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.boosts["def"] == -2


def test_いやなおと_みがわりを貫通してぼうぎょが下がる():
    """いやなおと: soundフラグを持つため、みがわり状態の相手にも効果が発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いやなおと"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "みがわり", hp=999)
    t.run_move(battle, 0)

    assert defender.boosts["def"] == -2
    assert defender.volatiles["みがわり"].hp == 999


def test_いわなだれ_ひるみが発動する():
    """いわなだれ: 30%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("イワーク", move_names=["いわなだれ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_うそなき_defenderのとくぼうが2段階下がる():
    """うそなき: 相手（defender）のとくぼうが2段階下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["うそなき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.boosts["spd"] == -2


def test_うたう_ねむり付与():
    """うたう: 相手をねむり状態にする（accuracy=100で固定）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["うたう"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.has_ailment("ねむり")


def test_うつしえ_かがくへんかガスで無効化された相手の特性は元の特性がコピーされる():
    """うつしえ: 相手の特性がかがくへんかガスで無効化されていても、
    とくせいなしとは異なり本来の特性（base_name）がコピーされる。"""
    battle = t.start_battle(
        team0=[Pokemon("ドガース", ability_name="かがくへんかガス", move_names=["うつしえ"])],
        team1=[Pokemon("カビゴン", ability_name="めんえき")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    assert not defender.ability.enabled

    t.run_move(battle, 0)

    assert attacker.ability.name == "めんえき"
    # 使用者自身の特性がかがくへんかガスでなくなったのでガスの効果が切れ、
    # 相手の特性（コピー元と同じめんえき）が有効に戻る
    assert defender.ability.enabled


def test_うつしえ_まもる状態の相手にも効果が発動する():
    """うつしえ: unprotectableフラグを持つため、まもる状態の相手にも特性コピーが発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいでんき", move_names=["うつしえ"])],
        team1=[Pokemon("カビゴン", ability_name="あついしぼう")],
        volatile1={"まもる": 1},
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.ability.name == "あついしぼう"


def test_うつしえ_みがわり状態の相手には防がれる():
    """うつしえ: みがわり状態の相手には効果が防がれる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいでんき", move_names=["うつしえ"])],
        team1=[Pokemon("カビゴン", ability_name="あついしぼう")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "みがわり", hp=999)
    t.run_move(battle, 0)

    assert attacker.ability.name == "せいでんき"


def test_うつしえ_交代後に元の特性に戻る():
    """うつしえ: 特性をコピーした使用者が交代すると元の特性に戻る"""
    battle = t.start_battle(
        team0=[
            Pokemon("ピカチュウ", ability_name="せいでんき", move_names=["うつしえ"]),
            Pokemon("ラッキー", ability_name="しぜんかいふく"),
        ],
        team1=[Pokemon("カビゴン", ability_name="めんえき")],
        accuracy=100,
    )
    attacker_before = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker_before.ability.name == "めんえき"

    # 交代後は元の特性に戻る
    t.run_switch(battle, 0, 1)
    assert attacker_before.ability.name == "せいでんき"


def test_うつしえ_使用者と対象の特性がすでに同じなら失敗():
    """うつしえ: 使用者と対象の特性がすでに同じ場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいでんき", move_names=["うつしえ"])],
        team1=[Pokemon("カビゴン", ability_name="せいでんき")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.ability.name == "せいでんき"


def test_うつしえ_使用者の特性がprotectedなら失敗():
    """うつしえ: 使用者の特性がprotectedフラグ持ち（上書きできない特性）なら失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="アイスフェイス", move_names=["うつしえ"])],
        team1=[Pokemon("ピカチュウ", ability_name="せいでんき")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert attacker.ability.name == "アイスフェイス"
    assert defender.ability.name == "せいでんき"


@pytest.mark.parametrize("d_ability", ["アイスフェイス", "イリュージョン"])
def test_うつしえ_対象がuncopyableフラグ持ちなら失敗(d_ability):
    """うつしえ: 対象がuncopyableフラグ持ち（コピーできない特性）の場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいでんき", move_names=["うつしえ"])],
        team1=[Pokemon("カビゴン", ability_name=d_ability)],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    # 使用者の特性は変化しない
    assert attacker.ability.name == "せいでんき"


def test_うつしえ_相手の特性が使用者にコピーされる():
    """うつしえ: 使用すると使用者の特性が相手と同じ特性に変わる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいでんき", move_names=["うつしえ"])],
        team1=[Pokemon("カビゴン", ability_name="めんえき")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert attacker.ability.name == "めんえき"
    # 対象側の特性は変化しない
    assert defender.ability.name == "めんえき"


def test_うらみ_ねごと経由ではねごとのPPが減る():
    """うらみ: 相手がねごとでサブ技を実行した場合、減るのはサブ技ではなく
    最後にPPを消費したねごと自身のPPである（サブ技はPPを消費しないため対象にならない）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["うらみ"])],
        team1=[Pokemon("カビゴン", move_names=["ねごと", "たいあたり"])],
        ailment1=("ねむり", 3),
        accuracy=100,
    )
    defender = battle.actives[1]
    negoto = defender.moves[0]
    taiatari = defender.moves[1]

    t.run_move(battle, 1, 0)  # カビゴン: ねごと（候補はたいあたりのみ）
    assert negoto.pp == 11, "ねごと自身のPPは1消費される"
    assert taiatari.pp == 35, "サブ技のPPは消費されない"

    t.run_move(battle, 0)  # ピカチュウ: うらみ

    assert negoto.pp == 11 - 4, "うらみで減るのはねごとのPP"
    assert taiatari.pp == 35, "サブ技のPPは変化しない"


def test_うらみ_みがわり状態の相手にも効果がある():
    """うらみ: みがわり状態の相手にも貫通して効果を発揮する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["うらみ"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        volatile1={"みがわり": 1},
        accuracy=100,
    )
    defender = battle.actives[1]
    move = defender.moves[0]
    # カビゴンに技を使わせて last_move を設定する
    t.run_move(battle, 1)
    pp_after_use = move.pp
    # うらみを使う（みがわりがあっても貫通する）
    t.run_move(battle, 0)

    assert move.pp == pp_after_use - 4


def test_うらみ_相手が技を使っていない場合は失敗():
    """うらみ: 相手がまだ技を使っていない場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["うらみ"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender = battle.actives[1]
    move = defender.moves[0]
    pp_before = move.pp
    # カビゴンはまだ技を使っていないのでうらみは失敗するはず
    t.run_move(battle, 0)

    # PPは変化しない
    assert move.pp == pp_before


def test_うらみ_相手のPPがすでに0の技には失敗():
    """うらみ: 相手の直前の技のPPがすでに0の場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["うらみ"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender = battle.actives[1]
    move = defender.moves[0]
    # カビゴンに技を使わせて last_move を設定したうえでPPを0にする
    t.run_move(battle, 1)
    move.modify_pp(-move.pp)
    assert move.pp == 0

    # うらみは失敗し、PPは0のまま変化しない
    t.run_move(battle, 0)
    assert move.pp == 0


def test_うらみ_相手の技のPPが4減る():
    """うらみ: 相手が前のターンに使った技のPPが4減る"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["うらみ"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender = battle.actives[1]
    move = defender.moves[0]
    # カビゴンに技を使わせて last_move を設定する
    t.run_move(battle, 1)
    pp_after_use = move.pp
    # うらみを使う
    t.run_move(battle, 0)

    assert move.pp == pp_after_use - 4


def test_うらみ_相手の直前の技がわるあがきの場合は失敗():
    """うらみ: 相手の直前の技がわるあがきの場合は失敗する（PPが無限のため対象外）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["うらみ"])],
        team1=[Pokemon("カビゴン", move_names=["わるあがき"])],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 1)
    assert defender.last_move.name == "わるあがき"
    pp_before = defender.last_move.pp

    # うらみは失敗する（わるあがきのPPは変化しない）
    t.run_move(battle, 0)
    assert defender.last_move.pp == pp_before


def test_エアスラッシュ_ひるみが発動する():
    """エアスラッシュ: 30%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピジョット", move_names=["エアスラッシュ"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_エレキフィールド_すでに同じ地形なら失敗():
    """エレキフィールド: すでにエレキフィールドが有効なら失敗（再設置されない）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["エレキフィールド"])],
        team1=[Pokemon("カビゴン")],
        terrain=("エレキフィールド", 3),
    )
    t.run_move(battle, 0)

    # カウントは変わらない
    assert battle.terrain.name == "エレキフィールド"
    assert battle.terrain.count == 3


def test_エレキフィールド_地形がエレキフィールドになる():
    """エレキフィールド: 使用後に地形がエレキフィールドになり5ターン継続する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["エレキフィールド"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)
    assert battle.terrain.name == "エレキフィールド"
    assert battle.terrain.count == 5


def test_えんまく_相手の命中率1段階下がる():
    """えんまく: 相手の命中率ランクが1段階下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["えんまく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.boosts["accuracy"] == -1


def test_おいかぜ_すでにおいかぜなら失敗():
    """おいかぜ: すでにおいかぜが有効なら失敗（再設置されない）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おいかぜ"])],
        team1=[Pokemon("カビゴン")],
        side0={"おいかぜ": 3},
    )
    side = battle.get_side(battle.actives[0])
    t.run_move(battle, 0)

    # カウントは変わらない
    assert side.fields["おいかぜ"].is_active
    assert side.fields["おいかぜ"].count == 3


def test_おいかぜ_自陣営に4ターン設置される():
    """おいかぜ: 使用すると自陣営に4ターンのおいかぜが設置される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おいかぜ"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)

    side = battle.get_side(battle.actives[0])
    assert side.fields["おいかぜ"].is_active
    assert side.fields["おいかぜ"].count == 4


def test_おいわい_マジックコートで跳ね返されない():
    """おいわい: 自分を対象とする技のため、相手のマジックコートで跳ね返されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おいわい"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
    )
    attacker, defender = battle.actives
    attacker_hp = attacker.hp
    defender_hp = defender.hp
    t.run_move(battle, 0)

    assert battle.move_executor.move_applied
    assert attacker.hp == attacker_hp
    assert defender.hp == defender_hp


def test_おいわい_まもるで防がれない():
    """おいわい: 自分を対象とする技のため、相手のまもるに関係なく成功する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おいわい"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1},
    )
    t.run_move(battle, 0)

    assert battle.move_executor.move_applied


def test_おいわい_使用してもHPやランクなど戦闘状態が変化しない():
    """おいわい: 効果のないわざのため、使用してもHP・ランクに一切変化がない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おいわい"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    attacker_hp = attacker.hp
    defender_hp = defender.hp
    t.run_move(battle, 0)

    assert battle.move_executor.move_applied
    assert attacker.hp == attacker_hp
    assert defender.hp == defender_hp
    assert all(v == 0 for v in attacker.boosts.values())
    assert all(v == 0 for v in defender.boosts.values())


def test_おかたづけ_こうげきとすばやさが1段階ずつ上がる():
    """おかたづけ: 使用するとこうげきとすばやさが1段階ずつ上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おかたづけ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.boosts["atk"] == 1
    assert attacker.boosts["spe"] == 1


def test_おかたづけ_みがわりを除去する():
    """おかたづけ: 相手のみがわりを除去する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おかたづけ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"みがわり": 1},
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert not defender.has_volatile("みがわり")


def test_おかたづけ_ランクが最大でもみがわりを除去する():
    """おかたづけ: こうげき・すばやさがすでに最大でも、みがわりの除去効果は発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おかたづけ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"みがわり": 1},
    )
    attacker, defender = battle.actives
    attacker.boosts["atk"] = 6
    attacker.boosts["spe"] = 6
    t.run_move(battle, 0)

    assert not defender.has_volatile("みがわり")


@pytest.mark.parametrize("trap_name", [
    "まきびし",
    "どくびし",
    "ステルスロック",
    "ねばねばネット",
])
def test_おかたづけ_両陣営のトラップを除去する(trap_name):
    """おかたづけ: 自陣・相手陣営双方のトラップを除去する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おかたづけ"])],
        team1=[Pokemon("カビゴン")],
        side0={trap_name: 1},
        side1={trap_name: 1},
    )
    t.run_move(battle, 0)

    assert not battle.side_managers[0].fields[trap_name].is_active
    assert not battle.side_managers[1].fields[trap_name].is_active


def test_おかたづけ_相手陣営のまきびしを除去する():
    """おかたづけ: 相手陣営のまきびしを除去する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おかたづけ"])],
        team1=[Pokemon("カビゴン")],
        side1={"まきびし": 1},
    )
    foe_side = battle.get_side(battle.actives[1])
    assert foe_side.get("まきびし").is_active
    t.run_move(battle, 0)

    assert not foe_side.get("まきびし").is_active


def test_おかたづけ_自分のみがわりも除去する():
    """おかたづけ: 使用者自身のみがわりも除去する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おかたづけ"])],
        team1=[Pokemon("カビゴン")],
        volatile0={"みがわり": 1},
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert not attacker.has_volatile("みがわり")


def test_おきみやげ_クリアボディでランク低下が防がれても使用者はひんしになる():
    """おきみやげ: 相手がクリアボディでランク低下を防いでも使用者はひんしになる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おきみやげ"])],
        team1=[Pokemon("カビゴン", ability_name="クリアボディ")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)

    assert attacker.fainted
    assert defender.boosts["atk"] == 0
    assert defender.boosts["spa"] == 0


def test_おきみやげ_まもるで防がれると使用者はひんしにならない():
    """おきみやげ: 相手にまもるがかかっている場合、使用者はひんしにならない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おきみやげ"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"まもる": 1}
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)

    assert not attacker.fainted
    assert defender.boosts["atk"] == 0
    assert defender.boosts["spa"] == 0


def test_おきみやげ_使用者がひんしになる():
    """おきみやげ: 使用者がひんしになる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おきみやげ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)

    assert attacker.fainted
    assert defender.boosts["atk"] == -2
    assert defender.boosts["spa"] == -2


def test_おきみやげ_相手のランクが共に最低でも使用者はひんしになる():
    """おきみやげ: 相手のこうげき・とくこうランクが共に-6でランク低下が起きなくても使用者はひんしになる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おきみやげ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    defender.boosts["atk"] = -6
    defender.boosts["spa"] = -6
    t.run_move(battle, 0)

    assert attacker.fainted
    assert defender.boosts["atk"] == -6
    assert defender.boosts["spa"] == -6


def test_おたけび_こうげきとくこう1段階ずつ下がる():
    """おたけび: 相手のこうげきととくこうランクが1段階ずつ下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おたけび"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.boosts["atk"] == -1
    assert defender.boosts["spa"] == -1


def test_おたけび_みがわりを貫通してこうげきとくこうが下がる():
    """おたけび: soundフラグを持つため、みがわり状態の相手にも効果が発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おたけび"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "みがわり", hp=999)
    t.run_move(battle, 0)

    assert defender.boosts["atk"] == -1
    assert defender.boosts["spa"] == -1
    assert defender.volatiles["みがわり"].hp == 999


def test_おだてる_こんらん済みでもとくこう最大未満なら成功():
    """おだてる: こんらん済みでもとくこうが+6未満であればとくこうアップのみ適用され技は成功する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おだてる"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"こんらん": 3},
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.boosts["spa"] == 1
    assert battle.move_executor.move_applied is True


def test_おだてる_すでにこんらんかつとくこう最大なら失敗():
    """おだてる: とくこうが+6かつこんらん済みなら技が失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おだてる"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"こんらん": 3},
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.modify_stats(defender, {"spa": 6}, source=battle.actives[0])
    t.run_move(battle, 0)

    # とくこうは変化せず、こんらんも新たに付与されない
    assert defender.boosts["spa"] == 6
    assert battle.move_executor.move_applied is False


def test_おだてる_とくこう1段階上がりこんらん付与():
    """おだてる: 相手のとくこうが1段階上がり、こんらん状態になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おだてる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.boosts["spa"] == 1
    assert defender.has_volatile("こんらん")
    assert battle.move_executor.move_applied is True


def test_おだてる_とくこう最大でもこんらん未付与なら成功():
    """おだてる: とくこうが+6でもこんらん状態でなければ技は成功しこんらんを付与する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おだてる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    battle.modify_stats(defender, {"spa": 6}, source=battle.actives[0])
    t.run_move(battle, 0)

    assert defender.boosts["spa"] == 6
    assert defender.has_volatile("こんらん")
    assert battle.move_executor.move_applied is True


def test_おちゃかい_HP条件を満たす場合は効果を受けて回復する():
    """おちゃかい: HPが半分以下のときにオボンのみを強制消費すると、通常通りHPが回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おちゃかい"], item_name="オボンのみ")],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    attacker.hp = attacker.max_hp // 2
    t.run_move(battle, 0)

    assert attacker.hp == attacker.max_hp // 2 + attacker.max_hp // 4
    assert not attacker.item.is_berry()


def test_おちゃかい_きのみを持つポケモンがいなくても技は成功する():
    """おちゃかい: 場にきのみを持つポケモンが1体もいなくても技自体は成功する（失敗しない）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おちゃかい"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    move = attacker.moves[0]
    pp_before = move.pp
    t.run_move(battle, 0)

    # 失敗判定は行われないため通常通りPPが1消費される
    assert move.pp == pp_before - 1


def test_おちゃかい_姿を隠しているポケモンはきのみを消費しない():
    """おちゃかい: そらをとぶ等で姿を隠しているポケモンはきのみを消費しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おちゃかい"])],
        team1=[Pokemon("カビゴン", item_name="オボンのみ")],
    )
    defender = battle.actives[1]
    battle.volatile_manager.apply(defender, "そらをとぶ")
    t.run_move(battle, 0)

    assert defender.item.is_berry()


def test_おちゃかい_相手のきのみも消費される():
    """おちゃかい: 相手が持っているきのみも同時に強制消費される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おちゃかい"])],
        team1=[Pokemon("カビゴン", item_name="オボンのみ")],
    )
    defender = battle.actives[1]
    assert defender.item.is_berry()
    t.run_move(battle, 0)

    assert not defender.item.is_berry()


def test_おちゃかい_自分のきのみが消費される():
    """おちゃかい: 使用者が持っているきのみは、HP条件を満たしていなくても強制的に消費される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おちゃかい"], item_name="オボンのみ")],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    assert attacker.item.is_berry()
    t.run_move(battle, 0)

    assert not attacker.item.is_berry()


def test_おどろかす_ひるみが発動する():
    """おどろかす: 30%でひるみを付与する。"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", move_names=["おどろかす"])],
        team1=[Pokemon("ゼニガメ")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


def test_おにび_すでに状態異常なら失敗():
    """おにび: 対象がすでに状態異常を持っている場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おにび"])],
        team1=[Pokemon("カビゴン")],
        ailment1=("まひ", None),
        accuracy=100,
    )
    t.run_move(battle, 0)
    # まひのまま変わっていないことを確認
    assert battle.actives[1].ailment.name == "まひ"


def test_おにび_ほのおタイプには無効():
    """おにび: 対象がほのおタイプの場合は失敗する（やけど無効）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おにび"])],
        team1=[Pokemon("ヒトカゲ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert not battle.actives[1].ailment.is_active


def test_おにび_やけど付与():
    """おにび: 相手をやけど状態にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おにび"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "やけど"


def test_オーロラベール_ゆき中なら自陣営に設置される():
    """オーロラベール: ゆき天候中に使用すると自陣営に5ターンのオーロラベールが設置される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["オーロラベール"])],
        team1=[Pokemon("カビゴン")],
        weather=("ゆき", 5),
    )
    t.run_move(battle, 0)

    side = battle.get_side(battle.actives[0])
    assert side.fields["オーロラベール"].is_active
    assert side.fields["オーロラベール"].count == 5


def test_オーロラベール_ゆき以外では失敗():
    """オーロラベール: ゆき天候でない場合は失敗する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["オーロラベール"])],
        team1=[Pokemon("カビゴン")],
    )
    t.run_move(battle, 0)

    side = battle.get_side(battle.actives[0])
    assert not side.fields["オーロラベール"].is_active
