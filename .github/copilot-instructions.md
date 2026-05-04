# Copilot 指示

## 対象
- ポケモン SV のシングルバトルのみを対象とする。
- 既存コードが対応していない限り、ダブルバトル前提の設計はしない。

## 最新実装スナップショット（2026-04-29）

進捗判断の基準は「データ定義での明示 `handlers` 登録」とする。

| カテゴリ | 総数 | 実装済み（明示 handlers） | 未実装 |
| --- | ---: | ---: | ---: |
| 特性 | 299 | 38 | 261 |
| 持ち物 | 154 | 59 | 95 |
| 技 | 693 | 130 | 563 |

補足:
- 仕様書ファイル数: 特性 87 / 持ち物 38 / 技 64
- 専用テスト関数数: `tests/test_ability.py` 71 / `tests/test_item.py` 10 / `tests/test_move.py` 12

## 実装時の参照順
1. `src/jpoke/core/handler.py`
2. `src/jpoke/core/context.py`
3. `src/jpoke/core/event.py`
4. `src/jpoke/core/battle.py`
5. `src/jpoke/data/models.py`
6. 対象 `src/jpoke/data/` と `src/jpoke/handlers/`
7. `tests/test_utils.py` と最寄りの既存テスト

## ルールの置き場所
- リポジトリ全体の方針はこのファイルに置く。
- Python 実装の詳細ルールは `.github/instructions/python.instructions.md` を使う。
- 文書更新の詳細ルールは `.github/instructions/docs.instructions.md` を使う。

## 実装方針メモ
- `data/*.py` の `partial(...)` は宣言的な定数束縛に留める。
- `handlers/*` では lambda を増やさず、名前付き関数か共通 helper を優先する。
- 特性・技・道具の意味が強い処理は、汎用 `partial(...)` で直接表さず `handlers/*` に寄せる。

## 作業後の更新ルール
- 作業完了前チェックとして、実装を変更したら対応する `progress/*.md` を必ず更新する。
- 進捗更新漏れを防ぐため、最終報告前に「変更ファイル」と `progress/*.md` の整合を確認する。
- `README.md` の集計は `progress/*.md` と一致させる。
- `.github/` 配下の指示書は短く保ち、重複する説明を増やさない。
