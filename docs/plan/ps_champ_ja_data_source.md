# 調査: ps-champ-ja を jpoke のデータ基盤にする

更新日: 2026-07-15

## 更新履歴

- **2026-07-16（実行）**: 技の静的パラメータ（type/category/pp/accuracy/priority/急所ランク
  ［`critical_rank`→`crit_ratio`に改名］/target）について、「照合・差分検出ツールとして使う」
  という当初方針から一歩進め、ps-champ-jaでカバーされる技（716件中500件）は
  `src/jpoke/data/moves/move_*.py`側のリテラル指定を削除し、起動時（`common_setup()`）に
  `src/jpoke/data/ps_champ_moves.json`（ps-champ-jaの`moves.json`スナップショット）から
  読み込む方式に変更した（`feature/sync-moves-from-ps-champ-ja`）。可変威力（`power=1`）・
  必ず急所（`crit_ratio=3`）のセンチネルを持つ技のみリテラル値を維持する。`target`は
  ps-champ-jaの13分類（ダブルバトルの隣接関係区別）をシングル専用の5分類へ縮約する
  マッピングで導出し、大部分の技で手入力していた`target=`を削除できた。副次効果として、
  既存の不整合（PP5件・急所ランク2件）が正しい値に修正された。moves/abilities/itemsの
  ハンドラ実装自体は今回も対象外（既存方針どおり）。再同期用スクリプト
  `scripts/ps_champ_ja/sync_moves.py`をチェックイン

## ゴール

https://github.com/tmwork1/ps-champ-ja の `data_jp/` を、jpoke の技・ポケモン等データの
基盤（自動取得・自動同期できるソース）にできるか調査する。

## 現状

- ダウンロードスクリプト `scripts/ps_champ_ja/download.py` を作成済み。GitHub Contents API で
  `data_jp/` 配下を列挙し、`ps-champ-ja/data_jp/` にミラーする（`ps-champ-ja/` は再取得可能な
  外部データとして `.gitignore` 対象）
- 「まるごと差し替え」は**しない**。理由は以下の調査結果の通り、カバー範囲・命名規則・スキーマの
  いずれも jpoke の内部データとそのまま一致しないため
- 現時点では調査のみで、実際の取り込み（変換スクリプト・マージ処理の実装）は未着手

## ps-champ-ja の構成

`tmwork1/ps-champ-ja` は次のパイプラインで `data_jp/` を生成している：

1. `data_raw/` `data_en/`: [Pokemon Showdown](https://github.com/smogon/pokemon-showdown) の
   `champions` mod から抽出（英語・showdown ID ベース）
2. `langmap/*.csv`: [poke-langmap](https://github.com/tmwork1/poke-langmap)（ポケモンWiki由来の
   和名対応表）をビルド時にダウンロード（リポジトリにはコミットされない）
3. `jpoke/`: **本プロジェクト（jpoke）自身の和名データを再利用**（`jpoke/pokedex.json` 等）
4. 上記を `scripts/translate-data.py` で合成し `data_jp/` を生成

`data_jp/` の中身は次の4ファイルのみ:

| ファイル | 内容 |
|---|---|
| `pokedex.json` | 種族データ（和名キー、種族値・タイプ・特性名配列・進化系統・性別比等） |
| `pokedex_excluded.json` | 和名重複等で `pokedex.json` から除外されたフォルム一覧 |
| `moves.json` | 技の静的パラメータ（タイプ・分類・PP・威力・命中率・優先度・急所ランク・対象・flags・Z技/ダイマックス技威力） |
| `learnsets.json` | 種族ごとの習得技リスト（技名のみ、習得方法・レベルの情報なし） |

**abilities.json・items.json は存在しない。** 特性・アイテムの挙動データはこのリポジトリでは
提供されておらず、`data_jp/` はあくまで「種族・技の静的パラメータ・技マシン等の習得可否」の
データセットである。

## ライセンス: 問題なし

ps-champ-ja は `data_raw/` `data_en/` `data_jp/` `jpoke/` を CC BY-NC-SA 4.0 で公開しており、
出典もポケモンWiki（jpoke の `LICENSE-DATA` と同一系統）。jpoke 自身のデータが ps-champ-ja に
再利用されている関係上、系統的な矛盾はない。実際に取り込む場合は `LICENSE-DATA` に
ps-champ-ja / Pokemon Showdown champions mod への言及を追記する。

## 調査結果: 支障となる点

### 1. 技データのカバー率が約70%しかない

| | 件数 |
|---|---|
| jpoke 実装済み技 | 716 |
| ps-champ-ja `moves.json` | 500 |
| ps-champ-ja にあって jpoke 未実装 | 1件（パワーシフト。`docs/progress/move.md` に追加済み。ただし `docs/champions/moves.md` に未掲載で公式仕様として実在するか要確認） |
| jpoke 実装済みだが ps-champ-ja に無い | 217件 |

PS の `champions` mod は「合法ポケモンの誰も覚えない技は収録しない」方針とみられ、README が
定める「第9世代（SV）の技を基本実装する」という jpoke の方針とはスコープが異なる。
**技データの単独の基盤にはできない。** りんごさん（power 90 / PP 12、`docs/champions/moves.md`
と完全一致）のように、カバーされている技の値の信頼度自体は高いため、既存実装済み技の
**値の照合・差分検出用途**には使える。

### 2. ポケモンデータ: jpoke 独自メガシンカ9体が ps-champ-ja に存在しない

| | 件数 |
|---|---|
| ps-champ-ja `pokedex.json` | 1339 |
| jpoke 実装済み | 1286 |

`src/jpoke/data/megaevol.py` に実装済みの以下9体が PS champions mod 側に存在しない：

メガグソクムシャ・メガシャリタツ・メガジガルデ・メガセグレイブ・メガゼラオラ・メガダークライ・
メガニャオニクス・メガヒードラン・メガマギアナ

これらはプロジェクト最初期から実装されている正規コンテンツであり、**上書きインポートすると
静かに消える。** 取り込む場合は追加専用マージ（jpoke 側にしか無いエントリは保持）で設計する
必要がある。

### 3. 命名規則の不一致（単純な名前一致でのマージは失敗する）

ps-champ-ja は基本フォルムを無印名（例: `ジガルデ`）、非基本フォルムのみサフィックス付き
（`ジガルデ(10%)`）で表現する。jpoke は基本フォルムにも明示サフィックスを付ける慣習
（`ジガルデ(50%)`）。該当例: オドリドリ／イキリンコ／トルネロス系／ボルトロス系／
ランドロス系／ギラティナ／フーパ／ザシアン／ザマゼンタ 等、多数。

加えて全角/半角の表記ゆれもある（`ポリゴン２`→`ポリゴン2`、`タイプ：ヌル`→`タイプ:ヌル`）。

単純な名前一致（Pokemon 名文字列での突合）で比較したところ、jpoke 側1286件中 **56件が
不一致**になった（内訳: カスタムメガ9件 + 基本フォルム命名規則差 + 全角半角ゆれ）。

### 4. スキーマが根本的に違う

- pokedex: `types` 配列 vs `type-1`/`type-2`、`baseStats` ネスト辞書 vs `H/A/B/C/D/S` フラット、
  `prevo`/`evos` vs `pre_evolution` のみ（`evos`・`genderRatio`・`requiredItem` は jpoke の
  `PokemonData` に対応するフィールドが無い）
- moves: 静的パラメータのみで、`src/jpoke/data/moves/*.py` が持つハンドラ登録（技固有ロジック）
  は当然含まれない

→ JSON をそのまま読み込むことはできず、**変換・マージスクリプトが必須**。

### 5. データ鮮度・継続同期の仕組みが未整備

`pushed_at: 2026-07-14`（調査時点で前日）と非常に新しいが、再ダウンロード時の差分検知・
バージョン管理の仕組みは現状ない。再実行すると無言で上書きされる。

## 推奨スコープ（今後着手する場合）

1. **pokedex（種族データ）**: 変換スクリプトでスキーマ・命名規則差を吸収しつつ、jpoke 独自
   エントリ（カスタムメガ9体等）を保持する追加専用マージとして実装
2. **moves**: 差し替えではなく、既存716技の power/PP/accuracy 等の**照合・差分検出ツール**
   として利用
3. **abilities/items**: 対象外。既存のポケモンWikiベースのパイプライン（`scripts/wiki/`）を
   継続使用

## 関連

- ダウンロードスクリプト: `scripts/ps_champ_ja/download.py`
- `docs/progress/move.md`: パワーシフトの行を追加済み（未実装・要確認扱い）
