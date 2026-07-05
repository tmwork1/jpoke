# コードレビュー — data/

日付: 2026-07-05
対象: `src/jpoke/data/`
（`ability.py`, `ailment.py`, `item.py`, `megaevol.py`, `models.py`, `move.py`, `nature.py`,
`pokedex.py`, `signature_items.py`, `type_chart.py`, `volatile.py`,
`field/__init__.py`, `field/field.py`, `field/weather.py`, `field/terrain.py`,
`field/global_field.py`, `field/side_field.py`）
観点: 責務分離、内部実装の隠蔽、拡張性、過剰設計

## 総論

`data/` 層は全体として CLAUDE.md の「定義（data）と実装（handlers）の分離」規約に高い水準で
従っている。`ability.py`(311件)/`move.py`(734件)/`item.py`(156件)/`volatile.py`(66件)/
`ailment.py`(8件) の全エントリを AST で走査し辞書キーの重複がないことを確認したが、
これだけの件数（合計1275件）を単一ファイル・単一辞書リテラルで維持しながら重複ゼロという
のは、`scripts/sort_data/sort_*.py` による自動整列運用が実効していることの裏付けであり、
評価できる。`data/field/` 配下や `ailment.py` を含め、ロジックが `if`/`for`/計算式として
data 層に漏れ出している箇所も（後述のラムダ4件を除き）見当たらなかった。

一方で、今回の精読で新たに **CRIT-1（`MEGA_POKEMONS` の生成器バグ）** という実害のある
不具合を発見した。また、既存レビュー（`architecture_review.md`）の ISSUE-13/14・MINOR-10・
NOTE-1 はいずれも現在のコードで再現・検証できたが、ISSUE-13 は行番号がずれており、根本的な
解決策（`ctx.move.name` を使えばラムダ自体が不要）も新たに見つかった。NOTE-1 で扱われた
「`lethal_handlers` 二重管理」については、まさに本日 (`docs/plan/_done/lethal_full_hp_dependent.md`)
に実際の再登録漏れインシデントが記録されており、抽象的な懸念ではなく実例のあるコストで
あることを確認した（ただし NOTE-1 に対するユーザーコメントで「並行体系自体はこのままでよい」
との結論が既に出ているため、本レビューでは体系の是非ではなく再発防止の観点から扱う）。

過剰設計の観点では、`GameEffect` 派生6クラスに対応する `data/models.py` の6dataclass
(`AbilityData`/`ItemData`/`MoveData`/`FieldData`/`AilmentData`/`VolatileData`) は、
各クラスが保持するフィールド（`fling_power`, `critical_rank`, `is_sleep`, `max_count` 等）が
実際に異なっており、統合すると nullable フィールドだらけの共用データクラスになるため、
分割は妥当と判断した（既存レビューの疑問に対する検証結果）。むしろ data 層で目についたのは
過剰な抽象化ではなく、6ファイルに渡ってほぼ同一の `common_setup()`（名前代入ループ）が
コピペされている、という「抽象化不足」寄りの重複である。

## 重大な指摘

### CRIT-1: `data/megaevol.py:98` の `MEGA_POKEMONS` がジェネレータ式であり、初回消費後は恒久的に壊れる

**ファイル**: `src/jpoke/data/megaevol.py:98`、使用箇所 `src/jpoke/model/pokemon.py:389`

```python
# src/jpoke/data/megaevol.py:98
MEGA_POKEMONS = (v[-1] for v in MEGA_STONES.values())
```

```python
# src/jpoke/model/pokemon.py:386-389
@property
def megaevolved(self) -> bool:
    """メガシンカしているかどうかを判定する。"""
    return self.name in MEGA_POKEMONS
```

`MEGA_POKEMONS` はモジュールロード時に一度だけ生成される**ジェネレータ式**であり、
リストやタプルではない。ジェネレータはワンショットであり、`in` 演算子で走査すると
消費される。つまり:

- 最初に `some_mon.name in MEGA_POKEMONS` を評価した時点で、`some_mon.name` が見つかるまで
  （見つからなければ末尾まで）内部イテレータが進む。
- 一度最後まで進み切ると（＝メガ進化形でない名前を1回でも判定すると）、以降は
  **どんな名前を渡しても必ず `False`** になる。
- 途中で見つかって停止した場合も、次回の呼び出しは前回の停止位置から再開するため、
  「本来 True になるはずの名前」が辞書順で前方にあると誤って `False` を返す。

呼び出し元は `core/command_manager.py:192` の `_can_use_megaevol`
(`all(not mon.megaevolved for mon in selection)`) で、メガシンカ済みポケモンの有無を
毎ターンのコマンド選択肢生成のたびに判定している。テストスイート内で1回でも
「メガシンカしていないポケモン」に対して `megaevolved` が評価されると（ほぼ全てのバトルで
発生しうる）、そのプロセス内では以後 `megaevolved` が恒久的に `False` を返し続ける。
`tests/` 内に `megaevolved` を直接検証するテストが存在しないため
（`grep megaevolved tests/` はゼロ件）、この不具合は現状のテストスイートでは検出されない。

**修正案**: `tuple(...)` または `frozenset(...)` に変えるだけで解決する。

```python
MEGA_POKEMONS: tuple[PokemonName, ...] = tuple(v[-1] for v in MEGA_STONES.values())
```

なお `in` での頻繁な判定用途であれば `frozenset` の方が計算量的にも適切。

## 中程度の指摘

### ISSUE-13（既存レビューを更新・検証）: `data/move.py` に規約違反のラムダが4箇所残存（行番号を更新）

**ファイル**: `src/jpoke/data/move.py:438, 3085, 3860, 4089`
（既存レビューの記載は `438, 3066, 3841, 4070` だったが、その後の行追加により
+19行ずれている。対象自体は変わらず健在）

```python
# src/jpoke/data/move.py:436-440
handlers={
    Event.ON_MOVE_CHARGE: h.MoveHandler(
        lambda b, c, v: h.charge_into_volatile(b, c, v, "あなをほる"),
    ),
}
```

同型のラムダが「シャドーダイブ」(3085)、「そらをとぶ」(3860)、「ダイビング」(4089)にも
存在し、いずれも `handlers/move.py:155` の `charge_into_volatile(battle, ctx, value, volatile)`
に技名文字列をカリー化して渡すためだけに使われている。CLAUDE.md の
「固有効果のロジックは `handlers/*` に名前付き関数で実装し、`data/*.py` からその関数を
登録する」という規約（暗黙にラムダ禁止を意味する）に反する。

**さらに調査した結果、この4箇所は `volatile` 引数自体が不要であることが分かった。**
4箇所とも渡している揮発状態名は、登録先の技名と完全に一致している
（`あなをほる` 技 → `あなをほる` 状態、`そらをとぶ` → `そらをとぶ`、`ダイビング` →
`ダイビング`、`シャドーダイブ` → `シャドーダイブ`）。`AttackContext.move: Move`
(`core/context.py:82`) を通じて `ctx.move.name` で技名を直接取得できる
（`Move` は `add_disable_reason` を呼ばないため `name` プロパティが空文字化することもない）。
つまり `charge_into_volatile` 内部で `volatile = ctx.move.name` とすれば、カリー化のための
ラムダそのものが不要になり、4箇所とも `h.MoveHandler(h.charge_into_volatile)` という
名前付き関数の直接登録に置き換えられる。これは既存レビューが提示した「ラムダを名前付き
関数に置き換える」よりも一段シンプルな解決になる。

### ISSUE-14（既存レビューを検証・維持）: 真偽値タグの管理方式が `Ability`/`Move` と `Item`/`Ailment`/`Volatile`/`Field` で不統一

**ファイル**: `src/jpoke/data/models.py:28`(`AbilityData.flags`), `:65`(`MoveData.flags`) 対
`:35-44`(`ItemData`), `:80-85`(`AilmentData`), `:89-93`(`VolatileData`), `:72-76`(`FieldData`)

現在のコードでも構図は変わっていない。`Ability`/`Move` は `flags: set[AbilityFlag]` /
`set[MoveFlag]` ＋ `has_flag()` という共通問い合わせ方式を持つが、`Item`
(`removable`, `no_fling`)・`Ailment`(`is_sleep`, `uncurable`)・`Volatile`(`forced`)・
`Field`(`max_count`) は個別スカラー属性のみで、対応する `Flag` 型も `has_flag()` 相当も
存在しない。

ただし今回 `types/literals.py:86-125` を確認したところ、`AbilityFlag` は6種類、`MoveFlag`
は28種類と定義数に大きな差があり、`Item` 側が個別属性で足りている（現状2〜3種類）のは
単純に管理対象のタグ数が少ないためという合理性もある。とはいえ「6クラスとも `GameEffect`
を基底にした統一的効果管理」という設計思想（`model/effect.py` の `EffectData` Protocol）
からすると、`flags` を持つかどうかの方針自体は明文化されておらず、今後 `Item` に
`has_flag` 相当の判定が複数必要になった場合（例えば「投げ技無効」「回収不可」などのタグが
増えた場合）、`flags: set` に寄せるべきか個別属性を増やし続けるべきかの判断基準がない。
`data/models.py` の docstring かクラスコメントで方針（タグ数が少なければスカラー属性、
多ければ `flags: set` + `has_flag()`）を明記すべき。

### ISSUE-15（新規）: `data/move.py` の `common_setup()` の docstring が実装と一致していない

**ファイル**: `src/jpoke/data/move.py:18-29`

```python
def common_setup() -> None:
    """
    全ての技に共通ハンドラを追加する。

    この関数は、MOVESディクショナリ内の全てのMoveDataに対して、
    呼び出しタイミング: モジュール初期化時（ファイル末尾）

    Note:
        dictインスタンスはスキップされます（MoveDataオブジェクトのみ処理）
    """
    for name, data in MOVES.items():
        data.name = name
```

docstring は「全ての技に共通ハンドラを追加する」「dictインスタンスはスキップされる」と
説明しているが、実装は単に `data.name = name` を代入するだけで、ハンドラの追加も
dict/非dictの分岐も一切行っていない（他の `ability.py`/`ailment.py`/`field/field.py` の
`common_setup()` と同じ「name属性のセットのみ」の実装）。docstring が別の設計案の名残
（あるいはコピー元の `volatile.py` のdocstringを流用した際の消し忘れ）と思われ、実装を
読まずに docstring だけを信じると誤解する。`volatile.py:13-24` の docstring
（「各VOLATILEのハンドラにログ用のテキスト（名前）を設定する」）と酷似しており、
コピー元として疑わしい。実装に合わせて簡潔な docstring に修正すべき。

## 過剰設計の観点

### OVER-1（既存 NOTE-1 の検証・発展）: `lethal_handlers` の二重登録は、本日まさに実際の登録漏れインシデントを引き起こしている

**ファイル**: `src/jpoke/data/models.py`（全6dataclassの `lethal_handlers` フィールド）、
`docs/plan/_done/lethal_full_hp_dependent.md`（2026-07-05付、本日完了の計画書）

既存レビュー NOTE-1 は「実戦闘用ハンドラ（`handlers`）と確率計算用ハンドラ
（`lethal_handlers`）の二重管理」を指摘し、ユーザーコメントで
「実装を共通化するコストと複雑化するリスクを考慮して独自体系としており、このままでよい」
という結論が既に出ている。したがって本レビューでは `LethalHandler` という並行イベント
体系自体の是非は蒸し返さない。

その上で今回、この「二重管理」が抽象論ではなく**実際に事故を起こした記録**を見つけた。
`docs/plan/_done/lethal_full_hp_dependent.md`（本日付・完了扱い）には次の記述がある。

> `core/lethal.py`（`_apply_damage` / `damage_dist_full` / `_calc_damage_dist`）と
> `handlers/lethal.py`（...）、`enums/event.py` の `LethalEvent.ON_APPLY_DAMAGE`、
> `types/literals.py` の `"full_hp_damage_modifier"` フラグはすでに実装済みだったが、
> 並列レビューエージェントによる `src/jpoke/data/ability.py` / `src/jpoke/data/item.py`
> への競合編集で、最後の登録手順（下記）だけが失われていた（`test_がんじょう_*` /
> `test_きあいのタスキ_*` / `test_マルチスケイル_満タン非満タン混在時も枝ごとに正しく半減`
> が回帰していた）。

つまり「がんじょう」「きあいのタスキ」の HP満タン依存ロジックを1つ実装するのに、
`data/ability.py`/`data/item.py` 側で最低3種類の別々の登録
（① `handlers` へのイベント登録、② `flags` への `"full_hp_damage_modifier"` 追加、
③ `lethal_handlers` への `LethalHandler` 登録）が必要で、しかもこの3つは
コード上どこにも「1つの効果として一緒に追加/削除すべき」という強制力（型・lint・テスト）
が存在しない。今回は編集の競合で③が失われ、実際にリーサル計算のテストが回帰した。

体系そのものを統合しない、という方針は尊重した上で、次のような**軽量な再発防止策**を
提案する。

- `docs/progress/ability.md` / `item.md` の「リーサル実装」列だけでなく、
  `flags` に `"full_hp_damage_modifier"` を持つ特性・技・アイテムに対して
  `lethal_handlers` の対応エントリが存在することを検査する簡単なテスト
  （例: `tests/test_lethal.py` に「`flags` と `lethal_handlers` の整合性チェック」を1つ追加）
  を用意すれば、次回同種の競合編集が起きても CI/テストで即座に検出できる。
  現状はこの整合性を保証する仕組みが「人間が `docs/progress/*.md` を見比べる」ことに
  依存しており、今回のように編集競合が起きると簡単にすり抜ける。

### OVER-2: `GameEffect` 派生6dataclass（`data/models.py`）は分割が妥当であり、統合は逆に悪化を招く

既存レビューが提起した「`GameEffect` 派生6クラスの分割は本当に必要か」という問いを
`data/models.py` の6dataclass (`AbilityData`/`ItemData`/`MoveData`/`FieldData`/
`AilmentData`/`VolatileData`) について検証した。各クラス固有のフィールドは以下の通りで、
共通するのは `handlers`/`lethal_handlers`/`name` の3つのみ。

| クラス | 固有フィールド |
|---|---|
| `AbilityData` | `flags` |
| `ItemData` | `removable`, `fling_power`, `no_fling`, `power_modifier_by_type`, `damage_modifier_by_type`, `mega_evolve` |
| `MoveData` | `type`, `category`, `pp`, `power`, `accuracy`, `priority`, `critical_rank`, `target`, `multi_hit`, `flags` |
| `FieldData` | `max_count` |
| `AilmentData` | `is_sleep`, `uncurable` |
| `VolatileData` | `forced` |

もしこれらを1つの汎用 `EffectData` dataclass に統合した場合、`MoveData` 固有の
`power`/`accuracy`/`multi_hit` のような技以外では無意味なフィールドまで全クラスが
`None` デフォルトで抱えることになり、型的な安全性（「`FieldData` に `power` を
うっかり設定できてしまう」等）が失われる。したがって、この分割は過剰設計ではなく
**必要最小限の分離**と判断する。過剰設計だとすれば、統合しなかったことではなく、
共通の3フィールド (`handlers`, `lethal_handlers`, `name`) を6回コピペしていること
（MINOR-12 参照）の方である。

### OVER-3: `data/item.py` の `_add_mega_stones` はデータ層内のロジックだが「過剰」ではなく妥当なDRY化

**ファイル**: `src/jpoke/data/item.py:23-36`

```python
def _add_mega_stones(items: dict[ItemName, ItemData]):
    """メガストーンをITEMS辞書に追加する。"""
    for name, forms in MEGA_STONES.items():
        items[name] = ItemData(
            removable=False,
            fling_power=80,
            mega_evolve=forms,
            handlers={
                Event.ON_MODIFY_COMMAND_OPTIONS: h.ItemHandler(
                    h.mega_modify_command_options,
                    subject_spec="source:self"
                ),
            }
        )
```

一見 data 層に `for` ループというロジックが漏れているように見えるが、中身は
「`MEGA_STONES`（92件）から機械的に同じ形の `ItemData` を生成する」という**データ生成の
自動化**であり、固有の戦闘ロジックではない（実際の効果は `h.mega_modify_command_options`
に委譲されている）。92種類のメガストーンを手書きで列挙するより明らかに保守性が高く、
「過剰設計」ではなくむしろ適切な重複排除。責務分離の観点でも問題ない実装として、
過剰設計の懸念からは除外してよい。

## 軽微な指摘

### MINOR-10（既存レビューを検証・維持）: `data/field/` のパッケージ分割基準が他カテゴリと比べて暗黙的

**ファイル**: `src/jpoke/data/field/{__init__,field,weather,terrain,global_field,side_field}.py`

`core/` 側の `WeatherManager`/`TerrainManager`/`GlobalFieldManager`/`SideFieldManager`
という4マネージャーと1対1対応しており分割自体は妥当。件数を数え直したところ
`WEATHER`=7件、`TERRAIN`=4件、`GLOBAL_FIELD`=5件、`SIDE_FIELD`=14件で、合計30件程度と
比較的少数である一方、`ability.py`(311件)/`move.py`(734件)/`item.py`(156件) は
単一ファイルのままで、どの時点でパッケージ化すべきかの基準がコード上どこにも
明文化されていない。実際に本日の `docs/plan/_done/lethal_full_hp_dependent.md` では
`data/ability.py`/`data/item.py` への「並列レビューエージェントによる競合編集」が
発生したと記録されており、大規模単一ファイルへの同時編集がコンフリクトの温床に
なっている実例がある。五十音の行（あ〜こ、さ〜と...）や効果カテゴリでの
サブモジュール分割を検討する価値がある。

### MINOR-11（新規）: `common_setup()` が6ファイルでほぼ同一の実装を繰り返している

**ファイル**: `src/jpoke/data/ability.py:17-20`, `item.py:15-17`（`_add_mega_stones`呼び出し込み）,
`move.py:18-29`, `ailment.py:8-12`, `volatile.py:13-23`, `field/field.py:8-11`

6つのモジュールすべてで「辞書の全エントリに対して `data.name = name` (または
`FIELDS[name].name = name`) をループで代入する」という3行程度の同一処理を
`common_setup()` として個別に実装している。処理内容は完全に同一（`field/field.py` のみ
`FIELDS[name].name = name` という添字アクセスだが等価）。`data/models.py` か新規の
`data/_util.py` に `def assign_names(registry: dict[str, T]) -> None: ...` を1つ用意し、
各ファイルから呼び出す形に統一すれば、6箇所の重複と、将来ロジックを変更する際に
6箇所を同時に直す必要があるリスクを解消できる。実害は小さいが、後述の MINOR-10 で
指摘した「大規模単一ファイルの同時編集コンフリクト」問題の一因（同じパターンの
ボイラープレートを毎回目視で確認する必要がある）にもなり得る。

### MINOR-12（新規）: `EffectData` Protocol が `lethal_handlers` を宣言しておらず、各モデルクラスでの手動再アノテーションに依存している

**ファイル**: `src/jpoke/model/effect.py:11-18`（`EffectData` Protocol）,
`src/jpoke/core/lethal.py:390-417`（`.data.lethal_handlers` への直接アクセス）,
`src/jpoke/model/{ability,item,move,ailment,volatile,field}.py`（`self.data: XxxData  # type hint` の6箇所）

`GameEffect.data` は `EffectData` という Protocol 型で宣言されているが、この Protocol は
`name` と `handlers` のみを要求しており、`data/models.py` の6dataclass全てが持つ
`lethal_handlers` を含んでいない。実際に `core/lethal.py` は `mon.ability.data.lethal_handlers`
のような形で直接アクセスしており、これが型的に安全なのは `Ability`/`Item`/`Move`/
`Ailment`/`Volatile`/`Field` の各 `__init__` が `self.data: AbilityData  # type hint` の
ように**個別に型を再宣言**しているため（`model/ability.py:38` 等、6クラス全てで同型の
1行コメント付きアノテーションが繰り返されている）。`EffectData` に `lethal_handlers`
フィールドを追加すれば、この6回の再宣言のうち型安全性目的の理由が一つ減り、
Protocol が実態（全6dataclassが `lethal_handlers` を持つ）とより一致する。
（この指摘は `model/` 層に踏み込むが、`data/models.py` の全dataclassが共通して
`lethal_handlers` を持つという事実に起因するため、境界の指摘として記載する。）

## 総評

`data/` 層は「定義と実装の分離」という中心規約についてはほぼ達成されており、
1275件のエントリで辞書キー重複ゼロという実績や、`field/` パッケージのマネージャー対応
設計、`_add_mega_stones` のようなデータ生成の自動化は評価できる。今回最も重要な発見は
`data/megaevol.py:98` の `MEGA_POKEMONS` ジェネレータバグ（CRIT-1）で、テストで検出されて
いない実害のある不具合として最優先の修正を推奨する。既存レビューの ISSUE-13/14・
MINOR-10・NOTE-1 はいずれも現在のコードで再現を確認したが、ISSUE-13 は行番号更新に加えて
「`ctx.move.name` を使えばラムダ自体が不要」というより根本的な解決策を提示できた。
過剰設計の観点では、`GameEffect` 派生6dataclass の分割自体は妥当と判断し（OVER-2）、
むしろ過剰設計よりも「6ファイルへの同一ボイラープレートのコピペ」（MINOR-11）や
「Protocol が実態を完全にカバーしていない」（MINOR-12）といった**抽象化不足**寄りの
指摘が中心になった。`lethal_handlers` の二重管理（OVER-1）は体系としては既に是認済みだが、
本日実際に登録漏れインシデントが記録されており、体系を変えずに整合性チェックを
追加する軽量な再発防止策を提案する。
