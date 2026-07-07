# コードレビュー — 総合インデックス

日付: 2026-07-05
対象: `src/jpoke/` 全体
観点: 責務分離、内部実装の隠蔽、拡張性、過剰設計

`src/jpoke/` をディレクトリ単位で5分割し、それぞれ独立にレビューした。各ファイルは
実装を実際に読み直した上で書かれており、過去に一度統合レビュー（現在は本ファイル群に
置き換え）で指摘された内容も全件再検証している。

| ファイル | 対象ディレクトリ | 重大 | 中程度 | 過剰設計 | 軽微 |
|---|---|---|---|---|---|
| [core.md](core.md) | `core/`（Battle Facade・専門マネージャー群） | 3 | 11 | 4 | 5 |
| [data.md](data.md) | `data/`（特性・技・アイテム等の定義・登録） | 1 | 3 | 3 | 3 |
| [handlers.md](handlers.md) | `handlers/`（固有効果ロジックの実装） | 1 | 6 | 2 | 4 |
| [model.md](model.md) | `model/`（`Pokemon`/`Move`/`GameEffect`系データモデル） | 1 | 5 | 3 | 6 |
| [types_enums_utils.md](types_enums_utils.md) | `types/`, `enums/`, `utils/` | 1 | 3 | 3 | 4 |

---

## 最優先で対応すべき指摘（実害のあるバグ）

今回のレビューで新規に見つかった、テストで検出されていない実際の不具合。

1. **`data/megaevol.py:98` の `MEGA_POKEMONS` がジェネレータ式**（[data.md CRIT-1](data.md#crit-1-datamegaevolpy98-の-mega_pokemons-がジェネレータ式であり初回消費後は恒久的に壊れる)）
   `Pokemon.megaevolved` が一度評価されると以後恒久的に壊れる。`tuple(...)`/`frozenset(...)` へ変更するだけの1行修正。
2. **`handlers/move_status.py` が `Pokemon._stats_manager` の内部可変リストを直接書き換え**（[model.md CRIT-1](model.md#crit-1-handlersmove_statuspy-が-pokemon-の非公開属性-_stats_manager-の内部可変リストを直接書き換えている)）
   ガードシェア/スピードスワップ/パワーシェア/パワートリックの4関数がカプセル化を迂回。`PokemonStats.stats` が防御的コピーをしていないため、モデル内部表現の変更でサイレントに壊れる。
3. **`RoleSpec` の役割混在が実行時にハンドラを恒久的にサイレント無効化しうる**（[types_enums_utils.md ISSUE-1](types_enums_utils.md#issue-1-rolespec-の役割混在が型エラーではなくサイレントな恒久的ハンドラ無効化として顕在化する既存-issue-6-の再検証深掘り)、core.md ISSUE-6 と対応）
   `subject_spec` にコンテキスト型と不整合な role を指定しても例外にならず、該当ハンドラが発動しなくなる。実装ミスに気づく手段がテスト実行のみ。
4. **`core/__init__.py` の import 順に依存した循環 import**（[core.md CRIT-3](core.md#crit-3-core__init__py-の-import-順に依存した脆弱な循環-import-パターン)）
   6ファイルが `jpoke.core` パッケージ経由で `EventContext` を import しており、`__init__.py` の行順を変えると即座に破綻する。

---

## モジュール横断で繰り返し見つかったパターン

### 1. ドキュメントドリフト（docstring・コメントが実装と乖離）
`enums/event.py` の emit/handle コメント（37箇所以上、[types_enums_utils.md CRIT-1](types_enums_utils.md)）を筆頭に、
`Battle` docstring（[core.md CRIT-2](core.md)）、`Volatile` docstring（[model.md ISSUE-4](model.md)）、
`common_setup()` docstring（[data.md ISSUE-15](data.md)）など、5ファイル中4ファイルで同種のドリフトが見つかった。
いずれも「リファクタ後にコメント/docstringだけ更新されずに取り残される」という共通の根本原因を持つ。
更新を強制する仕組み（lint・テスト）が存在しないため、今後も同種のドリフトが蓄積し続けると見られる。

### 2. Facade/カプセル化のバイパス（双方向）
`core.md` だけでも `TurnController`→`SwitchManager`直接アクセス（ISSUE-9）と
`PokemonQuery`→`TurnController.action_order`直接アクセス（ISSUE-10、今回新規発見）という
**逆方向の2つのバイパス**が見つかっており、「マネージャー間通信は `Battle` を介する」という
設計方針が両側から部分的に崩れている。`model.md` の `_stats_manager` 直接アクセス（CRIT-1）も
同種の「レイヤーをまたいだ非公開属性への直接アクセス」であり、`core/`・`model/`双方に
共通する構造的な弱点。

### 3. 過剰設計は「不要な抽象化」より「未共有の重複」の方が支配的
4モジュール（core/data/handlers/model）全てで過剰設計の観点を重点的に調査したが、
結論として「抽象化しすぎ」の実例（`core.md` OVER-1〜3の一部、`types_enums_utils.md` OVER-1〜2）は
限定的である一方、「共有すべきなのに個別にコピペされている」（`ON_MODIFY_DURATION`処理の3重複、
`common_setup()`の6ファイル重複、のみこむ/はきだすの重複）という**逆方向の指摘の方が多かった**。
唯一明確に「使われていない汎用性」と言えるのは `handlers/lethal.py` の `_heal_at_pinch`（OVER-2）と
`core/context.py` の `BaseContext.derive()`（OVER-3、呼び出し1箇所のみ）。

### 4. `id()`/生リストをキーにした一時状態の受け渡し
`handlers/ability.py` の `id(mon)` キー・グローバル辞書（[handlers.md CRIT-1](handlers.md)）は、
`Battle` の deepcopy 多用設計と根本的に相性が悪い。`メガソーラー` は状態フラグを
インスタンス属性化済みだが保存データだけがグローバル辞書に残るという「半分だけ正しい」
実装になっている点が新たに分かった。

---

## モジュール別の総評サマリ

- **core/**: アーキテクチャの一貫性は高いが、`Battle` Facade からの逸脱（ISSUE-8）と
  双方向のバイパス（ISSUE-9, 10）、import順依存の循環（CRIT-3）が優先対応事項。
  過剰設計としては「実体のない7マネージャーへの画一的deepcopy儀式」（OVER-1）が最大の発見。
- **data/**: 「定義と実装の分離」規約は高水準で守られている。最重要はジェネレータバグ（CRIT-1）。
  `GameEffect`派生6dataclassの分割は妥当と判断（過剰設計ではない）。
  `lethal_handlers`二重管理は本日実際に登録漏れインシデントを起こしており再発防止策を提案。
- **handlers/**: 約1,300関数の規模の割に規律が高い。`id()`キー辞書（CRIT-1）が最優先。
  Handlerラッパー6クラスはポリモーフィズムとして一度も使われておらず、ファクトリ関数への
  置き換えでISSUE-15とOVER-1が同時に解消できる。
- **model/**: `GameEffect`統一設計は健全だが、`_stats_manager`直接アクセス（CRIT-1）でカプセル化が
  実質破られている。有効/無効管理機構が6クラス中2クラスだけで使われている偏りも判明（OVER-1, 2）。
- **types/enums/utils/**: `enums/event.py`のドキュメントドリフトが3ディレクトリ中最重要（CRIT-1）。
  `utils/string_utils.py`は未宣言の外部依存を持つ完全なデッドコード（OVER-1）。

---

## 関連: 機能横断レビュー

`src/` のディレクトリ単位の分割とは別に、`Battle.step()` が方策関数内での木探索
（先読みシミュレーション）をどう支えているかを実装から読み解いた上でレビューした。

- [tree_search.md](tree_search.md) — `Battle.copy()`/`build_observation()`/
  `get_available_commands()`/`required_command_type` による木探索サポート機構の実態と、
  相手の合法手がコマンド種別でフィルタされず `sim.step()` が `ValueError` で落ちる
  新規バグ（CRIT-1）を含む指摘。
- [tree_search_framework.md](tree_search_framework.md)（2026-07-07） —
  実装済みの `TreeSearchPlayer`（`scripts/tree_search/framework.py`）を
  利用者・開発者の両視点でレビュー。相手の手が未公開だと探索が無言で退化する問題
  （FW-U1、動作確認済み）、`default_fallback` の再現性バグ（FW-U2）、
  内部 API 直呼び3箇所への構造的依存（FW-D1）など。改善は
  `src/jpoke/players/tree_search_player.py` への昇格（同ファイル4章）を土台に進める方針。

---

## 付記

各ファイルの「重大/中程度/過剰設計/軽微」の指摘には、既存の統合レビューから引き継いだ項目
（現存を再検証済み）と、今回新たに発見した項目が混在する。個々の指摘が既存/新規のどちらかは
各ファイル内の見出しに明記している。
