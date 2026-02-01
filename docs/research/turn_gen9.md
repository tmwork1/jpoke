# ターン進行フロー (第九世代)

本ドキュメントは、ポケモン第九世代のバトルにおけるターン進行の詳細仕様をまとめたものである。

## 出典

- [ポケモンwiki - ターン](https://wiki.xn--rckteqa2e.com/wiki/%E3%82%BF%E3%83%BC%E3%83%B3)

## 概要

ポケモンバトルは複数のフェーズに分かれており、各フェーズで特定の処理が順番に実行される。
本ドキュメントでは、ターン0(初期化)からターン完了までの全フローを網羅する。

---

## ターンフロー概要

### COMMON: 共通処理

| Step | Type | Name | Description | CodeMethod | Implemented |
|------|------|------|-------------|------------|-------------|
| 0.0 | Check | 割り込みチェック | 割り込みがないか確認 | `has_interrupt()` | ✓ |
| 0.1 | Process | ターンカウント増加 | ターン番号を1増やす | `increment_turn_count()` | ✓ |

### INIT: ターン0処理 (初期化)

| Step | Type | Name | Description | CodeMethod | Implemented |
|------|------|------|-------------|------------|-------------|
| 0.2 | Start | ターン0開始 | 初期ターン処理開始 | `_process_turn_phases()` | ✓ |
| 0.3 | Check | 割り込みチェック | 割り込みがないか確認 | `has_interrupt()` | ✓ |
| 0.4 | Process | 選出 | ポケモン選出処理 | `run_selection()` | ✓ |
| 0.5 | Process | 初期繰り出し | 選出したポケモンを場に出す | `run_initial_switch()` | ✓ |
| 0.6 | Interrupt | EJECTPACK_ON_START | だっしゅつパックによる交代 | `run_interrupt_switch()` | ✓ |
| 0.7 | End | ターン0終了 | この時点でreturn | - | - |

**注意**: ターン0ではこの時点で処理が終了し、ターン1以降の処理は行わない。

### TURN: ターン開始処理 (ターン1以降)

| Step | Type | Name | Description | CodeMethod | Implemented |
|------|------|------|-------------|------------|-------------|
| 1.0 | Start | ターン開始 | ターン1以降の処理開始 | - | - |
| 1.1 | Check | 割り込みチェック | 割り込みがないか確認 | `has_interrupt()` | ✓ |
| 1.2 | Process | ターン初期化 | プレイヤー状態のリセット | `init_turn()` | ✓ |
| 1.3 | Process | コマンド予約 | 行動コマンドの決定 | `choose_action_command()` | ✓ |
| 1.4 | Event | ON_BEFORE_ACTION | 行動前イベント発火 | `events.emit(ON_BEFORE_ACTION)` | ✓ |

### SWITCH_PHASE: 交代フェーズ

| Step | Type | Name | Description | CodeMethod | Implemented |
|------|------|------|-------------|------------|-------------|
| 2.0 | Start | 交代フェーズ開始 | ターン開始時の交代処理 | - | - |
| 2.1 | Loop | 速度順ループ開始 | 速度順でポケモンを処理 | `calc_speed_order()` | ✓ |
| 2.2 | Check | 割り込みチェック | 割り込みがないか確認 | `has_interrupt()` | ✓ |
| 2.3 | Check | 交代コマンド判定 | 交代コマンドか確認 | `reserved_commands[0].is_switch()` | ✓ |
| 2.4 | Process | 交代実行 | ポケモンを交代する | `run_switch(player, new)` | ✓ |
| 2.5 | Process | 割り込みフラグ更新 | だっしゅつパック用フラグ設定 | `override_interrupt(EJECTPACK)` | ✓ |
| 2.6 | Interrupt | EJECTPACK_ON_SWITCH | だっしゅつパックによる交代 | `run_interrupt_switch()` | ✓ |
| 2.7 | End | 速度順ループ終了 | 全ポケモンの処理完了 | - | - |

### MOVE_BEFORE: 技使用前イベント

| Step | Type | Name | Description | CodeMethod | Implemented |
|------|------|------|-------------|------------|-------------|
| 3.0 | Event | ON_BEFORE_MOVE | 技使用前イベント発火 | `events.emit(ON_BEFORE_MOVE)` | ✓ |

### MOVE_PHASE: 技実行フェーズ

| Step | Type | Name | Description | CodeMethod | Implemented |
|------|------|------|-------------|------------|-------------|
| 3.1 | Start | 技フェーズ開始 | 技の実行処理 | - | - |
| 3.2 | Loop | 行動順ループ開始 | 行動順でポケモンを処理 | `calc_action_order()` | ✓ |
| 3.3 | Log | 行動ログ | ポケモン名をログ出力 | `add_event_log()` | ✓ |
| 3.4 | Check | 割り込みチェック | 割り込みがないか確認 | `has_interrupt()` | ✓ |
| 3.5 | Process | 技発動 | 技を実行する | `run_move(mon, move)` | ✓ |
| 3.6 | Interrupt | EJECTBUTTON | だっしゅつボタンによる交代 | `run_interrupt_switch()` | ✓ |
| 3.7 | Interrupt | EMERGENCY | ききかいひによる交代 | `run_interrupt_switch()` | ✓ |
| 3.8 | Interrupt | PIVOT | 交代技による交代 | `run_interrupt_switch()` | ✓ |
| 3.9 | Process | 割り込みフラグ更新 | だっしゅつパック用フラグ設定 | `override_interrupt()` | ✓ |
| 3.10 | Interrupt | EJECTPACK_AFTER_MOVE | だっしゅつパックによる交代 | `run_interrupt_switch()` | ✓ |
| 3.11 | End | 行動順ループ終了 | 全ポケモンの処理完了 | - | - |

### END_1: ターン終了処理1

| Step | Type | Name | Description | CodeMethod | Implemented |
|------|------|------|-------------|------------|-------------|
| 4.1 | Check | 割り込みチェック | 割り込みがないか確認 | `has_interrupt()` | ✓ |
| 4.2 | Event | ON_TURN_END_1 | ターン終了処理1 | `events.emit(ON_TURN_END_1)` | ✓ |
| 4.3 | Interrupt | EMERGENCY | ききかいひによる交代 | `run_interrupt_switch()` | ✓ |

**処理内容**: 天気終了判定・天気ダメージ・特性回復等

### END_2: ターン終了処理2

| Step | Type | Name | Description | CodeMethod | Implemented |
|------|------|------|-------------|------------|-------------|
| 4.4 | Check | 割り込みチェック | 割り込みがないか確認 | `has_interrupt()` | ✓ |
| 4.5 | Event | ON_TURN_END_2 | ターン終了処理2 | `events.emit(ON_TURN_END_2)` | ✓ |
| 4.6 | Interrupt | EMERGENCY | ききかいひによる交代 | `run_interrupt_switch()` | ✓ |

**処理内容**: みらいよち・ねがいごと・設置技ダメージ等

### END_3: ターン終了処理3

| Step | Type | Name | Description | CodeMethod | Implemented |
|------|------|------|-------------|------------|-------------|
| 4.7 | Check | 割り込みチェック | 割り込みがないか確認 | `has_interrupt()` | ✓ |
| 4.8 | Event | ON_TURN_END_3 | ターン終了処理3 | `events.emit(ON_TURN_END_3)` | ✓ |
| 4.9 | Interrupt | EMERGENCY | ききかいひによる交代 | `run_interrupt_switch()` | ✓ |

**処理内容**: やどりぎ・バインド・状態異常ダメージ・状態変化終了等

### END_4: ターン終了処理4

| Step | Type | Name | Description | CodeMethod | Implemented |
|------|------|------|-------------|------------|-------------|
| 4.10 | Check | 割り込みチェック | 割り込みがないか確認 | `has_interrupt()` | ✓ |
| 4.11 | Event | ON_TURN_END_4 | ターン終了処理4 | `events.emit(ON_TURN_END_4)` | ✓ |
| 4.12 | Interrupt | EMERGENCY | ききかいひによる交代 | `run_interrupt_switch()` | ✓ |

**処理内容**: 場の状態継続・終了判定・さわぐ・特性効果等

### END_5: ターン終了処理5

| Step | Type | Name | Description | CodeMethod | Implemented |
|------|------|------|-------------|------------|-------------|
| 4.13 | Check | 割り込みチェック | 割り込みがないか確認 | `has_interrupt()` | ✓ |
| 4.14 | Event | ON_TURN_END_5 | ターン終了処理5 | `events.emit(ON_TURN_END_5)` | ✓ |
| 4.15 | Process | 割り込みフラグ更新 | だっしゅつパック用フラグ設定 | `override_interrupt()` | ✓ |
| 4.16 | Interrupt | EJECTPACK_ON_TURN_END | だっしゅつパックによる交代 | `run_interrupt_switch()` | ✓ |

**処理内容**: フォルムチェンジ（ダルマモード等）

### FAINT: 瀕死処理

| Step | Type | Name | Description | CodeMethod | Implemented |
|------|------|------|-------------|------------|-------------|
| 5.0 | Interrupt | FAINT_SWITCH | 瀕死による交代 | `run_faint_switch()` | ✓ |

### END_6: ターン終了処理6

| Step | Type | Name | Description | CodeMethod | Implemented |
|------|------|------|-------------|------------|-------------|
| 5.1 | Check | 割り込みチェック | 割り込みがないか確認 | `has_interrupt()` | ✓ |
| 5.2 | Event | ON_TURN_END_6 | ターン終了処理6 | `events.emit(ON_TURN_END_6)` | ✓ |

**処理内容**: ダイマックス終了判定

### COMPLETE: ターン完了

| Step | Type | Name | Description | CodeMethod | Implemented |
|------|------|------|-------------|------------|-------------|
| 9.0 | End | ターン完了 | ターン処理終了 | - | - |

**注意**: 次の`advance_turn()`呼び出しまで待機

---

## 関連ファイル

- 実装: [src/jpoke/core/turn_controller.py](../../src/jpoke/core/turn_controller.py)
- イベント詳細: [event_priority_gen9.md](event_priority_gen9.md)

---

## 更新履歴

- 2026-02-01: 初版作成 (.github/instructions/referencesから移行)
