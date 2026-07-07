# 計画書: HP吸収技（ドレイン系）

## 仕様要約

`docs/spec/moves/_move_secondary_2.md` の「HP吸収(与ダメ比)」列が非0の技をすべて対象とする。

- 攻撃命中後、与えたダメージに吸収率を乗算した値を攻撃側が回復する
- 吸収率 0.5: ウッドホーン・きゅうけつ・シャカシャカほう・すいとる・ドレインパンチ・パラボラチャージ・むねんのつるぎ・メガドレイン・ゆめくい
- 吸収率 0.75: デスウイング・ドレインキッス
- 回復量は `int(damage * heal_ratio)` で計算し、`ON_CALC_DRAIN` イベントを通じて外部修正の余地を持つ
- みがわりに対してダメージを与えた場合は `ctx.substitute_damage` を使用する
- ギガドレインは実装済みのためスキップ

## 現状の実装状況

| 技名 | MoveData 定義 | ハンドラ登録 | 備考 |
|------|:---:|:---:|------|
| ウッドホーン | 済 | 未 | `labels=["contact", "heal"]` |
| ギガドレイン | 済 | 済 | ON_HIT / `ギガドレイン_heal_attacker`（スキップ） |
| きゅうけつ | 済 | 未 | `labels=["contact", "heal"]` |
| シャカシャカほう | 済 | 未 | ON_DAMAGE_HIT にやけど追加効果ハンドラはあり。ドレインは未登録 |
| すいとる | 済 | 未 | `labels=["heal"]` |
| デスウイング | 未 | 未 | 新規 MoveData 追加が必要 |
| ドレインキッス | 済 | 未 | `labels=["contact", "heal"]` |
| ドレインパンチ | 済 | 未 | `labels=["contact", "punch", "heal"]` |
| パラボラチャージ | 済 | 未 | `labels=["heal"]` |
| むねんのつるぎ | 済 | 未 | `labels=["contact", "slash", "heal"]` |
| メガドレイン | 済 | 未 | `labels=["heal"]` |
| ゆめくい | 済 | 未 | `labels=["heal"]` |

> **訂正（レビュー時点）**: むねんのつるぎは一次情報（Wiki）と照合した結果、
> 回復量の端数を「切り上げ」で計算する点が他のドレイン技（切り捨て）と異なることが判明した。
> `_drain_hp` は再利用せず専用ロジックで実装する。詳細は
> `docs/plan/moves/むねんのつるぎ.md` を参照。本ファイルの以下の記載
> （むねんのつるぎに関する `_drain_hp(heal_ratio=0.5)` 再利用の記述）は誤りである。

> **訂正（ウッドホーン レビュー時点）**: 本ファイルおよび `_drain_hp` は
> 「回復量 = `int(damage * heal_ratio)`（切り捨て）」としていたが、これも誤りだった。
> `docs/wiki/moves/ウッドホーン.html`（および ギガドレイン・きゅうけつ 等の同種Wikiページ）の
> 「技の仕様」節に「回復量を算出する際、小数点以下は第四世代までは切り捨て、
> 第五世代以降は四捨五入する」と明記されている。`_drain_hp` は
> `max(1, round_half_up(damage * heal_ratio))` に修正済み（`handlers/move_attack.py`）。
> heal_ratio=0.5 の場合、四捨五入は「むねんのつるぎ」の「切り上げ」と常に同じ結果になる
> （ダメージが整数のため端数は必ず0か0.5であり、0.5は四捨五入でも切り上げになるため）。
> 詳細は `docs/plan/moves/ウッドホーン.md` を参照。
> なお本ファイルの「現状の実装状況」表・「ハンドラ構成」節の関数名（`_heal_attacker`）は
> 実装時に `_drain`（例: `ウッドホーン_drain`）へ変更されており古いままだが、
> 本レビューの対象範囲外のため修正していない（該当技の個別レビューで対応すること）。

## ハンドラ構成

| 技名 | イベント | Priority | subject_spec | 役割 |
|------|---------|---------|--------------|------|
| ウッドホーン | ON_HIT | 20 | attacker:self | 与ダメ×0.5 を回復 |
| きゅうけつ | ON_HIT | 20 | attacker:self | 与ダメ×0.5 を回復 |
| シャカシャカほう | ON_HIT | 20 | attacker:self | 与ダメ×0.5 を回復 |
| すいとる | ON_HIT | 20 | attacker:self | 与ダメ×0.5 を回復 |
| デスウイング | ON_HIT | 20 | attacker:self | 与ダメ×0.75 を回復 |
| ドレインキッス | ON_HIT | 20 | attacker:self | 与ダメ×0.75 を回復 |
| ドレインパンチ | ON_HIT | 20 | attacker:self | 与ダメ×0.5 を回復 |
| パラボラチャージ | ON_HIT | 20 | attacker:self | 与ダメ×0.5 を回復 |
| むねんのつるぎ | ON_HIT | 20 | attacker:self | 与ダメ×0.5 を回復 |
| メガドレイン | ON_HIT | 20 | attacker:self | 与ダメ×0.5 を回復 |
| ゆめくい | ON_HIT | 20 | attacker:self | 与ダメ×0.5 を回復 |

Priority 根拠: `docs/spec/turn.md` の `Event.ON_HIT` テーブル「priority=20: HP吸収技による回復」

## handlers/move_attack.py に追加する関数

既存の `_drain_hp` ヘルパーと `ギガドレイン_heal_attacker` を参照パターンとして、以下の関数を五十音順に追加する。

```python
def ウッドホーン_heal_attacker(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """ウッドホーンの回復量を計算する。"""
    _drain_hp(battle, ctx, value, heal_ratio=0.5)
    return HandlerReturn(value=value)


def きゅうけつ_heal_attacker(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """きゅうけつの回復量を計算する。"""
    _drain_hp(battle, ctx, value, heal_ratio=0.5)
    return HandlerReturn(value=value)


def シャカシャカほう_heal_attacker(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """シャカシャカほうの回復量を計算する。"""
    _drain_hp(battle, ctx, value, heal_ratio=0.5)
    return HandlerReturn(value=value)


def すいとる_heal_attacker(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """すいとるの回復量を計算する。"""
    _drain_hp(battle, ctx, value, heal_ratio=0.5)
    return HandlerReturn(value=value)


def デスウイング_heal_attacker(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """デスウイングの回復量を計算する。"""
    _drain_hp(battle, ctx, value, heal_ratio=0.75)
    return HandlerReturn(value=value)


def ドレインキッス_heal_attacker(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """ドレインキッスの回復量を計算する。"""
    _drain_hp(battle, ctx, value, heal_ratio=0.75)
    return HandlerReturn(value=value)


def ドレインパンチ_heal_attacker(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """ドレインパンチの回復量を計算する。"""
    _drain_hp(battle, ctx, value, heal_ratio=0.5)
    return HandlerReturn(value=value)


def パラボラチャージ_heal_attacker(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """パラボラチャージの回復量を計算する。"""
    _drain_hp(battle, ctx, value, heal_ratio=0.5)
    return HandlerReturn(value=value)


def むねんのつるぎ_heal_attacker(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """むねんのつるぎの回復量を計算する。"""
    _drain_hp(battle, ctx, value, heal_ratio=0.5)
    return HandlerReturn(value=value)


def メガドレイン_heal_attacker(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """メガドレインの回復量を計算する。"""
    _drain_hp(battle, ctx, value, heal_ratio=0.5)
    return HandlerReturn(value=value)


def ゆめくい_heal_attacker(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """ゆめくいの回復量を計算する。"""
    _drain_hp(battle, ctx, value, heal_ratio=0.5)
    return HandlerReturn(value=value)
```

## data/move.py の各 MoveData への handlers 追加

**ウッドホーン**（labels の後に追加）
```python
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.ウッドホーン_heal_attacker)
        }
```

**きゅうけつ**
```python
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.きゅうけつ_heal_attacker)
        }
```

**シャカシャカほう**（既存 ON_DAMAGE_HIT を残しつつ ON_HIT を追加）
```python
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.シャカシャカほう_heal_attacker),
            Event.ON_DAMAGE_HIT: h.MoveHandler(ha.シャカシャカほう_apply_ailment_to_defender),
        }
```

**すいとる**
```python
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.すいとる_heal_attacker)
        }
```

**デスウイング**（新規エントリ、MOVES 辞書の五十音順「デ」行付近に挿入）
```python
    "デスウイング": MoveData(
        type="ひこう",
        category="物理",
        pp=10,
        power=90,
        accuracy=100,
        labels=["contact", "heal"],
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.デスウイング_heal_attacker)
        }
    ),
```

**ドレインキッス**
```python
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.ドレインキッス_heal_attacker)
        }
```

**ドレインパンチ**
```python
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.ドレインパンチ_heal_attacker)
        }
```

**パラボラチャージ**
```python
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.パラボラチャージ_heal_attacker)
        }
```

**むねんのつるぎ**
```python
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.むねんのつるぎ_heal_attacker)
        }
```

**メガドレイン**
```python
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.メガドレイン_heal_attacker)
        }
```

**ゆめくい**
```python
        handlers={
            Event.ON_HIT: h.MoveHandler(ha.ゆめくい_heal_attacker)
        }
```

## 注意点・エッジケース

- `_drain_hp` 内で `damage = damage or ctx.substitute_damage` を処理するため、みがわり破壊時も正しく計算される
- `battle.modify_hp` 内部でHP最大値超えを防ぐ処理が保証されている
- シャカシャカほうは `ON_DAMAGE_HIT`（やけど）と `ON_HIT`（ドレイン）の両ハンドラを共存させる
- ゆめくいはねむり状態の相手にのみ命中するが、ドレインハンドラには使用条件チェック不要
- デスウイングの挿入位置は MOVES 辞書内「デ」行の五十音順に従う
