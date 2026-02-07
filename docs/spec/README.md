# Research Documentation Index

jpoke プロジェクトで実施した各種リサーチ結果を文書化したファイルが格納されています。

---

## 📋 目的

1. **仕様の正確な記録** - 第9世代ポケモンの仕様を正確に記録
2. **知識の共有** - チームメンバーや将来の開発者への情報共有
3. **参照性** - 実装・テストとは分離した調査資料として整理

---

## 📁 リサーチ文書一覧

| カテゴリ | ファイル | 調査日 | 備考 |
|---------|---------|--------|------|
| 状態異常 | [ailment.md](ailment.md) | - | まひ、やけど、ねむり、こおり |
| 命中・回避 | [accuracy.md](accuracy.md) | - | 命中率、回避率の整理 |
| 行動順 | [action_order.md](action_order.md) | - | 優先度、順序判定 |
| 急所 | [critical.md](critical.md) | - | 急所ランク、計算 |
| ダメージ計算 | [damage_calc.md](damage_calc.md) | - | ダメージ計算式詳細 |
| イベント進行 | [event.md](event.md) | - | 処理フロー整理 |
| フィールド | [field.md](field.md) | - | 天候・地形の概要 |
| グローバル場 | [global_field/](global_field/) | - | 天候・地形の個別メモ |
| サイド場 | [side_field/](side_field/) | - | サイド効果の個別メモ |
| 揮発性状態 | [volatile/](volatile/) | - | 個別メモ |
| アイテム | [item/](item/) | - | 個別メモ |
| テラスタル | [terastal.md](terastal.md) | - | テラスタル関連 |
| PP | [pp.md](pp.md) | - | PP周りの仕様 |
| 技カテゴリ | [move/カテゴリ.md](move/カテゴリ.md) | - | 追加効果別の分類 |
| 技一覧(物理) | [move/physical_move_list.md](move/physical_move_list.md) | - | 物理技一覧 |
| 技一覧(特殊) | [move/special_move_list.md](move/special_move_list.md) | - | 特殊技一覧 |
| 技一覧(変化) | [move/status_move_list.md](move/status_move_list.md) | - | 変化技一覧 |
| 技メモ(個別) | [move/](move/) | - | 個別技の調査メモ |

### 主要な参照元
- [ポケモンWiki - ターン](https://wiki.xn--rckteqa2e.com/wiki/%E3%82%BF%E3%83%BC%E3%83%B3)
- [ポケモンWiki](https://wiki.xn--rckteqa2e.com/)

---

## 📝 文書作成ガイドライン

### 必須項目
- **調査日** - リサーチを実施した日付
- **対象世代** - 第9世代など
- **調査範囲** - 調査した項目のリスト
- **基本効果** - 各項目の詳細な効果説明
- **参考資料** - 参照したURL（ポケモンWikiなど）

### 推奨項目
- **第9世代での変更点** - 過去世代からの変更
- **相互作用・注意点** - 他効果との組み合わせや例外

### 除外する内容
- 実装方針、テスト方針、進捗管理、コード参照

### ファイル命名規則
`[カテゴリ]_[テーマ].md` 形式で命名

例: `ability_telepathy.md`, `move_hazards.md`, `field_weather.md`

---

## 🔗 関連リソース

- [エージェントワークフロー](../../.github/instructions/agents/workflow.md) - リサーチから実装までの全体フロー
- [Research Specialist定義](../../.github/instructions/agents/05_research.md) - リサーチ専門家の役割
- [アーキテクチャ](../../.github/instructions/architecture.md) - システム設計詳細
- [ポケモンWiki](https://wiki.xn--rckteqa2e.com/) - 主要な参照元

---

## ✏️ 更新履歴

| 日付 | 変更内容 |
|------|---------|
| 2026-02-07 | 文書一覧を最新の構成に更新 |
| 2026-02-03 | リサーチ領域に限定するガイドラインを明記 |
| 2026-02-02 | README最適化（テーブル化、エージェント規則追加） |
| 2026-02-01 | README作成、ailment_gen9.md追加 |