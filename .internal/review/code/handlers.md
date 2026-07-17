# コードレビュー — handlers/

日付: 2026-07-05
対象: `src/jpoke/handlers/`
（`ability.py`, `ability_paradox.py`, `ailment.py`, `field.py`, `item.py`, `lethal.py`,
`move.py`, `move_attack.py`, `move_status.py`, `volatile.py`）
観点: 責務分離、内部実装の隠蔽、拡張性、過剰設計

---

## 総論

`handlers/` は約1,300関数（`ability.py` 350、`move_attack.py` 398、`move_status.py` 227、
`item.py` 212、`volatile.py` 118、他）からなる、このプロジェクトで最も件数の多いレイヤーである。
それにもかかわらず全体の一貫性は高い。特に `item.py`・`lethal.py` は「1効果1関数」を保ちながら
`_modify_power_by_type` / `_dedicated_item_modify_power` / `_heal_berry` / `_type_resist_berry` /
`_boost_on_quarter_hp` / `_boost_on_attack_category` / `_retaliate_on_category` のような
共通ヘルパーへ正しく分解されており、17種のタイプ半減きのみや専用道具群がほぼ1行の委譲で
実装されている。責務分離の観点では模範的な部類。

一方で、同日実施の `.internal/review/code/architecture_review.md`（以下「既存レビュー」）が
指摘した問題のうち `ability.py` の `id()` キー・グローバル辞書（CRIT-1）、Handler
ラッパークラスの不統一（ISSUE-15）、非公開ヘルパーの前方参照（ISSUE-16）、
`Field` 型の未インポート（ISSUE-17）、`うそなき` の命名ミス（ISSUE-18）、
`のみこむ`/`はきだす` の重複（ISSUE-19）は、実際にコードを読み直した結果すべて**現存を確認**した。
特に ISSUE-16 は `ability.py` にも既存レビュー未記載の追加事例があり、ISSUE-19 は
既存レビューが指摘した箇所以外にもう1組の重複関数がある。過剰設計の観点では、
カテゴリ別 `Handler` ラッパークラスがポリモーフィズムのために使われている形跡が
コードベース全体を通じて一切ない（`isinstance` によるハンドラ種別分岐はゼロ件）ことを
確認し、単なるコンストラクタの糖衣構文としてクラス化されている点を新たに指摘する。
また `handlers/lethal.py` の `_heal_at_pinch` は「特性由来の回復」を扱えるよう
汎用化されているが、実際の7箇所の呼び出しは全てアイテム由来の分岐のみを使っており、
特性側の分岐は現状デッドコードであることも確認した。

---

## 重大な指摘

### CRIT-1: `id(mon)` をキーにしたモジュールグローバル辞書による一時状態の受け渡し（既存・現存確認）

**ファイル**: `src/jpoke/handlers/ability.py:70`（`_メガソーラー_saved` 宣言）、
`:3083`（保存）、`:3099-3105`（`メガソーラー_deactivate` での早期リターンとpop）、
`:2019`（`_とびだすなかみ_hp_before` 宣言）、`:2011`（`とびだすなかみ_retaliate_on_ko` での参照。
辞書宣言より8行前に出現する前方参照）、`:2024`（`とびだすなかみ_save_hp` での書き込み）

```python
# handlers/ability.py:70
_メガソーラー_saved: dict[int, tuple[str, int]] = {}
...
# :3099
def メガソーラー_deactivate(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    mon = ctx.attacker
    if mon.ability.state != "active":
        return HandlerReturn(value=value)     # ← ここで早期リターンすると pop されない
    wm = battle.weather_manager
    saved = _メガソーラー_saved.pop(id(mon), None)
```

既存レビュー（CRIT-1）が指摘した通り、`Battle` は観測構築・致死率計算・盤面コピーで
deepcopy を多用する設計であり、`id()` は GC 後に再利用されうるため本質的に危険。
今回あらためて読み直して分かった点として、`メガソーラー_activate` はすでに
`mon.ability.state = "active"` という**インスタンス属性**で有効フラグを管理しており
（3095行目）、"技実行中だけ有効な一時状態をどこに置くか" という問題を半分は
正しく解決している。にもかかわらず、状態と対になっている `_メガソーラー_saved` の
実データ（保存前の天候名・はれカウント）だけがグローバル辞書に取り残されており、
一貫性がない。`mon.ability` 側に `saved_weather: tuple[str, int] | None` の
ようなフィールドを1つ追加するだけで、`id()` を経由せず deepcopy にも自然に追従する
実装に揃えられる。`とびだすなかみ_hp_before` も同様に `ctx.substitute_damage` の
ように `AttackContext` へフィールド化するか、`Pokemon` 側の一時属性にすべき。

**参考（悪い例との対比）**: `handlers/item.py:557,565` の `かいがらのすず_drain_on_hit` は
`ctx._shell_bell_total_damage` という動的属性を `AttackContext`（`@dataclass` で
`slots` 未指定のため代入自体は可能）に生やして連続技の合計ダメージを持ち越しており、
`id()` キー辞書よりは安全な代替になっている。ただし `AttackContext` の宣言済み
フィールドとして定義されていないため、`getattr(ctx, "_shell_bell_total_damage", 0)`
のような防御的アクセスが必要になっており（579行目）、型チェッカからも見えない。
CRIT-1 の是正時はこの動的属性方式ではなく、`AttackContext` に正式なフィールドとして
追加する形を推奨する。

---

## 中程度の指摘

### ISSUE-7: `ability.py:491` が `ctx.critical` ではなく `battle.move_executor.critical` を直接参照（既存・現存確認）

```python
def いかりのつぼ_max_atk_on_crit(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """いかりのつぼ特性: 急所に被弾したときこうげきを最大まで上げる。"""
    if not battle.move_executor.critical:
        return HandlerReturn(value=value)
```

`field.py` の `オーロラベール_reduce_damage`（145行目）・`ひかりのかべ_reduce_damage`（420行目）・
`リフレクター_reduce_damage`（561行目）はいずれも `ctx.critical` を参照しており、
`ability.py` だけ `battle.move_executor.critical` という別経路を使っている。
`AttackContext.critical` フィールド（`core/context.py:85`）が実質的に分裂した参照経路を
持っている実例であり、`ctx` を経由しない理由がコード上どこにも説明されていない。

### ISSUE-15: カテゴリ別 `Handler` ラッパークラスが基底のフィールドを各自の判断で選んで公開しており統一APIになっていない（既存・現存確認）

**現在のコンストラクタ引数**:
- `ability.py:72-84` `AbilityHandler(func, subject_spec, priority=100, once=False)` — `once` のみ追加公開
- `item.py:30-44` `ItemHandler(func, subject_spec, priority=100, once=False, ignored_disable_reasons=frozenset())` — 両方公開
- `move.py:16-39` `MoveHandler(func, subject_spec="attacker:self", priority=100)` — どちらも非公開。かわりに `skip_subject_check=True` を常時固定
- `ailment.py:12-22` `AilmentHandler(func, subject_spec, priority=100)` — どちらも非公開
- `volatile.py:24-36` `VolatileHandler(func, subject_spec="source:self", priority=100, once=False)` — `once` のみ
- `field.py:11-21` `FieldHandler(func, subject_spec, priority=100)` — どちらも非公開

基底 `Handler`（`core/handler.py:44-52`）が持つ `once` / `skip_subject_check` /
`ignored_disable_reasons` のうち、どれを各カテゴリのコンストラクタで露出するかが
場当たり的に決まっている。今回 `data/item.py` を grep したところ `ignored_disable_reasons`
の実使用は1件のみ（`ItemHandler` 経由でしか設定できない）であり、この引数自体は
必要だが、他カテゴリで同種の要件が出た場合にコンストラクタ側の追随を忘れるリスクがある。
`MoveHandler` が `skip_subject_check=True` を常時固定している設計はコメント1行のみで、
なぜ技ハンドラだけこの挙動が必要なのかがモジュールdocstringに説明されていない。

### ISSUE-16: 複数箇所から再利用される非公開ヘルパーが定義位置より数百行前方から呼ばれている（既存・現存確認 + 新規追加事例）

**既存レビュー記載分（現存確認）**:
- `handlers/move_attack.py:716`（`_recoil`）。初出は149行目 `アフロブレイク_recoil` で
  定義より567行前方。他12箇所以上から使用。
- `handlers/move_attack.py:709`（`_drain_hp`）。10箇所以上から使用。
- `handlers/volatile.py:966`（`_run_protect`）/`:958`（`_check_protect_success`）。
  初出は319行目 `かえんのまもり_protect` で定義より約650行前方。他6箇所から使用
  （まもる・トーチカ・キングシールド・スレッドトラップ・ニードルガード・ファストガード）。

**今回新たに確認した `ability.py` 内の同種の事例（既存レビュー未記載）**:
`_overwrite_ability_on_contact`（`ability.py:2982-2999`）は「直接攻撃を受けたとき
攻撃者の特性を書き換える」共通処理だが、初出は `とれないにおい_overwrite_attacker_ability`
（`ability.py:2044-2050`）であり、定義より**936行前方**で呼ばれている。もう1箇所の
利用先である `ミイラ_overwrite_attacker_ability`（3002-3006行）は定義の直後にあるため
気付きにくく、`とれないにおい` 側から辿ろうとすると3000行近くファイルを下る必要がある。

いずれもモジュール冒頭の docstring が謳う「関数定義は五十音順に配置」規約から外れた
Pythonの遅延バインディングへの依存であり、実害はないが検索コストが高い。各ファイル
先頭の共有ユーティリティ節（`ability.py` なら86-312行目の非公開ヘルパー群）に
まとめて移動するか、最低限モジュールdocstringに「複数特性/技から呼ばれる共通処理は
ファイル末尾/先頭にまとめる」旨を明記すべき。

### ISSUE-17: `handlers/field.py` で未インポートの `Field` 型がシグネチャに使われている（既存・現存確認）

**ファイル**: `src/jpoke/handlers/field.py:362, 385, 524`

```python
def ねがいごと_heal(battle: Battle, ctx: EventContext, value: Field) -> HandlerReturn:
def はめつのねがい_damage(battle: Battle, ctx: EventContext, value: Field) -> HandlerReturn:
def みらいよち_damage(battle: Battle, ctx: EventContext, value: Field) -> HandlerReturn:
```

`field.py` の import 文（1-9行目）に `Field` は含まれない。`from __future__ import
annotations` により実行時エラーにはならないが、静的型チェッカは未定義名として検出する。
同ファイルの他59個のハンドラは全て `value: Any` であり、この3箇所だけ型注釈が浮いている。

### ISSUE-18: `うそなき_reduce_defender_spe`（move_status.py:269）の関数名が実装と食い違っている（既存・現存確認）

```python
def うそなき_reduce_defender_spe(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"spd": -2})
```

直前の `いとをはく_reduce_defender_spe`（205行目、実際に `stats={"spe": -1}`）との
並びから、このファイルの `_spe` サフィックスは「すばやさを操作する」という意味で
統一されている。うそなき自体の効果（とくぼう2段階ダウン）は正しいが、関数名だけが
すばやさ操作を示唆しており、命名規則を信頼した保守者を誤読させる。

### ISSUE-19: たくわえるカウントの巻き戻し処理の重複が、既存レビュー記載よりもう1組多い（既存・拡張確認）

既存レビューは `のみこむ_apply`（`move_status.py:1318-1329`）と `はきだす_apply_after`
（1421-1428）の「ランク巻き戻し3行」の重複のみを指摘していたが、実際には
使用可否チェック関数もほぼ丸ごと重複している。

```python
# 1332-1344
def のみこむ_check_can_use(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    mon = ctx.attacker
    if (
        not mon.has_volatile("たくわえる")
        or mon.volatiles["たくわえる"].count == 0
    ):
        battle.add_event_log(mon, LogCode.MOVE_FAILED, payload={"reason": "のみこむ"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)

# 1431-1443（reasonの文字列以外は完全に同一のロジック）
def はきだす_check_can_use(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    mon = ctx.attacker
    if (
        not mon.has_volatile("たくわえる")
        or mon.volatiles["たくわえる"].count == 0
    ):
        battle.add_event_log(mon, LogCode.MOVE_FAILED, payload={"reason": "はきだす"})
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)
```

`のみこむ`/`はきだす` は「たくわえるの蓄積を消費する」という同一の前提条件・
巻き戻し処理を持つ技であり、`_check_can_use_stockpile(battle, mon, move_name) ->
HandlerReturn` と `_release_stockpile(battle, mon) -> int` のような共有ヘルパー2つに
統合すれば、重複4関数・約35行を実質2ヘルパー+2薄いラッパーへ縮小できる。

---

## 過剰設計の観点

（既存レビューが薄い観点のため重点的に調査した。結論として `handlers/` 全体では
過剰設計は限定的だが、以下2点は実際のコードで確認できた具体的な指摘である。）

### OVER-1: カテゴリ別 `Handler` サブクラス（6個）はポリモーフィズムとして使われておらず、単なる `source=` 固定のための継承

`AbilityHandler` / `ItemHandler` / `MoveHandler` / `AilmentHandler` / `VolatileHandler` /
`FieldHandler` の6クラス（前掲ISSUE-15参照）はいずれも `Handler.__init__` を呼ぶだけの
薄いラッパーである。プロジェクト全体（`src/jpoke/` 配下）を `isinstance(...,
XxxHandler)` で検索したが**該当箇所はゼロ件**だった。つまりこれらのクラスは
「ハンドラの種類によって振る舞いを分岐する」という継承本来の目的では一度も使われて
おらず、`data/*.py` の登録コードで `source="ability"` を毎回書く手間を省くためだけに
存在している。

この目的であれば、クラス階層である必要はなく

```python
def ability_handler(func, subject_spec, priority=100, once=False) -> Handler:
    return Handler(func=func, source="ability", subject_spec=subject_spec,
                   priority=priority, once=once)
```

のような1行のファクトリ関数で同じ利便性を得られる。現状は「基底 `Handler`
にフィールドが増えるたびに6クラスのコンストラクタ引数を個別に見直す」という
保守コストを継承のために払っており（実際に ISSUE-15 の露出不統一という形で
コストが表面化している）、その見返りとして得ている恩恵（ポリモーフィズム）は
実質ゼロである。ラッパークラスをファクトリ関数に置き換えれば、ISSUE-15 の
不統一自体も自然に解消される（引数を都度指定すれば良いだけになる）。

### OVER-2: `lethal.py` の `_heal_at_pinch` は特性分岐を汎用化しているが、現状の7呼び出しは全てアイテム分岐のみを使用

**ファイル**: `src/jpoke/handlers/lethal.py:45-95`

```python
def _heal_at_pinch(hp_dist: StateDist, target: Pokemon, v: int = 0, r: float = 0.,
                   threshold_rate: float = 0,
                   heal_with: Literal["ability", "item"] | None = None,
                   consume: bool = True) -> StateDist:
    ...
    for state, freq in hp_dist.items():
        if heal_with == "ability" and not state.ability_enabled:
            new_dist[state] += freq
            continue
        if heal_with == "item" and not state.item_enabled:
            new_dist[state] += freq
            continue
        ...
        keep_ability_enabled = not (heal_with == "ability" and consume)
        keep_item_enabled = not (heal_with == "item" and consume)
```

実際の呼び出し（イアのみ・ウイのみ・オボンのみ・オレンのみ・バンジのみ・フィラのみ・
マゴのみ、計7箇所、200/246/276/305/558/568/599行目）は**全て**
`heal_with="item", consume=True` で固定されている。`heal_with == "ability"` の分岐と
`consume=False` の分岐（`keep_ability_enabled`/`keep_item_enabled` を意図的に
`True` のまま残すケース）は現状デッドコードであり、対応する「特性由来の閾値回復」
（例えば理論上の「ポイズンヒールのような1/4回復特性」）は `handlers/lethal.py` 内に
存在しない（`ポイズンヒール_heal` は無条件回復のため別実装、590-594行目）。

対になる `_survive_at_full_hp`（104-122行目）は `consume: Literal["ability",
"item"]` を必須引数にしており、実際に `がんじょう_survive_lethal`（consume="ability"、
334行目）と `きあいのタスキ_survive_ohko`（consume="item"、344行目）の両方が
使われている。この対比から、`_heal_at_pinch` の作者は同じパターンを踏襲して
将来の特性追加に備えたと推測できるが、7/7の呼び出しが同じ分岐しか使わない現状では
早すぎる一般化（YAGNI違反）と言える。実害はない（未使用分岐がバグを埋め込む余地は
小さい）が、将来 `heal_with="ability"` の特性を追加する際に「本当にこの分岐が
このケースに合っているか」を7つの既存呼び出しでは検証できていない、というテスト
カバレッジの死角を生んでいる点は留意すべき。

### 検証したが過剰設計ではなかった例（参考）

- `handlers/volatile.py:966` の `_run_protect`（`stats_change_on_contact` /
  `ailment_on_contact` / `chip_on_contact` / `protect_non_attack` の4オプション）は
  7つの protect 系技（まもる・トーチカ・キングシールド・スレッドトラップ・
  かえんのまもり・ニードルガード・ファストガード）それぞれが異なる部分集合を
  実際に使っており、汎用化は妥当。
- `handlers/item.py` の `_dedicated_item_modify_power` / `_dedicated_item_form_change` /
  `_dedicated_item_prevent_item_change` / `_dedicated_item_prevent_transfer_to_base_form`
  は御三家伝説（ディアルガ/パルキア/ギラティナ、通常・オリジン・アナザー計）の
  専用道具6種以上で実際に共有されており妥当。
- `handlers/core.BaseContext.derive()`（`core/context.py:27-37`、`dataclasses.fields`
  を使った汎用フィールドコピー）は `handlers/` 内では
  `やどりぎのタネ_drain_hp`（`volatile.py:1229`）の1箇所でしか呼ばれておらず一見
  過剰に見えるが、`context.py` は `core/` の管轄でありこのレビュー対象外の
  呼び出し元（`move_executor.py` 等）が他にある可能性が高いため、`handlers/`
  だけを見て過剰設計と断定するのは早計と判断し参考記載に留める。

---

## 軽微な指摘

### MINOR-1: `handlers/item.py:86-96` の `mega_modify_command_options` がリストを走査しながら自身に追加している（既存・現存確認）

```python
def mega_modify_command_options(battle: Battle, ctx: EventContext, value: list[Command]) -> HandlerReturn:
    mon = ctx.source
    if not mon.can_megaevolve():
        return HandlerReturn(value=value)
    for cmd in value:
        if cmd.is_regular_move:
            value.append(Command.get_megaevol_command(cmd.index))
    return HandlerReturn(value=value)
```

現状は追加される `MEGAEVOL_x` コマンドが `is_regular_move` を満たさないため
無限ループにはならないが、"走査対象へ書き込みながら走査する" 構造自体が
わかりにくく壊れやすい。`for cmd in list(value):` として走査対象をスナップショット
化するか、`value + [新規コマンド...]` の形で新しいリストを作るべき。

### MINOR-11: `ability_paradox.py` の関数命名が `ability.py` の「特性名_動作」規約から外れている（既存・現存確認）

**ファイル**: `src/jpoke/handlers/ability_paradox.py:51, 98, 106, 126`

`refresh_paradox_charge_state` / `modify_speed` / `apply_atk_modifier` /
`apply_def_modifier` は英語の汎用名。こだいかっせい・クォークチャージの2特性を
1モジュールで共通処理する意図的設計と見え実害は小さいが、単純な特性名 grep
（例: `こだいかっせい_`）ではヒットしない。モジュールdocstring（1行目）は
「パラドックス特性専用ハンドラー」とだけ書かれており、命名方針までは
明記されていない。

### MINOR-12: `move_status.py`/`move_attack.py`/`ability.py` 先頭の共有ユーティリティが英語名で「五十音順」注記の例外になっている（既存・現存確認 + `ability.py` 追加）

**ファイル**: `move_status.py:42-69`（`on_blow_apply`, `blow`）、
`move_attack.py:26-50`（`pivot`, `ohko_damage`, `half_damage`）、
`ability.py:86-313`（`announce_ability_triggered` ほか非公開ヘルパー群）

いずれも定義位置がファイル冒頭で発見しやすいため実害は小さい。`ability.py` は
モジュールdocstringが「五十音順に配置」とだけ書いており、`move_attack.py`/
`move_status.py` と異なり「共有ユーティリティは先頭にまとめる」という運用が
明文化されていない点は3ファイルで足並みを揃えると良い。

### MINOR-13: `prevent_poison_ailment` 等5つの状態異常無効化ヘルパー（`ability.py:1052-1065`）が英語の汎用名で特性名プレフィックスを持たない

```python
def prevent_poison_ailment(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _prevent_ailment(battle, ctx, value, blocked_ailments=["どく", "もうどく"])
def prevent_paralysis_ailment(...): ...
def prevent_burn_ailment(...): ...
def prevent_sleep_ailment(...): ...
def prevent_freeze_ailment(...): ...
```

`data/ability.py` を確認したところ、それぞれ2〜3特性から `h.prevent_paralysis_ailment`
のように参照されており（例: 1156, 1237, 1995, 2283, 2556, 2808, 2909, 3004, 3070行目）
複数特性で共有される正当なヘルパーであることは確認できた。ただし
`きよめのしお_prevent_ailment`（1068行目、こちらは特性名プレフィックスあり）と
並んでいるため、複数特性で共有される関数だけが命名規則の例外になっている状態が
やや目立つ。MINOR-11/12と同種の「意図的だが未文書化な命名例外」であり、
まとめて対応する価値がある。

---

## 総評

`handlers/` は件数の多さの割に規律が保たれており、既存レビューが `handlers/` の
「残り」を「健全」と評価した判断は概ね妥当。ただし `ability.py` の CRIT-1（`id()`
キー辞書）は今回のコード確認でも解消されておらず最優先。ISSUE-15（Handlerラッパー
クラスの不統一）は、そもそも継承である必要がない（OVER-1）という根本原因に
遡ることができ、ラッパーをファクトリ関数へ置き換える1回のリファクタリングで
ISSUE-15とOVER-1の両方が解消できる。ISSUE-19（のみこむ/はきだすの重複）は
既存レビューの記載よりも実際の重複範囲が広いため、修正時は使用可否チェックまで
含めて統合すべき。過剰設計の観点では `_heal_at_pinch`（OVER-2）のような
「使われていない汎用性」が1件見つかったが、`_run_protect` や `item.py` の
専用道具ヘルパー群のように汎用化が実際の再利用で正当化されている例の方が多く、
`handlers/` 全体としては過剰設計より「共有すべきなのに未共有」（ISSUE-16,
ISSUE-19）の方が支配的な傾向である。
