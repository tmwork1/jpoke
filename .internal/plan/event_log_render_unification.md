# リファクタ計画: EventLog レンダリング形式の統一

更新日: 2026-07-11

## スコープ

- 対象: `src/jpoke/core/log_payload.py`（Payload dataclass 群）、
  `src/jpoke/core/event_logger.py`（`EventLog.render()` / `_get_base_text()`）、
  `src/jpoke/core/battle.py`（`get_log_lines()` / `print_logs()`）
- 実装状態: 未着手
- 方針: `render()` の文字列を頑張ってパースしやすくするのではなく、
  **プログラム解析の入口を構造化データ（`Payload` dataclass / `EventLog.to_dict()`）に
  一本化し、`render()` は人間向け表示専用として文体を統一する**。
  「表示規格の統一」を①構造データの統一、②解析インターフェースの明文化、
  ③人間向け文言の統一、の3層に分けて解決する。

## 前提（直前のリファクタとの関係）

`.internal/plan/archives/refactor_event_log_structure.md`（2026-07-04）で緩い辞書
Payload を LogCode カテゴリごとの dataclass に置き換え済み（直近コミット
`f7b3d62a` で `log_payload.py` に分離）。`EventLog.to_dict()`
（`event_logger.py:144-155`）は `asdict(payload)` で既に JSON 化可能な構造化データを
返しており、**分析用の土台は既にある**。今回の課題は「render() の文言がバラバラ」
であって「データが構造化されていない」ではない。

同計画は `.internal/spec/event_log.md` の新設を「必要であれば追加検討」として
未着手のまま残しており（同ファイル372行目）、また
`.internal/plan/archives/battle_log_replay.md:368-369` は
「`get_log_lines()`/`print_logs()` は人間可読用、変更不要」「`event_logger` は
『見るためのログ』」と明言している。つまり **`render()` 文字列自体をパースする
方向は既存方針と矛盾する** ため、本計画では採用しない。

## 動機（現状の課題）

### 1. `render()` が LogCode 36種を1つの巨大な `match` 文で個別実装している

`event_logger.py:171-320`。LogCode ごとに文体・語尾・省略ルールがバラバラ:

- `ABILITY_TRIGGERED`: `f"{ability}が発動した"`（`event_logger.py:212`、動詞文）
- `SWITCHED_IN`/`SWITCHED_OUT`: `f"{pokemon} 入場"`/`f"{pokemon} 退場"`
  （`event_logger.py:192,196`、体言止め・スペース区切り）
- `TEXT_LOG`: 呼び出し元が組み立てた完成文をそのまま素通し
  （`event_logger.py:199`、構造ゼロ）

同じ「〜が発動した」系でも助詞・敬体/常体・体言止めの使い分けに一貫したルールがない。

### 2. Payload間で「対象ポケモン」を示すフィールド名が統一されていない

`log_payload.py` を見ると、対象/主体を表すフィールドが LogCode カテゴリごとに
3パターンに分裂している。

- `pokemon` を持つ: `SwitchPayload.pokemon`（84-86行目）、
  `HPChangePayload.pokemon`（40行目）
- `source` を持つ（意味は「行為者」で対象ではない）: `StatChangePayload.source`
  （52行目）、`AilmentPayload.source`（61行目）、`VolatilePayload.source`（70行目）
- どちらも持たない: `AbilityPayload`、`ItemPayload`、`FieldPayload`、
  `MoveActionPayload`、`TerastalPayload`

この不統一が実害として出ているのが `battle.py:815`
（`get_log_lines()`）と `scripts/fuzz/fuzz_common.py:89`（同ロジックの重複）:

```python
pokemon = getattr(log.payload, "pokemon", "") if log.payload else ""
```

`pokemon` 属性を持つ Payload は `SwitchPayload`/`HPChangePayload` の2種だけなので、
**それ以外のLogCode（特性発動・能力変化・状態異常など大半）ではログ行頭の
ポケモン欄が常に空文字になる**。ダックタイピングで「たまたま同じ名前の属性が
あるものだけ」拾っている状態で、意図した設計ではなく統一漏れの副作用。

### 3. `STAT_CHANGED` だけ内部の英語 Literal がそのまま人間向けテキストに漏れる

`event_logger.py:258-263`:

```python
texts.append(f"{stat}{'+' if value > 0 else ''}{value}")
```

`Stat`（`types/literals.py:55`、`"atk"`/`"def"`/`"spa"`等の英語Literal）が
そのまま連結される（例: `"def-1 spd-1"`）。他の全LogCodeが完成した日本語文を
返すのに対し、ここだけ内部コードが露出しており、対象ポケモン名も含まれない。

### 4. `TEXT_LOG` が構造化を完全にバイパスする自由記述の逃げ道になっている

現在3箇所（`handlers/ability.py:741,3430`、`handlers/volatile.py:290`）。
件数は少ないが、ここに新規ケースが追加され続けると、他のLogCodeをどれだけ
統一しても「TEXT_LOGに逃げれば何でも書ける」状態がすり抜け穴として残る。

### 5. 構造化データを「プログラム解析の正式な入口」と明言したドキュメントがない

`to_dict()` は存在するが、これが分析用の公式インターフェースであり
`render()` の文字列を解析すべきではない、という方針がコード上にもdocs上にも
明文化されていない。将来的に「ログを解析したい」という要望が出るたびに
`render()` の文字列パースが再検討されるリスクがある。

## 方針

- **解析用インターフェース**: `EventLog.to_dict()` / `EventLog.payload`
  （dataclass 属性への直接アクセス）を正式な分析用APIとして
  `.internal/spec/event_log.md` に明文化する。LogCode → Payloadクラス → 各フィールドの
  意味、の対応表を作る。「render()の文字列パースは非推奨」も明記する。
- **構造データ自体の統一**: 対象ポケモンを表すフィールド名をPayload間で揃える
  （命名は実装フェーズで決定、例: 全カテゴリで対象を明示する共通の取得手段を用意）。
- **人間向け文言の統一**: `render()`のLogCodeごとの文体ルールを決めて揃える。
  データは既に構造化済みなので、大改造ではなく文言レベルの統一にとどめる。
- **TEXT_LOGの縮小**: 3箇所を構造化Payloadに置き換えられるか検討し、
  置き換えられないものは「意図的な自由記述の例外」として明記する。

## 実装ステップ

### フェーズ1: 構造データの命名統一（実施済み）

`add_event_log(source, log, payload)` の `source` にはほぼ全ての呼び出し箇所で
既に対象/主体の `Pokemon` インスタンスが渡されており（`idx` 算出に使っている
のと同じ引数）、Payloadサブクラスごとに `pokemon`/`source` を個別に持たせる
必要はないと判断した。そこで以下のように実装:

- `EventLog` に `pokemon: str | None = None` を追加し、
  `Battle.add_event_log()` が `source` が `Pokemon` インスタンスの場合に
  自動でセットする（`EventLogger.add()` 経由）。呼び出し元での明示的な
  `pokemon=mon.name` の指定は不要になった
- `SwitchPayload`（`pokemon` のみを持つクラス）は完全に不要になったため削除し、
  `SWITCHED_IN`/`SWITCHED_OUT` は `payload=None` で呼び出すだけになった
  （`switch_manager.py`）
- `HPChangePayload.pokemon` は `EventLog.pokemon` と重複していたため削除
  （`source`＝攻撃者名フィールドは引き続き `HPChangePayload` に残す）
- `battle.py` の `get_log_lines()` と `scripts/fuzz/fuzz_common.py` の
  `format_full_log()` にあった `getattr(log.payload, "pokemon", "")`
  というダックタイピングを撤廃し、`log.pokemon or ""` に置き換えた。
  これにより従来 `SwitchPayload`/`HPChangePayload` の2カテゴリでしか
  埋まらなかったログ行頭のポケモン欄が、全LogCodeで正しく埋まるようになった
  （実バトルで確認済み: `ABILITY_TRIGGERED`/`AILMENT_APPLIED`/`STAT_CHANGED`
  等でも対象ポケモン名が取得できる）
- `EventLog.to_dict()` にも `pokemon` を追加し、構造化データとして
  そのまま分析に使えるようにした
- 全テスト（4755件）・既存の `render()`/`EventLog` 等価比較ベースのテストは
  無変更で通過を確認済み

### フェーズ2: LogCode × Payload 対応表の明文化（実施済み）

当初は `.internal/spec/event_log.md` として新設する想定だったが、
`.internal/spec/README.md` を確認したところ `.internal/spec/` は
「第9世代ポケモンの挙動を実装する際に参照する調査資料（Wiki等の外部仕様）」
専用ディレクトリと明記されており（実装方針・進捗管理は含めない）、
EventLogのような内部コードのアーキテクチャ資料を置く場所として適切ではないと
判断した。コードとのドリフトを避ける観点からも、`log_payload.py` の
モジュール docstring に統合する方式に変更した。

- `log_payload.py` のモジュール docstring に、LogCode（36種、`enums/logcode.py`）
  × Payloadクラス × 主なフィールドの意味の対応表を追加
- 「プログラムでログを解析する場合は `render()` の文字列ではなく
  `EventLog.log`/`pokemon`/`payload`/`to_dict()` を使うこと」を明記
- `EventLog.render()`/`EventLog` クラスの docstring からも
  `log_payload.py` の対応表を参照するよう相互リンクを追加
- 全テスト（4769件）通過を確認済み

### フェーズ3: `render()` 文言の統一（実施済み・スコープを縮小）

`STAT_CHANGED` の内部Literal露出（`event_logger.py` の `_STAT_LABELS` 辞書で
`Stat` → 日本語ラベルに変換、`"こうげきが1段階下がった"` のような文に変更）を修正した。

一方、「LogCodeごとに動詞の活用・体言止め・語順が異なる」という当初の動機②の
残り部分（36ケース全体の文体統一）は、フェーズ2で
「`render()` は人間向け表示専用、プログラム解析は構造化データを使う」と
明文化した時点で実害（誤解析リスク）は解消済みと判断し、対応をスコープ外とした。
テストは `render()` の文字列を一切検証しておらず、統一のための書き換えは
見た目の一貫性のためだけの広範囲な変更になり、CLAUDE.mdの
「バグ修正に周辺クリーンアップを含めない」方針と逆行するため見送った。
STAT_CHANGEDのような実質的な情報欠落（内部コード露出）のみを修正対象とした。

- 全テスト（4769件）通過を確認済み
- 巨大 `match` 文自体の分割・テーブル化は行わない（可読性目的でも今回はスコープ外）

### フェーズ4: `TEXT_LOG` の廃止（実施済み）

3箇所すべてを専用LogCode/Payloadに置き換え、`TEXT_LOG`/`TextPayload` を
コードベースから完全に削除した（「意図的な自由記述の例外」として残す案は
採用せず、全廃する方針を選択）。

- `おみとおし`（`handlers/ability.py`）: 新設した `LogCode.ITEM_REVEALED` +
  `ItemRevealPayload(target, item)` に置き換え。`target`=持ち物を公開された
  相手のポケモン名、`item`=公開されたアイテム名。行動主体は `EventLog.pokemon`
- `よちむ`（`handlers/ability.py`）: 新設した `LogCode.MOVE_REVEALED` +
  `MoveRevealPayload(target, move)` に置き換え。フィールドの意味は上記と同様
- `おんねん`（`handlers/volatile.py`）: 既存の `LogCode.PP_CONSUMED` +
  `MoveActionPayload(move, value)` を再利用（「技のPPを全消費させる」という
  意味で構造的に一致するため新規Payloadを作らず流用）。`display_reason="おんねん"`
  を設定し、他のPP_CONSUMEDログと表示形式を統一（例:
  `"たいあたり PP -34 [おんねん]"`）
- `enums/logcode.py` から `TEXT_LOG` を削除し、`log_payload.py` から
  `TextPayload` を削除。`event_logger.py` の `match` 文・import、
  `log_payload.py` のモジュール docstring 対応表も同時に更新
- 全テスト（4769件）通過、実バトルで3ケースとも意図した表示になることを
  目視確認済み

### フェーズ5: テスト・検証

- LogCode全種が `_get_base_text()` の `match` 文でカバーされていること
  （既存の `case _: raise ValueError(...)` で担保済み、回帰確認のみ）
- `log_payload.py` の対応表とコードの対応が崩れていないかは、レビュー時の
  目視確認にとどめる（自動テスト化は費用対効果が低いため見送り）

## 影響範囲

- 144箇所の `add_event_log()` 呼び出し元には、フェーズ1のフィールド名変更が
  かかるもの以外、手を入れない
- 既存テストは `render()` の文字列ではなく `LogCode` enum や `EventLog`
  オブジェクトの等価比較で検証している（例: `tests/moves_status/test_move_sa.py:549`、
  `tests/test_replay.py:78,106`）ため、文言変更によるテスト破壊は基本的にない
- `tests/test_utils.py` の `print_logs()` 呼び出しはデバッグ出力目的であり
  アサーションではないため、文言変更の影響を受けない

## リスク・注意点

- フェーズ1はdataclassのフィールド構成変更のため、該当Payloadを生成している
  呼び出し元を機械的に洗い出す必要がある（grepで対象を絞り込めば影響範囲は限定的）
- フェーズ3で `render()` の文言を変えると、目視でログを確認している開発者にとって
  見た目が変わる。LogCode・構造化データの意味自体は変えないが、文言が変わりうる点は
  事前に合意する
- スコープが広いため、フェーズ単位でPRを分割することを推奨する
  （フェーズ1・2は互いに独立して着手可能）
