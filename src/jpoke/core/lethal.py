"""致死率計算ロジックを提供するモジュール。

技・アイテム・揮発状態などの効果をHP分布（StateDist）として扱い、
複数回攻撃後の確定数と致死率を求める。

分布そのものの演算（LethalState / StateDist / to_dist など）は
Battle に依存しないため `jpoke.utils.lethal_dist` に置く。
このモジュールは Battle/Pokemon/Move と結びついた計算ループを担う。

主要な型:
  LethalState  — HP・特性/道具の有効フラグをまとめた不変値（utils.lethal_dist）
  StateDist   — LethalState → 出現頻度 の辞書（確率分布、utils.lethal_dist）
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

from jpoke.types import Stat, AilmentName, LethalSubject
from jpoke.enums import LethalEvent
from jpoke.utils.lethal_dist import StateDist, State, to_dist, to_dist, subtract_dist


@dataclass(frozen=True)
class LethalHandler:
    """致死率計算専用のハンドラ定義。

    通常の Handler とは独立した仕組みで、StateDist を受け取り
    加工した StateDist を返す関数 func を保持する。

    Attributes:
        func: (battle, ctx, hp_dist) -> StateDist を返す関数。ダメージ分布の変更は `ctx.damage_dist` を更新すること。
        subject: 対象ロール（"attacker" / "defender" / "any"）
        priority: 同一イベント内での処理順（小さいほど先）
    """
    func: Callable[..., StateDist]
    subject: LethalSubject
    priority: int = 100


@dataclass
class LethalContext:
    """致死率計算中にハンドラへ渡すコンテキスト。"""
    attacker: Pokemon
    defender: Pokemon
    move: Move
    critical: bool = False
    n_attack: int = 1
    hit: int = 1
    # このヒットで与えたダメージ分布。ハンドラはこれを参照・更新して良い。
    damage_dist: StateDist = field(default_factory=lambda: to_dist(0))


class LethalResult:
    # TODO : 事後の加算ダメージ計算機能として、LethalResultどうしの和を取れるようにする
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
    hp_dist: StateDist
    damage_dist: StateDist
    # TODO : 将来的な拡張も見据えて、attacker/defenderの状態の記録方法を構造化する
    attacker_rank: dict[Stat, int] = field(default_factory=dict)
    defender_rank: dict[Stat, int] = field(default_factory=dict)
    attacker_ailment: AilmentName = ""
    defender_ailment: AilmentName = ""

    def update(self, hp_dist: StateDist, attacker: Pokemon, defender: Pokemon):
        self.hp_dist = hp_dist
        self.attacker_rank = attacker.rank.copy()
        self.defender_rank = defender.rank.copy()
        self.attacker_ailment = attacker.ailment.name
        self.defender_ailment = defender.ailment.name

    def _counter(self, dist: StateDist) -> dict[int, int]:
        """分布の HP値 → 出現頻度 の辞書を返す。ability_enabled / item_enabled は無視する。"""
        result: dict[int, int] = defaultdict(int)
        for state, freq in dist.items():
            result[state.value] += freq
        return dict(result)

    @property
    def hp_counter(self) -> dict[int, int]:
        """HP値 → 出現頻度 の辞書を返す。ability_enabled / item_enabled は無視する。"""
        return self._counter(self.hp_dist)

    @property
    def damage_counter(self) -> dict[int, int]:
        """ダメージ値 → 出現頻度 の辞書を返す。ability_enabled / item_enabled は無視する。"""
        return self._counter(self.damage_dist)

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


def fainted(dist: StateDist) -> bool:
    """分布内に HP=0 の状態が存在するか確認する。"""
    return any(state.value == 0 for state in dist)


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


def _lethal_loop(hp_dist: StateDist,
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
    ctx_list: list[tuple[int, LethalContext]] = [
        (n_hits, LethalContext(attacker, defender, move, critical=critical))
        for move, n_hits in move_list
    ]

    results = []
    for atk in range(1, max_attack + 1):
        for n_hits, ctx in ctx_list:
            ctx.n_attack = atk

            for hit in range(1, n_hits + 1):
                ctx.hit = hit
                # 技適用（ダメージ計算・ON_BEFORE_MOVE・ダメージ適用）
                hp_dist = _run_move(battle, ctx, hp_dist, secondary)

                # 結果を記録（ハンドラ適用前の最終ダメージ分布を反映）
                result = LethalResult(
                    n_attack=ctx.n_attack, move=ctx.move, hit=ctx.hit,
                    hp_dist=hp_dist, damage_dist=ctx.damage_dist
                )
                results.append(result)

                if fainted(hp_dist):
                    return results

            # ターン終了時のハンドラを適用（たべのこし回復など）
            hp_dist = _run_turn_end(battle, ctx, hp_dist)
            results[-1].hp_dist = hp_dist  # ターン終了後の HP 分布を反映
            if fainted(hp_dist):
                return results

    return results


def _run_move(battle: Battle,
              ctx: LethalContext,
              hp_dist: StateDist,
              secondary: bool) -> StateDist:
    """1回の技使用を計算する（LethalResult は生成しない）。

    この関数はダメージ計算、`ON_BEFORE_MOVE` の適用、ダメージの適用
    までを行い、更新された `hp_dist` を返す。ハンドラによる追加処理
    （`ON_HIT` / `ON_MOVE_SECONDARY`）および `LethalResult` の生成は呼び出し側で行う。
    """
    # 技ダメージを計算して ctx に格納する
    damages = battle.calc_damages(
        ctx.attacker, ctx.defender, ctx.move, critical=ctx.critical
    )
    ctx.damage_dist = to_dist(damages)

    # 技を適用する直前の処理（ハンドラは ctx.damage_dist を参照・更新する）
    hp_dist = _emit(LethalEvent.ON_BEFORE_MOVE, battle, ctx, hp_dist)

    # ダメージを適用する
    hp_dist = subtract_dist(hp_dist, ctx.damage_dist, minimum=0)
    _update_hp(ctx.defender, hp_dist)

    # ヒット時のハンドラを適用（きのみ回復など）
    hp_dist = _emit(LethalEvent.ON_HIT, battle, ctx, hp_dist)

    # 技の追加効果ハンドラを適用
    # TODO : move_secondaryは発動タイミングが技によって異なる場合があるため、イベントではなく技ハンドラ内の条件分岐で制御するようにする
    if secondary:
        hp_dist = _emit(LethalEvent.ON_MOVE_SECONDARY, battle, ctx, hp_dist)

    return hp_dist


def _run_turn_end(battle: Battle,
                  ctx: LethalContext,
                  hp_dist: StateDist) -> StateDist:
    return _emit(LethalEvent.ON_TURN_END, battle, ctx, hp_dist)


def _get_pokemon_handlers(event: LethalEvent,
                          mon: Pokemon,
                          subject: LethalSubject) -> list[LethalHandler]:
    """ポケモンの特性・道具・状態異常・揮発状態から該当ハンドラを取得する。"""
    candidates = [
        mon.ability.data.lethal_handlers.get(event),
        mon.item.data.lethal_handlers.get(event),
        mon.ailment.data.lethal_handlers.get(event),
    ]
    candidates += [v.data.lethal_handlers.get(event) for v in mon.volatiles.values()]
    return [h for h in candidates if h is not None and h.subject in {subject, "any"}]


def _get_global_field_handlers(event: LethalEvent, battle: Battle) -> list[LethalHandler]:
    """天候・地形・共通フィールドから該当ハンドラを取得する。"""
    fields = [battle.weather, battle.terrain] + \
        list(battle.global_manager.fields.values())
    candidates = [field.data.lethal_handlers.get(event) for field in fields if field.is_active]
    return [h for h in candidates if h is not None]


def _get_side_field_handlers(event: LethalEvent,
                             side: SideFieldManager,
                             subject: LethalSubject) -> list[LethalHandler]:
    """片側フィールド（ステルスロックなど）から該当ハンドラを取得する。"""
    fields = side.fields.values()
    candidates = [field.data.lethal_handlers.get(event) for field in fields if field.is_active]
    return [h for h in candidates if h is not None and h.subject in {subject, "any"}]


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
                    hp_dist: StateDist) -> StateDist:
    """ハンドラを順に適用する。HP=0 の状態が現れたら即打ち切り。

    ハンドラは `(battle, ctx, hp_dist) -> StateDist` を返す。ダメージ分布の変更は
    `ctx.damage_dist` を直接更新することで行う。
    """
    for h in handlers:
        if fainted(hp_dist):
            break
        hp_dist = h.func(battle, ctx, hp_dist)
    return hp_dist


def _update_hp(mon: Pokemon, hp_dist: StateDist):
    """分布内の最小 HP を mon.hp にセットする（後続ハンドラが参照するため）。"""
    mon.hp = min(state.value for state in hp_dist)


def _emit(event: LethalEvent,
          battle: Battle,
          ctx: LethalContext,
          hp_dist: StateDist) -> StateDist:
    """指定イベントのハンドラをすべて実行し、防御側のHPを更新して、更新後の hp_dist を返す。"""
    if fainted(hp_dist):
        return hp_dist
    handlers = _get_handlers(event, battle, ctx)
    hp_dist = _apply_handlers(battle, handlers, ctx, hp_dist)
    _update_hp(ctx.defender, hp_dist)
    return hp_dist
