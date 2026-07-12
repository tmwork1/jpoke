# 計画書: ダブルバトルのダメージ計算対応

## 目的

本プロジェクトの対象はポケモンチャンピオンズ**シングルバトルのみ**（README.md「対象範囲」）だが、
**ダメージ計算のみ**ダブルバトルの数値を再現できるようにしておきたい。あくまで「おまけ」の
計算オプションであり、ダブルバトルの対戦進行そのものを実装するものではない。

対応する影響は以下の2点のみ：

1. 範囲攻撃技（複数対象にヒットする技）は、ダメージが0.75倍(3072/4096)になる
2. リフレクター/ひかりのかべ/オーロラベールによるダメージ軽減率が、シングルの1/2(2048/4096)から
   ダブルでは2/3(2732/4096)に弱まる

**スコープ外**（今回は対応しない）:

- ダブルバトルの対戦進行そのもの（2体同時選出・味方対象技・巻き添え等）
- 技の対象選択ロジック（`Move.target` は今回変更しない。現状通り常に `"foe"`）
- コマンド生成・行動順・命中率補正など、ダメージ計算以外の一切のダブル固有仕様

つまり `Battle` はこれまで通り1体対1体のシングル戦のみを進行させる。今回追加するのは
`BattleOption.double_battle` という**単一のオプトインフラグのみ**であり、実際のターン進行
（`move_executor.py` の `_execute_hit` 等）の挙動は一切変更しない（`double_battle=False`
（デフォルト）のままなら常にこれまで通りの計算になる）。

## 現状分析

### `BattleOption`（`src/jpoke/core/battle.py` L67-84）

既存の対戦全体ルールオプション。`mega_evolution` / `terastal` のような bool フィールドを追加する前例がある。
`Battle.__init__`（L120-129）は各フィールドを個別キーワード引数として受け取り、内部で `BattleOption` にまとめる方式。
`tests/test_utils.py` の `start_battle`（L25-43）も同じキーワード引数をそのまま中継している。
→ 今回追加する `double_battle` もこの方式に合わせる。

`double_battle` は「壁（リフレクター等）が対戦全体を通してどちらの軽減率で動くか」「複数対象補正を
そもそも考慮するか」という**対戦中ずっと有効な恒常ルール**であり、`critical_mode` / `damage_roll` と
同じ「計算方法の方針」レベルのオプションである。呼び出しごとの引数（`is_spread_hit` のようなもの）は
追加しない。本機能は「おまけ」の計算オプションであり、`BattleOption.double_battle` 1個のフラグだけで
完結させる。すなわち **`double_battle=True` の `Battle` でダメージ計算を行う場合、対象の技が複数対象に
なり得る技であれば常に複数対象ヒットとして0.75倍補正を適用する**（味方が既に倒れている等で実際の対象が
1体しかいない場合の例外は切り捨てる近似。`calc_damages` は元々攻撃側・防御側2体だけを渡す1対1の
インターフェースであり対象数を厳密に扱う設計になっていないため、この簡略化は許容範囲と判断する）。

### 実装方式: 既存の「範囲攻撃技」ではなく共通ハンドラで実装する

`ON_CALC_DAMAGE_MODIFIER` を使ったダメージ補正は、フィルター・ハードロック・プリズムアーマー
（`data/ability.py`）が全て同一の共有関数 `h.ハードロック_reduce_effective` を参照して登録されている
ように、「複数のデータエントリから同じ関数を参照登録する」パターンが既に確立している。

さらに `handlers/move_attack.py` には `pivot`・`ohko_damage`・`half_damage`・`level_fixed_damage`・
`apply_bind_to_defender` のように、**特定の技名に紐付かない汎用ロジックは英語のスネークケース関数名**で
実装し、複数の技の `MoveData.handlers` から同じ関数を参照登録する前例がある
（技名を冠した日本語関数名は1技専用の効果にのみ使う）。

複数対象0.75倍補正は「技自体が複数対象になり得るか」＋「`battle.option.double_battle` が真か」だけで
決まる、**対象技すべてに共通の1本のロジック**である。したがって：

- **MoveFlag の新設・DamageCalculator（`src/jpoke/core/damage.py`）の変更は不要**。
  `ON_CALC_DAMAGE_MODIFIER` は既存の仕組みのまま（base=4096固定）で、対象各技の `MoveData.handlers`
  に共通ハンドラ関数を登録するだけで完結する（壁のハンドラが `data/field/side_field.py` 側で
  完結しているのと全く同じ形）。
- 対象技は同一の関数 `reduce_damage_in_double_battle`（`handlers/move_attack.py` の
  `pivot`/`ohko_damage` 等と同じ「汎用関数」セクションに配置）を共有登録する。
- テラクラスターだけは「使用者がステラテラスタルしている場合のみ」という追加条件があるため、
  専用の日本語関数 `テラクラスター_reduce_damage` を新設し、既存の日本語名ハンドラ群と同じ並びに置く
  （`scripts/sort_handlers.py` で自動的に五十音順に整列される）。

### 壁ハンドラ（`src/jpoke/handlers/field.py`）

`リフレクター_reduce_damage`（L560-568）・`ひかりのかべ_reduce_damage`（L420-428）・
`オーロラベール_reduce_damage`（L141-163）は全て `apply_fixed_modifier(value, 2048)` を固定値で呼んでいる。
→ `battle.option.double_battle` が真なら `2732`、そうでなければ `2048` を使うよう分岐するだけでよい。
3関数とも `battle: Battle` を引数に持つため追加の引数伝播は不要。イベント登録（`data/field/side_field.py`）
自体は変更不要（新規ハンドラ登録ではなく既存ハンドラ本体の定数分岐のため、`docs/spec/turn.md` の
priority確認は対象外）。

### `Move.target` は変更しない

`src/jpoke/types/literals.py` の `MoveTarget = Literal["foe", "foe_side", "own_side", "self", "field"]`
はシングル専用の設計上、攻撃技は常に `"foe"`（単体）のままでよい。上記の通り「複数対象になり得るか」は
`MoveData.handlers` への登録の有無そのもので表現するため、新しい型やフラグを追加する必要はない。

### 対象技の実データ確認

旧版の計画書に列挙されていた69技を `jpoke.data.MOVES` と `docs/champions/move_list.txt` に
突き合わせた結果、7技（かまいたち・グランドフォース・コアパニッシャー・ダークウェーブ・
ベノムトラップ・シンクロノイズ・マグニチュード）は `MOVES` に存在せず、`champions/move_list.txt`
にも技名の行が存在しなかったため対象外とした。

さらに実装作業中、並行して進んでいた別のレビュー作業により `トラップシェル` と `ビックリヘッド` の
2技が「第9世代（スカーレット・バイオレット）で使用不可能な技」と判定されプロジェクトから削除された
（詳細は `docs/review/moves/トラップシェル.md` / `docs/review/moves/ビックリヘッド.md`）。
この2技も自動的に対象外となった。

→ 最終的に共通ハンドラを登録したのは **59技＋テラクラスター専用ハンドラ1件＝計60技**。

### テラクラスターの特別扱い

テラクラスターは「使用者がテラスタルしたテラパゴス（ステラテラスタル）の場合のみ」複数対象になる、
という**使用者の状態に依存する動的な条件**であり、他の技と同じ共通ハンドラでは表現できない。
`handlers/move_attack.py` のテラバースト実装（L1597-1608）で `ctx.attacker.active_tera_type == 'ステラ'`
がステラテラスタル判定の既存パターンとして使われている。
→ テラクラスター専用の `テラクラスター_reduce_damage` を実装し、
`battle.option.double_battle and ctx.attacker.active_tera_type == "ステラ"` を条件にする。

## 設計

### 1. `BattleOption` に `double_battle` を追加（`src/jpoke/core/battle.py`）

```python
@dataclass
class BattleOption:
    """対戦全体のルールオプション設定クラス。

    Attributes:
        ...(既存)
        double_battle: ダブルバトル向けのダメージ計算補正
            （複数対象になり得る技のダメージ0.75倍・壁の軽減率2/3倍）を有効にするか
    """
    mega_evolution: bool = True
    terastal: bool = True
    critical_mode: CriticalMode = "通常"
    damage_roll: DamageRollMode = "通常"
    accuracy_fix_threshold: int | None = None
    effect_chance_threshold: float | None = None
    double_battle: bool = False
```

`Battle.__init__` にも既存オプションと同じ並びで `double_battle: bool = False` を追加し、
`BattleOption(..., double_battle=double_battle)` に渡す。Args docstring にも追記する。
`Battle.calc_damages` / `Battle.roll_damage`（L658-707）・`DamageCalculator.calc_damages`（damage.py）は
シグネチャ・実装ともに変更不要。

### 2. 共通ハンドラ `reduce_damage_in_double_battle` を実装（`src/jpoke/handlers/move_attack.py`）

`pivot` / `ohko_damage` / `half_damage` と同じ「汎用関数」セクション（ファイル冒頭付近）に追加する：

```python
def reduce_damage_in_double_battle(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """範囲攻撃技: ダブルバトルでは複数対象ヒットによりダメージ0.75倍になる。"""
    if battle.option.double_battle:
        value = apply_fixed_modifier(value, 3072)
    return HandlerReturn(value=value)
```

### 3. テラクラスター専用ハンドラ `テラクラスター_reduce_damage` を実装（同ファイル）

既存の日本語名ハンドラ群と同じ並び（テラクラスターの処理がある箇所付近）に追加する：

```python
def テラクラスター_reduce_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """テラクラスター: 使用者がステラテラスタルの場合のみ、ダブルバトルで複数対象ヒットによりダメージ0.75倍になる。"""
    if (
        battle.option.double_battle
        and ctx.attacker.active_tera_type == "ステラ"
    ):
        value = apply_fixed_modifier(value, 3072)
    return HandlerReturn(value=value)
```

### 4. 対象技の `MoveData.handlers` に共通ハンドラを登録

既存の `handlers={...}` 辞書（`handlers={}` の場合は新設）に
`Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(ha.reduce_damage_in_double_battle)` を追加する
（`MoveHandler` の `subject_spec` デフォルトが `"attacker:self"` のため省略可、
`しおふき` 等の既存 `ON_CALC_POWER_MODIFIER` 登録と同じ書き方）。

ファイル別対象技一覧（1件ずつ `handlers` に上記エントリを追加するのみ。他フィールドは変更しない）：

- `src/jpoke/data/moves/move_a.py`: アストラルビット, あわ, いにしえのうた, いわなだれ, エアカッター,
  エレキネット, オーバードライブ, うたかたのアリア
- `src/jpoke/data/moves/move_ka.py`: かみなりあらし, キラースピン, ゴールドラッシュ, こがらしあらし,
  こごえるかぜ, こごえるせかい, こなゆき, こんげんのはどう, かえんだん
- `src/jpoke/data/moves/move_sa.py`: しおふき, しっとのほのお, シャカシャカほう, スケイルノイズ,
  スピードスター, じしん, じならし, じばく
- `src/jpoke/data/moves/move_ta.py`: ダイヤストーム, だくりゅう, たつまき, だんがいのつるぎ, チャームボイス,
  どくガス, ドラゴンエナジー, だいばくはつ
  （**テラクラスターはここでは対象外**。上記「3.」の専用ハンドラを登録する。
  トラップシェルは実装時点で既にプロジェクトから削除されており対象外）
- `src/jpoke/data/moves/move_na.py`: なみのり, ねっさのあらし, ねっぷう
- `src/jpoke/data/moves/move_ha.py`: バークアウト, ハイパーボイス, はっぱカッター, はるのあらし, ふぶき,
  ブリザードランス, ふんか, ばくおんぱ, はなふぶき, パラボラチャージ, ふしょくガス,
  ふんえん, ぶんまわす, ヘドロウェーブ, ほうでん
  （ビックリヘッドは実装時点で既にプロジェクトから削除されており対象外）
- `src/jpoke/data/moves/move_ma.py`: マジカルシャイン, むしのていこう, もえあがるいかり, ミストバースト
- `src/jpoke/data/moves/move_ya.py`: やきつくす, ようかいえき
- `src/jpoke/data/moves/move_wa.py`: ワイドフォース, ワイドブレイカー

計59技＋テラクラスター1技（専用ハンドラ）＝60技。

### 5. 壁の軽減率をダブルで2/3にする（`src/jpoke/handlers/field.py`）

`リフレクター_reduce_damage` / `ひかりのかべ_reduce_damage` / `オーロラベール_reduce_damage` の
`apply_fixed_modifier(value, 2048)` を以下のように変更する（3関数とも同じパターン）：

```python
def リフレクター_reduce_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """リフレクターで物理技ダメージ軽減"""
    if (
        not ctx.critical
        and not ctx.can_bypass_screen(battle)
        and ctx.move.category == "physical"
    ):
        modifier = 2732 if battle.option.double_battle else 2048
        value = apply_fixed_modifier(value, modifier)
    return HandlerReturn(value=value)
```

`ひかりのかべ_reduce_damage`・`オーロラベール_reduce_damage` も同様に `2048` の行だけを置き換える
（オーロラベールの重複回避ロジック等、他の分岐はそのまま維持）。
イベント登録（`data/field/side_field.py`）や priority は変更しない。

### 6. `tests/test_utils.py` の `start_battle` にキーワード引数を追加

```python
def start_battle(...,
                 accuracy_fix_threshold: int | None = None,
                 effect_chance_threshold: float | None = None,
                 double_battle: bool = False) -> Battle:
    ...
    battle = Battle(
        ...,
        double_battle=double_battle,
    )
```

Args docstringにも追記する。

## 実装順序

1. `src/jpoke/core/battle.py`: `BattleOption.double_battle` 追加、`Battle.__init__` に kwarg 追加
2. `src/jpoke/handlers/move_attack.py`: `reduce_damage_in_double_battle`（汎用関数セクション）と
   `テラクラスター_reduce_damage`（日本語名ハンドラ群）を実装
3. `python scripts/sort_handlers.py src/jpoke/handlers/move_attack.py`
   （`テラクラスター_reduce_damage` を五十音順の正しい位置に整列させる）
4. `src/jpoke/data/moves/move_a.py` 〜 `move_wa.py`: 対象技の `handlers` に
   `Event.ON_CALC_DAMAGE_MODIFIER: h.MoveHandler(ha.reduce_damage_in_double_battle)` を追加、
   テラクラスターには `テラクラスター_reduce_damage` を追加
5. `python scripts/sort_data/sort_moves.py`（データ変更を伴うため念のため実行）
6. `src/jpoke/handlers/field.py`: リフレクター/ひかりのかべ/オーロラベールの3関数を修正
7. `tests/test_utils.py`: `start_battle` に `double_battle` kwarg 追加
8. `tests/test_battle_option.py` にテストを追加し、`python scripts/sort_tests.py tests/test_battle_option.py`
   → `python scripts/generate_test_list.py` → `python -m pytest tests/ -v` で確認

## テスト観点

`tests/test_battle_option.py` に以下を追加した（`battle.damage_calculator.damage_modifier` を直接検証）：

- 複数対象になり得る技（ハイパーボイス）は `double_battle=True` で0.75倍(3072)、`False` で等倍(4096)
- 単体技（たいあたり）は `double_battle=True` でも等倍(4096)のまま
- テラクラスターはステラテラスタル前は等倍(4096)、ステラテラスタル後のみ0.75倍(3072)
- 壁（リフレクター）は `double_battle=True` で2732、`False` で従来通り2048
- 壁+複数対象技を同時に満たす場合は両方が重複して乗算され2049になる

## 備考

- `handlers/move_attack.py` への関数追加・`data/moves/*.py` への登録エントリ追加を伴うため、
  CLAUDE.mdの「ハンドラの追加ルール」に従い `sort_handlers.py` / `sort_data/sort_moves.py` を実行した。
- 今回の変更は既存技への `ON_CALC_DAMAGE_MODIFIER` ハンドラ追加のみであり、`docs/progress/move.md`
  等の実装進捗表は「新規技の実装」を対象にしたものであるため更新していない。
- 新規イベントの新設は行っていない（既存 `ON_CALC_DAMAGE_MODIFIER` にハンドラを追加登録するのみ）ため
  `docs/spec/turn.md` の priority 確認は対象外とした（`MoveHandler` のデフォルト priority=100 を使用。
  他の `ON_CALC_DAMAGE_MODIFIER` ハンドラ（フィルター等）も同じデフォルトのため整合する）。
- 対象外9技（かまいたち・グランドフォース・コアパニッシャー・ダークウェーブ・ベノムトラップ・
  シンクロノイズ・マグニチュード・トラップシェル・ビックリヘッド）が将来 jpoke に実装された場合は、
  本計画と同じ基準で `reduce_damage_in_double_battle` を登録する。
