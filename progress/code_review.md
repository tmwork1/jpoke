# code review

対象: `src/jpoke/**/*.py`, `tests/**/*.py` を中心に、イベント駆動設計・可読性・不具合・SV仕様再現・性能の観点で確認。

## 主要な問題点（重大度順）

### 1) [High] ダメージ計算の分岐が型不一致で常に不発
該当: `src/jpoke/core/damage.py:387`, `src/jpoke/core/damage.py:391`, `src/jpoke/core/damage.py:468`

なぜ問題か:
- `move` は `Move` オブジェクトなのに、`'イカサマ'` / `'ボディプレス'` 文字列と比較しているため条件が常に偽になる。
- `attacker.ability` は `Ability` オブジェクトなのに、`'てんねん'` 文字列比較しているため条件が常に偽になる。
- 結果として、攻撃/防御参照ステータスやランク無視の仕様が誤る。実機再現の中核を崩す。

改善案:
- 比較を `move.name` / `ability.name` ベースに修正する。
- 回帰テストを追加する（`イカサマ`, `ボディプレス`, `てんねん`）。

修正例:
```python
# src/jpoke/core/damage.py
if move.name == "イカサマ":
    final_atk = defender.stats["A"]
    r_rank = rank_modifier(defender.rank["A"])
else:
    if move.name == "ボディプレス":
        stat = "B"
    elif move_category == "物理":
        stat = "A"
    else:
        stat = "C"

# ...
if attacker.ability.name == "てんねん" and r_rank != 1:
    r_rank = 1
```

### 2) [High] `_run_terastal()` のコマンド空参照で IndexError リスク
ユーザーコメント:
- テラスタルのタイミングは現在の実装が正しいので修正不要

該当: `src/jpoke/core/turn.py:116`, `src/jpoke/core/turn.py:120`, `src/jpoke/core/turn.py:170`

なぜ問題か:
- 交代コマンドは直前フェーズで `pop(0)` 済みだが、`_run_terastal()` で `player.reserved_commands[0]` を無条件参照しており、空リスト時に例外化しうる。

改善案:
- `reserved_commands` 参照前に空チェックを入れる（例: `if not player.reserved_commands: continue`）。
- テスト追加: 「交代コマンド混在ターンで `_run_terastal()` が例外を出さない」。

### 3) [Medium] 効果ロジックが `MoveExecutor` に直書きされ、イベント駆動の責務分離を崩している
該当: `src/jpoke/core/move_executor.py:67`, `src/jpoke/core/move_executor.py:71`

なぜ問題か:
- `スキルリンク` / `いかさまダイス` を `_resolve_hit_count()` で直接分岐している。
- 特性/道具の追加時に core を都度変更する必要があり、依存方向が逆転する。

改善案:
- `ON_RESOLVE_HIT_COUNT` 相当のイベントを追加し、特性/道具の補正は `handlers/ability.py` / `handlers/item.py` に寄せる。
- 連続技ロジックは「デフォルト分布のみ core、例外は handler」で統一する。

### 4) [Medium] デバッグ `print` が本体ロジックに残っている
該当: `src/jpoke/handlers/common.py:47`, `src/jpoke/handlers/volatile.py:242`

なぜ問題か:
- 実行時に標準出力が汚染され、テストやログ解析にノイズを混入させる。
- ライブラリ/エンジン層の副作用として不適切。

改善案:
- `print` を削除し、必要なら `EventLogger` へ統一的に記録する。

### 5) [Medium] 例外型が広すぎて呼び出し側で扱いづらい
該当: `src/jpoke/core/battle.py:326`, `src/jpoke/core/battle.py:343`

なぜ問題か:
- `raise Exception("Player not found.")` は意図が粗く、障害分類や復旧処理をしにくい。

改善案:
- `ValueError` など意味のある例外へ変更し、メッセージに `mon.name` 等の文脈を含める。

### 6) [Low] イベント発火ごとのハンドラソートで実効素早さを毎回再計算している
ユーザーコメント:
- パフォーマンスの最適化はあとまわしで

該当: `src/jpoke/core/event.py:160`

なぜ問題か:
- `_sort_handlers()` 内で `calc_effective_speed()` を都度呼ぶため、イベントが多いターンで計算コストが膨らみやすい。
- コメント上も再入リスクを意識した実装になっており、保守時の事故余地がある。

改善案:
- 直近は対応保留でよい。着手時は同一ターン内の速度キーをキャッシュする（失効条件: ランク変化、麻痺、天候/場変更など）。
- 代替として、イベント種別ごとに「ソート不要」フラグを明示して計算を抑える。

### 7) [Low] ターン終了フェーズ処理の重複（1-4は共通化余地あり）
ユーザーコメント:
- ON_TURN_END1~4はループでまとめて記述したほうがよいが、5以降は別の交代判定が介入するので分離する

該当: `src/jpoke/core/turn.py:226`

なぜ問題か:
- `ON_TURN_END_1` から `ON_TURN_END_4` は実行パターンが同形で重複している。
- フェーズ追加/順序変更時に差分漏れが起きやすい。

改善案:
- `ON_TURN_END_1` から `ON_TURN_END_4` のみループ化し、`ON_TURN_END_5` 以降は現状どおり分離して仕様順序を維持する。

## 可読性・設計での補足

- 命名はドメイン寄り（日本語能力名・状態名）で、仕様追跡しやすい。
- `Battle` から `TurnController` / `MoveExecutor` / `SwitchManager` へ責務分離されており、全体方針は良い。
- 一方で、`core` 側に特性/道具の個別例外が残っており、イベント駆動の一貫性を崩し始めている。

## ポケモン仕様観点の要点

- テラスタル発動タイミングは現方針を維持する前提で、まずは例外リスク（空参照）を潰す。
- ダメージ式の条件不発（イカサマ/ボディプレス/てんねん）は実機差分に直結する。

## 良い点（簡潔）

- イベント中心の拡張ポイントが明確（`EventManager` + `HandlerReturn`）。
- `modify_hp` / `modify_stats` を `Battle` に集約し、状態更新APIが統一されている。
- `ON_TURN_END_1..6` の分割は仕様順序を表現しやすい。
- テスト基盤 (`tests/test_utils.py`) が充実しており、回帰テスト追加がしやすい。

## テスト上のギャップ（重大項目に対応）

- `イカサマ` / `ボディプレス` / `てんねん` のダメージ計算回帰テストが見当たらない。
- 交代コマンドが含まれるターンでの `_run_terastal()` 安全性テストが見当たらない。
