"""盤面・コマンドを人間可読テキストに整形する公開API。

CLI・LLM・ログ・デバッグなど「盤面の状態やコマンドを文字列で見たい」という
用途は共通のため、`players/cli_player.py` に埋もれていた整形ロジックを
本モジュールへ切り出したもの。`jpoke/testing.py` と同格のトップレベル
モジュールとして扱う。

循環import回避のため、ランタイムでは `jpoke.enums` 以外を import しない
（`jpoke.core` / `jpoke.model` の型は `TYPE_CHECKING` 配下でのみ import する）。
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from jpoke.enums import Command

if TYPE_CHECKING:
    from jpoke.core import Battle, Player
    from jpoke.model import Pokemon

__all__ = [
    "describe_pokemon",
    "describe_command",
    "render_battle_state",
]


def describe_pokemon(mon: Pokemon | None) -> str:
    """ポケモン1体のHP・状態異常・ランク補正・テラスタル状況を1行で表す。"""
    if mon is None:
        return "(場に出ていない)"

    hp = f"HP {mon.hp}/{mon.max_hp}"
    ailment = f" 状態異常:{mon.ailment.name}" if mon.ailment.is_active else ""
    boosts = ", ".join(f"{stat}{v:+d}" for stat, v in mon.boosts.items() if v != 0)
    boost_str = f" ランク:[{boosts}]" if boosts else ""
    tera = f" (テラス:{mon.tera_type})" if mon.is_terastallized else ""
    return f"{mon.name}{tera} {hp}{ailment}{boost_str}"


def describe_command(battle: Battle, player: Player, command: Command) -> str:
    """コマンド1件を人間可読な説明文にする。"""
    if command in (Command.STRUGGLE, Command.FORCED):
        return "わるあがき" if command == Command.STRUGGLE else "強制続行"

    if command.is_switch:
        mon = battle.get_team(player)[command.index]
        return f"交代 → {mon.name} (HP {mon.hp}/{mon.max_hp})"

    move = battle.command_to_move(player, command)
    prefix = ""
    if command.is_terastal:
        prefix = "テラスタル+"
    elif command.is_megaevol:
        prefix = "メガシンカ+"
    elif command.is_gigamax:
        prefix = "ダイマックス+"
    elif command.is_zmove:
        prefix = "Z+"
    power = move.base_power if move.base_power is not None else "-"
    return (f"{prefix}{move.name} (タイプ:{move.type} 分類:{move.category} "
            f"威力:{power} PP:{move.pp}/{move.max_pp})")


def render_battle_state(battle: Battle, viewer: Player, *, include_logs: bool = True) -> list[str]:
    """盤面（ターン数・自分/相手のポケモン・天候・フィールド・場の状態）を行リストで返す。

    `choose_command()` に渡される battle は観測コピーであり、相手ポケモンは
    性格・努力値がマスク値に差し替えられたうえで **HP割合を保って最大HPが
    再計算**されている（`core/observation_builder.py` 参照）。したがって
    表示される相手の `hp/max_hp` の**絶対値は真値ではなく、割合のみが正しい**。
    特性・アイテムも未公開なら空インスタンスに差し替えられている。

    Args:
        battle: 対象の対戦オブジェクト
        viewer: 表示視点となるプレイヤー（`battle.observer` には依存しない）
        include_logs: Trueの場合、先頭に現在ターン分のログ（`battle.get_log_lines()`）
            を含める

    Returns:
        list[str]: 整形済みの行リスト。出力先（print / logging 等）は
            呼び出し側に委ねる
    """
    lines: list[str] = ["", f"=== ターン{battle.turn} : {viewer.username} ==="]
    if include_logs:
        lines.extend(battle.get_log_lines())

    opponent = battle.opponent(viewer)
    lines.append(f"[自分] {describe_pokemon(battle.get_active(viewer))}")
    lines.append(f"[相手] {describe_pokemon(battle.get_active(opponent))}")

    weather, terrain = battle.weather, battle.terrain
    if weather.is_active:
        lines.append(f"天候: {weather.name}")
    if terrain.is_active:
        lines.append(f"フィールド: {terrain.name}")

    for label, side_player in ((viewer.username, viewer), (opponent.username, opponent)):
        active_fields = [f.name for f in battle.active_side_fields(side_player)]
        if active_fields:
            lines.append(f"{label}側の場の状態: {', '.join(active_fields)}")

    return lines
