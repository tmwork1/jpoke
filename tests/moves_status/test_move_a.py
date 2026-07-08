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
    assert defender.rank["evasion"] == -2


def test_あまえる_defenderのこうげきが2段階下がる():
    """あまえる: 相手（defender）のこうげきが2段階下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あまえる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.rank["atk"] == -2


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


def test_アロマセラピー_状態異常なしでも失敗しない():
    """アロマセラピー: パーティ全員が状態異常でない場合でも技が失敗せず正常終了する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["アロマセラピー"])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    assert not attacker.ailment.is_active
    # 例外が発生せず正常完了することを確認する
    t.run_move(battle, 0)
    assert not attacker.ailment.is_active


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


def test_いちゃもん_使用で相手にいちゃもん状態が付与される():
    """いちゃもん: 相手が技を使った後に使うといちゃもん状態が付与され、直前に使用した技が記録される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いちゃもん"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 1)
    assert defender.executed_move.name == "たいあたり"

    t.run_move(battle, 0)
    assert defender.has_volatile("いちゃもん")
    assert defender.volatiles["いちゃもん"].move_name == "たいあたり"


def test_いちゃもん_未行動の相手にも成功する():
    """いちゃもん: 相手がまだ技を使っていない（executed_move が None）場合でも付与に成功する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いちゃもん"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    assert defender.executed_move is None

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

    assert defender.rank["spe"] == -2


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

    assert defender.rank["atk"] == 2
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

    assert defender.rank["atk"] == 6
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

    assert defender.rank["atk"] == 2
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
    assert defender.rank["atk"] == 6
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


def test_いやしのはどう_HPが半分回復する():
    """いやしのはどう: 相手のHPが減っているとき相手の最大HPの1/2を回復する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["いやしのはどう"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    defender.hp = 1
    t.run_move(battle, 0)

    assert defender.hp == 1 + int(defender.max_hp * 1 / 2)


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


def test_おかたづけ_こうげきとすばやさが1段階ずつ上がる():
    """おかたづけ: 使用するとこうげきとすばやさが1段階ずつ上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おかたづけ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)

    assert attacker.rank["atk"] == 1
    assert attacker.rank["spe"] == 1


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
    assert defender.rank["atk"] == 0
    assert defender.rank["spa"] == 0


def test_おきみやげ_使用者がひんしになる():
    """おきみやげ: 使用者がひんしになる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おきみやげ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)

    assert attacker.fainted
    assert defender.rank["atk"] == -2
    assert defender.rank["spa"] == -2


def test_おたけび_こうげきとくこう1段階ずつ下がる():
    """おたけび: 相手のこうげきととくこうランクが1段階ずつ下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おたけび"])],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["atk"] == -1
    assert defender.rank["spa"] == -1


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
    assert defender.rank["spa"] == 6


def test_おだてる_とくこう1段階上がりこんらん付与():
    """おだてる: 相手のとくこうが1段階上がり、こんらん状態になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おだてる"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)

    assert defender.rank["spa"] == 1
    assert defender.has_volatile("こんらん")


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

    assert defender.rank["spa"] == 6
    assert defender.has_volatile("こんらん")


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
