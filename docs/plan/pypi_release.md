# 計画: jpoke の PyPI 公開

更新日: 2026-07-11

## ゴール

`pip install jpoke` だけで対戦シミュレーションを始められる状態にして PyPI に公開する。

## スコープ

- 対象: `pyproject.toml`、`LICENSE`、`README.md`、`src/jpoke/__init__.py`、
  `src/jpoke/utils/string_utils.py`、`.github/workflows/`
- 実装状態: **フェーズ0〜3完了。`jpoke` 0.1.0 を PyPI に公開済み**
  （https://pypi.org/project/jpoke/ 。`v0.1.0` タグ push → `publish.yaml` の
  Trusted Publishing 経由で公開し、クリーン venv での `pip install jpoke` 実地確認も
  完了済み）。残るはフェーズ4（公開後の改善、ブロッカーではない）のみ
- レビュー方法: `git archive HEAD` のスナップショットを `python -m build` で実際に
  ビルドし、リポジトリ外のクリーン venv に wheel をインストールして `import jpoke` と
  README クイックスタートを実行する実地検証を実施済み

## 現状の結論

**現状の設定でビルドした wheel をインストールすると、`import jpoke` の時点で全ユーザーが
必ず `FileNotFoundError` になる**（`pokedex.json` のパッケージング漏れ。実機で再現確認済み）。
`pokedex.json` を手動配置すればクイックスタートが正常動作することも確認済みで、
パッケージング上の致命傷はこの1点のみ。コード本体は PyPI 配布への適性が高い:

- データ読み込みは `importlib.resources` 経由・`encoding='utf-8'` 明示（`data/pokedex.py`）
- `sys.path` 操作・`os.chdir`・環境変数依存・cwd 相対パスは `src/jpoke` 内に皆無
- OS 依存のパス構築なし。`print()` はオプトインの表示メソッド2箇所のみ
- `types/poke_env.py` は純粋なマッピング辞書のみで poke-env への import なし

問題はパッケージング設定・メタデータ・ドキュメントに集中している。

## フェーズ 0: 前提（本計画の外側）

- [x] 作業ツリーの未解決マージコンフリクト6ファイルを解決する
      （`core/move_executor.py`, `handlers/move_status.py`, `model/pokemon.py`,
      `tests/abilities/test_ability_ka.py`, `tests/moves_status/test_move_a.py`,
      `tests/moves_status/test_move_ta.py`）
- [x] `.loop` 系フローの main 反映（`_common.md` §共通6）を済ませてから作業ブランチを切る
      （`pyproject.toml` / `README.md` は共有ファイルのため衝突回避）

## フェーズ 1: 公開ブロッカーの修正（1 PR にまとまる規模）

### 1-1. `pokedex.json` のパッケージング漏れ【最優先】

- [x] 完了

`pyproject.toml` の `package-data` が `py.typed` しか宣言していない。

```toml
[tool.setuptools.package-data]
jpoke = ["py.typed"]
"jpoke.data" = ["*.json"]
```

修正後、`python -m build` → リポジトリ外のクリーン venv に wheel をインストール →
`import jpoke` + README クイックスタート実行で必ず検証する
（CI の `pip install -e .` は editable のためこの不具合を検出できない。フェーズ3参照）。

### 1-2. LICENSE 本文の破損

- [x] 完了

`LICENSE:17` が `IN NO イベント SHALL` になっている（過去の「EVENT→イベント」一括置換が
MIT 条文まで書き換えた事故）。`IN NO EVENT SHALL` に修正する。

### 1-3. 未宣言依存 `jaconv` / `rapidfuzz` の解消

- [x] 完了

`src/jpoke/utils/string_utils.py:1,3` が `jaconv` と `rapidfuzz` を import しているが
`dependencies = []` に未宣言。このモジュールは `utils/__init__.py` からも
`src/jpoke` 内のどこからも import されていないデッドコード。
**ファイルごと削除する**（将来必要になったら依存宣言とセットで復活させる）。
削除前に `scripts/` からの参照がないことを grep で確認する。

### 1-4. `__version__` の定義

- [x] 完了

`jpoke.__version__` が存在しない。`src/jpoke/__init__.py` に追加:

```python
from importlib.metadata import version as _version

__version__ = _version("jpoke")
```

あわせて `__all__` を定義する（現状のエクスポート: `Battle`, `Player`, `Pokemon`,
`Ability`, `Item`, `Move`, `POKEDEX`）。

### 1-5. pyproject.toml メタデータ整備

- [x] 完了

- `license = { file = "LICENSE" }` → PEP 639 書式へ（setuptools のビルド警告対象。
  2027-02 に非互換化予定）:

  ```toml
  license = "MIT"
  license-files = ["LICENSE"]
  ```

  あわせて classifier `License :: OSI Approved :: MIT License` を削除（二重管理・非推奨）。
- classifiers 追加: `Development Status :: 3 - Alpha`, `Intended Audience :: Developers`,
  `Topic :: Games/Entertainment :: Turn Based Strategy`,
  `Programming Language :: Python :: 3.10` / `3.11` / `3.12`,
  `Natural Language :: Japanese`, `Typing :: Typed`
- `keywords = ["pokemon", "battle", "simulator", "bot"]` を追加
- `[project.urls]` に `Issues = "https://github.com/tmwork1/jpoke/issues"` を追加
- `description` をスコープに合わせて具体化（例:
  `"Event-driven Pokemon Champions single-battle simulation library (unofficial)"`）

### 1-6. sdist への tests/ の中途半端な混入解消

- [x] 完了

MANIFEST.in 不在のため、sdist に `tests/` 直下の `test_*.py` だけが自動で拾われている
（サブディレクトリは入らない不完全な状態）。`MANIFEST.in` を新設して明示的に制御する:

```
prune tests
prune docs
prune scripts
prune .claude
prune .loop
```

（sdist にテストを同梱したい場合は逆に `recursive-include tests *.py` で全部入れる。
どちらかに寄せて「中途半端」を解消するのが目的。既定は prune 推奨。）

## フェーズ 2: README の PyPI 対応

PyPI のプロジェクトページは `readme = "README.md"` をそのまま表示するため、
以下を修正する:

- [x] 冒頭に `pip install jpoke` を追加し、`git clone` 手順は「開発用」見出しへ分離
- [x] 相対リンクを絶対 URL 化: `README.md:13` の `[CLAUDE.md](CLAUDE.md)`、
      `README.md:59` の `[tests/CLAUDE.md](tests/CLAUDE.md)`
      → `https://github.com/tmwork1/jpoke/blob/main/...`
- [x] クイックスタートから `tests/test_utils.py` 依存の記述（`README.md:56-72`）を除去。
      pip ユーザーには `tests/` が存在しないため。ヘルパー紹介は「開発（clone 前提）」
      節へ移動する。中期的には `jpoke.testing` として本体へ昇格を検討（フェーズ4）
- [x] 商標免責を追加（日英併記、冒頭または末尾）:

  > 本プロジェクトは株式会社ポケモン・任天堂・株式会社ゲームフリークとは無関係の
  > 非公式（fan-made）プロジェクトです。
  > This is an unofficial, fan-made project and is not affiliated with, endorsed by,
  > or sponsored by Nintendo, Game Freak, or The Pokémon Company.

  ※ v0.1.0後のREADME整理（3f6fcbe8「docs: READMEから英語説明文を削除」）で英語版が
  意図せず削除されていたが、2026-07-12 に日英併記へ復活済み。

- [x] 冒頭に3文程度の英語サマリを追加（全文翻訳は不要） (※現在は未掲載。上記コミットで
      英語説明文ごと削除されたまま復活していない。後続対応が必要)

## フェーズ 3: CI・リリース基盤

### 3-1. CI に wheel 検証ジョブを追加

- 実施済み（`.github/workflows/test.yml` に `package-check` ジョブを追加。
  `python -m build` → `twine check dist/*` → wheel インストール → `/tmp` からの
  `import jpoke` の一連をローカルでも再現確認済み）

今回の致命的不具合（1-1）を CI が素通しした根本原因は、`test.yml` が
`pip install -e .`（editable）しか行わないこと。`.github/workflows/test.yml` に追加:

```yaml
package-check:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with: { python-version: "3.12" }
    - run: pip install build twine
    - run: python -m build
    - run: twine check dist/*
    - run: pip install dist/*.whl
    # リポジトリ外から import できることを確認（cwd の src/ を拾わないよう /tmp で実行）
    - run: cd /tmp && python -c "import jpoke; print(jpoke.__version__)"
```

### 3-2. publish ワークフローの新設

- 実施済み（`.github/workflows/publish.yaml` を新設。`v*` タグの push をトリガーに
  build → publish の2ジョブ構成、publish ジョブに `environment: pypi` と
  `permissions: id-token: write` を設定し `pypa/gh-action-pypi-publish@release/v1` で
  Trusted Publishing する。ファイル名は当初 `publish.yml` だったが、PyPI 側の
  pending publisher 登録が `publish.yaml` だったため一致させるようリネーム済み
  （OIDC はワークフローファイル名を厳密照合するため）
- 実施済み（ユーザー側作業）: PyPI 側での pending publisher
  （リポジトリ `tmwork1/jpoke` / workflow `publish.yaml`）を登録済み。
  `v0.1.0` タグ push で実際に build → publish が成功したことを確認済み

### 3-3. バージョニングと初回リリース

- 実施済み: semver 採用方針を README に明記（0.x 系は minor bump で破壊的変更が
  あり得る旨）。`CHANGELOG.md` を新設（Keep a Changelog 形式）し `[0.1.0]` を記載、
  `[project.urls]` に `Changelog` を追加
- 実施済み: `version = "0.1.0"` へ更新、`v0.1.0` タグを作成・push し、
  Trusted Publishing 経由で PyPI へ実際に公開。クリーン venv から
  `pip install jpoke==0.1.0` → `import jpoke` の実地確認済み
  （TestPyPI でのリハーサルは省略し、本番公開のみで実施）

## フェーズ 4: 公開後の改善（ブロッカーではない）

- 実施済み: 利用者向け API リファレンスの整備。`docs/api/README.md` を新設し、
  `Battle`（コンストラクタ主要引数・対戦進行系/状態取得系/ダメージ計算系/シナリオ構築系/
  ログ系/poke-env互換プロパティ/リプレイ系にグルーピング）、`Player`（`add_pokemon()`,
  `choose_command()` のオーバーライド方法, `team` 属性がスナップショットである注意点,
  `battle_against()`）、`Pokemon`（コンストラクタ引数のデフォルト値, `set_evs()`/`set_ivs()`,
  `show()`, 状態読み取り系）を実際のソースコード（`core/battle.py`, `core/player.py`,
  `model/pokemon.py`）を読んで確認しながらまとめた。README.md の「ドキュメント」テーブルにも
  1行追加
- `tests/test_utils.py` の主要ヘルパー（`start_battle` / `run_move` / `run_switch`）を
  `jpoke.testing` として本体パッケージへ昇格
- 実施済み: `core` ⇔ `model` ⇔ `data` の循環 import 解消。パッケージ内の他ファイルが
  `from jpoke.core import X` / `from jpoke.model import X` / `from jpoke.data import X` という
  パッケージレベル絶対importを使い、対象パッケージの `__init__.py` が完全実行済みであることに
  暗黙依存していた（約43箇所）。同一パッケージ内の自己参照は相対import（`from .context import X`）、
  パッケージをまたぐ参照はサブモジュール直接指定の絶対import（`from jpoke.core.lethal import X` 等）に
  書き換え、`__init__.py` の実行順序に依存しない形へ統一した。
  実証実験: 修正前は `core/__init__.py` の `context` を `lethal` より前に並び替えると
  `ImportError: cannot import name 'LethalHandler' from partially initialized module 'jpoke.core'`
  が実際に発生することを確認。修正後は同じ並び替えを行っても `import jpoke` が成功することを確認済み
  （実験用の並び替えはコミットに含めず、`core/__init__.py` は元の順序のまま）
- `import jpoke` の初期化コスト削減（実測 約460ms。pokedex.json 544KB と
  全ハンドラテーブルを import 時に無条件ロードしている。遅延 import の余地あり）
- CONTRIBUTING.md / SECURITY.md の整備
- 実施済み: `CONTRIBUTING.md`（開発環境セットアップ・テスト実行・コードスタイル・
  ハンドラ追加の流れ・ブランチ/PRの流れ・対象範囲の注意）と `SECURITY.md`
  （サポート対象は0.x系のPyPI最新版のみ・GitHub Security Advisories経由の非公開報告を
  推奨・ローカル実行のみでアタックサーフェスが限定的である旨）をリポジトリルートに
  新設。README.md の「ドキュメント」節に両ファイルへの導線を追加
- 実施済み: 導入・AI学習資料向けサンプルスクリプトを `examples/` に新設（6本、公開APIのみ依存・
  `pip install jpoke` だけで実行可能）。`examples/README.md` と `tests/test_examples_smoke.py`
  （壊れたサンプルの放置防止）を追加し、CI/README の ruff 対象にも `examples/` を追加。
  サンプル作成時に見えた公開APIの使い勝手・既知の seed バグは `docs/plan/examples_api_feedback.md`
  に記録済み（API自体の変更は別タスク）

## 検証チェックリスト（フェーズ1〜3完了時）

- [x] `python -m build` が警告なしで成功する
- [x] `twine check dist/*` が PASSED
- [x] wheel に `jpoke/data/pokedex.json` と `jpoke/py.typed` が含まれる
- [x] sdist に `tests/` / `docs/` / `scripts/` / `.claude/` が混入していない
- [x] リポジトリ外のクリーン venv で wheel をインストールし、
      `import jpoke` と README クイックスタートが動く
- [x] `jpoke.__version__` が pyproject.toml の version と一致する
- [x] `python -m pytest tests/ -q` 全通過、`ruff check` / `mypy` 通過
- [ ] README を PyPI の Markdown レンダリングで確認（相対リンクなし・免責あり）
      — 自動取得（WebFetch）が Bot 対策で失敗するため未確認。ユーザーによる目視確認が必要
