# Research Documentation Index

jpoke プロジェクトで実施した各種リサーチの結果を文書化したファイルが格納されています。

---

## 📋 目的

1. **仕様の正確な記録** - 第9世代ポケモンの仕様を正確に記録
2. **実装の根拠** - コード実装の判断基準となる情報を提供
3. **知識の共有** - チームメンバーや将来の開発者への情報共有
4. **メンテナンス性** - 実装後の修正や拡張時の参照資料

---

## 📁 リサーチ文書一覧

| カテゴリ | ファイル | 調査日 | 実装状況 | 備考 |
|---------|---------|--------|---------|------|
| 状態異常 | [ailment_gen9.md](ailment_gen9.md) | 2026-02-01 | ✅ 完了 | まひ、やけど、ねむり、こおり |
| フィールド | [field_gen9.md](field_gen9.md) | 2026-02-01 | ✅ ほぼ完了 | 天候・地形・サイド・グローバル |
| 揮発性状態 | [volatile_gen9.md](volatile_gen9.md) | - | 🚧 作業中 | メロメロ、アンコール、こんらんなど |
| ダメージ計算 | [damage_calculation.md](damage_calculation.md) | - | ✅ 完了 | ダメージ計算式詳細 |
| イベント進行 | [event_gen9.md](event_gen9.md) | 2026-02-01 | 🚧 作業中 | 約500件の処理フロー（進捗管理兼用） |

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
- **実装上の考慮事項** - イベント、ハンドラ、エッジケース
- **実装マッピング** - コード実装との対応表
- **テスト方針** - 確認すべきテスト項目
- **既知の制限事項** - 未実装項目や今後の拡張ポイント

### ファイル命名規則
`[カテゴリ]_[テーマ].md` 形式で命名

例: `ability_telepathy.md`, `move_hazards.md`, `field_weather.md`

### エージェント別の役割
リサーチは **Research Specialist (RSC)** が担当し、発言時は先頭に `RSC:` を付けること。

詳細は [.copilot-instructions.md](../../.copilot-instructions.md) 参照。

---

## 🗂️ フォルダ構成

**現在の構成**: フラット（全ファイルを `docs/research/` 直下に配置）

各カテゴリのリサーチ文書が3件以上になった場合、サブフォルダへの分離を推奨：

```
docs/research/
├── README.md              # このファイル
├── abilities/             # 特性関連（3件以上で分離）
├── moves/                 # 技関連（3件以上で分離）
├── items/                 # 持ち物関連（3件以上で分離）
└── mechanics/             # バトルメカニクス関連（3件以上で分離）
```

---

## 🔗 関連リソース

- [.copilot-instructions.md](../../.copilot-instructions.md) - エージェント発言規則
- [エージェントワークフロー](../../.github/instructions/agents/workflow.md) - リサーチから実装までの全体フロー
- [Research Specialist定義](../../.github/instructions/agents/05_research.md) - リサーチ専門家の役割
- [ダッシュボード](../../dashboard.json) - 実装進捗状況
- [アーキテクチャ](../../.github/instructions/architecture.md) - システム設計詳細
- [ポケモンWiki](https://wiki.xn--rckteqa2e.com/) - 主要な参照元

---

## ✏️ 更新履歴

| 日付 | 変更内容 |
|------|---------|
| 2026-02-02 | README最適化（テーブル化、エージェント規則追加） |
| 2026-02-01 | field_gen9.md追加（.github/instructions/から移行） |
| 2026-02-01 | README作成、ailment_gen9.md追加 |