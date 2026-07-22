# 計画: TreeSearchPlayer の相手推定まわり TODO（TODO1〜3）の検討

更新日: 2026-07-23（TODO1・TODO2 の確定設計を追記し着手）

## 背景

`src/jpoke/players/tree_search_player.py` に残っている4件の `# TODO:` コメントを
ユーザーと議論した。うち1件（`evaluate_commands()` と `_best_command()` の重複解消、
旧L276）は設計判断を伴わない素直なリファクタリングだったため
`feature/tree-search-player-todo-cleanup` ブランチで即時対応済み
（`_score_commands()` ヘルパーへの共通化）。

残る3件は仕様・API設計の判断が必要なため、実装せず本計画書に論点を整理する。
**この3件はいずれも「着手する」ことが決定していない。** 実際のニーズが具体化した
時点で、本書を土台に計画を確定し `planner`/`impl` エージェントのフローに進める。

対象の3TODO（`tree_search_player.py` 内、行番号は
`feature/tree-search-player-todo-cleanup` ブランチ時点）:

1. `estimate_opponent()` のdocstring内（L89）: 相手チームの情報（特性・アイテム・技）と
   相手の選出番号とでは補完方法が異なるため、`estimate_opponent` に集約するより
   項目ごとにフックを分けたほうがエラーを防止できるかもしれない
2. `_toplevel_commands()`（L154）: 相手のコマンド候補が一部でも公開されている場合でも
   `estimate_opponent` を呼び、相手の推定値を更新させるようにする
   （実対戦における型推定に相当する）
3. `_worst_case_over_opponent()`（L217）: 自分のコマンドのスコアを計算する汎用関数として
   実装したほうが、評価方法を変更するときにオーバーライドするだけで済む

## 現状整理（実装コードから確認済みの事実）

- `estimate_opponent(battle, opponent)` が呼ばれるのは `_toplevel_commands()` から
  1箇所のみで、**相手の合法手（`battle.available_commands(opponent)`）が空のとき**
  に限られる（`tree_search_player.py:169-171`）。
- 相手の合法手が空になるのは「相手の技・控えが1つも公開されていない盤面
  （実対戦の初手など）」（同ファイルの `_toplevel_commands` docstring）。
  つまり相手の技が1つでも公開された時点で `opponent_commands` は非空になり、
  それ以降のターンでは `estimate_opponent` は一切呼ばれない。
- 実際の利用例は `examples/02_tree_search/03_estimate_opponent.ipynb` の1件のみで、
  「相手の未公開技をみずでっぽう1本と仮定する」という技の推定に限定されている。
  選出番号（どの3体を選出したか）を推定する使われ方は現状存在しない。
- `_has_estimate_opponent()`（L251）はサブクラスが `estimate_opponent` を
  オーバーライドしているかどうかで分岐しており、既定実装（何もしない）のままだと
  `_resolve_estimated_commands()` を呼ばない設計になっている
  （呼ぶと「わるあがき」だけが返り、推定していないのに空でなくなってしまうため）。
- `TreeSearchPlayer` クラスdocstring（L18-45）は「合法手を総当たりで評価する木探索
  プレイヤーの基底クラス」「相手が最善（自分にとって最悪）の手を選ぶと仮定した
  ミニマックスで評価する」と明記しており、ミニマックス方式であることが本クラスの
  アイデンティティになっている。過去のレビュー（`.internal/api_feedback/pre_loop/
  03_todo_comments.md`）でも `MinimaxPlayer` への改名案は「ミニマックスだけでなく
  `max_nodes`打ち切り・`fallback`・`opponent_estimator`・`configure_sim` を備えた
  探索フレームワーク基底であるため」という理由で見送り確定している。

## TODO1: estimate_opponent を項目ごとのフックに分割するか

### 論点

- 「特性・アイテム・技」の推定と「選出番号」の推定は、そもそも `estimate_opponent`
  の発火条件（相手の合法手が空＝行動選択フェーズで技が非公開）と噛み合わない
  可能性が高い。選出フェーズ（`phase == "selection"`）は通常合法手が空にならないため、
  現行のトリガー機構のままでは「選出番号推定フック」は事実上呼ばれない。
- 選出推定を実装するなら、`estimate_opponent` とは別の発火点（例えば選出フェーズの
  `choose_command` 内、あるいは新規フック `estimate_opponent_selection(battle,
  opponent)` を選出フェーズ専用に用意する）が必要になり、「既存フックを分割する」
  というより「新しい種類のフックを追加する」に近い変更になる。
- 技/特性/アイテムの推定についても、将来「技だけ推定して特性は既知」のような
  部分推定を書きたくなった場合にフック分割の恩恵が出る可能性はあるが、現状の
  唯一の利用例（技のみの推定）ではメリットが確認できない。

### 推奨

**保留。** 具体的な選出推定・部分推定のニーズが出るまで、現行の単一フックのままで
進める。TODOコメント自体は「将来の拡張候補メモ」として残す。着手する場合の
最初のステップは、選出フェーズで何を推定したいか（対戦相手の選出3体を予測する
アルゴリズムの仕様）を先に固めることで、フック分割はその後に決まる実装詳細に過ぎない。

## TODO2: 相手コマンドが一部公開されていても estimate_opponent を呼ぶか

### 論点

- 現状は「相手の技が1つでも公開されればそれ以降 `estimate_opponent` を呼ばない」
  ため、相手が4技中1つしか使っていない盤面では、探索は公開済みの1技のみを相手の
  選択肢として扱う。実戦の「型読み」（相手の未公開スロットを対戦データ等から
  推定して補完し続ける）とは異なる挙動になっている。
- 毎ターン呼ぶように変更する場合の設計上の論点:
  - **呼び出し頻度**: 相手の合法手が非空でも常に呼ぶとなると、`_toplevel_commands`
    の分岐（`if not opponent_commands and self._has_estimate_opponent()`）を
    「常に呼ぶ」方向に変える必要がある。ただし常時呼び出しにすると、
    `estimate_opponent` の実装コストが重い場合（外部データ参照など）に
    毎ターンのオーバーヘッドが発生する。
  - **未公開スロットの判定方法**: 「相手の技が何本公開済みで、残り何本が
    未公開か」を利用者側がどう知るかをAPIとして明確にする必要がある。
    `Pokemon` モデルの `moves` に公開済みかどうかを示す属性
    （`revealed` など、`GameEffect.revealed` と同様の仕組みが `Move`
    にもあるか要確認）が使えるなら追加の引数なしで実装できるが、
    ない場合は `estimate_opponent` に「未公開スロット数」等の追加情報を
    渡すシグネチャ変更が必要になり、既存の `estimate_opponent` を
    オーバーライドしている利用者（examples含む）への影響を検討しないといけない。
  - **べき等性**: 毎ターン呼ばれるようになると、`estimate_opponent` の実装が
    「既に推定済みの項目を上書きしない」よう気をつける必要が出てくる
    （たとえば1ターン目に技A・Bを推定済みなのに、2ターン目に呼ばれて
    技C・Dに上書きしてしまうと一貫性が崩れる）。既定実装は何もしないため
    問題ないが、独自実装をするユーザーへのガイドライン（docstring）が必要。

### 推奨

**着手するなら計画書を分けて先に技モデル側のAPI（未公開スロットの判定手段）を
確認すること。** 現状の `estimate_opponent` docstringは「相手の合法手が
未公開で空のときに呼ばれる」と明記されており、常時呼び出しに変えると
docstringの契約自体を書き換える破壊的変更になる（既存のオーバーライド実装が
「呼ばれるのは初手だけ」という前提で書かれている可能性がある）。
着手する場合の最初のステップ:

1. `Pokemon`/`Move` モデルに技ごとの公開状態を表す属性があるか確認する
   （`src/jpoke/model/pokemon.py` 周辺）。
2. なければ「未公開スロット数」をどう `estimate_opponent` に伝えるか
   （引数追加 or モデルから利用者が自分で調べる前提のままにするか）を決める。
3. 常時呼び出しにした場合のコスト（毎ターン発生するオーバーヘッド）を
   `_has_estimate_opponent()` によるオーバーライド有無の判定と組み合わせて
   許容範囲か検証する（オーバーライドしていないプレイヤーには影響なし）。
4. 既存 example（`03_estimate_opponent.ipynb`）や `_resolve_estimated_commands()`
   の呼び出し条件への影響を洗い出す。

## TODO3: `_worst_case_over_opponent` のスコア計算を汎用化・昇格するか

### 更新（2026-07-21）: MinimaxPlayer分離案に方針転換

当初は「代替評価方式の具体的ニーズが出るまで保留」としていたが、ユーザーとの議論で
「`TreeSearchPlayer` を抽象度を上げた探索フレームワーク基底に留め、現行のミニマックス
アルゴリズムは新設の `MinimaxPlayer(TreeSearchPlayer)` に切り出す」という案が出た。
これは単なる「`_worst_case_over_opponent` の可視性を上げる」以上に筋が通った解決で
あるため、方針をこちらに変更する。

**根拠**: 過去のレビュー（`.internal/api_feedback/pre_loop/03_todo_comments.md`）で
`TreeSearchPlayer` → `MinimaxPlayer` への**改名**は「本クラスがミニマックスだけでなく
`max_nodes`打ち切り・`fallback`・`estimate_opponent`・`configure_sim` を備えた探索
フレームワーク基底であるため」という理由で見送られた。これは裏を返せば「フレームワーク
部分とミニマックス固有部分が同居している」ことそのものを問題として認めている。
**改名ではなく新規サブクラス化**なら、フレームワーク部分を `TreeSearchPlayer` に残した
まま、「相手が最悪の手を選ぶと仮定する」という具体的アルゴリズムだけを `MinimaxPlayer`
に分離でき、過去の見送り判断とも矛盾しない。

### 新しいクラス設計

**`TreeSearchPlayer`（`src/jpoke/players/tree_search_player.py`、既存ファイル）**:
探索フレームワークの基底クラスとして維持する。以下は変更なしでそのまま残る:
- `max_plies` / `max_nodes` / `nodes_expanded` 等の属性、`choose_command()`
- `evaluate()`（既定: 残りHP割合差）、`fallback()`（既定: ランダム）、
  `estimate_opponent()`（既定: 何もしない）、`configure_sim()`（既定: 何もしない）
- `_best_command()` / `_score_commands()`（TODO4で共通化済み） / `_node_limit_reached()`
  / `_toplevel_commands()` / `_available_commands_with_recovery()` /
  `_has_estimate_opponent()` / `_resolve_estimated_commands()` / `evaluate_commands()`

新設する抽象メソッド:
```python
def _score_command(self,
                    battle: Battle,
                    my_cmd: Command,
                    opponent: Player,
                    opp_commands: list[Command],
                    plies: int) -> float:
    """自分の合法手 my_cmd を、相手の候補手 opp_commands を踏まえてスコア化する。

    具体的な評価アルゴリズム（相手が最悪の手を選ぶミニマックスか、期待値か等）は
    サブクラスが実装する。TreeSearchPlayer 単体はインスタンス化できるが、
    choose_command() 実行時にこのメソッドが呼ばれると NotImplementedError になる。
    """
    raise NotImplementedError
```
`_score_commands()`（TODO4で追加済みのヘルパー）は `self._worst_case_over_opponent(...)`
ではなく `self._score_command(...)` を呼ぶように1行修正するだけでよい（既にポリモーフィックな
`self.` 経由の呼び出しになっているため、サブクラス側の実装だけで差し替わる）。

クラスdocstringからは「ミニマックスで評価する」という記述を外し、「具体的な評価
アルゴリズムはサブクラスが `_score_command()` で実装する」という説明に一般化する。

**`MinimaxPlayer`（新設ファイル `src/jpoke/players/minimax_player.py`）**:
`random_player.py` が `RandomPlayer` 単体を持つのと同じ1クラス1ファイルの慣例に
合わせて新規ファイルに置く。
```python
from __future__ import annotations

from jpoke import Battle, Player
from jpoke.enums import Command
from .tree_search_player import TreeSearchPlayer


class MinimaxPlayer(TreeSearchPlayer):
    """相手が自分にとって最も不利な手を選ぶと仮定するミニマックスで評価する木探索プレイヤー。"""

    def _score_command(self,
                        battle: Battle,
                        my_cmd: Command,
                        opponent: Player,
                        opp_commands: list[Command],
                        plies: int) -> float:
        # 現行の _worst_case_over_opponent() の実装をそのまま移設
        # （battle.copy(reseed=True, copy_logs=False, omniscient=True) →
        #  configure_sim → sim.step() → _evaluate_node() → min() を取る、まで含む）
        ...
```
`_evaluate_node()` は「残りplies分だけ自分視点で再帰する」という探索継続ロジックで、
ミニマックスに限らず任意の評価アルゴリズムから使われる汎用インフラのため、
`TreeSearchPlayer` 側に残したまま `MinimaxPlayer._score_command()` から呼び出す。

サブクラスの実装ループ本体（`battle.copy()` → `configure_sim` → `sim.step()` →
評価 → 集約）は、将来 expectimax 等の別アルゴリズムを追加する際にほぼ丸ごと重複する
見込みだが、現時点で2つ目のアルゴリズムの具体的ニーズがないため、共通化はしない
（CLAUDE.mdの「3つの似た行はプリマチュアな抽象化より良い」という開発方針に沿う）。
2つ目のアルゴリズムが実装される時点で、重複したループ部分（`_scores_over_opponent_commands()`
のような形）を `TreeSearchPlayer` 側に引き上げる再抽出を検討する。

### 影響範囲（破壊的変更）

現状ミニマックス以外のアルゴリズムが存在しないため、`TreeSearchPlayer` を直接
インスタンス化・継承している箇所は全て `MinimaxPlayer` に置き換える。

- `src/jpoke/players/__init__.py` — `MinimaxPlayer` を追加エクスポート
- `tests/test_tree_search_framework.py` — 直接インスタンス化・匿名サブクラス化している
  全箇所（フレームワーク機能のテストのため、具体アルゴリズムとして `MinimaxPlayer` を使う）
- `tests/test_fuzz_regressions.py` — `TreeSearchPlayer(username=...)` 1箇所、
  `class X(TreeSearchPlayer)` 2箇所（回帰テストのdocstringにある
  `_worst_case_over_opponent` への言及も `MinimaxPlayer._score_command` に更新）
- `examples/02_tree_search/01〜04*.ipynb`（4本） — 全て `MinimaxPlayer` に置き換え
- `examples/05_advanced/04_janken_nash_cfr.py`
- `scripts/tree_search/tree_search_1〜4.py`（4本）
- `scripts/fuzz/fuzz_battle.py`
- `docs/api/README.md`、`docs/reference/tree_search_player.md`、`mkdocs.yml`、
  `examples/README.md`、`CLAUDE.md`（アーキテクチャ表の1行）
- `CHANGELOG.md` に破壊的変更として明記（`TreeSearchPlayer` は抽象フレームワーク化、
  具体アルゴリズムは新設 `MinimaxPlayer` を使うこと）

`.internal/review/` `.internal/api_feedback/` 等の過去レビュー記録は履歴のため変更しない。

### テスト方針

- `tests/test_tree_search_framework.py` の既存テストは全て `MinimaxPlayer` に
  置き換えれば挙動は変わらないはずなので、そのまま流用する
  （ロジック自体は移動するだけで変更しない）。
- 新規テストとして、`TreeSearchPlayer` を直接使うと `_score_command` 未実装で
  `NotImplementedError` になることを確認するテストを1件追加する。

## 確定設計（2026-07-23、TODO1・TODO2 同時着手）

事前調査で確認した事実:

- `Move` は `revealed` 属性を持ち、観測（`observation_builder._mask_moves`）では
  未公開の技が相手ポケモンの `moves` リストから **除去** される。つまり観測上の
  `len(active.moves)` が「公開済み技数」であり、推定側は追加の引数なしで
  未公開スロットの有無を判定できる（TODO2 推奨節ステップ1・2は解決）。
- `state.selected_indexes` も観測では公開済み（`revealed`）の個体のみに絞り込まれる。
  選出推定はここに未公開個体のインデックスを補うことに相当する。
- 選出フェーズの自分の選出決定は `choose_selection()` という別フックであり、
  `choose_command()`（探索）は選出フェーズでは呼ばれない。TODO1 の「選出番号の推定」は
  探索中の相手の交代候補（ベンチ）復元のためのものであり、発火点は
  `_toplevel_commands` のままでよい（選出フェーズ専用の発火点は不要）。
- `battle.available_commands(opponent)` は観測の `last_available_commands`
  （リスト実体）をそのまま返すため、探索側で候補を足す場合はコピーが必須。

### TODO1: テンプレートメソッド方式の項目別フック分割

`estimate_opponent(battle)` はフレームワークからの呼び出し入口として維持し、
既定実装を「項目別フック2つを順に呼ぶ」テンプレートメソッドに変更する:

- `estimate_opponent_team(battle) -> None` — 相手ポケモンのモデル
  （`battle.get_active(battle.opponent(self))` 等）に技・特性・アイテムの推定値を
  書き込む。既定は何もしない。従来の `estimate_opponent` の使い方はこちらに対応する。
- `estimate_opponent_selection(battle) -> list[int] | None` — 相手の
  選出インデックス（`state.team` 基準）の推定を **返り値** で返す。`None` なら
  推定しない。書き込み先（`player_states[opponent].selected_indexes`）は内部状態の
  ため利用者に直接触らせず、フレームワーク側がマージ（公開済みインデックスは維持し、
  未包含の推定分のみ追加）する。既定は `None`。
- `_has_estimate_opponent()` は3フックのいずれかがオーバーライドされているかを判定する。
- 既存の `estimate_opponent` 直接オーバーライド（example・テスト）は後方互換で動き続ける。
- ユーザーレビューにより `opponent` 引数は削除（`battle.opponent(self)` で取得する
  `evaluate`/`fallback` 等の他フックとの規約統一）。相手は3フックいずれも
  `battle.opponent(self)` で取得する。

### TODO2: 相手候補が部分公開でも毎回推定を呼ぶ（型推定）

`_toplevel_commands` を変更し、`_has_estimate_opponent()` が真なら相手の合法手の
有無に関わらず毎回 `estimate_opponent` を呼ぶ。相手候補は「観測スナップショット由来の
コマンド（コピー） ∪ `_resolve_estimated_commands` の列挙結果」の和集合
（`Command` 同一性で重複排除）とする:

- スナップショットが空のとき（従来の発火条件）の挙動は完全に従来と同一。
- 部分公開のときは、公開済み候補を失うことなく推定由来の候補だけが追加される
  （モデル列挙がスナップショットと万一食い違っても公開済み情報が消えない安全策）。
- docstring の契約を「探索の最上位（`choose_command` / `evaluate_commands`）のたびに
  呼ばれる」に書き換え、べき等性のガイドライン（観測は毎ターン再構築されるため
  公開済みスロットを上書きせず未公開分のみ補うこと）を明記する。

### 影響範囲

- `src/jpoke/players/tree_search_player.py` — 上記本体。TODO1・TODO2 のコメントは削除
- `tests/test_tree_search_framework.py` — 新規テスト（部分公開時の推定呼び出し・
  候補和集合、`estimate_opponent_team`、`estimate_opponent_selection` の選出マージ、
  既存の umbrella オーバーライド後方互換）
- `examples/02_tree_search/03_estimate_opponent.ipynb` — `estimate_opponent_team` を
  使った毎ターン型推定の例に更新
- `docs/quick_reference.md`（フック表）、`examples/README.md`、`CHANGELOG.md`（Unreleased）

## まとめ

| TODO | 対応 |
|---|---|
| TODO4（`evaluate_commands`/`_best_command`共通化） | 実装済み（`feature/tree-search-player-todo-cleanup`） |
| TODO1（フック分割） | **実装済み（2026-07-23）**: テンプレートメソッド方式で `estimate_opponent_team` / `estimate_opponent_selection` に分割 |
| TODO2（常時estimate_opponent呼び出し） | **実装済み（2026-07-23）**: 部分公開でも毎回推定を呼び、候補は和集合で拡張 |
| TODO3（スコア計算の汎用化） | 実装済み：`MinimaxPlayer` 分離 |

TODO1〜4 の全コードコメントは解消済みで、コード上には残っていない。
