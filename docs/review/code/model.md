# コードレビュー — model/

日付: 2026-07-05
対象: `src/jpoke/model/`（`ability.py`, `ailment.py`, `effect.py`, `field.py`, `item.py`, `move.py`, `pokemon.py`, `stats.py`, `volatile.py`, `__init__.py`）
観点: 責務分離、内部実装の隠蔽、拡張性、過剰設計

---

## 総論

`model/` は `GameEffect` を基底クラスとした `Ability`/`Item`/`Move`/`Ailment`/`Volatile`/`Field` の
6兄弟構成と、それらを束ねる `Pokemon`（+ 委譲先の `PokemonStats`）という構成になっている。
`enabled`/`_disabled_reasons`/`register_handlers`/`unregister_handlers` という「有効・無効管理と
ハンドラ登録」の共通基盤は明快で、各サブクラスは概ねデータ保持と最小限の振る舞いに留まっており、
`core/` 側のバトル進行ロジックが model 層に直接書かれているような大きな汚染は無い。

一方で実際にコードと呼び出し元を横断して読むと、次の3種類の問題が見つかった。

1. **重大な隠蔽違反**: `handlers/move_status.py` の4つの技ハンドラが `Pokemon` の非公開属性
   `_stats_manager` の内部可変リストへ直接書き込んでおり、`model/stats.py` が用意した
   カプセル化を丸ごと迂回している（後述 CRIT-1）。
2. **過剰設計**: `GameEffect` が提供する「有効/無効管理」機構（`add_disable_reason` 等）は、
   実際には6サブクラス中 `Ability`/`Item` の2つでしか使われておらず、`Move`/`Ailment`/
   `Volatile`/`Field` にとっては使われない土台を継承しているだけになっている（後述 OVER-1）。
   `PokemonStats` への分離も、外部から level/base/nature を毎回渡さねばならず自己完結して
   いない点で分離の恩恵が薄い（OVER-3）。
3. **ドキュメントドリフト**: `Volatile` の docstring `Attributes` が実装と大きく食い違っている
   （`value`→実際は `hp`、`disabled_move_name`/`locked_move_name`→実際は共用の `move_name`、
   `source_pokemon`→実装なし）。

既存の `architecture_review.md` が挙げた model/ 関連の指摘（`__deepcopy__` の重複、
`pp_consumed_moves` 残置、`set_stats_from_dict` の順序依存、ミュータブルデフォルト引数など）は
今回すべて実ファイルで再確認済みで、行番号のズレは無かった。以下では重複を避けつつ、
今回の観点（特に過剰設計）で新たに見つかった点を中心に記載する。

---

## 重大な指摘

### CRIT-1: `handlers/move_status.py` が `Pokemon` の非公開属性 `_stats_manager` の内部可変リストを直接書き換えている

**ファイル**:
- `src/jpoke/handlers/move_status.py:433-434`（ガードシェア）,`812-813`（スピードスワップ）,
  `1593-1594`（パワーシェア）,`1622-1623`（パワートリック）
- `src/jpoke/model/stats.py:72-79`（`PokemonStats.stats` が内部リストをコピーせず返している）

```python
# handlers/move_status.py:427-440
def ガードシェア_equalize_stats(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ガードシェア: 使用者と相手のぼうぎょ・とくぼうの実数値を平均化する。"""
    atk_stats = ctx.attacker._stats_manager.stats
    def_stats = ctx.defender._stats_manager.stats
    for idx in (2, 4):
        avg = (atk_stats[idx] + def_stats[idx]) // 2
        atk_stats[idx] = avg
        def_stats[idx] = avg
    return HandlerReturn(value=value)
```

同様のパターンが `スピードスワップ_swap_speed`（`atk_stats[5], def_stats[5] = ...`）、
`パワーシェア_equalize_stats`、`パワートリック_swap_stats`（`stats[1], stats[2] = stats[2], stats[1]`）
の計4関数に存在する。

問題点:

- `_stats_manager` は `model/pokemon.py:86` で定義される、命名規則上「非公開」を意味する
  アンダースコア始まりの属性であり、`Pokemon` 自身も `indiv`/`effort`/`stats`/`set_stats`/
  `set_effort` という一連の public プロパティ・メソッドでラップして公開している。にもかかわらず
  `handlers/move_status.py`（`model/` の外側、別レイヤーの `handlers/`）はこれらの public API を
  一切使わず、`ctx.attacker._stats_manager.stats` という非公開の内部オブジェクトへ直接アクセスし、
  さらに `PokemonStats.stats` プロパティ（`model/stats.py:72-79`）が防御的コピーをせず
  `self._stats` の参照をそのまま返しているため、返ってきたリストの要素へ代入するだけで
  実数値そのものが書き換わってしまう。
- CLAUDE.md は「`Pokemon.hp` へ直接代入禁止 → 必ず `battle.modify_hp(...)` を使う」
  「ランク変化は `battle.modify_stat(...)`」と、状態変更を一段介したAPI経由に限定する規約を
  明記しているが、この4関数が扱う「実数値そのものの書き換え」（ランクではなくステータス実値の
  平均化・入れ替え）にはそもそも `Pokemon`/`battle` 側に対応する公開メソッドが存在しない。
  そのため実装者は非公開属性への直接アクセスという抜け道を選ばざるを得なかったと見られる。
- 実害は現状無い（テストは通っている）が、`PokemonStats` の内部表現（リストの並び順やインデックス
  対応）を変更すると、`model/` 側を一切変更していなくても `handlers/move_status.py` の4関数が
  サイレントに壊れる。カプセル化が「他モジュールが読んでも安全」という前提を満たしていない。

**推奨**: `Pokemon` に `swap_stat_values(idx1, idx2)` / `average_stat_values(*idxs, targets=...)`
のような公開メソッド（内部で `_stats_manager` の該当インデックスを書き換える）を用意し、
`handlers/move_status.py` からは `ctx.attacker.xxx(...)` の形でのみ呼び出すようにすべき。
併せて `PokemonStats.stats`（`stats.py:72-79`）が生のリスト参照を返している点も、
呼び出し側に書き換えを許してしまう設計であることを認識しておく必要がある。

---

## 中程度の指摘

### ISSUE-1: `Pokemon.weight` に特性のロジックが直書きされている

**ファイル**: `src/jpoke/model/pokemon.py:239-259`

```python
@property
def weight(self) -> float:
    w = self.data.weight
    match self.ability.name:
        case 'ライトメタル':
            w = int(w*0.5*10)/10
        case 'ヘヴィメタル':
            w *= 2
    if self.has_item('かるいし', consider_enabled=True):
        w = int(w*0.5*10)/10
    return max(w, 0.1)
```

CLAUDE.md は「固有効果のロジックは `handlers/*` に名前付き関数で実装し、`data/*.py` からその関数を
登録する」と明記しており、実際 `model/` 全体を見渡してもこの1箇所以外に特性名で分岐する
コードは無い（`grep 'self.ability.name'` の一致はこの1件のみ）。`weight` に対応する `Event` が
`enums/event.py` に存在しないため、動的なフック無しで特性・アイテムの効果を扱う唯一の手段として
ここに直書きされたと考えられるが、結果的に「ライトメタル/ヘヴィメタル/かるいしの効果」という
特性・アイテム固有知識が `handlers/ability.py`/`handlers/item.py` ではなく `model/pokemon.py` に
漏れ出している。新しい重さ変更系の特性・アイテムを追加する際、実装者がこの箇所の存在に
気づかず `handlers/` 側だけを触ってしまうリスクもある。

**推奨**: 実害は小さいが、他の特性の慣例（イベントハンドラで倍率を積む）に合わせて
`ON_CALC_WEIGHT`（または類する）イベントを新設し、`handlers/ability.py`/`handlers/item.py` 側に
移すことを検討する価値がある。少なくとも、なぜここだけ直書きが許容されているのかを
コメントで明示すべき。

### ISSUE-2: `GameEffect` 派生6クラスの `__deepcopy__` が個別に再実装されている（既存指摘の再検証・具体化）

**ファイル**: `model/ability.py:40-44`, `item.py:30-35`, `ailment.py:47-51`,
`volatile.py:52-56`, `move.py:46-50`, `field.py:44-48`

```python
def __deepcopy__(self, memo):
    cls = self.__class__
    new = cls.__new__(cls)
    memo[id(self)] = new
    return fast_copy(self, new)
```

`architecture_review.md`（ISSUE-12）で既に指摘済みの内容で、現時点でも行番号・内容とも
そのまま該当する（`field.py` のみ `fast_copy(self, new, keys_to_deepcopy=[])` と明示するが、
`copy_utils.fast_copy` の実装上 `[]` は「未指定」と同義であり実質同一）。

拡張性の観点から補足すると、この重複は「新しい `GameEffect` 派生クラスを追加するたびに
`__deepcopy__` を一字一句コピーする」という手間を将来にわたって強制する。
`GameEffect` に以下のようなデフォルト実装を持たせ、`Pokemon.__deepcopy__` のように
選択的ディープコピーが必要なクラスだけがオーバーライドする形にすれば、
6クラス中5クラス（`Field` を除く全て）から `__deepcopy__` の定義自体を削除できる。

```python
# model/effect.py に追加するイメージ
def __deepcopy__(self, memo, keys_to_deepcopy: list[str] | None = None):
    cls = self.__class__
    new = cls.__new__(cls)
    memo[id(self)] = new
    return fast_copy(self, new, keys_to_deepcopy)
```

### ISSUE-3: `Pokemon.__deepcopy__` に存在しない属性 `pp_consumed_moves` が残置（既存指摘の再検証）

**ファイル**: `src/jpoke/model/pokemon.py:120-129`

```python
def __deepcopy__(self, memo):
    cls = self.__class__
    new = cls.__new__(cls)
    memo[id(self)] = new
    fast_copy(self, new, keys_to_deepcopy=[
        'ability', 'item', 'moves', 'ailment', 'volatiles',
        'executed_move', 'pp_consumed_moves',
        '_stats_manager',
    ])
    return new
```

`architecture_review.md`（ISSUE-1）の指摘どおり現在も残置を確認した
（`grep pp_consumed_moves src/` の一致は `model/pokemon.py:126` のみで、定義箇所は無い）。
`fast_copy` は `old.__dict__` に存在するキーのみ処理するため実害は無いが、削除すべき。

### ISSUE-4: `Volatile` の docstring `Attributes` が実装と大きく食い違っている

**ファイル**: `src/jpoke/model/volatile.py:15-31`（docstring） vs `33-50`（実装）

```python
class Volatile(GameEffect):
    """...
    Attributes:
        count: 揮発性状態の継続ターン数などを記録するカウンター
        value: 揮発性状態に紐づく数値（みがわりのHP等）
        disabled_move_name: かなしばりで使用禁止になっている技名
        locked_move_name: アンコールで固定されている技名
        source_pokemon: バインド等で使用者を記録（使用者が交代すると解除される）
    """

    def __init__(self, name, count=None, move_name="", hp=0, bind_damage_ratio=1/8):
        self.count = count
        self.move_name = move_name
        self.hp = hp
        self.bind_damage_ratio = bind_damage_ratio
```

docstring が挙げる5属性のうち実装と一致するのは `count` のみで、残りは食い違うか実装が無い。

| docstring 記載 | 実際の対応 |
|---|---|
| `value`（みがわりのHP等） | 実装では `hp`（属性名が異なる） |
| `disabled_move_name`（かなしばり用） | 実装は `move_name` を共用（`handlers/volatile.py:339`で確認） |
| `locked_move_name`（アンコール用） | 同じく実装は `move_name` を共用（`handlers/volatile.py:208`付近で確認） |
| `source_pokemon`（バインド使用者記録） | 該当する属性が実装に存在しない（`grep source_pokemon` は0件） |
| （docstring に記載なし） | `bind_damage_ratio` が実装に存在するが docstring には無い |

つまり「かなしばりの禁止技」と「アンコールの固定技」は同じ `move_name` フィールドを流用する
設計になっているが、docstring はそれぞれ別属性であるかのように書かれた古い設計メモが
そのまま残っていると見られる。`source_pokemon` に至っては実装されたことが無い（または
実装後に削除されて docstring だけ残った）ため、この docstring を信じて
`volatile.source_pokemon` にアクセスするコードを書くと即座に `AttributeError` になる。

**推奨**: 実装（`count`/`move_name`/`hp`/`bind_damage_ratio`）に合わせて `Attributes` を
書き直すべき。`move_name` がかなしばり・アンコールで意味を共用している旨も一言添えると良い。

### ISSUE-5: `model/ability.py` のみ `AbilityData` を定義元と異なるモジュールからインポートしている

**ファイル**: `src/jpoke/model/ability.py:4`（`from jpoke.data.ability import AbilityData`）
対 `item.py:5`, `field.py:8`, `ailment.py:6`, `volatile.py:6`（いずれも `from jpoke.data.models import XxxData`）

`AbilityData`/`ItemData`/`MoveData`/`AilmentData`/`VolatileData`/`FieldData` はすべて
`src/jpoke/data/models.py` で定義されているが、`model/ability.py` だけが定義元の `data/models.py`
ではなく、データ登録モジュールである `data/ability.py`（`ABILITIES` 辞書を定義するファイル）
経由で `AbilityData` を再インポートしている。実行上は `data/ability.py` が
`from .models import AbilityData` しているため動作するが、「型定義は `data/models.py` から
取る」という他5ファイルの一貫した参照経路から `ability.py` だけが外れている。
TYPE_CHECKING ブロック内のみの影響なので実害は無いが、`data/ability.py` 側の import 文が
将来変わると `model/ability.py` の型ヒントだけが壊れる、分かりにくい依存になっている。
`from jpoke.data.models import AbilityData` に統一すべき。

---

## 過剰設計の観点

### OVER-1: `GameEffect` の有効/無効管理機構は6サブクラス中 `Ability`/`Item` の2つにしか実質的に使われていない

**ファイル**: `model/effect.py:39,74-116`（`_disabled_reasons`/`add_disable_reason`/
`remove_disable_reason`/`enabled_ignoring`/`consumed`）

`GameEffect` は「有効/無効化や公開状態を管理する効果オブジェクトの共通基盤」として設計されて
おり、`_disabled_reasons: set[...]` を核に `enabled`/`enabled_ignoring`/`consumed`/
`add_disable_reason`/`remove_disable_reason`/`replace_disabled_reasons` という6つのAPIを
6サブクラス（`Ability`/`Item`/`Move`/`Ailment`/`Volatile`/`Field`）全てに一律で継承させている。

しかし実際に `add_disable_reason`/`remove_disable_reason` の呼び出し元を全文検索すると、
呼ばれているのは次の2箇所だけである。

```
core/ability_manager.py:141  mon.ability.add_disable_reason(reason)
core/ability_manager.py:158  mon.ability.remove_disable_reason(reason)
core/lethal.py:302,306       ctx.defender.ability.add_disable_reason/remove_disable_reason
core/item_manager.py:52      mon.item.add_disable_reason(reason)
core/item_manager.py:72      mon.item.remove_disable_reason(reason)
```

すべて `.ability` または `.item` に対する呼び出しであり、`Move`/`Ailment`/`Volatile`/`Field`
のインスタンスに対して `add_disable_reason` が呼ばれている箇所はコードベース全体に
1件も無い（同様に `enabled_ignoring` の呼び出しも `core/event_manager.py:203` の
`subject.item.enabled_ignoring(...)` の1件のみで、こちらも `.item` 限定）。

つまり `Move`/`Ailment`/`Volatile`/`Field` にとって `_disabled_reasons` は生成時の
空集合のまま永久に変化せず、`enabled` は常に `True`、`register_handlers`（`effect.py:129`）の
`if not self.enabled: return` という早期リターンは常に素通りする、実質デッドコードの
ガードになっている。`GameEffect` は「最も複雑な要求を持つ `Ability`」
（`per_battle_once` による自己無効化＝`consumed`）に合わせて設計された結果、
無効化という概念を持たない4クラスにまで同じ仕組みを強制する形になっている。

これは「拡張性のための共通化」自体は妥当な判断だが、実態としては
「6クラス共通の土台」ではなく「2クラス専用の機構を4クラスが黙って背負っている」状態であり、
新しく `GameEffect` 派生クラスを追加する実装者に「`add_disable_reason` をこのクラスでも
使うべきか」という誤った期待を持たせるリスクがある。ただし、リファクタの実益（4クラスから
未使用APIを剥がして `enabled` 判定を専用サブクラスへ移す）と混乱コストを比べると、
今すぐ手を入れるほどの実害は無い。**方針としては「無効化理由を持つのは `Ability`/`Item`
だけである」という制約をコメントか型で明示しておく**のが現実的な落としどころ。

### OVER-2: `revealed`（公開情報フラグ）の概念が `Ailment`/`Field`/`Volatile` では形骸化している

**ファイル**: `model/effect.py:38`, `ailment.py:37`, `field.py:40`, `volatile.py`（未設定）

`GameEffect.revealed` はデフォルト `False` で、`Ability`/`Item`/`Move`/`Pokemon` については
`core/observation_builder.py`（`mon.ability.revealed`, `mon.item.revealed`, `move.revealed`,
`mon.revealed`）で実際に「相手から見えている情報か」の判定に使われている。

一方 `Ailment`（`ailment.py:37`）と `Field`（`field.py:40`）はコンストラクタで
`self.revealed = True` と固定しているが、`grep revealed` を `observation_builder.py` 以外に
広げても `Ailment`/`Field` インスタンスの `.revealed` を読んでいる箇所は無く、
「常に `True` に固定しているだけで誰も読まない属性」になっている。さらに `Volatile` は
デフォルト値 `False` のまま一度も `True` に設定されず、読まれることも無い
（`observation_builder.py` が参照する対象に `volatiles` は含まれていない）。

`GameEffect` が全派生クラスに一律で持たせている「公開/非公開」という属性が、
実際に意味を持つのは4クラス中2〜3クラス（`Ability`/`Item`/`Move`）に限られており、
`Ailment`/`Field`/`Volatile` にとっては使われない状態フラグを継承しているだけになっている。
実害は「無駄なブール値が1つ増える」程度で小さいが、OVER-1と合わせて見ると、
`GameEffect` が持つ2つの横断的関心事（有効/無効管理・公開情報管理）のうち、
全サブクラスが両方をフルに使っているわけではないという傾向が一貫して見える。

### OVER-3: `PokemonStats`（`_stats_manager`）への分離が自己完結しておらず、抽象化の恩恵が薄い

**ファイル**: `model/stats.py:54-177`, `model/pokemon.py:438-591`

`PokemonStats` は `_stats`/`indiv`/`effort` という状態を持つが、再計算に必要な
`level`/`base`（種族値）/`nature` は一切保持しない設計になっている。そのため
`Pokemon` 側のほぼ全てのプロパティ・メソッドが「`_stats_manager` に処理を委譲しつつ、
`self._level`/`self.data.base`/`self._nature` を毎回引数として渡す」という形になっている。

```python
# pokemon.py:492-495
self._stats_manager.set_stats_from_dict(stats, self._level, self.data.base, self._nature)
self.update_stats()

# pokemon.py:576-578
return self._stats_manager.set_stats_from_value(
    idx, value, self._level, self.data.base, self._nature
)
```

`PokemonStats` の呼び出し元は現状 `Pokemon` 一箇所のみ（`grep 'PokemonStats('` は
`pokemon.py:86` の1件だけ）であり、他クラスから再利用されている実績も無い。
「ステータス計算ロジックを独立したクラスに切り出す」こと自体は
`model/stats.py` 冒頭のモジュール関数（`calc_hp`/`calc_stat`/`chmp_to_legacy_effort`）を
再利用可能にする点で意味があるが、`PokemonStats` というクラスの単位で見ると、
状態（`_stats`/`indiv`/`effort`）と計算に必要な入力（`level`/`base`/`nature`）が分裂しており、
呼び出し側の `Pokemon` がその橋渡しを毎回明示的に行わなければならない。
つまり「`Pokemon` の一部の属性を専用クラスに逃がした」割には `Pokemon` 側のコードが
単純化されておらず（`indiv`/`effort`/`stats`/`set_stats`/`set_effort`/`update_stats` の
6箇所すべてが薄い委譲＋パラメータの受け渡しのままである）、クラス分割の主目的である
「関心の分離」の効果が限定的である。

加えて CRIT-1 で述べたとおり、この分離は実際にはカプセル化としても機能しておらず
（`handlers/move_status.py` が `_stats_manager` を直接参照・変更している）、
「独立したクラスに分離した」という設計意図と「外部から素通りでアクセスされている」という
実態にズレがある。`_stats_manager` を `Pokemon` 内部に完全に隠すか（`stats`/`indiv`/`effort`
プロパティ経由のみで公開し、実数値の直接書き換えが必要な効果には専用の公開メソッドを
用意する）、あるいは `level`/`base`/`nature` も含めて `PokemonStats` に保持させて
真に自己完結したクラスにするか、どちらかに倒したほうが分離の意図が一貫する。

---

## 軽微な指摘

### MINOR-1: `Pokemon.show()`/`to_dict()` が既存の public プロパティを使わず `_stats_manager` に直接アクセスしている

**ファイル**: `src/jpoke/model/pokemon.py:799`, `819-820`

```python
# show() 内
for st, ef in zip(self._stats_manager.stats, self._stats_manager.effort):
    ...

# to_dict() 内
"indiv": self._stats_manager.indiv,
"effort": self._stats_manager.effort,
```

`Pokemon` 自身が `effort`（`pokemon.py:453-460`）や `indiv`（`432-438`）という public
プロパティを既に持っているにもかかわらず、`show()`/`to_dict()` はこれらを使わず
`_stats_manager` に直接アクセスしている（`stats` のリスト形式だけは public プロパティが
辞書形式しか提供していないため直接参照もやむを得ないが、`indiv`/`effort` は完全に等価な
public プロパティが存在する）。`Pokemon` クラス自身の内部メソッドがカプセル化を
自主的に破っている状態で、CRIT-1 の「外部モジュールが `_stats_manager` へ直接アクセスする」
問題を助長する悪い前例になっている。`self.indiv`/`self.effort` に置き換えるべき。

### MINOR-2: `Move.to_dict()` / `Pokemon.to_dict()` が呼び出し元を持たないデッドコード

**ファイル**: `src/jpoke/model/move.py:52-58`, `src/jpoke/model/pokemon.py:805-822`

`grep '\.to_dict()' src/ tests/ scripts/` では両メソッドとも呼び出し箇所が1件も見つからない
（`docs/plan/refactor_event_log_structure.md` 内の無関係な文字列一致を除く）。
シリアライズ用のユーティリティとして用意されたと見られるが、現状は使われておらず、
将来 `Pokemon`/`Move` に属性を追加した際にこの2メソッドの更新を忘れても
テストが失敗しないため、気づかれないまま実装と乖離していくリスクがある
（`Volatile` の docstring 同様のドリフトが将来ここでも起こり得る）。
使う予定が無いなら削除、使うなら呼び出し元を作るべき。

### MINOR-3: `PokemonStats.set_stats_from_dict` が辞書の挿入順に依存している（既存指摘の再検証）

**ファイル**: `src/jpoke/model/stats.py:132-143`

```python
def set_stats_from_dict(self, stats: dict[Stat, int], level, base, nature):
    stat_values = list(stats.values())
    for i in range(6):
        self._calculate_effort_from_stat(i, stat_values[i], level, base, nature)
```

`architecture_review.md`（MINOR-3）の指摘どおり現在も該当。呼び出し側の辞書キー順が
`STATS`（hp, atk, def, spa, spd, spe）と一致している前提でインデックスアクセスしており、
異なる順序の辞書を渡すと努力値が別のステータスに誤って割り当てられる。
`stats[STATS[i]]` のようにキーで引く実装にすべき。

### MINOR-4: `Pokemon.__init__` のミュータブルデフォルト引数（既存指摘の再検証）

**ファイル**: `src/jpoke/model/pokemon.py:56`

```python
def __init__(self, ..., move_names: list[MoveName] = ["はねる"], ...):
```

`architecture_review.md`（MINOR-4）の指摘どおり現在も該当。`set_moves` は
`[Move(name) for name in moves]` で新しいリストを作るだけなので実害は無いが、
典型的な落とし穴パターンであり `move_names: list[MoveName] | None = None` +
`move_names or ["はねる"]` に置き換えるのが安全。

### MINOR-5: `self.data` の型ヒント用コメントの表記ゆれ（既存指摘の再検証・3パターンの揺れを確認）

**ファイル**: `model/item.py:26`, `ailment.py:39`, `volatile.py:50`, `move.py:36`
（いずれも `# type hint`）, `field.py:42`（`# IDE hint`）, `ability.py:38`（日本語）

`architecture_review.md`（MINOR-8）が挙げた「英語 vs 日本語」の揺れに加え、実際には
英語表記の中でも `# type hint`（4ファイル）と `# IDE hint`（`field.py` のみ）という
2種類の言い回しが混在しており、揺れは2パターンではなく3パターンであることを確認した。
`ability.py:38` の日本語コメント（「型ヒントのための属性。実際のデータは
super().__init__で設定される」）に統一すべき。

### MINOR-6: `Ability.reset_enable_state` と `Item.reset_enable_state` がほぼ同一実装（既存指摘の再検証・呼び出し元を確認）

**ファイル**: `model/ability.py:56-66`, `model/item.py:46-51`

```python
# Ability.reset_enable_state
def reset_enable_state(self):
    reasons = set()
    if self.has_flag("per_battle_once") and self.consumed:
        reasons.add("consumed")
    self.replace_disabled_reasons(reasons)

# Item.reset_enable_state（Abilityのper_battle_once分岐を省いた部分集合）
def reset_enable_state(self):
    reasons = set()
    if self.consumed:
        reasons.add("consumed")
    self.replace_disabled_reasons(reasons)
```

`architecture_review.md`（MINOR-9）の指摘どおり現在も該当。なお `reset_enable_state` は
`grep` で確認する限り外部から呼ばれることはなく、それぞれ自身の `reset_on_switch_out`
内部だけから呼ばれる private ヘルパーに近い（`Move`/`Ailment`/`Volatile`/`Field` は
そもそも定義していない＝OVER-1 で述べた「無効化理由を実質使わない4クラス」と一致する）。
実害は小さいが、`GameEffect` にデフォルト実装（`Item` 相当の単純な版）を置き、
`Ability` だけが `per_battle_once` 分岐をオーバーライドする形にすれば重複は解消できる。

---

## 総評

`model/` の設計思想（`GameEffect` による統一的な有効/無効管理、`data/*.py` との明確な役割分担、
`Pokemon` への状態集約）自体は健全で、バトルロジックが model 層に大量に漏れ出しているような
大きな崩れは見られなかった。ただし今回「内部実装の隠蔽」と「過剰設計」を重点的に調べた結果、
次の2点が最も対応価値が高い。

1. **CRIT-1**（`handlers/move_status.py` による `_stats_manager` の直接ミューテーション）は、
   カプセル化が名前だけのものになっている実例であり、`Pokemon` に実数値操作用の公開APIを
   追加して塞ぐべき。
2. **OVER-1〜OVER-3**（`GameEffect` の有効/無効管理・公開情報管理が実質2〜3クラス専用に
   偏っている点、`PokemonStats` が自己完結しない分離になっている点）は、今すぐ壊れているわけ
   ではないが、次に7つ目の `GameEffect` 派生クラスを追加する際や `PokemonStats` を拡張する際に
   「このクラスにも `add_disable_reason` は必要か」「`PokemonStats` は本当に level/nature を
   持つべきでは」という判断に迷う実装者を生みやすい。方針をコメントとして明文化しておくだけでも
   価値がある。

`ISSUE-2`（`__deepcopy__` 重複）・`ISSUE-3`（`pp_consumed_moves` 残置）・`MINOR-3`/`MINOR-4`/
`MINOR-5`/`MINOR-6` は `architecture_review.md` の既存指摘を実ファイルで再検証したもので、
いずれも記載どおり現存することを確認した。`ISSUE-4`（`Volatile` docstring のドリフト）・
`ISSUE-5`（`AbilityData` import 経路の不統一）・`MINOR-1`/`MINOR-2` は今回新たに見つかった指摘。
