# 木探索サポート — 実態調査・レビュー

日付: 2026-07-05
対象: `Battle.step()` / `Player.choose_command()` を中心とした、方策関数内での木探索（先読みシミュレーション）サポート機構
関連ファイル: `core/battle.py`, `core/turn_controller.py`, `core/command_manager.py`,
`core/player.py`, `core/player_state.py`, `core/observation_builder.py`,
`core/switch_manager.py`, `core/query.py`, `utils/copy_utils.py`,
`scripts/tree_search/tree_search_1.py`〜`tree_search_4.py`

---

## 1. 実態（現状のドキュメント化）

### 1.1 何を指しているか

`Player.choose_command(battle)` の実装（方策関数）の中で、`battle.copy()` で盤面を複製し、
`sim.step(commands)` で明示コマンドを与えて1手先を展開する、という使い方をコードベースが
前提として設計されている。この「木探索」自体の探索アルゴリズム（MCTS・minimax・αβ等）は
コードベースに実装されておらず、`Battle`/`Player`/`CommandManager` 側は以下4点の基盤のみを
提供する。

1. 軽量な状態複製（`Battle.copy()`）
2. 情報隠蔽つきの観測複製（`Battle.build_observation(observer)`）
3. 合法手の列挙（`Battle.get_available_commands(player)`）
4. 明示コマンドでの1ターン進行（`Battle.step(commands)`）

### 1.2 `Battle.step()` の分岐

**`src/jpoke/core/battle.py:444-462`**

```python
def step(self, commands: dict[Player, Command] | None = None):
    if self.is_new_turn() and commands is None:
        # is_new_turn()だけで判定すると、行動コマンド選択時の木探索で
        # resolve_action_commands()が再帰的に呼ばれてしまうため、
        # command is Noneのガードが必要。
        commands = self.resolve_command("action")
    else:
        for player in self.players:
            command = commands.get(player)
            if not self.command_manager.validate_command(player, command):
                raise ValueError(f"Invalid command type for {player.name}: {command}.")

    if not commands:
        raise ValueError("No commands provided for step().")

    self.turn_controller.step(commands)
```

- `commands=None`（実対戦の通常経路）: `is_new_turn()`（`battle.py:581-587`、`not has_interrupt()`）
  が真の場合のみ `resolve_command("action")` を呼び、各プレイヤーの `choose_command()` を
  自動解決する。
- `commands={...}`（木探索が使う経路）: 木探索側が「この手の組み合わせで進めたい」と
  明示するための経路。`validate_command()`（`command_manager.py:164-180`）で
  `player_states[player].required_command_type` と型が一致するか検証してから
  `turn_controller.step(commands)` に委譲する。
- `commands is None` のガードが必須な理由: これを `is_new_turn()` のみにすると、
  木探索が「新しいターンの開始状態」を明示コマンド付きで `sim.step(commands)` した際に、
  渡した `commands` が `resolve_command("action")` の呼び出し結果で**上書き**され、
  木探索が指定した手ではなく `choose_command()` を再度呼んだ結果が使われてしまう
  （＝木探索の分岐指定が意味をなさなくなる）。このガードが、木探索での
  「盤面を複製して明示コマンドで進める」という使い方を成立させる要。

### 1.3 状態複製（`Battle.copy()` / `__deepcopy__`）

**`battle.py:141-210`**, **`utils/copy_utils.py`**

- `Battle.copy() -> Battle`（`battle.py:209-210`）は `deepcopy(self)` を呼ぶだけ。
- `__deepcopy__`（`battle.py:141-186`）は `fast_copy()`（`utils/copy_utils.py:9-25`）を使い、
  `keys_to_deepcopy` に列挙された属性（`random`, `_player_states`, 各種マネージャー）のみを
  真にディープコピーし、それ以外は `recursive_copy()`（同ファイル28-42行目）でリスト/辞書は
  再帰的に新規コンテナ化、それ以外（`players` タプル、`observer`、`copy_depth` 等の
  スカラー値・`Player` 参照）は**同一オブジェクト参照のまま**引き継ぐ。
  - `players`（タプル）が参照共有されることで、`commands: dict[Player, Command]` の
    キーとしての `Player` 同一性がコピー後も保たれる（木探索が
    `{self: my_cmd, opponent: opponent_cmd}` を作れる前提）。
  - `copy_depth`（int）は `fast_copy()` 後に `new.copy_depth += 1` で明示的にインクリメントされる
    （`battle.py:184`）。木探索の再帰深さを `choose_command()` 側が検知するためのカウンタ。
  - `random`（`random.Random` インスタンス）は `keys_to_deepcopy` に含まれ真にディープコピーされる。
    これにより、複製後のシミュレーションは元の乱数状態を引き継ぎつつ、複製後の消費が
    元の `Battle` の乱数状態に影響しない（枝ごとに独立した乱数系列で分岐できる）。

### 1.4 観測複製（情報隠蔽）— `build_observation()`

**`battle.py:221-242`**, **`core/observation_builder.py`**

- `Battle.build_observation(observer) -> Battle`（`battle.py:221-234`）:
  `self.is_observation()`（`observer is not None`）が真ならただの `self.copy()`、
  そうでなければ `observation_builder.build(self, observer)` に委譲して相手情報を隠蔽した
  コピーを作る。
- `observation_builder.build()`（`observation_builder.py:15-31`）: `deepcopy(battle)` した上で
  `new.observer = observer` をセットし、`_mask(new, opponent)` で相手の性格・努力値・
  未公開の特性/アイテム/技/テラスタイプを隠蔽し、`_mask_command()`（134-176行目）で
  観測用の合法手リスト（`state.last_available_commands`）を再構築する。
- **重要な性質**: `is_observation()` が真になったコピーに対して以降 `build_observation()` を
  何度呼んでも `_mask()` は再実行されない（`self.copy()` を返すだけ）。つまり、実対戦の
  トップレベル `resolve_command()` が呼ぶ最初の1回の `_mask()` 以降、木探索が
  `sim = battle.copy(); sim.step(commands)` をどれだけ再帰的に繰り返しても、
  途中の割り込み交代（瀕死・だっしゅつボタン・とんぼがえり等）で再度 `choose_command()` が
  呼ばれる際は `_mask()` を経由せず**単純コピーのみ**が行われる。

### 1.5 合法手の列挙 — `get_available_commands()`

**`battle.py:396-415`**

```python
def get_available_commands(self, player: Player) -> list[Command]:
    if self.observer == self.opponent(player):
        return self.player_states[player].last_available_commands
    match self.phase:
        case "action":
            return self.command_manager.get_available_action_commands(player)
        case "switch":
            return self.command_manager.get_available_switch_commands(player)
    raise ValueError(f"Invalid phase: {self.phase}")
```

- 自分（`observer`）自身の合法手は常に**ライブ計算**（現在の `phase` に応じて
  `CommandManager` に委譲）。
- 相手（`self.observer == self.opponent(player)` が真になるケース）の合法手は、
  `resolve_command()` が呼ばれた時点でスナップショットされた
  `state.last_available_commands` を返す（＝相手の「今まさに使える手」をライブ計算はしない。
  盤面が相手の手を知らない体で固定された情報を返す）。

### 1.6 `required_command_type` — 木探索が補うべきコマンド種別

**`player_state.py:22-23`**, **`command_manager.py:135-162`**, **`observation_builder.py:134-176`**

- `PlayerState.required_command_type: CommandType | None`
  （コメント: 「木探索を行う際に補完すべきコマンドタイプ（Noneの場合は補完不要）」）。
- `CommandManager.resolve_command()`（`command_manager.py:135-162`）は、`choose_command()` を
  呼ぶ直前に対象プレイヤー（複数可）の `required_command_type` を
  `"any"`（action フェーズ）または `"switch"`（switch フェーズ）に設定する。
- `observation_builder._mask_command()`（`observation_builder.py:134-176`）は、観測構築時に
  **相手側**の `required_command_type` を以下のルールで再設定する:
  - `phase == "action"` → `"any"`
  - `phase == "switch"` かつ相手が `query.is_second_actor()` かつ生存中 → `"move"`
    （＝相手はまだ今ターンの「技」コマンドを提出していないはずだと明示する）
  - それ以外 → `None`
  - 同時に `state.clear_reserved_commands()` で相手の（実際にはもう決定済みの）予約コマンドを
    観測上は消去する。これにより、とんぼがえり等で先攻が中断的に交代先を選ぶ局面で、
    「後攻の相手が実際にはどの技を選んでいたか」は木探索から見えなくなる
    （imperfect information の再現）。
- `CommandManager.validate_command()`（`command_manager.py:164-180`）は `sim.step(commands)`
  実行時に、各プレイヤーのコマンドが `required_command_type` と一致するかを検証する
  （`None`/`"any"` は無条件許可）。

### 1.7 参照実装 — `scripts/tree_search/`

`Player` をサブクラス化し `choose_command()` 内で `itertools.product` による総当たり1手探索を
行うデモが4本ある。いずれも探索アルゴリズム本体（評価関数・再帰的なミニマックス等）は
持たず、「1手先だけ展開してログを表示する」動作確認用スクリプト。

| ファイル | シナリオ | `copy_depth > 1` 時の挙動 |
|---|---|---|
| `tree_search_1.py` | 通常の行動コマンド選択 | `raise ValueError`（深さ2以上は未対応として例外） |
| `tree_search_2.py` | 自分が先攻でとんぼがえり使用（switch フェーズでの相手手の列挙） | `raise ValueError` |
| `tree_search_3.py` | 両者同時に瀕死交代 | `raise ValueError` |
| `tree_search_4.py` | 「一般的な木探索」 | `random.choice()` にフォールバック |

### 1.8 決定論化のための補助機構

- `Battle.seed` / `Battle.random`（`battle.py:104-106`）: シード指定でバトル全体を再現可能にする。
- `TestOption`（`battle.py:45-61`）: `accuracy` / `trigger_ailment` / `trigger_volatile` /
  `secondary_chance` を固定できる。木探索の評価時に確率分岐を打ち切りたい場合に使える。
- `tests/test_utils.py` の `fix_damage()` / `fix_random()`（278-295行目付近）:
  ダメージ乱数・汎用乱数を固定値化するテスト用ヘルパー。木探索の評価関数を書く際の
  決定論化パターンとして流用できる。

---

## 2. レビュー

### CRIT-1（新規・解消済み）: `get_available_commands()` が相手の合法手を `required_command_type` でフィルタしないため、参照実装の総当たり探索が `sim.step()` の `ValueError` で落ちる

**対応**: `observation_builder._mask_command()` の末尾で `state.last_available_commands` を
`required_command_type`（`None`/`"any"` 以外）でも絞り込むよう修正した（推奨対応1を採用）。
回帰テスト: `tests/test_copy.py::test_木探索用の観測でswitchフェーズ中の相手コマンドがrequired_command_typeでフィルタされる`。
詳細設計は `.internal/plan/archives/tree_search_framework.md` を参照。

**ファイル**: `src/jpoke/core/battle.py:396-415`（`get_available_commands`）、
`src/jpoke/core/observation_builder.py:134-176`（`_mask_command`）、
`src/jpoke/core/command_manager.py:164-180`（`validate_command`）

`_mask_command()` は相手の `required_command_type` を `"move"`（フェーズが `switch` かつ
相手が後攻かつ生存中）に絞り込むが、同時に返す `last_available_commands` 自体は
**公開状況（`revealed`）のみでフィルタし、コマンド種別ではフィルタしない**
（`observation_builder.py:156-175`）。したがって、相手のベンチに「公開済みで生存している」
控えポケモンが1匹でもいると、switch フェーズで `battle.get_available_commands(opponent)` は
`SWITCH_x` を含んだリストを返し続ける。木探索側がこれを `required_command_type` で
絞り込まずにそのまま `itertools.product()` へ渡すと、`sim.step({..., opponent: SWITCH_x})` は
`validate_command()`（`required_command_type == "move"` のため `SWITCH_x.is_type("move")`
が `False`）に弾かれ `ValueError: Invalid command type for ...` で例外になる。

**再現**（`tree_search_2.py` とほぼ同一の盤面で、相手のベンチを「公開済み」にしただけ）:

```python
player2.team[1].revealed = True  # ベンチのカメックスを公開済みにする
...
battle.step()
```

```
required_command_type(opponent)= move
opponent_commands= ['SWITCH_1']
...
ValueError: Invalid command type for RandomPlayer: SWITCH_1.
```

`tree_search_2.py` 自体が偶然クラッシュしないのは、そのスクリプトの相手チームの
ベンチ（`カメックス`）が明示的に `revealed` 化されていない（＝まだ一度も場に出ていない）
という盤面固有の事情によるものであり、根本原因は解消されていない。
実戦（対戦が数ターン進み、双方が switch 済みでベンチが公開されている状態）では
とんぼがえり／だっしゅつボタン／瀕死交代のいずれの中断的な交代局面でも高確率で発生しうる。

**影響**: `scripts/tree_search/tree_search_1〜3.py` はいずれも
`opponent_commands = battle.get_available_commands(opponent)` を `required_command_type` で
絞り込まずに `product()` へ渡しており、同じ条件（相手ベンチが公開済み）で同一の
クラッシュが起きる。唯一 `tree_search_3.py` は `required_command_type is None`
（同時瀕死交代でどちらも「後攻」ではないため絞り込みが働かない）ケースを扱っており、
`None` は無制限に許可されるため今回のクラッシュ経路には該当しない。

**推奨対応**（いずれか）:
1. `get_available_commands()` 側（または `_mask_command()` が返す
   `last_available_commands` の構築時点）で `required_command_type` によるフィルタも
   適用し、「絞り込み済みの合法手」を返すようにする。
2. 現状の設計を維持するなら、`required_command_type` は「呼び出し側が
   `get_available_commands()` の結果をさらに手動でフィルタする責務を負う」ものだと
   明記し、`scripts/tree_search/` の全参照実装にそのフィルタ処理を追加する。

現状は「`required_command_type` という補助情報を提供しているが、それを使った
フィルタ処理をフレームワーク側もリファレンス実装側もどちらも行っていない」という
片手落ちの状態であり、木探索を書く利用者が同じ罠に必ず引っかかる。

---

### ISSUE-1（解消済み）: 参照実装4本のうち3本が `copy_depth > 1` で無条件 `raise` しており、中断的な交代が発生する盤面では実戦投入できない

**対応**: `src/jpoke/players/tree_search_player.py`（当時は `scripts/tree_search/framework.py`、
その後 `src/jpoke/players/` へ昇格）の `TreeSearchPlayer` に、`copy_depth` の
決め打ちの代わりに `_searching` インスタンスフラグ（`try/finally` で確実に解除）による
再入検知を実装し、`tree_search_1〜4.py` を全てこのフレームワークを使う形に置き換えた。
詳細は `.internal/plan/archives/tree_search_framework.md` を参照。

**ファイル**: `scripts/tree_search/tree_search_1.py:15-16`,
`scripts/tree_search/tree_search_2.py:16-17`,
`scripts/tree_search/tree_search_3.py:15-16`

3本とも `if battle.copy_depth > 1: raise ValueError("木探索の深さが2を超えています。")`
という形で、深さ2以上の再帰を「起きてはいけない事態」として例外にしている。しかし
1.4 節の通り、`sim.step(commands)` の内部でだっしゅつボタン・ききかいひ・瀕死交代などの
中断的な交代が発生すると、`switch_manager.run_interrupt_switch()` が
`resolve_command("switch", player)` 経由で当該プレイヤーの `choose_command()` を
**さらに深いネストで**呼び出す（`build_observation()` の `.copy()` 分だけ `copy_depth` が
加算される）。この時 `self` が中断的な交代を要求される側（例えば自分の後衛が道連れ等で
同時に瀕死になった、被弾で追加の交代が発生した等）だと、探索1手目の評価中にこの
`raise` が飛び、探索全体が例外で停止する。

`tree_search_4.py` のみ `battle.copy_depth > 1` を `random.choice()` へのフォールバックに
している（`tree_search_4.py:17-19`）ため、同種の状況でもクラッシュしない。3本の
`raise` は「このデモが扱うシナリオでは深さ2以上は起こらないはず」という前提の
アサーションであり、汎用的な木探索の実装例としては流用できない（コメントで
「このスクリプトの盤面設定に閉じたアサーションであり、他の盤面へ流用する際は
`tree_search_4.py` のフォールバック方式を使うこと」等の注記がないと、参照実装を
そのまま複製した利用者が同じ落とし穴にはまる）。

---

### NOTE-1: `.internal/review/code/core.md` CRIT-1（`OBSERVED_MOVE_INDEXES` グローバル辞書）は、木探索の再帰経路そのものからは実際には再入されない

**ファイル**: `src/jpoke/core/observation_builder.py:12,41-42`

既存レビュー（`core.md` CRIT-1）は「`Battle` が `copy_depth` を持つほど深いネストしたコピー・
観測構築を行う設計であることを踏まえると、将来『観測構築中にさらに観測構築を行う』ような
再入が発生した場合に破綻しうる」と指摘している。今回木探索の実際の呼び出し経路を
追った結果、この再入は**木探索の同期的な再帰だけでは発生しない**ことを確認した。
理由は 1.4 節の通り、`is_observation()` が真になった `Battle` に対する以降の
`build_observation()` 呼び出しはすべて `_mask()` を経由しない単純 `copy()` にしかならないため
（`battle.py:232-233`）。したがって:

- 木探索がどれだけ深く `sim.copy(); sim.step(commands)` を再帰させても、
  `_mask()`（グローバル辞書 `OBSERVED_MOVE_INDEXES` の read/write が発生する唯一の場所）が
  呼ばれるのは、実対戦のトップレベル `resolve_command()` が最初にプレイヤーごとに呼ぶ
  たかだか2回（各プレイヤー1回ずつ、逐次実行）のみ。
- この2回の呼び出しは `for ply in players: sim = battle.build_observation(ply); commands[ply] = ply.choose_command(sim)`
  というシーケンシャルなループ内で、1人分の `choose_command()`（内部の木探索の再帰を
  含めて全て）が完了してから次のプレイヤーの `build_observation()` が呼ばれるため、
  同一プロセス・同一スレッドで動く限り重なりようがない。

CRIT-1 の指摘自体（グローバル辞書という設計は脆く、明示的な引数渡しにすべきという設計上の
弱点）は妥当だが、「木探索の深いネストが実際にこの問題を顕在化させる」という懸念は
現状のシングルスレッド同期実行という前提では成立しない。真に懸念すべきは
（CRIT-1 自身も触れている）木探索実装をマルチスレッド化した場合のみであり、
マルチプロセス化（プロセスごとにグローバル変数が独立する）であれば無関係。
木探索を高速化する目的でスレッド並列化を行う場合にのみ、この既知の指摘が実害化する
点を明記しておく。

---

## まとめ

| 項目 | 該当箇所 |
|---|---|
| `Battle.step()` の明示コマンド経路 | `battle.py:444-462` |
| 状態複製（`copy()`/`__deepcopy__`） | `battle.py:141-210`, `utils/copy_utils.py` |
| 観測複製（情報隠蔽） | `battle.py:221-242`, `observation_builder.py` |
| 合法手列挙 | `battle.py:396-415` |
| `required_command_type` の設定・検証 | `command_manager.py:135-180`, `observation_builder.py:134-176` |
| 探索深さ検知 | `battle.py:108,184`（`copy_depth`） |
| 参照実装 | `scripts/tree_search/tree_search_1〜4.py` |
| **CRIT-1（新規）** | 相手の合法手がコマンド種別でフィルタされず `sim.step()` がクラッシュしうる |
| **ISSUE-1（新規）** | 参照実装3本の `copy_depth > 1` ガードが `raise` で実戦投入不可 |
| **NOTE-1** | `core.md` CRIT-1 は木探索の再帰経路単体では再入しないことを確認 |
