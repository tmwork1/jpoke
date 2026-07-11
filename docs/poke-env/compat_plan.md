# poke-env 互換 実装計画

## 概要

poke-env（Pokémon Showdown クライアントライブラリ）との互換性を持たせる。
互換の方向は **poke-env → jpoke のみ**。jpoke オブジェクトを poke-env 形式でエクスポートするアダプタクラスは作成しない。

差異の詳細は `docs/poke-env/compat_analysis.md` を参照。

整理日: 2026-07-04（`docs/plan/poke_env_compat.md` から `docs/poke-env/compat_plan.md` へ移動。
ファイルパスを現在のコード構成（`src/jpoke/types/literals.py`）に合わせて修正し、
Phase 1 の完了状況と `Gender` → `PokemonGender` の改名漏れを反映）

レビュー日: 2026-07-07（`docs/poke-env/api_reference/` の poke-env 公式ドキュメントと照合。
`accuracy`（0〜1 float 化）・`expected_hits`（分布期待値）・`n_tied_battles`（`n_draw_battles` は存在しない）・
`won`/`lost`（プロパティで `bool | None`）の仕様誤りを修正し、Phase 2 の `rank → boosts` 漏れ、
Phase 3 の `max_pp`/`team`/`available_moves`/`available_switches` 漏れ、
Phase 4 の `SIDE_CONDITION_MAP`/`GLOBAL_FIELD_MAP` 不足と `evs` スケール変換を補完。
`Gender` 型名は改名しない方針（ユーザーコメント）に統一）

追記日: 2026-07-07（Phase 5 を新設。poke-env ユーザー向けのインターフェース互換として
`Player.battle_against()` を追加する計画を明文化。ユーザー方針: 実装を歪めない範囲で
インターフェースにも互換性を持たせる）

更新日: 2026-07-11（refactor/inline-pokemon-stats 系のリファクタ（Pokemonの一時状態のmemoryスコープ統一、
`executed_move` 算出プロパティ化、くちばしキャノン再実装による `protect_chain_move` 撤廃）を反映。
Phase 3 の `first_turn` 実装案を `active_turn == 0`（フィールド自体が廃止済み）から
`not acted_since_switch_in` に修正し、Phase 2 の `executed_move` 改名注意に
新設された `last_move_type`/`last_move_name` プロパティへの言及を追加。
`executed_move`/`indiv`/`effort`/`rank`/`terastallized`/`base_ability_name`（Pokemon）、
`power`/`critical_rank`（Move）、`name`/`n_won`/`n_game`（Player）、`opponent()`（Battle、対応済み）、
`Battle.__init__` のシグネチャ、`Command` Enum の構成は現行コードと照合済みで齟齬なし）

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

**型名について**: `Gender` → `PokemonGender` への型名改名は **行わない**（ユーザー判断）。
poke-env の `PokemonGender` とは型名が異なるが、値（`"male" / "female" / ""`）は互換のため実害はない。

---

### Phase 2: 改名（分類 A-1）
ユーザーコメント: 改名はユーザーが手動で行う

Phase 1（値の英語化）は完了済みのため、このフェーズから着手できる。エイリアスは残さず呼び出し元を一括変更する。

`types/literals.py` の型名 `Gender` は改名しない（ユーザーコメント: Genderは変更しない）。

**`model/pokemon.py`**

| 変更前 | 変更後 |
|---|---|
| `executed_move` | `last_move` |
| `hp_ratio` | `hp_fraction` |
| `terastallized` | `is_terastallized` |
| `base_ability_name` | `base_ability` |
| `indiv` | `ivs` |
| `effort` | `evs` |
| `rank` | `boosts` |

**`evs` 改名の注意**: jpoke の努力値は Champions 形式（各値 0〜32）で、poke-env の `evs`（各値 0〜252）とは
同名でもスケールが異なる。改名後は docstring にスケール差を明記する。
poke-env 形式からの取り込みは Phase 4 の `evs_from_poke_env`（変換関数）を経由する。

**`executed_move` 改名の注意**: テクスチャー2対応（コミット 90733267 等）で追加された
`last_move_type` / `last_move_name` プロパティ（`model/pokemon.py`）が `self.executed_move` を
直接参照している。改名時はこの2つのプロパティ本体も `self.last_move` に書き換える。
なお `last_move_type` / `last_move_name` 自体は poke-env 互換名ではなく jpoke 独自のテクスチャー2用
プロパティのため、改名対象にも A-2 の追加対象にも含めない。

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
def effects(self) -> dict:
    """volatiles のエイリアス（型変換なし）"""
    return self.volatiles

@property
def first_turn(self) -> bool:
    return not self.acted_since_switch_in
```

- `boosts` は Phase 2 で `rank` から改名するため、ここでのエイリアス追加は不要
- poke-env の `first_turn` は「交代で場に出てから最初の行動かどうか」。当初 `active_turn == 0`
  を想定していたが、`active_turn` フィールドは「Pokemonの一時状態をmemoryスコープに統一」リファクタ
  （2026-07-11）で廃止された。代わりに追加された `acted_since_switch_in`（`memory["switch"]["acted"]`
  のプロパティ、`model/pokemon.py`）が「場に出てから一度でも行動したか」を保持しているため、
  その否定形で代替する（2026-07-11 確認・修正）

**`model/move.py`**

```python
@property
def current_pp(self) -> int:
    return self.pp

@property
def max_pp(self) -> int:
    """data.pp のエイリアス（ユーザー判断）"""
    return self.data.pp

@property
def expected_hits(self) -> float:
    """期待ヒット数（poke-env の実装に合わせる）"""
    if self.min_hits == self.max_hits:
        return float(self.min_hits)
    # 2〜5回技のヒット数分布 2:3:4:5 = 35:35:15:15 の期待値 3.1（poke-env と同値）
    return (2 + 3) * 0.35 + (4 + 5) * 0.15
```

- `(min_hits + max_hits) / 2`（2〜5回技で 3.5）は poke-env の値（3.1）と一致しないため採用しない
- poke-env はトリプルキック・トリプルアクセル（1 ヒットごとに命中判定）を
  `1 + 2 * 0.9 + 3 * 0.81` と特別扱いしている。jpoke で再現する場合は技名で分岐する

**`core/player.py`**

```python
@property
def n_tied_battles(self) -> int:
    """jpoke に引き分けは存在しないため常に 0（poke-env 互換のために提供）"""
    return 0

@property
def n_lost_battles(self) -> int:
    return self.n_finished_battles - self.n_won_battles - self.n_tied_battles

@property
def win_rate(self) -> float:
    return self.n_won_battles / self.n_finished_battles if self.n_finished_battles > 0 else 0.0
```

- poke-env の名前は `n_tied_battles`（`n_draw_battles` という名前は存在しない）
- 旧案の `n_draw_battles = n_finished - n_won - n_lost` は定義上常に 0 になるバグだったため削除
- poke-env の `win_rate` はゼロ除算ガードなし。jpoke はガード付きとする（独自判断）

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

@property
def team(self) -> list[Pokemon]:
    """observer 側のチーム（poke-env は Dict[str, Pokemon] だが list のまま返す。ユーザー判断）"""
    if self.observer:
        return self.player_states[self.observer].team
    return []

@property
def available_moves(self) -> list[Move]:
    """observer の使用可能な技（get_available_commands の Command を Move に変換。ユーザー判断）"""
    ...

@property
def available_switches(self) -> list[Pokemon]:
    """observer の交代先候補（get_available_commands の交代コマンドから抽出。ユーザー判断）"""
    ...
```

- `available_moves` / `available_switches` の `Command` → `Move` / `Pokemon` 対応は
  `enums/command.py` の定義に従って実装時に確定する
- poke-env の `won` / `lost` は引数なしのプロパティで、未終了時は `None` を返す（`bool | None`）。
  jpoke は完全情報でプレイヤー視点が固定されないため `Player` を引数に取るメソッドとして提供する（意図的な差異）。
  未終了時に `False` を返す点も poke-env（`None`）と異なることを docstring に明記する
- poke-env の `tied` は jpoke に引き分けが存在しないため対象外

---

### Phase 4: 変換テーブルの追加（分類 B）

新規ファイル `src/jpoke/types/poke_env.py` を作成する。

**キーの正規化規則**: 各マップのキーは poke-env Enum の `name.lower()` に統一する
（例: `Weather.SUNNYDAY` → `"sunnyday"`、`Field.ELECTRIC_TERRAIN` → `"electric_terrain"`）。
Showdown のメッセージ ID（`"electricterrain"` 等）とは異なる場合があるので混同しない。

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

# poke-env の Status には FNT（瀕死）もあるが、jpoke は状態異常ではなく hp == 0 で表現するため対象外
STATUS_MAP: dict[str, str] = {
    "brn": "やけど", "frz": "こおり", "par": "まひ",
    "psn": "どく",   "slp": "ねむり", "tox": "もうどく",
}
STATUS_MAP_INV = {v: k for k, v in STATUS_MAP.items()}

# poke-env の Weather には HAIL（あられ）もあるが、Champions（第9世代準拠）は ゆき のみのため対象外
WEATHER_MAP: dict[str, str] = {
    "sunnyday":     "はれ",     "raindance":    "あめ",
    "sandstorm":    "すなあらし","snow":         "ゆき",
    "desolateland": "おおひでり","primordialsea":"おおあめ",
    "deltastream":  "らんきりゅう",
}
WEATHER_MAP_INV = {v: k for k, v in WEATHER_MAP.items()}

# poke-env の Field Enum のうち地形（terrain）4 種 → jpoke TerrainName
TERRAIN_MAP: dict[str, str] = {
    "electric_terrain": "エレキフィールド",
    "grassy_terrain":   "グラスフィールド",
    "psychic_terrain":  "サイコフィールド",
    "misty_terrain":    "ミストフィールド",
}
TERRAIN_MAP_INV = {v: k for k, v in TERRAIN_MAP.items()}

# poke-env の Field Enum のうち地形以外（jpoke では GlobalFieldName に分離）
GLOBAL_FIELD_MAP: dict[str, str] = {
    "gravity":    "じゅうりょく",   "trick_room":  "トリックルーム",
    "magic_room": "マジックルーム", "wonder_room": "ワンダールーム",
    "fairy_lock": "フェアリーロック",
}
GLOBAL_FIELD_MAP_INV = {v: k for k, v in GLOBAL_FIELD_MAP.items()}

# poke-env の SideCondition Enum → jpoke SideFieldName
# jpoke の SideFieldName のうち いやしのねがい・みかづきのまい・ねがいごと・みらいよち・はめつのねがい は
# poke-env では SideCondition ではなく slot condition 扱いのため対象外
SIDE_CONDITION_MAP: dict[str, str] = {
    "reflect":      "リフレクター",   "light_screen": "ひかりのかべ",
    "aurora_veil":  "オーロラベール", "safeguard":    "しんぴのまもり",
    "mist":         "しろいきり",     "tailwind":     "おいかぜ",
    "spikes":       "まきびし",       "toxic_spikes": "どくびし",
    "stealth_rock": "ステルスロック", "sticky_web":   "ねばねばネット",
}
SIDE_CONDITION_MAP_INV = {v: k for k, v in SIDE_CONDITION_MAP.items()}

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
    """poke-env の {"hp":..., "atk":...} をインデックス順（hp, atk, def, spa, spd, spe）のリストに変換"""
    return [d.get(k, 0) for k in ("hp", "atk", "def", "spa", "spd", "spe")]


def evs_from_poke_env(d: dict[str, int]) -> list[int]:
    """poke-env の evs（各値 0〜252）を Champions 形式の努力値（各値 0〜32）に変換する。

    Champions 形式は 0 または 8x - 4（x = 1〜32）に相当する値のみ表現できるため、
    中間値は切り捨てで近似する（非可逆）。
    """
    return [0 if v < 4 else (v + 4) // 8 for v in stats_from_poke_env(d)]
```

- `ivs`（0〜31）はスケールが同じため `stats_from_poke_env` をそのまま使える
- `evs` はスケールが異なる（poke-env: 0〜252、jpoke: Champions 形式 0〜32）ため
  必ず `evs_from_poke_env` を経由する

---

### Phase 5: インターフェース互換 — `Player.battle_against()`（分類 A-2 の入口 API）

poke-env ユーザーが最初に書くコード

```python
player.battle_against(opponent, n_battles=10)
print(player.win_rate)
```

を同じ書き味で動かせるようにする。既存の `Battle` / `TurnController` には手を入れず、
`Player` にメソッドを 1 つ追加するだけに留める（**実装を歪めない**）。

**`core/player.py`**

```python
def battle_against(self, *opponents: "Player", n_battles: int = 1) -> None:
    """各 opponent と n_battles 回ずつ対戦し、双方の戦績を更新する。

    poke-env と同じシグネチャ。ただしネットワーク I/O がないため同期メソッド
    （await / asyncio.run 不要。compat_analysis.md §0「同期モデル」参照）。
    """
    for opponent in opponents:
        for _ in range(n_battles):
            battle = Battle((self, opponent))
            battle.start()
            while battle.judge_winner() is None and battle.turn < MAX_TURNS:
                battle.step()
            winner = battle.judge_winner()
            for player in (self, opponent):
                player.n_finished_battles += 1
                if winner is player:
                    player.n_won_battles += 1
```

**実装メモ**

- 戦績の更新は `battle_against` 内で行い、`Battle` 側には自動更新の仕組みを追加しない。
  Phase 3 の `win_rate` / `n_lost_battles` / `n_tied_battles` はこのメソッドとセットで初めて意味を持つ
- フィールド名 `n_won_battles` / `n_finished_battles` は Phase 2 の改名（`n_won` / `n_game`）後の名前
- ターン上限で決着しないケースの扱い（上記 `MAX_TURNS` の値と、打ち切り時に `tod_score()` で
  勝者を決めるか未決着のまま戦績に数えないか）は実装時に確定する。
  既存の `scripts/fuzz_battle.py --player tree_search` は外部の `max_turns` ガードで打ち切っている
- `Battle` 生成時のパラメータ（`n_selected`, `seed` 等）を渡したい場合に備え、
  キーワード引数の素通し（`**battle_kwargs`）を検討する（jpoke 独自拡張。poke-env にはない）
- チームは poke-env のパックド文字列ではなく、事前に `player.team` へ `Pokemon` オブジェクトの
  リストを設定しておく前提（compat_analysis.md §0「チームの定義方法」参照）
- ドキュメントに「再現可能な対戦を組みたい場合は `TestOption` / `seed` を使う」導線を明記する
  （compat_analysis.md §0「決定論的テスト機能」参照）

**線引き（引き続き対象外とするもの）**

- `choose_move(battle) -> BattleOrder` / `teampreview(battle) -> str` / `create_order(...)` の互換は
  作らない。jpoke の Player は `choose_command(battle) -> Command` /
  `choose_selection(battle) -> list[int]` が正であり、`BattleOrder` 相当の変換層を挟むと
  行動選択の型安全性（`Command` Enum）を損なうため（分類 C）
- `accept_challenges` / `ladder` / `send_challenges` 等のサーバー接続系 API（分類 C）

---

## 依存関係とリスク

| フェーズ | 依存関係 | リスク |
|---|---|---|
| Phase 1 (Literal 値の英語化) | なし | **対応済み**。型名 `Gender` は改名しない（ユーザー判断） |
| Phase 2 (改名) | Phase 1 完了後 | 改名後の参照漏れ。grep で一括確認する |
| Phase 3 (property 追加) | Phase 2 完了後 | 既存コードへの影響なし |
| Phase 4 (変換テーブル) | 独立（いつでも可） | poke-env 依存なし |
| Phase 5 (`battle_against`) | Phase 2（`n_won_battles` 等の改名）・Phase 3（`win_rate` 等の property）完了後 | ターン上限で決着しない対戦の終了条件（`tod_score` 判定 or 戦績に数えない）が未確定 |

## 対象外

- jpoke → poke-env エクスポート（アダプタクラス・`BattleOrder`変換等）
- poke-env の Showdown サーバー接続機能（WebSocket 等）
- ダイナマックス・Z ワザ（jpoke 未実装）
