from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle, Player, PlayerState
    from jpoke.model import Pokemon

from jpoke.model import Move


def complete(battle: Battle, player: Player) -> None:
    """指定したプレイヤーの情報を補完し、木探索できる状態にする。

    Args:
        battle: Battle インスタンス
        player: 情報を補完するプレイヤー

    Returns:
        対象プレイヤーが予約すべきコマンドの種類
    """
    if battle.phase == "selection":
        raise ValueError("Cannot complete during selection phase.")

    state = battle.player_states[player]

    # 選出情報を補完する
    _complete_selection_indexes(battle, player)

    # ポケモンの情報を補完する
    for mon in state.team:
        _complete_pokemon(mon)


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


def _complete_pokemon(mon: Pokemon) -> None:
    """Pokemon インスタンスの情報を補完する。

    Args:
        mon: Pokemon インスタンス
    """
    # 技の情報を補完する
    if not mon.moves:
        mon.moves = [Move("はねる")]
