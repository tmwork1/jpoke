"""テストヘルパーの薄い再エクスポート層。

大半の実体は `jpoke.testing`（本体パッケージへ昇格済み）に移設した。既存テストコードの
`from . import test_utils as t` / `from .. import test_utils as t` という参照パターンを
壊さないための後方互換シムとして残している。新規コードは `jpoke.testing` を直接
参照してよい。

`fix_damage` / `fix_random` は対戦オブジェクトの内部属性を直接差し替えるデバッグ用
モンキーパッチであり、本番の対戦進行（bot 運用等）では使わないこと。`jpoke.testing`
はAPI安定性が求められる公開パッケージのため、この2つはリポジトリ内テスト専用として
本ファイルにのみ実装する。
"""
from jpoke import Battle
from jpoke.testing import (
    CustomPlayer,
    start_battle,
    reserve_command,
    build_context,
    run_move,
    run_switch,
    can_switch,
    change_item,
    end_turn,
    apply_ailment,
    get_action_order,
    calc_lethal,
    calc_move_priority,
)

__all__ = [
    "CustomPlayer",
    "start_battle",
    "reserve_command",
    "build_context",
    "run_move",
    "run_switch",
    "can_switch",
    "change_item",
    "end_turn",
    "apply_ailment",
    "get_action_order",
    "fix_damage",
    "fix_random",
    "calc_lethal",
    "calc_move_priority",
]


def fix_damage(battle: Battle, damage: int):
    """ダメージ計算のダイスロールを固定値にする。

    テスト・デバッグ専用のユーティリティであり、本番の対戦進行では使わないこと。
    `Battle.roll_damage` を差し替えるモンキーパッチのため、以降そのBattleインスタンスの
    ダメージ計算は全て固定値になる。

    Args:
        battle: Battleインスタンス
        damage: 固定するダメージ値
    """
    battle.roll_damage = lambda *args, **kwargs: damage


def fix_random(battle: Battle, value: float):
    """乱数を固定する。

    テスト・デバッグ専用のユーティリティであり、本番の対戦進行では使わないこと。
    `Battle.random.random` を差し替えるモンキーパッチのため、以降そのBattleインスタンスの
    `random()` 呼び出しは全て固定値になる（`choice`/`randint`/`shuffle`等の他のメソッドには
    効果がない点に注意）。

    Args:
        battle: Battleインスタンス
        value: 固定する乱数の値（0.0以上1.0未満）
    """
    battle.random.random = lambda: value
