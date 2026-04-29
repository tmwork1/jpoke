# jpoke ライブラリ使い勝手レビュー

**レビュー日:** 2026年4月29日  
**対象:** `random_1on1.py` スクリプト実装時の体験に基づく

---

## 概要

jpoke は**充実した機能を備えた優秀なシミュレータ**ですが、初心者向けのドキュメンテーションと API の一貫性に改善の余地があります。

---

## 👍 利点

### 1. 導入が簡単

```python
from jpoke import Battle, Player, Pokemon
# ほぼこれだけで動く
```

- インポート構造が直感的
- `Pokemon("ピカチュウ")` で即座にポケモンを生成可能
- `Battle([player1, player2])` で簡潔にバトル初期化

### 2. イベント駆動アーキテクチャが明確

- 特性、アイテム、技などの効果が一貫したハンドラ方式で実装されている
- コード全体の構造が予測可能で理解しやすい

### 3. データ構造が豊富

```python
pokedex[name]         # ポケモン図鑑データ
ABILITIES[name]       # 特性定義
ITEMS[name]           # アイテム定義
MOVES[name]           # 技定義
```

- ポケモン・特性・アイテム・技すべてがデータソースとして存在
- ランダム生成スクリプトなどが容易に書ける

### 4. Battle API が良好

- `battle.advance_turn()` - 単純で理解しやすい
- `battle.judge_winner()` - 勝敗判定が明確
- `battle.get_available_action_commands(player)` - アクション取得が簡潔

---

## ⚠️ 改善が必要な点

### 1. **API の一貫性不足** ★重要

#### 問題 a) ランク補正の大文字/小文字不一致

**実装コード:**  
`move_executor.py` (line 173)
```python
rank_diff = attacker.rank["acc"] - defender.rank["eva"]
```

**データ定義:**  
`pokemon.py` (line 111)
```python
self.rank: dict[Stat, int] = {k: 0 for k in STATS}
# STATS = ["H", "A", "B", "C", "D", "S", "ACC", "EVA"]  # 大文字
```

**影響:** KeyError でスクリプト破壊  
**改善案:** `rank` キーを統一して大文字に（`"ACC"`、`"EVA"`、`"H"`など）

#### 問題 b) アイテムが None をサポートしない

**実装コード:**
```python
mon = Pokemon(..., item=None)  # 指定可能に見えるが...
```

**実行時:**
```
battle.run_switch() → switch.py → 
mon.item.register_handlers()  # AttributeError: 'NoneType' object has no attribute 'register_handlers'
```

**改善案:**
- `item: str | Item | None = None` を明示する
- `Item` クラスで Null Object パターンを導入
- ドキュメント化

### 2. **初心者向けドキュメント不足**

#### 問題点

- **API ドキュメント不足**
  - `Player` クラスの `choose_selection_commands()` の用途が不明
  - `battle.get_available_action_commands()` が何を返すのか不明確
  - テンプレート実装の例がない

- **`test_utils.py` の隠れた複雑性**
  - `start_battle()` が多数のオプション引数を要求
  - 初心者は何を使うべきか判断困難

- **ハンドラシステムの説明不足**
  - `@handler` デコレータの書き方
  - イベント優先度の理解方法
  - 新しい特性・技を追加する方法

#### 推奨改善

```markdown
## はじめのバトル

### 最小限の実装

Player クラスを継承して行動を決定するロジックを実装します：

\`\`\`python
class SimplePlayer(Player):
    def choose_action_command(self, battle):
        # 利用可能なコマンドをランダムに選択
        commands = battle.get_available_action_commands(self)
        return random.choice(commands)

# バトル実行
p1 = SimplePlayer("Alice")
p2 = SimplePlayer("Bob")
p1.team.append(Pokemon("ピカチュウ"))
p2.team.append(Pokemon("フシギダネ"))

battle = Battle([p1, p2])
while battle.judge_winner() is None:
    battle.advance_turn()
\`\`\`
```

### 3. **エラーメッセージが不親切**

**例1: 無効な技**
```python
mon = Pokemon("ピカチュウ", moves=["えんげっき"])  # 第9世代にない技
# →制約なく受け入れ、実行時に謎のエラー
```

**例2: 存在しない特性**
```python
ability = ABILITIES["意味不な特性"]  # KeyError
```

**改善案:**
- `Pokemon.__init__()` で技の妥当性チェック
- `ABILITIES[name]` でデフォルト値を返す、または詳細エラーメッセージ
- バリデーション関数 `validate_pokemon()` を公開

---

## 📊 デバッグのしやすさ

### 良い点
- `battle.print_logs()` で進行状況確認可能
- `Battle.test_option.accuracy` で命中率固定化可能

### 悪い点
- ログ出力がデフォルトで冗長（ノイズが多い）
- デバッグレベル制御がない

---

## 🚀 パフォーマンス面

### 観察事項
- **1ターン = 約 0.1-1秒** 程度（初期化込み）
- 1000ゲーム連続実行は実用的
- イベント駆動での処理オーバーヘッドは許容範囲

---

## 💡 実装者向けのヒント

### 発見した使い方
1. **ランダムプレイヤーの実装**
   ```python
   available = battle.get_available_action_commands(self)
   return random.choice(available)
   ```
   この方法は汎用的で推奨

2. **データソースの作成**
   - `pokedex` リスト取得: `list(pokedex.keys())`
   - 特性・アイテム・技も同様

3. **バトル初期化のテンプレート**
   - `test_utils.start_battle()` を参考に状態セット可能

---

## 📋 まとめ：改善優先度

| 優先度 | 項目 | 工数 | 効果 |
|--------|------|------|------|
| **P1** | `rank` キーの一貫性修正 | 低 | バグ除去・信頼性向上 |
| **P1** | アイテム None サポート | 中 | API の安定化 |
| **P2** | 初心者向けドキュメント | 高 | 採用率向上 |
| **P2** | バリデーション関数 | 低 | 開発効率向上 |
| **P3** | エラーメッセージ改善 | 中 | DX 向上 |

---

## 結論

**総合評価: 7/10 ⭐**

jpoke はポケモンシミュレーション機能として**完成度が高い**ですが、

- **初期段階のユーザーにはハードルがやや高い**
- **API の一貫性がやや甘い**

という 2 点が課題です。特に **P1 の 2 つの修正** を行うだけで、安定性と信頼性が大幅に向上するでしょう。
