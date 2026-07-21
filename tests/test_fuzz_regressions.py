"""fuzzテストで発見されたバグの回帰テスト。

再現性のあるランダムシードをそのまま固定するのではなく、原因箇所を特定した上で
core/エンジン共通ロジックの最小ケースとして再現する。
"""
from jpoke import Battle, Player
from jpoke.model import Pokemon
from jpoke.enums import Command, Interrupt, LogCode
from jpoke.handlers.move import get_forced_switch_commands
from jpoke.players import MinimaxPlayer

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


def test_late_field_activation_ON_TURN_ENDでカウントダウンされないフィールドは補填されない():
    """`late_field_activation` によるカウントダウン補填は、強天候（おおひでり等）や
    まきびし等の設置技のように、そもそも `Event.ON_TURN_END` でカウントダウン
    されないフィールドには適用されないことの回帰テスト
    （`FieldManager._has_turn_end_tick` 参照）。

    まきびしは重ね掛けで層数（count）が増えるだけで、ターン経過による
    カウントダウンの対象ではない。誤って補填ロジックが適用されると、
    設置直後に層数が減ってしまう（活性化前は非アクティブなのでcount=0のまま
    減算されず実害はないが、意図せぬ副作用が起きないことを明示的に確認する）。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    player0, _ = battle.players
    side = battle.get_side(player0)

    with battle.late_field_activation_context():
        assert side.activate("まきびし", 1) is True

    assert side.get("まきびし").count == 1


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


def test_いちゃもん_タイプ無効で不発した直後でもその技を正しくロックする():
    """seed=916 (LogInconsistency@move_executor.py:run_move:482) の回帰テスト。

    MoveExecutor.run_move()内でのctx.attacker.selected_moveの更新は、修正前は
    タイプ相性判定・ON_TRY_MOVE_2・くさタイプ粉技無効判定などの「技が不発になる判定」を
    すべて通過した後（発動した技の確定ブロック）でしか行われていなかった。そのため、
    PPは消費されたがタイプ無効等で技自体が不発になった場合、selected_moveが更新されず、
    それより前に成功していた古い技のままになっていた。この結果、いちゃもん（相手の直前の
    選択技をロックする効果）が、実際に使われた技ではなく古い成功技を誤ってロックし続ける
    不整合が発生していた。

    修正後はPP消費直後（不発判定より前）にselected_moveを確定するため、タイプ無効で
    不発した直後にいちゃもんを使われても、実際に使われた（不発した）技が正しく
    ロックされることを確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック", "たいあたり"])],
        team1=[Pokemon("ゲンガー", move_names=["いちゃもん"])],  # ゴーストタイプはノーマル技を無効化する
        accuracy=100,
    )
    # このテストの主眼はいちゃもんによるselected_moveのロックであり、でんきショックの
    # 追加効果（10%でまひ）・まひによる行動失敗（12.5%）は無関係な副作用。
    # 乱数を発動しきい値より確実に大きい値に固定し、両方とも「発動しない」側に倒す
    # （apply_ailment_to_defenderは`random() >= chance`で不発、まひ_actionは
    # `random() < 0.125`で発動なので、どちらも0.99なら意図通りになる）。
    t.fix_random(battle, 0.99)
    attacker, defender = battle.actives

    # 1手目: でんきショック（電気技）が成功する（selected_move = でんきショック）
    t.run_move(battle, 0, 0)
    assert battle.move_executor.move_success
    assert attacker.selected_move.name == "でんきショック"

    # 2手目: たいあたり（ノーマル技）はゴーストタイプのゲンガーに無効化されて不発になるが、
    # PPは既に消費されているため selected_move は「たいあたり」に更新されるべき
    t.run_move(battle, 0, 1)
    assert battle.move_executor.move_success is False
    assert attacker.selected_move.name == "たいあたり"

    # defender（ゲンガー）がいちゃもんを使用 → 直前に選択した「たいあたり」がロックされる
    # （修正前は古い「でんきショック」が誤ってロックされていた）
    t.run_move(battle, 1, 0)
    assert attacker.has_volatile("いちゃもん")
    assert attacker.volatiles["いちゃもん"].move_name == "たいあたり"


def test_いやしのねがい_ステルスロックより後に設置してもHP回復がダメージより先に適用される():
    """seed=1879 (LogInconsistency) の回帰テスト。

    いやしのねがい・みかづきのまいのEvent.ON_SWITCH_INハンドラは、修正前は
    まきびし・ステルスロック等の設置技（デフォルトpriority=100）と同じ
    priority=100で登録されていた。EventManager._sort_handlersは同一priority
    同士のタイブレークをハンドラ登録順で行うため、ステルスロックが先に、
    いやしのねがいが後から設置された場合、登録順の関係でステルスロックの
    ダメージがいやしのねがいの回復より先に適用されてしまっていた。回復は
    常にHPを満タンにするため、この順序バグは最終的なHPが満タンのままに
    なってしまう（本来はステルスロックのダメージ分だけ減っているべき）
    という形で現れていた（.internal/spec/fields/いやしのねがい.md「設置技との
    順序」参照）。

    修正後はpriority=90を明示し、設置技より必ず先に発動するようにしたため、
    HPが一度満タンまで回復してからステルスロックのダメージが引かれ、
    最終的なHPが「満タン - ステルスロックのダメージ」になることを確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン")],
        # ステルスロックを先に、いやしのねがいを後から設置する
        # （設置順＝ハンドラ登録順のタイブレークを再現するため）
        side0={"ステルスロック": 1, "いやしのねがい": 1},
    )
    bench = battle.player_states[battle.players[0]].team[1]
    bench.hp = 1

    active = t.run_switch(battle, 0, 1)

    assert active is bench
    hazard_damage = active.max_hp // 8
    # 修正前は回復がダメージより後に適用され、最終的なHPが満タンのままだった
    assert active.hp == active.max_hp - hazard_damage
    assert not battle.get_side(active).get("いやしのねがい").is_active


def test_おだてる_自分自身のHPコストで同一ターン内にすでに瀕死になった相手には技が不発になる():
    """seed=572 (LogInconsistency@move_executor.py) の回帰テスト。

    瀕死交代は turn_controller._run_end_phase の最後にしか行われないため、
    同一ターン内で相手が自分自身のHPコスト（いのちのたまの反動等）によって
    すでに瀕死になっている場合、瀕死交代前の場に残ったままの瀕死ポケモンが
    別の技の対象になり得る。修正前はこの場合でもおだてるが瀕死のポケモンに
    とくこうランク上昇・こんらん付与を適用してしまっていた。

    修正後は core/move_executor.py の _check_target_fainted
    （Event.ON_TRY_MOVE_1, priority=90「対象が全員ひんし」相当のコアルール）
    により、相手単体対象技（ctx.move.target == "foe"）は対象がすでに瀕死なら
    不発になる（display_reason="相手がいない"）ことを確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["おだてる"])],
        team1=[Pokemon("フシギダネ", item_name="いのちのたま", move_names=["たいあたり"])],
        accuracy=100,
    )
    attacker, defender = battle.actives

    # いのちのたまの反動（最大HPの1/10、切り上げ、最低1）で確実に瀕死になるようHPを削っておく
    battle.modify_hp(defender, v=-(defender.max_hp - 1))
    assert defender.hp == 1

    t.run_move(battle, 1)  # 攻撃自体は成立するが、いのちのたまの反動で自分自身が瀕死になる
    assert defender.fainted

    logs_before = len(battle.event_logger.logs)
    t.run_move(battle, 0)  # おだてるが瀕死交代前の瀕死ポケモンを対象にする

    assert defender.boosts["spa"] == 0  # とくこうランク上昇が適用されていない
    assert not defender.has_volatile("こんらん")  # こんらんも付与されていない

    logs = battle.event_logger.logs[logs_before:]
    assert any(
        log.log == LogCode.MOVE_FAILED and log.payload.display_reason == "相手がいない"
        for log in logs
    )


def test_かなしばり_タイプ無効で不発した技はPPが消費されず対象にならない():
    """selected_move（本ファイルの いちゃもん 回帰テスト参照）と異なり、かなしばりが参照する
    pp_consumed_move は _consume_pp 内でPPが実際に消費された（v > 0）場合のみ更新される
    フィールドであり、今回のselected_move更新タイミング修正の対象外である。

    タイプ無効による不発自体はPP消費（v=1）の後に判定されるため、この回帰テストでは
    pp_consumed_moveが不発技（たいあたり）を指すこと自体は元々正しい。かなしばりが
    「タイプ無効で不発した技」を対象にできることを確認し、今回の修正がpp_consumed_move側の
    挙動に影響を与えていないことを確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["たいあたり"])],
        team1=[Pokemon("ゲンガー", move_names=["かなしばり"])],  # ゴーストタイプはノーマル技を無効化する
        accuracy=100,
    )
    attacker, defender = battle.actives

    t.run_move(battle, 0, 0)
    assert battle.move_executor.move_success is False  # タイプ無効で不発
    assert attacker.pp_consumed_move.name == "たいあたり"

    t.run_move(battle, 1, 0)
    assert attacker.has_volatile("かなしばり")
    assert attacker.volatiles["かなしばり"].move_name == "たいあたり"


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


def test_ききかいひ_通常の交代コマンドで場に出た直後の入場時ダメージによる緊急交代が同一ターン内で解決される():
    """seed=117420 player=random (IndexError@command_manager.py:resolve_move_from_command:156) の回帰テスト。

    通常の交代コマンド（TurnController._run_switch_phase）で場に出た直後、
    ステルスロックなどの入場時ダメージでききかいひが発動すると、
    SwitchManager._process_events_after_switch はON_SWITCH_INとだっしゅつパックの
    交代後リクエストのみを解決し、Interrupt.EMERGENCYを解決せずに呼び出し元へ
    処理を戻していた。Battle.is_new_turn()（=not has_interrupt()）はEMERGENCYが
    残っている間Falseのままになるため、以降の_resolve_action_order・_run_move_phase
    等の多くのフェーズが丸ごとスキップされ、まだ実行されていないもう一方の
    プレイヤーの技コマンドがpop_command()されないまま予約リストに残留してしまう。
    次ターンに新しいコマンドがFIFOの末尾に積まれるため、古いコマンドが先に使われ、
    その時点で技数が少ないポケモンに交代済みだった場合にresolve_move_from_commandで
    IndexErrorが発生していた。

    修正後は_process_events_after_switchがSwitchManager.resolve_pending_interrupts
    （だっしゅつパック・Interrupt.EMERGENCYの両方を一元的に解決する共通ヘルパー）を
    呼んでから呼び出し元へ処理を戻すため、同一ターン内でもう一方のプレイヤーの技が
    正しく実行され、次ターンも問題なく進行することを確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんきショック", "でんこうせっか"])],
        team1=[
            Pokemon("コラッタ", move_names=["たいあたり"]),
            Pokemon(
                "カビゴン", ability_name="ききかいひ",
                move_names=["まるくなる", "たいあたり"],
            ),
        ],
        side1={"ステルスロック": 1},
    )
    player0, player1 = battle.players

    # 交代先のカビゴンのHPを、ステルスロック1層のダメージ(1/8)を受けた直後に
    # ちょうど半分以下へ遷移するよう調整する。
    switch_in_mon = battle.player_states[player1].team[1]
    hazard_damage = switch_in_mon.max_hp // 8
    switch_in_mon.hp = switch_in_mon.max_hp // 2 + hazard_damage

    # Turn1: プレイヤー1が通常の交代コマンド（SWITCH_1）でカビゴンに交代する。
    # ステルスロックのダメージでカビゴンのHPが半分以下になりききかいひが発動し、
    # 唯一の生存する控え（コラッタ）へ即座に緊急交代する。
    # 修正前はこのInterrupt.EMERGENCYが解決されずに残留し、同一ターン内の
    # プレイヤー0の技（MOVE_1: でんこうせっか）が丸ごとスキップされていた。
    battle.step(commands={player0: Command.MOVE_1, player1: Command.SWITCH_1})

    assert battle.actives[1].name == "コラッタ"  # ききかいひで自動的に交代済み
    assert battle.player_states[player1].interrupt == Interrupt.NONE
    # 修正前はスキップされ実行されなかったプレイヤー0の技が、同一ターン内で
    # 正しく実行されたことを確認する。
    assert battle.actives[0].pp_consumed_move.name == "でんこうせっか"
    assert battle.turn == 1

    # Turn2: 修正前はプレイヤー0の技コマンドが予約リストに残留する余地があり、
    # 次ターンの行動順解決やコマンド解決でIndexErrorが発生し得た。
    # 修正後は残留がなく、例外なく次ターンへ進行することを確認する。
    battle.step()

    assert battle.turn == 2  # 例外なく2ターン目が完了したことを確認


def test_グローバルフィールド_ON_TURN_END通過後に発動した場合も通常設置と同じ継続ターンになる():
    """天候・地形と同じ処理順序の非対称性がグローバルフィールド
    （じゅうりょく・トリックルーム等）にも当てはまることの回帰テスト。

    現状このリポジトリのデータには、瀕死交代の入場特性・アイテムでグローバル
    フィールドを設置するものは存在しない（じゅうりょく等は全て技のみが設置する）
    ため、`TurnController._run_end_phase()` が張る
    `Battle.late_field_activation_context()` を直接使って「このターンの
    ON_TURN_END通過後に新規発動した」状況を再現する（`FieldManager` 側の
    実際の補填ロジックそのものを検証する）。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )

    with battle.late_field_activation_context():
        assert battle.activate_global_field("じゅうりょく", 5) is True

    # 修正前相当（補填なし）ならcount=5のままのところ、活性化直後に1回分を
    # 補填し、通常の技発動でじゅうりょくが発動した場合と同じcount=4になる。
    assert battle.get_global_field("じゅうりょく").count == 4

    for _ in range(3):
        t.end_turn(battle)
        assert battle.get_global_field("じゅうりょく").name == "じゅうりょく"
    assert battle.get_global_field("じゅうりょく").count == 1

    # 5ターン目（設置ターンを含め計5ターン）で終了する
    t.end_turn(battle)
    assert battle.get_global_field("じゅうりょく").name == ""


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
        commands = battle.available_commands(battle.players[0])

    # 固定技（MOVE_0）以外の技コマンドは除外され、控え5匹分の交代コマンドは全て候補に含まれる
    move_commands = [cmd for cmd in commands if cmd.is_regular_move]
    switch_commands = [cmd for cmd in commands if cmd.is_switch]
    assert move_commands == [Command.MOVE_0]
    assert switch_commands == [
        Command.SWITCH_1,
        Command.SWITCH_2,
        Command.SWITCH_3,
        Command.SWITCH_4,
        Command.SWITCH_5,
    ]


def test_こんらん_自傷ダメージが致死の場合動けないログが勝敗確定ログより先に記録される():
    """seed=532 (LogInconsistency@turn.py) の回帰テスト。

    handlers/volatile.py の こんらん_try_action は、Event.ON_TRY_ACTION が
    begin_deferred_winner_log()/end_deferred_winner_log() の抑制区間の外側で
    発火するにもかかわらず、「動けない[こんらん]」ログ（LogCode.ACTION_BLOCKED）
    を自傷ダメージの battle.modify_hp() 呼び出しより後に記録していた。
    自傷ダメージが致死だった場合、modify_hp内部でflush_winner_log()が即座に
    発火するため、勝敗確定ログ（GAME_WON/GAME_LOST）が「動けない[こんらん]」
    ログを追い越してしまっていた。

    修正後は先にACTION_BLOCKEDログを記録してから自傷ダメージを適用するため、
    ACTION_BLOCKEDログの方が勝敗確定ログより先に記録されることを確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("カビゴン")],
        volatile0={"こんらん": 2},
    )
    attacker = battle.actives[0]
    battle.test_option.trigger_volatile = True
    attacker.hp = 1
    t.fix_damage(battle, 1)

    t.run_move(battle, 0)

    assert attacker.fainted

    logs = battle.event_logger.logs
    blocked_idx = next(i for i, log in enumerate(logs) if log.log == LogCode.ACTION_BLOCKED)
    lost_idx = next(i for i, log in enumerate(logs) if log.log == LogCode.GAME_LOST)
    # 修正前は lost_idx < blocked_idx になっていた
    assert blocked_idx < lost_idx


def test_サイコメイカー_瀕死交代で発動した場合も通常設置と同じ5ターンで終了する():
    """seed=1607 (fuzz_log) の回帰テスト。

    地形も天候と同様、設置ターンを1ターン目として5ターンで終了する仕様
    （`.internal/spec/abilities/ひでり.md` と同じ考え方が地形にも適用される。
    `handlers/field.py` の `tick_terrain` 参照）。

    瀕死交代（対象ポケモンが瀕死になり、控えのポケモンが交代で入り、その入場
    特性が地形を設置する場合）は、天候と同じ理由（TurnController._run_end_phase()
    でON_TURN_ENDが交代より先に発火する）で、設置ターンのカウントダウン機会を
    逃し、本来5ターンで終了するはずの地形が6ターン継続してしまっていた。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんこうせっか"])],
        team1=[
            Pokemon("コイキング"),
            Pokemon("ピカチュウ", ability_name="サイコメイカー"),
        ],
        accuracy=100,
    )
    t.fix_damage(battle, 9999)  # コイキングを確実に瀕死にする
    player0, player1 = battle.players

    # コイキングが瀕死になり、控えのサイコメイカー持ちが瀕死交代で入場する
    # （このターンのON_TURN_END通過後に発生する交代）。
    battle.step(commands={player0: Command.MOVE_0, player1: Command.MOVE_0})

    assert battle.actives[1].ability.name == "サイコメイカー"
    assert battle.terrain.name == "サイコフィールド"
    # 修正前はこの時点でcount=5のまま。修正後は活性化直後に1回分を補填し、
    # 通常の交代・技発動でサイコフィールドが発動した場合と同じcount=4になる。
    assert battle.terrain.count == 4

    # 以降のターンでもう一方のポケモンが瀕死にならないよう、ダメージを0に
    # 固定する（fix_damageは以降の全てのダメージ計算に効くため、そのまま
    # だと次のターンで交代先も瀕死になってしまう）。
    t.fix_damage(battle, 0)

    # 残り3ターンはまだ持続する
    for _ in range(3):
        battle.step()
        assert battle.terrain.name == "サイコフィールド"
    assert battle.terrain.count == 1

    # 5ターン目（設置ターンを含め計5ターン）で終了する
    battle.step()
    assert battle.terrain.name == ""


def test_サイドフィールド_ON_TURN_END通過後に発動した場合も通常設置と同じ継続ターンになる():
    """天候・地形と同じ処理順序の非対称性がサイドフィールド
    （リフレクター・ひかりのかべ・おいかぜ等）にも当てはまることの回帰テスト。

    現状このリポジトリのデータには、瀕死交代の入場特性・アイテムでサイド
    フィールドを設置するものは存在しない（リフレクター等は全て技のみが設置する）
    ため、`test_グローバルフィールド_...` と同様に
    `Battle.late_field_activation_context()` を直接使って「このターンの
    ON_TURN_END通過後に新規発動した」状況を再現する。

    実戦のリフレクター等の壁技は `SideFieldManager.apply()`
    （ひかりのねんど等によるON_MODIFY_DURATION延長に対応する経路）を使うため、
    `StackableFieldManager.activate()` を使うグローバルフィールドとは別の
    コードパスを検証する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
    )
    player0, _ = battle.players
    side = battle.get_side(player0)

    with battle.late_field_activation_context():
        assert side.apply("リフレクター", 5) is True

    # 修正前相当（補填なし）ならcount=5のままのところ、活性化直後に1回分を
    # 補填し、通常の技発動でリフレクターが発動した場合と同じcount=4になる。
    assert side.get("リフレクター").count == 4

    for _ in range(3):
        t.end_turn(battle)
        assert side.get("リフレクター").name == "リフレクター"
    assert side.get("リフレクター").count == 1

    # 5ターン目（設置ターンを含め計5ターン）で終了する
    t.end_turn(battle)
    assert side.get("リフレクター").name == ""


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


def test_じばく_キングシールドでブロックされても使用者はひんしになる():
    """seed=2688 の関連回帰テスト。

    まもる系統の中でもキングシールドでブロックされた場合に同じ修正が効くことを
    確認する（キングシールドは接触時に攻撃側のこうげきを下げる効果を持つが、
    じばくは非接触技のため、この副次効果自体は発動しないことも合わせて確認する）。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["じばく"])],
        team1=[Pokemon("バンギラス")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    defender_hp_before = defender.hp
    defender_atk_boost_before = defender.boosts["atk"]
    battle.volatile_manager.apply(defender, "キングシールド", count=1)

    t.run_move(battle, 0)

    assert battle.move_executor.move_success is False
    assert attacker.fainted
    assert defender.hp == defender_hp_before
    assert defender.boosts["atk"] == defender_atk_boost_before  # 非接触技なので発動しない


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


def test_すいすい_両者ばんのうがさ所持時に素早さ計算がRecursionErrorにならず正しい順序で解決される():
    """seed=120351 player=random (RecursionError@event_manager.py:_sort_handlers:219) の回帰テスト。

    core/speed_calculator.py の SpeedCalculator.calc_effective_speed() は、素早さ順序の
    解決（resolve_speed_order等）の中で対象ポケモンごとに呼ばれ、内部でDomainEvent.ON_CALC_SPEED
    を発火する。すいすい特性のハンドラ（handlers/ability.py の すいすい_modify_speed）はこの中で
    battle.weather_for(ctx.source) を呼び、これが通常のEvent.ON_CHECK_WEATHER_IMMUNE を発火する。

    このイベントに「ばんのうがさ」等の免疫ハンドラが2体分以上登録されていると
    （＝場に出ている両者がばんのうがさを持つ場合。ON_CHECK_WEATHER_IMMUNE ハンドラは
    active化時にのみ登録されるため、シングルバトルでは両アクティブが持つ必要がある）、
    core/event_manager.py の _sort_handlers が素早さ順にソートしようとして、再度同じ
    すいすい持ちポケモンの calc_effective_speed() を要求する。修正前はここで
    calc_effective_speed → ON_CALC_SPEED → weather_for → ON_CHECK_WEATHER_IMMUNE →
    _sort_handlers → calc_effective_speed →... の循環が無限に続きRecursionErrorになっていた
    （実際のfuzzシードでは、すいすい・ばんのうがさを併せ持つルナトーンと、ばんのうがさを
    持つ相手ポケモンの組み合わせで発生した）。

    修正後は SpeedCalculator に再入防止ガード（_computing_speed）を追加し、同一ポケモンについて
    calc_effective_speed が再入した場合はON_CALC_SPEEDを再発火せず素早さ実数値
    （mon.stats["spe"]）を返して循環を打ち切る。ON_CHECK_WEATHER_IMMUNE はsubject_specで
    対象ポケモンに一致するハンドラのみが実際に効果を発揮するブール値の免疫判定イベントであり、
    ソートに使う速度値が不正確でも判定結果（免疫か否か）自体には影響しない。

    さらに、この再入ガードが働く状況（＝すいすい持ちのポケモン自身がばんのうがさを持ち、
    かつ相手もばんのうがさを持つ）では、すいすい持ちポケモン自身の天候ボーナスは
    自分のばんのうがさによって元々無効化されるべきであり、フォールバック値
    （素の実数値）と最終的に正しい値が一致する。本テストでは、素の実数値ではルナトーン
    （すいすい・ばんのうがさ持ち、spe=90）よりピカチュウ（ばんのうがさ持ち、spe=110）の方が
    速いことを前提に、あめ下でも resolve_speed_order() の結果がピカチュウ→ルナトーンの順に
    なる（＝ルナトーンの実効素早さが誤って2倍化されていない）ことを確認する。誤って
    ばんのうがさによる自己無効化が働かず2倍化されていれば、ルナトーンの実効素早さ(180)が
    ピカチュウ(110)を上回り順序が逆転するため、フォールバック値ではなく最終的に正しい
    素早さで判定されていることを検証できる。
    """
    battle = t.start_battle(
        team0=[Pokemon("ルナトーン", ability_name="すいすい", item_name="ばんのうがさ")],
        team1=[Pokemon("ピカチュウ", item_name="ばんのうがさ")],
        weather=("あめ", 5),
    )
    luna, pikachu = battle.actives
    assert pikachu.stats["spe"] > luna.stats["spe"]  # 前提: 素の実数値はピカチュウの方が速い

    order = battle.resolve_speed_order()  # 修正前はここでRecursionErrorになっていた

    # 両者ばんのうがさ持ちのため、あめによるすいすいの倍化はルナトーン自身に適用されず、
    # 素の実数値通りピカチュウが先に来る
    assert order == [pikachu, luna]


def test_すなはき_攻撃技で致命打を受けたポケモンのON_HIT特性も瀕死ガードをすり抜けて発動する():
    """seed=2225 (LogInconsistency@event_manager.py:_check_handler_validity:214) の回帰テスト。

    core/move_executor.py は battle.modify_hp(ctx.defender, ...) をEvent.ON_HIT発火より前に
    実行する。そのため致命打（防御側のHPを0にする一撃）の場合、ON_HIT発火時点で
    ctx.defender.fainted が既にTrueになっている。core/event_manager.py の
    _check_handler_validity はHandler.allow_fainted_subject=Trueが明示されていない限り、
    subject_specが指すポケモンが瀕死ならハンドラをスキップする一元ガードを持つため、
    「攻撃技でHPが0になったときも特性を発動させてからひんしになる」仕様
    （.internal/spec/abilities/すなはき.md 等）を持つ Event.ON_HIT + subject_spec="defender:self"
    の特性が軒並み発動しなくなっていた。

    すなはき・こぼれダネ・どくげしょう・どくのトゲ・ふうりょくでんき・ほのおのからだの
    6特性にHandler.allow_fainted_subject=Trueを追加して修正した。個別の回帰テストは
    各特性のテストファイル（例: tests/abilities/test_ability_sa.py の
    test_すなはき_致命打でも発動する）に追加済みのため、ここでは代表としてすなはきのみを
    確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", ability_name="すなはき")],
        team1=[Pokemon("カビゴン", move_names=["たいあたり"])],
    )
    defender = battle.actives[0]
    defender.hp = 1
    t.fix_damage(battle, 9999)

    t.run_move(battle, 1)

    assert defender.fainted
    assert battle.weather.name == "すなあらし"
    assert battle.weather.count == 5


def test_ターン終了処理_ON_TURN_ENDの継続ダメージで決着した場合発動アナウンスログが勝敗確定ログより先に記録される():
    """seed=509 (LogInconsistency) の回帰テスト。

    TurnController._run_end_phase は Event.ON_TURN_END を発火する際、
    stop_if_winner_determined=True で決着後の残りハンドラの実行を打ち切る一方、
    決着させた当のハンドラ自身が続けて記録するログ（くろいヘドロ・どく・やけど等の
    発動アナウンス）は打ち切りの対象にならない。修正前は、そのハンドラの中で
    battle.modify_hp() が瀕死を検知した時点で battle.judge_winner() の呼び出しから
    即座に GAME_WON/GAME_LOST ログが記録されてしまい、「HP変化→勝敗確定→
    発動アナウンス」という不整合な順序になっていた。

    修正後は Event.ON_TURN_END の発火全体を begin_deferred_winner_log() /
    end_deferred_winner_log() の抑制区間で囲むため、「HP変化→発動アナウンス→
    勝敗確定」の正しい順序で記録されることを確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="くろいヘドロ", move_names=["はねる"])],
        team1=[Pokemon("カビゴン", move_names=["はねる"])],
        accuracy=100,
    )
    player0, player1 = battle.players
    mon = battle.actives[0]
    mon.hp = 1

    battle.step(commands={player0: Command.MOVE_0, player1: Command.MOVE_0})

    assert mon.fainted
    assert battle.winner is player1

    logs = [log for log in battle.event_logger.logs if log.turn == battle.turn]
    hp_idx = next(i for i, log in enumerate(logs) if log.log == LogCode.HP_CHANGED)
    item_idx = next(i for i, log in enumerate(logs) if log.log == LogCode.ITEM_TRIGGERED)
    won_idx = next(i for i, log in enumerate(logs) if log.log == LogCode.GAME_WON)
    # 修正前は won_idx < item_idx になっていた
    assert hp_idx < item_idx < won_idx


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


def test_だいばくはつ_まもるでブロックされても使用者はひんしになる():
    """seed=2688 (LogInconsistency@move_executor.py:_execute_move:429) の回帰テスト。

    まもる・ワイドガード等のブロック判定（handlers/volatile.py の _run_protect）は
    しめりけと同じEvent.ON_TRY_MOVE_1に登録されているため、move_executor は
    ON_TRY_MOVE_1が失敗した時点で一律にEvent.ON_PAY_HP（じばく・だいばくはつ・
    ミストバースト・てっていこうせんのHPコスト支払い）をスキップしていた。この結果、
    だいばくはつをまもるでブロックすると使用者が自滅しない（本来必ずひんしになる
    べき）というバグになっていた（.internal/spec/moves/だいばくはつ.md
    「まもる: 防がれる（防がれてもひんしになる）」）。

    修正後は AttackContext.blocked_by_protect フラグを見て、protectブロックの
    場合のみON_TRY_MOVE_1失敗後もEvent.ON_PAY_HPを発火させるため、まもるで
    ブロックされても使用者は必ずひんしになる。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["だいばくはつ"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    defender_hp_before = defender.hp
    battle.volatile_manager.apply(defender, "まもる", count=1)

    t.run_move(battle, 0)

    assert battle.move_executor.move_success is False  # まもるで技自体は不発
    assert attacker.fainted  # それでも使用者はひんしになる
    assert defender.hp == defender_hp_before  # まもるにより相手はダメージを受けない


def test_だいばくはつ_まもるでブロックされて自滅した場合の勝敗ログ記録タイミングが正しい():
    """seed=2688 の関連回帰テスト。

    まもるのブロック成立ログ（LogCode.PROTECT_SUCCEEDED）は、ON_PAY_HPより前の
    Event.ON_TRY_MOVE_1で即座に記録される。一方、ON_PAY_HPによる自滅で勝敗が
    確定した場合のGAME_LOST/GAME_WONログは、move_executorがbegin_deferred_winner_log
    ～end_deferred_winner_log（ON_MOVE_END完了後）の区間で抑制してから記録する。
    そのため、まもるでブロックされて自滅した場合でも、保護成立ログの方が
    勝敗確定ログより先に記録されることを確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["だいばくはつ"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    battle.volatile_manager.apply(defender, "まもる", count=1)

    t.run_move(battle, 0)

    assert attacker.fainted  # team0の唯一のポケモンがひんしになり勝敗が確定する

    logs = battle.event_logger.logs
    protect_idx = next(i for i, log in enumerate(logs) if log.log == LogCode.PROTECT_SUCCEEDED)
    lost_idx = next(i for i, log in enumerate(logs) if log.log == LogCode.GAME_LOST)
    assert protect_idx < lost_idx


def test_だっしゅつパック_メガシンカに伴ういかくで相手が発動条件を満たしてもメガシンカした側の技は実行される():
    """seed=147267 と同一根本原因の関連ケース。

    TurnController._run_megaevolve_phaseでメガシンカに伴いいかくが発動して
    相手（だっしゅつパック持ち）のInterrupt.EJECTPACK_REQUESTEDが立つと、
    修正前はこれが_run_move_phaseの各行動枠末尾でしか解決されなかった。
    battle.is_new_turn()はプレイヤーを問わない全体判定のため、メガシンカした
    自分自身（だっしゅつパックとは無関係）が相手より先に処理される行動枠でも
    「技を実行」ブロックが丸ごとスキップされ、メガシンカした側の技が
    そのターン一度も実行されないまま失われていた（技コマンドも
    pop_command()されずに残留し、次ターンのコマンド列がズレる）。

    修正後はTurnController._run_megaevolve_phase自体がフェーズ内で新たに
    発生しただっしゅつパックの発動条件をその場で解決するため、後続の
    _run_move_phaseが開始する時点でis_new_turn()は正しく真になり、
    メガシンカした側の技が無関係な相手の交代に巻き込まれず実行されることを
    確認する。

    自分自身より高速なライボルトがライボルトナイトでメガシンカし、メガ
    フォルムのいかく（ON_ABILITY_ENABLEDで再発動）で低速な相手（カビゴン、
    素早さ種族値30）のだっしゅつパックが発動する。
    """
    battle = t.start_battle(
        team0=[
            Pokemon("ライボルト", item_name="ライボルトナイト", move_names=["でんきショック"]),
        ],
        team1=[
            Pokemon("カビゴン", item_name="だっしゅつパック", move_names=["まるくなる", "たいあたり"]),
            Pokemon("コラッタ", move_names=["たいあたり"]),
        ],
        accuracy=100,
    )
    player0, player1 = battle.players
    # でんきショックのダメージ乱数・急所を固定し、だっしゅつパックで交代してきた
    # コラッタがそのまま被弾で瀕死になって強制的にカビゴンへ交代し戻る事態を防ぐ
    # （本題はメガシンカフェーズの割り込み交代解決であり、後続のでんきショックの
    # 命中先が生存し続けることが前提のテストのため、ダメージ量自体は関心事ではない）。
    t.fix_damage(battle, 0)

    # Turn1: 高速なライボルト側がメガシンカし、メガライボルトのいかくで
    # 低速なカビゴンのこうげきが下がりだっしゅつパックが発動する。
    # 修正前はライボルト自身のでんきショックが一度も実行されなかった。
    battle.step(commands={player0: Command.MEGAEVOL_0, player1: Command.MOVE_1})

    assert battle.actives[0].name == "メガライボルト"
    assert battle.actives[1].name == "コラッタ"  # だっしゅつパックで自動的に交代済み

    # 修正前はメガライボルトのでんきショックが丸ごとスキップされ、
    # pp_consumed_moveがNoneのままだった。
    assert battle.actives[0].pp_consumed_move.name == "でんきショック"
    assert battle.player_states[player0].reserved_commands == []
    assert battle.player_states[player1].reserved_commands == []

    # Turn2: 残留コマンドが無く、例外なく次ターンへ進行することを確認する。
    battle.step()

    assert battle.turn == 2


def test_だっしゅつパック_メガシンカに伴ういかくで自分自身が発動条件を満たしても残留コマンドが次ターンに持ち越されない():
    """seed=147267 player=random (IndexError@command_manager.py:resolve_move_from_command:156) の回帰テスト。

    TurnController._run_megaevolve_phase（_run_move_phaseより前のフェーズ）で
    メガシンカに伴う特性発動（Event.ON_ABILITY_ENABLED）からいかくが発動し、
    だっしゅつパック持ち自身の発動条件が満たされると、Interrupt.EJECTPACK_REQUESTED
    が立つ（この時点では交代は未実行）。_run_move_phaseのループが素早さで先に
    処理される自分自身の行動枠に到達すると、battle.is_new_turn()（=全体で
    割り込みが無いこと）がこのEJECTPACK_REQUESTEDのせいで偽と判定され、
    「技を実行」ブロックが丸ごとスキップされたまま、直後のだっしゅつパック
    解決処理で自分自身がちょうどそのタイミングで交代してしまう。この場合、
    今ターンの予約コマンド（例: MOVE_x）は一度もpop_command()されないまま
    残留し、次ターンのコマンド解決でIndexErrorになっていた。

    修正後はTurnController._run_move_phase末尾で「交代済みかつコマンドが
    未使用のまま残っている」場合に破棄するため、残留が起きないことを確認する。
    さらに今回はTurnController._run_megaevolve_phase自体でも、フェーズ内で
    新たに発生しただっしゅつパックの発動条件をその場で解決し、交代済みの
    残留コマンドを破棄するよう修正しているため、後続のフェーズが
    is_new_turn()を誤判定して無関係なプレイヤーの行動まで巻き込むことも無い。

    自分自身より低速な相手（ライボルト、素早さ種族値105）がライボルトナイトで
    メガシンカし、メガフォルムのいかく（ON_ABILITY_ENABLEDで再発動）を受けて、
    自分自身より高速なだっしゅつパック持ち（サンダース、素早さ種族値130）の
    こうげきランクが下がりだっしゅつパックが発動する。

    Note:
        本テストはflaky（間欠的失敗）だったことがある。原因はエンジン側の
        非決定性ではなく、後続のメガライボルトのでんきショックのダメージ乱数・
        急所を固定していなかったことによるテスト側の不備だった。だっしゅつパック
        で交代してきたコラッタ（低耐久）がでんきショックの急所+乱数上振れで
        ちょうど瀕死になると、控えがサンダースしか残っておらず死に出しで
        サンダースへ戻ってしまい、`battle.actives[0].name == "コラッタ"`が
        まれに失敗していた（本題の割り込み交代解決自体は正しく1回行われている）。
        `test_だっしゅつパック_メガシンカに伴ういかくで相手が発動条件を満たしても
        メガシンカした側の技は実行される`で既に踏んだのと同一原因パターンのため、
        同様に`t.fix_damage`でダメージを固定して対策している。
    """
    battle = t.start_battle(
        team0=[
            Pokemon("サンダース", item_name="だっしゅつパック", move_names=["たいあたり"]),
            Pokemon("コラッタ", move_names=["たいあたり"]),
        ],
        team1=[
            Pokemon("ライボルト", item_name="ライボルトナイト", move_names=["でんきショック"]),
        ],
        accuracy=100,
    )
    player0, player1 = battle.players
    # でんきショックのダメージ乱数・急所を固定し、だっしゅつパックで交代してきた
    # コラッタ（低耐久）がそのまま被弾で瀕死になり、控えがサンダースしか残っていない
    # ために死に出しでサンダースへ戻ってしまう事態を防ぐ（本題はメガシンカフェーズの
    # 割り込み交代解決であり、後続のでんきショックの命中先が生存し続けることが
    # 前提のテストのため、ダメージ量自体は関心事ではない。件の
    # 「相手が発動条件を満たしても～」テストと同一原因のflaky対策）。
    t.fix_damage(battle, 0)

    # Turn1: 低速なライボルト側がメガシンカし、メガライボルトのいかく
    # （とくせいの再発動）で高速なサンダースのこうげきが下がり、だっしゅつパックが
    # 発動する。修正前はサンダースが予約していたMOVE_0が一度も使われずに残る。
    battle.step(commands={player0: Command.MOVE_0, player1: Command.MEGAEVOL_0})

    assert battle.actives[0].name == "コラッタ"  # だっしゅつパックで自動的に交代済み
    assert battle.actives[1].name == "メガライボルト"
    assert battle.player_states[player0].interrupt == Interrupt.NONE
    assert battle.player_states[player0].reserved_commands == []
    assert battle.player_states[player1].reserved_commands == []

    # Turn2: 修正前は残留したMOVE_0が次ターンのコマンド列に紛れ込み、
    # command_manager.resolve_move_from_commandでIndexErrorが発生し得た。
    battle.step()

    assert battle.turn == 2  # 例外なく2ターン目が完了したことを確認


def test_だっしゅつパック_横断リファクタ_交代フェーズ由来の割り込みで残るテラスタルコマンドも破棄される():
    """個別のfuzzシード（1755, 18407, 23090, 117420, 147267等）はいずれも
    「割り込み交代で行動権を失ったプレイヤーの予約コマンドが破棄されず残留する」という
    同一の原因パターンだったが、その都度MOVE_x・MEGAEVOL_xコマンドが残留するケースだけを
    個別に手当てしてきた（TurnController._run_switch_phase／_run_megaevolve_phase／
    _run_move_phaseにそれぞれ同じ2行の破棄処理を手書きしていた）。

    この横断的な原因パターンに対応するため、破棄処理を
    TurnController._discard_stale_commands() という1つの共通ヘルパーに一元化した。
    このヘルパーはコマンドの種類を問わず（has_switched かつ command_reserved() であれば）
    破棄するため、過去に実際にテストされていなかったTERASTAL_xコマンドの残留について、
    交代フェーズ（_run_switch_phase）起点のケースでも同様に破棄されることを確認する。

    仮に破棄されなければ、後続の_run_terastal_phaseが交代前のポケモン用に予約された
    TERASTAL_0コマンドを交代後の別のポケモンにそのまま適用してしまい、
    本来テラスタルするはずのないポケモンが誤ってテラスタルする、という
    クラッシュを伴わない静かな誤動作になり得る。
    """
    battle = t.start_battle(
        team0=[
            Pokemon("ピカチュウ", move_names=["たいあたり"]),
            Pokemon("コラッタ", ability_name="いかく", move_names=["たいあたり"]),
        ],
        team1=[
            Pokemon(
                "カビゴン", item_name="だっしゅつパック", tera_type="じめん",
                move_names=["たいあたり"],
            ),
            Pokemon("ビードル", move_names=["たいあたり"]),
        ],
    )
    player0, player1 = battle.players

    # Turn1: プレイヤー0がいかく持ちのコラッタに交代する（交代フェーズ内の処理）。
    # いかくでカビゴンのこうげきが下がり、だっしゅつパックの割り込み交代が
    # 交代フェーズ内で発生する。プレイヤー1が予約していたTERASTAL_0は
    # 一度も使われないまま残るはずの箇所が今回のヘルパーの対象。
    battle.step(commands={player0: Command.SWITCH_1, player1: Command.TERASTAL_0})

    assert battle.actives[0].name == "コラッタ"
    assert battle.actives[1].name == "ビードル"  # だっしゅつパックで自動的に交代済み
    assert battle.player_states[player1].interrupt == Interrupt.NONE
    # 残留したTERASTAL_0が破棄され、交代後のビードルに誤って適用されていない
    assert battle.player_states[player1].reserved_commands == []
    assert battle.actives[1].is_terastallized is False

    # Turn2: 残留コマンドが無く、例外なく次ターンへ進行することを確認する。
    battle.step()

    assert battle.turn == 2


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
    SwitchManager.resolve_pending_interrupts()（通常経路と共通化した解決処理）が
    呼ばれるため、だっしゅつパックの強制交代が同一ターン内で解決され、次ターンへ
    正常に進行することを確認する。
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
    GAME_WON/GAME_LOSTログが記録されてしまっていた（.internal/spec/moves/てっていこうせん.md
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
    （.internal/spec/moves/てっていこうせん.md「HP0でのひんし・全滅判定」）。
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


def test_てっていこうせん_まもるでブロックされても反動でHPが減る():
    """seed=2688 の関連回帰テスト（.internal/spec/moves/てっていこうせん.md
    「まもる: 防がれる（防がれても反動は受ける）」）。

    てっていこうせんはHP全消費技（self_cost）ではなく最大HPの1/2を固定で
    消費する反動技（fixed_recoil）だが、同じON_PAY_HP機構を使うため、
    まもるでブロックされた場合も反動によるHP消費が正しく発生することを確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ドサイドン", move_names=["てっていこうせん"])],
        team1=[Pokemon("カビゴン")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    expected_cost = max(1, (attacker.max_hp + 1) // 2)
    hp_before = attacker.hp
    defender_hp_before = defender.hp
    battle.volatile_manager.apply(defender, "まもる", count=1)

    t.run_move(battle, 0)

    assert battle.move_executor.move_success is False  # まもるで技自体は不発
    assert attacker.hp == hp_before - expected_cost  # それでも反動でHPが減る
    assert defender.hp == defender_hp_before  # まもるにより相手はダメージを受けない


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


def test_とくせいなし_解除時に瀕死なら特性有効化イベントが発動しない():
    """seed=980 (LogInconsistency@core/ability_manager.py:remove_disabled_reason:151) の回帰テスト。

    AbilityManager.remove_disabled_reason は、とくせいなし等の無効化理由が
    解除され特性の有効状態がFalse→Trueに変化した際、対象ポケモンの瀕死判定を
    行わずにEvent.ON_ABILITY_ENABLEDを発火していた。とくせいなし状態は退場時に
    remove_all_volatiles経由で解除され、とくせいなし_enable_ability
    （handlers/volatile.py）がremove_ability_disabled_reasonを呼び出すため、
    対象が瀕死（HP0）になった直後でもゆきふらし等の天候形成特性
    （ON_ABILITY_ENABLEDに登録された入場特性群）が誤発動してしまっていた
    （seed=980ではベロリンガが瀕死になった直後にゆきふらしが発動し天候が
    変化していた）。修正後はON_ABILITY_ENABLEDの発火にskip_if_subject_fainted=True
    を指定し、対象が瀕死の場合はハンドラが実行されないことを確認する。
    """
    battle = t.start_battle(
        team0=[
            Pokemon("ベロリンガ", ability_name="ゆきふらし"),
            Pokemon("ピカチュウ"),
        ],
        team1=[Pokemon("ピカチュウ")],
    )
    mon = battle.actives[0]
    # 場に出た時点でゆきふらしのON_SWITCH_INが発動し天候がゆきになっているため、
    # 本題の検証（ON_ABILITY_ENABLED経由の誤発動）に影響しないよう一旦解除しておく
    battle.weather_manager.remove()
    assert battle.weather.name == ""

    battle.add_ability_disabled_reason(mon, "とくせいなし")
    battle.modify_hp(mon, -mon.hp)
    assert mon.fainted

    # 瀕死状態でとくせいなしを解除しても、天候形成特性は発動しない
    battle.remove_ability_disabled_reason(mon, "とくせいなし")
    assert battle.weather.name == ""


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


def test_どくびし_2層目でFIELD_STACKEDログが記録される():
    """seed=493 (LogInconsistency@field_manager.py:StackableFieldManager.activate)
    の回帰テスト。

    StackableFieldManager.activate() の count += 1 分岐（2層目以降の重ね掛け）では
    ログが一切記録されていなかった。修正後は新設のLogCode.FIELD_STACKEDが記録され、
    FieldPayload.count には増加後の層数が入る。1層目はFIELD_STARTEDのみが記録される。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("カビゴン")],
    )
    assert battle.activate_side_field(battle.players[0], "どくびし", 1)
    assert battle.activate_side_field(battle.players[0], "どくびし", 1)

    logs = battle.event_logger.logs
    started = [log for log in logs if log.log == LogCode.FIELD_STARTED]
    stacked = [log for log in logs if log.log == LogCode.FIELD_STACKED]
    assert len(started) == 1
    assert started[0].payload.count == 1
    assert len(stacked) == 1
    assert stacked[0].payload.count == 2
    assert stacked[0].idx == 0

    field = battle.get_side(battle.players[0]).get("どくびし")
    assert field.count == 2


def test_どくびし_Player1側に設置されるとログもPlayer1で記録される():
    """seed=493 (LogInconsistency@field_manager.py:BaseFieldManager._activate_field)
    の回帰テスト。

    BaseFieldManager._activate_field / _deactivate_field は、add_event_log の
    source引数に固定値0を渡していたため、SideFieldManager（owners=単一プレイヤー）で
    Player1（相手）側にどくびし等が設置・解除された場合でも、ログは常にPlayer0として
    記録されてしまっていた。

    修正後はfield.owners[0]をsourceに渡すため、Player1側への設置・解除ログは
    Player1のインデックスで記録されることを確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("カビゴン")],
    )
    assert battle.activate_side_field(battle.players[1], "どくびし", 1)

    logs = battle.event_logger.logs
    started = next(log for log in logs if log.log == LogCode.FIELD_STARTED)
    assert started.idx == 1

    assert battle.side_managers[1].deactivate("どくびし")
    ended = next(log for log in logs if log.log == LogCode.FIELD_ENDED)
    assert ended.idx == 1


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


def test_ねがいごと_両陣営が使用しても正しい対象へ正しい回復量が1回だけ適用される():
    """seed=2946 (LogInconsistency@handlers/field.py:ねがいごと_heal:406-409) の回帰テスト。

    core/field_manager.py の BaseFieldManager._deactivate_field は、
    Event.ON_FIELD_DEACTIVATE をemitしてからunregister_handlersする実装のため、
    あるFieldインスタンス（例: プレイヤー0のねがいごと）の解除で発火したemit呼び出しに、
    まだ解除されていない別インスタンス（プレイヤー1のねがいごと。countが残っている）の
    ハンドラも同じ共有ハンドラバケツ経由で巻き込まれて発火してしまっていた。
    core/event_manager.py のemit()はctx=Noneの場合ハンドラごとに_build_context()で
    独立にコンテキストを構築するため、value（実際に解除されたFieldインスタンス）と
    ctx.source（そのハンドラ自身のsubjectから解決したポケモン）の対応が一致するとは
    限らない。この結果、修正前はプレイヤー1のポケモンがプレイヤー0のねがいごとの
    回復量で誤って回復してしまっていた。

    修正後は handlers/field.py の `_is_own_field(value, own_field)` により、
    valueが「呼び出し側自身の効果に紐づくFieldインスタンス」と同一かどうかを
    identity比較で確認し、無関係なemitへの巻き込みを防ぐ。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン")],
        team1=[Pokemon("カビゴン")],
        # プレイヤー0は1ターン後、プレイヤー1は2ターン後に解決するようずらす
        side0={"ねがいごと": 1},
        side1={"ねがいごと": 2},
    )
    field0 = battle.get_side(battle.players[0]).get("ねがいごと")
    field1 = battle.get_side(battle.players[1]).get("ねがいごと")
    field0.heal = 30
    field1.heal = 77

    mon0, mon1 = battle.actives
    battle.modify_hp(mon0, v=-(mon0.hp - 1))
    battle.modify_hp(mon1, v=-(mon1.hp - 1))

    # Turn1: プレイヤー0のねがいごとのみが解決する
    t.end_turn(battle)
    assert mon0.hp == 1 + 30, "プレイヤー0の回復量が正しくない"
    assert mon1.hp == 1, "プレイヤー1がプレイヤー0のねがいごとの解決に巻き込まれて回復した"
    assert not field0.is_active
    assert field1.is_active and field1.count == 1, "プレイヤー1のねがいごとが誤って解除された"

    # Turn2: プレイヤー1のねがいごとが解決する
    t.end_turn(battle)
    assert mon1.hp == 1 + 77, "プレイヤー1の回復量が正しくない"
    assert mon0.hp == 1 + 30, "プレイヤー0が二重に回復していない"
    assert not field1.is_active


def test_はめつのねがい_両陣営が使用しても正しい対象へ正しいダメージ量が1回だけ適用される():
    """seed=2946 と同一原因（LogInconsistency@handlers/field.py）の横展開の回帰テスト。

    はめつのねがい_damageも ねがいごと_heal と同じ共有ハンドラバケツ経由の巻き込み
    バグの対象だった。両陣営が独立してはめつのねがいを設置した場合に、
    それぞれ正しい対象へ正しいダメージ量が1回だけ適用されることを確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン")],
        team1=[Pokemon("カビゴン")],
        side0={"はめつのねがい": 1},
        side1={"はめつのねがい": 2},
    )
    field0 = battle.get_side(battle.players[0]).get("はめつのねがい")
    field1 = battle.get_side(battle.players[1]).get("はめつのねがい")
    field0.damage = 30
    field1.damage = 77

    mon0, mon1 = battle.actives
    hp0_before, hp1_before = mon0.hp, mon1.hp

    # Turn1: プレイヤー0のはめつのねがいのみが解決する
    t.end_turn(battle)
    assert mon0.hp == hp0_before - 30, "プレイヤー0のダメージ量が正しくない"
    assert mon1.hp == hp1_before, "プレイヤー1がプレイヤー0のはめつのねがいの解決に巻き込まれてダメージを受けた"
    assert not field0.is_active
    assert field1.is_active and field1.count == 1, "プレイヤー1のはめつのねがいが誤って解除された"

    # Turn2: プレイヤー1のはめつのねがいが解決する
    t.end_turn(battle)
    assert mon1.hp == hp1_before - 77, "プレイヤー1のダメージ量が正しくない"
    assert mon0.hp == hp0_before - 30, "プレイヤー0が二重にダメージを受けていない"
    assert not field1.is_active


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


def test_ひでり_瀕死交代で発動した場合も通常設置と同じ5ターンで終了する():
    """seed=1609 (fuzz_log) の回帰テスト。

    天候は設置ターンを1ターン目として5ターンで終了する仕様
    （.internal/spec/abilities/ひでり.md「交代によりこの特性のポケモンを繰り出した
    ターンも1ターンに数える」）。通常の交代・技発動で設置された場合は、
    設置ターンの Event.ON_TURN_END で即座に1回分カウントダウンされるため、
    この仕様通り5ターンで終了する。

    しかし瀕死交代（対象ポケモンが瀕死になり、控えのポケモンが交代で入り、
    その入場特性が天候を設置する場合）は、TurnController._run_end_phase() で
    Event.ON_TURN_END が交代（SwitchManager.run_faint_switch）より先に発火する
    ため、設置ターンがそのターンのカウントダウン機会を逃してしまい、本来
    5ターンで終了するはずの天候が6ターン継続してしまっていた。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["でんこうせっか"])],
        team1=[
            Pokemon("コイキング"),
            Pokemon("ピカチュウ", ability_name="ひでり"),
        ],
        accuracy=100,
    )
    t.fix_damage(battle, 9999)  # コイキングを確実に瀕死にする
    player0, player1 = battle.players

    # コイキングが瀕死になり、控えのひでり持ちが瀕死交代で入場する
    # （このターンのON_TURN_END通過後に発生する交代）。
    battle.step(commands={player0: Command.MOVE_0, player1: Command.MOVE_0})

    assert battle.actives[1].ability.name == "ひでり"
    assert battle.weather.name == "はれ"
    # 修正前はこの時点でcount=5のまま（このターンのカウントダウン機会を
    # 逃していた）。修正後は活性化直後に1回分を補填し、通常の交代・技発動で
    # ひでりが発動した場合と同じcount=4になる。
    assert battle.weather.count == 4

    # 以降のターンでもう一方のポケモンが瀕死にならないよう、ダメージを0に
    # 固定する（fix_damageは以降の全てのダメージ計算に効くため、そのまま
    # だと次のターンで交代先も瀕死になってしまう）。
    t.fix_damage(battle, 0)

    # 残り3ターンはまだ持続する
    for _ in range(3):
        battle.step()
        assert battle.weather.name == "はれ"
    assert battle.weather.count == 1

    # 5ターン目（設置ターンを含め計5ターン）で終了する
    battle.step()
    assert battle.weather.name == ""


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


def test_ほろびのうた_ターン経過で瀕死になった側の敗北ログはVOLATILE_REMOVEDログより後に記録される():
    """seed=492 (LogInconsistency@volatile_manager.py:VolatileManager.remove) の回帰テスト。

    最後の1体がほろびのうたのカウント切れで瀕死になり、そのまま負けが確定する場合、
    ON_VOLATILE_END（ほろびのうた_faint）がmodify_hpで致死ダメージを与えたことに伴う
    勝者判定（battle.judge_winner()）はmodify_hp内で即座に行われる。修正前は
    VolatileManager.removeがbegin/end_deferred_winner_logで囲まれていなかったため、
    GAME_WON/GAME_LOSTログがVOLATILE_REMOVEDログより先に記録されてしまっていた。

    修正後はVOLATILE_REMOVEDログがGAME_WON/GAME_LOSTログより先に記録されることを
    確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"ほろびのうた": 1},
    )
    mon = battle.actives[0]

    t.end_turn(battle)

    assert mon.fainted
    # team0に控えがいないため、この瞬間に勝敗が決する
    assert battle.winner is battle.players[1]

    logs = battle.event_logger.logs
    removed_idx = next(i for i, log in enumerate(logs) if log.log == LogCode.VOLATILE_REMOVED)
    winner_indices = [
        i for i, log in enumerate(logs)
        if log.log in (LogCode.GAME_WON, LogCode.GAME_LOST)
    ]
    assert len(winner_indices) == 2
    # 修正前はVOLATILE_REMOVEDより先にGAME_WON/GAME_LOSTが記録されていた
    assert removed_idx < min(winner_indices)


def test_ほろびのうた_決着しない解除ではHP変化ログの後にVOLATILE_REMOVEDログが記録される():
    """seed=492関連の回帰確認。決着しない通常の揮発性状態解除ケース（瀕死になった側に
    交代先の控えがいて負けが確定しない場合）でも、ほろびのうたによるHP_CHANGEDログの後に
    VOLATILE_REMOVEDログが記録される順序は変わらない
    （begin/end_deferred_winner_logで囲んでもログ順序自体は変えない）。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("カビゴン")],
        team1=[Pokemon("ピカチュウ")],
        volatile0={"ほろびのうた": 1},
    )
    mon = battle.actives[0]

    t.end_turn(battle)

    assert mon.fainted
    # team0には控えがいるため、まだ勝敗は決していない
    assert battle.winner is None

    logs = battle.event_logger.logs
    hp_changed_idx = next(i for i, log in enumerate(logs) if log.log == LogCode.HP_CHANGED)
    removed_idx = next(i for i, log in enumerate(logs) if log.log == LogCode.VOLATILE_REMOVED)
    assert hp_changed_idx < removed_idx
    assert not any(log.log in (LogCode.GAME_WON, LogCode.GAME_LOST) for log in logs)


def test_まきびし_3層目までFIELD_STACKEDログの層数が正しい():
    """seed=493関連 (LogInconsistency@field_manager.py:StackableFieldManager.activate)
    の回帰テスト。max_count=3のまきびしで1層ずつ設置した場合、2層目・3層目の
    FIELD_STACKEDログのFieldPayload.countがそれぞれ2, 3になることを確認する。
    最大層に達した4回目の発動は失敗しログも増えない。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("カビゴン")],
    )
    for _ in range(3):
        assert battle.activate_side_field(battle.players[0], "まきびし", 1)
    assert not battle.activate_side_field(battle.players[0], "まきびし", 1)

    logs = battle.event_logger.logs
    stacked = [log for log in logs if log.log == LogCode.FIELD_STACKED]
    assert [log.payload.count for log in stacked] == [2, 3]

    field = battle.get_side(battle.players[0]).get("まきびし")
    assert field.count == 3


def test_マジックルーム_ねがいごと解除に巻き込まれずアイテム無効化状態が維持される():
    """seed=2946 と同一原因（LogInconsistency@handlers/field.py）の横展開の回帰テスト。

    マジックルーム_removeも同じ共有ハンドラバケツ経由の巻き込みバグの対象だった。
    グローバルフィールドのマジックルームは、サイドフィールドのねがいごととは別の
    Fieldインスタンスであるにもかかわらず、修正前は無関係なねがいごとの解除
    （Event.ON_FIELD_DEACTIVATE）に巻き込まれて、マジックルーム自身のcountが
    まだ残っているのにアイテム無効化状態が解除されてしまっていた。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", item_name="たべのこし")],
        team1=[Pokemon("ピカチュウ")],
        field={"マジックルーム": 5},
        side0={"ねがいごと": 1},
    )
    mon = battle.actives[0]
    assert not mon.item.enabled, "前提: マジックルーム中はアイテムが無効化されている"

    # ターン終了時にねがいごとが解除される（Event.ON_FIELD_DEACTIVATEが共有バケツで発火する）
    t.end_turn(battle)
    magic_room = battle.get_global_field("マジックルーム")
    assert magic_room.is_active, "マジックルームが誤って解除された"
    assert not mon.item.enabled, (
        "ねがいごとの解除に巻き込まれてマジックルームのアイテム無効化状態が解除された"
    )

    # マジックルームがまだ有効な間はアイテム無効化状態が維持され続ける
    t.end_turn(battle)
    assert magic_room.is_active
    assert not mon.item.enabled, "マジックルーム有効中にアイテムが有効化された"


def test_みかづきのまい_ステルスロックより後に設置してもHP回復がダメージより先に適用される():
    """seed=1879 (LogInconsistency) の回帰テスト。詳細な原因は
    test_いやしのねがい_ステルスロックより後に設置してもHP回復がダメージより先に適用される
    を参照（いやしのねがいと全く同じ構造のバグをみかづきのまいも抱えていた）。

    修正後はみかづきのまいのEvent.ON_SWITCH_INハンドラもpriority=90を明示し、
    設置技より必ず先に発動するようにしたため、HPが一度満タンまで回復してから
    ステルスロックのダメージが引かれ、最終的なHPが「満タン - ステルスロックの
    ダメージ」になることを確認する（.internal/spec/fields/みかづきのまい.md
    「設置技との順序」参照）。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ"), Pokemon("ライチュウ")],
        team1=[Pokemon("カビゴン")],
        # ステルスロックを先に、みかづきのまいを後から設置する
        # （設置順＝ハンドラ登録順のタイブレークを再現するため）
        side0={"ステルスロック": 1, "みかづきのまい": 1},
    )
    bench = battle.player_states[battle.players[0]].team[1]
    bench.hp = 1

    active = t.run_switch(battle, 0, 1)

    assert active is bench
    hazard_damage = active.max_hp // 8
    # 修正前は回復がダメージより後に適用され、最終的なHPが満タンのままだった
    assert active.hp == active.max_hp - hazard_damage
    assert not battle.get_side(active).get("みかづきのまい").is_active


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


def test_ミストバースト_ワイドガードでブロックされても使用者はひんしになる():
    """seed=2688 の関連回帰テスト。ワイドガード（is_blocked_by_wide_guard 経由の
    protectブロック）でも同じ修正が効くことを確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン", move_names=["ミストバースト"])],
        team1=[Pokemon("ピカチュウ")],
        accuracy=100,
    )
    attacker, defender = battle.actives
    defender_hp_before = defender.hp
    battle.volatile_manager.apply(defender, "ワイドガード", count=1)

    t.run_move(battle, 0)

    assert battle.move_executor.move_success is False
    assert attacker.fainted
    assert defender.hp == defender_hp_before


def test_みらいよち_両陣営が使用しても正しい対象へ正しいダメージ量が1回だけ適用される():
    """seed=2946 と同一原因（LogInconsistency@handlers/field.py）の横展開の回帰テスト。

    みらいよち_damageも ねがいごと_heal と同じ共有ハンドラバケツ経由の巻き込み
    バグの対象だった。両陣営が独立してみらいよちを設置した場合に、
    それぞれ正しい対象へ正しいダメージ量が1回だけ適用されることを確認する。
    """
    battle = t.start_battle(
        team0=[Pokemon("カビゴン")],
        team1=[Pokemon("カビゴン")],
        side0={"みらいよち": 1},
        side1={"みらいよち": 2},
    )
    field0 = battle.get_side(battle.players[0]).get("みらいよち")
    field1 = battle.get_side(battle.players[1]).get("みらいよち")
    field0.damage = 30
    field1.damage = 77

    mon0, mon1 = battle.actives
    hp0_before, hp1_before = mon0.hp, mon1.hp

    # Turn1: プレイヤー0のみらいよちのみが解決する
    t.end_turn(battle)
    assert mon0.hp == hp0_before - 30, "プレイヤー0のダメージ量が正しくない"
    assert mon1.hp == hp1_before, "プレイヤー1がプレイヤー0のみらいよちの解決に巻き込まれてダメージを受けた"
    assert not field0.is_active
    assert field1.is_active and field1.count == 1, "プレイヤー1のみらいよちが誤って解除された"

    # Turn2: プレイヤー1のみらいよちが解決する
    t.end_turn(battle)
    assert mon1.hp == hp1_before - 77, "プレイヤー1のダメージ量が正しくない"
    assert mon0.hp == hp0_before - 30, "プレイヤー0が二重にダメージを受けていない"
    assert not field1.is_active


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


def test_リフレクター_再発動はFIELD_STACKEDログを出さず失敗する():
    """seed=493関連の回帰確認。max_count<=1のフィールド（リフレクター等）は
    既に有効な場合、StackableFieldManager.activate()がFalseを返すのみで
    FIELD_STACKEDログは出ない（バグ2修正がmax_count<=1のフィールドに
    影響していないことの確認）。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("カビゴン")],
    )
    assert battle.activate_side_field(battle.players[0], "リフレクター", 5)
    assert not battle.activate_side_field(battle.players[0], "リフレクター", 5)

    logs = battle.event_logger.logs
    assert not any(log.log == LogCode.FIELD_STACKED for log in logs)
    field = battle.get_side(battle.players[0]).get("リフレクター")
    assert field.count == 5


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
        commands = battle.available_commands(player0)
    switch_commands = [cmd for cmd in commands if cmd.is_switch]
    assert switch_commands == [Command.SWITCH_1]


def test_天候_発動ログはPlayer0で記録され修正の影響を受けない():
    """seed=493関連の回帰確認。WeatherManager/GlobalFieldManager（owners=両プレイヤー）は
    field.owners[0]が常にPlayer0の要素であるため、バグ1修正（add_event_logの
    source引数をfield.owners[0]に変更）の前後で天候・グローバルフィールドの
    発動ログ表示は変わらない。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ")],
        team1=[Pokemon("カビゴン")],
    )
    assert battle.set_weather("あめ", 5)
    assert battle.activate_global_field("じゅうりょく", 5)

    logs = battle.event_logger.logs
    started = [log for log in logs if log.log == LogCode.FIELD_STARTED]
    assert len(started) == 2
    assert all(log.idx == 0 for log in started)


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


def test_技反射_反射直後のハンドラ解除主体の食い違いによるリークで無関係な相手に技効果が誤発動しない():
    """seed=825 (LogInconsistency@move_executor.py:run_move:339) の回帰テスト。

    MoveExecutor.run_move() は技開始時に ctx.move.register_handlers(events, attacker)
    （この時点では ctx.attacker == attacker）で技固有ハンドラ（なかよくするの
    ON_STATUS_HITハンドラ等）を登録し、finally節末尾で ctx.move.unregister_handlers(...)
    で解除する。しかしマジックミラー等（Event.ON_CHECK_REFLECT）で技が反射されると、
    途中で ctx.attacker/ctx.defender が入れ替わる。修正前は finally節の解除呼び出しに
    ctx.attacker（反射後の入れ替わった主体）をそのまま渡していたため、登録時の主体
    （反射前の攻撃者）と解除時に渡す主体が食い違い、EventManager.off() の完全一致
    チェック（rh.handler == handler and rh.registered_subject == subject）が失敗して
    削除が空振りし、ハンドラが登録されたまま永続的にリークしていた。

    なかよくするのハンドラは MoveHandler(skip_subject_check=True) で登録されているため、
    リークした状態でも以降の任意の別の変化技の ON_STATUS_HIT 発火時に主体を問わず
    無条件で再実行され、その時点の無関係な相手に効果を誤って適用してしまっていた。

    修正後は unregister_handlers に ctx.attacker ではなく run_move の引数（登録時と
    同じ主体）を渡すため、反射が起きてもハンドラは正しく解除される。
    """
    battle = t.start_battle(
        team0=[Pokemon("ピカチュウ", move_names=["なかよくする", "つるぎのまい"])],
        team1=[
            Pokemon("ニャース", ability_name="マジックミラー"),
            Pokemon("コラッタ"),
        ],
    )
    attacker = battle.actives[0]
    mirror_holder = battle.actives[1]

    # Step1: なかよくするがマジックミラーで反射される。反射によりctx.attacker/defenderが
    # 入れ替わり、修正前はunregister_handlersに渡す主体が食い違ってハンドラがリークしていた。
    t.run_move(battle, 0, 0)
    assert attacker.boosts["atk"] == -1  # 反射で自分自身のこうげきが下がる
    assert mirror_holder.boosts["atk"] == 0  # マジックミラー側は無傷

    # Step2: 無関係な相手（コラッタ）に交代し、リーク元とは無関係なつるぎのまい
    # （自己強化、ON_STATUS_HITを使用する変化技）を使わせる。リークしたなかよくするの
    # ハンドラが残っていると、skip_subject_check=Trueのため主体を問わず無条件に再発火し、
    # この時点の相手（コラッタ）のこうげきを誤って下げてしまう。
    other = t.run_switch(battle, 1, 1)
    t.run_move(battle, 0, 1)
    assert attacker.boosts["atk"] == 1  # つるぎのまいで自分のこうげきが+2される (-1+2)
    assert other.boosts["atk"] == 0  # 無関係な相手のこうげきは変化しない（リークなし）

    # Step3: 反射されない形で再度なかよくするを使わせる。リークしたハンドラが二重登録
    # されて残っていた場合はこうげきが-2されてしまう。正規の効果のみ(-1)が
    # 1回だけ適用されることを確認する。
    t.run_move(battle, 0, 0)
    assert other.boosts["atk"] == -1


def test_木探索_探索中に相手自身の割り込み交代が起きても観測マスクで交代先が消えずIndexErrorにならない():
    """tsfuzz seed=4698 (IndexError@tree_search_player.py:choose_command:118) の回帰テスト。

    TreeSearchPlayer（の具体実装である MinimaxPlayer）が自分自身の割り込み交代
    （ききかいひ等のEMERGENCY）を解決する際、`MinimaxPlayer._score_command`
    （旧 `_worst_case_over_opponent`）は `battle.build_observation(自分)` の子孫である
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
    (相手)` が空になり、相手の MinimaxPlayer.fallback() が
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
    class ForcedActionPlayer(MinimaxPlayer):
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

    searcher = MinimaxPlayer(username="Searcher")
    searcher.team = [
        Pokemon("グソクムシャ", ability_name="ききかいひ", move_names=["たいあたり"]),
        Pokemon("ヒトカゲ", move_names=["たいあたり"]),
    ]

    opponent = ForcedActionPlayer(username="Opponent", forced_move_name="とんぼがえり")
    opponent.team = [
        Pokemon("ゼニガメ", move_names=["とんぼがえり"]),
        Pokemon("カメックス", move_names=["たいあたり"]),
    ]
    battle = Battle(searcher, opponent, n_selected=2, seed=1)
    battle.test_option.accuracy = 100
    battle.start()
    battle.player_states[opponent].team[0].moves[0].revealed = True  # とんぼがえりだけ公開。カメックスは非公開のまま
    battle.actives[0].hp = 100  # グソクムシャの最大HP150の半分(75)超
    battle.roll_damage = lambda attacker, defender, move, critical=False: 50  # 半分を跨ぐ固定ダメージ

    battle.step()  # 修正前はここでIndexErrorになっていた

    assert searcher._searching is False
    assert opponent._searching is False


def test_木探索_観測用盤面をコピーしてもobserverが引き継がれ瀕死交代の無限再帰が起きない():
    """tsfuzz seed=3 (RecursionError@copy_utils.py:fast_copy:22) の回帰テスト。

    jpoke.players.minimax_player の MinimaxPlayer._score_command
    （旧 `TreeSearchPlayer._worst_case_over_opponent`）は
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
    - Searcher側はmax_plies=1のMinimaxPlayerとし、あらゆる攻撃を固定ダメージで
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

    class DeterministicFallbackPlayer(MinimaxPlayer):
        def fallback(self, battle: Battle) -> Command:
            return battle.available_commands(self)[0]

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
