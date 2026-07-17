# コードレビュー — handlers/move（攻撃技・変化技ハンドラ）

日付: 2026-07-12
対象:
`src/jpoke/handlers/move_attack.py`（3665行）、
`src/jpoke/handlers/move_status.py`（3046行）、
`src/jpoke/handlers/move.py`（197行）
観点:
1. 一般的な品質観点（前回指摘の現状確認、`move.py` の直近変更、責務分離・重複、過剰設計、実害あるバグの可能性）
2. 関数・変数名の一貫性と妥当性（技名→関数名の変換規則、攻撃技/変化技間での命名パターンの整合、attacker/defender/user/target等の使い分け、ローカル変数名の妥当性）

前回の総合レビュー（`.internal/review/code/index.md`、2026-07-05付）は `handlers/` 全体を
1ファイル（[handlers.md](handlers.md)）でまとめており、`move_attack.py`/`move_status.py`は
`_recoil`/`_drain_hp`の前方参照（ISSUE-16）と`うそなき`の命名ミス（ISSUE-18）、
のみこむ/はきだすの重複（ISSUE-19）のみが個別言及されていた。本レビューは両ファイルを
全文精読し、特に命名の一貫性を新規の主眼として調査した。

---

## 総論

`move_attack.py`・`move_status.py`はいずれも「1技=1関数」を基本単位とし、
`modify_attacker_stats`/`modify_defender_stats`/`apply_ailment_to_defender`/
`apply_volatile_to_attacker`/`apply_volatile_to_defender`/`apply_confusion_to_defender`という
`handlers/move.py`共通ヘルパー群への薄い委譲がほとんどを占める。約630関数（`move_attack.py`
約400、`move_status.py`約230）の規模の割に、個々の関数は短く見通しが良い。

最重要の確認事項である**前回`model.md CRIT-1`（`handlers/move_status.py`が`Pokemon`の
非公開属性`_stats_manager`を直接書き換えている問題）は、2026-07-11のコミット
`1df19540`「refactor: PokemonStatsクラスを廃止しPokemonに統合」で解消済みであることを
確認した**。`PokemonStats`クラス自体が廃止されて`Pokemon`に統合され、ガードシェア・
スピードスワップ・パワーシェア・パワートリックの4関数（`move_status.py:657, 1274, 2355, 2382`）は
現在すべて`Pokemon.get_raw_stat(idx)`/`Pokemon.set_raw_stat(idx, value)`という公開APIを
経由している（`model/pokemon.py:689-704`、`set_raw_stat`のdocstringに
「ガードシェア・パワーシェア・パワートリック・スピードスワップなど、努力値の再計算を
伴わずに実数値そのものを操作する専用効果でのみ使用する」と明記）。カプセル化違反は
解消済みであり、対応する`.internal/review/code/model.md`のCRIT-1記載は現状と乖離しているため
別途更新が望ましい（本タスクの範囲外につき本ファイルでは指摘に留める）。

`git log --since=2026-07-05 -- src/jpoke/handlers/move.py`で確認した唯一の変更
（コミット`841a8e31`「fix: 半透明技の2ターン目がわるあがきにすり替わるバグを修正」、
`charge_into_volatile`関数、`move.py:173-197`）は、`battle.volatile_manager.apply`に
`move_name=ctx.move.name`を明示的に渡すよう修正するもので、コメントも含めて意図が
明確であり問題は見当たらない。

責務分離の観点では、`move_attack.py`の`_recoil`/`_drain_hp`/`_force_switch_random`/
`_is_sheer_force_blocked`/`_clear_spin_effects`のように、実際に複数技から呼ばれる処理は
アンダースコア接頭辞付きの非公開ヘルパーへ正しく括り出されている。一方で
「こおりの解凍」（`_thaw_attacker`系、11関数）のように、複数技にまたがって同一の
本体・docstringがそのままコピーされているにもかかわらずヘルパー化されていない例も
見つかった（後述ISSUE-3）。

過剰設計は本2ファイルでは限定的である。`ソーラービーム系_charge`/`weather_skip`
（呼び出し元2技: ソーラービーム/ソーラーブレード）は今後も同系統技が増えにくいため
早すぎる一般化とまでは言えず、既存レビューが指摘した`_run_protect`（`handlers/volatile.py`）や
`_heal_at_pinch`（`handlers/lethal.py`）ほど疑わしい汎用化は見当たらなかった。

今回の主目的である命名の一貫性については、**`move_attack.py`と`move_status.py`が
「能力ランク変化」という同一カテゴリの効果に対して系統的に異なる命名規則を採用している**
ことが最大の発見であり、詳細は末尾の「命名の一貫性・妥当性」節にまとめる。

---

## 重大な指摘

今回の精読では、ゲームロジックに実害を及ぼす明確なバグは見つからなかった。
前回指摘のCRIT-1（`_stats_manager`直接アクセス）は上記の通り解消済みであるため、
このカテゴリに新規記載する項目はない。

---

## 中程度の指摘

### ISSUE-1: `move_attack.py:1706-1707` `ダイヤストーム_sharply_boost_defender_B` の関数名が実装と矛盾している

```python
def ダイヤストーム_sharply_boost_defender_B(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_attacker_stats(battle, ctx, value, stats={"def": 2}, chance=0.5)
```

関数名は「defender（相手）のぼうぎょを上げる」ことを示唆しているが、実装は
`modify_attacker_stats`を呼んでおり、実際に上がるのは**使用者自身（attacker）**の
ぼうぎょである（ダイヤストームの実際の効果＝自分のぼうぎょ50%上昇、と一致）。
効果自体は正しいが、関数名だけが逆を指しており、前回`handlers.md`ISSUE-18で
指摘された`うそなき`（現在は`うそなき_modify_defender_stats`に改名され解消済み、
`move_status.py:401`）と同種の「命名規則を信頼した保守者を誤読させる」バグである。
同じ`_B`サフィックスを使う`はがねのつばさ_boost_attacker_B`（`move_attack.py:2409`）・
`バリアーラッシュ_boost_attacker_B`（`move_attack.py:2617`）は正しく`attacker`を
名乗っており、本関数だけが逆転している。`ダイヤストーム_sharply_boost_attacker_B`への
改名を推奨する。

### ISSUE-2: `move_status.py:498-502` `おきみやげ_apply` が `modify_defender_stats` の戻り値を捨てている

```python
def おきみやげ_apply(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """おきみやげ: 使用者をひんしにし、相手のこうげき・とくこうを2段階ずつ下げる。"""
    battle.faint(ctx.attacker)
    modify_defender_stats(battle, ctx, value, stats={"atk": -2, "spa": -2})
    return HandlerReturn(value=value)
```

`handlers/move.py`の`modify_defender_stats`のdocstringは「ON_STATUS_HIT（value=bool）では
ランク変化が完全に阻まれた場合に技を失敗させるため、`battle.modify_stats()`の戻り値を
valueとして返す」と明記しており、実際に`みをけずる_apply`（`move_status.py:2892-2895`）は

```python
result = modify_attacker_stats(battle, ctx, value, stats={"atk": 2, "spa": 2, "spe": 2})
if result.value:
    battle.modify_hp(ctx.attacker, r=-0.5)
return result
```

のように戻り値`result`を捕捉し、それを最終的な`HandlerReturn`として返している。
`おきみやげ_apply`は`modify_defender_stats(...)`の呼び出し結果を変数に代入せず、
副作用（実際のランク変化）だけを起こして捨てており、常に元の`value`（True想定）を
返している。ゲーム仕様上「おきみやげは相手の特性等でランク変化が完全にブロックされても
使用者は必ずひんしになる」という点では現状の挙動（常に成功扱い）は結果的に妥当である
可能性が高いが、その意図がコード上どこにも説明されておらず、`modify_defender_stats`の
戻り値を捨てる書き方が偶然の産物なのか意図的なのか判別できない。少なくとも
「ランク変化が完全ブロックされても技自体は成功する」という一次情報根拠をコメントに
追記するか、`みをけずる_apply`と同様に戻り値を明示的に扱う書き方に揃えるべき。

### ISSUE-3: `move_attack.py` で「こおりの解凍」ロジックが11関数に一字一句コピーされている

**ファイル**: `move_attack.py:549`（かえんぐるま）, `574`（かえんボール）,
`1020`（クロスフレイム）, `1350`（シャカシャカほう）, `1492`（スチームバースト）,
`1541`（せいなるほのお）, `2324`（ねっさのだいち）, `2341`（ねっとう）,
`2392`（ハイドロスチーム）, `2885`（フレアドライブ）, `3410`（もえつきる）

11関数すべてが次の同一本体・同一docstringを持つ。

```python
def <技名>_thaw_attacker(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """<技名>: こおり状態でも使用可能にし、こおりを解凍する。

    こおり_action (priority=10) より先に発火させる (priority=5) ことで、
    ailment が除去された状態で こおり_action の validity check が走り、
    こおり_action がスキップされる。
    """
    mon = ctx.attacker
    if mon.ailment.name == "こおり":
        battle.ailment_manager.remove(mon)
    return HandlerReturn(value=value)
```

同じファイル内の`_recoil`（149行目初出、`move_attack.py:880`定義）や`_drain_hp`
（`move_attack.py:869`定義）は複数技から呼ばれる共通処理として正しく非公開ヘルパー化
されているのに対し、この「こおり解凍」ロジックだけは11箇所にそのままコピーされている。
`_thaw_attacker(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn`という
共通ヘルパーを追加し、11関数を1行の委譲に置き換えれば、約100行の重複を解消できる
（`data/moves/*.py`側の登録名は変更不要）。実害はないが、priorityに関する説明コメントが
11箇所で同時にドリフトするリスクを抱えている。

### ISSUE-4: `move_status.py:214-227` `アロマセラピー_cure_team_ailment` と `342-356` `いやしのすず_cure_ailment` が実装重複かつ命名も不揃い

```python
# アロマセラピー（214-227行目）
def アロマセラピー_cure_team_ailment(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    mon = ctx.attacker
    player = battle.get_player(mon)
    state = battle.player_states[player]
    targets = [m for m in state.selection if m.ailment.is_active]
    if not targets:
        return HandlerReturn(value=False, stop_event=True)
    for target in targets:
        battle.ailment_manager.remove(target)
    return HandlerReturn(value=value)

# いやしのすず（342-356行目、docstringのみ「音技のためみがわり貫通」の言及が増えるが本体は同一）
def いやしのすず_cure_ailment(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    mon = ctx.attacker
    player = battle.get_player(mon)
    state = battle.player_states[player]
    targets = [m for m in state.selection if m.ailment.is_active]
    ...（以下同一）
```

どちらも「選出チーム全体の状態異常を回復する」という同一効果で、コード本体も
完全に一致している。にもかかわらず関数名の末尾が`cure_team_ailment`と`cure_ailment`で
異なっており、「チーム全体」という同じ対象範囲を示す語が一方にしかない。共有ヘルパー
`_cure_team_ailment(battle, mon)`へ統合し、命名も統一することを推奨する。

---

## 過剰設計の疑い

今回の2ファイルでは、前回`handlers.md`が指摘したような「使われていない汎用性」の
明確な事例は見つからなかった。`ソーラービーム系_charge`/`ソーラービーム系_weather_skip`
（`move_attack.py:1603-1637`、呼び出し元はソーラービーム/ソーラーブレードの2技）は
汎用化のコストに対して再利用が最小限（2技）だが、同系統の新技が今後追加されうる
（実際にゲーム内には他の「ためターン技」が多数存在する）ため、時期尚早と断定するには
根拠が弱く、参考記載に留める。

---

## 軽微な指摘

### MINOR-1: 命中率・回避率変更の略称が「acc」と「accuracy」で不統一

**ファイル**: `move_attack.py:1710`（だくりゅう_lower_acc）, `2064`（どろかけ_lower_acc）,
`2068`（どろばくだん_lower_acc）, `2078`（ナイトバースト_lower_acc）,
`3238`（ミラーショット_lower_acc）

いずれも`modify_defender_stats(..., stats={"accuracy": -1})`を呼んでおり、実際の
辞書キーは`"accuracy"`（省略なしのフルスペル）だが、関数名では`acc`と3文字に
省略されている。他のステータス（atk/def/spa/spd/spe）は辞書キーと関数名中の略称が
完全一致しているのに対し、命中率だけは関数名と実装中のキー文字列が異なる。
`_lower_defender_accuracy`のようにキーとの対応を保つか、省略記法自体を許容するなら
その旨をモジュールdocstringに明記すべき。

### MINOR-2: `move_attack.py:2476` `level_fixed_damage` と `2480` `apply_bind_to_defender` が非公開ヘルパーの慣例（アンダースコア接頭辞）から外れている

両関数は`data/moves/move_na.py`・`move_ta.py`（`level_fixed_damage`）、
`move_ha.py`・`move_a.py`・`move_ma.py`（×3）・`move_ta.py`・`move_sa.py`（×3）
（`apply_bind_to_defender`）という複数技データから直接参照される共有ハンドラであり、
`_recoil`/`_drain_hp`/`_force_switch_random`などと同じ「複数技共有ヘルパー」の
位置づけである。しかし後者群がアンダースコア接頭辞で「モジュール内非公開」であることを
明示しているのに対し、この2関数は接頭辞なしの英語名で、五十音順配置の慣例上も
「はきだす」と「はたきおとす」の間という一見関係のない位置に置かれている
（技名を持たない共有ヘルパーの配置基準は`.internal/review/code/data_moves.md` ISSUE-3でも
指摘されており、本レビューでは特に「アンダースコア接頭辞の有無」という観点を追加する）。
`data/*.py`から直接参照されるため`_`接頭辞を付けると呼び出し側の可読性が落ちる
トレードオフはあるが、`on_blow_apply`/`blow`（`move_status.py:101, 128`）などファイル冒頭の
共有ユーティリティ群と同じ並びに移動するだけでも発見しやすさは改善する。

---

## 命名の一貫性・妥当性

### 1. 【最重要】能力ランク変化ハンドラの命名規則が move_attack.py と move_status.py で系統的に異なる

`move_attack.py`は能力ランク変化技を一貫して「`<技名>_<方向>_<主体>_<略称ステータス名>`」
という具体的な命名で表現する。

```
アイスハンマー_lower_attacker_spe
オーバーヒート_lower_attacker_spa
エナジーボール_lower_defender_spd
とびかかる_lower_defender_atk
くさわけ_boost_attacker_spe
```

`grep`で確認したところ、この`_lower_<attacker|defender>_<stat>`/`_boost_<attacker|defender>_<stat>`
系の命名は`move_attack.py`内に66件存在する。

一方`move_status.py`では、同じ「単一・固定内容の能力ランク変化」を表す関数の**50件**が、
呼び出しているヘルパー関数名をそのまま関数名に転記した`<技名>_modify_defender_stats`/
`<技名>_modify_attacker_stats`という、変化するステータスも方向も名前から一切わからない
汎用名になっている。

```
あまいかおり_modify_defender_stats   → 実際は evasion -2
あまえる_modify_defender_stats       → 実際は atk -2
めいそう_modify_attacker_stats       → 実際は spa +1, spd +1
わるだくみ_modify_attacker_stats     → 実際は spa +2
りゅうのまい_modify_attacker_stats   → 実際は atk +1, spe +1
```

さらに`move_status.py`自身の中でも、`いやなおと_lower_defender_def`（397行目）・
`かげぶんしん_boost_attacker_evasion`（608行目）の2件だけが`move_attack.py`と同じ
具体的命名を使っており、直後の`うそなき_modify_defender_stats`（401行目）と並べると
ファイル内で規則が割れていることが一目でわかる。

```python
def いやなおと_lower_defender_def(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return modify_defender_stats(battle, ctx, value, stats={"def": -2})


def うそなき_modify_defender_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """うそなきの効果: 相手のとくぼうを2段階下げる。"""
    return modify_defender_stats(battle, ctx, value, stats={"spd": -2})
```

`うそなき`は前回`handlers.md` ISSUE-18で「関数名`_reduce_defender_spe`が実装
（`spd`）と食い違う」と指摘されていたバグ持ちの関数だったが、現在は具体名を放棄して
ヘルパー名そのものに改名する形で「矛盾」自体は解消されている。しかし結果として
「命名ミスを防ぐために情報量を捨てる」という後退した解決になっており、
`move_attack.py`側の規約（具体的なステータス名・方向を関数名に含める）とは逆行する。
どちらの流儀を正とするか（多くの関数がある`move_status.py`側に合わせて全体を
汎用名にするか、`move_attack.py`側に合わせて具体名を回復するか）をCLAUDE.mdまたは
各モジュールdocstringに明文化した上で統一することを推奨する。

### 2. 状態異常付与ハンドラの命名も同様に分裂している

`move_attack.py`は単一の固定状態異常を付与する関数を`apply_<状態異常名>_to_defender`
という具体名で統一している（`apply_burn_to_defender`, `apply_paralysis_to_defender`,
`apply_poison_to_defender`, `apply_freeze_to_defender`など、数十件）。汎用名
`apply_ailment_to_defender`が使われるのは、複数の状態異常から確率的に1つを選ぶ
`トライアタック_apply_ailment_to_defender`（1981行目）・
`フェイタルクロー_apply_ailment_to_defender`（2749行目）の2件のみであり、
「複数候補があるときだけ汎用名を使う」という区別が明確に守られている。

対して`move_status.py`は、**単一の固定状態異常しか付与しない**技（あくまのキッス→ねむり、
キノコのほうし→まひ、さいみんじゅつ→ねむり、しびれごな→まひ、どくガス→どく、
どくどく→もうどく、どくのこな→どく、ねむりごな→ねむり、へびにらみ→まひ、
でんじは→まひ）が軒並み`apply_ailment_to_defender`という汎用名になっている
（`move_status.py:172, 689, 947, 1039, 1737, 1748, 1764, 2029, 2491, 1675`）。
さらに`うたう_apply_sleep`（406行目）・`おにび_apply_burn`（551行目）・
`ダークホール_apply_sleep`（1412行目）の3件は`_to_defender`まで省いた第3の命名
パターンになっており、同一カテゴリの効果に対して`move_status.py`単独で
少なくとも3種類の命名パターンが並存している。

### 3. move_attack.py 内の能力ランク変化サフィックスに English 略称と日本語1文字表記が混在する

`move_attack.py`のステータス変化サフィックスは`atk`/`def`/`spa`/`spd`/`spe`という
辞書キー相当の英語略称が主流（前述66件）だが、以下の約20関数だけがゲーム内表記の
1文字（A/B/C）を使っている。

```
グロウパンチ_boost_attacker_A / コメットパンチ_boost_attacker_A / メタルクロー_boost_attacker_A
はがねのつばさ_boost_attacker_B / バリアーラッシュ_boost_attacker_B
しんぴのちから_boost_spa_C / チャージビーム_boost_spa_C / フレアソング_boost_spa_C / ほのおのまい_boost_spa_C
ゴールドラッシュ_sharply_lower_spa_C / サイコブースト_sharply_lower_spa_C /
  フルールカノン_sharply_lower_spa_C / りゅうせいぐん_sharply_lower_spa_C / リーフストーム_sharply_lower_spa_C
ソウルクラッシュ_lower_spa_C / はいよるいちげき_lower_spa_C / バークアウト_lower_spa_C /
  マジカルフレイム_lower_spa_C / ミストボール_lower_spa_C / むしのていこう_lower_spa_C / ムーンフォース_lower_spa_C
```

特に問題なのは`_boost_spa_C`/`_lower_spa_C`/`_sharply_lower_spa_C`という3系列で、
いずれも`attacker`/`defender`を名前に含めていない。実装を確認したところ

- `boost_spa_C`（4件）: すべて`modify_attacker_stats`（自分のとくこうを上げる。例:
  `しんぴのちから_boost_spa_C`, 1381-1382行目）
- `sharply_lower_spa_C`（5件）: すべて`modify_attacker_stats`（自分のとくこうを
  2段階下げる。例: `サイコブースト_sharply_lower_spa_C`, 1209-1210行目）
- `lower_spa_C`（7件、`sharply`を含まない）: すべて`modify_defender_stats`
  （相手のとくこうを下げる。例: `ソウルクラッシュ_lower_spa_C`, 1576-1577行目）

という規則性はあるものの、これは**実装を読まないと分からない暗黙のルール**であり、
「`sharply`の有無で対象がattacker/defenderに切り替わる」という設計はこのファイルの
どこにも明文化されていない。同じ`_lower_spa_C`という文字列が技によってattacker/defenderの
どちらを指すか変わる状態は、`move_attack.py`が他の66件で徹底している
「関数名だけで主体・対象・ステータス・方向が特定できる」という規約から明確に逸脱している。
また`とどめばり_boost_attacker_atk`（1910行目）は同じ「自分のこうげきを上げる」効果を
`atk`という英語略称で表現しており、`グロウパンチ_boost_attacker_A`らの`_A`表記と
表記系統が異なる（1つのファイル内でA/B/CとatK/def/spa/spd/speの2系統が併存）。

### 4. 非公開ヘルパーの命名・可視性規約が move_attack.py と move_status.py で異なる

`move_attack.py`は複数技から呼ばれる共有ロジックに一貫してアンダースコア接頭辞を
付ける（`_recoil`, `_drain_hp`, `_force_switch_random`, `_is_sheer_force_blocked`,
`_clear_spin_effects`, `_weight_to_power`, `_weight_ratio_to_power`,
`_hp_low_to_power`, `_はやてがえし_can_apply`, `_ふいうち系_can_apply`の10件）。

`move_status.py`には**アンダースコア接頭辞を持つ関数が1件も存在しない**
（`grep '^def _'`で0件、モジュールレベル定数`_BATON_PASS_VOLATILES`等3件のみ該当）。
同じ「複数技から呼ばれる内部ヘルパー」に相当する`まもる系_連続使用失敗チェック`
（2668行目、まもる・トーチカ・キングシールド等9技で使用）・
`みちづれ_連続使用失敗チェック`（2805行目）・`テクスチャー2_取得_変更候補タイプ`
（1569行目）・`ミラータイプ_取得_対象タイプ`（2867行目）はいずれも接頭辞なしの
公開名であり、しかも後2者は英語動詞を一切使わない日本語名詞句（`取得_変更候補タイプ`、
`取得_対象タイプ`）になっている。`move_attack.py`側の私的ヘルパーはすべて
英語動詞ベースの`snake_case`（技名を含む場合も`_技名_can_apply`のように英語動詞部分は
保つ）であるのに対し、`move_status.py`側は英語動詞を持たない構成が2件ある点で、
「アンダースコア接頭辞の有無」「英語動詞の有無」の両面でファイル間の慣例が揃っていない。
なお`複数技で共有される汎用ハンドラの命名規則が3パターンに分裂している`問題自体は
`.internal/review/code/data_moves.md` ISSUE-3で既に指摘されており、本節はそれに
「非公開／公開の可視性表現」という観点を追加するものである。

### 5. attacker/defender の使い分けは全体として健全

`AttackContext`を受け取るハンドラでの`ctx.attacker`/`ctx.defender`の参照は、
本レビューで確認した範囲（約630関数）で誤用は見当たらなかった。`いやしのはどう_heal_defender`
（`move_status.py:380`、相手を回復）、`スケイルショット_apply_stat_change`
（`move_attack.py:1470`、命中側の能力を変化、`ctx.attacker`を正しく使用）など、
「効果の対象語（heal/lower/boost）」と「実際に操作する主体（attacker/defender）」の
対応関係が名前と実装で一致しないケースは、前述のISSUE-1（ダイヤストーム）を除いて
見つからなかった。`user`/`target`という語は`AttackContext`系ハンドラでは使われておらず
（`attacker`/`defender`に統一）、`move.py`の共通ヘルパーもCLAUDE.mdの規約通り
`attacker:self`/`defender:self`のみを使用しており、`source:self`/`target:self`との
混在は無い（`MoveHandler`は`skip_subject_check=True`を常時使うため`subject_spec`の
実効チェックは行われないが、値自体は規約通り指定されている）。

### 6. ランク変化系ヘルパー群（スワップ/シェア系）の命名は模範的

`move_status.py`の能力コピー・交換技群は、対象が「ランク補正値（boosts）」か
「実数値そのもの」かを動詞で正確に区別しており、良い実例として記録しておく。

| 関数 | 対象 | 動詞 |
|---|---|---|
| `ガードシェア_equalize_stats`（657行目） | 実数値（防御・特防） | `equalize`（平均化） |
| `ガードスワップ_swap_ranks`（672行目） | ランク補正値（防御・特防） | `swap`（交換） |
| `パワーシェア_equalize_stats`（2355行目） | 実数値（攻撃・特攻） | `equalize` |
| `パワースワップ_swap_ranks`（2370行目） | ランク補正値（攻撃・特攻） | `swap_ranks` |
| `パワートリック_swap_stats`（2382行目） | 実数値（攻撃⇔防御） | `swap_stats` |
| `スピードスワップ_swap_speed`（1274行目） | 実数値（すばやさ） | `swap_speed` |
| `ハートスワップ_swap_ranks`（2292行目） | ランク補正値（全ステータス） | `swap_ranks` |

「ranks」＝ランク補正値、「stats」＝実数値という語の使い分けが7関数すべてで一貫しており、
実装（`get_raw_stat`/`set_raw_stat`経由か`.boosts`辞書経由か）とも正確に対応している。
前述1〜4の指摘とは対照的に、この一群は「効果の性質に応じて動詞を選ぶ」という
命名の理想形に近い。

---

## 総評

`move_attack.py`・`move_status.py`は、前回レビューの最重要課題だった
`_stats_manager`直接書き換え（model.md CRIT-1）が`PokemonStats`廃止・`Pokemon`統合
リファクタ（2026-07-11、コミット`1df19540`）によって既に解消されており、
カプセル化の観点では健全な状態にある。`move.py`の直近変更（半透明技のmove_name修正）も
問題なし。

一方で今回新たに重点調査した命名の一貫性については、**「能力ランク変化」という
単一の効果カテゴリに対して`move_attack.py`（具体名: `_lower_defender_spd`等、66件）と
`move_status.py`（汎用名: `_modify_defender_stats`等、50件）が全く異なる命名規則を
採用している**という、ファイル横断で最も規模の大きい不整合を確認した。これは
個々のバグではなく設計判断の分裂であり、`うそなき`（旧ISSUE-18）が「具体名を捨てて
矛盾を消す」形で解消されたことからも、`move_status.py`側が今後も汎用名へ収束していく
可能性がある。どちらの流儀に統一するかを決めてCLAUDE.mdまたは各ファイルの
モジュールdocstringに明記し、新規実装時に迷わないようにすることを推奨する。

個別のバグとしては`ダイヤストーム_sharply_boost_defender_B`（ISSUE-1）の
attacker/defender誤表記が実質的な実害はないものの`うそなき`と同種の再発であり、
優先して改名すべき。`おきみやげ_apply`の戻り値破棄（ISSUE-2）は挙動自体は
妥当と思われるが意図の明文化が必要。`_thaw_attacker`11重複（ISSUE-3）と
アロマセラピー/いやしのすず重複（ISSUE-4）は実害のない reuse 機会である。
