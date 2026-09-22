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
from jpoke.core.lethal import LethalContext, LethalMonitor
from jpoke.data.move import MOVES
from jpoke.enums import LethalEvent
from jpoke.handlers import lethal as l
from jpoke.utils.lethal_dist import State, to_dist

from . import test_utils as t

# ── resume_from（前回計算結果からの再開）────────────────────────────────

# ── 固定ダメージ技・一撃必殺技（lethal計算対応） ──────────────────────────


def test_Gのちから_ぼうぎょダウン_secondary有り():
    """Gのちから: secondary=True のとき相手のぼうぎょが1段階下がり、2発目のダメージが増加する"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=Move("Gのちから"), max_attack=2, secondary=True)
    assert results[1].min_damage > results[0].min_damage


def test_Gのちから_ぼうぎょダウン_secondary無し():
    """Gのちから: secondary=False のときはぼうぎょダウンが発動せず2発目のダメージが変わらない"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=Move("Gのちから"), max_attack=2, secondary=False)
    assert results[1].min_damage == results[0].min_damage


def test_LethalHitResult加算_hp_dist合成ロジックが直接計算と一致する():
    """LethalHitResult.__add__ のhp_dist合成ロジックを検証する。

    たいあたりを2発直接計算した累積結果（1発目→2発目）と、1発目の結果に
    「フルHPから1発だけ独立に計算した結果」を__add__で合成した結果は一致するはずである。
    たいあたりはランク変化を伴わないため、2発目のダメージ分布は1発目と同一であり、
    直接計算（2発とも同じ乱数範囲を畳み込む）と合成計算（__add__によるhp_dist差し引き）は
    数学的に同じ結果になる。
    """
    battle_direct = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    results_direct = t.calc_lethal(battle_direct, player_idx=0, moves=Move("たいあたり"), max_attack=2)

    battle_second_hit = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    results_second_hit = t.calc_lethal(battle_second_hit, player_idx=0, moves=Move("たいあたり"), max_attack=1)

    combined = results_direct[0] + results_second_hit[0]

    assert combined.attack_count == 2
    assert combined.hit_count == 1
    assert combined.hp_dist == results_direct[1].hp_dist
    # damage_distは両ヒット分の合算（20~24 + 20~24）
    assert combined.min_damage == 40
    assert combined.max_damage == 48


def test_Vジェネレート_ランクダウン_secondary有り():
    """Vジェネレート: secondary=Trueのとき、命中後に攻撃側のぼうぎょ・とくぼう・すばやさが1段階下がる"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン")],
        team1=[Pokemon("カビゴン")],
    )
    monitor = LethalMonitor()
    t.calc_lethal(battle, player_idx=0, moves=Move("Vジェネレート"), max_attack=1, secondary=True, monitor=monitor)
    assert monitor.attacker.boosts["def"] == -1
    assert monitor.attacker.boosts["spd"] == -1
    assert monitor.attacker.boosts["spe"] == -1


def test_Vジェネレート_ランクダウン_secondary無し():
    """Vジェネレート: secondary=Falseのときはランクダウンが発生しない（ちからずくで無効化される場合を想定）"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン")],
        team1=[Pokemon("カビゴン")],
    )
    monitor = LethalMonitor()
    t.calc_lethal(battle, player_idx=0, moves=Move("Vジェネレート"), max_attack=1, secondary=False, monitor=monitor)
    assert monitor.attacker.boosts.get("def", 0) == 0
    assert monitor.attacker.boosts.get("spd", 0) == 0
    assert monitor.attacker.boosts.get("spe", 0) == 0


def test_resume_from_HP0枝を含む分布から再開しても生存枝にON_BEFORE_MOVEが適用される():
    """HP0 枝を含む分布（4ヒット目で乱数1発）から resume_from で再開した場合、
    ON_BEFORE_MOVE ハンドラ（メテオビームのとくこう上昇）が生存枝に対して適用される"""
    battle1 = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    first = t.calc_lethal(battle1, player_idx=0, moves=[(Move("スケイルショット"), 4)])
    assert 0 < first[-1].lethal_probability < 1

    monitor = LethalMonitor()
    battle2 = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    second = t.calc_lethal(
        battle2, player_idx=0, moves=Move("メテオビーム"), max_attack=1,
        secondary=True, resume_from=first[-1], monitor=monitor,
    )

    assert monitor.attacker.boosts["spa"] == 1
    assert second[-1].lethal_probability == 1.0


def test_resume_from_HP分布が1発目終了時点から連続する():
    """1発目終了時点のHP分布の各枝から、resume_from した2発目でさらにダメージが
    差し引かれていることを確認する（たいあたりは20~24固定のダメージ幅を持つ）。"""
    battle1 = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    first = t.calc_lethal(battle1, player_idx=0, moves=Move("たいあたり"), max_attack=1)

    battle2 = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    second = t.calc_lethal(
        battle2, player_idx=0, moves=Move("たいあたり"), max_attack=1, resume_from=first[-1],
    )

    assert second[0].min_damage == 20
    assert second[0].max_damage == 24
    # 2発目のHP分布は「1発目終了時点の各枝」からさらにダメージが引かれた範囲になる
    assert max(second[0].hp_counter) == max(first[0].hp_counter) - 20
    assert min(second[0].hp_counter) == min(first[0].hp_counter) - 24


def test_resume_from_attack_countが連番になる():
    """max_attack=1 で計算した結果を resume_from に渡して再度 max_attack=1 で計算すると、
    新しい結果の attack_count が2になる（1回目は1、2回目の呼び出しは2から始まる）。"""
    battle1 = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    first = t.calc_lethal(battle1, player_idx=0, moves=Move("たいあたり"), max_attack=1)
    assert first[0].attack_count == 1

    battle2 = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    second = t.calc_lethal(
        battle2, player_idx=0, moves=Move("たいあたり"), max_attack=1, resume_from=first[-1],
    )
    assert second[0].attack_count == 2


def test_resume_from_ランク補正は引き継がれない():
    """Gのちから: resume_from はランク補正を引き継がない既知の制約を確認する。
    1発目でぼうぎょランクを下げた状態から resume_from して2発目を計算しても、
    ランクダウンは反映されず、フルHP・無補正から独立計算した場合と同じダメージに
    なる（同一 calc_lethal 呼び出し内で連続攻撃した場合の実際の値より小さい）。"""
    battle_direct = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    results_direct = t.calc_lethal(
        battle_direct, player_idx=0, moves=Move("Gのちから"), max_attack=2, secondary=True,
    )

    battle_first = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    first_hit = t.calc_lethal(
        battle_first, player_idx=0, moves=Move("Gのちから"), max_attack=1, secondary=True,
    )

    battle_resume = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    monitor = LethalMonitor()
    resumed = t.calc_lethal(
        battle_resume, player_idx=0, moves=Move("Gのちから"), max_attack=1,
        secondary=True, resume_from=first_hit[-1], monitor=monitor,
    )

    battle_independent = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    independent = t.calc_lethal(
        battle_independent, player_idx=0, moves=Move("Gのちから"), max_attack=1, secondary=True,
    )

    # resume_fromはランク補正を引き継がないため、1発目のランクダウンが無い状態
    # （＝独立計算と同じ）から2発目が計算される
    assert resumed[0].attack_count == 2
    assert resumed[0].min_damage == independent[0].min_damage
    assert resumed[0].max_damage == independent[0].max_damage

    # ランク補正が正しく引き継がれていれば一致するはずの「直接2発計算」の
    # 2発目より、ダメージが小さい（引き継がれていないことの確認）
    assert resumed[0].min_damage < results_direct[1].min_damage

    # 呼び出し完了時点の防御側ぼうぎょランクは、resume呼び出し自身の1回分の
    # ダウンのみを反映しており、1発目の分（-1）は引き継がれていない（-2にならない）
    assert monitor.defender.boosts["def"] == -1


def test_resume_from_状態異常は引き継がれない():
    """キラースピン（secondary=True）で1発目に付与したどく状態は、resume_from した
    2発目呼び出しには引き継がれない（防御側の状態異常は空に戻る、既知の制約）。"""
    battle1 = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    first = t.calc_lethal(
        battle1, player_idx=0, moves=Move("キラースピン"), max_attack=1, secondary=True,
    )

    battle2 = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    monitor = LethalMonitor()
    t.calc_lethal(
        battle2, player_idx=0, moves=Move("キラースピン"), max_attack=1,
        resume_from=first[-1], monitor=monitor,
    )
    assert monitor.defender.ailment.name == ""


def test_set_ailmentでどくを付与すると確定数が短縮される():
    """calc_lethal は防御側の状態異常による毎ターンダメージも合算する。

    battle.set_ailment() でどくを付与すると、技ダメージに加えて毎ターンの
    どくダメージが積み重なるため、どく無しの場合より少ない攻撃回数で
    致死率がほぼ確定（100%近く）に達することを確認する。
    """
    battle_without = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カバルドン")],
    )
    results_without = t.calc_lethal(
        battle_without, player_idx=0, moves=Move("ドラゴンテール"), max_attack=10
    )

    battle_with = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カバルドン")],
    )
    defender = battle_with.actives[1]
    assert battle_with.set_ailment(defender, "どく")
    results_with = t.calc_lethal(
        battle_with, player_idx=0, moves=Move("ドラゴンテール"), max_attack=10
    )

    assert results_without[-1].attack_count == 5
    assert results_with[-1].attack_count == 3
    assert results_with[-1].attack_count < results_without[-1].attack_count
    assert results_with[-1].lethal_probability > 0.9


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

    results_with = t.calc_lethal(with_ability, player_idx=0, moves=Move("たいあたり"), max_attack=2)
    results_without = t.calc_lethal(without_ability, player_idx=0, moves=Move("たいあたり"), max_attack=2)

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

    results_with = t.calc_lethal(with_volatile, player_idx=0, moves=Move("たいあたり"), max_attack=2)
    results_without = t.calc_lethal(without_volatile, player_idx=0, moves=Move("たいあたり"), max_attack=2)

    max_hp = with_volatile.actives[1].max_hp
    heal = max(1, max_hp // 16)
    assert max(results_with[1].hp_counter) - max(results_without[1].hp_counter) == heal * 2


def test_アシッドボム_とくぼうダウン():
    """アシッドボム: 命中後に相手のとくぼうが2段階下がるため2発目のダメージが増加する"""
    battle = t.start_battle(
        team0=[Pokemon("カイリュー")],
        team1=[Pokemon("カビゴン")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=Move("アシッドボム"), max_attack=2)
    assert results[1].min_damage > results[0].min_damage


def test_アッキのみ_ちからずくの対象技では発動しない():
    """ちからずく所持者の追加効果あり物理技を受けてもアッキのみは発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス", ability_name="ちからずく")],
        team1=[Pokemon("カイリュー", item_name="アッキのみ")],
    )
    # かみなりパンチ（物理・追加効果あり）で2回攻撃
    results = t.calc_lethal(battle, player_idx=0, moves=[(Move("かみなりパンチ"), 1)], max_attack=2)

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
    results = t.calc_lethal(battle, player_idx=0, moves=[(Move("たいあたり"), 1)], max_attack=3)

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
    results = t.calc_lethal(battle, player_idx=0, moves=[(Move("ドラゴンテール"), 1)], max_attack=2)

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
    results = t.calc_lethal(battle, player_idx=0, moves=[(Move("りゅうのはどう"), 1)], max_attack=2)

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

    results_with = t.calc_lethal(with_ability, player_idx=0, moves=Move("たいあたり"), max_attack=2)
    results_without = t.calc_lethal(without_ability, player_idx=0, moves=Move("たいあたり"), max_attack=2)

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

    results_with = t.calc_lethal(with_item, player_idx=0, moves=[(Move("たいあたり"), 1)], max_attack=7)
    results_without = t.calc_lethal(without_item, player_idx=0, moves=[(Move("たいあたり"), 1)], max_attack=7)

    max_hp = with_item.actives[1].max_hp  # 166
    heal = max(1, int(max_hp * 1 / 3))   # 55
    assert max(results_with[-1].hp_counter) - max(results_without[-1].hp_counter) == heal


def test_いかりのまえば_残りHPの半分ずつ逓減する():
    """いかりのまえば: ダメージ = 直前の防御側HP × 1/2（端数切り捨て、最低1）。
    枝依存（damage_from_hp）のため、ヒットごとに直前HPを参照して逓減していくはずである。

    手計算: A150ガブリアス → H166/B115カイリュー（max_hp=166、ドキュメント冒頭コメント参照）。
    1発目 166//2=83 → 残166-83=83
    2発目 83//2=41  → 残83-41=42
    3発目 42//2=21  → 残42-21=21
    4発目 21//2=10  → 残21-10=11（HPは0を下回らず1以上を維持）
    """
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    max_hp = battle.actives[1].max_hp
    results = t.calc_lethal(battle, player_idx=0, moves=Move("いかりのまえば"), max_attack=4)

    hp = max_hp
    assert len(results) == 4
    for r in results:
        expected_damage = max(1, hp // 2)
        assert r.min_damage == expected_damage
        assert r.max_damage == expected_damage
        hp -= expected_damage
        # 直前HPから計算した通りに残りHPが減っていく（一意に定まる＝乱数幅なし）
        assert list(r.hp_counter.keys()) == [hp]
        assert hp >= 1


def test_いじげんラッシュ_ぼうぎょランクダウン():
    """いじげんラッシュ: 確定効果（ちからずくの対象外）のため、secondary指定に関わらず攻撃側のぼうぎょが1段階下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カビゴン")],
    )
    monitor = LethalMonitor()
    t.calc_lethal(battle, player_idx=0, moves=Move("いじげんラッシュ"), max_attack=1, secondary=False, monitor=monitor)
    assert monitor.attacker.boosts["def"] == -1


def test_いのちがけ_1発目は現在HP2発目は0():
    """いのちがけ: ダメージ = 使用者の現在HP（一律）。命中時に使用者は必ずひんしになるため、
    lethal計算では ctx.attacker.hp を0に直接代入することでこれを再現する。
    同じ技を繰り返し指定した場合、2発目移行は使用者のHPが既に0のため hp_cost=0 となり、
    自然にダメージ0になる（使用者が実際には行動できないはずという制約は
    test_いのちがけ_後続の技は同じ攻撃機会内で発動しない でカバーする）。

    防御側（カビゴン、非常に高HP）は使用者（ピカチュウ）のHPを1発受けても倒れない
    ように、意図的にタフな防御側を選んでいる（そうしないと1発目で防御側も
    倒れてしまい、2発目の結果自体が存在しなくなる）。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", level=50)],
        team1=[Pokemon("カビゴン", level=50)],
    )
    attacker_hp = battle.actives[0].hp

    results = t.calc_lethal(battle, player_idx=0, moves=Move("いのちがけ"), max_attack=2)

    assert results[0].min_damage == attacker_hp
    assert results[0].max_damage == attacker_hp
    assert results[1].min_damage == 0
    assert results[1].max_damage == 0


def test_いのちがけ_後続の技は同じ攻撃機会内で発動しない():
    """いのちがけで使用者がひんしになった場合、moves にリストで渡した後続の技
    （例: じしん）は同じ攻撃機会内でも、それ以降のどの攻撃回でも一切ダメージを
    与えないことを確認する（ひんしになった攻撃側はもう技を使えないはず、という
    レビューで見つかった問題への回帰テスト。core/lethal.py の _lethal_loop に
    attacker.fainted チェックを追加して対応した）。

    防御側（カビゴン）は1発目のいのちがけ（使用者の現在HP分のダメージ）を受けても
    倒れない高HPのポケモンを選ぶ。これにより2発目・3発目のラウンドまで計算が
    続き、「じしん が一度も実行されない」ことを実際に検証できる
    （防御側が1発目で倒れてしまうと、じしん が実行されないのは単に計算が
    打ち切られたからという別の理由になり、本来確認したい制約を検証できない）。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", level=50)],
        team1=[Pokemon("カビゴン", level=50)],
    )
    results = t.calc_lethal(
        battle, player_idx=0,
        moves=[(Move("いのちがけ"), 1), (Move("じしん"), 1)],
        max_attack=3,
    )

    # じしん は一度も実行されない（いのちがけ による使用者の自滅が優先されるため）
    assert all(r.move.name == "いのちがけ" for r in results)
    # 防御側が生存し続け、3ラウンド分（いのちがけのみ）計算が続いたことを確認する
    assert len(results) == 3


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
    results_move = t.calc_lethal(battle_move, player_idx=0, moves=Move("うずしお"), max_attack=2)
    results_pre = t.calc_lethal(battle_pre, player_idx=0, moves=Move("うずしお"), max_attack=2)
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
    t.apply_ailment(battle_secondary, player_idx=1, ailment_name="やけど")
    t.apply_ailment(battle_no_secondary, player_idx=1, ailment_name="やけど")

    results_with = t.calc_lethal(battle_secondary, player_idx=0, moves=Move("うたかたのアリア"), max_attack=2, secondary=True)
    results_without = t.calc_lethal(battle_no_secondary, player_idx=0, moves=Move("うたかたのアリア"), max_attack=2, secondary=False)
    max_hp = battle_secondary.actives[1].max_hp
    burn_damage = max(1, max_hp // 16)
    assert max(results_with[1].hp_counter) - max(results_without[1].hp_counter) == burn_damage * 2


def test_エレクトロビーム_とくこうアップ_secondary有り():
    """エレクトロビーム: secondary=True のときチャージ前にとくこうが1段階上がり、2発目のダメージが増加する"""
    battle = t.start_battle(
        team0=[Pokemon("カイリュー")],
        team1=[Pokemon("カビゴン")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=Move("エレクトロビーム"), max_attack=2, secondary=True)
    assert results[1].min_damage > results[0].min_damage


def test_エレクトロビーム_とくこうアップ_secondary無し():
    """エレクトロビーム: secondary=False のときとくこうアップが発動せず2発目のダメージが変わらない"""
    battle = t.start_battle(
        team0=[Pokemon("カイリュー")],
        team1=[Pokemon("カビゴン")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=Move("エレクトロビーム"), max_attack=2, secondary=False)
    assert results[1].min_damage == results[0].min_damage


def test_オボンのみ_スケイルショット5発_乱数1発():
    """オボンのみ所持時、多段技はヒットごとにHP半分以下判定・回復が発生するため
    5発目終了時点でも乱数1発 (80.31%) になる"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", item_name="オボンのみ")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=[(Move("スケイルショット"), 5)])

    assert results[-1].attack_count == 1
    assert results[-1].hit_count == 5
    assert results[-1].lethal_probability == pytest.approx(0.8031, abs=0.001)


def test_オボンのみ_乱数2発():
    """オボンのみ所持時、HPが半分以下になった1発目で回復するため乱数2になる"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", item_name="オボンのみ")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=[(Move("ドラゴンテール"), 1)])

    assert results[0].min_damage == 90
    assert results[0].max_damage == 108
    assert results[-1].attack_count == 2
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
    results_with = t.calc_lethal(with_ability, player_idx=0, moves=Move("たいあたり"), max_attack=1)
    results_without = t.calc_lethal(without_ability, player_idx=0, moves=Move("たいあたり"), max_attack=1)

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

    results_with = t.calc_lethal(with_item, player_idx=0, moves=[(Move("ドラゴンテール"), 1)])
    results_without = t.calc_lethal(without_item, player_idx=0, moves=[(Move("ドラゴンテール"), 1)])

    assert max(results_with[0].hp_counter) - max(results_without[0].hp_counter) == 10


def test_オーバーヒート_とくこうダウン():
    """オーバーヒート: 命中後にとくこうが2段階下がるため2発目のダメージが減少する"""
    battle = t.start_battle(
        team0=[Pokemon("カイリュー")],
        team1=[Pokemon("カビゴン")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=Move("オーバーヒート"), max_attack=2)
    assert results[1].min_damage < results[0].min_damage


def test_カウンター_直近の物理被弾ダメージの2倍を与える():
    """カウンター: 直近に受けた物理ダメージ×2を固定ダメージとして与える。"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    attacker = battle.actives[0]
    attacker.last_damage_taken = {"damage": 50, "category": "physical"}

    results = t.calc_lethal(battle, player_idx=0, moves=Move("カウンター"), max_attack=1)

    assert results[0].min_damage == 100
    assert results[0].max_damage == 100


def test_カウンター_被弾記録が無ければダメージ0():
    """カウンター: 直近の物理被弾記録が無い（0以下の）場合は実戦の使用可否チェックに
    相当する形でダメージ0になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=Move("カウンター"), max_attack=1)

    assert results[0].min_damage == 0
    assert results[0].max_damage == 0


def test_カタストロフィ_残りHPの半分ずつ逓減する():
    """カタストロフィはいかりのまえばと同じ式（防御側の現在HP×1/2、最低1、枝依存）を
    使う（handlers/lethal.py の half_damage を共用）。"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    max_hp = battle.actives[1].max_hp
    results = t.calc_lethal(battle, player_idx=0, moves=Move("カタストロフィ"), max_attack=4)

    hp = max_hp
    for r in results:
        expected_damage = max(1, hp // 2)
        assert r.min_damage == expected_damage
        assert r.max_damage == expected_damage
        hp -= expected_damage


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
    results_with = t.calc_lethal(with_ability, player_idx=0, moves=Move("たいあたり"), max_attack=2)
    results_without = t.calc_lethal(without_ability, player_idx=0, moves=Move("たいあたり"), max_attack=2)

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
    results_with = t.calc_lethal(with_ability, player_idx=0, moves=Move("たいあたり"), max_attack=2)
    results_without = t.calc_lethal(without_ability, player_idx=0, moves=Move("たいあたり"), max_attack=2)

    max_hp = with_ability.actives[1].max_hp
    damage = max(1, max_hp // 8)
    assert max(results_without[1].hp_counter) - max(results_with[1].hp_counter) == damage * 2


def test_がむしゃら_防御側HPと攻撃側HPの差分ダメージ():
    """がむしゃら: ダメージ = 防御側の現在HP − 攻撃側の現在HP（最低0）。

    手計算: 攻撃側HPを30に固定し、防御側は満タン（カビゴンlevel50、max_hp=235）のまま
    1発目を撃つと、ダメージ = 235-30 = 205、防御側の残りHPは30（攻撃側と同値）になる。
    2発目は差分が0になるため、ダメージ0のまま防御側は倒れない。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", level=50)],
        team1=[Pokemon("カビゴン", level=50)],
    )
    attacker = battle.actives[0]
    attacker.hp = 30  # テストのセットアップ専用の直接代入（本番の対戦進行では使わない）
    defender_hp = battle.actives[1].hp

    results = t.calc_lethal(battle, player_idx=0, moves=Move("がむしゃら"), max_attack=2)

    assert results[0].min_damage == defender_hp - 30
    assert results[0].max_damage == defender_hp - 30
    assert list(results[0].hp_counter.keys()) == [30]
    # 2発目: 防御側HP(30) - 攻撃側HP(30) = 0 のためダメージが発生しない
    assert results[1].min_damage == 0
    assert results[1].max_damage == 0


def test_がんじょう_リーサル計算全体で正しく発動する():
    """calc_lethal 経由の一連の処理でも、がんじょうの登録（data/ability.py）が
    正しく機能してHP1で耐えることを確認する（実戦形式の統合テスト）。"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス", level=100)],
        team1=[Pokemon("トゲピー", level=1, ability_name="がんじょう")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=Move("じしん"), max_attack=1)

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
    results_with = t.calc_lethal(battle_secondary, player_idx=0, moves=Move("キラースピン"), max_attack=2, secondary=True)
    results_without = t.calc_lethal(battle_no_secondary, player_idx=0, moves=Move("キラースピン"), max_attack=2, secondary=False)
    max_hp = battle_secondary.actives[1].max_hp
    poison_damage = max(1, max_hp // 8)
    assert max(results_without[1].hp_counter) - max(results_with[1].hp_counter) == poison_damage * 2


def test_クリアスモッグ_とくぼうリセットで2発目のダメージが増加する():
    """クリアスモッグ: あらかじめ上がっていた相手のとくぼうが命中後にリセットされるため、
    2発目のダメージが増加する"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    battle.actives[1].boosts["spd"] = 2
    results = t.calc_lethal(battle, player_idx=0, moves=Move("クリアスモッグ"), max_attack=2)
    assert results[1].min_damage > results[0].min_damage


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

    results_with = t.calc_lethal(with_item, player_idx=0, moves=[(Move("たいあたり"), 1)], max_attack=2)
    results_without = t.calc_lethal(without_item, player_idx=0, moves=[(Move("たいあたり"), 1)], max_attack=2)

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

    results_with = t.calc_lethal(with_item, player_idx=0, moves=[(Move("たいあたり"), 1)], max_attack=2)
    results_without = t.calc_lethal(without_item, player_idx=0, moves=[(Move("たいあたり"), 1)], max_attack=2)

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

    results_with = t.calc_lethal(with_terrain, player_idx=0, moves=Move("たいあたり"), max_attack=2)
    results_without = t.calc_lethal(without_terrain, player_idx=0, moves=Move("たいあたり"), max_attack=2)

    max_hp = with_terrain.actives[1].max_hp
    heal = max(1, max_hp // 16)
    assert max(results_with[1].hp_counter) - max(results_without[1].hp_counter) == heal * 2


def test_グロウパンチ_secondary無しなら発動しない():
    """グロウパンチ: secondary=False（ちからずく想定）のときはこうげきが上がらない"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー")],
        team1=[Pokemon("カビゴン")],
    )
    monitor = LethalMonitor()
    t.calc_lethal(battle, player_idx=0, moves=Move("グロウパンチ"), max_attack=1, secondary=False, monitor=monitor)
    assert monitor.attacker.boosts.get("atk", 0) == 0


def test_グロウパンチ_こうげきランクアップ_secondary有り():
    """グロウパンチ: secondary=Trueのとき、命中後に攻撃側のこうげきが1段階上がる"""
    battle = t.start_battle(
        team0=[Pokemon("カイリキー")],
        team1=[Pokemon("カビゴン")],
    )
    monitor = LethalMonitor()
    t.calc_lethal(battle, player_idx=0, moves=Move("グロウパンチ"), max_attack=1, secondary=True, monitor=monitor)
    assert monitor.attacker.boosts["atk"] == 1


def test_ゴールドラッシュ_とくこうダウン():
    """ゴールドラッシュ: 命中後にとくこうが2段階下がる（Champions基準）ため2発目のダメージが減少する"""
    battle = t.start_battle(
        team0=[Pokemon("カイリュー")],
        team1=[Pokemon("カビゴン")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=Move("ゴールドラッシュ"), max_attack=2)
    assert results[1].min_damage < results[0].min_damage


def test_サイコノイズ_かいふくふうじでたべのこし回復がブロックされる():
    """サイコノイズ: secondary=True で命中後にかいふくふうじを付与し、
    たべのこしのターン終了回復がブロックされる。"""
    battle_secondary = t.start_battle(
        team0=[Pokemon("フーディン")],
        team1=[Pokemon("カビゴン", item_name="たべのこし")],
    )
    battle_no_secondary = t.start_battle(
        team0=[Pokemon("フーディン")],
        team1=[Pokemon("カビゴン", item_name="たべのこし")],
    )
    results_with = t.calc_lethal(
        battle_secondary, player_idx=0, moves=Move("サイコノイズ"), max_attack=2, secondary=True,
    )
    results_without = t.calc_lethal(
        battle_no_secondary, player_idx=0, moves=Move("サイコノイズ"), max_attack=2, secondary=False,
    )

    leftover_heal = battle_secondary.actives[1].max_hp // 16
    assert (
        max(results_without[1].hp_counter) - max(results_with[1].hp_counter)
        == leftover_heal * 2
    )


def test_サイコブースト_とくこうダウン():
    """サイコブースト: 命中後にとくこうが2段階下がるため2発目のダメージが減少する"""
    battle = t.start_battle(
        team0=[Pokemon("デオキシス(アタック)")],
        team1=[Pokemon("カビゴン")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=Move("サイコブースト"), max_attack=2)
    assert results[1].min_damage < results[0].min_damage


def test_サンダープリズン_バインド付与():
    """サンダープリズンは命中後にバインドを付与し、ターン終了時ダメージが発生する（バインド事前付与と同じ結果）"""
    battle_move = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    battle_pre = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
        volatile1={"バインド": 5},
    )
    results_move = t.calc_lethal(battle_move, player_idx=0, moves=Move("サンダープリズン"), max_attack=2)
    results_pre = t.calc_lethal(battle_pre, player_idx=0, moves=Move("サンダープリズン"), max_attack=2)
    assert max(results_move[1].hp_counter) == max(results_pre[1].hp_counter)


def test_サンパワー_はれでダメージ():
    """サンパワー: defender がサンパワーを持つ場合、はれ天気のターン終了時に最大HPの1/8ダメージを受ける"""
    with_ability = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", ability_name="サンパワー")],
        weather=("はれ", 5),
    )
    without_ability = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
        weather=("はれ", 5),
    )
    results_with = t.calc_lethal(with_ability, player_idx=0, moves=Move("たいあたり"), max_attack=2)
    results_without = t.calc_lethal(without_ability, player_idx=0, moves=Move("たいあたり"), max_attack=2)

    max_hp = with_ability.actives[1].max_hp
    damage = max(1, max_hp // 8)
    assert max(results_without[1].hp_counter) - max(results_with[1].hp_counter) == damage * 2


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

    results_with = t.calc_lethal(with_volatile, player_idx=0, moves=Move("たいあたり"), max_attack=2)
    results_without = t.calc_lethal(without_volatile, player_idx=0, moves=Move("たいあたり"), max_attack=2)

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
    results_with = t.calc_lethal(battle_secondary, player_idx=0, moves=Move("しおづけ"), max_attack=2, secondary=True)
    results_without = t.calc_lethal(battle_no_secondary, player_idx=0, moves=Move("しおづけ"), max_attack=2, secondary=False)
    max_hp = battle_secondary.actives[1].max_hp
    damage = max(1, max_hp // 16)
    assert max(results_without[1].hp_counter) - max(results_with[1].hp_counter) == damage * 2


def test_しっとのほのお_やけど付与_ランク上昇時_secondary有り():
    """しっとのほのお: 相手がそのターンにランクが上がっていれば、secondary=Trueでやけど状態にする"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン")],
        team1=[Pokemon("カビゴン")],
    )
    battle.actives[1].stat_raised_this_turn = True
    monitor = LethalMonitor()
    t.calc_lethal(battle, player_idx=0, moves=Move("しっとのほのお"), max_attack=1, secondary=True, monitor=monitor)
    assert monitor.defender.ailment.name == "やけど"


def test_しっとのほのお_ランク上昇なしなら発動しない():
    """しっとのほのお: 相手がそのターンにランクが上がっていなければ、secondary=Trueでも発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("リザードン")],
        team1=[Pokemon("カビゴン")],
    )
    monitor = LethalMonitor()
    t.calc_lethal(battle, player_idx=0, moves=Move("しっとのほのお"), max_attack=1, secondary=True, monitor=monitor)
    assert monitor.defender.ailment.name == ""


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
    results_move = t.calc_lethal(battle_move, player_idx=0, moves=Move("しめつける"), max_attack=2)
    results_pre = t.calc_lethal(battle_pre, player_idx=0, moves=Move("しめつける"), max_attack=2)
    assert max(results_move[1].hp_counter) == max(results_pre[1].hp_counter)


def test_しんぴのちから_とくこうアップ_secondary有り():
    """しんぴのちから: secondary=True のとき命中後にとくこうが1段階上がり、2発目のダメージが増加する"""
    battle = t.start_battle(
        team0=[Pokemon("カイリュー")],
        team1=[Pokemon("カビゴン")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=Move("しんぴのちから"), max_attack=2, secondary=True)
    assert results[1].min_damage > results[0].min_damage


def test_しんぴのちから_とくこうアップ_secondary無し():
    """しんぴのちから: secondary=False のときとくこうアップが発動せず2発目のダメージが変わらない"""
    battle = t.start_battle(
        team0=[Pokemon("カイリュー")],
        team1=[Pokemon("カビゴン")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=Move("しんぴのちから"), max_attack=2, secondary=False)
    assert results[1].min_damage == results[0].min_damage


def test_じきゅうりょく_物理技受けるとぼうぎょ上昇():
    """じきゅうりょく: 物理技を受けるたびにぼうぎょが+1され、2発目のダメージが減少する"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", ability_name="じきゅうりょく")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=Move("ドラゴンテール"), max_attack=2)

    # 1発目: B rank 0
    assert results[0].min_damage == 90
    assert results[0].max_damage == 108
    # 2発目: ぼうぎょ+1（rank +1: ×3/2補正）でダメージが減少
    assert results[1].min_damage == 62
    assert results[1].max_damage == 74


def test_じわれ_ひこうタイプに無効でダメージ0():
    """じわれ（じめんタイプ技）はひこうタイプに無効（0倍）のため、
    一撃必殺技であってもlethal計算でダメージ0になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", level=50)],
        team1=[Pokemon("ピジョット")],  # ノーマル/ひこう
    )
    results = t.calc_lethal(battle, player_idx=0, moves=Move("じわれ"), max_attack=3)

    assert all(r.min_damage == 0 and r.max_damage == 0 for r in results)


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

    results_with = t.calc_lethal(with_weather, player_idx=0, moves=Move("たいあたり"), max_attack=2)
    results_without = t.calc_lethal(without_weather, player_idx=0, moves=Move("たいあたり"), max_attack=2)

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
    results_move = t.calc_lethal(battle_move, player_idx=0, moves=Move("すなじごく"), max_attack=2)
    results_pre = t.calc_lethal(battle_pre, player_idx=0, moves=Move("すなじごく"), max_attack=2)
    assert max(results_move[1].hp_counter) == max(results_pre[1].hp_counter)


def test_ぜったいれいど_こおりタイプに無効でダメージ0():
    """ぜったいれいど: 通常のタイプ相性表ではこおりタイプへの一致技は0.5倍でしかなく
    無効化されないが、本技はこおりタイプの相手には専用ルールで必ず無効化される
    （ぜったいれいど_check_ice_immunity, Event.ON_TRY_MOVE_2 相当）。
    lethal側の ohko_damage にも同じ個別分岐が実装されている。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", level=50)],
        team1=[Pokemon("ジュゴン")],  # こおり/みず
    )
    results = t.calc_lethal(battle, player_idx=0, moves=Move("ぜったいれいど"), max_attack=3)

    assert all(r.min_damage == 0 and r.max_damage == 0 for r in results)


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
    results = t.calc_lethal(battle, player_idx=0, moves=Move(move_name), max_attack=3)

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
        with_item, player_idx=0, moves=[(Move("たいあたり"), 1)], max_attack=2,
    )
    results_without_item = t.calc_lethal(
        without_item, player_idx=0, moves=[(Move("たいあたり"), 1)], max_attack=2,
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
    results = t.calc_lethal(battle, player_idx=0, moves=[(Move("でんきショック"), 1)], max_attack=2)

    # ランクが変わらないため1発目と2発目のダメージが同じ
    assert results[0].min_damage == results[1].min_damage
    assert results[0].max_damage == results[1].max_damage


def test_タラプのみ_物理技では発動しない():
    """物理技を受けてもタラプのみは発動せず、2発目のダメージが変わらない。"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", item_name="タラプのみ")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=[(Move("ドラゴンテール"), 1)], max_attack=2)

    # ランクが変わらないため1発目と2発目のダメージが同じ
    assert results[0].min_damage == results[1].min_damage
    assert results[0].max_damage == results[1].max_damage


def test_タラプのみ_特殊技受けた後とくぼう上昇():
    """特殊技を受けた直後にとくぼう+1し、2発目のダメージが減少する。"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", item_name="タラプのみ")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=[(Move("りゅうのはどう"), 1)], max_attack=2)

    # 1発目: タラプのみ未発動、A150ガブリアス C110 vs D120カイリュー
    assert results[0].min_damage == 84
    assert results[0].max_damage == 98
    # 2発目: とくぼう+1 (D120→D180相当) でダメージ減少
    assert results[1].min_damage == 54
    assert results[1].max_damage == 66


def test_ちきゅうなげ_ゴーストタイプに無効でダメージ0():
    """ちきゅうなげ（ノーマルタイプ技）はゴーストタイプに無効（0倍）のため、
    lethal計算でもダメージ0・致死率0%が最大攻撃回数まで維持される。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", level=50)],
        team1=[Pokemon("ゲンガー")],  # ゴースト/どく
    )
    results = t.calc_lethal(battle, player_idx=0, moves=Move("ちきゅうなげ"), max_attack=10)

    assert all(r.min_damage == 0 and r.max_damage == 0 for r in results)
    assert len(results) == 10
    assert results[-1].lethal_probability == 0.0


def test_ちきゅうなげ_レベル固定ダメージで確定数がceil_max_hp_levelになる():
    """ちきゅうなげ: ダメージは使用者のレベルに固定される（防御・威力・タイプ相性の
    倍率・急所・乱数を一切使用しない）。よって確定数は ceil(防御側max_hp / 使用者level)
    になるはずである（最終手前のヒットまでは致死率0%、最終ヒットで100%に切り替わる）。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", level=50)],
        team1=[Pokemon("カビゴン", level=50)],
    )
    level = battle.actives[0].level
    max_hp = battle.actives[1].max_hp
    # 手計算: ceil(max_hp / level) = -(-max_hp // level)（Python算術での天井除算）
    expected_hits = -(-max_hp // level)

    results = t.calc_lethal(battle, player_idx=0, moves=Move("ちきゅうなげ"), max_attack=30)

    # 毎ヒットのダメージは常に使用者のレベルと一致する（乱数幅が無い＝min=max）
    assert all(r.min_damage == level and r.max_damage == level for r in results)
    assert len(results) == expected_hits
    assert results[-1].attack_count == expected_hits
    assert results[-1].lethal_probability == 1.0
    if expected_hits > 1:
        assert results[-2].lethal_probability == 0.0


def test_チャージビーム_とくこうアップ_secondary有り():
    """チャージビーム: secondary=True のとき命中後にとくこうが1段階上がり、2発目のダメージが増加する"""
    battle = t.start_battle(
        team0=[Pokemon("カイリュー")],
        team1=[Pokemon("カビゴン")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=Move("チャージビーム"), max_attack=2, secondary=True)
    assert results[1].min_damage > results[0].min_damage


def test_チャージビーム_とくこうアップ_secondary無し():
    """チャージビーム: secondary=False のときとくこうアップが発動せず2発目のダメージが変わらない"""
    battle = t.start_battle(
        team0=[Pokemon("カイリュー")],
        team1=[Pokemon("カビゴン")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=Move("チャージビーム"), max_attack=2, secondary=False)
    assert results[1].min_damage == results[0].min_damage


def test_つのドリル_1発で致死率が100パーセントになる():
    """一撃必殺技（つのドリル）: 命中すれば相手の残りHPそのものがダメージになるため、
    タイプ相性・特性等による免除が無ければ1発で致死率100%になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=Move("つのドリル"), max_attack=1)

    assert results[0].lethal_probability == 1.0


def test_テラスシェル_満タン時タイプ相性を等倍に丸める():
    """テラスシェル: HPが満タンのとき、等倍以上の相性の技を受けると相性が等倍(1x)に丸められ
    ダメージが半減する。HPが満タンでなければ通常通りのダメージを受ける。"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", ability_name="テラスシェル")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=[(Move("たいあたり"), 1)], max_attack=2)

    assert results[0].min_damage == 10
    assert results[0].max_damage == 12
    assert results[1].min_damage == 20
    assert results[1].max_damage == 24


def test_テラバースト_ステラでこうげきとくこうダウン():
    """テラバースト: ステラタイプにテラスタルして命中すると、こうげき・とくこうが1段階ずつ下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", tera_type="ステラ")],
        team1=[Pokemon("カビゴン")],
    )
    battle.actives[0].terastallize()
    monitor = LethalMonitor()
    t.calc_lethal(battle, player_idx=0, moves=Move("テラバースト"), max_attack=1, monitor=monitor)
    assert monitor.attacker.boosts["atk"] == -1
    assert monitor.attacker.boosts["spa"] == -1


def test_テラバースト_ステラ以外はランクが下がらない():
    """テラバースト: ステラ以外のタイプにテラスタルした場合はランクが下がらない"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", tera_type="でんき")],
        team1=[Pokemon("カビゴン")],
    )
    battle.actives[0].terastallize()
    monitor = LethalMonitor()
    t.calc_lethal(battle, player_idx=0, moves=Move("テラバースト"), max_attack=1, monitor=monitor)
    assert monitor.attacker.boosts["atk"] == 0
    assert monitor.attacker.boosts["spa"] == 0


def test_トラバサミ_バインド付与():
    """トラバサミは命中後にバインドを付与し、ターン終了時ダメージが発生する（バインド事前付与と同じ結果）"""
    battle_move = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    battle_pre = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
        volatile1={"バインド": 5},
    )
    results_move = t.calc_lethal(battle_move, player_idx=0, moves=Move("トラバサミ"), max_attack=2)
    results_pre = t.calc_lethal(battle_pre, player_idx=0, moves=Move("トラバサミ"), max_attack=2)
    assert max(results_move[1].hp_counter) == max(results_pre[1].hp_counter)


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
    t.apply_ailment(with_ailment, player_idx=1, ailment_name="どく")

    results_with = t.calc_lethal(with_ailment, player_idx=0, moves=Move("たいあたり"), max_attack=2)
    results_without = t.calc_lethal(without_ailment, player_idx=0, moves=Move("たいあたり"), max_attack=2)

    max_hp = with_ailment.actives[1].max_hp
    damage = max(1, max_hp // 8)
    assert max(results_without[1].hp_counter) - max(results_with[1].hp_counter) == damage * 2


def test_ナイトヘッド_ノーマルタイプに無効でダメージ0():
    """ナイトヘッド（ゴーストタイプ技）はノーマルタイプに無効（0倍）のため、
    lethal計算でもダメージ0になる。"""
    battle = t.start_battle(
        team0=[Pokemon("ゲンガー", level=50)],
        team1=[Pokemon("カビゴン")],  # ノーマル
    )
    results = t.calc_lethal(battle, player_idx=0, moves=Move("ナイトヘッド"), max_attack=3)

    assert all(r.min_damage == 0 and r.max_damage == 0 for r in results)


def test_なげつける_オボンのみ_相手のHP回復():
    """なげつける: オボンのみを投げると、相手のHPが最大HPの1/4回復する"""
    battle_with_item = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="オボンのみ")],
        team1=[Pokemon("カビゴン")],
    )
    battle_without_item = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("カビゴン")],
    )
    max_hp = battle_with_item.actives[1].max_hp
    # なげつけるはMoveData上base_power=1のプレースホルダーのため、
    # 実際の威力（本来はfling_powerで決まる）を明示的に設定する。
    # 乱数ダメージ幅の最小値がヒールの回復量を上回るよう、十分に大きい威力にする
    # （そうでないとHPが上限に張り付き、回復量の差分を観測できない）。
    move_with = Move("なげつける")
    move_with.base_power = 250
    move_without = Move("なげつける")
    move_without.base_power = 250
    results_with = t.calc_lethal(battle_with_item, player_idx=0, moves=move_with, max_attack=1, secondary=True)
    results_without = t.calc_lethal(battle_without_item, player_idx=0, moves=move_without, max_attack=1, secondary=True)
    heal = max(1, max_hp // 4)
    assert max(results_with[0].hp_counter) - max(results_without[0].hp_counter) == heal


def test_なげつける_しろいハーブ_下がったランクをリセット():
    """なげつける: しろいハーブを投げると、相手の下がった能力ランクが0に戻る"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="しろいハーブ")],
        team1=[Pokemon("カビゴン")],
    )
    battle.actives[1].boosts["atk"] = -2
    monitor = LethalMonitor()
    t.calc_lethal(battle, player_idx=0, moves=Move("なげつける"), max_attack=1, secondary=True, monitor=monitor)
    assert monitor.defender.boosts["atk"] == 0


def test_なげつける_チイラのみ_相手のこうげきランク上昇():
    """なげつける: チイラのみを投げると、相手のこうげきランクが1段階上がる"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="チイラのみ")],
        team1=[Pokemon("カビゴン")],
    )
    monitor = LethalMonitor()
    t.calc_lethal(battle, player_idx=0, moves=Move("なげつける"), max_attack=1, secondary=True, monitor=monitor)
    assert monitor.defender.boosts["atk"] == 1


def test_なげつける_でんきだま_secondary無しなら発動しない():
    """なげつける: secondary=Falseのときは状態異常が付与されない（りんぷん・おんみつマント等を想定）"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="でんきだま")],
        team1=[Pokemon("カビゴン")],
    )
    monitor = LethalMonitor()
    t.calc_lethal(battle, player_idx=0, moves=Move("なげつける"), max_attack=1, secondary=False, monitor=monitor)
    assert monitor.defender.ailment.name == ""


def test_なげつける_でんきだま_まひ付与_secondary有り():
    """なげつける: でんきだまを投げると、secondary=Trueのとき相手をまひ状態にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="でんきだま")],
        team1=[Pokemon("カビゴン")],
    )
    monitor = LethalMonitor()
    t.calc_lethal(battle, player_idx=0, moves=Move("なげつける"), max_attack=1, secondary=True, monitor=monitor)
    assert monitor.defender.ailment.name == "まひ"


def test_なげつける_ラムのみ_状態異常を治す():
    """なげつける: ラムのみを投げると、相手の状態異常が治る"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="ラムのみ")],
        team1=[Pokemon("カビゴン")],
    )
    t.apply_ailment(battle, player_idx=1, ailment_name="まひ")
    monitor = LethalMonitor()
    t.calc_lethal(battle, player_idx=0, moves=Move("なげつける"), max_attack=1, secondary=True, monitor=monitor)
    assert monitor.defender.ailment.name == ""


def test_ナモのみ_抜群ダメージ半減():
    """ナモのみ: あく抜群技の1発目が半減され、2発目は通常ダメージになる"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("エーフィ", item_name="ナモのみ")],
    )
    # かみくだく（あく物理）: エーフィはエスパー単タイプ → あく2倍
    results = t.calc_lethal(battle, player_idx=0, moves=Move("かみくだく"), max_attack=3)

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
    results = t.calc_lethal(battle, player_idx=0, moves=Move("かみくだく"), max_attack=2)

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

    results_with = t.calc_lethal(with_volatile, player_idx=0, moves=Move("たいあたり"), max_attack=2)
    results_without = t.calc_lethal(without_volatile, player_idx=0, moves=Move("たいあたり"), max_attack=2)

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

    results_with = t.calc_lethal(with_volatile, player_idx=0, moves=Move("たいあたり"), max_attack=2)
    results_without = t.calc_lethal(without_volatile, player_idx=0, moves=Move("たいあたり"), max_attack=2)

    max_hp = with_volatile.actives[1].max_hp
    damage = max(1, max_hp // 4)
    assert max(results_without[1].hp_counter) - max(results_with[1].hp_counter) == damage * 2


def test_はきだす_たくわえなしならランク変化なし():
    """はきだす: たくわえるを使っていなければランク変化は起きない"""
    battle = t.start_battle(
        team0=[Pokemon("ドサイドン")],
        team1=[Pokemon("カビゴン")],
    )
    move = Move("はきだす")
    move.base_power = 1
    monitor = LethalMonitor()
    t.calc_lethal(battle, player_idx=0, moves=move, max_attack=1, monitor=monitor)
    assert monitor.attacker.boosts.get("def", 0) == 0
    assert monitor.attacker.boosts.get("spd", 0) == 0


def test_はきだす_たくわえるぶんのランクダウン():
    """はきだす: 使用後にたくわえるで上がった分のぼうぎょ・とくぼうランクが下がる"""
    battle = t.start_battle(
        team0=[Pokemon("ドサイドン")],
        team1=[Pokemon("カビゴン")],
        volatile0={"たくわえる": 2},
    )
    move = Move("はきだす")
    move.base_power = 200
    monitor = LethalMonitor()
    t.calc_lethal(battle, player_idx=0, moves=move, max_attack=1, monitor=monitor)
    assert monitor.attacker.boosts["def"] == -2
    assert monitor.attacker.boosts["spd"] == -2


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

    results_with = t.calc_lethal(with_volatile, player_idx=0, moves=Move("たいあたり"), max_attack=2)
    results_without = t.calc_lethal(without_volatile, player_idx=0, moves=Move("たいあたり"), max_attack=2)

    max_hp = with_volatile.actives[1].max_hp
    damage = max(1, int(max_hp / 8))
    assert max(results_without[1].hp_counter) - max(results_with[1].hp_counter) == damage * 2


def test_ばかぢから_こうげきダウン():
    """ばかぢから: 命中後にこうげきが1段階下がるため2発目のダメージが減少する"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=Move("ばかぢから"), max_attack=2)
    assert results[1].min_damage < results[0].min_damage


def test_ばかぢから_こうげきとぼうぎょが両方ダウン():
    """ばかぢから: 命中後にこうげき・ぼうぎょの両方が1段階ずつ下がる（リーサル計算側）"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    monitor = LethalMonitor()
    t.calc_lethal(battle, player_idx=0, moves=Move("ばかぢから"), max_attack=1, monitor=monitor)
    assert monitor.attacker.boosts["atk"] == -1
    assert monitor.attacker.boosts["def"] == -1


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

    results_with = t.calc_lethal(with_ability, player_idx=0, moves=Move("ドラゴンテール"), max_attack=5)
    results_without = t.calc_lethal(without_ability, player_idx=0, moves=Move("ドラゴンテール"), max_attack=5)

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

    results = t.calc_lethal(battle, player_idx=0, moves=Move("ドラゴンテール"), max_attack=5)

    # 1発目: ダメージ分布が0（攻撃は無効化される）
    assert results[0].min_damage == 0
    assert results[0].max_damage == 0
    # 1発目後のHP = max_hp - 変身解除ダメージのみ
    assert max(results[0].hp_counter) == max_hp - disguise_damage
    # 1発目後: 全状態でability_enabledがFalseになる
    assert all(not state.ability_enabled for state in results[0].hp_dist)


def test_フルールカノン_とくこうダウン():
    """フルールカノン: 命中後にとくこうが2段階下がるため2発目のダメージが減少する"""
    battle = t.start_battle(
        team0=[Pokemon("マギアナ")],
        team1=[Pokemon("カビゴン")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=Move("フルールカノン"), max_attack=2)
    assert results[1].min_damage < results[0].min_damage


def test_フレアソング_とくこうアップ_secondary有り():
    """フレアソング: secondary=True のとき命中後にとくこうが1段階上がり、2発目のダメージが増加する"""
    battle = t.start_battle(
        team0=[Pokemon("カイリュー")],
        team1=[Pokemon("カビゴン")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=Move("フレアソング"), max_attack=2, secondary=True)
    assert results[1].min_damage > results[0].min_damage


def test_フレアソング_とくこうアップ_secondary無し():
    """フレアソング: secondary=False のときとくこうアップが発動せず2発目のダメージが変わらない"""
    battle = t.start_battle(
        team0=[Pokemon("カイリュー")],
        team1=[Pokemon("カビゴン")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=Move("フレアソング"), max_attack=2, secondary=False)
    assert results[1].min_damage == results[0].min_damage


def test_ホイールスピン_すばやさランクダウン():
    """ホイールスピン: 確定効果（ちからずくの対象外）のため、secondary指定に関わらず攻撃側のすばやさが2段階下がる"""
    battle = t.start_battle(
        team0=[Pokemon("メタグロス")],
        team1=[Pokemon("カビゴン")],
    )
    monitor = LethalMonitor()
    t.calc_lethal(battle, player_idx=0, moves=Move("ホイールスピン"), max_attack=1, secondary=False, monitor=monitor)
    assert monitor.attacker.boosts["spe"] == -2


def test_ほうふく_直近の被弾ダメージの1_5倍を与える():
    """ほうふく: メタルバーストと同じ式（直近の被弾ダメージ×1.5、切り捨て）。"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    attacker = battle.actives[0]
    attacker.last_damage_taken = {"damage": 51, "category": "special"}

    results = t.calc_lethal(battle, player_idx=0, moves=Move("ほうふく"), max_attack=1)

    assert results[0].min_damage == 76
    assert results[0].max_damage == 76


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
    r_with = t.calc_lethal(with_item, player_idx=0, moves=move, max_attack=3)
    r_without = t.calc_lethal(without_item, player_idx=0, moves=move, max_attack=3)

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
    results_move = t.calc_lethal(battle_move, player_idx=0, moves=Move("ほのおのうず"), max_attack=2)
    results_pre = t.calc_lethal(battle_pre, player_idx=0, moves=Move("ほのおのうず"), max_attack=2)
    assert max(results_move[1].hp_counter) == max(results_pre[1].hp_counter)


def test_ほのおのまい_とくこうアップ_secondary有り():
    """ほのおのまい: secondary=True のとき命中後にとくこうが1段階上がり、2発目のダメージが増加する"""
    battle = t.start_battle(
        team0=[Pokemon("カイリュー")],
        team1=[Pokemon("カビゴン")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=Move("ほのおのまい"), max_attack=2, secondary=True)
    assert results[1].min_damage > results[0].min_damage


def test_ほのおのまい_とくこうアップ_secondary無し():
    """ほのおのまい: secondary=False のときとくこうアップが発動せず2発目のダメージが変わらない"""
    battle = t.start_battle(
        team0=[Pokemon("カイリュー")],
        team1=[Pokemon("カビゴン")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=Move("ほのおのまい"), max_attack=2, secondary=False)
    assert results[1].min_damage == results[0].min_damage


def test_ほのおのムチ_ぼうぎょダウン_secondary有り():
    """ほのおのムチ: secondary=True のとき相手のぼうぎょが1段階下がり、2発目のダメージが増加する"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=Move("ほのおのムチ"), max_attack=2, secondary=True)
    assert results[1].min_damage > results[0].min_damage


def test_ほのおのムチ_ぼうぎょダウン_secondary無し():
    """ほのおのムチ: secondary=False のときはぼうぎょダウンが発動せず2発目のダメージが変わらない"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=Move("ほのおのムチ"), max_attack=2, secondary=False)
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
    t.apply_ailment(with_ability, player_idx=1, ailment_name="どく")

    results_with = t.calc_lethal(with_ability, player_idx=0, moves=Move("たいあたり"), max_attack=2)
    results_without = t.calc_lethal(without_ability, player_idx=0, moves=Move("たいあたり"), max_attack=2)

    max_hp = with_ability.actives[1].max_hp
    heal = max(1, max_hp // 8)
    assert max(results_with[1].hp_counter) - max(results_without[1].hp_counter) == heal * 2


def test_まきつく_バインド付与():
    """まきつくは命中後にバインドを付与し、ターン終了時ダメージが発生する（バインド事前付与と同じ結果）"""
    battle_move = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    battle_pre = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
        volatile1={"バインド": 5},
    )
    results_move = t.calc_lethal(battle_move, player_idx=0, moves=Move("まきつく"), max_attack=2)
    results_pre = t.calc_lethal(battle_pre, player_idx=0, moves=Move("まきつく"), max_attack=2)
    assert max(results_move[1].hp_counter) == max(results_pre[1].hp_counter)


def test_まとわりつく_バインド付与():
    """まとわりつくは命中後にバインドを付与し、ターン終了時ダメージが発生する（バインド事前付与と同じ結果）"""
    battle_move = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    battle_pre = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
        volatile1={"バインド": 5},
    )
    results_move = t.calc_lethal(battle_move, player_idx=0, moves=Move("まとわりつく"), max_attack=2)
    results_pre = t.calc_lethal(battle_pre, player_idx=0, moves=Move("まとわりつく"), max_attack=2)
    assert max(results_move[1].hp_counter) == max(results_pre[1].hp_counter)


def test_マルチスケイル_ダメージ半減():
    """マルチスケイル所持時、HP満タンの1発目のみダメージが半減する"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", ability_name="マルチスケイル")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=[(Move("ドラゴンテール"), 1)])

    assert results[-1].attack_count == 3
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


def test_みねうち_HPが1で止まり致死率が常に0になる():
    """みねうち: 通常のダメージ計算結果を「直前の防御側HP-1」でキャップするため、
    相手をひんしにさせることは無い。防御側のHPをあらかじめ低い値（5）にしておき、
    通常ダメージなら確実に上回る状況を作って、キャップが効いてHP1で止まり続ける
    ことを確認する（2発目以降、HPが1のときはキャップにより実ダメージも0になる）。"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    defender = battle.actives[1]
    defender.hp = 5  # テストのセットアップ専用の直接代入

    results = t.calc_lethal(battle, player_idx=0, moves=Move("みねうち"), max_attack=3)

    for r in results:
        assert r.lethal_probability == 0.0
        assert list(r.hp_counter.keys()) == [1]
    # 1発目: 5-1=4 に確定でキャップされる（通常ダメージはこれを上回るため）
    assert results[0].min_damage == 4
    assert results[0].max_damage == 4
    # 2発目以降: 直前HPが既に1のため、キャップの結果ダメージは常に0
    assert results[1].min_damage == 0
    assert results[1].max_damage == 0


def test_ミラーコート_直近の特殊被弾ダメージの2倍を与える():
    """ミラーコート: 直近に受けた特殊ダメージ×2を固定ダメージとして与える。"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    attacker = battle.actives[0]
    attacker.last_damage_taken = {"damage": 50, "category": "special"}

    results = t.calc_lethal(battle, player_idx=0, moves=Move("ミラーコート"), max_attack=1)

    assert results[0].min_damage == 100
    assert results[0].max_damage == 100


def test_みわくのボイス_こんらん付与_ランク上昇時_secondary有り():
    """みわくのボイス: 相手がそのターンにランクが上がっていれば、secondary=Trueでこんらん状態にする"""
    battle = t.start_battle(
        team0=[Pokemon("ピクシー")],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    defender.stat_raised_this_turn = True
    ctx = LethalContext(battle.actives[0], defender, Move("みわくのボイス"), move_secondary=True)
    l.みわくのボイス_apply_confusion_to_defender(battle, ctx, to_dist(defender.hp))
    assert "こんらん" in defender.volatiles


def test_みわくのボイス_ランク上昇なしなら発動しない():
    """みわくのボイス: 相手がそのターンにランクが上がっていなければ、secondary=Trueでも発動しない"""
    battle = t.start_battle(
        team0=[Pokemon("ピクシー")],
        team1=[Pokemon("カビゴン")],
    )
    defender = battle.actives[1]
    ctx = LethalContext(battle.actives[0], defender, Move("みわくのボイス"), move_secondary=True)
    l.みわくのボイス_apply_confusion_to_defender(battle, ctx, to_dist(defender.hp))
    assert "こんらん" not in defender.volatiles


def test_メタルバースト_直近の被弾ダメージの1_5倍を与える():
    """メタルバースト: 直近に受けたダメージ（種別問わず）×1.5（切り捨て）を固定ダメージ
    として与える。手計算: 51 × 1.5 = 76.5 → 切り捨てで76。"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    attacker = battle.actives[0]
    attacker.last_damage_taken = {"damage": 51, "category": "physical"}

    results = t.calc_lethal(battle, player_idx=0, moves=Move("メタルバースト"), max_attack=1)

    assert results[0].min_damage == 76
    assert results[0].max_damage == 76


def test_メテオビーム_とくこうアップ_secondary有り():
    """メテオビーム: secondary=True のときチャージ前にとくこうが1段階上がり、2発目のダメージが増加する"""
    battle = t.start_battle(
        team0=[Pokemon("カイリュー")],
        team1=[Pokemon("カビゴン")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=Move("メテオビーム"), max_attack=2, secondary=True)
    assert results[1].min_damage > results[0].min_damage


def test_メテオビーム_とくこうアップ_secondary無し():
    """メテオビーム: secondary=False のときとくこうアップが発動せず2発目のダメージが変わらない"""
    battle = t.start_battle(
        team0=[Pokemon("カイリュー")],
        team1=[Pokemon("カビゴン")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=Move("メテオビーム"), max_attack=2, secondary=False)
    assert results[1].min_damage == results[0].min_damage


def test_もうどく_ポイズンヒール所持でも経過ターンは加算される():
    """もうどく: ポイズンヒール所持時はダメージを与えないが、
    実際にダメージを受けたかどうかに関わらず経過ターン数は通常どおり加算される"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("グライオン", ability_name="ポイズンヒール")],
    )
    attacker = battle.actives[0]
    defender = battle.actives[1]
    t.apply_ailment(battle, player_idx=1, ailment_name="もうどく")

    ctx = LethalContext(attacker, defender, Move("たいあたり"))
    hp_dist = to_dist(defender.max_hp)

    result = l.もうどく_damage(battle, ctx, hp_dist)

    assert defender.ailment.elapsed_turns == 1, "ポイズンヒール所持時もelapsed_turnsは加算される"
    assert set(result) == {State(defender.max_hp)}, "ポイズンヒール所持時はダメージを与えない"


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
    t.apply_ailment(with_ailment, player_idx=1, ailment_name="もうどく")

    results_with = t.calc_lethal(with_ailment, player_idx=0, moves=Move("たいあたり"), max_attack=2)
    results_without = t.calc_lethal(without_ailment, player_idx=0, moves=Move("たいあたり"), max_attack=2)

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
    t.apply_ailment(with_ailment, player_idx=1, ailment_name="やけど")

    results_with = t.calc_lethal(with_ailment, player_idx=0, moves=Move("たいあたり"), max_attack=2)
    results_without = t.calc_lethal(without_ailment, player_idx=0, moves=Move("たいあたり"), max_attack=2)

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

    results_with = t.calc_lethal(with_volatile, player_idx=0, moves=Move("たいあたり"), max_attack=2)
    results_without = t.calc_lethal(without_volatile, player_idx=0, moves=Move("たいあたり"), max_attack=2)

    max_hp = with_volatile.actives[1].max_hp
    damage = max(1, max_hp // 8)
    assert max(results_without[1].hp_counter) - max(results_with[1].hp_counter) == damage * 2


def test_りゅうせいぐん_とくこうダウン():
    """りゅうせいぐん: 命中後にとくこうが2段階下がるため2発目のダメージが減少する"""
    battle = t.start_battle(
        team0=[Pokemon("カイリュー")],
        team1=[Pokemon("カビゴン")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=Move("りゅうせいぐん"), max_attack=2)
    assert results[1].min_damage < results[0].min_damage


def test_りんごさん_とくぼうダウン_secondary有り():
    """りんごさん: secondary=True のとき相手のとくぼうが1段階下がり、2発目のダメージが増加する"""
    battle = t.start_battle(
        team0=[Pokemon("カイリュー")],
        team1=[Pokemon("カビゴン")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=Move("りんごさん"), max_attack=2, secondary=True)
    assert results[1].min_damage > results[0].min_damage


def test_りんごさん_とくぼうダウン_secondary無し():
    """りんごさん: secondary=False のときはとくぼうダウンが発動せず2発目のダメージが変わらない"""
    battle = t.start_battle(
        team0=[Pokemon("カイリュー")],
        team1=[Pokemon("カビゴン")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=Move("りんごさん"), max_attack=2, secondary=False)
    assert results[1].min_damage == results[0].min_damage


def test_リーフストーム_とくこうダウン():
    """リーフストーム: 命中後にとくこうが2段階下がるため2発目のダメージが減少する"""
    battle = t.start_battle(
        team0=[Pokemon("カイリュー")],
        team1=[Pokemon("カビゴン")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=Move("リーフストーム"), max_attack=2)
    assert results[1].min_damage < results[0].min_damage


def test_ルミナコリジョン_とくぼうダウン_secondary有り():
    """ルミナコリジョン: secondary=True のとき命中後に相手のとくぼうが2段階下がるため2発目のダメージが増加する"""
    battle = t.start_battle(
        team0=[Pokemon("カイリュー")],
        team1=[Pokemon("カビゴン")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=Move("ルミナコリジョン"), max_attack=2, secondary=True)
    assert results[1].min_damage > results[0].min_damage


def test_ルミナコリジョン_とくぼうダウン_secondary無し():
    """ルミナコリジョン: secondary=False のときはとくぼうダウンが発動せず2発目のダメージが変わらない"""
    battle = t.start_battle(
        team0=[Pokemon("カイリュー")],
        team1=[Pokemon("カビゴン")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=Move("ルミナコリジョン"), max_attack=2, secondary=False)
    assert results[1].min_damage == results[0].min_damage


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
    results_with = t.calc_lethal(battle_secondary, player_idx=0, moves=Move("れんごく"), max_attack=2, secondary=True)
    results_without = t.calc_lethal(battle_no_secondary, player_idx=0, moves=Move("れんごく"), max_attack=2, secondary=False)
    max_hp = battle_secondary.actives[1].max_hp
    burn_damage = max(1, max_hp // 16)
    assert max(results_without[1].hp_counter) - max(results_with[1].hp_counter) == burn_damage * 2


def test_一撃必殺技_がんじょう所持で1発目は耐えて2発目で倒れる():
    """がんじょうは満タンHPから瀕死になる攻撃をHP1で耐える。一撃必殺技のダメージは
    満タンHPそのものになるため、この防御が自然に働き1発目はHP1で生存
    （致死率0%）、2発目（残りHP1へのダメージ1）で確定的に倒れる（致死率100%）。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", level=50)],
        team1=[Pokemon("カビゴン", ability_name="がんじょう")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=Move("じわれ"), max_attack=2)

    assert results[0].lethal_probability == 0.0
    assert list(results[0].hp_counter.keys()) == [1]
    assert results[1].lethal_probability == 1.0


def test_一撃必殺技_きあいのタスキ所持で1発目はHP1で耐える():
    """きあいのタスキも満タンHPからの瀕死をHP1で耐える（1回のみ消費）。
    一撃必殺技の1発目でもこの効果が発動することを確認する。"""
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", level=50)],
        team1=[Pokemon("カビゴン", item_name="きあいのタスキ")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=Move("じわれ"), max_attack=1)

    assert results[0].lethal_probability == 0.0
    assert list(results[0].hp_counter.keys()) == [1]


def test_固定ダメージ技と一撃必殺技のlethal_handlers登録漏れが無い():
    """回帰防止テスト: `flags` に fixed_damage または ohko を持つ実装済み技すべてが
    lethal_handlers に LethalEvent.ON_BEFORE_HIT のエントリを持つことを機械的に検証する。
    将来これらのフラグを持つ新しい技が実装された際、lethal_handlers の登録漏れ
    （＝lethal計算で常にダメージ0になるバグ、本PRの根本原因）を検知する。

    カウンター・ミラーコート・メタルバースト・ほうふくは fixed_damage/ohko フラグを
    持たない（実戦でも通常のダメージ計算経路を通らず ON_MODIFY_MOVE_DAMAGE で
    直接上書きする方式のため）ため、対象技名を明示リストで別途検証する。
    """
    missing_by_flag = [
        name for name, data in MOVES.items()
        if data.exist
        and (data.flags & {"fixed_damage", "ohko"})
        and LethalEvent.ON_BEFORE_HIT not in data.lethal_handlers
    ]
    assert missing_by_flag == []

    reflect_moves = ["カウンター", "ミラーコート", "メタルバースト", "ほうふく"]
    missing_reflect = [
        name for name in reflect_moves
        if LethalEvent.ON_BEFORE_HIT not in MOVES[name].lethal_handlers
    ]
    assert missing_reflect == []


def test_多段技_2攻撃目の途中で致死枝が出ても確定数が正しい():
    """ドデカバシ タネマシンガン5ヒット(22~26/hit) → カバルドン H215:
    2攻撃目の4ヒット目(累計9ヒット)で最高乱数側のみ HP0 になるが、
    5ヒット目まで適用されて確定2発になる"""
    attacker = Pokemon("ドデカバシ", nature="いじっぱり", ability_name="スキルリンク")
    defender = Pokemon("カバルドン", nature="わんぱく")
    defender.set_evs({"hp": 32}, hp_policy="full")
    battle = t.start_battle(team0=[attacker], team1=[defender])
    results = t.calc_lethal(
        battle, player_idx=0, moves=[(Move("タネマシンガン"), 5)], max_attack=2,
    )

    assert results[0].min_damage == 22
    assert results[0].max_damage == 26
    assert results[-2].lethal_probability == pytest.approx(0.0336, abs=0.001)
    assert results[-1].attack_count == 2
    assert results[-1].hit_count == 5
    assert results[-1].lethal_probability == 1.0


def test_多段技_resume_from経由でも2攻撃目の確定数が正しい():
    """1攻撃目の results[-1] を resume_from に渡して2攻撃目を計算しても、
    max_attack=2 で一括計算した場合と同じ確定2発になる"""
    attacker = Pokemon("ドデカバシ", nature="いじっぱり", ability_name="スキルリンク")
    defender = Pokemon("カバルドン", nature="わんぱく")
    defender.set_evs({"hp": 32}, hp_policy="full")
    battle = t.start_battle(team0=[attacker], team1=[defender])
    first = t.calc_lethal(
        battle, player_idx=0, moves=[(Move("タネマシンガン"), 5)], max_attack=1,
    )
    second = t.calc_lethal(
        battle, player_idx=0, moves=[(Move("タネマシンガン"), 5)], max_attack=1,
        resume_from=first[-1],
    )

    assert first[-1].lethal_probability == 0.0
    assert [r.hit_count for r in second] == [1, 2, 3, 4, 5]
    assert second[-1].attack_count == 2
    assert second[-1].lethal_probability == 1.0


def test_多段技_ヒットごとに分布を記録():
    """スケイルショットのような多段技は、ヒットごとに LethalHitResult が積まれる"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", ability_name="マルチスケイル")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=[(Move("スケイルショット"), 4)])

    assert [r.hit_count for r in results] == [1, 2, 3, 4]
    assert all(r.attack_count == 1 for r in results)
    assert results[0].min_damage == 19
    assert results[0].max_damage == 24


def test_多段技_全枝がHP0になった後のヒットはダメージ0():
    """全枝が HP0 になった後のヒットは damage_dist が {0: 1} になる"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=[(Move("スケイルショット"), 6)])

    assert results[4].lethal_probability == 1.0
    assert results[5].hit_count == 6
    assert results[5].damage_counter == {0: 1}
    assert results[5].lethal_probability == 1.0


def test_多段技_致死枝が出た後も生存枝のダメージ分布が汚れない():
    """致死枝が出た後のヒットの damage_dist は生存枝に対するダメージ分布であり、
    HP0 枝の 0 ダメージが混ざらない"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=[(Move("スケイルショット"), 5)])

    assert results[3].lethal_probability > 0
    assert results[4].min_damage == 38
    assert results[4].max_damage == 48


def test_多段技_致死枝が出た後も生存枝のヒット時ハンドラが動く():
    """致死枝が出た後のヒットでも、生存枝には ON_HIT ハンドラ（じきゅうりょくの
    ぼうぎょ上昇）が適用される。4ヒット目で一部の枝が HP0 になった後、
    5ヒット目のダメージは4ヒット目のぼうぎょ上昇を反映して下がる"""
    monitor = LethalMonitor()
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("ピカチュウ", ability_name="じきゅうりょく")],
    )
    results = t.calc_lethal(
        battle, player_idx=0, moves=[(Move("スケイルショット"), 5)], monitor=monitor,
    )

    assert 0 < results[3].lethal_probability < 1
    assert results[3].max_damage == 19
    assert results[4].max_damage == 16
    # 5ヒット目の生存枝にも ON_HIT が適用され、ぼうぎょは5段階上がる
    assert monitor.defender.boosts["def"] == 5


def test_多段技_途中ヒットで致死枝が出ても全ヒット適用する():
    """連続技の途中ヒットで一部の枝が HP0 になっても、指定ヒット数まで
    すべて適用される（参考値 1.2: 4hit 乱数1発 81.91%, 5hit 確定1発）"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=[(Move("スケイルショット"), 5)])

    assert [r.hit_count for r in results] == [1, 2, 3, 4, 5]
    assert results[3].lethal_probability == pytest.approx(0.8191, abs=0.001)
    assert results[4].lethal_probability == 1.0


def test_多段技マルチスケイル_1ヒット目のみ半減():
    """多段技はヒットごとにHPが実際に更新されるため、マルチスケイルはHP満タンの
    1ヒット目のみ発動し、2ヒット目以降はダメージが半減されない"""
    battle = t.start_battle(
        team0=[Pokemon("ガブリアス")],
        team1=[Pokemon("カイリュー", ability_name="マルチスケイル")],
    )
    results = t.calc_lethal(battle, player_idx=0, moves=[(Move("スケイルショット"), 4)])

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
    results = t.calc_lethal(battle, player_idx=0, moves=[(Move("ドラゴンテール"), 1)])

    assert results[-1].attack_count == 2
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
        battle, player_idx=0, moves=[(Move("ドラゴンテール"), 1), (Move("ドラゴンクロー"), 1)],
    )

    assert results[0].attack_count == 1
    assert results[0].move.name == "ドラゴンテール"
    assert results[1].attack_count == 1
    assert results[1].move.name == "ドラゴンクロー"
    assert results[-1].attack_count == 1
    assert results[-1].lethal_probability == pytest.approx(0.9453, abs=0.001)
