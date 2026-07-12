# コードレビュー — types/ enums/ utils/

日付: 2026-07-12（初版: 2026-07-05）
対象:
- `src/jpoke/types/`: `__init__.py`, `ability.py`, `ailment.py`, `global_field.py`, `item.py`, `literals.py`, `move.py`, `poke_env.py`, `pokemon.py`, `side_field.py`, `terrain.py`, `volatile.py`, `weather.py`（前回比 +1: `poke_env.py` が新規追加）
- `src/jpoke/enums/`: `__init__.py`, `command.py`, `event.py`, `interrupt.py`, `logcode.py`
- `src/jpoke/utils/`: `__init__.py`, `constants.py`, `copy_utils.py`, `lethal_dist.py`, `math.py`（前回比 -1: `string_utils.py` が削除済み）

観点: 責務分離、内部実装の隠蔽、拡張性、過剰設計、命名の一貫性・妥当性

前回レビュー（2026-07-05）以降の差分は `git log --since=2026-07-05 -- src/jpoke/types src/jpoke/enums src/jpoke/utils`
で全コミットを洗い出し、変更箇所を重点的に再検証した。主な変更点は以下の通り。

- `utils/string_utils.py`（58行、未宣言依存を持つデッドコード）が `707ebfb2`（PyPI公開ブロッカー解消）で**完全に削除された**
- `types/poke_env.py`（107行）が `7fc56bf9`（poke-env互換実装 Phase 4/5）で新規追加された
- `types/literals.py` に `HpPolicy` が追加され、`CriticalMode` / `DamageRollMode` / `AbilityDisabledReason` の内部値が日本語→英語に変更された
- `core/context.py` の `resolve_role` に、コンテキスト型に存在しないロールを指定した場合の挙動を説明するコメントが追加された（後述 ISSUE-1）
- `enums/logcode.py` から `TEXT_LOG` が全廃された（`TERASALLIZED` の綴り誤りは残存）

---

## 総論

3ディレクトリの大枠の役割分担（`types/` = データ形状の Literal 定義、`enums/` = 状態機械・列挙、
`utils/` = ドメイン非依存の汎用処理）は今回も大筋で守られている。前回指摘した2つの重大事項は
明暗が分かれた。

1. **CRIT-1（`enums/event.py` のドキュメントドリフト）は一切改善されておらず、むしろ実態がより
   悪いことが再検証で判明した**。`emit: core/battle.py` と記載された13箇所を実際に
   `grep`で突き合わせたところ、正しいのは1箇所（`ON_CHECK_WEATHER_IMMUNE`）のみで、残り12箇所は
   全て誤り（実際の発火元は `ability_manager.py` / `item_manager.py` / `status_manager.py` /
   `field_manager.py` / `command_manager.py` に分散）。さらに `ON_REFRESH_PARADOX_BOOST` に
   至っては、コメントは「emit: core/battle.py」と主張しているにもかかわらず、
   `battle.events.emit(Event.ON_REFRESH_PARADOX_BOOST, ...)` という呼び出しがコードベース全体に
   **1件も存在しない**ことを確認した（詳細後述）。一方で今回の期間中に新設された
   `ON_BEFORE_MOVE`（くちばしキャノン再実装、`272a249d`）のコメントは
   `core/turn_controller.py` で正確に検証でき、新規追加分は正しく書けている。つまり
   「新規追加時は正確に書けるが、既存の記載を遡ってメンテする仕組みがない」という前回の
   診断がそのまま裏付けられた形になる。
2. **OVER-1（`utils/string_utils.py` のデッドコード）は完全に解消された**。`707ebfb2`
   （PyPI公開ブロッカーを解消）で削除されており、`jaconv`/`rapidfuzz` への未宣言依存も含めて
   コードベースから痕跡が消えている（`grep -rn "string_utils|jaconv|rapidfuzz"` で0件を確認）。
3. **ISSUE-1（`RoleSpec` の役割混在によるサイレントな恒久的ハンドラ無効化）は構造的には未解決**。
   `core/context.py:58-59` に「コンテキスト型に存在しないロール（例: EventContext に
   'attacker'）は None を返し、呼び出し側でハンドラをスキップさせる」という説明コメントが
   追加され、この挙動が偶発ではなく認識済みであることは明確になった。しかし
   `RoleSpec` を非攻撃系/攻撃系に分割する、または `Handler.__post_init__`
   （`core/handler.py:54-68`）でコンテキスト型との整合性を検証するといった、
   誤登録を検出する仕組みは依然として存在しない。「バグとして気づかれる」ではなく
   「意図的な仕様として文書化される」方向に倒れた点は前回との違いだが、根本原因は残っている。
4. 今回新規に発見した最大の論点は `types/poke_env.py` の位置づけである。`types/` は
   CLAUDE.md が定める「新しい `Literal` 型は `types/` に追加する」という契約のもと、
   既存12ファイル全てが Literal 型定義のみで構成されていたが、`poke_env.py` は
   変換用の辞書定数7種・関数2種のみで構成され、Literal 型を1つも定義していない。
   さらにモジュール docstring が「互換の方向は poke-env → jpoke のみ（jpoke → poke-env の
   エクスポートは対象外）」と明言しているにもかかわらず、逆方向専用の `_INV` 辞書が7つ
   実装されており、現時点で `src/`・`tests/` のどこからも参照されていない。

---

## 重大な指摘

### CRIT-1（既存・再検証・悪化を確認）: `enums/event.py` の emit/handle コメントのドキュメントドリフトが依然として全域に及ぶ

**ファイル**: `src/jpoke/enums/event.py`（450行）

前回レビューが「37箇所以上」と報告したドリフトについて、今回は `emit:`/`handle:` コメントに
現れる全ファイル名を機械的に集計し、実際の `emit(Event.XXX` / `emit(DomainEvent.XXX` 呼び出しと
突き合わせた。結果は以下の通り（該当箇所数は `grep -oE` による集計）。

| コメント上の記載 | 出現数 | 実態 |
|---|---|---|
| `emit: core/battle.py` | 13 | **12箇所が誤り**（`ON_CHECK_WEATHER_IMMUNE` の1箇所のみ正しい。他は `ability_manager.py`/`item_manager.py`/`status_manager.py`/`field_manager.py`/`command_manager.py` が実際の発火元） |
| `emit: core/pokemon_state.py` | 11 | ファイル自体が存在しない（`core/ailment_manager.py`/`status_manager.py`/`volatile_manager.py` 等への分割リファクタで消滅済み） |
| `emit: core/speed.py` | 4（+ `DomainEvent` docstring 1件） | ファイル自体が存在しない。実体は `core/speed_calculator.py`（`grep` で `ON_CALC_SPEED` 等4イベント全ての emit 元がこのファイルであることを確認済み） |
| `emit: core/switch.py` | 2 | ファイル自体が存在しない。実体は `core/switch_manager.py` |
| `emit: core/pokemon_query.py` | 1 | ファイル自体が存在しない。実体は `core/query.py` |
| `emit: handlers/common.py` | 1（`ON_MODIFY_SECONDARY_CHANCE`） | `handlers/common.py` というファイルは存在しない。実際の発火元は `core/battle.py:921` |
| `handle: data/field.py` | 7 | `src/jpoke/data/field.py` という単体ファイルは存在しない。実体は `data/field/` パッケージ（`field.py`/`global_field.py`/`side_field.py`/`terrain.py`/`weather.py`） |
| `handle: data/move.py` | 8 | `data/move.py`（54行）自体は存在するが、内容は `data/moves/move_*.py` 10ファイルを束ねる集約モジュール＋`common_setup()`のみで、個々の技のハンドラ登録は全て `data/moves/move_a.py` 等のサブファイルに実装されている。コメントが指す実体と実際の実装場所が食い違う |

**新たに確認した、単なる誤記より深刻な事例**: `ON_REFRESH_PARADOX_BOOST`（event.py:114-116）は
「emit: core/battle.py（特性有効状態変化後の再判定要求）」とコメントされているが、
`grep -rn "ON_REFRESH_PARADOX_BOOST" src/jpoke` の結果、このイベントは
`data/ability.py`（こだいかっせい・クォークチャージのハンドラ登録側）にのみ現れ、
`battle.events.emit(Event.ON_REFRESH_PARADOX_BOOST, ...)` という発火呼び出しは
**コードベース全体に1件も存在しない**。同ファイル内には `ON_BEFORE_ACTION` や `ON_PROTECT_SUCCESS`
のように「emit: 未実装」と正直に書かれているイベントが複数あり（event.py:126-128, 180-182,
252-254, 434-436）、書き方の慣習は確立されているにもかかわらず、`ON_REFRESH_PARADOX_BOOST`
だけは未実装であることを隠す形で具体的な（しかも誤った）ファイル名が書かれている。
これが実際に「こだいかっせい/クォークチャージの再判定が想定タイミングで走っていない」という
機能バグを意味するのか、それとも他の経路（例えば毎ターンの `ON_SWITCH_IN`/`ON_FIELD_CHANGE`
等が実質的に代替している）で担保されているのかは、`handlers/ability_paradox.py` の実装を
掘り下げる必要があり本レビューのスコープ外だが、**ドキュメントとして読む限りは実装されていない
機能が実装済みであるかのように記載されている**という点で、他のファイル名誤記より一段深刻である。

**新規に追加されたイベントは正確に記載されている**: 今回の期間中に新設された
`ON_BEFORE_MOVE`（`272a249d` くちばしキャノン再実装、event.py:134-136「emit:
core/turn_controller.py（行動順解決後・各技実行前...）」）は、実際に
`core/turn_controller.py:286` の `self._events.emit(Event.ON_BEFORE_MOVE, ...)` と正確に一致する
ことを確認した。これは「新規追加時に正確な記述をする規律は機能しているが、既存コメントを
リファクタのたびに追随させる仕組み（lint・テスト等）が存在しないため、時間とともに乖離が
蓄積し続ける」という前回レビューの根本原因診断を裏付ける。

**推奨**（前回から変更なし）:
- `emit:`/`handle:` コメントから具体的なファイル名を削除し、抽象的な役割の説明に留める。
- どうしても残す場合は、`event.py` のコメントと実際の emit/handle 元を突き合わせて検証する
  簡易スクリプトを用意し、CI で不整合を検出できるようにする。
- `ON_REFRESH_PARADOX_BOOST` については、コメントの正確性とは別に、こだいかっせい/
  クォークチャージの再判定が実際にどの経路で行われているかを別途確認することを推奨する。

---

## 中程度の指摘

### ISSUE-1（既存・再検証）: `RoleSpec` の役割混在は「文書化された既知の挙動」になったが、根本原因は未解決

**ファイル**: `src/jpoke/types/literals.py:33-41`, `src/jpoke/core/context.py:43-63`,
`src/jpoke/core/handler.py:54-68`

前回指摘した「`EventContext`/`AttackContext` が持たないロールを `subject_spec` に指定すると
`getattr(self, role, None)` が黙って `None` を返し、ハンドラが恒久的にスキップされ続ける」という
バグ経路について、`core/context.py` の該当箇所に説明コメントが追加された。

```python
# core/context.py:55-60
role, side = spec.split(":")
if role not in ("source", "target", "attacker", "defender"):
    raise ValueError(f"不正なロール指定: {spec}")
# コンテキスト型に存在しないロール（例: EventContext に 'attacker'）は
# None を返し、呼び出し側でハンドラをスキップさせる
mon = getattr(self, role, None)
```

`role` の値自体（"source"/"target"/"attacker"/"defender" のいずれか）を検証する `ValueError` は
追加されたが、これは「値が4種の役割名のどれかであるか」の構文チェックであり、「そのロールが
現在のコンテキスト型（`EventContext` か `AttackContext` か）に実在するか」は検証していない。
`core/handler.py:54-68` の `Handler.__post_init__` も同様に `parts[0] not in ("source", "target",
"attacker", "defender")` という構文チェックのみで、`subject_spec` が登録先イベントの
コンテキスト型と整合するかは検証しない。したがって、非攻撃系イベント（`EventContext` を渡す）に
`subject_spec="attacker:self"` を指定するミスは今も静かに握りつぶされる。

変化したのは「これが意図的な仕様として文書化された」という点のみである。当初バグとして
発見されるはずだった挙動が、今はコメントによって「正常な仕様」として説明されてしまっている
ため、今後このコードを読む開発者が「危険な挙動だ」と気づく機会がむしろ減っている可能性がある
（コメントは *なぜ* None を返すかを説明しているが、*これが登録ミスを検出不能にする* という
リスクには触れていない）。

**推奨**（前回から変更なし。優先度を維持）: `RoleSpec` を `EventRoleSpec`（"source:self" 等）と
`AttackRoleSpec`（"attacker:self" 等）に分割し、`Handler` 側もイベント登録時にコンテキスト型との
整合を検証する。最低限、`resolve_role` 内で `hasattr` チェックを行い、非対応ロールの指定を
`AssertionError` 等で即座に検出できるようにする。

### ISSUE-2（既存・再検証・変化なし）: `HandlerSource` の全ケースを `EventManager` の分岐が網羅していない

**ファイル**: `src/jpoke/types/literals.py:29`, `src/jpoke/core/event_manager.py:198-210`

前回指摘のとおり、`HandlerSource = Literal["ability", "item", "move", "ailment", "volatile",
"field"]`（6種）に対し、`_check_handler_validity` の `match rh.handler.source:` は `"ability"` /
`"item"` / `"ailment"` の3種のみを処理し、`case _:` もコメントもない。今回の差分でこの箇所に
変更はなかった。

**推奨**（前回から変更なし）: `match` の末尾に対象外であることを示すコメントを残すか、
`HandlerSource` を Enum 化して網羅性チェックを効かせる。

### ISSUE-3（既存・再検証・事例を追加）: 同名ファイルが3層に存在し、`event.py` の省略記法の指す先が曖昧

**ファイル**: `src/jpoke/types/ability.py`, `src/jpoke/data/ability.py`,
`src/jpoke/handlers/ability.py`（`item.py`/`move.py`/`volatile.py`/`ailment.py` も同様）

前回指摘した「`ability.py`/`item.py`/`move.py`/`volatile.py` が `types/`・`data/`・`handlers/`
の3ディレクトリに重複して存在し、`event.py` の `handle: ability.py`（prefixなし）が
どれを指すか字面上判別できない」という問題は変化していない。CRIT-1 の集計で確認した
とおり `handle: ability.py`（32件）・`handle: volatile.py`（17件）・`handle: item.py`（13件）・
`handle: ailment.py`（2件）は全て prefix なしの省略記法である一方、`handle: data/item.py`
（1件）・`handle: data/ability.py`（1件）・`handle: handlers/volatile.py`（1件）のように
稀に正しく prefix が付いている箇所もあり、記法自体が一貫していない。

**推奨**（前回から変更なし）: ファイルパスに言及する際は必ず `data/` または `handlers/` の
ディレクトリ prefix を付ける。

### ISSUE-4（新規）: `types/poke_env.py` が `types/` の確立された契約（Literal型定義専用）から逸脱している

**ファイル**: `src/jpoke/types/poke_env.py`（107行、全文）

`types/` は本レビュー対象13ファイル中12ファイルが `Literal` 型の定義のみで構成されており、
CLAUDE.md も「新しい `Literal` 型は `types/` に追加する」と明記している。しかし新規追加された
`poke_env.py` は `Literal` 型を1つも定義せず、`TYPE_MAP`/`STATUS_MAP`/`WEATHER_MAP` 等7種の
辞書定数と、`stats_from_poke_env`/`evs_from_poke_env` の2関数のみで構成されている。中身は
「poke-env の値表現 ⇔ jpoke の値表現」を変換するロジックであり、性質としては
`utils/lethal_dist.py`（致死率計算専用の分布演算ロジックが `utils/` に置かれている前例、
既存 MINOR-4 参照）に近い。

`from jpoke.types import poke_env` という参照経路はテスト（`tests/test_poke_env_compat.py`）
以外どこにも存在せず（`grep -rn "poke_env" src/jpoke` で `types/poke_env.py` 自身を除くと
`model/pokemon.py` のdocstring内言及のみ）、`types/__init__.py` の `__all__` にも一切
re-export されていない。つまり「types/ パッケージの一員」として扱われているのはディレクトリ
配置上のみで、実際の利用形態は独立モジュールに近い。

**推奨**: `utils/poke_env.py` へ移動するか、`docs/poke-env/` に対応する新設パッケージ
（例: `src/jpoke/interop/`。実際 `docs/plan/poke-env/poke_env_battle_converter.md:7` は
将来的に `src/jpoke/interop/` パッケージを新設する計画に言及している）に統合し、
`types/` は Literal 型定義専用という現在の契約を維持する。

### ISSUE-5（新規）: `ContextRole`/`Side` の妥当値集合が `literals.py`・`handler.py`・`context.py` の3箇所に独立して重複定義されている

**ファイル**: `src/jpoke/types/literals.py:33,44`, `src/jpoke/core/handler.py:56-59`,
`src/jpoke/core/context.py:56`

```python
# types/literals.py:33
ContextRole = Literal["source", "target", "attacker", "defender"]
# types/literals.py:44
Side = Literal["self", "foe"]
```

```python
# core/handler.py:56-59（Handler.__post_init__）
if (
    len(parts) != 2
    or parts[0] not in ("source", "target", "attacker", "defender")
    or parts[1] not in ("self", "foe")
):
```

```python
# core/context.py:56（resolve_role）
if role not in ("source", "target", "attacker", "defender"):
```

`ContextRole`/`Side` という Literal 型は定義されているにもかかわらず、実行時バリデーションでは
`typing.get_args(ContextRole)` のように型定義から動的に値集合を導出せず、同じ4値・2値の
タプルを2箇所（`handler.py`・`context.py`）に手書きで再定義している。`ContextRole` 自体は
`core/handler.py:51` の型アノテーション（`role: ContextRole = field(init=False)`）以外に
一切参照されていない。将来 `ContextRole` に新しいロールを追加する際、`literals.py` を
更新しても `handler.py`/`context.py` のタプルを更新し忘れると、`Handler.__post_init__` が
新ロールを不正な `subject_spec` として `ValueError` で拒否する（"フェイルファストではあるが
気づきにくい" 形の不整合）。

**推奨**: `handler.py`/`context.py` の両方で `typing.get_args(ContextRole)` /
`typing.get_args(Side)` を使い、`literals.py` を単一の情報源にする。

---

## 過剰設計の疑い

### OVER-1（既存・解消済み）: `utils/string_utils.py` は完全に削除された

**ファイル**: `src/jpoke/utils/string_utils.py`（削除済み）, `pyproject.toml`

前回レビューで「全体から一切参照されないデッドコードで、`pyproject.toml` に未宣言の
`jaconv`/`rapidfuzz` に依存している」と指摘した本ファイルは、`707ebfb2`
（`fix: PyPI公開ブロッカーを解消(pokedex.jsonパッケージング漏れ他)`）で削除された。
コミットメッセージにも「未宣言依存のデッドコード...を解消」と明記されている。

`grep -rn "string_utils|jaconv|rapidfuzz|find_most_similar|japanese_char_ratio|
to_upper_japanese|remove_dakuten"` を `src/`・`tests/`・`scripts/`・`pyproject.toml` 全体に
対して実行し、**残存する参照が1件もないこと**を確認した。対応完了として扱ってよい。

### OVER-2（既存・再検証・変化なし）: 自動生成 Literal ファイルが「1行ファイル」単位まで細分化されている

**ファイル**: `src/jpoke/types/ailment.py`（4行）, `global_field.py`（4行）,
`side_field.py`（4行）, `terrain.py`（4行）, `weather.py`（4行）

前回指摘の状況に変化はない。5ファイルとも実質1行（Literal定義1行のみ）で、生成元
（`data/field/` 配下の対応ファイル）と1:1対応させる方針の結果、実質空ファイルが
5個リポジトリに存在し続けている。

**推奨**（前回から変更なし）: 生成スクリプトの出力先を1ファイルに統合するか、
`types/field_names.py` のような1ファイルにまとめる。

### OVER-3（既存・再検証・対象範囲が拡大）: `literals.py` と自動生成ファイル群とで Literal の粒度方針が対照的で一貫しない

**ファイル**: `src/jpoke/types/literals.py`（136行、前回比 +11行）

前回125行だった `literals.py` は、今回の期間中に `HpPolicy`（+6行、`c9e9111b`）・
`fixed_recoil` reason（+2行、`b348caa8`）・`きょじゅうだん` 関連の追加（`ce493308`）などで
136行に増加し、無関係な概念を1ファイルへ詰め込む方針がさらに進行した。一方 OVER-2 の
自動生成側は要素数5〜8個でもファイルを分割する方針を崩していない。粒度方針の不一致という
構造は前回と変わらないが、`literals.py` 側の混在度は着実に増している。

**推奨**（前回から変更なし）: `literals.py` 内をセクションコメントで区切るか、
関連する Literal 群を別ファイルに切り出す。

### OVER-4（新規）: `types/poke_env.py` の `_INV` 系7辞書が、自身の docstring が明言する対象範囲外の方向を実装しており、現時点で使用箇所ゼロ

**ファイル**: `src/jpoke/types/poke_env.py:1-9,20,27,36,45,53,65,82`

```python
# types/poke_env.py:1-9（モジュール docstring）
"""poke-env との相互変換テーブル・変換関数。

互換の方向は poke-env → jpoke のみ（jpoke → poke-env のエクスポートは対象外）。
docs/poke-env/compat_plan.md の Phase 4 に対応する。
...
"""
```

モジュール docstring は変換方向を「poke-env → jpoke のみ」と明言しているが、実装は
`TYPE_MAP`/`STATUS_MAP`/`WEATHER_MAP`/`TERRAIN_MAP`/`GLOBAL_FIELD_MAP`/`SIDE_CONDITION_MAP`/
`NATURE_MAP` の7つの辞書それぞれに対して逆引き用の `..._INV = {v: k for k, v in ...}`
を機械的に生成しており、これは正確に docstring が「対象外」と述べている
「jpoke → poke-env」方向の実装そのものである。

`grep -n "_INV\b" tests/test_poke_env_compat.py src/jpoke/types/poke_env.py` で確認したところ、
7つの `_INV` 辞書はいずれも定義元の `poke_env.py` 自身にしか出現せず、**テストを含め
コードベースのどこからも参照されていない**。ただし前回の `string_utils.py`（OVER-1、対応する
計画すら存在しなかった）とは異なり、`docs/plan/poke-env/poke_env_battle_converter.md`
（2026-07-11付、実装状態「未着手」）が `types/poke_env.py` の既存資産として `_INV` 辞書群を
名指しし、将来の poke-env Battle → jpoke Battle 変換機構で利用する計画に言及している。
つまり完全な放置ではなく「未着手の後続機能を見越して先行実装された」コードである。

とはいえ、(1) 現時点で参照ゼロであること、(2) 同じファイルの docstring が「対象外」と
明言する方向を実装していて自己矛盾していること、の2点は開発時点の設計判断として妥当性が
低い。後続機能が実装されるまでは、docstring の主張とコードの実態が食い違ったままになる。

**推奨**: `_INV` 辞書群を今使う計画があるなら docstring の「対象外」という記述を
「Phase 4 では未使用だが `poke_env_battle_converter.md` の実装で使用予定」に修正する。
使う予定が具体化しないなら、後続機能の着手時に生成すればよいコードなので一旦削除し、
`docs/plan/poke-env/poke_env_battle_converter.md` にある通り「実装が必要になったタイミングで
追加する」方針に倒す。

---

## 命名の一貫性・妥当性（新設）

### NAME-1（新規・良好事例）: `types/` の `XName` サフィックスは10ファイル全てで完全に統一されている

**ファイル**: `AbilityName` / `AilmentName` / `GlobalFieldName` / `ItemName` / `MoveName` /
`PokemonName` / `SideFieldName` / `TerrainName` / `VolatileName` / `WeatherName`

ゲーム内の固有名詞を列挙する10個の Literal 型は、例外なく `X + Name` という命名規則で
統一されている。値も全て日本語の公式表記に揃っており、この点は前回・今回を通じて崩れが
見つからなかった。参考として明記しておく。

### NAME-2（新規）: 類似概念の Literal に対するサフィックス選択が `Mode` と `Policy` で割れている

**ファイル**: `src/jpoke/types/literals.py:7-14`

```python
CriticalMode = Literal["normal", "always"]
DamageRollMode = Literal["normal", "average", "max", "min"]

HpPolicy = Literal["keep_absolute", "keep_ratio", "reset"]
```

`CriticalMode`/`DamageRollMode`（`5202f62f` で日本語→英語化）と `HpPolicy`（`c9e9111b` で
新規追加）はいずれも「ある処理をどの方式で行うか」を表す3値程度の Literal で、性質は
ほぼ同じ（計算・更新時の挙動選択）である。しかし前者は `Mode`、後者は `Policy` と
サフィックスが異なっており、選択基準がコード上どこにも説明されていない。両コミットは
2026-07-05〜2026-07-11 の近い期間に作られており、既存の `Mode` という語彙が
使われていたにもかかわらず `HpPolicy` だけ別の語を採用した理由が読み取れない。

**推奨**: どちらかに統一する（例えば「値の選択肢が少なく計算方式を切り替えるもの」は
`Mode`、「戻し方・保持方針を選ぶもの」は `Policy` という使い分けをするなら、その基準を
`literals.py` 冒頭にコメントで明記する）。

### NAME-3（既存の深掘り）: `AbilityDisabledReason` の英日混在の分割基準がコード上どこにも明文化されていない

**ファイル**: `src/jpoke/types/literals.py:19-22`

```python
AbilityDisabledReason = Literal[
    "consumed", "かがくへんかガス", "かたやぶり", "シャドーレイ", "とくせいなし", "フォトンゲイザー", "メテオドライブ",
    "lethal_calculation",
]
```

`5202f62f`（`CriticalMode/DamageRollModeとリーサル計算用disable_reasonを英語化`）のコミット
メッセージは「ポケモン固有名詞ではなく内部的な設定値である...を英語表記に統一する。
とくせいなし等の公式用語（VolatileNameと兼用）はそのまま維持」という分割基準を説明している。
しかし、この基準は commit message にのみ存在し、`literals.py` 本体にはコメントとして
一切書き写されていない。今後 `AbilityDisabledReason` に新しい値を追加する開発者は、
git log を遡らない限り「新しい理由は英語にすべきか、日本語の公式用語を使うべきか」を
判断する材料をコード上から得られない。

**推奨**: `literals.py` の `AbilityDisabledReason` 定義の直前に、コミットメッセージの
分割基準（「特性・技・状態等の公式名と重複する値は日本語、それ以外の内部的な設定値は
英語」）をコメントとして転記する。

### NAME-4（新規）: `Gender`/`MoveCategory` は公式表示用語であるにもかかわらず英語表記で、他の大多数の Literal の慣習から外れている

**ファイル**: `src/jpoke/types/literals.py:64,66`

```python
Gender = Literal["", "male", "female"]
MoveCategory = Literal["physical", "special", "status"]
```

`types/` 全体を通じて、ゲーム内で表示・言及される公式概念（`Type`・`Nature`・`AilmentName`・
`VolatileName`・`WeatherName` 等）は日本語表記が徹底されている一方、`Gender`
（せいべつ: おす/めす）と `MoveCategory`（物理/特殊/変化）は、これらと同格の
「ゲームが公式に表示する分類」でありながら英語で表現されている。`AbilityDisabledReason`
（NAME-3）のように「公式名は日本語、内部設定は英語」という不文律があるとすれば、
性別・技分類は本来「公式名」側に分類されるべき概念であり、この2つだけが慣習の
例外になっている。実害は現状ないが、新しい Literal を追加する際にどちらの言語を
選ぶべきかの判断基準として機能していない一例。

**推奨**: 対応不要（実害なし）。ただし `AbilityDisabledReason` にコメントで基準を
明文化する際（NAME-3）、この2つが例外である理由（英語圏由来の技術用語として定着している、
等）も合わせて記載すると一貫性の議論が今後しやすくなる。

### NAME-5（新規）: `enums/` のメンバー名は4 Enum 全てで英語 SCREAMING_SNAKE_CASE に統一されている（良好事例、ただし既存タイポ1件を除く）

**ファイル**: `src/jpoke/enums/command.py`, `event.py`, `interrupt.py`, `logcode.py`

`Command`（`SWITCH_0`等）・`Event`/`DomainEvent`/`LethalEvent`（`ON_`接頭辞＋英語）・
`Interrupt`（`EJECTPACK_ON_AFTER_SWITCH`等）・`LogCode`（`SWITCHED_IN`等）の4種は、
メンバー名は例外なく英語の `SCREAMING_SNAKE_CASE` で統一されており、日本語の意味説明は
全て末尾のインラインコメントに寄せる方針が徹底されている。`enums/logcode.py` は今回の
期間中に `TEXT_LOG`（自由記述の抜け道だった特殊メンバー）が全廃され（`63eb8a81`）、
残る全メンバーがこの規則に沿う形に整理された点は前回よりも改善している。

唯一の例外は既存指摘の `LogCode.TERASALLIZED`（`logcode.py:63`、正しくは
`TERASTALLIZED`）で、`core/event_logger.py`/`core/turn_controller.py` 双方で同じ綴りが
一貫使用されているため実害はないが、依然として残存している（MINOR-2として後述）。

### NAME-6（新規）: `types/poke_env.py` の定数命名は poke-env 側の識別子と jpoke 側の識別子が同じ変数内に同居し、キーの言語規則がモジュール docstring 頼みになっている

**ファイル**: `src/jpoke/types/poke_env.py:11-19`

```python
TYPE_MAP: dict[str, str] = {
    "Normal":   "ノーマル", "Fire":    "ほのお", "Water":   "みず",
    ...
}
```

`TYPE_MAP` 等の辞書はキーが poke-env 側（英語 PascalCase または lower_snake_case）、
値が jpoke 側（日本語）という変換テーブルである設計自体は妥当だが、キーの大文字小文字規則が
辞書ごとに異なる（`TYPE_MAP`: `"Normal"` は PascalCase、`STATUS_MAP`: `"brn"` は
lowercase、`NATURE_MAP`: `"Lonely"` は PascalCase）。これはモジュール docstring
（`poke_env.py:6-8`）が「各マップのキーは poke-env Enum の `name.lower()` に統一する」と
書いているにもかかわらず、`TYPE_MAP`/`NATURE_MAP` のキーは実際には lower ではなく
PascalCase のままである点で、**docstring とコードの実態がこのファイル自身の中で食い違って
いる**（poke-env の `Type.NORMAL`/`Nature.LONELY` の `.name.lower()` は本来
`"normal"`/`"lonely"` になるはずで、`"Normal"`/`"Lonely"` にはならない）。

**推奨**: `TYPE_MAP`/`NATURE_MAP` のキーを docstring の規則（`name.lower()`）に合わせて
小文字化するか、docstring 側に「`Type`/`Nature` は poke-env 側に `.value`（表示名）が
別途あるため例外的に元の表記を保持する」旨の注記を追加する。テスト
（`tests/test_poke_env_compat.py`）がどちらの表記を前提にしているかも合わせて確認されたい。

---

## 軽微な指摘

### MINOR-1（既存・再検証・対象ファイル数が変化）: `utils/__init__.py` が `copy_utils` のみ re-export し、他サブモジュールと扱いが非対称

**ファイル**: `src/jpoke/utils/__init__.py`（8行）

```python
from .copy_utils import fast_copy, recursive_copy
__all__ = ["fast_copy", "recursive_copy"]
```

前回指摘の状況は変わらないが、`string_utils.py` の削除（OVER-1解消）により、
re-export されていないサブモジュールは `math.py`/`constants.py`/`lethal_dist.py` の
3ファイルに減った。`recursive_copy` が `__all__` に載りながら外部からの利用が
皆無である点も含め、指摘内容自体に変化はない。

**推奨**（前回から変更なし）: `fast_copy` だけを特別扱いする理由を明記するか、
主要関数を一貫して re-export する。

### MINOR-2（既存・再検証・変化なし）: `enums/logcode.py` の `TERASALLIZED` は綴りの誤り

**ファイル**: `src/jpoke/enums/logcode.py:63`

```python
TERASALLIZED = auto()  # テラスタル化
```

前回指摘のとおり `TERASTALLIZED` の誤字と思われる。`TEXT_LOG` 全廃（`63eb8a81`）の
リファクタでも修正されておらず、`core/event_logger.py`/`core/turn_controller.py`
双方で同じ誤字が一貫使用されているため実害はない。

### MINOR-3（既存・再検証・変化なし）: `Command.is_type` 系メソッドの `name[:-2]` 文字列スライスが命名規則に暗黙依存

**ファイル**: `src/jpoke/enums/command.py:130-149`

前回指摘のコード・状況に変化はない。`{"SELECT", "SWITCH"}` の `"SELECT"` は現在の
`Command` に存在しないプレフィックスで、死んだ分岐のままである。

### MINOR-4（既存・再検証・変化なし）: `utils/lethal_dist.py` の `State` はドメイン概念を抱えており「純粋な分布演算のみ」という docstring の主張と若干ずれる

**ファイル**: `src/jpoke/utils/lethal_dist.py:1-4,12-21`

前回指摘の状況に変化はない。`ability_enabled`/`item_enabled` はポケモンバトル特有の
概念語彙であり、`math.py`/`copy_utils.py` の無色透明な汎用処理とは抽象度が異なる。

### MINOR-5（新規）: `types/item.py` のメガストーン70件以上が区切りコメントなしで通常アイテムの一覧に直結している

**ファイル**: `src/jpoke/types/item.py:177-270`

```python
    "ロックメモリ",
    "フシギバナイト",
    "リザードナイトX",
    ...
```

`item.py`（270行）は通常アイテム約180件のあとに、区切りコメントなしでメガストーン
約90件がそのまま続く。他の自動生成ファイル（`ailment.py`等）は要素数が少なく問題に
ならないが、`item.py` は最大級の自動生成ファイルであるため、「通常アイテム」と
「メガストーン」という性質の異なる2グループが1つの Literal 内で無言語で連結されている
状態は、目視での該当箇所特定を難しくしている。生成元スクリプト
（`scripts/generate_literals/generate_item_literal.py`）側でカテゴリ境界に
コメントを挿入する余地がある。

**推奨**: 対応不要な軽微事項。生成スクリプトの改修コストと見合うかは要検討。

---

## 総評

`types/`/`enums/`/`utils/` の3ディレクトリは、前回レビュー以降の7日間で活発な変更
（poke-env互換実装、TEXT_LOG全廃、英語化リファクタ等）を経ており、個々の変更自体は
規律を保って実装されている（新規追加イベントのコメントが正確、デッドコード削除等）。
一方で、今回のレビューが最も強く示したのは「新規追加時の規律の高さ」と
「既存資産のメンテナンス不履行」の落差である。

- CRIT-1（`event.py` ドキュメントドリフト）は**改善ゼロ、悪化を確認**。「core/battle.py」
  という記載13箇所のうち12箇所が誤りという、前回よりもさらに定量的に深刻な実態が
  判明した。`ON_REFRESH_PARADOX_BOOST` に至っては emit 呼び出し自体がコード上に
  存在しない可能性があり、ドキュメントの信頼性だけでなく機能面の疑義にも発展しうる。
- OVER-1（`string_utils.py` デッドコード）は**完全に解消**。PyPI公開対応のついでとはいえ、
  未宣言依存を含む問題のあるコードが実際に削除されたことは明確な前進。
- ISSUE-1（`RoleSpec` サイレント無効化バグ）は**「バグ」から「文書化された仕様」へと
  性質が変わったが未解決**。型レベルの安全網（`RoleSpec` 分割、登録時検証）は
  引き続き存在しない。
- 新設した「命名の一貫性・妥当性」の観点では、既存12ファイルが確立していた
  「`XName` サフィックス統一」「公式用語は日本語・内部設定は英語」という慣習に対し、
  新規追加された `types/poke_env.py`（ISSUE-4/OVER-4/NAME-6）が最も逸脱の大きい
  ファイルであることが分かった。Literal型を1つも持たないファイルが `types/`
  に配置され、docstring が主張する変換方向と実装が食い違い、docstring 自身が
  述べるキー正規化規則もコード上守られていない、という3重の不整合を抱えている。
  poke-env 互換実装は現在も `docs/plan/poke-env/` で後続フェーズが計画中であり、
  今のうちに配置・命名規則を是正しておくことが望ましい。
