"""致死率計算（core/lethal.py）のテスト

ダメージ計算の参考値
1. A150 ガブリアス -> H166/B115 カイリュー
1.1 ドラゴンテール 90~108 (確定2発)
1.2 スケイルショット 38~48/hit (4hit: 乱数1発 81.91%, 5hit: 確定1発)
1.3 たいあたり 20~24 (低威力技、確定数の乱数比較には非使用)

2. A150 ガブリアス -> H166/B115 カイリュー 特性マルチスケイル
2.1 ドラゴンテール 45~54 (確定2発)
2.2 スケイルショット 19~24/hit (4hit: 乱数1発 0.01%, 5hit: 確定1発)

3. タイプ半減きのみ
3.1 A150 ガブリアス -> H140/B80 エーフィ（エスパー）: かみくだく(あく2倍) 114~136
    ナモのみ適用後1発目: 57~68, 2発目: 114~136
3.2 A150 ガブリアス -> H166/B115 カイリュー: たいあたり(ノーマル等倍) 20~24
    ホズのみ適用後1発目: 10~12, 2発目: 20~24
3.3 A150 ガブリアス -> H45/B40 フシギダネ（くさ/どく）: かえんほうしゃ(ほのお2倍) 80~96
    オッカのみ適用後1発目: 40~48, 2発目: 80~96
3.4 A150 ガブリアス -> H41/B55 ミニリュウ（ドラゴン）: こおりのつぶて(こおり2倍) 70~84
    ヤチェのみ適用後1発目: 35~42, 2発目: 70~84
3.5 A150 ガブリアス -> H41/B55 ミニリュウ（ドラゴン）: マジカルシャイン(フェアリー2倍) 88~104
    ロゼルのみ適用後1発目: 44~52, 2発目: 88~104
"""
import pytest

from jpoke import Pokemon, Move
from jpoke.core import lethal as core_lethal
from jpoke.core.lethal import LethalContext
from jpoke.utils.lethal_dist import State, to_dist

from . import test_utils as t


def test_Gのちから_ぼうぎょダウン_secondary有り():
    """Gのちから: secondary=True のとき相手のぼうぎょが1段階下がり、2発目のダメージが増加する"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    results = t.calc_lethal(battle, atk_idx=0, moves=Move("Gのちから"), max_attack=2, secondary=True)
    assert results[1].min_damage > results[0].min_damage


def test_Gのちから_ぼうぎょダウン_secondary無し():
    """Gのちから: secondary=False のときはぼうぎょダウンが発動せず2発目のダメージが変わらない"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    results = t.calc_lethal(battle, atk_idx=0, moves=Move("Gのちから"), max_attack=2, secondary=False)
    assert results[1].min_damage == results[0].min_damage


def test_アイスボディ_ゆき天気でターン終了時回復():
    """アイスボディ所持時、ゆき天気のターン終了時に最大HPの1/16を回復する"""
    with_ability = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", ability_name="アイスボディ")],
        weather=("ゆき", 5),
    )
    without_ability = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
        weather=("ゆき", 5),
    )

    results_with = t.calc_lethal(with_ability, atk_idx=0, moves=Move("たいあたり"), max_attack=2)
    results_without = t.calc_lethal(without_ability, atk_idx=0, moves=Move("たいあたり"), max_attack=2)

    max_hp = with_ability.actives[1].max_hp
    heal = max(1, max_hp // 16)
    assert max(results_with[1].hp_counter) - max(results_without[1].hp_counter) == heal * 2


def test_アクアリング_ターン終了時回復():
    """アクアリング状態のポケモンはターン終了時に最大HPの1/16を回復する"""
    with_volatile = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
        volatile1={"アクアリング": 5},
    )
    without_volatile = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )

    results_with = t.calc_lethal(with_volatile, atk_idx=0, moves=Move("たいあたり"), max_attack=2)
    results_without = t.calc_lethal(without_volatile, atk_idx=0, moves=Move("たいあたり"), max_attack=2)

    max_hp = with_volatile.actives[1].max_hp
    heal = max(1, max_hp // 16)
    assert max(results_with[1].hp_counter) - max(results_without[1].hp_counter) == heal * 2


def test_アシッドボム_とくぼうダウン():
    """アシッドボム: 命中後に相手のとくぼうが2段階下がるため2発目のダメージが増加する"""
    battle = t.start_battle(
        team0=[Pokemon("カイリュー")],
        team1=[Pokemon("カビゴン")],
    )
    results = t.calc_lethal(battle, atk_idx=0, moves=Move("アシッドボム"), max_attack=2)
    assert results[1].min_damage > results[0].min_damage


def test_アッキのみ_ちからずくの対象技では発動しない():
    """ちからずく所持者の追加効果あり物理技を受けてもアッキのみは発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス", ability_name="ちからずく")],
        team1=[Pokemon("カイリュー", item_name="アッキのみ")],
    )
    # かみなりパンチ（物理・追加効果あり）で2回攻撃
    results = t.calc_lethal(battle, atk_idx=0, moves=[(Move("かみなりパンチ"), 1)], max_attack=2)

    assert len(results) == 2
    # ランクが変わらないため1発目と2発目のダメージが同じ
    assert results[0].min_damage == results[1].min_damage
    assert results[0].max_damage == results[1].max_damage


def test_アッキのみ_消費後は発動しない():
    """アッキのみは1回だけ発動し、2発目以降は効果がない（2発目と3発目のダメージが同じ）"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", item_name="アッキのみ")],
    )
    # たいあたり（低威力）で3回攻撃。カイリューは3発では倒れない
    results = t.calc_lethal(battle, atk_idx=0, moves=[(Move("たいあたり"), 1)], max_attack=3)

    assert len(results) == 3
    # 1発目: アッキのみ未発動（rank 0）
    assert results[0].min_damage == 20
    assert results[0].max_damage == 24
    # 2発目と3発目のダメージが同じ（消費後は再発動しない）
    assert results[1].min_damage == results[2].min_damage
    assert results[1].max_damage == results[2].max_damage
    # 2発目はぼうぎょ+1が乗るため1発目より少ない
    assert results[1].max_damage < results[0].min_damage


def test_アッキのみ_物理技受けた後ぼうぎょ上昇():
    """物理技を受けた直後にぼうぎょ+1し、2発目のダメージが減少する"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", item_name="アッキのみ")],
    )
    results = t.calc_lethal(battle, atk_idx=0, moves=[(Move("ドラゴンテール"), 1)], max_attack=2)

    # 1発目: アッキのみ未発動（rank 0）、ガブA150 vs カイリューB115
    assert results[0].min_damage == 90
    assert results[0].max_damage == 108
    # 2発目: ぼうぎょ+1（rank +1: × 3/2 補正）でダメージが減少
    assert results[1].min_damage == 62
    assert results[1].max_damage == 74


def test_アッキのみ_特殊技では発動しない():
    """特殊技を受けてもアッキのみは発動せず、2発目のダメージが1発目と変わらない"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", item_name="アッキのみ")],
    )
    # りゅうのはどう（ドラゴン特殊技）で2回攻撃
    results = t.calc_lethal(battle, atk_idx=0, moves=[(Move("りゅうのはどう"), 1)], max_attack=2)

    assert len(results) == 2
    # ランクが変わらないため1発目と2発目のダメージが同じ
    assert results[0].min_damage == results[1].min_damage
    assert results[0].max_damage == results[1].max_damage


def test_あめうけざら_あめ天気でターン終了時回復():
    """あめうけざら所持時、あめ天気のターン終了時に最大HPの1/16を回復する"""
    with_ability = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", ability_name="あめうけざら")],
        weather=("あめ", 5),
    )
    without_ability = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
        weather=("あめ", 5),
    )

    results_with = t.calc_lethal(with_ability, atk_idx=0, moves=Move("たいあたり"), max_attack=2)
    results_without = t.calc_lethal(without_ability, atk_idx=0, moves=Move("たいあたり"), max_attack=2)

    max_hp = with_ability.actives[1].max_hp
    heal = max(1, max_hp // 16)
    assert max(results_with[1].hp_counter) - max(results_without[1].hp_counter) == heal * 2


def test_イアのみ_HP4分の1以下で回復():
    """イアのみ所持時、HP が 1/4 以下になると max_hp の 1/3 回復する。

    たいあたり(20-24)を7回撃つと、最小ダメージ経路では7発目で HP が 1/4 以下に落ちて回復する。
    アイテムなしとの最大 HP 差が int(max_hp * 1/3) = 55 になることを確認する。
    """
    with_item = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", item_name="イアのみ")],
    )
    without_item = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )

    results_with = t.calc_lethal(with_item, atk_idx=0, moves=[(Move("たいあたり"), 1)], max_attack=7)
    results_without = t.calc_lethal(without_item, atk_idx=0, moves=[(Move("たいあたり"), 1)], max_attack=7)

    max_hp = with_item.actives[1].max_hp  # 166
    heal = max(1, int(max_hp * 1 / 3))   # 55
    assert max(results_with[-1].hp_counter) - max(results_without[-1].hp_counter) == heal


def test_うずしお_バインド付与():
    """うずしおは命中後にバインドを付与し、ターン終了時ダメージが発生する（バインド事前付与と同じ結果）"""
    battle_move = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    battle_pre = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
        volatile1={"バインド": 5},
    )
    results_move = t.calc_lethal(battle_move, atk_idx=0, moves=Move("うずしお"), max_attack=2)
    results_pre = t.calc_lethal(battle_pre, atk_idx=0, moves=Move("うずしお"), max_attack=2)
    assert max(results_move[1].hp_counter) == max(results_pre[1].hp_counter)


def test_うたかたのアリア_やけど回復_secondary有り():
    """うたかたのアリア: secondary=True のとき命中後にやけど状態を治し、以降ターン終了時ダメージが発生しなくなる"""
    battle_secondary = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    battle_no_secondary = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    t.apply_ailment(battle_secondary, active_index=1, ailment_name="やけど")
    t.apply_ailment(battle_no_secondary, active_index=1, ailment_name="やけど")

    results_with = t.calc_lethal(battle_secondary, atk_idx=0, moves=Move("うたかたのアリア"), max_attack=2, secondary=True)
    results_without = t.calc_lethal(battle_no_secondary, atk_idx=0, moves=Move("うたかたのアリア"), max_attack=2, secondary=False)
    max_hp = battle_secondary.actives[1].max_hp
    burn_damage = max(1, max_hp // 16)
    assert max(results_with[1].hp_counter) - max(results_without[1].hp_counter) == burn_damage * 2


def test_エレクトロビーム_とくこうアップ_secondary有り():
    """エレクトロビーム: secondary=True のときチャージ前にとくこうが1段階上がり、2発目のダメージが増加する"""
    battle = t.start_battle(
        team0=[Pokemon("カイリュー")],
        team1=[Pokemon("カビゴン")],
    )
    results = t.calc_lethal(battle, atk_idx=0, moves=Move("エレクトロビーム"), max_attack=2, secondary=True)
    assert results[1].min_damage > results[0].min_damage


def test_エレクトロビーム_とくこうアップ_secondary無し():
    """エレクトロビーム: secondary=False のときとくこうアップが発動せず2発目のダメージが変わらない"""
    battle = t.start_battle(
        team0=[Pokemon("カイリュー")],
        team1=[Pokemon("カビゴン")],
    )
    results = t.calc_lethal(battle, atk_idx=0, moves=Move("エレクトロビーム"), max_attack=2, secondary=False)
    assert results[1].min_damage == results[0].min_damage


def test_オボンのみ_スケイルショット5発_乱数1発():
    """オボンのみ所持時、多段技はヒットごとにHP半分以下判定・回復が発生するため
    5発目終了時点でも乱数1発 (80.31%) になる"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", item_name="オボンのみ")],
    )
    results = t.calc_lethal(battle, atk_idx=0, moves=[(Move("スケイルショット"), 5)])

    assert results[-1].n_attack == 1
    assert results[-1].hit == 5
    assert results[-1].lethal_probability == pytest.approx(0.8031, abs=0.001)


def test_オボンのみ_乱数2発():
    """オボンのみ所持時、HPが半分以下になった1発目で回復するため乱数2になる"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", item_name="オボンのみ")],
    )
    results = t.calc_lethal(battle, atk_idx=0, moves=[(Move("ドラゴンテール"), 1)])

    assert results[0].min_damage == 90
    assert results[0].max_damage == 108
    assert results[-1].n_attack == 2
    assert results[-1].lethal_probability == pytest.approx(0.0585, abs=0.001)


def test_おやこあい_2ヒット目ダメージ加算():
    """おやこあい: 単発攻撃技の命中後、2ヒット目（1/4ダメージ、最低1）が加算される"""
    with_ability = t.start_battle(
        team0=[Pokemon("ガブリアス", ability_name="おやこあい")],
        team1=[Pokemon("カイリュー")],
    )
    without_ability = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    results_with = t.calc_lethal(with_ability, atk_idx=0, moves=Move("たいあたり"), max_attack=1)
    results_without = t.calc_lethal(without_ability, atk_idx=0, moves=Move("たいあたり"), max_attack=1)

    # baseline: 20~24
    assert results_without[0].min_damage == 20
    assert results_without[0].max_damage == 24
    # おやこあい: 2ヒット目（1/4）加算 → 20+5=25, 24+6=30
    assert results_with[0].min_damage == 25
    assert results_with[0].max_damage == 30


def test_オレンのみ_HP2分の1以下で10回復():
    """オレンのみ所持時、HP が 1/2 以下になると 10 固定回復する。

    ドラゴンテール(90-108)を1回撃つと HP が 1/2 以下になり、全状態で回復が発動する。
    アイテムなしとの最大 HP 差が 10 になることを確認する。
    """
    with_item = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", item_name="オレンのみ")],
    )
    without_item = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )

    results_with = t.calc_lethal(with_item, atk_idx=0, moves=[(Move("ドラゴンテール"), 1)])
    results_without = t.calc_lethal(without_item, atk_idx=0, moves=[(Move("ドラゴンテール"), 1)])

    assert max(results_with[0].hp_counter) - max(results_without[0].hp_counter) == 10


def test_オーバーヒート_とくこうダウン():
    """オーバーヒート: 命中後にとくこうが2段階下がるため2発目のダメージが減少する"""
    battle = t.start_battle(
        team0=[Pokemon("カイリュー")],
        team1=[Pokemon("カビゴン")],
    )
    results = t.calc_lethal(battle, atk_idx=0, moves=Move("オーバーヒート"), max_attack=2)
    assert results[1].min_damage < results[0].min_damage


def test_かんそうはだ_あめで回復():
    """かんそうはだ: あめ天気のターン終了時に最大HPの1/8を回復する"""
    with_ability = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", ability_name="かんそうはだ")],
        weather=("あめ", 5),
    )
    without_ability = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
        weather=("あめ", 5),
    )
    results_with = t.calc_lethal(with_ability, atk_idx=0, moves=Move("たいあたり"), max_attack=2)
    results_without = t.calc_lethal(without_ability, atk_idx=0, moves=Move("たいあたり"), max_attack=2)

    max_hp = with_ability.actives[1].max_hp
    heal = max(1, max_hp // 8)
    assert max(results_with[1].hp_counter) - max(results_without[1].hp_counter) == heal * 2


def test_かんそうはだ_はれでダメージ():
    """かんそうはだ: はれ天気のターン終了時に最大HPの1/8ダメージを受ける"""
    with_ability = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", ability_name="かんそうはだ")],
        weather=("はれ", 5),
    )
    without_ability = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
        weather=("はれ", 5),
    )
    results_with = t.calc_lethal(with_ability, atk_idx=0, moves=Move("たいあたり"), max_attack=2)
    results_without = t.calc_lethal(without_ability, atk_idx=0, moves=Move("たいあたり"), max_attack=2)

    max_hp = with_ability.actives[1].max_hp
    damage = max(1, max_hp // 8)
    assert max(results_without[1].hp_counter) - max(results_with[1].hp_counter) == damage * 2


def test_がんじょう_リーサル計算全体で正しく発動する():
    """calc_lethal 経由の一連の処理でも、がんじょうの登録（data/ability.py）が
    正しく機能してHP1で耐えることを確認する（実戦形式の統合テスト）。"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス", level=100)],
        team1=[Pokemon("トゲピー", level=1, ability_name="がんじょう")],
    )
    results = t.calc_lethal(battle, atk_idx=0, moves=Move("じしん"), max_attack=1)

    assert results[0].lethal_probability == 0.0
    assert min(results[0].hp_counter) == 1


def test_がんじょう_満タンからHP1で耐える():
    """がんじょう: HPが満タンの状態で一撃ひんしになるダメージを受けても、HP1で耐える。

    _apply_damage を直接呼び出すホワイトボックステスト。ctx.damage_dist に致死量の
    固定値を設定し、HP満タンの hp_dist を与えたときに ON_APPLY_DAMAGE ハンドラ
    （がんじょう_survive_lethal）が正しく発動することを確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", ability_name="がんじょう")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    max_hp = defender.max_hp

    ctx = LethalContext(attacker, defender, Move("たいあたり"))
    ctx.damage_dist = to_dist(max_hp * 10)
    hp_dist = to_dist(max_hp)

    result = core_lethal._apply_damage(battle, ctx, hp_dist)

    assert set(result) == {State(1)}


def test_がんじょう_満タンでなければ発動しない():
    """がんじょう: HPが満タンでない状態では、一撃ひんしになるダメージに対して発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", ability_name="がんじょう")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    max_hp = defender.max_hp

    ctx = LethalContext(attacker, defender, Move("たいあたり"))
    ctx.damage_dist = to_dist(max_hp * 10)
    hp_dist = to_dist(max_hp - 1)

    result = core_lethal._apply_damage(battle, ctx, hp_dist)

    assert set(result) == {State(0)}


def test_がんじょうときあいのタスキ_がんじょうが優先():
    """がんじょうときあいのタスキを両方持つ場合、がんじょうが先に発動し、
    きあいのタスキは消費されない（item_enabled は True のまま）。"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", ability_name="がんじょう", item_name="きあいのタスキ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    max_hp = defender.max_hp

    ctx = LethalContext(attacker, defender, Move("たいあたり"))
    ctx.damage_dist = to_dist(max_hp * 10)
    hp_dist = to_dist(max_hp)

    result = core_lethal._apply_damage(battle, ctx, hp_dist)

    assert set(result) == {State(1)}


def test_きあいのタスキ_満タンからHP1で耐えて消費():
    """きあいのタスキ: HPが満タンの状態で一撃ひんしになるダメージをHP1で耐え、消費する
    （item_enabled が False になる）。"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", item_name="きあいのタスキ")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    max_hp = defender.max_hp

    ctx = LethalContext(attacker, defender, Move("たいあたり"))
    ctx.damage_dist = to_dist(max_hp * 10)
    hp_dist = to_dist(max_hp)

    result = core_lethal._apply_damage(battle, ctx, hp_dist)

    assert set(result) == {State(1, item_enabled=False)}


def test_キラースピン_どく付与_secondary有り():
    """キラースピン: secondary=True のとき命中後にどく状態を付与し、ターン終了時ダメージが発生する"""
    battle_secondary = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    battle_no_secondary = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    results_with = t.calc_lethal(battle_secondary, atk_idx=0, moves=Move("キラースピン"), max_attack=2, secondary=True)
    results_without = t.calc_lethal(battle_no_secondary, atk_idx=0, moves=Move("キラースピン"), max_attack=2, secondary=False)
    max_hp = battle_secondary.actives[1].max_hp
    poison_damage = max(1, max_hp // 8)
    assert max(results_without[1].hp_counter) - max(results_with[1].hp_counter) == poison_damage * 2


def test_くろいヘドロ_どくタイプは毎ターン回復():
    """くろいヘドロ所持のどくタイプポケモンは、ターン終了時に最大HPの1/16を回復する。"""
    with_item = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("アーボック", item_name="くろいヘドロ")],
    )
    without_item = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("アーボック")],
    )

    results_with = t.calc_lethal(with_item, atk_idx=0, moves=[(Move("たいあたり"), 1)], max_attack=2)
    results_without = t.calc_lethal(without_item, atk_idx=0, moves=[(Move("たいあたり"), 1)], max_attack=2)

    heal = with_item.actives[1].max_hp // 16
    assert (
        max(results_with[1].hp_counter) - max(results_without[1].hp_counter)
        == heal * 2
    )


def test_くろいヘドロ_非どくタイプは毎ターンダメージ():
    """くろいヘドロ所持の非どくタイプポケモンは、ターン終了時に最大HPの1/8のダメージを受ける。"""
    with_item = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", item_name="くろいヘドロ")],
    )
    without_item = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )

    results_with = t.calc_lethal(with_item, atk_idx=0, moves=[(Move("たいあたり"), 1)], max_attack=2)
    results_without = t.calc_lethal(without_item, atk_idx=0, moves=[(Move("たいあたり"), 1)], max_attack=2)

    damage = with_item.actives[1].max_hp // 8
    assert (
        max(results_without[1].hp_counter) - max(results_with[1].hp_counter)
        == damage * 2
    )


def test_グラスフィールド_接地ポケモンのターン終了時回復():
    """グラスフィールド中、接地しているポケモンはターン終了時に最大HPの1/16を回復する"""
    with_terrain = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("アーボック")],
        terrain=("グラスフィールド", 5),
    )
    without_terrain = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("アーボック")],
    )

    results_with = t.calc_lethal(with_terrain, atk_idx=0, moves=Move("たいあたり"), max_attack=2)
    results_without = t.calc_lethal(without_terrain, atk_idx=0, moves=Move("たいあたり"), max_attack=2)

    max_hp = with_terrain.actives[1].max_hp
    heal = max(1, max_hp // 16)
    assert max(results_with[1].hp_counter) - max(results_without[1].hp_counter) == heal * 2


def test_しおづけ_ターン終了時ダメージ():
    """しおづけ状態の非みず・はがねタイプはターン終了時に最大HPの1/16ダメージを受ける"""
    with_volatile = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
        volatile1={"しおづけ": 5},
    )
    without_volatile = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )

    results_with = t.calc_lethal(with_volatile, atk_idx=0, moves=Move("たいあたり"), max_attack=2)
    results_without = t.calc_lethal(without_volatile, atk_idx=0, moves=Move("たいあたり"), max_attack=2)

    max_hp = with_volatile.actives[1].max_hp
    damage = max(1, max_hp // 16)
    assert max(results_without[1].hp_counter) - max(results_with[1].hp_counter) == damage * 2


def test_しおづけ技_しおづけ付与_secondary有り():
    """しおづけ（技）: secondary=True のとき命中後にしおづけ状態を付与し、ターン終了時ダメージが発生する"""
    battle_secondary = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    battle_no_secondary = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    results_with = t.calc_lethal(battle_secondary, atk_idx=0, moves=Move("しおづけ"), max_attack=2, secondary=True)
    results_without = t.calc_lethal(battle_no_secondary, atk_idx=0, moves=Move("しおづけ"), max_attack=2, secondary=False)
    max_hp = battle_secondary.actives[1].max_hp
    damage = max(1, max_hp // 16)
    assert max(results_without[1].hp_counter) - max(results_with[1].hp_counter) == damage * 2


def test_しめつける_バインド付与():
    """しめつけるは命中後にバインドを付与し、ターン終了時ダメージが発生する（バインド事前付与と同じ結果）"""
    battle_move = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    battle_pre = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
        volatile1={"バインド": 5},
    )
    results_move = t.calc_lethal(battle_move, atk_idx=0, moves=Move("しめつける"), max_attack=2)
    results_pre = t.calc_lethal(battle_pre, atk_idx=0, moves=Move("しめつける"), max_attack=2)
    assert max(results_move[1].hp_counter) == max(results_pre[1].hp_counter)


def test_しんぴのちから_とくこうアップ_secondary有り():
    """しんぴのちから: secondary=True のとき命中後にとくこうが1段階上がり、2発目のダメージが増加する"""
    battle = t.start_battle(
        team0=[Pokemon("カイリュー")],
        team1=[Pokemon("カビゴン")],
    )
    results = t.calc_lethal(battle, atk_idx=0, moves=Move("しんぴのちから"), max_attack=2, secondary=True)
    assert results[1].min_damage > results[0].min_damage


def test_しんぴのちから_とくこうアップ_secondary無し():
    """しんぴのちから: secondary=False のときとくこうアップが発動せず2発目のダメージが変わらない"""
    battle = t.start_battle(
        team0=[Pokemon("カイリュー")],
        team1=[Pokemon("カビゴン")],
    )
    results = t.calc_lethal(battle, atk_idx=0, moves=Move("しんぴのちから"), max_attack=2, secondary=False)
    assert results[1].min_damage == results[0].min_damage


def test_じきゅうりょく_物理技受けるとぼうぎょ上昇():
    """じきゅうりょく: 物理技を受けるたびにぼうぎょが+1され、2発目のダメージが減少する"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", ability_name="じきゅうりょく")],
    )
    results = t.calc_lethal(battle, atk_idx=0, moves=Move("ドラゴンテール"), max_attack=2)

    # 1発目: B rank 0
    assert results[0].min_damage == 90
    assert results[0].max_damage == 108
    # 2発目: ぼうぎょ+1（rank +1: ×3/2補正）でダメージが減少
    assert results[1].min_damage == 62
    assert results[1].max_damage == 74


def test_すなあらし_非いわじめんはがねタイプにダメージ():
    """すなあらし天気中、いわ・じめん・はがね以外のポケモンはターン終了時に最大HPの1/16ダメージを受ける"""
    with_weather = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
        weather=("すなあらし", 5),
    )
    without_weather = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )

    results_with = t.calc_lethal(with_weather, atk_idx=0, moves=Move("たいあたり"), max_attack=2)
    results_without = t.calc_lethal(without_weather, atk_idx=0, moves=Move("たいあたり"), max_attack=2)

    max_hp = with_weather.actives[1].max_hp
    damage = max(1, max_hp // 16)
    assert max(results_without[1].hp_counter) - max(results_with[1].hp_counter) == damage * 2


def test_すなじごく_バインド付与():
    """すなじごくは命中後にバインドを付与し、ターン終了時ダメージが発生する（バインド事前付与と同じ結果）"""
    battle_move = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    battle_pre = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
        volatile1={"バインド": 5},
    )
    results_move = t.calc_lethal(battle_move, atk_idx=0, moves=Move("すなじごく"), max_attack=2)
    results_pre = t.calc_lethal(battle_pre, atk_idx=0, moves=Move("すなじごく"), max_attack=2)
    assert max(results_move[1].hp_counter) == max(results_pre[1].hp_counter)


@pytest.mark.parametrize("item_name, move_name, defender_name, dmg1_min, dmg1_max, dmg2_min, dmg2_max", [
    # オッカのみ（ほのお）: フシギダネ（くさ/どく） → ほのお2倍
    ("オッカのみ", "かえんほうしゃ", "フシギダネ", 40, 48, 80, 96),
    # ヤチェのみ（こおり）: ミニリュウ（ドラゴン） → こおり2倍
    ("ヤチェのみ", "こおりのつぶて", "ミニリュウ", 35, 42, 70, 84),
    # ロゼルのみ（フェアリー）: ミニリュウ（ドラゴン） → フェアリー2倍
    ("ロゼルのみ", "マジカルシャイン", "ミニリュウ", 44, 52, 88, 104),
])
def test_タイプ半減きのみ_代表種(item_name, move_name, defender_name,
                               dmg1_min, dmg1_max, dmg2_min, dmg2_max):
    """タイプ半減きのみ: 効果抜群技の1発目が半減され、2発目は通常ダメージになる"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon(defender_name, item_name=item_name)],
    )
    results = t.calc_lethal(battle, atk_idx=0, moves=Move(move_name), max_attack=3)

    assert results[0].min_damage == dmg1_min
    assert results[0].max_damage == dmg1_max
    assert results[1].min_damage == dmg2_min
    assert results[1].max_damage == dmg2_max


def test_たべのこし_ターン終了時に回復():
    """たべのこし所持時、ターン終了時に最大HPの1/16回復した状態が次の攻撃に引き継がれる"""
    with_item = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", item_name="たべのこし")]
    )
    without_item = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )

    # ドラゴンテールは確定2発でカイリューを倒すため、たべのこしの回復量を
    # 検証できるよう威力の低いたいあたりで2発目までHPが残る状況を作る
    results_with_item = t.calc_lethal(
        with_item, atk_idx=0, moves=[(Move("たいあたり"), 1)], max_attack=2,
    )
    results_without_item = t.calc_lethal(
        without_item, atk_idx=0, moves=[(Move("たいあたり"), 1)], max_attack=2,
    )

    # ターン終了時のたべのこし回復は1発目・2発目それぞれの直後に発生するため、
    # 2発目終了時点のHP分布は最大HPの1/16 x 2 だけ高くなる
    leftover_heal = with_item.actives[1].max_hp // 16
    assert (
        max(results_with_item[1].hp_counter) - max(results_without_item[1].hp_counter)
        == leftover_heal * 2
    )


def test_タラプのみ_ちからずくの対象技では発動しない():
    """ちからずく所持者の追加効果あり特殊技を受けてもタラプのみは発動しない。"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス", ability_name="ちからずく")],
        team1=[Pokemon("カイリュー", item_name="タラプのみ")],
    )
    # でんきショック（特殊・追加効果あり）で2回攻撃
    results = t.calc_lethal(battle, atk_idx=0, moves=[(Move("でんきショック"), 1)], max_attack=2)

    # ランクが変わらないため1発目と2発目のダメージが同じ
    assert results[0].min_damage == results[1].min_damage
    assert results[0].max_damage == results[1].max_damage


def test_タラプのみ_物理技では発動しない():
    """物理技を受けてもタラプのみは発動せず、2発目のダメージが変わらない。"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", item_name="タラプのみ")],
    )
    results = t.calc_lethal(battle, atk_idx=0, moves=[(Move("ドラゴンテール"), 1)], max_attack=2)

    # ランクが変わらないため1発目と2発目のダメージが同じ
    assert results[0].min_damage == results[1].min_damage
    assert results[0].max_damage == results[1].max_damage


def test_タラプのみ_特殊技受けた後とくぼう上昇():
    """特殊技を受けた直後にとくぼう+1し、2発目のダメージが減少する。"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", item_name="タラプのみ")],
    )
    results = t.calc_lethal(battle, atk_idx=0, moves=[(Move("りゅうのはどう"), 1)], max_attack=2)

    # 1発目: タラプのみ未発動、A150ガブリアス C110 vs D120カイリュー
    assert results[0].min_damage == 84
    assert results[0].max_damage == 98
    # 2発目: とくぼう+1 (D120→D180相当) でダメージ減少
    assert results[1].min_damage == 54
    assert results[1].max_damage == 66


def test_テラスシェル_満タン時タイプ相性を等倍に丸める():
    """テラスシェル: HPが満タンのとき、等倍以上の相性の技を受けると相性が等倍(1x)に丸められ
    ダメージが半減する。HPが満タンでなければ通常通りのダメージを受ける。"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", ability_name="テラスシェル")],
    )
    results = t.calc_lethal(battle, atk_idx=0, moves=[(Move("たいあたり"), 1)], max_attack=2)

    assert results[0].min_damage == 10
    assert results[0].max_damage == 12
    assert results[1].min_damage == 20
    assert results[1].max_damage == 24


def test_どく_ターン終了時ダメージ():
    """どく状態のポケモンはターン終了時に最大HPの1/8ダメージを受ける"""
    with_ailment = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    without_ailment = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    t.apply_ailment(with_ailment, active_index=1, ailment_name="どく")

    results_with = t.calc_lethal(with_ailment, atk_idx=0, moves=Move("たいあたり"), max_attack=2)
    results_without = t.calc_lethal(without_ailment, atk_idx=0, moves=Move("たいあたり"), max_attack=2)

    max_hp = with_ailment.actives[1].max_hp
    damage = max(1, max_hp // 8)
    assert max(results_without[1].hp_counter) - max(results_with[1].hp_counter) == damage * 2


def test_ナモのみ_抜群ダメージ半減():
    """ナモのみ: あく抜群技の1発目が半減され、2発目は通常ダメージになる"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("エーフィ", item_name="ナモのみ")],
    )
    # かみくだく（あく物理）: エーフィはエスパー単タイプ → あく2倍
    results = t.calc_lethal(battle, atk_idx=0, moves=Move("かみくだく"), max_attack=3)

    # 1発目: ナモのみで半減（57~68）
    assert results[0].min_damage == 57
    assert results[0].max_damage == 68
    # 2発目以降: アイテム消費済みで通常ダメージ（114~136）
    assert results[1].min_damage == 114
    assert results[1].max_damage == 136


def test_ナモのみ_非抜群では発動しない():
    """ナモのみ: 効果バツグンでないあく技では lethal ハンドラが発動しない
    （ただし通常ハンドラは発火し続けるため、非抜群時は全打でダメージが揃う）"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カビゴン", item_name="ナモのみ")],
    )
    # かみくだく（あく）vs カビゴン（ノーマル）: あく vs ノーマル = 等倍
    results = t.calc_lethal(battle, atk_idx=0, moves=Move("かみくだく"), max_attack=2)

    # lethal ハンドラが発動しないため、1発目と2発目のダメージが同じ
    assert results[0].min_damage == results[1].min_damage
    assert results[0].max_damage == results[1].max_damage


def test_ねをはる_ターン終了時回復():
    """ねをはる状態のポケモンはターン終了時に最大HPの1/16を回復する"""
    with_volatile = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
        volatile1={"ねをはる": 5},
    )
    without_volatile = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )

    results_with = t.calc_lethal(with_volatile, atk_idx=0, moves=Move("たいあたり"), max_attack=2)
    results_without = t.calc_lethal(without_volatile, atk_idx=0, moves=Move("たいあたり"), max_attack=2)

    max_hp = with_volatile.actives[1].max_hp
    heal = max(1, max_hp // 16)
    assert max(results_with[1].hp_counter) - max(results_without[1].hp_counter) == heal * 2


def test_のろい_ターン終了時ダメージ():
    """のろい状態のポケモンはターン終了時に最大HPの1/4ダメージを受ける"""
    with_volatile = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
        volatile1={"のろい": 5},
    )
    without_volatile = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )

    results_with = t.calc_lethal(with_volatile, atk_idx=0, moves=Move("たいあたり"), max_attack=2)
    results_without = t.calc_lethal(without_volatile, atk_idx=0, moves=Move("たいあたり"), max_attack=2)

    max_hp = with_volatile.actives[1].max_hp
    damage = max(1, max_hp // 4)
    assert max(results_without[1].hp_counter) - max(results_with[1].hp_counter) == damage * 2


def test_バインド_ターン終了時ダメージ():
    """バインド状態のポケモンはターン終了時にbind_damage_ratio（デフォルト1/8）のダメージを受ける"""
    with_volatile = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
        volatile1={"バインド": 5},
    )
    without_volatile = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )

    results_with = t.calc_lethal(with_volatile, atk_idx=0, moves=Move("たいあたり"), max_attack=2)
    results_without = t.calc_lethal(without_volatile, atk_idx=0, moves=Move("たいあたり"), max_attack=2)

    max_hp = with_volatile.actives[1].max_hp
    damage = max(1, int(max_hp / 8))
    assert max(results_without[1].hp_counter) - max(results_with[1].hp_counter) == damage * 2


def test_ばかぢから_こうげきダウン():
    """ばかぢから: 命中後にこうげきが1段階下がるため2発目のダメージが減少する"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    results = t.calc_lethal(battle, atk_idx=0, moves=Move("ばかぢから"), max_attack=2)
    assert results[1].min_damage < results[0].min_damage


def test_ばけのかわ_2発目は通常ダメージ():
    """ばけのかわ: 1発目後はability_enabledがFalseになり、2発目以降は通常ダメージ"""
    with_ability = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("ミミッキュ", ability_name="ばけのかわ")],
    )
    without_ability = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("ミミッキュ")],
    )

    results_with = t.calc_lethal(with_ability, atk_idx=0, moves=Move("ドラゴンテール"), max_attack=5)
    results_without = t.calc_lethal(without_ability, atk_idx=0, moves=Move("ドラゴンテール"), max_attack=5)

    # 2発目以降は通常ダメージと同じ
    assert results_with[1].min_damage == results_without[0].min_damage
    assert results_with[1].max_damage == results_without[0].max_damage


def test_ばけのかわ_初回攻撃を無効化():
    """ばけのかわ: 初回攻撃を無効化し、変身解除ダメージ(max_hp/8)のみ受ける"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("ミミッキュ", ability_name="ばけのかわ")],
    )
    max_hp = battle.actives[1].max_hp
    disguise_damage = max(1, max_hp // 8)

    results = t.calc_lethal(battle, atk_idx=0, moves=Move("ドラゴンテール"), max_attack=5)

    # 1発目: ダメージ分布が0（攻撃は無効化される）
    assert results[0].min_damage == 0
    assert results[0].max_damage == 0
    # 1発目後のHP = max_hp - 変身解除ダメージのみ
    assert max(results[0].hp_counter) == max_hp - disguise_damage
    # 1発目後: 全状態でability_enabledがFalseになる
    assert all(not state.ability_enabled for state in results[0].hp_dist)


def test_フレアソング_とくこうアップ_secondary有り():
    """フレアソング: secondary=True のとき命中後にとくこうが1段階上がり、2発目のダメージが増加する"""
    battle = t.start_battle(
        team0=[Pokemon("カイリュー")],
        team1=[Pokemon("カビゴン")],
    )
    results = t.calc_lethal(battle, atk_idx=0, moves=Move("フレアソング"), max_attack=2, secondary=True)
    assert results[1].min_damage > results[0].min_damage


def test_フレアソング_とくこうアップ_secondary無し():
    """フレアソング: secondary=False のときとくこうアップが発動せず2発目のダメージが変わらない"""
    battle = t.start_battle(
        team0=[Pokemon("カイリュー")],
        team1=[Pokemon("カビゴン")],
    )
    results = t.calc_lethal(battle, atk_idx=0, moves=Move("フレアソング"), max_attack=2, secondary=False)
    assert results[1].min_damage == results[0].min_damage


def test_ホズのみ_ノーマル技ダメージ半減():
    """ホズのみ: ノーマルタイプ技のダメージが半減され（抜群不要）、2発目は通常ダメージになる"""
    with_item = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", item_name="ホズのみ")],
    )
    without_item = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    move = Move("たいあたり")
    r_with = t.calc_lethal(with_item, atk_idx=0, moves=move, max_attack=3)
    r_without = t.calc_lethal(without_item, atk_idx=0, moves=move, max_attack=3)

    # 1発目: ホズのみで半減（10~12）
    assert r_with[0].min_damage == 10
    assert r_with[0].max_damage == 12
    # 2発目: アイテム消費済みで通常ダメージ（20~24）
    assert r_with[1].min_damage == 20
    assert r_with[1].max_damage == 24
    # ホズのみなしと同じ通常ダメージ
    assert r_with[1].min_damage == r_without[1].min_damage
    assert r_with[1].max_damage == r_without[1].max_damage


def test_ほのおのうず_バインド付与():
    """ほのおのうずは命中後にバインドを付与し、ターン終了時ダメージが発生する（バインド事前付与と同じ結果）"""
    battle_move = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    battle_pre = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
        volatile1={"バインド": 5},
    )
    results_move = t.calc_lethal(battle_move, atk_idx=0, moves=Move("ほのおのうず"), max_attack=2)
    results_pre = t.calc_lethal(battle_pre, atk_idx=0, moves=Move("ほのおのうず"), max_attack=2)
    assert max(results_move[1].hp_counter) == max(results_pre[1].hp_counter)


def test_ほのおのムチ_ぼうぎょダウン_secondary有り():
    """ほのおのムチ: secondary=True のとき相手のぼうぎょが1段階下がり、2発目のダメージが増加する"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    results = t.calc_lethal(battle, atk_idx=0, moves=Move("ほのおのムチ"), max_attack=2, secondary=True)
    assert results[1].min_damage > results[0].min_damage


def test_ほのおのムチ_ぼうぎょダウン_secondary無し():
    """ほのおのムチ: secondary=False のときはぼうぎょダウンが発動せず2発目のダメージが変わらない"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    results = t.calc_lethal(battle, atk_idx=0, moves=Move("ほのおのムチ"), max_attack=2, secondary=False)
    assert results[1].min_damage == results[0].min_damage


def test_ポイズンヒール_どく状態でターン終了時回復():
    """ポイズンヒール所持のどく状態ポケモンは、ターン終了時に最大HPの1/8を回復する"""
    with_ability = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", ability_name="ポイズンヒール")],
    )
    without_ability = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    t.apply_ailment(with_ability, active_index=1, ailment_name="どく")

    results_with = t.calc_lethal(with_ability, atk_idx=0, moves=Move("たいあたり"), max_attack=2)
    results_without = t.calc_lethal(without_ability, atk_idx=0, moves=Move("たいあたり"), max_attack=2)

    max_hp = with_ability.actives[1].max_hp
    heal = max(1, max_hp // 8)
    assert max(results_with[1].hp_counter) - max(results_without[1].hp_counter) == heal * 2


def test_マルチスケイル_ダメージ半減():
    """マルチスケイル所持時、HP満タンの1発目のみダメージが半減する"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", ability_name="マルチスケイル")],
    )
    results = t.calc_lethal(battle, atk_idx=0, moves=[(Move("ドラゴンテール"), 1)])

    assert results[-1].n_attack == 3
    assert results[0].min_damage == 45
    assert results[0].max_damage == 54
    assert results[1].min_damage == 90
    assert results[1].max_damage == 108
    assert results[2].lethal_probability == 1.0


def test_マルチスケイル_満タン非満タン混在時も枝ごとに正しく半減():
    """満タン枝と非満タン枝が混在する hp_dist でも、_update_hp（最小値代表）に依存せず
    枝ごとにマルチスケイルの半減が正しく適用されることを確認する回帰テスト。

    参考値（ファイル冒頭のコメント参照）: たいあたり 20~24（半減後 10~12）。
    """
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", ability_name="マルチスケイル")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    max_hp = defender.max_hp

    ctx = LethalContext(attacker, defender, Move("たいあたり"))
    hp_dist = {
        State(max_hp): 1,      # 満タン枝: マルチスケイルが発動し半減する
        State(max_hp - 1): 1,  # 非満タン枝: 発動せず通常通りのダメージを受ける
    }

    core_lethal._calc_damage_dist(battle, ctx, hp_dist)

    # 満タン枝用のダメージ分布のみ半減されている
    assert ctx.damage_dist_full is not None
    assert min(s.value for s in ctx.damage_dist_full) == 10
    assert max(s.value for s in ctx.damage_dist_full) == 12
    assert min(s.value for s in ctx.damage_dist) == 20
    assert max(s.value for s in ctx.damage_dist) == 24

    # 枝ごとに正しいダメージ分布が適用されて hp_dist に反映される
    result = core_lethal._apply_damage(battle, ctx, hp_dist)
    result_values = {s.value for s in result}
    expected_full = {max_hp - d for d in range(10, 13)}
    expected_other = {(max_hp - 1) - d for d in range(20, 25)}
    assert result_values == expected_full | expected_other


def test_もうどく_増加ダメージ():
    """もうどく状態のポケモンはターン終了時に経過ターンに応じて増加するダメージを受ける"""
    with_ailment = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    without_ailment = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    t.apply_ailment(with_ailment, active_index=1, ailment_name="もうどく")

    results_with = t.calc_lethal(with_ailment, atk_idx=0, moves=Move("たいあたり"), max_attack=2)
    results_without = t.calc_lethal(without_ailment, atk_idx=0, moves=Move("たいあたり"), max_attack=2)

    max_hp = with_ailment.actives[1].max_hp
    d1 = max(1, max_hp * 1 // 16)
    d2 = max(1, max_hp * 2 // 16)
    assert max(results_without[1].hp_counter) - max(results_with[1].hp_counter) == d1 + d2


def test_やけど_ターン終了時ダメージ():
    """やけど状態のポケモンはターン終了時に最大HPの1/16ダメージを受ける"""
    with_ailment = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    without_ailment = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    t.apply_ailment(with_ailment, active_index=1, ailment_name="やけど")

    results_with = t.calc_lethal(with_ailment, atk_idx=0, moves=Move("たいあたり"), max_attack=2)
    results_without = t.calc_lethal(without_ailment, atk_idx=0, moves=Move("たいあたり"), max_attack=2)

    max_hp = with_ailment.actives[1].max_hp
    damage = max(1, max_hp // 16)
    assert max(results_without[1].hp_counter) - max(results_with[1].hp_counter) == damage * 2


def test_やどりぎのタネ_ターン終了時ダメージ():
    """やどりぎのタネ状態のポケモンはターン終了時に最大HPの1/8ダメージを受ける"""
    with_volatile = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
        volatile1={"やどりぎのタネ": 5},
    )
    without_volatile = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )

    results_with = t.calc_lethal(with_volatile, atk_idx=0, moves=Move("たいあたり"), max_attack=2)
    results_without = t.calc_lethal(without_volatile, atk_idx=0, moves=Move("たいあたり"), max_attack=2)

    max_hp = with_volatile.actives[1].max_hp
    damage = max(1, max_hp // 8)
    assert max(results_without[1].hp_counter) - max(results_with[1].hp_counter) == damage * 2


def test_りゅうせいぐん_とくこうダウン():
    """りゅうせいぐん: 命中後にとくこうが2段階下がるため2発目のダメージが減少する"""
    battle = t.start_battle(
        team0=[Pokemon("カイリュー")],
        team1=[Pokemon("カビゴン")],
    )
    results = t.calc_lethal(battle, atk_idx=0, moves=Move("りゅうせいぐん"), max_attack=2)
    assert results[1].min_damage < results[0].min_damage


def test_りんごさん_とくぼうダウン_secondary有り():
    """りんごさん: secondary=True のとき相手のとくぼうが1段階下がり、2発目のダメージが増加する"""
    battle = t.start_battle(
        team0=[Pokemon("カイリュー")],
        team1=[Pokemon("カビゴン")],
    )
    results = t.calc_lethal(battle, atk_idx=0, moves=Move("りんごさん"), max_attack=2, secondary=True)
    assert results[1].min_damage > results[0].min_damage


def test_りんごさん_とくぼうダウン_secondary無し():
    """りんごさん: secondary=False のときはとくぼうダウンが発動せず2発目のダメージが変わらない"""
    battle = t.start_battle(
        team0=[Pokemon("カイリュー")],
        team1=[Pokemon("カビゴン")],
    )
    results = t.calc_lethal(battle, atk_idx=0, moves=Move("りんごさん"), max_attack=2, secondary=False)
    assert results[1].min_damage == results[0].min_damage


def test_リーフストーム_とくこうダウン():
    """リーフストーム: 命中後にとくこうが2段階下がるため2発目のダメージが減少する"""
    battle = t.start_battle(
        team0=[Pokemon("カイリュー")],
        team1=[Pokemon("カビゴン")],
    )
    results = t.calc_lethal(battle, atk_idx=0, moves=Move("リーフストーム"), max_attack=2)
    assert results[1].min_damage < results[0].min_damage


def test_ルミナコリジョン_とくぼうダウン():
    """ルミナコリジョン: 命中後に相手のとくぼうが2段階下がるため2発目のダメージが増加する"""
    battle = t.start_battle(
        team0=[Pokemon("カイリュー")],
        team1=[Pokemon("カビゴン")],
    )
    results = t.calc_lethal(battle, atk_idx=0, moves=Move("ルミナコリジョン"), max_attack=2)
    assert results[1].min_damage > results[0].min_damage


def test_れんごく_やけど付与_secondary有り():
    """れんごく: secondary=True のとき命中後にやけど状態を付与し、ターン終了時ダメージが発生する"""
    battle_secondary = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    battle_no_secondary = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    results_with = t.calc_lethal(battle_secondary, atk_idx=0, moves=Move("れんごく"), max_attack=2, secondary=True)
    results_without = t.calc_lethal(battle_no_secondary, atk_idx=0, moves=Move("れんごく"), max_attack=2, secondary=False)
    max_hp = battle_secondary.actives[1].max_hp
    burn_damage = max(1, max_hp // 16)
    assert max(results_without[1].hp_counter) - max(results_with[1].hp_counter) == burn_damage * 2


def test_多段技_ヒットごとに分布を記録():
    """スケイルショットのような多段技は、ヒットごとに LethalResult が積まれる"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", ability_name="マルチスケイル")],
    )
    results = t.calc_lethal(battle, atk_idx=0, moves=[(Move("スケイルショット"), 4)])

    assert [r.hit for r in results] == [1, 2, 3, 4]
    assert all(r.n_attack == 1 for r in results)
    assert results[0].min_damage == 19
    assert results[0].max_damage == 24


def test_多段技マルチスケイル_1ヒット目のみ半減():
    """多段技はヒットごとにHPが実際に更新されるため、マルチスケイルはHP満タンの
    1ヒット目のみ発動し、2ヒット目以降はダメージが半減されない"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", ability_name="マルチスケイル")],
    )
    results = t.calc_lethal(battle, atk_idx=0, moves=[(Move("スケイルショット"), 4)])

    assert results[0].min_damage == 19
    assert results[0].max_damage == 24
    for r in results[1:]:
        assert r.min_damage == 38
        assert r.max_damage == 48


def test_特性道具なし():
    """特性・道具の影響がない場合、確定数どおりに致死率が変化する"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    results = t.calc_lethal(battle, atk_idx=0, moves=[(Move("ドラゴンテール"), 1)])

    assert results[-1].n_attack == 2
    assert results[-1].lethal_probability == 1.0
    assert results[0].min_damage == 90
    assert results[0].max_damage == 108


def test_複数技_順に使用():
    """moves にリストを渡すと、1回の攻撃機会で技を順番に使用する"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", ability_name="マルチスケイル")],
    )
    results = t.calc_lethal(
        battle, atk_idx=0, moves=[(Move("ドラゴンテール"), 1), (Move("ドラゴンクロー"), 1)],
    )

    assert results[0].n_attack == 1
    assert results[0].move.name == "ドラゴンテール"
    assert results[1].n_attack == 1
    assert results[1].move.name == "ドラゴンクロー"
    assert results[-1].n_attack == 1
    assert results[-1].lethal_probability == pytest.approx(0.9453, abs=0.001)
