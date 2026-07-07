# 修正計画: リーサル計算のHP満タン依存効果

更新日: 2026-07-05

## スコープ

- 対象: `src/jpoke/core/lethal.py`、`src/jpoke/handlers/lethal.py`、
  `src/jpoke/data/ability.py`、`src/jpoke/data/item.py`、
  `src/jpoke/enums/event.py`、`src/jpoke/types/literals.py`
- 実装状態: 完了（2026-07-05）
- 対象特性・道具: マルチスケイル、ファントムガード、テラスシェル、がんじょう、きあいのタスキ

## 完了時の追記（2026-07-05）

`core/lethal.py`（`_apply_damage` / `damage_dist_full` / `_calc_damage_dist`）と
`handlers/lethal.py`（`_survive_at_full_hp` / `がんじょう_survive_lethal` /
`きあいのタスキ_survive_ohko`）、`enums/event.py` の `LethalEvent.ON_APPLY_DAMAGE`、
`types/literals.py` の `"full_hp_damage_modifier"` フラグはすでに実装済みだったが、
並列レビューエージェントによる `src/jpoke/data/ability.py` / `src/jpoke/data/item.py`
への競合編集で、最後の登録手順（下記）だけが失われていた（`test_がんじょう_*` /
`test_きあいのタスキ_*` / `test_マルチスケイル_満タン非満タン混在時も枝ごとに正しく半減`
が回帰していた）。

- `data/ability.py` の `"がんじょう"` に `lethal_handlers={LethalEvent.ON_APPLY_DAMAGE:
  LethalHandler(l.がんじょう_survive_lethal, subject="defender")}` を再登録。
- `data/item.py` の `"きあいのタスキ"` に同様の `lethal_handlers` を再登録。
- `data/ability.py` の `"マルチスケイル"` `"ファントムガード"` `"テラスシェル"` の
  `flags` に `"full_hp_damage_modifier"` を再登録。

`docs/progress/ability.md` の該当5行（がんじょう・マルチスケイル・ファントムガード・
テラスシェル）の「リーサル実装」列を更新した
（マルチスケイル・テラスシェル・がんじょうは「リーサルテスト」列も専用テストがあるため更新。
ファントムガードは専用のリーサル計算テストが無いため「リーサルテスト」列は `-` のまま）。
`docs/progress/item.md` のきあいのタスキは登録前から x/x のまま
（ドキュメント側は先に更新済みで、コード側の登録のみ失われていた）だったため変更なし。
全テスト `python -m pytest tests/ -v` で3257 passed, 1 skipped を確認。

## 動機（現状の課題）

`core/lethal.py` はHPを `StateDist`（HP値→出現頻度の確率分布）として扱うが、`_update_hp`
（`core/lethal.py:373`）が分布内の**最小値**を `defender.hp`（スカラー）に代入し、それを
通常の `battle.calc_damages` が参照することで「HP満タン依存」の特性・道具を間接的に
効かせている。

これは分布の各枝ごとに「そのHPがちょうど満タンかどうか」を判定すべきところを、代表値
（最小値）1つに潰してから判定しているため、**満タンの枝と非満タンの枝が同一分布内に混在する
場面**（例: ナゾのみ等で一部の確率枝だけ満タンまで回復した、みがわりで防いで0ダメージだった、
など。`docs/spec/abilities/マルチスケイル.md` 16行目に明記）で誤った結果になる。既存テスト
（`test_マルチスケイル_ダメージ半減` 等）は「全枝が満タン」か「全枝が非満タン」のどちらかしか
作らないケースのみを検証しており、混在ケースの誤りは検出できていない。

加えて、がんじょう・きあいのタスキの「満タン時HP1耐え」はそもそも `lethal_handlers` に一切
登録されておらず、リーサル計算では完全に無視されている（`docs/progress/ability.md` /
`item.md` でも該当行は `リーサル実装 n/a`）。

調査の結果、リーサル計算に関与する「防御側HP依存」の効果は**すべて `defender.hp ==
defender.max_hp` の等号判定のみ**（`grep "defender.hp ==" handlers/ability.py
handlers/item.py` で確認、他の閾値判定は存在しない）で、性質の異なる2種類に分かれる。

- **A. ダメージ計算自体を変える系**（マルチスケイル・ファントムガード・テラスシェル）:
  `battle.calc_damages` 内部の通常ハンドラ（`Event.ON_CALC_DAMAGE_MODIFIER` /
  `ON_CALC_DEF_TYPE_MODIFIER`）が `defender.hp == defender.max_hp` を見て発動する。
- **B. 確定後のダメージをHP1に補正する系**（がんじょう・きあいのタスキ）:
  `calc_damages` の外側、ダメージ適用時に「満タンから瀕死になるなら1残す」という
  別イベント（`Event.ON_MODIFY_MOVE_DAMAGE`）で処理される。calc_damagesが返す
  ダメージ乱数列そのものは変えない。

この2種類は性質が異なるため、リーサル計算でも別々の仕組みで正しく再現する。
`_update_hp` 自体（他イベントでも使われる汎用の代表値更新）は変更しない
— どの仕組みも `_update_hp` が何を代表値にしているかに依存しない設計にする。

## 設計

### A. マルチスケイル系: 満タン枝は `calc_damages` を特性有効のままもう一度呼ぶ

`calc_damages` 内部のダメージ修正ロジック（半減・タイプ相性丸めなど）を `handlers/lethal.py`
に再実装すると、`handlers/ability.py` 側のロジックと二重管理になり乖離のリスクがある。
そのため**既存の通常ハンドラをそのまま再利用**する。満タン依存の**ダメージ計算修正**を持つ
特性には `AbilityData.flags` に新しい印 `"full_hp_damage_modifier"` を付ける
（`data/ability.py` の `"マルチスケイル"` / `"ファントムガード"` / `"テラスシェル"`
3箇所。既存の `"mold_breaker_ignorable"` 等と同じ `flags: set[str]` に追加するだけ）。

`core/lethal.py` の `_run_move`（273行目付近）で、この印を持つ特性かつ `hp_dist` に
満タン枝が存在する場合のみ、`battle.calc_damages` を**2回**呼ぶ:

```python
def _run_move(battle: Battle, ctx: LethalContext, hp_dist: StateDist,
              every_event_handlers: list[LethalHandler]) -> StateDist:
    max_hp = ctx.defender.max_hp
    needs_full_hp_split = (
        ctx.defender.ability.has_flag("full_hp_damage_modifier")
        and any(s.value == max_hp for s in hp_dist)
    )

    if needs_full_hp_split:
        # 満タン枝用: 特性を有効なまま hp=max_hp で計算する。
        # 既存の通常ハンドラ（マルチスケイル_reduce_damage 等）がそのまま正しく発火するため
        # 半減・タイプ相性丸め等のロジックを複製する必要がない。
        saved_hp = ctx.defender.hp
        ctx.defender.hp = max_hp
        full_damages = battle.calc_damages(ctx.attacker, ctx.defender, ctx.move, critical=ctx.critical)
        ctx.defender.hp = saved_hp

        # 非満タン枝(ベースライン)用: 特性を一時無効化して確実に条件を無効化する。
        # defender.hp が(_update_hp由来で)どんな値であっても結果に影響しないようにするため、
        # hpを操作するのではなく特性そのものを無効化する。
        ctx.defender.ability.add_disable_reason("リーサル計算")
        try:
            damages = battle.calc_damages(ctx.attacker, ctx.defender, ctx.move, critical=ctx.critical)
        finally:
            ctx.defender.ability.remove_disable_reason("リーサル計算")

        ctx.damage_dist = to_dist(damages)
        ctx.damage_dist_full = to_dist(full_damages) if full_damages != damages else None
    else:
        damages = battle.calc_damages(ctx.attacker, ctx.defender, ctx.move, critical=ctx.critical)
        ctx.damage_dist = to_dist(damages)
        ctx.damage_dist_full = None

    # (ON_BEFORE_HIT 以降は変更なし)
```

印を持たない特性（大多数）は `needs_full_hp_split` が常に `False` になり、従来通り1回だけ
呼ぶ。この変更は既存動作に影響しない。

`ability.enabled` は読み取り専用プロパティ（`model/effect.py:66` `not
self._disabled_reasons`）なので直接代入できない。`add_disable_reason` /
`remove_disable_reason`（`model/effect.py` 既存メソッド、かがくへんかガス等で使われているのと
同じ仕組み、`core/ability_manager.py:140-159` 参照）で一時的にON/OFFする。
`types/literals.py` の `AbilityDisabledReason` に新しい理由 `"リーサル計算"` を追加する:

```python
AbilityDisabledReason = Literal[
    "consumed", "かがくへんかガス", "かたやぶり", "シャドーレイ", "とくせいなし", "フォトンゲイザー", "メテオドライブ",
    "リーサル計算",
]
```

`event_manager.py:200` の `_check_handler_validity` は `subject.ability.enabled` を
発火の都度動的にチェックしているため、ハンドラの再登録は不要でこの一時無効化だけで
確実に該当ハンドラをスキップできる。

`LethalContext`（`core/lethal.py`）に `damage_dist_full: StateDist | None = None` を追加し、
2回目の呼び出し結果が1回目と異なる場合のみ設定する（同じなら特性が実質発動していないので
`None` のまま — 例えば非満タン枝しか無く2回目の呼び出し自体スキップされた場合)。

`ctx.damage_dist` を書き換える既存 `ON_BEFORE_HIT` ハンドラは2つだけ
（`おやこあい_boost_damage`、`ばけのかわ_block_damage`）。両方とも `ctx.damage_dist_full`
が設定されていれば同じ変換を追随させる（1行追加ずつ）。

かたやぶり等によるマルチスケイル/テラスシェルの無効化は、通常戦闘と同じ既存の
イベント発火の仕組み（`ignored_disable_reasons` 等）がそのまま働くため、ここで
明示的にチェックする必要はない（[[feedback_no_gas_mold_check]] 参照）。

### B. がんじょう・きあいのタスキ: 新規 `LethalEvent.ON_APPLY_DAMAGE`
ユーザーコメント:　既存のON_BEFORE_HITイベントでダメージを書き換えてはどうか
`enums/event.py` の `LethalEvent` に `ON_APPLY_DAMAGE` を追加。ダメージ適用後・
満タン由来の枝にのみ適用するイベント。

`core/lethal.py` に `_apply_damage` を新設し、既存の
```python
hp_dist = subtract_dist(hp_dist, ctx.damage_dist, minimum=0)
_update_hp(ctx.defender, hp_dist)
```
を
```python
hp_dist = _apply_damage(battle, ctx, hp_dist)
_update_hp(ctx.defender, hp_dist)
```
に置き換える:

```python
def _apply_damage(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """満タン枝と非満タン枝でダメージ適用を分ける。

    満タン枝には damage_dist_full（未設定なら damage_dist）を適用してから
    ON_APPLY_DAMAGE ハンドラ（がんじょう・きあいのタスキ等のHP1耐え）を通す。
    非満タン枝には damage_dist をそのまま適用する。
    該当ハンドラが無ければ通常の subtract_dist(hp_dist, ctx.damage_dist) と完全に同じ結果になる。
    """
    max_hp = ctx.defender.max_hp
    full_states = {s: f for s, f in hp_dist.items() if s.value == max_hp}
    other_states = {s: f for s, f in hp_dist.items() if s.value != max_hp}

    result: StateDist = defaultdict(int)
    if full_states:
        dmg = ctx.damage_dist_full if ctx.damage_dist_full is not None else ctx.damage_dist
        full_result = subtract_dist(full_states, dmg, minimum=0)
        for h in _get_handlers(LethalEvent.ON_APPLY_DAMAGE, battle, ctx):
            full_result = h.func(battle, ctx, full_result)
        for s, f in full_result.items():
            result[s] += f
    if other_states:
        for s, f in subtract_dist(other_states, ctx.damage_dist, minimum=0).items():
            result[s] += f
    return dict(result)
```

`handlers/lethal.py` に追加（五十音順の位置、`scripts/sort_handlers.py` で整列）:

```python
def _survive_at_full_hp(hp_dist: StateDist, consume: Literal["ability", "item"]) -> StateDist:
    """満タン枝でHPが0になった状態をHP1に補正する（がんじょう/きあいのタスキ共通処理）。

    呼び出し側で hp_dist は「満タン枝のみ・ダメージ適用後」に絞られているため、
    ここでは value == 0 かどうかだけを見ればよい。
    consume="item" のときは補正と同時に item_enabled を False にする（きあいのタスキの消費）。
    consume="ability" のときは何度でも発動する（がんじょうは消費しない）。
    """
    new_dist: StateDist = defaultdict(int)
    for state, freq in hp_dist.items():
        flag = state.ability_enabled if consume == "ability" else state.item_enabled
        if state.value == 0 and flag:
            state = State(
                1,
                ability_enabled=state.ability_enabled,
                item_enabled=False if consume == "item" else state.item_enabled,
            )
        new_dist[state] += freq
    return dict(new_dist)


def がんじょう_survive_lethal(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """がんじょう: 満タン状態から瀕死になった場合、HP1で耐える。(ON_APPLY_DAMAGE / subject="defender")

    何度でも発動する。docs/spec/abilities/がんじょう.md 20行目参照。
    """
    return _survive_at_full_hp(hp_dist, consume="ability")


def きあいのタスキ_survive_ohko(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """きあいのタスキ: 満タン状態から瀕死になった場合、HP1で耐えて消費する。
    (ON_APPLY_DAMAGE / subject="defender")

    docs/spec/items/きあいのタスキ.md 参照。多段技の2発目以降は item_enabled=False
    により発動しない。
    """
    return _survive_at_full_hp(hp_dist, consume="item")
```

`data/ability.py` の `"がんじょう"` に `lethal_handlers={LethalEvent.ON_APPLY_DAMAGE:
LethalHandler(l.がんじょう_survive_lethal, subject="defender")}` を追加。
`data/item.py` の `"きあいのタスキ"` に同様に `LethalHandler(l.きあいのタスキ_survive_ohko,
subject="defender")` を追加。

優先順位: `_get_pokemon_handlers` は ability→item の順で候補を積み、`_get_handlers` は
`priority` でスタブルソートするため、両方デフォルト優先度のままで「がんじょうが先に発動し、
きあいのタスキは消費されない」という仕様(`docs/spec/items/きあいのタスキ.md` 26行目)を
自動的に満たす（がんじょうが先に `state.value` を1へ補正すれば、後段のきあいのタスキは
`state.value == 0` を満たさず何もしない）。

マルチスケイル(A)ときあいのタスキ(B)を両方持つケース（例: マルチスケイル所持カイリューが
きあいのタスキを持つ）も、`_apply_damage` 内の処理順（A: `damage_dist_full` 適用 →
`subtract_dist` → B: `ON_APPLY_DAMAGE`）で自然に正しく動作する（先に半減、それでも
致死ならタスキが耐える）。

## 変更対象ファイル

| ファイル | 変更内容 |
|---|---|
| `src/jpoke/types/literals.py` | `AbilityDisabledReason` に `"リーサル計算"` を追加 |
| `src/jpoke/enums/event.py` | `LethalEvent` に `ON_APPLY_DAMAGE` を追加 |
| `src/jpoke/core/lethal.py` | `LethalContext.damage_dist_full` 追加。`_run_move` のダメージ計算部分に「印を持つ特性のみ2回呼ぶ」分岐を追加。`_apply_damage` を新設し `subtract_dist` 呼び出し箇所を置き換え。`_update_hp` は変更しない |
| `src/jpoke/handlers/lethal.py` | `_survive_at_full_hp` / `がんじょう_survive_lethal` / `きあいのタスキ_survive_ohko` を追加。`おやこあい_boost_damage` / `ばけのかわ_block_damage` を `damage_dist_full` 追随の1行ずつ更新 |
| `src/jpoke/data/ability.py` | `"マルチスケイル"` `"ファントムガード"` `"テラスシェル"` の `flags` に `"full_hp_damage_modifier"` を追加。`"がんじょう"` に `lethal_handlers` 追加 |
| `src/jpoke/data/item.py` | `"きあいのタスキ"` に `lethal_handlers` 追加 |
| `tests/test_lethal.py` | 新規テスト追加（下記） |
| `docs/progress/ability.md` / `docs/progress/item.md` | がんじょう・きあいのタスキ・マルチスケイル・ファントムガード・テラスシェルの `リーサル実装` / `リーサルテスト` 列を `n/a` → `x` に更新 |

## テスト方針

1. `test_がんじょう_満タンからHP1で耐える` / `test_がんじょう_満タンでなければ発動しない`
2. `test_きあいのタスキ_満タンからHP1で耐えて消費`（2発目は耐えない）
3. `test_がんじょうときあいのタスキ_がんじょうが優先`（きあいのタスキが消費されない）
4. `test_マルチスケイル_満タン非満タン混在時も枝ごとに正しく半減`:
   `_update_hp`（最小値代表）方式だと壊れる混在分布の回帰テスト。自然な戦闘設定だけで
   安定再現するのが難しい場合は `from jpoke.core import lethal as lethal_module` で
   `_run_move`/`_apply_damage` を直接呼ぶホワイトボックステストとする。
5. `test_テラスシェル_満タン時タイプ相性を等倍に丸める`
6. 既存テスト（`test_マルチスケイル_ダメージ半減`, `test_多段技マルチスケイル_1ヒット目のみ半減`,
   `test_ばけのかわ_*`, `test_おやこあい_2ヒット目ダメージ加算`, タイプ半減きのみ系）が
   変更後も全てパスすることを回帰確認する。

## リスクと対策

- **リスク**: `"full_hp_damage_modifier"` フラグの付け忘れで、将来追加される同種の特性が
  この仕組みに乗らない。
  - **対策**: 新しい特性を実装する計画書のレビュー時に、
    「`defender.hp == defender.max_hp` を見るダメージ修正か」を確認する観点を明記する。
- **リスク**: `calc_damages` を2回呼ぶことによるパフォーマンス低下。
  - **対策**: 該当特性を持つ defender かつ hp_dist に満タン枝がある場合のみ発生し、
    対象特性は3種類のみ（マルチスケイル・ファントムガード・テラスシェル）。
    リーサル計算はそもそも複数回 `calc_damages` を呼ぶ設計であり、影響は限定的。

## 検証コマンド

```powershell
python scripts/sort_handlers.py src/jpoke/handlers/lethal.py
python scripts/sort_data/sort_abilities.py
python scripts/sort_data/sort_items.py
python scripts/sort_tests.py tests/test_lethal.py
python scripts/generate_test_list.py
python -m pytest tests/ -v
```
