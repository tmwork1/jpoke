# コードレビュー — model・players

日付: 2026-07-12
対象: `src/jpoke/model/`（`ability.py`, `ailment.py`, `effect.py`, `field.py`, `item.py`,
`move.py`, `pokemon.py`, `stats.py`, `volatile.py`, `__init__.py`）、
`src/jpoke/players/`（`__init__.py`, `random_player.py`, `tree_search_player.py`）
観点: 責務分離、内部実装の隠蔽、拡張性、過剰設計、変数・関数・クラス・プロパティ名の一貫性と妥当性
前提: [model.md](model.md)（2026-07-05、`model/` 単体レビュー）、
[tree_search.md](tree_search.md)（2026-07-05）、[tree_search_framework.md](tree_search_framework.md)（2026-07-07、
`scripts/tree_search/framework.py` 時代のレビュー）を踏襲した後継ファイル。`model.md` は削除せず残置する。

`git log --since=2026-07-05 -- src/jpoke/model src/jpoke/players` で確認できる17件の変更
（`PokemonStatsクラスを廃止しPokemonに統合`、`Pokemonの一時状態をmemoryスコープに統一`、
`TreeSearchPlayer を src/jpoke/players/ へ昇格`、`RandomPlayerを追加` 等）を実際にコードへ反映
された結果として読み直し、前回指摘の現状確認と新規観点（命名）の両方を行った。

---

## 総論

前回（2026-07-05）`model.md` が最重大と位置づけた **CRIT-1**（`handlers/move_status.py` が
`Pokemon` の非公開属性 `_stats_manager` の内部可変リストを直接書き換えている）は、
`1df19540 refactor: PokemonStatsクラスを廃止しPokemonに統合` により **解消済み** であることを
実装で確認した。`PokemonStats`（`_stats_manager`）というクラスそのものが撤廃されて
`Pokemon` に統合され、`_stats`/`_ivs`/`_evs` は `Pokemon` 自身の非公開属性になった。
さらに、旧レビューが推奨していた「実数値の直接操作専用の公開メソッドを用意する」という
対応がそのまま実装されており（`Pokemon.get_raw_stat`/`set_raw_stat`、`pokemon.py:689-704`）、
`handlers/move_status.py` の該当4関数（ガードシェア・スピードスワップ・パワーシェア・
パワートリック）は現在すべてこの公開APIを経由するよう書き換わっている
（`handlers/move_status.py:666-668, 1281-1283, 2364-2366, 2390-2392`）。この統合により、
旧レビューが同時に指摘していた **OVER-3**（`PokemonStats` が `level`/`base`/`nature` を
保持せず自己完結していない分離）も併せて解消された。model/players 領域における
今回最大のポジティブな変化である。

一方で、今回「命名の一貫性」を軸に読み直した結果、**`.boosts`（能力ランク辞書）に
`_stats_manager` とほぼ同型の問題が新たに見つかった**（後述 CRIT-1）。`Pokemon.modify_stat`
（`battle.modify_stat`/`modify_stats` 経由、差分指定のみ）には「絶対値を設定する」操作に
対応する公開APIが無く、じこあんじ（相手ランクをコピー）やひっくりかえす（全ランク反転）、
しろいハーブ系（マイナスランクを0にリセット）など**差分では表現できない絶対値操作**を
実装する40箇所以上のハンドラが `mon.boosts[stat] = ...` という辞書への直接書き込みで
これを回避している。`_stats`/`_ivs`/`_evs` が今回の統合で明確に非公開化・API化された
のに対し、`boosts` は依然として素の public dict のままであり、`Pokemon` 内の「保護の強さ」に
非対称が生まれている。

`players/` は前回（2026-07-07 `tree_search_framework.md`）のレビュー時点では
`scripts/tree_search/framework.py` という未昇格の状態だったが、`9fb6dee2 refactor: TreeSearchPlayer
を src/jpoke/players/ へ昇格しフックをメソッド化` で `src/jpoke/players/tree_search_player.py`
へ完全に移行し、同レビューが「解消済み」と記載していた FW-U1/FW-U2/FW-U4/FW-D1/FW-D4 の
対応内容を実装ファイルで独立に再確認した（後述、いずれも実装が記述どおりであることを
コード上で確認できた）。加えて `779f1544 feat: Player.teamのスナップショット警告と
RandomPlayerを追加` により `players/random_player.py` が新設された。`players/` 側で
新規のバグは見つからなかった。

---

## 重大な指摘

### CRIT-1（新規）: `Pokemon.boosts` が `_stats` と異なり非公開化・専用APIを持たず、40箇所以上のハンドラが絶対値操作のため直接書き込みしている

**ファイル**: `src/jpoke/model/pokemon.py:107`（`self.boosts: dict[Stat, int]` の定義）,
`867-882`（`modify_stat`、差分指定のみ）

```python
# pokemon.py:867-882
def modify_stat(self, stat: Stat, v: int) -> int:
    """ランク補正を変更する。
    ...
    """
    old = self.boosts[stat]
    self.boosts[stat] = m.clamp_stats(old + v)
    return self.boosts[stat] - old
```

`Pokemon.modify_stat`（`battle.modify_stat`/`modify_stats` から呼ばれる、`core/status_manager.py:110-150`）
は **差分（delta）を渡してランクを増減させる** ことしかできない。ところが実際のゲーム
メカニクスには「絶対値での操作」が必要な効果が複数存在する。

```python
# handlers/move_status.py:1108（じこあんじ: 相手のランクを自分にコピー）
attacker.boosts[stat] = defender.boosts[stat]

# handlers/move_status.py:2416-2417（ひっくりかえす: 全ランクを反転）
for stat in mon.boosts:
    mon.boosts[stat] = -mon.boosts[stat]

# handlers/item.py:77-81（しろいハーブ等: マイナスランクを0にリセットする共通ヘルパー）
changed = {s: -v for s, v in mon.boosts.items() if v < 0}
for s in changed:
    mon.boosts[s] = 0
```

`grep '\.boosts\['` で確認すると、同種の直接書き込みが
`handlers/lethal.py`（20箇所以上）、`handlers/move_attack.py:976,2123`、
`handlers/item.py:81`、`handlers/move_status.py:764,1108,1118,2417`、
`core/switch_manager.py:87` に散在している（`lethal.py` は確定数計算専用の
軽量シミュレーションでありイベント発火自体が不要な設計だが、それ以外は通常の
バトル進行フローの一部）。

これは旧 `model.md CRIT-1` と構造的に同一の問題である。**`Pokemon` の公開APIが
「絶対値でのランク操作」という正当なユースケースをカバーしていないため、実装者が
非公開の内部表現（`boosts` 辞書）へ直接アクセスするしかない** という状況になっている。
違いは以下の2点:

1. `_stats`/`_ivs`/`_evs` は今回の統合でアンダースコア始まりの非公開属性として整理され、
   絶対値操作用に `get_raw_stat`/`set_raw_stat` という narrow な公開APIが用意された
   （CRIT-1 は解消済み）。一方 `boosts` はアンダースコアの付かない **public** 属性のまま
   残っており、同種の絶対値操作用APIが存在しない。命名規則上「公開」を意味する
   `boosts` に対して、実装者が `battle.modify_stat` という正規経路を意識せず
   直接書き込むことへの心理的抵抗が `_stats_manager` の時より低い。
2. `battle.modify_stat`/`modify_stats`（`core/status_manager.py:110-150`）は
   `ON_BEFORE_MODIFY_STAT` イベントの発火、および `stat_lowered_this_turn`/
   `stat_raised_this_turn`（うっぷんばらし・みわくのボイス・しっとのほのお用の
   スコープ付きフラグ、`pokemon.py:173-180, 227-233`）の更新を行うが、`.boosts[stat] = `
   の直接書き込みはこれらを一切経由しない。じこあんじの実装コメント
   （`handlers/move_status.py:1099-1101`）は「direct代入により、たんじゅん・
   あまのじゃく・クリアボディ・だっしゅつパック等のランク変化に反応する特性・
   アイテムを経由しない」という**意図的な**バイパスであることを明記しているが、
   同じパターンの他の呼び出し箇所（`handlers/move_attack.py`, `handlers/item.py` 等）
   の大半にはこの種の意図表明コメントが無く、「絶対値操作のため仕方なく直接書き込んだ」
   のか「本来 `battle.modify_stat` を通すべきだが書き忘れた」のか、コードを読むだけでは
   区別できない。

**推奨**: `Pokemon` に絶対値操作用の narrow な公開API（例:
`set_raw_boost(stat, value)` / `invert_boosts()` / `reset_negative_boosts()` のような、
`get_raw_stat`/`set_raw_stat` と対になる命名）を追加し、少なくとも
`handlers/move_status.py`・`handlers/move_attack.py`・`handlers/item.py` 側の
`mon.boosts[...] = ` をこの経由に統一する。イベント発火をあえて回避する必要がある
効果（じこあんじ等）については、そのAPI自体を「イベント非発火の絶対値セット」として
明示的に設計し、呼び出し側のコメントに頼らず意図を型・メソッド名で表現できるようにすべき。

---

## 中程度の指摘

### ISSUE-1（新規・ドキュメントドリフト）: `Pokemon.critical_rank` セッターの docstring が「テスト・デバッグ用」と説明しているが、実際は本番ハンドラ（じこあんじ）から使われている

**ファイル**: `src/jpoke/model/pokemon.py:898-917`, `src/jpoke/handlers/move_status.py:1111`

```python
# pokemon.py:898-917
@critical_rank.setter
def critical_rank(self, value: int):
    """急所ランクを設定する。
    ...
    Note:
        内部的にvolatile["きゅうしょアップ"]を管理するため、
        テストやデバッグ用に使用される。
    """
```

```python
# handlers/move_status.py:1096-1111（じこあんじ）
def じこあんじ_copy_ranks(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """じこあんじ: 相手の能力ランク変化・急所ランクをすべて自分にコピーする。..."""
    ...
    # 急所ランクに関する効果（きゅうしょアップ状態）も第六世代以降コピー対象。
    attacker.critical_rank = defender.critical_rank
```

このセッターは実際には本番のバトルフロー（じこあんじ技のハンドラ）から呼ばれており、
`テストやデバッグ用に使用される` という docstring の説明は誤り。すぐ隣にある兄弟プロパティ
`sub_hp`（`pokemon.py:999-1018`）は一字一句ほぼ同じ docstring（「内部的に
volatile["みがわり"]を管理するため、テストやデバッグ用に使用される」）を持つが、
こちらは `grep '\.sub_hp\s*='` の結果コードベース中に本番の呼び出し元が無く、
実際にテスト専用（`tests/moves_status/test_move_sa.py` 等）である。つまり同じ文言を
コピーして書かれた2つのセッターのうち、片方だけがその後の機能追加（じこあんじ実装）で
実態と乖離した、典型的なドキュメントドリフトの実例。

**推奨**: `critical_rank` セッターの Note を「じこあんじ（能力ランクコピー技）や
テスト・デバッグから、`volatiles["きゅうしょアップ"]` を経由せず急所ランクを
直接設定するために使う」のように実態に合わせて書き直す。

### ISSUE-2（新規）: `has_flag` が `Ability` と `Move` で同名・異なる引数契約になっている

**ファイル**: `src/jpoke/model/ability.py:68-77`, `src/jpoke/model/move.py:60-72`

```python
# ability.py:68-77
def has_flag(self, flag: str) -> bool:
    """特性の状態フラグを判定する。..."""
    return flag in self.data.flags

# move.py:60-72
def has_flag(self, flag: MoveFlag | list[MoveFlag]) -> bool:
    """技が特定のフラグを持っているかを判定する。
    複数のフラグが指定された場合、いずれかのフラグを持っていればTrueを返す
    """
    if isinstance(flag, list):
        return any(s in self.data.flags for s in flag)
    return flag in self.data.flags
```

同じメソッド名 `has_flag` が `Move` では「単一文字列 or リスト（OR条件）」を受け付けるのに対し、
`Ability` では単一文字列のみを想定している。`Move.has_flag(["a", "b"])` のような呼び出しに
慣れた実装者が誤って `mon.ability.has_flag(["a", "b"])` を書いた場合、`Ability.has_flag` の
実装は `["a", "b"] in self.data.flags`（リストがリストの要素として存在するかの判定）を
評価するため、`TypeError` にはならず**常に `False` を静かに返す**。特性側にリスト対応の
実装漏れがあるというより意図の違いだが、同名メソッドで異なる契約を持つこと自体が、
コードベース内で最も踏みやすい種類の呼び出しミス（型エラーにならない）を生んでいる。
`Item` は `has_flag` を持たない（`is_berry()` のような専用の判定メソッドのみ）ため、
この非対称は `Ability`/`Move` の2クラス間に限られる。

**推奨**: `Ability.has_flag` も `flag: str | list[str]` を受け付けるよう `Move` に合わせるか、
少なくとも docstring に「複数フラグの一括判定はサポートしない」旨を明記する。

### ISSUE-3（既存指摘の再検証・現存確認）: `Volatile` の docstring `Attributes` が実装と食い違ったまま残っている（model.md ISSUE-4 相当）

**ファイル**: `src/jpoke/model/volatile.py:20-25`（docstring） vs `31-48`（実装）

```python
# volatile.py:20-25（docstring）
Attributes:
    count: 揮発性状態の継続ターン数などを記録するカウンター
    value: 揮発性状態に紐づく数値（みがわりのHP等）
    disabled_move_name: かなしばりで使用禁止になっている技名
    locked_move_name: アンコールで固定されている技名
    source_pokemon: バインド等で使用者を記録（使用者が交代すると解除される）
```

実装は `count`/`move_name`/`hp`/`bind_damage_ratio` の4属性のみで、`value`/
`disabled_move_name`/`locked_move_name`/`source_pokemon` はいずれも実在しない
（`grep source_pokemon src/` は0件）。前回レビュー（`model.md ISSUE-4`）からの
17件の変更ではこのファイルは触られておらず、そのまま現存する。

### ISSUE-4（既存指摘の再検証・現存確認）: `Pokemon.weight` に特性名の直接分岐が残っている（model.md ISSUE-1 相当）

**ファイル**: `src/jpoke/model/pokemon.py:424-443`

```python
@property
def weight(self) -> float:
    w = self.data.weight
    match self.ability.name:
        case 'ライトメタル':
            w = int(w*0.5*10)/10
        case 'ヘヴィメタル':
            w *= 2
    if self.has_item('かるいし', consider_enabled=True):
        w = int(w*0.5*10)/10
    return max(w, 0.1)
```

`grep 'self.ability.name'` は今も `model/` 全体でこの1箇所のみ。CLAUDE.md の
「固有効果のロジックは `handlers/*` に実装し `data/*.py` から登録する」という規約から
唯一外れている箇所である点は前回から変わっていない。

### ISSUE-5（既存指摘の再検証・現存確認）: `model/ability.py` だけ `AbilityData` を `data/ability.py` 経由でインポートしている（model.md ISSUE-5 相当）

**ファイル**: `src/jpoke/model/ability.py:4`

```python
if TYPE_CHECKING:
    from jpoke.data.ability import AbilityData
```

他5ファイル（`item.py`, `field.py`, `ailment.py`, `volatile.py`, `move.py`）はいずれも
定義元の `jpoke.data.models` から直接インポートしている（`grep 'from jpoke.data.models import'`
で確認）。`ability.py` だけが `ABILITIES` 辞書を定義する `data/ability.py` 経由の再エクスポートに
依存しており、実害は無いが参照経路の一貫性が崩れている。

### ISSUE-6（既存指摘の再検証・移設先で現存確認）: 実数値の辞書設定が挿入順に依存している（model.md MINOR-3 相当、`PokemonStats` 統合に伴い `Pokemon.set_stats` へ移設）

**ファイル**: `src/jpoke/model/pokemon.py:675-687`

```python
def set_stats(self, stats: dict[Stat, int], hp_policy: HpPolicy = "keep_absolute"):
    """実数値から努力値を逆算して設定する。..."""
    for i, value in enumerate(stats.values()):
        self._set_stat_from_value(i, value)
    self.update_stats(hp_policy)
```

旧 `PokemonStats.set_stats_from_dict`（`model.md MINOR-3`）が指摘していた
「辞書の値を `enumerate` でインデックスアクセスし、キーの並びが `STATS`
（hp, atk, def, spa, spd, spe）と一致する前提を検証しない」というバグは、
`PokemonStats` 撤廃後の移設先である `Pokemon.set_stats` にそのまま引き継がれている。
呼び出し側が異なる順序の辞書を渡すと努力値が誤ったステータスに割り当てられる。
`stats[STATS[i]]` のようにキーで引く実装にすべき。

### ISSUE-7（新規）: `Player` 派生クラスの置き場所が `players/` と `core/replay.py` に分裂している

**ファイル**: `src/jpoke/players/__init__.py:5`, `src/jpoke/core/replay.py:82-102`

```python
# players/__init__.py:1-6
"""`Player` の派生方策実装を集約するパッケージ。

木探索ベースの `TreeSearchPlayer`、ランダム選択の `RandomPlayer` など、
bot・探索コードから再利用される方策実装をここに置く。
リプレイ再生用の `ReplayPlayer` / `replay_battle()` は `jpoke.core.replay` を参照。
"""
```

`TreeSearchPlayer`/`RandomPlayer` は `players/` パッケージに集約されているが、同じ
`XxxPlayer` 命名の `ReplayPlayer`（`core/replay.py:82-102`）だけは `core/` 側に残っている。
`players/__init__.py` 自身のdocstringがこの分裂を能動的に注記せざるを得ない状態であり、
「`Player` を継承した実装クラスは `players/` を見ればよい」という単純な期待が成立しない。
`ReplayPlayer` は `BattleReplayData`/`RecordedCommand`（リプレイ用のデータ構造）と
密結合しているため `core/replay.py` に置く設計判断自体は理解できるが、`jpoke.players`
のトップレベル docstring に例外を書かねばならない時点で、命名規約（`players/` =
「`Player` 派生の置き場所」）と実際の配置がずれていることを示している。

**推奨**: 実利は小さいが、`players/replay_player.py` に `ReplayPlayer` クラスのみを移動し、
データ構造（`RecordedCommand`/`BattleReplayData`/`replay_battle()`）は `core/replay.py` に
残す分割も検討に値する。最低限、`core/replay.py` 側のモジュール docstring にも
`players/` との使い分け方針を対で書いておくと、片方だけを読んだ実装者の混乱を防げる。

---

## 過剰設計の疑い

### OVER-1（既存指摘の再検証・現存確認）: `GameEffect` の有効/無効管理機構は依然として `Ability`/`Item` の2クラス専用（model.md OVER-1 相当）

**ファイル**: `src/jpoke/model/effect.py:39, 74-116`

`add_disable_reason`/`remove_disable_reason` の呼び出し元を再度 `grep` した結果、
`core/ability_manager.py:141,158`、`core/item_manager.py:52,72`、`core/lethal.py:319,323`
の5箇所のみで、すべて `.ability` または `.item` に対する呼び出しだった。`Move`/`Ailment`/
`Volatile`/`Field` に対する呼び出しは今回も0件。前回指摘から変化なし。

### OVER-2（既存指摘の再検証・現存確認）: `revealed` フラグが `Ailment`/`Field`/`Volatile` で形骸化したまま（model.md OVER-2 相当）

**ファイル**: `src/jpoke/model/ailment.py:35`, `src/jpoke/model/field.py:40`,
`src/jpoke/model/volatile.py`（未設定）

`core/observation_builder.py` が `.revealed` を読む対象は `mon.ability`/`mon.item`/
`move`/`mon`（Pokemon自身）の4種のみで、`Ailment`/`Field`/`Volatile` インスタンスの
`.revealed` を読む箇所は今回も見つからなかった。`Ailment`/`Field` は今も
コンストラクタで `revealed = True` を固定するだけの未使用属性、`Volatile` は
デフォルト `False` のまま一度も設定されない。前回指摘から変化なし。

### OVER-3（既存指摘の再検証・現存確認）: `GameEffect` 6派生クラスの `__deepcopy__` が個別実装のまま重複している（model.md ISSUE-2 相当）

**ファイル**: `model/ability.py:40-44`, `item.py:30-35`, `ailment.py:45-49`,
`volatile.py:50-54`, `move.py:46-50`, `field.py:44-48`

いずれも `cls.__new__` → `memo[id(self)] = new` → `fast_copy(self, new)` という
一字一句同じ6行が6ファイルに複製されている。前回指摘から変化なし。

### OVER-4（新規・軽微）: `pp_consumed_moves`/`removed_types` のセッターが未使用のまま残っている一方、`added_types` の同型セッターは使われている

**ファイル**: `src/jpoke/model/pokemon.py:259-261`（`pp_consumed_moves` セッター）,
`304-306`（`removed_types` セッター）, `295-297`（`added_types` セッター、使用あり）

`pp_consumed_moves`/`added_types`/`removed_types`/`stellar_boosted_types` はいずれも
`memory` の該当スコープに対する `get`+`setdefault` の薄いプロパティだが、
セッターの有無と使用実績が4者でバラバラになっている。

| プロパティ | セッター定義 | 実使用箇所（`grep '\.<name>\s*='`） |
|---|---|---|
| `added_types` | あり（295-297） | `handlers/move_status.py:1523,1602,2839`（`= []` でクリア） |
| `pp_consumed_moves` | あり（259-261） | 0件 |
| `removed_types` | あり（304-306） | 0件 |
| `stellar_boosted_types` | なし | ―（`.add()` による in-place 変更のみ、`move_executor.py:530`） |

`pp_consumed_moves`/`removed_types` は交代時に `memory["switch"] = {}` で
スコープごと一括リセットされる設計（`reset_on_switch_in`, `pokemon.py:135-137`）のため、
個別セッターを呼ぶ必要が実質無い（`added_types` だけはターン中盤で明示的にクリアする
効果が存在するため実際に使われている）。`.internal/plan/moves/とっておき.md`・
`.internal/plan/moves/はねやすめ.md` にはこれらのセッターを使う想定の記述が残っているが、
実装ではスコープ一括リセットに統合された結果、計画書の記述だけが古いまま取り残されている。
実害は無いが、「4つの同型プロパティのうち、どれにセッターがあり、どれが実際に使われているか」
が名前だけからは分からない状態になっている。

---

## 軽微な指摘

### MINOR-1（既存指摘の再検証・現存確認）: `self.data` の型ヒント用コメントが3パターンに割れている（model.md MINOR-5 相当）

**ファイル**: `item.py:26`, `ailment.py:37`, `volatile.py:48`, `move.py:36`
（`# type hint`）、`field.py:42`（`# IDE hint`）、`ability.py:38`（日本語）。
前回指摘から変化なし。

### MINOR-2（既存指摘の再検証・現存確認）: `Ability.reset_enable_state` と `Item.reset_enable_state` がほぼ同一実装（model.md MINOR-6 相当）

**ファイル**: `model/ability.py:56-66`, `model/item.py:46-51`。前回指摘から変化なし。

### MINOR-3（部分的に解消・部分的に現存）: `to_dict()`/`from_dict()` は `Pokemon` では実利用され始めたが `Move` では依然デッドコードのまま（model.md MINOR-2 の再検証）

**ファイル**: `src/jpoke/model/pokemon.py:1102-1137`（`Pokemon.to_dict`/`from_dict`）,
`src/jpoke/model/move.py:52-58`（`Move.to_dict`）

前回 `model.md MINOR-2` は「`Pokemon.to_dict()`/`Move.to_dict()` はいずれも呼び出し元が
無いデッドコード」と指摘していたが、`c9e9111b feat: 対戦ログのリプレイ再現機能` により
`Pokemon.to_dict()`/`from_dict()` は `core/replay.py:56,92` および
`tests/test_replay.py` から実際に呼ばれるようになった（`Pokemon.to_dict()` は
`BattleReplayData.teams` のスナップショットとして使われる）。一方 `Move.to_dict()`
（`move.py:52-58`）は `grep 'move\.to_dict\('` で今回もヒット0件のままで、
`Pokemon.to_dict()` 自体も技名の保存には `[move.name for move in self.moves]`
（`pokemon.py:1115`）を使っており `Move.to_dict()` を呼んでいない。`Move.to_dict()` の
デッドコードとしての性質は変わっていない。

### MINOR-4（新規）: `Move.reset()` は同系統の他メソッドと異なり、名前にトリガーとなるタイミングを含んでいない

**ファイル**: `src/jpoke/model/move.py:38-44`

```python
def reset(self, reset_pp: bool = False):
    """技の状態をリセットする。"""
```

`Pokemon.reset_on_switch_out()`（`pokemon.py:139`）、`Pokemon.reset_turn_state()`
（`pokemon.py:165`）、`Ability.reset_enable_state()`（`ability.py:56`）、
`Item.reset_enable_state()`（`item.py:46`）は、いずれも「いつ・何をリセットするか」を
メソッド名自体に含めている。一方 `Move.reset()` だけは単に `reset` で、実際に
`core/move_executor.py:313` の `ctx.move.reset()` から**技使用後**に呼ばれている
（テクスチャー等で一時的に上書きされたタイプ・威力・分類を戻す）ことは名前からは
読み取れない。兄弟メソッド群の命名パターン（`reset_on_switch_out`/`reset_turn_state`/
`reset_enable_state`）に倣うなら `reset_after_use()` のような名前の方が一貫する。

### MINOR-5（新規）: `modify_hp` にある「内部用・外部は `battle.modify_hp` を使う」という注記が、同じ規約対象である `modify_stat` には無い

**ファイル**: `src/jpoke/model/pokemon.py:850-865`（`modify_hp`）,
`867-882`（`modify_stat`）

```python
# modify_hp のNote（850-865）
"""
...
Note:
    HPは0から最大HPの範囲に制限される。
    このメソッドは内部用です。外部からはbattle.modify_hp()を使用してください。
"""

# modify_stat のNote（867-882、同種の警告なし）
"""
...
Note:
    ランクは-6から+6の範囲に制限される。
"""
```

CLAUDE.md は「`Pokemon.hp` へ直接代入禁止 → 必ず `battle.modify_hp(...)` を使う。
ランク変化は `battle.modify_stat(...)`」と両者を並列に規定しているが、`Pokemon` 側の
docstring では `modify_hp` にだけ「内部用です、外部は `battle.modify_hp()` を」という
明示的な誘導があり、`modify_stat` には同種の注記が無い。CRIT-1 で述べた `boosts` への
直接書き込みが多発している一因として、この注記の非対称も無関係ではないと考えられる。

---

## 命名の一貫性・妥当性

### 1. `model/` 内の getter/setter・状態変更メソッドの命名パターンは全体として高い一貫性を保っている

`Pokemon` を軸に整理すると、以下の対応がおおむね一貫して守られている。

- **絶対値の設定**: `set_level`/`set_nature`/`set_base`/`set_ivs`/`set_evs`/`set_stats`/
  `set_stat`/`set_evs_at`/`set_moves`/`set_form` と、いずれも `set_` プレフィックス。
- **差分（delta）の適用**: `modify_hp`/`modify_stat`（`Pokemon`）、`modify_pp`（`Move`）が
  揃って `modify_` プレフィックスを使い、戻り値も「実際に変化した量」で統一されている
  （`modify_hp` は実HP変化量、`modify_stat` は実ランク変化量、`modify_pp` は戻り値なしだが
  クランプの実装パターンは共通）。
- **所持・保有の判定**: `has_type`/`has_item`/`has_ailment`/`has_volatile`/`has_move`
  （`Pokemon`）が全て `has_` プレフィックスで統一され、「自分が何を持っているか」を表す。
- **状態そのものの判定**: `is_active`（`Ailment`/`Field`）、`is_sleep`/`uncurable`
  （`Ailment`）、`is_berry`（`Item`）、`is_attack`/`is_blocked_by_protect`/
  `is_reflectable`（`Move`）が `is_` プレフィックスで統一され、「対象それ自身が
  どういう状態か」を表す。`has_`（Pokemon視点の所持判定）と `is_`（対象自身の状態判定）が
  プレフィックスで綺麗に住み分けられており、意図的な命名規約として機能している。

この一貫性は前回（`model.md`）が指摘していた `indiv`/`effort` という独自語も、
今回の `PokemonStats` 統合に伴って `ivs`/`evs`（poke-env と同じ語彙、`evs` は
Champions固有スケールの注記付き）に統一されたことでさらに向上している
（`grep 'def indiv\|def effort'` は0件、完全に置き換わったことを確認済み）。

### 2. `set_stat` と `set_raw_stat` は名前が近すぎる割に意味が大きく異なる

**ファイル**: `src/jpoke/model/pokemon.py:815-834`（`set_stat`）,
`697-704`（`set_raw_stat`）

```python
def set_stat(self, idx: int, value: int, hp_policy: HpPolicy = "keep_absolute") -> bool:
    """指定した実数値になるよう努力値を設定する。... Returns: 設定に成功した場合True、失敗した場合False"""

def set_raw_stat(self, idx: int, value: int):
    """指定インデックスの実数値を努力値と無関係に直接書き換える。
    Note: ガードシェア・パワーシェア・パワートリック・スピードスワップなど、
    努力値の再計算を伴わずに実数値そのものを操作する専用効果でのみ使用する。"""
```

両者は「1文字 `raw` の有無」だけで区別される名前だが、意味は大きく異なる。
`set_stat` は努力値を逆算するため**失敗しうる**（対応する努力値が見つからなければ
`False` を返し状態は変わらない）上、`交代でリセットされる`（`reset_on_switch_out` →
`update_stats()` が努力値から再計算し直すため、永続的な変更になる）。一方
`set_raw_stat` は**必ず成功し**、努力値と無関係に実数値を直接上書きするため
`交代でリセットされる`（`update_stats()` が呼ばれると努力値ベースの値に巻き戻る＝
一時的な変更にしかならない）。「`raw` を付け忘れると別のメソッドが存在し、
かつ挙動が似て非なる」という組み合わせは、`set_stat` を書くつもりで補完候補から
`set_raw_stat` を誤選択（あるいはその逆）しても構文エラーにならず気づきにくい。
`set_raw_stat` の docstring は用途を専用効果に限定する注記があるため実害は
今のところ出ていないが、命名だけで「一時的操作 vs 永続的操作」の違いを表現できていない
点は改善の余地がある（例: `override_raw_stat`/`poke_stat` のように、より
「一時的に上書きする」ニュアンスを持つ動詞を検討する）。

### 3. `memory` スコープ付きプロパティの命名が、実際に保持されるスコープと必ずしも対応していない

**ファイル**: `src/jpoke/model/pokemon.py:173-347`

`Pokemon.memory` は `turn`/`switch`/`battle` の3スコープを持ち、各プロパティの
docstring・命名がどのスコープに属するかを示唆する設計になっている
（コメント: `pokemon.py:117-120` 「代表的なフラグへのアクセスは下部のプロパティ...を参照」）。
実際に対応関係を突き合わせると、以下のようになる。

| プロパティ | 命名が示唆するスコープ | 実際の格納スコープ |
|---|---|---|
| `stat_lowered_this_turn` | turn | `memory["turn"]`（一致） |
| `stat_raised_this_turn` | turn | `memory["turn"]`（一致） |
| `hits_taken` | turn（docstring「このターン中に」） | `memory["turn"]`（一致） |
| `last_damage_taken` 系 | turn（docstring「今ターン最後に」） | `memory["turn"]`（一致） |
| `acted_since_switch_in` | switch（命名に明示） | `memory["switch"]`（一致） |
| `ate_berry` | battle（docstring「今バトル中に」） | `memory["battle"]`（一致） |
| **`failed_or_immobile_last_turn`** | **turn**（「_last_turn」という命名） | **`memory["switch"]`**（不一致） |

`failed_or_immobile_last_turn`（`pokemon.py:235-242`）だけが、命名パターン上は
他の `_this_turn`/`turn` 系プロパティと同じ「ターン単位の情報」に見えるにもかかわらず、
実装は `switch` スコープに格納されている。これは「`turn` スコープに置くと
`reset_turn_state()` が次ターン開始時に即座にクリアしてしまい、『前のターンどうだったか』
を新しいターンの行動選択時に参照できなくなる」ため、意図的に `switch` スコープ
（登場・退場時のみリセット）を選んだ設計だと考えられ、**バグではなく正しい設計判断**
である可能性が高い。しかし、この設計上の理由はコード上どこにも明記されておらず、
命名だけを見た実装者が「なぜこの1つだけ `turn` スコープの他のプロパティと違う場所に
実装されているのか」を誤解し、次に似た「〇〇_last_turn」的なフラグを追加する際に
`memory["turn"]` へ格納してしまう（＝タイミングのバグを作り込む）リスクがある。
docstring に「`turn` スコープではなく `switch` スコープに保持する（ターン境界を
またいで参照する必要があるため）」旨を一言残すことを推奨する。

### 4. `players/` のクラス名は実際のアルゴリズム・挙動をおおむね正確に表しているが、境界の粒度に注意点がある

- **`TreeSearchPlayer`**: 実装（`_best_command`/`_worst_case_over_opponent`、
  `tree_search_player.py:201-298`）は「合法手を総当たり列挙し、相手が最悪の手を選ぶと
  仮定したミニマックスで評価する」という具体的なアルゴリズムであり、MCTS等の
  他の木探索アルゴリズムは実装していない。クラス docstring
  （`tree_search_player.py:17-50`）が「合法手を総当たりで評価する木探索プレイヤーの
  基底クラス」「ミニマックスで評価する」と明記しているため誤解の余地は小さいが、
  クラス名自体は `TreeSearchPlayer` という広いカテゴリ名であり、`MinimaxPlayer` のように
  具体的なアルゴリズム名を含む命名に比べると、分岐数が `len(my)×len(opp)` の
  累乗オーダーで増える（＝計算コストの特性がアルゴリズム名から連想しにくい）という
  情報がクラス名からは読み取れない。利用者が docstring を読まずにクラス名だけで
  「木探索＝賢く枝刈りしてくれるはず」と誤解するリスクはゼロではない。
- **`RandomPlayer`**: `choose_command()`（`random_player.py:22-24`）のみを
  `battle.decision_random.choice(...)` でランダム化しており、`choose_selection()`
  （選出の決定）は `Player` 基底クラスの既定実装（先頭から順番に選出、
  `core/player.py:108-120`）をそのまま継承している。docstring
  （`random_player.py:13`「合法手からランダムに選ぶだけのプレイヤー」）はこの範囲を
  正しく限定しているため誤りではないが、クラス名だけを見た利用者が
  「`RandomPlayer` を使えば選出もランダムになる」と期待する可能性はある
  （`choose_selection` も含めて完全にランダム化したい場合は自前でオーバーライドが必要）。

### 5. `Player` 基底クラスと派生クラス間のメソッド名・引数名のオーバーライドは一貫している

`Player.choose_command(self, battle: Battle) -> Command`（`core/player.py:122-137`）に対し、
`RandomPlayer.choose_command(self, battle: Battle) -> Command`
（`random_player.py:22`）、`TreeSearchPlayer.choose_command(self, battle: Battle) -> Command`
（`tree_search_player.py:110`）、`core/replay.py` の `ReplayPlayer.choose_command`/
`choose_selection` のいずれも、引数名（`battle`）・戻り値型を完全に一致させて
オーバーライドしている。`TreeSearchPlayer.__init__(self, username: str, max_plies: int = 1,
max_nodes: int | None = None)` も第一引数 `username` を基底クラス
（`Player.__init__(self, username: str = "")`）と同名で踏襲しており、
派生クラス間のシグネチャの一貫性という観点では問題は見つからなかった。

### 6. `GameEffect` 派生6クラスの `name`/`base_name` の意味論は共通だが、`Field.name` だけが独自の追加条件を持つ

`GameEffect.name`（`effect.py:53-63`）は「`enabled` なら `data.name`、無効化されていれば
空文字」という契約を6クラス共通で継承しているが、`Field.name`（`field.py:50-57`）だけが

```python
@property
def name(self) -> str:
    return super().name if self.count else ""
```

と `count > 0` という追加条件をオーバーライドで挿入している。`Field` は OVER-1 で
述べたとおり `add_disable_reason` が一度も呼ばれないため `enabled` は実質的に常に
`True` であり、この `name` プロパティの実際の意味は「`count > 0` のときだけ真の名前を
返す」という、他5クラスとは異なる基準（ターン数ベース）にほぼ完全にすり替わっている。
プロパティ名・契約自体は継承されているが、実質的な判定基準がサブクラスごとに
食い違う点は、命名の一貫性というより「同名プロパティが暗黙に意味を変える」設計上の
注意点として記録しておく価値がある。
