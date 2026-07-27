# 実装計画: 致死率計算（lethal）における固定ダメージ技対応

更新日: 2026-07-27
ブランチ: `fix/lethal-fixed-damage-moves`

## 背景・根本原因

`Battle.calc_lethal` は実戦の `move_executor.py::_execute_hit` と異なり
`Event.ON_MODIFY_MOVE_DAMAGE` を一切発火しない（`core/lethal.py::_calc_damage_dist` は
`battle.calc_damages(...)` のみを呼ぶ）。加えて `core/damage.py:91-92` の
`if not move.base_power: return [0]` により、威力0/Noneの技（固定ダメージ・割合ダメージ・
一撃必殺・カウンター系）は lethal 計算で常にダメージ0＝致死率0%になる。

`ON_MODIFY_MOVE_DAMAGE` をそのまま lethal から発火する案は採らない。実HPを削る・
アイテムを奪う等の副作用を持つハンドラが混在し、かつ defender 側のハンドラ（ばけのかわ・
がんじょう・きあいのタスキ）は既に `LethalEvent` 側で実装済みのため二重計上になる
（みがわりは調査の結果、現時点で lethal_handlers 未登録・未対応であることが判明した。
本計画のスコープ外の既存ギャップであり、今回は変更しない）。

## 採用する設計

既存の `LethalEvent` / `LethalHandler` フレームワークに、技ごとの固定ダメージハンドラを
追加する。実戦ハンドラ（`handlers/move_attack.py`）の計算式をそのままミラーする。

### 1. コア変更（`src/jpoke/core/lethal.py`）

- `LethalContext` に `damage_from_hp: Callable[[int], int | list[int]] | None = None` を追加。
  「枝ごとの防御側HPからダメージを決める関数」。設定されている間は
  `damage_dist` / `damage_dist_full` の代わりにこちらが使われる。
- `_calc_damage_dist` の先頭で毎ヒット `ctx.damage_from_hp = None` にリセットする
  （`damage_dist_full` と同じ扱い。ヒットごとに再設定される前提）。
- `_apply_damage` を分岐: `ctx.damage_from_hp is not None` のとき新設の
  `_apply_damage_by_branch` に委譲する。
  - 枝（State）ごとに `ctx.damage_from_hp(state.value)` を呼び、`to_dist(...)` で
    その枝専用のダメージ分布に正規化し、`subtract_dist({state: freq}, branch_dmg, minimum=0)`
    でその枝だけに適用する。
  - HP満タンの枝（`state.value == max_hp`）には既存どおり
    `LethalEvent.ON_APPLY_DAMAGE` ハンドラ（がんじょう・きあいのタスキ）を通す。
    これにより一撃必殺技をがんじょう/きあいのタスキが防ぐ挙動が自然に再現される
    （一撃必殺のダメージ＝満タンHPそのものなので、満タン枝は必ずこの経路を通る）。
  - 処理後、`ctx.damage_dist` を「実際に適用されたダメージの周辺分布」（各枝の出現頻度で
    重み付けして合算したもの）に更新する（`LethalHitResult.damage_dist` 等の記録用）。
  - `damage_dist_full`（マルチスケイル等の満タン分岐）はこの経路では参照しない。
    固定ダメージ技は `base_power` が None/0 のため `_calc_damage_dist` の
    `needs_full_hp_split` 分岐（`battle.calc_damages` を2回呼ぶ経路）に到達せず、
    `damage_dist_full` は常に `None` のまま（＝両者は実質排他）。ただし例外として
    みねうち（Tier1、後述）は実際の `base_power` を持つ通常攻撃技なので理論上は
    `needs_full_hp_split` に該当し得るが、みねうちを持つ技は「相手を瀕死にしない」
    という別の絶対制約があるため、フルHP限定の特殊ダメージ補正（マルチスケイル等）が
    絡んでも `damage_from_hp` 経由でHP-1キャップが最終防衛ラインとして効く
    （キャップ処理は `ctx.damage_dist`＝既に補正適用済みの値を土台にするため、
    マルチスケイル補正自体は正しく反映されたうえでキャップされる）。

### 2. 技ごとのハンドラ（`src/jpoke/handlers/lethal.py`）

共通ヘルパー:
- `_is_immune(battle, ctx) -> bool`: タイプ相性0倍、またはふしぎなまもり
  （効果抜群でない攻撃技を無効化）による免疫を判定する。
  `battle.damage_calculator.calc_def_type_modifier(AttackContext(...))` を直接呼ぶ
  （`core/move_executor.py::_check_hit_by_type` が実戦で使っているのと全く同じ関数）。
  これが発火する `Event.ON_CALC_DEF_TYPE_MODIFIER` ハンドラ（きもったま・しんがん・
  テラスシェル・らんきりゅう・ねらいのまと・フライングプレス・フリーズドライ）は
  すべて読み取り専用・副作用なしを確認済みのため、lethal計算中（deepcopy済みの
  battle）で呼んでも安全。ちょすい・よびみず・そうしょく・どしょく・ひらいしん等の
  「吸収して行動自体をブロックする」系はこの関数の対象外（`Event.ON_BEFORE_APPLY_MOVE`
  という別経路で、lethal側は元々どの技に対してもモデル化していない既存の制約のため）。
  かたやぶり等の相手特性無視効果も、lethal計算では `Event.ON_BEGIN_MOVE` 相当が
  一切モデル化されていない（`data/ability.py` のかたやぶり系に `lethal_handlers` 登録が
  無いことを確認済み）ため本関数でも考慮しない。これは今回のスコープではなく
  lethal システム全体の既知の未対応事項。
- `_zero_damage(ctx)`: `damage_dist` / `damage_dist_full` / `damage_from_hp` を
  まとめてダメージ0にリセットする（ばけのかわ等、ダメージを完全に無効化するハンドラ用）。

Tier1（固定値・比例・一撃必殺・みねうち）:

| 技 | 関数 | priority | 式 |
|---|---|---|---|
| ナイトヘッド・ちきゅうなげ | `level_fixed_damage` | 15 | 一律 `attacker.level`（免疫なら0） |
| いかりのまえば・カタストロフィ | `half_damage` | 15 | 枝依存 `max(1, hp // 2)`（免疫なら0） |
| がむしゃら | `がむしゃら_modify_damage` | 15 | 枝依存 `max(0, hp - attacker.hp)` |
| いのちがけ | `いのちがけ_modify_damage` | 15 | 一律 `attacker.hp`。適用後 `attacker.hp = 0` を直接代入（lethal.py の既存慣行`_update_hp`と同様の直接代入に倣う） |
| つのドリル・ハサミギロチン・じわれ・ぜったいれいど | `ohko_damage` | 15 | 枝依存 `hp`（そのまま＝満タン以外も含め常にHP0にする。免疫なら0） |

（実装時に判明した追加事項）ぜったいれいど⇔こおりタイプは通常のタイプ相性表では
0.5倍でしかなく `calc_def_type_modifier`（`_is_immune`）では検出できない。実戦は
`ぜったいれいど_check_ice_immunity`（`Event.ON_TRY_MOVE_2`）という本技専用の判定を
別途持っているため、`ohko_damage` 内に `ctx.move.name == "ぜったいれいど" and
ctx.defender.has_type("こおり")` の個別分岐を追加した（動作確認スクリプトの
「ぜったいれいど vs フリーザー」で当初この無効化が漏れていたのを発見して追加した）。
| みねうち | `みねうち_modify_damage` | 15 | 枝依存: 既に `_calc_damage_dist` で計算済みの通常ダメージ分布（`ctx.damage_dist`）を捕捉し、`hp<=1` なら0、それ以外は `min(v, hp-1)` で各ロールをキャップ |

Tier2（反射系、`ctx.attacker.last_*_damage_received` 参照。calc実行時点のスナップショットに基づく）:

| 技 | 関数 | priority | 式 |
|---|---|---|---|
| カウンター | `カウンター_modify_damage` | 15 | 一律 `last_physical_damage_received * 2`（0以下なら失敗＝0） |
| ミラーコート | `ミラーコート_modify_damage` | 15 | 一律 `last_special_damage_received * 2` |
| メタルバースト・ほうふく | `メタルバースト_modify_damage` / `ほうふく_modify_damage` | 15 | 一律 `int(last_damage_received * 1.5)` |

Tier3: プレゼント — **未対応**（後述）。

priority=15 の根拠: LethalEvent は `.internal/spec/turn.md` に掲載が無い
lethal計算専用の制御イベントのため、既存の同種ハンドラ（`ON_BEFORE_HIT` に登録済みの
`おやこあい_boost_damage` ・ `ばけのかわ_block_damage` ・タイプ半減きのみ群、いずれも
デフォルト値100）を参照して決定する。固定ダメージ技のハンドラは
「`ばけのかわ_block_damage`（defender, 100）より必ず先に `damage_from_hp` を設定し、
ばけのかわ側がそれを正しくクリアできるようにする」「`おやこあい_boost_damage`
（attacker, 100）より必ず先に走り、おやこあい側が `damage_from_hp` の存在を見て
2ヒット目を正しく合成できるようにする」という2点を満たす必要があるため、100未満の
値であれば要件を満たす。実戦の `Event.ON_MODIFY_MOVE_DAMAGE` で固定ダメージ系
ハンドラ（`level_fixed_damage`/`half_damage`/`がむしゃら_modify_damage`/
`いのちがけ_modify_damage`）が使っている priority=15 とそのまま同じ数値を採用し、
実戦の優先度体系との対応関係を分かりやすくする（実戦のみねうち=60・一撃必殺=90・
カウンター系=デフォルトはLethalEvent側の名前空間には直接対応しないが、統一的に15を
採用しても上記2要件を満たすため問題ない）。

### 3. 既存ハンドラとの整合

- `ばけのかわ_block_damage`（`handlers/lethal.py:745`付近）: `damage_dist` /
  `damage_dist_full` を直接0にしている箇所を `_zero_damage(ctx)` 呼び出しに置き換える。
- `おやこあい_boost_damage`（`handlers/lethal.py:340`）: 実戦の
  `おやこあい_modify_hit_count`（`handlers/ability.py`）が2ヒット化の対象外とする
  技（がむしゃら・ころがる・アイスボール）と同じ条件を追加する。加えて `いのちがけ` も
  除外する（1ヒット目で使用者が必ずひんしになるため、実戦では2ヒット目のループ自体が
  `attacker.fainted` チェックで打ち切られ実行されない）。
  `ctx.damage_from_hp` が設定されている技（固定/枝依存ダメージ技）は、その関数を
  ラップして「1ヒット目と同じ式で得たダメージ値の1/4（最低1、0以下ならそのまま0）」を
  加算する（通常攻撃技向けの既存 `_add_second_hit` と同じ近似方針：2ヒット目を
  HP変化後に独立再計算するのではなく、1ヒット目の値を基準に減衰させる）。
  ただし `みねうち` は「このわざで相手を瀕死にさせない」という絶対制約があるため、
  ラップ後の合成値をさらに `hp-1` で再キャップする特殊処理を入れる
  （そうしないと2ヒット合成分がHP1のガードを超えてしまう）。
  一撃必殺技は合成後もどのみち0にクランプされる（`subtract_dist(..., minimum=0)`）ため
  追加のガードは不要（数値的に無害）。

## 対象技一覧（実装範囲）

Tier1: ナイトヘッド・ちきゅうなげ・いかりのまえば・カタストロフィ・がむしゃら・
いのちがけ・つのドリル・ハサミギロチン・じわれ・ぜったいれいど・みねうち

Tier2: カウンター・ミラーコート・メタルバースト・ほうふく

## 未対応事項

**プレゼント**: `プレゼント_roll_outcome`（実戦, `ON_TRY_MOVE_1`）が
40%/30%/10%/20%の確率で `ctx.move.base_power` を 40/80/120/0 に書き換えたうえで
通常のダメージ計算を行い、0のときは代わりに相手のHPを1/4回復する
（`プレゼント_apply_heal`）。この確率的な威力決定は `_calc_damage_dist` が
`battle.calc_damages` を呼ぶ**前**に行われる必要があるが、lethal 計算の
`LethalEvent.ON_BEFORE_HIT` は `_calc_damage_dist` の**後**にしか発火しない
（ダメージ計算前フックが存在しない）ため、既存アーキテクチャでは技の威力を
確率的に差し替えられない。さらに20%の確率で「ダメージではなく相手を回復する」
分岐があり、`damage_from_hp` は「ダメージ（HPを減らす量）」を返す関数として
`subtract_dist(..., minimum=0)` 一本で処理される設計のため、"回復"という上限
（`maximum=max_hp`）付きの逆方向の変化を同じ経路で表現できない。
確率混合（3通りの威力×16ロール＋回復20%）を正しく表現するには
「ダメージ計算前に威力を確率的に決定するフック」と「damage_from_hp が回復方向の
枝も返せるようにする（+ 上限クランプ）」という2つのアーキテクチャ拡張が追加で必要になり、
本タスクのスコープ（固定ダメージ技のダメージ0バグ修正）を超える。誤った近似
（回復20%を無視してダメージのみ扱う、威力を期待値で丸める等）を入れると
プレゼントの致死率が実際より過大/過小に出て、かえって信頼性を損なうため、
**今回は実装せず見送る**。

## 検証方針

scratchpad に動作確認スクリプトを書き、以下を確認する:
- ちきゅうなげ: レベル固定ダメージ、確定数が `max_hp / level` 相当
- いかりのまえば: 初回 `max_hp // 2`、2回目以降は残りHPに対して半減し続ける
- ぜったいれいど: 1発で致死率100%、がんじょう持ちには1発で倒せない
- みねうち: HPが1で止まり、致死率0%のまま
- がむしゃら・いのちがけ
- タイプ無効: ちきゅうなげ vs ゴースト、ぜったいれいど vs こおり → ダメージ0

`python -m pytest tests/ -q` で全テスト通過を確認する。

## レビュー結果（review-testエージェント、2026-07-27）

実戦ハンドラ（`handlers/move_attack.py`）との式の突合、`_is_immune` が発火する
`Event.ON_CALC_DEF_TYPE_MODIFIER` ハンドラの副作用有無、`_apply_damage_by_branch` の
頻度重み付け、`ALLOWED_FILES` の妥当性を確認した。結果はすべて「問題なし」だったが、
以下2点は実装時に想定されていなかった問題として見つかり、修正した。

1. **`いのちがけ_modify_damage` が `ctx.attacker.hp = 0` する副作用が、`moves` に
   [`("いのちがけ",1)`, `("じしん",1)`] のようなリストを渡した場合に、ひんしになった
   はずの攻撃側がそのまま次の技（じしん）を使ってしまう**バグがあった。
   `core/lethal.py::_lethal_loop` に `ctx.attacker.fainted` チェックを追加し、
   攻撃側がひんしになった場合は同ラウンドの `ctx_list` の残りの技とターン終了処理を
   スキップするよう修正した（`break`。ただし `return` にはせず、次の `atk` ラウンドへは
   進む。`moves=Move("いのちがけ")` を単独で繰り返し指定するケースでは、2回目以降は
   `hp_cost=0` により自然にダメージ0になり続けるだけ、という既存の想定挙動を壊さない
   ため）。
2. **`みねうち_modify_damage` が `base_damages = ctx.damage_dist` をクロージャに早期束縛
   していた**点。現在登録されている全ハンドラを調査した結果、`ON_BEFORE_HIT` の
   priority=15 より後に `ctx.damage_dist` を直接書き換えるハンドラは存在せず
   （`おやこあい_boost_damage` は `damage_from_hp` 経由に分岐する早期returnがあるため
   到達しない。タイプ半減きのみ群は `ctx.damage_dist` を変更しない設計）、現状では
   実害は無いことを確認した。ただし将来同種のハンドラが追加された際に取りこぼす
   リスクがあるため、`_capped` 内で `ctx.damage_dist` を呼び出し時に遅延参照する
   よう修正し、保守性を高めた。

いずれも `handlers/lethal.py` / `core/lethal.py` を直接修正済み。`tests/test_lethal.py`
に新規テスト20件（固定ダメージ技・比例ダメージ技・反射系・一撃必殺技・みねうち・
上記2点の回帰テストを含む）を追加し、全テストが通過することを確認した。
