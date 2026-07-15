"""技データ定義モジュール。

Note:
    技データは五十音の行ごとに `data/moves/` 以下のモジュールに分割されている
    （scripts/sort_data/sort_moves.py が並び替えを行う）。
    このモジュールはそれらを統合し、後方互換のため引き続き `MOVES` を提供する。
"""
import json
from importlib import resources

from jpoke.types import MoveName

from .models import MoveData

from .moves.move_symbol import MOVES_SYMBOL
from .moves.move_a import MOVES_A
from .moves.move_ka import MOVES_KA
from .moves.move_sa import MOVES_SA
from .moves.move_ta import MOVES_TA
from .moves.move_na import MOVES_NA
from .moves.move_ha import MOVES_HA
from .moves.move_ma import MOVES_MA
from .moves.move_ya import MOVES_YA
from .moves.move_ra import MOVES_RA
from .moves.move_wa import MOVES_WA


def resource_path(*path_parts: str) -> str:
    """リソースファイルのパスを取得する。"""
    return str(resources.files("jpoke").joinpath(*path_parts))


_CATEGORY_MAP = {"Physical": "physical", "Special": "special", "Status": "status"}


def _load_ps_champ_moves() -> dict[str, dict]:
    with open(resource_path("data", "ps_champ_moves.json"), encoding="utf-8") as f:
        return json.load(f)


def common_setup() -> None:
    """
    全ての技に静的パラメータ（ps-champ-jaでカバーされる技のみ）とハンドラ登録に必要な
    名前を設定する。

    呼び出しタイミング: モジュール初期化時（ファイル末尾）

    Note:
        ps-champ-jaでカバーされる技（`MOVES_SYMBOL`の擬似技を除く）は、
        `type`/`category`/`pp`/`accuracy`/`priority`/`crit_ratio`を
        `data/ps_champ_moves.json`（ps-champ-jaのスナップショット）から読み込み、
        move_*.py側のリテラル値を上書きする。カバーされない技はmove_*.py側で
        明示されたリテラル値をそのまま使う（未設定ならエラーにする）。
    """
    ps_champ = _load_ps_champ_moves()
    symbol_names = set(MOVES_SYMBOL.keys())

    for name, data in MOVES.items():
        data.name = name

        if name in symbol_names:
            # 擬似技はtype=""（無効化を表す）等の固有表現を使うため検証・json読み込みの対象外
            if data.target == "":
                data.target = "foe"
            continue

        p = ps_champ.get(name)
        if p is None:
            assert data.type and data.category and data.pp, f"{name}: 静的パラメータが未設定"
            if data.target == "":
                data.target = "foe"
            continue

        data.exist = True
        data.type = p["type"]
        data.category = _CATEGORY_MAP[p["category"]]
        data.pp = p["pp"]
        data.accuracy = p["accuracy"]
        data.priority = p["priority"]
        if data.power is None:
            data.power = p["power"]
        if data.crit_ratio != 3:
            data.crit_ratio = 1 if p["critRatio"] >= 2 else 0
        if data.target == "":
            data.target = "foe"


MOVES: dict[MoveName, MoveData] = {
    **MOVES_SYMBOL,
    **MOVES_A,
    **MOVES_KA,
    **MOVES_SA,
    **MOVES_TA,
    **MOVES_NA,
    **MOVES_HA,
    **MOVES_MA,
    **MOVES_YA,
    **MOVES_RA,
    **MOVES_WA,
}


common_setup()
