"""特性ハンドラの単体テスト"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    pass

import pytest

from jpoke import Pokemon
from jpoke.enums import LogCode
from jpoke.types import AilmentName, WeatherName

from .. import test_utils as t


def test_やるき_すでにねむり状態のポケモンを場に出すと即座に回復する():
    """やるき: 元の特性がやるきのポケモンが、特性を書き換えられてねむり状態になった後、
    交代でベンチに戻ると特性はやるきに戻る（ねむりは残る）。この状態のポケモンを再び
    場に出すと、場に出た直後に特性の効果でねむりが治る。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいでんき", move_names=["スキルスワップ"])],
        team1=[
            Pokemon("カビゴン", ability_name="やるき"),
            Pokemon("ラッキー", ability_name="しぜんかいふく"),
        ],
        accuracy=100,
    )
    defender = battle.actives[1]
    # スキルスワップで特性を入れ替え、やるきの効果を持たない状態にする
    t.run_move(battle, 0)
    assert defender.ability.name == "せいでんき"
    assert defender.base_ability == "やるき"

    # 特性がやるきでない間にねむり状態にする
    assert battle.ailment_manager.apply(defender, "ねむり", count=3)

    # ベンチに戻ると特性は元のやるきに戻るが、ねむりはそのまま残る
    t.run_switch(battle, 1, 1)
    bench = battle.get_team(battle.players[1])[0]
    assert bench.ability.name == "やるき"
    assert bench.ailment.name == "ねむり"

    # 再び場に出すと、場に出た直後にやるきの効果でねむりが治る
    t.run_switch(battle, 1, 0)
    active = battle.actives[1]
    assert active.ability.name == "やるき"
    assert not active.ailment.is_active


def test_やるき_どくびしと同時に発生した場合はどくびしの毒付与が不発してから回復する():
    """やるき: すでにねむり状態のやるきのポケモンを、どくびしが設置されたサイドに
    出した場合、どくびしのどく付与判定はねむり状態により不発してから、やるきの
    効果でねむりが治る（どくびしの効果は防がれる）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="せいでんき", move_names=["スキルスワップ"])],
        team1=[
            Pokemon("カビゴン", ability_name="やるき"),
            Pokemon("ラッキー", ability_name="しぜんかいふく"),
        ],
        accuracy=100,
        side1={"どくびし": 2},
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert battle.ailment_manager.apply(defender, "ねむり", count=3)

    t.run_switch(battle, 1, 1)
    t.run_switch(battle, 1, 0)
    active = battle.actives[1]

    # ねむりは治り、どくびしのどくも付与されない
    assert not active.ailment.is_active


def test_ゆうばく_攻撃側がしめりけを持つ場合発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ゆうばく")],
        team1=[Pokemon("カビゴン", ability_name="しめりけ", move_names=["たいあたり"])],
    )
    mon, foe = battle.actives
    mon.hp = 1
    t.run_move(battle, 1)
    assert mon.fainted
    assert foe.hp == foe.max_hp


def test_ゆうばく_直接攻撃KO時に攻撃者に1_4ダメージ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ゆうばく")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    mon, foe = battle.actives
    mon.hp = 1
    t.run_move(battle, 1)
    assert mon.fainted
    assert foe.hp == foe.max_hp - foe.max_hp // 4


def test_ゆうばく_非接触KOでは発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ゆうばく")],
        team1=[Pokemon("カビゴン", move_names=["でんきショック"])],
    )
    mon, foe = battle.actives
    mon.hp = 1
    t.run_move(battle, 1)
    assert mon.fainted
    assert foe.hp == foe.max_hp


def test_ようりょくそ_おおひでり中も素早さ2倍():
    """ようりょくそ: おおひでり状態でもはれと同様に素早さが2倍になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ようりょくそ")],
        team1=[Pokemon("カビゴン")],
        weather=("おおひでり", 99),
    )
    mon = battle.actives[0]
    assert battle.speed_calculator.calc_effective_speed(mon) == mon.stats["spe"] * 2


def test_ゆうばく_マジックガード持ちの攻撃者にはダメージが入らない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ゆうばく")],
        team1=[Pokemon("カビゴン", ability_name="マジックガード", move_names=["たいあたり"])],
    )
    mon, foe = battle.actives
    mon.hp = 1
    t.run_move(battle, 1)
    assert mon.fainted
    assert foe.hp == foe.max_hp


def test_ゆうばく_攻撃者がぼうごパットを持つ場合発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ゆうばく")],
        team1=[Pokemon("カビゴン", item_name="ぼうごパット", move_names=["たいあたり"])],
    )
    mon, foe = battle.actives
    mon.hp = 1
    t.run_move(battle, 1)
    assert mon.fainted
    assert foe.hp == foe.max_hp


def test_ゆうばく_攻撃者が反動で既にひんしの場合は発動しない():
    """とっしんの反動（ON_HIT）は ON_MOVE_KO より先に発火するため、反動だけで
    攻撃者がひんしになった場合ゆうばくは発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ゆうばく")],
        team1=[Pokemon("カビゴン", move_names=["とっしん"])],
        accuracy=100,
    )
    mon, foe = battle.actives
    mon.hp = 1
    foe.hp = 1
    t.run_move(battle, 1)
    assert mon.fainted
    assert foe.fainted
    logs = [
        log for log in battle.event_logger.logs
        if log.log == LogCode.ABILITY_TRIGGERED
        and log.payload is not None
        and getattr(log.payload, "ability", None) == "ゆうばく"
    ]
    assert len(logs) == 0


def test_ゆうばく_攻撃者がみがわり状態でも本体にダメージが入る():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ゆうばく")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    mon, foe = battle.actives
    mon.hp = 1
    battle.volatile_manager.apply(foe, "みがわり", hp=100)
    t.run_move(battle, 1)
    assert mon.fainted
    # みがわりの身代わり(hp=100)ではなく、攻撃者自身の実HPが減っている
    assert foe.hp == foe.max_hp - foe.max_hp // 4
    assert foe.volatiles["みがわり"].hp == 100


def test_ゆうばく_相手も同時にひんしになった場合ゆうばく側が負ける():
    """通信対戦の現行仕様（第七世代以降）: ゆうばくの反撃ダメージで相手も
    ひんしになり両者全滅した場合、ゆうばく側の負けとなる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ゆうばく")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    mon, foe = battle.actives
    mon.hp = 1
    foe.hp = foe.max_hp // 4
    t.run_move(battle, 1)
    assert mon.fainted
    assert foe.fainted
    assert battle.judge_winner() is battle.players[1]


def test_よちむ_場に出たとき相手の最高威力の技が公開される():
    """よちむ: 登場時に相手の技のうち最高威力の技が公開される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="よちむ")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり", "10まんボルト"])],
    )
    _, foe = battle.actives
    assert foe.moves[1].revealed
    assert not foe.moves[0].revealed


def test_よちむ_変化技も公開される():
    """よちむ: 変化技のみの場合は(威力0の技の中から)いずれかが公開される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="よちむ")],
        team1=[Pokemon("カビゴン", move_names=["つるぎのまい"])],
    )
    _, foe = battle.actives
    assert foe.moves[0].revealed


def test_よちむ_威力欄が変動する技は見なし威力で判定される():
    """よちむ: くさむすびは実際の内部データ上の威力（対象の重さで変動、格納値は
    プレースホルダの1）ではなく、技説明で表示される見なし威力80で判定される。
    そのため威力40のたいあたりより優先して読み取られる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="よちむ")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり", "くさむすび"])],
    )
    _, foe = battle.actives
    assert foe.moves[1].revealed
    assert not foe.moves[0].revealed


def test_よちむ_一撃必殺技は見なし威力150として最優先で読み取られる():
    """よちむ: じわれは実威力0（固定即死ダメージ）だが、見なし威力150として扱われ、
    見なし威力80のくさむすびより優先して読み取られる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="よちむ")],
        team1=[Pokemon("カビゴン", move_names=["じわれ", "くさむすび"])],
    )
    _, foe = battle.actives
    assert foe.moves[0].revealed
    assert not foe.moves[1].revealed


def test_よびみず_エレキフィールドなど場を対象とするでんき技には発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["あまごい"])],
        team1=[Pokemon("カビゴン", ability_name="よびみず")],
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert battle.weather.name == "あめ"
    assert defender.boosts["spa"] == 0
    assert not defender.ability.revealed


def test_よびみず_アクアリングなど自分自身を対象とするみず技には発動しない():
    """よびみず: アクアリングは自分自身が対象の技のため、自分のよびみずには発動しない
    （アクアリング自体の効果は通常どおり発生する）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="よびみず", move_names=["アクアリング"])],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)
    assert mon.has_volatile("アクアリング")
    assert mon.boosts["spa"] == 0


def test_よびみず_みずタイプの変化技も無効化する():
    """よびみず: みずびたしのようなみずタイプの変化技を受けても無効化し、タイプは変わらない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="よびみず")],
        team1=[Pokemon("カビゴン", move_names=["みずびたし"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 1)
    assert mon.types == ["でんき"]
    assert mon.boosts["spa"] == 1


def test_よびみず_マジックコートで跳ね返された変化技を受けるととくこうが上がる():
    """よびみず: 自分が使ったみずタイプの変化技が相手のマジックコートで跳ね返され、
    跳ね返った技を自分自身が受けた場合はよびみずが発動してとくこうが上がる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="よびみず", move_names=["みずびたし"])],
        team1=[Pokemon("カビゴン")],
        volatile1={"マジックコート": 1},
        accuracy=100,
    )
    mon = battle.actives[0]
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert mon.boosts["spa"] == 1
    assert foe.types == ["ノーマル"]


def test_よびみず_マジックコート状態では変化技を跳ね返しとくこうが上がらない():
    """よびみず: マジックコート状態のよびみず持ちがみずタイプの変化技を受けても、
    先に跳ね返されるためよびみずは発動せずとくこうは上がらない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="よびみず")],
        team1=[Pokemon("カビゴン", move_names=["みずびたし"])],
        volatile0={"マジックコート": 1},
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 1)
    assert mon.boosts["spa"] == 0
    assert not mon.ability.revealed


def test_よびみず_まもるで防がれたときは発動しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="よびみず")],
        team1=[Pokemon("カビゴン", move_names=["みずでっぽう"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "まもる", count=1)
    t.run_move(battle, 1)
    assert mon.boosts["spa"] == 0
    assert not mon.ability.revealed


def test_よびみず_みがわり状態の攻撃技でも発動する():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="よびみず")],
        team1=[Pokemon("カビゴン", move_names=["みずでっぽう"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "みがわり", count=mon.max_hp // 4)
    t.run_move(battle, 1)
    assert mon.boosts["spa"] == 1
    assert mon.has_volatile("みがわり")


def test_よびみず_無効化時にきゅうこんは発動しない():
    """よびみず: きゅうこんのようなみず技被弾で発動するアイテムは、
    よびみずで無効化されたときは発動しない（ダメージ処理自体が行われないため）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="よびみず", item_name="きゅうこん")],
        team1=[Pokemon("カビゴン", move_names=["みずでっぽう"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 1)
    assert mon.hp == mon.max_hp
    assert mon.boosts["spa"] == 1
    assert mon.has_item()


def test_よびみず_連続技を受けてもとくこう上昇は1回のみ():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="よびみず")],
        team1=[Pokemon("カビゴン", move_names=["すいりゅうれんだ"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 1)
    assert mon.boosts["spa"] == 1
    assert mon.hp == mon.max_hp


@pytest.mark.parametrize(
    "move_name",
    ["でんきショック", "たいあたり"]
)
def test_よわき_HP半分以下で攻撃補正0_5倍(move_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="よわき", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
    )
    attacker = battle.actives[0]
    attacker.hp = attacker.max_hp // 2
    t.run_move(battle, 0)
    assert 2048 == battle.damage_calculator.atk_modifier


def test_ライトメタル_おもさが半分になりくさむすびの威力が下がる():
    """ライトメタル: 自分のおもさが半分になる。フシギバナ(100.0kg)は50.0kgとなり、
    くさむすびの威力は100(100kg以上200kg未満)から80(50kg以上100kg未満)に下がる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["くさむすび"])],
        team1=[Pokemon("フシギバナ", ability_name="ライトメタル")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 80


def test_ライトメタル_かたやぶりで無効化されおもさが基本値になる():
    """ライトメタル: かたやぶり持ちの技を受けると特性が無視され、
    おもさを参照する技（くさむすび）の威力が基本のおもさ基準になる。
    フシギバナ(100.0kg)はライトメタルで50.0kg扱いとなり本来威力80だが、
    かたやぶりを受けると100.0kgのまま(威力100)で計算される。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["くさむすび"])],
        team1=[Pokemon("フシギバナ", ability_name="ライトメタル")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.final_power == 100


def test_ライトメタル_かるいしと重複しておもさが4分の1になる():
    """ライトメタル: かるいしを持っていると、特性の効果とかるいしの効果は累積し、おもさは1/4になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ライトメタル", item_name="かるいし")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.weight == int(mon.data.weight * 0.25 * 10) / 10


def test_リベロ_へんげんじざいと同様に技実行直前にタイプが変化する():
    """リベロはへんげんじざいと同一効果（共通ハンドラ）を持ち、技実行直前に技タイプへ変化する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="リベロ", move_names=["たいあたり", "ひのこ"])],
        team1=[Pokemon("カビゴン")],
    )
    attacker = battle.actives[0]

    t.run_move(battle, 0, 0)
    assert attacker.types == ["ノーマル"]

    # 同一滞在で1回のみ発動するため、2回目の技では変化しない
    t.run_move(battle, 0, 1)
    assert attacker.types == ["ノーマル"]


def test_リベロ_交代でリセットされ再発動できる():
    battle = t.start_battle(
        team0=[
            Pokemon("ピカチュウ", ability_name="リベロ", move_names=["たいあたり", "ひのこ"]),
            Pokemon("ピカチュウ"),
        ],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]

    t.run_move(battle, 0, 0)
    assert mon.types == ["ノーマル"]

    t.run_switch(battle, 0, 1)
    t.run_switch(battle, 0, 0)
    t.run_move(battle, 0, 1)

    assert mon.types == ["ほのお"]


def test_リミットシールド_HP1_2以下で登場してもコアの姿のまま():
    battle = t.start_battle(
        team0=[Pokemon("メテノ(コア)", ability_name="リミットシールド")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2
    # ターン終了時に判定される（登場直後はまだりゅうせい）
    assert mon.name == "メテノ(りゅうせい)"


def test_リミットシールド_HP1_2超で登場するとりゅうせいのすがたになる():
    battle = t.start_battle(
        team0=[Pokemon("メテノ(コア)", ability_name="リミットシールド")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "メテノ(りゅうせい)"


def test_リミットシールド_コアのすがたでは状態異常になる():
    battle = t.start_battle(
        team0=[Pokemon("メテノ(コア)", ability_name="リミットシールド")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2
    t.end_turn(battle)
    assert mon.name == "メテノ(コア)"
    assert t.apply_ailment(battle, 0, "まひ")


def test_リミットシールド_ターン終了時にHP1_2以下ならコアの姿になる():
    battle = t.start_battle(
        team0=[Pokemon("メテノ(コア)", ability_name="リミットシールド")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "メテノ(りゅうせい)"
    mon.hp = mon.max_hp // 2
    t.end_turn(battle)
    assert mon.name == "メテノ(コア)"


def test_リミットシールド_ターン終了時にHP1_2超ならりゅうせいのすがたを維持する():
    battle = t.start_battle(
        team0=[Pokemon("メテノ(コア)", ability_name="リミットシールド")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "メテノ(りゅうせい)"
    t.end_turn(battle)
    assert mon.name == "メテノ(りゅうせい)"


def test_リミットシールド_メテノ以外の種族ではターン終了時にフォルムが変化しない():
    """seed=214 の回帰テスト。

    fuzzerは特性を種族と無関係に割り当てるため、メテノ以外のポケモンに
    リミットシールドが付与されることがある。ターン終了時のフォルム更新
    ハンドラに種族チェックが漏れていると、メテノ以外のポケモンにも
    set_form(METEONO_METEOR/CORE)が無条件に呼ばれ、種族・技リストが
    メテノのものへ書き換わってしまっていた。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="リミットシールド")],
        team1=[Pokemon("コラッタ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 2
    t.end_turn(battle)
    assert mon.name == "ピカチュウ"


@pytest.mark.parametrize(
    "ailment_name",
    ["どく", "もうどく", "まひ", "やけど", "ねむり", "こおり"],
)
def test_リミットシールド_りゅうせいのすがたで状態異常にならない(ailment_name: AilmentName):
    battle = t.start_battle(
        team0=[Pokemon("メテノ(コア)", ability_name="リミットシールド")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "メテノ(りゅうせい)"
    assert not t.apply_ailment(battle, 0, ailment_name)


def test_リミットシールド_交代するとコアの姿に戻る():
    battle = t.start_battle(
        team0=[Pokemon("メテノ(コア)", ability_name="リミットシールド"), Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.name == "メテノ(りゅうせい)"
    t.run_switch(battle, 0, 1)
    assert mon.name == "メテノ(コア)"


def test_りんぷん_かたやぶりで無効化():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["ほっぺすりすり"])],
        team1=[Pokemon("ニャース", ability_name="りんぷん")],
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name == "まひ"


def test_りんぷん_追加効果を受けない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほっぺすりすり"])],
        team1=[Pokemon("ニャース", ability_name="りんぷん")],
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.is_active is False


@pytest.mark.parametrize(
    "ailment_name",
    ["どく", "もうどく", "まひ", "やけど", "ねむり", "こおり"],
)
def test_リーフガード_すべての状態異常を防ぐ(ailment_name: AilmentName):
    battle = t.start_battle(
        team0=[Pokemon("コラッタ", ability_name="リーフガード")],
        team1=[Pokemon("ピカチュウ")],
        weather=("はれ", 5)
    )
    mon = battle.actives[0]
    assert battle.ailment_manager.apply(mon, ailment_name) is False


@pytest.mark.parametrize(
    "weather, result",
    [
        ("はれ", False),
        ("おおひでり", False),
        ("あめ", True),
        ("すなあらし", True),
        ("ゆき", True),
        (None, True),
    ],
)
def test_リーフガード_はれ中に状態異常を防ぐ(weather: WeatherName | None, result: bool):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="リーフガード")],
        team1=[Pokemon("ピカチュウ")],
        weather=(weather, 5) if weather else None
    )
    mon = battle.actives[0]
    assert battle.ailment_manager.apply(mon, "どく") is result


@pytest.mark.parametrize(
    "ability_name, move_name",
    [
        ("わざわいのおふだ", "たいあたり"),
        ("わざわいのうつわ", "ひのこ"),
    ],
)
def test_わざわい_相手攻撃補正を0_75倍(ability_name: str, move_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=[move_name])],
        team1=[Pokemon("ピカチュウ", ability_name=ability_name)],
    )
    t.run_move(battle, 0)
    assert 3072 == battle.damage_calculator.atk_modifier


@pytest.mark.parametrize(
    "ability_name, move_name",
    [
        ("わざわいのつるぎ", "たいあたり"),
        ("わざわいのたま", "ひのこ"),
    ],
)
def test_わざわい_相手防御補正を0_75倍(ability_name: str, move_name: str):
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name=ability_name, move_names=[move_name])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 3072 == battle.damage_calculator.def_modifier


def test_わざわいのおふだ_かたやぶりで無効化されない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="わざわいのおふだ")],
    )
    t.run_move(battle, 0)
    assert 3072 == battle.damage_calculator.atk_modifier


def test_わたげ_クリアボディではブロックされる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="わたげ")],
        team1=[Pokemon("カビゴン", ability_name="クリアボディ", move_names=["たいあたり"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[1].boosts["spe"] == 0


def test_わたげ_被弾で攻撃者のSが1段階下がる():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="わたげ")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    t.run_move(battle, 1)
    assert battle.actives[1].boosts["spe"] == -1


def test_わるいてぐせ_接触技を受けたら相手のアイテムを奪う():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="たべのこし", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="わるいてぐせ")],
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert defender.item.name == "たべのこし"
    assert not attacker.has_item()


def test_わるいてぐせ_自分がアイテムを持っている場合は奪わない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="たべのこし", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="わるいてぐせ", item_name="いのちのたま")],
    )
    attacker, _ = battle.actives
    t.run_move(battle, 0)
    assert attacker.has_item()


def test_わるいてぐせ_非接触技には反応しない():
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="たべのこし", move_names=["でんきショック"])],
        team1=[Pokemon("ピカチュウ", ability_name="わるいてぐせ")],
    )
    attacker, _ = battle.actives
    t.run_move(battle, 0)
    assert attacker.has_item()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
