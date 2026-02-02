# 作用のヒエラルキーと実装原則

複数の作用が相互に影響する場合、どの作用をどこに実装すべきかを明確化。

## 基本原則

### 1. 効果の所有者原則

**効果は、それを所有するエンティティに実装**

| 効果 | 所有者 | 実装場所 |
|-----|-------|---------|
| 天候を「はれ」にする | 特性「ひでり」 | `data/ability.py` |
| はれターンを延長 | アイテム「あついいわ」 | `data/item.py` |
| ほのお技の威力1.5倍 | 天候「はれ」 | `data/field.py` |
| ソーラービームの溜めなし | 技「ソーラービーム」 | `data/move.py` |
| 晴れ時に素早さ2倍 | 特性「ようりょくそ」 | `data/ability.py` |

### 2. 単一責任の原則

各エンティティは自分の責任範囲のみを実装。

```python
# 推奨
# data/field.py - 天候「はれ」
"はれ": FieldData(
    handlers={
        Event.ON_CALC_POWER_MODIFIER: Handler(はれ_power_modifier, ...)
    }
)

# data/ability.py - 特性「ひでり」
"ひでり": AbilityData(
    handlers={
        Event.ON_SWITCH_IN: AbilityHandler(
            partial(common.activate_weather, weather="はれ", ...),
            ...
        )
    }
)
```

### 3. イベント駆動の原則

相互作用はイベントを通じて実現。エンティティ間は直接依存しない。

## 作用のヒエラルキー

### レイヤー1: 状態変更 (State Modification)

天候地形場の状態揮発性状態を**変更**する作用

| 作用 | 実装場所 | 例 |
|------|---------|---|
| 天候変更 | 技データ | にほんばれ、あまごい |
| 天候変更 | 特性データ | ひでり、あめふらし |
| 地形変更 | 技データ | エレキフィールド |
| 地形変更 | 特性データ | エレキメイカー |
| 揮発性状態付与 | 技データ | みがわり、アンコール |

**実装方法**: `common.activate_weather()`, `common.activate_terrain()` 等を使用

```python
# 技「にほんばれ」
"にほんばれ": MoveData(
    handlers={
        Event.ON_HIT: MoveHandler(
            partial(common.activate_weather, weather="はれ", source_spec="attacker:self"),
            subject_spec="attacker:self",
        )
    }
)
```

### レイヤー2: 状態影響 (State Effects)

現在の状態に応じて**影響**を与える作用

| 作用 | 実装場所 | 例 |
|------|---------|---|
| 天候による威力補正 | フィールドデータ | はれ、あめ |
| 地形による威力補正 | フィールドデータ | エレキフィールド |
| 揮発性状態の効果 | 揮発性データ | みがわり |

**実装方法**: フィールドデータまたは揮発性データの handlers に実装

```python
# data/field.py - 天候「はれ」
"はれ": FieldData(
    handlers={
        Event.ON_CALC_POWER_MODIFIER: Handler(
            はれ_power_modifier,  # ほのお技1.5倍、みず技0.5倍
            subject_spec="attacker:self",
            log="never",
        )
    }
)
```

### レイヤー3: 特性アイテムによる補正 (Ability/Item Modifiers)

特性アイテムが**補正**を加える作用

| 作用 | 実装場所 | 例 |
|------|---------|---|
| 特性による威力補正 | 特性データ | てきおうりょく、テクニシャン |
| アイテムによる補正 | アイテムデータ | いのちのたま、こだわりハチマキ |
| 特性による状態耐性 | 特性データ | めんえき、じゅうなん |

**実装方法**: 特性データまたはアイテムデータの handlers に実装

```python
# data/ability.py - 特性「てきおうりょく」
"てきおうりょく": AbilityData(
    handlers={
        Event.ON_CALC_POWER_MODIFIER: AbilityHandler(
            てきおうりょく_power,
            subject_spec="attacker:self",
            log="never",
        )
    }
)
```

## 作用の組み合わせ例

### 例1: はれ状態での技威力計算

```
1. 特性「ひでり」発動 (レイヤー1)
    天候を「はれ」に変更

2. 技「かえんほうしゃ」使用
    ON_CALC_POWER_MODIFIER イベント発火

3. 天候「はれ」の補正 (レイヤー2)
    ほのお技威力 1.5倍

4. 特性「てきおうりょく」の補正 (レイヤー3)
    タイプ一致技威力 さらに1.3倍

5. アイテム「いのちのたま」の補正 (レイヤー3)
    技威力 さらに1.3倍
```

## 実装ガイドライン

###  推奨

- 効果は所有者に実装
- イベント経由で作用
- 共通処理は `handlers/common.py` に集約
- 名前付き関数を使用

###  回避

- 他のエンティティの効果を実装
- 直接的な依存関係
- Lambda の多用

## 優先度の設定

同じイベントで複数のハンドラが発動する場合、`priority` で順序を制御:

```python
Handler(
    func,
    priority=10,  # 小さいほど先に実行
    ...
)
```

## デバッグのコツ

- `log="always"` で動作確認
- Handler 名を明確に（Lambda 避ける）
- EventManager のログで発火順序確認

## 次のステップ

- アーキテクチャ詳細: `architecture.md`
- ワークフロー: `agents/workflow.md`
