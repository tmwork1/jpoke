# Copilot 指示

## 対象
- ポケモン SV のシングルバトルのみを対象とする。
- 既存コードが対応していない限り、ダブルバトル前提の設計はしない。

## 進捗の見方

- 進捗判断の基準は「データ定義での明示 `handlers` 登録」とする。
- 実装状況の詳細は `progress/ability.md`、`progress/item.md`、`progress/move.md` を参照する。
- `README.md` は全体像の案内に留め、実装数の集計は載せない。

## 実装時の参照順
1. `src/jpoke/core/handler.py`
2. `src/jpoke/core/context.py`
3. `src/jpoke/core/event.py`
4. `src/jpoke/core/battle.py`
5. `src/jpoke/data/models.py`
6. 対象 `src/jpoke/data/` と `src/jpoke/handlers/`
7. `tests/test_utils.py` と最寄りの既存テスト

## ルールの置き場所
- リポジトリ全体の方針（対象、実装時の参照、進捗管理）はこのファイルに置く。
- Python 実装の詳細ルール（Handler の約束事、状態変更、イベント駆動、テスト）は `.github/instructions/python.instructions.md` を参照。
- 文書更新の詳細ルール（計画書、README、仕様書）は `.github/instructions/docs.instructions.md` を参照。

## 作業後の更新ルール
- 作業完了前チェックとして、実装を変更したら対応する `progress/*.md` を必ず更新する。
- 進捗更新漏れを防ぐため、最終報告前に「変更ファイル」と `progress/*.md` の整合を確認する。
- `README.md` の集計は `progress/*.md` と一致させる。
- `.github/` 配下の指示書は短く保ち、重複する説明を増やさない。
