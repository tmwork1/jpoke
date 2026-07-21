# 計画: ドキュメント構造の見直し（poke-env比較レビュー）

更新日: 2026-07-21

## 背景

ユーザー依頼: 「poke-envの導入ドキュメントは非常にわかりやすい。参考にして、jpokeの
ドキュメントの構造をレビューせよ」。poke-env公式ドキュメント（`.internal/poke-env/api_reference/`
にキャッシュ済みのHTML）とjpoke側の`README.md` / `CONTRIBUTING.md` / `docs/` /
`examples/` を比較した結果を、このレビュー会話のレポートとして本ファイルに記録し、
指摘事項のうち合意が得られたものを本ブランチで実施する。

## poke-envの構造（参考にした点）

Sphinxベースの3階層構成。どのページからでも同一のサイドバーツリーが表示され、
迷わない。

1. **User guide**: 「Getting Started」（インストール→ローカルサーバー起動→
   実際に動いて出力が出る最小サンプル→エージェント作成へのリンク集→接続設定→
   "What Next"で次の一手を提示）と「Examples」（一覧ページ＋積み上げ式の
   Quickstartノートブック。実行済みセル番号[1][2][3]…と出力がサイト内に
   埋め込まれている）
2. **Main modules documentation**: `Battle`/`Player`/`Pokemon`/`Move`等、
   ドメインオブジェクトごとに1ページ。docstringからの自動生成のみ（手書きの
   並行リファレンスは持たない）
3. **Standalone submodules documentation**: `Data`/`PS Client`/`Teambuilder`等の
   ユーティリティ系を上記と明確に分離

## jpokeの現状構造との対応

| poke-env | jpoke |
|---|---|
| Getting Started（独立ページ） | 無し。`README.md`（`docs/index.md`が`include-markdown`で丸ごと取り込み）が兼務 |
| Examples（一覧＋積み上げ式Quickstart、サイト内で実行結果を閲覧可） | `examples/README.md`（一覧、各`.ipynb`はGoogle Colabバッジ経由でワンクリック実行） |
| Main/Standalone modules（自動生成のみ） | `docs/api/README.md`（手書き890行）＋`docs/reference/*.md`（mkdocstrings自動生成）の二重構成 |
| CONTRIBUTING（開発者向けを分離） | `CONTRIBUTING.md`はあるが`README.md`と内容重複 |

## 所見（優先度順、および見送り事項）

1. **`README.md`が利用者向け/貢献者向け情報を1ページに混在**（246行）。
   インストール→クイックスタート→アーキテクチャ→ドキュメント地図→実装状況→
   計算速度ベンチマーク→テストヘルパー→開発セットアップ→テスト実行→
   開発ツール→ライセンス、と一枚に積み上がっている。
2. **`README.md`と`CONTRIBUTING.md`の内容重複**。`README.md`の「開発
   （clone前提）」「テストの実行」「開発ツール」節が`CONTRIBUTING.md`の
   「開発環境のセットアップ」「テストの実行」「コードスタイル」節とほぼ
   同一テキストで存在し、`docs/index.md`・`docs/contributing.md`双方が
   `include-markdown`でそのまま公開されるため、片方だけ更新されて
   食い違うドリフトリスクがある。
3. **APIリファレンスの二重構成**（`docs/api/README.md`手書き890行 +
   `docs/reference/*.md`自動生成）。`docs/reference/index.md`で役割の説明は
   あるが、`docs/api/README.md`自体の冒頭には簡潔な相互参照はあるものの
   十分に目立たない。なお本構成自体は`.internal/plan/notebook_examples.md`
   （notebook化プロジェクト）で「examplesのAPI仕様説明を`docs/api/README.md`に
   統合する」という意図的な設計判断として導入された経緯があり、内容を
   薄める対象ではなく**役割分担の明示を強化する**対応にとどめる。
4. **`examples/04_research/`が空のまま放置**され、`examples/README.md`にも
   記載が無い（`04_others/`のみ記載）。

### 見送り事項（意図的にpoke-env流を採用しない）

- poke-envはExamplesページ自体にノートブックの実行結果を静的に埋め込んでいるが、
  jpokeは**Google Colabバッジ経由でその場で実行できる**方式を取っている
  （`.internal/plan/notebook_examples.md`で意図的に構築済み）。ユーザー確認の
  結果、**Colab上でその場で動かせる点はjpoke独自の強みであり維持する**。
  ドキュメントサイト内へのノートブック出力の静的埋め込みは行わない。

## スコープ・対象ファイル

- `examples/04_research/`（削除）
- `README.md`（開発者向け重複節の整理、`CONTRIBUTING.md`への導線化）
- `CONTRIBUTING.md`（変更なし。重複解消後の一次情報源として維持）
- `docs/api/README.md`（冒頭の役割説明を強化）
- `docs/reference/index.md`（相互参照の追記、必要なら）

## フェーズ

### フェーズ0: 前提

- [x] `feature/docs-restructure`ブランチ・worktree（`jpoke-work/docs-restructure`）を作成
- [x] 本計画書を作成

### フェーズ1: `examples/04_research/`削除

- [x] 空ディレクトリを削除（`examples/README.md`に記載が無く、`git ls-files`にも
      現れないため追跡対象外と確認済み）

### フェーズ2: README/CONTRIBUTING.mdの重複解消

- [x] `README.md`の「開発（clone前提）」「テストの実行」「開発ツール」節を、
      `CONTRIBUTING.md`への短い導線（「開発に貢献する」節）に置き換える
- [x] `README.md`の他の節（対象範囲・インストール・クイックスタート・
      アーキテクチャ・ドキュメント地図・実装状況・計算速度・テストヘルパー・
      ライセンス）はそのまま維持する（GitHub/PyPI/docsサイト共通の
      ランディングとして必要な内容のため）
- [x] README側から削った「五十音順チェック（`--check`）コマンド」は
      `CONTRIBUTING.md`のコードスタイル節に移設し、内容を失わないようにした
- [x] `tests/test_code_conventions.py`（`README_PATH`を参照する既存テスト）に
      抵触しないことを確認（10 passed）

### フェーズ3: APIリファレンスの役割分担の明示強化

- [x] `docs/api/README.md`冒頭に、全シグネチャ・全メソッドを網羅した
      自動生成リファレンス（`docs/reference/index.md`）への明示的なリンクを追記
- [x] 内容そのもの（890行のプロース解説）は削らない

### フェーズ4: 検証・PR

- [x] `python -m pytest tests/ -v`が通ることを確認（6127 passed, 1 skipped）
- [x] `python -m ruff check src/ tests/ scripts/ examples/`（All checks passed!）
- [ ] `gh pr create` → 確認のうえ`gh pr merge`
