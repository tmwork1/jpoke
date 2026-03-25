# spec/ — 仕様調査メモ置き場

第9世代ポケモンの挙動を実装する際に参照する調査資料をまとめたディレクトリ。
実装方針・テスト方針・進捗管理はここには含めない。

---

## ファイル一覧

| カテゴリ | ファイル / ディレクトリ | 内容 |
|---------|----------------------|------|
| ターン進行 | [turn.md](turn.md) | ターン全体の処理フロー |
| 行動順 | [action_order.md](action_order.md) | 優先度・速度順の判定 |
| ダメージ計算 | [damage.md](damage.md) | ダメージ計算式詳細 |
| 命中・回避 | [accuracy.md](accuracy.md) | 命中率・回避率の整理 |
| 急所 | [critical.md](critical.md) | 急所ランク・計算 |
| 状態異常 | [ailment.md](ailment.md) | どく・まひ・やけど・ねむり・こおり |
| フィールド概要 | [field.md](field.md) | 天候・地形の概要 |
| グローバル場 | [global_field/](global_field/) | 天候・地形の個別メモ |
| サイド場 | [side_field/](side_field/) | リフレクター等サイド効果 |
| 揮発性状態 | [volatile/](volatile/) | こんらん等一時的な状態 |
| 特性 | [ability/](ability/) | 特性ごとの個別メモ |
| アイテム | [item/](item/) | アイテムごとの個別メモ |
| テラスタル | [terastal.md](terastal.md) | テラスタル関連仕様 |
| PP | [pp.md](pp.md) | PP消費・枯渇まわりの仕様 |
| 技一覧(物理) | [move/physical_move.md](move/physical_move.md) | 物理技の一覧 |
| 技一覧(特殊) | [move/special_move.md](move/special_move.md) | 特殊技の一覧 |
| 技一覧(変化) | [move/status_move.md](move/status_move.md) | 変化技の一覧 |
| 追加効果 | [move/move_secondary.md](move/move_secondary.md) | 攻撃技の追加効果 |
| 技ラベル | [move/move_label.md](move/move_label.md) | ハンドラから参照される識別子 |
| 技メモ(個別) | [move/](move/) | 個別技の調査メモ |
| その他 | [misc/](misc/) | 上記に分類しにくい雑多なメモ |

---

## 文書の書き方

各ファイルに含めるべき内容：

- **基本効果** — 第9世代での動作（必須）
- **第9世代での変更点** — 過去世代からの差分（あれば）
- **相互作用・例外** — 他効果との組み合わせや特殊ケース（あれば）
- **参考資料** — 参照したURL（ポケモンWikiなど）

実装方針・テスト仕様・進捗は書かない。

---

## 参照元

- [ポケモンWiki](https://wiki.xn--rckteqa2e.com/)