# 実装計画: poke-env Battle → jpoke Battle 変換機構

更新日: 2026-07-11

## スコープ

- 対象: 新規 `src/jpoke/interop/` パッケージ、`src/jpoke/types/poke_env.py`（改修・追加）、
  `src/jpoke/core/battle.py`（`Battle.from_poke_env()` classmethod 追加）、
  `src/jpoke/exceptions.py`（`PokeEnvConversionError` 追加）
- 実装状態: 未着手（本ドキュメントは計画のみ。実装は別途着手する）
- 方針: poke-env の `Battle` オブジェクト（進行中の対戦状態）を渡すと、jpoke の `Battle`
  インスタンスを生成する変換機構を作る。既存の poke-env 互換実装（`docs/poke-env/compat_plan.md`
  Phase 1〜5、mainにマージ済み）はプロパティ名・値レベルの互換に留まっていたが、本計画は
  battle レベルのファクトリを新設する点で毛色が異なる。

## 前提

- `docs/poke-env/compat_plan.md`（Phase 1〜5）・`docs/poke-env/compat_analysis.md` は
  「poke-env → jpoke 一方向のみ、jpoke → poke-env のエクスポートは対象外」という方針だが、
  「poke-env の Battle オブジェクト全体から jpoke Battle を構築する」battle レベルの
  コンバータへの言及はなく、本計画が初出。既存方針とは矛盾しない（クラスではなく関数/classmethod
  を追加するのみで、jpoke → poke-env 方向のアダプタクラスではない）。
- `src/jpoke/types/poke_env.py` に既存の変換テーブル・関数がある: `TYPE_MAP`, `STATUS_MAP`,
  `WEATHER_MAP`, `TERRAIN_MAP`, `GLOBAL_FIELD_MAP`, `SIDE_CONDITION_MAP`, `NATURE_MAP`
  （各 `_INV` 逆引きも有り）、`STAT_INDEX`, `stats_from_poke_env`, `evs_from_poke_env`。
- **種族名・技名・特性名・アイテム名の EN→JP 変換テーブルはリポジトリに一切存在しない**
  （`pokedex.json` は日本語名のみで管理。生成元の `zukan.json` は削除済みで復元不可）。
  **ユーザー方針: 中身のデータは別途ユーザー側で用意する。本計画はマッピングを受け取って参照する
  設計・スタブ（空dict）の用意までに留め、実データ投入はスコープ外とする。**
- poke-env の `Battle` は部分観測（相手の個体値・努力値・特性・持ち物・未使用技が `None`/不明に
  なりうる）。**ユーザー方針: 不明値は妥当なデフォルト値で補完し、変換自体は必ず成功させる。**
- **ユーザー方針: チーム編成だけでなく、進行中バトルの状態（HP・状態異常・ランク変化・場の状態・
  ターン数）まで同期する深いレベルまで対応する。**
- poke-env は jpoke 本体の実行時依存には追加しない（`interop/poke_env.py` は `TYPE_CHECKING`
  限定でのみ import し、実行時は `Any` で受け取る）。ただし**検証（テスト）には実際の poke-env を
  使う**（ユーザー方針）。`pip index versions poke-env` で PyPI 経由のインストールが可能なことを
  確認済み（最新 0.15.0）。`[dependency-groups] dev`（`pyproject.toml`）にテスト専用依存として
  追加する。

### 調査で判明した重要事項（`docs/poke-env/api_reference/` の poke-env 公式ドキュメントより）

- 最新 poke-env（`poke_env.battle.pokemon.Pokemon`）では `ivs`/`evs` は `dict` ではなく
  `list[int] | None`（`[HP, Atk, Def, SpA, SpD, Spe]` 順、jpokeと同じ並び）。既存の
  `stats_from_poke_env`/`evs_from_poke_env`（`types/poke_env.py`）は dict 入力前提のため改修が必要。
- `weather`/`fields`/`side_conditions` の値は「残りターン数」ではなく「開始ターン」または
  「層数（スタック可能なもののみ）」。jpoke の `Field.count`（残りターン数）に変換するには
  `標準継続ターン数 - (battle.turn - 開始ターン)` の計算と、延長アイテムを考慮しない
  「基本ターン数を仮定する」近似が必要（個体値31固定などと同種の不明値デフォルト補完）。
- 相手ポケモンの `current_hp`/`max_hp` はスケールが信用できない（0〜100 or ピクセルスケールの
  場合がある）。`current_hp_fraction`（float、信頼できる）を正として使う。
- `ability`/`item`/`nature` は `None` を取りうる（不明値のデフォルト補完対象）。
- `DoubleBattle.active_pokemon` は list になる（`Battle` は `Pokemon | None`）。ダブルバトルは
  ダックタイピングで検知しスコープ外として拒否する（CLAUDE.m「対象はシングルバトルのみ」に整合）。
- **実機検証済み**: 一時venvに `poke-env==0.15.0` をインストールし、`Battle(battle_tag, username,
  logger, gen=9)` を生成後 `battle.parse_message([...])` に合成プロトコル行
  （`['', 'switch', 'p1a: Pikachu', 'Pikachu, L50, M', '100/100']` 等）を渡すだけで、実サーバー
  接続なしに実物の `Battle`/`Pokemon` インスタンスを構築できることを確認した（poke-env 本家の
  テストスイートと同じ手法）。`battle.team` のキーは `"p1: Pikachu"`（`{role}: {表示名}`）形式
  （`compat_analysis.md` の「英語識別子キー」という記述より具体的）。本計画の変換処理は
  `team.values()` からPokemonオブジェクトのみを取り出すため、このキー形式に依存しない。

### jpoke 内部の調査結果（`Battle.start()` をバイパスせず活用する方針の根拠）

- `TurnController.start_battle()`（`core/turn_controller.py`）は
  「選出（`Player.choose_selection()` 呼び出し）→ `turn=0` → 先頭ポケモンを場に出す
  （`ON_SWITCH_IN` 発火）→ だっしゅつパック割り込み」という手順。`n_selected` は
  デフォルトの `choose_selection` 実装以外からは一切参照されないため、選出順序を制御する
  カスタム `Player` サブクラスで「poke-env で実際に場に出ているポケモンを先頭にする」ことができる。
- `weather_manager.apply()` 等の field manager 系メソッドはイベント発火を伴う（副作用あり）が、
  `tests/test_utils.py` の `start_battle()` ヘルパーが「`battle.start()` 完了後に manager を
  直接呼んで初期状態を構築する」という前例を既に確立している。本計画もこれに倣う。
- `battle.turn` の直接上書きは安全（`turn` に依存する他の内部カウンタは独立していることを確認済み）。
- HP・状態異常・ランク変化・揮発性状態の「イベントを発火させない直接代入」
  （`mon.hp = value`、`mon.ailment = Ailment(...)` 等）は、内部実装（`ailment_manager.py`、
  `switch_manager.py` のバトンタッチ処理等）や既存テスト（`tests/abilities/test_ability_*.py` での
  `mon.hp = 1` 等）に前例がある「初期状態構築用途」としての意図的な例外。ただし active な
  ポケモンについては `register_handlers`/`unregister_handlers`（`GameEffect` 基底クラスの公開メソッド）
  を手動で呼び直す必要がある。

## 方針

### モジュール構成

```
src/jpoke/interop/__init__.py     # 新規パッケージ（battleレベルのオーケストレーション）
src/jpoke/interop/poke_env.py     # 変換本体（新規）
src/jpoke/types/poke_env.py       # 既存テーブルの改修・追加
src/jpoke/core/battle.py          # Battle.from_poke_env() classmethod を追加（薄い入口）
src/jpoke/exceptions.py           # PokeEnvConversionError を追加
```

`types/poke_env.py` は既存方針上「プロパティ単位の変換テーブル・純粋関数」に限定されているため、
Player/Pokemon/Battle をまたいで手順を制御するオーケストレーション処理は新規 `interop/` パッケージに
分離する。利用者向けの公開入口は `Battle.from_poke_env()` 1つに絞り（CLAUDE.md
「外部APIはBattleの公開メソッドを入口にする」に整合）、内部実装は `interop/poke_env.py` に置く。

## 実装ステップ

### ステップ1: `types/poke_env.py` の改修・追加

- `stats_from_poke_env` / `evs_from_poke_env` を **dict と list 両対応**に改修する
  （`None` はそのまま `None` を返し、呼び出し側でデフォルト補完する）。既存の型を緩めるだけで
  戻り値の意味は不変（後方互換）。
- 新規マッピングを追加:
  - `GENDER_MAP`（`"Male"/"Female"/"Neutral"` → jpoke `Gender` の `"male"/"female"/""`）
  - `EFFECT_MAP`（poke-env `Effect` Enum → jpoke `VolatileName`。判明分のみ実装し、未対応キーは
    変換時に `PokeEnvConversionError` で明示的に失敗させる）
  - `DEFAULT_FIELD_DURATION`（天候・地形・グローバル・サイドフィールドの「延長アイテムなし基本
    継続ターン数」表）
- キー表記揺れに注意: 既存 `TYPE_MAP`/`NATURE_MAP` は `Capitalize`、`WEATHER_MAP` 等は全小文字。
  モジュール冒頭のコメント（`name.lower()` に統一、という記述）は実装と食い違っているため、
  改修時にコメントを実態に合わせて修正する。

### ステップ2: `interop/poke_env.py`（新規）

```python
from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from poke_env.battle import Battle as PokeEnvBattle, Pokemon as PokeEnvPokemon

@dataclass
class PokeEnvNameMaps:
    """種族名・技名・特性名・アイテム名のEN→JP変換テーブル（中身は利用者が用意する）。"""
    species: dict[str, str] = field(default_factory=dict)
    moves: dict[str, str] = field(default_factory=dict)
    abilities: dict[str, str] = field(default_factory=dict)
    items: dict[str, str] = field(default_factory=dict)

def from_poke_env_battle(pe_battle, name_maps: PokeEnvNameMaps, *,
                          n_selected=None, seed=None,
                          mega_evolution=True, terastal=True) -> Battle: ...

def _convert_pokemon(pe_mon, name_maps, *, known_stats: bool) -> Pokemon: ...
```

**Pokemon 変換（`_convert_pokemon`）**:
種族名・特性・アイテム・技名は `name_maps.*` で解決（`KeyError` は変換元の値を含めて
`PokeEnvConversionError` に変換）。不明値の補完:
- 個体値/努力値が `None` → 何もしない（`Pokemon` の既定値 `ivs=[31]*6`/`evs=[0]*6` が
  そのままユーザー方針「個体値31固定・努力値0」と一致するため補完不要）
- 特性 `None` → `POKEDEX[species_ja].abilities[0]`（候補先頭）
- アイテム `None`/`""` → `""`
- 性格 `None` → `"まじめ"`
- 技が4件未満 → 残り枠を `"はねる"` で埋める（`Pokemon.__init__` 既定のプレースホルダーと同じ）
- テラスタイプ `None` → `Pokemon.__init__` に渡さず、既存の自動補完（`base_types[0]`）に任せる

**Battle 変換（`from_poke_env_battle`、手順）**:
1. ダブルバトル検知（`active_pokemon` が list/tuple なら `PokeEnvConversionError`）
2. `pe_battle.team` / `opponent_team` の各 Pokemon を変換し `list[Pokemon]` を得る
3. `Player` 2体を生成し `.team` にセット（`players[0]` = 自分視点固定、とドキュメント化）
4. 選出を固定する内部限定の `_FixedSelectionPlayer(Player)` を使い、`choose_selection` で
   「現在アクティブな種族が先頭に来る」順序を返す
5. `Battle((self_player, opponent_player), n_selected=..., seed=..., mega_evolution=..., terastal=...)`
   を構築し `battle.start()` を呼ぶ（通常のON_SWITCH_INフロー。副作用は後続手順の上書きで解消される）
6. active一致検証（だっしゅつパック等の割り込みで想定外の交代が起きていないか）。
   不一致なら `PokeEnvConversionError`
7. 天候・地形・グローバル・サイドフィールドを `DEFAULT_FIELD_DURATION` から残りターン数を算出して
   `battle.weather_manager.apply()` / `terrain_manager.apply()` / `global_manager.activate()` /
   `side_managers[i].activate()` で注入
8. `battle.turn = pe_battle.turn` を直接上書き
9. 全ポケモン（ベンチ含む）に HP・状態異常を注入。自チームは `current_hp` をそのまま、
   相手チームは `round(current_hp_fraction * mon.max_hp)` で概算
10. active な2体のみランク変化（`battle.modify_stats()`、公開API）と揮発性状態
    （`EFFECT_MAP` 経由、直接代入）を注入。手順9で `ailment` を差し替えた active 2体は
    `mon.ailment.register_handlers(battle.events, mon)` を呼び直す

### ステップ3: `core/battle.py` への追加

```python
@classmethod
def from_poke_env(cls, pe_battle: Any, name_maps: "PokeEnvNameMaps", **kwargs) -> "Battle":
    from jpoke.interop.poke_env import from_poke_env_battle  # 循環import回避の遅延import
    return from_poke_env_battle(pe_battle, name_maps, **kwargs)
```

### ステップ4: `exceptions.py` への追加

```python
class PokeEnvConversionError(JpokeError, ValueError):
    """poke-env Battle/Pokemon から jpoke への変換に失敗した場合の例外。"""
```

### ステップ5: テスト・検証

**ユーザー方針: モック（`SimpleNamespace`）ではなく実際の poke-env を使って検証する。**

- `poke-env` を `[dependency-groups] dev`（`pyproject.toml`）にテスト専用依存として追加する
  （jpoke 本体の実行時依存には追加しない。`interop/poke_env.py` は引き続き `TYPE_CHECKING` 限定 import）
- `tests/interop/test_poke_env.py`（新規）で、実際に `poke_env.battle.Battle` /
  `poke_env.battle.Pokemon` を構築して検証する。実サーバー接続は不要で、
  `Battle(battle_tag, username, logger, gen=9)` を生成し `battle.parse_message([...])` に合成の
  Pokémon Showdown プロトコル行を渡すことで実物のオブジェクトを組み立てられる（実機検証済み。
  poke-env 本家のテストスイートと同じ手法）。例:
  ```python
  battle = Battle("battle-gen9ou-1", "myuser", logger, gen=9)
  battle.parse_message(["", "player", "p1", "myuser", "", ""])
  battle.parse_message(["", "player", "p2", "opponent", "", ""])
  battle.parse_message(["", "switch", "p1a: Pikachu", "Pikachu, L50, M", "100/100"])
  battle.parse_message(["", "switch", "p2a: Charizard", "Charizard, L50, M", "100/100"])
  battle.parse_message(["", "-weather", "SunnyDay"])
  ```
- 正常系: 自チーム/相手チームの変換、HP割合換算、天候/地形の残りターン数計算、選出・active一致、
  ランク変化・状態異常・揮発性状態の注入。`ivs`/`evs`/`ability`/`item`/`nature` が `None`
  （未判明）のケースはプロトコル行を送らず自然に再現できる（実機検証で確認済み: 何も送らなければ
  `ivs`/`evs` は `None` のまま）
- 異常系: 未知の種族名/技名/特性名/アイテム名、ダブルバトル拒否、active不一致時のエラー
- 全体: `python -m pytest tests/ -v` で既存テストに regression がないことを確認
- `docs/poke-env/compat_plan.md` に「Phase 6: Battle変換機構」として本計画の要約を追記し、
  `docs/poke-env/compat_analysis.md` にも battle-level converter の存在を追記する

## 影響範囲

| 項目 | 内容 |
|---|---|
| CLAUDE.md「外部APIはBattleの公開メソッドを入口にする」 | `Battle.from_poke_env()` classmethodを唯一の公開入口とすることで遵守 |
| `battle.modify_hp` 必須ルール | HP注入は `mon.hp = value` の直接代入を採用（既存テストの前例に基づく意図的な例外）。プロジェクトのCLAUDE.mdに「初期状態構築時は直接代入を許容する」旨の追記を実装と合わせて検討する |
| Phase1-5（compat_plan.md）との整合 | 既存4テーブルをそのまま再利用。`stats_from_poke_env`/`evs_from_poke_env` のdict/list両対応化は破壊的変更ではない |

## リスク・注意点

- 新規テーブル（GENDER_MAP, EFFECT_MAP）はPhase4に存在しなかった欠落。追加時は既存のキー表記揺れ
  （Capitalize vs lower）に注意する
- 種族名・技名・特性名・アイテム名データは `PokeEnvNameMaps` の空dictスタブのみ用意し、実データは対象外
- だっしゅつパック等による初期繰り出し時の想定外交代は、`start()` 実行後の active 一致検証で検知し、
  サイレントに進めず例外化する（レアケースのため無理な回避策は設けない）
- 強天候（おおひでり等）の残りターン数概念は `handlers/ability.py` 側の tick_down 抑制ロジックを
  実装時に要確認。本計画では暫定的に標準ターン数を設定する前提を置いている
- メガシンカ中/テラスタル中ポケモンの変換は進化前情報の逆引きを簡略化する（進化後の状態をそのまま
  変換元として扱う）。将来的な精緻化の余地として明記する
- ダブルバトル（`DoubleBattle`）は明示的にスコープ外として拒否する

## 対象外（今回のスコープ外）

- 種族名・技名・特性名・アイテム名の実データ投入（`PokeEnvNameMaps` はスタブのみ、中身はユーザーが用意）
- ダブルバトル（`DoubleBattle`）対応
- jpoke → poke-env のエクスポート方向（既存方針を継続）
- メガシンカ/テラスタル前の状態への逆変換（進化後の状態をそのまま変換元として扱う簡略化）
