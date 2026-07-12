# jpoke — Claude Code ガイド

## プロジェクト概要

ポケモンバトルシミュレーション開発用 Python ライブラリ。
対象範囲（ターゲット世代・チャンピオンズとの関係）の定義は [README.md](README.md) の
「対象範囲」を正とする。
テスト・仕様書・コード内コメントは **日本語** で書く。

## テストの実行

```powershell
# 全テスト
python -m pytest tests/ -v

# カテゴリ別
python -m pytest tests/abilities/ -v
python -m pytest tests/moves_attack/ -v
python -m pytest tests/moves_status/ -v
python -m pytest tests/volatiles/ -v

# 特定ファイル
python -m pytest tests/abilities/test_ability_ka.py -v

# 特定テスト関数（日本語関数名も可）
python -m pytest tests/abilities/ -k "ARシステム" -v
```

テストは `tests/` 直下（ailment, copy, damage, field, item, megaevol, terastal など）と
サブディレクトリ（`abilities/`, `moves_attack/`, `moves_status/`, `volatiles/`）に分かれている。
`tests/test_utils.py` はテストヘルパー（テスト対象外）。

## アーキテクチャ

### 主要コンポーネント

| クラス／モジュール | 役割 |
|---|---|
| `core/battle.py` `Battle` | バトル全体の状態管理・ターン進行 |
| `core/turn_controller.py` | ターン順・行動順の制御 |
| `core/event_manager.py` | イベント発火・ハンドラ呼び出し |
| `core/handler.py` `Handler` | ハンドラ定義（subject, subject_spec, 関数） |
| `core/context.py` `BaseContext` / `EventContext` / `AttackContext` | ハンドラに渡すイベントコンテキスト（攻撃フローは `AttackContext`、それ以外は `EventContext`） |
| `model/` | `Pokemon`, `Move`, `Field` などのモデル |
| `data/` | `ability.py`, `move.py`, `item.py` など — 各エンティティのデータ定義とハンドラ登録 |
| `handlers/` | `ability.py`, `ability_paradox.py`, `ailment.py`, `field.py`, `item.py`, `lethal.py`, `move.py`, `move_attack.py`, `move_status.py`, `volatile.py` など — ハンドラ実装 |
| `players/` | `Player` の派生方策実装（`tree_search_player.py` の `TreeSearchPlayer` など） |
| `enums/` | `Event`, `Command`, `Interrupt`, `LogCode` |
| `types/` | `Stat`, `Type`, `AilmentName`, `VolatileName` など Literal 型の定義 |

### イベント駆動モデル

1. バトルロジックが `Event` を発火
2. `EventManager` が登録済み `Handler` を順に呼び出す
3. 各 `Handler` は `HandlerReturn(value, stop_event)` を返す
4. ハンドラ登録は `data/ability.py`, `data/item.py` などで行う

### ハンドラ追加の流れ

```
data/ability.py  →  handlers/ability.py に実装  →  data/ability.py に登録
```

### テストユーティリティ

`tests/test_utils.py` のヘルパー API は `tests/CLAUDE.md` を参照。

## 実装時の参照順

新しい特性・技・アイテムを実装する前に以下の順で読む：

1. `src/jpoke/core/handler.py`
2. `src/jpoke/core/context.py`
3. `src/jpoke/enums/event.py`
4. `src/jpoke/core/battle.py`
5. `src/jpoke/model/pokemon.py`
6. 対象の `src/jpoke/data/<category>.py` と `src/jpoke/handlers/<category>.py`
7. `tests/test_utils.py` と最寄りの既存テスト
8. **`docs/spec/turn.md`** — 実装するイベントの priority を確認し、計画書に明記する

## Handler の約束事

- `HandlerReturn` は `value` と `stop_event` のみを持つ
- `subject_spec` は必須。イベントが渡すコンテキスト型のロールと一致させる
  - 攻撃フェーズ（`AttackContext`）: `attacker:self` / `defender:self`
  - 非攻撃フェーズ（`EventContext`）: `source:self` / `target:self`
- 固有効果のロジックは `handlers/*` に名前付き関数で実装し、`data/*.py` からその関数を登録する
- `handlers/*` の並びは `data/*.py` の定義順（五十音順）に合わせる
- イベント発火側で前提が保証されている場合、ハンドラ側の重複ガード（`if not mon.alive` など）は不要
- **priority は `docs/spec/turn.md` で対象イベントの行を必ず確認する。未掲載のイベント（ダメージ計算内部等）は既存の同種ハンドラを参照して決定し、計画書に根拠を明記する**

## 状態変更ルール

- `Pokemon.hp` へ直接代入禁止 → 必ず `battle.modify_hp(...)` を使う
- ランク変化は `battle.modify_stat(...)` または `battle.modify_stats(...)`
- 状態異常・揮発性状態・天候・地形・場の状態は各 manager を通して更新する


## 仕様書・ドキュメント

| ディレクトリ | 役割 |
|---|---|
| `docs/spec/` | 技・アイテム・特性・場の効果の挙動仕様（実装前に読む） |
| `docs/plan/` | 現在の実行計画と優先順位 |
| `docs/progress/` | カテゴリ別の実装追跡（`ability.md`, `item.md`, `move.md`） |
| `docs/tests/` | テスト一覧（`scripts/generate_test_list.py` で生成） |

実装が完了したら、以下の順で進捗を更新する：

1. `docs/progress/<category>.md` の該当行を更新する（実装済みフラグ・件数）

## ループディスパッチャー

`/loop <name>` を受け取ったとき、`.claude/loop/<name>.md` が存在する場合は **その指示書を Read して内容に従って実行する**。
ループの開始時に `.claude/loop/instructions.md` を Read してフロー一覧を確認すること。

## Git運用ルール

### ブランチ・PR

- **`.loop/` 経由の自動作業以外は main への直接コミット禁止**。作業前に必ず `feature/<内容>` などの
  作業ブランチを切る
- 完了したら `gh pr create` でPRを作成し、確認のうえ `gh pr merge` でmainに取り込む（`--no-verify` は使わない）
- リポジトリは `delete_branch_on_merge` が有効。PRマージ後、**リモートブランチは自動削除されるが
  ローカルブランチは残るので `git branch -d <branch>` で必ず削除する**（残したまま気づかず同じ
  ブランチに追いコミットしてしまう事故を防ぐ）
- **PRマージ後は、作業していたworktree（work1等）だけでなく、リポジトリルートも含めて main を
  必ず `git pull`（または `git fetch` + `checkout`）で最新化する**。worktreeだけ最新化してリポジトリ
  ルート側の `git pull` を忘れると、後続作業がマージ済みの変更に気づかないまま古い状態で進んでしまう
  事故につながる
- 既存ブランチで作業を再開する前に、そのブランチが既にmainへマージ済みでないか
  （`git log <branch>..main`、`gh pr list --state merged`）を確認する
- `.loop/` 系フロー（impl / review / todo / lethal / fuzz / replay_fuzz / flaky）は対象外。既存の
  分離済みブランチ（`loop/{flow}` / `loop/{flow}/integration`）で作業し、ローカルテストを通過した
  単位（`fuzz`/`replay_fuzz`/`flaky`は1件ごと、`todo`は5件ごと、`lethal`は10件ごと、`impl`/`review`
  は §共通5 のバッチ整形ごと）でディスパッチャーが `_common.md` §共通6 の手順に従い GitHub PR経由
  （`gh pr create` → 即 `gh pr merge`、人間レビュー待ちはしない）で自動的にmainへ反映する。
  **ローカルの `jpoke/`（main の作業ツリー）へ直接コミット・マージすることは絶対にしない**
  （同一 `.git` を共有する他セッション・他worktreeのローカル `main` refを不用意に動かし混乱を招くため）
- ループはmain反映を自動かつ継続的に行うため、手動ブランチと `data/*.py` / `docs/progress/*` /
  `docs/tests/*` など同じ共有ファイルに触れる作業を始める直前は `git pull` してmainを最新化すると
  衝突を避けやすい

### 一時保存・worktree

- 一時退避に `git stash` を使わない。中断する作業でも作業ブランチにWIPコミットしておく
  （stashは `git status` にも `git branch` にも現れず、存在を忘れて長期間放置されやすい）
- worktree（Agentの`isolation: "worktree"`で作られたものか、`work1`/`work3`のように汎用作業用に
  手動作成したものかを問わず）は、タスクの結論（マージ or 破棄）が出た時点で `git worktree remove`
  する。永続ワークスペースとして残す例外は設けない。**worktreeを除去するコマンドはworktreeの外
  （リポジトリルート等）から実行する**（内部の作業ディレクトリから実行すると削除に失敗し孤立
  ディレクトリが残ることがある）
- 作業の節目や `.loop` 以外のセッション終了時には `git status` / `git worktree list` /
  `git stash list` で放置物がないか確認する

## 開発ルール

- **対象はポケモンチャンピオンズシングルバトルのみ**
- 外部 API（テスト・bot・探索コード）は `Battle` の公開メソッドを入口にする。
  `battle.<manager>.<method>()` の直呼びは `src/jpoke` 内部実装に限る
- **`.loop` 作業中はユーザーの指示がない限り確認を取らず最後まで完遂する**
- コメント・docstringは **日本語** で書く
- テスト関数名は `test_<特性名/技名>_<確認内容>` の形式
- ハンドラの実装は `handlers/`、登録は `data/` で行う
- 新しい `Literal` 型は `types/` に追加する
- 型アノテーションは Python 3.10+ の構文（`X | Y`, `list[X]`）を使う
- 長い `if` 文（80文字以上）は括弧で囲んで複数行に展開し、`and` で条件ごとに改行する

## ハンドラの追加ルール

- `handlers/<category>.py` に関数を実装したら、以下の順で実行する：
  1. `python scripts/sort_handlers.py src/jpoke/handlers/<category>.py` — 日本語始まりの公開ハンドラ関数を五十音順に並び替える
  2. `data/ability.py` / `data/item.py` / `data/move.py` にエントリを追加・変更した場合、対応するスクリプトを実行する：
     - `python scripts/sort_data/sort_abilities.py` — `ABILITIES` 辞書を五十音順に並び替える
     - `python scripts/sort_data/sort_items.py` — `ITEMS` 辞書を五十音順に並び替える
     - `python scripts/sort_data/sort_moves.py` — `MOVES` 辞書を五十音順に並び替える
  3. `python -m pytest tests/ -v` — 全テストが通ることを確認する

## テストの追加ルール

- `test_utils.py` の `start_battle`、`run_move`、`run_switch` などを再利用する
- テスト項目を追加・修正したら、以下の順で実行する：
  1. `python scripts/sort_tests.py <対象ファイル>` — テスト関数を五十音順に並び替える（複数指定可、例: `tests/abilities/test_ability_ka.py tests/moves_attack/test_move_ka.py`）
  2. `python scripts/generate_test_list.py` — `docs/tests/` のテスト一覧を更新する
  3. `python -m pytest tests/ -v` — 全テストが通ることを確認する
