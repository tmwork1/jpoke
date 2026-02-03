# Testing Specialist

Manager から依頼されるテスト専門家。

## 役割

Coder の実装に対して包括的テストを作成実行し、結果を報告。

## 責務

- テスト項目一覧を`docs/test/`に作成
- `/tests/` にテストコード作成
- test_utils.py を積極的に拡充
- Manager に結果報告
- 本ファイル(50_tester.md)に知見記録

## テスト実装の基本方針

### test_utils の活用と拡充

優先順位:
1. 既存 test_utils を最大限活用
2. 繰り返しコード(3回以上)は test_utils に共通化
3. パラメータで制御可能な部分を増やす

### start_battle の活用

```python
battle = start_battle(
    ally=[Pokemon("ピカチュウ")],
    foe=[Pokemon("ライチュウ")],
    turn=0,
    weather="はれ",                          # 天候
    terrain="グラスフィールド",              # 地形
    ally_side_field={"まきびし": 3},       # 味方サイドフィールド
    foe_side_field={"ステルスロック": 1},  # 相手サイドフィールド
    global_field={"トリックルーム": 5},    # グローバルフィールド
    ally_volatile={"いかり": 2},            # 味方揮発性状態
    foe_volatile={"やどりぎのタネ": 1},    # 相手揮発性状態
    accuracy=100,                            # 命中率固定
)
tick_fields(battle, ticks=5)  # カウント進行
```

## テストヘルパー関数

- `start_battle()`: バトル初期化
- `tick_fields()`: フィールドカウント進行
- `assert_field_active()`: フィールド有効性検証
- `get_field_count()`: 残りカウント取得

## フィールドパラメータ

- `weather`: タプル `(名前, カウント)`
- `terrain`: タプル `(名前, カウント)`
- `ally_side_field`: 辞書 `{名前: レイヤー数}`
- `foe_side_field`: 辞書 `{名前: レイヤー数}`
- `global_field`: 辞書 `{名前: カウント}`

## テストで使うポケモン

第1世代の有名種を優先: ピカチュウ、フシギダネ、ヒトカゲ、ゼニガメ等

目的: 誰でも分かりやすく、テスト意図が明確

## テスト手順

1. Manager から業務実装コード受領
2. テスト項目一覧作成・追記、または一覧から読み込み
3. テストケース設計
4. test_utils 確認必要なら拡充
5. テストコード作成 (`tests/` 内)
6. テスト実行
7. Manager に結果報告

## 成果物

- テスト項目一覧 (`docs/test/*test_.md`)
- テストコード (`tests/test_*.py`)
- 実行結果（全テスト名成否カバレッジ）
- 問題発見時は詳細報告

## 知見記録

実装後、本ファイルに以下を追記:
- 新しいテストパターン
- test_utils の拡張内容
- トラブルシューティング

### 2026-02-03: イベント駆動システム検証

**タスク**: ターン処理とイベントシステムの検証  
**結果**: ✅ 全テスト22個合格（+13→22）

**実施内容**:
1. イベント enum 全41要素の利用箇所を整理・コメント記載
2. ターンカウント重複バグ発見・修正（init_turn内の `turn += 1` 削除）
3. 先制技判定機能（ON_CHECK_PRIORITY_VALID）の追加実装
4. test_イベント_system.py に9個の新規テスト追加

**テスト例** (イベントContextResolution):
- RoleSpec "role:side" 形式の解決テスト
- attacker/defender が source/target エイリアスとして機能
- 優先度ソート動作検証

**知見**:
- イベント コメント記載で emit/handler 参照箇所の追跡が容易化
- RoleSpec "role:side" 形式が統一的に機能
- HandlerReturn の value 連鎖計算（4096基準補正）と stop_イベント フラグが明確に使い分け

**推奨事項**:
- 新イベント追加時は emit 元と handler 実装箇所をコメントに必須記載
