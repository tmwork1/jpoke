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
- **TurnController** ([core/turn_controller.py](src/jpoke/core/turn_controller.py)) - ターン進行制御
- **MoveExecutor** ([core/move_executor.py](src/jpoke/core/move_executor.py)) - 技の実行処理
- **DamageCalculator** ([core/damage.py](src/jpoke/core/damage.py)) - ダメージ計算
- **SpeedCalculator** ([core/speed_calculator.py](src/jpoke/core/speed_calculator.py)) - 行動順計算
- **EventManager** ([core/event.py](src/jpoke/core/event.py)) - イベント駆動システム
- **FieldManager** ([core/field_manager.py](src/jpoke/core/field_manager.py)) - フィールド効果管理
- **SwitchManager** ([core/switch_manager.py](src/jpoke/core/switch_manager.py)) - 交代処理

### データモデル

- **Pokemon** ([model/pokemon.py](src/jpoke/model/pokemon.py)) - ポケモンのデータ構造
- **Move** ([model/move.py](src/jpoke/model/move.py)) - 技のデータ構造
- **Ability** ([model/ability.py](src/jpoke/model/ability.py)) - 特性のデータ構造
- **Item** ([model/item.py](src/jpoke/model/item.py)) - 持ち物のデータ構造
- **Stats** ([model/stats.py](src/jpoke/model/stats.py)) - ステータス管理

### データ定義

- **ABILITIES** ([data/ability.py](src/jpoke/data/ability.py)) - 特性定義（304種）
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

## 実装状況（2026年2月7日時点）

### サマリー

| カテゴリ | 実装済み | 総数 | 進捗率 |
|---------|---------|------|--------|
| **状態異常** | 6 | 6 | **100.0%** ✅ |
| **フィールド効果** | 18 | 20 | 90.0% |
| **揮発性状態** | 19 | 25 | 76.0% |
| **アイテム** | 56 | 154 | 36.4% |
| **技** | 106 | 692 | 15.3% |
| **特性** | 17 | 304 | 5.6% |

### 最新改善：コード品質とアーキテクチャの改善 ✅

**コード品質向上**:
- ✅ handler/ability.py に包括的な docstring を追加（Args/Returns/Notes）
- ✅ type hint を改善（Any → str、int、dict など）
- ✅ volatile.py を五十音順に再編成（69関数）
- ✅ TODO comments を詳細に記載

**アーキテクチャ改善**:
- ✅ Volatile クラスへの状態管理の集約
  - `sub_hp`（みがわりHP）と `critical_rank`（急所ランク）を移行
  - Pokemon クラスから古い属性を削除
- ✅ property accessor でテスト互換性を確保
- ✅ data/handlers モジュールに五十音順の説明を追記

**テスト実績**:
- 全テスト 178/179 成功（99.4%）
- volatile.py 再編成後も全機能正常動作

### 実装完了項目

#### フィールド効果（18/18）✅
- エレキフィールド、グラスフィールド、サイコフィールド、ミストフィールド
- ステルスロック、まきびし、どくびし、ねばねばネット
- リフレクター、ひかりのかべ、オーロラベール
- しろいきり、しんぴのまもり、おいかぜ、トリックルーム
- ワイドガード、ファストガード、まもる

#### 状態異常（2/6）
- どく、もうどく

#### 揮発性状態（1/24）
- みがわり

#### アイテム（6/154）
- きあいのタスキ、こだわりハチマキ、こだわりメガネ、こだわりスカーフ
- とつげきチョッキ、いのちのたま

#### 特性（9/304）
- いかく、かちき、きんちょうかん
- ありじごく、かげふみ、じりょく
- すなかき、グラスメイカー、ぜったいねむり

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

## 開発ツール

### 実装状況ダッシュボード

```bash
python -m jpoke.utils.dashboard
```

各カテゴリの実装状況をJSON形式で出力します（[dashboard.json](dashboard.json)）。

### テスト

pytest でテストを実行します。テストコードは **失敗時のみ出力** が表示されます。成功したテストは結果を表示せずに進行します。

```bash
# 全テスト実行（tests フォルダから）
cd tests
python run.py

# または pytest を直接使用
pytest ailment.py ability.py move.py volatile.py -v

# 個別テスト実行
python ailment.py
python move.py
python ability.py
python volatile.py
```
python tests/volatile.py
```

## 今後の実装予定

### 優先度高
1. **基本的な状態異常** - まひ、ねむり、こおり、やけど
2. **主要な揮発性状態** - ちょうはつ、アンコール、しめつける、やどりぎのタネ
3. **よく使われる特性** - てんねん、マルチスケイル、がんじょう、ばけのかわ
4. **主要なアイテム** - たべのこし、オボンのみ、ゴツゴツメット

### 優先度中
- 複数回攻撃技の実装
- 天候効果の追加
- 連続技・反動技の実装

### 優先度低
- AIプレイヤーの改善（MCTS実装）
- UI/UXの改善
- パフォーマンス最適化

## ライセンス

MIT License
