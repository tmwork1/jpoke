"""jpoke 固有のドメイン例外を定義するモジュール。

ライブラリ利用者（bot開発者等）が特定の失敗理由を except しやすいように、
素の `ValueError` の代わりに使うドメイン例外をここに集約する。

後方互換のため、各例外は `JpokeError` と `ValueError` の両方を継承する
（`except ValueError` で捕捉していた既存コードを壊さない）。
"""


class JpokeError(Exception):
    """jpoke が送出するドメイン例外の基底クラス。"""


class InvalidCommandError(JpokeError, ValueError):
    """バトルに渡されたコマンドが不正、または不足している場合の例外。"""


class InvalidPhaseError(JpokeError, ValueError):
    """現在のバトルフェーズでは実行できない操作を試みた場合の例外。"""


class PokemonNotFoundError(JpokeError, ValueError):
    """指定したポケモンがバトル中の期待される位置（場・チーム等）に見つからない場合の例外。"""


class InvalidStatModificationError(JpokeError, ValueError):
    """`modify_hp` 等のステータス変更呼び出しの引数が仕様と矛盾している場合の例外。"""


class PokeApiResolveError(JpokeError, ValueError):
    """和名からPokeAPI URLやIDを解決できない場合の例外。"""
