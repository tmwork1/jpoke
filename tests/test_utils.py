from jpoke.core import Battle, Player, BattleContext
from jpoke.model import Pokemon
from jpoke.utils.type_defs import VolatileName, Weather, Terrain
from jpoke.enums import Event, Command

# 定数定義
DEFAULT_DURATION = 999  # フィールド効果のデフォルト継続ターン数
DEFAULT_POKEMON = "ピカチュウ"  # デフォルトのポケモン種族名


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


def start_battle(ally: list[Pokemon] | None = None,
                 foe: list[Pokemon] | None = None,
                 turn: int = 0,
                 weather: tuple[Weather, int] | None = None,
                 terrain: tuple[Terrain, int] | None = None,
                 ally_volatile: dict[VolatileName, int] | None = None,
                 foe_volatile: dict[VolatileName, int] | None = None,
                 ally_side_field: dict[str, int] | None = None,
                 foe_side_field: dict[str, int] | None = None,
                 global_field: dict[str, int] | None = None,
                 accuracy: int | None = 100) -> Battle:
    """バトルを初期化し、指定された状態でセットアップする。

    Args:
        ally: 味方のポケモンリスト（Noneの場合はデフォルトポケモン）
        foe: 相手のポケモンリスト（Noneの場合はデフォルトポケモン）
        turn: 開始前に進めるターン数（デフォルト: 0）
        weather: 初期天候のタプル(天候名, カウント)（Noneの場合は天候なし）
        terrain: 初期地形のタプル(地形名, カウント)（Noneの場合は地形なし）
        ally_volatile: 味方の場に付与する揮発効果の辞書{名前: カウント}（Noneの場合は効果なし）
        foe_volatile: 相手の場に付与する揮発効果の辞書{名前: カウント}（Noneの場合は効果なし）
        ally_side_field: 味方のサイドに設置する場の効果の辞書{名前: レイヤー数}（Noneの場合は効果なし）
        foe_side_field: 相手のサイドに設置する場の効果の辞書{名前: レイヤー数}（Noneの場合は効果なし）
        global_field: グローバルフィールドに設置する場の効果の辞書{名前: カウント}（Noneの場合は効果なし）
        accuracy: 固定命中率（Noneの場合は通常計算、デフォルト: 100）

    Returns:
        Battle: セットアップ済みのBattleインスタンス
    """
    # プレイヤーとバトルのセットアップ
    if not ally:
        ally = [Pokemon(DEFAULT_POKEMON)]
    if not foe:
        foe = [Pokemon(DEFAULT_POKEMON)]

    players = [CustomPlayer() for _ in range(2)]
    for player, mons in zip(players, [ally, foe]):
        for mon in mons:
            player.team.append(mon)

    battle = Battle(players)

    # 0ターン目の進行
    battle.advance_turn()
    battle.print_logs()

    # 天候・地形の有効化
    if weather:
        name, weather_count = weather
        battle.weather_manager.activate(name, weather_count)
    if terrain:
        name, terrain_count = terrain
        battle.terrain_manager.activate(name, terrain_count)

    # 命中率の設定
    if accuracy is not None:
        battle.test_option.accuracy = accuracy

    # サイドフィールドの有効化（初期ターン後に実行してポケモンへのダメージを回避）
    if ally_side_field:
        for name, layers in ally_side_field.items():
            battle.side_manager[0].fields[name].activate(battle, DEFAULT_DURATION)
            battle.side_manager[0].fields[name].count = layers
    if foe_side_field:
        for name, layers in foe_side_field.items():
            battle.side_manager[1].fields[name].activate(battle, DEFAULT_DURATION)
            battle.side_manager[1].fields[name].count = layers

    # グローバルフィールドの有効化
    if global_field:
        for name, count in global_field.items():
            battle.field_manager.fields[name].activate(battle, count)

    # 揮発効果の適用
    if ally_volatile or foe_volatile:
        volatiles = [ally_volatile, foe_volatile]
        for idx, mon in enumerate(battle.actives):
            if not volatiles[idx]:
                continue
            for name, count in volatiles[idx].items():
                mon.apply_volatile(battle, name, count=count)

    # ターン進行
    for _ in range(turn):
        battle.advance_turn()
        battle.print_logs()
        if battle.judge_winner():
            break

    return battle


def get_try_result(battle: Battle,
                   event: Event,
                   atk_idx: int = 0) -> bool:
    attacker = battle.actives[atk_idx]
    defender = battle.actives[1 - atk_idx]
    result = battle.events.emit(
        event,
        BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        True,
    )
    return result


def calc_damage_modifier(battle: Battle,
                         event: Event,
                         base: int = 4096,
                         atk_idx: int = 0) -> int:
    """ダメージ計算の補正値を検証するヘルパー関数。"""
    attacker = battle.actives[atk_idx]
    defender = battle.actives[1 - atk_idx]
    return battle.events.emit(
        event,
        BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        base
    )


def calc_accuracy(battle: Battle,
                  base: float = 100,
                  atk_idx: int = 0):
    """命中率補正値を検証するヘルパー関数。"""
    attacker = battle.actives[atk_idx]
    defender = battle.actives[1 - atk_idx]
    return battle.events.emit(
        Event.ON_MODIFY_ACCURACY,
        BattleContext(attacker=attacker, defender=defender, move=attacker.moves[0]),
        base
    )


def reserve_command(battle: Battle):
    """各プレイヤーがコマンドを予約した状態にする

    Args:
        battle: Battleインスタンス
    """
    for player in battle.players:
        player.init_turn()
        command = player.choose_action_command(battle)
        player.reserve_command(command)


def can_switch(battle: Battle, idx: int = 0) -> bool:
    """指定されたプレイヤーが交代可能かチェックする。

    Args:
        battle: Battleインスタンス
        idx: プレイヤーのインデックス（0または1）

    Returns:
        bool: 交代可能な場合True、そうでない場合False

    Raises:
        IndexError: 無効なプレイヤーインデックスが指定された場合
    """
    if not (0 <= idx < len(battle.players)):
        raise IndexError(f"Invalid player index: {idx}. Must be between 0 and {len(battle.players) - 1}")
    commands = battle.get_available_action_commands(battle.players[idx])
    return any(c.is_switch() for c in commands)


def assert_log_contains(battle: Battle, text: str, player_idx: int | None = None, turn: int | None = None):
    """指定したテキストがログに含まれていることを検証する。

    Args:
        battle: Battleインスタンス
        text: ログに含まれるべきテキスト
        player_idx: プレイヤーのインデックス（Noneの場合は全プレイヤー）
        turn: ターン番号（Noneの場合は現在のターン）

    Raises:
        AssertionError: ログにテキストが含まれていない場合
    """
    if turn is None:
        turn = battle.turn

    event_logs = battle.get_event_logs(turn)

    if player_idx is not None:
        # 特定プレイヤーのログをチェック
        player = battle.players[player_idx]
        logs = event_logs.get(player, [])
        assert any(text in log for log in logs), f"Log does not contain '{text}'. Logs: {logs}"
    else:
        # 全プレイヤーのログをチェック
        all_logs = []
        for logs in event_logs.values():
            all_logs.extend(logs)
        assert any(text in log for log in all_logs), f"Log does not contain '{text}'. Logs: {all_logs}"


def assert_log_not_contains(battle: Battle, text: str, player_idx: int | None = None, turn: int | None = None):
    """指定したテキストがログに含まれていないことを検証する。

    Args:
        battle: Battleインスタンス
        text: ログに含まれるべきでないテキスト
        player_idx: プレイヤーのインデックス（Noneの場合は全プレイヤー）
        turn: ターン番号（Noneの場合は現在のターン）

    Raises:
        AssertionError: ログにテキストが含まれている場合
    """
    if turn is None:
        turn = battle.turn

    event_logs = battle.get_event_logs(turn)

    if player_idx is not None:
        # 特定プレイヤーのログをチェック
        player = battle.players[player_idx]
        logs = event_logs.get(player, [])
        assert not any(text in log for log in logs), f"Log should not contain '{text}'. Logs: {logs}"
    else:
        # 全プレイヤーのログをチェック
        all_logs = []
        for logs in event_logs.values():
            all_logs.extend(logs)
        assert not any(text in log for log in all_logs), f"Log should not contain '{text}'. Logs: {all_logs}"
