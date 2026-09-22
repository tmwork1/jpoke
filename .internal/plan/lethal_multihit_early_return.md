# 計画: calc_lethal の連続技(多段ヒット)が途中で打ち切られ確定数が過小評価される件

更新日: 2026-09-22

## 症状

poke-guide のダメージ計算で、ドデカバシ(スキルリンク)のタネマシンガン5発
→ カバルドン(H215)が、1攻撃(5ヒット)合計 110〜130 ダメージ(2攻撃で 220〜260 ≥ 215)
であるにもかかわらず「乱2 3.36%」と判定される。本来は「確2」。

jpoke 単体でも再現する(poke-guide 側は `Battle.calc_lethal()` の結果をそのまま
表示しているだけで、poke-guide 側の問題ではない)。

```python
from jpoke import Pokemon, Move
from tests import test_utils as t

# tests/test_lethal.py 冒頭の参考値 1.2 「スケイルショット 38~48/hit (5hit: 確定1発)」
b = t.start_battle(team0=[Pokemon("ガブリアス")], team1=[Pokemon("カイリュー")])
r = t.calc_lethal(b, player_idx=0, moves=[(Move("スケイルショット"), 5)])
[(x.attack_count, x.hit_count, round(x.lethal_probability, 4)) for x in r]
# 実際: [(1, 1, 0.0), (1, 2, 0.0), (1, 3, 0.0), (1, 4, 0.8191)]
# 期待: [..., (1, 4, 0.8191), (1, 5, 1.0)]
```

5ヒット指定なのに4ヒット目で結果が終わり、致死率は「4ヒット時点の 81.91%」のまま。
`max_attack=2` にしても同じ4件しか返らない。

ドデカバシの例では、2攻撃目の4ヒット目(累計9ヒット、22〜26×9 = 198〜234)で
最高乱数側の枝だけが HP0 に到達し、そこで打ち切られて5ヒット目が適用されないため、
「9ヒット時点の致死率 3.36%」が2攻撃目の値として返っている。

## 原因

`src/jpoke/core/lethal.py` `_lethal_loop()` のヒットループ内の早期 return:

```python
for atk in range(1, max_attack + 1):
    for n_hits, ctx in ctx_list:
        ...
        for hit in range(1, n_hits + 1):
            ctx.hit_count = hit
            hp_dist = _run_move(battle, ctx, hp_dist, every_event_handlers)
            results.append(LethalHitResult(...))
            if fainted(hp_dist):      # ← ここ
                return results
            ...
        hp_dist = _run_turn_end(...)
        results[-1].hp_dist = hp_dist
        if fainted(hp_dist):
            return results
```

`fainted(dist)`(`lethal.py:144`)は「分布内に **HP0 の枝が1つでもあれば** True」。
これは「致死枝が初めて現れた攻撃回で打ち切り、その時点の `lethal_probability` を
乱数N発の確率として返す」という攻撃単位の打ち切り条件としては正しいが、
ヒットループの内側に置かれているため、**1攻撃の途中(n_hits 未満)で一部の枝が
HP0 になった瞬間に残りのヒットが捨てられる**。

単発技(n_hits=1)では「攻撃=ヒット」なので影響がなく、連続技で
「途中ヒットで一部枝だけが落ちる」場合にのみ顕在化する。既存テスト
`test_オボンのみ_スケイルショット5発_乱数1発` が5ヒット目まで到達しているのは、
オボンのみ回復により4ヒット目までに HP0 の枝が生じないためで、この経路を
検証できていない。

### 副作用の範囲

1. **致死率の過小評価(本件)**: `results[-1].lethal_probability` が「途中ヒット時点」
   の値になる。poke-guide では確N判定が「確2 → 乱2 3.36%」のように誤る。
2. **打点の過小評価**: `LethalHitResult.damage_dist` は「そのヒット1発分」の分布で、
   利用側(poke-guide `pyodide-engine.ts` の `fold_damage_dist`)が全ヒット分を
   畳み込んで1攻撃の打点を作る。ヒットが捨てられると畳み込みの母数が減り、
   例えば5ヒット技が「4ヒット分の合計」として表示される。
3. `resume_from` で攻撃を1回ずつ繋ぐ利用(poke-guide の sequential/perAttack 系列)
   でも、繋ぎ元の `LethalHitResult` が途中ヒットのものになるため、以降の攻撃回の
   致死率がすべてずれる。

## 修正方針

### 前提: HP0 枝を残したままハンドラを回すことはできない

`_emit` / `_apply_handlers` は「分布内に HP0 枝が1つでもあれば全ハンドラをスキップ」し、
`_update_hp` は `ctx.defender.hp = min(...)` → 0 をセットする。このため、単にヒット
ループ内の早期 return を外して残りヒットを適用しても、致死枝が出た後のヒットでは
生存枝に対する ON_BEFORE_HIT(いかりのまえば等の `damage_from_hp` 設定・タイプ半減
きのみ)・ON_HIT(オボン等)が丸ごと抜け、以降の `calc_damages` も防御側 HP0 前提で
動く。道具・特性なしのケースでは正しく見えるが、道具・特性持ちで新たな不具合を
仕込むことになる。

### 本命: HP0 枝を入口で分離し、生存枝にだけ処理を通して末尾で合流する

意味的にも「ひんし後の枝にはヒットが発生しない」で正しく、`fainted` ガードと
`defender.hp = 0` の問題がまとめて消える。

```python
def _split_fainted(hp_dist: StateDist) -> tuple[StateDist, StateDist]:
    """(生存枝, HP0枝) に分ける。"""
    alive = {s: f for s, f in hp_dist.items() if s.value > 0}
    dead = {s: f for s, f in hp_dist.items() if s.value == 0}
    return alive, dead


def _merge_dist(alive: StateDist, dead: StateDist) -> StateDist:
    result: StateDist = defaultdict(int, alive)
    for s, f in dead.items():
        result[s] += f
    return dict(result)
```

適用箇所:

1. **`_run_move` 全体を包む**: 入口で分離し、`_calc_damage_dist` → ON_BEFORE_HIT →
   `_apply_damage` → `_update_hp` → ON_HIT を生存枝のみで実行、出口で合流する。
   生存枝が空なら `ctx.damage_dist = to_dist(0)` にして即返す。
2. **`_emit` の `if fainted(hp_dist): return hp_dist` を分離+合流に置き換える**。
   `_before_move` / `_run_turn_end` は `_emit` を直接呼ぶため、ここを直さないと
   `resume_from` に HP0 枝を含む `results[-1]` を渡したときに ON_BEFORE_MOVE が
   丸ごとスキップされる(現状の隠れた不具合。poke-guide の sequential/perAttack
   系列はまさにこの経路)。
3. **`_apply_handlers` のハンドラ間ガードも分離方式にする**: 「このハンドラで 0 に
   なった枝は次のハンドラに渡さない」という意味は残す必要がある(例: ON_HIT 内で
   オボン回復より先に別ハンドラで 0 になった枝を回復させない)。

   ```python
   dead: StateDist = defaultdict(int)
   for h in handlers:
       hp_dist, d = _split_fainted(hp_dist)
       for s, f in d.items():
           dead[s] += f
       if not hp_dist:
           break
       hp_dist = h.func(battle, ctx, hp_dist)
   return _merge_dist(hp_dist, dead)
   ```
4. `_update_hp` は生存枝しか受け取らなくなるので自然に `min > 0` になる
   (生存枝が空のときに呼ばないよう注意)。

`_lethal_loop` 側はヒットループ内の `if fainted(hp_dist): return results` を削除し、
ループ後・`_run_turn_end` 前に移す(攻撃単位の打ち切り):

```python
            attacker_fainted_mid_round = False
            for hit in range(1, n_hits + 1):
                ctx.hit_count = hit
                hp_dist = _run_move(battle, ctx, hp_dist, every_event_handlers)
                results.append(LethalHitResult(...))

                # いのちがけ等、攻撃側自身がひんしになる技を使った場合はそこで打ち切る。
                if ctx.attacker.fainted:
                    attacker_fainted_mid_round = True
                    break

            if fainted(hp_dist):
                # 1つでも致死枝が出たらこの攻撃回で打ち切る。ヒットループ内では
                # 打ち切らない(連続技の途中で切ると生存枝への残りヒットが捨てられ、
                # 致死率・打点が過小になる)。
                return results

            if attacker_fainted_mid_round:
                break

            hp_dist = _run_turn_end(...)
            ...
```

防御側致死の return を攻撃側ひんしの break より先に判定する。

### `LethalHitResult.damage_dist` の仕様

分離後、`damage_dist` は **「そのヒットを受けた生存枝に対するダメージ分布」**
(全枝が既に HP0 なら `{0: 1}`)になる。HP0 枝に 0 ダメージを混ぜない
(poke-guide の `fold_damage_dist` は全ヒットを畳み込んで打点を作るため、混ぜると
打点表示の最小値が 0 に汚れる)。`LethalHitResult` の docstring に明記し、
テスト4で固定する。

### 検討事項

- **ターン終了処理のスキップ**: 現状も「致死枝が1つでもあればターン終了処理
  (たべのこし回復等)を丸ごとスキップ」しており、生存枝にとっては回復が
  抜けている。これは既存挙動で本件の範囲外とし、変更しない。ただし分離ヘルパを
  入れると、将来「致死枝が出ても `max_attack` まで回して攻撃回ごとの致死率を返す」
  (乱1 3% で止まらず乱2 の値も出す)拡張が容易になる。
- `ctx.attacker.fainted`(いのちがけ等)との優先順位: 防御側致死を先に判定して
  return し、攻撃側のみひんしなら従来どおり次の atk ラウンドへ進む。

## テスト

`tests/test_lethal.py` に追加:

1. `test_多段技_途中ヒットで致死枝が出ても全ヒット適用する`
   ガブリアス → カイリュー(道具なし) スケイルショット5ヒット。
   `[r.hit_count for r in results] == [1, 2, 3, 4, 5]`、
   `results[3].lethal_probability ≈ 0.8191`、`results[4].lethal_probability == 1.0`
   (ファイル冒頭の参考値 1.2 と一致させる)。
2. `test_多段技_2攻撃目の途中で致死枝が出ても確定数が正しい`
   ドデカバシ(いじっぱり・スキルリンク) タネマシンガン5ヒット →
   カバルドン(わんぱく・H252 = HP215)を `max_attack=2` で計算し、
   `results[-1].attack_count == 2`、`hit_count == 5`、`lethal_probability == 1.0`
   (1攻撃 110〜130、2攻撃 220〜260 ≥ 215)。
3. `resume_from` 経由でも同じ結果になること(1攻撃目の `results[-1]` を渡して
   2攻撃目を計算し、`lethal_probability == 1.0`)。
4. `test_多段技_致死枝が出た後も生存枝のダメージ分布が汚れない`
   テスト1で `results[4].min_damage == 38`, `results[4].max_damage == 48`
   (HP0 枝の 0 ダメージが混ざらない)。
5. `test_多段技_致死枝が出た後も生存枝のヒット時ハンドラが動く`
   オボンのみ(ON_HIT)持ちの防御側で「4ヒット目で一部枝が HP0、残り枝がオボン
   発動域」になる HP を組み、5ヒット目の分布に回復が反映されていることを確認する
   (§修正方針の前提の退行検知用。具体的な数値は実装時に調整)。
6. `test_resume_from_HP0枝を含む分布から再開しても生存枝にON_BEFORE_MOVEが適用される`
   現状の隠れ不具合の回帰テスト。ON_BEFORE_MOVE を持つハンドラ(例: 攻撃側の
   状態や場の効果)を用意し、HP0 枝を含む `results[-1]` から再開したときに生存枝へ
   効果が乗ることを確認する。

既存の `test_オボンのみ_スケイルショット5発_乱数1発` / `test_多段技_ヒットごとに分布を記録`
/ `test_多段技マルチスケイル_1ヒット目のみ半減` は変更なしで通る想定
(いずれも途中ヒットで致死枝が出ないケース)。

## 影響先

- poke-guide `vendor/jpoke` は同一コードを同梱しているため、jpoke 側の修正後に
  vendor を更新して取り込む(poke-guide 側のコード変更は不要)。
- `README`/`docs` の calc_lethal 説明に「連続技はヒット単位で結果が積まれる」旨が
  あれば、「致死枝が出ても1攻撃分のヒットは最後まで記録される」ことを追記する。

## 備考

- 本修正は `main` から `feature/fix-lethal-multihit-early-return` を切って行う
  (`feature/calc-move-power` の差分は `e559661c7` でコミット済みのため混ざらない)。
