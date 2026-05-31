from jpoke.core import Battle, Player, EventContext
from jpoke.model import Pokemon, Move
from jpoke.utils.type_defs import AilmentName, VolatileName, Weather, Terrain, GlobalField, SideField
from jpoke.enums import Event, Command, LogCode


class CustomPlayer(Player):
    """テスト用のカスタムプレイヤークラス。

    常に利用可能な最初のコマンドを選択します。
    """

    def choose_selection_commands(self, battle: Battle) -> list[Command]:
        """選出コマンドを選択する。"""
        return battle.get_available_selection_commands(self)

    def choose_action_command(self, battle: Battle) -> Command:
        """行動コマンドを選択する（常に最初の利用可能なコマンド）。"""
        return battle.get_available_action_commands(self)[0]


def build_context(battle: Battle, atk_idx: int = 0, move_idx: int = 0) -> EventContext:
    """EventContextを構築するヘルパー関数。"""
    attacker = battle.actives[atk_idx]
    defender = battle.foe(attacker)
    move = attacker.moves[move_idx]
    return EventContext(attacker=attacker, defender=defender, move=move)


def run_move(battle: Battle, atk_idx: int, move_idx: int = 0) -> Move:
    attacker = battle.actives[atk_idx]
    move = attacker.moves[move_idx]
    battle.run_move(attacker, move)
    battle.print_logs()
    return move


def run_switch(battle: Battle, player_idx: int, new_idx: int) -> Pokemon:
    player = battle.players[player_idx]
    mon = battle.player_states[player].team[new_idx]
    battle.run_switch(player, mon)
    return mon


def start_battle(team0: list[Pokemon],
                 team1: list[Pokemon],
                 ailment0: dict[AilmentName, int] | None = None,
                 ailment1: dict[AilmentName, int] | None = None,
                 volatile0: dict[VolatileName, int] | None = None,
                 volatile1: dict[VolatileName, int] | None = None,
                 weather: tuple[Weather, int] | None = None,
                 terrain: tuple[Terrain, int] | None = None,
                 field: dict[GlobalField, int] | None = None,
                 side0: dict[SideField, int] | None = None,
                 side1: dict[SideField, int] | None = None,
                 accuracy: int | None = None) -> Battle:
    """バトルを初期化し、指定された状態でセットアップする。

    Args:
        team0: 味方のポケモンリスト
        team1: 相手のポケモンリスト
        ailment0: 味方の状態異常の辞書{名前: カウント}（Noneの場合は状態異常なし）
        ailment1: 相手の状態異常の辞書{名前: カウント}（Noneの場合は状態異常なし）
        volatile0: 味方の揮発効果の辞書{名前: カウント}（Noneの場合は効果なし）
        volatile1: 相手の揮発効果の辞書{名前: カウント}（Noneの場合は効果なし）
        weather: 初期天候のタプル(天候名, カウント)（Noneの場合は天候なし）
        terrain: 初期地形のタプル(地形名, カウント)（Noneの場合は地形なし）
        side0: 味方のサイドに設置する場の効果の辞書{名前: レイヤー数}（Noneの場合は効果なし）
        side1: 相手のサイドに設置する場の効果の辞書{名前: レイヤー数}（Noneの場合は効果なし）
        field: グローバルフィールドに設置する場の効果の辞書{名前: カウント}（Noneの場合は効果なし）
        accuracy: 固定命中率（Noneの場合は通常計算、デフォルト: None）

    Returns:
        Battle: セットアップ済みのBattleインスタンス
    """
    # プレイヤーとバトルのセットアップ
    if not team0:
        raise ValueError("ally must contain at least one Pokemon")
    if not team1:
        raise ValueError("foe must contain at least one Pokemon")

    players = (CustomPlayer("Player 1"), CustomPlayer("Player 2"))
    for player, mons in zip(players, [team0, team1]):
        for mon in mons:
            player.team.append(mon)

    battle = Battle(players)
    battle.start()

    if ailment0 or ailment1:
        ailments = [ailment0, ailment1]
        for idx, mon in enumerate(battle.actives):
            if not ailments[idx]:
                continue
            for name, count in ailments[idx].items():
                battle.ailment_manager.apply(mon, name, count=count)

    # 揮発効果の適用
    if volatile0 or volatile1:
        volatiles = [volatile0, volatile1]
        for idx, mon in enumerate(battle.actives):
            if not volatiles[idx]:
                continue
            for name, count in volatiles[idx].items():
                battle.volatile_manager.apply(mon, name, count=count)

    # 天候の有効化
    if weather:
        name, weather_count = weather
        battle.weather_manager.apply(name, weather_count)

    # 地形の有効化
    if terrain:
        name, terrain_count = terrain
        battle.terrain_manager.apply(name, terrain_count)

    # グローバルフィールドの有効化
    if field:
        for name, count in field.items():
            battle.global_manager.activate(name, count)

    # サイドフィールドの有効化（初期ターン後に実行してポケモンへのダメージを回避）
    if side0:
        for name, layers in side0.items():
            battle.side_managers[0].activate(name, layers)
    if side1:
        for name, layers in side1.items():
            battle.side_managers[1].activate(name, layers)

    # 命中率の設定
    if accuracy is not None:
        battle.test_option.accuracy = accuracy

    battle.print_logs()

    return battle


def reserve_command(battle: Battle,
                    command0: Command | None = None,
                    command1: Command | None = None):
    """各プレイヤーがコマンドを予約した状態にする

    Args:
        battle: Battleインスタンス
    """
    commands = [command0, command1]
    for i, (player, state) in enumerate(battle.player_states.items()):
        state.reset_turn_state()
        command = commands[i]
        if command is None:
            command = player.choose_action_command(battle)
        state.reserve_command(command)


def end_turn(battle: Battle):
    battle.events.emit(Event.ON_TURN_END)
