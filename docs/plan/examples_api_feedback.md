# examples/ 作成から見えたAPIフィードバック

作成日: 2026-07-11

## 運用ルール

- 本ドキュメントの項目は `[ ]` / `[x]` のチェックリスト形式で管理する。`[x]` は
  「実装対応済み」または「検討のうえ対応しないと決定した（見送り確定）」の両方を含み、
  `[ ]` は「まだ判断・対応していない」項目を指す。チェックを付けたら、その項目の末尾に
  `→ 対応内容 (日付)` を追記する
- **妥当と判断したフィードバックは、判断した時点で即座にsonnet sub agentへ実装を委任する**。
  本体（Fable）は仕様の精査・妥当性判断・差分レビュー・PR操作を担当し、実装・テスト・
  検証はsonnetサブエージェント（`Agent` ツール、`model: sonnet`、`isolation: "worktree"`）に
  詳細な指示書付きで委任する。1件ずつ都度サブエージェントに投げてよく、まとめて
  バッチ実行する必要はない（関連メモ: `feedback_sonnet_subagent_for_work`）

## 教材としての質

- [x] 難易度勾配（01→06）は概ね適切。01/02で進行、03で方策、04で計算、05で探索、06で統計と段階的に積み上がっており、各docstring冒頭の「jpoke で学べること:」統一フォーマットも良い。（対応不要・肯定的所感）
- [x] 04（ダメージ計算）は03（カスタム方策）と05（木探索）のAI系列に割り込む配置。ユースケース別に独立した題材なので現状でも許容だが、AI開発の連続性を優先するなら 03→05 を隣接させ、04を後ろに回す選択肢もある。（見送り確定: フィードバック自身が「現状でも許容」としており、連番・README対応表への影響に見合わないため据え置き。2026-07-12判断）
- [x] 02 のループ内コメント（瀕死→自動交代の説明3行）はループ本体より長く、docstringへ移した方が読みやすい。05 のdocstringは `src/jpoke/players/...` を参照させているが、「clone不要で動く」前提の読者はソースを持っていないため、参照先はGitHub URLかAPIドキュメントにすべき。（→ 2026-07-11 f41f4df5で対応済み）
- [x] 「次に何を試すか」の誘導が弱い。各サンプル末尾に1行の「試してみよう」（例: 01→技を変える、03→評価関数にHP割合を加える、06→n_battlesや構成を変える）があると学習動線が明確になる。（→ 2026-07-11 examples 01〜06全てに追加）
- [x] examples/README.md の対応表（ファイル/学べる内容/ユースケース）は簡潔で分かりやすい。ルートREADMEのユースケース記述と用語（戦術研究・AI開発・ダメージ計算ツール開発）が揃っている点も良い。（対応不要・肯定的所感）
- [x] 06 の `build_player(item_name, item_name)` は username にアイテム名を渡しており、初見では引数の取り違えに見える。`build_player(username=..., item_name=...)` とキーワード渡しにするだけで誤読が消える。（→ 2026-07-11 f41f4df5で対応済み）

## 公開APIの使い勝手

- [x] `Player.team` への追加方法が `.append()`（01,03,05,06）と `= [...]` 代入（02,04）で混在。どちらも動くが教材として一貫性がなく、また `team` が素のlistのため6匹超過などの検証が入らない。`add_pokemon()` 等の正規ルートを1つ定めるか、examples内だけでも書式を統一したい。（→ 2026-07-11/12 `Player.add_pokemon()` を新設し、examples全体で統一）
- [x] `player.team` はコンストラクタ時点のスナップショットで対戦中は更新されず、対戦中の状態は `battle.get_active(player)` で取る必要がある（03のコメントで補足している通り）。「自分のチームなのに戦況が反映されない」のは学習者が最初に踏む罠で、docstringだけでなくAPIリファレンスでの明示が必要。（未対応: examples/03のコード内コメントのみで、`Player.team`属性のdocstring自体には未反映）（→ 2026-07-12 `Player` の `Attributes:` の `team` 説明にスナップショットである旨と `battle.get_active(player)` / `battle.get_team(player)` への誘導を追記）
- [x] 場のポケモンの取得方法が `battle.get_active(player)`（03）と `battle.actives[0]`（04）の2通り登場する。相手チーム参照に至っては `battle.player_states[battle.opponent(self)].team`（05）と内部構造に踏み込んでおり、「外部APIはBattleの公開メソッドを入口にする」方針と齟齬がある。`battle.get_team(player)` のような公開アクセサが欲しい。（→ 2026-07-11 `Battle.get_team()` を新設し、examples全体で`get_active`/`get_team`に統一）
- [x] `Pokemon.__init__` の暗黙デフォルトが多い: `nature="まじめ"`, `level=50`, `move_names` 省略時は `["はねる"]`, `ability_name=""`, IV31/EV0。特に「技を渡さないとはねるになる」「特性が空文字で何になるか」はコードから読み取れず、docstringでの明記かクラスメソッド（例: `Pokemon.simple(...)`）での整理を検討したい。（→ 2026-07-11 docstringに明記して対応。代替コンストラクタは`add_pokemon()`が実質的に代替するため追加実装は見送り）
- [x] `n_selected` のデフォルト3とチーム1匹構成の組み合わせは、01のように毎回 `n_selected=1` を明示する必要がある。省略時に「min(3, len(team))に自動調整」する方が導入体験は滑らか。（→ 2026-07-11 自動調整を実装）
- [x] `Command` から技実体への到達が `mon.moves[command.index]` という2段の間接参照（03）。`command` 自体が技を知らないため学習者が `index` の意味を推測する必要があり、`battle.get_move(command)` のようなヘルパーがあると方策実装が書きやすい。（見送り確定: 優先度メモに含まれず「検討したい」止まりのため、今回は対応しない。2026-07-12判断）

## 既知のバグ・要修正候補

- [x] `Battle(seed=None)` が `int(time.time())`（秒精度）にフォールバックする（`src/jpoke/core/battle.py:155`）。`battle_against(n_battles=30)` をseed省略で呼ぶと30戦全てが同一seedになり勝率が0%/100%に張り付く。対応案: (1) フォールバックを `time.time_ns()` または `Random(None)`（OSエントロピー）に変更、(2) `battle_against` 側で `seed` 指定時は対局ごとに `seed+i` の派生seedを振る。両方入れれば `examples/06` のワークアラウンド（n_battles=1×ループ）を素直な `battle_against(..., n_battles=30)` に書き戻せる。（→ 2026-07-11 `secrets.randbits(32)` に変更 + `battle_against`の対局別seed派生を実装）
- [x] デフォルト `Player.choose_command()` が「利用可能なコマンドの先頭を選ぶ」決定的挙動である点は、seedを変えても同一展開になりやすく、06のような統計比較の分散を殺す方向に働く。ベースラインとしてランダム選択（05の `RandomPlayer` 相当）を標準提供するか、既定挙動をdocstringで強調すべき。（未対応）（→ 2026-07-12 `jpoke.players.RandomPlayer` を新設（`battle.random` ベースで `Battle(seed=...)` の再現性を保つ）。examples/05のローカル定義を置き換え、`Player.choose_command()` のdocstringにも既定実装が決定的である旨と `RandomPlayer` への誘導を追記）

## 優先度メモ

1. [x] **seed フォールバックの修正 + battle_against の対局別seed派生**（上記バグ）。統計的に誤った結果を静かに返す罠であり、examples/06 の注意書きと歪んだ書き方を解消できるため最優先。（→ 2026-07-11 対応済み）
2. [x] **対戦中状態へのアクセスAPI整理**（`get_active` / `actives` / `player_states` の一本化と `get_team` 追加）。教材3本にまたがって説明コメントが必要になっている＝学習コストが最も高い箇所。（→ 2026-07-11 対応済み）
3. [x] **`n_selected` の自動調整（min(3, len(team))）**。全サンプルで `n_selected=1` の明示とコメントが必要になっており、導入の最初の1行目の摩擦を減らせる。（→ 2026-07-11 対応済み）

## 再レビュー指摘（2026-07-12 Fableサブエージェント、PR #38差分）

- [x] `tests/moves_attack/test_move_ha.py` の `test_はたきおとす_相手のアイテムがないとき威力補正なし` が同種のflakiness（急所のブレでダメージ比較が逆転しうる）を持つとMonte Carlo実測（300回中8回失敗）で指摘 → `fix_random()` を追加して解消
- [x] `Battle.roll_damage()` の `int(random() * len(damages))` が `random()==1.0` の境界（一部テストが `battle.random.random = lambda: 1.0` を使用）でIndexErrorになり得ると指摘 → `min(index, len(damages)-1)` のクランプを追加
- [x] `examples/README.md` の01の説明が `Pokemon` importなし化に追従していなかったと指摘 → 修正
- [x] `n_selected` 自動調整のdocstringに「チーム間で手持ち数が異なっても両者に同じ値が適用される」旨の追記が必要と指摘 → 追記
- [x] `battle_against` のdocstringに「複数opponent指定時は対戦通番がopponentごとにリセットされ、同じseed系列を使い回す」旨の追記が必要と指摘 → 追記
- [x] （付随発見・スコープ外）`tests/abilities/test_ability_a.py:667`（いかりのつぼ）で `random()==1.0` 固定時に技自体がミスして意図せず空虚に合格する既存の問題を発見 → 今回の変更が原因ではなく、examples APIフィードバック対応のスコープ外のため見送り確定

## 実施記録（詳細ログ）

### 2026-07-11 実装（優先度メモ1〜3 + 教材としての質）

- `Battle(seed=None)` のフォールバックを `secrets.randbits(32)`（OSエントロピー）に変更。
  `Player.battle_against(..., seed=...)` は対戦ごとに `seed + 対戦通番` の派生シードを
  自動的に使うよう変更し、examples/06 のワークアラウンド（seedを手動でずらすループ）を
  `battle_against(..., n_battles=N, seed=1)` の素直な呼び出しに戻した
  - 副作用として、`Battle.roll_damage()` の通常ロール抽選が `random.choice()`
    （`getrandbits()` 依存）だったため、テストヘルパー `fix_random()`（`random()` のみ固定）
    では制御できず、seedの高エントロピー化により一部テストが乱数依存で不安定化することが
    判明した。`roll_damage()` の抽選を `random.random()` ベースに変更し、`fix_random()` で
    完全に制御できるようにして解消（`tests/moves_attack/test_move_ma.py` の1件は
    `fix_random()` 追加で対応）
  - さらに `critical_mode="確定のみ"` は「急所を確定させる」設定ではなく「急所レート
    計算を特性等の割り込みなしの基礎値のみにする」設定で、急所に当たるか自体は
    引き続き `random.random()` の実ロールに依存すると判明。`damage_roll="最大"` /
    `critical_mode="確定のみ"` だけに頼り `fix_random()` を使っていなかった
    `test_move_ta.py`（DDラリアット×2）・`test_move_sa.py`（ソーラービーム×2）の
    比較系テストが急所のブレで偶発的に失敗し得たため、`fix_random()` を追加して解消。
    フルテストスイートを10回超連続実行して再発しないことを確認済み
- `Battle(n_selected=None)` を `min(3, 各プレイヤーの手持ち数)` に自動設定するよう変更。
  全examplesから冗長な `n_selected=1`/`n_selected=3` の明示を削除
- `Battle.get_team(player)` を追加し、examples/05 の
  `battle.player_states[battle.opponent(self)].team` を置き換え。examples/04 の
  `battle.actives[0]` も `battle.get_active()` に統一
- 各サンプル末尾に「試してみよう」の1行コメントを追加（01/02/03/04/05/06）
- `Player.team` への追加方法を `.append()` に統一（02, 04 の `= [...]` 代入を書き換え）
- `Pokemon.__init__` のdocstringに暗黙のデフォルト（性格・レベル・特性・技・個体値/努力値）を明記
- ユーザー指摘により、`Player.add_pokemon(name, **kwargs)` を新設。`Pokemon` を直接
  importせずにチームを組めるようにし、examples全体で `from jpoke import ... Pokemon` の
  importと `team.append(Pokemon(...))` を置き換えた（教材としての質・公開APIの使い勝手
  双方の指摘に対応）
- 04の防御側表示も `defender_player.team[0]` から `battle.get_active(defender_player)` に統一

### 2026-07-12 再レビュー対応

PR #38 の差分に対して再度Fableモデルでレビューを受け、上記「再レビュー指摘」の内容を修正した。

### 2026-07-12 残り2項目の実装（`player.team`スナップショット警告 + `RandomPlayer`新設）

- `Player`（`src/jpoke/core/player.py`）の `Attributes:` の `team` 説明に、対戦中は
  更新されないスナップショットであることと、対戦中の実際の状態は
  `battle.get_active(player)` / `battle.get_team(player)` を使うべき旨を追記
- `src/jpoke/players/random_player.py` に `RandomPlayer(Player)` を新設。
  `battle.random.choice(battle.get_available_commands(self))` で選ぶ実装で、
  `examples/05_tree_search_ai.py` に元々ローカル定義されていたものと同等
  （`battle.random` を使うため `Battle(seed=...)` の再現性を壊さない）
- `src/jpoke/players/__init__.py` に `RandomPlayer` を追加してエクスポート
- `Player.choose_command()` のdocstringに、既定実装が決定的（常に先頭のコマンドを
  選ぶ）である旨と、統計比較などで分散が必要な場合は `jpoke.players.RandomPlayer`
  を使うとよい旨を追記
- `examples/05_tree_search_ai.py` のローカル `RandomPlayer` 定義を削除し、
  `from jpoke.players import RandomPlayer` に置き換え（未使用になった `Player` /
  `Command` importも削除）
- `CHANGELOG.md` の `[Unreleased]` / `### Added` に `RandomPlayer` の追加を記載
- `tests/test_poke_env_compat.py` に `RandomPlayer` のテストを2件追加
  （選択コマンドが常に `get_available_commands()` に含まれること、
  `battle.random` 経由で同一seedなら同一コマンド列を再現すること）。
  `scripts/sort_tests.py` / `scripts/generate_test_list.py` を実行し、
  フルテストスイートを3回連続実行して全件成功・非flakyを確認済み
  （worktree分離環境ではeditable installが別チェックアウトの`src`を指すため、
  `tests/test_examples_smoke.py`（サブプロセス起動によるスモークテスト）を
  検証する際は `PYTHONPATH=<worktree>/src` を明示してworktree内の実装を
  優先させる必要があった。mainマージ後は不要な手当て）
