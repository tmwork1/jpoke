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
| 状態異常 | [ailment_gen9.md](ailment_gen9.md) | 2026-02-01 | まひ、やけど、ねむり、こおり |
| フィールド | [field_gen9.md](field_gen9.md) | 2026-02-01 | 天候・地形・サイド・グローバル |
| 揮発性状態 | [volatile_gen9.md](volatile_gen9.md) | 2026-02-01 | メロメロ、アンコール、こんらんなど |
| ダメージ計算 | [damage_calculation.md](damage_calculation.md) | - | ダメージ計算式詳細 |
| イベント進行 | [event_gen9.md](event_gen9.md) | 2026-02-01 | 処理フロー整理 |
| アイテム | [item_gen9.md](item_gen9.md) | - |  |
| 技分類 | [move_gen9.md](move_gen9.md) | 2026-02-02 | 追加効果別の分類メモ |

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
| 2026-02-03 | リサーチ領域に限定するガイドラインを明記 |
| 2026-02-02 | README最適化（テーブル化、エージェント規則追加） |
| 2026-02-01 | README作成、ailment_gen9.md追加 |