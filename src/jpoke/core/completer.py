from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle, Player, PlayerState
    from jpoke.model import Pokemon, Move

from jpoke.enums import Command


def complete(battle: Battle, player: Player) -> None:
    """指定したプレイヤーの情報を補完し、木探索できる状態にする。

    Args:
        battle: Battle インスタンス
        player: 情報を補完するプレイヤー
    """
    _complete_selection_indexes(battle, player)

    match battle.phase:
        case "action":
            _complete_action_command(battle, player)
        case "switch":
            _complete_switch_command(battle, player)


def _complete_selection_indexes(battle: Battle, player: Player) -> None:
    """PlayerState インスタンスの選出indexを補完する。

    Args:
        battle: Battle インスタンス
        player: Player インスタンス
    """
    state = battle.player_states[player]
    n_unrevealed = battle.n_selected - len(state.selection_indexes)
    if n_unrevealed > 0:
        unrevealed_indexes = [
            i for i, mon in enumerate(state.team) if not mon.revealed
        ]
        state.selection_indexes.extend(unrevealed_indexes[:n_unrevealed])


def _complete_action_command(battle: Battle, player: Player) -> None:
    """PlayerState インスタンスの行動コマンドを補完する。

    Args:
        battle: Battle インスタンス
        player: Player インスタンス
    """
    state = battle.player_states[player]

    if state.command_reserved():
        if state.next_command.is_action():
            # 予約済みコマンドがある場合は補完不要
            print(f"DEBUG: Action command {state.next_command} is already reserved. No need to complete.")
            return
        else:
            # 不適切なコマンドが予約されている場合はクリアする
            print(f"DEBUG: {state.next_command} is not an action command. Clearing reserved command.")
            state.clear_reserved_commands()

    commands = state.legal_commands

    # 合法手がない場合は、MOVE_0を合法手とする
    if not commands:
        commands = [Command.MOVE_0]

    state.reserve_command(commands[0])
    print(f"DEBUG: Reserving action command {state.next_command} for player {player.name}.")


def _complete_switch_command(battle: Battle, player: Player) -> None:
    """PlayerState インスタンスの交代コマンドを補完する。

    Args:
        battle: Battle インスタンス
        player: Player インスタンス
    """
    state = battle.player_states[player]

    # 場のポケモンが瀕死でないならば補完不要
    if not state.active.fainted:
        print(f"DEBUG: Active Pokémon {state.active} is not fainted. No need to complete switch command.")
        return

    if state.command_reserved():
        if state.next_command.is_switch:
            # 予約済みコマンドがある場合は補完不要
            print(f"DEBUG: Switch command {state.next_command} is already reserved. No need to complete.")
            return
        else:
            # 不適切なコマンドが予約されている場合はクリアする
            print(f"DEBUG: {state.next_command} is not a switch command. Clearing reserved command.")
            state.clear_reserved_commands()

    commands = state.legal_commands

    # 合法手がない場合は、ベンチの先頭ポケモンを交代コマンドとする
    if not commands:
        mon = state.bench[0]
        mon_index = state.team.index(mon)
        commands = [Command.get_switch_command(mon_index)]

    state.reserve_command(commands[0])
    print(f"DEBUG: Reserving switch command {state.next_command} for player {player.name}.")
