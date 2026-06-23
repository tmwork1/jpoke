from jpoke.core import Battle, Player, EventContext, AttackContext
from jpoke.model import Pokemon, Move
from jpoke.utils.type_defs import AilmentName, VolatileName, WeatherName, TerrainName, GlobalFieldName, SideFieldName
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


def start_battle(team0: list[Pokemon],
                 team1: list[Pokemon],
                 ailment0: tuple[AilmentName, int | None] | None = None,
                 ailment1: tuple[AilmentName, int | None] | None = None,
                 volatile0: dict[VolatileName, int] | None = None,
                 volatile1: dict[VolatileName, int] | None = None,
                 weather: tuple[WeatherName, int] | None = None,
                 terrain: tuple[TerrainName, int] | None = None,
                 field: dict[GlobalFieldName, int] | None = None,
                 side0: dict[SideFieldName, int] | None = None,
                 side1: dict[SideFieldName, int] | None = None,
                 accuracy: int | None = None,
                 secondary_chance: float | None = None) -> Battle:
    """バトルを初期化し、指定された状態でセットアップする。

    Args:
        team0: 味方のポケモンリスト
        team1: 相手のポケモンリスト
        ailment0: 味方の状態異常のタプル(名前, カウント)（Noneの場合は状態異常なし）
        ailment1: 相手の状態異常のタプル(名前, カウント)（Noneの場合は状態異常なし）
        volatile0: 味方の揮発効果の辞書{名前: カウント}（Noneの場合は効果なし）
        volatile1: 相手の揮発効果の辞書{名前: カウント}（Noneの場合は効果なし）
        weather: 初期天候のタプル(天候名, カウント)（Noneの場合は天候なし）
        terrain: 初期地形のタプル(地形名, カウント)（Noneの場合は地形なし）
        side0: 味方のサイドに設置する場の効果の辞書{名前: レイヤー数}（Noneの場合は効果なし）
        side1: 相手のサイドに設置する場の効果の辞書{名前: レイヤー数}（Noneの場合は効果なし）
        field: グローバルフィールドに設置する場の効果の辞書{名前: カウント}（Noneの場合は効果なし）
        accuracy: 固定命中率（Noneの場合は通常計算、デフォルト: None）
        secondary_chance: 追加効果確率の固定値（1.0=必ず発動, 0.0=発動しない, Noneの場合は通常計算）

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
            name, count = ailments[idx]
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

    # 追加効果確率の設定
    if secondary_chance is not None:
        battle.test_option.secondary_chance = secondary_chance

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


def build_context(battle: Battle, atk_idx: int, move_idx: int = 0) -> AttackContext:
    """AttackContextを構築するヘルパー関数。"""
    attacker = battle.actives[atk_idx]
    defender = battle.foe(attacker)
    move = attacker.moves[move_idx]
    return AttackContext(attacker=attacker, defender=defender, move=move)


def run_move(battle: Battle, atk_idx: int, move_idx: int = 0) -> Move:
    """技を実行するヘルパー関数。

    Args:
        battle: Battleインスタンス
        atk_idx: 技を使用するポケモンのインデックス
        move_idx: 使用する技のインデックス（デフォルト: 0）

    Returns:
        使用した技のインスタンス
    """
    attacker = battle.actives[atk_idx]
    move = attacker.moves[move_idx]
    battle.run_move(attacker, move)
    battle.print_logs()
    return move


def run_switch(battle: Battle, player_idx: int, new_idx: int) -> Pokemon:
    """ポケモンを入れ替えるヘルパー関数。

    Args:
        battle: Battleインスタンス
        player_idx: 入れ替えるプレイヤーのインデックス
        new_idx: 入れ替えるポケモンのインデックス

    Returns:
        入れ替えたポケモンのインスタンス
    """
    player = battle.players[player_idx]
    mon = battle.player_states[player].team[new_idx]
    battle.run_switch(player, mon)
    return mon


def can_switch(battle: Battle, player_idx: int) -> bool:
    """ポケモンを入れ替え可能か判定するヘルパー関数。

    Args:
        battle: Battleインスタンス
        player_idx: 判定するプレイヤーのインデックス

    Returns:
        入れ替え可能かどうか
    """
    player = battle.players[player_idx]
    return battle.can_switch(player)


def change_item(battle: Battle,
                mon: Pokemon,
                item_name: str,
                source: Pokemon | None = None) -> bool:
    """アイテムを変更する。

    Args:
        battle: Battleインスタンス
        mon: アイテムを変更するポケモン
        item_name: 変更後のアイテム名（空文字列の場合はアイテムを外す）
        source: アイテムを変更する原因となったポケモン（例: 交換元のポケモン、技の使用者など）

    Returns:
        アイテムの変更が成功したかどうか
    """
    if mon.has_item(item_name):
        return True

    if not mon.has_item():
        return battle.gain_item(mon, item_name)

    if not item_name:
        return battle.remove_item(mon, source=source)

    if not battle.can_change_item(mon, source=source):
        return False

    battle.item_manager._change_item(mon, item_name)
    return True


def end_turn(battle: Battle):
    """ターンを終了するヘルパー関数。"""
    battle.events.emit(Event.ON_TURN_END)


def apply_ailment(battle: Battle,
                  active_index: int,
                  ailment_name: AilmentName,
                  count: int = 1,
                  by_foe: bool = False,
                  overwrite: bool = False) -> bool:
    """状態異常を適用するヘルパー関数。

    Args:
        battle: Battleインスタンス
        active_index: 状態異常を適用するポケモンのインデックス
        ailment_name: 適用する状態異常の名前
        count: 状態異常のカウント（デフォルト: 1）
        by_foe: 相手によって状態異常が適用されたかどうか（デフォルト: False）
        overwrite: 既存の状態異常を上書きするかどうか（デフォルト: False）

    Returns:
        状態異常の適用が成功したかどうか
    """
    mon = battle.actives[active_index]
    source = battle.foe(mon) if by_foe else None
    return battle.ailment_manager.apply(
        mon, ailment_name, count=count, source=source, overwrite=overwrite
    )


def get_action_order(battle: Battle,
                     command0: Command | None = None,
                     command1: Command | None = None) -> list[Pokemon]:
    """行動順を取得するヘルパー関数。

    Args:
        battle: Battleインスタンス
        command0: プレイヤー0のコマンド（Noneの場合はプレイヤーが選択）
        command1: プレイヤー1のコマンド（Noneの場合はプレイヤーが選択）

    Returns:
        行動順のポケモンのリスト
    """
    reserve_command(battle, command0, command1)
    return battle.resolve_action_order()


def fix_damage(battle: Battle, damage: int):
    """ダメージ計算のダイスロールを固定値にする。

    Args:
        battle: Battleインスタンス
        damage: 固定するダメージ値
    """
    battle.roll_damage = lambda *args, **kwargs: damage


def fix_random(battle: Battle, value: float):
    """乱数を固定する

    Args:
        battle: Battleインスタンス
        value: 固定する乱数の値（0.0以上1.0未満）
    """
    battle.random.random = lambda: value


def calc_move_priority(battle: Battle, player_index: int, move_index: int = 0) -> int:
    """技を発動したときの優先度を返す

    Args:
        battle: Battleインスタンス
        player_index: 技を使用するポケモンのインデックス
        move_index: 使用する技のインデックス（デフォルト: 0）

    Returns:
        技の優先度
    """
    mon = battle.actives[player_index]
    move = mon.moves[move_index]
    return battle.speed_calculator.calc_move_priority(mon, move)
