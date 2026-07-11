# examples/ 作成から見えたAPIフィードバック

作成日: 2026-07-11

## 教材としての質

- 難易度勾配（01→06）は概ね適切。01/02で進行、03で方策、04で計算、05で探索、06で統計と段階的に積み上がっており、各docstring冒頭の「jpoke で学べること:」統一フォーマットも良い。
- 04（ダメージ計算）は03（カスタム方策）と05（木探索）のAI系列に割り込む配置。ユースケース別に独立した題材なので現状でも許容だが、AI開発の連続性を優先するなら 03→05 を隣接させ、04を後ろに回す選択肢もある。
- 02 のループ内コメント（瀕死→自動交代の説明3行）はループ本体より長く、docstringへ移した方が読みやすい。05 のdocstringは `src/jpoke/players/...` を参照させているが、「clone不要で動く」前提の読者はソースを持っていないため、参照先はGitHub URLかAPIドキュメントにすべき。
- 「次に何を試すか」の誘導が弱い。各サンプル末尾に1行の「試してみよう」（例: 01→技を変える、03→評価関数にHP割合を加える、06→n_battlesや構成を変える）があると学習動線が明確になる。
- examples/README.md の対応表（ファイル/学べる内容/ユースケース）は簡潔で分かりやすい。ルートREADMEのユースケース記述と用語（戦術研究・AI開発・ダメージ計算ツール開発）が揃っている点も良い。
- 06 の `build_player(item_name, item_name)` は username にアイテム名を渡しており、初見では引数の取り違えに見える。`build_player(username=..., item_name=...)` とキーワード渡しにするだけで誤読が消える。

## 公開APIの使い勝手

- `Player.team` への追加方法が `.append()`（01,03,05,06）と `= [...]` 代入（02,04）で混在。どちらも動くが教材として一貫性がなく、また `team` が素のlistのため6匹超過などの検証が入らない。`add_pokemon()` 等の正規ルートを1つ定めるか、examples内だけでも書式を統一したい。
- `player.team` はコンストラクタ時点のスナップショットで対戦中は更新されず、対戦中の状態は `battle.get_active(player)` で取る必要がある（03のコメントで補足している通り）。「自分のチームなのに戦況が反映されない」のは学習者が最初に踏む罠で、docstringだけでなくAPIリファレンスでの明示が必要。
- 場のポケモンの取得方法が `battle.get_active(player)`（03）と `battle.actives[0]`（04）の2通り登場する。相手チーム参照に至っては `battle.player_states[battle.opponent(self)].team`（05）と内部構造に踏み込んでおり、「外部APIはBattleの公開メソッドを入口にする」方針と齟齬がある。`battle.get_team(player)` のような公開アクセサが欲しい。
- `Pokemon.__init__` の暗黙デフォルトが多い: `nature="まじめ"`, `level=50`, `move_names` 省略時は `["はねる"]`, `ability_name=""`, IV31/EV0。特に「技を渡さないとはねるになる」「特性が空文字で何になるか」はコードから読み取れず、docstringでの明記かクラスメソッド（例: `Pokemon.simple(...)`）での整理を検討したい。
- `n_selected` のデフォルト3とチーム1匹構成の組み合わせは、01のように毎回 `n_selected=1` を明示する必要がある。省略時に「min(3, len(team))に自動調整」する方が導入体験は滑らか。
- `Command` から技実体への到達が `mon.moves[command.index]` という2段の間接参照（03）。`command` 自体が技を知らないため学習者が `index` の意味を推測する必要があり、`battle.get_move(command)` のようなヘルパーがあると方策実装が書きやすい。

## 既知のバグ・要修正候補

- `Battle(seed=None)` が `int(time.time())`（秒精度）にフォールバックする（`src/jpoke/core/battle.py:155`）。`battle_against(n_battles=30)` をseed省略で呼ぶと30戦全てが同一seedになり勝率が0%/100%に張り付く。対応案: (1) フォールバックを `time.time_ns()` または `Random(None)`（OSエントロピー）に変更、(2) `battle_against` 側で `seed` 指定時は対局ごとに `seed+i` の派生seedを振る。両方入れれば `examples/06` のワークアラウンド（n_battles=1×ループ）を素直な `battle_against(..., n_battles=30)` に書き戻せる。
- デフォルト `Player.choose_command()` が「利用可能なコマンドの先頭を選ぶ」決定的挙動である点は、seedを変えても同一展開になりやすく、06のような統計比較の分散を殺す方向に働く。ベースラインとしてランダム選択（05の `RandomPlayer` 相当）を標準提供するか、既定挙動をdocstringで強調すべき。

## 優先度メモ

1. **seed フォールバックの修正 + battle_against の対局別seed派生**（上記バグ）。統計的に誤った結果を静かに返す罠であり、examples/06 の注意書きと歪んだ書き方を解消できるため最優先。
2. **対戦中状態へのアクセスAPI整理**（`get_active` / `actives` / `player_states` の一本化と `get_team` 追加）。教材3本にまたがって説明コメントが必要になっている＝学習コストが最も高い箇所。
3. **`n_selected` の自動調整（min(3, len(team))）**。全サンプルで `n_selected=1` の明示とコメントが必要になっており、導入の最初の1行目の摩擦を減らせる。
