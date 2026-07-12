"""fuzzテストで発見されたバグの回帰テスト。

再現性のあるランダムシードをそのまま固定するのではなく、原因箇所を特定した上で
core/エンジン共通ロジックの最小ケースとして再現する。
"""
from jpoke import Battle, Player
from jpoke.model import Pokemon
from jpoke.enums import Command, LogCode
from jpoke.handlers.move import get_forced_switch_commands
from jpoke.players import TreeSearchPlayer

from . import test_utils as t


def test_Vジェネレート_相手を撃破した場合でも自己ランク低下ログが勝敗確定ログより先に記録される():
    """seed=5 (LogInconsistency@status_manager.py:modify_hp:94) の回帰テスト。

    StatusManager.modify_hp は、瀕死判定でON_HP_CHANGEDを発火する前に
    battle.judge_winner()（GAME_WON/GAME_LOSTログの記録を含む）を呼んでいたため、
    ログの記述順序が実際の処理順序と矛盾していた。修正前は、相手の最後の1匹を
    倒す技（Vジェネレート等、Event.ON_HITで自己ランクを下げる技）を使うと、
    「勝利/敗北」ログの後に「ぼうぎょが1段階下がった…」ログが記録されてしまい、
    ログを時系列順に読んだときに勝敗確定後もダメージ処理由来の効果が
    発生しているように見えてしまっていた。

    修正後は、勝者の判定・確定（battle.winner の設定）自体は即座に行うが、
    GAME_WON/GAME_LOSTログの記録は core/move_executor.py の _execute_hit が
    ON_HIT・ON_DAMAGE_HIT・ON_MOVE_KOの発火まで完了してから
    battle.end_deferred_winner_log() で行うため、自己ランク低下ログの方が
    先に記録されることを確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["Vジェネレート"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    defender.hp = 1
    t.fix_damage(battle, 1)

    t.run_move(battle, 0)

    assert defender.fainted
    assert attacker.boosts["def"] == -1
    assert attacker.boosts["spd"] == -1
    assert attacker.boosts["spe"] == -1

    logs = battle.event_logger.logs
    stat_idx = next(i for i, log in enumerate(logs) if log.log == LogCode.STAT_CHANGED)
    won_idx = next(i for i, log in enumerate(logs) if log.log == LogCode.GAME_WON)
    # 修正前は won_idx < stat_idx になっていた
    assert stat_idx < won_idx


def test_あめまみれ_ミラーアーマー所持者自身にかかった場合でもAttributeErrorが発生しない():
    """seed=13 (AttributeError@status_manager.py:modify_stats:132) の回帰テスト。

    handlers/volatile.py の あめまみれ_turn_end は、ターン終了時の自傷的な
    すばやさ低下 (`battle.modify_stats(mon, {"spe": -1})`) を発生させる際に
    source引数を渡していなかった。このコードベースの自傷効果（かえんだまの
    自己やけど、ムラっけの自己ランク変化など）は source=自分自身 を明示する
    規約になっており、省略するとEventContext.source=Noneになる。

    あめまみれを受けたポケモンがミラーアーマーを持っていると、
    handlers/ability.py の ミラーアーマー_reflect_stat_drop が
    ctx.is_foe_target()（source != targetで判定）でNone != targetのため
    真になってしまい、「相手由来のランク低下」と誤認識してctx.source（=None）
    へ反射しようとし、None.modify_statでAttributeErrorになっていた。

    修正後は source=mon が明示され、is_foe_target()がFalseになるため、
    反射は発動せず自分自身のすばやさのみが下がることを確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="ミラーアーマー")],
        team1=[Pokemon("カビゴン")],
        volatile0={"あめまみれ": 2},
    )
    mon, foe = battle.actives

    battle.step()  # 修正前はここでAttributeErrorになっていた

    assert mon.boosts["spe"] == -1
    assert foe.boosts["spe"] == 0


def test_いかく_交代フェーズの割り込み連鎖でValueErrorや残留コマンドのIndexErrorが発生しない():
    """seed=214 (IndexError@command_manager.py:resolve_move_from_command:133) の回帰テスト。

    交代フェーズ（_run_switch_phase）で素早さの速いプレイヤーがいかく持ちに交代すると、
    相手のだっしゅつパック持ちの攻撃ランクが下がり、その相手自身の行動順が交代フェーズの
    ループに回ってくる前に割り込みで強制交代される。この場合、修正前は2つの不具合があった。

    1. `self.battle.actives.index(attacker)` でループのたびに場を引き直していたため、
       既に割り込みで交代してactivesから消えた元のポケモン参照に対してValueErrorが発生していた。
    2. 相手（だっしゅつパック側）が元々予約していた技コマンド（MOVE_1）は、交代フェーズでも
       技フェーズでも一度もpop_command()されないまま予約リストに残り続けていた。
       次ターンに新しいコマンドが予約リストの末尾に積まれるため、残留したMOVE_1が先に使われ、
       交代後の（技を1つしか持たない）ポケモンに対してcommand_manager.resolve_move_from_commandで
       IndexErrorが発生していた。
    """
    battle = t.start_battle(
        team0=[
            Pokemon("ピカチュウ", move_names=["でんきショック"]),
            Pokemon("コラッタ", ability_name="いかく", move_names=["たいあたり"]),
        ],
        team1=[
            Pokemon("カビゴン", item_name="だっしゅつパック", move_names=["まるくなる", "たいあたり"]),
            Pokemon("ポッポ", move_names=["たいあたり"]),
        ],
    )
    player0, player1 = battle.players

    # Turn1: 通常ターンを進め、両者が交代コマンドを選べる状態にする。
    battle.step(commands={player0: Command.MOVE_0, player1: Command.MOVE_0})

    # Turn2: 素早さの速いピカチュウ側がいかく持ちのコラッタに交代する。
    # いかくでカビゴンのこうげきが下がり、だっしゅつパックの割り込み交代が発生する。
    # この時点でカビゴンが予約していたMOVE_1（たいあたり）は一度も使われずに残る。
    # 修正前はこのターンでValueErrorが発生していた。
    battle.step(commands={player0: Command.SWITCH_1, player1: Command.MOVE_1})

    assert battle.actives[0].name == "コラッタ"
    # だっしゅつパックの割り込みでポッポに自動的に交代済み
    assert battle.actives[1].name == "ポッポ"

    # Turn3: 交代後のポッポは技を1つ（index=0）しか持たない。
    # 修正前は残留したMOVE_1（index=1）が誤って使われ、IndexErrorが発生していた。
    battle.step()

    assert battle.turn == 3  # 例外なく3ターン目が完了したことを確認


def test_ききかいひ_割り込み交代で使われなかった行動コマンドが次のターンに誤って使われない():
    """seed=214 (IndexError@command_manager.py:resolve_move_from_command:133) の回帰テスト。

    ききかいひ・だっしゅつパックなどの割り込み交代が、対象プレイヤー自身の行動順が
    来る前に発動すると、そのプレイヤーが元々予約していた行動コマンド（交代前の
    ポケモン用の技コマンド）がpop_command()されないまま予約リストに残ってしまう。
    次のターンに新しく選択されたコマンドがFIFOの末尾に積まれるため、古い（交代前の
    ポケモン用の）コマンドが先に使われ、交代後の（技が少ない）ポケモンのmovesに
    対して範囲外アクセスしIndexErrorになっていた。

    交代後のポケモンが技を1つしか持たない状態で、交代前に予約していた2番目の技
    コマンド（index=1）が破棄され、次のターンの行動順解決でIndexErrorが発生しない
    ことを確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック"])],
        team1=[
            Pokemon(
                "カビゴン", ability_name="ききかいひ",
                move_names=["まるくなる", "たいあたり"],
            ),
            Pokemon("コラッタ", move_names=["たいあたり"]),
        ],
    )
    player0, player1 = battle.players
    defender = battle.actives[1]
    defender.hp = defender.max_hp // 2 + 1
    t.fix_damage(battle, 1)

    # Turn1: ピカチュウが先制して攻撃し、カビゴンのHPが半分以下になってききかいひが
    # 発動する。この時点でカビゴンが元々予約していたMOVE_1（たいあたり）は
    # 使われないまま予約リストに残ってしまう箇所が今回のバグの原因。
    battle.step(commands={player0: Command.MOVE_0, player1: Command.MOVE_1})

    assert battle.actives[1].name == "コラッタ"

    # Turn2: 交代後のコラッタは技を1つ（index=0）しか持たない。
    # 修正前は残留したMOVE_1（index=1）が誤って使われ、
    # command_manager.resolve_move_from_commandでIndexErrorが発生していた。
    battle.step()

    assert battle.turn == 2  # 例外なく2ターン目が完了したことを確認


def test_こだわり_技を4つ持つ状態で控えが5匹以上いてもコマンド取得でIndexErrorが発生しない():
    """seed=109 (IndexError@volatile.py:restrict_commands:126) の回帰テスト。

    restrict_commandsは、コマンド候補が交代コマンドか技コマンドかを判定する前に
    `mon.moves[cmd.index]` へアクセスしていたため、技を4つしか持たないポケモンが
    こだわり状態で控えを5匹以上（SWITCH_5など、index>=4のスロット番号）抱えている場合、
    交代コマンドの評価時にIndexErrorが発生していた。
    技コマンドか交代コマンドかを判定した後にのみmovesへアクセスすることで、
    交代コマンドが正しく候補に含まれ、固定技以外の技コマンドは除外されることを確認する。
    """
    battle = t.start_battle(
        team0=[
            Pokemon("ピカチュウ", move_names=["たいあたり", "でんきショック", "なきごえ", "でんこうせっか"]),
            Pokemon("コラッタ"),
            Pokemon("ポッポ"),
            Pokemon("キャタピー"),
            Pokemon("ビードル"),
            Pokemon("イーブイ"),
        ],
        team1=[Pokemon("カビゴン")],
    )
    mon = battle.actives[0]
    battle.volatile_manager.apply(mon, "こだわり", move_name="たいあたり")

    with battle.phase_context("action"):
        commands = battle.get_available_commands(battle.players[0])

    # 固定技（MOVE_0）以外の技コマンドは除外され、控え5匹分の交代コマンドは全て候補に含まれる
    move_commands = [cmd for cmd in commands if cmd.is_regular_move]
    switch_commands = [cmd for cmd in commands if cmd.is_type("switch")]
    assert move_commands == [Command.MOVE_0]
    assert switch_commands == [
        Command.SWITCH_1,
        Command.SWITCH_2,
        Command.SWITCH_3,
        Command.SWITCH_4,
        Command.SWITCH_5,
    ]


def test_さめはだ_相手を撃破した場合でも反撃ダメージログが勝敗確定ログより先に記録される():
    """seed=5 と同一signature（LogInconsistency@status_manager.py:modify_hp:94）の
    根本原因に対する横展開の回帰テスト。

    modify_hp(defer_winner_log=True) で技のダメージ処理だけを遅延させる最初の
    修正案は、Event.ON_HIT / ON_DAMAGE_HIT の発火中に発生する「別の」modify_hp
    呼び出し（さめはだ・てつのトゲ等、接触技を受けた際に攻撃側へ固定ダメージを
    返す特性。デフォルト引数で呼ばれるため defer_winner_log=False）が、
    技のダメージ処理でまだ確定していないGAME_WON/GAME_LOSTログを巻き込んで
    即座にフラッシュしてしまう問題が残っていた。相手の最後の1匹をさめはだ持ちの
    ポケモンに接触技で倒すと、「勝利/敗北」ログの後に「さめはだが発動した」ログ
    （および攻撃側へのHP変化ログ）が記録されてしまっていた。

    修正後は core/turn_controller.py にネスト可能な抑制区間
    （begin_deferred_winner_log / end_deferred_winner_log）を導入し、
    move_executor._execute_hit の1ヒット処理全体をこの区間で囲むことで、
    区間内で発生する任意のmodify_hp呼び出し（デフォルト引数のものを含む）による
    自動フラッシュを抑制し、区間を開いた呼び出し元が明示的に区間を閉じた時点で
    まとめて記録する。さめはだの反撃ダメージログの方が勝敗確定ログより
    先に記録されることを確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["たいあたり"])],
        team1=[Pokemon("ゴローニャ", ability_name="さめはだ")],
    )
    attacker, defender = battle.actives
    defender.hp = 1
    t.fix_damage(battle, 1)

    t.run_move(battle, 0)

    assert defender.fainted
    assert attacker.hp < attacker.max_hp  # さめはだの反撃ダメージ

    logs = battle.event_logger.logs
    ability_idx = next(i for i, log in enumerate(logs) if log.log == LogCode.ABILITY_TRIGGERED)
    won_idx = next(i for i, log in enumerate(logs) if log.log == LogCode.GAME_WON)
    # 修正前は won_idx < ability_idx になっていた
    assert ability_idx < won_idx


def test_しょうりのほし_ノーガード相手への攻撃でNoneのままTypeErrorが発生しない():
    """seed=1200 (TypeError@math.py:apply_fixed_modifier:41) の回帰テスト。

    ON_MODIFY_ACCURACY イベントチェーンでは、handlers/ability.py の
    ノーガード_guarantee_hit が命中率を必中確定として value=None に書き換えるが、
    stop_event を立てないため後続ハンドラにも value=None がそのまま渡る。
    しょうりのほし_modify_accuracy は value=None を考慮せず
    apply_fixed_modifier(None, 4506) を呼び出し、value * modifier の乗算で
    TypeError（NoneType * int）になっていた。

    攻撃側にしょうりのほし、防御側にノーガードを持たせ、防御側の方が素早いことで
    ON_MODIFY_ACCURACY のハンドラ実行順（priority同点は素早さ降順）で
    ノーガードのvalue=None書き換えがしょうりのほしより先に評価されるようにする
    （この順序でなければ修正前でも偶然クラッシュしない）。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", ability_name="しょうりのほし", move_names=["さいみんじゅつ"])],
        team1=[Pokemon("ピカチュウ", ability_name="ノーガード")],
    )
    t.run_move(battle, 0)  # 修正前はここでTypeErrorになっていた

    assert battle.move_executor.accuracy is None  # ノーガードの必中確定が維持される


def test_じゅうりょく_ノーガード相手への攻撃でNoneのままTypeErrorが発生しない():
    """seed=1200 (TypeError@math.py:apply_fixed_modifier:41) の関連回帰テスト。

    じゅうりょく_modify_accuracy（場の効果）も value=None を考慮せず乗算していた1箇所。
    特性・アイテム・揮発性状態だけでなく場の効果も同種のバグを持っていたことを確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ハイドロポンプ"])],
        team1=[Pokemon("ピカチュウ", ability_name="ノーガード")],
        field={"じゅうりょく": 5},
    )

    t.run_move(battle, 0)  # 修正前はここでTypeErrorになっていた

    assert battle.move_executor.accuracy is None  # 倍率は適用されない


def test_つめたいいわ_所持者がいる場でバインド技を使ってもValueErrorが発生しない():
    """seed=10 player=random (ValueError@context.py:resolve_role:70) の回帰テスト。

    core/query.py の get_volatile_duration（バインド技の継続ターン数を決定する）は
    AttackContext から Event.ON_MODIFY_DURATION を発火していたが、
    ON_MODIFY_DURATION はフィールド・場の状態（天候・地形・壁）の残りターン延長
    ハンドラ（天候いわ系アイテム等、EventContext・subject_spec="source:self"）
    にも登録されていた。天候いわ系アイテム所持者が場にいる状態でバインド技が
    使われると、この共有イベントの発火時にAttackContextからsubject_spec
    "source:self" を解決しようとして、AttackContextがroleを持たない
    （resolve_roleのhasattrチェック）ためValueErrorが発生していた。

    修正後は get_volatile_duration がAttackContext専用の新イベント
    Event.ON_MODIFY_BIND_DURATION を発火するようになり、ON_MODIFY_DURATION
    （EventContext専用）のハンドラとコンテキスト型が競合しなくなる。
    つめたいいわ自体はバインドの継続ターンに影響しないため、通常通り
    4か5ターンになることも確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["まきつく"])],
        team1=[Pokemon("カビゴン", item_name="つめたいいわ")],
        accuracy=100,
    )
    foe = battle.actives[1]

    t.run_move(battle, 0)  # 修正前はここでValueErrorになっていた

    assert foe.has_volatile("バインド")
    assert foe.volatiles["バインド"].count in {4, 5}  # つめたいいわの影響を受けない


def test_トレース_相手の特性をコピーしたまま退場してもハンドラが残留せずON_TURN_END時にValueErrorが発生しない():
    """seed=169 player=random (ValueError@battle.py:foe:556) の回帰テスト。

    core/switch_manager.py の _switch_out は、退場処理内で
    mon.reset_on_switch_out()（トレース等でコピーした特性を素の特性に差し替える）を
    self._unregister_handlers_on_switch_out(mon)（現在登録されている特性のハンドラを
    解除する）より先に実行していた。この順序では、ハンドラを解除する時点で既に
    mon.ability が素の特性（トレース）に差し替わっており、実際に登録されていた
    コピー先の特性（ナイトメア）のハンドラは解除されないまま残留してしまう。

    残留したナイトメアのON_TURN_ENDハンドラ（subject_spec="source:self"）は、
    resolve_roleがctx.source自身（=登録時のsubjectそのもの）を返すため、退場して
    もう場にいないポケモンに対してもsubject一致チェックを素通りして発火し続けてしまい、
    ハンドラ内の battle.foe(mon) が場にいないポケモンに対して呼び出されてValueError
    になっていた。

    修正後はハンドラ解除を特性差し替えより先に行うため、実際に登録されていた
    ナイトメアのハンドラが正しく解除され、退場後のON_TURN_ENDで例外なく完了する
    ことを確認する。
    """
    battle = t.start_battle(
        team0=[
            Pokemon("メタモン", ability_name="トレース"),
            Pokemon("コラッタ"),
        ],
        team1=[Pokemon("デンヂムシ", ability_name="ナイトメア")],
    )
    trace_mon = battle.actives[0]
    # battle.start()時点のON_SWITCH_INでトレースが相手のナイトメアを既にコピー済み
    assert trace_mon.ability.base_name == "ナイトメア"

    t.run_switch(battle, 0, 1)  # 退場処理自体は修正前でも例外は起きない
    assert battle.actives[0].name == "コラッタ"
    assert trace_mon.ability.base_name == "トレース"  # 退場時に素の特性へ戻る

    t.end_turn(battle)  # 修正前はここでValueErrorになっていた


def test_バインド_瀕死交代時にとらわれ状態チェックが誤って適用されない():
    """seed=4 (IndexError@command_manager.py:resolve_command:156) の回帰テスト。

    バインドなどのとらわれ状態を持ったまま瀕死になったポケモンの強制交代は、
    退場処理（とらわれ状態の解除）より前にコマンド解決が行われるため、
    とらわれ状態チェックによって交代コマンド候補が空にならず、
    生存している控えへ正常に交代できることを確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("コラッタ")],
        team1=[Pokemon("カビゴン")],
        volatile0={"バインド": 5},
    )
    mon = battle.actives[0]
    # バインドのターン終了時ダメージ（最低1）で確実に瀕死になるようHPを1にしておく
    battle.modify_hp(mon, v=-(mon.max_hp - 1))
    assert mon.hp == 1

    # ターンを進めると、ターン終了時のバインドダメージで瀕死になり、
    # 瀕死交代が発生する。修正前はcommand_manager.get_available_switch_commandsが
    # とらわれ状態チェックを行い、交代コマンド候補が空になってIndexErrorが発生していた。
    battle.step()

    assert mon.fainted
    assert battle.actives[0] is not mon
    assert battle.actives[0].name == "コラッタ"


def test_ヘドロえき_さいきのいのりで蘇生する瀕死の控えに対してもValueErrorが発生しない():
    """seed=64 player=random (ValueError@battle.py:foe:556) の回帰テスト。

    core/status_manager.py の modify_hp は、HPを回復させる直前に
    Event.ON_MODIFY_HEAL を発火する。さいきのいのりで蘇生する対象（ctx.target）は
    復活処理の時点ではまだ場に出ていない（ベンチのまま）ポケモンだが、
    ヘドロえき特性（subject_spec="target:foe"）のハンドラ有効性チェック
    （core/event_manager.py の _check_handler_validity 経由で呼ばれる
    BaseContext.resolve_role）は、side="foe"のロールをbattle.foe()でそのまま
    解決しようとしていたため、targetが場に出ていないと
    「場に出ていないため、相手のポケモンを特定できません」でValueErrorになっていた。

    修正後は resolve_role が、side="foe"の対象ロールのポケモンがbattle.actives
    （場に出ているポケモン）に含まれない場合、例外を送出せずNoneを返す（「相手」
    という関係自体が定義できない＝該当ハンドラは単に不適用として扱う）。
    ヘドロえき所持ポケモンが場にいる状態でさいきのいのりが例外なく完了し、
    蘇生対象のHPが正しく回復することを確認する。
    """
    battle = t.start_battle(
        team0=[
            Pokemon("ピカチュウ", move_names=["さいきのいのり"]),
            Pokemon("カビゴン"),
        ],
        team1=[Pokemon("ドラピオン", ability_name="ヘドロえき")],
    )
    ally = battle.player_states[battle.players[0]].team[1]
    battle.faint(ally)
    assert ally.hp == 0

    t.run_move(battle, 0)  # 修正前はここでValueErrorになっていた

    assert ally.alive
    assert ally.hp == ally.max_hp // 2


def test_ほえる_強制交代技が選出制限で未選出のポケモンを対象にしない():
    """seed=1 (LogInconsistency@command_manager.py:get_available_switch_commands:69-79)
    の回帰テスト。

    handlers/move.py の get_forced_switch_commands（ほえる・ふきとばし・ともえなげ・
    ドラゴンテール等の強制交代技用の交代先候補生成）は、`state.team`（チーム全体）を
    そのまま走査して交代候補コマンドを組み立てており、選出制限
    （`state.selected_indexes` / `state.selection`）を無視していた。このため
    3匹以上のチームで選出数を絞ったバトルでは、未選出のポケモンまで強制交代の
    対象候補になってしまっていた。

    修正後は `PlayerState.bench`（選出制限を正しく適用した既存プロパティ）を使い、
    未選出のポケモンが候補コマンドに含まれないことを確認する。
    """
    attacker = Player("Attacker")
    attacker.team = [
        Pokemon("ピカチュウ", move_names=["ほえる"]),
        Pokemon("イーブイ"),
    ]
    defender = Player("Defender")
    defender.team = [
        Pokemon("カビゴン"),  # 場に出る（active）
        Pokemon("コラッタ"),  # 選出済みの控え
        Pokemon("ポッポ"),  # 未選出（選出数2に絞っているため選ばれない）
    ]
    battle = Battle(attacker, defender, n_selected=2, seed=1)
    battle.start()

    # 修正前は未選出のポッポ(team index=2)へのSWITCH_2も候補に含まれていた
    commands = get_forced_switch_commands(battle, defender)
    assert commands == [Command.SWITCH_1]


def test_ミクルのみ_ノーガード相手への攻撃でNoneのまま消費されTypeErrorが発生しない():
    """seed=1200 (TypeError@math.py:apply_fixed_modifier:41) の関連回帰テスト。

    ミクルのみ_boost_accuracy も value=None を考慮せず乗算していた1箇所。
    ノーガードでvalue=None書き換えが先に評価される順序でも、アイテムの効果自体
    （消費）は行われるが命中率への倍率は適用されないことを確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="ミクルのみ", move_names=["ハイドロポンプ"])],
        team1=[Pokemon("ピカチュウ", ability_name="ノーガード")],
    )
    mon = battle.actives[0]
    mon.hp = mon.max_hp // 4 + 1
    battle.modify_hp(mon, v=-1)

    t.run_move(battle, 0)  # 修正前はここでTypeErrorになっていた

    assert battle.move_executor.accuracy is None  # 倍率は適用されない
    assert not mon.has_item()  # 効果自体は消費される


def test_めいちゅうアップ_ノーガード相手への攻撃でNoneのまま消費されTypeErrorが発生しない():
    """seed=1200 (TypeError@math.py:apply_fixed_modifier:41) の関連回帰テスト。

    めいちゅうアップ_boost_accuracy も value=None を考慮せず乗算していた1箇所。
    ノーガードでvalue=None書き換えが先に評価される順序でも、揮発性状態の解除
    （効果消費）は行われるが命中率への倍率は適用されないことを確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ハイドロポンプ"])],
        team1=[Pokemon("ピカチュウ", ability_name="ノーガード")],
        volatile0={"めいちゅうアップ": None},
    )
    mon = battle.actives[0]

    t.run_move(battle, 0)  # 修正前はここでTypeErrorになっていた

    assert battle.move_executor.accuracy is None  # 倍率は適用されない
    assert not mon.has_volatile("めいちゅうアップ")  # 効果自体は消費される


def test_レッドカード_選出制限で未選出のポケモンへ強制交代させない():
    """seed=1 (LogInconsistency@command_manager.py:get_available_switch_commands:69-79)
    の回帰テスト。

    handlers/item.py の _レッドカード_try_force_switch（レッドカード発動時、
    攻撃者をランダムな控えポケモンと強制交代させる処理）は、交代候補コマンドを
    `state.team`（チーム全体）から生成しており、選出制限
    （`state.selected_indexes` / `state.selection`）を無視していた。このため
    3匹以上のチームで選出数を絞ったバトルでは、未選出のポケモンへ強制交代させて
    しまうバグがあった。

    修正後は `PlayerState.bench` を使うため、`battle.random.choice` に渡される
    候補コマンドの時点で未選出のポケモンが除外されていることを確認する
    （乱数任せの結果だけでなく、候補生成そのものが正しいことを保証するため
    `random.choice` をラップして渡された候補集合を直接検証する）。
    """
    attacker = Player("Attacker")
    attacker.team = [
        Pokemon("ピカチュウ", move_names=["たいあたり"]),
        Pokemon("コラッタ"),  # 選出済みの控え
        Pokemon("ポッポ"),  # 未選出（選出数2に絞っているため選ばれない）
    ]
    defender = Player("Defender")
    defender.team = [
        Pokemon("カビゴン", item_name="レッドカード"),
        Pokemon("イーブイ"),
    ]
    battle = Battle(attacker, defender, n_selected=2, seed=1)
    battle.start()
    t.fix_damage(battle, 10)

    captured_candidates: list[Command] = []
    original_choice = battle.random.choice

    def capture_choice(seq):
        captured_candidates.extend(seq)
        return original_choice(seq)

    battle.random.choice = capture_choice

    t.run_move(battle, 0)  # ピカチュウのたいあたりでレッドカードが発動する

    # 修正前は未選出のポッポ(team index=2)へのSWITCH_2も候補に含まれていた
    assert captured_candidates == [Command.SWITCH_1]
    assert battle.actives[0].name == "コラッタ"


def test_わるあがき_反動ダメージがON_HITイベントの実ダメージ量を破壊せずレッドカードが正しいタイミングで発動する():
    """seed=430 (ValueError@battle.py:foe:473) の根本原因となった不具合の回帰テスト。

    handlers/move_attack.py の わるあがき_self_damage は、Event.ON_HIT の戻り値
    チェーン（value=相手への実ダメージ量。後続のON_HITハンドラに引き継がれる）に、
    自身への反動ダメージ処理（battle.modify_hp の戻り値、自傷ダメージ量なので負の値）
    をそのまま返してしまっていた。他の反動技用ヘルパー（handlers/move_attack.py の
    _recoil）は元の value をそのまま返しており、この点で一貫していなかった。

    この汚染により、相手が持つレッドカードの「実ダメージ0以下」専用ハンドラ
    （レッドカード_force_switch_on_zero_damage、Event.ON_HIT）が、相手に正の実
    ダメージを与えているにもかかわらず「実ダメージ0以下だった」と誤認識し、
    本来 Event.ON_DAMAGE_HIT 側で発動すべきタイミングより前に攻撃者を強制交代
    させてしまっていた。この誤発動タイミングでは core/move_executor.py の
    _execute_hit がヒット後処理（last_physical_damage_received等の記録）のために
    battle.foe(ctx.attacker) を再解決しようとし、攻撃者が既に交代済みのため
    ValueError が発生していた（まねっこを経由しなくても、わるあがきを直接使う
    だけで再現する最小ケース）。
    """
    battle = t.start_battle(
        team0=[
            Pokemon("ピカチュウ", move_names=["わるあがき"]),
            Pokemon("コラッタ"),
        ],
        team1=[Pokemon("カビゴン", item_name="レッドカード")],
    )
    t.fix_damage(battle, 10)

    t.run_move(battle, 0, 0)  # 修正前はここでValueErrorになっていた

    # コピー元のダメージは正しく相手(カビゴン)に通っている
    assert battle.actives[1].hp == battle.actives[1].max_hp - 10
    # レッドカードで攻撃者(ピカチュウ)が控え(コラッタ)へ強制交代させられている
    assert battle.actives[0].name == "コラッタ"


def test_わるあがき_攻撃時にレッドカードで攻撃者が強制交代してもValueErrorが発生しない():
    """seed=430 (ValueError@battle.py:foe:473) の回帰テスト。

    わるあがきが対象（レッドカード持ち）に実ダメージを与えると、レッドカードが
    発動して攻撃者が強制交代させられる。この強制交代が Event.ON_HIT の時点
    （本来より早いタイミング。詳細は
    test_わるあがき_反動ダメージがON_HITイベントの実ダメージ量を破壊せず
    レッドカードが正しいタイミングで発動する を参照）で発生すると、
    core/move_executor.py の _execute_hit がヒット後処理で
    battle.query.deals_physical_damage(ctx.attacker, ctx.move) 経由で
    battle.foe(ctx.attacker) を再解決しようとし、攻撃者が既に交代済みのため
    ValueError が発生していた。

    修正後は、技のカテゴリは run_move 実行時に確定済みの ctx.move.category を
    再利用するため battle.foe を再解決せず、また わるあがき の反動ダメージ処理も
    ON_HIT の実ダメージ量を破壊しなくなり、例外なく完了することを確認する。

    元のfuzz発見時（seed=430）はまねっこ経由でわるあがきをコピーした際に発生したが、
    その後 わるあがき に non_copycat フラグが付与されまねっこの対象外になったため、
    ここでは わるあがき を直接使用する形で同じ経路を再現する。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", item_name="レッドカード")],
        team1=[
            Pokemon("アブリボン", move_names=["わるあがき"]),
            Pokemon("ニドクイン"),
        ],
    )
    t.fix_damage(battle, 10)

    t.run_move(battle, 1, 0)  # 修正前はここでValueErrorになっていた

    # わるあがきのダメージは正しく相手(カビゴン)に通っている
    assert battle.actives[0].hp == battle.actives[0].max_hp - 10
    # レッドカードでわるあがき使用者(アブリボン)が控え(ニドクイン)へ強制交代させられている
    assert battle.actives[1].name == "ニドクイン"


def test_交代コマンド生成_選出制限で未選出のポケモンを含まない():
    """seed=1 (LogInconsistency@command_manager.py:get_available_switch_commands:69-79)
    の回帰テスト。

    CommandManager.get_available_switch_commands が交代候補コマンドを `state.team`
    （チーム全体）から生成しており、選出制限（`state.selected_indexes` /
    `state.selection`）を無視していた。これにより、3匹以上のチームで選出数を
    絞ったバトルでは、未選出のポケモンまで交代候補コマンドとして生成され、
    瀕死交代・任意交代時に実際に場へ出てしまうバグがあった
    （fuzz_log_battle.py --start-seed 1 --count 1 --max-turns 30 --n-pokemon 3 で検出）。

    修正後は `PlayerState.bench`（選出制限を正しく適用した既存プロパティ）を使い、
    未選出のポケモンが交代候補コマンドに含まれないことを確認する。
    """
    player0 = Player("P0")
    player0.team = [
        Pokemon("ピカチュウ"),  # 場に出る（active）
        Pokemon("コラッタ"),  # 選出済みの控え
        Pokemon("ポッポ"),  # 未選出（選出数2に絞っているため選ばれない）
    ]
    player1 = Player("P1")
    player1.team = [Pokemon("カビゴン"), Pokemon("ゴローニャ")]

    battle = Battle(player0, player1, n_selected=2, seed=1)
    battle.start()

    # 修正前は未選出のポッポ(team index=2)へのSWITCH_2も候補に含まれていた
    with battle.phase_context("action"):
        commands = battle.get_available_commands(player0)
    switch_commands = [cmd for cmd in commands if cmd.is_type("switch")]
    assert switch_commands == [Command.SWITCH_1]


def test_技の追加効果_ダメージで相手を瀕死にした場合は揮発性状態が付与されない():
    """seed=4 (LogInconsistency@volatile_manager.py:apply:51) の回帰テスト。

    VolatileManager.apply も同様に、targetが瀕死かどうかを確認せずに揮発性状態を
    付与していたため、まきつくのように「ダメージを与えたうえで追加効果として
    バインド状態を付与する」技で、その一撃で相手をちょうど瀕死にした場合でも
    バインド状態が付与されてしまっていた。

    修正後は、ダメージでちょうど瀕死になった相手にはバインド状態が付与されないことを
    確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("アーボ", move_names=["まきつく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    defender = battle.actives[1]
    defender.hp = 1
    t.fix_damage(battle, 1)  # ちょうど瀕死になるダメージに固定

    t.run_move(battle, 0)

    assert defender.fainted
    assert not defender.has_volatile("バインド")


def test_技の追加効果_ダメージで相手を瀕死にした場合は状態異常が付与されない():
    """seed=4 (LogInconsistency@ailment_manager.py:apply:51) の回帰テスト。

    AilmentManager.apply は、targetが瀕死かどうかを確認せずに状態異常を付与していたため、
    どくばりのように「ダメージを与えたうえで追加効果として状態異常を付与する」技で、
    その一撃で相手をちょうど瀕死にした場合でも状態異常が付与されてしまっていた
    （実機では、追加効果でダメージにより瀕死になった相手には効果が適用されない）。

    修正後は、ダメージでちょうど瀕死になった相手にはどくが付与されないことを確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["どくばり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    defender = battle.actives[1]
    defender.hp = 1
    t.fix_damage(battle, 1)  # ちょうど瀕死になるダメージに固定

    t.run_move(battle, 0)

    assert defender.fainted
    assert not defender.ailment.is_active


def test_技の追加効果_相手を瀕死にしない場合は状態異常と揮発性状態が従来通り付与される():
    """seed=4 の回帰テストの反例確認。

    瀕死ガードを追加しても、相手が生存する場合の追加効果付与そのものは
    従来通り機能することを確認する（どくばりのどく、まきつくのバインドの両方）。
    """
    poison_battle = t.start_battle(
        team0=[Pokemon("カイリキー", move_names=["どくばり"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
        secondary_chance=1.0,
    )
    poison_defender = poison_battle.actives[1]
    poison_defender.hp = 2
    t.fix_damage(poison_battle, 1)  # 1残して生存させる

    t.run_move(poison_battle, 0)

    assert not poison_defender.fainted
    assert poison_defender.ailment.name == "どく"

    bind_battle = t.start_battle(
        team0=[Pokemon("アーボ", move_names=["まきつく"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    bind_defender = bind_battle.actives[1]
    bind_defender.hp = 2
    t.fix_damage(bind_battle, 1)  # 1残して生存させる

    t.run_move(bind_battle, 0)

    assert not bind_defender.fainted
    assert bind_defender.has_volatile("バインド")


def test_木探索_観測用盤面をコピーしてもobserverが引き継がれ瀕死交代の無限再帰が起きない():
    """tsfuzz seed=3 (RecursionError@copy_utils.py:fast_copy:22) の回帰テスト。

    jpoke.players.tree_search_player の TreeSearchPlayer._worst_case_over_opponent は
    `sim = battle.copy()` で盤面を複製するが、渡された battle が観測用（is_observation()
    が真、つまり observer が設定済み）の場合、Battle.build_observation() は
    is_observation() が真の盤面ではマスク処理自体をスキップして単純な copy() を返すため、
    複製後の sim にも元の観測者がそのまま残ってしまう。

    get_available_commands() は `self.observer == self.opponent(player)` の条件で
    「相手観測分岐」（最後に利用可能だったコマンドのスナップショットを返す）に切り替える。
    sim.step() の内部で瀕死交代が発生し、resolve_command() 経由で observer と食い違う
    プレイヤーのコマンド解決が必要になると、この判定が誤って真になり、まだ交代する前の
    （すでに瀕死になった自分自身への交代コマンドを含む）stale な
    last_available_commands を返し続けてしまう。この結果、選ばれたコマンドが
    実際には瀕死のポケモンへの交代（自分自身への無意味な「交代」）になり、
    switch_manager.run_faint_switch が同じ局面のまま無限に再帰してRecursionErrorになる。

    修正前を決定的に再現するため、以下のように盤面を組む。
    - Victim側はteam[0]が最初はベンチに来るよう選出順序を反転させておく
      （SWITCH_0がteam[0]への交代コマンドとして合法手に含まれるようにするため）。
    - Searcher側はmax_plies=1のTreeSearchPlayerとし、あらゆる攻撃を固定ダメージで
      即座に致死量にする。
    - Victim側の技とベンチを公開済みにし、Searcherの探索木にVictim側のSWITCH_0を
      含む合法手が観測される（build_observationのマスク処理を通過する）ようにする。
    Searcherの探索内部シミュレーションで「Victimがteam[0]に交代し、その直後に
    Searcherの攻撃でteam[0]が瀕死になる」分岐を評価すると、瀕死交代の解決時に
    上記のobserver不整合が発生し、修正前はRecursionErrorになっていた。
    """
    class VictimPlayer(Player):
        """team[0]が最初はベンチに来るよう選出順序を反転させるプレイヤー。"""

        def choose_selection(self, battle: Battle) -> list[int]:
            return list(reversed(range(battle.n_selected)))

    victim = VictimPlayer(username="Victim")
    victim.team = [
        Pokemon("コイキング", move_names=["はねる"]),
        Pokemon("ヒトカゲ", move_names=["たいあたり"]),
    ]

    class DeterministicFallbackPlayer(TreeSearchPlayer):
        def fallback(self, battle: Battle) -> Command:
            return battle.get_available_commands(self)[0]

    searcher = DeterministicFallbackPlayer(username="Searcher", max_plies=1)
    searcher.team = [
        Pokemon("ゼニガメ", move_names=["たいあたり"]),
        Pokemon("カメックス", move_names=["たいあたり"]),
    ]

    battle = Battle(
        victim, searcher, n_selected=2, seed=1,
        mega_evolution=False, terastal=False,
    )
    battle.test_option.accuracy = 100
    battle.start()

    # Searcherの探索木にVictim側の合法手（SWITCH_0を含む）が観測されるように、
    # アクティブの技とベンチのポケモンを公開済みにしておく
    victim_team = battle.player_states[victim].team
    victim_team[1].moves[0].revealed = True
    victim_team[0].revealed = True

    t.fix_damage(battle, 999)  # あらゆる攻撃を確実に致死量にする

    battle.step()  # 修正前はここでRecursionErrorになっていた
