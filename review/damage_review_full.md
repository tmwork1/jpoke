# damage.py レビュー（詳細版）

## 全体像
DamageCalculator は **Showdown 互換を強く意識した高精度実装**です。
補正順序・丸め・乱数幅が正確で、検証用途にも耐える品質です。

---

## 良い点

### 1. DamageContext
- critical / self_harm / power_multiplier を明示
- 状態を引数地獄にしない良設計

### 2. 補正のイベント化
- 威力・攻撃・防御・タイプ・最終ダメージがすべて Event 経由
- 特性・フィールド・持ち物拡張が容易

### 3. 丸め処理
- Decimal + ROUND_HALF_DOWN
- 実機挙動に非常に忠実

### 4. ダメージ分布
- 16 パターンを明示的に生成
- 致死率計算や期待値評価に直結

---

## 問題点

### 1. single_hit_damages が巨大
- 責務：
  - 威力計算
  - 攻撃計算
  - 防御計算
  - ダメージ算出
  - ログ生成

### 2. 文字列依存
- 技名・特性名が文字列比較
- typo や多言語対応に弱い

### 3. ログ責務の混在
- DamageCalculator が UI 寄りのログを持つ

---

## 改善提案

### 1. 関数分割
```text
calc_final_power
calc_final_attack
calc_final_defense
calc_base_damage
apply_modifiers
```

### 2. 正規化
- Move / Ability を ID or enum 管理
- 表示名は別レイヤー

### 3. DamageResult 導入
```python
@dataclass
class DamageResult:
    damages: list[int]
    logs: list[str]
```
→ 表示と計算を分離

---

## 総括
**計算精度は完成域**にあります。
次の段階は「保守性」と「拡張性」の改善です。
