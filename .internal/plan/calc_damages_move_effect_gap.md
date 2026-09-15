# 調査報告: `Battle.calc_damages()` で技の効果が反映されない

更新日: 2026-09-15
ブランチ: `feature/calc-damages-move-effect`
報告元: poke-guide のダメージ計算UIで「特性スカイスキンがダメージに反映されない」という不具合報告

## 要約

`Battle.calc_damages()` は技実行フロー（`MoveExecutor.execute()`）を経ないため、技実行の
前処理でしか行われない2つの準備が抜け落ちている。

1. **技の有効タイプ・分類が解決されない**（`Event.ON_MODIFY_MOVE_TYPE` /
   `ON_MODIFY_MOVE_CATEGORY` が一度も発火しない）
2. **技データ側のハンドラが EventManager に登録されない**
   （`Move.register_handlers()` が呼ばれない）

1 によりスキン系特性のタイプ変換が無視され、2 により技データに実装された効果
（威力補正・タイプ変化・分類変化）がすべて無視される。両者は独立した欠落で、
2 のほうが影響範囲が広い。加えて、かたやぶり系の特性無効化も `ON_BEGIN_MOVE` /
`ON_END_MOVE` を経ないため反映されない（原因3）。

`Battle.calc_lethal()` も `battle.calc_damages()` 経由（`core/lethal.py:386` 他）なので
致死率計算にも同じ影響が出る。

## 実測（いずれも現在の main、無改変のコードで測定）

測定コードは `Player` にポケモンを1体ずつ入れて `Battle.start()` 後に
`battle.calc_damages(attacker, defender, move)` を呼ぶだけの最小構成。Lv50・努力値0。

### 症状1: スキン系特性のタイプ変換が効かない

メガボーマンダ（ドラゴン/ひこう）の すてみタックル（ノーマル・威力120）:

| 特性 | 相手 | 実測 | 期待 |
|---|---|---|---|
| スカイスキン | カビゴン | 105–124 | ひこう化＋タイプ一致1.5倍が乗るはず |
| いかく | カビゴン | 88–104 | （比較用） |
| スカイスキン | ゲンガー | **0–0** | ひこう化していればゴーストに通るはず |
| スカイスキン | フシギバナ | 87–103 | ひこう2倍が乗るはず |
| いかく | フシギバナ | 73–86 | （比較用） |

105/88 ≒ 1.19。つまり**威力1.2倍（`スカイスキン_modify_power`）だけが効き、
ひこうへのタイプ変換（`スカイスキン_modify_move_type`）が丸ごと無視されている**。
ゲンガーに0が出るのが決定的で、技タイプがノーマルのまま計算されている。

特性のハンドラは `AbilityManager` が場に出たときに登録する（`core/ability_manager.py:50`）
ため `ON_MODIFY_MOVE_TYPE` のリスナー自体は存在するが、**発火する側がいない**。

### 症状2: 技データのハンドラが一切効かない

| 技 | 条件 | 実測 | 期待 |
|---|---|---|---|
| ウェザーボール | 天候なし | 21–25 | ノーマル・威力50 |
| ウェザーボール | はれ | 21–25 | ほのお・威力100 |
| ウェザーボール | あめ | 21–25 | みず・威力100 |
| アクロバット | もちものなし | 58–69 | 威力110（2倍） |
| アクロバット | たべのこし | 58–69 | 威力55 |

天候を変えても、もちものの有無を変えても値が動かない。
`ウェザーボール` は `ON_MODIFY_MOVE_TYPE` と `ON_CALC_POWER_MODIFIER` の両方を、
`アクロバット` は `ON_CALC_POWER_MODIFIER` のみを技データに持つが、どちらも発動していない。

## 原因

### 原因1: `calc_damages` が有効タイプ・分類を解決していない

`Move` は `data` の値をコピーした可変フィールド `type` / `category` を持つ
（`model/move.py:37`, `model/move.py:39`）。これを更新しているのは技実行フローだけ:

```
core/move_executor.py:300  ctx.move.register_handlers(self._events, ctx.attacker)
core/move_executor.py:306  ctx.move.type = self.resolve_move_type(ctx.attacker, ctx.move)
```

`resolve_move_type()` / `resolve_move_category()`（`move_executor.py:719` / `:739`）が
`ON_MODIFY_MOVE_TYPE` / `ON_MODIFY_MOVE_CATEGORY` を発火する唯一の場所である。

一方 `Battle.calc_damages()`（`core/battle.py:1466`）は
`damage_calculator.calc_damages()` へ直行し、`DamageCalculator.calc_damages()`
（`core/damage.py:73`）は `AttackContext` を組み立てたあとすぐ威力・攻撃・防御の計算に入る。
タイプ一致補正（`damage.py:181`）とタイプ相性補正（`damage.py:225`）はどちらも
`ctx.move.type` を読むため、`data` の素のタイプで計算される。分類も同様に
`damage.py:346` の `move.category == "physical"` が素の分類を読む。

### 原因2: `calc_damages` が技データのハンドラを登録していない

`Move.register_handlers()` の呼び出しは `move_executor.py:300` の1箇所のみで、
解除は `:370`。つまり**技データのハンドラは技を撃っている最中しか EventManager に
存在しない**。`calc_damages` はこの登録を行わないため、技データに書かれた
`ON_CALC_POWER_MODIFIER` / `ON_MODIFY_MOVE_TYPE` / `ON_MODIFY_MOVE_CATEGORY` などは
すべて無視される。

原因1を直しても、技データ側のタイプ変化（ウェザーボール等）は原因2が残る限り直らない。
逆に原因2だけを直しても、発火する側がいないままなのでタイプ・分類は直らない。
**両方を直して初めて揃う。**

## 影響範囲

### `ON_MODIFY_MOVE_TYPE` を持つ効果

特性（`data/ability.py`。**原因1のみで直る**）:
うるおいボイス / スカイスキン / ドラゴンスキン / ノーマルスキン /
フェアリースキン / フリーズスキン

揮発性状態（`data/volatile.py:415`。付与元次第だが登録は Volatile 側なので原因1のみで直る）:
そうでん

技（`data/moves/`。**原因1と原因2の両方が必要**）:
ウェザーボール / オーラぐるま / めざめるダンス / レイジングブル / さばきのつぶて /
だいちのはどう / ツタこんぼう / テラクラスター / テラバースト

### `ON_MODIFY_MOVE_CATEGORY` を持つ効果

技のみ（**原因1と原因2の両方が必要**）:
フォトンゲイザー / シェルアームズ / テラクラスター / テラバースト

テラバースト・テラクラスターは実数値に応じて物理/特殊が変わるため、ダメージ計算UIでの
影響が大きい。

### 技データのその他のハンドラ（原因2のみ）

`ON_CALC_POWER_MODIFIER` を技データに持つ技すべて（アクロバット等）。
数が多いため本書では網羅していないが、**外部のダメージ計算ツールから見ると
「技固有の威力補正が全部効かない」状態**である点を強調しておく。

## 原因3（追加）: かたやぶり系の特性無効化が反映されない

かたやぶり / ターボブレイズ / テラボルテージ（`data/ability.py:530,1727,1932`）と
シャドーレイ / フォトンゲイザー / メテオドライブ（技データ）、メガソーラーは
`ON_BEGIN_MOVE` で適用し `ON_END_MOVE` で解除する（`move_executor.py:330` / `:362`）。
`calc_damages` はどちらも発火しないため、**原因1・2を直しても** 外部問い合わせでは
防御側のマルチスケイル等が無効化されず、技実行時のダメージと一致しない。
ダメージ計算器としての用途を考えると、これも外部API経由で当然反映されるべきなので
本件のスコープに含める。

## 修正方針（確定）

**`Battle.calc_damages()` / `Battle.roll_damage()` を「前処理あり」の外部APIにし、
内部実装（技実行中の呼び出し）は `DamageCalculator` を直呼びする。**

`CLAUDE.md` の「外部APIは `Battle` の公開メソッドを入口、`battle.<manager>.<method>()`
直呼びは `src/jpoke` 内部実装に限る」という規約と整合し、公開API 2 つの結果が
食い違うことも、フラグによる冪等化も不要になる。

### 1. `DamageCalculator.roll_damage()` の新設

`Battle.roll_damage()` にある乱数選択ロジック（`option.damage_roll` 分岐、
`core/battle.py:1449-1464`）を `DamageCalculator` へ移す。`DamageCalculator` の
公開メソッド（`calc_damages` / `roll_damage`）は **「技のハンドラ登録・タイプ/分類の
解決・かたやぶり適用が済んでいる前提」** で動く内部実装であることを docstring に明記する。

### 2. 前処理コンテキストマネージャ（`Battle` 内）

```python
@contextmanager
def _prepare_move_for_query(self, attacker, defender, move):
    """外部問い合わせ用に技実行と同じ前処理を施し、終了時に元へ戻す。"""
    if not self._query_needs_preparation(attacker, defender, move):
        yield
        return
    original_type, original_category = move.type, move.category
    ctx = AttackContext(attacker=attacker, defender=defender, move=move)
    move.register_handlers(self.events, attacker)
    try:
        # MoveExecutor.resolve_move_type / resolve_move_category と同じ基準値
        # （タイプは data.type、分類は現在値）で解決する
        move.type = self.events.emit(Event.ON_MODIFY_MOVE_TYPE, ctx, value=move.data.type)
        move.category = self.events.emit(Event.ON_MODIFY_MOVE_CATEGORY, ctx, value=move.category)
        self.events.emit(Event.ON_SETUP_MOVE, ctx)      # かたやぶり等の適用（後述）
        try:
            yield
        finally:
            self.events.emit(Event.ON_TEARDOWN_MOVE, ctx)  # かたやぶり等の解除
    finally:
        move.unregister_handlers(self.events, attacker)
        move.type, move.category = original_type, original_category
```

- `resolve_move_type` / `resolve_move_category` は `defender=battle.foe(attacker)` 固定で
  `AttackContext` を組むため再利用せず、渡された `defender` で自前に `emit` する。
- 分類の基準値が現在値（タイプは `data.type`）なのは `MoveExecutor` の踏襲。
  `Move.reset()` が都度 `data` 値に戻す設計で、`move.type` / `move.category` を書き換える
  箇所は `move_executor.py:306,310` の2箇所のみなので、実害はない。理由はコードにコメントで残す。
- **早期リターン（性能対策）**: `_query_needs_preparation` は、`move.data.handlers` が空、
  かつ `ON_MODIFY_MOVE_TYPE` / `ON_MODIFY_MOVE_CATEGORY` / `ON_SETUP_MOVE` のリスナーが
  `EventManager` に1つも登録されていない場合に False を返し、前処理を丸ごとスキップする。
  技データにハンドラを持たない大多数の技ではこれで従来と同じコストになる。

### 3. かたやぶり系の適用/解除を専用イベントに分離

`ON_BEGIN_MOVE` / `ON_END_MOVE` をそのまま問い合わせで発火することは **できない**。
`ON_END_MOVE` にはメトロノーム（回数加算）・はきだす（たくわえる消費）・ミクルのみ・
めいちゅうアップ（フラグ解除）など、技を実際に使った副作用を担うハンドラが登録されており、
問い合わせのたびに状態が壊れる。

そこで「技実行環境の適用/解除」だけを担う専用イベント対 `ON_SETUP_MOVE` / `ON_TEARDOWN_MOVE`
（既存の `ON_BEGIN_MOVE` / `ON_END_MOVE` と同じ `ON_<動詞>_MOVE` 形式。制御系カテゴリに
`ON_BEGIN_MOVE` の直前へ追加する）を `enums/event.py` に新設し、以下のハンドラを移す：

| 効果 | 現在 | 移動先 |
|---|---|---|
| かたやぶり / ターボブレイズ / テラボルテージ（`data/ability.py:540,544,1726,1730,1931,1935`） | ON_BEGIN_MOVE / ON_END_MOVE | ON_SETUP_MOVE / ON_TEARDOWN_MOVE |
| シャドーレイ / フォトンゲイザー / メテオドライブ（技データ） | 同上 | 同上 |
| メガソーラー（`data/ability.py:3409` 付近、天候上書き） | 同上 | 同上 |
| きんしのちから（変化技のみ対象。ダメージ問い合わせには無関係だが対称性のため） | 同上 | 同上 |

`MoveExecutor` は `ON_BEGIN_MOVE` の直前に `ON_SETUP_MOVE`、`ON_END_MOVE` の直後に
`ON_TEARDOWN_MOVE` を発火する（技実行時の順序は不変）。とびだすなかみの `save_hp`
（ctx への保存のみ）と、はきだす・りんしょう・メトロノーム・ミクルのみ・めいちゅうアップは
`ON_BEGIN_MOVE` / `ON_END_MOVE` に残す。

priority: `ON_BEGIN_MOVE` / `ON_END_MOVE` は `.internal/spec/turn.md` に未掲載。
移動するハンドラの priority は現状の値をそのまま引き継ぐ（相対順序が変わらないため）。

### 4. 内部呼び出し元を `damage_calculator` 直呼びに切り替える

技実行中は Executor が既に登録・解決・かたやぶり適用済みのため、前処理は不要かつ
有害（`EventManager.on()` は非冪等、`off()` は一致ハンドラを全削除するため、
二重登録と Executor 側登録の消失を起こす）。

| 呼び出し元 | 備考 |
|---|---|
| `core/move_executor.py:640` | 本流 |
| `handlers/move_attack.py:2741`（はめつのねがい） | 技実行中の `ctx.move` を渡す |
| `handlers/move_attack.py:3460`（みらいよち） | 同上 |
| `handlers/volatile.py:608`（こんらん自傷） | **`move="_こんらん"` と文字列で渡している。** `str → Move` 変換は `Battle.calc_damages()` 内（`battle.py:1476`）で行われるため、切り替え時は `Move("_こんらん")` を明示的に生成する。技実行外だが、前処理でスキン系のタイプ変換等が乗ると挙動が変わりうるので内部呼びに揃える |

呼び出し元は上記4箇所で全数（grep で確認済み）。

### 5. そのまま残す呼び出し元

- `core/lethal.py:386,394,400`（`calc_lethal`）: 外部問い合わせなので前処理ありが正しい。
  `_calc_damage_dist` で同一 `ctx.move` を2回（フルHP分岐用・通常用）渡す経路も、
  都度 `data.type` / 現在値を基準に前処理→復元するので残留状態は漏れない。
  deepcopy された battle 上でも `EventManager.__deepcopy__` / `update_reference` で
  `battle` 参照が張り替わるため整合性は保たれる。
- `players/max_damage_player.py:29`: 同上。

### 採らない案

- **報告書初版の案A**（`DamageCalculator.calc_damages()` 内で無条件に登録/解除）:
  技実行経路（`_execute_hit` → `roll_damage` → `calc_damages`）で確実に二重登録と
  ハンドラ消失を起こす。
- **フラグで冪等化して単一経路にする案**（`Move` に登録済みフラグを持たせ未登録時のみ前処理）:
  設計は成立するが、イベント発火は毎回必要になるので早期リターンによる性能対策と相性が悪く、
  「内部実装は前処理済み前提」という契約を明文化できる分離案のほうが見通しがよい。
- **案C（呼び出し側で前処理）**: 利用者ごとの再実装になり、技データのハンドラ登録は
  外部から再現できない。poke-guide 側でも外付け対応は行わない。

## リスク・確認事項

1. **性能（最重要）**: `calc_damages` は 2026-09-10 の `feature/perf-damage-lethal` で −70%
   （0.0735ms → 0.0217ms）に高速化されたホットパスで、木探索では1手あたり数十〜数百回呼ばれる
   （`.internal/plan/damage_lethal_performance.md`）。早期リターンを入れた上で、同ドキュメントと
   同条件のベンチマークを修正前後で取り、劣化がないことを確認する。
2. **問い合わせで発火するイベントの副作用**: `ON_MODIFY_MOVE_TYPE` のハンドラ（スキン系・
   そうでん `handlers/volatile.py:809`）は value を返すだけで状態を変えない（そうでんの解除は
   `ON_TURN_END` のみ）ことを確認済み。`ON_SETUP_MOVE` / `ON_TEARDOWN_MOVE` に移すハンドラは
   適用/解除が対称であることを1つずつ確認する（メガソーラーは深度カウンターで多重発動を
   管理しているので問い合わせでの再入も安全なはず）。
3. **既存テストの前提**: `calc_damages` / `calc_lethal` を使うテストは25ファイル。
   素のタイプ・かたやぶり非適用の前提で書かれた期待値がないか洗い出す。
4. **技実行中に別 `Move` で問い合わせる経路**: ハンドラ内から実行中の技と異なる `Move` で
   `battle.calc_damages` を呼ぶ既存コードがあるか確認する（現状の grep では該当なし）。
5. **poke-guide への反映**: 修正後は wheel の再ビルドと
   poke-guide 側 `public/master-data/pyodide/wheels/` への vendoring が必要。

## テスト方針

- スキン系特性4種（スカイスキン / フェアリースキン / フリーズスキン / ノーマルスキン）
  それぞれで、(a) タイプ相性が変わる相手、(b) 無効化されていた相手（ゴーストへのノーマル）、
  の2ケースを `calc_damages` で検証する。
- ウェザーボールを天候4種で、アクロバットをもちもの有無で検証する（原因2の回帰）。
- テラバーストで攻撃側のA/Cを入れ替え、分類が切り替わることを検証する（分類の回帰）。
- かたやぶり持ちの攻撃側 vs マルチスケイル持ちの防御側で `calc_damages` が無効化込みの値を
  返し、問い合わせ後に防御側の特性が復帰していることを検証する（原因3）。シャドーレイでも同様。
- `calc_lethal` のフルHP分岐（マルチスケイル等）で、2回の `calc_damages` 呼び出しの両方で
  スキン系・ウェザーボールが正しく解決されることを検証する。
- ハンドラを持たない技（たいあたり等）で `calc_damages` の結果が完全不変であること
  （早期リターンのガード）。
- こんらん自傷ダメージ・はめつのねがい・みらいよちの既存テストが修正前後で不変であること。
- 技実行フロー（`battle.step()`）でのダメージが修正前後で同一であること。加えて
  **連続技（スケイルショット等）の2発目以降のダメージが同一であること**、および
  **技実行後に技データのハンドラが `EventManager` に残っていないこと** を確認する
  （二重登録・`off()` 全削除の回帰検出。ダメージ不変だけでは `ON_HIT` 系の消失を検出できない）。
- メトロノーム・はきだす・ミクルのみ等 `ON_END_MOVE` に残すハンドラが、問い合わせでは
  発動しないことを確認する。
- 性能ベンチマーク（リスク1）。

## レビュー履歴

- 2026-09-15: 初版（案A）に対し、技実行経路との二重登録が確定で発生する点を指摘。
  `Battle` 層と `DamageCalculator` 層の分離方針に改訂。Fable によるセカンドオピニオン
  （条件付き同意）を受け、性能の早期リターン・こんらん自傷の文字列引数・かたやぶりを反映。
  かたやぶりはスコープ外ではなく対応対象とする判断（ダメージ計算器の用途上、当然反映されるべき）。
