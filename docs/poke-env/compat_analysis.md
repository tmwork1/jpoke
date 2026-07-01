# poke-env 互換性調査書

調査日: 2026-07-01

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

| poke-env | jpoke | 差異の種類 | ユーザーコメント |
|---|---|---|---|
| `current_hp` | `hp` | 変数名違い ||
| `current_hp_fraction` | `hp_ratio` | 変数名違い ||
| `weight` | `weight` | 同名だが意味が異なる（poke-env: 図鑑値、jpoke: 特性・アイテム反映済み） ||
| `nature` | `nature` | 同名（英語 vs 日本語） ||
| `ability: str \| None` | `ability: Ability`（`.name` で文字列） | 型違い ||
| `base_ability: str \| None` | `base_ability_name: str` | 変数名・型違い ||
| `item: str \| None` | `item: Item`（`.name` で文字列） | 型違い ||
| `status: Status \| None` | `ailment: Ailment`（`.name` で文字列） | 変数名・型・言語違い ||
| `status_counter: int` | `ailment.turn_count` | アクセスパス違い ||
| `boosts: Dict[str, int]` | `rank: dict[Stat, int]` | 変数名・キー言語違い ||
| `effects: Dict[Effect, int]` | `volatiles: dict[VolatileName, Volatile]` | 変数名・型違い ||
| `moves: Dict[str, Move]` | `moves: list[Move]` | コンテナ型違い ||
| `last_move: Move \| None` | `executed_move: Move \| None` | 変数名違い ||
| `stats: Dict[str, int]` | `stats: dict[Stat, int]` | キー言語違い（"atk" vs "A"） ||
| `base_stats: Dict[str, int]` | `base: list[int]` | 変数名・コンテナ型違い ||
| `ivs: Dict[str, int]` | `indiv: list[int]` | 変数名・コンテナ型違い ||
| `evs: Dict[str, int]` | `effort: list[int]` | 変数名・コンテナ型違い ||
| `types: List[PokemonType]` | `types: list[Type]` | Enum vs 日本語 Literal ||
| `base_types: List[PokemonType]` | `base_types: list[Type]` | 同名・型違い ||
| `is_terastallized: bool` | `terastallized: bool` | 変数名違い ||
| `tera_type: PokemonType \| None` | `tera_type: Type` | Enum vs 日本語 Literal ||
| `first_turn: bool` | （`active_turn == 0` で代替） | 直接プロパティなし ||
| `must_recharge: bool` | （`has_volatile("リチャージ")` で代替） | 直接プロパティなし ||
| `protect_counter: int` | （volatile 内部に保持） | アクセスパス違い ||
| `gender: PokemonGender` | `gender: Gender` | Enum vs 日本語 Literal ||
| `name: str` | `name: str` | 同名（英語 vs 日本語） ||

### 2-2. Move プロパティ対応

| poke-env | jpoke | 差異の種類 | ユーザーコメント |
|---|---|---|---|
| `id: str` | `name: str` | 変数名・言語違い（英語 ID vs 日本語名） ||
| `base_power: int` | `power: int \| None` | 変数名違い ||
| `accuracy: int \| bool` | `accuracy: int \| None` | 必中表現違い（True vs None） ||
| `current_pp: int` | `pp: int` | 変数名違い ||
| `max_pp: int` | `data.pp: int` | アクセスパス違い ||
| `crit_ratio: int` | `critical_rank: int` | 変数名違い ||
| `category: MoveCategory` | `category: MoveCategory（日本語 Literal）` | Enum vs 日本語 Literal ||
| `type: PokemonType` | `type: Type（日本語 Literal）` | Enum vs 日本語 Literal ||
| `n_hit: tuple[int, int]` | `min_hits, max_hits` | 単一プロパティ vs 分割 ||
| `flags: Dict[str, int]` | `data.labels: list[MoveLabel]` | 表現形式違い ||
| `recoil: float` | `has_label("recoil")` | float値 vs bool判定 ||
| `is_protect_move: bool` | `has_label(...)` | ラベルで代替 ||

### 2-3. Battle プロパティ対応

| poke-env（AbstractBattle） | jpoke（Battle） | 差異の種類 | ユーザーコメント |
|---|---|---|---|
| `active_pokemon` | `get_active(player)` / `actives[0]` | 自分視点固定 vs プレイヤー指定 ||
| `opponent_active_pokemon` | `foe(mon)` / `actives[1]` | 同上 ||
| `team: Dict[str, Pokemon]` | `player_states[p].team: list[Pokemon]` | Dict vs list ||
| `available_moves: List[Move]` | `get_available_commands(player): list[Command]` | Move リスト vs Command Enum ||
| `available_switches: List[Pokemon]` | コマンドから抽出 | 直接プロパティなし ||
| `weather: Dict[Weather, int]` | `weather: Field` | Dict vs Field オブジェクト ||
| `fields: Dict[Field, int]` | `terrain: Field` | Dict vs Field オブジェクト ||
| `side_conditions` | `side_managers[i].fields` | アクセスパス違い ||
| `finished: bool` | `winner is not None` | 直接フラグなし ||
| `won / lost` | `winner == self_player` | 計算で対応 ||

### 2-4. Player メソッド対応

| poke-env | jpoke | 差異の種類 | ユーザーコメント |
|---|---|---|---|
| `choose_move(battle) -> BattleOrder` | `choose_command(battle) -> Command` | 返り値型が異なる ||
| `teampreview(battle) -> str` | `choose_selection(battle) -> list[int]` | 選出表現が異なる ||
| `username: str` | `name: str` | 変数名違い ||
| `n_won_battles` | `n_won` | 変数名違い ||
| `n_finished_battles` | `n_game` | 変数名違い ||

### 2-5. Enum 値の対応

| 概念 | poke-env | jpoke |  | ユーザーコメント |
|---|---|---|---|
| タイプ（ほのお） | `PokemonType.FIRE` | `"ほのお"` ||
| 状態異常（まひ） | `Status.PAR` | `"まひ"` ||
| 技カテゴリ（物理） | `MoveCategory.PHYSICAL` | `"物理"` ||
| 性別（オス） | `PokemonGender.MALE` | `"オス"` ||
| 天候（はれ） | `Weather.SUNNYDAY` | `"はれ"` ||
| 天候（おおひでり） | `Weather.DESOLATELAND` | `"おおひでり"` ||
| フィールド（グラス） | `Field.GRASSY_TERRAIN` | `"グラスフィールド"` ||
| フィールド（エレキ） | `Field.ELECTRIC_TERRAIN` | `"エレキフィールド"` ||

---

## 3. 互換方針の分類

**互換の方向: poke-env → jpoke のみ**

poke-env のデータ（チーム構成・技仕様等）を jpoke へ取り込む方向のみを対象とする。
jpoke オブジェクトを poke-env 形式でエクスポートする機能（アダプタクラス等）は対象外。

### 分類 A: エイリアス property の追加で済むもの

既存コードへの影響ゼロ。jpoke 側に後方互換 property を追加するだけ。
poke-env に慣れたユーザーが jpoke を違和感なく扱えるようにする命名エイリアス。

| 追加先クラス | poke-env 名 | jpoke 名 |　ユーザーコメント |
|---|---|---|
| `Pokemon` | `current_hp` | `hp` ||
| `Pokemon` | `current_hp_fraction` | `hp_ratio` | エイリアス対応するほか、hp_ratio -> hp_fractionに改名する |
| `Pokemon` | `last_move` | `executed_move` | poke-envに合わせて改名する |
| `Pokemon` | `is_terastallized` | `terastallized` | poke-envに合わせて改名する |
| `Pokemon` | `first_turn` | `active_turn == 0` ||
| `Pokemon` | `stab_multiplier` | 計算で実装 | 非対応 |
| `Move` | `base_power` | `power` | poke-envに合わせて改名する |
| `Move` | `current_pp` | `pp` ||
| `Move` | `crit_ratio` | `critical_rank` | poke-envに合わせて改名する |
| `Move` | `expected_hits` | `(min_hits + max_hits) / 2` ||
| `Move` | `n_hit` | `(min_hits, max_hits)` | 非対応 |
| `Player` | `username` | `name` | poke-envに合わせて改名する |
| `Player` | `n_won_battles` | `n_won` | poke-envに合わせて改名する |
| `Player` | `n_finished_battles` | `n_game` | poke-envに合わせて改名する |
| `Player` | `n_lost_battles` | `n_game - n_won` | poke-envに合わせて変数化し、n_draw_battles = n_finished - n_won - n_lost とする |
| `Player` | `win_rate` | `n_won / n_game` ||
| `Battle` | `finished` | `winner is not None` ||
| `Battle` | `won` | `winner == player` ||
| `Battle` | `lost` | `winner is not None and winner != player` ||
| `Battle` | `active_pokemon` | `get_active(observer)` ||
| `Battle` | `opponent_active_pokemon` | `get_active(rival(observer))` | rival -> opponent に改名する　|
| `Pokemon` | `base_ability` | `base_ability_name` | poke-envに合わせて改名する |

---

### 分類 B: 変換ユーティリティが必要なもの（poke-env → jpoke 方向のみ）

jpoke→poke-env エクスポートは対象外のため、アダプタクラスは作成しない。
変換ユーティリティ関数として jpoke 側に用意する。

#### B-1: Enum → 日本語 Literal 変換テーブル

最も広範囲に影響する差異。poke-env のデータを jpoke へ取り込む際の基盤。
以下のプロパティの変換すべてに共通する。

| 対象プロパティ | poke-env 型 | jpoke 型 | ユーザーコメント |
|---|---|---|
| `types` / `base_types` | `List[PokemonType]` | `list[Type]`（日本語 Literal） ||
| `tera_type` | `PokemonType \| None` | `Type`（日本語 Literal） ||
| `gender` | `PokemonGender` | `Gender`（日本語 Literal） ||
| `status` → `ailment.name` | `Status` Enum | 日本語 Literal（"まひ" 等） ||
| `effects` → `volatiles` のキー | `Effect` Enum | `VolatileName`（日本語 Literal） ||
| Move `type` | `PokemonType` | `Type`（日本語 Literal） ||
| Move `category` | `MoveCategory` | `MoveCategory`（日本語 Literal） ||

実装: `utils/type_defs.py` または専用モジュールに変換辞書として用意する。

#### B-2: 名前マッピング（英語 ↔ 日本語）

以下のプロパティは英日の名前マッピングテーブルが必要。

| 対象プロパティ | 変換内容 |
|---|---|
| Pokemon `name` | 英語名 ↔ 日本語名 |
| Move `id` / `name` | 英語 ID ↔ 日本語名 |
| `nature` | 英語性格名 ↔ 日本語性格名 |
| `ability` / `base_ability` | 英語特性名 → `data/ability.py` の日本語エントリ検索 |
| `item` | 英語アイテム名 → `data/item.py` の日本語エントリ検索 |

#### B-3: 数値形式変換

[ユーザーコメント] jpokeのリスト管理のメリットを調査し、メリットがなければpoke-envの定義に合わせてリファクタしてもよい。

| 対象プロパティ | poke-env | jpoke | 変換内容 |
|---|---|---|---|
| `stats` | `Dict[str, int]`（英語キー） | `dict[Stat, int]`（"H","A",...） | キーマッピング |
| `base_stats` | `Dict[str, int]`（英語キー） | `list[int]`（インデックス順） | キー→インデックス変換 |
| `ivs` / `indiv` | `Dict[str, int]`（英語キー） | `list[int]` | 同上 |
| `evs` / `effort` | `Dict[str, int]`（英語キー） | `list[int]` | 同上 |
| `boosts` / `rank` | `Dict[str, int]`（英語キー） | `dict[Stat, int]`（"A","B",...） | キーマッピング |

```
インデックス対応: hp=0, atk=1, def=2, spa=3, spd=4, spe=5
Stat キー対応:   H="hp", A="atk", B="def", C="spa", D="spd", S="spe"
```

#### B-4: その他変換

| 対象プロパティ（差異一覧の項目） | 差異 | 変換方法 |
|---|---|---|
| Move `accuracy` | True = 必中（poke-env）vs None = 必中（jpoke） | `True → None` に変換 |
| `status_counter` | `ailment.turn_count`（アクセスパス違い） | インポート時に `Ailment.turn_count` に設定 |
| `must_recharge` | `has_volatile("リチャージ")` で代替 | 揮発性状態名で判定 |
| `protect_counter` | volatile 内部に保持 | `Volatile.counter` から取得 |
| Move `max_pp` | `data.pp`（アクセスパス違い） | `move.data.pp` 経由でアクセス |
| Move `flags` / `data.labels` | `Dict[str, int]` vs `list[MoveLabel]` | contact, sound 等をラベルに変換 |
| Pokemon `moves` | `Dict[str, Move]`（英語 ID キー）vs `list[Move]` | B-2 の名前マッピング経由でリストに変換 |
| `effects` / `volatiles` | `Dict[Effect, int]` vs `dict[VolatileName, Volatile]` | B-1 の Enum→Literal 変換後に lookup |
| Move `recoil: float` | 割合の数値（poke-env）vs `has_label("recoil")`（jpoke） | jpoke は割合を保持しないため精度に制限あり |

---

### 分類 C: 対象外

以下はいずれも対象外。

**jpoke に存在しない poke-env 機能（実装しない）**

- Pokémon Showdown サーバーへの WebSocket 接続全般（`parse_message`, `accept_challenges`, `ladder` 等）
- バトルフォーマット（`format`）・世代（`gen`）・バトルタグ（`battle_tag`）
- ダイナマックス（`is_dynamaxed`, `can_dynamax` 等）— jpoke 未実装
- Z ワザ（`available_z_moves`, `can_z_move` 等）— jpoke 未実装
- リプレイ保存（`save_replay`）
- `available_moves_from_request(request)` — PS リクエスト JSON 解析
- `was_illusioned()` — イリュージョン解除
- `selected_in_teampreview` — チームプレビュー選出フラグ

**jpoke → poke-env エクスポート（方針として対象外）**

差異一覧の以下の項目はすべて jpoke 状態を poke-env 形式で読み出す（export）方向のため対象外。

| 差異一覧の項目 | 対象外の理由 |
|---|---|
| Battle `available_moves: List[Move]` | `Command` → `Move` 変換が必要（export） |
| Battle `available_switches: List[Pokemon]` | jpoke バトル状態から抽出・変換が必要（export） |
| Battle `team: Dict[str, Pokemon]` | `list[Pokemon]` → `Dict` 変換（export） |
| Battle `weather: Dict[Weather, int]` | `Field` オブジェクト → `Dict` 変換（export） |
| Battle `fields: Dict[Field, int]` | `Field` オブジェクト → `Dict` 変換（export） |
| Battle `side_conditions` | `side_managers` → `Dict` 変換（export） |
| Player `choose_move(battle) -> BattleOrder` | `Command` ↔ `BattleOrder` 変換が必要（export） |
| Player `teampreview(battle) -> str` | `choose_selection` → 文字列変換（export） |
| PokeEnvBattleAdapter 等アダプタクラス | jpoke オブジェクトを poke-env 形式でラップ（export） |

**既知の意味的差異（API 変更なし）**

- Pokemon `weight`: 同名だが poke-env は図鑑値、jpoke は特性・アイテム反映済みの値。インポート時に注意が必要だが変換は行わない。
- Pokemon `name` / Move `id`: 英語 vs 日本語の言語差異は B-2 の名前マッピングで対処。

---

### 分類 D: jpoke 側にのみある機能（変更不要・jpoke の強み）

| 機能 | 説明 |
|---|---|
| `build_observation(observer) -> Battle` | 情報隠蔽バトルコピー（相手非公開情報を隠蔽） |
| `calc_lethal(attacker, moves, ...) -> list[LethalResult]` | 確定数計算 |
| `roll_damage() / calc_damages()` | ダメージ分布の全候補計算 |
| `EventManager + Event Enum` | イベント駆動の特性・アイテム・技発動管理 |
| `MoveLabel システム` | contact, sound, punch 等のラベルによるメタ分類 |
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
    pokemon.py    ← エイリアス property 追加（分類 A）
    move.py       ← エイリアス property 追加（分類 A）
  core/
    player.py     ← エイリアス property 追加（分類 A）
    battle.py     ← エイリアス property 追加（分類 A）
  utils/
    type_defs.py  ← poke-env Enum ↔ 日本語 Literal 変換テーブル追記（分類 B-1）
```

新規モジュール（`compat/` 等）は作成しない。変換テーブルは既存の `utils/type_defs.py` へ追記し、
stats 形式変換はヘルパー関数として `utils/` に置く。

[ユーザーコメント]　変換テーブルが肥大化する可能性があるため、専用モジュールに実装したい。

### 依存関係

- poke-env への依存なし（変換テーブルは純粋な辞書・関数）
- 既存テストへの影響なし（エイリアス property の追加のみ）

### 実装方針

- エイリアス property は既存クラスに直接追加する（アダプタクラスは作成しない）
- 変換テーブルは `utils/type_defs.py` に集約し、他所でハードコーディングしない
- poke-env → jpoke のインポートは「変換関数」として提供し、呼び出し側が明示的に変換する

詳細な実装計画は `docs/plan/poke_env_compat.md` を参照。
