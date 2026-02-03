from jpoke import Battle, Player, Pokemon
from jpoke.utils.type_defs import VolatileName, Weather, Terrain
from jpoke.utils.enums import Command

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


def start_battle(
    ally: list[Pokemon] | None = None,
    foe: list[Pokemon] | None = None,
    turn: int = 0,
    weather: tuple[Weather, int] | None = None,
    terrain: tuple[Terrain, int] | None = None,
    ally_volatile: dict[VolatileName, int] | None = None,
    foe_volatile: dict[VolatileName, int] | None = None,
    ally_side_field: dict[str, int] | None = None,
    foe_side_field: dict[str, int] | None = None,
    global_field: dict[str, int] | None = None,
    accuracy: int | None = 100,
) -> Battle:
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

    # 天候・地形の有効化
    if weather:
        weather_name, weather_count = weather
        battle.weather_mgr.activate(weather_name, weather_count)
    if terrain:
        terrain_name, terrain_count = terrain
        battle.terrain_mgr.activate(terrain_name, terrain_count)

    # 命中率の設定
    if accuracy is not None:
        battle.test_option.accuracy = accuracy

    # バトル開始（advance_turnは使わず内部フェーズを実行）
    run_turn(battle)
    battle.print_logs()

    # サイドフィールドの有効化（初期ターン後に実行してポケモンへのダメージを回避）
    if ally_side_field:
        for field_name, layers in ally_side_field.items():
            battle.side_mgrs[0].fields[field_name].activate(battle.events, DEFAULT_DURATION)
            battle.side_mgrs[0].fields[field_name].layers = layers
    if foe_side_field:
        for field_name, layers in foe_side_field.items():
            battle.side_mgrs[1].fields[field_name].activate(battle.events, DEFAULT_DURATION)
            battle.side_mgrs[1].fields[field_name].layers = layers

    # グローバルフィールドの有効化
    if global_field:
        for field_name, count in global_field.items():
            battle.field_mgr.fields[field_name].activate(battle.events, count)

    # 揮発効果の適用
    if ally_volatile or foe_volatile:
        volatiles = [ally_volatile, foe_volatile]
        for idx, mon in enumerate(battle.actives):
            if volatiles[idx]:
                for name, count in volatiles[idx].items():
                    mon.apply_volatile(battle.events, name, count=count)

    # ターン進行
    for _ in range(turn):
        run_turn(battle)
        battle.print_logs()
        if battle.winner():
            break

    return battle


def tick_fields(battle: Battle, ticks: int = 1):
    """フィールド効果のカウントを経過させる。

    Args:
        battle: Battleインスタンス
        ticks: 経過させるカウント数（デフォルト: 1）
    """
    for _ in range(ticks):
        # 天候のカウントダウン
        if battle.weather_mgr.current.is_active:
            battle.weather_mgr.tick()

        # 地形のカウントダウン
        if battle.terrain_mgr.current.is_active:
            battle.terrain_mgr.tick()

        # グローバルフィールドのカウントダウン
        for field in battle.field_mgr.fields.values():
            if field.is_active:
                battle.field_mgr.tick(field.data.name)

        # サイドフィールドのカウントダウン
        for side in battle.side_mgrs:
            for field in side.fields.values():
                if field.is_active:
                    side.tick(field.data.name)


def run_turn(battle: Battle, commands: dict[Player, Command] | None = None):
    """テスト用にターンを1つ進める。

    advance_turn() には依存せず、内部のフェーズ処理を直接呼び出す。

    Args:
        battle: Battleインスタンス
        commands: 予約するコマンド辞書（任意）
    """
    if commands:
        for player, command in commands.items():
            player.reserve_command(command)
            battle.add_command_log(player, command)

    battle.turn_controller._process_turn_phases()


def can_switch(battle: Battle, idx: int) -> bool:
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


def assert_field_active(battle: Battle, field_type: str, field_name: str, active: bool = True):
    """フィールドが有効/無効であることを検証する。

    Args:
        battle: Battleインスタンス
        field_type: フィールドタイプ ('weather', 'terrain', 'global', 'ally_side', 'foe_side')
        field_name: フィールド名
        active: 有効であるべきか（デフォルト: True）

    Raises:
        AssertionError: フィールドの状態が期待と異なる場合
    """
    if field_type == 'weather':
        is_active = battle.weather_mgr.current.is_active and battle.weather_mgr.current.data.name == field_name
    elif field_type == 'terrain':
        is_active = battle.terrain_mgr.current.is_active and battle.terrain_mgr.current.data.name == field_name
    elif field_type == 'global':
        is_active = battle.field_mgr.fields[field_name].is_active
    elif field_type == 'ally_side':
        is_active = battle.side_mgrs[0].fields[field_name].is_active
    elif field_type == 'foe_side':
        is_active = battle.side_mgrs[1].fields[field_name].is_active
    else:
        raise ValueError(f"Unknown field type: {field_type}")

    assert is_active == active, f"{field_type} field '{field_name}' should be {'active' if active else 'inactive'}, but is {'active' if is_active else 'inactive'}"


def get_field_count(battle: Battle, field_type: str, field_name: str) -> int:
    """フィールドの残りカウントを取得する。

    Args:
        battle: Battleインスタンス
        field_type: フィールドタイプ ('weather', 'terrain', 'global', 'ally_side', 'foe_side')
        field_name: フィールド名

    Returns:
        int: フィールドの残りカウント
    """
    if field_type == 'weather':
        return battle.weather_mgr.current.count if battle.weather_mgr.current.is_active else 0
    elif field_type == 'terrain':
        return battle.terrain_mgr.current.count if battle.terrain_mgr.current.is_active else 0
    elif field_type == 'global':
        return battle.field_mgr.fields[field_name].count
    elif field_type in ['ally_side', 'foe_side']:
        idx = 0 if field_type == 'ally_side' else 1
        return battle.side_mgrs[idx].fields[field_name].count
    else:
        raise ValueError(f"Unknown field type: {field_type}")


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
