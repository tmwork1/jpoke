from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle, Player, PlayerState
    from jpoke.model import Pokemon

from jpoke.utils.type_defs import CommandType
from jpoke.enums import Command
from jpoke.model import Move


def complete(battle: Battle, player: Player) -> CommandType | None:
    """指定したプレイヤーの情報を補完し、木探索できる状態にする。

    Args:
        battle: Battle インスタンス
        player: 情報を補完するプレイヤー

    Returns:
        対象プレイヤーが予約すべきコマンドの種類
    """
    if battle.phase == "selection":
        raise ValueError("Cannot complete commands during selection phase.")

    state = battle.player_states[player]

    # 選出情報を補完する
    _complete_selection_indexes(battle, player)

    # ポケモンの情報を補完する
    for mon in state.team:
        _complete_pokemon(mon)

    # 予約コマンドを補完する
    if battle.phase == "action":
        state.clear_reserved_commands()
        return "action"

    elif battle.phase == "switch":
        return _complete_switch_command(battle, player)


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


def _complete_switch_command(battle: Battle, player: Player) -> CommandType | None:
    """PlayerState インスタンスの交代コマンドを補完する。

    Args:
        battle: Battle インスタンス
        player: Player インスタンス
    """
    state = battle.player_states[player]

    # 相手がまだ行動していない場合は、技コマンドが必要であることを示す
    if battle.query.is_second_actor(player):
        return "move"

    # 相手の場のポケモンが瀕死の場合は、交代コマンドが必要であることを示す
    if state.active.fainted:
        return "switch"


def _complete_pokemon(mon: Pokemon) -> None:
    """Pokemon インスタンスの情報を補完する。

    Args:
        mon: Pokemon インスタンス
    """
    # 技の情報を補完する
    if not mon.moves:
        mon.moves = [Move("はねる")]
