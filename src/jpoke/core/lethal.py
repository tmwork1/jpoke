"""致死率計算ロジックを提供するモジュール。

技・アイテム・揮発状態などの効果をHP分布（StateDist）として扱い、
複数回攻撃後の確定数と致死率を求める。

分布そのものの演算（LethalState / StateDist / to_dist など）は
Battle に依存しないため `jpoke.utils.lethal_dist` に置く。
このモジュールは Battle/Pokemon/Move と結びついた計算ループを担う。

主要な型:
  LethalState  — HP・特性/道具の有効フラグをまとめた不変値（utils.lethal_dist）
  StateDist   — LethalState → 出現頻度 の辞書（確率分布、utils.lethal_dist）
  LethalHitResult — 1ヒット分の計算結果（HP分布・ダメージ分布・致死率など）
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle, SideFieldManager
    from jpoke.model import Pokemon, Move
    from jpoke.types import MoveName

from copy import deepcopy
from dataclasses import dataclass, field
from collections import defaultdict

from jpoke.types import LethalSubject
from jpoke.enums import LethalEvent
from jpoke.utils.lethal_dist import StateDist, to_dist, add_dist, subtract_dist


@dataclass(frozen=True)
class LethalHandler:
    """致死率計算専用のハンドラ定義。

    通常の Handler とは独立した仕組みで、StateDist を受け取り
    加工した StateDist を返す関数 func を保持する。

    Attributes:
        func: (battle, ctx, hp_dist) -> StateDist を返す関数。ダメージ分布の変更は `ctx.damage_dist` を更新すること。
        subject: 対象ロール（"attacker" / "defender"）
        priority: 同一イベント内での処理順（小さいほど先）
    """
    func: Callable[..., StateDist]
    subject: LethalSubject | None = None
    priority: int = 100


@dataclass
class LethalContext:
    """致死率計算中にハンドラへ渡すコンテキスト。"""
    attacker: Pokemon
    defender: Pokemon
    move: Move
    critical: bool = False
    move_secondary: bool = False
    attack_count: int = 1
    hit_count: int = 1
    # このヒットで与えたダメージ分布。ハンドラはこれを参照・更新して良い。
    damage_dist: StateDist = field(default_factory=lambda: to_dist(0))
    # HP満タン枝専用のダメージ分布。defender が full_hp_damage_modifier を持ち、
    # 満タン時と非満タン時でダメージが異なる場合のみ設定される（それ以外は None）。
    damage_dist_full: StateDist | None = None
    # 枝ごとの防御側HPからダメージを決める関数。固定ダメージ技・割合ダメージ技・
    # 一撃必殺技・みねうち等、枝のHP値に依存してダメージが変わる技で設定される。
    # 設定されている間は damage_dist / damage_dist_full ではなくこの関数が使われる。
    damage_from_hp: Callable[[int], int | list[int]] | None = None


@dataclass
class LethalHitResult:
    """1ヒットごとの致死率計算結果。

    Attributes:
        initial_hp: 防御側の初期状態のHP
        move: 使用した技
        attack_count: 何回目の攻撃か（1始まり）
        hit_count: 多段技の何ヒット目か（1始まり）
        hp_dist: ダメージ適用後のHP分布
        damage_dist: このヒットで与えたダメージの分布
    """
    initial_hp: int
    move: Move
    attack_count: int
    hit_count: int
    hp_dist: StateDist
    damage_dist: StateDist

    def __add__(self, other: LethalHitResult) -> LethalHitResult:
        """2つのLethalHitResultのHP分布・ダメージ分布を合成する。

        hp_dist: other.initial_hpからother.hp_distを差し引いた分布を加算されるダメージとみなし、self.hp_distから引く。
        damage_dist: self.damage_distとother.damage_distを加算する。
        """
        if not isinstance(other, LethalHitResult):
            return NotImplemented

        hp_dist = subtract_dist(self.hp_dist, subtract_dist(
            other.initial_hp, other.hp_dist))
        damage_dist = add_dist(self.damage_dist, other.damage_dist)
        return LethalHitResult(
            initial_hp=self.initial_hp,
            move=other.move,
            attack_count=self.attack_count + other.attack_count,
            hit_count=1,
            hp_dist=hp_dist,
            damage_dist=damage_dist,
        )

    def _counter(self, dist: StateDist) -> dict[int, int]:
        """分布の HP値 → 出現頻度 の辞書を返す。ability_enabled / item_enabled は無視する。"""
        result: dict[int, int] = defaultdict(int)
        for state, freq in dist.items():
            result[state.value] += freq
        return dict(result)

    @property
    def hp_counter(self) -> dict[int, int]:
        """HP値 → 出現頻度 の辞書を返す。ability_enabled / item_enabled は無視する。"""
        return dict(sorted(self._counter(self.hp_dist).items()))

    @property
    def damage_counter(self) -> dict[int, int]:
        """ダメージ値 → 出現頻度 の辞書を返す。ability_enabled / item_enabled は無視する。"""
        return dict(sorted(self._counter(self.damage_dist).items()))

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


@dataclass
class LethalMonitor:
    """テスト・デバッグ専用: calc_lethal 内部で使われる（deepcopyされた）攻撃側・
    防御側の Pokemon への参照を保持する。呼び出し前に空のインスタンスを渡すと、
    呼び出し後に attacker/defender が設定され、ランク補正・状態異常などの
    内部状態を外部から確認できる。本番の対戦進行やロジックでは使わないこと
    （calc_lethal は本来 battle を deepcopy して副作用を外部に漏らさない設計であり、
    この monitor はテストの検証のためだけにその deepcopy 内部への参照を意図的に
    漏らす後方口である）。

    Attributes:
        attacker: calc_lethal 呼び出し完了時点の攻撃側 Pokemon（deepcopy後の実体）
        defender: calc_lethal 呼び出し完了時点の防御側 Pokemon（deepcopy後の実体）
    """
    attacker: Pokemon | None = None
    defender: Pokemon | None = None


def calc_lethal(battle: Battle,
                attacker: Pokemon,
                moves: MoveName | Move | tuple[MoveName | Move, int]
                | list[MoveName | Move | tuple[MoveName | Move, int]],
                critical: bool,
                move_secondary: bool,
                max_attack: int,
                resume_from: LethalHitResult | None = None,
                monitor: LethalMonitor | None = None) -> list[LethalHitResult]:
    """致死率計算のエントリーポイント。

    Args:
        battle: 現在のバトル状態（deepcopy して使用するため破壊しない）
        attacker: 攻撃側ポケモン
        moves: 技（単体 / (技, ヒット数) / リスト）。技名の文字列を渡した場合は
            内部で `Move(name)` に正規化される
        critical: 急所計算をするか
        move_secondary: 追加効果ハンドラを適用するか
        max_attack: 最大攻撃回数
        resume_from: 指定した場合、フルHPからの新規計算ではなく、この
            `LethalHitResult`（通常は直前の `calc_lethal()` 呼び出しの
            `results[-1]`）が表す状態から計算を再開する。引き継がれるのは
            チェーン全体の起点HP（`initial_hp`）、`resume_from` 終了時点の
            HP分布（`hp_dist`、分岐ごとの特性/道具消費フラグを含む）、
            `attack_count`（後続の攻撃回数に加算されるオフセットとして使う）
            の3つのみ。**攻撃側・防御側のランク補正（`boosts`）・状態異常
            （`ailment`）・揮発性状態（バインド・しおづけ・かいふくふうじ・
            こんらん・たくわえる等）はいずれも引き継がれない**（既知の制約）。
            `None`（デフォルト）の場合は従来通りフルHPから新規に計算する。
        monitor: テスト・デバッグ専用。通常の利用では指定しないこと。指定すると
            計算に使う（deepcopyされた）攻撃側・防御側 Pokemon への参照を
            `monitor.attacker` / `monitor.defender` に設定する。詳細は
            `LethalMonitor` のdocstring参照。

    Returns:
        各ヒット後の LethalHitResult のリスト（確定数が出た時点で打ち切り）。
        `resume_from` を指定した場合でも、返るのは新規に計算したヒット分のみ
        （`resume_from` 自体やそれ以前の履歴は含まない）。呼び出し側で必要なら
        `resume_from` の元リストと連結すればよい。
    """
    # 攻撃側のインデックスを取得
    attacker_index = battle._get_player_index(attacker)

    # deepcopy してバトル状態を壊さずに計算する
    battle = deepcopy(battle)
    attacker = battle.actives[attacker_index]
    defender = battle.foe(attacker)

    if monitor is not None:
        monitor.attacker = attacker
        monitor.defender = defender

    if resume_from is not None:
        initial_hp = resume_from.initial_hp
        hp_dist = resume_from.hp_dist
        attack_offset = resume_from.attack_count

        # _update_hp が通常行っている同期をループ開始前に前倒しで行う
        # （ループ内の最初のイベントで ctx.defender.hp を参照するハンドラのために必要）。
        defender.hp = min(state.value for state in hp_dist)
    else:
        initial_hp = defender.hp
        hp_dist = to_dist(
            defender.hp,
            ability_enabled=defender.ability.enabled,
            item_enabled=defender.item.enabled
        )
        attack_offset = 0

    move_list = _generate_move_list(moves)

    return _lethal_loop(
        initial_hp, hp_dist, battle, attacker, defender, move_list,
        critical, move_secondary, max_attack, attack_offset=attack_offset,
    )


def _generate_move_list(
    moves: MoveName | Move | tuple[MoveName | Move, int]
        | list[MoveName | Move | tuple[MoveName | Move, int]],
) -> list[tuple[Move, int]]:
    """moves 引数を (技, ヒット数) のリストに正規化する。技名の文字列は `Move` に変換する。"""
    def to_move(x: MoveName | Move) -> Move:
        if isinstance(x, str):
            # jpoke.model はモジュールトップレベルでは import しない。
            # jpoke.data.ability 等が jpoke.core.lethal（本モジュール）を import しているため、
            # トップレベルで from jpoke.model import Move すると循環importになる。
            from jpoke.model import Move
            return Move(x)
        return x

    if isinstance(moves, list):
        result = []
        for x in moves:
            if isinstance(x, tuple):
                move, n_hit = x
                result.append((to_move(move), n_hit))
            else:
                result.append((to_move(x), 1))
        return result
    elif isinstance(moves, tuple):
        move, n_hit = moves
        return [(to_move(move), n_hit)]
    else:
        return [(to_move(moves), 1)]


def _lethal_loop(initial_hp: int,
                 hp_dist: StateDist,
                 battle: Battle,
                 attacker: Pokemon,
                 defender: Pokemon,
                 move_list: list[tuple[Move, int]],
                 critical: bool,
                 move_secondary: bool,
                 max_attack: int,
                 attack_offset: int = 0) -> list[LethalHitResult]:
    """致死率計算のメインループ。

    max_attack 回分、move_list の技を順に使用し、各ヒット後の LethalHitResult を返す。
    いずれかの時点で HP=0 の状態が現れたら途中で打ち切る。

    Args:
        attack_offset: `resume_from` 指定時、`ctx.attack_count` に加算するオフセット
            （`resume_from.attack_count`）。`hit_count` には影響しない
            （各ラウンドで1から数え直す既存の挙動のまま）。
    """
    # move ごとに LethalContext を作成しておく（ループ内で毎回作る必要がないため）
    ctx_list: list[tuple[int, LethalContext]] = [
        (n_hits, LethalContext(attacker, defender, move,
         critical=critical, move_secondary=move_secondary))
        for move, n_hits in move_list
    ]

    results = []
    for atk in range(1, max_attack + 1):
        for n_hits, ctx in ctx_list:
            ctx.attack_count = atk + attack_offset
            # ON_EVERY_EVENT ハンドラは同じ ctx では変化しないため、1回だけ取得する
            every_event_handlers = _get_handlers(
                LethalEvent.ON_EVERY_EVENT, battle, ctx)

            hp_dist = _before_move(battle, ctx, hp_dist, every_event_handlers)

            attacker_fainted_mid_round = False
            for hit in range(1, n_hits + 1):
                ctx.hit_count = hit
                # 技の適用
                hp_dist = _run_move(battle, ctx, hp_dist, every_event_handlers)

                result = LethalHitResult(
                    initial_hp=initial_hp,
                    move=ctx.move,
                    attack_count=ctx.attack_count,
                    hit_count=ctx.hit_count,
                    hp_dist=hp_dist,
                    damage_dist=ctx.damage_dist,
                )
                results.append(result)

                if fainted(hp_dist):
                    return results

                # いのちがけ等、攻撃側自身がひんしになる技を使った場合はそこで打ち切る。
                if ctx.attacker.fainted:
                    attacker_fainted_mid_round = True
                    break

            if attacker_fainted_mid_round:
                # ctx_list に後続の技（例: [("いのちがけ", 1), ("じしん", 1)] の
                # じしん）が残っていても、ひんしになった攻撃側はもう使用できないため、
                # 今ラウンドの残りの ctx_list 要素とターン終了処理をスキップする
                # （防御側がひんしになった場合に turn_end をスキップするのと同じ扱い）。
                # ただし calc_lethal 呼び出し自体は打ち切らない: 単体の技を
                # 繰り返し指定するケース（例: moves=Move("いのちがけ") を
                # max_attack=2 で呼ぶ）では、2回目以降は hp_cost=0 により
                # 自然にダメージ0になるだけで、その結果を記録し続けるのが
                # 既存の想定挙動のため、次の atk ラウンドへは進む。
                break

            # ターン終了時のハンドラを適用（たべのこし回復など）
            hp_dist = _run_turn_end(battle, ctx, hp_dist, every_event_handlers)
            results[-1].hp_dist = hp_dist  # ターン終了後の HP 分布を反映
            if fainted(hp_dist):
                return results

    return results


def _before_move(battle: Battle,
                 ctx: LethalContext,
                 hp_dist: StateDist,
                 every_event_handlers: list[LethalHandler]) -> StateDist:
    """ON_BEFORE_MOVE イベントのハンドラを適用する。"""
    return _emit(LethalEvent.ON_BEFORE_MOVE, battle, ctx, hp_dist, every_event_handlers)


def _calc_damage_dist(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> None:
    """技ダメージを計算し、ctx.damage_dist / ctx.damage_dist_full に格納する。

    defender が "full_hp_damage_modifier" フラグを持つ特性（マルチスケイル等）を持ち、
    hp_dist に満タン枝が存在する場合のみ、calc_damages を2回呼んで満タン枝用と
    非満タン枝(ベースライン)用のダメージ分布を別々に求める。
    非満タン枝用は特性を一時的に無効化することで、defender.hp の値に関係なく
    確実に特性の効果を除いた値を得る。
    """
    # 固定ダメージ技（ナイトヘッド・いかりのまえば・一撃必殺技・みねうち等）が
    # ON_BEFORE_HIT で新たに設定するフィールドのため、他のヒットの値を引き継がない
    # よう damage_dist_full と同様に毎ヒットリセットする（技ごとのハンドラが
    # 設定しない限り None のまま＝通常のダメージ計算経路が使われる）。
    ctx.damage_from_hp = None

    max_hp = ctx.defender.max_hp
    needs_full_hp_split = (
        ctx.defender.ability.has_flag("full_hp_damage_modifier")
        and any(state.value == max_hp for state in hp_dist)
    )

    if not needs_full_hp_split:
        damages = battle.calc_damages(
            ctx.attacker, ctx.defender, ctx.move, critical=ctx.critical)
        ctx.damage_dist = to_dist(damages)
        ctx.damage_dist_full = None
        return

    saved_hp = ctx.defender.hp
    ctx.defender.hp = max_hp
    full_damages = battle.calc_damages(
        ctx.attacker, ctx.defender, ctx.move, critical=ctx.critical)
    ctx.defender.hp = saved_hp

    ctx.defender.ability.add_disable_reason("lethal_calculation")
    try:
        damages = battle.calc_damages(
            ctx.attacker, ctx.defender, ctx.move, critical=ctx.critical)
    finally:
        ctx.defender.ability.remove_disable_reason("lethal_calculation")

    ctx.damage_dist = to_dist(damages)
    ctx.damage_dist_full = to_dist(
        full_damages) if full_damages != damages else None


def _apply_damage_by_branch(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """ctx.damage_from_hp が設定されている場合のダメージ適用（枝ごとのHPに依存するダメージ）。

    いかりのまえば・がむしゃら・一撃必殺技・みねうち等は、そのヒットを受ける直前の
    防御側HP自体によってダメージが変わるため、hp_dist 全体に一律の damage_dist を
    適用できない。枝（State）ごとに damage_from_hp(state.value) を呼んでその枝専用の
    ダメージ分布を求め、その枝だけに subtract_dist(..., minimum=0) を適用する。

    HP満タンの枝は既存の full_hp 経路と同様に ON_APPLY_DAMAGE ハンドラ
    （がんじょう・きあいのタスキ等のHP1耐え）を通す。一撃必殺技はダメージ＝満タンHP
    そのものになるため、この経路を通ることで「がんじょう・きあいのタスキが一撃必殺技を
    防ぐ」挙動が自然に再現される。

    damage_dist_full（マルチスケイル等の満タン専用ダメージ補正）はこの経路では参照しない。
    固定ダメージ技は base_power が None/0 のため _calc_damage_dist の
    needs_full_hp_split 分岐（calc_damages を2回呼ぶ経路）に到達せず、
    damage_dist_full は常に None のまま（＝両者は実質排他）。みねうちのように
    base_power を持つ通常攻撃技であっても、_calc_damage_dist の時点で必要なダメージ補正
    （マルチスケイル等）は既に damage_dist に反映済みであり、ここではその damage_dist
    自体を枝ごとにHP-1でキャップする関数として使うだけなので問題ない。

    処理後、LethalHitResult 等の記録用に ctx.damage_dist を「実際に適用されたダメージの
    周辺分布」（各枝の出現頻度で重み付けして合算したもの）に更新する。
    """
    max_hp = ctx.defender.max_hp
    full_handlers = _get_handlers(LethalEvent.ON_APPLY_DAMAGE, battle, ctx)

    result: StateDist = defaultdict(int)
    recorded: StateDist = defaultdict(int)

    for state, freq in hp_dist.items():
        branch_dmg = to_dist(ctx.damage_from_hp(state.value))
        subtracted = subtract_dist({state: freq}, branch_dmg, minimum=0)

        if state.value == max_hp:
            for h in full_handlers:
                subtracted = h.func(battle, ctx, subtracted)

        for s, f in subtracted.items():
            result[s] += f
        for d, f in branch_dmg.items():
            recorded[d] += f * freq

    ctx.damage_dist = dict(recorded)
    return dict(result)


def _apply_damage(battle: Battle, ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """満タン枝と非満タン枝でダメージ適用を分ける。

    ctx.damage_from_hp が設定されている場合（固定ダメージ技・割合ダメージ技・
    一撃必殺技・みねうち等、枝のHP値に依存してダメージが変わる技）は
    _apply_damage_by_branch に処理を委譲する。

    それ以外は満タン枝には damage_dist_full（未設定なら damage_dist）を適用してから
    ON_APPLY_DAMAGE ハンドラ（がんじょう・きあいのタスキ等のHP1耐え）を通す。
    非満タン枝には damage_dist をそのまま適用する。
    該当ハンドラが無ければ通常の subtract_dist(hp_dist, ctx.damage_dist) と完全に同じ結果になる。

    処理後、LethalHitResult 等の記録用に ctx.damage_dist を「実際に適用されたダメージ分布」
    に更新する（満タン枝のみなら damage_dist_full、両方混在するなら合算）。
    """
    if ctx.damage_from_hp is not None:
        return _apply_damage_by_branch(battle, ctx, hp_dist)

    max_hp = ctx.defender.max_hp
    full_states = {s: f for s, f in hp_dist.items() if s.value == max_hp}
    other_states={s: f for s, f in hp_dist.items() if s.value != max_hp}

    baseline_dmg=ctx.damage_dist
    full_dmg=ctx.damage_dist_full if ctx.damage_dist_full is not None else baseline_dmg

    result: StateDist = defaultdict(int)
    if full_states:
        full_result = subtract_dist(full_states, full_dmg, minimum=0)
        for h in _get_handlers(LethalEvent.ON_APPLY_DAMAGE, battle, ctx):
            full_result = h.func(battle, ctx, full_result)
        for s, f in full_result.items():
            result[s] += f
    if other_states:
        for s, f in subtract_dist(other_states, baseline_dmg, minimum=0).items():
            result[s] += f

    if full_states and other_states:
        merged: StateDist = defaultdict(int)
        for s, f in full_dmg.items():
            merged[s] += f
        for s, f in baseline_dmg.items():
            merged[s] += f
        ctx.damage_dist = dict(merged)
    elif full_states:
        ctx.damage_dist = full_dmg

    return dict(result)


def _run_move(battle: Battle,
              ctx: LethalContext,
              hp_dist: StateDist,
              every_event_handlers: list[LethalHandler]) -> StateDist:
    """1回の技使用を計算する。

    この関数はダメージ計算・ON_BEFORE_MOVE・ダメージ適用・ON_HITを順に実行する。
    """
    # 技ダメージを計算して ctx に格納する
    _calc_damage_dist(battle, ctx, hp_dist)

    # 技を適用する直前の処理（ハンドラは ctx.damage_dist を参照・更新する）
    hp_dist = _emit(LethalEvent.ON_BEFORE_HIT, battle,
                    ctx, hp_dist, every_event_handlers)

    # ダメージを適用する（満タン枝・非満タン枝を分けて処理する）
    hp_dist = _apply_damage(battle, ctx, hp_dist)
    hp_dist = _update_hp(ctx, hp_dist)

    # ヒット時のハンドラを適用（きのみ回復など）
    hp_dist = _emit(LethalEvent.ON_HIT, battle, ctx,
                    hp_dist, every_event_handlers)

    return hp_dist


def _run_turn_end(battle: Battle,
                  ctx: LethalContext,
                  hp_dist: StateDist,
                  every_event_handlers: list[LethalHandler]) -> StateDist:
    return _emit(LethalEvent.ON_TURN_END, battle, ctx, hp_dist, every_event_handlers)


def _get_pokemon_handlers(event: LethalEvent,
                          mon: Pokemon,
                          subject: LethalSubject) -> list[LethalHandler]:
    """ポケモンの特性・道具・状態異常・揮発状態から該当ハンドラを取得する。"""
    candidates = [
        mon.ability.data.lethal_handlers.get(event),
        mon.item.data.lethal_handlers.get(event),
        mon.ailment.data.lethal_handlers.get(event),
    ]
    candidates += [v.data.lethal_handlers.get(event)
                   for v in mon.volatiles.values()]
    return [h for h in candidates if h is not None and h.subject in {subject, None}]


def _get_move_handlers(event: LethalEvent, ctx: LethalContext) -> list[LethalHandler]:
    """技のハンドラを取得する。"""
    move_handler = ctx.move.data.lethal_handlers.get(event)
    return [move_handler] if move_handler else []


def _get_global_field_handlers(event: LethalEvent, battle: Battle) -> list[LethalHandler]:
    """天候・地形・共通フィールドから該当ハンドラを取得する。"""
    fields = [battle.weather, battle.terrain] + \
        list(battle.global_manager.fields.values())
    candidates = [field.data.lethal_handlers.get(
        event) for field in fields if field.is_active]
    return [h for h in candidates if h is not None]


def _get_side_field_handlers(event: LethalEvent,
                             side: SideFieldManager,
                             subject: LethalSubject) -> list[LethalHandler]:
    """片側フィールド（ステルスロックなど）から該当ハンドラを取得する。"""
    fields = side.fields.values()
    candidates = [field.data.lethal_handlers.get(
        event) for field in fields if field.is_active]
    return [h for h in candidates if h is not None and h.subject in {subject, None}]


def _get_handlers(event: LethalEvent,
                  battle: Battle,
                  ctx: LethalContext) -> list[LethalHandler]:
    """イベントに対応する全ハンドラを priority 順で返す。"""
    handlers = []
    handlers += _get_pokemon_handlers(event, ctx.attacker, "attacker")
    handlers += _get_pokemon_handlers(event, ctx.defender, "defender")
    handlers += _get_move_handlers(event, ctx)
    handlers += _get_global_field_handlers(event, battle)
    handlers += _get_side_field_handlers(event,
                                         battle.get_side(ctx.attacker), "attacker")
    handlers += _get_side_field_handlers(event,
                                         battle.get_side(ctx.defender), "defender")
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


def _update_hp(ctx: LethalContext, hp_dist: StateDist) -> StateDist:
    """分布内の最小 HP を防御側の hp にセットする（後続ハンドラが参照するため）。"""
    ctx.defender.hp = min(state.value for state in hp_dist)
    return hp_dist


def _emit(event: LethalEvent,
          battle: Battle,
          ctx: LethalContext,
          hp_dist: StateDist,
          every_event_handlers: list[LethalHandler]) -> StateDist:
    """指定イベントのハンドラをすべて実行し、防御側のHPを更新して、更新後の hp_dist を返す。

    Args:
        every_event_handlers: 呼び出し元で事前取得した ON_EVERY_EVENT ハンドラ。
    """
    if fainted(hp_dist):
        return hp_dist

    handlers = _get_handlers(event, battle, ctx)
    hp_dist = _apply_handlers(battle, handlers, ctx, hp_dist)
    hp_dist = _update_hp(ctx, hp_dist)

    hp_dist = _apply_handlers(battle, every_event_handlers, ctx, hp_dist)
    hp_dist = _update_hp(ctx, hp_dist)

    return hp_dist
