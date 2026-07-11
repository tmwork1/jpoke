"""fuzzテストで発見されたバグの回帰テスト。

再現性のあるランダムシードをそのまま固定するのではなく、原因箇所を特定した上で
core/エンジン共通ロジックの最小ケースとして再現する。
"""
from jpoke import Battle, Player
from jpoke.model import Pokemon
from jpoke.enums import Command
from jpoke.players import TreeSearchPlayer

from . import test_utils as t


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
        (victim, searcher), n_selected=2, seed=1,
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

    assert battle.turn == 1  # 例外なく1ターン目が完了したことを確認
