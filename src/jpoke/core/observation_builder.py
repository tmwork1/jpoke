from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle, Player, PlayerState
    from jpoke.model import Pokemon, Move

from copy import deepcopy

from jpoke.model import Ability, Item, Move


def build(battle: Battle, observer: Player) -> Battle:
    """Battle インスタンスから Observation インスタンスを構築する。

    Args:
        battle: Battle インスタンス
        observer: 観測対象のプレイヤー

    Returns:
        Observation インスタンス
    """
    rival = battle.rival(observer)

    # Battle インスタンスをコピーして、観測対象のプレイヤー以外の情報を隠蔽する
    new = deepcopy(battle)
    _mask(new, rival)
    return new


def _mask(battle: Battle, player: Player) -> PlayerState:
    """PlayerState インスタンスの情報を隠蔽する。

    Args:
        battle: Battle インスタンス
        player: 隠蔽対象のプレイヤー
    """
    state = battle.player_states[player]

    _mask_commands(state)

    # チームのポケモンの情報を隠蔽する
    for mon in state.team:
        _mask_pokemon(mon)

    # 選出されているポケモンのインデックスを、公開されているポケモンのみに更新する
    state.selection_indexes = [
        i for i in state.selection_indexes if state.team[i].revealed
    ]

    return state


def _mask_commands(state: PlayerState):
    """PlayerState インスタンスの予約コマンドを隠蔽する。

    Args:
        state: PlayerState インスタンス
    """
    # 予約済みコマンドをクリアする
    state.clear_reserved_commands()

    # 利用可能なコマンドのうち、開示されている選択肢のみを残す
    predictable_commands = []
    for cmd in state.legal_commands:
        if cmd.is_move:
            move = state.active.moves[cmd.index]
            if move.revealed:
                predictable_commands.append(cmd)

        elif cmd.is_switch:
            mon = state.team[cmd.index]
            if mon.revealed:
                predictable_commands.append(cmd)

    state.legal_commands = predictable_commands


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
    """Ability インスタンスの情報を隠蔽する。

    Args:
        mon: Pokemon インスタンス
    """
    if (
        not mon.ability.revealed
        and len(mon.data.abilities) > 1
    ):
        mon.ability = Ability()


def _mask_item(mon: Pokemon):
    """Item インスタンスの情報を隠蔽する。

    Args:
        mon: Pokemon インスタンス
    """
    if not mon.item.revealed:
        mon.item = Item()


def _mask_move(mon: Pokemon):
    """Move インスタンスの情報を隠蔽する。

    Args:
        mon: Pokemon インスタンス
    """
    mon.moves = [move for move in mon.moves if move.revealed]
    if not mon.moves:
        mon.moves = [Move("はねる")]  # デフォルトの技を設定
