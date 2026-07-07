# 木探索フレームワーク（TreeSearchPlayer）レビュー — 開発者・利用者の両視点

日付: 2026-07-07
対象: `scripts/tree_search/framework.py`（`TreeSearchPlayer` / `default_fallback` / `hp_ratio_evaluate`）、
`scripts/tree_search/tree_search_1〜4.py`、`tests/test_tree_search_framework.py`、
および関連するエンジン側基盤（`core/battle.py`, `core/command_manager.py`, `core/observation_builder.py`）
前提: [tree_search.md](tree_search.md)（2026-07-05 の実態調査）と
`docs/plan/archives/tree_search_framework.md`（実装計画・完了済み）の続編。
CRIT-1（`_mask_command()` のコマンド種別フィルタ漏れ）と ISSUE-1（`copy_depth` 決め打ち `raise`）は
解消済みであることを再確認した上で、**実装後のフレームワークそのもの**を
「利用者（bot・探索コードを書く人）」と「開発者（jpoke エンジンの保守者）」の両視点でレビューする。

指摘 ID は旧レビューとの衝突を避けるため `FW-U*`（利用者視点）/ `FW-D*`（開発者視点）を使う。

改善方針: 各指摘の解消は **`src/jpoke/players/tree_search_player.py` への昇格（4章）を土台**に行う。
配置問題（FW-U4）と内部 API 直呼びの規約違反（FW-D1）は昇格自体で解消し、
残りの指摘は昇格後の公開 API として設計する。

---

## 1. 現状サマリ

`TreeSearchPlayer` は `Player` のサブクラスで、`choose_command()` 内で以下を行う。

- 自分・相手の合法手を列挙し、全組み合わせ（`len(my) × len(opp)`）について
  `battle.copy()` → `sim.step({self: my_cmd, opponent: opp_cmd})` で1ターン展開する
- 相手が自分にとって最悪の手を選ぶと仮定するミニマックスで、自分の最善手を選ぶ
- `max_plies >= 2` なら葉ノードで `_best_command()` を直接再帰し、複数ターン先まで評価する
- 探索中にエンジンが割り込み交代（瀕死・だっしゅつボタン等）で `choose_command()` を
  再入呼び出しした場合は、`_searching` フラグで検知して `fallback` 方策（既定はランダム）で即決する
- 利用者は評価関数 `evaluate: (Battle, Player) -> float` を差し替えるだけでよい
  （既定は残りHP割合差の `hp_ratio_evaluate`）

情報の扱いは「探索1手目は情報隠蔽済みの観測を尊重、2手目以降の内部シミュレーションは全知」
という設計（理由は `framework.py` の `_best_command()` コメントおよび計画書を参照）。

### 良い点（両視点共通）

- **責務分離が明快**: エンジンは4つの基盤（`copy()` / `build_observation()` /
  `get_available_commands()` / `step(commands)`）のみを提供し、探索アルゴリズムは
  `scripts/` 側に隔離されている。エンジン側に探索固有のコードが漏れていない。
- **旧レビューの2バグが回帰テスト付きで解消済み**: CRIT-1 は
  `tests/test_copy.py`、ISSUE-1 は `tests/test_tree_search_framework.py` で担保されている。
- **再入検知の設計が堅牢**: `_searching` は `try/finally` で確実に解除され、
  評価関数が例外を投げてもフォールバック状態に固着しない（テストあり）。
  `copy_depth` 決め打ちと違い「意図した多段再帰」と「エンジン起因の再入」を正しく区別できる。
- **難所のドキュメントが充実**: stale observer による `run_faint_switch()` 無限再帰
  （`_worst_case_over_opponent()` のコメント）など、ハマりどころの経緯がコード内に残されている。

---

## 2. 利用者（bot・探索コードを書く人）視点

### FW-U1（重大・動作確認済み）: 相手の手が未公開だと探索が無言で退化し、先頭コマンドを選ぶだけになる

**ファイル**: `scripts/tree_search/framework.py:121-128, 130-163`

探索1手目の相手の合法手は情報隠蔽済みスナップショット（`last_available_commands`）であり、
`_mask_command()` は**公開済み（`revealed`）の技・控えしか残さない**。相手の技が1つも
公開されていない盤面（＝実対戦の初手は必ずこの状態）では相手の合法手が**空リスト**になり、

1. `_worst_case_over_opponent()` のループが一度も回らず `worst = float("inf")` のまま返る
2. 自分の全コマンドが同点 `+inf` になる
3. `_best_command()` は先頭コマンド（通常は技1）を返す

つまり**シミュレーションを1回も実行せずに、デフォルト `Player`（先頭コマンド選択）と
同じ挙動に退化する**。例外も警告も出ないため、利用者は探索が機能していないことに気づけない。

**再現**（2026-07-07 に実行して確認）:

```python
# 相手（HP50に設定）の技・控えを一切 revealed にせず battle.step()
# ヒトカゲの技: [たいあたり(ダメージ1に固定), 10まんボルト(ダメージ200に固定)]
battle.step()
# → 確殺の10まんボルトではなく、先頭のたいあたりが選ばれる
# → 観測盤面の get_available_commands(opponent) は [] を返している
```

既存テスト4件は全て `player2.team[0].moves[0].revealed = True`
（コメント「相手の技を公開し合法手が空にならないようにする」）でこの状態を**回避**しており、
制約の存在自体は実装者に認識されているが、フレームワークの docstring にも
デモスクリプトにも利用者向けの説明がない。

**推奨対応**（いずれか、併用可）:
1. `framework.py` 側: 相手の合法手が空の場合の推定手を注入するフック
   （例: `opponent_command_guesser: Callable[[Battle, Player], list[Command]]`、
   既定は「わるあがき相当のダミー行動1つ」）を設け、少なくとも
   「相手が何もしてこない仮定で自分の手だけ比較する」状態まで回復させる
   → **方針変更**: 実装時に「利用者が `Command` を直接組み立てる」この設計は
     採用せず、「利用者は推定した技・アイテムをモデルに書き込むだけにし、
     コマンドへの変換は `CommandManager` に行わせる」`opponent_estimator` へ
     設計を変更した。理由・詳細は本節末尾の「解消済み」を参照
2. 最低限の対応として、空リスト時に `fallback` へ委譲し、docstring に
   「相手の情報が未公開の局面では探索できない」と明記する
3. 将来的（エンジン側・別計画）: 観測構築時に未公開技を「不明技」プレースホルダとして
   残す設計。現状は `_mask_move()` が技オブジェクトごと削除するため、
   「相手は公開技しか持たない世界」しか探索できない（FW-U5 も参照）

**解消済み**（`src/jpoke/players/tree_search_player.py`）: 推奨対応1・2を組み合わせて実装した。
相手の合法手が空のまま `opponent_estimator` も未指定なら即座に `fallback` へ委譲する（無言の
先頭コマンド退化はなくなった）。`opponent_estimator: Callable[[Battle, Player], None]` を
指定すると、相手ポケモンのモデル（`moves`/`item` 等）へ推定値を書き込むだけでよく、
`Command` の組み立て（インデックス対応・テラスタル/メガシンカ変種・交代コマンド併記）は
`CommandManager.get_available_action_commands()`/`get_available_switch_commands()` に
やり直させる設計にした。当初案の `opponent_command_guesser`（利用者が `list[Command]` を
直接組み立てる形）は、コマンド構築の知識を要求しコード再利用も生まないため採用せず、
「技・アイテムの推定だけに専念させ、コマンド解決はシステム側が行う」形に設計を改めた。

### FW-U2（バグ）: `default_fallback` がグローバル `random` を使うため、seed 固定でも対戦が再現しない

**ファイル**: `scripts/tree_search/framework.py:11, 21-26`

```python
import random
...
return random.choice(battle.get_available_commands(player))
```

`Battle(seed=...)` で乱数を固定しても、探索中の割り込み交代で `default_fallback` が呼ばれると
プロセスグローバルの乱数系列から手が選ばれる。フォールバックの選択は各分岐の評価値
→ 実対戦で選ばれるコマンドに影響するため、**seed を固定したバトル全体の再現性が壊れる**。
エンジン側が `battle.random` の分離コピー（枝ごとに独立した乱数系列）まで丁寧に
設計しているのと対照的で、フレームワーク側だけが再現性を破っている。

**推奨対応**: `battle.random.choice(...)` に変更する（1行）。
渡ってくる `battle` は探索用 sim またはエンジンが作った観測コピーであり、
その乱数を消費しても実盤面には影響しない。

### FW-U3（中程度）: 分岐爆発への防御・計測手段がなく、時間予算もない

**ファイル**: `scripts/tree_search/framework.py:57-59, 121-128`

- 分岐数は1プライあたり `len(my) × len(opp)`。テラスタル・メガシンカ変種
  （`get_available_action_commands()` は技ごとに `TERASTAL_x`/`MEGAEVOL_x` を追加する）と
  交代を含めると自分側だけで10手を超えることが珍しくなく、`max_plies=2` で
  1万オーダーの `Battle.copy()`（deepcopy ベース）＋フルターンシミュレーションが走る。
- docstring に「評価関数の呼び出し回数に注意」とあるだけで、ノード数上限・時間予算・
  探索打ち切りのいずれも存在せず、**実際に何ノード展開したかを知る手段もない**
  （展開ノード数カウンタすらないため、利用者はチューニングの手がかりを得られない）。
- 自己対戦（両者 `TreeSearchPlayer`）では追加の落とし穴がある:
  自分の探索 sim 内で割り込み交代が起きると、エンジンは**相手プレイヤーの実インスタンス**の
  `choose_command()` を呼ぶ。相手も `TreeSearchPlayer` の場合、相手側の `_searching` は
  False なので、**自分の探索の1分岐の中で相手のフル探索がネスト実行される**。
  αβ枝刈り等が別計画スコープなのは妥当だが、この自己対戦時の挙動は
  フレームワーク利用者が確実に踏むため文書化が必要。

**推奨対応**: (1) 展開ノード数のカウンタと任意の上限（超過時は探索を打ち切り現時点の
最善手を返す）を追加する。(2) 自己対戦時は双方に軽量な `fallback` を指定する運用を
docstring・デモに明記する。

### FW-U4（中程度）: `scripts/` 配置のため import に sys.path 操作が必要で、探索用オプションを注入するフックもない

- `framework.py` は `jpoke` パッケージ外にあるため、利用者（および
  `tests/test_tree_search_framework.py` 自身）は
  `sys.path.insert(0, ".../scripts/tree_search")` という手作業が必要。
  計画書は「実戦投入や再利用ニーズが出た段階で `src/jpoke/search/` へ昇格」としており
  段階的方針自体は妥当だが、**テストが既に sys.path ハックを常用している時点で
  「再利用ニーズ」は顕在化している**と言える。なお pyproject.toml は
  `packages.find where = ["src"]`・pytest `pythonpath = ["src"]` の src レイアウトであり、
  プロジェクトルート直下（例: `prj_root/player/`）に置いてもパッケージに含まれず
  pytest のパスにも乗らないため、昇格先は `src/jpoke/` 配下でなければ問題が解決しない。
- 計画書の「決定論化」節は「`sim` を作った直後にオプションを設定する形で利用者が選べる」と
  しているが、実際には sim の生成（`_worst_case_over_opponent()` 内の `battle.copy()`）と
  `sim.step()` の間に利用者が介入できる公開フックは**存在しない**。`evaluate` に渡るのは
  `step()` 実行後の盤面であり、ダメージ乱数の平均化（`BattleOption.damage_roll="平均"`）や
  命中固定を探索時だけ有効にしたい場合、私有メソッドのオーバーライドが必要になる。

**推奨対応**: 配置問題は `src/jpoke/players/tree_search_player.py` への昇格（4章）で解消する。
`from jpoke.players import TreeSearchPlayer` の一文で import でき、テストの
sys.path ハックも不要になる。オプション注入は昇格後の公開 API として、sim 生成直後に
呼ばれるフック（例: `configure_sim: Callable[[Battle], None] | None`）を追加する。
これで「実対戦は通常乱数・探索中だけ平均ダメージ」という自然な使い方が
オーバーライドなしで書けるようになる。

**解消済み**（`src/jpoke/players/tree_search_player.py` へ昇格）: 配置問題は
`from jpoke.players import TreeSearchPlayer` で解消し、`tests/test_tree_search_framework.py`
の sys.path ハックも削除した。`configure_sim` フックも追加済み。

### FW-U5（軽微・注記）: 「2手目以降は全知」という説明は正確ではない — 相手の未公開技は探索世界から消えたまま

`_best_command()` の else 分岐は `CommandManager` から合法手をライブ計算するが、
探索対象の盤面はトップレベルの観測構築時に `_mask_move()` が相手の未公開技を
**リストから物理削除した後**のコピーである。したがって多段探索で「全知」になるのは
コマンド列挙の経路だけで、盤面情報は「相手が公開技しか持たない世界」のまま。
評価が楽観側（相手の脅威を過小評価）に系統的に偏ることを、利用者向けに明記すべき。

同様に、各分岐の評価は乱数1サンプル（1発のダメージロール・命中判定）に基づくため、
「ノイズを含むサンプルの min を取る」ミニマックスは相手側評価が悲観側に偏る
統計的バイアスを持つ。`copy(reseed=True)`（枝ごとの乱数分離）はエンジン側に実装済みだが
フレームワークからは使われておらず、共通乱数（全分岐が同一乱数系列）で比較している。
共通乱数は分散低減の観点でむしろ望ましい選択だが、意図的な選択であることが
どこにも書かれていないため、docstring に1行残すとよい。

### FW-U6（軽微）: スコア・読み筋の取得手段がなく、同点時は常に先頭コマンドに倒れる

`_best_command()` は `(command, score)` を返すが `choose_command()` がスコアを捨てるため、
利用者がデバッグ時に「各コマンドの評価値一覧」や読み筋（PV）を得るには
私有メソッドを直接呼ぶしかない。また同点時は strict な `>` 比較で先頭優先となり、
評価関数が粗い（同点が多い）ほど技1に偏る。前者は評価値一覧を返す公開メソッド
（例: `evaluate_commands(battle) -> dict[Command, float]`）の追加、後者は
docstring への明記（または同点時の `battle.random` によるタイブレーク）で解消できる。

---

## 3. 開発者（jpoke エンジン保守者）視点

### FW-D1（中程度・構造）: フレームワークがエンジン内部 API の直呼びと内部状態の書き換えで成立しており、プロジェクト自身の API 方針に反している

**ファイル**: `scripts/tree_search/framework.py:116-119, 159`

`CLAUDE.md` は「外部 API（テスト・bot・探索コード）は `Battle` の公開メソッドを入口にする。
`battle.<manager>.<method>()` の直呼びは `src/jpoke` 内部実装に限る」と定めているが、
`scripts/`（＝外部）にある `framework.py` は以下を行っている。

1. `battle.command_manager.get_available_action_commands(...)` の直呼び（2手目以降の合法手列挙）
2. `battle.player_states[...].required_command_type = "any"` の直接書き換え
3. `sim.observer = None` の直接書き換え（stale observer 起因の無限再帰回避）

いずれも「その操作なしでは動かない」ことが長文コメントで正当化されており、
**エンジンの公開 API が木探索の実需要（『観測コピーから新しいターンを正しく進める』）を
カバーできていない**ことの証拠になっている。個々の回避策は正しいが、
エンジン内部（`observer` の意味論、`required_command_type` のライフサイクル、
`last_available_commands` のスナップショットタイミング）を変更すると
`scripts/` 側がサイレントに壊れる密結合が生まれている。

**推奨対応**: `src/jpoke/players/` への昇格（4章）で解消する。パッケージ内に入れば
この3操作は「`src/jpoke` 内部実装間の結合」となり規約に適合し、エンジン内部
（`observer` の意味論、`required_command_type` のライフサイクル）を変更する際も
同一パッケージ内で `players/` を一緒に保守できる。エンジン側の公開 API 新設を待たずに
規約違反を解消できるのがこの方針の実利。

昇格後の任意の追加改善として、上記3操作を1つのメソッドに吸収する案
（例: `Battle.detach_observation() -> Battle`「観測コンテキストを破棄し、
以降のターンを全知シミュレーションとして進められる複製を返す」）は引き続き有効。
`tree_search_player.py` 側は `sim = battle.detach_observation()` を呼ぶだけになり、
結合が1メソッドの契約に集約されるため、`players/` 以外の第2の探索実装や
外部利用者が現れた時点で実施する。

**解消済み**（`src/jpoke/players/tree_search_player.py` へ昇格）: 内部 API 直呼び3操作は
パッケージ内実装間の結合として規約に適合するようになった。任意の追加改善
（`detach_observation()`）は引き続き未実施。

### FW-D2（中程度・エンジン堅牢性）: stale な交代コマンドで `run_faint_switch()` が無限再帰するエンジン側の脆弱性が未対処のまま残っている

**ファイル**: `scripts/tree_search/framework.py:140-158`（コメントに経緯）、
`src/jpoke/core/switch_manager.py`（`run_faint_switch`）

`_worst_case_over_opponent()` のコメントは「stale な `last_available_commands` から
交代不能なコマンドを選び続けると、交代が一切進行せず `run_faint_switch()` が
同じ局面のまま無限に再帰する（テストで確認済みのバグ）」と明記している。
フレームワーク側は `sim.observer = None` でこの経路を回避したが、
**エンジン側には「方策関数が無効な（進行しない）コマンドを返し続けたときの
非進行ガード」が依然として存在しない**。ユーザーが独自の `Player` サブクラスで
観測盤面を持ち回るコードを書けば、同じ無限再帰（実際には `RecursionError`）を踏む。

**推奨対応**: `run_faint_switch()`（または `resolve_command` の switch 経路）に
再試行上限か「選ばれたコマンドが状況を進行させたか」の検証を入れ、
超過時は `InvalidCommandError` 等の診断可能な例外で落とす。
無限再帰よりはるかにデバッグしやすくなる。

### FW-D3（軽微・エンジン設計の制約）: 探索 sim の中で「相手プレイヤーの実インスタンス」の方策が呼ばれる構造は、対戦相手が外部エージェントになった時点で破綻する

探索 sim 内の割り込み交代処理は `resolve_command()` 経由で相手 `Player` の
`choose_command()` を呼ぶ。相手がコード内の方策関数である限り動くが、
相手が人間 UI・ネットワーク越しの bot 等になると「探索のたびに実対戦相手へ
シミュレーション用の意思決定を要求する」ことになり成立しない。
`Player` インスタンスの同一性が `player_states` のキーとして構造的に固定されているため、
「sim 内だけ相手を軽量な相手モデルに差し替える」ことも現状は不可能。
実戦投入（外部対戦相手）を見据えるなら、sim 用の方策差し替え機構
（例: `Battle.copy(policy_overrides={player: fn})`）がエンジン側にいずれ必要になる。
現時点では自己完結した対戦しか想定していないため軽微とするが、
チャンピオンズ実戦を目標とするプロジェクトのロードマップ上は避けて通れない。

### FW-D4（軽微・ドキュメント）: 計画書の移動でコード内リンクが切れている

計画書は `docs/plan/tree_search_framework.md` から
`docs/plan/archives/tree_search_framework.md` へ移動済みだが、以下が旧パスのまま:

- `scripts/tree_search/framework.py:7, 81, 115`（docstring・コメント3箇所）
- `tests/test_tree_search_framework.py:3`
- `docs/review/code/tree_search.md`（CRIT-1・ISSUE-1 の対応記述2箇所）

旧レビュー群（[index.md](index.md) 横断パターン1）が指摘した
「ドキュメントドリフト」と同型の問題が、実装から2日で早くも発生している。

**推奨対応**: 昇格（4章）で `framework.py` 自体が `src/jpoke/players/` へ移動し
docstring・コメントの書き直しが発生するため、その際にまとめて修正する。

**解消済み**（`src/jpoke/players/tree_search_player.py` へ昇格）: 移動時に
`docs/plan/tree_search_framework.md` への旧パス参照3箇所と
`docs/review/code/tree_search.md` の旧パス参照2箇所を
`docs/plan/archives/tree_search_framework.md` に修正した。

### FW-D5（軽微・テスト）: 退化ケース・全知境界のテストが不足

`tests/test_tree_search_framework.py` は回帰4件として適切だが、以下が未カバー:

- 相手の合法手が空のケース（FW-U1）。現状は全テストが `revealed = True` で回避しており、
  「退化する」という現仕様すらテストで固定されていない
  （FW-U1 の対応後は、その新仕様のテストに置き換える）
- `max_plies=2` の探索が「1手目は観測準拠・2手目は全知」の境界で正しく動くこと
  （例: 相手の未公開技が2手目の分岐にも現れないこと）
- `fallback` に独自関数を渡した場合にそれが実際に使われること
- 計画書のテスト観点にあった「分岐数が `len(my)×len(opp)` の2乗オーダーで増える」ことの
  カウンタ確認（FW-U3 のノード数カウンタ導入とセットで実施可能）

昇格（4章）に伴い、これらは `tests/test_tree_search_framework.py` の sys.path ハック除去と
併せて整備する。

---

## 4. 改善の基本方針: `src/jpoke/players/tree_search_player.py` への昇格

個別の指摘に入る前提として、フレームワークを「利用者に提供する派生 `Player` クラス」と
位置づけ直し、`scripts/tree_search/framework.py` から
**`src/jpoke/players/tree_search_player.py`** へ昇格させる。これを他の全改善の土台とする。

### 配置の根拠

- **パッケージ外では import 問題が解決しない**: pyproject.toml は src レイアウト
  （`packages.find where = ["src"]`、pytest `pythonpath = ["src"]`）のため、
  `scripts/` はもちろんプロジェクトルート直下の別ディレクトリでも、パッケージに含まれず
  テスト・利用者双方に sys.path 操作を強いる。`src/jpoke/players/` なら
  `from jpoke.players import TreeSearchPlayer` の一文で完結する（FW-U4 解消）。
- **内部 API への依存が規約に適合する**: `battle.command_manager` 直呼び等の3操作
  （FW-D1）は、パッケージ内に入れば CLAUDE.md の「直呼びは `src/jpoke` 内部実装に限る」
  の範囲内となり、エンジン変更時も同一パッケージ内で一緒に保守される。
- **ディレクトリ名は複数形 `players/`**: 単数 `player/` は基底クラスを持つ
  `jpoke.core.player` と紛らわしい。複数形なら、`tree_search_2.py` 内に使い捨て定義されている
  `RandomPlayer` のような方策実装を今後集約する置き場としても据わりが良い。
- 計画書自身が「再利用ニーズが出た段階で `src/jpoke/` へ昇格。その場合 CLAUDE.md の
  アーキテクチャ表への追記とテストの整備が必要」と昇格条件を定めており、
  テストが sys.path ハックを常用している現状はその条件を満たしている。

### 作業項目

1. `src/jpoke/players/`（`__init__.py` + `tree_search_player.py`）を新設し、
   `framework.py` の内容（`TreeSearchPlayer` / `default_fallback` / `hp_ratio_evaluate`）を移動
2. `scripts/tree_search/tree_search_1〜4.py` と `tests/test_tree_search_framework.py` を
   `from jpoke.players import TreeSearchPlayer` に書き換え（sys.path ハック削除）
3. `scripts/tree_search/framework.py` を削除
4. CLAUDE.md のアーキテクチャ表に `players/` の行を追加
5. docstring・コメント内の計画書リンクを `docs/plan/archives/` の現パスに修正（FW-D4 と同時解消）
6. 本ファイルの該当指摘（FW-U4・FW-D1・FW-D4）に解消済みの注記を追加

残りの指摘（FW-U1〜U3, U6, FW-D2, D5）は昇格後の `jpoke.players` の公開 API として設計する。

---

## 5. 推奨対応の優先順位

| 優先 | ID | 内容 | 規模 |
|---|---|---|---|
| 1 | FW-U4・FW-D1・FW-D4 | `src/jpoke/players/tree_search_player.py` への昇格（4章。他の改善の土台） | 中 |
| 2 | FW-U2 | `default_fallback` を `battle.random.choice` に変更（再現性バグ。昇格と同時に実施） | 1行 |
| 3 | FW-U1 | 相手合法手が空のときの退化を検知し、推定手フック or 明示的フォールバック＋文書化 | 小 |
| 4 | FW-D2 | `run_faint_switch()` の非進行ガード（エンジン側。昇格とは独立に実施可能） | 中 |
| 5 | FW-U3/U6 | ノード数カウンタ・上限、評価値一覧の公開メソッド | 中 |
| 6 | FW-U4残 | `configure_sim` フック追加（探索専用の決定論化オプション） | 小 |
| 7 | FW-D1残 | `Battle.detach_observation()`（仮称）で内部 API 依存を1メソッドの契約に集約（任意） | 中 |
| 8 | FW-D3 | sim 内の相手モデル差し替え機構（実戦投入時に再検討） | 大・別計画 |

FW-U5・FW-D5 は上記対応時に docstring・テストとして併せて解消するのが効率的。

---

## まとめ

フレームワークは「評価関数を差し替えるだけで木探索プレイヤーが作れる」という
計画書の目標を達成しており、再入検知・バグ回避の設計品質は高い。改善は
**`src/jpoke/players/tree_search_player.py` への昇格を土台**に進める（4章）。

- **利用者視点**では「相手の手が未公開だと探索が無言で退化する」（FW-U1、動作確認済み）が
  実対戦の初手で必ず発生する最大の穴であり、`default_fallback` の再現性バグ（FW-U2）と
  合わせて、実際に bot を書き始めた利用者が最初に踏む問題になっている。
  昇格により import の敷居（FW-U4）も同時に消え、`from jpoke.players import TreeSearchPlayer`
  が bot 開発の公式な入口になる。
- **開発者視点**では、フレームワークが内部 API 直呼び3箇所の上に成立している構造（FW-D1）が
  最重要だったが、これも昇格により「パッケージ内部実装間の結合」として規約に適合する。

---

## 追記（2026-07-07）: フック引数をコンストラクタ注入からオーバーライド可能なメソッドへ変更

本レビューが前提としていた `evaluate` / `fallback` / `opponent_estimator` / `configure_sim` は、
当初コンストラクタに渡す関数（`Callable[[Battle, Player], float]` 等）として設計・実装したが、
実際の利用（`scripts/fuzz_battle.py --player tree_search` の `TreeSearchFuzzPlayer`）は `TreeSearchPlayer` を
継承した上で `super().__init__(fallback=lambda ...)` のように1つのフックのためだけに
コンストラクタ引数を経由する必要があり、「利用者は継承して使う」という前提と
「差し替えは関数注入」という設計が食い違っていた。

`src/jpoke/players/tree_search_player.py` を Template Method パターンに変更し、
4つのフックを全てオーバーライド可能なメソッド（`evaluate(battle)` / `fallback(battle)` /
`opponent_estimator(battle, opponent)` / `configure_sim(sim)`）に変更した。
既定実装（旧 `hp_ratio_evaluate` / `default_fallback` 相当、`opponent_estimator`・
`configure_sim` は何もしない no-op）はメソッド本体にそのまま残し、`hp_ratio_evaluate`・
`default_fallback` という独立関数とその型エイリアス（`EvaluateFn` 等）は削除した。

この変更で1つ潜在バグが顕在化し同時に修正した: `opponent_estimator` が「未指定
（`None`）」から「既定は no-op メソッド」に変わったことで、`_toplevel_commands()` が
無条件に `_resolve_estimated_commands()`（`CommandManager.get_available_action_commands()`
を直接呼ぶ）を呼ぶと、推定を一切行っていなくても「技候補が0件ならわるあがきを補う」
という `CommandManager` 側の挙動により `opponent_commands` が非空になり、
FW-U1 で意図した「未公開なら fallback へ委譲」が壊れてしまう。
`type(self).opponent_estimator is not TreeSearchPlayer.opponent_estimator` で
オーバーライドの有無を判定し、オーバーライドされている場合のみ推定・再列挙を行うことで解消した
（`_has_opponent_estimator()`）。
  エンジン公開 API への吸収（`detach_observation()`）は、第2の探索実装や外部利用者が
  現れた時点の任意改善に格下げする。エンジン側に残る本質的な課題は
  `run_faint_switch()` の非進行ガード（FW-D2）と、実戦投入時に必要になる
  sim 内の相手モデル差し替え機構（FW-D3）の2点。
