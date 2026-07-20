# コードレビュー — handlers/status・field・lethal

日付: 2026-07-12
対象: `src/jpoke/handlers/volatile.py`（1432行）、`src/jpoke/handlers/ailment.py`（165行）、
`src/jpoke/handlers/field.py`（611行）、`src/jpoke/handlers/lethal.py`（761行）
観点:
1. 一般的な品質観点（前回指摘の現状確認、2026-07-05以降の変更点の重点レビュー、責務分離、重複、過剰設計、実際のバグの可能性）
2. **関数・変数名の一貫性と妥当性**（新設。揮発性状態名・状態異常名からハンドラ関数名への変換規則、天候/地形/場のハンドラ間の命名パターン、`lethal.py`のドメイン表現力、4ファイル間で共通する概念の命名統一）

前回総合レビュー（`.internal/review/code/index.md`, 2026-07-05）の `handlers.md`（`handlers/` 全体レビュー）、
`lethal_2026-07-01.md`（`lethal.py` 関連の過去レビュー）を確認した上で、対象4ファイルを全文読み直した。
`git log --since=2026-07-05` で対象4ファイルへの変更（40件超のコミット、うち多くは技レビュー由来の追加・
リファクタ）を洗い出し、新規/変更箇所を重点的に確認した。

---

## 総論

前回 `handlers.md`（OVER-2）が指摘した「`handlers/lethal.py` の `_heal_at_pinch` が未使用の汎用性を持つ
（過剰設計）」は、**今回のコード確認でも現状維持を確認した**。`heal_with: Literal["ability", "item"] | None`
という汎用シグネチャに対し、実際の呼び出し（イアのみ・ウイのみ・オボンのみ・オレンのみ・バンジのみ・
フィラのみ・マゴのみ、計7箇所）は全て `heal_with="item", consume=True` で固定されたままであり、
`heal_with="ability"` 分岐に対応する特性は7/5〜7/12の追加分にも登場しなかった（詳細は
[過剰設計の疑い OVER-1](#over-1-heal_at_pinch-の-heal_with-ability-分岐は依然デッドコード前回指摘の現状確認)
参照）。対になる `_survive_at_full_hp`（がんじょう/きあいのタスキ）は両分岐とも実際に使われており対照的。

2026-07-05以降の変更は主に「技レビュー」フローによる新規実装・修正（くちばしキャノンの再設計、
ころがる・きょけんとつげきの新規実装、にげられない/はいすいのじんの解除条件修正、TEXT_LOG廃止に伴う
Payload置き換え、poke-env互換の`rank→boosts`改名など）で構成されている。このうち `lethal.py` への
`rank→boosts` 一括改名（コミット `7fc56bf9`）を機械的に検証したところ、**`ばかぢから` の
リーサルハンドラが実バトル側のハンドラと異なり ぼうぎょ down を欠いたまま実装されている**という、
改名作業とは無関係の既存バグを新規に発見した（[重大な指摘 CRIT-1](#crit-1-lethalpy-の-ばかぢから_lower_atk-がぼうぎょ低下を実装していない実バトルとの乖離)）。
このバグは奇しくも「関数名自体が実装の欠落を正直に反映している」ケースであり、命名の妥当性チェックが
実バグの発見につながった好例になった。

命名の一貫性の観点では、各ファイル内はおおむね規律が保たれている一方（`_tick_volatile`/`_remove_volatile`/
`_power_modifier`/`_boost_X`/`_prevent_X` 等の接尾辞パターンは大多数の関数で守られている）、
**ファイルをまたいで同一概念を表す箇所ほど語彙が割れる**という傾向がはっきり見られた。
`ON_CHECK_FLOATING` に対する `field.py` の `じゅうりょく_grounded` と `volatile.py` の
`_check_floating` 系3関数、`disabled_reason` ライフサイクル管理に対する `volatile.py` の
`とくせいなし_disable_ability`/`enable_ability` と `field.py` の `マジックルーム_apply`/`remove`、
`lethal.py` と `move_attack.py` 間での同一技ハンドラの命名不一致（`ばかぢから`、`テラバースト`）などが
代表例で、詳細は [命名の一貫性・妥当性](#命名の一貫性妥当性) にまとめた。

---

## 重大な指摘

### CRIT-1: `lethal.py` の `ばかぢから_lower_atk` がぼうぎょ低下を実装していない（実バトルとの乖離）

**ファイル**: `src/jpoke/handlers/lethal.py:573-576` vs `src/jpoke/handlers/move_attack.py:2604-2605`

```python
# handlers/move_attack.py:2604-2605（実バトル側、正しい実装）
def ばかぢから_lower_attacker_def(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"atk": -1, "def": -1})

# handlers/lethal.py:573-576（リーサル側、ぼうぎょ低下が欠落）
def ばかぢから_lower_atk(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """ばかぢから: 命中後、攻撃側のこうげきを1段階下げる。"""
    ctx.attacker.boosts["atk"] = clamp_stats(ctx.attacker.boosts["atk"] - 1)
    return hp_dist
```

ばかぢから（Superpower）は命中後にこうげき・ぼうぎょの両方を1段階下げる技（`move_attack.py` の
`stats={"atk": -1, "def": -1}` が正）。しかし `lethal.py` 側のリーサル計算ハンドラはこうげきの
低下しか反映しておらず、`ctx.attacker.boosts["def"]` の更新が丸ごと抜けている。`data/moves/move_ha.py:453`
（`LethalEvent.ON_HIT: LethalHandler(l.ばかぢから_lower_atk)`）で実際に登録されており、テスト漏れの
デッドコードではなく本番経路で使われる。この関数のリーサル計算結果を使う致死率判定・木探索は、
ばかぢから使用後の防御側追撃技（相手が物理技で追撃するケースを想定した自身の耐久評価等、`ctx.attacker`
自身のぼうぎょが下がった状態を踏まえるべき場面）で誤った生存確率を返す。

注目すべきは、関数名 `_lower_atk`（単数形・atkのみ）自体が実装の欠落を正確に反映している点である。
`テラバースト_lower_attacker_atk_spa`（`lethal.py:523-529`）のように2ステータス変化を扱う技では
名前に両方のステータス記号（`atk_spa`）を含める命名がすでに存在しており、`ばかぢから` 側も
`_lower_atk_def` のような名前にしていれば実装漏れに気づきやすかったと考えられる（
[命名の一貫性・妥当性](#8-lethalpy-と-move_attackpy-間で同一技のハンドラ名が一致せずばかぢからでは実装漏れと直結している) 参照）。
`ctx.defender.boosts["def"]` ではなく `ctx.attacker.boosts["def"]` を追加で下げる1行修正で解消する。

---

## 中程度の指摘

### ISSUE-1: `ロックオン_remove_volatile` が共有ヘルパーを経由せず、同名の他関数と異なりログを出さない

**ファイル**: `src/jpoke/handlers/volatile.py:1424-1428`

```python
def ロックオン_remove_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """相手が交代したときに自分のロックオン状態を解除する。"""
    mon = battle.foe(ctx.source)
    battle.volatile_manager.remove(mon, "ロックオン")
    return HandlerReturn(value=value)
```

`volatile.py` 内で `_remove_volatile` という名前を持つ関数は他に20個以上あり、そのほぼ全てが
モジュール共有ヘルパー `remove_volatile()`（62-83行目、解除に成功すると `LogCode.VOLATILE_REMOVED`
をログ出力する）を呼び出す形で統一されている（例: `あなをほる_remove_volatile:159`,
`コールドフレア_remove_volatile:552`, `フリーズボルト_remove_volatile:1159` 等）。ところが
`ロックオン_remove_volatile` だけは `battle.volatile_manager.remove()` を直接呼んでおり、
解除に成功してもログが出力されない。`にげられない_remove_on_foe_switch`（885-911行目）や
`バインド_remove`（1044-1057行目）も同様に直接呼び出しだが、こちらは関数名自体が
`_remove_volatile` パターンから外れているため「名前と挙動が一致しない」問題は発生しない。
`ロックオン_remove_volatile` は名前だけ他の20個と揃えているぶん、挙動差が発見しづらい。
`remove_volatile(battle, ctx, value, volatile="ロックオン")` に置き換えて統一すべき。

### ISSUE-2: `.internal/spec/turn.md` を含む32ファイルが現存しないイベント名 `Event.ON_CHECK_ACTION` を参照している

**ファイル**: `.internal/spec/turn.md:172-203`, `.internal/spec/ailments/こおり.md:47-53`,
`.internal/spec/ailments/やけど.md:44-`, `.internal/spec/ailments/どく.md:44-` ほか計32ファイル
（`.internal/spec/volatiles/ひるみ.md`, `.internal/spec/volatiles/ふういん.md` 含む）

`src/jpoke/enums/event.py:152` の実装は `ON_TRY_ACTION`（コメント「emit: core/move_executor.py
（行動実行可否の判定）、handle: ailment.py（まひ・ねむり・こおり）, volatile.py（こんらん・ひるみ・
どろぼう状態等）」）のみで、`ON_CHECK_ACTION` という名前のイベントはコードベース上に存在しない。
しかし `.internal/spec/turn.md:172`（`## Event.ON_CHECK_ACTION`）や `.internal/spec/ailments/こおり.md:49`
（``.internal/spec/turn.md` の `Event.ON_TRY_ACTION` より`` と本文で書きつつ見出しは旧名のまま）など、
過去に `ON_CHECK_ACTION → ON_TRY_ACTION` へリネームされた形跡がありながら `.internal/spec/` 側の更新が
追いついていない。実際に `src/jpoke/data/ailment.py:53,82,91`（`まひ_action`/`ねむり_check_action`/
`こおり_action` の登録）の `priority=120/10/10` は `.internal/spec/turn.md:194-195`
（`| 110 | こんらんの自傷の判定 | / | 120 | まひして技が出せない |`）の値と一致しており実害はまだ
出ていないが、CLAUDE.md が「priority は `.internal/spec/turn.md` で対象イベントの行を必ず確認する」と
明記している以上、次に `ON_TRY_ACTION` の優先度を確認する実装者が旧イベント名で検索して見つからず
混乱するリスクがある。`index.md` が指摘する「ドキュメントドリフト」パターン（37箇所以上の
emit/handleコメント）と同種の問題が `.internal/spec/turn.md` 側にも及んでいることが今回新たに分かった。

### ISSUE-3: `いちゃもん`/`かなしばり`/`デカハンマー`/`ブラッドムーン` の「除外型」コマンド変更ロジックが手書きで重複しており、`じごくづき_restrict_commands` も同型のロジックを名前だけ異なるパターンに寄せて実装している

**ファイル**: `src/jpoke/handlers/volatile.py:227-247`（いちゃもん）, `359-378`（かなしばり）,
`641-659`（じごくづき）, `835-847`（デカハンマー）, `1164-1176`（ブラッドムーン）

```python
# いちゃもん_modify_command_options（227-247）とかなしばり_modify_command_options（359-378）は
# 「volatiles[name].move_name と一致する技コマンドを除外する」という同一ロジックをほぼ丸ごと重複している
def いちゃもん_modify_command_options(battle, ctx, value):
    mon = ctx.source
    last_move_name = mon.volatiles["いちゃもん"].move_name
    new_options = []
    for cmd in value:
        if not cmd.is_move or mon.moves[cmd.index].name != last_move_name:
            new_options.append(cmd)
    return HandlerReturn(value=new_options)
```

`アンコール_restrict_commands`（219-220）/`こだわり_restrict_commands`（470-471）はモジュール共有の
`restrict_commands()` ヘルパー（121-136行目、「指定技のみ選択可」という**包含型**フィルタ）へ委譲して
いるが、`いちゃもん`/`かなしばり`/`デカハンマー`/`ブラッドムーン` は「指定技のみ除外」という**除外型**
フィルタを4関数それぞれで手書きしており、共有ヘルパー化されていない。さらに `じごくづき_restrict_commands`
（641-659）は「sound技を除外する」という同じ除外型ロジックを実装しているにもかかわらず、関数名は
`restrict_commands()` を呼ぶ包含型の2関数と同じ `_restrict_commands` 接尾辞を名乗っている。
名前だけでは「共有ヘルパーを呼ぶ側」か「独自実装側」かを判別できず、命名と実装パターンの対応関係が
崩れている（詳細は [命名の一貫性・妥当性 7](#7-lethalpy-の-_apply_x-系命名でキラースピン_apply_どくれんごく_apply_やけどは対象状態名を明示するがしおづけサイコノイズは汎用語止まり) の姉妹問題として本節に記載）。
`exclude_move_command(battle, ctx, value, excluded_move_name)` のような共有ヘルパーを1つ追加すれば
4関数の重複が解消し、`じごくづき` は名前を `_exclude_sound_commands` 等に改めることで実装との対応も
明確になる。

---

## 過剰設計の疑い

### OVER-1: `_heal_at_pinch` の `heal_with="ability"` 分岐は依然デッドコード（前回指摘の現状確認）

**ファイル**: `src/jpoke/handlers/lethal.py:49-103`

前回 `handlers.md`（OVER-2）の指摘通り、`heal_with: Literal["ability", "item"] | None` という
汎用シグネチャに対し、実際の7呼び出し（イアのみ`:208`、ウイのみ`:254`、オボンのみ`:284`、
オレンのみ`:313`、バンジのみ`:616`、フィラのみ`:626`、マゴのみ`:670`）は全て
`heal_with="item", consume=True` に固定されたままであり、`heal_with == "ability"` 分岐
（81-83行目, 94-100行目の `keep_ability_enabled` 計算）は今回のレビュー時点でも未使用と確認した。
2026-07-05以降に技レビューで多数のリーサルハンドラが追加されたが（`しんぴのちから`, `ほのおのまい`,
`しおづけ`, `サイコノイズ` 等）、いずれもこのヘルパーの新規利用ではなく、`_heal`/`_damage`/独自実装
（`うたかたのアリア`, `キラースピン` 等）を使っている。対になる `_survive_at_full_hp`
（112-130行目）は `consume="ability"`（がんじょう `:342`）と `consume="item"`
（きあいのタスキ `:352`）の両方が使われており対照的。実害はないが、YAGNI的な早すぎる一般化として
現状維持を確認した。

---

## 軽微な指摘

### MINOR-1: `じゅうでん_boost_electric` が `remove_volatile()` の戻り値を使わず、位置引数で呼んでいる

**ファイル**: `src/jpoke/handlers/volatile.py:677-691`

```python
def じゅうでん_boost_electric(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    if ctx.move.type == "でんき":
        value *= 2
        remove_volatile(battle, ctx, value, "じゅうでん")
    return HandlerReturn(value=value)
```

他の呼び出し20件超は全て `remove_volatile(battle, ctx, value, volatile="XXX")` とキーワード引数で
`volatile=` を明示しているが、この1箇所のみ位置引数で渡している。実害はないが、シグネチャ変更時に
気づかれにくい書き方であり、キーワード引数に揃えるべき。

### MINOR-2: `あばれる_tick`/`あめまみれ_turn_end`/`バインド_damage` が `tick_volatile()` 共有ヘルパーを経由せず `battle.volatile_manager.tick()` を直接呼んでいる

**ファイル**: `src/jpoke/handlers/volatile.py:164-179`（あばれる）, `182-199`（あめまみれ）,
`1017-1041`（バインド）

いずれも「tick に付随する追加処理（混乱付与・ランク低下・ダメージ）があるため共有ヘルパーを使わない」
という合理的な理由があるが、関数名がそれぞれ `_tick`/`_turn_end`/`_damage` とバラバラであり、
「なぜこの3つだけ `tick_volatile()` を経由しないか」がコード上に説明されていない。命名面の指摘は
[命名の一貫性・妥当性 2](#2-揮発状態の解除処理を表す接尾辞が-volatilepy-内だけで-5-種類に分裂している) を参照。

---

## 命名の一貫性・妥当性

### 1. `ailment.py`: 同一の役割を持つ行動不能チェック3関数が `_action` と `_check_action` に分裂している

**ファイル**: `src/jpoke/handlers/ailment.py:25-56`（こおり）, `92-113`（ねむり）,
`116-131`（まひ）

```python
def こおり_action(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """こおり状態による行動不能チェック。"""
def ねむり_check_action(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ねむり状態による行動不能チェック"""
def まひ_action(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """まひ状態による行動不能チェック（12.5%確率）。"""
```

3関数はいずれも `Event.ON_TRY_ACTION` に登録され（`data/ailment.py:53,82,91`）、docstring も
一字一句「◯◯状態による行動不能チェック」という同一の文言を使っているにもかかわらず、関数名の
接尾辞だけ `_action`（こおり・まひ）と `_check_action`（ねむり）に分かれている。`git log` で
確認したところ、2026-07-06のコミット `b7c9cba7`（ねっとうレビュー）で3関数を五十音順に並び替える
リファクタが行われたが、この時点でも命名の統一は行われなかった。3ファイル中もっとも短い
ファイル（165行）にもかかわらず見つかった、最も直接的な命名不統一の実例。`_check_action` へ
統一するか `_action` へ統一するかは実装判断だが、少なくとも同一ファイル内・同一イベント登録の
3関数は揃えるべき。

### 2. 揮発状態の「解除」処理を表す接尾辞が `volatile.py` 内だけで5種類に分裂している

**ファイル**: `src/jpoke/handlers/volatile.py` 全体

| 接尾辞 | 代表例 | 共有ヘルパー `remove_volatile()` を経由するか |
|---|---|---|
| `_remove_volatile` | `あなをほる`, `コールドフレア`, `フリーズボルト` ほか20件超 | する（ロックオンのみ例外、ISSUE-1参照） |
| `_remove` | `バインド_remove:1044`, `みちづれ_remove:1317` | バインドはしない／みちづれはする（さらに割れている） |
| `_remove_on_foe_switch` | `にげられない_remove_on_foe_switch:885` | しない |
| `_end_heating` | `くちばしキャノン_end_heating:459` | する |
| `_check_interrupt` | `ころがる_check_interrupt:501`（解除は副作用） | する |
| `_turn_end` | `そうでん_turn_end:713`（無条件解除、ログなし） | しない |

特に `バインド_remove`（1044-1057行目）と `にげられない_remove_on_foe_switch`（885-911行目）は、
「`ctx.source` が場を離れたときに、その相手が持つ揮発状態を消す」という**全く同一のロジック**
（`foe = battle.foe(ctx.source); battle.volatile_manager.remove(foe, "XXX")`）を実装しており、
`にげられない` 側の docstring 自身が「バインド状態の`バインド_remove`と同じパターン」と明記している
（896行目）。にもかかわらず関数名は `_remove` と `_remove_on_foe_switch` で異なる。同じく
`data/volatile.py` で `Event.ON_SWITCH_OUT` + `subject_spec="source:foe"` という同一の登録形も
確認済み（`バインド:654-657`, `にげられない:588-591`, `ロックオン:828-831`）。この3件は
「相手の交代で解除される」という共通パターンを持つグループとして命名を揃える価値がある
（例: 全て `_remove_on_foe_switch` に統一するか、`remove_on_foe_switch()` という第3の共有ヘルパー
を新設して呼び出し元を委譲する）。

また `_turn_end` という接尾辞は3つの異なる意味で使われている点も紛らわしい: `あめまみれ_turn_end`
（182-199、ランク低下+tick）、`そうでん_turn_end`（713-716、無条件解除・ログなし）、
`マジックコート_turn_end`（1208-1210、共有ヘルパー経由の解除・ログあり）。「ターン終了時に何かする」
という以上の情報を接尾辞から読み取れない。

### 3. `field.py` の `じゅうりょく_grounded` が `volatile.py` の `_check_floating` 系と同一イベントに対して異なる語彙を使っている

**ファイル**: `src/jpoke/handlers/field.py:278-280`, `src/jpoke/handlers/volatile.py:250-261`
（うちおとす）, `855-857`（でんじふゆう）, `956-958`（ねをはる）

```python
# field.py:278-280
def じゅうりょく_grounded(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """じゅうりょく中は全ポケモンを地面に接地扱いにする"""
    return HandlerReturn(value=False, stop_event=True)
```

`data/field/global_field.py:16-18` で `Event.ON_CHECK_FLOATING` に登録されており、これは
`volatile.py` の `うちおとす_check_floating`（250-261行目）・`でんじふゆう_check_floating`
（855-857行目）・`ねをはる_check_floating`（956-958行目）と**全く同じイベント**に対する
ハンドラである。後者3件はいずれも「浮遊しているかどうかを判定・強制する」という役割を
`_check_floating` という接尾辞で一貫して表現しているが、`field.py` 側だけ効果の結果
（「接地扱いになる」）を表す `_grounded` という語を使っており、同一イベントに対する
命名パターンが `field.py`/`volatile.py` の境界で分裂している。`じゅうりょく_check_floating`
へ改名すれば、`Event.ON_CHECK_FLOATING` ハンドラを横断検索する際の一貫性が得られる。

### 4. `disabled_reason` ライフサイクル管理の命名が `volatile.py`（効果を明示）と `field.py`（汎用語）で異なる語彙選択をしている

**ファイル**: `src/jpoke/handlers/volatile.py:864-873`（とくせいなし）,
`src/jpoke/handlers/field.py:480-489`（マジックルーム）

```python
# volatile.py: 効果そのものを動詞化した名前
def とくせいなし_disable_ability(battle, ctx, value):
    battle.add_ability_disabled_reason(ctx.source, "とくせいなし")
def とくせいなし_enable_ability(battle, ctx, value):
    battle.remove_ability_disabled_reason(ctx.source, "とくせいなし")

# field.py: ライフサイクルイベント名をそのまま踏襲した汎用語
def マジックルーム_apply(battle, ctx, value):
    battle.item_manager.add_disabled_reason(ctx.source, "マジックルーム")
def マジックルーム_remove(battle, ctx, value):
    battle.item_manager.remove_disabled_reason(ctx.source, "マジックルーム")
```

両者は「`ON_VOLATILE_START`/`ON_FIELD_ACTIVATE` で特性/アイテムを`disabled_reason`経由で
無効化し、`ON_VOLATILE_END`/`ON_FIELD_DEACTIVATE` で再有効化する」という同一のライフサイクル
パターン（登録は `data/volatile.py:572-579`, `data/field/global_field.py:55-66` で確認済み）を
実装しているが、`とくせいなし` は効果を説明する動詞（`disable_ability`/`enable_ability`）を、
`マジックルーム` はイベント名をなぞっただけの汎用語（`apply`/`remove`、他の大多数のフィールド
ハンドラが「発動時処理」の意味で使う語と同じ）を使っている。`マジックルーム_apply`という名前
だけを見てもアイテムを無効化する効果だとは分からず、`とくせいなし` 側の命名方針（効果を明示する）
に揃えるなら `マジックルーム_disable_item`/`マジックルーム_enable_item` のような名前が一貫する。

### 5. `lethal.py` の能力ランク低下ハンドラで `_lower_X` と `_reduce_X` が混在している

**ファイル**: `src/jpoke/handlers/lethal.py:152-155`（アシッドボム）,
`316-319`（オーバーヒート）ほか計8件の `_lower_X`

`lethal.py` 内でランクを下げるハンドラは `オーバーヒート_lower_attacker_spa`（316）,
`サイコブースト_lower_spa`（400）, `フルールカノン_lower_spa`（629）, `りゅうせいぐん_lower_spa`
（721）, `ゴールドラッシュ_lower_spa`（386）, `ばかぢから_lower_atk`（573）,
`ほのおのムチ_lower_def`（654）, `りんごさん_lower_spd`（732）の8件が `_lower_X` 接尾辞を
使っているのに対し、`アシッドボム_reduce_spd`（152-155行目、docstring は他と同じ「とくぼうを
2段階下げる」）だけが `_reduce_spd` を使っている。同種の混在は `field.py` の
`ねばねばネット_reduce_spe`（389-399行目、「素早さランクを1段階下げる」）にも見られ、
4ファイル内では「ランクを下げる」動詞として `lower`（多数派）と `reduce`（少数派2件）が
並立している。`アシッドボム`/`ねばねばネット` を `_lower_X` に揃えることで多数派に統一できる。

### 6. `lethal.py` の `_lower_X` 系で、対象（attacker/defender）を名前に含めるかどうかが不統一

**ファイル**: `src/jpoke/handlers/lethal.py:316`（オーバーヒート）, `523`（テラバースト）,
`400`（サイコブースト）ほか

`オーバーヒート_lower_attacker_spa`（316）と `テラバースト_lower_attacker_atk_spa`（523）は
明示的に `attacker` を名前に含めるが、同じく `ctx.attacker.boosts` を操作する
`サイコブースト_lower_spa`（400）・`フルールカノン_lower_spa`（629）・`りゅうせいぐん_lower_spa`
（721）・`ゴールドラッシュ_lower_spa`（386）は `attacker` を省略している。逆に `ctx.defender`
を操作する `ほのおのムチ_lower_def`（654）・`りんごさん_lower_spd`（732）・`Gのちから_lower_def`
（145）も `defender` を省略しており、「atk/spa低下＝暗黙にattacker、def/spd低下＝暗黙にdefender」
という不文律に依存している。`オーバーヒート`/`テラバースト` だけがこの不文律を破って明示している
理由は特に説明されておらず、8件中2件だけ違うパターンを踏襲する必然性は薄い。

### 7. `lethal.py` の `_apply_X` 系命名で、キラースピン`_apply_どく`/れんごく`_apply_やけど`は対象状態名を明示するが、しおづけ/サイコノイズは汎用語止まり

**ファイル**: `src/jpoke/handlers/lethal.py:355-360`（キラースピン）, `392-397`（サイコノイズ）,
`411-416`（しおづけ）, `751-756`（れんごく）

```python
def キラースピン_apply_どく(battle, ctx, hp_dist):          # 状態異常名を明示
def れんごく_apply_やけど(battle, ctx, hp_dist):            # 状態異常名を明示
def しおづけ_apply_volatile(battle, ctx, hp_dist):          # 汎用語「volatile」のみ
def サイコノイズ_apply_volatile(battle, ctx, hp_dist):      # 汎用語「volatile」のみ
```

`しおづけ_apply_volatile` は自分自身と同名の「しおづけ」揮発状態を付与するため実害は小さいが、
`サイコノイズ_apply_volatile` は技名と異なる**「かいふくふうじ」状態**を付与する（392-397行目、
`ctx.defender.volatiles["かいふくふうじ"] = Volatile("かいふくふうじ", count=2)`）。関数名からは
何の状態が付与されるか一切読み取れず、`キラースピン_apply_どく`/`れんごく_apply_やけど` の
命名方針（付与対象を明示する）と食い違う。`サイコノイズ_apply_かいふくふうじ` のように改名すべき。

### 8. `lethal.py` と `move_attack.py` 間で同一技のハンドラ名が一致せず、`ばかぢから`では実装漏れと直結している

**ファイル**: `src/jpoke/handlers/lethal.py:523-529, 573-576`,
`src/jpoke/handlers/move_attack.py:1821-1824, 2604-2605`

同じ技を実バトル用（`move_attack.py`）とリーサル計算用（`lethal.py`）の2箇所で実装する構成上、
本来なら両ハンドラの対応関係を追いやすい命名が望ましいが、実際には一致していない。

| 技 | `move_attack.py` | `lethal.py` | 実装の一致 |
|---|---|---|---|
| テラバースト | `テラバースト_stellar_stat_drop` | `テラバースト_lower_attacker_atk_spa` | 一致（atk/spa両方） |
| ばかぢから | `ばかぢから_lower_attacker_def`（実際はatk+def両方） | `ばかぢから_lower_atk`（atkのみ） | **不一致（バグ、CRIT-1参照）** |

`テラバースト` は名前こそ違うが実装は一致しており実害はない。しかし `ばかぢから` では
`move_attack.py` 側の関数名自体が「defのみ」と誤解を招く名前（実際はatk+defの両方を変更）に
なっており、`lethal.py` 側はその誤解をそのまま引き継いだ上に「atkのみ」実装してしまったと
見られる。技レビューフローで両ファイルを同時に触る際、`clamp_stats` 呼び出しの引数（stats辞書の
キー集合）を関数名の対象ステータス表記と機械的に突き合わせるチェックを設けることで、同種の
実装漏れを防げる。

### 9. 良い実例: `ailment.py`/`lethal.py` 間でターン終了ダメージハンドラの命名が完全一致している

**ファイル**: `src/jpoke/handlers/ailment.py:84,139,153`, `src/jpoke/handlers/lethal.py:532,680,694`

上記8とは対照的に、`どく_damage`/`もうどく_damage`/`やけど_damage` は `ailment.py`（実バトルの
`ON_TURN_END` ハンドラ）と `lethal.py`（リーサル計算の `ON_TURN_END` ハンドラ）の両方で
一字一句同じ関数名になっている。`バインド_damage`（`volatile.py:1017`, `lethal.py:564`）も同様。
実バトル経路とリーサルシミュレーション経路という別の実行系列に属する関数でも、「同じ技/状態異常が
起点なら同じ関数名を与える」という命名規則が徹底されていれば対応関係を機械的に追跡でき、
CRIT-1のような実装漏れの発見も容易になる。8で指摘した `ばかぢから`/`テラバースト` はこの模範的な
パターンから外れた例外であり、命名規則を「両ファイルで技名を関数名の先頭に置き、可能な限り
同一の効果記述子を使う」と明文化した上で、既存のずれを解消する価値がある。

---

## 総評

一般品質の観点では、前回指摘の `_heal_at_pinch`（過剰設計疑い）は現状維持を確認し、
2026-07-05以降の変更点を精査する過程で `ばかぢから` のリーサル計算バグ（CRIT-1）という
実害のある新規指摘を発見した。このバグは「関数名がぼうぎょ低下の欠落を正直に反映していた」
という点で、命名レビューと品質レビューが独立でなく相互補完的であることを示す実例になった。

命名の一貫性の観点では、単一ファイル内の規律は総じて高い（`volatile.py` の `_tick_volatile`/
`_power_modifier`/`_prevent_X`、`field.py` の `_power_modifier`/`_tick`、`lethal.py` の
`_heal`/`_damage`/`_resist_X` はいずれも高い一貫性を保っている）一方、**ファイル境界をまたぐ
概念の命名は体系的に揃っていない**。具体的には (a) `field.py`⇔`volatile.py` 間の
`ON_CHECK_FLOATING` ハンドラ（`_grounded` vs `_check_floating`）、(b) `field.py`⇔`volatile.py`
間の `disabled_reason` ライフサイクル管理（`_apply`/`_remove` vs `_disable_ability`/
`_enable_ability`）、(c) `lethal.py`⇔`move_attack.py` 間の同一技ハンドラ（`ばかぢから`/
`テラバースト`）という3種類の「同一概念・異なる語彙」パターンが見つかった。(c) は実際の
バグと直結した一方、(a)(b) は現時点で実害のない可読性上の指摘にとどまる。`ailment.py`⇔
`lethal.py` 間の状態異常ダメージハンドラ（どく/もうどく/やけど）は逆に模範的な統一例であり、
この命名規則（技名/状態名を関数名の先頭に置き、実行経路が違っても同じ効果記述子を使う）を
プロジェクト全体の慣習として明文化する価値がある。

`ailment.py` 内の `_action`/`_check_action` 分裂（命名1）と `volatile.py` 内の「解除」接尾辞
5分裂（命名2）は、いずれもファイル内で完結する指摘でありながら、docstringが完全一致するほど
同一の役割を持つ関数群に異なる名前が付いているという点で、命名レビューの新規観点として
もっとも明確な実例だった。
