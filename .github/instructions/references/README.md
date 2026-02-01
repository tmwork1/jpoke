# 参考資料

本ディレクトリには、**ターンフローや効果処理の仕様**を定義した資料が格納されている。
実装時は、これらの仕様を参照すること。

## ファイル一覧

### `turn_flow.csv`
- **内容**: ターン処理フローの詳細
- **用途**: ターン制御の実装時に参照
- **関連ファイル**: `src/jpoke/core/turn_controller.py`

### `event_priority_flow_detailed.md`
- **内容**: イベント/Priority/処理の詳細一覧（1処理1行形式）
- **用途**: 各イベント時の処理フロー確認、実装進捗トラッキング
- **元データ**: `jpoke - ターン.csv`
- **関連ファイル**: `src/jpoke/core/turn_controller.py`, `src/jpoke/handlers/*.py`

### `jpoke - ターン.csv`
- **内容**: ターン処理の詳細フロー（元データ）
- **用途**: Copilot向け仕様書作成の基礎資料
- **関連ファイル**: `src/jpoke/core/turn_controller.py`

---

## 使い方

これらのファイルは、ターン制御のロジックを実装・検証する際に参照すること。

詳細なアーキテクチャについては、[`architecture.md`](../architecture.md) を参照。
