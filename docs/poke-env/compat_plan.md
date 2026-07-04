# poke-env 互換 実装計画

## 概要

poke-env（Pokémon Showdown クライアントライブラリ）との互換性を持たせる。
互換の方向は **poke-env → jpoke のみ**。jpoke オブジェクトを poke-env 形式でエクスポートするアダプタクラスは作成しない。

差異の詳細は `docs/poke-env/compat_analysis.md` を参照。

整理日: 2026-07-04（`docs/plan/poke_env_compat.md` から `docs/poke-env/compat_plan.md` へ移動。
ファイルパスを現在のコード構成（`src/jpoke/types/literals.py`）に合わせて修正し、
Phase 1 の完了状況と `Gender` → `PokemonGender` の改名漏れを反映）

---

## 実装フェーズ

### Phase 1: Literal 値の英語化（分類 A-1、影響範囲最大） — **値の変更は対応済み**

コードベース全体に影響するため最初に実施する想定だったが、`Stat` / `MoveCategory` / `Gender` の
**値**は本計画に先行して `src/jpoke/types/literals.py` で英語化済み（2026-07-02 確認）。

**対象: `src/jpoke/types/literals.py`**

| 型 | 変更前 | 変更後（現状） |
|---|---|---|
| `Stat` | `"H", "A", "B", "C", "D", "S"` | `"hp", "atk", "def", "spa", "spd", "spe", "accuracy", "evasion"` |
| `MoveCategory` | `"物理", "特殊", "変化"` | `"physical", "special", "status"` |
| `Gender` | `"オス", "メス", ""` | `"male", "female", ""` |

`Stat` 変更の影響範囲（対応済み）:
- `Pokemon.rank`, `Pokemon.stats` のキー
- `battle.modify_stat(stat, ...)` の引数
- ハンドラ内のすべての `Stat` 参照
- テスト内のすべての `Stat` 参照

**残タスク**: 型名 `Gender` → `PokemonGender` への改名は未着手（値のみ先行済み）。
Phase 2 の改名作業とあわせて実施する。

---

### Phase 2: 改名（分類 A-1）
ユーザーコメント: 改名はユーザーが手動で行う

Phase 1（値の英語化）は完了済みのため、このフェーズから着手できる。エイリアスは残さず呼び出し元を一括変更する。

**`types/literals.py`**

| 変更前 | 変更後 |
|---|---|
| `Gender`（型名） | `PokemonGender` |　ユーザーコメント: Genderは変更しない。

**`model/pokemon.py`**

| 変更前 | 変更後 |
|---|---|
| `executed_move` | `last_move` |
| `hp_ratio` | `hp_fraction` |
| `terastallized` | `is_terastallized` |
| `base_ability_name` | `base_ability` |
| `indiv` | `ivs` |
| `effort` | `evs` |

**`model/move.py`**

| 変更前 | 変更後 |
|---|---|
| `power` | `base_power` |
| `critical_rank` | `crit_ratio` |

**`core/player.py`**

| 変更前 | 変更後 |
|---|---|
| `name` | `username` |
| `n_won` | `n_won_battles` |
| `n_game` | `n_finished_battles` |

**`core/battle.py`**

| 変更前 | 変更後 |
|---|---|
| `rival(player)` | `opponent(player)` |

---

### Phase 3: property / エイリアスの追加（分類 A-2）

既存クラスに poke-env 互換 property を直接追加する。

**`model/pokemon.py`**

```python
@property
def current_hp(self) -> int:
    return self.hp

@property
def current_hp_fraction(self) -> float:
    return self.hp_fraction

@property
def status(self) -> str:
    """ailment.name のエイリアス（型変換なし）"""
    return self.ailment.name

@property
def boosts(self) -> dict[str, int]:
    """rank のエイリアス（Stat 英語化後はキーが一致）"""
    return self.rank

@property
def effects(self) -> dict:
    """volatiles のエイリアス（型変換なし）"""
    return self.volatiles

@property
def first_turn(self) -> bool:
    return self.active_turn == 0
```

**`model/move.py`**

```python
@property
def current_pp(self) -> int:
    return self.pp

@property
def expected_hits(self) -> float:
    return (self.min_hits + self.max_hits) / 2
```

**`core/player.py`**

```python
@property
def n_lost_battles(self) -> int:
    return self.n_finished_battles - self.n_won_battles

@property
def n_draw_battles(self) -> int:
    return self.n_finished_battles - self.n_won_battles - self.n_lost_battles

@property
def win_rate(self) -> float:
    return self.n_won_battles / self.n_finished_battles if self.n_finished_battles > 0 else 0.0
```

**`core/battle.py`**

```python
@property
def finished(self) -> bool:
    return self.winner is not None

def won(self, player: Player) -> bool:
    return self.winner is player

def lost(self, player: Player) -> bool:
    return self.winner is not None and self.winner is not player

@property
def active_pokemon(self) -> Pokemon | None:
    if self.observer:
        return self.get_active(self.observer)
    return self.actives[0] if self.actives else None

@property
def opponent_active_pokemon(self) -> Pokemon | None:
    if self.observer:
        rival = self.opponent(self.observer)
        return self.get_active(rival)
    return self.actives[1] if len(self.actives) > 1 else None

@property
def side_conditions(self) -> dict:
    """observer 側の side_managers.fields のエイリアス"""
    if self.observer:
        idx = self.players.index(self.observer)
        return self.side_managers[idx].fields
    return {}
```

---

### Phase 4: 変換テーブルの追加（分類 B）

新規ファイル `src/jpoke/types/poke_env.py` を作成する。

```python
# src/jpoke/types/poke_env.py

TYPE_MAP: dict[str, str] = {
    "Normal":   "ノーマル", "Fire":    "ほのお", "Water":   "みず",
    "Electric": "でんき",  "Grass":   "くさ",   "Ice":     "こおり",
    "Fighting": "かくとう","Poison":  "どく",   "Ground":  "じめん",
    "Flying":   "ひこう",  "Psychic": "エスパー","Bug":     "むし",
    "Rock":     "いわ",    "Ghost":   "ゴースト","Dragon":  "ドラゴン",
    "Dark":     "あく",    "Steel":   "はがね",  "Fairy":  "フェアリー",
    "Stellar":  "ステラ",
}
TYPE_MAP_INV = {v: k for k, v in TYPE_MAP.items()}

STATUS_MAP: dict[str, str] = {
    "brn": "やけど", "frz": "こおり", "par": "まひ",
    "psn": "どく",   "slp": "ねむり", "tox": "もうどく",
}
STATUS_MAP_INV = {v: k for k, v in STATUS_MAP.items()}

WEATHER_MAP: dict[str, str] = {
    "sunnyday":     "はれ",     "raindance":    "あめ",
    "sandstorm":    "すなあらし","snow":         "ゆき",
    "desolateland": "おおひでり","primordialsea":"おおあめ",
    "deltastream":  "らんきりゅう",
}
WEATHER_MAP_INV = {v: k for k, v in WEATHER_MAP.items()}

TERRAIN_MAP: dict[str, str] = {
    "electricterrain": "エレキフィールド",
    "grassyterrain":   "グラスフィールド",
    "psychicterrain":  "サイコフィールド",
    "mistyterrain":    "ミストフィールド",
}
TERRAIN_MAP_INV = {v: k for k, v in TERRAIN_MAP.items()}

NATURE_MAP: dict[str, str] = {
    "Lonely": "さみしがり", "Adamant": "いじっぱり",
    "Naughty": "やんちゃ",  "Brave":   "ゆうかん",
    "Bold":    "ずぶとい",  "Impish":  "わんぱく",
    "Lax":     "のうてんき","Relaxed": "のんき",
    "Modest":  "ひかえめ",  "Mild":    "おっとり",
    "Rash":    "うっかりや","Quiet":   "れいせい",
    "Calm":    "おだやか",  "Gentle":  "おとなしい",
    "Careful": "しんちょう","Sassy":   "なまいき",
    "Timid":   "おくびょう","Hasty":   "せっかち",
    "Jolly":   "ようき",    "Naive":   "むじゃき",
    "Hardy":   "がんばりや","Docile":  "すなお",
    "Bashful": "てれや",    "Quirky":  "きまぐれ",
    "Serious": "まじめ",
}
NATURE_MAP_INV = {v: k for k, v in NATURE_MAP.items()}

STAT_INDEX: dict[str, int] = {
    "hp": 0, "atk": 1, "def": 2, "spa": 3, "spd": 4, "spe": 5,
}


# ユーザーコメント: jpokeもatk, def, ...に変更済み
def stats_from_poke_env(d: dict[str, int]) -> list[int]:
    """poke-env の {"hp":..., "atk":...} を jpoke の [H,A,B,C,D,S] リストに変換"""
    return [d.get(k, 0) for k in ("hp", "atk", "def", "spa", "spd", "spe")]
```

---

## 依存関係とリスク

| フェーズ | 依存関係 | リスク |
|---|---|---|
| Phase 1 (Literal 値の英語化) | なし | **対応済み**。`Gender` → `PokemonGender` の型名改名のみ Phase 2 に持ち越し |
| Phase 2 (改名) | Phase 1 完了後 | 改名後の参照漏れ。grep で一括確認する |
| Phase 3 (property 追加) | Phase 2 完了後 | 既存コードへの影響なし |
| Phase 4 (変換テーブル) | 独立（いつでも可） | poke-env 依存なし |

## 対象外

- jpoke → poke-env エクスポート（アダプタクラス・`BattleOrder`変換等）
- poke-env の Showdown サーバー接続機能（WebSocket 等）
- ダイナマックス・Z ワザ（jpoke 未実装）
