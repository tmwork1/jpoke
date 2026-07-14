"""状態異常/揮発性状態/場の状態を誘発する技・特性・アイテムの集合を、
`src/jpoke/handlers/*.py`（ハンドラ実装）と `src/jpoke/data/*.py`（登録側）の
ソースコードを静的解析（ast）して機械的に求めるモジュール。

判定基準:
    ハンドラ関数（の呼び出しグラフの先）が以下のいずれかを直接呼び出している場合、
    そのハンドラが登録されている技/特性/アイテムを「誘発系」とみなす。
        - battle.ailment_manager.apply(...)                    -> 状態異常
        - battle.volatile_manager.apply(...) / .apply_confusion(...) -> 揮発性状態
        - battle.weather_manager.apply(...) / battle.terrain_manager.apply(...) -> 天候/地形
        - battle.global_manager.activate(...)                  -> グローバル場の状態
          （`manager = battle.global_manager` のようなローカル変数エイリアス経由の
          呼び出しも検出する）
        - battle.get_side(...).apply(...) / .activate(...)     -> サイドフィールド状態
          （`side = battle.get_side(...)` のようなローカル変数エイリアス経由の
          呼び出しも検出する）

    ハンドラ本体が上記を直接呼ばず、別関数（内部ヘルパーや、`handlers/move.py` の
    `apply_ailment_to_defender` のように `from .move import ...` で他の handlers
    モジュールから読み込んだ共通ヘルパー）を経由して間接的に呼んでいる場合も、
    handlers パッケージ全体の呼び出しグラフを辿って誘発系として検出する
    （例: `handlers/ability.py` の `_apply_contact_counter_ailment` を複数の
    接触反撃系特性ハンドラが呼び出している。`handlers/move_status.py` の
    `どくどく_apply_ailment_to_defender` は `handlers/move.py` の
    `apply_ailment_to_defender` を呼び出している）。

    技名/特性名/アイテム名の一覧そのものは対応する `data/*.py` の辞書リテラル
    （文字列キー）を機械的に走査して求める。当て推量による名前リストのハード
    コーディングは行わない。

fuzz_log_battle.py だけがこのモジュールが提供する集合を
`fuzz_common.random_team_spec(..., effect_bias=...)` 経由で使う
（fuzz_battle.py / replay_fuzz_battle.py は使わず、既定の一様ランダム挙動を保つ）。
"""

from __future__ import annotations

import ast
from functools import lru_cache
from pathlib import Path

_SRC_ROOT = Path(__file__).resolve().parent.parent.parent / "src" / "jpoke"
_HANDLERS_DIR = _SRC_ROOT / "handlers"

# battle.<attr>.<method>(...) の直接呼び出しで「誘発」とみなす対応表
_DIRECT_MANAGER_METHODS: dict[str, set[str]] = {
    "ailment_manager": {"apply"},
    "volatile_manager": {"apply", "apply_confusion"},
    "weather_manager": {"apply"},
    "terrain_manager": {"apply"},
    "global_manager": {"activate"},
}
# ローカル変数エイリアス経由で呼び出された場合に「誘発」とみなすメソッド名
_ALIAS_METHODS = {"apply", "activate"}


def _collect_local_aliases(func: ast.FunctionDef) -> tuple[set[str], set[str]]:
    """`manager = battle.global_manager` / `side = battle.get_side(...)` のような
    ローカル変数エイリアスを収集する。

    Returns:
        (global_field_aliases, side_field_aliases) のタプル
    """
    global_field_aliases: set[str] = set()
    side_field_aliases: set[str] = set()

    for node in ast.walk(func):
        if not (isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)):
            continue
        target_name = node.targets[0].id
        value = node.value
        if isinstance(value, ast.Attribute) and value.attr == "global_manager":
            global_field_aliases.add(target_name)
        elif (isinstance(value, ast.Call)
              and isinstance(value.func, ast.Attribute)
              and value.func.attr == "get_side"):
            side_field_aliases.add(target_name)

    return global_field_aliases, side_field_aliases


def _has_direct_induce_call(func: ast.FunctionDef) -> bool:
    """関数本体が状態異常/揮発性状態/場の状態を発生させる呼び出しを直接含むか判定する。"""
    global_field_aliases, side_field_aliases = _collect_local_aliases(func)

    for node in ast.walk(func):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue
        call = node.func
        method = call.attr
        base = call.value

        # 直接呼び出し: battle.<manager>.<method>(...)
        if isinstance(base, ast.Attribute) and base.attr in _DIRECT_MANAGER_METHODS:
            if method in _DIRECT_MANAGER_METHODS[base.attr]:
                return True
            continue

        # エイリアス経由: manager = battle.global_manager ; manager.activate(...)
        #              side = battle.get_side(...)        ; side.apply(...) / .activate(...)
        if isinstance(base, ast.Name) and method in _ALIAS_METHODS:
            if base.id in global_field_aliases or base.id in side_field_aliases:
                return True

    return False


def _handler_module_names() -> list[str]:
    """`handlers/` 直下のモジュール名（`__init__` を除く）一覧。"""
    return sorted(p.stem for p in _HANDLERS_DIR.glob("*.py") if p.stem != "__init__")


def _local_import_map(tree: ast.Module, own_module: str) -> dict[str, tuple[str, str]]:
    """モジュール内で `from .X import a, b as c` / `from jpoke.handlers.X import ...`
    で読み込んだ名前 -> (X, 元の名前) の対応表を作る（handlersパッケージ内のみ対象）。
    """
    handler_modules = set(_handler_module_names())
    mapping: dict[str, tuple[str, str]] = {}
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom):
            continue
        module = node.module or ""
        # 相対import（from .move import ...）と絶対import（from jpoke.handlers.move import ...）の両方に対応
        if node.level > 0:
            target_module = module
        elif module.startswith("jpoke.handlers."):
            target_module = module[len("jpoke.handlers."):]
        else:
            continue
        if target_module not in handler_modules or target_module == own_module:
            continue
        for alias in node.names:
            mapping[alias.asname or alias.name] = (target_module, alias.name)
    return mapping


@lru_cache(maxsize=None)
def _project_inducing_functions() -> dict[str, frozenset[str]]:
    """handlers パッケージ全体を解析し、モジュール名 -> 「誘発系」関数名の集合を返す。

    ハンドラ本体が直接 manager 呼び出しを含む関数だけでなく、同一モジュール内の
    ヘルパーや、`from .move import ...` のように他の handlers モジュールから
    読み込んだ共通ヘルパーを経由して間接的に誘発する関数も、パッケージ全体の
    呼び出しグラフを辿って含める。
    """
    module_names = _handler_module_names()
    trees: dict[str, ast.Module] = {
        name: ast.parse((_HANDLERS_DIR / f"{name}.py").read_text(encoding="utf-8-sig"))
        for name in module_names
    }
    # モジュール名 -> {関数名: FunctionDefノード}
    funcs_by_module: dict[str, dict[str, ast.FunctionDef]] = {
        name: {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
        for name, tree in trees.items()
    }
    # モジュール名 -> {ローカル名: (呼び出し先モジュール, 呼び出し先関数名)}（他モジュールからのimport分）
    import_maps: dict[str, dict[str, tuple[str, str]]] = {
        name: _local_import_map(tree, name) for name, tree in trees.items()
    }

    direct: set[tuple[str, str]] = {
        (module, name)
        for module, funcs in funcs_by_module.items()
        for name, node in funcs.items()
        if _has_direct_induce_call(node)
    }

    # 呼び出しグラフ: (モジュール, 関数名) -> 呼び出す (モジュール, 関数名) の集合
    # （同一モジュール内の関数呼び出し・他モジュールからimportした関数呼び出しの両方を解決する）
    calls: dict[tuple[str, str], set[tuple[str, str]]] = {}
    for module, funcs in funcs_by_module.items():
        own_funcs = funcs
        imported = import_maps[module]
        for name, node in funcs.items():
            called: set[tuple[str, str]] = set()
            for sub in ast.walk(node):
                if not (isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name)):
                    continue
                callee_id = sub.func.id
                if callee_id in own_funcs and callee_id != name:
                    called.add((module, callee_id))
                elif callee_id in imported:
                    target_module, target_name = imported[callee_id]
                    if target_name in funcs_by_module.get(target_module, {}):
                        called.add((target_module, target_name))
            calls[(module, name)] = called

    # 誘発関数を（間接的にでも）呼ぶ関数を誘発扱いにする（不動点に達するまで伝播）
    inducing = set(direct)
    changed = True
    while changed:
        changed = False
        for key, called in calls.items():
            if key not in inducing and called & inducing:
                inducing.add(key)
                changed = True

    result: dict[str, set[str]] = {name: set() for name in module_names}
    for module, name in inducing:
        result[module].add(name)
    return {module: frozenset(names) for module, names in result.items()}


def _module_inducing_functions(filename: str) -> frozenset[str]:
    """`handlers/<filename>` 内の「誘発系」トップレベル関数名の集合を返す。"""
    module_name = filename.removesuffix(".py")
    return _project_inducing_functions().get(module_name, frozenset())


def _import_aliases(tree: ast.Module) -> dict[str, str]:
    """`from jpoke.handlers import X as alias` の alias -> X（モジュール名）対応表を作る。"""
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "jpoke.handlers":
            for alias in node.names:
                module_name = alias.name
                if (_HANDLERS_DIR / f"{module_name}.py").exists():
                    aliases[alias.asname or alias.name] = module_name
    return aliases


def _collect_inducing_entity_names(data_path: Path) -> frozenset[str]:
    """データ定義ファイル（`data/ability.py` 等）を解析し、「誘発系」ハンドラが
    1つ以上登録されているエンティティ（技/特性/アイテム）名の集合を返す。

    実体を表す `{"技名": MoveData(...), ...}` のような辞書リテラル（キーが文字列
    リテラルのdict）を機械的に検出する。`handlers={Event.X: ...}` のような内側の
    辞書（キーがEvent等でstrではない）は対象外になる。
    """
    tree = ast.parse(data_path.read_text(encoding="utf-8-sig"))
    alias_to_module = _import_aliases(tree)
    inducing_names: set[str] = set()

    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        for key, value in zip(node.keys, node.values):
            if not (isinstance(key, ast.Constant) and isinstance(key.value, str)):
                continue
            if not key.value or not isinstance(value, ast.Call):
                continue
            entity_name = key.value

            for sub in ast.walk(value):
                if not (isinstance(sub, ast.Attribute)
                        and isinstance(sub.value, ast.Name)
                        and sub.value.id in alias_to_module):
                    continue
                module_name = alias_to_module[sub.value.id]
                if sub.attr in _module_inducing_functions(f"{module_name}.py"):
                    inducing_names.add(entity_name)
                    break  # このエンティティは誘発系確定。次のsub探索は不要

    return frozenset(inducing_names)


@lru_cache(maxsize=None)
def inducing_ability_names() -> frozenset[str]:
    """状態異常/揮発性状態/場の状態を誘発するハンドラを持つ特性名の集合。"""
    return _collect_inducing_entity_names(_SRC_ROOT / "data" / "ability.py")


@lru_cache(maxsize=None)
def inducing_item_names() -> frozenset[str]:
    """状態異常/揮発性状態/場の状態を誘発するハンドラを持つアイテム名の集合。"""
    return _collect_inducing_entity_names(_SRC_ROOT / "data" / "item.py")


@lru_cache(maxsize=None)
def inducing_move_names() -> frozenset[str]:
    """状態異常/揮発性状態/場の状態を誘発するハンドラを持つ技名の集合。"""
    names: set[str] = set()
    for path in sorted((_SRC_ROOT / "data" / "moves").glob("move_*.py")):
        names |= _collect_inducing_entity_names(path)
    return frozenset(names)


if __name__ == "__main__":
    # 動作確認用: 抽出件数を表示する
    print(f"特性: {len(inducing_ability_names())}件")
    print(f"アイテム: {len(inducing_item_names())}件")
    print(f"技: {len(inducing_move_names())}件")
