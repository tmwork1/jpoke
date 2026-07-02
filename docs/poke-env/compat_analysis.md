# poke-env 互換性調査書

調査日: 2026-07-01
清書日: 2026-07-02（ユーザーコメントを反映し、`src/jpoke/types/` の最新 Literal 定義と照合済み）

## 1. poke-env 主要 API まとめ

### AbstractBattle / Battle のプロパティ

| プロパティ名 | 型 | 説明 |
|---|---|---|
| `active_pokemon` | `Pokemon \| None` | 自分の場のポケモン |
| `opponent_active_pokemon` | `Pokemon \| None` | 相手の場のポケモン |
| `team` | `Dict[str, Pokemon]` | 自チーム（英語識別子キー） |
| `opponent_team` | `Dict[str, Pokemon]` | 相手チーム |
| `available_moves` | `List[Move]` | 使用可能な技リスト |
| `available_switches` | `List[Pokemon]` | 交代可能なポケモンリスト |
| `weather` | `Dict[Weather, int]` | 天候（WeatherEnum → ターン数） |
| `fields` | `Dict[Field, int]` | グローバルフィールド状態 |
| `side_conditions` | `Dict[SideCondition, int]` | 自陣コンディション |
| `opponent_side_conditions` | `Dict[SideCondition, int]` | 相手陣コンディション |
| `turn` | `int` | 現在ターン数 |
| `finished` | `bool` | バトル終了フラグ |
| `won / lost` | `bool` | 勝敗フラグ |
| `can_tera / can_mega_evolve / can_dynamax` | `bool` | 変身可能フラグ |
| `trapped / force_switch` | `bool` | トラップ・強制交代フラグ |

### Pokemon のプロパティ

| プロパティ名 | 型 | 説明 |
|---|---|---|
| `name` | `str` | ポケモン名（英語） |
| `ability` | `str \| None` | 特性名（文字列） |
| `item` | `str \| None` | アイテム名（文字列） |
| `current_hp` | `int \| None` | 現在 HP |
| `max_hp` | `int \| None` | 最大 HP |
| `current_hp_fraction` | `float` | HP 割合 |
| `moves` | `Dict[str, Move]` | 技辞書（英語 ID キー） |
| `last_move` | `Move \| None` | 最後に使用した技 |
| `status` | `Status \| None` | 状態異常（Status Enum） |
| `status_counter` | `int` | 状態異常カウンター |
| `boosts` | `Dict[str, int]` | 能力ランク（英語キー: atk/def/spa/spd/spe/accuracy/evasion） |
| `effects` | `Dict[Effect, int]` | 揮発性状態 |
| `stats` | `Dict[str, int] \| None` | 実数値（英語キー） |
| `base_stats` | `Dict[str, int]` | 種族値（英語キー） |
| `ivs / evs` | `Dict[str, int]` | 個体値・努力値（英語キー） |
| `types` | `List[PokemonType]` | 現在のタイプ（PokemonType Enum） |
| `base_types` | `List[PokemonType]` | 基本タイプ |
| `tera_type` | `PokemonType \| None` | テラスタルタイプ（Enum） |
| `is_terastallized` | `bool` | テラスタル中か |
| `fainted` | `bool` | 瀕死か |
| `first_turn` | `bool` | 出た初ターンか |
| `must_recharge` | `bool` | リチャージ中か |
| `protect_counter` | `int` | まもるカウンター |
| `gender` | `PokemonGender \| None` | 性別（Enum） |
| `level` | `int` | レベル |
| `nature` | `str \| None` | 性格（英語） |
| `weight` | `float` | 体重 |
| `stab_multiplier` | `float` | STAB 倍率 |

### Move のプロパティ

| プロパティ名 | 型 | 説明 |
|---|---|---|
| `id` | `str` | 技 ID（英語小文字） |
| `type` | `PokemonType` | タイプ（Enum） |
| `category` | `MoveCategory` | カテゴリ（Enum） |
| `base_power` | `int` | 威力 |
| `accuracy` | `int \| bool` | 命中率（True = 必中） |
| `priority` | `int` | 優先度 |
| `current_pp` | `int` | 現在 PP |
| `max_pp` | `int` | 最大 PP |
| `crit_ratio` | `int` | 急所ランク補正 |
| `n_hit` | `tuple[int, int]` | （最小, 最大）ヒット数 |
| `expected_hits` | `float` | 期待ヒット数 |
| `target` | `str` | ターゲット文字列 |
| `flags` | `Dict[str, int]` | フラグ辞書（contact, sound 等） |
| `recoil / drain / heal` | `float` | 反動・吸収・回復割合 |
| `status` | `Status \| None` | 付与する状態異常 |
| `boosts / self_boost` | `Dict[str, int] \| None` | 付与するランク変化 |
| `secondary` | `List[Dict] \| None` | 追加効果リスト |
| `force_switch` | `bool` | 強制交代技か |
| `is_protect_move` | `bool` | まもる系か |
| `breaks_protect` | `bool` | まもる貫通か |
| `ignore_ability` | `bool` | 特性無視か |

### Player インターフェース

| メソッド / プロパティ | 説明 |
|---|---|
| `choose_move(battle) -> BattleOrder` | **唯一の抽象メソッド**。行動選択 |
| `teampreview(battle) -> str` | チームプレビューでの選出文字列 |
| `create_order(order, mega, z_move, dynamax, tera_type) -> BattleOrder` | BattleOrder 生成ヘルパー |
| `username: str` | ユーザー名 |
| `n_won_battles / n_lost_battles / n_finished_battles` | 戦績 |
| `win_rate: float` | 勝率 |
| `battles: Dict[str, AbstractBattle]` | バトル一覧 |

### 主要 Enum

| Enum 名 | 代表値 |
|---|---|
| `PokemonType` | NORMAL, FIRE, WATER, ELECTRIC, GRASS, ICE, FIGHTING, POISON, GROUND, FLYING, PSYCHIC, BUG, ROCK, GHOST, DRAGON, DARK, STEEL, FAIRY, STELLAR |
| `Status` | BRN, FRZ, PAR, PSN, SLP, TOX |
| `MoveCategory` | PHYSICAL, SPECIAL, STATUS |
| `PokemonGender` | FEMALE, MALE, NEUTRAL |
| `Weather` | SUNNYDAY, RAINDANCE, SANDSTORM, SNOW, DESOLATELAND, PRIMORDIALSEA, DELTASTREAM |
| `Field` | ELECTRIC_TERRAIN, GRASSY_TERRAIN, PSYCHIC_TERRAIN, MISTY_TERRAIN |

---

## 2. jpoke との差異一覧

### 2-1. Pokemon プロパティ対応

| poke-env | jpoke（現在） | 差異の種類 | 対応方針 |
|---|---|---|---|
| `current_hp` | `hp` | 変数名違い | A-2: `current_hp` エイリアス追加 |
| `current_hp_fraction` | `hp_ratio` | 変数名違い | A-1: `hp_ratio` → `hp_fraction` に改名 |
| `weight` | `weight` | 意味が異なる（poke-env: 図鑑値、jpoke: 特性・アイテム反映済み） | C: API 変更なし |
| `name` | `name` | 英語 vs 日本語 | B-2: ポケモン名マッピング |
| `nature` | `nature` | 英語 vs 日本語 | B-2: 性格名マッピング |
| `ability: str \| None` | `ability: Ability`（`.name` で文字列） | 型違い | B-2: 特性名マッピング |
| `base_ability: str \| None` | `base_ability_name: str` | 変数名・型違い | A-1: `base_ability_name` → `base_ability` に改名 |
| `item: str \| None` | `item: Item`（`.name` で文字列） | 型違い | B-2: アイテム名マッピング |
| `status: Status \| None` | `ailment: Ailment`（`.name` で文字列） | 変数名・型・言語違い | A-2: `status` エイリアス追加（型変換なし） |
| `status_counter: int` | `ailment.turn_count` | アクセスパス違い | B-4 |
| `boosts: Dict[str, int]` | `rank: dict[Stat, int]`（`Stat` キーは英語化済み） | 変数名違い | A-1: `rank` → `boosts` に改名（ユーザー判断: エイリアスではなく改名で対応） |
| `effects: Dict[Effect, int]` | `volatiles: dict[VolatileName, Volatile]` | 変数名・型違い | A-2: `effects` エイリアス追加（型変換なし） |
| `moves: Dict[str, Move]` | `moves: list[Move]` | コンテナ型違い | B-4 |
| `last_move: Move \| None` | `executed_move: Move \| None` | 変数名違い | A-1: `executed_move` → `last_move` に改名 |
| `stats: Dict[str, int]` | `stats: dict[Stat, int]` | 解消済み（`Stat` Literal は英語キーに変更済み） | — |
| `base_stats: Dict[str, int]` | `base: list[int]` | 変数名・コンテナ型違い | B-3 |
| `ivs: Dict[str, int]` | `indiv: list[int]` | 変数名・コンテナ型違い | A-1: `indiv` → `ivs` に改名 |
| `evs: Dict[str, int]` | `effort: list[int]` | 変数名・コンテナ型違い | A-1: `effort` → `evs` に改名 |
| `types: List[PokemonType]` | `types: list[PokemonType]`（型名は一致・値は日本語 Literal） | Enum vs 日本語 Literal | B-1 |
| `base_types: List[PokemonType]` | `base_types: list[PokemonType]` | 型違い（Enum vs Literal） | B-1 |
| `is_terastallized: bool` | `terastallized: bool` | 変数名違い | A-1: `terastallized` → `is_terastallized` に改名 |
| `tera_type: PokemonType \| None` | `tera_type: PokemonType` | Enum vs 日本語 Literal | B-1 |
| `first_turn: bool` | （`active_turn == 0` で代替） | 直接プロパティなし | A-2: property 追加 |
| `must_recharge: bool` | （`has_volatile("リチャージ")` で代替） | 直接プロパティなし | B-4 |
| `protect_counter: int` | （volatile 内部に保持） | アクセスパス違い | B-4 |
| `gender: PokemonGender` | `gender: PokemonGender`（値: `"male" / "female" / ""`） | 解消済み（型名・値ともに一致。Enum vs Literal の違いのみ残る） | — |
| `stab_multiplier: float` | （なし） | jpoke 非対応 | C: 対象外 |

### 2-2. Move プロパティ対応

| poke-env | jpoke（現在） | 差異の種類 | 対応方針 |
|---|---|---|---|
| `id: str` | `name: str` | 変数名・言語違い | B-2: 技名マッピング |
| `base_power: int` | `power: int \| None` | 変数名違い | A-1: `power` → `base_power` に改名 |
| `accuracy: int \| bool` | `accuracy: int \| None` | 必中表現違い（True vs None） | B-4 |
| `current_pp: int` | `pp: int` | 変数名違い | A-2: `current_pp` エイリアス追加 |
| `max_pp: int` | `data.pp: int` | アクセスパス違い | A-2: `max_pp` property を追加（`data.pp` のエイリアス。ユーザー判断） |
| `crit_ratio: int` | `critical_rank: int` | 変数名違い | A-1: `critical_rank` → `crit_ratio` に改名 |
| `category: MoveCategory` | `category: MoveCategory（日本語 Literal）` | Enum vs 日本語 Literal | A-1: `MoveCategory` Literal を英語値に変更 |
| `type: PokemonType` | `type: PokemonType`（日本語 Literal） | Enum vs 日本語 Literal | B-1 |
| `expected_hits: float` | （`(min_hits + max_hits) / 2`） | 直接プロパティなし | A-2: property 追加 |
| `n_hit: tuple[int, int]` | `min_hits, max_hits`（分割） | 単一 vs 分割 | C: 対象外 |
| `flags: Dict[str, int]` | `data.flags: list[MoveFlag]`（`labels`/`MoveLabel` から改名済み） | 名称は一致・表現形式のみ違い（Dict vs list） | B-4: contact, sound 等の判定を bool 変換 |
| `recoil: float` | `has_label("recoil")`（bool） | float vs bool | C: 精度制限のため対象外 |
| `is_protect_move: bool` | `has_label(...)` | ラベルで代替 | B-4 |

### 2-3. Battle プロパティ対応

| poke-env（AbstractBattle） | jpoke（Battle） | 差異の種類 | 対応方針 |
|---|---|---|---|
| `active_pokemon` | `get_active(player)` / `actives[0]` | 自分視点固定 vs プレイヤー指定 | A-2: property 追加 |
| `opponent_active_pokemon` | `get_active(opponent(observer))` | 同上 | A-2: property 追加（`rival` → `opponent` 改名は対応済み） |
| `finished: bool` | `winner is not None` | 直接フラグなし | A-2: property 追加 |
| `won / lost` | `winner == self_player` | 直接フラグなし | A-2: property 追加 |
| `side_conditions` | `side_managers[i].fields` | アクセスパス違い | A-2: `side_conditions` エイリアス追加 |
| `team: Dict[str, Pokemon]` | `player_states[p].team: list[Pokemon]` | Dict vs list | A-2: `team` property を追加（型は `list[Pokemon]` のまま、`Dict` への変換はしない。ユーザー判断） |
| `available_moves: List[Move]` | `get_available_commands(player): list[Command]` | Move vs Command Enum | A-2 + B-4: `available_moves` property を追加し `Command` → `Move` に変換して `list[Move]` を返す（ユーザー判断） |
| `available_switches: List[Pokemon]` | コマンドから抽出 | 直接プロパティなし | A-2 + B-4: `available_switches` property を追加し `list[Pokemon]` を返す（ユーザー判断） |
| `weather: Dict[Weather, int]` | `weather: Field` | Dict vs Field オブジェクト | C: export 対象外 |
| `fields: Dict[Field, int]` | `terrain: Field` | Dict vs Field オブジェクト | C: export 対象外 |

### 2-4. Player メソッド・プロパティ対応

| poke-env | jpoke（現在） | 差異の種類 | 対応方針 |
|---|---|---|---|
| `username: str` | `name: str` | 変数名違い | A-1: `name` → `username` に改名 |
| `n_won_battles` | `n_won` | 変数名違い | A-1: `n_won` → `n_won_battles` に改名 |
| `n_finished_battles` | `n_game` | 変数名違い | A-1: `n_game` → `n_finished_battles` に改名 |
| `n_lost_battles` | （なし） | 直接プロパティなし | A-2: property 追加。あわせて `n_draw_battles` も追加 |
| `win_rate: float` | （なし） | 直接プロパティなし | A-2: property 追加 |
| `choose_move(battle) -> BattleOrder` | `choose_command(battle) -> Command` | 返り値型が異なる | C: export 対象外 |
| `teampreview(battle) -> str` | `choose_selection(battle) -> list[int]` | 選出表現が異なる | C: export 対象外 |

### 2-5. Enum 値の対応

| 概念 | poke-env | jpoke（現在） | 対応方針 |
|---|---|---|---|
| タイプ（ほのお） | `PokemonType.FIRE` | `"ほのお"` | B-1: 変換テーブル |
| 状態異常（まひ） | `Status.PAR` | `"まひ"` | B-1: 変換テーブル |
| 技カテゴリ（物理） | `MoveCategory.PHYSICAL` | `"物理"` | A-1: `"physical"` に変更 |
| 性別（オス） | `PokemonGender.MALE` | `"オス"` | A-1: `"male"` に変更 |
| 天候（はれ） | `Weather.SUNNYDAY` | `"はれ"` | B-1: 変換テーブル |
| 天候（おおひでり） | `Weather.DESOLATELAND` | `"おおひでり"` | B-1: 変換テーブル |
| フィールド（グラス） | `Field.GRASSY_TERRAIN` | `"グラスフィールド"` | B-1: 変換テーブル |
| フィールド（エレキ） | `Field.ELECTRIC_TERRAIN` | `"エレキフィールド"` | B-1: 変換テーブル |
| 能力値（攻撃） | `"atk"` | `"A"` | A-1: `Stat` Literal を `"atk"` 等に変更 |

---

## 3. 互換方針の分類

**互換の方向: poke-env → jpoke のみ**

poke-env のデータ（チーム構成・技仕様等）を jpoke へ取り込む方向のみを対象とする。
jpoke オブジェクトを poke-env 形式でエクスポートする機能（アダプタクラス等）は対象外。

---

### 分類 A-1: jpoke 側の改名

既存の jpoke 名を poke-env に合わせて変更する。エイリアスは残さず、呼び出し元も一括変更する。

**プロパティ・変数の改名**

| 変更前（jpoke 現在） | 変更後 | 対象 | 状態（2026-07-02 時点） |
|---|---|---|---|
| `executed_move` | `last_move` | `Pokemon` | 未対応 |
| `hp_ratio` | `hp_fraction` | `Pokemon` | 未対応 |
| `terastallized` | `is_terastallized` | `Pokemon` | 未対応 |
| `base_ability_name` | `base_ability` | `Pokemon` | 未対応 |
| `indiv` | `ivs` | `Pokemon` | 未対応 |
| `effort` | `evs` | `Pokemon` | 未対応 |
| `rank` | `boosts` | `Pokemon` | 未対応（ユーザー判断: エイリアスではなく改名で対応） |
| `power` | `base_power` | `Move` | 未対応 |
| `critical_rank` | `crit_ratio` | `Move` | 未対応 |
| `name` | `username` | `Player` | 未対応 |
| `n_won` | `n_won_battles` | `Player` | 未対応 |
| `n_game` | `n_finished_battles` | `Player` | 未対応 |
| `rival()` | `opponent()` | `Battle` | **対応済み** |

**Literal 型の英語化**（`src/jpoke/types/literals.py`） — **対応済み**（2026-07-02 時点で確認。当初の想定より先行して実施されていた）

| 型 | 変更前 | 変更後（現状） |
|---|---|---|
| `Stat` | `"H", "A", "B", "C", "D", "S"` | `"hp", "atk", "def", "spa", "spd", "spe", "accuracy", "evasion"` |
| `MoveCategory` | `"物理", "特殊", "変化"` | `"physical", "special", "status"` |
| `Gender` → `PokemonGender` | `"オス", "メス", ""` | `"male", "female", ""`（型名も poke-env に合わせ `PokemonGender` に改名済み） |

`Stat` の変更は `rank`（→ `boosts` に改名予定）、`stats`、`base`、`ivs`、`evs` 等を参照するすべての箇所に反映済み。

---

### 分類 A-2: property / エイリアスの追加

jpoke の既存名は維持しつつ、poke-env 互換名を property として追加する。

| poke-env 名 | 実装方法 | 対象クラス |
|---|---|---|
| `current_hp` | `hp` のエイリアス | `Pokemon` |
| `current_hp_fraction` | `hp_fraction` のエイリアス | `Pokemon` |
| `status` | `ailment.name` を返す property（型変換なし） | `Pokemon` |
| `effects` | `volatiles` のエイリアス（型変換なし） | `Pokemon` |
| `first_turn` | `active_turn == 0` property | `Pokemon` |
| `current_pp` | `pp` のエイリアス | `Move` |
| `max_pp` | `data.pp` のエイリアス（ユーザー判断） | `Move` |
| `expected_hits` | `(min_hits + max_hits) / 2` property | `Move` |
| `finished` | `winner is not None` property | `Battle` |
| `won` / `lost` | `winner` から計算する property | `Battle` |
| `active_pokemon` | `get_active(observer)` property | `Battle` |
| `opponent_active_pokemon` | `get_active(opponent(observer))` property | `Battle` |
| `side_conditions` | `side_managers[i].fields` のエイリアス | `Battle` |
| `team` | `player_states[observer].team` のエイリアス（型は `list[Pokemon]` のまま。ユーザー判断） | `Battle` |
| `available_moves` | `get_available_commands(observer)` の `Command` を `Move` に変換して `list[Move]` を返す（ユーザー判断） | `Battle` |
| `available_switches` | 同上のコマンドから交代先を抽出し `list[Pokemon]` を返す（ユーザー判断） | `Battle` |
| `n_lost_battles` | `n_finished_battles - n_won_battles` property | `Player` |
| `n_draw_battles` | `n_finished_battles - n_won_battles - n_lost_battles` property | `Player` |
| `win_rate` | `n_won_battles / n_finished_battles` property | `Player` |

`boosts` は当初エイリアス追加を想定していたが、A-1 の `rank` → `boosts` 改名に方針変更したため本表から削除（上記「分類 A-1」参照）。

---

### 分類 B: 変換ユーティリティ（poke-env → jpoke 方向のみ）

アダプタクラスは作成せず、変換関数として `src/jpoke/types/` に用意する。
変換テーブルが肥大化するため専用モジュール（`src/jpoke/types/poke_env.py`、未作成）を設ける。

#### B-1: Enum → 日本語 Literal 変換テーブル

| 対象プロパティ | poke-env 型 | jpoke 型 |
|---|---|---|
| `types` / `base_types` / `tera_type` | `PokemonType` Enum | 日本語 Literal（`PokemonType`） |
| `status` → `ailment.name` | `Status` Enum | 日本語 Literal（`AilmentName`） |
| `effects` → `volatiles` のキー | `Effect` Enum | 日本語 Literal（`VolatileName`） |
| Move `type` | `PokemonType` Enum | 日本語 Literal（`PokemonType`） |
| `weather` | `Weather` Enum | 日本語 Literal（`WeatherName`） |
| `fields` | `Field` Enum | 日本語 Literal（`TerrainName`。じゅうりょく等の疑似天候は `GlobalFieldName`、リフレクター等の場は `SideFieldName` に分離済み） |

`MoveCategory`・`Gender`（`PokemonGender`）・`Stat` の変換は A-1 の Literal 英語化によって既に不要（対応済み）。
`PokemonType` は jpoke 側の型名も `PokemonType` で一致している（値のみ日本語 Literal）。

#### B-2: 名前マッピング（英語 ↔ 日本語）

| 対象プロパティ | 変換内容 |
|---|---|
| Pokemon `name` | 英語名 ↔ 日本語名 |
| Move `id` / `name` | 英語 ID ↔ 日本語名 |
| `nature` | 英語性格名 ↔ 日本語性格名 |
| `ability` / `base_ability` | 英語特性名 → `data/ability.py` の日本語エントリ検索 |
| `item` | 英語アイテム名 → `data/item.py` の日本語エントリ検索 |

#### B-3: 数値形式変換
`Stat` キー英語化（A-1）後も、poke-env は辞書形式・jpoke はリスト形式の差異が残る。

| 対象 | poke-env 形式 | jpoke 形式 | 変換 |
|---|---|---|---|
| `base_stats` | `Dict[str, int]`（英語キー） | `list[int]`（インデックス順） | キー → インデックス変換 |
| `ivs`・`evs` のインポート | `Dict[str, int]`（英語キー） | `list[int]` | 同上 |

```
インデックス対応: hp=0, atk=1, def=2, spa=3, spd=4, spe=5
```

#### B-4: その他変換

| 対象プロパティ | 差異 | 変換方法 |
|---|---|---|
| Move `accuracy` | True = 必中（poke-env）vs None = 必中（jpoke） | `True → None` |
| `status_counter` | `ailment.turn_count`（アクセスパス違い） | インポート時に `Ailment.turn_count` に設定 |
| `must_recharge` | `has_volatile("リチャージ")` で代替 | 揮発性状態名で判定 |
| `protect_counter` | volatile 内部に保持 | `Volatile.counter` から取得 |
| Move `flags` | `Dict[str, int]` vs `list[MoveFlag]`（名称は改名済み、形式のみ相違） | contact, sound 等を bool に変換 |
| Pokemon `moves` | `Dict[str, Move]`（英語 ID キー）vs `list[Move]` | B-2 の名前マッピング経由でリストに変換 |
| `effects` / `volatiles` | `Dict[Effect, int]` vs `dict[VolatileName, Volatile]` | B-1 の Enum → Literal 変換後に lookup |
| Move `is_protect_move` | `has_flag(...)` で代替（`has_label` から改名済み） | フラグ名で判定 |

Move `max_pp` は A-2 のエイリアス追加で対応する方針に変更（上記「分類 A-2」参照）。

---

### 分類 C: 対象外

**jpoke → poke-env エクスポート（方針として対象外）**

| 差異一覧の項目 | 対象外の理由 |
|---|---|
| Battle `weather: Dict[Weather, int]` | `Field` → `Dict` 変換（export） |
| Battle `fields: Dict[Field, int]` | `Field` → `Dict` 変換（export） |
| Player `choose_move(battle) -> BattleOrder` | `Command` ↔ `BattleOrder` 変換が必要（export） |
| Player `teampreview(battle) -> str` | `choose_selection` → 文字列変換（export） |

Battle `available_moves` / `available_switches` / `team` は当初 export 扱いで対象外としていたが、
ユーザー判断により A-2（+ B-4）でエイリアス・変換 property を追加する方針に変更した（上記「分類 A-2」参照）。

**jpoke 非対応**

| 項目 | 理由 |
|---|---|
| `stab_multiplier` | 計算可能だが利用頻度が低い |
| Move `n_hit: tuple[int, int]` | jpoke は `min_hits` / `max_hits` を個別に保持 |
| Move `recoil: float` | jpoke は割合を保持しないため精度制限あり |

**jpoke に存在しない poke-env 機能**

- Pokémon Showdown サーバーへの接続全般（`parse_message`, `accept_challenges`, `ladder` 等）
- バトルフォーマット（`format`）・世代（`gen`）・バトルタグ（`battle_tag`）
- ダイナマックス・Z ワザ — jpoke 未実装
- リプレイ保存（`save_replay`）
- `available_moves_from_request(request)` — PS リクエスト JSON 解析

**既知の意味的差異（API 変更なし）**

- Pokemon `weight`: poke-env は図鑑値、jpoke は特性・アイテム反映済み。インポート時に注意が必要だが変換は行わない。

---

### 分類 D: jpoke 独自機能（変更不要）

| 機能 | 説明 |
|---|---|
| `build_observation(observer) -> Battle` | 情報隠蔽バトルコピー（相手非公開情報を隠蔽） |
| `calc_lethal(attacker, moves, ...) -> list[LethalResult]` | 確定数計算 |
| `roll_damage() / calc_damages()` | ダメージ分布の全候補計算 |
| `EventManager + Event Enum` | イベント駆動の特性・アイテム・技発動管理 |
| `MoveFlag システム`（旧 `MoveLabel`） | contact, sound, punch 等のフラグによるメタ分類 |
| `paradox_boost_active / paradox_boost_stat` | こだいかっせい・クォークチャージ補正状態 |
| `stellar_boosted_types` | ステラテラスタルのタイプ別ブースト追跡 |
| `added_types / removed_types` | タイプ動的変更の追跡 |
| `active_turn: int` | 出場ターン数カウント |
| `hits_taken / last_physical_damage_received` | ターン内被弾記録 |
| `Command Enum` | 型安全な行動選択 |
| `TestOption` | 命中率・状態異常確率固定のテスト用オプション |
| `tod_score(alpha)` | Time Over Death スコア計算 |
| `choose_selection(battle) -> list[int]` | 整数インデックスで返す選出 API |

---

## 4. 実装方針まとめ

### 実装ファイル構成

```
src/jpoke/
  model/
    pokemon.py         ← A-1 改名（rank → boosts 含む）/ A-2 property 追加
    move.py            ← A-1 改名 / A-2 property 追加
  core/
    player.py          ← A-1 改名 / A-2 property 追加
    battle.py          ← A-1 改名（rival → opponent、対応済み）/ A-2 property 追加
  types/
    literals.py        ← 対応済み: Stat / MoveCategory / PokemonGender の Literal 英語化
    ailment.py, volatile.py, weather.py, terrain.py,
    global_field.py, side_field.py                 ← B-1 が参照する既存の日本語 Literal 群（変更不要）
    poke_env.py        ← 新規: B-1 Enum→Literal 変換テーブル / B-2 名前マッピング / B-3・B-4 変換関数
```

### 依存関係

- poke-env パッケージへの依存なし（変換テーブルは純粋な辞書・関数）
- `Stat` / `MoveCategory` / `PokemonGender` の Literal 英語化（A-1）は既に完了しているため、
  他の A-1 改名（`rank` → `boosts` 等）は英語化済みの `Stat` を前提に進めてよい

### 実装方針

- A-1 の改名はエイリアスを残さず、呼び出し元を一括変更する
- A-2 のエイリアス・property は既存クラスに直接追加する（アダプタクラスは作成しない）
- 変換テーブルは `src/jpoke/types/poke_env.py`（新規作成）に集約し、他所でハードコーディングしない
- poke-env → jpoke のインポートは変換関数として提供し、呼び出し側が明示的に変換する

詳細な実装計画は `docs/plan/poke_env_compat.md` を参照。
