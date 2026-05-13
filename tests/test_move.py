"""技ハンドラの単体テスト。"""

import pytest
from jpoke import Pokemon
from jpoke.core import Handler, HandlerReturn
from jpoke.enums import Event, LogCode, Command
import test_utils as t


# ──────────────────────────────────────────────────────────────────
# テラバースト
# ──────────────────────────────────────────────────────────────────


def test_テラバースト_テラスタル時にタイプがテラスタイプへ変化():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", tera_type="ほのお", moves=["テラバースト"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    move = attacker.moves[0]

    move.register_handlers(battle.events, attacker)

    assert battle.move_executor.get_effective_move_type(attacker, move) == "ノーマル"

    attacker.terastallize()
    assert battle.move_executor.get_effective_move_type(attacker, move) == "ほのお"

    move.unregister_handlers(battle.events, attacker)


@pytest.mark.parametrize(
    ("attacker_name", "expected"),
    [
        ("カイリキー", "物理"),
        ("フーディン", "特殊"),
    ],
)
def test_テラバースト_テラスタル時に高い攻撃値の分類になる(attacker_name: str, expected: str):
    battle = t.start_battle(
        ally=[Pokemon(attacker_name, tera_type="でんき", moves=["テラバースト"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    move = attacker.moves[0]

    move.register_handlers(battle.events, attacker)

    assert battle.move_executor.resolve_move_category(attacker, move) == "特殊"

    attacker.terastallize()
    assert battle.move_executor.resolve_move_category(attacker, move) == expected

    move.unregister_handlers(battle.events, attacker)

# ──────────────────────────────────────────────────────────────────
# 一撃必殺技
# ──────────────────────────────────────────────────────────────────


def test_一撃必殺技_命中時は相手を一撃で倒す():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["つのドリル"])],
        foe=[Pokemon("ピカチュウ", moves=["はねる"])],
        accuracy=100,
    )

    t.reserve_command(battle, ally_command=Command.MOVE_0, foe_command=Command.MOVE_0)
    battle.advance_turn()

    assert battle.actives[1].hp == 0


def test_一撃必殺技_外した時はダメージを与えない():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["つのドリル"])],
        foe=[Pokemon("ピカチュウ", moves=["はねる"])],
        accuracy=0,
    )
    before_foe_hp = battle.actives[1].hp

    t.reserve_command(battle, ally_command=Command.MOVE_0, foe_command=Command.MOVE_0)
    battle.advance_turn()

    assert battle.actives[1].hp == before_foe_hp


@pytest.mark.parametrize(
    ("move_name", "foe_name"),
    [
        ("つのドリル", "ゴース"),
        ("じわれ", "ピジョン"),
    ],
)
def test_一撃必殺技_タイプ相性で無効化される(move_name: str, foe_name: str):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=[move_name])],
        foe=[Pokemon(foe_name, moves=["はねる"])],
        accuracy=100,
    )
    before_foe_hp = battle.actives[1].hp

    t.reserve_command(battle, ally_command=Command.MOVE_0, foe_command=Command.MOVE_0)
    battle.advance_turn()

    assert battle.actives[1].hp == before_foe_hp
    assert t.log_contains(battle, LogCode.MOVE_IMMUNE, player_idx=1)

# ──────────────────────────────────────────────────────────────────
# にどげり
# ──────────────────────────────────────────────────────────────────


def test_にどげり_命中判定1回で2回ヒットする():
    """にどげり: 命中判定は1回だけで、2ヒットする。"""
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")],
                            ally=[Pokemon("ピカチュウ", moves=["にどげり"])],
                            )
    call_count = 0
    original_check_hit = battle.move_executor.check_hit

    def wrapped_check_hit(attacker, move):
        nonlocal call_count
        call_count += 1
        return original_check_hit(attacker, move)

    battle.move_executor.check_hit = wrapped_check_hit

    battle.advance_turn()

    assert call_count == 1
    assert battle.actives[1].hits_taken == 2

# ──────────────────────────────────────────────────────────────────
# タネマシンガン
# ──────────────────────────────────────────────────────────────────


def test_タネマシンガン_スキルリンクで5回ヒットする():
    """タネマシンガン: スキルリンクなら5ヒット固定になる。"""
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")],
                            ally=[Pokemon("ピカチュウ", ability="スキルリンク", moves=["タネマシンガン"])],
                            )
    battle.advance_turn()
    assert battle.actives[1].hits_taken == 5


@pytest.mark.parametrize(
    "roll, expected",
    [
        (0.0, 2),
        (0.3749, 2),
        (0.375, 3),
        (0.7499, 3),
        (0.75, 4),
        (0.8749, 4),
        (0.875, 5),
        (0.9999, 5),
    ],
)
def test_タネマシンガン_ヒット数が2から5の範囲で決まる(roll: float, expected: int):
    """タネマシンガン: 乱数ロールに応じて2~5ヒットが決まる。"""
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")],
                            ally=[Pokemon("ピカチュウ", moves=["タネマシンガン"])],
                            )
    attacker = battle.actives[0]
    move = attacker.moves[0]

    original_random = battle.random.random
    battle.random.random = lambda: roll
    try:
        hit_count = battle.move_executor._resolve_hit_count(attacker, move)
    finally:
        battle.random.random = original_random

    assert hit_count == expected


def test_タネマシンガン_相手HP1で最初の1発で処理中断():
    """タネマシンガン: 相手の初期HPが1のときに、最初の1発で相手がひんしになり処理が中断される。"""
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")],
                            ally=[Pokemon("ピカチュウ", moves=["タネマシンガン"])],
                            )

    # 相手のHPを1に設定（最大HPから現在HPを1に減らす処理）
    defender = battle.actives[1]
    defender._hp = 1

    # ダメージ計算の呼び出し回数をカウント
    damage_call_count = 0

    def counting_determine_damage(attacker, defender, move, critical=False):
        nonlocal damage_call_count
        damage_call_count += 1
        return 1  # 常に1ダメージ

    battle.roll_damage = counting_determine_damage
    battle.advance_turn()

    # 複数ヒット予定（min_hits=2）なのに、最初の1発で相手がひんしになったため処理が中断される
    # ダメージ計算が1回だけ実行される
    assert damage_call_count == 1
    assert defender.hp == 0

# ──────────────────────────────────────────────────────────────────
# トリプルアクセル
# ──────────────────────────────────────────────────────────────────


def test_トリプルアクセル_各ヒットで命中判定と威力更新を行う():
    """トリプルアクセル: 各ヒットで命中判定し、威力が20→40→60で更新される。"""
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")],
                            ally=[Pokemon("ピカチュウ", moves=["トリプルアクセル"])],
                            )
    call_count = 0
    powers = []

    def fake_check_hit(attacker, move):
        nonlocal call_count
        call_count += 1
        return True

    def fake_determine_damage(attacker, defender, move, critical=False):
        powers.append(move.power)
        return 1

    battle.move_executor.check_hit = fake_check_hit
    battle.move_executor.check_critical = lambda ctx: False
    battle.move_executor._resolve_hit_count = lambda attacker, move: 3  # 必ず3ヒット
    battle.roll_damage = fake_determine_damage

    t.reserve_command(battle)
    battle.advance_turn()

    assert call_count == 3
    assert powers == [20, 40, 60]
    assert battle.actives[1].hits_taken == 3
    assert battle.actives[0].moves[0].power == battle.actives[0].moves[0].data.power

# ──────────────────────────────────────────────────────────────────
# はやてがえし
# ──────────────────────────────────────────────────────────────────


def test_はやてがえし_先制攻撃技に成功():
    """はやてがえし: 相手が先制攻撃技を選んだ時のみ成功し、ひるませる。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["はやてがえし"])],
        foe=[Pokemon("ピカチュウ", moves=["でんこうせっか"])],
    )
    before_foe_hp = battle.actives[1].hp
    before_ally_hp = battle.actives[0].hp
    t.reserve_command(battle)

    battle.advance_turn()
    assert battle.actives[1].hp < before_foe_hp
    assert battle.actives[0].hp == before_ally_hp
    assert t.log_contains(battle, LogCode.ACTION_BLOCKED, player_idx=1)


def test_はやてがえし_通常攻撃技には失敗():
    """はやてがえし: 優先度0の攻撃技を選んだ相手には失敗する。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["はやてがえし"])],
        foe=[Pokemon("ピカチュウ", moves=["１０まんボルト"])],
    )
    before_foe_hp = battle.actives[1].hp
    before_ally_hp = battle.actives[0].hp
    t.reserve_command(battle)
    battle.advance_turn()

    assert battle.actives[1].hp == before_foe_hp
    assert battle.actives[0].hp < before_ally_hp
    assert not t.log_contains(battle, LogCode.ACTION_BLOCKED, player_idx=1)


def test_はやてがえし_先制変化技には失敗():
    """はやてがえし: 先制変化技（まもる）には失敗する。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["はやてがえし"])],
        foe=[Pokemon("ピカチュウ", moves=["まもる"])],
    )
    before_foe_hp = battle.actives[1].hp
    t.reserve_command(battle)
    battle.advance_turn()

    assert battle.actives[1].hp == before_foe_hp
    assert not t.log_contains(battle, LogCode.ACTION_BLOCKED, player_idx=1)

# ──────────────────────────────────────────────────────────────────
# きあいパンチ
# ──────────────────────────────────────────────────────────────────


def test_きあいパンチ_行動前にダメージを受けず成功():
    """きあいパンチ: 行動前に被弾していなければ成功する。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["きあいパンチ"])],
        foe=[Pokemon("ピカチュウ", moves=["はねる"])],
    )
    before_foe_hp = battle.actives[1].hp

    t.reserve_command(battle)
    battle.advance_turn()

    assert battle.actives[1].hp < before_foe_hp


def test_きあいパンチ_攻撃ダメージを受けると失敗():
    """きあいパンチ: 行動前に攻撃ダメージを受けた場合は不発。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["きあいパンチ"])],
        foe=[Pokemon("ピカチュウ", moves=["でんこうせっか"])],
    )
    before_foe_hp = battle.actives[1].hp
    before_ally_hp = battle.actives[0].hp

    t.reserve_command(battle)
    battle.advance_turn()

    assert battle.actives[1].hp == before_foe_hp
    assert battle.actives[0].hp < before_ally_hp
    assert t.log_contains(battle, LogCode.ACTION_BLOCKED, player_idx=0)


def test_きあいパンチ_みがわりへの被弾では中断しない():
    """きあいパンチ: みがわりが被弾しても使用者は中断されない。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["きあいパンチ"])],
        foe=[Pokemon("ピカチュウ", moves=["でんこうせっか"])],
    )
    battle.volatile_manager.apply(battle.actives[0], "みがわり", hp=999)
    before_foe_hp = battle.actives[1].hp
    before_ally_hp = battle.actives[0].hp

    t.reserve_command(battle)
    battle.advance_turn()

    assert battle.actives[1].hp < before_foe_hp
    assert battle.actives[0].hp == before_ally_hp


# ──────────────────────────────────────────────────────────────────
# テラバースト
# ──────────────────────────────────────────────────────────────────

def test_ステラ技_テラスタルポケモンへ効果抜群():
    """ステラタイプの技はテラスタル済みポケモンに対して2.0倍の相性補正。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", tera_type="ステラ", moves=["テラバースト"])],
        foe=[Pokemon("コイキング", tera_type="みず")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    attacker.terastallize()

    move = attacker.moves[0]
    move.register_handlers(battle.events, attacker)
    # テラバーストのタイプをステラに設定
    move_type = battle.move_executor.get_effective_move_type(attacker, move)
    move.set_type(move_type)

    ctx = BattleContext(attacker=attacker, defender=defender, move=move)

    # 非テラスタル相手: 等倍
    assert battle.damage_calculator.calc_def_type_modifier(ctx) == pytest.approx(1.0)

    # テラスタル相手: 効果抜群
    defender.terastallize()
    assert battle.damage_calculator.calc_def_type_modifier(ctx) == pytest.approx(2.0)

    move.unregister_handlers(battle.events, attacker)


def test_テラバースト_ステラ時に威力100():
    """ステラ テラスタル中のテラバーストは威力が100になる。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", tera_type="ステラ", moves=["テラバースト"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    attacker.terastallize()

    move = attacker.moves[0]
    move.register_handlers(battle.events, attacker)

    ctx = BattleContext(attacker=attacker, defender=defender, move=move)
    assert battle.damage_calculator.calc_final_power(ctx) == 100

    move.unregister_handlers(battle.events, attacker)


def test_テラバースト_非ステラ時は威力80():
    """通常テラスタル中のテラバーストは威力80のまま。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", tera_type="ほのお", moves=["テラバースト"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    attacker.terastallize()

    move = attacker.moves[0]
    move.register_handlers(battle.events, attacker)

    ctx = BattleContext(attacker=attacker, defender=defender, move=move)
    assert battle.damage_calculator.calc_final_power(ctx) == 80

    move.unregister_handlers(battle.events, attacker)


def test_テラバースト_ステラ時に攻撃と特攻が1段階低下():
    """ステラ テラスタル中にテラバーストを使うと攻撃・特攻が-1段階になる。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", tera_type="ステラ", moves=["テラバースト"])],
        foe=[Pokemon("コイキング", moves=["はねる"])],
    )
    attacker = battle.actives[0]

    t.reserve_command(
        battle,
        ally_command=Command.TERASTAL_0,
        foe_command=Command.MOVE_0,
    )
    battle.advance_turn()

    assert attacker.terastallized
    assert attacker.rank["A"] == -1
    assert attacker.rank["C"] == -1


def test_テラバースト_非ステラ時は能力低下しない():
    """通常テラスタル中のテラバーストでは能力低下は起きない。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", tera_type="ほのお", moves=["テラバースト"])],
        foe=[Pokemon("コイキング", moves=["はねる"])],
    )
    attacker = battle.actives[0]

    t.reserve_command(
        battle,
        ally_command=Command.TERASTAL_0,
        foe_command=Command.MOVE_0,
    )
    battle.advance_turn()

    assert attacker.terastallized
    assert attacker.rank["A"] == 0
    assert attacker.rank["C"] == 0


# ──────────────────────────────────────────────────────────────────
# ナイトヘッド、ちきゅうなげ
# ──────────────────────────────────────────────────────────────────

def test_ナイトヘッド_与ダメージは使用者レベル固定():
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")],
                            ally=[Pokemon("ピカチュウ", level=50, moves=["ナイトヘッド"])],
                            )
    before_hp = battle.actives[1].hp
    battle.advance_turn()
    assert before_hp - battle.actives[1].hp == 50


def test_ちきゅうなげ_ゴーストには無効():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["ちきゅうなげ"])],
        foe=[Pokemon("ゴース", moves=["はねる"])],
    )
    battle.advance_turn()
    assert battle.actives[1].hp == battle.actives[1].max_hp
    assert t.log_contains(battle, LogCode.MOVE_IMMUNE, player_idx=1)


# ──────────────────────────────────────────────────────────────────
# いかりのまえば
# ──────────────────────────────────────────────────────────────────

def test_いかりのまえば_現在HPの半分を与える_最低1():
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")],
                            ally=[Pokemon("ピカチュウ", moves=["いかりのまえば"])],
                            )
    battle.actives[1]._hp = 1
    battle.advance_turn()
    assert battle.actives[1].hp == 0

# ──────────────────────────────────────────────────────────────────
# がむしゃら
# ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("attacker_hp", "defender_hp", "expected_damage"),
    [
        (30, 100, 70),
        (80, 60, 0),
    ],
)
def test_がむしゃら_相手HPとの差分ダメージ(attacker_hp: int, defender_hp: int, expected_damage: int):
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")],
                            ally=[Pokemon("ピカチュウ", moves=["がむしゃら"])],
                            )
    battle.modify_hp(battle.actives[0], v=attacker_hp - battle.actives[0].hp)
    battle.modify_hp(battle.actives[1], v=defender_hp - battle.actives[1].hp)
    before_hp = battle.actives[1].hp
    battle.advance_turn()
    assert before_hp - battle.actives[1].hp == expected_damage

# ──────────────────────────────────────────────────────────────────
# いのちがけ
# ──────────────────────────────────────────────────────────────────


def test_いのちがけ_与ダメージは現在HPで使用者はひんし():
    battle = t.start_battle(foe=[Pokemon("ピカチュウ")],
                            ally=[Pokemon("ピカチュウ", moves=["いのちがけ"])],
                            )
    battle.actives[0]._hp = 40
    battle.advance_turn()
    assert battle.actives[1].damage_taken == 40
    assert battle.actives[0].hp == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
