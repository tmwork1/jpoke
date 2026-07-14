# テストユーティリティ API

`tests/test_utils.py` の各ヘルパーを再利用する。

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
