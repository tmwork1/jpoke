# battle.py レビュー（詳細版）

## 全体像
Battle クラスは **ポケモン対戦の進行を完全に司る中核クラス**であり、
イベント駆動設計（EventManager）と割り込み（Interrupt）を組み合わせることで、
非常に高い再現性と拡張性を実現しています。

一方で、現在の設計は「完成度が高いがゆえに」
**責務が Battle に集中し始めている段階**に入っています。

---

## 良い点

### 1. イベント駆動設計
- ダメージ・能力・フィールド・持ち物などを Event 経由で分離
- Showdown 系実装に近い拡張性
- calc_effective_speed / calc_damage などが外部介入可能

### 2. Interrupt モデル
- 交代・瀕死・だっしゅつ系を明確に enum 化
- 割り込み理由がコード上で追跡しやすい
- run_interrupt_switch に集約しようとする設計意図が明確

### 3. AI / 探索を意識した設計
- deepcopy + masked による完全情報／不完全情報切替
- seed 管理・Random の隠蔽
- コマンド予約方式（reserve_command）が MCTS と相性が良い

---

## 問題点

### 1. 神クラス化の兆候
Battle が以下すべてを直接管理しています：
- ターン進行
- 行動順決定
- 交代処理
- 勝敗判定
- ログ出力
- 割り込み解決

→ 今後のルール追加で破綻しやすい

### 2. 割り込み処理の分散
- override_interrupt / has_interrupt / run_interrupt_switch が複雑に絡む
- ターンのどのフェーズで何が起きるか把握しづらい

### 3. 探索コスト
- find_player / foe / team_idx が O(n)
- 探索回数が多いため AI 探索時にボトルネック化

### 4. 行動順の float ハック
- speed * 1e-5 による疑似優先度
- 意図は明確だが可読性・安全性が低い

---

## 改善提案

### 1. TurnRunner / Phase 分離
```text
Battle
 ├─ TurnRunner
 │   ├─ SwitchPhase
 │   ├─ ActionPhase
 │   └─ EndPhase
```
→ フェーズ単位でロジックを分割

### 2. InterruptQueue 導入
- 割り込みを「状態」ではなく「キュー」として扱う
- 発生源・理由・優先度を明示

### 3. 逆引きテーブル
```python
self.mon_to_player: dict[Pokemon, Player]
```
- find_player 系を O(1) に

### 4. 行動順の明示的ソート
```python
(priority, speed, rng)
```
のタプルで比較

---

## 総括
**設計レベルは非常に高く、OSS として十分通用する品質**です。
今リファクタリングすれば、将来の拡張・AI 実装が飛躍的に楽になります。
