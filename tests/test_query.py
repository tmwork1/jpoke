"""battle.query（PokemonQuery）のうち、Battle直下に委譲された判定系メソッドのテスト。

Pokemon/Player単体の引数で完結する9メソッド
（has_available_bench/is_floating/is_trapped/is_nervous/is_hazard_immune/
can_use_last_resort/get_forced_move_name/is_first_actor/is_second_actor）が
battle.query.<method>() へ正しく委譲されていることを確認する軽量な回帰テスト。
"""
from jpoke import Pokemon
from . import test_utils as t


def test_can_use_last_resort_他の技をすべて使用済みならtrue():
    """can_use_last_resort(): とっておき以外の技をすべて使用済みならTrue"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["でんこうせっか", "とっておき"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0, 0)
    assert battle.can_use_last_resort(attacker) is True


def test_can_use_last_resort_未使用技が残っている場合はfalse():
    """can_use_last_resort(): とっておき以外の技が未使用ならFalse"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["でんこうせっか", "とっておき"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    assert battle.can_use_last_resort(attacker) is False


def test_get_forced_move_name_あなをほるで固定技名を返す():
    """get_forced_move_name(): あなをほるの1ターン目で固定される技名を返す"""
    battle = t.start_battle(
        team0=[Pokemon("ディグダ", move_names=["あなをほる"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.has_volatile("あなをほる")
    assert battle.get_forced_move_name(attacker) == "あなをほる"


def test_get_forced_move_name_固定されていない場合はnone():
    """get_forced_move_name(): 強制行動中でなければNoneを返す"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン")],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]
    assert battle.get_forced_move_name(attacker) is None


def test_has_available_bench_とらわれ状態でも控えの生存で判定する():
    """has_available_bench(): とらわれ状態を無視して控えの生存を判定する（can_switchとの違い）"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン"), Pokemon("ピカチュウ")],
        team1=[Pokemon("カビゴン")],
    )
    player0 = battle.players[0]
    active = battle.actives[0]
    battle.set_volatile(active, "にげられない")

    # can_switch はとらわれ状態でFalseになるが、has_available_bench は無視してTrue
    assert battle.can_switch(player0) is False
    assert battle.has_available_bench(player0) is True


def test_has_available_bench_控えが全滅していればfalse():
    """has_available_bench(): 控えが全滅していればFalse"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン"), Pokemon("ピカチュウ")],
        team1=[Pokemon("カビゴン")],
    )
    player0 = battle.players[0]
    bench = battle.player_states[player0].bench[0]
    battle.modify_hp(bench, -bench.max_hp)
    assert battle.has_available_bench(player0) is False


def test_is_first_actor_行動順に基づき先攻を判定する():
    """is_first_actor(): 確定した行動順に基づき先攻かどうかを返す"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン")],
        team1=[Pokemon("ピカチュウ")],
    )
    player0, player1 = battle.players
    battle.turn_controller.action_order = [0, 1]
    assert battle.is_first_actor(player0) is True
    assert battle.is_first_actor(player1) is False


def test_is_first_actor_行動順未確定ならnone():
    """is_first_actor(): 行動順が未確定の場合はNoneを返す"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン")],
        team1=[Pokemon("ピカチュウ")],
    )
    player0 = battle.players[0]
    assert battle.turn_controller.action_order == []
    assert battle.is_first_actor(player0) is None


def test_is_floating_ひこうタイプはtrue():
    """is_floating(): ひこうタイプは浮いている状態と判定される"""
    battle = t.start_battle(
        team0=[Pokemon("ピジョット")],
        team1=[Pokemon("カビゴン")],
    )
    flyer = battle.actives[0]
    grounded = battle.actives[1]
    assert battle.is_floating(flyer) is True
    assert battle.is_floating(grounded) is False


def test_is_hazard_immune_あつぞこブーツでtrue():
    """is_hazard_immune(): あつぞこブーツ所持でエントリーハザード免疫になる"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="あつぞこブーツ")],
        team1=[Pokemon("カビゴン")],
    )
    protected = battle.actives[0]
    unprotected = battle.actives[1]
    assert battle.is_hazard_immune(protected) is True
    assert battle.is_hazard_immune(unprotected) is False


def test_is_nervous_相手のきんちょうかんでtrue():
    """is_nervous(): 相手が特性きんちょうかんを持つ場合Trueになる"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="きんちょうかん")],
        team1=[Pokemon("ピカチュウ")],
    )
    target = battle.actives[1]
    assert battle.is_nervous(target) is True


def test_is_second_actor_行動順に基づき後攻を判定する():
    """is_second_actor(): 確定した行動順に基づき後攻かどうかを返す"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン")],
        team1=[Pokemon("ピカチュウ")],
    )
    player0, player1 = battle.players
    battle.turn_controller.action_order = [0, 1]
    assert battle.is_second_actor(player1) is True
    assert battle.is_second_actor(player0) is False


def test_is_trapped_ゴーストタイプはにげられないでも逃げられる():
    """is_trapped(): にげられない状態でもゴーストタイプは逃げられる"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー")],
        team1=[Pokemon("カビゴン")],
    )
    ghost = battle.actives[0]
    battle.set_volatile(ghost, "にげられない")
    assert battle.is_trapped(ghost) is False


def test_is_trapped_にげられないでtrue():
    """is_trapped(): にげられない状態を付与すると逃げられない状態になる"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン")],
        team1=[Pokemon("カビゴン")],
    )
    trapped = battle.actives[0]
    assert battle.is_trapped(trapped) is False
    battle.set_volatile(trapped, "にげられない")
    assert battle.is_trapped(trapped) is True
