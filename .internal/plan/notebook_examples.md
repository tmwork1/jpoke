# 計画: examples/ の Jupyter Notebook 化と Google Colab 公開

更新日: 2026-07-17

## ゴール

`examples/` 配下のサンプルスクリプトのうち、重い処理・並列処理を含むもの以外を
Jupyter Notebook（`.ipynb`）化し、GitHub上の `.ipynb` を Google Colab の
`https://colab.research.google.com/github/...` URL経由でそのまま開いて実行できる
状態にする。あわせて、examples内に混在している「APIの仕様説明」を
`docs/api/README.md` に統合し、examples自体は「学習用サンプル」としての
役割に絞る。

## スコープ

- 対象: `examples/**/*.py`（現時点で計31本）、`examples/README.md`、
  `docs/api/README.md`、`tests/test_examples_smoke.py`、
  `.internal/tests/test_examples_smoke.md`、`pyproject.toml`、
  `.github/workflows/test.yml`、`.gitignore`
- notebook化する29本は旧 `.py` を削除し `.ipynb` を唯一の正とする
  （jupytext等でのpy/ipynbペア運用はしない）
- **`.py` のまま残す2本**（重い処理・並列処理のため notebook化・Colab対応の対象外）:
  - `examples/04_research/03_janken_nash_fictitious_play.py`
    （`ProcessPoolExecutor` による並列モンテカルロ、数十秒級）
  - `examples/04_research/04_janken_nash_cfr.py`
    （ロールアウトベースのregret matching学習、数十秒級）
- レビュー方法: notebook化した29本は papermill/`jupyter nbconvert --execute`で
  実行しエラーなく完走することを確認。nash系2本は既存どおりサブプロセス実行で
  確認。`ruff check` と `pytest tests/ -v` がリポジトリ全体で通ることを確認。
  少なくとも1本（`01_basics/01_battle_against_intro.ipynb`）はColab実機での
  動作確認をユーザーに依頼する

## 事前調査で確認済みの事実

- リポジトリは public（`github.com/tmwork1/jpoke`）、`jpoke` は PyPI に公開済み
  （`pip install jpoke` が実際に機能する）→ Colabバッジ・`pip install`セルが
  機能する前提が揃っている
- notebook化対象の29本はほぼ「モジュールdocstring（解説）→ import →
  `def main(): ...` → `if __name__ == "__main__": main()`」という共通構造
- `examples/05_benchmark/01_step_time_benchmark.py` のみ `argparse` でCLI引数
  （`--n-battles` 等）を受けている → notebook化するとCLI引数の概念が
  なくなるため、セル内変数に置き換える
- 現行スモークテスト `tests/test_examples_smoke.py` は各 `.py` をサブプロセス
  実行し `returncode == 0` を見ているだけ。`05_benchmark` だけ `EXTRA_ARGS` で
  軽量パラメータを渡している
- CI（`.github/workflows/test.yml`）は `ruff check ... examples/` を実行して
  おり、`examples/` の中身が変わるとlint対象も変わる。mypyは
  `src/jpoke/core` のみが対象で `examples/` は無関係
- `.gitignore` に `.ipynb_checkpoints/` は未登録
- `docs/api/README.md` は現状 `Battle` / `Player` / `Pokemon` / `Command` /
  `Move` / テストユーティリティの節のみで、`TreeSearchPlayer`
  （`02_ai/*`が多用する `evaluate_commands()` / `estimate_opponent()` /
  `configure_sim()` / `fallback()` 等）の節が無い

## 非コード部分の整理方針

notebook移行に合わせ、examples全31本（nash系2本含む）の非コード部分
（docstring・コメント）も整理する。判定基準：

- 「戻り値の挙動」「引数の内部仕様」などAPI固有の仕様説明
  → `docs/api/README.md` の該当セクションへ統合し、example側は
  1行の参照コメントに圧縮する
- `lambda`式・内包表記などPython自体の文法解説
  → 学習コメントとして example にそのまま残す（削除しない）
- 「このサンプルで何を学ぶか」という文脈説明
  → example の docstring として残す（学習用サンプルとしての価値の中核）

## notebook変換方針

1本ずつ nbformat の JSON を手書きするのではなく、jupytextを変換ツールとして
のみ使う（リポジトリにpy/ipynbペアを残す運用はしない）：

- 各 `.py` に一時的に `# %%` / `# %% [markdown]` のセル区切りマーカーを追記
  （percent形式）
- `jupytext --to notebook` で `.ipynb` を生成
- 生成後、元の `.py`（マーカー入りの中間ファイルも含む）を削除し、
  `.ipynb` のみをコミット

セル分割の基本パターン（notebook化する29本共通）：

- モジュールdocstring → markdownセル（解説文）
- 先頭に Colab用の `!pip install -q jpoke` セル
- `import` 文 → 1セル
- `def main(): ...` の中身 → 意味のあるまとまり単位で複数セルに分割し、
  `main()` 関数定義は展開してトップレベルコードにする
  （`if __name__ == "__main__":` ガードは削除）
- `05_benchmark/01_step_time_benchmark.py` は `argparse` 部分を
  「パラメータセル」（`n_battles = 300` 等の素の変数代入、papermillの
  `parameters` タグを付与）に置き換える

## フェーズ 0: 前提

- [x] `feature/notebook-examples` ブランチを作成
- [x] `pyproject.toml` の `[dependency-groups] dev` に `jupytext`, `papermill`,
      `ipykernel` を追加
- [x] `.github/workflows/test.yml` の `Install dependencies` に
      `papermill ipykernel` を追加
- [x] `.gitignore` を確認（`.ipynb_checkpoints` は既に登録済みだった）

## フェーズ 1: 非コード部分の整理（全31本）

- [x] 全31本のdocstring・コメントを精査し、上記判定基準に従って分類する
- [x] API固有の仕様説明を `docs/api/README.md` の該当セクションへ統合
      （`TreeSearchPlayer` セクションの新設含む。POKEDEX節も新設）
- [x] 整理後、`python -m pytest tests/ -v`（既存の `.py` ベースの
      スモークテスト）が通ることを確認（ローカル環境のeditable installが
      別worktreeを指していたため `PYTHONPATH=src` を付与して確認。
      6050 passed, 0 failed, 1 skipped）

## フェーズ 2: パイロット変換

- [x] `examples/01_basics/01_battle_against_intro.py` を変換しパターンを確立
- [x] `05_benchmark/01_step_time_benchmark.py`（argparse→パラメータセル）を
      変換し、papermillのパラメータ注入を検証

**重要な環境問題**: グローバルpip環境の `jpoke` editable installが別worktree
（`C:\Users\tmtmh\Documents\pokemon\jpoke-loop\fuzz_log`）を指しており、Jupyter
カーネル経由の実行がそちらの古いコード（`Battle.can_continue()`未実装）を見て
しまい `AttributeError` で失敗する現象が発生した。グローバル環境は他セッションと
共有のため書き換えず、`C:\Users\tmtmh\AppData\Local\Temp\jpoke_nbvenv` に
本リポジトリを editable install した検証専用venvを作成し、カーネル名
`jpoke-nb-verify` として登録した。以降のnotebook実行検証は必ずこのvenv/カーネルを
使う（`-k jpoke-nb-verify` を明示）。scratchpad配下にvenvを作るとWindowsの
パス長制限でpipインストールに失敗するため、短いパス（`%TEMP%` 直下）に作成する。

## フェーズ 3: 残り27本の一括変換

- [x] 4並列Agentでディレクトリごとに変換、元の `.py` 29本分を削除
      （nash系2本は残す）。ruff（`.ipynb`のF404はper-file-ignoreで許容）・
      検証venv経由の一括papermill実行（29本すべてOK）で確認済み

## フェーズ 4: スモークテスト・ドキュメント更新

- [x] `tests/test_examples_smoke.py` を ipynb(papermill) + py(サブプロセス)の
      二本立てに書き換え（検証venvで31件全passを確認）
- [x] `.internal/tests/test_examples_smoke.md` を更新（`scripts/generate_test_list.py`
      実行時に無関係な `.internal/tests/items.md` の差分が出たため、そちらは破棄した）
- [x] `examples/README.md` にColabバッジ・実行導線を反映（各 `.ipynb` 冒頭に個別のColabリンクを追加、
      `9e1011ac8`（`example修正`）でのディレクトリ再編（01_basics→01_getting_started 等）に
      追随できていなかった README を現行構成に合わせて全面更新。ルート `README.md` の
      `examples/01_basics/...` `examples/05_benchmark/...` という古いパス記載も修正）

## フェーズ 5: 検証・PR

- [x] `ruff check src/ tests/ scripts/ examples/`（`.ipynb`のF404は
      per-file-ignoreで許容）、`mypy`、`pytest tests/ -v`
      （6032 passed, 1 skipped + test_examples_smoke.py 31 passed）が
      通ることを確認
- [x] `tests/test_code_conventions.py` が `examples/` を `.py` 固定で
      走査しており `.ipynb` 化した29本の回帰検知（jpoke.testing言及、
      アイテムAPI言及、actives[直接アクセス禁止等7項目）が効かなく
      なっていたのを発見・修正（`_iter_example_files`/`_example_text`/
      `_example_first_code_text` ヘルパーを追加し `.py`/`.ipynb` 両対応化）
- [ ] `gh pr create` → 確認の上 `gh pr merge`
