# コードレビュー — 総合インデックス

日付: 2026-07-12（初版2026-07-05、2026-07-07 tree_search系追加、本改訂で全面再検証・「命名の一貫性・妥当性」を新規観点として追加）
対象: `src/jpoke/` 全体
観点: (1) 責務分離・内部実装の隠蔽・拡張性・過剰設計（既存観点の再検証）、
(2) 変数・関数・クラス・定数名の一貫性と妥当性（新規重点観点）

`src/jpoke/` を8モジュール群に分割し、Sonnetサブエージェント8体を並列投入してそれぞれ独立に
レビューした。各エージェントは対象ファイルを実際に全文読み、前回（2026-07-05, 一部2026-07-07）
レビューの指摘を1件ずつ再検証した上で、今回の主眼である命名観点を新設セクションとして追加した。

| ファイル | 対象ディレクトリ | 重大 | 中程度 | 過剰設計 | 軽微 | 命名 |
|---|---|---|---|---|---|---|
| [core.md](core.md) | `core/`（Battle Facade・専門マネージャー群） | 4 | 12 | 4 | 6 | 8 |
| [data_core.md](data_core.md) | `data/`（`moves/`除く。特性・アイテム・状態異常・場等の定義） | 1 | 3 | 0 | 4 | 5 |
| [data_moves.md](data_moves.md) | `data/moves/`（技データ定義、初回レビュー） | 2 | 3 | 0 | 2 | 3節 |
| [handlers_ability_item.md](handlers_ability_item.md) | `handlers/ability.py`, `ability_paradox.py`, `item.py` | 1 | 4 | 0 | 2 | 7 |
| [handlers_move.md](handlers_move.md) | `handlers/move_attack.py`, `move_status.py`, `move.py` | 0 | 4 | 0 | 2 | 6節 |
| [handlers_status_field.md](handlers_status_field.md) | `handlers/volatile.py`, `ailment.py`, `field.py`, `lethal.py` | 1 | 3 | 1 | 2 | 9 |
| [model_players.md](model_players.md) | `model/`, `players/`（`model.md`の後継） | 1 | 7 | 4 | 5 | 6節 |
| [types_enums_utils.md](types_enums_utils.md) | `types/`, `enums/`, `utils/` | 1 | 5 | 4 | 5 | 6 |

`data_moves.md` は今回が初回レビュー（前回2026-07-05は対象外だった）。`model_players.md` は
`model.md`（2026-07-05）・`tree_search.md`（2026-07-05）・`tree_search_framework.md`（2026-07-07）の
後継ファイルで、旧3ファイルは削除せず残置している。

---

## 最優先で対応すべき指摘（実害のあるバグ）

今回のレビューで新規に見つかった、テストで検出されていない実際の不具合。★は本ラウンドで修正着手。

1. ★**`data/megaevol.py:98` の `MEGA_POKEMONS` がジェネレータ式のまま未修正**
   （[data_core.md CRIT-1](data_core.md#crit-1既存未修正-datamegaevolpy98-の-mega_pokemons-ジェネレータバグが依然として存在する)）。
   2026-07-05に指摘済みだが1週間経っても着手されておらず、`Pokemon.megaevolved` が初回評価後
   恒久的に `False` を返し続ける。`tuple(...)`/`frozenset(...)` へ変更するだけの1行修正。
2. ★**`handlers/lethal.py:573` の `ばかぢから_lower_atk` がぼうぎょ低下を実装していない**
   （[handlers_status_field.md CRIT-1](handlers_status_field.md#crit-1-lethalpy-の-ばかぢから_lower_atk-がぼうぎょ低下を実装していない実バトルとの乖離)）。
   実バトル側（`move_attack.py`）は`atk`/`def`両方を下げるが、リーサル計算側は`atk`のみ。
   詰み判定・木探索が誤った生存確率を返しうる。命名の一貫性チェックから発見された実バグ。
3. ★**`data/moves/move_ha.py:404` の `ハートスワップ` が兄弟技・自系統仕様書と矛盾する
   `accuracy`/`flags` を持つ**（[data_moves.md CRIT-2](data_moves.md#crit-2-ハートスワップmove_hapy404-414の-accuracyflags-が兄弟技自系統の仕様書と食い違っている)）。
   `.internal/spec/moves/パワースワップ.md` は`ハートスワップ`を含む3技全てに`accuracy=None`必中を
   要求しているが、`accuracy=100`のまま。相手の回避率上昇時に本来必中のはずの技が外れる。
4. ★**`core/ailment_manager.py:51` `AilmentManager.apply()` の `ctx` 引数が完全な no-op**
   （[core.md CRIT-4](core.md#crit-4新規-ailmentmanagerapply-の-ctx-引数が完全に-no-op-になっている)）。
   `handlers/`側15箇所以上が`ctx=ctx`を意図的に渡しているが、実装は`if ctx is not None`の
   両分岐が同一の`EventContext`を生成しており一切反映されない。本ラウンドで検証した結果、
   `ON_BEFORE_APPLY_AILMENT`の全登録ハンドラは`source:self`/`target:self`のみを使い
   `AttackContext`固有フィールドを要求していないため、`ctx`パラメータ自体が不要と判断し削除する。
5. ★**`core/battle.py:752` `Battle.set_ailment()` の docstring が実装と矛盾する**
   （[core.md CRIT-5](core.md#crit-5新規-battlesetailment-の-docstring-が実装と矛盾する)）。
   「特性・タイプ等による無効化判定は行わない」と明記するが、実際は型免疫・特性無効化を
   素通りしない。挙動を変えると`examples/`・既存テストへの影響が読めないため、docstring側を
   実装に合わせて修正する（挙動は変更しない）。
6. ★**`handlers/move_attack.py:1706` `ダイヤストーム_sharply_boost_defender_B` の関数名が
   実装と逆**（[handlers_move.md ISSUE-1](handlers_move.md#issue-1-move_attackpy1706-1707-ダイヤストーム_sharply_boost_defender_b-の関数名が実装と矛盾している)）。
   実装（自分の防御+2）は正しいが名前が`defender`を指しており、旧`うそなき`（解消済み）と
   同種の「命名を信頼した保守者を誤読させる」パターン。`_boost_attacker_B`へ改名。
7. `handlers/ability.py:1099,1164` `しろのいななき_boost` が特性キー `じしんかじょう` にも
   登録されている件（[handlers_ability_item.md ISSUE-1](handlers_ability_item.md#issue-1新規-しろのいななき_boost-が異なる2つのabilitydataエントリに登録されdocstringも実名と食い違っている)）は、
   `.internal/spec/abilities/じしんかじょう.md`/`しろのいななき.md` を確認した結果**データ登録は
   正しい**（両特性は公式に同一効果の別名特性）と判明。★docstringのみ実態（2特性共有）に
   合わせて修正する。

---

## モジュール横断で繰り返し見つかったパターン

### 1. ドキュメントドリフト（docstring・コメントが実装と乖離）— 前回から悪化
`enums/event.py` の emit/handle コメントについて、今回13箇所の `emit: core/battle.py` 記載を
実際の呼び出し元と機械的に突き合わせたところ**12箇所が誤り**、`ON_REFRESH_PARADOX_BOOST` に
至っては該当する `emit()` 呼び出しがコードベースに1件も存在しないことが判明した
（[types_enums_utils.md CRIT-1](types_enums_utils.md)）。`Battle` docstring の属性欠落は
前回よりさらに拡大（[core.md CRIT-2](core.md)）。`data/moves/*.py` では2026-07-11のドキュメント
リネーム（`move_list.txt`→`moves.md`）に13箇所のコメントが追随できていなかった
（[data_moves.md CRIT-1](data_moves.md)）。「新規追加時は正確に書けるが、既存記載を遡って
メンテする仕組みがない」という前回の診断が定量的に裏付けられた形。

### 2. Facade/カプセル化のバイパスが新たな形で見つかった
`core/` の双方向バイパス（`TurnController`⇔`SwitchManager`、`PokemonQuery`⇔`TurnController`）は
前回から変化なし。今回新たに、`Pokemon.boosts`（能力ランク辞書）が `_stats`/`_ivs`/`_evs`
と異なり非公開化・専用API化されておらず、40箇所以上のハンドラが絶対値操作のため直接
`mon.boosts[stat] = ...` と書き込んでいることが判明した（[model_players.md CRIT-1](model_players.md)）。
これは旧`_stats_manager`問題（2026-07-05 CRIT-1、`PokemonStats`廃止・`Pokemon`統合により
**解消済み**）と構造的に同一のパターンが、統合から漏れた`boosts`側で再発した形である。

### 3. 命名の一貫性チェックが実バグ発見に直結した（新規観点の最大の成果）
今回新設した「命名の一貫性・妥当性」観点は、単なるスタイル指摘に留まらず複数の実バグ発見に
つながった。`ばかぢから`（`lethal.py`のリーサル計算漏れ）は関数名`_lower_atk`が実装の欠落を
正直に反映していたことで発見され、`ハートスワップ`は「兄弟技と同じハンドラ命名パターンを持つ
技は他の属性も揃っているはず」という前提の検証から発見された。両者に共通するのは、
「命名規則が一貫している箇所ほど、その規則から外れた1件が本物の不整合の兆候になる」という点。

### 4. カテゴリ横断の命名不統一（能力ランク変化・状態異常付与）
`handlers/move_attack.py`（能力ランク変化を具体名`_lower_defender_spd`等66件で表現）と
`handlers/move_status.py`（同じ効果を`_modify_defender_stats`等50件の汎用名で表現）が、
「能力ランク変化」という同一カテゴリに対して系統的に異なる命名規則を採っている
（[handlers_move.md](handlers_move.md)）。状態異常付与でも同様の分裂が`move_status.py`単体で
3パターン発生している。`core/`でも「対象ポケモンの引数名（mon/target）」「イベント補正付き
値計算の動詞（calc_/resolve_）」が10〜15箇所以上にまたがって不統一（[core.md](core.md)）。

### 5. ファイル境界をまたぐ概念の命名は体系的に揃っていない
単一ファイル内の命名規律は総じて高い一方、`field.py`⇔`volatile.py` 間の `ON_CHECK_FLOATING`
ハンドラ（`_grounded` vs `_check_floating`）、`disabled_reason` ライフサイクル管理
（`_apply`/`_remove` vs `_disable_ability`/`_enable_ability`）、`lethal.py`⇔`move_attack.py`
間の同一技ハンドラ命名（`ばかぢから`/`テラバースト`、後者は一致せずとも実装は一致）など、
「同一概念・異なる語彙」パターンが複数モジュールにまたがって見つかった
（[handlers_status_field.md](handlers_status_field.md)）。対照的に `ailment.py`⇔`lethal.py`
間の状態異常ダメージハンドラ（どく/もうどく/やけど）は関数名が完全一致しており、模範例として
記録されている。

### 6. 過剰設計は前回同様「不要な抽象化」より「未共有の重複」が支配的
`_heal_at_pinch`（`lethal.py`）の`heal_with="ability"`分岐が7/7呼び出しとも未使用のまま
現存（[handlers_status_field.md OVER-1](handlers_status_field.md)）、`_INNATE_FLINCH_MOVES`が
`ability.py`/`item.py`に独立して重複定義（[handlers_ability_item.md ISSUE-3](handlers_ability_item.md)）、
`_thaw_attacker`ロジックが11関数に一字一句コピー（[handlers_move.md ISSUE-3](handlers_move.md)）
など、今回も「共有すべきなのに個別に実装されている」指摘の方が「抽象化しすぎ」より多かった。

---

## モジュール別の総評サマリ

- **core/**: `import`順依存の循環import（旧CRIT-3）が解消済みと確認。一方`AilmentManager.apply()`の
  `ctx` no-op（新CRIT-4）と`set_ailment()`のdocstring矛盾（新CRIT-5）という、テストでは
  検出されにくい実装漏れを新規発見。命名観点では「対象ポケモン引数名（mon/target）」
  「calc_/resolve_接頭辞」の不統一が最も広範囲に及んだ。
- **data/（コア定義）**: 前回同様「定義と実装の分離」は高水準維持。`megaevol.py`ジェネレータ
  バグが1週間放置されたままの点が最重要。`ability.py`単体で`subject_spec`位置引数渡しが
  41件見つかるなど、キーワード引数の使用方針がファイルによって徹底されていない。
- **data/moves/**: 初回レビュー。フィールド名・記述順序・五十音順という構造面は約850エントリ
  全件で完全に統一されていた一方、命名パターンの一貫性チェックから`ハートスワップ`の
  仕様違反という実データバグを発見。PP根拠コメント13箇所がドキュメントリネームに未追随。
- **handlers/ability・item**: 旧CRIT-1（`id(mon)`グローバル辞書、メガソーラー半端実装）が
  38コミットを経ても未着手のまま現存、優先度は変わらず最高。新規追加分（どんかん/マイペース）が
  既存の共有ヘルパー化規約を踏襲せずコピー実装された点も要フォロー。
- **handlers/move**: 旧`_stats_manager`問題（model.md CRIT-1相当）は`PokemonStats`廃止
  リファクタで解消済みと確認。新規に`ダイヤストーム`の命名バグを発見。最大の発見は
  `move_attack.py`/`move_status.py`間の能力ランク変化命名規則の系統的分裂。
- **handlers/status・field・lethal**: `_heal_at_pinch`過剰設計は現状維持。命名チェックから
  `ばかぢから`のリーサル計算バグを新規発見（本ラウンド最重要の実害バグの1つ）。
- **model/players**: 旧CRIT-1（`_stats_manager`）解消を確認できた最大の前進。ただし
  同型の新規重大指摘として`Pokemon.boosts`の非公開化・専用API不備が判明。`players/`は
  `TreeSearchPlayer`昇格・`RandomPlayer`新設ともに新規バグなし。
- **types/enums/utils/**: `string_utils.py`デッドコード（旧OVER-1）は完全解消。一方
  `enums/event.py`のドキュメントドリフト（旧CRIT-1）は悪化を確認（13箇所中12箇所誤り）。
  新規追加`types/poke_env.py`が`types/`の「Literal型定義専用」契約から逸脱している点が
  最大の新規論点。

---

## 本ラウンドで着手した修正（★印の7件）

最優先指摘のうち★印を付けた7件は実害または明確な矛盾を伴い、修正方針が一意に定まる
（一次情報・既存規約と突き合わせ済み）ため、本レビューに続けて修正作業を実施した。
修正内容・検証結果は各作業ブランチのコミット履歴を参照。以下は本ラウンドでは着手しない
（プロジェクト全体の命名標準・大規模リファクタの意思決定を要する）項目。

- `enums/event.py` の emit/handle コメント37箇所超のドキュメントドリフト是正（機械的検証
  スクリプトの導入を含めて別タスク化を推奨）
- `move_attack.py`/`move_status.py`間の能力ランク変化命名規則の統一（どちらの流儀に
  寄せるかはCLAUDE.md等での方針決定が前提）
- `core/`の`mon`/`target`引数名統一、`calc_`/`resolve_`接頭辞統一
- `RoleSpec`のコンテキスト型別分割・登録時検証の追加（`ISSUE-1`、設計変更を伴う）
- `Pokemon.boosts`の非公開化・専用API追加（`set_raw_boost`等、40箇所以上の呼び出し修正を伴う
  大規模変更）
- `Battle`Facadeの`ItemManager`向けメソッド追加（ISSUE-12）

## 関連: 機能横断レビュー（2026-07-05/07、本ラウンドでは再検証対象外）

- [tree_search.md](tree_search.md) — `Battle.copy()`/`build_observation()`等による木探索
  サポート機構のレビュー（2026-07-05）。
- [tree_search_framework.md](tree_search_framework.md) — `TreeSearchPlayer`昇格前
  （`scripts/tree_search/framework.py`時代）のレビュー（2026-07-07）。指摘内容は
  `model_players.md`で再検証済み（FW-U1/U2/U4/D1/D4は解消を確認）。

## 付記

各ファイルの「重大/中程度/過剰設計/軽微/命名」件数には、既存レビューから引き継いだ項目
（現存を再検証済み）と、今回新たに発見した項目が混在する。個々の指摘が既存/新規のどちらかは
各ファイル内の見出しに明記している。`data_moves.md`は初回レビューのため全件新規。
