# イベントログ監査 — 機械的検証観点での過不足調査

日付: 2026-07-17
対象: `src/jpoke/core/event_logger.py`, `core/log_payload.py`, `enums/logcode.py`,
`core/status_manager.py`, `core/ailment_manager.py`, `core/volatile_manager.py`,
`core/field_manager.py`, `core/item_manager.py`, `core/switch_manager.py`,
`core/move_executor.py`, `handlers/*.py`, `tests/`, `players/tree_search_player.py`
観点: 実際のゲーム画面のような人間向け冗長ログではなく、**開発者・AIが機械的にログを
確認する際に不備がないか**（発行漏れ・重複・一貫性・順序保証・乱数分岐の追跡可能性）。

読み取り専用調査（Explore サブエージェント使用）。コードは変更していない。

**追記（2026-07-17, `feature/event-log-audit-fixes`）**: 指摘一覧の #1〜#4 と、順序保証の
欠如（§4-1）を修正した。#1（ランク変化ログ発行漏れ）、#2（揮発状態ブロックの二重ログ）、
#3（状態異常ブロックのサイレント化）、#4（`STAT_CHANGE_BLOCKED` のdocstring不一致）に加え、
`EventLog` に `seq`（連番）フィールドを追加し、`turn`/`idx` が同じログ同士の順序を機械的に
判別できるようにした。§4-2（乱数分岐結果の非記録）と§4-3（コートチェンジのログ省略）は
意図的な設計判断のため今回は対象外。

---

## 総括

1. ログの構造自体（`EventLog`/`Payload` 体系）は既に2回のリファクタ
   （`.internal/plan/archives/refactor_event_log_structure.md` 2026-07-04、
   `.internal/plan/event_log_render_unification.md` 2026-07-11）を経ており、機械可読性
   （`to_dict()` によるJSON化、`LogCode` ごとの専用 `dataclass`、`display_reason`/
   `internal_reason` の分離）は既に高い水準にある。
2. しかし**「発行漏れ」を検出する仕組みは失敗パス（`MOVE_FAILED` の重複防止）にしか
   存在せず、成功パスの発行漏れを防ぐ仕組みがない**（§1）。
3. **ブロック系イベント（状態異常／揮発状態の付与阻止）の記録経路が発生源
   （特性／タイプ／フィールド／揮発状態）ごとに非対称**で、片方は二重記録（§2）、
   もう片方は完全にサイレント（§3）という具体的な不整合がある。
4. **`EventLog` にはターン番号・プレイヤーインデックスはあるがフェーズ・シーケンス番号が
   なく**、順序保証はリスト格納順に依存している。テストコードも実際にそれに依存している
   （§4）。
5. 設計思想として event_logger のログは「見るためのログ」（`.internal/plan/archives/
   battle_log_replay.md` L368-369）であり、**対戦の完全な再現性はシード＋コマンド列
   （`BattleReplayData`）が担う**。AIプレイヤー（`tree_search_player.py`）も状態判断に
   ログを使わず、`Pokemon` の直接属性・`PokemonQuery`・`observation_builder` を使う
   （§5）。したがって「機械的検証に過不足がないか」を論じる際は、ログを唯一の真実源として
   扱う前提ではなく、直接状態アクセスと併用する設計であることを踏まえる必要がある。

---

## データ構造（前提）

`EventLog`（`core/event_logger.py` L26-64）:

```python
@dataclass(frozen=True)
class EventLog:
    turn: int
    idx: int
    log: LogCode
    payload: Payload | None = None
    pokemon: str | None = None
```

- `turn`/`idx`（プレイヤーインデックス）/`log`/`payload`/`pokemon` の5フィールドのみ。
  シーケンス番号・タイムスタンプ・`Battle.phase`（selection/action/switch）を示す
  フィールドは存在しない。
- `LogCode` は全36種、7カテゴリ（ルール／交代／技／HP／能力値／特性／アイテム／
  状態異常／揮発状態／場／その他）。
- `add_event_log()`（`battle.py` L1282-1299）が唯一の公開記録経路。呼び出し数は
  187箇所（`handlers/move_status.py` 77件、`move_attack.py` 31件、`ability.py` 20件、
  `volatile.py` 18件 など）。

---

## §1 成功パスでのランク変化ログ発行漏れ（確定）

`status_manager.modify_stats()` に一元化されているはずのランク変化ログが、以下の
直接代入箇所ではバイパスされ**記録されない**。

| 箇所 | 内容 |
|---|---|
| `handlers/move_status.py` L1186-1198（`じこあんじ_copy_ranks`） | 相手の全ランクをコピーするが `STAT_CHANGED` なし |
| `handlers/move_status.py` L2431-2438（`ハートスワップ_swap_ranks`） | 両者の全ランク入替えだが `STAT_CHANGED` なし |
| `handlers/move_status.py` L2543-2557（`ひっくりかえす_invert_ranks`） | 全ランク反転だが `STAT_CHANGED` なし |
| `core/switch_manager.py` L88-92（バトンタッチのランク引き継ぎ） | `SWITCHED_IN` はpayload=Noneで出るが引き継ぎ量は記録なし |

`tests/moves_status/test_move_ha.py` L1319-1330 の
`test_ひっくりかえす_こうげきプラスが反転する` は `assert defender.boosts["atk"] == -2` と
直接属性を検証しており、ログ側の検証テストは存在しない（欠落が可視化されにくい状態）。

対照として、同様に直接代入する `くろいきり_reset_all_ranks`
（`handlers/move_status.py` L831-847）、`クリアスモッグ_reset_defender_rank`
（`handlers/move_attack.py` L1039-1059）、しろいハーブ発動（`move_attack.py`
L2221-2232）、`_reset_negative_ranks`（`handlers/item.py` L65-88）は直接代入直後に
手動で `STAT_CHANGED` を記録しており正しい。**「直接代入する場合は自分でログも書く」
という規約はあるが強制されておらず、実際に複数箇所で漏れている。**

根本原因: `move_executor._execute_status_hit()`（`core/move_executor.py` L638-664）は
**失敗時**のみ「ハンドラが既にログを記録したか」を検証するフォールバック機構を持つが
（重複防止目的）、**成功時に「何らかのログが記録されたか」を検証する機構は存在しない**。
失敗パスには二重ログ防止の安全網があるのに、成功パスにはログ欠落防止の安全網がない、
という非対称な設計になっている。

---

## §2 揮発状態ブロック時の二重ログ（確定）

- `core/volatile_manager.py` L81-92（`VolatileManager.apply()`）: `ON_BEFORE_APPLY_VOLATILE`
  でハンドラが値をブロックすると、manager 側が**無条件に** `VOLATILE_IMMUNE`（理由なし）を
  記録する。
- `handlers/ability.py` L334-355（`_prevent_volatile`、どんかん／アロマベール／
  せいしんりょく等134箇所中の一部が利用）: 特性ハンドラ自身が**先に**
  `VOLATILE_PREVENTED`（理由=特性名あり）を記録し `stop_event=True` を返す。

`event_manager.emit()`（L140-161）は `stop_event=True` で即座に値を返すため、
`volatile_manager.apply()` に戻った時点で `resolved_name = None` となり、**同一の1回の
付与試行に対して `VOLATILE_PREVENTED`（理由あり）→ `VOLATILE_IMMUNE`（理由なし）の
2件が連続して記録される**。

機械的検証者が「1イベント=1ログ」を前提にログ件数をアサートすると誤判定を起こしうる。
`test_move_ha.py` L1471 のテストが `MOVE_FAILED` の二重ログ回帰を明示的に確認している
実績があるにも関わらず、この `VOLATILE_PREVENTED`/`VOLATILE_IMMUNE` の組み合わせには
同種の対策が入っていない。

---

## §3 状態異常ブロックのログ発行が経路依存でサイレント化（確定）

`core/ailment_manager.py` L114-120 は `ON_BEFORE_APPLY_AILMENT` でブロックされた場合、
**manager側のフォールバックログが一切ない**（§2の `VolatilePayload` 版と非対称）。
記録されるかどうかは完全にハンドラ実装依存になる。

- 特性由来のブロック（`_prevent_ailment`、`handlers/ability.py` L311-332）は自分で
  ログする → 正常。
- **フィールド／揮発状態由来のブロックはログを一切出さない**:
  - `handlers/field.py` L92-109（エレキフィールドのねむけ・ねむり阻止）
  - `handlers/field.py` L542-564（ミストフィールドの状態異常・こんらん阻止）
  - `data/field/side_field.py` L48-57（しんぴのまもり）
  - `handlers/volatile.py` L619-631（さわぐ状態下のねむり阻止）

  いずれも `HandlerReturn(value="", stop_event=True)` のみで `add_event_log` を
  呼んでいない。「エレキフィールド上でねむり付与が阻止された」等はログから追跡不能で、
  `target.ailment` が変化していないことを消去法で確認するしかない。

まとめ（発生源別の非対称性）:

| 経路 | 状態異常ブロック | 揮発状態ブロック |
|---|---|---|
| タイプ無効 | `AILMENT_PREVENTED`（理由="タイプ無効"） | (該当機構なし) |
| 特性ブロック | `AILMENT_PREVENTED`（理由=特性名） | `VOLATILE_PREVENTED` **+** `VOLATILE_IMMUNE` の二重（§2） |
| フィールド／揮発状態ブロック | **ログなし（サイレント）** | `VOLATILE_IMMUNE`（理由なし） |

---

## §4 順序保証・乱数分岐の追跡可能性

### 4-1 順序フィールドの欠如
`EventLog` に明示的な順序フィールド（シーケンス番号／フェーズ）がなく、同一
`turn`/`idx` 内の順序は `EventLogger.logs` のリスト格納順のみで担保される。
テスト側もこれを前提にインデックス比較している実例:
`tests/abilities/test_ability_ha.py` L741-790（`ability_idx < lost_idx` のような
リストインデックス比較）。

### 4-2 乱数分岐の結果がログに残らない
- 命中判定（`move_executor._check_hit()` L148-195）: 実際の命中率は `self.accuracy`
  に「デバッグ用」として保持されるのみでログ化されない。失敗時は `MOVE_MISSED` が残るが、
  成功時に「命中した」ことを直接示すログはない。
- 急所判定（`_check_critical()` L197-234）: `self.critical_rank` も同様にログ化されず、
  `CRITICAL_HIT` は技名のみで急所ランク・確率は含まれない。
- ダメージ乱数（`Battle.roll_damage()` L1188-1220）: 16通りのロール値のうちどれが
  選ばれたかを示すログはない。
- 追加効果発動抽選: 発動時は個別ログが残るが、「抽選に外れた」ことを示す専用ログはなく、
  "何も起きなかった" として観測される。

再現性自体はシード＋コマンド列（リプレイ機構、§5）で担保されるため実害は限定的だが、
「ログ単体でデバッグ完結」を狙う場合はこの情報不足が問題になりうる。

### 4-3 意図的なログ省略
`core/field_manager.py` L387-395（`SideFieldManager.swap_fields()`、コートチェンジ用）
はコメントで明示的に `FIELD_STARTED`/`FIELD_ENDED` を出さない設計だと述べている。
「フィールド効果のライフサイクルは `FIELD_STARTED`/`FIELD_ENDED` のペアで必ず追える」と
仮定する機械検証者にとっては、この経路だけ抜け落ちる点に注意が必要。

### 4-4 Payload構成の小さなドキュメントドリフト
`log_payload.py` のdocstring対応表（L27）は `STAT_CHANGE_BLOCKED` を
`FailureLogPayload`（`move`フィールド）としているが、唯一の呼び出し元
`status_manager.py` L187 は `payload` を渡しておらず常に `None`。ドキュメント記載と
実装が食い違っている。また、この呼び出しは「なぜブロックされたか」（既に上限±6段階／
まもる等）の情報を一切持たないため、機械検証者は原因を判別できない。

---

## §5 ログ消費側の実態（ポジティブ・ネガティブ両面）

### テスト側
`tests/test_utils.py`（`jpoke.testing` の再エクスポート）は**ログ専用のアサーション
ヘルパーを提供していない**。個々のテストが `battle.event_logger.logs` を直接フィルタ
している（§4-1参照）。

`tests/test_replay.py` L78, L106 は `EventLog` が `frozen dataclass`（値等価）である
ことを利用し、`assert replayed.event_logger.logs == battle.event_logger.logs` という
**ログ列全体の等価比較**でリプレイ再現性を検証している。ただしこれは「同じ入力から
同じログが再生成されるか」の回帰チェックであり、§1〜§3のような**ログの欠落自体は
検出できない**（欠落したまま再生しても両者は一致してしまう）。

### AIプレイヤー側
`players/tree_search_player.py` の既定 `evaluate()`（L62-79）は `event_logger` を
一切参照せず、`battle.judge_winner()` と `Pokemon.hp/max_hp` を直接参照する。コード中の
コメント（L309-313）で「ログはコストがかかるためシミュレーション中は複製しない」旨が
明記されており、`battle.copy(reseed=True, copy_logs=False)`（L315）でログを空にして
複製するパフォーマンス最適化まで行われている。**設計上、ログはAIの意思決定経路から
完全に切り離されている**（状態把握は `Pokemon` 属性・`core/query.py`・
`core/observation_builder.py` 経由）。

### 位置づけの明文化
`.internal/plan/archives/battle_log_replay.md` L368-369:
> 「`BattleReplayData` は『再生に必要な最小限の入力』、`event_logger` は
> 『見るためのログ』という役割分担になる」

一方で `log_payload.py` のモジュールdocstringは「プログラムでログを解析する場合は
`to_dict()`/`log`/`pokemon`/`payload` を使う」と機械可読性を前提に書いている。
「見るためのログ」という位置づけと「機械解析の正式入口」という位置づけが同一ドキュメント群
内で両立しており、ややニュアンスのズレがある。

---

## §6 良好な点（対照確認）

- **HP変化の網羅性は良好**: `Pokemon._modify_hp_raw()`（`model/pokemon.py` L911-929）は
  「外部コード（テスト・bot・探索コードを含む）から直接呼び出さないこと」と明記され、
  ログ・イベント発火・瀕死判定を一切行わない内部専用関数として隔離されている。実バトル中の
  `.hp` 直接書き換えは `core/lethal.py` L183 の `deepcopy(battle)`、
  `handlers/move_attack.py` L312-317 の一時退避コピーなど、実バトルを汚染しない用途に
  限定されていることを確認した。ランク変化（§1）と比べて設計が徹底されている。
- **特性発動・アイテム消費のログは単一の集約ヘルパーに一元化**されている
  （`handlers/ability.py` の `_announce_ability_triggered()` L128-140、134箇所から
  呼ばれる／`handlers/item.py` の `_announce_item_triggered()` L54-59）。単一障害点だが
  逆に漏れが起きにくい設計。
- ログの構造自体（`to_dict()`によるJSON化、`display_reason`/`internal_reason`の分離）は
  機械可読性を意識して設計されている。

---

## 指摘一覧（優先度目安）

| # | 内容 | 該当箇所 | 種別 |
|---|---|---|---|
| 1 | ランク変化の直接代入によるログ発行漏れ | `move_status.py` L1186, L2431, L2543 / `switch_manager.py` L88 | 発行漏れ（確定） |
| 2 | 揮発状態ブロックの二重ログ | `volatile_manager.py` L81-92 + `ability.py` L334-355 | 重複記録（確定） |
| 3 | 状態異常ブロック（フィールド／揮発状態由来）のサイレント化 | `handlers/field.py` L92-109, L542-564 / `side_field.py` L48-57 / `handlers/volatile.py` L619-631 | 発行漏れ（確定） |
| 4 | `STAT_CHANGE_BLOCKED` のdocstring/実装不一致 | `log_payload.py` L27 vs `status_manager.py` L187 | ドキュメントドリフト |
| 5 | 順序フィールド（シーケンス番号／フェーズ）の欠如 | `event_logger.py` `EventLog` | 構造上の制約 |
| 6 | 乱数分岐結果（命中率・急所ランク・ダメージロール・抽選外れ）がログに残らない | `move_executor.py` L148-234, `battle.py` L1188-1220 | 情報不足（意図的、実害は限定的） |
| 7 | コートチェンジの `FIELD_STARTED`/`FIELD_ENDED` 意図的省略 | `field_manager.py` L387-395 | 設計上の例外（要認知） |

本調査はコードを変更していない。#1〜#4は「機械検証がログを信頼しきると誤判定・見落としに
つながる」実害のある不整合であり、修正を検討する場合は本文書の該当節を参照のこと。
