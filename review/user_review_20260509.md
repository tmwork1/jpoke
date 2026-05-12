# ユーザーレビュー

2026/5/9

## 特性
### どくぼうそう
現状はどく技の威力が上がる効果として実装されているが、正しくはどく・もうどく状態のとき、物理技の威力が1.5倍になるという効果。
特性の仕様書(spec/ability/)とダメージ計算仕様 (spec/damage.md)を再確認して、実装とテストを修正する。

### ねつぼうそう
現状はほのお技の威力が上がる効果として実装されているが、正しくはやけど状態のとき、特殊技の威力が1.5倍になるという効果。
特性の仕様書(spec/ability/)とダメージ計算仕様 (spec/damage.md)を再確認して、実装とテストを修正する。

## ログ書き込み
battle.add_event_log()を使うパターンと、battle.event_logger.add()を直接呼び出すパターンが混在している。battle.add_event_log()に統一してコード量を減らす。

## Battleクラスに天候、フィールド、その他global field, side field を自由に設定・解除する関数を持たせる
テストやユーザーカスタマイズに便利

## テスト
### 補正係数の検証では、数値を左辺に置く
'''
4096 == assert t.calc_damage_modifier(battle, Event.ON_CALC_DAMAGE_MODIFIER)
'''

### かたやぶり
かたやぶりによる無効化テストは、_activate_mold_breaker()を使って疑似的に再現するより、
なるべく battle.move_executor.run_move() を使って実環境に近い条件でテストしたい。
battle.move_executor.run_move() で検証しづらいテストは、_activate_mold_breaker()を使う。

### test_utils.py
汎用関数の引数の atk_idx を省略不可にして明示させる

### 補正係数の検証では、数値を左辺に置く
'''
4096 == assert t.calc_damage_modifier(battle, Event.ON_CALC_DAMAGE_MODIFIER)
'''

### attacker, defender の定義を一行にまとめる
修正前
'''
    defender = battle.actives[0]
    attacker = battle.actives[1]
'''

修正後
'''
    defender, attacker = battle.actives
'''


## その他
コード中のTODOを確認