from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle, Player
    from jpoke.model import Pokemon

from copy import deepcopy

from jpoke.core.event_logger import EventLogger
from jpoke.model.ability import Ability
from jpoke.model.item import Item


OBSERVED_MOVE_INDEXES: dict[Pokemon, dict[int, int]] = {}  # 技のインデックス変更を記録する辞書. dict[Pokemon, dict[old_index, new_index]]


def build(battle: Battle, observer: Player, copy_logs: bool = True) -> Battle:
    """Battle インスタンスから Observation インスタンスを構築する。

    Args:
        battle: Battle インスタンス
        observer: 観測対象のプレイヤー
        copy_logs: Falseの場合、event_logger/command_log（対戦開始からの
            全履歴）をdeepcopyせず、複製先に空の新規ログを持たせる
            （複製元のログは変更されない）。全履歴のdeepcopyはターン数に
            比例してコストが増えるため、ログを参照しない用途で使うと
            コピー負荷を削減できる。既定はTrueで、従来通り履歴を
            引き継いだ複製を作る（Battle.copy()のdocstring参照）。

    Returns:
        Observation インスタンス

    Warning:
        本関数はモジュールグローバルな辞書 OBSERVED_MOVE_INDEXES を
        呼び出しのたびに再代入・書き込み・読み出しする実装であり、
        スレッドセーフではない。自己対戦データ収集などで並列化する場合は
        ProcessPoolExecutor 等のプロセス並列を使うこと。
        ThreadPoolExecutor 等で複数スレッドから同時に build() を呼び出すと、
        インデックス対応表が競合して壊れる可能性がある。
        copy_logs=Falseの場合はさらに、deepcopy実行中に battle の
        event_logger/command_log を一時的に空へ差し替える（完了後は
        直ちに元へ復元する）。この間に別スレッドが同じ battle の
        event_logger/command_log へ読み書きすると競合しうる。

    Note:
        copy_logs=Falseは Battle.copy(copy_logs=False) と同じ「ログを
        一時的に空へ差し替えてから deepcopy し、完了後直ちに復元する」
        方式を再利用している。
    """
    opponent = battle.opponent(observer)

    # Battle インスタンスをコピーして、相手プレイヤーの情報を隠蔽する
    if copy_logs:
        new = deepcopy(battle)
    else:
        saved_event_logger, saved_command_log = battle.event_logger, battle.command_log
        battle.event_logger, battle.command_log = EventLogger(), []
        try:
            new = deepcopy(battle)
        finally:
            battle.event_logger, battle.command_log = saved_event_logger, saved_command_log
    # ゲーム進行用の random は deepcopy のまま独立させる（本体と共有すると、方策が
    # choose_command() 内で sim.random を直接触った場合に、本来は技実行後（ダメージ
    # ロール・命中判定・急所判定等）に消費されるはずの乱数列を行動選択時点で先取り
    # 消費できてしまい、「これから打つ技が急所に当たるか」を打つ前に知った上で行動を
    # 選べるチート的先読みが可能になる。そのため行動選択専用の decision_random だけを
    # 本体と同一のオブジェクト参照に差し替える。
    # 観測用コピーは choose_command()/choose_selection() に渡され、RandomPlayer 等は
    # sim.decision_random（＝battle.decision_random）を消費して選択する。これを
    # deepcopyのまま独立させると、技を使わず交代のみが選ばれ続けるターンでは本体の
    # battle.decision_random が一切進まず、次のターンも同じ乱数状態から観測用コピーが
    # 作られて同じ選択を繰り返す無限ループに陥る
    # （交代コマンドのみ選ばれ続け技が二度と使われない不具合の原因だった）。
    new.decision_random = battle.decision_random
    new.observer = observer
    _mask(new, opponent)
    return new


def _mask(battle: Battle, player: Player):
    """PlayerState インスタンスの情報を隠蔽する。

    Args:
        battle: Battle インスタンス
        player: 隠蔽対象のプレイヤー
    """
    global OBSERVED_MOVE_INDEXES
    OBSERVED_MOVE_INDEXES = {}

    state = battle.player_states[player]

    # 場に出ているポケモンを特定する（交代前など active_index が未設定の局面もあるため
    # battle.actives/get_active は使わない。両者とも未設定なら例外を送出する仕様のため）。
    active_mon = state.team[state.active_index] if state.active_index is not None else None

    # チームのポケモンの情報を隠蔽する
    for mon in state.team:
        _mask_pokemon(battle, mon, mon is active_mon)

    # 選出されているポケモンのインデックスを、公開されているポケモンのみに更新する
    state.selected_indexes = [
        i for i in state.selected_indexes if state.team[i].revealed
    ]

    if battle.phase == "selection":
        return

    _mask_command(battle, player)
    return


def _mask_pokemon(battle: Battle, mon: Pokemon, is_active: bool) -> Pokemon:
    """Pokemon インスタンスの情報を隠蔽する。

    Args:
        battle: Battle インスタンス（特性・アイテムのハンドラ登録の同期に使う）
        mon: Pokemon インスタンス
        is_active: mon が現在場に出ているかどうか
    """
    # ステータス情報を隠蔽する
    # 相手に見えるのはHP割合（HPバー）であって絶対量ではないため、
    # マスキングによる最大HP変化でHP割合が歪まないよう keep_ratio で揃える。
    mon.set_nature("まじめ", hp_policy="keep_ratio")  # 無補正
    mon.set_evs([0] * 6, hp_policy="keep_ratio")

    # テラスタイプをベースタイプに上書きして隠蔽する
    if not mon.is_terastallized:
        mon.tera_type = mon.base_types[0]

    # 特性の情報を隠蔽する
    _mask_ability(battle, mon, is_active)

    # アイテムの情報を隠蔽する
    _mask_item(battle, mon, is_active)

    # 技の情報を隠蔽する
    _mask_move(mon)

    return mon


def _mask_ability(battle: Battle, mon: Pokemon, is_active: bool):
    """特性情報を隠蔽する。

    Args:
        battle: Battle インスタンス（特性ハンドラ登録の同期に使う）
        mon: Pokemon インスタンス
        is_active: mon が現在場に出ているかどうか

    Note:
        mon が場に出ている場合、既に mon.ability の特性ハンドラが
        EventManager に登録されている。ここで mon.ability を新しい
        （無特性の）インスタンスに差し替えるだけだと、EventManager 側の
        登録は古い特性のハンドラを参照したまま残ってしまい、後で交代処理が
        mon.ability.unregister_handlers() を呼んでも（差し替え後の無特性
        インスタンスにはハンドラが無いため）何も解除されず、退場済みの
        ポケモンの特性ハンドラが発火し続けるバグになる
        （例: ものひろいのターン終了時ハンドラが交代後も残り続け、
        battle.foe() が「場に出ていない」で例外を送出する）。
        差し替え前に登録済みハンドラを解除し、差し替え後の（無特性の
        ＝ハンドラを持たない）インスタンスで登録し直すことで、
        EventManager の登録内容と mon.ability を一致させる。
    """
    if (
        not mon.ability.revealed
        and len(mon.data.abilities) > 1
    ):
        if is_active:
            mon.ability.unregister_handlers(battle.events, mon)
        mon.ability = Ability()
        if is_active:
            mon.ability.register_handlers(battle.events, mon)


def _mask_item(battle: Battle, mon: Pokemon, is_active: bool):
    """アイテム情報を隠蔽する。

    Args:
        battle: Battle インスタンス（アイテムハンドラ登録の同期に使う）
        mon: Pokemon インスタンス
        is_active: mon が現在場に出ているかどうか

    Note:
        _mask_ability と同様の理由で、mon が場に出ている場合は
        差し替え前後で EventManager の登録を同期させる必要がある。
    """
    if not mon.item.revealed:
        if is_active:
            mon.item.unregister_handlers(battle.events, mon)
        mon.item = Item()
        if is_active:
            mon.item.register_handlers(battle.events, mon)


def _mask_move(mon: Pokemon):
    """技情報を隠蔽する。

    Args:
        mon: Pokemon インスタンス

    Note:
        技のリストを作り直すため、そのままだとインデックス情報が壊れてコマンドとの対応関係が壊れてしまう。
        そこで NEW_MOVE_IDNEXES に新旧インデックスを記録しておき、コマンドを隠蔽する際に利用する。
    """
    global OBSERVED_MOVE_INDEXES
    OBSERVED_MOVE_INDEXES[mon] = {}

    new_moves = []
    for i, move in enumerate(mon.moves):
        if move.revealed:
            new_moves.append(move)
            new_index = len(new_moves) - 1
            OBSERVED_MOVE_INDEXES[mon][i] = new_index

    mon.moves = new_moves


def _mask_command(battle: Battle, player: Player):
    state = battle.player_states[player]
    active = state.active

    # 予約済みコマンドをクリアする
    state.clear_reserved_commands()

    # 予約が必要なコマンドの種類を記録する
    state.required_command_type = None
    if battle.phase == "action":
        state.required_command_type = "any"
    elif battle.phase == "switch":
        # 後攻でかつ生存している場合は技コマンドの予約が必要
        if (
            battle.query.is_second_actor(player)
            and active.alive
        ):
            state.required_command_type = "move"

    observed_move_indexes = OBSERVED_MOVE_INDEXES[active]

    # last_available_commandsを隠蔽する。これは観測盤面における合法手として扱われる。
    commands = []
    for cmd in state.last_available_commands:
        idx = cmd.index
        # 交代コマンドは、控えのポケモンが公開されている場合のみ利用可能とする
        if cmd.is_switch:
            mon = state.team[idx]
            if mon.revealed:
                commands.append(cmd)
            continue

        # 技コマンドは、技が公開されている場合のみ利用可能とする
        if not active.moves:
            continue

        if idx in observed_move_indexes:
            observed_index = observed_move_indexes[idx]
            new_cmd = cmd.change_index(observed_index)
            commands.append(new_cmd)

    # 公開状況だけでなく required_command_type でも絞り込む。ここを飛ばすと、
    # 木探索が相手の合法手を総当たりした際に「相手がまだ提出していないはずの
    # コマンド種別」が混入し、sim.step() の validate_command() に弾かれて
    # ValueError になる（例: switch フェーズで後攻の相手に対して SWITCH_x を渡してしまう）。
    required = state.required_command_type
    if required not in (None, "any"):
        commands = [cmd for cmd in commands if cmd.is_type(required)]

    state.last_available_commands = commands
