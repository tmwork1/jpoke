"""プレイヤークラスとプレイヤー管理機能。

バトルに参加するプレイヤーの情報と、コマンドの予約・管理を行います。
選出、交代、行動の選択などプレイヤー固有の処理を提供します。
"""
from __future__ import annotations
from typing import Any, Callable, TYPE_CHECKING
if TYPE_CHECKING:
    from jpoke.core import Battle
    from jpoke.model import Pokemon

from jpoke.enums import Command
from jpoke.types import AbilityName, Gender, ItemName, MoveName, Nature, PokemonName, Stat, Type

# poke-env 互換の battle_against() でターン上限に使う既定値。
# scripts/fuzz/fuzz_battle.py の "random" プリセット（max_turns=100）を参考にした値。
MAX_TURNS = 100


class Player:
    """バトルプレイヤーを表すクラス。

    Attributes:
        username: プレイヤー名
        team: ポケモンチームのリスト（最大6匹）。**コンストラクタ〜対戦開始前の
            スナップショット**であり、`Battle` 開始後の対戦中はここに反映される
            HP・瀕死・状態異常・ランク変化などは更新されない。対戦中の実際の
            状態を見たい場合は `battle.get_active(player)`（場に出ている
            ポケモン）や `battle.get_team(player)`（チーム全体の実体）を使う。
        n_finished_battles: 対戦数
        n_won_battles: 勝利数
        rating: レーティング値

    Note:
        `team` へポケモンを追加するには `add_pokemon()` を使う（`from jpoke import
        Pokemon` が不要になる）。`team.append(Pokemon(...))` でも動作するが、
        `Pokemon` を直接構築する場合に比べて import が1つ減る分、導入時の
        依存関係が単純になる。
    """

    def __init__(self, username: str = ""):
        """Playerインスタンスを初期化する。

        Args:
            username: プレイヤー名（デフォルトは空文字列）
        """
        self.username = username

        self.team: list[Pokemon] = []
        self.n_finished_battles: int = 0
        self.n_won_battles: int = 0
        self.rating: float = 1500

    def add_pokemon(self,
                    name: PokemonName,
                    gender: Gender = "",
                    nature: Nature = "まじめ",
                    level: int = 50,
                    ability: AbilityName = "",
                    item: ItemName = "",
                    moves: list[MoveName] | None = None,
                    tera_type: Type | None = None,
                    evs: dict[Stat, int] | None = None,
                    ivs: dict[Stat, int] | None = None) -> Pokemon:
        """ポケモンを1体作成し、チームに追加する。

        `from jpoke import Pokemon` を使わずにチームを組める、`team` への
        正規の追加ルート。`evs`/`ivs` 以外の引数は `Pokemon.__init__` にそのまま渡す。

        Args:
            evs: Champions形式の努力値（各値0〜32）を指定するステータスのみの辞書。
                `None`（デフォルト）の場合は設定せず、`Pokemon` の既定値のまま
            ivs: 個体値を指定するステータスのみの辞書。`None`（デフォルト）の
                場合は設定せず、`Pokemon` の既定値（全て31）のまま

        Returns:
            Pokemon: 追加したポケモンのインスタンス（交代先の参照などに使う）
        """
        # jpoke.model はデータ定義（jpoke.data）経由でハンドラ（jpoke.core.handler が
        # Player をimportする）まで依存が繋がっており、モジュールトップレベルで
        # importすると循環importになる。関数内での遅延importで回避する。
        from jpoke.model.pokemon import Pokemon

        mon = Pokemon(
            name,
            gender=gender,
            nature=nature,
            level=level,
            ability_name=ability,
            item_name=item,
            move_names=moves,
            tera_type=tera_type,
        )
        if evs is not None:
            mon.set_evs(evs)
        if ivs is not None:
            mon.set_ivs(ivs)
        self.team.append(mon)
        return mon

    # ── poke-env 互換 ───────────────────────────────────────────

    @property
    def n_tied_battles(self) -> int:
        """poke-env 互換: 引き分け数。jpoke に引き分けは存在しないため常に0。"""
        return 0

    @property
    def n_lost_battles(self) -> int:
        """poke-env 互換: 敗北数。"""
        return self.n_finished_battles - self.n_won_battles - self.n_tied_battles

    @property
    def win_rate(self) -> float:
        """poke-env 互換: 勝率。poke-env と異なりゼロ除算を防ぐガード付き。"""
        if self.n_finished_battles == 0:
            return 0.0
        return self.n_won_battles / self.n_finished_battles

    def choose_selection(self, battle: Battle) -> list[int]:
        """選出番号を返す

        デフォルト実装では先頭から順番に選出する。

        Args:
            battle: バトルオブジェクト

        Returns:
            選択された選出番号のリスト
        """
        n = battle.n_selected
        return list(range(n))

    def choose_command(self, battle: Battle) -> Command:
        """コマンドを選択する。

        デフォルト実装では利用可能な行動コマンドの最初の1つを返す。この既定実装は
        決定的（常に先頭のコマンドを選ぶ）で、`seed` を変えても展開が変わらない。
        `Player.battle_against()` で複数回対戦して統計比較する場合など、行動選択に
        分散が必要な場合は `jpoke.players.RandomPlayer` を使うとよい。

        Args:
            battle: バトルオブジェクト

        Returns:
            選択された行動コマンド
        """
        commands = battle.available_commands(self)
        return commands[0]

    def battle_against(
        self,
        *opponents: "Player",
        n_battles: int = 1,
        on_battle_end: Callable[["Battle"], None] | None = None,
        **battle_kwargs: Any,
    ) -> None:
        """poke-env 互換: 各 opponent と n_battles 回ずつ対戦し、双方の戦績を更新する。

        poke-env と同じシグネチャ。ただしネットワーク I/O がないため同期メソッド
        （await / asyncio.run は不要）。

        Args:
            *opponents: 対戦相手のPlayerインスタンス（複数指定可）
            n_battles: 各opponentと対戦する回数（デフォルト1）
            on_battle_end: poke-envにはないjpoke独自の拡張。各対戦の
                `play_out()` 完了直後に、その対戦の `Battle` インスタンスを
                引数として呼び出されるコールバック。自己対戦のリプレイ・
                観測データ収集（強化学習用など）に使う。ターン上限で決着が
                つかず戦績に数えられなかった対戦（`winner is None`）でも
                呼び出される。`None`（デフォルト）の場合は呼び出さず、
                各対戦の `Battle` は `play_out()` 完了後に破棄される
            **battle_kwargs: `Battle.__init__` へ素通しするキーワード引数
                （`n_selected`, `seed`, `mega_evolution` 等）。poke-envにはない
                jpoke独自の拡張。`seed` を指定すると対戦ごとに `seed + 対戦通番`
                の派生シードを自動的に使うため、`n_battles` 回すべてが同一の
                展開になることはない。省略した場合は `Battle` 側の既定（OSの
                乱数源から生成する高エントロピーな値）に従う。`opponents` を
                複数指定した場合、対戦通番は opponent ごとに0からリセットされる
                ため、`seed` 指定時は各 opponent との対戦がそれぞれ同じ
                `seed, seed+1, ...` の系列を使う点に注意

        Note:
            ターン数が `MAX_TURNS` に達しても決着しない対戦は、勝者を強制的に
            決めず（`tod_score()` 等によるダメージレース判定は行わない）、
            戦績に一切数えない（`n_finished_battles` もインクリメントしない）。
            対戦の成立・不成立を戦績に反映する方が、引き分けを持たない
            jpokeの仕様（`n_tied_battles` は常に0）と整合するための判断。
        """
        # Battleをモジュールトップレベルでimportすると、battle.pyがPlayerを
        # importしているため循環importになる。関数内での遅延importで回避する。
        from .battle import Battle

        base_seed = battle_kwargs.pop("seed", None)

        for opponent in opponents:
            for i in range(n_battles):
                seed = base_seed + i if base_seed is not None else None
                battle = Battle(self, opponent, seed=seed, **battle_kwargs)
                battle.play_out(max_turns=MAX_TURNS)
                winner = battle.winner
                if on_battle_end is not None:
                    on_battle_end(battle)
                if winner is None:
                    # ターン上限で決着しなかった対戦は不成立として戦績に数えない
                    continue
                for player in (self, opponent):
                    player.n_finished_battles += 1
                    if winner is player:
                        player.n_won_battles += 1
