# jpoke
ポケモンのシングル対戦シミュレータ

## 基本方針

- **ポケモンの仕様は第9世代（スカーレット・バイオレット）を参照する**
- **第9世代で実装されていない技・アイテム・特性・ポケモンなどは実装しない**

## ドキュメント方針

- `docs/spec/` は調査内容のみを記載し、実装・テスト・進捗管理は含めない

## プロジェクト構成

### コアシステム

- **Battle** ([core/battle.py](src/jpoke/core/battle.py)) - バトル全体を管理
- **TurnManager** ([core/turn.py](src/jpoke/core/turn.py)) - ターン進行制御
- **MoveExecutor** ([core/move_executor.py](src/jpoke/core/move_executor.py)) - 技の実行処理
- **DamageCalculator** ([core/damage.py](src/jpoke/core/damage.py)) - ダメージ計算
- **SpeedManager** ([core/speed.py](src/jpoke/core/speed.py)) - 行動順計算
- **EventManager** ([core/event.py](src/jpoke/core/event.py)) - イベント駆動システム
- **FieldManager** ([core/field_manager.py](src/jpoke/core/field_manager.py)) - フィールド効果管理
- **SwitchManager** ([core/switch.py](src/jpoke/core/switch.py)) - 交代処理

### データモデル

- **Pokemon** ([model/pokemon.py](src/jpoke/model/pokemon.py)) - ポケモンのデータ構造
- **Move** ([model/move.py](src/jpoke/model/move.py)) - 技のデータ構造
- **Ability** ([model/ability.py](src/jpoke/model/ability.py)) - 特性のデータ構造
- **Item** ([model/item.py](src/jpoke/model/item.py)) - 持ち物のデータ構造
- **Stats** ([model/stats.py](src/jpoke/model/stats.py)) - ステータス管理

### データ定義

- **ABILITIES** ([data/ability.py](src/jpoke/data/ability.py)) - 特性定義（299種）
- **ITEMS** ([data/item.py](src/jpoke/data/item.py)) - アイテム定義（154種）
- **FIELDS** ([data/field.py](src/jpoke/data/field.py)) - フィールド効果定義（18種）
- **VOLATILES** ([data/volatile.py](src/jpoke/data/volatile.py)) - 揮発性状態定義（24種）
- **AILMENTS** ([data/ailment.py](src/jpoke/data/ailment.py)) - 状態異常定義（6種）

### ハンドラシステム

- **AbilityHandlers** ([handlers/ability.py](src/jpoke/handlers/ability.py)) - 特性効果の実装
- **ItemHandlers** ([handlers/item.py](src/jpoke/handlers/item.py)) - アイテム効果の実装
- **MoveHandlers** ([handlers/move.py](src/jpoke/handlers/move.py)) - 技効果の実装
- **FieldHandlers** ([handlers/field.py](src/jpoke/handlers/field.py)) - フィールド効果の実装
- **VolatileHandlers** ([handlers/volatile.py](src/jpoke/handlers/volatile.py)) - 揮発性状態の実装
- **AilmentHandlers** ([handlers/ailment.py](src/jpoke/handlers/ailment.py)) - 状態異常の実装

## 実装状況（2026年5月4日時点）

### 集計基準

- 特性・持ち物・技の進捗は、`src/jpoke/data/*.py` の `*Data(..., handlers={...})` 明示定義を実装済みとして集計する。
- 仕様書・テスト件数は進捗管理の補助指標として扱う。

### サマリー（コード基準）

| カテゴリ | 実装済み | 総数 | 進捗率 |
| --- | ---: | ---: | ---: |
| **特性** | 220 | 300 | 73.3% |
| **持ち物** | 59 | 154 | 38.3% |
| **技** | 130 | 693 | 18.8% |

### 仕様書・テストの補助指標

| カテゴリ | 仕様書ファイル数 | 専用テスト関数数 |
| --- | ---: | ---: |
| **特性** | 291 | 325 |
| **持ち物** | 38 | 10 |
| **技** | 64 | 12 |

最新の詳細一覧は以下を参照:

- [progress/ability.md](progress/ability.md)
- [progress/item.md](progress/item.md)
- [progress/move.md](progress/move.md)

## 主要機能

### イベント駆動アーキテクチャ

全ての効果（特性、アイテム、技など）はイベントハンドラとして実装され、優先度順に実行されます。

```python
# 例: 特性「いかく」の実装
def intimidate_on_switch_in(events, player, mon):
    """場に出たときに相手の攻撃を1段階下げる"""
    opponent = player.opponent
    if opponent.active:
        events.emit(イベントType.CHANGE_STAT_STAGE, 
                   mon=opponent.active, 
                   stat=Stat.ATTACK, 
                   delta=-1)
```

### ダメージ計算システム

ポケモンの公式に準拠したダメージ計算を実装:

$$
\text{Damage} = \left\lfloor \left\lfloor \left\lfloor \frac{\text{Level} \times 2}{5} + 2 \right\rfloor \times \frac{\text{Power} \times \text{Attack}}{\text{Defense}} \right\rfloor \times \text{Mod} + 2 \right\rfloor
$$

### 行動順計算

すばやさランク補正、特性、フィールド効果を考慮した行動順を決定します。

## テスト

pytest でテストを実行します。テストコードは **失敗時のみ出力** が表示されます。成功したテストは結果を表示せずに進行します。

```bash
# 全テスト実行
python tests/run.py

# または pytest を直接使用
pytest tests -v

# 個別テスト実行
pytest tests/test_ability.py -v
pytest tests/test_item.py -v
pytest tests/test_move.py -v
```

## ライセンス

MIT License
