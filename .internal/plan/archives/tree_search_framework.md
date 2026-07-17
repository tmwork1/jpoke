# 計画書: 木探索フレームワーク 【実装済み】

## 実装結果

- 前提バグ修正1・2は `src/jpoke/core/observation_builder.py` の `_mask_command()` に反映済み。
- `scripts/tree_search/framework.py` に `TreeSearchPlayer` / `default_fallback` /
  `hp_ratio_evaluate` を実装した。設計から変更した点:
  - `max_plies >= 2` の内部再帰（2手目以降）では、`sim.step(commands)` が
    `resolve_command()` を経由しないため `required_command_type` と
    情報隠蔽スナップショット（`last_available_commands`）が新しいターン用に
    更新されない問題が実装時に発覚した。`is_observation()` が真の盤面では
    `build_observation()` がマスク処理自体をスキップする（NOTE-1）ため、
    情報隠蔽つきスナップショットを新しいターン用に作り直す手段が存在しない。
    対応として、探索の最上位呼び出し（`plies == self.max_plies`）でのみ
    情報隠蔽済みの `get_available_commands()` を使い、2手目以降は
    `CommandManager` から直接ライブ計算した合法手を使う「内部シミュレーションは
    全知」という設計に変更した。詳細は `framework.py` の `_best_command()` の
    コメントを参照。
- `scripts/tree_search/tree_search_1〜4.py` を `TreeSearchPlayer` を使う形に置き換えた。
  `tree_search_4.py` は `max_plies=2` の利用例。
- 回帰テスト: `tests/test_copy.py`（CRIT-1）、`tests/test_tree_search_framework.py`
  （CRIT-1・ISSUE-1・例外時の `_searching` 解除・基本的な意思決定の健全性）。
- 全テストスイート（3335件）パス。

## 目的

`.internal/review/code/tree_search.md` で調査した通り、`Battle`/`Player`/`CommandManager` は
木探索（方策関数内での先読みシミュレーション）に必要な4つの基盤
（`Battle.copy()` / `build_observation()` / `get_available_commands()` / `Battle.step(commands)`）
のみを提供しており、探索アルゴリズム自体は `scripts/tree_search/tree_search_1〜4.py` という
シナリオ限定の使い捨てデモにとどまっている。

本計画は以下2点を行う。

1. **前提バグの修正**（同レビューの CRIT-1 / ISSUE-1）。フレームワークの土台として先に直す。
2. **再利用可能な木探索フレームワークの新設**（`TreeSearchPlayer` 基底クラス）。
   4本のデモに共通する「合法手の総当たり」「盤面複製」「評価」「割り込み交代時の再帰」を
   1箇所にまとめ、利用者は評価関数（`evaluate`）を差し替えるだけで済むようにする。

探索アルゴリズムは深さ固定のミニマックス（1手先の総当たり＋任意でNプライ再帰）に限定し、
αβ枝刈り・並列化・モンテカルロ木探索は今回のスコープ外とする（「備考」に発展案を残す）。

---

## 前提バグの修正

### 修正1（CRIT-1相当）: `_mask_command()` が `required_command_type` でフィルタしていない

**ファイル**: `src/jpoke/core/observation_builder.py:134-176`

現状、`_mask_command()` は `state.last_available_commands` を公開状況（`revealed`）のみで
フィルタし、直前に設定した `state.required_command_type`（例: `"move"`）を無視している。
このため、相手のベンチが公開済みの状態で後攻の相手が switch フェーズに入ると、
`battle.get_available_commands(opponent)` は `SWITCH_x` を含んだリストを返し続け、
これを `itertools.product()` でそのまま使うと `sim.step()` の `validate_command()` に弾かれて
`ValueError` になる（再現済み、詳細は `tree_search.md` CRIT-1）。

`last_available_commands` は `get_available_commands()` の相手観測分岐からしか参照されない
（`command_manager.py:153` で書き込み、`observation_builder.py:157`・`battle.py:407` で
読み取りのみ）ため、ここで `required_command_type` フィルタを追加しても他の経路に影響しない。

```python
def _mask_command(battle: Battle, player: Player):
    state = battle.player_states[player]
    active = state.active

    # 予約済みコマンドをクリアする
    state.clear_reserved_commands()

    # 予約が必要なコマンドの種類を記録する
    state.required_command_type = None
    if battle.phase == "action":
        state.required_command_type = "any"
    elif battle.phase == "switch":
        # 後攻でかつ生存している場合は技コマンドの予約が必要
        if (
            battle.query.is_second_actor(player)
            and active.alive
        ):
            state.required_command_type = "move"

    observed_move_indexes = OBSERVED_MOVE_INDEXES[active]

    # last_available_commandsを隠蔽する。これは観測盤面における合法手として扱われる。
    commands = []
    for cmd in state.last_available_commands:
        idx = cmd.index
        # 交代コマンドは、控えのポケモンが公開されている場合のみ利用可能とする
        if cmd.is_type("switch"):
            mon = state.team[idx]
            if mon.revealed:
                commands.append(cmd)
            continue

        # 技コマンドは、技が公開されている場合のみ利用可能とする
        if not active.moves:
            continue

        if idx in observed_move_indexes:
            observed_index = observed_move_indexes[idx]
            new_cmd = cmd.change_index(observed_index)
            commands.append(new_cmd)

    # 公開状況だけでなく required_command_type でも絞り込む。ここを飛ばすと、
    # 木探索が相手の合法手を総当たりした際に「相手がまだ提出していないはずの
    # コマンド種別」が混入し、sim.step() の validate_command() に弾かれて
    # ValueError になる（例: switch フェーズで後攻の相手に対して SWITCH_x を渡してしまう）。
    required = state.required_command_type
    if required not in (None, "any"):
        commands = [cmd for cmd in commands if cmd.is_type(required)]

    state.last_available_commands = commands
```

この修正により、`battle.get_available_commands(opponent)` は常に
「今その局面で相手が本当に提出できるコマンド種別」に絞り込まれた結果を返すようになるため、
以降のフレームワーク側は追加のフィルタ処理を持つ必要がなくなる。

### 修正2（ISSUE-1相当）: `copy_depth > 1` での `raise`/`random` 決め打ちを廃止

`scripts/tree_search/tree_search_1〜3.py` の `if battle.copy_depth > 1: raise ValueError(...)` は
「探索中に割り込み交代が起きて `choose_command()` が再度呼ばれる」ケースを異常系として
扱っている。これはフレームワーク側で「再入検知フラグ＋フォールバック方策」として
恒久的に解消する（次節の `TreeSearchPlayer._searching` を参照）。個別スクリプトを
1本ずつ直すのではなく、フレームワークに一度実装して4本とも置き換える。

---

## フレームワークの設計

### 配置

`scripts/tree_search/framework.py` に置く（`scripts/tree_search/` は既に木探索関連の
置き場として使われているため、既存の慣習を踏襲する）。

`src/jpoke/` 配下の正式なパッケージ（例: `src/jpoke/search/`）にする案も検討したが、
今回はまず `scripts/` 側で汎用化し、実戦投入や外部からの再利用ニーズが出た段階で
`src/jpoke/search/` へ昇格させる方が段階的でリスクが小さいと判断した。
昇格する場合は `CLAUDE.md` のアーキテクチャ表への追記とテストの `tests/` 配下への
移設が必要になる（「備考」参照）。

### `TreeSearchPlayer` 基底クラス

```python
"""木探索プレイヤーの共通フレームワーク。

scripts/tree_search/tree_search_1〜4.py に重複していた「合法手の総当たり列挙」
「盤面複製」「割り込み交代での再帰呼び出しの処理」を1箇所にまとめる。
利用者は evaluate（葉ノード評価関数）を差し替えるだけで木探索プレイヤーを作れる。
"""
from __future__ import annotations
from typing import Callable
import random

from jpoke import Battle, Player
from jpoke.enums import Command


EvaluateFn = Callable[[Battle, Player], float]
FallbackFn = Callable[[Battle, Player], Command]


def default_fallback(battle: Battle, player: Player) -> Command:
    """探索の再入時（割り込み交代など）に使う既定のフォールバック方策。

    評価値付きの探索は行わず、合法手からランダムに1つ選ぶだけの軽量な方策。
    """
    return random.choice(battle.get_available_commands(player))


class TreeSearchPlayer(Player):
    """合法手を総当たりで評価する木探索プレイヤーの基底クラス。

    Attributes:
        evaluate: 葉ノードの盤面を評価する関数。値が大きいほど自分に有利。
        max_plies: 探索する手数（1以上）。1手ごとに
            `len(my_commands) * len(opponent_commands)` 倍に分岐が増えるため、
            2以上を指定する場合は評価関数の呼び出し回数に注意する。
        fallback: 探索の再帰呼び出し（割り込み交代など）で使う方策。
    """

    def __init__(self,
                 name: str,
                 evaluate: EvaluateFn,
                 max_plies: int = 1,
                 fallback: FallbackFn | None = None):
        super().__init__(name=name)
        self.evaluate = evaluate
        self.max_plies = max_plies
        self.fallback = fallback or default_fallback
        self._searching = False

    def choose_command(self, battle: Battle) -> Command:
        if self._searching:
            # sim.step() の内部で発生した割り込み交代（瀕死・だっしゅつボタン・
            # だっしゅつパック・とんぼがえり等）による再帰呼び出し。この局面は
            # 探索木の分岐には含めず、フォールバック方策で即決する。
            # tree_search_1〜3.py の「copy_depth > 1 なら raise」を置き換えるもの:
            # 起きてはいけない事態としてではなく、探索の対象外として自然に処理する。
            return self.fallback(battle, self)

        self._searching = True
        try:
            command, _ = self._best_command(battle, self.max_plies)
            return command
        finally:
            self._searching = False

    def _best_command(self, battle: Battle, plies: int) -> tuple[Command, float]:
        """自分の各合法手について、相手が最善に対抗した場合の評価値を求め、
        その中で最大の評価値を持つ手を返す（ミニマックス）。
        """
        opponent = battle.opponent(self)
        my_commands = battle.get_available_commands(self)
        opponent_commands = battle.get_available_commands(opponent)

        best_command, best_score = my_commands[0], float("-inf")
        for my_cmd in my_commands:
            score = self._worst_case_over_opponent(
                battle, my_cmd, opponent, opponent_commands, plies
            )
            if score > best_score:
                best_command, best_score = my_cmd, score
        return best_command, best_score

    def _worst_case_over_opponent(self,
                                   battle: Battle,
                                   my_cmd: Command,
                                   opponent: Player,
                                   opponent_commands: list[Command],
                                   plies: int) -> float:
        """相手が自分にとって最も不利な手を選ぶと仮定し、その評価値を返す。"""
        worst = float("inf")
        for opp_cmd in opponent_commands:
            sim = battle.copy()
            sim.step({self: my_cmd, opponent: opp_cmd})
            score = self._evaluate_node(sim, plies)
            worst = min(worst, score)
        return worst

    def _evaluate_node(self, sim: Battle, plies: int) -> float:
        if sim.judge_winner() is not None or plies <= 1:
            return self.evaluate(sim, self)
        # 残りプライ数分だけ自分の視点で再帰する。sim.step() ではなく直接
        # _best_command() を呼ぶことで、意図した多段探索の再帰と、
        # 割り込み交代によるエンジン起因の再帰（choose_command() 経由）を
        # 明確に分離している（後者だけが _searching フラグの対象になる）。
        _, score = self._best_command(sim, plies - 1)
        return score
```

### 評価関数の既定実装（サンプル）

```python
def hp_ratio_evaluate(battle: Battle, player: Player) -> float:
    """自分と相手の残りHP割合の差を返す簡易評価関数。

    決着がついている場合は勝敗を最優先する（±inf）。
    """
    opponent = battle.opponent(player)
    winner = battle.judge_winner()
    if winner is player:
        return float("inf")
    if winner is opponent:
        return float("-inf")

    def hp_ratio(target: Player) -> float:
        team = battle.player_states[target].team
        return sum(mon.hp / mon.max_hp for mon in team if not mon.fainted)

    return hp_ratio(player) - hp_ratio(opponent)
```

### 再入検知の設計根拠

- `tree_search_1〜3.py` は `battle.copy_depth > 1` を「起きてはいけない事態」として
  `raise` していたが、`copy_depth` は「今の盤面が何回複製を経たか」を表すだけで、
  「意図した多段探索の再帰」と「割り込み交代によるエンジン起因の再帰呼び出し」を
  区別できない（詳細は `tree_search.md` 1.3節・ISSUE-1）。
- `TreeSearchPlayer` は代わりに `self._searching`（インスタンス属性）で
  「今まさに探索の最上位呼び出しが進行中かどうか」を明示的に管理する。
  - 最上位の `choose_command()` 呼び出し（`_searching == False`）でのみ探索を開始する。
  - 探索中に `sim.step()` が割り込み交代を発生させ、その中で自分の
    `choose_command()` が再度呼ばれた場合（`_searching == True`）はフォールバックする。
  - `try/finally` により、探索中に例外が飛んだ場合でも `_searching` は必ず解除される。
- 意図した多段探索（`max_plies >= 2`）の再帰は `_best_command()` を直接呼ぶ Python の
  関数再帰であり、`Battle.step()`／`choose_command()` を経由しないため、
  `_searching` フラグの対象にはならない（そもそも同一フラグの二重チェックにならない）。
- この設計は `Player` インスタンスの同一性が `Battle.copy()` を経ても保持される
  （`tree_search.md` 1.3節）という既存の前提に依存している。将来 木探索を
  スレッド並列化する場合、同一 `Player` インスタンスを複数スレッドが同時に探索すると
  `_searching` フラグが競合する。この制約は `tree_search.md` NOTE-1
  （`OBSERVED_MOVE_INDEXES` の並列化時懸念）と同種であり、対応するなら
  スレッドローカル化またはプレイヤーインスタンスをスレッドごとに分離する必要がある。

### 決定論化（乱数を伴う評価の扱い）

`sim.step()` 内部ではダメージ乱数・命中判定・追加効果確率などが `battle.random` を通じて
都度消費される。評価を安定させたい場合は、既存の `TestOption`
（`sim.test_option.accuracy = 100` 等）を探索用の `sim` にだけ設定して上書きするか、
`.internal/plan/battle_option.md` で提案中の `BattleOption`（`damage_roll="平均"` 等、対戦全体の
オプション）が実装された場合はそちらを使う方法もある。本フレームワークはどちらの方式にも
依存しない（`evaluate` 関数の内部、または `sim` を作った直後にオプションを設定する形で
利用者が選べる）ため、今回は特別な対応を追加しない。

---

## `scripts/tree_search/` 参照実装の置き換え

既存の4本を `TreeSearchPlayer` を使った形に置き換える。

| 旧ファイル | 置き換え後 |
|---|---|
| `tree_search_1.py` | `TreeSearchPlayer(max_plies=1)` の最小利用例 |
| `tree_search_2.py` | とんぼがえりで switch フェーズに入るシナリオでの利用例（修正1により相手のベンチが公開済みでもクラッシュしないことを示す） |
| `tree_search_3.py` | 両者同時瀕死交代のシナリオ（`required_command_type is None` のケース） |
| `tree_search_4.py` | `max_plies=2` 以上を指定した多段探索の利用例 |

いずれも `choose_command()` 内の総当たりロジックは `framework.py` に移り、各スクリプトは
`evaluate` 関数の定義とチーム構築・対戦ループのみを残す。

---

## 実装順序

1. `src/jpoke/core/observation_builder.py` の `_mask_command()` を修正（前提バグ修正1）
2. `python -m pytest tests/ -v` で既存テストへの影響がないことを確認
   （`last_available_commands` は木探索の観測分岐でしか使われないため回帰は想定しない）
3. `scripts/tree_search/framework.py` を新規作成（`TreeSearchPlayer` / `default_fallback` /
   `hp_ratio_evaluate`）
4. `scripts/tree_search/tree_search_1〜4.py` を `framework.py` を使う形に書き換え
5. `scripts/tree_search/` 配下に回帰テストを追加する場合は `tests/` 配下
   （例: `tests/test_tree_search_framework.py`）に置く。`scripts/` は現状テスト対象外
   （`CLAUDE.md` の対象ディレクトリ一覧に含まれない）ため、`Battle`/`Player` を直接使う
   pytest テストとして書く。

## テスト観点（新規テストを書く場合）

- **CRIT-1回帰**: 相手のベンチが `revealed = True` の状態でとんぼがえり等により switch
  フェーズへ入っても、`TreeSearchPlayer` の探索が `ValueError` を起こさず完了すること
- **ISSUE-1回帰**: 探索対象の盤面で瀕死交代・だっしゅつボタン等の割り込みが発生しても、
  `fallback` が呼ばれて例外にならず `choose_command()` が正常にコマンドを返すこと
- `_searching` フラグが `evaluate` 内で例外を投げた場合でも `finally` で解除されること
  （解除されないと、次のターンの最上位呼び出しまでフォールバックし続けてしまう）
- `max_plies=1` の単純なシナリオ（例: 有利な等倍技 vs 不利な技）で、直感的に正しい
  コマンドが選ばれること
- `max_plies=2` で分岐数が `len(my)*len(opp)` の2乗のオーダーで増えることを
  ログ・カウンタなどで確認（性能上の注意点としてドキュメント化）

## 備考

- 今回のスコープでは αβ枝刈り・相手の合法手のサンプリング（重み付き期待値探索）・
  トランスポジションテーブル・反復深化（時間予算制御）は実装しない。
  分岐数が `max_plies` に対して指数的に増えるため、実戦投入時にこれらの拡張が
  必要になった段階で別計画として切り出す。
- `scripts/tree_search/framework.py` を `src/jpoke/search/` へ昇格させる場合は、
  `CLAUDE.md` のアーキテクチャ表に行を追加し、`.internal/progress/` 配下に
  進捗ドキュメントを新設するかを別途判断する。
- 本計画は `.internal/review/code/tree_search.md` の CRIT-1 / ISSUE-1 の解消を兼ねる。
  実装完了後、同ファイルの該当セクションに「解消済み」の注記を追加すること。
