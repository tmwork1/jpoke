# コードレビュー — types/ enums/ utils/

日付: 2026-07-05
対象:
- `src/jpoke/types/`: `__init__.py`, `ability.py`, `ailment.py`, `global_field.py`, `item.py`, `literals.py`, `move.py`, `pokemon.py`, `side_field.py`, `terrain.py`, `volatile.py`, `weather.py`
- `src/jpoke/enums/`: `__init__.py`, `command.py`, `event.py`, `interrupt.py`, `logcode.py`
- `src/jpoke/utils/`: `__init__.py`, `constants.py`, `copy_utils.py`, `lethal_dist.py`, `math.py`, `string_utils.py`

観点: 責務分離、内部実装の隠蔽、拡張性、過剰設計

---

## 総論

3ディレクトリの大枠の役割分担（`types/` = データ形状の Literal 定義、`enums/` = 状態機械・列挙、
`utils/` = ドメイン非依存の汎用処理）はおおむね守られている。`types/*.py` の大半（`ability.py` /
`ailment.py` / `global_field.py` / `item.py` / `move.py` / `pokemon.py` / `side_field.py` /
`terrain.py` / `weather.py`）は `scripts/generate_literals/` によって `data/` 側の定義から
自動生成されており、手動編集される `literals.py`・`volatile.py` と役割が明確に分かれている点は
良い設計。

一方で、実際にコードを読み込んで検証した結果、以下の問題が見つかった。

1. **`enums/event.py` のドキュメントドリフトは既存レビュー（`architecture_review.md` CRIT-2）が
   指摘した「25箇所以上」を超え、実際には少なくとも**37箇所**（`core/battle.py` 9件、
   `core/pokemon_state.py` 11件、`core/switch.py` 2件、`core/speed.py` 4件、
   `core/pokemon_query.py` 1件、`handlers/common.py` 1件、`data/field.py` 8件、加えて
   `ON_TRY_BLOW` の emit 先誤り1件）**が現存しないファイル名／誤ったファイル名を指している。
   独自に grep で emit 元を全数確認し、既存の指摘が正確であることを裏付けつつ、新規のドリフト
   （`DomainEvent` ブロックと `handlers/common.py` の誤記）も追加で発見した。
2. `RoleSpec` の `attacker:self`/`defender:self` と `source:self`/`target:self` の混在
   （既存レビュー ISSUE-6）は型レベルの問題にとどまらず、`EventContext.resolve_role` /
   `AttackContext` の `getattr(self, role, None)` 経由で**サイレントにハンドラが恒久的に
   無効化されるバグ経路**として実際にコード上に存在することを `core/context.py` /
   `core/event_manager.py` の読み込みで確認した。
3. `utils/string_utils.py` はプロジェクト全体（`src/`, `tests/`, `scripts/`）のどこからも
   import されていない完全なデッドコードであり、しかも `pyproject.toml` に一切宣言されていない
   `jaconv` / `rapidfuzz` に依存している。過剰設計観点で最も具体的な指摘。
4. 自動生成 Literal ファイル群（`ailment.py` / `global_field.py` / `side_field.py` /
   `terrain.py` / `weather.py`）はいずれも中身が1行（4〜5行のファイル）であり、
   同じ「自動生成」カテゴリでありながら5ファイルに分散している。一方 `literals.py` は
   15種の性質の異なる Literal を1ファイルに無差別に同居させており、粒度の方針が
   ファイルごとにバラバラになっている。

---

## 重大な指摘

### CRIT-1: `enums/event.py` の emit/handle コメントのドキュメントドリフトが既存指摘より広範（再検証・拡張）

**ファイル**: `src/jpoke/enums/event.py`

既存レビュー（`docs/review/code/architecture_review.md` CRIT-2）が指摘した6項目・25箇所以上の
ドリフトは、実際に `grep -n "emit(Event\."` / `emit(DomainEvent\.` で全イベントの発火元を
突き合わせた結果、**行番号を含めて完全に正しい**ことを確認した（差分なし、コードは既存レビュー時点
から変化していない）。その上で、既存レビューが対象にしていなかった `DomainEvent` ブロックと
`handlers/common.py` の誤記、および `ON_TRY_BLOW` の emit 先誤りを新たに発見した。

**新規に確認したドリフト**:

| コメント上の記載 | 実際の発火元 | 該当行 |
|---|---|---|
| `core/speed.py`（`DomainEvent` docstring および emit コメント4件） | `core/speed_calculator.py` | event.py:20,25,28,31,34 |
| `core/pokemon_query.py`（`ON_CHECK_HAZARD_IMMUNE`） | `core/query.py` | event.py:316 |
| `handlers/common.py`（`ON_MODIFY_SECONDARY_CHANCE`） | `core/battle.py:646` | event.py:210 |
| `core/move_executor.py`（`ON_TRY_BLOW`、「ふきとばし・ほえる等の強制交代を試行」） | `handlers/move_status.py:44` / `handlers/move_attack.py:1431` | event.py:66 |

`core/speed.py` は現存しないファイル名で、実体は `core/speed_calculator.py`。既存レビューが
「25箇所以上」と述べていたのは実質的な下限であり、`DomainEvent` の4件・`handlers/common.py`
・`core/pokemon_query.py` を加えると**確認できただけで37箇所**に達する。また `ON_TRY_BLOW` の
ケースは単なるファイル名のリネーム漏れではなく、「技実行の共通フローで emit される」という
誤った設計理解を招く点で他の項目より実害が大きい（実際には ふきとばし・ほえる 等、個別の技
ハンドラ側が明示的に `battle.events.emit(Event.ON_TRY_BLOW, ...)` を呼んでいる）。

さらに、`data/field.py` という記載も8箇所（event.py:107,111,157,262,270,283,313,364,385,398,419
のうち `data/field.py` 表記のもの）で使われているが、`src/jpoke/data/` に `field.py` という
単体ファイルは存在しない。実体は `data/field/`（`field.py`・`global_field.py`・
`side_field.py`・`terrain.py`・`weather.py` から成るパッケージ）であり、`data/field.py` という
表記はパッケージ全体を指しているのか特定のサブモジュールを指しているのか曖昧である。

**根本原因（既存レビューの見立てを支持）**: `core/battle.py` の巨大化を解消するための
マネージャークラス分割リファクタ（`ability_manager.py` / `item_manager.py` /
`switch_manager.py` / `status_manager.py` / `ailment_manager.py` / `volatile_manager.py` /
`query.py` / `command_manager.py` / `field_manager.py` / `speed_calculator.py` への分割）は
実施されたが、`event.py` のコメントは一切追随していない。事実、今回 grep で確認した限り
「emit: core/battle.py」と書かれた9箇所は**1つの例外もなく**実際の発火元が別ファイルであり、
`core/battle.py` から直接 emit されているのは `ON_MODIFY_SECONDARY_CHANCE`（`battle.py:646`）
だけだが、そのコメントは逆に `handlers/common.py` という架空のファイルを指している。つまり
「`core/battle.py` が emit 元」という記載は事実上すべて誤りで、唯一 `battle.py` が本当に
emit している箇所は別の誤ったファイル名で説明されている。

**内部実装の隠蔽の観点から見た本質的な問題**: この「emit/handle 地図」はモジュール docstring
（event.py:1-4, 39-52）で公式にドキュメントとして案内されているにもかかわらず、
1) 更新を強制する仕組み（lint・テスト・pre-commit）が存在せず、2) `CLAUDE.md` の
「ハンドラ追加ルール」にも `event.py` のコメント更新は含まれていない。一方、優先度（priority）の
一次情報源は `docs/spec/turn.md`（678行、実装時の参照順としてCLAUDE.mdに明記）であり、
更新を促す運用が別途存在する。`event.py` のコメントは同じ「イベントシステムの地図」を
自称しながら、更新を保証する仕組みを持たない二次情報源として放置されており、今回のような
リファクタのたびに古い実装詳細（具体的なファイル名）を抱えたまま腐敗し続ける構造になっている。

**推奨**:
- `emit:`/`handle:` コメントから具体的なファイル名を削除し、「どの層（ability/item/switch/
  field/query 等の manager、または個別 handler）が扱うか」という抽象的な役割の説明に留める。
  ファイルパスを知りたい場合は `grep -rn "Event.ON_XXX" src/jpoke/core` で正確な現在地が
  一意に取得できるため、コメントで重複管理する意味が薄い。
- どうしてもファイルパスを残したい場合は、`scripts/` に `event.py` のコメントと実際の
  emit 元を突き合わせて検証する簡易スクリプトを用意し、CI やレビュー時に不整合を検出できる
  ようにする。

---

## 中程度の指摘

### ISSUE-1: `RoleSpec` の役割混在が型エラーではなくサイレントな恒久的ハンドラ無効化として顕在化する（既存 ISSUE-6 の再検証・深掘り）

**ファイル**: `src/jpoke/types/literals.py:24-32`, `src/jpoke/core/context.py:43-59`,
`src/jpoke/core/event_manager.py:187-195`

```python
# types/literals.py:24-32
ContextRole = Literal["source", "target", "attacker", "defender"]

RoleSpec = Literal[
    "source:self", "source:foe",
    "target:self", "target:foe",
    "attacker:self",
    "defender:self",
]  # role:side 形式で、特定の側のロールを指定
```

既存レビュー ISSUE-6 が指摘した「非攻撃フェーズ用イベントには `attacker:self` を指定できない
という制約が型レベルで表現されていない」という点は現在も該当する行番号のまま正しい。
今回、実際に `RoleSpec` がどう消費されるかを追跡したところ、これは単なる型の緩さにとどまらず、
**実行時にサイレントにハンドラが無効化され続けるバグ経路**になっていることを確認した。

```python
# core/context.py:43-59 BaseContext.resolve_role
def resolve_role(self, battle: Battle, spec: RoleSpec) -> Pokemon | None:
    if spec is None:
        return None
    role, side = spec.split(":")
    mon = getattr(self, role, None)   # ← EventContext に attacker/defender は存在しない
    if mon is not None and side == "foe":
        mon = battle.foe(mon)
    return mon
```

```python
# core/event_manager.py:187-195 EventManager._check_handler_validity
def _check_handler_validity(self, rh: RegisteredHandler, ctx: BaseContext) -> bool:
    subject = self._resolve_subject(rh)
    if (
        not rh.handler.skip_subject_check
        and subject != ctx.resolve_role(self.battle, rh.handler.subject_spec)
    ):
        return False
    ...
```

`EventContext`（`source`/`target` のみを持つ）に対して誤って
`subject_spec="attacker:self"` を指定したハンドラを登録してしまった場合、
`getattr(self, "attacker", None)` は `AttributeError` ではなく黙って `None` を返す。
その結果 `subject != None` は（`subject` が実在のポケモンである限り）ほぼ常に `True` となり、
`_check_handler_validity` は `False` を返してハンドラを**恒久的にスキップし続ける**。
逆に `AttackContext`（`kw_only`・必須フィールドとして `attacker`/`defender` のみを持ち、
`source`/`target` を持たない）に対して `subject_spec="source:self"` を指定した場合も同様の
無効化が起きる。例外もログも出ないため、単体テストで発火自体を確認しない限り
「特性が発動しない」という形でしか症状が現れず、原因追跡が難しい。

**推奨**: `RoleSpec` を非攻撃系（`EventContext`）用と攻撃系（`AttackContext`）用の2つの
Literal に分割し、`Handler` 側も `subject_spec: EventRoleSpec | AttackRoleSpec` のように
コンテキストの型と対応付ける。もしくは `resolve_role` 内で `getattr` の代わりに
`hasattr` チェックを行い、対応しないロールが指定された場合は `AssertionError` 等で
即座に失敗させることで、少なくとも「登録ミスがサイレントに握りつぶされる」事態は防げる。

### ISSUE-2: `HandlerSource` の全ケースを `EventManager` の分岐が網羅していない

**ファイル**: `src/jpoke/types/literals.py:20`, `src/jpoke/core/event_manager.py:197-207`

```python
# types/literals.py:20
HandlerSource = Literal["ability", "item", "move", "ailment", "volatile", "field"]
```

```python
# core/event_manager.py:197-207
match rh.handler.source:
    case "ability":
        if not subject.ability.enabled:
            return False
    case "item":
        if not subject.item.enabled_ignoring(rh.handler.ignored_disable_reasons):
            return False
    case "ailment":
        if not subject.ailment.is_active:
            return False

return True
```

`HandlerSource` は6種類の値を許容する Literal だが、有効性チェックの `match` は
`"ability"` / `"item"` / `"ailment"` の3種類しか処理しない。`"move"` / `"volatile"` /
`"field"` を `source` に指定したハンドラは、意図的にチェック対象外なのか、単に実装漏れなのかが
コード上からは判別できない（`match` に `case _:` もコメントもない）。Literal は Enum と異なり
`match` の網羅性を静的に保証する仕組みを持たないため、`HandlerSource` に新しい値
（例えば将来 `"field"` の有効/無効判定を追加したくなった場合）を追加しても、ここを更新し
忘れてもエラーにならない。

**推奨**: 少なくとも `match` の末尾に `case "move" | "volatile" | "field": pass  # 対象外` の
ように明示コメントを残すか、`HandlerSource` を Enum 化して `assert_never` パターンで
網羅性を確保する。責務分離の観点でも、「どの `HandlerSource` が有効性ゲートの対象か」という
情報は `types/literals.py`（値の列挙）ではなく `event_manager.py`（挙動）側にしか存在せず、
2ファイルを突き合わせないと全体像が分からない構造になっている。

### ISSUE-3: 同名ファイルが3層に存在し、`event.py` の省略記法「handle: ability.py」の指す先が曖昧

**ファイル**: `src/jpoke/types/ability.py`, `src/jpoke/data/ability.py`,
`src/jpoke/handlers/ability.py`（同様に `item.py` / `move.py` / `volatile.py` も3層構造）

`CLAUDE.md` が定める「`data/ability.py` に登録 → `handlers/ability.py` に実装」という
2層構造に加えて `types/ability.py`（`AbilityName` Literal）が存在するため、`ability.py` /
`item.py` / `move.py` / `volatile.py` という同一ベース名のファイルが3ディレクトリに
重複して存在する。CRIT-1で指摘した `event.py` の `handle: ability.py`
（ディレクトリ prefix なし）という省略記法は、実務上は「`handlers/ability.py`」を指す
意図と推測できるが、字面上は `data/ability.py` とも `types/ability.py` とも区別が
つかない。責務分離自体は正しく行われているが、同名多重構造ゆえに他ドキュメントでの
省略参照が曖昧になりやすい、という副作用がある。

**推奨**: `event.py` のコメントでファイルパスに言及する際は必ず `data/` または `handlers/`
のディレクトリ prefix を付ける（CRIT-1の推奨と合わせて対応可能）。

---

## 過剰設計の観点

### OVER-1: `utils/string_utils.py` は全体から一切参照されないデッドコードで、未宣言の外部依存を持つ

**ファイル**: `src/jpoke/utils/string_utils.py`（58行）, `pyproject.toml`

```python
# utils/string_utils.py:1-3
import jaconv
import unicodedata
from rapidfuzz.distance import Levenshtein
```

`find_most_similar` / `japanese_char_ratio` / `to_upper_japanese` / `remove_dakuten` の
4関数について、`src/`・`tests/`・`scripts/` 全体を関数名・モジュール名の両方で grep したが
**呼び出し箇所は1件もなかった**（本ファイル自身の内部呼び出しを除く）。さらに
`pyproject.toml` の `dependencies` は空配列であり、本ファイルが import する `jaconv` /
`rapidfuzz` はプロジェクトの依存として一切宣言されていない（開発環境にたまたま
インストールされているだけで、クリーンな環境では `ImportError` になる）。

`git log --all` で履歴を辿ると、本ファイルは初期コミット（`cb71a667`）以来ほぼ手が
入っておらず、あいまい検索・日本語文字判定といった、恐らく初期構想段階で想定していた
「ユーザー入力からの技/特性名のあいまい一致」機能のために用意されたまま、実際の利用箇所
（CLI・パーサ等）が実装されずに取り残されたと見られる。**存在するだけで「使われている
はず」という誤解を招き、依存関係の把握を難しくする典型的な過剰設計（YAGNI違反）** である。

**推奨**: 実際に使う予定があるなら `pyproject.toml` に `jaconv`/`rapidfuzz` を追加した上で
呼び出し元を実装する。使う予定がないなら削除する（Git 履歴に残るためいつでも復元可能）。

### OVER-2: 自動生成 Literal ファイルが「1行ファイル」単位まで細分化されている

**ファイル**: `src/jpoke/types/ailment.py`（4行）, `global_field.py`（4行）,
`side_field.py`（4行）, `terrain.py`（4行）, `weather.py`（4行）

```python
# types/global_field.py（全文）
from typing import Literal


GlobalFieldName = Literal["じゅうりょく", "トリックルーム", "フェアリーロック", "マジックルーム", "ワンダールーム"]  # 自動生成: ...
```

`AilmentName` / `GlobalFieldName` / `SideFieldName` / `TerrainName` / `WeatherName` は
いずれも `import` 2行 + Literal 定義1行という、実質1行の情報量しか持たないファイルとして
個別に切り出されている。`AbilityName`（317行）や `MoveName`（740行）のように要素数が
数百に及ぶものは独立ファイルにする合理性があるが、要素数が5〜8個程度のこの5ファイルは
1つの `field_literals.py`（あるいは既存の `literals.py`）にまとめても可読性・生成スクリプトの
単純さのいずれも損なわない。現状は「`data/field/` 配下のファイル構成と1:1で対応させる」という
一貫した方針の結果と見られるが、その一貫性を保つために5個の実質空ファイルをリポジトリに
持ち続けるコストが見合っているかは疑問である。

**推奨**: 生成スクリプト（`scripts/generate_literals/generate_*_literal.py`）の出力先を
1ファイルに統合するよう変更し、`ailment.py` 等を廃止する。1:1対応を残したいのであれば、
最低限これらを `types/field_names.py` のような1ファイルにまとめ、`__init__.py` の
import 元を1箇所に減らす。

### OVER-3: `literals.py` と自動生成ファイル群とで Literal の粒度方針が対照的で一貫しない

**ファイル**: `src/jpoke/types/literals.py`（125行、15種の Literal を1ファイルに同居）

`literals.py` は `BattlePhase` / `CommandType` / `LethalSubject` / `AbilityDisabledReason` /
`ItemDisabledReason` / `HandlerSource` / `AbilityState` / `ContextRole` / `RoleSpec` /
`Side` / `Nature` / `Stat` / `Type` / `Gender` / `MoveCategory` / `MoveTarget` /
`BoostSource` / `HPChangeReason` / `StatChangeReason` / `AbilityFlag` / `MoveFlag` という、
互いに無関係な15種類以上の概念を無差別に1ファイルへ詰め込んでいる（セクション分けの
コメントすらない）。一方で OVER-2 のとおり自動生成側は5要素程度の Literal でも
ファイルを分割する。「どのくらいの粒度でファイルを割るか」という方針が手動側と自動生成側で
正反対であり、新しい Literal を追加する開発者はどちらの慣習に従うべきか判断材料がない。

**推奨**: 少なくとも `literals.py` 内をセクションコメント（`# --- コマンド関連 ---` 等）で
区切るか、`HPChangeReason`/`StatChangeReason`/`AbilityFlag`/`MoveFlag` のような「効果別の
列挙」を別ファイル（例: `types/reasons.py`, `types/flags.py`）に切り出し、OVER-2の対応と
合わせてファイル粒度の基準（「要素数」なのか「関連する `data/` ファイルとの対応」なのか）を
1つに揃える。

---

## 軽微な指摘

### MINOR-1: `utils/__init__.py` が `copy_utils` のみ re-export し、他サブモジュールと扱いが非対称（既存 MINOR-13 再検証）

**ファイル**: `src/jpoke/utils/__init__.py`（8行）

```python
from .copy_utils import fast_copy, recursive_copy
__all__ = ["fast_copy", "recursive_copy"]
```

既存レビュー MINOR-13 の指摘は現在も正しい。実際に `grep` で確認したところ、
`fast_copy` はプロジェクト全体で `from jpoke.utils import fast_copy`
（パッケージ直下からのインポート、17箇所）という一貫した形で使われている一方、
`math.py` / `string_utils.py` / `constants.py` / `lethal_dist.py` は常に
`from jpoke.utils.math import ...` のようにサブモジュールを明示してインポートされている
（`core/move_executor.py:11`, `handlers/ability.py:16` 等）。`recursive_copy` に至っては
`__all__` に載っているにもかかわらず `copy_utils.py` 内部からしか呼ばれておらず、
外部からの利用は皆無だった。

**推奨**: `fast_copy` だけを特別扱いする理由（利用頻度が高いための利便性）を
docstring に明記するか、他の主要関数（`apply_fixed_modifier`, `clamp_stats` 等）も
`__init__.py` で re-export して一貫させる。`recursive_copy` は外部 API として
公開する必要がないなら `__all__` から外し、内部専用であることを明示する
（アンダースコア接頭辞や `_recursive_copy` へのリネームも選択肢）。

### MINOR-2: `enums/logcode.py` の `TERASALLIZED` は綴りの誤り

**ファイル**: `src/jpoke/enums/logcode.py:61`

```python
TERASALLIZED = auto()  # テラスタル化
```

正しくは `TERASTALLIZED`（テラスタル = Terastal + -ize/-ized）と思われるが、
`core/event_logger.py:218` と `core/turn_controller.py:229` の両方で同じ誤字が
一貫して使われているため実害はない。今後 `LogCode` にテキストとして表示する
機能（ログの英語化、外部 API 化等）を追加する際に混乱を招く可能性がある程度の軽微な指摘。

### MINOR-3: `Command.is_type` 系メソッドの `name[:-2]` 文字列スライスが `SWITCH_N` 等の命名規則に暗黙依存

**ファイル**: `src/jpoke/enums/command.py:130-149`

```python
def is_type(self, command_type: CommandType | None) -> bool:
    match command_type:
        case "move":
            return self.name[:-2] not in {"SELECT", "SWITCH"}
        case "switch":
            return self.name[:-2] == "SWITCH"

def is_switch(self) -> bool:
    return self.name[:-2] == "SWITCH"
```

`is_type` / `is_switch` / `is_regular_move` / `is_terastal` 等はすべて
`self.name[:-2]`（末尾2文字を除去、`_N` サフィックスを想定）という文字列スライスに
依存している。しかし `Command` には `STRUGGLE` / `FORCED` という `_N` サフィックスを
持たないメンバーも存在し、これらに対して `is_type("move")` を呼ぶと
`"STRUGGLE"[:-2] = "STRUGG"` のように意味のない文字列同士の比較になる
（`{"SELECT", "SWITCH"}` に含まれないため `True` を返し、"move" 型と誤判定される）。
`command_manager.py:101` の `if not any(cmd.is_type("move") for cmd in commands)` は
呼び出し時点で `commands` に `STRUGGLE`/`FORCED` が含まれない実行順序になっており、
現状は実害が出ていないことをコードパスの確認で裏付けたが、これは「たまたま安全な
呼び出し順序になっている」だけであり、`is_type` 自体の実装が持つ前提（全メンバーが
`{PREFIX}_{0-9}` 形式である）を保証する仕組みはない。また `{"SELECT", "SWITCH"}` の
`"SELECT"` は現在の `Command` に存在しないプレフィックスであり、死んだ分岐と見られる。

**推奨**: `_N` サフィックスの有無で判定する代わりに、各メンバーが属するカテゴリを
明示的に保持する（例えば `name` のプレフィックスを走査するのではなく、
`_MOVE_LIKE = {Command.STRUGGLE, Command.FORCED, *regular_move_commands(), ...}` の
ような明示的な集合、または `IntEnum` 化してレンジで判定する等）。少なくとも
`"SELECT"` という死んだ文字列は削除する。

### MINOR-4: `utils/lethal_dist.py` の `State` はドメイン概念（`ability_enabled`/`item_enabled`）を抱えており、「純粋な分布演算のみ」という docstring の主張と若干ずれる

**ファイル**: `src/jpoke/utils/lethal_dist.py:1-4, 12-21`

モジュール docstring は「Battle・Pokemon・Move に依存しない純粋な分布演算のみを提供する」と
謳っており、実際に `Battle`/`Pokemon`/`Move` 型への依存はゼロで、`core/lethal.py` と
`handlers/lethal.py` からのみ import されている（利用箇所も確認済み）ことから、
「計算カーネルを純粋関数として切り出す」設計判断自体は妥当である。ただし `State` の
フィールド名 `ability_enabled` / `item_enabled` はポケモンバトル特有の概念語彙であり、
汎用ユーティリティというより致死率計算ドメインの中核データ構造に近い。`utils/` に
置くこと自体の是非は既存レビューでも指摘されていないが、`math.py`/`copy_utils.py` の
ような無色透明な汎用処理と、この致死率計算専用の分布演算とでは「utils」という括りの中での
抽象度が大きく異なる点は留意されたい（重大な問題ではないため MINOR 扱い）。

**推奨**: 対応不要だが、将来 `utils/` にさらにドメイン固有の計算ロジックを追加する際は、
`utils/lethal/` のようなサブパッケージに切り出すか、`core/lethal_dist.py` として
「計算補助モジュール」であることを core 側の一部として明示する方が、
「utils = ドメイン非依存」という原則をファイル配置からも読み取りやすくなる。

---

## 総評

`types/` / `enums/` / `utils/` の3ディレクトリは、個々のファイル単位で見れば概ね単一責任で
書かれており、自動生成と手動編集の分離、`data/*.py` との対応関係も明快である。今回の
レビューで最も重い指摘は CRIT-1（`enums/event.py` のドキュメントドリフト）で、既存レビューの
指摘を裏付けた上でさらに広範囲（37箇所以上）にわたることを確認した。ISSUE-1（`RoleSpec` の
型不足が実行時のサイレントなハンドラ無効化に直結する）は型設計の弱さが実際のバグ経路として
存在する点で優先度を上げて対応すべきである。

過剰設計の観点では、これまでのレビューが手薄だった分野として `utils/string_utils.py` の
完全なデッドコード化（未宣言の外部依存込み）と、自動生成 Literal ファイル群の
過度な断片化（5個の実質1行ファイル）という、性質の異なる2種類の「過剰」を具体的に
特定できた。前者は削除、後者は統合によって、いずれも構造を単純化する方向で
即座に対応可能である。総じて、個々のファイルの質は高いが、リファクタリング（マネージャー
分割）や機能構想の変化（あいまい検索機能の未着手化）に伴う「取り残し」がコメントや
モジュール単位で複数箇所に蓄積している状態であり、定期的な棚卸しが必要な段階にある。
