# 実装計画: ダメージ計算・致死率計算の高速化

更新日: 2026-09-10
ブランチ: `feature/perf-damage-lethal`（worktree: `../work-perf`、`origin/main` @ `850cb07b1` 起点）
実装担当: **codex**（本計画書は設計・計測のみ。実装コードは codex が書く）

---

## 1. 目的と非目的

### 目的

`Battle.calc_damages()` と `Battle.calc_lethal()` は、外部の木探索プレイヤー・
bot・RL 学習ループから**1手の評価あたり数十〜数百回**呼ばれる最内側のプリミティブである。
現状これらは Python レベルの無駄（`Decimal` による丸め、乱数生成器の要素単位 deepcopy、
frozen dataclass のハッシュ）で実力の 2〜4 倍遅くなっている。

**挙動を1ビットも変えずに** これらを高速化する。

### 結論（先出し）

worktree で試作・実測した結果、**計算式に一切手を入れずに**以下が得られた。

| | main | 本計画適用後（実測） |
|---|---:|---:|
| `calc_damages` | 0.0735 ms | **0.0217 ms（−70%）** |
| `calc_lethal`（代表4ケース） | 1.93〜4.48 ms | **0.95〜1.61 ms（−49〜−65%）** |
| `calc_lethal` @ ターン20 | 2.459 ms | **0.925 ms（−62%）** |
| `deepcopy(battle)`（木探索の枝生成） | 0.712 ms | **0.521 ms（−27%）** |

全 6,240 テスト通過（1 skipped）、致死率・ダメージ分布の出力は完全一致。
**最大の要因は `Decimal` による丸めと乱数生成器の deepcopy** という、
仕様と無関係な実装上の無駄である。

### 非目的

- 計算式・仕様の変更（ダメージ値・致死率の出力は完全一致させる）
- 公開 API のシグネチャ変更
- 並列化（プロセス並列は呼び出し側の責務。本計画はシングルスレッド性能のみ扱う）
- `TreeSearchPlayer` 等、探索アルゴリズム側の改善

---

## 2. 計測環境とベースライン

| 項目 | 値 |
|---|---|
| OS | Windows 11 Home 10.0.26200 |
| Python | CPython 3.11.9 |
| 対象 | `origin/main` @ `850cb07b1` |
| 実行方法 | `PYTHONPATH=src python <bench>`（共有 editable install を汚さないため） |

計測は `time.perf_counter()` によるループ平均（warmup 1回）。
プロファイルは `cProfile` + `pstats(sort="tottime")`。

### 2.1 ベースライン実測値

対戦: ガブリアス（攻）× カイリュー（防, マルチスケイル / オボンのみ）、3vs3、開幕直後。

| ケース | main | 備考 |
|---|---:|---|
| `calc_damages(じしん)` | **0.0735 ms** | 1回の攻撃の16乱数 |
| `deepcopy(battle)` | **0.712 ms** | `calc_lethal` が毎回1回払う |
| `calc_lethal(じしん, max_attack=10)` | **3.134 ms** | |
| `calc_lethal(ドラゴンテール)` vs マルチスケイル | **1.930 ms** | 満タン枝分岐あり |
| `calc_lethal((スケイルショット, 3))` | **2.174 ms** | 多段技 |
| `calc_lethal(でんこうせっか, max_attack=10)` ピカチュウ→ハピナス | **4.484 ms** | 分布が育つ最悪ケース |

### 2.2 `deepcopy(battle)` のターン依存

`calc_lethal` は毎回 `deepcopy(battle)` する。`event_logger` / `command_log` は
対戦開始からの全履歴を持つため、**ターンが進むほど致死率計算が重くなる**。

| ターン | `deepcopy(battle)` | `battle.copy(copy_logs=False)` | `calc_lethal(じしん)` |
|---:|---:|---:|---:|
| 0 | 0.528 ms | 0.461 ms | 0.722 ms |
| 5 | 0.600 ms | 0.432 ms | 0.878 ms |
| 10 | 0.835 ms | 0.412 ms | 1.645 ms |
| 20 | **1.205 ms** | **0.419 ms** | 1.943 ms |

ログを外せばコピーコストはターン数に対して**定数**になる（0.41〜0.46 ms）。

---

## 3. ボトルネック分析（cProfile）

### 3.1 `calc_lethal(じしん, max_attack=10)` × 200回（main, 合計 2.070 s）

| 区分 | cumtime | 比率 |
|---|---:|---:|
| `deepcopy(battle)`（`copy.deepcopy`） | 0.765 s | 37% |
| `calc_damages`（うち `round_half_down` 0.297 s） | 0.714 s | 34% |
| `lethal._get_handlers`（ハンドラ探索） | 0.374 s | 18% |

`round_half_down` は **332,000 回**呼ばれ、その中で `Decimal(str(v)).quantize(...)` を実行している。
`Field.is_active`（プロパティ）は **444,000 回**呼ばれている。

### 3.2 `calc_damages` 単体 × 5000回（main, 合計 0.860 s）

| 関数 | tottime | 比率 |
|---|---:|---:|
| `utils/math.py::round_half_down` | 0.288 s | **43%（cumtime 0.371 s）** |
| `damage.py::calc_damages` 本体 | 0.132 s | 15% |
| `Decimal.quantize` | 0.083 s | 10% |

**`calc_damages` の実行時間の 4 割超が `Decimal` による丸め**。
16乱数 × 5補正 = 80 回の `Decimal(str(float))` を毎回作っている。

### 3.3 `deepcopy(battle)` × 500回（main, 合計 1.713 s）

属性別の内訳（単独 deepcopy 実測）:

| 属性 | 時間 |
|---|---:|
| `random` | 0.120 ms |
| `decision_random` | 0.121 ms |
| `_player_states`（ポケモン6体） | 0.133 ms |
| `players` | 0.134 ms |
| `side_managers` | 0.066 ms |
| その他マネージャー計 | ≈0.06 ms |

`random.Random` は `getstate()` が **625 要素のメルセンヌ状態タプル**を持ち、
`copy.deepcopy` はこれを**要素ごとに** deepcopy する（`_deepcopy_tuple` の
リスト内包が deepcopy 全体の 38% を占める）。乱数生成器2個だけで
`deepcopy(battle)` の **約30%** を消費している。

### 3.4 分布が育つケース（`でんこうせっか` × 10, 合計 0.361 s / 30回）

| 関数 | tottime | 比率 |
|---|---:|---:|
| `lethal_dist._convolve` | 0.072 s | **20%（cumtime 0.140 s = 39%）** |
| `State.__hash__`（dataclass 生成） | 0.033 s | 9% |
| `State.__eq__`（dataclass 生成） | 0.020 s | 6% |

`@dataclass(frozen=True)` が生成する `__hash__` / `__eq__` は Python 関数呼び出しになるため、
分布の畳み込みで辞書キーとして使うと非常に高い。**合計 15%** がハッシュ・比較に消えている。

---

## 4. 改善方針

Phase 1・Phase 2（2-1〜2-3）は worktree で**プロトタイプ実装して実測済み**。
Phase 3 は設計のみ。数値はすべて実測値。

### Phase 1: 低リスク・高効果（実測済み）

#### 1-1. `round_half_down` / `round_half_up` から `Decimal` を撤去

`src/jpoke/utils/math.py:26,31`

```python
def round_half_down(v: float) -> int:
    """五捨五超入で丸める。"""
    return math.ceil(v - 0.5)


def round_half_up(v: float) -> int:
    """四捨五入で丸める（ちょうど0.5は切り上げ）。"""
    return math.floor(v + 0.5)
```

**等価性の根拠**: 旧実装（`Decimal(str(v))`）と新実装を **421,579 ケース**で
差分比較し、不一致 **0 件**を確認済み。ケース内訳は
(a) `value*modifier/4096`（value 1〜1199 × 代表 modifier 12種）、
(b) `max_hp * r`（max_hp 1〜799 × 割合9種）、
(c) `uniform(0, 5000)` の乱数 200,000 件、
(d) 整数 + {0, 0.25, 0.5, 0.75} の乱数 200,000 件。

> `str(float)` は「その float に丸め戻る最短10進表現」を返すため、
> `Decimal(str(v))` の丸めは実質「float が表す実数値の丸め」と一致する。
> `v - 0.5` / `v + 0.5` の減算誤差はダメージ計算の値域（< 10^6）では
> 丸め境界をまたがない。上記の差分比較がこれを裏づけている。

#### 1-2. 固定小数点補正を整数演算にする（`calc_damages` の核心）

`src/jpoke/utils/math.py` に追加:

```python
def apply_modifier_half_down(value: int, modifier: int) -> int:
    """4096基準の固定小数点補正を五捨五超入で適用する（整数演算）。"""
    return (value * modifier + 2047) >> 12
```

`round_half_down(value * modifier / 4096) == (value * modifier + 2047) >> 12` は
**value 0〜2999 × modifier 0〜8192（7刻み, 3.5M 通り）で不一致 0 件**を確認済み。
（五捨五超入 = `ceil(x - 0.5)`、`x = value*modifier/4096` を整数化すると
`(value*modifier - 2048 + 4095) // 4096 = (value*modifier + 2047) >> 12`。）

`src/jpoke/core/damage.py:143` の16乱数ループを整数化する:

```python
        floor_one = m_def_type * m_damage > 0

        damages = [0]*16
        for i in range(16):
            # 乱数 85~100%
            d = max_damage * (85 + i) // 100
            d = (d * m_atk_type + 2047) >> 12   # タイプ一致補正
            d = (d * m_def_type + 2047) >> 12   # タイプ相性補正
            d = (d * m_burn + 2047) >> 12       # やけど補正
            d = (d * m_damage + 2047) >> 12     # ダメージ補正
            d = (d * m_protect + 2047) >> 12    # まもる貫通系補正
            if floor_one and d < 1:             # 最低ダメージ補償
                d = 1
            damages[i] = d
```

あわせて `damage.py` 内の以下も整数化する（いずれも `value * modifier / 4096` 形）:

- `damage.py:118` 急所補正 `round_half_down(max_damage * 1.5)` → `(max_damage * 3) // 2`
- `damage.py:269` `_calc_final_power` → `apply_modifier_half_down(power, power_modifier)`
- `damage.py:344` `_calc_final_attack` → `apply_modifier_half_down(final_attack, atk_modifier)`
- `damage.py:389` `_calc_final_defense` → `apply_modifier_half_down(final_defense, def_modifier)`

> **注**: `int(max_damage * (0.85 + 0.01*i))` → `max_damage * (85 + i) // 100` は
> 副次的に float 誤差（`0.85+0.01*7 == 0.9199999999999999`）も除去する。
> 全テストで差分が出ないことは確認済みだが、レビュー時にこの1行は個別に見ること。

**`handlers/*.py` 側の `round_half_down(x * m / 4096)` 形（`item.py:632`,
`move_status.py:1381,2650` 等）も同じ置換対象**だが、ホットパスではないので
Phase 1 では 1-1 の恩恵に留め、任意作業とする。

#### 1-3. 乱数生成器の複製を `getstate`/`setstate` にする

`src/jpoke/utils/copy_utils.py` に追加:

```python
def copy_random(rng: random.Random) -> random.Random:
    """乱数生成器を複製する。

    `copy.deepcopy` は 625 要素のメルセンヌ状態タプルを要素ごとにコピーするため
    極端に遅い。状態は不変な int のタプルなので getstate/setstate で複製できる。
    """
    new = random.Random()
    new.setstate(rng.getstate())
    return new
```

`src/jpoke/utils/__init__.py` の `from .copy_utils import ...` と `__all__` にも
`copy_random` を追加する（既存の `fast_copy` / `recursive_copy` に倣う）。

`src/jpoke/core/battle.py`:

- `_EXTRA_DEEPCOPY_KEYS`（`battle.py:303`）から `"random"`, `"decision_random"` を削除
- `__deepcopy__`（`battle.py:331`）の `fast_copy(...)` 直後に以下を置く:

```python
        # 乱数生成器は getstate/setstate で複製する（deepcopy は 625 要素の
        # メルセンヌ状態タプルを要素ごとにコピーするため極めて遅い）
        new.random = copy_random(self.random)
        new.decision_random = copy_random(self.decision_random)
```

> `_EXTRA_DEEPCOPY_KEYS` から外すと `fast_copy` の `recursive_copy` 経路で
> **同一インスタンスが共有されてしまう**ため、直後の明示的な再代入は必須。
> 順序を入れ替えないこと。

**副次効果**: `Battle.copy()` を使う木探索の枝生成すべてが速くなる。

#### 1-4. `State` を frozen dataclass → `NamedTuple` にする

`src/jpoke/utils/lethal_dist.py:13`

```python
class State(NamedTuple):
    """HP分布の1要素。HP値と特性・道具の有効フラグを保持する。

    ability_enabled / item_enabled は「消耗型アイテム使用済み」など
    一度無効になったら戻らない状態を追跡するために使う。
    """
    value: int
    ability_enabled: bool = True
    item_enabled: bool = True
```

`__hash__` / `__eq__` が C レベルのタプル実装になる。
既存の生成箇所は `State(hp, ability_enabled=..., item_enabled=...)` の
位置引数+キーワード形式（`src/`・`tests/` 合わせて20箇所）で、
`NamedTuple` にそのまま置き換えられる。`dataclasses.replace` の使用箇所は無い。

> 差異: `NamedTuple` はタプルなのでイテレート・インデックスアクセスが可能になり、
> `State(1) == (1, True, True)` が True になる。既存コードはフィールド名アクセス
> しかしていないため影響しないが、`isinstance(x, tuple)` で分岐する箇所が
> 将来増えないよう docstring に明記する。
> なお `lethal_dist.py` の `dataclass` import は不要になるので削除する。

#### Phase 1 実測結果（プロトタイプ）

| ケース | main | Phase 1 | 改善 |
|---|---:|---:|---:|
| `calc_damages(じしん)` | 0.0735 ms | **0.0213 ms** | **−71%（3.5倍）** |
| `deepcopy(battle)` | 0.712 ms | **0.543 ms** | −24% |
| `calc_lethal(じしん, max=10)` | 3.134 ms | **1.734 ms** | **−45%** |
| `calc_lethal(ドラゴンテール)` | 1.930 ms | **1.003 ms** | **−48%** |
| `calc_lethal((スケイルショット,3))` | 2.174 ms | **1.266 ms** | −42% |
| `calc_lethal(でんこうせっか, max=10)` | 4.484 ms | **2.046 ms** | **−54%** |

致死率の出力値は完全一致（例: でんこうせっか10発の致死率
`0.8872787186410278` が前後で同一）。

---

### Phase 2: 設計を要する改善（2-1〜2-3 は実測済み）

#### 2-1. `calc_lethal` の複製をログ抜きにする

`src/jpoke/core/lethal.py:211`

```python
    battle = deepcopy(battle)
```

を

```python
    # 致死率計算はイベントログを参照しないため、対戦開始からの全履歴を
    # コピーしない（ログのコピーコストはターン数に比例して増える）。
    battle = battle.copy(copy_logs=False)
```

に変える。§2.2 の実測どおり、**ターン20 で複製コストが 1.205 ms → 0.419 ms（−65%）**、
以降ターンが進んでも定数のまま。序盤ではほぼ効果がないが、
実戦の中盤以降・木探索の深い枝ほど効く。

**実測効果**（`calc_lethal(じしん)`。ランダム3vs3・seed=1 のバトルを進めながら計測）:

| ターン | Phase 1 のみ | Phase 1 + 2-1 + 2-2 |
|---:|---:|---:|
| 0 | 0.722 ms | 0.601 ms |
| 10 | 1.645 ms | 1.105 ms |
| 20 | 1.943 ms | 1.305 ms |

（2-3 まで入れた最終形の数値は「Phase 1 + 2 の累積実測結果」を参照）

**確認事項（codex が実装前に検証すること）**:
- `Battle.copy()` は `copy_depth` を増やす／`late_field_activation` を False にする等、
  `__deepcopy__` と同じ経路を通る。`reseed=False` / `omniscient=False` の既定で
  `deepcopy(battle)` と等価か（`battle.py:393` の docstring と実装を読む）
- lethal ハンドラが `battle.add_event_log()` を呼んでいないか
  （呼んでいても複製先の空ログに書かれるだけで呼び出し元は汚れないが、
  ログを見るテストがあれば影響する）
- `Battle.copy()` は複製元のログを一時退避する（`battle.py` の Warning 参照）。
  スレッド安全性の前提は変わらない旨をテストコメントに残す
- `lethal.py` の `from copy import deepcopy` が他で使われていなければ import を消す

#### 2-2. lethal のハンドラ探索を1攻撃ラウンドあたり1回にする

`_get_handlers`（`lethal.py:584`）は `_emit` のたびに
特性・道具・状態異常・揮発状態・技・天候・地形・グローバル場・両サイド場の
**9系統からリストを組み立てて `sorted()`** している。1回の `calc_lethal` で 60 回呼ばれ、
Phase 1 適用後は **`calc_lethal` の 27%** を占める最大のホットスポットになる。

特に場の効果の探索が重い:

- `_get_global_field_handlers`（`lethal.py:565`）: `[weather, terrain] + list(global_manager.fields.values())`
  を毎回**新規リストとして構築**し、`Field.is_active` プロパティを全件呼ぶ
- `_get_side_field_handlers`（`lethal.py:574`）: 同様の処理を両サイド分

結果、`Field.is_active` が 1回の `calc_lethal` で **2,220 回**呼ばれる。

**調査結果（実測・確定）**:

`lethal_handlers` の登録元を全数調査したところ、`src/jpoke/data/` 配下で
`lethal_handlers` を登録しているのは
`ability.py` / `ailment.py` / `item.py` / `volatile.py` / `moves/*.py` と
**`data/field/weather.py` / `data/field/terrain.py` だけ**である。

- **グローバル場（5種）・サイド場（片側15種 × 2）に `lethal_handlers` は1つも無い**
- したがって `_get_global_field_handlers` のグローバル分と
  `_get_side_field_handlers` の全体は、**常に空リストを返すことが確定している**
- それでも毎イベント 5 + 15 + 15 = **35個の場に対し `Field.is_active`
  プロパティを呼び、3本の中間リストを新規生成している**

さらに、致死率ハンドラは `mon.volatiles` を書き換える
（`handlers/lethal.py` でバインド・かいふくふうじ・しおづけ・こんらん の追加、
たくわえる の削除）。**ポケモン側のハンドラ集合はループ中に変化しうる**ため、
ポケモン側をラウンド単位でキャッシュするのは不可。一方、
**場の `count` を書き換える致死率ハンドラは存在しない**。

**設計案（推奨・低リスク）**: キャッシュは導入せず、
**`lethal_handlers` が空かどうか**を最初に見て短絡させる。

> **重要（試作で判明）**: 単に `is_active` と `.get(event)` の順序を入れ替えるだけでは
> **かえって遅くなる**。`LethalEvent` は `Enum` で `Enum.__hash__` が Python 関数
> （`enum.py`）のため、辞書引きのキーにするコストが高い。実際、順序入れ替えのみの版では
> `enum.__hash__` の呼び出しが 132,400 → 576,400 回に増え、`_get_handlers` の
> cumtime が悪化した。
>
> `if not handlers: continue` という**ハッシュを伴わない空辞書判定**を先に置くのが正解。
> ハンドラを持たない場は `lethal_handlers` が空 dict なので、
> ここで 35 個中 35 個が落ちる（enum のハッシュも `is_active` も呼ばれない）。

```python
def _get_global_field_handlers(event: LethalEvent, battle: Battle) -> list[LethalHandler]:
    """天候・地形・共通フィールドから該当ハンドラを取得する。

    `lethal_handlers` が空の場を先に弾くことで、`LethalEvent` を
    キーにした辞書引き（Enum.__hash__ が重い）と `is_active`
    プロパティ呼び出し、中間リストの生成をまとめて避ける。
    """
    result = []
    for field in (battle.weather, battle.terrain,
                  *battle.global_manager.fields.values()):
        handlers = field.data.lethal_handlers
        if not handlers:
            continue
        h = handlers.get(event)
        if h is not None and field.is_active:
            result.append(h)
    return result
```

`_get_side_field_handlers` も同型にする（`subject` 判定は `is_active` の後）。
`_get_pokemon_handlers`（`lethal.py:545`）にも同じ空辞書短絡を入れる
（特性・道具・状態異常・揮発状態の多くは `lethal_handlers` が空）。

**あわせて入れる小改善**:
- `_get_handlers`（`lethal.py:584`）の `sorted()` を `len(handlers) > 1` のときだけ呼ぶ
- `handlers = []` + `extend` に統一し、`+=` によるリスト連結の一時オブジェクトを減らす
- `_get_pokemon_handlers`（`lethal.py:545`）の `candidates` リスト構築も、
  `.get()` の結果が `None` でないものだけを直接 `append` する形にする

**この案を採らない場合の代替**（効果は大きいが要検証）: 場のソースだけを
`_lethal_loop` の攻撃ラウンド先頭で1回組み立ててキャッシュする。
上の調査どおり致死率ハンドラは場を書き換えないので安全だが、
将来ハンドラが追加されたときに壊れる暗黙の前提を作るため**非推奨**。

**実測効果**: 単独では `calc_lethal(じしん)` 1.73 ms → 1.66 ms（−4%）と小さい。
2-1 と合わせて 1.73 ms → **1.59 ms（−8%）**。
プロファイル上の比率（27%）ほどには効かない（`_get_handlers` の残りコストは
ポケモン側の探索と関数呼び出しオーバーヘッドで、そこは削れないため）。
**費用対効果は Phase 1 や 2-1 より低い。工数が厳しければ後回しでよい。**

#### 2-3. `subtract_dist` / `_convolve` の融合

`src/jpoke/utils/lethal_dist.py:102`

現状 `subtract_dist(a, b, minimum=0)` は
`to_dist(b)` → `flip_dist(y)`（**新しい dict と State を全件生成**）→
`_convolve`（**さらに State を全件生成**）→ `_clip_dist`（**3度目の State 生成**）
と、中間 dict を3つ作り `State` を3回作り直している。

分布が育つケース（§3.4）では `_convolve` が **39%** を占める。

**設計案**: `add_dist` / `subtract_dist` を共通の
`_combine(a, b, sign, minimum, maximum)` に寄せて畳み込みとクランプを1パスにする。
さらに **`b` 側のフラグが全て `(True, True)` のときは `and` 演算とキー再構築を省く**
分岐を入れると効果が大きい（`ctx.damage_dist` は `to_dist(list[int])` で作られるので通常この形）。

```python
def _combine(a, b, sign: int, minimum: int | None, maximum: int | None) -> StateDist:
    """a と b を1パスで畳み込み・クランプする（HP は sign 倍した b を加算）。"""
    x, y = to_dist(a), to_dist(b)

    # b 側のフラグが全て True なら AND 演算とフラグ再構築を省ける（通常のダメージ分布）
    plain = all(k.ability_enabled and k.item_enabled for k in y)

    result: dict[State, int] = defaultdict(int)
    for sx, fx in x.items():
        vx, ax, ix = sx.value, sx.ability_enabled, sx.item_enabled
        for sy, fy in y.items():
            hp = vx + sign * sy.value
            if minimum is not None and hp < minimum:
                hp = minimum
            if maximum is not None and hp > maximum:
                hp = maximum
            if plain:
                result[State(hp, ax, ix)] += fx * fy
            else:
                result[State(hp,
                             ax and sy.ability_enabled,
                             ix and sy.item_enabled)] += fx * fy
    return dict(result)
```

**融合後は `flip_dist`（`lethal_dist.py:44`）・`_clip_dist`（同:52）・
`_convolve`（同:71）の3つが完全に未参照になる**（`src/` `tests/` 全体で他に呼び出し無し、
`jpoke.utils.__init__` からも `docs/reference/` からも非公開）。**削除すること。**

> **注意**: main のファイル内の並びは
> `to_dist` → `flip_dist` → `_clip_dist` → `_convolve` → **`add_dist`** → `subtract_dist`
> であり、`add_dist` が削除対象の3関数に挟まれている。
> 範囲削除すると `add_dist` を巻き込む（試作時に実際にやった）。関数単位で消すこと。
> `add_dist` は `handlers/lethal.py` の `_heal` / `_heal_at_pinch` などから
> 使われているので必ず残す。

**実測効果**: 分布が育つケース（でんこうせっか×10）で
Phase 1+2-1+2-2 の 2.05 ms → **1.63 ms（−20%）**、
多段技（スケイルショット×3）で 1.16 ms → **1.01 ms（−13%）**。

#### Phase 1 + 2 の累積実測結果

ガブリアス×カイリュー（マルチスケイル/オボンのみ）3vs3・開幕直後:

| ケース | main | Phase 1 | Phase 1+2 | 累積改善 |
|---|---:|---:|---:|---:|
| `calc_damages(じしん)` | 0.0735 ms | 0.0213 ms | **0.0217 ms** | **−70%** |
| `deepcopy(battle)` | 0.712 ms | 0.543 ms | **0.521 ms** | −27% |
| `calc_lethal(じしん, max=10)` | 3.134 ms | 1.734 ms | **1.613 ms** | **−49%** |
| `calc_lethal(ドラゴンテール)` | 1.930 ms | 1.003 ms | **0.948 ms** | **−51%** |
| `calc_lethal((スケイルショット,3))` | 2.174 ms | 1.266 ms | **1.095 ms** | **−50%** |
| `calc_lethal(でんこうせっか, max=10)`※ | 4.484 ms | 2.046 ms | **1.565 ms** | **−65%** |

※ ピカチュウ→ハピナス。分布が最も大きく育つケース。

ランダム3vs3（seed=1）を進めながらの `calc_lethal(じしん)`:

| ターン | main | Phase 1+2 | 改善 |
|---:|---:|---:|---:|
| 0 | 1.095 ms | **0.568 ms** | −48% |
| 5 | 1.316 ms | **0.649 ms** | −51% |
| 10 | 2.286 ms | **0.904 ms** | **−60%** |
| 20 | 2.459 ms | **0.925 ms** | **−62%** |

**ターンが進むほど改善幅が大きい**（2-1 でログのコピーが消え、
複製コストがターン数に対して定数になるため）。

いずれも致死率・ダメージ分布の出力は main と完全一致
（例: でんこうせっか10発の致死率 `0.8872787186410278` が全段階で同一）。

---

### Phase 3: 任意（効果は限定的 or 検証コスト高）

#### 3-1. 頻度の GCD 正規化

分布の総頻度は1ヒットごとに16倍される（実測: 8ヒットで 33bit）。
`(スケイルショット, 3)` × `max_attack=10` のような30ヒット級では
**120bit の多倍長整数**になり、辞書値の加算・乗算が遅くなる。

各ヒット後に `math.gcd` で全頻度を割って正規化すれば機械語整数に収まる。
`lethal_probability` は比なので値は変わらないが、
**`hp_counter` / `damage_counter` の生の頻度値は変わる**（比は保存される）。
これらを絶対値で見ているテストがあれば壊れるため、
`tests/` を grep して影響を確認してから判断すること。

#### 3-2. `calc_lethal` 内での `calc_damages` メモ化

`_calc_damage_dist`（`lethal.py`）は攻撃回数分 `battle.calc_damages()` を呼ぶが、
ランク変化・状態異常・アイテム消費が無ければ**毎回同じ結果**になる。
入力フィンガープリント（攻守のステータス・ランク・特性/道具名・揮発状態・
防御側HP・技・天候/地形/場のカウント）をキーにメモ化すれば
`calc_lethal` の残り 26% をほぼ消せる。

**ただし依存要素の取りこぼしが即バグになる**ため、
Phase 1・2 が入って効果を再測してから、必要と判断した場合のみ着手する。
着手する場合は `scripts/fuzz` を使った差分等価性検証（§5.3）を必須とする。

---

## 5. 評価計画

### 5.1 ベンチマークスクリプトの新設

`scripts/bench/bench_damage_lethal.py` を追加する（`scripts/` 配下は
ruff の `F841` 除外対象になっている実験用スクリプト置き場）。

要件:

- 固定シードで再現可能なこと
- 以下のケースを計測すること
  1. `calc_damages`（通常技 / タイプ相性0.5倍 / 一致技）
  2. `deepcopy(battle)` および `battle.copy(copy_logs=False)`
  3. `calc_lethal` × {単発技, マルチスケイル相手（満タン枝分岐）, 多段技, 分布が育つ弱技}
  4. **ターン 0 / 5 / 10 / 20 での `calc_lethal`**（§2.2 のログ肥大の回帰を検出する）
- `--json <path>` で結果を機械可読に吐けること
- `--baseline <path>` で過去結果と比較して増減率を表示できること

CI には載せない（Windows ローカル実行前提、計測ノイズが大きいため）。
`.internal/tests/logs/` に実行結果を残す。

### 5.2 回帰テスト（必須）

```powershell
python -m pytest tests/ -v
```

Phase 1 プロトタイプでは damage / lethal 関連テストは**全て通過**している
（結果は §7 に記載）。

加えて、`tests/test_damage.py` に丸め等価性の単体テストを追加する
（`tests/` 直下、既存の `test_damage.py` / `test_lethal.py` がダメージ・致死率担当）:

- `apply_modifier_half_down(v, m) == round_half_down(v * m / 4096)` を
  代表値の直積で検証（value 0〜300、modifier は実際に使われる値の一覧）
- `round_half_down` / `round_half_up` の境界値（`x.5` ちょうど、
  `x.4999999999999999`、`x.5000000000000001`、0、負値）
- **旧実装（`Decimal(str(v)).quantize(...)`）をテスト内にローカル関数として置き、
  新実装と突き合わせる**形にすると意図が伝わりやすい

テスト関数名は `test_<対象>_<確認内容>` 形式、日本語可。
追加後は `python scripts/sort_tests.py tests/test_damage.py` を実行する。

`tests/test_copy.py` には `Battle.copy()` / `deepcopy` の等価性テストが既にあるので、
1-3（乱数生成器の複製）では**そこに「複製後の乱数系列が複製元と一致する」テストを追加**する。

### 5.3 差分等価性検証（Phase 2-1 / 2-2 / 3-2 では必須）

既存の fuzz 基盤を流用する。`scripts/fuzz/dump_battle_log.py` は
シードから完全ランダムなパーティで1バトルを走らせ、
**全ターンのバトルログをファイルに書き出す**。

手順:

1. `main` の worktree で seed 1〜200 のログを出力
2. 改善ブランチで同じ seed のログを出力
3. `diff` が **全 seed で空**であることを確認

これで「乱数消費列を含めて挙動が1ビットも変わっていない」ことを示せる。
特に **1-3（乱数生成器の複製方法変更）は乱数系列の同一性が要**なので、
Phase 1 の PR でもこの検証を実施すること。

さらに `calc_lethal` については、main と改善版で同一入力の
`hp_counter` / `damage_counter` / `lethal_probability` が完全一致することを
ランダムな攻守・技の組み合わせ数千通りで確認する簡易スクリプトを
`scripts/bench/` に置く（ベンチと共用でよい）。

### 5.4 受け入れ基準

| # | 基準 |
|---|---|
| A | `python -m pytest tests/ -v` が全通過（下記の既知ドリフトを除く） |
| B | fuzz seed 1〜200 のバトルログが main と完全一致 |
| C | `calc_lethal` のランダム入力 3,000 通りで `hp_counter` / `damage_counter` が main と完全一致 |
| D | `calc_damages` が **−60% 以上**高速化 |
| E | `calc_lethal`（代表4ケース）が **−40% 以上**高速化 |
| F | ターン20 の `calc_lethal` が Phase 2-1 適用後にターン0 比 +30% 以内に収まる |
| G | `ruff check` / `mypy`（`src/jpoke/core` 対象）がクリーン |

---

## 6. codex への作業指示

### 6.1 作業ブランチ

- worktree `../work-perf`、ブランチ `feature/perf-damage-lethal`（`origin/main` 起点、作成済み）
- 別セッションが `jpoke/` 本体（`feature/regulation-mc-support`）で並走しているため、
  **リポジトリルートでは作業しないこと**
- 共有の editable install（`pip install -e .`）は `jpoke/` 本体を指している。
  worktree でのテスト・ベンチは **`PYTHONPATH=src` を付けて実行**し、
  install を貼り替えないこと（貼り替えると並走セッションが壊れる）
- main への直接コミット・マージは禁止。完了後 `gh pr create` → 確認のうえ `gh pr merge`

### 6.2 PR 分割

| PR | 内容 | 優先 | 検証 |
|---|---|---|---|
| **PR0** | ベンチマークスクリプト（§5.1）+ main のベースライン記録 | 最初 | — |
| **PR1** | Phase 1-1 + 1-2（丸めの整数化） | 高 | A, B, C, D + 丸め単体テスト |
| **PR2** | Phase 1-3（乱数生成器の複製） | 高 | A, **B（最重要）** |
| **PR3** | Phase 1-4（`State` の NamedTuple 化） | 高 | A, C |
| **PR4** | Phase 2-1（`copy_logs=False`） | 高 | A, B, F |
| **PR5** | Phase 2-3（`add_dist`/`subtract_dist` の1パス化 + 死んだヘルパー削除） | 中 | A, C |
| **PR6** | Phase 2-2（場ハンドラ探索の短絡化） | 低 | A, C |

**PR1〜4 は互いに独立**なので順不同で構わないが、
各 PR ごとに §5.4 の該当基準を満たしてからマージすること。
PR0 を最初に入れておくと以降の PR で増減率をそのまま記録できる。

PR6 は実測で −4〜8% と効果が小さいので、工数が厳しければ落としてよい。

Phase 3 は本計画では着手しない。PR1〜6 完了後に再計測し、
必要と判断された場合のみ別途計画する。

### 6.3 実装時の約束事（CLAUDE.md 準拠）

- コメント・docstring は日本語
- 型アノテーションは Python 3.10+ 構文（`X | Y`, `list[X]`）
- 80文字を超える `if` は括弧で複数行に展開し `and` ごとに改行
- `Pokemon.hp` への直接代入禁止（本計画の範囲では該当しないはずだが留意）
- `data/*.py` に触らないので `scripts/sort_data/*` の実行は不要。
  `handlers/*.py` に関数を足す場合のみ `python scripts/sort_handlers.py` を実行
- テストを足したら `python scripts/sort_tests.py <対象>` を実行
- **`CHANGELOG.md` に記載する**。`StateDist`（= `dict[State, int]`）は
  `jpoke.core.__init__` から再エクスポートされている公開型なので、
  1-4 の `State` の実装変更（frozen dataclass → NamedTuple）は
  外部から観測できる変更として1行残す。
  「タプルになるので比較・アンパックが可能になった」旨も添える
- `.internal/progress/*.md` は特性・技・アイテムの実装追跡用なので本作業では更新不要

---

## 7. 付記

### 7.1 プロトタイプの検証状況

本計画書の Phase 1・Phase 2 は worktree `../work-perf` で実際にパッチを当てて計測した。
**試作パッチ自体は計画書提出時点で worktree に残していない（破棄済み）**。
差分は参考として `.internal/plan/damage_lethal_performance_prototype.diff` に保存してある。
codex はこれを**参考にしてよいが、そのまま適用せず**、
本計画書の記述に沿って PR 単位で実装し直すこと
（試作は計測のために一気に当てたもので、テスト追加・CHANGELOG・
命名やコメントの整備を含んでいない）。

- 丸め等価性: 421,579 ケースで不一致 0 件（§4 Phase 1-1）
- 固定小数点: value 0〜2999 × modifier 0〜8192（7刻み, 約350万通り）で不一致 0 件（§4 Phase 1-2）
- 致死率の出力: 全ケースで main と完全一致
- `pytest tests/`: **6240 passed, 1 skipped**（`test_types_generated.py` は §7.2 の
  既知ドリフトのため除外して実行。Phase 1 単体でも Phase 1+2 の最終形でも同結果）

### 7.2 スコープ外の既知の問題

`tests/test_types_generated.py::test_generateliteralスクリプト_再実行しても差分が出ない[generate_item_literal.py-src/jpoke/types/item.py]`
が `origin/main` で失敗する。`src/jpoke/types/item.py` に
「グソクムシャナイト」「セグレイブナイト」が欠けており、
生成スクリプトを再実行すると差分が出る（wiki スクレイピングキャッシュの更新漏れ）。

**本計画とは無関係**だが、このテストは失敗時に対象ファイルを
**書き換えたまま残す**（次回実行は通ってしまう）ため、
codex は作業中に `git status` で `src/jpoke/types/item.py` が変更されていないか
確認し、変更されていたら `git checkout --` で戻すこと。
恒久対応は別タスクで行う。
