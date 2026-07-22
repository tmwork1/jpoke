# Contributing to jpoke

jpoke への貢献に関心を持っていただきありがとうございます。このドキュメントは
開発環境のセットアップからプルリクエストまでの流れをまとめたものです。

## 対象範囲について

jpoke は **ポケモンチャンピオンズのシングルバトルのみ** を対象としています
（ダブルバトル等は対象外）。技・特性・アイテム・ポケモンなどの仕様ソースは
**第9世代（スカーレット・バイオレット）** を基本とし、ポケモンチャンピオンズ側で
ルールが異なる場合はそちらを優先します。第9世代で実装されていない技・アイテム・
特性・ポケモンなどは実装対象外です。詳細は
[README.md](https://github.com/tmwork1/jpoke/blob/main/README.md) の
「対象範囲」を参照してください。

## 開発環境のセットアップ

```bash
git clone https://github.com/tmwork1/jpoke.git
cd jpoke

# 開発（テスト・lint・型チェック）に必要な依存を含めてインストール
pip install -e . pytest pytest-cov ruff mypy
# または uv を使う場合（pyproject.toml の [dependency-groups] dev がそのまま使われる）
uv sync
```

`requires-python = ">=3.11"`。型アノテーションは Python 3.10+ の構文
（`X | Y`, `list[X]`）を使用してください。

## テストの実行

```bash
# 全テスト
python -m pytest tests/ -v

# カテゴリ別
python -m pytest tests/abilities/ -v
python -m pytest tests/items/ -v
python -m pytest tests/moves_attack/ -v
python -m pytest tests/moves_status/ -v
python -m pytest tests/volatiles/ -v

# 特定ファイル
python -m pytest tests/abilities/test_ability_ka.py -v

# 特定テスト関数（日本語関数名も可）
python -m pytest tests/abilities/ -k "ARシステム" -v

# カバレッジ付き
python -m pytest tests/ -q --cov=jpoke --cov-report=term
```

プルリクエストを出す前に、変更内容に関わらず `python -m pytest tests/ -v` が
全件成功することを確認してください。

## コードスタイル

- 型アノテーションは Python 3.10+ の構文（`X | Y`, `list[X]`）を使う
- コメント・docstring は **日本語** で書く
- テスト関数名は `test_<特性名/技名>_<確認内容>` の形式にする
- 長い `if` 文（80文字以上）は括弧で囲んで複数行に展開し、`and` で条件ごとに改行する
- lint は ruff で確認する:

  ```bash
  python -m ruff check src/ tests/ scripts/ examples/
  ```

- 型チェック（`src/jpoke/core` のみを対象に段階導入中）:

  ```bash
  python -m mypy
  ```

- 五十音順の維持・データ整合性チェック（`--check` は変更せず確認のみ）:

  ```bash
  python scripts/sort_handlers.py --check
  python scripts/sort_data/sort_abilities.py --check
  python scripts/sort_data/sort_items.py --check
  python scripts/sort_data/sort_moves.py --check
  python scripts/sort_tests.py --check tests/**/test_*.py
  ```

`.pre-commit-config.yaml` を使うと、これらのチェック（の一部）をコミット前に
ローカルで自動実行できます（`pip install pre-commit && pre-commit install`）。
CI（`.github/workflows/test.yml`）でも push/PR ごとに同等のチェックを
Windows + Linux × Python 3.11/3.12 のマトリクスで実行しています。

## バージョン管理

`pyproject.toml` の `version` と `src/jpoke/__init__.py` の `__version__` は
（`importlib.metadata` の import コストを避けるため）二重管理になっています。
`pyproject.toml` の `version` を上げる際は `src/jpoke/__init__.py` の
`__version__` も同じ値に **手動で** 揃えてください。両者の不一致は
`tests/test_version.py` が検知します。

## アーキテクチャとハンドラ追加の流れ

jpoke はイベント駆動アーキテクチャを採用しています。バトルロジックが `Event` を
発火し、`EventManager` が登録済み `Handler` を優先度順に呼び出す、という流れです。
主要コンポーネントの役割やイベントモデルの詳細は [CLAUDE.md](https://github.com/tmwork1/jpoke/blob/main/CLAUDE.md) の
「アーキテクチャ」節を参照してください。

新しい特性・技・アイテムなどのハンドラを追加する場合は、以下の対応で実装します。

```
data/ability.py  →  handlers/ability.py に実装  →  data/ability.py に登録
```

- 固有効果のロジックは `handlers/<category>.py` に名前付き関数として実装し、
  `data/<category>.py` からその関数を登録する
- `handlers/*` の並びは `data/*.py` の定義順（五十音順）に合わせる

`handlers/<category>.py` に関数を実装したら、以下の順で実行してください。

1. `python scripts/sort_handlers.py src/jpoke/handlers/<category>.py`
   — 日本語始まりの公開ハンドラ関数を五十音順に並び替える
2. `data/ability.py` / `data/item.py` / `data/move.py` にエントリを追加・変更した
   場合、対応するスクリプトを実行する:
   - `python scripts/sort_data/sort_abilities.py` — `ABILITIES` 辞書を五十音順に並び替える
   - `python scripts/sort_data/sort_items.py` — `ITEMS` 辞書を五十音順に並び替える
   - `python scripts/sort_data/sort_moves.py` — `MOVES` 辞書を五十音順に並び替える
3. `python -m pytest tests/ -v` — 全テストが通ることを確認する

テストを追加・修正した場合は、以下の順で実行してください。

1. `python scripts/sort_tests.py <対象ファイル>` — テスト関数を五十音順に並び替える
   （複数指定可、例: `tests/abilities/test_ability_ka.py tests/moves_attack/test_move_ka.py`）
2. `python -m pytest tests/ -v` — 全テストが通ることを確認する

新しい `Literal` 型（`Stat`, `Type`, `AilmentName` など）が必要な場合は `types/` に
追加してください。

## ブランチ・プルリクエストの流れ

1. 作業前に `feature/<内容>` などの作業ブランチを切る（main への直接コミットは
   禁止）
2. 変更をコミットし、`gh pr create` でプルリクエストを作成する
3. レビュー後、`gh pr merge` で main に取り込む（`--no-verify` は使わない）
4. このリポジトリは `delete_branch_on_merge` が有効です。マージ後、リモート
   ブランチは自動削除されますが、**ローカルブランチは残るので
   `git branch -d <branch>` で必ず削除してください**
5. マージ後は、作業していた worktree だけでなくリポジトリルートも含めて
   `git pull`（または `git fetch` + `checkout`）で main を必ず最新化してください

## 困ったときは

このプロジェクトの詳細な規約・アーキテクチャ・ディレクトリ構成は
[CLAUDE.md](https://github.com/tmwork1/jpoke/blob/main/CLAUDE.md) に集約されています。実装や規約で迷った場合はまず
CLAUDE.md を参照してください。
