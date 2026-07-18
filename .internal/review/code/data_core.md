# コードレビュー — data/（コア定義）

日付: 2026-07-12
対象: `src/jpoke/data/` のうち `data/moves/` を除くコア定義ファイル
（`ability.py`(3326行/311件), `item.py`(2072行/172件), `volatile.py`(989行/72件),
`type_chart.py`(443行), `megaevol.py`(98行), `ailment.py`(109行/7件),
`models.py`(93行), `move.py`(54行, `MOVES` 統合レイヤーのみ), `signature_items.py`(41行),
`nature.py`(29行), `pokedex.py`(21行), `__init__.py`,
`field/{__init__,field,global_field,side_field,terrain,weather}.py`(計約517行)）
合計約9500行を全文精読。
観点: (1) 一般的な品質観点（責務分離・重複・拡張性・過剰設計・実バグ）、
(2) 変数・関数・辞書キー・定数名の一貫性と妥当性（新規観点）。

前回レビュー（2026-07-05、`.internal/review/code/data.md`）以降の `src/jpoke/data` への変更を
`git log --since=2026-07-05` で確認したところ、対象ファイル群への直接のコミットは
`megaevol.py`/`item.py`/`ability.py`/`volatile.py` を含めて0件だった
（`git log --since=2026-07-05 -- src/jpoke/data` はヒットしたが、いずれも `data/moves/` 配下の
個別技レビューコミットのみ）。つまり今回のレビュー対象ファイルは前回レビュー時点から
**変更されていない**。

## 総論

前回レビュー（`data.md`）が指摘した「定義と実装の分離」規約自体は今回も高水準で維持されている。
`ability.py`/`item.py`/`volatile.py` を通読した限り、data 層に `if`/`for`/計算式のようなロジックが
漏れ出している箇所は `_add_mega_stones`（データ生成の自動化として妥当、`data.md` OVER-3で既に
検証済み）以外に見当たらない。

一方で最重要の発見は、前回 CRIT-1 として報告された **`megaevol.py:98` の `MEGA_POKEMONS`
ジェネレータバグが1週間経った現在も一切修正されていない**ことである（後述）。

今回の主眼である「命名の一貫性・妥当性」を全件精読で確認した結果、`data/` 層は辞書キー
（技名・特性名・アイテム名の日本語文字列）自体の一貫性は非常に高い一方、**登録コード側の
書き方（引数の渡し方・共有ハンドラの命名・型注釈）に複数の異なる流儀が同一ファイル内で
並立している**ことが分かった。特に `ability.py` 単体で `subject_spec` をキーワード引数ではなく
位置引数で渡している箇所が41件あり（同ファイル内の残り330件はキーワード引数）、
`item.py`/`volatile.py`/`field/*.py` ではこの逸脱が1件もないことと対照的だった。
これらはいずれも `Handler` 派生クラスの `__init__` で `subject_spec` が第2位置引数として
固定されているため実行時には正しく動作する（**実害のあるバグではない**）が、大規模ファイルを
`grep`/目視でレビューする際の一貫性を損なっている。

## 重大な指摘

### CRIT-1（既存・未修正）: `data/megaevol.py:98` の `MEGA_POKEMONS` ジェネレータバグが依然として存在する

**ファイル**: `src/jpoke/data/megaevol.py:98`、使用箇所 `src/jpoke/model/pokemon.py:389`

```python
# src/jpoke/data/megaevol.py:98（現在も変更なし）
MEGA_POKEMONS = (v[-1] for v in MEGA_STONES.values())
```

前回レビュー（2026-07-05、`data.md` CRIT-1）で報告した「`MEGA_POKEMONS` がジェネレータ式であり、
`Pokemon.megaevolved` プロパティ（`in` 演算子でこれを走査する）が初回消費後は恒久的に
壊れる」という指摘について、`git log --since=2026-07-05 -- src/jpoke/data/megaevol.py` は
**0件**であり、ファイル内容も前回レビュー時点から一字一句変わっていないことを確認した。
つまり1週間分の実装作業（`git log --since=2026-07-05 -- src/jpoke/data` には50件以上のコミットが
あるが、いずれも `data/moves/` 配下の個別技レビューのみ）を経ても、この1行の修正は
着手されていない。

再掲: `some_mon.name in MEGA_POKEMONS` が一度でも評価されると、内部イテレータが末尾まで
進んだ場合（＝非メガシンカ形の名前を判定した場合）以降、**同一プロセス内では常に `False`**
を返し続ける。`core/command_manager.py:192` の `_can_use_megaevol` が毎ターンのコマンド選択肢
生成のたびにこれを評価しているため、通常のバトルで容易に発生しうる。`tests/` に
`megaevolved` を直接検証するテストが存在しないため、現状のテストスイートでは検出されない。

**修正案は変わらず**: `tuple(...)`（あるいは頻繁な `in` 判定用途なら `frozenset(...)`）に
変えるだけの1行修正で解決する。

```python
MEGA_POKEMONS: frozenset[PokemonName] = frozenset(v[-1] for v in MEGA_STONES.values())
```

## 中程度の指摘

### ISSUE-1（新規）: `ability.py` の41箇所で `subject_spec` がキーワード引数ではなく位置引数で渡されている

**ファイル**: `src/jpoke/data/ability.py`（41箇所。例: 311-313行目`エレキメイカー`, 383-397行目
`おわりのだいち`, 864-866行目`グラスメイカー`, 1174-1176行目`じゅうなん`,
1255-1261行目`スイートベール`, 1309-1315行目`すなおこし`, 1441-1443行目`せいしんりょく`,
1791-1805行目`デルタストリーム`, 1964-1966行目`どんかん`, 2022-2024行目`ねつこうかん`,
2112-2126行目`はじまりのうみ`, 2154-2160行目`ハドロンエンジン`, 2310-2312行目`パステルベール`,
2334-2340行目`ひでり`, 2354-2360行目`ひひいろのこどう`, 2583-2589行目`ふみん`,
2828-2830行目`マイペース`, 2843-2845行目`マグマのよろい`, 2925-2927行目`ミストメイカー`,
2945-2947行目`めんえき`, 3040-3042行目`パステルベール`系, 3106-3112行目`やるき`,
3145-3151行目`ゆきふらし` 等）

```python
# ability.py:311-315（キーワードなし）
Event.ON_SWITCH_IN: h.AbilityHandler(
    h.エレキメイカー_activate_terrain,
    "source:self",
)
```

```python
# ability.py:32-35（同ファイル内の大多数はこちら。キーワードあり）
Event.ON_SWITCH_IN: h.AbilityHandler(
    h.ARシステム_apply_type,
    subject_spec="source:self",
),
```

`ability.py` 全体で `subject_spec=` というキーワード引数の書き方は371件中330件（89%）で
採用されているが、残り41件（11%）は同じ値を裸の文字列リテラルとして位置引数で渡している。
`handlers/ability.py:78-83`（`AbilityHandler.__init__`）、`handlers/item.py:32-38`、
`handlers/field.py:13-17`、`handlers/ailment.py:12-16`、`handlers/volatile.py:27-33` を
確認したところ、いずれも `subject_spec` は `func` に続く第2位置引数として固定されているため、
**この41件は実行時には正しく動作しており、機能バグではない**。ただし
`item.py`/`volatile.py`/`field/{weather,terrain,global_field,side_field}.py` を同じ正規表現
（`^\s*"(source|target|attacker|defender):(self|foe)",\s*$` という裸文字列行）で走査すると
**1件もヒットしない**ため、この逸脱は `ability.py` に特有かつ局所的ではなく約40箇所に
散在している。CLAUDE.md は「`subject_spec` は必須」と明記しているが、キーワード引数で
書くことまでは明文化されていない。とはいえ他の3ファイルで100%守られている書き方が
`ability.py` だけ11%崩れているのは、`ARシステム`（先頭付近）を含む多数のエントリと比較して
読み手に「このエントリは何か違うのでは」という誤った疑念を抱かせるコストがある。
`subject_spec=` を明示するよう統一することを推奨する（機械的な一括置換で対応可能）。

### ISSUE-2（新規）: `LethalHandler` の `func` 引数がキーワード有無で混在している

**ファイル**: `src/jpoke/data/ability.py:378, 587, 637`, `src/jpoke/data/item.py:447`

```python
# ability.py:378（位置引数）
LethalEvent.ON_BEFORE_HIT: LethalHandler(l.おやこあい_boost_damage, subject="attacker")
# ability.py:587（位置引数）
LethalEvent.ON_TURN_END: LethalHandler(l.かんそうはだ_weather_hp, subject="defender")
# ability.py:636-639（位置引数、複数行）
LethalEvent.ON_APPLY_DAMAGE: LethalHandler(
    l.がんじょう_survive_lethal,
    subject="defender",
)
```

```python
# ability.py:75-78（同ファイルの大多数はこちら）
LethalEvent.ON_TURN_END: LethalHandler(
    func=l.アイスボディ_heal,
    subject="defender",
)
```

`ability.py` は `LethalHandler(func=l.xxx, ...)` を6件、`LethalHandler(l.xxx, ...)`
（`func=` キーワードなし）を3件持ち、`lethal_handlers` を持つ9エントリ中3件（33%）が
少数派の書き方になっている。`item.py` は同様のパターンが30件中1件
（`きあいのタスキ`、447行目 `LethalHandler(l.きあいのタスキ_survive_ohko, subject="defender")`）
のみで、比率としては `ability.py` の方が乱れが大きい。`LethalHandler` のフィールド定義
（`core/lethal.py`）でも `func` は第1位置引数のはずであり機能上の実害はないが、
ISSUE-1 と合わせて「data 層のハンドラ登録コードにおけるキーワード引数の使用方針」が
ファイルごとに（また同一ファイル内でも）徹底されていないことを示す実例である。

### ISSUE-3（新規）: `VOLATILES` 辞書の五十音順がファイル末尾で崩れており、モジュール docstring の主張と矛盾している

**ファイル**: `src/jpoke/data/volatile.py:1-5`（docstring）, `818-985`（該当ブロック）

`volatile.py` のモジュール docstring は次のように明記している。

```python
"""揮発状態データ定義モジュール。

Note:
    このモジュール内の揮発状態定義はVOLATILES辞書内で五十音順に配置されています。
"""
```

実際には「アクアリング」〜「ロックオン」までの59件は五十音順（濁点・半濁点・拗音を
除けばおおむね正確）に並んでいるが、`ロックオン`（ら行）の直後に次の13件が続けて
追加されており、五十音順から明確に外れている。

```
ロックオン → まもる → かえんのまもり → キングシールド → スレッドトラップ →
トーチカ → ニードルガード → ファストガード → ハロウィン → はねやすめ →
まほうのこな → みずびたし → もりののろい
```

`まもる`(ま行)の後に`かえんのまもり`(か行)が続く時点で明らかに逆行しており、この13件は
「まもる系（`ON_TRY_MOVE_1` で防御する変化技グループ）」と「はねやすめ/まほうのこな等
（`ON_VOLATILE_START`/`ON_VOLATILE_END` でタイプを変更するグループ）」を
機能カテゴリ単位でまとめて末尾に追記した結果とみられる。`ability.py`/`item.py`/`move.py`
には `scripts/sort_data/sort_abilities.py`/`sort_items.py`/`sort_moves.py` という自動整列
スクリプトが存在し（CLAUDE.mdの「ハンドラの追加ルール」参照）、実際に3ファイルとも
辞書順の乱れは見つからなかった。一方 `volatile.py` にはそれに相当する
`sort_volatiles.py` が存在せず（`scripts/sort_data/` には3ファイルのみ）、この乖離が
機械的に検出・是正される仕組みがないまま放置されている。docstring の主張を実態に合わせて
修正するか、`sort_volatiles.py` を追加して自動整列の対象に加えることを推奨する。

## 過剰設計の疑い

前回レビュー（`data.md` OVER-1〜3）が検証した「`GameEffect` 派生6dataclassの分割は妥当」
「`_add_mega_stones` は妥当なDRY化」「`lethal_handlers` 二重管理は体系として是認済み」は、
対象ファイルが前回から無変更であるため今回も同一の結論が成立する。今回の全文精読で新たに
過剰設計と呼べる箇所は見つからなかった。強いて言えば、`common_setup()`
（`ability.py:17-20`, `item.py:15-17`, `move.py:25-36`, `ailment.py:8-12`, `volatile.py:13-23`,
`field/field.py:8-11` の6ファイル）が「辞書の全エントリに `data.name = name` を代入する」
という同一の3行処理を個別に実装している状態（前回 MINOR-11）も変化していない。

## 軽微な指摘

### MINOR-1（新規）: `type_chart.py` の攻撃タイプ `""` の行だけ `"ステラ"` 列が欠落している

**ファイル**: `src/jpoke/data/type_chart.py:2-22`（`""` の行）対 `23-44`（`"ノーマル"` の行）

`TYPE_MODIFIER` は20種類の攻撃タイプ（`""` を含む）それぞれについて防御タイプ19〜20種の
倍率を持つ辞書だが、`""` の行（2-22行目）だけ末尾に `"ステラ": 1.0` が無く、他の19行
（`"ノーマル"` 以降）は全て `"ステラ"` を持つ。`core/damage.py:235,250`
（`calc_def_type_modifier`）は `TYPE_MODIFIER.get(move_type, {})` と
`type_chart.get(def_type, 1.0)` のように `.get()` にデフォルト値を与えて呼び出しているため
**実行時に例外は発生しない**（実害のあるバグではない）。ただし20行×20列であるべき表の
1マスだけが非対称に欠けており、将来 `TYPE_MODIFIER` を辞書内包表記などで機械的に
生成し直す際の混乱要因になりうる。

### MINOR-2（新規）: 「効果なし」の表現方法が `handlers={}` の明示と省略の2流儀で混在している

**ファイル**: `src/jpoke/data/item.py:1257-1260`（`でかいきんのたま`）対
`45-47`（`アイスメモリ`）等17件のメモリ系アイテム

```python
"でかいきんのたま": ItemData(
    fling_power=130,
    handlers={}  # 効果なし
),
```

```python
"アイスメモリ": ItemData(
    fling_power=50,
),
```

どちらも `ItemData.handlers` は `field(default_factory=dict)` により実質的に同じ空辞書になるが、
前者は意図（「効果は実装漏れではなく仕様として存在しない」）をコメント付きで明示し、
後者（メモリ系17件、シルバリー専用アイテムで単体では無効果）は `handlers` 自体を省略する。
どちらも妥当な書き方だが、同じ「効果を持たないアイテム」という状態を表す2つの流儀が
使い分けの基準なく混在しており、なぜ `でかいきんのたま` だけ明示的なのかがコード上からは
読み取れない。

### MINOR-3（新規）: `data/models.py` の `VolatileData` だけフィールド定義順が他5dataclassと異なる

**ファイル**: `src/jpoke/data/models.py:26-93`

`AbilityData`/`ItemData`/`MoveData`/`FieldData`/`AilmentData` はいずれも
「固有フィールド → `handlers` → `lethal_handlers` → `name`」の順で定義されているが、
`VolatileData` のみ `handlers` → `forced`（固有フィールド） → `lethal_handlers` → `name`
の順で、固有フィールドである `forced` が `handlers` の後ろに置かれている。

```python
@dataclass
class VolatileData:
    handlers: dict[Event | DomainEvent, Handler | list[Handler]] = field(default_factory=dict)
    forced: bool = False
    lethal_handlers: dict[LethalEvent, LethalHandler] = field(default_factory=dict)
    name: str = ""
```

全て `dataclass` でキーワード引数経由の呼び出しが前提のため実害はないが、6dataclass中
5つが従う並び順の規則から1つだけ外れている。

### MINOR-4（新規）: `ability.py` に `flags=set()` を明示する2エントリがある

**ファイル**: `src/jpoke/data/ability.py:522-523`（`かちき`）, `650-651`（`ききかいひ`）

```python
"かちき": AbilityData(
    flags=set(),
    handlers={...}
),
```

`AbilityData.flags` は `field(default_factory=set)` であるため、`flags=set()` は
デフォルト値を明示的に再代入しているだけで意味を持たない。同種の「`flags` を持たない特性」
は309件中307件が単に `flags` 引数を省略しており（例: `いやしのこころ`, `おどりこ` 等）、
この2件だけ明示的に空集合を渡している。実害はないが、削除して他エントリと表記を揃えるべき。

## 命名の一貫性・妥当性

今回の主眼である「変数・関数・辞書キー・定数名の一貫性と妥当性」について、
`ability.py`/`item.py`/`volatile.py`/`field/*.py` を全件突き合わせて調査した結果を以下にまとめる。

### N-1: 複数エントリで共有されるハンドラ関数の命名に3つの異なる流儀が並立している

`ability.py` には、同じ効果を持つ複数の特性が1つのハンドラ関数を共有するケースが
多数あるが、その共有関数の命名方針が最低3種類に分かれている。

**(a) 最初に定義された特性の名前をそのまま流用する（最多）**

```python
"シェルアーマー": AbilityData(
    handlers={
        Event.ON_MODIFY_CRITICAL_RATE: h.AbilityHandler(
            h.カブトアーマー_block_crit,   # ← カブトアーマーの関数を流用
            subject_spec="defender:self",
        )
    }
),
```

同様のパターンが `ハードロック_reduce_effective`（→`フィルター`, `プリズムアーマー`が使用）、
`クリアボディ_block_stat_drop`（→`しろいけむり`, `メタルプロテクト`）、
`じょおうのいげん_block_priority`（→`テイルアーマー`, `ビビッドボディ`）、
`きんちょうかん_check_nervous`（→`じんばいったい`）、`きゅうばん_block_blow`（→`ばんけん`）、
`エアロック_check_weather_enabled`（→`ノーてんき`）、`ふゆう_float`（→`うなぎのぼり`）、
`しろのいななき_boost`（→`じしんかじょう`）、`へんげんじざい_change_type`（→`リベロ`）、
`さめはだ_chip_contact_attacker`（→`てつのトゲ`）、`ききかいひ_switch_on_half_hp`
（→`にげごし`）など10件以上で確認できる。

**(b) 共有先すべての特性名を連結した超長い識別子を新設する**

```python
# handlers/ability.py:1557
def しんりょくもうかげきりゅうむしのしらせ_modify_atk(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """ピンチ系特性: HP1/3以下かつ対応タイプ技で攻撃補正を1.5倍にする。"""
```

`げきりゅう`・`しんりょく`・`むしのしらせ`・`もうか`（HP低下時に対応タイプの攻撃を
1.5倍にする、いわゆる「ピンチ系特性」4種）は全てこの1関数を共有しているが、関数名は
4特性名をそのまま連結した17文字の識別子になっている（`ability.py:872-877, 949-952,
1139-1146, 2979-2983, 3046-3053` で使用）。

**(c) 特性名を一切含まない汎用英語スネークケースにする**

```python
# handlers/ability.py:1142-1155
def prevent_poison_ailment(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _prevent_ailment(battle, ctx, value, blocked_ailments=["どく", "もうどく"])
def prevent_paralysis_ailment(...): ...
def prevent_burn_ailment(...): ...
def prevent_sleep_ailment(...): ...
def prevent_freeze_ailment(...): ...
```

状態異常無効系の特性（`めんえき`/`パステルベール`→毒、`じゅうなん`→まひ、
`ねつこうかん`/`みずのベール`→やけど、`ふみん`/`やるき`/`スイートベール`→ねむり、
`マグマのよろい`→こおり）は、日本語の特性名を一切含まない汎用英語名の共有関数を使う。
`announce_ability_triggered`（かたやぶり系の発動ログ用）や `item.py` の
`flinch_on_hit_10pct`（`おうじゃのしるし`/`するどいキバ`が共有）も同じ流儀。

これら (a)(b)(c) はいずれもそれ単体では妥当な選択だが、「複数エントリに共有される
ハンドラをどう命名するか」という同一の設計判断に対して同じ `ability.py` 内で
3流儀が並立しており、方針がコード上どこにも明文化されていない。特に (b) は
「シェアされている」という情報を関数名から読み取れる利点はあるものの、新しい特性を
5つ目の共有先として追加する場合に関数名をリネームするのか、`__` 区切りを増やすのかの
判断基準がなく、スケールしない命名パターンである。少なくとも (b) のような
連結命名は今後増やさず、(a) のように代表となる特性名を1つ選ぶか、(c) のように
効果内容を表す汎用名にするかの二択に統一することを推奨する。

### N-2: `field/` パッケージ内で「tick処理」の命名・実装パターンが weather・terrain と global_field・side_field で異なる

**ファイル**: `src/jpoke/data/field/weather.py`, `terrain.py`, `global_field.py`,
`side_field.py`、実装は `src/jpoke/handlers/field.py:25-35, 37-44, 115-116` 等

`global_field.py`/`side_field.py` は、場の効果ごとに `<効果名>_tick` という個別の
名前付きラッパー関数を用意し、内部で共通ヘルパー（`_tick_global_field`/`_tick_side_field`）
に委譲する。

```python
# handlers/field.py:298-299
def じゅうりょく_tick(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _tick_global_field(battle, ctx, value, name="じゅうりょく")
```

一方 `weather.py`/`terrain.py` は個別ラッパーを作らず、`tick_weather`/`tick_terrain` という
天候・地形共通の1関数をそのまま全エントリに登録している。

```python
# handlers/field.py:25-29
def tick_weather(battle: Battle, ctx: EventContext, value: Any):
    if battle.get_player(ctx.source) is battle.players[0]:
        battle.weather_manager.tick_down_current()
    return HandlerReturn(value=value)
```

同じ `field/` パッケージ内、同じ「持続ターンを1つ減らす」という概念に対して、
(1) 効果名を冠した個別関数を8個以上量産する設計と、(2) カテゴリ共通の1関数で済ませる設計、
という異なるアーキテクチャ上の判断が並立している。天候・地形はどのエントリも
「該当天候/地形自身のカウントダウン」という完全に対称な処理のため (2) の方が実装コストは
低く、`global_field`/`side_field` 側も実質的には `name` 引数を変えているだけで
ロジックは共通ヘルパーに委譲されている。つまり後者も (2) 相当の共通化は既にできており、
残っているのは「関数名を場の効果ごとに分けるかどうか」という命名レベルの違いだけである。
両者を比べると `weather.py`/`terrain.py` 側（(2)）の方が明らかに簡潔で、
`global_field.py`/`side_field.py` 側の8個の1行ラッパー関数（前回レビュー `data.md`
未指摘）は将来的に (2) の形に統一できる余地がある。

### N-3: `data/models.py` の `name` フィールドの型注釈が、対応する自動生成 Literal 型と一致していない

**ファイル**: `src/jpoke/data/models.py:31, 44, 68, 76, 85, 93`

`types/` 配下には `data/ailment.py`・`data/field/{global_field,side_field,terrain,weather}.py`・
`data/volatile.py` の辞書キーから自動生成される専用の `Literal` 型が存在する
（いずれも自動生成コメント付きで、生成元ファイルが明記されている）。

```python
# src/jpoke/types/ailment.py:4
AilmentName = Literal["", "どく", "もうどく", "まひ", "やけど", "ねむり", "こおり", "ゆめうつつ"]
# 自動生成: python scripts/generate_literals/generate_ailment_literal.py で更新（元: src/jpoke/data/ailment.py）

# src/jpoke/types/volatile.py:4
VolatileName = Literal[...]  # 同様に自動生成
```

にもかかわらず、`data/models.py` の対応する dataclass は次のように型注釈がまちまちである。

| dataclass | `name` フィールドの型 | 対応する専用 Literal 型 |
|---|---|---|
| `AbilityData` | `AbilityName` | （一致） |
| `ItemData` | `ItemName` | （一致） |
| `MoveData` | `MoveName \| Literal[""]` | （一致） |
| `FieldData` | `str` | `WeatherName`/`TerrainName`/`GlobalFieldName`/`SideFieldName`（4種、統合先なし） |
| `AilmentData` | `str` | `AilmentName`（存在するが未使用） |
| `VolatileData` | `str` | `VolatileName`（存在するが未使用） |

`AbilityData`/`ItemData`/`MoveData` の3クラスは自身の辞書キー型（`AbilityName`/`ItemName`/
`MoveName`）を `name` の型注釈として正しく使っているが、`AilmentData.name`/`VolatileData.name`
は対応する `AilmentName`/`VolatileName` が `types/` に既に存在するにもかかわらず汎用 `str`
のままになっている。`FieldData` は `WEATHER`/`TERRAIN`/`GLOBAL_FIELD`/`SIDE_FIELD` の4カテゴリを
1つのクラスで表現しているため対応する単一の Literal 型が存在せず（`str` のままなのは
一定の合理性がある）、この3クラスとは事情が異なる。少なくとも `AilmentData.name: AilmentName`,
`VolatileData.name: VolatileName` への変更は、既存の自動生成型をそのまま活用でき、
`common_setup()` が代入する値が辞書キーの型と静的に一致することを型チェッカーで保証できる
ため、追加コストなしに型安全性を上げられる改善である。

### N-4（ISSUE-1/ISSUE-2の要約・命名観点からの位置づけ）

前掲 ISSUE-1（`subject_spec` の位置引数41件）・ISSUE-2（`LethalHandler.func` の位置引数4件）は、
いずれも「キーワード引数名を明示するかどうか」という命名・可読性の一貫性問題である。
`item.py`/`volatile.py`/`field/*.py` ではこの逸脱がほぼ皆無（`item.py` の `LethalHandler` のみ
1/30件）である一方、`ability.py` は `subject_spec` で41/371件、`LethalHandler.func` で
3/9件と、逸脱の大部分が同一ファイルに集中している。`ability.py` は本レビュー対象中
最大（3326行/311件）のファイルであり、複数人・複数時期にわたる編集が重なりやすいことが
一因と推測される。機械的な `subject_spec="..."` / `func=` への統一（正規表現一括置換で
安全に実施できる）を推奨する。

### N-5（ISSUE-3の要約）

`VOLATILES` 辞書の五十音順崩れ（ISSUE-3で詳述）も、広義には「辞書内配置という一種の
命名・整理規則」の一貫性問題である。`ability.py`/`item.py`/`move.py` は自動整列スクリプトで
機械的に担保されている一方、`volatile.py` は同種のスクリプトを持たないため、docstring の
主張（五十音順）と実態が乖離したまま検出されずに残っている。

## 総評

`data/` コア定義層は、辞書キー（技名・特性名・アイテム名の日本語文字列）そのものの命名は
一貫しており重複もない一方、**登録コードの「書き方」レベル**（キーワード引数の有無、
共有ハンドラの命名方針、型注釈の専用型 vs 汎用型）では複数の流儀が同じファイル内で
並立していることが今回の全文精読で明らかになった。中でも `ability.py` は最大のファイルである
分、`subject_spec` 位置引数（41件）・`LethalHandler.func` 位置引数（3件）の集中先になっており、
機械的な一括置換で解消可能な軽微だが件数の多い逸脱として最優先で手を付けやすい。

最も重要な既存の指摘は、前回（2026-07-05）報告した `megaevol.py:98` の `MEGA_POKEMONS`
ジェネレータバグが、対象ファイルへのコミットが1件も無いまま**今日時点でも完全に未修正**で
あることである。1行の修正で解消するにもかかわらず1週間以上放置されており、
`Pokemon.megaevolved` を利用するあらゆるバトルで恒久的に誤った判定を返しうる実害のある
不具合として、他のどの指摘よりも優先して対応すべきである。
