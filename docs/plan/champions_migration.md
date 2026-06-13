# SVからChampions仕様への移行計画

更新日: 2026-06-13

仕様差分の出典: `docs/champions/changes_from_sv.md`, `docs/spec/moves/_all_moves.md`

---

## 1. 努力値システムの変更

### 仕様変更
- SV: 0〜252（8n調整）
- Champions: 0〜32（整数）
- 変換式: `eff_sv = 0 if eff_chmp == 0 else 8*eff_chmp - 4`
  - 0→0, 1→4, 2→12, ..., 32→252（既存の8n値と完全一致）

### 対象ファイル
- `src/jpoke/model/stats.py`

### 実装方針
内部計算式 `effort//4` はそのまま維持し、Champions EV（0〜32）をSV等価値に変換してから格納する。

| 変更箇所 | 内容 |
|---|---|
| `PokemonStats.__init__` | 内部 `_effort` の意味をSV等価値として維持（変更なし） |
| 変換関数の追加 | モジュール内に `chmp_to_sv_effort(e: int) -> int` と `sv_to_chmp_effort(e: int) -> int` を追加 |
| `_calculate_effort_from_stat` | 探索リストを `efforts_chmp = [chmp_to_sv_effort(i) for i in range(33)]` に変更（現行の `efforts_50` と同一内容なので計算結果は変わらない） |
| `effort` setter / Pokemon API | 受け取り時に0〜32の値を検証し、変換してから格納するか、または外部APIを`set_effort_chmp()`として追加 |

### テスト
- 既存の努力値テスト（実数値計算）が引き続き通ることを確認
- 0と1〜32の境界値テスト

---

## 2. 技のPP変更

### 仕様変更
全技のPPが8・12・16・20の4段階に統一。`docs/spec/moves/_all_moves.md` に全技の正しいPP値が記載されている。

### 対象ファイル
- `src/jpoke/data/move.py`（各 `MoveData` の `pp=` 引数を更新）
- `docs/spec/moves/_all_moves.md` を参照して一括更新

### 実装方針
`_all_moves.md` を解析し、現行 `data/move.py` の各技エントリの `pp=` 値を更新する。  
未実装技のPPも将来の実装のために先に変更して問題ない（PP値はデータ定義のみ）。

### 変更規模
500技以上。スクリプトで `_all_moves.md` をパースして自動更新することを推奨。

---

## 3. 技の仕様変更（個別）

### 3-1. 威力変更（12技）

| 技名 | 変更 |
|---|---|
| ボーンラッシュ | 威力 25→30 |
| であいがしら | 威力 90→100 |
| かげぬい | 威力 80→90 |
| トロピカルキック | 威力 70→85 |
| くちばしキャノン | 威力 100→120 |
| ほのおのムチ | 威力 80→90 |
| Gのちから | 威力 80→90 |
| りんごさん | 威力 80→90 |
| ナイトバースト | 威力 85→90 |
| ひゃっきやこう | 威力 60→65 |
| バリアーラッシュ | 威力 70→90 |
| ひょうざんおろし | 威力 100→120 |

対象: `src/jpoke/data/move.py` の各 `MoveData(power=...)` を更新。

### 3-2. 命中変更（2技）

| 技名 | 変更 |
|---|---|
| クラブハンマー | 命中 90→95 |
| みずあめボム | 命中 85→90 |

対象: `src/jpoke/data/move.py` の各 `MoveData(accuracy=...)` を更新。

### 3-3. 効果変更（11技）

| 技名 | 変更内容 | 対象ハンドラ |
|---|---|---|
| ムーンフォース | 特攻ダウン確率 30%→10% | `handlers/move_attack.py` またはMoveData |
| アイアンヘッド | ひるみ確率 30%→20% | 同上（すでに20%実装済みの可能性あり） |
| どくのいと | どく＋素早さ1段ダウン → どく＋素早さ**2**段ダウン | `handlers/move_status.py` |
| しおづけ | 毎ターンダメージが従来の**半分**に | `handlers/move_attack.py` |
| トラバサミ | タイプ: くさ→**はがね** | `data/move.py` の `type=` |
| フェイタルクロー | どく/まひ/ねむり確率 50%→**30%**、スラッシュ技に追加 | `data/move.py`（`labels=` に `"slash"` 追加）、ハンドラの確率修正 |
| ドラゴンエール | **音技**に追加 | `data/move.py`（`labels=` に `"sound"` 追加） |
| ドラゴンクロー | **スラッシュ技**に追加 | `data/move.py`（`labels=` に `"slash"` 追加） |
| シャドークロー | **スラッシュ技**に追加 | `data/move.py`（`labels=` に `"slash"` 追加） |
| ブレイククロー | **スラッシュ技**に追加 | `data/move.py`（`labels=` に `"slash"` 追加） |
| フリーズドライ | こおり状態の追加効果を削除 | `handlers/move_attack.py` |

---

## 4. 状態異常の仕様変更

### 4-1. まひ（麻痺）

| | SV | Champions |
|---|---|---|
| 行動不能確率 | 25% | 12.5% |

対象: `src/jpoke/handlers/ailment.py` の `まひ_action`

```python
# 変更前
trigger = battle.random.random() < 0.25
# 変更後
trigger = battle.random.random() < 0.125
```

進捗テーブル更新: `docs/progress/ailment.md` の「まひ」行を `12.5%` に修正。

### 4-2. ねむり（睡眠）

| | SV | Champions |
|---|---|---|
| 最大行動不能ターン | 3 | 2 |
| 解除条件 | カウント0 | 2ターン目に1/3で解除、3ターン目は必ず解除 |

現行の `ねむり_check_action` は `tick()` でカウントを減らして0になると解除する設計。
Champions仕様では**経過ターン数**に基づいた確率解除になるため、ロジックを変更する。

変更方針:
- `ねむり_check_action` でカウント（=初期化時のランダム継続ターン）ではなく `elapsed_turns` で判定
- turn 1（眠った次のターン）: 行動不能、解除なし
- turn 2（elapsed_turns == 2）: 1/3で解除
- turn 3以降（elapsed_turns >= 3）: 必ず解除

対象: `src/jpoke/handlers/ailment.py` の `ねむり_check_action`

注: `Ailment` に `count` を渡す箇所（`ailment_manager.apply` の呼び出し側）でランダム継続ターン設定をしている場合は不要になるため、ねむり付与時の `count` 引数を廃止または無視する。

### 4-3. こおり（凍結）

| | SV | Champions |
|---|---|---|
| 自然解凍確率 | 20% | 25% |
| 3ターン目 | 確率のまま | **必ず**解凍 |

変更方針:
- `こおり_action` 内の確率を `0.2 → 0.25` に変更
- `elapsed_turns >= 3` で強制解除を追加

対象: `src/jpoke/handlers/ailment.py` の `こおり_action`

---

## 5. 優先度と作業順

| 優先度 | 作業 | 理由 |
|---|---|---|
| 高 | 状態異常4種（まひ・ねむり・こおり） | ロジック変更、既存テスト修正が必要 |
| 高 | 技の効果変更（3-3） | ハンドラ修正が必要 |
| 中 | 技の威力・命中変更（3-1, 3-2） | データ変更のみ |
| 中 | 努力値システム変更 | API変更だが内部計算は同等 |
| 低 | 技のPP変更 | 数が多いがデータ変更のみ、スクリプト化推奨 |

---

## 6. テスト修正が必要な箇所

- `tests/test_ailment.py`: まひ（25%→12.5%）、ねむり（3ターン→2ターン）、こおり（20%→25%）の期待値修正
- 上記3状態異常に関連する特性・道具テスト（スリープ中特性など）も確認
- 努力値設定テストがある場合、Champions形式の入力値で通ることを確認
