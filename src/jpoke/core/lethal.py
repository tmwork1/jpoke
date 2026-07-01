"""致死率計算ロジックを提供するモジュール。

技・アイテム・揮発状態などの効果をHP分布（LethalDist）として扱い、
複数回攻撃後の確定数と致死率を求める。

分布そのものの演算（LethalState / LethalDist / to_dist など）は
Battle に依存しないため `jpoke.utils.lethal_dist` に置く。
このモジュールは Battle/Pokemon/Move と結びついた計算ループを担う。

主要な型:
  LethalState  — HP・特性/道具の有効フラグをまとめた不変値（utils.lethal_dist）
  LethalDist   — LethalState → 出現頻度 の辞書（確率分布、utils.lethal_dist）
  LethalResult — 1ヒット分の計算結果（HP分布・ダメージ分布・致死率など）
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle, SideFieldManager
    from jpoke.model import Pokemon, Move

from copy import deepcopy
from dataclasses import dataclass, field
from collections import defaultdict

from jpoke.types import Stat, AilmentName, LethalEvent, LethalSubject
from jpoke.utils.lethal_dist import LethalDist, to_dist, _check_hp, subtract_dist


@dataclass(frozen=True)
class LethalHandler:
    """致死率計算専用のハンドラ定義。

    通常の Handler とは独立した仕組みで、LethalDist を受け取り
    加工した LethalDist を返す関数 func を保持する。

    Attributes:
        func: (battle, ctx, hp_dist) -> LethalDist を返す関数
        event: 発火イベント種別（"on_damage" / "on_move_secondary" / "on_turn_end" / "any"）
        subject: 対象ロール（"attacker" / "defender" / "any"）
        priority: 同一イベント内での処理順（小さいほど先）
    """
    func: Callable[..., LethalDist]
    event: LethalEvent
    subject: LethalSubject
    priority: int = 100


@dataclass(frozen=True)
class LethalContext:
    """致死率計算中にハンドラへ渡すコンテキスト。"""
    attacker: Pokemon
    defender: Pokemon
    move: Move
    critical: bool = False


@dataclass(frozen=True)
class LethalResult:
    """1ヒット時点の致死率計算結果。

    Attributes:
        n_attack: 何回目の攻撃か（1始まり）
        move: 使用した技
        hit: 多段技の何ヒット目か（1始まり）
        hp_dist: ダメージ適用後のHP分布
        damage_dist: このヒットで与えたダメージの分布
        attacker_rank / defender_rank: 計算時のランク補正
        attacker_ailment / defender_ailment: 計算時の状態異常
    """
    n_attack: int
    move: Move
    hit: int
    hp_dist: LethalDist
    damage_dist: LethalDist
    attacker_rank: dict[Stat, int] = field(default_factory=dict)
    defender_rank: dict[Stat, int] = field(default_factory=dict)
    attacker_ailment: AilmentName = ""
    defender_ailment: AilmentName = ""

    @property
    def hp_counter(self) -> dict[int, int]:
        """HP値 → 出現頻度 の辞書を返す。ability_enabled / item_enabled は無視する。"""
        result: dict[int, int] = defaultdict(int)
        for state, freq in self.hp_dist.items():
            result[state.hp] += freq
        return dict(result)

    @property
    def damage_counter(self) -> dict[int, int]:
        """ダメージ値 → 出現頻度 の辞書を返す。"""
        return {state.hp: freq for state, freq in self.damage_dist.items()}

    @property
    def min_damage(self) -> int:
        return min(self.damage_counter.keys())

    @property
    def max_damage(self) -> int:
        return max(self.damage_counter.keys())

    @property
    def lethal_probability(self) -> float:
        """HP が 0 になる確率（0.0〜1.0）を返す。"""
        hp_counter = self.hp_counter
        zero_freq = hp_counter.get(0, 0)
        total_freq = sum(hp_counter.values())
        return zero_freq / total_freq


def _lethal_loop(hp_dist: LethalDist,
                 battle: Battle,
                 attacker: Pokemon,
                 defender: Pokemon,
                 move_list: list[tuple[Move, int]],
                 critical: bool,
                 secondary: bool,
                 max_attack: int) -> list[LethalResult]:
    """致死率計算のメインループ。

    max_attack 回分、move_list の技を順に使用し、各ヒット後の LethalResult を返す。
    いずれかの時点で HP=0 の状態が現れたら途中で打ち切る。
    """
    # attacker, defender, critical はループ中に変化しないため、move ごとに1回だけ ctx を作る
    ctx_list = [
        (move, count, LethalContext(attacker, defender, move, critical=critical))
        for move, count in move_list
    ]

    results = []
    for atk in range(1, max_attack + 1):
        for move, count, ctx in ctx_list:
            for hit in range(1, count + 1):
                # 技ダメージを適用
                hp_dist, damage_dist = _apply_damage(battle, ctx, hp_dist)
                results.append(
                    LethalResult(n_attack=atk, move=move, hit=hit,
                                 hp_dist=hp_dist, damage_dist=damage_dist)
                )
                if _check_hp(hp_dist, 0):
                    return results

                # ヒット時のハンドラを適用（きのみ回復など）
                hp_dist = _emit("on_damage", battle, ctx, hp_dist)
                if _check_hp(hp_dist, 0):
                    return results

                # 技の追加効果ハンドラを適用
                if secondary:
                    hp_dist = _emit("on_move_secondary", battle, ctx, hp_dist)
                    if _check_hp(hp_dist, 0):
                        return results

            # ターン終了時のハンドラを適用（たべのこし回復など）
            hp_dist = _emit("on_turn_end", battle, ctx, hp_dist)
            if _check_hp(hp_dist, 0):
                return results

    return results


def calc_lethal(battle: Battle,
                attacker: Pokemon,
                moves: Move | tuple[Move, int] | list[Move | tuple[Move, int]],
                critical: bool,
                secondary: bool,
                max_attack: int) -> list[LethalResult]:
    """致死率計算のエントリーポイント。

    Args:
        battle: 現在のバトル状態（deepcopy して使用するため破壊しない）
        attacker: 攻撃側ポケモン
        moves: 技（単体 / (技, ヒット数) / リスト）
        critical: 急所計算をするか
        secondary: 追加効果ハンドラを適用するか
        max_attack: 最大攻撃回数

    Returns:
        各ヒット後の LethalResult のリスト（確定数が出た時点で打ち切り）
    """
    # 攻撃側のインデックスを取得
    attacker_index = battle._get_player_index(attacker)

    # deepcopy してバトル状態を壊さずに計算する
    battle = deepcopy(battle)
    attacker = battle.actives[attacker_index]
    defender = battle.foe(attacker)

    hp_dist = to_dist(
        defender.hp,
        ability_enabled=defender.ability.enabled,
        item_enabled=defender.item.enabled
    )
    move_list = _generate_move_list(moves)

    return _lethal_loop(hp_dist, battle, attacker, defender, move_list, critical, secondary, max_attack)


def _generate_move_list(moves: Move | tuple[Move, int] | list[Move | tuple[Move, int]]) -> list[tuple[Move, int]]:
    """moves 引数を (技, ヒット数) のリストに正規化する。"""
    if isinstance(moves, list):
        result = []
        for x in moves:
            if isinstance(x, tuple):
                result.append(x)
            else:
                result.append((x, 1))
        return result
    elif isinstance(moves, tuple):
        return [moves]
    else:
        return [(moves, 1)]


def _get_pokemon_handlers(event: LethalEvent,
                          mon: Pokemon,
                          subject: LethalSubject) -> list[LethalHandler]:
    """ポケモンの特性・道具・状態異常・揮発状態から該当ハンドラを取得する。"""
    candidates = [
        mon.ability.data.lethal_handler,
        mon.item.data.lethal_handler,
        mon.ailment.data.lethal_handler,
    ]
    candidates += [v.data.lethal_handler for v in mon.volatiles.values()]
    return [h for h in candidates if (
        h is not None and h.event in {event, "any"} and h.subject in {subject, "any"}
    )]


def _get_global_field_handlers(event: LethalEvent, battle: Battle) -> list[LethalHandler]:
    """天候・地形・共通フィールドから該当ハンドラを取得する。"""
    fields = [battle.weather, battle.terrain] + \
        list(battle.global_manager.fields.values())
    candidates = [field.data.lethal_handler for field in fields if field.is_active]
    return [h for h in candidates if h is not None and h.event in {event, "any"}]


def _get_side_field_handlers(event: LethalEvent,
                             side: SideFieldManager,
                             subject: LethalSubject) -> list[LethalHandler]:
    """片側フィールド（ステルスロックなど）から該当ハンドラを取得する。"""
    fields = side.fields.values()
    candidates = [field.data.lethal_handler for field in fields if field.is_active]
    return [h for h in candidates if (
        h is not None and h.event in {event, "any"} and h.subject in {subject, "any"}
    )]


def _get_handlers(event: LethalEvent,
                  battle: Battle,
                  ctx: LethalContext) -> list[LethalHandler]:
    """イベントに対応する全ハンドラを priority 順で返す。"""
    handlers = []
    handlers += _get_pokemon_handlers(event, ctx.attacker, "attacker")
    handlers += _get_pokemon_handlers(event, ctx.defender, "defender")
    handlers += _get_global_field_handlers(event, battle)
    handlers += _get_side_field_handlers(event, battle.get_side(ctx.attacker), "attacker")
    handlers += _get_side_field_handlers(event, battle.get_side(ctx.defender), "defender")
    return sorted(handlers, key=lambda h: h.priority)


def _apply_handlers(battle: Battle,
                    handlers: list[LethalHandler],
                    ctx: LethalContext,
                    hp_dist: LethalDist) -> LethalDist:
    """ハンドラを順に適用する。HP=0 の状態が現れたら即打ち切り。"""
    for h in handlers:
        if _check_hp(hp_dist, 0):
            break
        hp_dist = h.func(battle, ctx, hp_dist)
    return hp_dist


def _update_hp(mon: Pokemon, hp_dist: LethalDist):
    """分布内の最小 HP を mon.hp にセットする（後続ハンドラが参照するため）。"""
    mon.hp = min(state.hp for state in hp_dist)


def _emit(event: LethalEvent,
          battle: Battle,
          ctx: LethalContext,
          hp_dist: LethalDist) -> LethalDist:
    """指定イベントのハンドラをすべて実行し、更新された HP 分布を返す。"""
    if _check_hp(hp_dist, 0):
        return hp_dist
    handlers = _get_handlers(event, battle, ctx)
    hp_dist = _apply_handlers(battle, handlers, ctx, hp_dist)
    _update_hp(ctx.defender, hp_dist)
    return hp_dist


def _apply_damage(battle: Battle,
                  ctx: LethalContext,
                  hp_dist: LethalDist) -> tuple[LethalDist, ...]:
    """技ダメージを計算し、HP 分布を更新する。ダメージ分布も返す。"""
    damages = battle.calc_damages(
        ctx.attacker, ctx.defender, ctx.move, critical=ctx.critical
    )
    damage_dist = to_dist(damages)
    hp_dist = subtract_dist(hp_dist, damage_dist, minimum=0)
    _update_hp(ctx.defender, hp_dist)
    return hp_dist, damage_dist
