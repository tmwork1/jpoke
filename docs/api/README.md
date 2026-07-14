# jpoke API リファレンス

`pip install jpoke` でインストールしたライブラリ利用者向けに、よく使う公開APIをまとめたもの。
内部実装（`data/`, `handlers/`, 各種 `*_manager.py` など）の詳細は
[CLAUDE.md](https://github.com/tmwork1/jpoke/blob/main/CLAUDE.md) を参照。

外部からの利用（テスト・bot・探索コード）は `Battle` の公開メソッドを入口にする方針
（[CLAUDE.md#開発ルール](https://github.com/tmwork1/jpoke/blob/main/CLAUDE.md)）のため、
本リファレンスも `battle.<manager>.<method>()` のような内部マネージャーへの直接アクセスや、
`_` 始まりの非公開属性は載せない。

このドキュメントは **よく使う公開APIの見取り図**であり、全メソッド・全引数を網羅する
ものではない。詳細な挙動・戻り値・例外条件は各クラスのdocstring（ソースコード:
`src/jpoke/core/battle.py`, `src/jpoke/core/player.py`, `src/jpoke/model/pokemon.py`）を
直接参照すること。

対象範囲・アーキテクチャの全体像は [README.md](https://github.com/tmwork1/jpoke/blob/main/README.md)
を参照。

## 目次

- [Battle](#battle)
- [Player](#player)
- [Pokemon](#pokemon)
- [Command](#command)
- [Move](#move)
- [テストユーティリティ（jpoke.testing）](#テストユーティリティjpoketesting)

## Battle

`src/jpoke/core/battle.py`。バトル全体の状態管理・ターン進行を担う中心クラス。

### コンストラクタ

```python
Battle(
    *players: Player,
    n_selected: int | None = None,
    seed: int | None = None,
    mega_evolution: bool = True,
    terastal: bool = True,
    critical_mode: CriticalMode = "normal",       # "normal" / "always"
    damage_roll: DamageRollMode = "normal",        # "normal" / "average" / "max" / "min"
    accuracy_fix_threshold: int | None = None,
    effect_chance_threshold: float | None = None,
    double_battle: bool = False,
)
```

- `*players`: 参加プレイヤー（可変長引数、通常2人）。`Battle(player1, player2)` のように
  個別の位置引数で渡す（タプル渡しは不可）
- `n_selected`: 選出可能なポケモンの数。省略時は `min(3, 各プレイヤーの手持ち数)` が自動設定される。
  手持ち数がプレイヤー間で異なる場合も両者に同じ値が適用されるため、片方の手持ちが少ないと
  両者とも選出数が絞られる点に注意
- `seed`: 乱数シード値。省略時はOSの乱数源から高エントロピーな値を生成する
- `mega_evolution` / `terastal`: メガシンカ／テラスタルを許可するか（デフォルト両方 `True`）
- `critical_mode`: 急所判定モード（デフォルト `"normal"`）
- `damage_roll`: ダメージ乱数モード（デフォルト `"normal"`）
- `accuracy_fix_threshold`: この値以上の命中率を100%固定にする（`None` なら無効）
- `effect_chance_threshold`: この値未満の追加効果確率を0%にする（`None` なら無効）
- `double_battle`: ダブルバトル向けのダメージ計算補正を有効にするか（デフォルト `False`。
  **対戦進行自体はシングルバトル専用**であることに変わりはない）

```python
from jpoke import Battle, Player

player1 = Player("Player 1")
player1.add_pokemon("ピカチュウ", move_names=["でんこうせっか"])
player2 = Player("Player 2")
player2.add_pokemon("フシギダネ", move_names=["たいあたり"])

battle = Battle(player1, player2, seed=1, damage_roll="max", critical_mode="always")
battle.start()
```

### 対戦進行系

| API | 概要 |
|---|---|
| `start()` | 選出と初期繰り出しを完了し、以降の `step()` を可能にする |
| `step(commands=None)` | ターンを1つ進める。`commands` を省略すると各 `Player.choose_command()` に従う |
| `play_out(max_turns=100)` | 決着がつくかターン上限に達するまで `step()` を自動的に繰り返す。勝者（`Player`）を返し、ターン上限で決着しなければ `None` |
| `finished` (property) | poke-env互換。対戦が終了しているか |
| `winner` (attribute) | 勝者の `Player`（未決着なら `None`）。`judge_winner()` を一度も呼ばないと未更新のままな点に注意（`finished`/`play_out()` 経由なら自動更新される） |
| `judge_winner()` | 勝者を判定する（未決着なら `None`） |
| `turn` (attribute) | 現在のターン数 |

```python
while not battle.finished and battle.turn < 100:
    battle.step()
print(battle.winner.username if battle.winner else "決着つかず")
```

`play_out()` を使うと上記ループは次の1行にまとめられる:

```python
winner = battle.play_out(max_turns=100)
```

### 状態取得系

| API | 概要 |
|---|---|
| `get_active(player)` | 指定プレイヤーの現在場に出ているポケモンを取得（交代中などは `None`） |
| `get_team(player)` | 指定プレイヤーの対戦中のチーム（選出漏れの控えも含む）を取得。`player.team` は開始前のスナップショットで対戦中は更新されないため、HP・瀕死・状態異常などバトル中の実際の状態を見るにはこちらを使う |
| `get_available_commands(player)` | 現在使用可能な `Command` のリストを取得 |
| `command_to_move(player, command)` | コマンドから `Move` オブジェクトを取得。`choose_command()` の実装で使う |

```python
active = battle.get_active(player1)
team = battle.get_team(player1)  # 瀕死・HP変化などを反映した実体
commands = battle.get_available_commands(player1)
move = battle.command_to_move(player1, commands[0])
```

`battle.query`（`PokemonQuery`）には他にも判定用メソッドがあるが、そのうち `Pokemon`/`Player`
単体の引数で完結するものは以下の通り `Battle` 直下からも呼べる（`AttackContext`/`EventContext`
を要求する内部専用メソッドは委譲していない）。`resolve_secondary_chance(ctx, chance, ...)` など
`AttackContext`/`EventContext` を引数に取る `Battle` のメソッドは、`handlers/*.py` のハンドラ
関数が受け取った ctx をそのまま渡す用途を想定した内部専用API。両型は
`from jpoke.core import EventContext, AttackContext` でインポートできる。

| API | 概要 |
|---|---|
| `can_switch(player)` | プレイヤーが交代可能かどうかを判定する（場のポケモンがとらわれ状態、または控えが全滅していれば不可） |
| `has_available_bench(player)` | とらわれ状態を無視して、控えに瀕死でないポケモンが残っているかを判定する（だっしゅつパック等の強制交代判定用） |
| `is_floating(pokemon)` | 浮いている状態か判定する（ひこうタイプ・特性・技の効果を考慮） |
| `is_trapped(pokemon)` | 逃げられない状態か判定する（ゴーストタイプは逃げられる） |
| `is_nervous(pokemon)` | きんちょうかん状態か判定する |
| `is_hazard_immune(pokemon)` | エントリーハザードへの免疫があるか判定する |
| `can_use_last_resort(pokemon)` | とっておきの発動条件を満たしているか判定する |
| `get_forced_move_name(pokemon)` | 強制行動中のポケモンが実行すべき技名を返す（固定されていなければ`None`） |
| `is_first_actor(player)` / `is_second_actor(player)` | このターンでplayerが先攻/後攻かどうかを判定する（1vs1想定、行動順未確定なら`None`） |
| `calc_move_priority(attacker, move)` | 指定した `Pokemon`/`Move` オブジェクトで技を発動したときの優先度（ON_MODIFY_MOVE_PRIORITYイベントによる補正込み）を計算する。`jpoke.testing.calc_move_priority(battle, player_index, move_index=0)` はインデックス指定の薄いラッパーで、内部でこちらを呼ぶ |
| `resolve_speed_order()` | 現在の実効素早さでソートしたポケモンのリストを返す（引数なし）。行動順そのものが必要な場合は予約済みコマンドを考慮する `resolve_action_order()` を使う |

```python
active = battle.get_active(player1)
if battle.can_switch(player1):
    ...
print(battle.is_floating(active), battle.can_use_last_resort(active))

# 優先度・素早さ順の確認
priority = battle.calc_move_priority(active, active.moves[0])
speed_order = battle.resolve_speed_order()
```

### ダメージ計算系

| API | 概要 |
|---|---|
| `calc_lethal(attacker, moves, critical=False, secondary=False, max_attack=10)` | 指定した技（列）を最大 `max_attack` 回撃ち込んだ場合の致死率を計算する。`moves` には技名の文字列・`Move`・`(技, ヒット数)` のタプル、およびそれらのリストを渡せる。`list[LethalResult]` を返す（各要素が1ヒットに対応し、最終的な致死率は `results[-1].lethal_probability`） |
| `calc_damages(attacker, defender, move, critical=False)` | 乱数によるダメージ幅を考慮した、可能な全ダメージ値のリスト（通常16通り）を返す |
| `roll_damage(attacker, defender, move, critical=False)` | `calc_damages()` の結果から `option.damage_roll` に従って1つ選んで返す |

```python
results = battle.calc_lethal(attacker, moves="ドラゴンテール", max_attack=5)
final = results[-1]
print(f"{final.n_attack}回攻撃した時点の致死率: {final.lethal_probability:.2%}")

raw_damages = battle.calc_damages(attacker, defender, "ドラゴンテール")
one_damage = battle.roll_damage(attacker, defender, "ドラゴンテール")
```

### シナリオ構築系

`Pokemon.hp` への直接代入や `boosts` の直接書き換えは禁止されている。状態を作るときは
必ず以下の `Battle` 経由のメソッドを使う。

| API | 概要 |
|---|---|
| `modify_hp(target, v=0, r=0, source=None, reason="")` | HPを変更する。`v`（固定量）と `r`（最大HPに対する割合、-1.0〜1.0）は同時指定不可 |
| `faint(target, source=None, reason="")` | 対象を即座にひんしにする（`modify_hp(v=-target.max_hp)` の薄いラッパー） |
| `modify_stats(target, stats, source=None, reason="")` | 複数の能力ランクを同時に変更する |
| `set_ailment(target, name, count=None)` | 状態異常を直接付与する（特性・タイプによる無効化判定はしない、シナリオ構築用の薄いラッパー） |
| `set_volatile(target, name, count=None)` | 揮発性状態（やどりぎのタネ等）を直接付与する |
| `set_weather(name, count=5)` | 天候を直接発動する |
| `set_terrain(name, count=5)` | 地形を直接発動する |
| `activate_global_field(name, count)` | グローバルフィールド効果（じゅうりょく・トリックルーム等）を直接発動する |
| `activate_side_field(player, name, count)` | 指定プレイヤーのサイドフィールド効果（リフレクター・ステルスロック等）を直接発動する |

```python
battle.modify_hp(defender, r=-0.6, reason="シナリオ構築用")   # 最大HPの60%分ダメージ
battle.modify_stats(defender, {"def": 1})                    # ぼうぎょ+1
battle.set_ailment(defender, "どく")
battle.set_volatile(defender, "やどりぎのタネ")
battle.activate_global_field("トリックルーム", 5)
battle.activate_side_field(player1, "ステルスロック", 1)
battle.faint(defender)
```

#### `set_*` と `activate_*` の使い分け

上表のメソッド名の動詞が `set_ailment`/`set_volatile`/`set_weather`/`set_terrain` と
`activate_global_field`/`activate_side_field` とで異なるのは意図的な区別であり、リネームの
予定はない。

- **`set_*`（状態異常・揮発性状態・天候・地形）**: 対象（ポケモン、またはバトル全体）に
  「単一の状態を直接セットする」メソッド。天候・地形は排他的（同時に有効なのは常に1つ）で、
  新しい状態を発動すると既存の状態を置き換える。状態異常・揮発性状態も対象ポケモンに紐づく
  個別の状態であり、いずれも「差し替え」のニュアンスが自然
- **`activate_*`（グローバルフィールド効果・サイドフィールド効果）**: 複数の効果が
  同時にスタックしうる（例: まきびし＋どくびし＋ステルスロックが同じサイドに共存）ため、
  「発動」のニュアンスが強い。内部実装でも `StackableFieldManager.activate()` を使っており、
  天候・地形が使う `ExclusiveFieldManager.apply()`（`set_weather`/`set_terrain`の委譲先）とは
  別クラスの別メソッドになっている

`set_weather`/`set_terrain` の `count` に既定値5があるのに対し `activate_global_field`/
`activate_side_field` に既定値が無いのも同じ理由に由来する整備漏れではなく意図的な差である。
天候・地形は通常の発動元（技・特性）が例外なく5ターンで発動するため単一の既定値が安全だが
（強天候〔おおひでり・おおあめ・らんきりゅう〕を発動する特性は`count=1`で発動するものの、
ターン経過による自然消滅の仕組み自体を持たず特性保持者が場を離れるまで持続するため、
この既定値の判断に影響しない。詳細は`set_weather`のdocstringを参照）、
グローバルフィールド効果はフェアリーロックのみ1ターン（他は5ターン）、サイドフィールド効果は
壁技（5ターン）・設置技（1層ずつ）・遅延効果（発動までのターン数）が同じ引数に混在するため、
単一の既定値を設けるとかえって誤ったシナリオを組んでしまう恐れがある。そのため
`activate_global_field`/`activate_side_field` では `count` を必須のまま維持している
（詳細は各メソッドのdocstringを参照）。

### ログ系

| API | 概要 |
|---|---|
| `print_logs(turn=None)` | 指定ターンのログを整形して出力する。`turn="all"` で1ターン目から現在までの全ログ |
| `get_log_lines(turn=None)` | `print_logs()` と同じ内容を文字列のリストとして返す（出力先を呼び出し側に委ねたい場合） |
| `get_event_logs(turn=None)` | `LogCode` 付きの構造化ログ（`EventLog`）を `Player` をキーとする辞書で返す。特定の種類のイベント（急所発生など）だけをプログラムで抽出したいときに使う |

```python
battle.print_logs()  # 現在ターンのログを表示

from jpoke.enums import LogCode
critical_hits = [
    log.pokemon
    for logs in battle.get_event_logs().values()
    for log in logs
    if log.log is LogCode.CRITICAL_HIT
]
```

### poke-env互換プロパティ

`observer`（プレイヤー視点）が設定されている前提のプロパティ群。方策実装（`choose_command()`）に
渡される `battle` は観測用コピーで、`battle.observer` が呼び出し元プレイヤー自身に設定されている。

| API | 概要 |
|---|---|
| `active_pokemon` | observer視点の場のポケモン |
| `opponent_active_pokemon` | observerから見た相手側の場のポケモン |
| `available_moves` | observerが選択可能な技（`Move`）のリスト |
| `available_switches` | observerが交代可能なポケモンのリスト |
| `side_conditions` | observer側のサイドフィールド状態の辞書 |
| `team` | observer側のチーム（`list[Pokemon]`。poke-envは`Dict[str, Pokemon]`だが差異あり） |
| `finished` / `won(player)` / `lost(player)` | 対戦終了判定・勝敗判定 |

```python
class MyPlayer(Player):
    def choose_command(self, battle: Battle) -> Command:
        moves = battle.available_moves
        if not moves:
            return battle.get_available_commands(self)[0]
        # battle.active_pokemon / battle.opponent_active_pokemon なども
        # 自分視点の情報としてそのまま使える
        ...
```

### リプレイ系

| API | 概要 |
|---|---|
| `build_replay_data()` | 対戦を再現するためのリプレイデータ（`BattleReplayData`）を組み立てる。対戦の途中でも呼べる |

```python
from jpoke.core.replay import replay_battle

replay_data = battle.build_replay_data()
serialized = replay_data.to_dict()          # json.dumps() 可能な辞書へ
restored = type(replay_data).from_dict(serialized)
replayed_battle = replay_battle(restored)   # 同じ展開の対戦を再生
```

## Player

`src/jpoke/core/player.py`。バトルに参加するプレイヤー（人間・AI方策どちらの土台にもなる）。

```python
Player(username: str = "")
```

### `add_pokemon()`

```python
add_pokemon(
    name: PokemonName,
    gender: Gender = "",
    nature: Nature = "まじめ",
    level: int = 50,
    ability_name: AbilityName = "",
    item_name: ItemName = "",
    move_names: list[MoveName] | None = None,
    tera_type: Type | None = None,
) -> Pokemon
```

ポケモンを1体作成し `team` に追加する。`from jpoke import Pokemon` を使わずにチームを
組める正規の追加ルート。引数はそのまま `Pokemon.__init__` に渡される。戻り値の `Pokemon`
は交代先の参照などに使える。

```python
from jpoke import Player

player = Player("Player 1")
attacker = player.add_pokemon(
    "ガブリアス", nature="いじっぱり", ability_name="さめはだ",
    item_name="こだわりスカーフ", move_names=["じしん", "げきりん"],
)
```

### `team` 属性の注意点

`player.team` は **コンストラクタ〜対戦開始前のスナップショット**であり、`Battle` 開始後の
対戦中はここに反映されるHP・瀕死・状態異常・ランク変化などは更新されない。対戦中の実際の
状態を見たい場合は `battle.get_active(player)`（場に出ているポケモン）や
`battle.get_team(player)`（チーム全体の実体）を使う。

### `choose_command()` のオーバーライド

方策（AI）を実装するには `Player` を継承し `choose_command()` をオーバーライドする。
デフォルト実装は「利用可能な行動コマンドの最初の1つを返す」だけの決定的な実装。

```python
from jpoke import Battle, Player
from jpoke.enums import Command

class StrongestMovePlayer(Player):
    """毎ターン、利用可能な技の中から最も威力の高い技を選ぶプレイヤー。"""

    def choose_command(self, battle: Battle) -> Command:
        commands = battle.get_available_commands(self)

        def move_power(command: Command) -> int:
            if not command.is_regular_move:
                return -1
            move = battle.command_to_move(self, command)
            return move.base_power if move.is_attack else 0

        return max(commands, key=move_power)
```

選出番号を決める `choose_selection(battle)`（デフォルトは先頭から順に選出）も同様の要領で
オーバーライドできる。

### `battle_against()`

poke-env互換: 各対戦相手と `n_battles` 回ずつ対戦し、双方の戦績（`n_finished_battles` /
`n_won_battles` など）を更新する。ネットワークI/Oがないため同期メソッド。

```python
player1.battle_against(player2, n_battles=100, seed=1)
print(f"{player1.username} 勝率: {player1.win_rate:.1%}")
```

## Pokemon

`src/jpoke/model/pokemon.py`。ポケモン1体の全状態（種族値・技・特性・アイテム・状態異常など）を
管理するクラス。

### コンストラクタ

```python
Pokemon(
    name: PokemonName,
    gender: Gender = "",
    nature: Nature = "まじめ",           # デフォルトはステータス補正なし
    level: int = 50,
    ability_name: AbilityName = "",     # 省略時は特性なし扱い
    item_name: ItemName = "",           # 省略時はアイテムなし
    move_names: list[MoveName] | None = None,  # 省略時は["はねる"]の1技のみ
    tera_type: Type | None = None,      # 省略時はそのポケモンの第1タイプを引き継ぐ
)
```

個体値・努力値はコンストラクタの引数ではなく、初期状態は**個体値31・努力値0固定**で
生成される。変更する場合は生成後に `set_ivs()` / `set_evs()` を呼ぶ。

```python
from jpoke import Pokemon

mon = Pokemon(
    "ガブリアス", nature="いじっぱり", ability_name="さめはだ",
    item_name="こだわりスカーフ", move_names=["じしん", "げきりん"],
)
mon.set_evs([0, 32, 0, 0, 0, 0])   # こうげき努力値をChampions形式（0〜32）で最大まで振る
mon.set_ivs([31, 31, 31, 31, 31, 0])
```

### `set_evs()` / `set_ivs()`

- `set_evs(evs, hp_policy="keep_absolute")`: 努力値を**Champions形式（各値0〜32）**で設定する。
  poke-envの努力値（各値0〜252）とはスケールが異なるため、poke-env形式の値をそのまま渡さない
  こと（`types/poke_env.py` の `evs_from_poke_env` で変換する）
- `set_ivs(ivs, hp_policy="keep_absolute")`: 個体値を設定する
- どちらも設定後にステータスを自動再計算する。`hp_policy` は最大HPが変化したときの現在HPの
  追従方法を指定する引数（`Pokemon.set_level` など他のステータス変更系メソッドにも共通）

### `show()`

```python
mon.show()   # 実数値・性格・特性・持ち物・テラスタイプ・技構成をまとめて表示
```

出力先を選びたい場合は `render_info()`（文字列を返すだけで `print` しない）を使う。

### 状態読み取り系

| API | 概要 |
|---|---|
| `status` (property) | poke-env互換。状態異常名（`ailment.name` のエイリアス） |
| `has_ailment(*ailment_names)` | 指定した状態異常のいずれかを持っているか |
| `has_volatile(volatile_name)` | 指定した揮発性状態を持っているか |
| `fainted` (property) | HPが0（ひんし）かどうか |
| `alive` (property) | HPが0より大きいかどうか |
| `hp` / `max_hp` / `hp_fraction` | 現在HP／最大HP／HP割合 |
| `has_item(name=None, consider_enabled=False)` | アイテムを持っているか |
| `has_move(move)` | 指定した技を持っているか |

```python
print(mon.status, mon.has_ailment("どく"), mon.has_volatile("こんらん"))
print(mon.fainted, mon.hp, mon.max_hp)
```

### シナリオ構築系（フォルム変化）

| API | 概要 |
|---|---|
| `set_form(name, hp_policy="keep_absolute", set_default_ability=False)` | フォルムをエイリアス（図鑑上の別名）指定で切り替える。種族値・タイプ・特性候補が変更先のものに差し替わる（ロトムの姿、ザシアン/ザマゼンタの剣王/盾王、ディアルガ等のオリジンフォルムなど）。既に同じフォルムなら何もせず `False` を返す。`hp_policy` は最大HPが変化したときの現在HPの追従方法（`set_evs`/`set_ivs`と共通）。`set_default_ability=True` の場合、特性を変更先の先頭特性にリセットする |

```python
mon = Pokemon("ロトム")           # でんき/ゴースト
mon.set_form("ヒートロトム")       # でんき/ほのお に切り替わる（種族値・タイプ込み）
print(mon.types, mon.stats)
```

`Battle` の「シナリオ構築系」（`modify_hp`/`set_ailment`等、[上記参照](#シナリオ構築系)）と
同じく対戦を進行させずに状態を直接組み立てるためのメソッドだが、`set_form` は `Pokemon`
自身のメソッドである点に注意（`Battle` 側に委譲ラッパーは無く、`mon.set_form(...)` の形で
直接呼ぶ）。

## Command

`src/jpoke/enums/command.py`。プレイヤーの1回の行動（技使用・交代・テラスタル等）を表す
`Enum`。`Player.choose_command()` の戻り値、`Battle.step(commands=...)` の値として使う。
`from jpoke import Command`（トップレベルパッケージからの再エクスポート）でも
`from jpoke.enums import Command` と同じものが取得できる。

### 定数

命名規則は `{種別}_{インデックス}`（インデックスは0〜9、手持ち・技のスロット番号に対応）。

| 定数 | 概要 |
|---|---|
| `Command.MOVE_0` 〜 `Command.MOVE_9` | 技コマンド（インデックスは `Pokemon.moves` の順） |
| `Command.SWITCH_0` 〜 `Command.SWITCH_9` | 交代コマンド（インデックスは `Player.team` の順） |
| `Command.TERASTAL_0` 〜 `Command.TERASTAL_9` | テラスタル＋技使用コマンド |
| `Command.MEGAEVOL_0` 〜 `Command.MEGAEVOL_9` | メガシンカ＋技使用コマンド |
| `Command.GIGAMAX_0` 〜 `Command.GIGAMAX_9` | ダイマックス＋技使用コマンド（**未実装**、下記注記参照） |
| `Command.ZMOVE_0` 〜 `Command.ZMOVE_9` | Zワザ使用コマンド（**未実装**、下記注記参照） |
| `Command.STRUGGLE` | わるあがき（技のPPが全て0の場合に強制される） |
| `Command.FORCED` | 強制再行動（きゅうしょにあたる等、選択の余地がない行動） |

> **注記**: `GIGAMAX_*` / `ZMOVE_*` はダイマックス・Zワザに対応するための定義だが、本プロジェクトの
> 対象範囲（[README.md 対象範囲](../../README.md#対象範囲)参照）であるポケモンチャンピオンズの
> シングルバトルにダイマックス・Zワザは存在しないため未実装。`get_available_commands()` が
> これらのコマンドを選択肢として返すことはなく、`battle.step()` に明示的に渡した場合も常に
> わるあがき扱いになる（`command_manager.py` の `resolve_move_from_command()` を参照）。将来的な
> 拡張やAPIとしての完全性のために `Command` の定義自体は残しているが、現時点では使用しないこと。

```python
from jpoke.enums import Command

battle.step({player1: Command.MOVE_0, player2: Command.SWITCH_1})
```

### クラスメソッド

インデックスから対応するコマンドを組み立てる際に使う。`get_available_commands()` の結果を
手作業で組み立てたい場合や、決まったインデックスの技・交代先を指定したい場合に使う。

| API | 概要 |
|---|---|
| `Command.get_move_command(index)` | 指定インデックスの技コマンドを取得 |
| `Command.get_switch_command(index)` | 指定インデックスの交代コマンドを取得 |
| `Command.get_terastal_command(index)` | 指定インデックスのテラスタルコマンドを取得 |
| `Command.get_megaevol_command(index)` | 指定インデックスのメガシンカコマンドを取得 |
| `Command.get_gigamax_command(index)` | 指定インデックスのダイマックスコマンドを取得（**未実装**、上記注記参照） |
| `Command.get_zmove_command(index)` | 指定インデックスのZワザコマンドを取得（**未実装**、上記注記参照） |

```python
from jpoke.enums import Command

# battle.get_team(player) 内でのインデックスから交代コマンドを組み立てる
bench_index = battle.get_team(player).index(bench_pokemon)
switch_command = Command.get_switch_command(bench_index)
battle.step({player: switch_command, opponent: Command.MOVE_0})
```

### インスタンスプロパティ・メソッド

`battle.get_available_commands(player)` で取得した `Command` の種別判定に使う。

| API | 概要 |
|---|---|
| `is_type(command_type)` | 指定した種別（`"any"` / `"move"` / `"switch"`）かどうか。`"move"` は通常技コマンドに加え、テラスタル・メガシンカ・ダイマックス・Zワザを伴う技コマンドも含む（`is_regular_move` は通常技コマンドのみ） |
| `is_regular_move` (property) | 技コマンド（`MOVE_*`）かどうか |
| `is_switch()` | 交代コマンド（`SWITCH_*`）かどうか |
| `is_terastal` (property) | テラスタルコマンドかどうか |
| `is_megaevol` (property) | メガシンカコマンドかどうか |
| `is_gigamax` (property) | ダイマックスコマンドかどうか（**未実装**、上記注記参照） |
| `is_zmove` (property) | Zワザコマンドかどうか（**未実装**、上記注記参照） |
| `index` (property) | コマンドのインデックス（特殊コマンドは0） |

```python
def choose_command(self, battle: Battle) -> Command:
    commands = battle.get_available_commands(self)
    move_commands = [c for c in commands if c.is_regular_move]
    return move_commands[0] if move_commands else commands[0]
```

## Move

`src/jpoke/model/move.py`。技1つ分のデータと現在のPPを保持するクラス。
`Pokemon.moves` の要素、`battle.command_to_move(player, command)` の戻り値、
`battle.available_moves` の要素として得られる。

```python
Move(name: MoveName)
```

通常は `Pokemon` のコンストラクタ（`move_names=[...]`）経由で生成されるため、直接
インスタンス化する機会は少ない。

### 主要属性

| API | 概要 |
|---|---|
| `name` (property) | 技名 |
| `pp` / `current_pp` | 現在のPP（`current_pp` はpoke-env互換のエイリアス） |
| `max_pp` (property) | 最大PP |
| `type` | 技のタイプ（一部の効果で戦闘中に変化しうる） |
| `base_power` | 技の威力。変化技は `None` |
| `category` | `"physical"` / `"special"` / `"status"` |
| `priority` (property) | 技の優先度 |
| `accuracy` (property) | 命中率。`None` の場合は必中 |
| `target` (property) | 技の対象（`"foe"` / `"self"` など） |
| `crit_ratio` (property) | 急所ランク補正値 |

```python
move = battle.command_to_move(player1, Command.MOVE_0)
print(move.name, move.type, move.category, move.base_power, move.pp)
```

### 判定系プロパティ

| API | 概要 |
|---|---|
| `is_attack` (property) | 物理・特殊技（攻撃技）かどうか。変化技は `False` |
| `is_blocked_by_protect` (property) | 「まもる」で防がれる技かどうか |
| `is_reflectable` (property) | マジックコート・マジックミラーで跳ね返される技かどうか |
| `has_flag(flag)` | 指定した技フラグ（`MoveFlag`）を持つか。リストを渡すといずれか1つ持てば `True` |

```python
if move.is_attack:
    print(f"{move.name} の威力: {move.base_power}")
print(move.has_flag("sound"))          # 音技かどうか
print(move.has_flag(["punch", "bite"]))  # パンチ技かかみつき技のどちらか
```

### 連続技系

| API | 概要 |
|---|---|
| `min_hits` (property) | 最小ヒット数（連続技でなければ1） |
| `max_hits` (property) | 最大ヒット数（連続技でなければ1） |
| `expected_hits` (property) | poke-env互換の期待ヒット数（2〜5回技は分布 2:3:4:5=35:35:15:15 に基づく3.1固定） |

```python
print(f"{move.name}: {move.min_hits}〜{move.max_hits}回技、期待ヒット数 {move.expected_hits:.1f}")
```

### PP操作

| API | 概要 |
|---|---|
| `modify_pp(v)` | PPを `v` 分だけ増減する（0〜最大PPの範囲でクリップ） |

```python
move.modify_pp(-1)   # 技を1回使用した分PPを減らす
move.modify_pp(-99)  # PPを0にする（わるあがきを誘発させたい場合など）
```

## テストユーティリティ（jpoke.testing）

`src/jpoke/testing.py`。上記の `Battle` / `Player` / `Pokemon` を毎回組み立てる代わりに、
状態異常・揮発性状態・天候・場の効果などを指定してバトルを一発でセットアップできる
薄いヘルパー集。`tests/test_utils.py` にあった内部テスト専用ヘルパーが本体パッケージへ
昇格したもので、`pip install jpoke` だけで（`jpoke` リポジトリを clone せずに）
ピンポイントな状態検証・技の実行・行動順の確認などができる。

`fix_damage()` / `fix_random()` は `Battle` の内部属性を直接差し替えるモンキーパッチの
デバッグ用ユーティリティであり、本番の対戦進行（bot 運用等）では使わないこと。

```python
from jpoke import Pokemon
from jpoke.testing import start_battle, run_move, calc_lethal

# start_battle() は Battle(...).start() に加えて、状態異常・揮発性状態・天候・
# 場の効果・命中率固定などをまとめて指定できる
battle = start_battle(
    team0=[Pokemon("ピカチュウ", move_names=["でんこうせっか"])],
    team1=[Pokemon("フシギダネ", move_names=["たいあたり"])],
    weather=("はれ", 5),
    accuracy=100,          # 命中率を固定
    secondary_chance=1.0,  # 追加効果を必ず発動
)

# run_move() は指定インデックスのポケモンが指定インデックスの技を使い、ログを出力する
run_move(battle, atk_idx=0, move_idx=0)

# calc_lethal() は Battle.calc_lethal() のインデックス指定版
results = calc_lethal(battle, atk_idx=0, moves="でんこうせっか", max_attack=3)
print(results[-1].lethal_probability)
```

| API | 概要 |
|---|---|
| `start_battle(team0, team1, ...)` | チーム・状態異常・揮発性状態・天候・地形・場の効果・命中率固定などを指定して `Battle` を初期化し `start()` まで済ませる |
| `run_move(battle, atk_idx, move_idx=0)` | 指定インデックスのポケモンに指定インデックスの技を使わせ、ログを出力する |
| `run_switch(battle, player_idx, new_idx)` | 指定インデックスのポケモンに交代させる |
| `can_switch(battle, player_idx)` | 指定プレイヤーが交代可能か判定する |
| `apply_ailment(battle, active_index, ailment_name, count=1, by_foe=False, overwrite=False)` | 指定インデックスのポケモンに状態異常を直接付与する |
| `change_item(battle, mon, item_name, source=None)` | ポケモンのアイテムを変更する |
| `get_action_order(battle, command0=None, command1=None)` | コマンドを予約し、そのターンの行動順を取得する |
| `reserve_command(battle, command0=None, command1=None)` | `step()` を介さずコマンド予約状態だけを作る（行動順・優先度だけを検証したい場合） |
| `build_context(battle, atk_idx, move_idx=0)` | `AttackContext` を組み立てる |
| `calc_lethal(battle, atk_idx, moves, critical=False, secondary=False, max_attack=10)` | `Battle.calc_lethal()` のインデックス指定版 |
| `calc_move_priority(battle, player_index, move_index=0)` | 指定インデックスの技を使ったときの優先度を返す。`Battle.calc_move_priority(pokemon, move)` のインデックス指定版 |
| `end_turn(battle)` | `Battle.end_turn()` のラッパー |
| `fix_damage(battle, damage)` | ダメージ計算を固定値にする（デバッグ専用モンキーパッチ） |
| `fix_random(battle, value)` | `battle.random.random()` を固定値にする（デバッグ専用モンキーパッチ） |
| `CustomPlayer` | 常に利用可能な最初のコマンドを選択する `Player` 実装。上記ヘルパーの内部で使われる |

## 関連リンク

- [README.md](https://github.com/tmwork1/jpoke/blob/main/README.md) — クイックスタート・
  アーキテクチャ概要・対象範囲の定義
- [examples/](https://github.com/tmwork1/jpoke/blob/main/examples/README.md) — 導入・AI開発・
  ダメージ計算ツール開発・戦術研究のユースケース別サンプルスクリプト
- `tests/CLAUDE.md` — clone前提のテストヘルパー（`start_battle` / `run_move` 等）の使い方
