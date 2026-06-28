from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle, Player, PlayerState
    from jpoke.model import Pokemon

from copy import deepcopy

from jpoke.model import Ability, Item


OBSERVED_MOVE_INDEXES: dict[Pokemon, dict[int, int]] = {}  # 技のインデックス変更を記録する辞書. dict[Pokemon, dict[old_index, new_index]]


def build(battle: Battle, observer: Player) -> Battle:
    """Battle インスタンスから Observation インスタンスを構築する。

    Args:
        battle: Battle インスタンス
        observer: 観測対象のプレイヤー

    Returns:
        Observation インスタンス
    """
    rival = battle.rival(observer)

    # Battle インスタンスをコピーして、相手プレイヤーの情報を隠蔽する
    new = deepcopy(battle)
    new.observer = observer
    _mask(new, rival)
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

    # チームのポケモンの情報を隠蔽する
    for mon in state.team:
        _mask_pokemon(mon)

    if battle.phase == "selection":
        return

    # 選出されているポケモンのインデックスを、公開されているポケモンのみに更新する
    state.selection_indexes = [
        i for i in state.selection_indexes if state.team[i].revealed
    ]

    _mask_command(battle, player)

    return


def _mask_pokemon(mon: Pokemon) -> Pokemon:
    """Pokemon インスタンスの情報を隠蔽する。

    Args:
        mon: Pokemon インスタンス
    """
    # ステータス情報を隠蔽する
    mon.nature = "まじめ"  # 無補正
    mon.effort = [0] * 6

    # テラスタイプをベースタイプに上書きして隠蔽する
    if not mon.terastallized:
        mon.tera_type = mon.base_types[0]

    # 特性の情報を隠蔽する
    _mask_ability(mon)

    # アイテムの情報を隠蔽する
    _mask_item(mon)

    # 技の情報を隠蔽する
    _mask_move(mon)

    return mon


def _mask_ability(mon: Pokemon):
    """特性情報を隠蔽する。

    Args:
        mon: Pokemon インスタンス
    """
    if (
        not mon.ability.revealed
        and len(mon.data.abilities) > 1
    ):
        mon.ability = Ability()


def _mask_item(mon: Pokemon):
    """アイテム情報を隠蔽する。

    Args:
        mon: Pokemon インスタンス
    """
    if not mon.item.revealed:
        mon.item = Item()


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
    state.required_command_type = ""
    if battle.phase == "action":
        state.required_command_type = "action"
    elif battle.phase == "switch":
        # 後攻でかつ生存している場合は技コマンドの予約が必要
        if (
            battle.query.is_second_actor(player)
            and active.alive
        ):
            state.required_command_type = "move"

    print(f"DEBUG: phase={battle.phase} {player.name} requried={state.required_command_type}")

    observed_move_indexes = OBSERVED_MOVE_INDEXES[active]

    # last_available_commandsを隠蔽する。これは観測盤面における合法手として扱われる。
    commands = []
    for cmd in state.last_available_commands:
        idx = cmd.index
        # 交代コマンドは、控えのポケモンが公開されている場合のみ利用可能とする
        if cmd.is_type("switch"):
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

    state.last_available_commands = commands
