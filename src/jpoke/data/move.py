"""技データ定義モジュール。

Note:
    技データは五十音の行ごとに `data/moves/` 以下のモジュールに分割されている
    （scripts/sort_data/sort_moves.py が並び替えを行う）。
    このモジュールはそれらを統合し、後方互換のため引き続き `MOVES` を提供する。
"""
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


def common_setup() -> None:
    """
    全ての技に共通ハンドラを追加する。

    この関数は、MOVESディクショナリ内の全てのMoveDataに対して、
    呼び出しタイミング: モジュール初期化時（ファイル末尾）

    Note:
        dictインスタンスはスキップされます（MoveDataオブジェクトのみ処理）
    """
    for name, data in MOVES.items():
        data.name = name


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
