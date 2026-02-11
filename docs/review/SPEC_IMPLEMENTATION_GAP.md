# 仕様と実装のギャップ分析

**作成日**: 2026年2月7日

---

## 概要

このドキュメントは、`docs/spec/` の仕様ドキュメントと、`src/jpoke/` の実装コードのギャップを詳細に分析したものです。

---

## 1. ダメージ計算における未実装特性

### 1.1 防御側特性によるダメージ軽減

**仕様**: `docs/spec/damage_calc.md` Lines 245-276

| 特性 | 軽減倍率 | 4096基準 | 実装状態 | 優先度 |
|------|---------|---------|---------|--------|
| マルチスケイル | 0.5倍 | 2048 | ❌ | 高 |
| ファントムガード | 0.5倍 | 2048 | ❌ | 高 |
| たいねつ | 0.5倍 | 2048 | ❌ | 中 |
| あついしぼう | 0.5倍 | 2048 | ❌ | 中 |
| かんそうはだ | 0.5倍 | 2048 | ❌ | 中 |
| ちょすい | 無効化 | 0 | ❌ | 中 |
| よびみず | 無効化 | 0 | ❌ | 中 |

**実装方法**:
これらの特性は `ON_CALC_DAMAGE_MODIFIER` イベントハンドラで実装する必要があります。

```python
# handlers/ability.py に追加

def マルチスケイル(battle: Battle, ctx: BattleContext, value: int) -> HandlerReturn:
    """マルチスケイル: HPが満タンの場合、ダメージを50%軽減する。
    
    イベント: ON_CALC_DAMAGE_MODIFIER
    
    Args:
        value: ダメージ補正倍率（4096基準）
    
    Returns:
        HandlerReturn: (is_affected, 軽減後の補正倍率)
    """
    # HPが満タンかチェック
    if ctx.target.hp != ctx.target.max_hp:
        return HandlerReturn(False, value)
    
    # 0.5倍軽減 = 2048/4096
    modified = round_half_down(value * 2048 / 4096)
    return HandlerReturn(True, modified)
```

---

### 1.2 攻撃側特性によるダメージ補正

**仕様**: `docs/spec/damage_calc.md` Lines 278-300

| 特性 | 補正倍率 | 4096基準 | 実装状態 |
|------|---------|---------|---------|
| ちからづく | 1.3倍 | 5325 | 確認推奨 |
| テラボルテージ (攻撃) | 1.5倍 | 6144 | ❌ |
| かんそうはだ (ほのお強化) | 1.25倍 | 5120 | ❌ |
| もふもふ (ほのお強化) | 2.0倍 | 8192 | ❌ |

---

## 2. ターン処理フローにおける未実装要素

### 2.1 ON_SWITCH_IN イベント

**仕様**: `docs/spec/turn_flow.md` Lines 19-107

**実装状態**: ✅ 基本的には実装されている

**確認項目**:
- [ ] Priority 10: テラスチェンジ
- [ ] Priority 20: かがくへんかガス
- [ ] Priority 30: きんちょうかん, じんばいったい
- [ ] Priority 100: 各種特性（50+個）
- [ ] Priority 120: ぎたい, ぎょぐん等
- [ ] Priority 140: アイスフェイス等

**実装の参照**: `core/battle.py` の `run_initial_switch()` メソッド

---

### 2.2 ON_BEFORE_ACTION イベント

**仕様**: `docs/spec/turn_flow.md` Lines 180-187

| Priority | 処理 | 実装状態 |
|----------|------|---------|
| - | クイックドロウ | ❌ 未確認 |
| - | せんせいのツメ | ❌ 未確認 |
| - | イバンのみ | ❌ 未確認 |

**確認推奨**: これらは優先度ハンドラなし（`-`）で実装される可能性あり。検証が必要。

---

### 2.3 ON_TRY_ACTION イベント

**仕様**: `docs/spec/turn_flow.md` Lines 190-227

**実装状態**: ⚠️ 部分的

実装されているもの:
- ❌ 自身のおんねん状態の解除
- ❌ 自身のいかり状態の解除
- ❌ なまけのカウント消費
- ❌ 技の反動で動けない
- ❌ ねむりのカウント消費
- ✅ こおりの回復判定
- ✅ PPが残っていない
- ❌ いろいろな動作不可条件

**実装ファイル**: `handlers/volatile.py`

---

### 2.4 ON_TRY_MOVE イベント

**仕様**: `docs/spec/turn_flow.md` Lines 230-406

**パート別実装状況**:

#### Priority 10-30: 基本的な失敗判定
- [ ] こだわり系判定 (Priority 10)
- [ ] ほのおタイプ+もえつきる (Priority 10)
- [ ] 天気による失敗 (Priority 10)
- [ ] ふんじんによる失敗 (Priority 10)
- [ ] ミクルのみ消費 (Priority 20)

#### Priority 30: 技ごとの仕様
- [ ] 30+ 個の技固有のルール

**参考**: 仕様では「Priority 30が複数あるため実行順不定」と明記されている。

---

## 3. ターン終了時の処理（ON_TURN_END）

**仕様**: `docs/spec/turn_flow.md` Lines 408-460

**実装状態**: ⚠️ 基本的には実装されているが、詳細な検証が必要

```
ON_TURN_END_1 → EMERGENCY (ききかいひ)
ON_TURN_END_2 → EMERGENCY
ON_TURN_END_3 → EMERGENCY
ON_TURN_END_4 → EMERGENCY
ON_TURN_END_5 → EJECTPACK
ON_TURN_END_6
```

**実装確認**: `core/turn_controller.py` Lines 208-249

```python
if not self.battle.has_interrupt():
    self.battle.events.emit(Event.ON_TURN_END_1)

# ききかいひによる交代 (1)
self.battle.run_interrupt_switch(Interrupt.EMERGENCY)

# ... 以降も同様
```

✅ 構造は仕様と一致している

---

## 4. 急所（クリティカル）計算

**仕様**: `docs/spec/critical.md`

**実装**: `core/damage.py` Lines 119-130

```python
def _calc_critical(self, critical_rank: int) -> bool:
    """急所判定を行う。
    
    急所ランクに基づいて急所確率を計算します：
    - ランク0: 1/24（約4.17%）
    - ランク1: 1/8（12.5%）
    - ランク2: 1/4（25%）
    - ランク3以上: 1/2（50%、上限）
    """
```

**確認項目**:
- 急所ランク3以上で50%固定は正しいか？ -> 修正済み
- 第9世代での計算式は変更されたか？ -> 修正済み

---

## 5. 命中率計算

**仕様**: `docs/spec/accuracy.md` Lines 1-55

**実装**: `core/move_executor.py` Lines 62-74

```python
def check_hit(self, attacker: Pokemon, move: Move) -> bool:
    if self.battle.test_option.accuracy is not None:
        accuracy = self.battle.test_option.accuracy
    else:
        if move.accuracy is None:
            return True
        accuracy = self.battle.events.emit(
            Event.ON_CALC_ACCURACY,
            BattleContext(attacker=attacker, defender=self.battle.foe(attacker), move=move),
            move.accuracy
        )
```

**評価**: ✅ 基本的には正しい

**ただし、詳細な確認項目**:
- [ ] ランク倍率の計算式が正しいか
- [ ] ミクルのみの補正（4915/4096）が実装されているか
- [ ] 最大100への制限が実装されているか

---

## 6. フィールド効果

### 6.1 グローバルフィールド（天候・地形）

**仕様**: `docs/spec/global_field/` (10+個のファイル)

**実装**: `core/field_manager.py`, `handlers/field.py`

**確認推奨**: 各天候・地形の効果が仕様通りに実装されているか検証

---

### 6.2 サイドフィールド効果

**仕様**: `docs/spec/side_field/` + `docs/spec/damage_calc.md` Lines 190-203

| 効果 | 補正倍率 | 実装状態 |
|------|---------|---------|
| リフレクター | 0.5倍 | ✅ 記載あり |
| ひかりのかべ | 0.5倍 | ✅ 記載あり |
| オーロラベール | 0.5倍 | ❌ 未実装 |
-> 修正済み

---

## 7. アイテムによる補正

### 7.1 アイテム系ダメージ補正

**仕様**: `docs/spec/damage_calc.md` Lines 226-308

**例**: 
- フィルター (0.75倍) - 未実装
- ハードロック (0.75倍) - 未実装
- プリズムアーマー (0.75倍) - 未実装

---

## 8. 状態異常時の処理

### 8.1 やけど多重効果

**仕様**: `docs/spec/ailment.md` での詳細仕様

**実装確認事項**:
- [ ] やけど時のダメージ計算 (0.5倍)
- [ ] ほのおタイプへの無効化
- [ ] みずのベール等による防止
- [ ] とうそういん等による治療　<- 存在しない。無視

---

## 9. 揮発状態（Volatile Conditions）

### 9.1 未実装のTODO項目

**ファイル**: `handlers/volatile.py`

| 行番号 | TODO内容 | 優先度 |
|--------|---------|--------|
| 173 | 拘束バンド判定を追加 | 中 |
| 423 | ねむり状態に移行させる | 高 |
| 631 | こんらん状態を付与する処理 | 高 |
| 665 | ひんしになったとき最後の技PP0 | 低 |
| 829 | 最後に使用した技以外不可 | 中 |
| 863 | みちづれでひんし時相手もひんし | 中 |

---

## 10. テラスタル

**仕様**: `docs/spec/terastal.md`

**実装**: `core/turn_controller.py` Lines 141-142

```python
# 30 | テラスタル
```

**確認推奨**: テラスタルの全仕様が実装されているか検証

---

## 11. PP（パワーポイント）

**仕様**: `docs/spec/pp.md`

**実装**: `handlers/move.py` Lines 49-56

```python
def consume_pp(battle: Battle, ctx: BattleContext, value: Any) -> HandlerReturn:
    v = battle.events.emit(Event.ON_CHECK_PP_CONSUMED, ctx, 1)
    ctx.move.pp = max(0, ctx.move.pp - v)
```

**確認推奨**: リサイクルなどのPP回復機能が実装されているか

---

## 12. 行動順序（Action Order）

**仕様**: `docs/spec/action_order.md`

**実装**: `core/speed_calculator.py`

**確認事項**:
- [ ] 優先度順の並び替え
- [ ] 優先度が同じ場合の素早さ順
- [ ] 同一速度時の乱数判定

---

## 実装優先度の推奨

### Phase 1: 高優先度 (1～2週間)
1. ハンドラ docstring 作成
2. マルチスケイル等の防御特性実装
3. TODO項目の完結

### Phase 2: 中優先度 (2～4週間)
1. 未実装のダメージ補正特性
2. 詳細なON_TRY_MOVE判定
3. テラスタルの詳細実装確認

### Phase 3: 低優先度 (継続)
1. PP回復機能の強化
2. マイナー仕様の完全実装

---

## 検証方法

各未実装項目を検証するための推奨テスト：

```python
# tests/test_spec_compliance.py (新規作成推奨)

def test_multi_scale_damage_reduction():
    """マルチスケイルがダメージを50%軽減するか確認"""
    # テストコード
    pass

def test_hard_rock_super_effective():
    """ハードロックが効果ばつぐんを0.75倍にするか確認"""
    pass

def test_turn_end_events_order():
    """ON_TURN_END イベントが正しい順序で発火するか"""
    pass
```

---

**最終更新**: 2026年2月7日
