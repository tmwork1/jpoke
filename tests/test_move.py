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

    assert battle.move_executor.resolve_move_type(attacker, move) == "ノーマル"

    attacker.terastallize()
    assert battle.move_executor.resolve_move_type(attacker, move) == "ほのお"

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
        foe=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    battle.run_move(attacker, attacker.moves[0])
    assert defender.hp == 0


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
        # ("じわれ", "ピジョン"),
    ],
)
def test_一撃必殺技_タイプ相性で無効化される(move_name: str, foe_name: str):
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=[move_name])],
        foe=[Pokemon(foe_name)],
        accuracy=100,
    )
    attacker, defender = battle.actives
    battle.run_move(attacker, attacker.moves[0])
    assert defender.hp == defender.max_hp

# ──────────────────────────────────────────────────────────────────
# にどげり
# ──────────────────────────────────────────────────────────────────


def test_にどげり_命中判定1回で2回ヒットする():
    """にどげり: 命中判定は1回だけで、2ヒットする。"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["にどげり"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    battle.run_move(attacker, attacker.moves[0])
    assert defender.hits_taken == 2

# ──────────────────────────────────────────────────────────────────
# タネマシンガン
# ──────────────────────────────────────────────────────────────────


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
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["タネマシンガン"])],
        foe=[Pokemon("ピカチュウ")],
    )
    battle.random.random = lambda: roll
    hit_count = battle.move_executor._resolve_hit_count(
        t.build_context(battle, atk_idx=0)
    )
    assert hit_count == expected


def test_タネマシンガン_相手HP1で最初の1発で処理中断():
    """タネマシンガン: 相手の初期HPが1のときに、最初の1発で相手がひんしになり処理が中断される。"""
    battle = t.start_battle(
        foe=[Pokemon("ピカチュウ")],
        ally=[Pokemon("ピカチュウ", moves=["タネマシンガン"])],
    )

    # 相手のHPを1に設定（最大HPから現在HPを1に減らす処理）
    defender = battle.actives[1]
    defender.hp = 1

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

def test_テラバースト_ステラ():
    """ステラタイプ"""
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", tera_type="ステラ", moves=["テラバースト"])],
        foe=[Pokemon("ピカチュウ", tera_type="でんき")],
    )
    ctx = t.build_context(battle, atk_idx=0)
    attacker = ctx.attacker
    move = attacker.moves[0]

    attacker.terastallize()
    battle.run_move(attacker, move)

    assert move.type == "ステラ"
    assert battle.damage_calculator.final_power == 100
    assert attacker.rank["A"] == -1
    assert attacker.rank["C"] == -1


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


# ──────────────────────────────────────────────────────────────────
# いかりのまえば
# ──────────────────────────────────────────────────────────────────

def test_いかりのまえば_最低1ダメージ():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["いかりのまえば"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    defender.hp = 1
    battle.run_move(attacker, attacker.moves[0])
    assert defender.hp == 0

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
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["がむしゃら"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    attacker.hp = attacker_hp
    defender.hp = defender_hp

    battle.run_move(attacker, attacker.moves[0])
    battle.print_logs()
    damage = defender_hp - defender.hp
    assert damage == expected_damage

# ──────────────────────────────────────────────────────────────────
# いのちがけ
# ──────────────────────────────────────────────────────────────────


def test_いのちがけ_与ダメージは現在HPで使用者はひんし():
    battle = t.start_battle(
        ally=[Pokemon("ピカチュウ", moves=["いのちがけ"])],
        foe=[Pokemon("ピカチュウ")],
    )
    attacker, defender = battle.actives
    attacker.hp = 40
    battle.run_move(attacker, attacker.moves[0])
    assert defender.damage_taken == 40
    assert attacker.hp == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
