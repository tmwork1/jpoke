# コードレビュー — handlers/ability・item

日付: 2026-07-12
対象: `src/jpoke/handlers/ability.py`（3564行）、`src/jpoke/handlers/ability_paradox.py`（130行）、
`src/jpoke/handlers/item.py`（2009行）
観点: 前回総合レビュー（2026-07-05、`.internal/review/code/index.md` / `handlers.md`）で指摘された
`id(mon)`グローバル辞書問題・メガソーラー半端実装の現状確認、2026-07-05以降の変更点の重点確認、
責務分離・重複コード・過剰設計・実バグの可能性、および**関数・変数名の一貫性と妥当性**（新規観点）。

3ファイルを全文読み直した上で執筆している。`git log --since=2026-07-05` で対象3ファイルに触れた
コミットは38件（うち大半は個別特性/技の `review:` コミット、加えて `TEXT_LOG廃止`・
`core/model/data間の循環import解消`・`poke-env互換実装`・`Pokemonの一時状態をmemoryスコープに統一`
などのリファクタが混在）。実際の差分は3ファイル合計で+310/-105行（310行追加・105行削除）であり、
差分は全て読み込んで重点的にレビューした。

---

## 総論

前回レビューの最重要指摘であった **CRIT-1（`id(mon)` キー・グローバル辞書）は今回のコード確認でも
解消されておらず、`handlers/ability.py` に2件（`_メガソーラー_saved` 辞書、`_とびだすなかみ_hp_before`
辞書）とも現存している**。特にメガソーラーは、有効フラグ自体は `mon.ability.state = "active"` という
インスタンス属性で管理されているにもかかわらず、それと対になる保存データ（元の天候名・はれカウント）
だけが `id(mon)` キーのモジュールグローバル辞書に残るという「半分だけ正しい」実装のままである。
これは前回指摘からの1週間で対応されておらず、`Battle` の deepcopy 多用設計（探索・観測構築・
致死率計算）との相性の悪さは変わらず存在する。

2026-07-05以降の差分は、全体としては既存の命名規約・ヘルパー分解の作法に忠実に追随している
（例: `いのちのたま_recoil` のいのちのたま再確認ロジック、`ばんけん_boost_atk_on_intimidate` の
辞書コピーへの書き換えなど、丁寧な追加修正が多い）。一方で、今回の全文精読によって以下の点が
新たに見つかった。

1. `しろのいななき`/`じしんかじょう` という**別々のAbilityDataエントリが同一の関数
   `しろのいななき_boost` を共有**しており（`data/ability.py:1099,1164`）、docstringは
   「じしんかじょう特性」を名乗るが関数名は「しろのいななき」のまま（命名の一貫性節で詳述）。
2. `どんかん_block_intimidate`/`マイペース_block_intimidate`（いずれも今回の差分で新規追加）が、
   既存の `きもったま_block_intimidate`/`せいしんりょく_block_intimidate` と全く同じ3行ロジックを
   コピーしており、共有ヘルパーに切り出す機会を逃している。
3. 関数・変数命名の一貫性を横断的に調べた結果、`announce_ability_triggered`（公開）と
   `_announce_ability_triggered`（非公開）のような紛らわしい対、非公開ヘルパーの引数順序の
   ゆらぎ、ability.py と item.py で同種処理（ひるみ追加効果の重複防止・タイプ半減効果）の
   命名思想が食い違っている実例が複数見つかった。詳細は「命名の一貫性・妥当性」節にまとめる。

---

## 重大な指摘

### CRIT-1（既存・現存確認）: `id(mon)` キー・モジュールグローバル辞書による一時状態の受け渡し

**ファイル**: `src/jpoke/handlers/ability.py:76`（`_メガソーラー_saved` 宣言）、`:3224`（保存）、
`:3243-3246`（`メガソーラー_deactivate` での早期リターンとpop）、`:2124`（`_とびだすなかみ_hp_before`
宣言）、`:2116`（`とびだすなかみ_retaliate_on_ko` での参照。辞書宣言より14行前に出現する前方参照）、
`:2129`（`とびだすなかみ_save_hp` での書き込み）

```python
# handlers/ability.py:76
_メガソーラー_saved: dict[int, tuple[str, int]] = {}
...
# handlers/ability.py:3218-3237（メガソーラー_activate）
def メガソーラー_activate(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    mon = ctx.attacker
    wm = battle.weather_manager
    original_name = wm.current_name
    original_hare_count = wm.fields["はれ"].count
    _メガソーラー_saved[id(mon)] = (original_name, original_hare_count)
    ...
    mon.ability.state = "active"          # ← 有効フラグはインスタンス属性
    return HandlerReturn(value=value)

# handlers/ability.py:3240-3259（メガソーラー_deactivate）
def メガソーラー_deactivate(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    mon = ctx.attacker
    if mon.ability.state != "active":
        return HandlerReturn(value=value)  # ← ここで早期リターンすると pop されない
    wm = battle.weather_manager
    saved = _メガソーラー_saved.pop(id(mon), None)
```

前回レビュー（handlers.md CRIT-1）で指摘した「`Battle` の deepcopy 多用設計と `id()` の
本質的な危険性（GC後の再利用によるキー衝突）」「メガソーラーの有効フラグはインスタンス属性化
済みだが保存データだけがグローバル辞書に残る片手落ち」の両方が、今回のコード再確認でも一切
変わっていないことを確認した。1週間の開発で ability.py には多数の変更が入ったが（38コミット）、
この根本問題への着手は行われていない。修正方針は前回同様、`mon.ability` 側に
`saved_weather: tuple[str, int] | None` のようなフィールドを追加し、`_とびだすなかみ_hp_before` も
`AttackContext` へのフィールド化または `Pokemon` 側の一時属性化を推奨する。

`_とびだすなかみ_hp_before` は宣言（2124行目）より前（2116行目、`とびだすなかみ_retaliate_on_ko`
内）で参照されており、モジュール冒頭の「五十音順配置」規約からも外れた特異な位置（本来の
五十音順であれば "と" 節の先頭付近にあるべき定数がハンドラ2つの間に埋め込まれている）にある点も
前回から変化していない。

---

## 中程度の指摘

### ISSUE-1（新規）: `しろのいななき_boost` が異なる2つのAbilityDataエントリに登録され、docstringも実名と食い違っている

**ファイル**: `src/jpoke/handlers/ability.py:1488-1490`、`src/jpoke/data/ability.py:1096-1103, 1161-1166`

```python
# handlers/ability.py:1488-1490
def しろのいななき_boost(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """じしんかじょう特性: 攻撃技で相手を倒すと攻撃が1段階上がる。"""
    return _boost_on_move_ko(battle, ctx, value, stats={"atk": +1})
```

```python
# data/ability.py:1096-1103
"しろのいななき": AbilityData(
    handlers={
        Event.ON_MOVE_KO: h.AbilityHandler(h.しろのいななき_boost, subject_spec="attacker:self")
    }
),
...
# data/ability.py:1161-1166
"じしんかじょう": AbilityData(
    handlers={
        Event.ON_MOVE_KO: h.AbilityHandler(h.しろのいななき_boost, subject_spec="attacker:self")
```

`しろのいななき` と `じしんかじょう` という2つの別々の特性キーが同一の関数 `しろのいななき_boost`
を共有している。この関数のdocstringは「じしんかじょう特性」を名乗っており、関数名 `しろのいななき`
とは一致しない（`じしんかじょう` 側から検索すると別名の関数に辿り着き、`しろのいななき` 側の
docstringを読むと自分の特性名が出てこない）。

同ファイルには複数特性で共有されるハンドラの命名規約が既に存在し（`しんりょくもうかげきりゅう
むしのしらせ_modify_atk`、1557行目、しんりょく/もうか/げきりゅう/むしのしらせ4特性を関数名に
すべて連結）、`しろのいななき_boost` はこの規約に従っていない。さらに、実際の「じしんかじょう」
（Orichalcum Pulse、はれ展開+はれ中物理攻撃1.33倍）に相当する効果は同ファイル内の
`ひひいろのこどう_activate_weather`/`ひひいろのこどう_modify_atk`（2609-2620行目）として別途
正しく実装されているように見え、この「じしんかじょう」エントリ自体が意図しない重複登録である
可能性が高い。`data/ability.py` 側の "じしんかじょう" キーが本当に必要な別特性なのか、削除すべき
誤登録なのかを一次情報で確認し、必要なら `くろのいななき_boost`（既存、1303-1305行目）と対になる
形で `しろのいななき_boost` の関数名・docstringを一致させるか、正式に2特性共有として関数名を
連結すべき。

### ISSUE-2（新規）: `どんかん_block_intimidate`/`マイペース_block_intimidate` が既存の同型ロジックをそのままコピーしている

**ファイル**: `src/jpoke/handlers/ability.py:1110-1114`（きもったま）、`:1814-1819`（せいしんりょく）、
`:2255-2259`（どんかん、今回の差分で新規追加）、`:3060-3064`（マイペース、今回の差分で新規追加）

```python
def きもったま_block_intimidate(battle: Battle, ctx: EventContext, value: dict) -> HandlerReturn:
    """きもったま特性: いかくによるこうげきランク低下を無効化する。"""
    if ctx.stat_change_reason == "いかく":
        value = {}
    return HandlerReturn(value=value)

def どんかん_block_intimidate(battle: Battle, ctx: EventContext, value: dict) -> HandlerReturn:
    """どんかん特性: いかくによるこうげきランク低下を無効化する (第八世代以降)。"""
    if ctx.stat_change_reason == "いかく":
        value = {}
    return HandlerReturn(value=value)
```

4関数とも本体は事実上同一（`せいしんりょく` のみ発動ログ呼び出しが1行多い）。ファイルは
`_prevent_ailment`/`_prevent_volatile`/`_block_stat_drop_by_foe` のように「複数特性で共有される
処理は非公開ヘルパーに切り出す」規約を随所で実践しているにもかかわらず、今回新規追加された
`どんかん`/`マイペース` の2件はこの規約を踏襲せず、既存2件をそのままコピーする形で実装された。
`_block_intimidate(battle, ctx, value, *, announce=False) -> HandlerReturn` のような共有ヘルパーへ
統合すべき（`いかく`関連は `ビビリだま_boost_speed_on_intimidate` のdocstringが列挙する対象
特性・アイテム一覧からも分かる通り、今後も同種の追加が見込まれる領域）。

### ISSUE-3（既存の重複を拡張確認）: `_INNATE_FLINCH_MOVES` が ability.py と item.py に独立して重複定義されている

**ファイル**: `src/jpoke/handlers/ability.py:385-393`、`src/jpoke/handlers/item.py:513-522`

```python
# handlers/ability.py:385
# handlers/item.py の _INNATE_FLINCH_MOVES（おうじゃのしるし・するどいキバ）と同一。
_INNATE_FLINCH_MOVES: frozenset[str] = frozenset({...})

# handlers/item.py:513-514
# 元々ひるみの追加効果を持つ技名の集合。
# 現行世代（第五世代以降）ではこれらの技におうじゃのしるし・するどいキバの効果は重複しない。
_INNATE_FLINCH_MOVES: frozenset[str] = frozenset({...})
```

実装者自身が「item.py と同一」とコメントで明記するほど内容が一致した定数集合が、2ファイルに
それぞれ独立したモジュールグローバルとして存在する。今回の差分では両方の集合が同時に更新され
内容の一致は保たれているが（アイアンヘッド等の技リストから同じ8技が削除された）、これは
コメントで相互参照しているから気付けた偶然に近く、共有すべき定数が共有されていない状態が
「未共有の重複」として残っている（前回レビューの横断パターン#3と同種）。`data/` または
`handlers/` 配下の共有モジュール（例: `handlers/_move_sets.py`）へ1箇所化すべき。

### ISSUE-4（新規、軽微よりの中程度）: `とうそうしん_modify_atk` のdocstringにタイポがある

**ファイル**: `src/jpoke/handlers/ability.py:2098`

```python
def とうそうしん_modify_atk(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """とうそうしん特性: 同性の相手にこうげく/とくこうが1.25倍、異性には0.75倍になる。"""
```

「こうげく」は「こうげき」の誤字。実装ロジック自体は正しい。

---

## 過剰設計の疑い

今回の対象範囲では新規の過剰設計パターンは見つからなかった。前回レビュー（handlers.md）が
指摘した「カテゴリ別 `Handler` ラッパークラス（`AbilityHandler`/`ItemHandler` 含む）が
ポリモーフィズムとして使われていない」（OVER-1）は `ability.py:78-90`・`item.py:32-46` に
現存しており、指摘内容も変わらず有効である。`item.py` の `_dedicated_item_form_change`/
`_dedicated_item_modify_power`/`_dedicated_item_prevent_item_change`/
`_dedicated_item_prevent_transfer_to_base_form` は今回の全文精読でも御三家伝説6種
（ディアルガ/パルキア/ギラティナ、通常・オリジン・アナザー、加えてザシアン/ザマゼンタ/
オーガポン用の類似手書き実装）で実際に再利用されており、汎用化は妥当と判断した。

---

## 軽微な指摘

### MINOR-1（新規）: `だっしゅつパック_reserve_switch` にdocstringが無い

**ファイル**: `src/jpoke/handlers/item.py:1185-1196`

近い役割の `だっしゅつボタン_reserve_switch`（1199-1223行目）が発動条件・除外ケースを詳細に
説明する厚いdocstringを持つのに対し、`だっしゅつパック_reserve_switch` は関数直下のインライン
コメントのみでdocstringが存在しない。2アイテムの実装は非常に似ているため、docstringの有無が
どちらかの実装漏れの兆候に見えかねない。

### MINOR-2（新規）: `_move_power(move)` の引数に型注釈が無い

**ファイル**: `src/jpoke/handlers/ability.py:3405`

```python
def _move_power(move) -> int:
    if move.data.power is None:
        return 0
    return move.data.power
```

ability.py の非公開ヘルパー約20個の中で `move` 引数に型注釈（`Move`）が付いていないのはこの
関数のみ。単純な見落としと見られる。

---

## 命名の一貫性・妥当性

### N-1: 「公開のannounce系ハンドラ」と「非公開の内部ヘルパー」がアンダースコア1文字だけで区別されており紛らわしい

**ファイル**: `src/jpoke/handlers/ability.py:92-110`（`announce_ability_triggered`、`data/ability.py`
から `h.announce_ability_triggered` として8箇所で直接ハンドラ登録される）、`:112-119`
（`_announce_ability_triggered`、ability.py内で約190箇所から呼ばれる内部ヘルパー）、
`src/jpoke/handlers/item.py:48-50`（`announce_item_triggered`）、`:52-57`
（`_announce_item_triggered`）

`announce_ability_triggered`（公開・"何もしないが発動ログだけ出す"特性専用にHandlerとして直接
登録される）と `_announce_ability_triggered`（非公開・あらゆる特性ハンドラから呼ばれる真の
共通処理）は、名前がアンダースコアの有無でしか区別されず、役割の違い（「登録可能なHandler
関数」か「内部実装ヘルパー」か）が名前から読み取れない。item.py の
`announce_item_triggered`/`_announce_item_triggered` も同型。

さらに、この公開版と全く同じ処理を独自関数として再実装している例がある。

```python
# handlers/ability.py:2897-2900
def プレッシャー_announce(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """プレッシャー特性: 登場時にアナウンスを出す。"""
    _announce_ability_triggered(battle, ctx.source)
    return HandlerReturn(value=value)
```

`プレッシャー`は「登場時にアナウンスするだけ」という点で `オーラブレイク`
（`data/ability.py:406-409`、`h.announce_ability_triggered` を直接登録）と全く同じ要件だが、
`プレッシャー` 側は独自に薄いラッパー関数を書いている。同じニーズに対して「共有の公開ハンドラを
直接登録する」方式と「特性名を冠したラッパーを新設する」方式の2通りが併存しており、
どちらを使うべきかの基準がコード上どこにも明文化されていない。item.py側の
`とくせいガード_check_ability_disable`（1265-1268行目）も同様に `_announce_item_triggered` を
直接呼び、共有の公開版 `announce_item_triggered` を使っていない。

推奨: 公開ハンドラ側に `xxx_only_announce` のような役割が分かる名前を付けるか、逆に
非公開ヘルパーとの呼び出し関係をモジュールdocstringに明記する。

### N-2: 非公開ヘルパーの引数順序が ability.py 内でも、item.py との比較でも一貫していない

**ファイル**: `src/jpoke/handlers/ability.py:261`（`_block_stat_drop_by_foe`）

```python
def _block_stat_drop_by_foe(value: dict, ctx: EventContext, stat: Stat | None = None) -> dict:
```

ability.py の非公開ヘルパー約20個のうち、`battle` を取らないのはこの関数のみであり、かつ
唯一 `value` を `ctx` より前に置いている（他の全ヘルパーは `battle, ctx, value, ...` の順で
統一）。一方 item.py 側にも `battle` を取らない非公開ヘルパーが4つ存在するが
（`_modify_power_by_type(move, value, ...)`、`_dedicated_item_modify_power(ctx, value, ...)`、
`_dedicated_item_prevent_item_change(ctx, value, ...)`、
`_dedicated_item_prevent_transfer_to_base_form(ctx, value, ...)`）、いずれも `ctx` を `value` より
前に置く一貫した順序を保っている。つまり `_block_stat_drop_by_foe` は、自ファイル内の規約からも
item.py の対応する規約からも外れた、両ファイル中で唯一 `value, ctx` の順を取る関数になっている。

### N-3: `メガソーラー` のみが `wm = battle.weather_manager` というローカル変数の略記を導入している

**ファイル**: `src/jpoke/handlers/ability.py:3221, 3245`

`メガソーラー_activate`/`メガソーラー_deactivate` の2関数だけが `wm` という2文字の略記変数を
使用しており、同ファイルの他約60箇所の天候操作コード（`battle.weather_manager.apply(...)` 等）は
すべてフルスペルで参照している。ファイル全体でこの種の略記変数（`wm`, `vm`, `am` 等）は他に
存在せず、孤立した命名習慣になっている。

### N-4: ability.py と item.py で「ひるみ追加効果の重複防止」ハンドラの命名思想が食い違っている

**ファイル**: `src/jpoke/handlers/ability.py:396-413`（`あくしゅう_maybe_flinch`）、
`src/jpoke/handlers/item.py:524-540`（`flinch_on_hit_10pct`）

同じ「10%の確率でひるみを追加付与するが、元々ひるみ効果を持つ技には重複しない」という効果を
実装するハンドラが、ability.py では特性名を冠した日本語プレフィックス
（`あくしゅう_maybe_flinch`）である一方、item.py では英語のみで対象アイテム名を含まない
（`flinch_on_hit_10pct`、おうじゃのしるし・するどいキバの2アイテムで共有）。ability.py側の
慣例（1効果1特性名プレフィックス）に従うなら item.py 側も `おうじゃのしるし_maybe_flinch` の
ような名前になるはずだが、item.py はこの関数を含め全体で「複数アイテムに共有される処理は
英語の汎用名で登録する」という別の慣例（前回レビューの `_dedicated_item_*` 系と同様の思想）を
採っており、2ファイル間で「特性名/アイテム名を冠するかどうか」の判断基準が異なっている。

### N-5: `いかさまダイス_modify_hit_check_each_time`/`スキルリンク_modify_hit_check_each_time` は良い一貫性の実例

**ファイル**: `src/jpoke/handlers/item.py:412-414`、`src/jpoke/handlers/ability.py:1653-1655`
（今回の差分で新規追加）

```python
def いかさまダイス_modify_hit_check_each_time(_battle: Battle, _ctx: AttackContext, _value: bool) -> HandlerReturn:
    return HandlerReturn(value=False)

def スキルリンク_modify_hit_check_each_time(battle: Battle, ctx: AttackContext, value: bool) -> HandlerReturn:
    return HandlerReturn(value=False)
```

同じ「トリプルキック等の毎ヒット命中判定を初回のみにする」効果が、ability.py・item.py の両方で
全く同じ関数名パターン（`<特性/アイテム名>_modify_hit_check_each_time`）・同じdocstring文言で
実装されている。N-4と対照的に、こちらは今回の差分で新規追加されたにもかかわらず両ファイル間の
命名が完全に揃っており、他の同種処理を実装する際の模範例として言及する。

### N-6: `ノーマルジュエル_modify_power_by_type` は命名パターンが実装内容を誤解させる

**ファイル**: `src/jpoke/handlers/item.py:1387-1392`

```python
def ノーマルジュエル_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ノーマルジュエル: ノーマルタイプの攻撃技威力を1.3倍(5325/4096倍)にして消費する。"""
    if ctx.move.type == "ノーマル":
        value = apply_fixed_modifier(value, 5325)
        _announce_and_consume_item(battle, ctx.attacker)
    return HandlerReturn(value=value)
```

item.py には `<アイテム名>_modify_power_by_type` という命名の関数が15個以上あり
（`かたいいし_modify_power_by_type`、`じしゃく_modify_power_by_type` 等）、その全てが共有ヘルパー
`_modify_power_by_type(move, value, type_, modifier)` へ1行で委譲する統一実装になっている。
`ノーマルジュエル_modify_power_by_type` だけは同じ関数名パターンを持ちながらこの共有ヘルパーを
呼ばず、威力補正とアイテム消費（ジュエル系は永続装備のプレート等と異なり単発消費）を独自に
インライン実装している。ジュエル系の挙動がプレート系と異なるのは仕様として正しいが、
関数名だけを見ると「他の`_modify_power_by_type`関数と同じ薄い委譲」に見えてしまい、実装を
開いて初めて消費有りの特殊系だと分かる。`ノーマルジュエル_modify_power_by_type_and_consume` の
ような名前、あるいは共有ヘルパー側に `consume: bool = False` を追加する形が誤解を防げる。

### N-7（前回指摘の位置関係を再確認）: `prevent_poison_ailment` 等5ヘルパーの配置がアルファベット順配置ルールの例外になっている

**ファイル**: `src/jpoke/handlers/ability.py:1142-1156`

前回レビュー（handlers.md MINOR-13）が指摘した「英語名で特性名プレフィックスを持たない
状態異常無効化ヘルパー5つ（`prevent_poison_ailment` 等）」は今回も同じ位置・同じ内容で存在する
ことを確認した。これらは「きょううん」（1137行目）と「きよめのしお」（1158行目）の間、
五十音順でいえば "き" の途中に割り込む形で配置されており、複数特性で共有されるヘルパーが
「最初に使われた特性の直後」に置かれるという別ルールの副作用で、五十音順配置の原則から
視覚的に逸脱する実例になっている。是正は不要だが、モジュールdocstringに
「複数特性で共有する非公開ヘルパーはファイル冒頭にまとめる」旨を明記すれば今後の同種混乱を
防げる（前回のISSUE-16と同じ根本原因）。

---

## 総評

前回レビューの最重要課題であった `id(mon)` グローバル辞書問題（CRIT-1）は、38コミットに及ぶ
1週間の開発を経ても未着手のまま残っている。実害が顕在化していないのは `Battle` のdeepcopyが
「技実行中の短命な一時状態」と時間的に競合するケースが今のところ発生していないためと見られるが、
探索プレイヤー（`TreeSearchPlayer`）による先読みシミュレーションが増えるほどリスクは高まるため、
優先度は変わらず最高と判断する。

新規観点である命名の一貫性については、ability.py・item.py とも「`<特性/アイテム名>_<動作>`」
という基本パターンの遵守率は非常に高く、全体の秩序は保たれている。その一方で、(1) 公開/非公開の
announce系ヘルパーの役割がアンダースコアだけで区別され実際に重複実装を招いている点、
(2) `しろのいななき_boost` が別の特性キー `じしんかじょう` に誤って共有され、docstringも実名と
食い違っている点、(3) ability.py と item.py の間で「複数エンティティに共有される処理をどう
命名するか」の思想が統一されていない点、の3つは実際の可読性・保守性に影響する具体的な問題として
今回新たに発見された。特に(2)は特性データの正確性そのものに関わる可能性があるため、一次情報との
突き合わせを推奨する。
