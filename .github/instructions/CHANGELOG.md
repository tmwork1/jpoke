# 変更履歴

## 2026年3月1日

### 指示書の大幅更新

- .github/copilot-instructions.md: HandlerReturn の仕様変更（stop_event が bool に）を反映
- .github/instructions/architecture.md: BattleContext のエイリアス仕様、マネージャー構成の最新化
- 実装状況の追加（状態異常100%完了、フィールド効果100%完了等）
- ファイル構成の詳細化（core/, model/, data/, handlers/ 配下のファイル一覧）

**背景:**
プロジェクトの成長に伴い、HandlerReturn の仕様が NamedTuple に変更され、BattleContext のエイリアス機能が追加されました。また、多数のマネージャークラスが core/field_manager.py に整理され、フィールド効果管理が体系化されました。

**主な変更点:**
- HandlerReturn: `stop_event` が `HandlerResult` から `bool` に変更
- BattleContext: `source`/`target` と `attacker`/`defender` のエイリアス関係を明確化
- Battle クラス: WeatherManager, TerrainManager, GlobalFieldManager, SideFieldManager の導入
- 実装進捗: 状態異常（6/6）、フィールド効果（21/21）完了

**影響ファイル:** .github/copilot-instructions.md, .github/instructions/architecture.md

---

## ハルシネーション記録

### オートガード の架空実装（2026年2月6日 削除）

**発生原因:** 優先度データ検証時にAIが"オートガード"という技を実装候補として追加したが、実際のポケモン第9世代には存在しない架空の技であった

**削除対象:**
- src/jpoke/data/move.py の "オートガード" MoveData 定義
- docs/spec/action_order.md の +4優先度リストからオートガード削除

**教訓:** ゲーム仕様の外部検証が必要。技・アイテム・特性などの追加時は公式ポケモン図鑑/仕様書との突合確認を実施すべき

---

## 2026年2月1日

### フィールドシステムの日本語化と tick_fields 追加

- type_defs.py: GlobalField/SideField を日本語化
- field_manager.py: 辞書キーを日本語に変更
- tick_fields 関数追加（tests/test_utils.py）
- サイドフィールド効果を修正（イベントManager、ねばねばネット）
- test_utils.start_battle に ally_side_field, foe_side_field, global_field パラメータ追加
- テストコード大幅簡略化（3-5行短縮/テスト）

**影響ファイル:** src/jpoke/utils/, src/jpoke/core/, src/jpoke/handlers/field.py, tests/

## テンプレート

### YYYY年MM月DD日

**修正内容:**
- 変更1

**影響ファイル:**
- ファイル1
