# 実装計画: ドラゴンスキン

作成日: 2026-06-04

## 効果
ノーマルタイプの技をドラゴンタイプに変換し、威力 1.2 倍にする。

## イベント／ハンドラ

| イベント | priority | subject_spec | 関数名 |
|---------|---------|-------------|--------|
| `ON_MODIFY_MOVE_TYPE` | 100 | `source:self` | `ドラゴンスキン_modify_move_type` |
| `ON_CALC_POWER_MODIFIER` | 100 | `attacker:self` | `ドラゴンスキン_modify_power` |

## 実装

`フェアリースキン` と完全に同じ構造。既存の `_skin_modify_move_type` / `_skin_boost_power` ヘルパーに引数を変えて委譲するだけ。

```python
def ドラゴンスキン_modify_move_type(battle, ctx, value):
    return _skin_modify_move_type(battle, ctx, value, from_type="ノーマル", to_type="ドラゴン")

def ドラゴンスキン_modify_power(battle, ctx, value):
    return _skin_boost_power(battle, ctx, value, trigger_type="ノーマル")
```

## data/ability.py 登録

```python
"ドラゴンスキン": AbilityData(
    handlers={
        Event.ON_MODIFY_MOVE_TYPE: h.AbilityHandler(
            h.ドラゴンスキン_modify_move_type,
            subject_spec="source:self",
        ),
        Event.ON_CALC_POWER_MODIFIER: h.AbilityHandler(
            h.ドラゴンスキン_modify_power,
            subject_spec="attacker:self",
        ),
    }
),
```

## テストケース
- ノーマル技がドラゴンタイプになる
- 威力が 1.2 倍になる（4915/4096 補正）
- 非ノーマル技はタイプ・威力とも変化なし
- テラスタル後もノーマル技は変換される
