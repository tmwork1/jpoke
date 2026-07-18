"""アイテムハンドラの単体テスト"""
import pytest
from jpoke import Pokemon
from jpoke.enums import Command, LogCode
from .. import test_utils as t


def test_はっきんだま_ギラティナオリジンでも効果がある():
    """はっきんだま: ギラティナ(オリジン)が持っていてもドラゴン・ゴースト技に補正がかかる"""
    battle = t.start_battle(
        team0=[Pokemon("ギラティナ(オリジン)", item_name="はっきんだま", move_names=["ドラゴンクロー"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4915


def test_はっきんだま_ギラティナ以外が持っても効果がない():
    """はっきんだま: ギラティナ以外が持っていてもドラゴン・ゴースト技に補正がかからない"""
    battle = t.start_battle(
        team0=[Pokemon("パルキア", item_name="はっきんだま", move_names=["ドラゴンクロー"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_はっきんだま_なげつけるで威力60になる():
    """はっきんだま: ギラティナ以外が持っている場合は通常の道具でありなげつけるで使用でき、威力60でダメージを与える"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="はっきんだま", move_names=["なげつける"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)
    assert defender.hp < hp_before
    assert not attacker.has_item()


def test_はっきんだま_はたきおとすで奪われる():
    """はっきんだま: だいはっきんだまと異なり、ギラティナが持っていても通常通りはたきおとすで奪われる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["はたきおとす"])],
        team1=[Pokemon("ギラティナ(オリジン)", item_name="はっきんだま")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert not defender.has_item()


def test_はっきんだま_対象外タイプの技には効果がない():
    """はっきんだま: ギラティナが持っていてもドラゴン・ゴースト以外の技には補正がかからない"""
    battle = t.start_battle(
        team0=[Pokemon("ギラティナ(アナザー)", item_name="はっきんだま", move_names=["はかいこうせん"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4096


def test_バコウのみ_ついばむで奪われる前に消費されダメージ半減():
    """バコウのみ: 効果抜群のついばむを受けた場合、技の効果よりバコウのみの効果が優先されてダメージが半減し、消費済みのため奪われない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ついばむ"])],
        team1=[Pokemon("キモリ", item_name="バコウのみ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert battle.damage_calculator.damage_modifier == 2048
    assert not defender.has_item()  # バコウのみの効果で消費済み
    assert not attacker.has_item()  # ついばむによる奪取は失敗する


def test_バコウのみ_フライングプレスでは発動しない():
    """バコウのみ: フライングプレスがひこう複合相性で抜群になっても発動するのはヨプのみでありバコウのみは発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ルカリオ", move_names=["フライングプレス"])],
        team1=[Pokemon("キモリ", item_name="バコウのみ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert battle.damage_calculator.damage_modifier != 2048
    assert defender.has_item()  # バコウのみは消費されない


def test_バンジのみ_それ以外の性格ではこんらんしない():
    """バンジのみ: にがい味が嫌いでない性格では発動してもこんらんしない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="バンジのみ", nature="まじめ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.hp == mon.max_hp // 4 + mon.max_hp // 3
    assert not mon.has_item()
    assert not mon.has_volatile("こんらん")


@pytest.mark.parametrize(
    "nature",
    ["やんちゃ", "のうてんき", "うっかりや", "むじゃき"]
)
def test_バンジのみ_とくぼうが上がりにくい性格でこんらんする(nature):
    """バンジのみ: にがい味が嫌いな性格（とくぼうが上がりにくい）は発動と同時にこんらんする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="バンジのみ", nature=nature)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.hp == mon.max_hp // 4 + mon.max_hp // 3
    assert not mon.has_item()
    assert mon.has_volatile("こんらん")


def test_ばんのうがさ_あさのひざしが晴れでも半分回復():
    """ばんのうがさ使用者: 晴れ状態でもあさのひざしの回復量が最大HPの1/2になる"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", move_names=["あさのひざし"], item_name="ばんのうがさ")],
        team1=[Pokemon("ピカチュウ")],
        weather=("はれ", 99),
        accuracy=100,
    )
    mon = battle.actives[0]
    max_hp = mon.max_hp
    # HPを1にして回復量を確認する
    mon.hp = 1
    t.run_move(battle, 0)
    # 晴れなら2/3回復 (int(max_hp * 2/3)) のはずだが、
    # ばんのうがさで1/2回復 (int(max_hp * 1/2)) になる
    expected_hp = 1 + int(max_hp * 0.5)
    assert mon.hp == expected_hp


def test_ばんのうがさ_すいすいが発動しない():
    """ばんのうがさ使用者: 雨状態でもすいすいによる素早さ上昇が発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="すいすい", item_name="ばんのうがさ")],
        team1=[Pokemon("カビゴン")],
        weather=("あめ", 99),
    )
    mon = battle.actives[0]
    # ばんのうがさがあるので素早さは2倍にならない
    assert battle.speed_calculator.calc_effective_speed(mon) == mon.stats["spe"]


def test_ばんのうがさ_ようりょくそが発動しない():
    """ばんのうがさ使用者: 晴れ状態でもようりょくそによる素早さ上昇が発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ようりょくそ", item_name="ばんのうがさ")],
        team1=[Pokemon("カビゴン")],
        weather=("はれ", 99),
    )
    mon = battle.actives[0]
    # ばんのうがさがあるので素早さは2倍にならない
    assert battle.speed_calculator.calc_effective_speed(mon) == mon.stats["spe"]


def test_ばんのうがさ_持たないポケモンは晴れ中にこおりにならない():
    """ばんのうがさを持たないポケモンは、これまで通り晴れ中はこおり状態にならない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
        weather=("はれ", 99),
    )
    target = battle.actives[0]
    result = battle.ailment_manager.apply(target, "こおり")
    assert not result, "ばんのうがさなしのポケモンが晴れ中にこおりになった"
    assert not target.ailment.is_active


def test_ばんのうがさ_晴れでかみなりの命中率低下なし():
    """ばんのうがさ攻撃側: 晴れ状態でもかみなりの命中率が50に下がらない（必中にはならない）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["かみなり"], item_name="ばんのうがさ")],
        team1=[Pokemon("カビゴン")],
        weather=("はれ", 99),
    )
    attacker = battle.actives[0]
    # ばんのうがさを持つ攻撃側に対する晴れ天候は「なし」として扱われる
    assert not battle.weather_for(attacker).sunny
    assert battle.weather.sunny


def test_ばんのうがさ_晴れでもこおり状態になる():
    """ばんのうがさ使用者: 晴れ中でも通常通りこおり状態になる（はれ_こおり防止が働かない）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ばんのうがさ")],
        team1=[Pokemon("ピカチュウ")],
        weather=("はれ", 99),
    )
    target = battle.actives[0]
    result = battle.ailment_manager.apply(target, "こおり")
    assert result, "ばんのうがさ使用者が晴れ中にこおり状態にならなかった"
    assert target.ailment.name == "こおり"


def test_ばんのうがさ_晴れでもソーラービームを溜める():
    """ばんのうがさ攻撃側: 晴れ状態でもソーラービームの自動溜めスキップが発動せず、1ターン目は溜めるだけになる"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ソーラービーム"], item_name="ばんのうがさ")],
        team1=[Pokemon("カビゴン")],
        weather=("はれ", 99),
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    hp_before = defender.hp
    t.run_move(battle, 0)  # 1ターン目: 溜め（本来なら晴れで即攻撃するはず）
    assert attacker.has_volatile("ソーラービーム")
    assert defender.hp == hp_before


def test_ばんのうがさ_晴れのほのお技強化が無効():
    """ばんのうがさ防御側: 晴れでほのお技の1.5倍補正を受けない"""
    battle = t.start_battle(
        team0=[Pokemon("ヒトカゲ", move_names=["ひのこ"])],
        team1=[Pokemon("ピカチュウ", item_name="ばんのうがさ")],
        weather=("はれ", 99),
        accuracy=100,
    )
    t.run_move(battle, 0)
    # 天候補正なし (4096 = 等倍)
    assert battle.damage_calculator.power_modifier == 4096


def test_ばんのうがさ_晴れのみず技弱化が無効():
    """ばんのうがさ防御側: 晴れでみず技の0.5倍補正を受けない"""
    battle = t.start_battle(
        team0=[Pokemon("ゼニガメ", move_names=["みずでっぽう"])],
        team1=[Pokemon("ピカチュウ", item_name="ばんのうがさ")],
        weather=("はれ", 99),
        accuracy=100,
    )
    t.run_move(battle, 0)
    # 天候補正なし (4096 = 等倍)
    assert battle.damage_calculator.power_modifier == 4096


def test_ばんのうがさ_雨でかみなりが必中にならない():
    """ばんのうがさ防御側: 雨状態でもかみなりが必中にならない"""
    # test_option.accuracy を設定すると命中率判定がスキップされるため、ここでは使用しない
    # 代わりに weather_for の返り値を直接検証する
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["かみなり"])],
        team1=[Pokemon("カビゴン", item_name="ばんのうがさ")],
        weather=("あめ", 99),
    )
    defender = battle.actives[1]
    # ばんのうがさを持つ防御側に対する雨天候は「なし」として扱われる
    assert not battle.weather_for(defender).rainy
    # 攻撃側は雨天候の恩恵を受ける（必中になるはず、ばんのうがさなし）
    assert battle.weather.rainy


def test_ばんのうがさ_雨のほのお技弱化が無効():
    """ばんのうがさ防御側: 雨でほのお技の0.5倍補正を受けない"""
    battle = t.start_battle(
        team0=[Pokemon("ヒトカゲ", move_names=["ひのこ"])],
        team1=[Pokemon("ピカチュウ", item_name="ばんのうがさ")],
        weather=("あめ", 99),
        accuracy=100,
    )
    t.run_move(battle, 0)
    # 天候補正なし (4096 = 等倍)
    assert battle.damage_calculator.power_modifier == 4096


def test_ばんのうがさ_雨のみず技強化が無効():
    """ばんのうがさ防御側: 雨でみず技の1.5倍補正を受けない"""
    battle = t.start_battle(
        team0=[Pokemon("ゼニガメ", move_names=["みずでっぽう"])],
        team1=[Pokemon("ピカチュウ", item_name="ばんのうがさ")],
        weather=("あめ", 99),
        accuracy=100,
    )
    t.run_move(battle, 0)
    # 天候補正なし (4096 = 等倍)
    assert battle.damage_calculator.power_modifier == 4096


def test_パワフルハーブ_あめ下のエレクトロビームは天候優先で消費されない():
    """パワフルハーブ: あめによる溜めスキップが優先され、アイテムは消費されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="パワフルハーブ", move_names=["エレクトロビーム"])],
        team1=[Pokemon("カビゴン")],
        weather=("あめ", 99),
        accuracy=100,
    )
    mon = battle.actives[0]
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert mon.has_item()
    assert foe.hp < foe.max_hp
    assert mon.boosts["spa"] == 1


def test_パワフルハーブ_おおひでり下のダイビングが失敗しても消費されない():
    """パワフルハーブ: おおひでりでダイビングが失敗したときはアイテムを消費しない"""
    battle = t.start_battle(
        team0=[Pokemon("カメックス", item_name="パワフルハーブ", move_names=["ダイビング"])],
        team1=[Pokemon("カビゴン")],
        weather=("おおひでり", 99),
        accuracy=100,
    )
    mon = battle.actives[0]
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert mon.has_item()
    assert foe.hp == foe.max_hp


def test_パワフルハーブ_にほんばれ下のソーラービームは天候優先で消費されない():
    """パワフルハーブ: にほんばれによる溜めスキップが優先され、アイテムは消費されない"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", item_name="パワフルハーブ", move_names=["ソーラービーム"])],
        team1=[Pokemon("カビゴン")],
        weather=("はれ", 99),
        accuracy=100,
    )
    mon = battle.actives[0]
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert mon.has_item()
    assert foe.hp < foe.max_hp


def test_パワフルハーブ_動けなくなる系の技では発動しない():
    """パワフルハーブ: ブラッドムーン/デカハンマーのように反動で動けなくなる技は
    Event.ON_MOVE_CHARGE ハンドラを自身に登録しない（＝溜め技ではない）ため、
    パワフルハーブの対象に含まれないことを確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="パワフルハーブ", move_names=["ブラッドムーン"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)
    assert mon.has_item()

    battle2 = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="パワフルハーブ", move_names=["デカハンマー"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    mon2 = battle2.actives[0]
    t.run_move(battle2, 0)
    assert mon2.has_item()


def test_パワフルハーブ_消費後は溜め技が2ターンかかる():
    """パワフルハーブ: 消費後は溜め技が通常通り2ターンかかるようになる"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", item_name="パワフルハーブ", move_names=["ソーラービーム"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    foe = battle.actives[1]

    # 1回目: パワフルハーブで即発動して消費される
    t.run_move(battle, 0)
    assert not mon.has_item()
    hp_after_first = foe.hp
    assert hp_after_first < foe.max_hp

    # 2回目: アイテムがないため通常通り1ターン目は溜めるだけでダメージを与えない
    t.run_move(battle, 0)
    assert foe.hp == hp_after_first
    assert mon.has_volatile("ソーラービーム")


def test_パワフルハーブ_溜め技をスキップ():
    """パワフルハーブ: 溜め技の溜めターンをスキップして即発動"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", item_name="パワフルハーブ", move_names=["ソーラービーム"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert not mon.has_item()
    assert foe.hp < foe.max_hp


def test_パワフルハーブ_通常技では発動しない():
    """パワフルハーブ: seed=995 (LogInconsistency) の回帰テスト。

    Event.ON_MOVE_CHARGE は move_executor.run_move が全ての技実行のたびに発火する
    汎用イベントであり、くらいつくのような溜め技ではない通常技でも発火する。
    修正前はパワフルハーブ_skip_charge が対象技の種類を判定せずに無条件でアイテムを
    消費していたため、通常技を使っただけでパワフルハーブが誤発動していた。
    """
    battle = t.start_battle(
        team0=[Pokemon("カジリガメ", item_name="パワフルハーブ", move_names=["くらいつく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)
    assert mon.has_item()
    logs = [log for log in battle.event_logger.logs if log.turn == battle.turn]
    assert not any(log.log == LogCode.ITEM_TRIGGERED for log in logs)


def test_パンチグローブ_パンチ技の威力1_1倍():
    """パンチグローブ: パンチ技の威力を1.1倍にする"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="パンチグローブ", move_names=["ほのおのパンチ"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 4506


def test_パンチグローブ_パンチ技の接触判定を無効化():
    """パンチグローブ: パンチ技の接触判定を無効化する"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="パンチグローブ", move_names=["ほのおのパンチ"])],
        team1=[Pokemon("ピカチュウ", item_name="ゴツゴツメット")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.hp == attacker.max_hp


def test_ひかりごけ_あまのじゃくでDランクが最小のとき発動しない():
    """ひかりごけ: あまのじゃく所持者はとくぼうランクがすでに最小のとき発動せず消費もしない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みずでっぽう"])],
        team1=[Pokemon("カビゴン", item_name="ひかりごけ", ability_name="あまのじゃく")],
        accuracy=100,
    )
    foe = battle.actives[1]
    foe.boosts["spd"] = -6
    t.run_move(battle, 0)
    assert foe.boosts["spd"] == -6
    assert foe.has_item()


def test_ひかりごけ_あまのじゃくでD下降():
    """ひかりごけ: あまのじゃく所持者はとくぼうが1段階下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みずでっぽう"])],
        team1=[Pokemon("カビゴン", item_name="ひかりごけ", ability_name="あまのじゃく")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.boosts["spd"] == -1
    assert not foe.has_item()


def test_ひかりごけ_かたやぶりのみず技はたんじゅんあまのじゃくでもD上昇():
    """ひかりごけ: かたやぶりの効果があるみず技に対してはたんじゅん・あまのじゃくは発動せず通常通り+1される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたやぶり", move_names=["みずでっぽう"])],
        team1=[Pokemon("カビゴン", item_name="ひかりごけ", ability_name="あまのじゃく")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.boosts["spd"] == 1
    assert not foe.has_item()


def test_ひかりごけ_たんじゅんでD2段階上昇():
    """ひかりごけ: たんじゅん所持者はとくぼうが2段階上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みずでっぽう"])],
        team1=[Pokemon("カビゴン", item_name="ひかりごけ", ability_name="たんじゅん")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.boosts["spd"] == 2
    assert not foe.has_item()


def test_ひかりごけ_とくぼうランクが最大のとき発動しない():
    """ひかりごけ: すでにとくぼうランクが最大まで上がっているときは発動せず消費もしない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["みずでっぽう"])],
        team1=[Pokemon("カビゴン", item_name="ひかりごけ")],
        accuracy=100,
    )
    foe = battle.actives[1]
    foe.boosts["spd"] = 6
    t.run_move(battle, 0)
    assert foe.boosts["spd"] == 6
    assert foe.has_item()


def test_ひかりごけ_マジシャンより先に発動して奪われない():
    """ひかりごけ: 特性マジシャンのみず技を受けても、ひかりごけが先に発動して消費されるため奪われない
    （攻撃側の素早さが防御側より高い場合でも、素早さに依存せずひかりごけが先に発動する）
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="マジシャン", move_names=["みずでっぽう"])],
        team1=[Pokemon("カビゴン", item_name="ひかりごけ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.boosts["spd"] == 1
    assert not foe.has_item()
    assert not attacker.has_item()


def test_ひかりごけ_みず以外では発動しない():
    """ひかりごけ: みず以外の技では発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", item_name="ひかりごけ")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.boosts["spd"] == 0
    assert foe.has_item()


def test_ひかりごけ_みず被弾でD上昇():
    """ひかりごけ: みず技でダメージを受けたときとくぼう+1"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なみのり"])],
        team1=[Pokemon("カビゴン", item_name="ひかりごけ")],
        accuracy=100,
    )
    foe = battle.actives[1]
    t.run_move(battle, 0)
    assert foe.boosts["spd"] == 1
    assert not foe.has_item()


def test_ひかりのこな_一撃必殺技には適用されない():
    """ひかりのこな: 一撃必殺技の命中率には影響しない（第三世代以降の仕様）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["つのドリル"])],
        team1=[Pokemon("カビゴン", item_name="ひかりのこな")],
    )
    t.run_move(battle, 0)
    assert battle.move_executor.accuracy == 30


def test_ひかりのこな_命中率が0_9倍になる():
    """ひかりのこな: 持たせた側に対する技の命中率が0.9倍になる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["さいみんじゅつ"])],
        team1=[Pokemon("カビゴン", item_name="ひかりのこな")],
    )
    move = t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy * 3686 // 4096


def test_ひかりのこな_非所持では命中率が変化しない():
    """ひかりのこな: 持っていない場合は命中率が変化しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["さいみんじゅつ"])],
        team1=[Pokemon("カビゴン")],
    )
    move = t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy


def test_ひかりのねんど_スクリーン8ターンに延長():
    """ひかりのねんど: リフレクターを8ターンに延長する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ひかりのねんど", move_names=["リフレクター"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    # ひかりのねんどによりリフレクターが8ターンに延長されている
    side = battle.get_side(battle.players[0])
    assert side.get("リフレクター").count == 8


@pytest.mark.parametrize("field_name", ["リフレクター", "ひかりのかべ", "オーロラベール"])
def test_ひかりのねんど_対象の壁を8ターンに延長(field_name):
    """ひかりのねんど: リフレクター・ひかりのかべ・オーロラベールいずれも8ターンに延長する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ひかりのねんど")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    side = battle.get_side(mon)
    side.apply(field_name, 5, source=mon)
    assert side.get(field_name).count == 8


def test_ひかりのねんど_対象外の場は延長されない():
    """ひかりのねんど: リフレクター・ひかりのかべ・オーロラベール以外の場状態は延長されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ひかりのねんど")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    side = battle.get_side(mon)
    side.apply("しんぴのまもり", 5, source=mon)
    assert side.get("しんぴのまもり").count == 5


def test_ひかりのねんど_非所持では5ターンのまま():
    """ひかりのねんど: 所持していない場合はリフレクターが5ターンで終了する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    side = battle.get_side(mon)
    side.apply("リフレクター", 5, source=mon)
    assert side.get("リフレクター").count == 5


def test_ヒメリのみ_PPが0でない場合は発動しない():
    """ヒメリのみ: 技を使ってもPPが0にならない場合は発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ヒメリのみ", move_names=["でんこうせっか"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 0)
    assert mon.moves[0].pp == 19
    assert mon.has_item()


def test_ヒメリのみ_PPが0になった技のPPを回復する():
    """ヒメリのみ: 自分の技を使ってPPが0になったとき、その技のPPが回復し消費される。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ヒメリのみ", move_names=["でんこうせっか"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    mon = battle.actives[0]
    mon.moves[0].pp = 1
    t.run_move(battle, 0)
    assert mon.moves[0].pp == 10
    assert not mon.has_item()


def test_ヒメリのみ_PPが0の技が複数ある場合は最後に使われた技を優先する():
    """ヒメリのみ: PPが0の技が複数ある場合、最後に使われた技を優先して回復する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="ヒメリのみ", move_names=["なげつける"])],
        team1=[Pokemon("ピカチュウ", move_names=["でんこうせっか", "たいあたり"])],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.moves[0].pp = 0
    defender.moves[1].pp = 0
    defender.pp_consumed_move = defender.moves[1]
    t.run_move(battle, 0)
    assert defender.moves[0].pp == 0
    assert defender.moves[1].pp == 10


def test_ヒメリのみ_うらみでPPが0になったとき発動する():
    """ヒメリのみ: うらみの効果でPPが0になったときも発動する。

    move.modify_pp は通常のPP消費経路を経由しないため、Event.ON_PP_CONSUMED を
    改めて発火する実装になっていることを確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["うらみ"])],
        team1=[Pokemon("ピカチュウ", item_name="ヒメリのみ", move_names=["でんこうせっか"])],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.moves[0].pp = 4
    defender.pp_consumed_move = defender.moves[0]
    t.run_move(battle, 0)
    assert defender.moves[0].pp == 10
    assert not defender.has_item()


def test_ヒメリのみ_ぶきみなじゅもんでPPが0になったとき発動する():
    """ヒメリのみ: ぶきみなじゅもんの追加効果でPPが0になったときも発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("フーディン", move_names=["ぶきみなじゅもん"])],
        team1=[Pokemon("ピカチュウ", item_name="ヒメリのみ", move_names=["でんこうせっか"])],
        accuracy=100,
        secondary_chance=1.0,
    )
    defender = battle.actives[1]
    defender.moves[0].pp = 3
    defender.pp_consumed_move = defender.moves[0]
    t.run_move(battle, 0)
    assert defender.moves[0].pp == 10
    assert not defender.has_item()


def test_ヒメリのみ_ぶきよう解除時にPPが0のままなら発動する():
    """ヒメリのみ: 特性ぶきようでアイテムが無効化されている間はPPが0でも発動せず、
    特性が変わって無効化が解除されたときにPPが0のままなら即座に発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ぶきよう", item_name="ヒメリのみ", move_names=["でんこうせっか"])],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    mon.moves[0].pp = 0
    battle.change_ability(mon, "せいでんき")
    assert mon.moves[0].pp == 10
    assert not mon.has_item()


def test_ヒメリのみ_ほおばるで発動してPPを回復する():
    """ヒメリのみ: ほおばるで自分のヒメリのみを強制消費したとき、PPが0の技があれば回復する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="ヒメリのみ", move_names=["ほおばる", "たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.moves[1].pp = 0
    t.run_move(battle, 0)
    assert mon.moves[1].pp == 10
    assert not mon.has_item()


def test_ヒメリのみ_マジックルーム解除時にPPが0のままなら発動する():
    """ヒメリのみ: マジックルームでアイテムが無効化されている間はPPが0でも発動せず、
    解除時にPPが0のままなら即座に発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ヒメリのみ", move_names=["でんこうせっか"])],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    battle.item_manager.add_disabled_reason(mon, "マジックルーム")
    mon.moves[0].pp = 0
    assert mon.moves[0].pp == 0
    assert mon.has_item()
    battle.item_manager.remove_disabled_reason(mon, "マジックルーム")
    assert mon.moves[0].pp == 10
    assert not mon.has_item()


def test_ヒメリのみ_むしくいで奪われて食べられたとき技のPPを回復する():
    """ヒメリのみ: むしくいで奪われて食べられたとき、奪った側の技のPPが回復する。"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["むしくい", "たいあたり"])],
        team1=[Pokemon("ピカチュウ", item_name="ヒメリのみ", move_names=["でんこうせっか"])],
        accuracy=100,
    )
    attacker = battle.actives[0]
    attacker.moves[1].pp = 0
    t.run_move(battle, 0)
    assert not battle.actives[1].has_item()
    assert attacker.moves[1].pp == 10


def test_ヒメリのみ_場に出た直後にPPが0の技があれば発動する():
    """ヒメリのみ: 場に出た直後にPPが0の技があった場合、即座に発動する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ヒメリのみ", move_names=["でんこうせっか"]),
               Pokemon("カイリュー")],
        team1=[Pokemon("カビゴン")],
    )
    switched_out = battle.actives[0]
    switched_out.moves[0].pp = 0
    t.run_switch(battle, 0, 1)
    t.run_switch(battle, 0, 0)
    mon = battle.actives[0]
    assert mon.moves[0].pp == 10
    assert not mon.has_item()


@pytest.mark.parametrize("item_name", ["おうじゃのしるし", "するどいキバ"])
def test_ひるみ付与アイテム_てんのめぐみで確率2倍(item_name):
    """おうじゃのしるし・するどいキバ: 特性てんのめぐみによりひるみ確率が2倍(20%)になる"""
    without_megumi = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name, move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.fix_random(without_megumi, 0.15)
    t.run_move(without_megumi, 0)
    assert not without_megumi.actives[1].has_volatile("ひるみ")

    with_megumi = t.start_battle(
        team0=[Pokemon(
            "ピカチュウ", item_name=item_name, ability_name="てんのめぐみ",
            move_names=["たいあたり"],
        )],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.fix_random(with_megumi, 0.15)
    t.run_move(with_megumi, 0)
    assert with_megumi.actives[1].has_volatile("ひるみ")


@pytest.mark.parametrize("item_name", ["おうじゃのしるし", "するどいキバ"])
def test_ひるみ付与アイテム_なげつけるで確実にひるませる(item_name):
    """おうじゃのしるし・するどいキバ: なげつけるで使用した場合、100%の確率で相手をひるませる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name, move_names=["なげつける"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.fix_random(battle, 0.99)
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


@pytest.mark.parametrize("item_name", ["おうじゃのしるし", "するどいキバ"])
def test_ひるみ付与アイテム_ひるまない確率(item_name):
    """おうじゃのしるし・するどいキバ: 乱数が0.1以上のときひるまない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name, move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.fix_random(battle, 0.5)
    t.run_move(battle, 0)
    assert not battle.actives[1].has_volatile("ひるみ")


@pytest.mark.parametrize("item_name", ["おうじゃのしるし", "するどいキバ"])
def test_ひるみ付与アイテム_ひるみ付与(item_name):
    """おうじゃのしるし・するどいキバ: 攻撃命中時10%の確率でひるみ付与"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name, move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert battle.actives[1].has_volatile("ひるみ")


@pytest.mark.parametrize("item_name", ["おうじゃのしるし", "するどいキバ"])
def test_ひるみ付与アイテム_りんぷんで無効化(item_name):
    """おうじゃのしるし・するどいキバ: 特性りんぷんにより効果が無効化される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name, move_names=["たいあたり"])],
        team1=[Pokemon("ニャース", ability_name="りんぷん")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert not battle.actives[1].has_volatile("ひるみ")


@pytest.mark.parametrize("item_name", ["おうじゃのしるし", "するどいキバ"])
def test_ひるみ付与アイテム_一撃必殺技には効果がない(item_name):
    """おうじゃのしるし・するどいキバ: 一撃必殺技には効果が無い（追加の乱数判定が発生しないことで確認する）

    きあいのタスキで耐えた場合の挙動も合わせて確認する。
    """
    def count_random_calls(has_item: bool) -> int:
        kwargs = {"item_name": item_name} if has_item else {}
        battle = t.start_battle(
            team0=[Pokemon("ピカチュウ", move_names=["じわれ"], **kwargs)],
            team1=[Pokemon("ピカチュウ", item_name="きあいのタスキ")],
            accuracy=100,
        )
        count = 0

        def counting_random() -> float:
            nonlocal count
            count += 1
            return 0.5

        battle.random.random = counting_random
        t.run_move(battle, 0)
        assert battle.actives[1].hp == 1
        return count

    assert count_random_calls(True) == count_random_calls(False)


@pytest.mark.parametrize("item_name", ["おうじゃのしるし", "するどいキバ"])
def test_ひるみ付与アイテム_元々ひるみ効果がある技には重複しない(item_name):
    """おうじゃのしるし・するどいキバ: 元々ひるみの追加効果がある技（エアスラッシュ等）には
    重複して効果が発動しない（追加の乱数判定が発生しないことで確認する）"""
    def count_random_calls(has_item: bool) -> int:
        kwargs = {"item_name": item_name} if has_item else {}
        battle = t.start_battle(
            team0=[Pokemon("ピカチュウ", move_names=["エアスラッシュ"], **kwargs)],
            team1=[Pokemon("ピカチュウ")],
            accuracy=100,
        )
        count = 0

        def counting_random() -> float:
            nonlocal count
            count += 1
            return 0.5

        battle.random.random = counting_random
        t.run_move(battle, 0)
        return count

    assert count_random_calls(True) == count_random_calls(False)


@pytest.mark.parametrize("item_name", ["おうじゃのしるし", "するどいキバ"])
def test_ひるみ付与アイテム_変化技では発動しない(item_name):
    """おうじゃのしるし・するどいキバ: 変化技では発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name, move_names=["でんじは"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.fix_random(battle, 0.0)
    t.run_move(battle, 0)
    assert not battle.actives[1].has_volatile("ひるみ")


def test_ビビリだま_あまのじゃく所持者はこうげき上昇時にすばやさが下がる():
    """ビビリだま: あまのじゃく所持者はいかくでこうげきが上昇し、ビビリだまの効果も反転してすばやさが下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="あまのじゃく", item_name="ビビリだま")],
        team1=[Pokemon("ピカチュウ", ability_name="いかく")],
    )
    mon = battle.actives[0]
    assert mon.boosts["atk"] == 1
    assert mon.boosts["spe"] == -1
    assert not mon.has_item()


def test_ビビリだま_いかくでS上昇():
    """ビビリだま: いかくによってこうげきが下がったときすばやさ+1"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ビビリだま")],
        team1=[Pokemon("ピカチュウ", ability_name="いかく")],
    )
    mon = battle.actives[0]
    assert mon.boosts["spe"] == 1
    assert mon.boosts["atk"] == -1
    assert not mon.has_item()


def test_ビビリだま_クリアボディでいかくが無効化されても発動する():
    """ビビリだま: クリアボディでこうげき低下自体は防がれても、ビビリだまは発動する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="クリアボディ", item_name="ビビリだま")],
        team1=[Pokemon("カビゴン", ability_name="いかく")],
    )
    mon = battle.actives[0]
    assert mon.boosts["atk"] == 0
    assert mon.boosts["spe"] == 1
    assert not mon.has_item()


def test_ビビリだま_こうげきが最低ランクで変化しない場合は発動しない():
    """ビビリだま: こうげきが既に最低ランクでいかくが不発だった場合は発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ビビリだま")],
        team1=[Pokemon("ピカチュウ"), Pokemon("コラッタ", ability_name="いかく")],
    )
    mon = battle.actives[0]
    mon.boosts["atk"] = -6
    t.run_switch(battle, 1, 1)
    assert mon.boosts["atk"] == -6
    assert mon.boosts["spe"] == 0
    assert mon.has_item()


def test_ビビリだま_すばやさが最大ランクの場合は発動しない():
    """ビビリだま: すばやさが既に最大ランクの場合は発動・消費されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ビビリだま")],
        team1=[Pokemon("ピカチュウ"), Pokemon("コラッタ", ability_name="いかく")],
    )
    mon = battle.actives[0]
    mon.boosts["spe"] = 6
    t.run_switch(battle, 1, 1)
    assert mon.boosts["atk"] == -1
    assert mon.boosts["spe"] == 6
    assert mon.has_item()


def test_ビビリだま_ミラーアーマー所持者自身は跳ね返した時点では発動しない():
    """ビビリだま: ミラーアーマーでいかくを跳ね返した時点ではビビリだまは発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ミラーアーマー", item_name="ビビリだま")],
        team1=[Pokemon("カビゴン", ability_name="いかく")],
    )
    mon = battle.actives[0]
    assert mon.boosts["atk"] == 0
    assert mon.boosts["spe"] == 0
    assert mon.has_item()


def test_ピントレンズ_急所ランク加算():
    """ピントレンズ: 急所ランクを+1する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ピントレンズ", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    t.fix_random(battle, 0.5)  # 急所が出ない程度に固定（0.5 < 急所ランク+1の閾値以下）
    t.run_move(battle, 0)
    assert battle.move_executor.critical_rank == 1


@pytest.mark.parametrize(
    "nature",
    ["ずぶとい", "ひかえめ", "おだやか", "おくびょう"]
)
def test_フィラのみ_こうげきが上がりにくい性格でこんらんする(nature):
    """フィラのみ: からい味が嫌いな性格（こうげきが上がりにくい）は発動と同時にこんらんする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="フィラのみ", nature=nature)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.hp == mon.max_hp // 4 + mon.max_hp // 3
    assert not mon.has_item()
    assert mon.has_volatile("こんらん")


def test_フィラのみ_それ以外の性格ではこんらんしない():
    """フィラのみ: からい味が嫌いでない性格では発動してもこんらんしない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="フィラのみ", nature="まじめ")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)
    assert mon.hp == mon.max_hp // 4 + mon.max_hp // 3
    assert not mon.has_item()
    assert not mon.has_volatile("こんらん")


@pytest.mark.parametrize("item_name", ["エレキシード", "グラスシード", "サイコシード", "ミストシード"])
def test_フィールドシード_フィールドなしでは発動しない(item_name):
    """フィールドシード系: 対応フィールドがないとき発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.boosts["def"] == 0
    assert mon.boosts["spd"] == 0
    assert mon.has_item()


@pytest.mark.parametrize("item_name, terrain, stat", [
    ("エレキシード", "エレキフィールド", "def"),
    ("グラスシード", "グラスフィールド", "def"),
    ("サイコシード", "サイコフィールド", "spd"),
    ("ミストシード", "ミストフィールド", "spd"),
])
def test_フィールドシード_ランク最大時は消費しない(item_name, terrain, stat):
    """フィールドシード系: 対応能力ランクがすでに最大のときは発動せずアイテムも消費されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name)],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    battle.modify_stats(mon, {stat: 6})
    battle.terrain_manager.apply(terrain, 5)
    assert mon.boosts[stat] == 6
    assert mon.has_item()


@pytest.mark.parametrize("item_name, terrain, stat", [
    ("エレキシード", "エレキフィールド", "def"),
    ("グラスシード", "グラスフィールド", "def"),
    ("サイコシード", "サイコフィールド", "spd"),
    ("ミストシード", "ミストフィールド", "spd"),
])
def test_フィールドシード_発動(item_name, terrain, stat):
    """フィールドシード系: 対応フィールド展開時に登場してランク+1"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name=item_name)],
        team1=[Pokemon("ピカチュウ")],
        terrain=(terrain, 5),
    )
    mon = battle.actives[0]
    assert mon.boosts[stat] == 1
    assert not mon.has_item()


def test_フィールドシード_自身の特性による地形形成では二重発動しない():
    """フィールドシード系: 自身が持つ特性（ハドロンエンジン等）が登場と同時にフィールドを
    展開するケースで、ネストしたON_FIELD_CHANGEで1回発動した後にON_SWITCH_INの
    ハンドラ一覧スナップショットに残る自身の登録が再度実行されて二重発動しないことを確認する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ハドロンエンジン", item_name="エレキシード")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert battle.terrain.name == "エレキフィールド"
    assert mon.boosts["def"] == 1
    assert not mon.has_item()


def test_ふうせん_じめん技を無効化():
    """ふうせん: 浮遊状態でじめん技が当たらない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ふうせん")],
        team1=[Pokemon("ゼニガメ", move_names=["じしん"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 1)
    assert mon.hp == mon.max_hp


def test_ふうせん_じゅうりょく下では浮遊が無効になる():
    """ふうせん: じゅうりょく状態では浮遊効果が打ち消されじめん技が命中する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ふうせん")],
        team1=[Pokemon("ゼニガメ", move_names=["じしん"])],
        field={"じゅうりょく": 5},
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 1)
    assert mon.hp < mon.max_hp


def test_ふうせん_ダメージが0でも割れる():
    """ふうせん: ダメージ量が0でも攻撃技が有効に命中していれば割れる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ふうせん")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.fix_damage(battle, 0)
    t.run_move(battle, 1)
    assert not mon.has_item()


def test_ふうせん_ダメージを受けると割れる():
    """ふうせん: ダメージを受けるとアイテムが消費される"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ふうせん")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 1)
    assert not mon.has_item()


def test_ふうせん_ぶきようで無効化される():
    """ふうせん: 特性ぶきようによりアイテム効果が失われ、じめん技が命中する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ふうせん", ability_name="ぶきよう")],
        team1=[Pokemon("ゼニガメ", move_names=["じしん"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 1)
    assert mon.hp < mon.max_hp


def test_ふうせん_みがわりが肩代わりしても割れる():
    """ふうせん: みがわりが攻撃を肩代わりした場合でも本体が有効な攻撃を受けたことになり割れる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ふうせん")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "みがわり", hp=100)
    t.run_move(battle, 1)
    assert mon.hp == mon.max_hp
    assert not mon.has_item()


def test_ふうせん_変化技では割れない():
    """ふうせん: 変化技を受けてもアイテムは消費されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ふうせん")],
        team1=[Pokemon("ピカチュウ", move_names=["なきごえ"])],
        accuracy=100,
    )
    mon = battle.actives[0]
    t.run_move(battle, 1)
    assert mon.has_item()


def test_フォーカスレンズ_一撃必殺技には適用されない():
    """フォーカスレンズ: 一撃必殺技の命中率には影響しない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="フォーカスレンズ", move_names=["つのドリル"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    battle.step()
    assert battle.move_executor.accuracy == 30


def test_フォーカスレンズ_交代直後の相手には効果がない():
    """フォーカスレンズ: そのターンに交代してきたばかりで技を未使用の相手には効果がない（第五世代以降の仕様）"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="フォーカスレンズ", move_names=["さいみんじゅつ"])],
        team1=[Pokemon("ピカチュウ"), Pokemon("コイル")],
    )
    t.reserve_command(battle, command0=Command.MOVE_0, command1=Command.SWITCH_1)
    battle.step()
    move = battle.actives[0].moves[0]
    assert battle.move_executor.accuracy == move.accuracy


def test_フォーカスレンズ_先攻なら命中率が変化しない():
    """フォーカスレンズ: 相手がまだそのターンに行動していない場合は命中率が変化しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="フォーカスレンズ", move_names=["さいみんじゅつ"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    move = t.run_move(battle, 0)
    assert battle.move_executor.accuracy == move.accuracy


def test_フォーカスレンズ_後攻なら命中率が1_2倍になる():
    """フォーカスレンズ: すでに行動している相手に対して使う技の命中率が1.2倍になる"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="フォーカスレンズ", move_names=["さいみんじゅつ"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    battle.step()
    move = battle.actives[0].moves[0]
    assert battle.move_executor.accuracy == move.accuracy * 4915 // 4096


def test_フォーカスレンズ_非所持では命中率が変化しない():
    """フォーカスレンズ: 持っていない場合は命中率が変化しない"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["さいみんじゅつ"])],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
    )
    battle.step()
    move = battle.actives[0].moves[0]
    assert battle.move_executor.accuracy == move.accuracy


def test_ブーストエナジー_かがくへんかガスで特性無効化中でもトリックで奪えない():
    """ブーストエナジー: こだいかっせい/クォークチャージがかがくへんかガスで
    無効化されているときでも、トリックによる授受は防がれる
    (.internal/spec/abilities/クォークチャージ.md 「特性が変更されたり、無効化されたり
    しているときでも...ブーストエナジーが渡る効果や、奪う効果は無効となる」)。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かがくへんかガス", move_names=["トリック"])],
        team1=[Pokemon("カビゴン", ability_name="クォークチャージ", item_name="ブーストエナジー")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    assert defender.ability.name == ""  # ガスで無効化されている
    t.run_move(battle, 0)
    assert not attacker.has_item()
    assert defender.item.name == "ブーストエナジー"


def test_ブーストエナジー_こだいかっせいマジックルーム解除後に発動():
    """ブーストエナジー: マジックルーム解除後にこだいかっせいブーストが発動する"""
    battle = t.start_battle(
        team0=[Pokemon("コライドン", ability_name="こだいかっせい", item_name="ブーストエナジー")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    # マジックルーム下ではアイテムが無効で、ブーストが発動していないはず
    battle.item_manager.add_disabled_reason(mon, "マジックルーム")
    assert mon.paradox_boost_stat is None or mon.paradox_boost_source == "item"
    # マジックルーム解除後にブーストが発動する
    battle.item_manager.remove_disabled_reason(mon, "マジックルーム")
    assert mon.paradox_boost_stat is not None
    assert mon.paradox_boost_source == "item"


def test_ブーストエナジー_こだいかっせい登場時に発動():
    """ブーストエナジー: こだいかっせい持ちが登場時にブーストを発動する"""
    battle = t.start_battle(
        team0=[Pokemon("コライドン", ability_name="こだいかっせい", item_name="ブーストエナジー")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.paradox_boost_stat is not None
    assert mon.paradox_boost_source == "item"
    assert not mon.has_item()


def test_ブーストエナジー_バトル中に取得すると即座に発動する():
    """ブーストエナジー: バトル中にアイテムを新たに取得すると即座にブーストが発動する"""
    battle = t.start_battle(
        team0=[Pokemon("コライドン", ability_name="こだいかっせい")],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    assert mon.paradox_boost_stat is None
    battle.item_manager.gain_item(mon, "ブーストエナジー")
    assert mon.paradox_boost_stat is not None
    assert mon.paradox_boost_source == "item"
    assert not mon.has_item()


def test_ブーストエナジー_パラドックス特性を持たないポケモンが取得しても発動しない():
    """ブーストエナジー: こだいかっせい/クォークチャージを持たないポケモンが取得しても何も起きない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    battle.item_manager.gain_item(mon, "ブーストエナジー")
    assert mon.paradox_boost_stat is None
    assert mon.has_item("ブーストエナジー")


def test_ブーストエナジー_パラドックス特性持ちからトリックで奪えない():
    """ブーストエナジー: こだいかっせい/クォークチャージ持ちが持っている間はトリック・すりかえで交換されない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="エレキメイカー", move_names=["トリック"], item_name="たべのこし")],
        team1=[Pokemon("カビゴン", ability_name="クォークチャージ", item_name="ブーストエナジー")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    assert defender.has_item("ブーストエナジー")
    t.run_move(battle, 0)
    assert attacker.item.name == "たべのこし"
    assert defender.item.name == "ブーストエナジー"


@pytest.mark.parametrize("move_name", ["はたきおとす", "どろぼう"])
def test_ブーストエナジー_パラドックス特性持ちから奪えない(move_name):
    """ブーストエナジー: こだいかっせい/クォークチャージ持ちが持っている間ははたきおとす・どろぼう等で奪われない。
    エレキメイカーは登場時優先度がクォークチャージの判定より先に発動するため、
    同時に登場させることでエレキフィールドを発動源にし、アイテムを未消費のまま維持できる。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="エレキメイカー", move_names=[move_name])],
        team1=[Pokemon("カビゴン", ability_name="クォークチャージ", item_name="ブーストエナジー")],
        accuracy=100,
    )
    defender = battle.actives[1]
    assert defender.has_item("ブーストエナジー")
    t.run_move(battle, 0)
    assert defender.has_item("ブーストエナジー")


def test_ブーストエナジー_パラドックス特性持ちへトリックで渡せない():
    """ブーストエナジー: こだいかっせい/クォークチャージ持ちへはトリック等で渡すことができない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["トリック"], item_name="ブーストエナジー")],
        team1=[Pokemon("カビゴン", ability_name="クォークチャージ", item_name="たべのこし")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert attacker.item.name == "ブーストエナジー"
    assert defender.item.name == "たべのこし"


def test_ホズのみ_あくタイプのどろぼうでは発動せず奪われる():
    """ホズのみ: どろぼうはあくタイプのため発動せず、アイテムは奪われる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["どろぼう"])],
        team1=[Pokemon("エーフィ", item_name="ホズのみ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert not defender.has_item()
    assert attacker.has_item()  # どろぼうでの奪取は成功する


def test_ホズのみ_ノーマルスキンで変化したはたきおとすで威力補正を保ったままダメージ半減():
    """ホズのみ: ノーマルスキンでノーマル化したはたきおとすを受けても、威力補正は維持されたままダメージが半減する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ノーマルスキン", move_names=["はたきおとす"])],
        team1=[Pokemon("カビゴン", item_name="ホズのみ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert battle.damage_calculator.power_modifier == 7372  # ノーマルスキン補正と持ち物所持による1.5倍が両方乗る
    assert battle.damage_calculator.damage_modifier == 2048  # ダメージは半減される
    assert not defender.has_item()  # ホズのみの効果で消費済み（はたきおとすの除去は不発）


def test_ホズのみ_ノーマル技のダメージを半減して消費する():
    """ホズのみ: 効果バツグンでなくてもノーマル技を受けたらダメージを半減して消費する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", item_name="ホズのみ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert battle.damage_calculator.damage_modifier == 2048
    assert not defender.has_item()


def test_ホズのみ_ほしがるでは奪われない():
    """ホズのみ: ノーマルタイプのほしがるを受けた場合、先に消費されるため奪われない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["ほしがる"])],
        team1=[Pokemon("エーフィ", item_name="ホズのみ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert not defender.has_item()  # ホズのみの効果で消費済み
    assert not attacker.has_item()  # ほしがるでの奪取は失敗する


def test_ホズのみ_わるあがきでは発動しない():
    """ホズのみ: わるあがきはタイプを持たないため発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["わるあがき"])],
        team1=[Pokemon("カビゴン", item_name="ホズのみ")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert battle.damage_calculator.damage_modifier == 4096
    assert defender.has_item()


def test_ぼうごパット_かたいツメの威力補正は防がない():
    """ぼうごパット: 自分の技が接触技であることに由来する効果（かたいツメ）は防がない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="かたいツメ", item_name="ぼうごパット", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    t.run_move(battle, 0)
    assert 5325 == battle.damage_calculator.power_modifier


def test_ぼうごパット_ゴツゴツメットのダメージを防ぐ():
    """ぼうごパット: 相手が接触を受けたことに反応する持ち物（ゴツゴツメット）の効果を防ぐ"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ぼうごパット", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", item_name="ゴツゴツメット")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.hp == attacker.max_hp


def test_ぼうごパット_さまようたましいの特性交換を防ぐ():
    """ぼうごパット: 相手が接触を受けたことに反応する特性（さまようたましい）の効果を防ぐ"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="いかく", item_name="ぼうごパット", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="さまようたましい")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    t.run_move(battle, 0)
    assert attacker.ability.name == "いかく"
    assert defender.ability.name == "さまようたましい"


def test_ぼうごパット_さめはだのダメージを防ぐ():
    """ぼうごパット: 相手が接触を受けたことに反応する特性（さめはだ）の効果を防ぐ"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ぼうごパット", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", ability_name="さめはだ")],
        accuracy=100,
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert attacker.hp == attacker.max_hp


def test_ぼうごパット_どくしゅの追加効果は防がない():
    """ぼうごパット: 自分の技が接触技であることに由来する効果（どくしゅ）は防がない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="どくしゅ", item_name="ぼうごパット", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ")],
    )
    defender = battle.actives[1]
    battle.random.random = lambda: 0.0
    t.run_move(battle, 0)
    assert defender.has_ailment("どく")


def test_ぼうごパット_もふもふのダメージ半減は防がない():
    """ぼうごパット: ぼうごパットの効果対象外である相手のもふもふによるダメージ半減は防げない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ぼうごパット", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="もふもふ")],
    )
    t.run_move(battle, 0)
    assert 2048 == battle.damage_calculator.damage_modifier


def test_ぼうごパット_わるいてぐせによるアイテム強奪は防げない():
    """ぼうごパット: ぼうごパットの効果対象外である相手のわるいてぐせによってぼうごパットを奪われる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ぼうごパット", move_names=["たいあたり"])],
        team1=[Pokemon("ピカチュウ", ability_name="わるいてぐせ")],
    )
    attacker = battle.actives[0]
    t.run_move(battle, 0)
    assert not attacker.has_item()


def test_ぼうじんゴーグル_天候ダメージを無効化():
    """ぼうじんゴーグル: すなあらしによるターン終了ダメージを無効化する"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ぼうじんゴーグル")],
        team1=[Pokemon("ピカチュウ")],
        weather=("すなあらし", 5),
    )
    mon = battle.actives[0]
    initial_hp = mon.max_hp
    t.end_turn(battle)
    assert mon.hp == initial_hp


def test_ぼうじんゴーグル_特性ほうしによる状態異常を無効化():
    """ぼうじんゴーグル: 接触した相手の特性ほうし(Effect Spore)による状態異常を無効化する"""
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="ほうし")],
        team1=[Pokemon("ピカチュウ", move_names=["たいあたり"], item_name="ぼうじんゴーグル")],
        accuracy=100,
    )
    battle.random.random = lambda: 0.0
    t.run_move(battle, 1)
    assert not battle.actives[1].ailment.is_active


def test_ぼうじんゴーグル_特性ぼうじんと同時に持つ場合は特性側が優先():
    """ぼうじんゴーグル: 特性ぼうじんを併せ持つ場合、特性側の無効化が優先されアイテムは公開されない"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", move_names=["ねむりごな"])],
        team1=[Pokemon("ピカチュウ", ability_name="ぼうじん", item_name="ぼうじんゴーグル")],
        accuracy=100,
    )
    defender = battle.actives[1]
    t.run_move(battle, 0)
    assert defender.ailment.name != "ねむり"
    assert not defender.item.revealed


def test_ぼうじんゴーグル_粉技を無効化():
    """ぼうじんゴーグル: 粉技（ねむりごな等）を無効化する"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", move_names=["ねむりごな"])],
        team1=[Pokemon("ピカチュウ", item_name="ぼうじんゴーグル")],
        accuracy=100,
    )
    t.run_move(battle, 0)
    assert battle.actives[1].ailment.name != "ねむり"


def test_ぼうじんゴーグル_粉技を無効化した際にアイテムが公開される():
    """ぼうじんゴーグル: 粉技を無効化した際にアイテムが公開される"""
    battle = t.start_battle(
        team0=[Pokemon("フシギダネ", move_names=["ねむりごな"])],
        team1=[Pokemon("ピカチュウ", item_name="ぼうじんゴーグル")],
        accuracy=100,
    )
    defender = battle.actives[1]
    assert not defender.item.revealed
    t.run_move(battle, 0)
    assert defender.item.revealed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
