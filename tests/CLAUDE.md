# テストユーティリティ API

`tests/test_utils.py` の各ヘルパーを再利用する。

## fuzz回帰テストのflaky対策（重要）

`tests/test_fuzz_regressions.py` のように `battle.step(...)` でターンを進行させた後、
`battle.actives[i].name == "..."` のように特定個体が場に残っている/交代済みであることを
断定するテストでは、**そのステップ内で実行される攻撃技のダメージ乱数・急所判定を
`t.fix_damage(battle, ...)` で必ず固定すること**。固定していないと、まれに想定外の
ポケモンが急所+乱数上振れで瀕死になり、意図しない強制交代・死に出しが起きて
アサーションが間欠的に失敗する（同一原因のflakyがこれまで3回、個別に発見・修正された）。

判断の目安:
- そのステップで攻撃技（`Command.MOVE_x`）が実行され得るか（交代・だっしゅつパック等の
  割り込みで攻撃側自身が行動前に交代してしまい、技が一度も実行されない場合は対象外）
- 攻撃対象が、アサーション対象と同じ側の「場に残る/交代先候補になり得るポケモン」か
- 対象のHPが、その技の急所・乱数上振れ込みの最大ダメージより十分高いか
  （目安: メガシンカ等で攻撃側が強化されている、または対象が低耐久で瀕死交代直後など、
  最大ダメージがHPに対して無視できない場合は要注意）

`t.fix_damage(battle, 0)` で無関係な攻撃のダメージを無害化するのが基本形（既存の修正例を
参照）。命中率も固定したい場合は `accuracy=100` を、急所だけ排除したい場合は
`critical_mode` 等 `start_battle` の他の引数も確認すること。

```python
# バトルのセットアップ
battle = t.start_battle(
    team0=[Pokemon("ピカチュウ", ability_name="せいでんき")],
    team1=[Pokemon("カビゴン")],
    weather=("はれ", 5),
    accuracy=100,          # 命中率を固定
    secondary_chance=1.0,  # 追加効果を必ず発動
)

# 技の実行
t.run_move(battle, player_idx=0, move_idx=0)

# ポケモンの交代
t.run_switch(battle, player_idx=0, new_idx=1)

# ターン終了処理
t.end_turn(battle)

# 状態異常の適用
t.apply_ailment(battle, player_idx=0, ailment_name="やけど", by_foe=True)

# ダメージ固定 / 乱数固定
t.fix_damage(battle, 100)
t.fix_random(battle, 0.0)

# アイテム変更
t.change_item(battle, mon, "たべのこし")

# 行動順の取得
order = t.get_action_order(battle)

# AttackContext の構築
ctx = t.build_context(battle, player_idx=0, move_idx=0)
```
