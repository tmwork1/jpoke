# poke-env 互換レイヤ 実装計画

## 概要

poke-env（Pokémon Showdown クライアントライブラリ）との互換性を持たせる。
jpoke で学習・開発した AI エージェントを poke-env 経由で Showdown サーバーへ接続しやすくすることが目的。

互換の方向は **「poke-env の Player インターフェースを使って jpoke バトルを動かせる」** こと。
逆方向（jpoke から Showdown サーバーへの直接接続）は本計画のスコープ外。

## 差異の分類

調査の結果、差異を 4 種類に分類した。

| 分類 | 内容 | 方針 |
|---|---|---|
| A | 変数名の違いのみ | jpoke 側にエイリアス property を追加 |
| B | 型・構造・言語の違い | アダプタクラスを別モジュールに実装 |
| C | poke-env 側にのみある機能 | スコープ外（主に PS サーバー接続） |
| D | jpoke 側にのみある機能 | 変更不要（jpoke の強み） |

---

## Phase 1: エイリアス property の追加（分類 A）

既存クラスに後方互換 property を追加するだけ。既存コードへの影響ゼロ。

### 1-1. `Pokemon` クラス（`model/pokemon.py`）

```python
# 追加する property
@property
def current_hp(self) -> int:       # current_hp -> hp
    return self.hp

@property
def current_hp_fraction(self) -> float:  # current_hp_fraction -> hp_ratio
    return self.hp_ratio

@property
def last_move(self) -> Move | None:  # last_move -> executed_move
    return self.executed_move

@property
def is_terastallized(self) -> bool:  # is_terastallized -> terastallized
    return self.terastallized

@property
def first_turn(self) -> bool:        # first_turn -> active_turn == 0
    return self.active_turn == 0

@property
def stab_multiplier(self) -> float:
    return 1.5  # テラスタル・適応力は別途検討
```

### 1-2. `Move` クラス（`model/move.py`）

```python
@property
def base_power(self) -> int | None:  # base_power -> power
    return self.power

@property
def current_pp(self) -> int:         # current_pp -> pp
    return self.pp

@property
def crit_ratio(self) -> int:         # crit_ratio -> critical_rank
    return self.critical_rank

@property
def expected_hits(self) -> float:
    return (self.min_hits + self.max_hits) / 2
```

### 1-3. `Player` クラス（`core/player.py`）

```python
@property
def username(self) -> str:           # username -> name
    return self.name

@property
def n_won_battles(self) -> int:      # n_won_battles -> n_won
    return self.n_won

@property
def n_finished_battles(self) -> int: # n_finished_battles -> n_game
    return self.n_game

@property
def n_lost_battles(self) -> int:
    return self.n_game - self.n_won

@property
def win_rate(self) -> float:
    return self.n_won / self.n_game if self.n_game > 0 else 0.0
```

### 1-4. `Battle` クラス（`core/battle.py`）

```python
@property
def finished(self) -> bool:
    return self.winner is not None

@property
def active_pokemon(self) -> Pokemon | None:
    # observer が設定されている場合は observer 視点
    if self.observer:
        return self.get_active(self.observer)
    return self.actives[0] if self.actives else None

@property
def opponent_active_pokemon(self) -> Pokemon | None:
    if self.observer:
        rival = self.rival(self.observer)
        return self.get_active(rival)
    return self.actives[1] if len(self.actives) > 1 else None
```

---

## Phase 2: 変換ユーティリティの追加（分類 B）

新規ファイル `src/jpoke/compat/poke_env.py` を作成する。

### 2-1. Enum ↔ 日本語 Literal 変換テーブル

最も影響範囲が広い。すべての型変換の基盤となる。

```python
# src/jpoke/compat/poke_env.py

TYPE_MAP: dict[str, str] = {
    "Normal":   "ノーマル",
    "Fire":     "ほのお",
    "Water":    "みず",
    "Electric": "でんき",
    "Grass":    "くさ",
    "Ice":      "こおり",
    "Fighting": "かくとう",
    "Poison":   "どく",
    "Ground":   "じめん",
    "Flying":   "ひこう",
    "Psychic":  "エスパー",
    "Bug":      "むし",
    "Rock":     "いわ",
    "Ghost":    "ゴースト",
    "Dragon":   "ドラゴン",
    "Dark":     "あく",
    "Steel":    "はがね",
    "Fairy":    "フェアリー",
    "Stellar":  "ステラ",
}
TYPE_MAP_INV = {v: k for k, v in TYPE_MAP.items()}

STATUS_MAP: dict[str, str] = {
    "brn": "やけど",
    "frz": "こおり",
    "par": "まひ",
    "psn": "どく",
    "slp": "ねむり",
    "tox": "もうどく",
}
STATUS_MAP_INV = {v: k for k, v in STATUS_MAP.items()}

CATEGORY_MAP: dict[str, str] = {
    "Physical": "物理",
    "Special":  "特殊",
    "Status":   "変化",
}
CATEGORY_MAP_INV = {v: k for k, v in CATEGORY_MAP.items()}

STAT_KEY_MAP: dict[str, str] = {
    # poke-env 英語キー -> jpoke Stat Literal
    "hp":  "H",
    "atk": "A",
    "def": "B",
    "spa": "C",
    "spd": "D",
    "spe": "S",
}
STAT_KEY_MAP_INV = {v: k for k, v in STAT_KEY_MAP.items()}

STAT_INDEX_MAP: dict[str, int] = {
    # poke-env 英語キー -> jpoke list インデックス
    "hp": 0, "atk": 1, "def": 2, "spa": 3, "spd": 4, "spe": 5,
}

WEATHER_MAP: dict[str, str] = {
    "sunnyday":     "はれ",
    "raindance":    "あめ",
    "sandstorm":    "すなあらし",
    "snow":         "ゆき",
    "desolateland": "おおひでり",
    "primordialsea":"おおあめ",
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
```

### 2-2. `stats` / `ivs` / `evs` 変換ヘルパー

```python
def stats_to_poke_env(jpoke_list: list[int]) -> dict[str, int]:
    """jpoke の [H,A,B,C,D,S] リストを poke-env の {"hp":..., "atk":...} 形式に変換"""
    keys = ["hp", "atk", "def", "spa", "spd", "spe"]
    return dict(zip(keys, jpoke_list))

def stats_to_jpoke(poke_env_dict: dict[str, int]) -> list[int]:
    """poke-env の {"hp":..., ...} を jpoke の [H,A,B,C,D,S] リストに変換"""
    keys = ["hp", "atk", "def", "spa", "spd", "spe"]
    return [poke_env_dict.get(k, 0) for k in keys]

def boosts_to_poke_env(rank: dict[str, int]) -> dict[str, int]:
    """jpoke の rank（Stat キー）を poke-env の boosts（英語キー）に変換"""
    out = {}
    for jpoke_key, en_key in STAT_KEY_MAP_INV.items():
        if jpoke_key in rank:
            out[en_key] = rank[jpoke_key]
    return out
```

### 2-3. `PokeEnvBattleAdapter` クラス

poke-env の `Player.choose_move(battle)` に渡す Battle 互換オブジェクト。
jpoke の `Battle` をラップし、poke-env が期待するインターフェースを提供する。

```python
class PokeEnvBattleAdapter:
    """poke-env の AbstractBattle 互換インターフェースを提供するアダプタ"""

    def __init__(self, battle: Battle, player: Player):
        self._battle = battle
        self._player = player

    @property
    def active_pokemon(self) -> PokeEnvPokemonAdapter:
        return PokeEnvPokemonAdapter(self._battle.get_active(self._player))

    @property
    def opponent_active_pokemon(self) -> PokeEnvPokemonAdapter:
        rival = self._battle.rival(self._player)
        return PokeEnvPokemonAdapter(self._battle.get_active(rival))

    @property
    def available_moves(self) -> list[PokeEnvMoveAdapter]:
        commands = self._battle.get_available_commands(self._player)
        moves = []
        for cmd in commands:
            move = self._battle.command_to_move(self._player, cmd)
            if move:
                moves.append(PokeEnvMoveAdapter(move))
        return moves

    @property
    def available_switches(self) -> list[PokeEnvPokemonAdapter]:
        ps = self._battle.player_states[self._player]
        active = self._battle.get_active(self._player)
        return [
            PokeEnvPokemonAdapter(mon)
            for mon in ps.team
            if mon.alive and mon is not active
        ]

    @property
    def team(self) -> dict[str, PokeEnvPokemonAdapter]:
        ps = self._battle.player_states[self._player]
        return {mon.name: PokeEnvPokemonAdapter(mon) for mon in ps.team}

    @property
    def opponent_team(self) -> dict[str, PokeEnvPokemonAdapter]:
        rival = self._battle.rival(self._player)
        ps = self._battle.player_states[rival]
        return {mon.name: PokeEnvPokemonAdapter(mon) for mon in ps.team}

    @property
    def weather(self) -> dict[str, int]:
        w = self._battle.weather
        if w.name:
            return {WEATHER_MAP_INV.get(w.name, w.name): w.count}
        return {}

    @property
    def fields(self) -> dict[str, int]:
        t = self._battle.terrain
        if t.name:
            return {TERRAIN_MAP_INV.get(t.name, t.name): t.count}
        return {}

    @property
    def turn(self) -> int:
        return self._battle.turn

    @property
    def finished(self) -> bool:
        return self._battle.winner is not None

    @property
    def won(self) -> bool:
        return self._battle.winner is self._player

    @property
    def lost(self) -> bool:
        return self._battle.winner is not None and not self.won

    @property
    def can_tera(self) -> bool:
        ps = self._battle.player_states[self._player]
        return not ps.used_terastal

    @property
    def can_mega_evolve(self) -> bool:
        ps = self._battle.player_states[self._player]
        return not ps.used_megaevol
```

### 2-4. `PokeEnvPokemonAdapter` クラス

```python
class PokeEnvPokemonAdapter:
    """poke-env の Pokemon 互換インターフェースを提供するアダプタ"""

    def __init__(self, mon: Pokemon):
        self._mon = mon

    # 委譲
    def __getattr__(self, name):
        return getattr(self._mon, name)

    @property
    def current_hp(self) -> int:
        return self._mon.hp

    @property
    def max_hp(self) -> int:
        return self._mon.max_hp

    @property
    def current_hp_fraction(self) -> float:
        return self._mon.hp_ratio

    @property
    def ability(self) -> str | None:
        return self._mon.ability.name if self._mon.ability else None

    @property
    def item(self) -> str | None:
        return self._mon.item.name if self._mon.item else None

    @property
    def status(self) -> str | None:
        if self._mon.ailment.name:
            return STATUS_MAP_INV.get(self._mon.ailment.name)
        return None

    @property
    def boosts(self) -> dict[str, int]:
        return boosts_to_poke_env(self._mon.rank)

    @property
    def stats(self) -> dict[str, int]:
        return stats_to_poke_env(list(self._mon.stats.values()))

    @property
    def ivs(self) -> dict[str, int]:
        return stats_to_poke_env(self._mon.indiv)

    @property
    def evs(self) -> dict[str, int]:
        return stats_to_poke_env(self._mon.effort)

    @property
    def moves(self) -> dict[str, PokeEnvMoveAdapter]:
        return {m.name: PokeEnvMoveAdapter(m) for m in self._mon.moves}

    @property
    def last_move(self):
        if self._mon.executed_move:
            return PokeEnvMoveAdapter(self._mon.executed_move)
        return None

    @property
    def is_terastallized(self) -> bool:
        return self._mon.terastallized

    @property
    def first_turn(self) -> bool:
        return self._mon.active_turn == 0

    @property
    def fainted(self) -> bool:
        return self._mon.fainted
```

### 2-5. `PokeEnvMoveAdapter` クラス

```python
class PokeEnvMoveAdapter:
    """poke-env の Move 互換インターフェースを提供するアダプタ"""

    def __init__(self, move: Move):
        self._move = move

    def __getattr__(self, name):
        return getattr(self._move, name)

    @property
    def base_power(self) -> int | None:
        return self._move.power

    @property
    def current_pp(self) -> int:
        return self._move.pp

    @property
    def crit_ratio(self) -> int:
        return self._move.critical_rank

    @property
    def accuracy(self) -> int | bool:
        # jpoke: None = 必中, poke-env: True = 必中
        if self._move.accuracy is None:
            return True
        return self._move.accuracy

    @property
    def category(self) -> str:
        return CATEGORY_MAP_INV.get(self._move.category, self._move.category)

    @property
    def type(self) -> str:
        return TYPE_MAP_INV.get(self._move.type, self._move.type)

    @property
    def expected_hits(self) -> float:
        return (self._move.min_hits + self._move.max_hits) / 2

    @property
    def n_hit(self) -> tuple[int, int]:
        return (self._move.min_hits, self._move.max_hits)
```

### 2-6. `PokeEnvPlayerAdapter` クラス

poke-env の `Player` 規約（`choose_move(battle) -> BattleOrder`）に準拠した jpoke Player ラッパー。
これを使うことで、jpoke の `Player` サブクラスを poke-env 対応 AI フレームワークから呼べる。

```python
class PokeEnvPlayerAdapter:
    """
    jpoke の Player を poke-env の Player 規約に変換するアダプタ。
    poke-env の BattleOrder を jpoke の Command に橋渡しする。
    """

    def __init__(self, player: Player):
        self._player = player

    def choose_move(self, battle) -> "BattleOrder":
        """
        poke-env が呼ぶエントリポイント。
        PokeEnvBattleAdapter を受け取り、jpoke の choose_command を呼んで
        Command を BattleOrder に変換する。
        """
        adapted = PokeEnvBattleAdapter(battle._jpoke_battle, self._player)
        command = self._player.choose_command(adapted._battle)
        return _command_to_battle_order(adapted._battle, self._player, command)

    @property
    def username(self) -> str:
        return self._player.name

    @property
    def n_won_battles(self) -> int:
        return self._player.n_won

    @property
    def n_finished_battles(self) -> int:
        return self._player.n_game
```

---

## Phase 3: `Command` → `BattleOrder` 変換（分類 B の中核）

poke-env の `BattleOrder` は技か交代を包むラッパーオブジェクト。
jpoke の `Command` Enum（MOVE_0, SWITCH_2, TERASTAL_0 等）との対応が必要。

```python
def _command_to_battle_order(battle, player, command):
    """jpoke Command を poke-env BattleOrder に変換する"""
    from poke_env.player import BattleOrder
    cmd_str = command.name.lower()

    if cmd_str.startswith("move_"):
        idx = int(cmd_str[-1])
        move = battle.player_states[player].team[0].moves[idx]  # 簡略
        return BattleOrder(PokeEnvMoveAdapter(move))

    if cmd_str.startswith("switch_"):
        idx = int(cmd_str[-1])
        mon = battle.player_states[player].team[idx]
        return BattleOrder(PokeEnvPokemonAdapter(mon))

    if cmd_str.startswith("terastal_"):
        idx = int(cmd_str[-1])
        move = battle.player_states[player].team[0].moves[idx]
        return BattleOrder(PokeEnvMoveAdapter(move), terastallize=True)

    if cmd_str.startswith("megaevol_"):
        idx = int(cmd_str[-1])
        move = battle.player_states[player].team[0].moves[idx]
        return BattleOrder(PokeEnvMoveAdapter(move), mega=True)

    raise ValueError(f"変換できない Command: {command}")
```

---

## ファイル構成

```
src/jpoke/
  compat/
    __init__.py          # PokeEnvBattleAdapter, PokeEnvPokemonAdapter,
                         # PokeEnvMoveAdapter, PokeEnvPlayerAdapter をエクスポート
    poke_env.py          # 上記すべてのアダプタクラスと変換テーブル
```

既存クラスへのエイリアス追加（Phase 1）は各ファイルへの直接追記。

---

## スコープ外（分類 C）

以下は本計画では対応しない：

- Pokémon Showdown サーバーへの WebSocket 接続（`parse_message`, `accept_challenges`, `ladder` 等）
- ダイナマックス・Zyワザ（jpoke 未実装）
- リプレイ保存（`save_replay`）
- `format` / `gen` / `battle_tag` などのメタ情報
- `available_moves_from_request`（PS リクエスト JSON 解析）

---

## 実装順序

| 順序 | 作業 | ファイル | 難易度 |
|---|---|---|---|
| 1 | エイリアス property 追加（Pokemon） | `model/pokemon.py` | 低 |
| 2 | エイリアス property 追加（Move） | `model/move.py` | 低 |
| 3 | エイリアス property 追加（Player） | `core/player.py` | 低 |
| 4 | エイリアス property 追加（Battle） | `core/battle.py` | 低 |
| 5 | 変換テーブル作成 | `compat/poke_env.py` | 低 |
| 6 | `PokeEnvMoveAdapter` 実装 | `compat/poke_env.py` | 低 |
| 7 | `PokeEnvPokemonAdapter` 実装 | `compat/poke_env.py` | 中 |
| 8 | `PokeEnvBattleAdapter` 実装 | `compat/poke_env.py` | 中 |
| 9 | `Command` → `BattleOrder` 変換 | `compat/poke_env.py` | 高 |
| 10 | `PokeEnvPlayerAdapter` 実装 | `compat/poke_env.py` | 高 |

Phase 1（1〜4）は独立して実施可能で即効性が高い。
Phase 2（5〜10）は poke-env への実依存が発生するため、`poke_env` がインストール済みの環境でのみ動作する。`ImportError` で graceful に fallback するガード節を入れること。

---

## 留意事項

- **言語差異（英語 ↔ 日本語）は変換テーブルで吸収**する。変換テーブルは `compat/poke_env.py` に集約し、他所でハードコーディングしない。
- アダプタクラスは **`__getattr__` で未定義プロパティを委譲**することで、jpoke 固有機能（`calc_lethal`, `build_observation` 等）を poke-env 互換環境からも透過的に使える。
- Phase 1 のエイリアスは既存テストへの影響なし。Phase 2 は poke-env を `import` しないため既存テストへの影響なし。
- `PokeEnvPlayerAdapter` を使う場合、バトルの進行（`battle.step()`）は jpoke 側が担う。poke-env の非同期 I/O ループとの統合は別途検討。
