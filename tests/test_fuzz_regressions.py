"""fuzzテストで発見されたバグの回帰テスト。

再現性のあるランダムシードをそのまま固定するのではなく、原因箇所を特定した上で
core/エンジン共通ロジックの最小ケースとして再現する。
"""
from jpoke import Battle, Player
from jpoke.model import Pokemon
from jpoke.enums import Command, Interrupt, LogCode
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


def test_ききかいひ_とんぼがえりのPIVOT割り込みと同時発生してもだっしゅつパック交代処理が無限ループしない():
    """examples/05_benchmark/01_step_time_benchmark.py の完全ランダム編成ベンチマークで、
    PYTHONHASHSEED（プロセスごとに変わる文字列ハッシュのランダム化シード）に依存して
    特定のバトルが終了しなくなる不具合の回帰テスト。

    SwitchManager._process_events_after_switch の交代後リクエスト処理ループは、
    `battle.has_interrupt()`（全プレイヤーの割り込み種別を問わず判定）をループ条件に
    使っていた。しかしこのループの本体が実際に解決できるのは
    Interrupt.EJECTPACK_REQUESTED（だっしゅつパックの連鎖交代）のみで、それ以外の
    割り込み種別（Interrupt.PIVOT等）が残っていても解消する手段を持たない。

    とんぼがえりを撃った側は自分自身にInterrupt.PIVOTを立てるが、そのターンの
    TurnController._run_move_phase では Interrupt.PIVOT の処理より先に
    Interrupt.EMERGENCY（ききかいひ等の緊急交代）の処理が実行される。とんぼがえりの
    一撃で相手をHP半分以下に追い込みききかいひを誘発すると、EMERGENCY割り込み処理内の
    交代後処理（_process_events_after_switch）が、まだ処理されていない自分自身の
    Interrupt.PIVOTを検知してループ条件が永久に真になり、無限ループしていた
    （ハッシュ乱数を用いる処理の関係で、どのランダム編成のバトルでこの状況が
    再現するかはPYTHONHASHSEEDに依存していた）。

    修正後はループ条件をInterrupt.EJECTPACK_REQUESTEDの有無に限定したため、
    自分自身のInterrupt.PIVOTが残っていてもこのループはすぐに終了し、
    呼び出し元のTurnController._run_move_phaseへ処理が戻ってPIVOT割り込みが
    正しく処理されることを確認する。
    """
    battle = t.start_battle(
        team0=[
            Pokemon("ゲッコウガ", move_names=["とんぼがえり"]),
            Pokemon("コイキング"),
        ],
        team1=[
            Pokemon("カビゴン", ability_name="ききかいひ"),
            Pokemon("ポッポ"),
        ],
        accuracy=100,
    )
    attacker, defender = battle.actives
    t.fix_damage(battle, defender.max_hp // 2 + 1)
    player0, player1 = battle.players

    # 修正前はここで無限ループしていた
    battle.step(commands={player0: Command.MOVE_0, player1: Command.MOVE_0})

    assert battle.turn == 1
    assert battle.actives[0].name == "コイキング"  # とんぼがえりで交代
    assert battle.actives[1].name == "ポッポ"  # ききかいひの緊急交代
    assert battle.player_states[player0].interrupt == Interrupt.NONE
    assert battle.player_states[player1].interrupt == Interrupt.NONE


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


def test_さいはい_割り込みで相手を瀕死にし勝敗が確定した場合対象自身の本来の行動は実行されない():
    """seed=0 (LogInconsistency@turn_controller.py:_run_move_phase:351) の回帰テスト。

    TurnController._run_move_phase は self.action_order を無条件にループしており、
    各行動の実行前に battle.winner を確認していなかった。さいはいの効果
    （handlers/move_status.py の さいはい_instruct）は対象の技を
    battle.run_move() でネストして即時再実行するため、その中で相手（さいはいの
    使用者）を瀕死にして勝敗が確定することがある。この場合、action_order には
    さいはいで指示された側（このケースのカビゴン）が今ターン本来予約していた
    別の行動（なきごえ）がまだ残っており、修正前はこれがそのまま実行されて
    しまっていた（元のバグでは「さいはい→かふんだんご再使用→デオキシス瀕死→
    勝敗確定」の直後に、ザシアン自身の本来の行動「りんしょう」が実行されていた）。

    修正後は self.battle.run_move(attacker, move) の直後に battle.winner を
    確認し、決着済みならそこでループを打ち切るため、カビゴンが本来予約していた
    なきごえ（MOVE_1）は一度も実行されないことを確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("サンダース", move_names=["さいはい"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり", "なきごえ"])],
        accuracy=100,
    )
    attacker, defender = battle.actives
    player0, player1 = battle.players
    t.fix_damage(battle, 1)

    # Turn1: カビゴンがたいあたりを使い、pp_consumed_moveをたいあたりにしておく。
    # サンダースのさいはいは、まだ相手が技を使っていないため失敗する。
    battle.step(commands={player0: Command.MOVE_0, player1: Command.MOVE_0})
    assert defender.pp_consumed_move.name == "たいあたり"
    growl_pp_before = defender.moves[1].pp

    # たいあたりの再実行で確実に瀕死になるようサンダースのHPを削っておく
    attacker.hp = 1

    # Turn2: サンダースが先制してさいはいを使い、カビゴンにたいあたりを
    # 再実行させる。これでサンダースが瀕死になり勝敗が確定する。カビゴンが
    # 本来このターンに予約していたなきごえ（MOVE_1）は実行されないはず。
    battle.step(commands={player0: Command.MOVE_0, player1: Command.MOVE_1})

    assert attacker.fainted
    assert battle.winner is player1
    assert defender.moves[1].pp == growl_pp_before  # なきごえは実行されていない


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


def test_じばく_HP全消費で瀕死になっても技は相手に命中しダメージを与える():
    """seed=14 (LogInconsistency@move_executor.py:_execute_move:423) の関連回帰テスト。

    ON_PAY_HP発火を勝敗ログ抑制区間で囲む修正が、じばく・だいばくはつ・
    ミストバースト等の他のHPコスト技の基本動作（HP全消費で瀕死になった上で、
    技自体は通常どおり相手に命中しダメージを与える）を壊していないことを確認する。
    """
    battle = t.start_battle(
        team0=[
            Pokemon("カビゴン", move_names=["じばく"]),
            Pokemon("コラッタ"),
        ],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    defender_hp_before = defender.hp
    t.fix_damage(battle, 30)

    t.run_move(battle, 0)

    assert attacker.fainted  # HP全消費で瀕死
    assert defender.hp == defender_hp_before - 30  # 技のダメージは通常どおり相手に届く


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


def test_ターン終了処理_ON_TURN_END発火中に決着した場合別個体の継続ダメージ処理が打ち切られる():
    """seed=42 (LogInconsistency@event_manager.py:emit:154) の回帰テスト。

    test_ターン終了処理_決着ターンでは継続ダメージのON_TURN_ENDが処理されない
    （seed=24）は、ターン中の技実行など Event.ON_TURN_END を発火する「前」に
    既に決着しているケース（_run_end_phase 側のフェーズ開始時ガード）の
    回帰テストだった。

    今回のバグはそれとは異なり、Event.ON_TURN_END の発火「中」に決着するケース。
    EventManager.emit は1回の呼び出しの中で、どく・やけど等の異なる個体を対象と
    する複数のハンドラを素早さ順（速い個体が先）にまとめて処理する。修正前は、
    先に処理された個体（速い側）の継続ダメージで瀕死になり battle.judge_winner()
    により決着が確定しても、同じ emit() 呼び出し内の後続ハンドラ（遅い側の
    継続ダメージ）がチェックされずそのまま実行され、決着後にもかかわらず
    無関係な個体へのダメージ・HP変化ログが記録されてしまっていた。

    速いピカチュウ・遅いカビゴンの両者をどく状態にし、技のダメージを0に固定して
    ターン終了時の毒ダメージのみで決着させる。ピカチュウは素早さが速いため
    ON_TURN_ENDの毒ダメージ処理が先に実行されて瀕死になり決着するが、修正前は
    その直後に処理されるカビゴン側の毒ダメージも実行されてしまっていた。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        ailment0=("どく", None),
        ailment1=("どく", None),
        accuracy=100,
    )
    player0, player1 = battle.players
    attacker, defender = battle.actives
    attacker.hp = 1
    t.fix_damage(battle, 0)  # 技のダメージを0に固定し、毒ダメージのみで決着させる

    # Turn1: 技は互いに0ダメージ。ターン終了時、速いピカチュウの毒ダメージが
    # 先に処理されて瀕死になり決着する。修正前は続けて遅いカビゴンの毒ダメージも
    # 処理されてしまっていた。
    battle.step(commands={player0: Command.MOVE_0, player1: Command.MOVE_0})

    assert attacker.fainted
    assert battle.winner is player1
    # カビゴンのHPは変化しない（技は0ダメージ、決着後の毒ダメージも処理されない）
    assert defender.hp == defender.max_hp

    logs = [log for log in battle.event_logger.logs if log.turn == battle.turn]
    defender_hp_changed_logs = [
        log for log in logs
        if log.log == LogCode.HP_CHANGED and log.pokemon == defender.name
    ]
    assert len(defender_hp_changed_logs) == 0  # カビゴン側のHP変化ログは一切記録されない


def test_ターン終了処理_同ターンに瀕死になったポケモンへのON_TURN_END回復が適用されない():
    """seed=38 (LogInconsistency@handlers/volatile.py:ねをはる_self_heal:970) の回帰テスト。

    Event.ON_TURN_END は瀕死ポケモンの交代処理（run_faint_switch）より前に発火するため、
    同ターンの攻撃で先にHPが0になったポケモンが、まだ場に残ったまま ON_TURN_END の
    自己回復系ハンドラ（ねをはる等）を受けてしまい、瀕死のまま蘇生されて戦闘を継続して
    しまうバグがあった（元のバグではザシアンがねをはるのターン終了時回復で毎ターン
    蘇生され続け、退場せずに戦闘を継続していた）。

    ねをはる状態のポケモンが、そのターンの相手の攻撃で瀕死になった場合、ON_TURN_END の
    ねをはる回復では蘇生されず、正しく瀕死のまま退場・交代することを確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんこうせっか"]), Pokemon("コラッタ")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        volatile0={"ねをはる": 1},
        accuracy=100,
    )
    player0, player1 = battle.players
    mon = battle.actives[0]
    mon.hp = 1
    t.fix_damage(battle, 1)

    battle.step(commands={player0: Command.MOVE_0, player1: Command.MOVE_0})

    # ねをはる状態のポケモンは、同ターンの攻撃で瀕死になった後、
    # ON_TURN_END のねをはる回復で蘇生されず、正しく退場・交代している
    assert mon.fainted
    assert mon.hp == 0
    assert battle.actives[0] is not mon
    assert battle.actives[0].name == "コラッタ"


def test_ターン終了処理_決着ターンでは継続ダメージのON_TURN_ENDが処理されない():
    """seed=24 (LogInconsistency@turn_controller.py:_run_end_phase:422) の回帰テスト。

    TurnController._run_end_phase は、ターン中の技実行等で既に勝敗が確定している
    場合でも Event.ON_TURN_END（どく等のターン終了時の継続ダメージ処理）を
    無条件に発火していた。そのため、そのターンの技実行で勝敗が確定した後に、
    決着に関与しない側のポケモンが毒状態であれば、決着後にもかかわらず
    毒ダメージが処理されHP変化・ログが記録されてしまっていた
    （元のバグでは「勝利/敗北」ログの前に、既に決着した側の毒ダメージログが
    紛れ込んでいた）。

    1匹選出同士で、相手（team1）の技によって自分（team0）の最後の1匹が
    瀕死になり決着するターンに、相手側が毒状態であってもそのターンの
    毒ダメージログ・HP変化が発生しないことを確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("コラッタ", move_names=["たいあたり"])],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        ailment1=("どく", None),
        accuracy=100,
    )
    player0, player1 = battle.players
    attacker, defender = battle.actives
    attacker.hp = 1
    t.fix_damage(battle, 1)

    # Turn1: たいあたりの打ち合いで、たいあたり1発で瀕死になるコラッタが
    # 先に決着する。カビゴンは毒状態だが、決着後の毒ダメージは処理されないはず。
    battle.step(commands={player0: Command.MOVE_0, player1: Command.MOVE_0})

    assert attacker.fainted
    assert battle.winner is player1
    # カビゴンのHP変化はたいあたりの1ダメージのみで、毒ダメージ分は含まれない
    assert defender.hp == defender.max_hp - 1

    logs = [log for log in battle.event_logger.logs if log.turn == battle.turn]
    hp_changed_logs = [
        log for log in logs
        if log.log == LogCode.HP_CHANGED and log.pokemon == defender.name
    ]
    assert len(hp_changed_logs) == 1  # たいあたりの反撃分のみ（毒ダメージ分の追加ログが無い）


def test_だっしゅつパック_瀕死交代の遅延ON_SWITCH_IN中に発生した割り込みが同一ターン内で解決される():
    """seed=23090 player=random (InvalidCommandError@battle.py:step:887) の回帰テスト。

    SwitchManager.run_faint_switch() は run_interrupt_switch(Interrupt.FAINTED, False)
    で瀕死交代を処理する。process_event_on_each_switch=False のこの経路は、
    通常の交代経路（_process_events_after_switch）と異なり、ON_SWITCH_INの発火を
    交代したプレイヤー全員分まとめて遅延させる。修正前はこの遅延発火の直後に
    新たに Interrupt.EJECTPACK_REQUESTED が発生しても誰にも解決されず残留していた。

    瀕死交代で場に出ただっしゅつパック持ちが、入場時効果（ねばねばネットによる
    すばやさ低下）でだっしゅつパックの発動条件を満たすと、この経路で
    EJECTPACK_REQUESTEDが立つ。修正前はこれが解決されずに残留し、
    battle.is_new_turn()（=not has_interrupt()）がFalseのままになり、
    次のbattle.step()がcommands=Noneで呼ばれてInvalidCommandErrorになっていた。

    修正後は run_interrupt_switch の process_event_on_each_switch=False 分岐でも
    _resolve_ejectpack_after_switch()（通常経路と共通化した解決処理）が呼ばれるため、
    だっしゅつパックの強制交代が同一ターン内で解決され、次ターンへ正常に
    進行することを確認する。
    """
    battle = t.start_battle(
        team0=[
            Pokemon("ピカチュウ", move_names=["たいあたり"]),
            Pokemon("コラッタ", item_name="だっしゅつパック"),
            Pokemon("ポッポ"),
        ],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        side0={"ねばねばネット": 1},
        accuracy=100,
    )
    player0, player1 = battle.players
    attacker0 = battle.actives[0]
    attacker0.hp = 1  # 相手の一撃で確実に瀕死になるようにしておく
    t.fix_damage(battle, 1)

    # Turn1: ピカチュウが瀕死になり、コラッタ(だっしゅつパック)が瀕死交代で場に出る。
    # ねばねばネットの入場時すばやさ低下でだっしゅつパックの発動条件を満たし、
    # ポッポへの強制交代が発生する。修正前はこのEJECTPACK_REQUESTEDが
    # 解決されずに残留していた。
    battle.step(commands={player0: Command.MOVE_0, player1: Command.MOVE_0})

    assert battle.actives[0].name == "ポッポ"  # だっしゅつパックで自動的に交代済み
    assert battle.player_states[player0].interrupt == Interrupt.NONE

    # 修正前はここでInvalidCommandErrorになっていた
    # （is_new_turn()がFalseのままcommands=Noneでstep()が呼ばれるため）。
    battle.step()
    assert battle.turn == 2


def test_だっしゅつパック_自分の番より後の割り込み交代で残った予約コマンドが次ターンに持ち越されない():
    """seed=1755 player=random (IndexError@command_manager.py:resolve_move_from_command:149) の回帰テスト。

    TurnController._run_switch_phase は resolve_speed_order() の速度順でプレイヤーを
    1人ずつ処理する。修正前は「自分の番がループで回ってくる前に既に交代済みだった
    場合」だけ、使われなかった予約コマンド（MOVE_x等）をその場（自分の番の
    イテレーション時点）で破棄していた。

    しかし、自分の番の処理が既に終わった後に、後から処理される別プレイヤーの交代
    （その switch-in 効果によるランクダウン）に付随してだっしゅつパックの割り込み
    交代が発生するケースでは、対象プレイヤーの予約コマンドは一度も pop されない
    まま reserved_commands に残り続けていた。resolve_action_order() は
    has_switched なプレイヤーを action_order から除外するため、_run_move_phase 側の
    同種の破棄ロジックにも到達せず、残留コマンドは次ターン以降までそのまま
    持ち越されてしまう。

    修正後はループ全体が終わった後の後処理として、has_switched かつコマンドが
    残っている全プレイヤーの予約コマンドをまとめて破棄するため、割り込み交代が
    ループの前半・後半どちらのタイミングで起きても残留コマンドは残らない。

    速いピカチュウ（だっしゅつパック持ち）が通常の技コマンド（MOVE_1）を予約し、
    自分の番の処理が終わった後に、遅いカビゴン側がいかく持ちのコラッタに交代して
    ピカチュウのこうげきを下げ、だっしゅつパックの割り込み交代を誘発する。
    交代後のビードルは技を1つ（index=0）しか持たないため、残留したMOVE_1
    （index=1）が破棄されていないと、次ターンの技実行でIndexErrorが発生する。
    """
    battle = t.start_battle(
        team0=[
            Pokemon(
                "ピカチュウ", item_name="だっしゅつパック",
                move_names=["でんきショック", "でんこうせっか"],
            ),
            Pokemon("ビードル", move_names=["たいあたり"]),
        ],
        team1=[
            Pokemon("カビゴン", move_names=["たいあたり"]),
            Pokemon("コラッタ", ability_name="いかく", move_names=["たいあたり"]),
        ],
    )
    player0, player1 = battle.players

    # Turn1: ピカチュウ（速い）はMOVE_1（でんこうせっか）を予約するが、
    # 自分の番の処理では交代コマンドではないため何も起きずそのまま残る。
    # その後、遅いカビゴン側がいかく持ちのコラッタに交代し、ピカチュウの
    # こうげきが下がってだっしゅつパックの割り込み交代が発生する。この時点で
    # ピカチュウの予約コマンド（MOVE_1）は一度も使われずに残る。
    battle.step(commands={player0: Command.MOVE_1, player1: Command.SWITCH_1})

    assert battle.actives[0].name == "ビードル"  # だっしゅつパックで自動的に交代済み
    assert battle.actives[1].name == "コラッタ"

    # Turn2: 交代後のビードルは技を1つ（index=0）しか持たない。
    # 修正前は残留したMOVE_1（index=1）が誤って使われ、
    # command_manager.resolve_move_from_commandでIndexErrorが発生していた。
    battle.step()

    assert battle.turn == 2  # 例外なく2ターン目が完了したことを確認
    assert battle.actives[0].pp_consumed_move.name == "たいあたり"  # 新しいコマンドが正しく使われた


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


def test_てっていこうせん_HP支払いで相打ちになった場合でも撃破時特性ログが勝敗確定ログより先に記録される():
    """seed=14 (LogInconsistency@move_executor.py:_execute_move:423) の回帰テスト。

    core/move_executor.py の _execute_move は、Event.ON_PAY_HP（てっていこうせん・じばく・
    だいばくはつ・ミストバースト等、HPコストを支払う技の共通フロー）の発火を
    begin_deferred_winner_log() / end_deferred_winner_log() の抑制区間の外で行っていた。
    そのため、HPコスト支払いにより使用者が瀕死になり勝敗が確定すると、その直後に
    相手へのダメージ適用や撃破時特性（じんばいったい等）の発動より先に
    GAME_WON/GAME_LOSTログが記録されてしまっていた（docs/spec/moves/てっていこうせん.md
    「HP消費の順序」「HP0でのひんし・全滅判定」が定める、HP0になった状態でも
    そのまま命中判定・ダメージ計算が実行され相手に攻撃が届くという仕様自体は、
    勝者判定（battle.winner の確定）が modify_hp 内で即座に行われるため壊れていない。
    問題はログの記録タイミングのみ）。

    修正後は Event.ON_PAY_HP の発火から連続ヒット処理・Event.ON_MOVE_ENDまでを
    begin_deferred_winner_log() / end_deferred_winner_log() で囲むため、HPコスト
    支払いによる使用者の瀕死とダメージによる相手の瀕死が同時に起きる相打ちでも、
    相手への与ダメージログ・撃破時特性（じんばいったい）の能力変化ログ・特性発動ログの
    方がGAME_WON/GAME_LOSTログより先に記録されることを確認する。使用者側は先に
    倒れているため、この技による相打ちでは使用者側の負けとなる
    （docs/spec/moves/てっていこうせん.md「HP0でのひんし・全滅判定」）。
    """
    battle = t.start_battle(
        team0=[Pokemon("バンギラス", ability_name="じんばいったい", move_names=["てっていこうせん"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    player0, player1 = battle.players
    # HPコスト（最大HPの1/2切り上げ）でちょうど瀕死になるようHPを調整する
    cost = max(1, (attacker.max_hp + 1) // 2)
    attacker.hp = cost
    defender.hp = 1
    t.fix_damage(battle, 1)

    t.run_move(battle, 0)

    assert attacker.fainted  # HPコスト支払いで瀕死
    assert defender.fainted  # てっていこうせんのダメージで瀕死（相打ち）
    assert battle.winner is player1  # 使用者側が先に倒れるため使用者側の負け

    logs = battle.event_logger.logs
    stat_idx = next(i for i, log in enumerate(logs) if log.log == LogCode.STAT_CHANGED)
    ability_idx = next(i for i, log in enumerate(logs) if log.log == LogCode.ABILITY_TRIGGERED)
    won_idx = next(i for i, log in enumerate(logs) if log.log == LogCode.GAME_WON)
    lost_idx = next(i for i, log in enumerate(logs) if log.log == LogCode.GAME_LOST)
    # 修正前はwon_idx/lost_idxがstat_idx/ability_idxより先になっていた
    assert stat_idx < won_idx
    assert ability_idx < won_idx
    assert won_idx < lost_idx


def test_でんじは_タイプ免疫で失敗した場合も無効化ログが記録される():
    """seed=242 (LogInconsistency@ailment_manager.py:apply:100-111) の回帰テスト。

    AilmentManager.apply() は _can_apply_by_type がタイプ免疫（でんき等）により
    False を返した場合、ログを一切記録せず return False するだけだった。まひ限定の
    バグではなく、どく/もうどく・やけど・こおり等 _can_apply_by_type で判定する
    全状態異常付与に共通する欠陥だったため、AilmentManager.apply() 自体に
    LogCode.AILMENT_PREVENTED（display_reason="タイプ無効"）のログ記録を追加した。
    でんじは（でんきタイプへのまひ付与）で無効化ログが記録され、その後に
    「技は失敗した」ログが続くことを確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],  # でんきタイプ
        team1=[Pokemon("コラッタ", move_names=["でんじは"])],
        accuracy=100,
    )
    attacker = battle.actives[0]

    t.run_move(battle, 1)

    assert attacker.ailment.is_active is False  # まひは付与されない

    logs = battle.event_logger.logs
    prevented_idx = next(
        i for i, log in enumerate(logs)
        if log.log == LogCode.AILMENT_PREVENTED and log.pokemon == attacker.name
    )
    assert logs[prevented_idx].payload.display_reason == "タイプ無効"
    failed_idx = next(i for i, log in enumerate(logs) if log.log == LogCode.MOVE_FAILED)
    assert prevented_idx < failed_idx  # 無効化ログの方が失敗ログより先に記録される


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


def test_とんぼがえり_相手を瀕死にして勝敗が確定した場合使用者自身の交代処理も実行されない():
    """seed=0 (LogInconsistency@turn_controller.py:_run_move_phase:351) の関連回帰テスト。

    さいはい等の割り込みを介さない、通常の技実行だけで勝敗が確定するケースの
    回帰テスト。TurnController._run_move_phase は self.battle.run_move(attacker,
    move) の実行直後にも battle.winner を確認していなかったため、とんぼがえりで
    相手の最後の1匹を瀕死にして勝敗が確定した場合でも、使用者自身の交代処理
    （Interrupt.PIVOT による self._switch.run_interrupt_switch）がそのまま
    実行されてしまっていた（勝敗が決した後に使用者が控えへ交代するという、
    ログ上不整合な状態が発生する）。

    修正後は run_move 実行直後に battle.winner を確認してループを打ち切るため、
    ピカチュウはライチュウに交代せず場に残り続け、瀕死になったコイキングが
    本来予約していたたいあたりも実行されない（ピカチュウのHPが変化しない）
    ことを確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["とんぼがえり"]), Pokemon("ライチュウ")],
        team1=[Pokemon("コイキング", move_names=["たいあたり"])],
        accuracy=100,
    )
    player0 = battle.players[0]
    defender = battle.actives[1]
    defender.hp = 1
    hp_before = battle.actives[0].hp

    battle.step()  # 修正前はここでピカチュウがライチュウへ交代してしまっていた

    assert defender.fainted
    assert battle.winner is player0
    assert battle.actives[0].name == "ピカチュウ"  # 交代処理が実行されず場に残る
    assert battle.actives[0].hp == hp_before  # コイキングのたいあたりは実行されない
    # 交代処理自体は実行されなかったため、PIVOTフラグは立ったまま残る
    assert battle.player_states[player0].interrupt == Interrupt.PIVOT


def test_にげごし_瀕死交代後のまきびしダメージで発生した緊急交代割り込みが同一ターン内で解決される():
    """seed=18407 player=random (InvalidCommandError@battle.py:step:887) の回帰テスト。

    TurnController._run_end_phase は
    run_interrupt_switch(EMERGENCY) → run_interrupt_switch(EJECTPACK_ON_TURN_END) →
    run_faint_switch() の順に実行する。修正前のSwitchManager.run_faint_switch()は
    Interrupt.FAINTEDのみを対象にしていたが、瀕死交代の内部で行われる
    ON_SWITCH_INの遅延発火（process_event_on_each_switch=False）の中でまきびし等の
    入場時ダメージがにげごし・ききかいひのHP50%閾値を新たに跨いでInterrupt.EMERGENCYを
    立てても、既にrun_interrupt_switch(EMERGENCY)の呼び出しは終わっているため誰にも
    解決されずに残留していた。これによりBattle.is_new_turn()（=not has_interrupt()）が
    Falseのままになり、次のbattle.step()がcommands=Noneで呼ばれてInvalidCommandErrorに
    なっていた。

    修正後はrun_faint_switch()がFAINTED・EMERGENCYの両方の割り込みがなくなるまで
    再帰するため、瀕死交代の連鎖で発生した緊急交代も同一ターン内で解決され、
    次ターンへ正常に進行することを確認する。
    """
    battle = t.start_battle(
        team0=[
            Pokemon("ピカチュウ", move_names=["たいあたり"]),
            Pokemon("コラッタ", ability_name="にげごし"),
            Pokemon("ポッポ"),
        ],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
        side0={"まきびし": 1},
        accuracy=100,
    )
    player0, player1 = battle.players
    attacker0 = battle.actives[0]
    attacker0.hp = 1  # 相手の一撃で確実に瀕死になるようにしておく
    t.fix_damage(battle, 1)

    # 瀕死交代で場に出るコラッタ(にげごし)のHPを、まきびし1層のダメージ(1/8)を
    # 受けた直後にちょうど半分以下へ遷移するよう調整する。
    switch_in_mon = battle.player_states[player0].team[1]
    spike_damage = switch_in_mon.max_hp // 8
    switch_in_mon.hp = switch_in_mon.max_hp // 2 + spike_damage

    # Turn1: ピカチュウが瀕死になり、コラッタが瀕死交代で場に出る。
    # まきびしダメージでにげごしのHP50%閾値を跨ぎ、ポッポへ緊急交代する。
    # 修正前はこの緊急交代のInterrupt.EMERGENCYが解決されずに残留していた。
    battle.step(commands={player0: Command.MOVE_0, player1: Command.MOVE_0})

    assert battle.actives[0].name == "ポッポ"
    assert battle.player_states[player0].interrupt == Interrupt.NONE

    # 修正前はここでInvalidCommandErrorになっていた
    # （is_new_turn()がFalseのままcommands=Noneでstep()が呼ばれるため）。
    battle.step()
    assert battle.turn == 2


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


def test_木探索_探索中に相手自身の割り込み交代が起きても観測マスクで交代先が消えずIndexErrorにならない():
    """tsfuzz seed=4698 (IndexError@tree_search_player.py:choose_command:118) の回帰テスト。

    TreeSearchPlayer が自分自身の割り込み交代（ききかいひ等のEMERGENCY）を解決する際、
    `_worst_case_over_opponent` は `battle.build_observation(自分)` の子孫である
    観測用コピー上で `sim.step()` を実行して探索する。この sim.step() の中で
    相手側のとんぼがえり（PIVOT）が再現され、相手自身の choose_command() が
    再帰的に呼ばれる。

    しかし observation_builder._mask() は「観測者から見て未公開の控え」を
    `state.selected_indexes` から除外する処理を、観測対象（＝相手）の
    PlayerState に対して直接・不可逆に適用する。この sim は探索側（自分）を
    観測者として構築された盤面の子孫であるため、相手の未公開の控えは
    `selected_indexes` からすでに除外されており、その後 sim 内で相手自身が
    観測者として再マスクされても（＝相手自身の観点では本来ハンドラを持つ
    はずの控えでも）一度失われた `selected_indexes` は復元されない。

    この結果、相手自身の PIVOT 割り込み解決時に `battle.get_available_commands
    (相手)` が空になり、相手の TreeSearchPlayer.fallback() が
    `battle.decision_random.choice([])` で IndexError になっていた
    （実際に控えのポケモンが存在しないわけではなく、観測マスクの副作用による
    見かけ上の欠落）。

    修正前を決定的に再現するため、以下のように盤面を組む。
    - Searcher側の場のポケモンはききかいひ持ちにし、ぴったり半分を跨ぐ
      固定ダメージ（roll_damage）でちょうどEMERGENCY交代を誘発させる。
    - Opponent側はとんぼがえりだけを公開済みにし、ベンチのポケモンは
      非公開のままにしておく（fuzzで実際に踏んだ状況の再現）。
    - Opponent側の行動選択はとんぼがえり固定のForcedActionPlayerとする
      （割り込み交代の再入時は基底クラスの探索・フォールバックに委ねる）。
    Searcher（ききかいひ）の割り込み交代解決の探索中に、Opponent自身の
    とんぼがえりのPIVOT割り込みが再帰的に発生し、修正前はOpponent自身の
    交代先が観測マスクで消えてIndexErrorになっていた。
    """
    class ForcedActionPlayer(TreeSearchPlayer):
        """トップレベルの行動選択（action phase）だけ固定技を強制し、探索中の
        割り込み交代（switch phase の再入）は基底クラスに委ねる。"""

        def __init__(self, username: str, forced_move_name: str):
            super().__init__(username=username)
            self.forced_move_name = forced_move_name

        def choose_command(self, battle: Battle) -> Command:
            if not self._searching and battle.phase == "action":
                active = battle.player_states[self].active
                for i, move in enumerate(active.moves):
                    if move.name == self.forced_move_name:
                        return Command.get_move_command(i)
            return super().choose_command(battle)

    searcher = TreeSearchPlayer(username="Searcher")
    searcher.team = [
        Pokemon("グソクムシャ", ability_name="ききかいひ", move_names=["たいあたり"]),
        Pokemon("ヒトカゲ", move_names=["たいあたり"]),
    ]

    opponent = ForcedActionPlayer(username="Opponent", forced_move_name="とんぼがえり")
    opponent.team = [
        Pokemon("ゼニガメ", move_names=["とんぼがえり"]),
        Pokemon("カメックス", move_names=["たいあたり"]),
    ]
    opponent.team[0].moves[0].revealed = True  # とんぼがえりだけ公開。カメックスは非公開のまま

    battle = Battle(searcher, opponent, n_selected=2, seed=1)
    battle.test_option.accuracy = 100
    battle.start()
    battle.actives[0].hp = 100  # グソクムシャの最大HP150の半分(75)超
    battle.roll_damage = lambda attacker, defender, move, critical=False: 50  # 半分を跨ぐ固定ダメージ

    battle.step()  # 修正前はここでIndexErrorになっていた

    assert searcher._searching is False
    assert opponent._searching is False


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


def test_観測マスク_未公開特性を持つ場のポケモンが観測用コピー内で交代してもハンドラが残留せずValueErrorが発生しない():
    """seed=9134 player=tree_search (ValueError@battle.py:foe:556) の回帰テスト。

    TreeSearchPlayerは`battle.build_observation(player)`で作った観測用（未公開
    情報マスク済み）バトルコピーに対してシミュレーションを進める。
    core/observation_builder.py の _mask_ability / _mask_item は、未公開の
    特性・アイテムを持つポケモンに対して mon.ability = Ability() /
    mon.item = Item() と新しい空インスタンスに直接差し替えていたが、対象
    ポケモンが場に出ている場合、元の特性・アイテムのハンドラは既にEventManagerに
    登録済みである。差し替えはEventManager側の登録を更新しないため、後で
    SwitchManager._switch_out() が mon.ability.unregister_handlers(...) を
    呼んでも差し替え後の（ハンドラを持たない）空インスタンスに対して解除を
    試みるだけで、実際に登録されていた元の特性のハンドラは解除されずに残留する。

    残留した「ものひろい」のON_TURN_ENDハンドラ（subject_spec="source:self"）は、
    観測用コピー内で対象ポケモンが交代した後もsubject一致チェックを素通りして
    発火し続け、ハンドラ内の battle.foe(mon) が場にいないポケモンに対して
    呼び出されてValueErrorになっていた。

    修正後は、対象ポケモンが場に出ている場合のみ差し替え前に旧インスタンスの
    unregister_handlers()を呼び、差し替え後の空インスタンスでregister_handlers()を
    呼び直すため、観測用コピー内で交代してもハンドラが残留せず、
    交代後のON_TURN_ENDで例外なく完了することを確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[
            Pokemon("マルヤクデ", ability_name="ものひろい"),
            Pokemon("フシギダネ"),
        ],
    )
    observer, _ = battle.players
    opponent_active = battle.actives[1]
    assert not opponent_active.ability.revealed  # 前提: 未公開のため隠蔽対象になる

    obs = battle.build_observation(observer)
    obs_opponent = obs.opponent(observer)
    obs_active = obs.player_states[obs_opponent].active
    assert obs_active.ability.name == ""  # マスクされている（前提）

    # 観測用コピー内で交代させる。旧「ものひろい」ハンドラが残留していると、
    # ここでは例外は出ず、後続のターン終了時イベントで初めて表面化する。
    t.run_switch(obs, 1, 1)

    t.end_turn(obs)  # 修正前はここでValueErrorになっていた
