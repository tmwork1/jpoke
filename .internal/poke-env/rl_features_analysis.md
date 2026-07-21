# poke-env の強化学習(RL)関連機能 調査書

調査日: 2026-07-21

## 結論（真偽）

**事実。しかも「一機能」ではなく poke-env の主目的そのもの。**

- PyPI/GitHub 双方の `pyproject.toml` で `description = "A python interface for training
  Reinforcement Learning bots to battle on pokemon showdown."` と明記されている（poke-env 0.15.0）。
- 実行時依存に `gymnasium>=1.0.0` と `pettingzoo>=1.24.3` を持つ。単なる「Gym風のオプション機能」
  ではなく、RL用ライブラリ（Farama Gymnasium / PettingZoo）をコア依存として組み込んでいる。
- 既存の `.internal/poke-env/compat_analysis.md` / `compat_plan.md`（属性・命名レベルの互換調査）は
  `Battle`/`Pokemon`/`Move`/`Player` の**データモデル**の互換性のみを扱っており、RL用の
  `PokeEnv`（Gymnasium/PettingZoo環境クラス）自体には触れていなかった。今回はその欠けていた部分の調査。

## poke-env の RL 関連 API

### モジュール構成（現行 `master`、0.15.0 時点で実機確認）

```
poke_env/environment/
  env.py               # PokeEnv 基底クラス（PettingZoo ParallelEnv を継承）
  singles_env.py        # SinglesEnv(PokeEnv[int64])
  doubles_env.py         # DoublesEnv(PokeEnv[ndarray])
  single_agent_wrapper.py # SingleAgentWrapper（標準 Gymnasium Env への単一エージェント化）
```

### `PokeEnv` の実体（重要な点）

- `class PokeEnv(ParallelEnv[str, Dict[str, Any], ActionType])` — **2体の `_EnvPlayer` を裏で
  Pokémon Showdown サーバーに接続させ**、その対戦を PettingZoo の `step()`/`reset()` API で
  ラップしたもの。`asyncio` イベントループを別スレッドで回し、`_AsyncQueue` で
  行動（`BattleOrder`）とバトル状態（`AbstractBattle`）をやり取りする。
- つまり **「サーバー不要の軽量シミュレータに Gym API を被せたもの」ではない**。内部は
  ネットワーク越しの実対戦そのものであり、`compat_analysis.md` §0 で整理済みの
  「実行基盤（要サーバー）」「通信方式（WebSocket）」「同期モデル（asyncio）」という
  poke-env の制約をそのまま引き継いでいる。

### 実装が必須の抽象メソッド

| メソッド | シグネチャ | 役割 |
|---|---|---|
| `calc_reward(battle) -> float` | インスタンスメソッド | 現在のバトル状態から報酬を計算 |
| `embed_battle(battle) -> Any` | インスタンスメソッド | バトル状態を観測ベクトル（Gymnasium互換形式）に変換 |
| `action_to_order(action, battle, fake, strict) -> BattleOrder` | staticmethod | 行動値→コマンド変換 |
| `order_to_action(order, battle, fake, strict) -> ActionType` | staticmethod | コマンド→行動値変換（逆方向） |
| `get_action_mask(battle) -> list[int]` | staticmethod | 合法行動のマスク配列 |
| `get_action_space_size(gen) -> int` | staticmethod | 世代別の行動空間サイズ |

### `SinglesEnv` の行動エンコーディング（int64 単一値）

```
-2: デフォルト行動   -1: 投了
 0-5:  交代（最大6体）
 6-9:  通常技（最大4）
10-13: メガシンカ+技
14-17: Z技+技
18-21: ダイマックス+技
22-25: テラスタル+技
```

`DoublesEnv` は行動が配列（各要素に -2〜2 のターゲット指定を追加）で、`get_action_mask_individual()`
で個別マスクも取れる。

### `reward_computing_helper()`（報酬シェーピングの標準実装）

`fainted_value` / `hp_value` / `status_value` / `victory_value` の重み付けで、**前回呼び出し時との
状態値の差分**を報酬として返す（`WeakKeyDictionary` でバトルごとに前回値を保持）。
`battle.won` / `battle.lost` を使うため、poke-env 側の `won`/`lost` が `bool | None` プロパティで
あることが前提になっている。

### 観測空間

`observation_spaces` に `Dict({"observation": embed_battleの型, "action_mask": Box(...)})` が
自動で組み立てられる（`__setattr__` オーバーライドで気づかれにくい形で注入されている）。
つまり **action masking が一級市民として組み込まれている**。

### シングル/マルチエージェント

- `PokeEnv` 自体は2エージェント同時対戦の `ParallelEnv`（マルチエージェントRL、self-play前提）。
- `SingleAgentWrapper` で「片方を固定オポーネントにした単一エージェントの標準 `gymnasium.Env`」
  に変換できる（一般的なRL入門はこちら経由）。

## jpoke の現状（RLの観点で何があり、何がないか）

**既にあるもの**

- `build_observation(observer)`（`compat_analysis.md` 分類D）— 相手の非公開情報を隠した
  部分観測ビューを明示的に取得できる。poke-env の「部分観測がデフォルト」という前提を、
  jpoke は「完全情報がデフォルトだが要求すれば部分観測に変換できる」という設計で担保済み。
- `TreeSearchPlayer` / `MinimaxPlayer`（`players/tree_search_player.py`, `minimax_player.py`）—
  探索ベースのAI基底実装。ただし学習（重み更新）は行わない静的評価関数ベース。
- `Command` Enum（型安全な行動表現）、`Battle.get_available_commands(player)`（合法手の列挙）—
  poke-env の `get_action_mask` に相当する情報は既に存在するが、**int⇔Command の固定エンコーディング
  としては未整備**（`available_moves`/`available_switches` は `list[Move]`/`list[Pokemon]` を返す
  互換propertyまでで止まっている。`compat_plan.md` Phase3）。
- `Player.battle_against()`（`compat_plan.md` Phase5、実装済み）— 同期的な一括対戦・戦績集計。
  RLの「多数エピソードを回す」用途にそのまま使える下地。
- `Battle.copy()` / ロールアウト — `examples/05_advanced/04_janken_nash_cfr.py` が
  `Battle.copy()` を使った自己対戦学習（CFR風のregret matching）を実演済み。**表形式の学習**
  （tabular RL）の実例は既にある。

**ないもの（poke-envのPokeEnvに相当する部分）**

1. **`gymnasium.Env` 互換のクラス**（`reset()`/`step()`/`action_space`/`observation_space` を
   Gymnasium仕様で持つラッパー）が存在しない。`Battle.step()` はあるが、これは戦闘ターン進行の
   意味で、Gym の `step(action) -> (obs, reward, terminated, truncated, info)` とは無関係。
2. **観測のベクトル化（`embed_battle` 相当）** — `build_observation()` は「jpoke Battleオブジェクトの
   部分観測コピー」を返すのみで、数値テンソル/配列への変換は利用者側に委ねられている
   （poke-envも同様に「利用者が実装する」設計だが、参考実装や助言用のヘルパーは一切ない）。
3. **報酬シェーピングのヘルパー**（`reward_computing_helper` 相当）— HP割合・瀕死・状態異常・勝敗を
   使った差分報酬というAPIとしての形はjpokeにない。`tod_score(alpha)`（分類D）はダメージレース評価用の
   スコアで、エピソード単位の報酬シェーピングとは目的が異なる。ただし構成要素の一部は既にある:
   `total_hp_ratio(battle, target)`（`players/tree_search_player.py`）が「チームの残りHP割合合計」を
   既に提供しており、`TreeSearchPlayer.evaluate()`（ミニマックス葉ノード評価、勝敗確定時は±inf）が
   これを使っている。RL用の報酬ヘルパー（`rl_support.md` の `calc_state_value`）はこの関数を
   再利用し、HP項の計算ロジックを二重実装しない設計にする（詳細は `rl_support.md` 論点4）。
4. **行動マスク配列としての出力**（`Command`自体は固定順Enumで実質int変換済みだが、
   `get_available_commands(player)` の結果を `Discrete(N)` 用の0/1マスク配列に変換する層は未整備）。
5. **`gymnasium`/`pettingzoo` への依存自体**（jpokeの実行時依存には一切なし。追加するかどうかも論点）。

## アーキテクチャ上の非対称性（見落としやすい点）

poke-env の `PokeEnv` は「RL向けの機能」を持っているが、その実体は**実サーバー対戦をGym APIで
ラップしただけ**であり、俊敏性・並列実行性能の面ではむしろ弱い（1ステップごとにネットワークI/O・
asyncioスレッド切り替えが発生する）。

一方 jpoke は既に「サーバー不要・同期・プロセス内関数呼び出しのみ」という、RL学習（大量ロールアウト
が必要）にとって本質的に有利な特性を持っている（README「計算速度」章: 1step 3.8ms、
`ProcessPoolExecutor` 並列化の実例も `examples/05_advanced/03_janken_nash_fictitious_play.py` に有）。
つまり **jpokeがGym互換ラッパーを提供すれば、poke-envより高速なRL環境になり得る** というのが
今回調査で見えた最大の機会。逆に言うと、RL対応の欠如は「本質的な設計の違いによる原理的な制約」では
なく「単に未実装」であるため、対応する価値がある可能性が高い。

## 検討: jpoke に必要な対応（選択肢）

### A案: 対応しない（現状維持）
- 理由: README「対象範囲」はチャンピオンズシングル対戦のシミュレーション・ダメージ計算が主眼で、
  RLフレームワーク自体の提供は明言されていない。`TreeSearchPlayer`/`MinimaxPlayer` や
  `janken_nash_cfr.py` の自己対戦学習実例で「AI開発」需要は既にある程度満たしている、という立場もありうる。
- リスク: poke-env ユーザーが「RL目的でjpokeに来たが最小限のGym Envもない」と離脱する可能性。
  `compat_plan.md`/`compat_analysis.md` を整備してpoke-env経験者の導線を作ってきた既存投資と矛盾する。

### B案: 外部ライブラリ非依存のRL支援ヘルパーを新設（推奨候補・ユーザー方針: 外部ライブラリは追加しない）

**ユーザー方針（2026-07-21確認）: `gymnasium`/`pettingzoo` 等の外部ライブラリは依存に追加しない。
その代わり、強化学習を始めるのに便利な機能（行動の列挙・マスク・観測ベクトル化・報酬ヘルパー）は
jpoke自身が素の Python（`dependencies = []` を維持）で提供する。**

- `gymnasium.Env` を継承するクラスは作らない。代わりに `reset()`/`step(action)` という
  gymnasium と同じ「形」のメソッドを持つが、返り値は `gymnasium.spaces.*` オブジェクトではなく
  素の `list[int]`/`dict`/`float`/`bool` のみで構成する薄いクラス（例: `RLBattleEnv`）を用意する。
  利用者が実際に `gymnasium.Env` を使いたい場合は、数行のアダプタ（`observation, reward,
  terminated, truncated, info = rl_env.step(action)` をそのまま右辺に流すだけ）で被せられる
  設計にする（＝gymnasium前提の学習コードとの互換性は保ちつつ、jpoke自体はimportしない）。
- 最小構成案:
  - **行動の列挙・マスク**: `enums/command.py` の `Command` はすでに `SWITCH_0..9` / `MOVE_0..9` /
    `TERASTAL_0..9` / `MEGAEVOL_0..9` / `GIGAMAX_0..9` / `ZMOVE_0..9` という固定順のEnumで、
    `index` プロパティ・`get_*_command(index)` classmethodまで揃っている。これに「固定サイズの
    行動空間（`Command`一覧に対応する整数レンジ）」「`get_available_commands(player)` から
    0/1マスク配列（`list[int]`、gymnasiumの`Box`は使わずただのlist）を作る関数」を追加すれば
    ほぼ完成する（ゼロから設計する必要はない）
  - **観測ベクトル化**: `build_observation()` から素朴な数値配列（`list[float]`）を組み立てる
    参考実装を1つ用意する（poke-envの`embed_battle`は利用者に委ねる設計で参考実装自体がないため、
    ここはjpoke独自の付加価値になる）
  - **報酬ヘルパー**: `reward_computing_helper` 相当の**純粋関数**（クラスメソッドではなく、
    `Battle`と前回の状態値を受け取り差分を返す関数）を用意する。HP割合・瀕死・状態異常・勝敗の
    重み付けは poke-env と同じ発想を踏襲しつつ、`Battle.won(player)`/`lost(player)`（`Player`引数版、
    実装済み）を使う
  - `step`/`reset`: 既存の `Battle.step()` / `Battle.play_out()` / `Player.battle_against()` の下地を
    そのまま流用できる（サーバー・asyncio・スレッドが一切不要な分、poke-envの
    `_EnvPlayer`/`_AsyncQueue`相当の複雑さが丸ごと要らない）
- 依存関係: **追加しない**（`pyproject.toml` の `dependencies = []` を維持）。これにより
  `pip install jpoke` だけで動く既存の使い勝手を損なわない。
- CLAUDE.md「対象はポケモンチャンピオンズのシングルバトルのみ」との整合: ダブルバトル相当の
  対応は最初から対象外でよい（jpoke自体がダブル非対応のため自然に一致）。

### C案: 既存の `interop/poke_env.py` 計画（Battleコンバータ、未着手）にRL変換を統合
- `.internal/plan/poke-env/poke_env_battle_converter.md` は「poke-env の進行中Battleをjpoke Battleに
  変換する」計画だが、これはRLとは別軸（既存のShowdown対戦ログをjpokeで解析したい場合の用途）。
- RL用途で欲しいのは逆方向、すなわち「jpoke Battleから学習用の行動/観測/報酬を作る」変換であり、
  C案（poke-env→jpoke一方向）の対象範囲には元々含まれない。B案と混同しないよう切り分けが必要。

## 推奨

B案（外部ライブラリ非依存のRL支援ヘルパー新設）を推奨。理由:

1. poke-env のRL機能は「サーバー接続込みのGym化」であり、jpokeが持つ「サーバー不要・高速・
   完全情報」という強みと組み合わせると、素直に上位互換のRL環境になり得る。外部ライブラリの
   `gymnasium`/`pettingzoo`自体を持ち込まなくても、その「形」だけ真似た薄いクラス・関数群で
   十分に効果を再現できる。
2. `dependencies = []` を維持したまま提供できるため、`pip install jpoke` だけで動く既存の
   使い勝手を一切損なわない（`gymnasium`が使いたい利用者は自分の環境にだけ追加すればよい）。
3. 既存の `.internal/poke-env/compat_*.md` 一連の投資（poke-env経験者の導線づくり）の延長として
   自然。「poke-envのGymnasiumインターフェースを知っている人が次に触っても迷わないもの」を
   用意する形になる。
4. `players/` フレームワーク（`TreeSearchPlayer` 等）と共存可能（`Player`のサブクラスとしてではなく
   別レイヤーのヘルパー群として追加するため、既存の設計を壊さない）。

実装計画は `.internal/plan/poke-env/rl_support.md` を参照。
