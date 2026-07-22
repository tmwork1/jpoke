"""アイテムハンドラーモジュール。

Note:
    このモジュール内の関数定義は五十音順に配置されています。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable
if TYPE_CHECKING:
    from jpoke.core import Battle, EventContext, AttackContext
    from jpoke.model import Pokemon, Move

from jpoke.types import RoleSpec, Stat, Type, MoveCategory, \
    AilmentName, WeatherName, TerrainName, SideFieldName, ItemName
from jpoke.utils.math import apply_fixed_modifier, round_half_down
from jpoke.enums import Event, Interrupt, LogCode, Command
from jpoke.core.handler import HandlerReturn, Handler
from jpoke.core.log_payload import ItemPayload, StatChangePayload
from jpoke.data.type_chart import TYPE_MODIFIER
from jpoke.data.megaevol import MEGA_STONES
from jpoke.data.pokedex import POKEDEX
from . import ability_paradox as paradox

# 何らかのポケモンの進化前として登録されている = 進化先が存在する（未進化）ポケモン名の集合
_HAS_EVOLUTION: frozenset[str] = frozenset(
    d.pre_evolution for d in POKEDEX.values() if d.pre_evolution
)

# メルタン: メルメタルへの進化手段（アメ400個）が通常の進化データと異なるため、
# 内部的には「進化の余地がある」と判定されず、しんかのきせきの効果を得られない例外。
_EVIOLITE_NO_EFFECT: frozenset[str] = frozenset({"メルタン"})

class ItemHandler(Handler):
    def __init__(self,
                 func: Callable,
                 subject_spec: RoleSpec,
                 priority: int = 100,
                 once: bool = False,
                 ignored_disable_reasons: frozenset[str] = frozenset(),
                 allow_fainted_subject: bool = False) -> None:
        super().__init__(
            func=func,
            source="item",
            subject_spec=subject_spec,
            priority=priority,
            once=once,
            ignored_disable_reasons=ignored_disable_reasons,
            allow_fainted_subject=allow_fainted_subject,
        )

def announce_item_triggered(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    _announce_item_triggered(battle, ctx.source)
    return HandlerReturn(value=value)

def _announce_item_triggered(battle: Battle, mon: Pokemon) -> None:
    mon.item.revealed = True
    battle.add_event_log(
        mon, LogCode.ITEM_TRIGGERED,
        payload=ItemPayload(item=mon.item.name)
    )

def _announce_and_consume_item(battle: Battle, mon: Pokemon, *, track_loss: bool = True) -> None:
    _announce_item_triggered(battle, mon)
    battle.item_manager.consume_item(mon, track_loss=track_loss)

def _reset_negative_ranks(battle: Battle, mon: Pokemon, reason: str) -> bool:
    """能力ランクがマイナスのステータスを全て0に戻す（しろいハーブ・くろいきり等で使用）。

    Event.ON_MODIFY_STAT を経由せず直接ランクを書き換えることで、この復元自体が
    他の特性・アイテム（かちき・びんじょう等）を再度反応させないようにする。

    Args:
        battle: バトルインスタンス
        mon: 対象のポケモン
        reason: ログ記録用の理由文字列

    Returns:
        いずれかのランクが変化した場合True
    """
    changed = {s: -v for s, v in mon.boosts.items() if v < 0}
    if not changed:
        return False
    for s in changed:
        mon.boosts[s] = 0
    battle.add_event_log(
        mon, LogCode.STAT_CHANGED,
        payload=StatChangePayload(stats=changed, display_reason=reason),
    )
    return True

def mega_modify_command_options(battle: Battle, ctx: EventContext, value: list[Command]) -> HandlerReturn:
    """メガストーン: メガシンカコマンドを追加する。"""
    mon = ctx.source
    if not battle.option.mega_evolution or not mon.can_megaevolve():
        return HandlerReturn(value=value)

    for cmd in value:
        if cmd.is_regular_move:
            value.append(Command.get_megaevol_command(cmd.index))

    return HandlerReturn(value=value)

def mega_prevent_item_change(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """メガストーン: 対応する種族（メガシンカ前後どちらも含む）が持っている間は
    トリック・すりかえ・ほしがる・どろぼう・特性マジシャン・わるいてぐせ・
    ふしょくガス・はたきおとすによる奪取/交換/除去を防ぐ。
    対応する種族以外が持っている場合は通常通り奪取/交換/除去できる。
    """
    mon = ctx.target
    if mon is None:
        return HandlerReturn(value=value)
    forms = MEGA_STONES.get(mon.item.name)
    if forms is not None and mon.name in forms:
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)

def _modify_power_by_type(move: Move,
                          value: Any,
                          type_: Type,
                          modifier: int) -> HandlerReturn:
    if move.type == type_:
        value = apply_fixed_modifier(value, modifier)
    return HandlerReturn(value=value)

def _modify_super_effective_damage(battle: Battle,
                                   ctx: AttackContext,
                                   value: Any,
                                   type_: Type,
                                   modifier: float,
                                   super_effective_only: bool = True) -> HandlerReturn:
    """タイプ半減きのみの共通処理（ON_CALC_DAMAGE_MODIFIER）。

    super_effective_only=True  : 17種の通常タイプ半減きのみ。効果バツグン時のみ発動する。
    super_effective_only=False : ホズのみ用。ノーマルタイプ技全般で発動する
                                 （ノーマルは抜群にならないため super_effective 判定を省く）。
    """
    if ctx.move.type != type_:
        return HandlerReturn(value=value)
    # 相手のきんちょうかん・じんばいったいの影響下では発動しない
    if battle.query.is_nervous(ctx.defender):
        return HandlerReturn(value=value)
    def_type_modifier = battle.damage_calculator.calc_def_type_modifier(ctx)
    if super_effective_only:
        triggers = def_type_modifier > 4096
    else:
        triggers = def_type_modifier > 0
    if triggers:
        # じゅくせい所持時は被ダメージが1/4になる。modifier(1/2)を2回掛けるのではなく、
        # 1回の乗算で1/4を算出する（一次情報: 端数処理が異なるため）。
        applied_modifier = modifier * modifier if is_ripen(ctx.defender) else modifier
        value = int(value * applied_modifier)
        _announce_and_consume_item(battle, ctx.defender)
    return HandlerReturn(value=value)

def _resolve_field_count(value: list,
                         *fields: WeatherName | TerrainName | SideFieldName,
                         additonal_count: int) -> HandlerReturn:
    """指定場状態と一致するとき継続ターン数に加算する。"""
    if value[0] in fields:
        value[1] += additonal_count
    return HandlerReturn(value=value)

def _terrain_seed_boost(battle: Battle, ctx: EventContext, value: Any,
                        terrain: TerrainName, stat: Stat, item_name: ItemName) -> HandlerReturn:
    """フィールドシード系: 対応フィールド展開時にランク+1し、自身を消費する。

    Event.ON_SWITCH_IN / Event.ON_FIELD_CHANGE / Event.ON_ITEM_ENABLED の
    3つに登録されているため、例えばエレキメイカー・ハドロンエンジン等
    「登場と同時にフィールドを展開する特性」を自身が持つ場合、登場時の
    ON_SWITCH_IN処理中にその特性がネストしてON_FIELD_CHANGEを発火させ、
    本ハンドラが既に一度発動・アイテムを消費した後、同一ON_SWITCH_IN発火の
    中でハンドラ一覧のスナップショットに残っていた自身のON_SWITCH_IN登録が
    続けて実行されてしまう（二重発動）。そのため、発動条件の判定前に
    このアイテムをまだ保持しているか（消費済みでないか）を確認する。
    """
    mon = ctx.source
    assert mon is not None
    if not mon.has_item(item_name):
        return HandlerReturn(value=value)
    if battle.terrain.name == terrain:
        changes = battle.modify_stats(mon, {stat: +1})
        if changes:  # すでにランクが最大の場合は不発・消費しない
            _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)

def _apply_contact_item_chip(battle: Battle,
                             ctx: AttackContext,
                             *,
                             ratio: float) -> bool:
    """接触被弾時アイテムの固定割合ダメージを攻撃者に適用する。

    Returns:
        bool: ダメージが適用された場合True
    """
    if battle.query.is_contact_reaction(ctx):
        v = battle.modify_hp(ctx.attacker, r=-ratio)
        if v:
            # ダメおし判定用: ゴツゴツメット等によるダメージも「そのターンに攻撃を
            # 受けた」扱いにする（一次情報: .internal/wiki/moves/ダメおし.html 技の仕様節）。
            ctx.attacker.hits_taken += 1
        return bool(v)
    return False

def _gluttony_denominator(mon: Pokemon, denominator: int) -> int:
    """くいしんぼう: 残りHP1/4以下(denominator=4)で発動するきのみの発動条件を
    残りHP1/2以下(denominator=2)に緩和する。

    もとから最大HPの1/2以下で発動するきのみ（オボンのみ等、denominator=2）には
    効果が無いため、denominator=4のときのみ変換する。
    """
    if denominator == 4 and mon.ability.name == "くいしんぼう":
        return 2
    return denominator

def is_ripen(mon: Pokemon) -> bool:
    """じゅくせい: 効果を受け取る本人（きのみを消費するポケモン）の特性を判定する。"""
    return mon.ability.name == "じゅくせい"

def berry_heal_amount(mon: Pokemon, *, r: float | None = None, v: int | None = None) -> int:
    """じゅくせい: きのみによる回復量を計算する。

    最大HP割合(r)指定の場合は端数を切り捨てた後の値をじゅくせい所持時に2倍にする
    （切り捨て前の割合を2倍にしてから丸めるわけではない）。固定値(v)指定の場合は
    そのまま2倍にする。
    """
    if r is not None:
        amount = max(1, int(mon.max_hp * r))
    else:
        assert v is not None
        amount = v
    if is_ripen(mon):
        amount *= 2
    return amount

def _heal_berry(battle: Battle,
                ctx: EventContext,
                value: Any,
                *,
                denominator: int,
                heal_r: float | None = None,
                heal_v: int | None = None,
                confuse_natures: tuple[str, ...] | None = None) -> HandlerReturn:
    mon = ctx.target
    assert mon is not None
    denominator = _gluttony_denominator(mon, denominator)
    # value >= mon.max_hp はほおばる等による強制発動（HP閾値チェックを無視する）
    forced = value >= mon.max_hp
    if not forced:
        # こんらんの自傷ダメージでは発動しない（第五世代以降の仕様）
        if ctx.hp_change_reason == "self_attack":
            return HandlerReturn(value=value)
        # 相手のきんちょうかん・じんばいったいの影響下では発動しない
        if battle.query.is_nervous(mon):
            return HandlerReturn(value=value)
    if forced or mon.hp * denominator <= mon.max_hp:
        healed = battle.modify_hp(mon, v=berry_heal_amount(mon, r=heal_r, v=heal_v))
        # 通常発動（HP閾値到達）時、かいふくふうじ等で回復が完全に無効化された場合は
        # 発動条件を満たしていないとみなし消費しない。一方、なげつける・おちゃかい・
        # ほおばる等による強制発動では、既に満タンHPで回復量が0であっても
        # 味覚（アイテム消費・こんらん判定）は独立して発生する。
        if forced or healed:
            _announce_and_consume_item(battle, mon)
            # 嫌いな味（性格でぼうぎょ等が下がりにくい/上がりにくい組）のときこんらんする
            if confuse_natures is not None and mon.nature in confuse_natures:
                battle.volatile_manager.apply_confusion(mon, source=mon)
    return HandlerReturn(value=value)

def _apply_ailment_from_item(battle: Battle, ctx: EventContext, value: Any, ailment: AilmentName) -> HandlerReturn:
    mon = ctx.source
    assert mon is not None
    if battle.ailment_manager.apply(mon, ailment, source=mon):
        _announce_item_triggered(battle, mon)
    return HandlerReturn(value=value)

def _cure_ailment_berry(battle: Battle,
                        ctx: EventContext,
                        value: Any,
                        *ailment_names: str) -> HandlerReturn:
    mon = ctx.source
    assert mon is not None
    condition = mon.ailment.name in ailment_names if ailment_names else mon.ailment.is_active
    if condition and battle.ailment_manager.remove(mon):
        _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)

def _cure_ailment_berry_on_apply(battle: Battle,
                                 ctx: EventContext,
                                 value: Any,
                                 *ailment_names: str) -> HandlerReturn:
    """ON_APPLY_AILMENT用: 状態異常付与直後に治療して消費する共通処理。"""
    mon = ctx.target
    assert mon is not None
    if not ailment_names or value in ailment_names:
        if battle.ailment_manager.remove(mon):
            _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)

def _cure_ailment_and_confusion(battle: Battle, mon: Pokemon) -> bool:
    """状態異常・こんらんの両方をチェックし、該当するものをまとめて回復する（ラムのみ用）。

    発動時点で状態異常とこんらんが重複していた場合、両方を同時に回復する。

    Returns:
        いずれかを回復した場合True
    """
    cured_ailment = mon.ailment.is_active and battle.ailment_manager.remove(mon)
    cured_confusion = mon.has_volatile("こんらん") and battle.volatile_manager.remove(mon, "こんらん")
    return bool(cured_ailment or cured_confusion)

def _boost_on_quarter_hp(battle: Battle,
                         ctx: EventContext,
                         value: Any,
                         stat: Stat,
                         amount: int) -> HandlerReturn:
    """1/4HP以下になった瞬間に能力を上昇させる共通処理。

    value >= mon.max_hp はほおばる等による強制発動（HP閾値チェックを無視する）。
    くいしんぼう所持時は1/2HP以下に緩和される。
    """
    mon = ctx.target
    assert mon is not None
    forced = value >= mon.max_hp
    denominator = _gluttony_denominator(mon, 4)
    if not forced:
        # こんらんの自傷ダメージでは発動しない（第五世代以降の仕様）
        if ctx.hp_change_reason == "self_attack":
            return HandlerReturn(value=value)
        # 相手のきんちょうかん・じんばいったいの影響下では発動しない
        if battle.query.is_nervous(mon):
            return HandlerReturn(value=value)
        if mon.hp * denominator > mon.max_hp:
            return HandlerReturn(value=value)
    # じゅくせい所持時はランク上昇量が2倍になる
    boost = amount * 2 if is_ripen(mon) else amount
    if battle.modify_stats(mon, {stat: boost}):  # すでにランクが最大の場合は不発・消費しない
        _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)

def _boost_on_attack_category(battle: Battle,
                              ctx: AttackContext,
                              value: Any,
                              category: MoveCategory,
                              stat: Stat,
                              amount: int) -> HandlerReturn:
    """指定カテゴリの技でダメージを受けたとき能力を上昇させる共通処理。

    source=mon（自発的な変化）として扱うことで、あまのじゃくにより変化量が
    反転して下降になった場合でもしろいきり・フラワーベールで防がれないようにする。
    また、ランクがすでに上限/下限で実際に変化しなかった場合はアイテムを消費しない。
    特性ちからずくの対象技（追加効果あり技）を受けたときは発動しない。
    """
    mon = ctx.defender
    assert mon is not None
    if (
        ctx.attacker.ability.name == "ちからずく"
        and ctx.move.has_flag("secondary_effect")
    ):
        return HandlerReturn(value=value)
    # 相手のきんちょうかん・じんばいったいの影響下では発動しない
    if battle.query.is_nervous(mon):
        return HandlerReturn(value=value)
    if ctx.move.category == category:
        # じゅくせい所持時はランク上昇量が2倍になる
        boost = amount * 2 if is_ripen(mon) else amount
        if battle.modify_stats(mon, {stat: boost}, source=mon):
            _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)

def _retaliate_on_category(battle: Battle,
                           ctx: AttackContext,
                           value: Any,
                           category: MoveCategory) -> HandlerReturn:
    """指定カテゴリの技でダメージを受けたとき攻撃者に反撃ダメージを与える共通処理。

    マジックガードなどで実際にダメージが通らなかった場合（攻撃者がすでに
    ひんしの場合を含む）は発動・消費しない。
    """
    mon = ctx.defender
    assert mon is not None
    # 相手のきんちょうかん・じんばいったいの影響下では発動しない
    if battle.query.is_nervous(mon):
        return HandlerReturn(value=value)
    if ctx.move.category == category:
        # じゅくせい所持時は最大HPの1/4ダメージになる。1/8を2倍にするのではなく、
        # 1回の乗算で1/4を算出する（一次情報: 端数処理が異なるため）。
        r = -1/4 if is_ripen(mon) else -1/8
        if battle.modify_hp(ctx.attacker, r=r):
            # ダメおし判定用: ジャポのみ/レンブのみによるダメージも「そのターンに
            # 攻撃を受けた」扱いにする（一次情報: .internal/wiki/moves/ダメおし.html 技の仕様節）。
            ctx.attacker.hits_taken += 1
            _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)

def _dedicated_item_form_change(battle: Battle,
                                ctx: EventContext,
                                value: Any,
                                base_form: str,
                                origin_form: str) -> HandlerReturn:
    mon = ctx.source
    if mon is not None and mon.name == base_form:
        mon.set_form(origin_form)
    return HandlerReturn(value=value)

def _dedicated_item_modify_power(ctx: AttackContext,
                                 value: Any,
                                 allowed_names: frozenset[str],
                                 allowed_types: tuple[Type, ...]) -> HandlerReturn:
    if (
        ctx.attacker.name in allowed_names
        and ctx.move.type in allowed_types
    ):
        value = apply_fixed_modifier(value, 4915)
    return HandlerReturn(value=value)

def _dedicated_item_prevent_item_change(ctx: EventContext,
                                        value: bool,
                                        name_prefix: str) -> HandlerReturn:
    """専用道具: 対象のポケモンが持っている間はトリック・すりかえ・ほしがる・どろぼう・
    特性マジシャン・わるいてぐせ・ふしょくガス・はたきおとすによる奪取/交換/除去を防ぐ。
    """
    mon = ctx.target
    if mon is not None and mon.name.startswith(name_prefix):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)

def _dedicated_item_prevent_transfer_to_base_form(ctx: EventContext,
                                                  value: bool,
                                                  base_form: str) -> HandlerReturn:
    """専用道具: 通常の姿へトリック・すりかえ等で渡すことを防ぐ。"""
    mon = ctx.target
    if mon is not None and mon.name == base_form:
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)

def _boost_stat_on_type_hit(battle: Battle,
                            ctx: AttackContext,
                            value: Any,
                            *,
                            type_: Type,
                            stats: dict[Stat, int]) -> HandlerReturn:
    mon = ctx.defender
    assert mon is not None
    if ctx.move.type == type_:
        changes = battle.modify_stats(mon, stats)
        if changes:  # ランク上限などで不発の場合は消費しない
            _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)


def あおぞらプレート_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="ひこう", modifier=4915)


def あかいいと_infatuate_foe(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """あかいいと: 持ち主がメロメロになったとき相手にもメロメロを付与する。"""
    if value != "メロメロ":
        return HandlerReturn(value=value)
    foe = battle.foe(ctx.source)
    battle.volatile_manager.apply(foe, "メロメロ", source=ctx.source)
    return HandlerReturn(value=value)


def アッキのみ_boost_defense_on_physical_hit(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """アッキのみ: 物理技でダメージを受けたときぼうぎょ+1。"""
    return _boost_on_attack_category(battle, ctx, value, "physical", "def", +1)


def あついいわ_resolve_field_count(_battle: Battle, _ctx: EventContext, value: Any) -> HandlerReturn:
    return _resolve_field_count(value, "はれ", additonal_count=3)


def あつぞこブーツ_check_hazard_immune(_battle: Battle, _ctx: EventContext, _value: Any) -> HandlerReturn:
    """あつぞこブーツ: エントリーハザードを無効化する。"""
    return HandlerReturn(value=True, stop_event=True)


def イアのみ_heal_on_quarter_hp(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """イアのみ: HPが1/4以下になった瞬間に最大HPの1/3を回復するが、
    ぼうぎょが上がりにくい性格（さみしがり・おっとり・おとなしい・せっかち）は
    すっぱい味を嫌うためこんらんする。
    """
    return _heal_berry(
        battle, ctx, value, denominator=4, heal_r=1/3,
        confuse_natures=("さみしがり", "おっとり", "おとなしい", "せっかち"),
    )


def いかさまダイス_modify_hit_check_each_time(_battle: Battle, _ctx: AttackContext, _value: bool) -> HandlerReturn:
    """いかさまダイス: トリプルキック等、毎ヒット命中判定する技を初回ヒットのみの判定にする。"""
    return HandlerReturn(value=False)


def いかさまダイス_modify_hit_count(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """いかさまダイス: 2-5回連続技のヒット数を4回または5回へ補正する。"""
    min_hits, max_hits = ctx.move.min_hits, ctx.move.max_hits
    if (min_hits, max_hits) == (2, 5):
        value = 4 if battle.random.random() < 0.5 else 5
    return HandlerReturn(value=value)


def いかずちプレート_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="でんき", modifier=4915)


def イトケのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="みず", modifier=2048/4096)


def いのちのたま_boost_atk(_battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """いのちのたま: 攻撃技の攻撃補正を1.3倍にする。"""
    if ctx.move.is_attack:
        value = apply_fixed_modifier(value, 5324)
    return HandlerReturn(value=value)


def いのちのたま_recoil(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """いのちのたま: 攻撃技命中後、最大HPの1/10の反動ダメージを受ける。
    連続攻撃技は最後のヒットでのみ発動。ちからずくの対象技（追加効果あり技）を
    ちからずく所持者が使用した場合は反動が発生しない。

    なげつけるでいのちのたまを投げた場合、同じEvent.ON_HIT内でこのハンドラより先に
    アイテムが消費されるが、イベント発火時にハンドラ一覧がスナップショットされる
    仕様上、消費後もこのハンドラ自体は呼び出される。そのため、ここで改めて
    いのちのたまを保持しているかを確認し、既に手放している場合は反動を発生させない
    （ダメージ倍率は増えるが反動は受けない、という一次情報の仕様通り）。
    """
    if (
        ctx.attacker.has_item("いのちのたま")
        and ctx.move.is_attack
        and ctx.hit_index == ctx.hit_count
        and not (
            ctx.attacker.ability.name == "ちからずく"
            and ctx.move.has_flag("secondary_effect")
        )
    ):
        battle.modify_hp(ctx.attacker, r=-1/10, source=ctx.attacker)
        # ダメおし判定用: いのちのたまの反動ダメージも「そのターンに攻撃を受けた」
        # 扱いにする（一次情報: .internal/wiki/moves/ダメおし.html 技の仕様節）。
        ctx.attacker.hits_taken += 1
        _announce_item_triggered(battle, ctx.attacker)
    return HandlerReturn(value=value)


def イバンのみ_boost_priority(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """イバンのみ: 先制フラグが立っているとき行動ティアを+1する。

    相手のきんちょうかん・じんばいったいの影響下では消費・発動しない
    （フラグは持ち越され、その効果が無くなったターンで発動する）。
    所有者の特性がきんしのちからで変化技を選んだ場合も発動しない。
    """
    mon = ctx.attacker
    if (
        mon.ability.name == "きんしのちから"
        and not ctx.move.is_attack
    ):
        return HandlerReturn(value=value)
    if mon.item.count == 1 and not battle.query.is_nervous(mon):
        battle.item_manager.consume_item(mon)
        return HandlerReturn(value=value + 1)
    return HandlerReturn(value=value)


def イバンのみ_set_priority_flag(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """イバンのみ: HPが1/4以下に下がった瞬間に先制フラグを立てる。

    こんらんの自傷ダメージでは発動しない（第五世代以降の仕様）。
    くいしんぼう所持時は1/2HP以下に緩和される。
    """
    mon = ctx.target
    assert mon is not None
    if ctx.hp_change_reason == "self_attack":
        return HandlerReturn(value=value)
    denominator = _gluttony_denominator(mon, 4)
    hp_after = mon.hp
    hp_before = hp_after + value
    if hp_before * denominator > mon.max_hp and hp_after * denominator <= mon.max_hp:
        mon.item.count = 1
        _announce_item_triggered(battle, mon)
    return HandlerReturn(value=value)


def ウイのみ_heal_on_quarter_hp(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ウイのみ: HPが1/4以下になった瞬間に最大HPの1/3を回復するが、
    とくこうが上がりにくい性格（いじっぱり・わんぱく・ようき・しんちょう）は
    しぶい味を嫌うためこんらんする。
    """
    return _heal_berry(
        battle, ctx, value, denominator=4, heal_r=1/3,
        confuse_natures=("いじっぱり", "わんぱく", "ようき", "しんちょう"),
    )


def ウタンのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="エスパー", modifier=2048/4096)


def エレキシード_boost_defense(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _terrain_seed_boost(battle, ctx, value, "エレキフィールド", "def", "エレキシード")


# 元々ひるみの追加効果を持つ技名の集合。
# 現行世代（第五世代以降）ではこれらの技におうじゃのしるし・するどいキバの効果は重複しない。
_INNATE_FLINCH_MOVES: frozenset[str] = frozenset({
    "3ぼんのや", "アイアンヘッド", "あくのはどう", "いびき", "いわなだれ", "エアスラッシュ",
    "おどろかす", "かみつく", "かみなりのキバ", "こおりのキバ", "ゴッドバード", "しねんのずつき",
    "じんつうりき", "ずつき", "たきのぼり", "たつまき", "つららおとし",
    "ドラゴンダイブ", "ねこだまし", "はやてがえし",
    "ひょうざんおろし", "びりびりちくちく", "ふみつけ",
    "ほのおのキバ", "もえあがるいかり",
})

def flinch_on_hit_10pct(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """おうじゃのしるし、するどいキバ: ダメージ技命中時10%の確率で相手をひるませる。

    元々ひるみの追加効果を持つ技（アイアンヘッド等）や一撃必殺技には効果が無い。
    りんぷん（無効化）・てんのめぐみ（確率2倍）の影響を受ける。
    """
    defender = ctx.defender
    if (
        ctx.move.is_attack
        and defender is not None
        and not ctx.move.has_flag("ohko")
        and ctx.move.name not in _INNATE_FLINCH_MOVES
    ):
        chance = battle.resolve_secondary_chance(ctx, 0.1)
        if battle.random.random() < chance:
            battle.volatile_manager.apply(defender, "ひるみ", source=ctx.attacker)
    return HandlerReturn(value=value)


def おおきなねっこ_boost_drain(_battle: Battle, _ctx: Any, value: int) -> HandlerReturn:
    """おおきなねっこ: HPを吸収する効果の回復量を1.3倍(5324/4096倍、五捨五超入)にする。"""
    return HandlerReturn(value=round_half_down(value * 5324 / 4096))


def オッカのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="ほのお", modifier=2048/4096)


def オボンのみ_heal_on_half_hp(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _heal_berry(battle, ctx, value, denominator=2, heal_r=1/4)


def オレンのみ_heal_on_half_hp(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _heal_berry(battle, ctx, value, denominator=2, heal_v=10)


def おんみつマント_negate_secondary(_battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """おんみつマント: 技の追加効果の確率を0にする。

    りんぷん特性と同様に、他のハンドラに上書きされないよう stop_event=True で確定させる。
    コメットパンチなど、使用者自身の能力が変化する追加効果（ctx.secondary_effect_target
    == "attacker"）は、所持者が使用したときも所持者に対して使われたときも発動するため
    防げない（一次情報: 「自分のランクを上げる追加効果は、所持者が使用したときも、
    所持者に対して使われたときも発動する」）。

    でんじは・どくどく等の変化技（ctx.move.category == "status"）は、状態異常等の
    付与そのものが技の唯一の効果であり「追加効果」には当たらないため対象外とする
    （一次情報: 「相手の“攻撃技”による追加効果を受けなくなる」。
    .internal/spec/items/おんみつマント.md）。りんぷんの同種修正（handlers/ability.py の
    りんぷん_block_secondary_chance）と揃える。
    """
    if ctx.secondary_effect_target != "defender":
        return HandlerReturn(value=value)
    if ctx.move.category == "status":
        return HandlerReturn(value=value)
    return HandlerReturn(value=0, stop_event=True)


def オーガポンのめん_boost_atk(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """オーガポンのめん共通: 攻撃技の威力を物理・特殊問わず1.2倍にする。"""
    if ctx.move.is_attack:
        value = apply_fixed_modifier(value, 4915)
    return HandlerReturn(value=value)


def オーガポンのめん_prevent_item_change(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """オーガポンのめん共通: オーガポンが持っている間はトリック・すりかえ・ほしがる・どろぼう・
    特性マジシャン・わるいてぐせ・ふしょくガス・はたきおとすによる奪取/交換/除去を防ぐ。
    オーガポン以外が持っている場合は通常通り奪取/交換/除去できる。
    """
    return _dedicated_item_prevent_item_change(ctx, value, "オーガポン")


def かいがらのすず_drain_on_hit(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """かいがらのすず: 攻撃技命中後に与ダメージの1/8を回復する。

    みがわりに阻まれた場合は、みがわりへの与ダメージから算出する（第五世代以降の仕様）。
    特性ちからずくの対象技を使った場合は回復効果が無くなる。
    連続攻撃技は最後のヒット（相手または自分がひんしになって中断した場合はその時点）の後に
    まとめて発動し、回復量は全ヒットの合計ダメージから算出する。
    """
    if (
        ctx.attacker.ability.name == "ちからずく"
        and ctx.move.has_flag("secondary_effect")
    ):
        return HandlerReturn(value=value)

    damage = value or ctx.substitute_damage
    total_damage = getattr(ctx, "_shell_bell_total_damage", 0) + damage

    is_last_hit = (
        ctx.hit_index == ctx.hit_count
        or ctx.defender.fainted
        or ctx.attacker.fainted
    )
    if not is_last_hit:
        ctx._shell_bell_total_damage = total_damage
        return HandlerReturn(value=value)

    heal_amount = total_damage // 8
    if (
        not ctx.attacker.fainted
        and heal_amount > 0
        and battle.modify_hp(ctx.attacker, v=heal_amount)
    ):
        _announce_item_triggered(battle, ctx.attacker)
    return HandlerReturn(value=value)


def かえんだま_apply_burn(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """かえんだま: ターン終了時にやけどを付与する。"""
    return _apply_ailment_from_item(battle, ctx, value, "やけど")


def カゴのみ_cure_sleep(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _cure_ailment_berry(battle, ctx, value, "ねむり")


def カゴのみ_cure_sleep_on_apply(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """カゴのみ: ねむり付与直後に治療して消費する。"""
    return _cure_ailment_berry_on_apply(battle, ctx, value, "ねむり")


def カシブのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="ゴースト", modifier=2048/4096)


def かたいいし_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="いわ", modifier=4915)


def カムラのみ_boost_speed(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """カムラのみ: HP1/4以下ですばやさ+1。"""
    return _boost_on_quarter_hp(battle, ctx, value, stat="spe", amount=+1)


def からぶりほけん_boost_speed_on_miss(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """からぶりほけん: 技が外れたときすばやさ+2。

    一撃必殺技を外したときは発動しない。
    連続技は最初の1発が外れたときのみ発動する（2発目以降の命中判定失敗では発動しない）。
    """
    mon = ctx.attacker
    assert mon is not None
    if ctx.move.has_flag("ohko"):
        return HandlerReturn(value=value)
    if ctx.hit_index != 1:
        return HandlerReturn(value=value)
    changes = battle.modify_stats(mon, {"spe": +2})
    if changes:  # ランク上限などで不発の場合は消費しない
        _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)


def がんせきプレート_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="いわ", modifier=4915)


def きあいのタスキ_survive_ohko(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """きあいのタスキ: HPが満タンのときひんし以上のダメージをHP1で耐える。"""
    mon = ctx.defender
    assert mon is not None
    if mon.hp == mon.max_hp and value >= mon.hp:
        value = mon.hp - 1
        _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)


def きあいのハチマキ_survive_by_chance(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """きあいのハチマキ: ひんし以上のダメージを10%の確率でHP1で耐える。"""
    mon = ctx.defender
    assert mon is not None
    if value >= mon.hp and battle.random.random() < 0.1:
        value = mon.hp - 1
        _announce_item_triggered(battle, mon)
    return HandlerReturn(value=value)


def きせきのタネ_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="くさ", modifier=4915)


def きゅうこん_boost_spatk_on_water_hit(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """きゅうこん: みず技でダメージを受けたときとくこう+1。"""
    return _boost_stat_on_type_hit(battle, ctx, value, type_="みず", stats={"spa": +1})


def きれいなぬけがら_check_trapped(_battle: Battle, _ctx: EventContext, _value: Any) -> HandlerReturn:
    """きれいなぬけがら: 拘束効果を無効化する。"""
    return HandlerReturn(value=False, stop_event=True)


def キーのみ_cure_confusion(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """キーのみ: こんらん状態を回復する。"""
    mon = ctx.source
    assert mon is not None
    if mon.has_volatile("こんらん"):
        battle.volatile_manager.remove(mon, "こんらん")
        _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)


def ぎんのこな_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="むし", modifier=4915)


def くちたけん_form_change(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """くちたけん: ザシアン(れきせん)をザシアン(けんのおう)にフォルムチェンジする。"""
    mon = ctx.source
    if mon.name == "ザシアン(れきせん)":
        mon.set_form("ザシアン(けんのおう)")
    return HandlerReturn(value=value)


def くちたけん_prevent_item_change(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """くちたけん: ザシアンが持っている間はトリック・すりかえ・ほしがる・どろぼう・
    特性マジシャン・わるいてぐせ・ふしょくガス・はたきおとすによる奪取/交換/除去を防ぐ。
    ザシアン以外が持っている場合は通常通り奪取/交換/除去できる。
    """
    mon = ctx.target
    if mon is not None and mon.name.startswith("ザシアン"):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def くちたけん_prevent_transfer_to_hero(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """くちたけん: れきせんのゆうしゃザシアンへトリック・すりかえ等で渡すことを防ぐ。"""
    mon = ctx.target
    if mon is not None and mon.name == "ザシアン(れきせん)":
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def くちたたて_form_change(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """くちたたて: ザマゼンタ(れきせん)をザマゼンタ(たてのおう)にフォルムチェンジする。"""
    mon = ctx.source
    if mon.name == "ザマゼンタ(れきせん)":
        mon.set_form("ザマゼンタ(たてのおう)")
    return HandlerReturn(value=value)


def くちたたて_prevent_item_change(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """くちたたて: ザマゼンタが持っている間はトリック・すりかえ・ほしがる・どろぼう・
    特性マジシャン・わるいてぐせ・ふしょくガス・はたきおとすによる奪取/交換/除去を防ぐ。
    ザマゼンタ以外が持っている場合は通常通り奪取/交換/除去できる。
    """
    mon = ctx.target
    if mon is not None and mon.name.startswith("ザマゼンタ"):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def くちたたて_prevent_transfer_to_hero(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """くちたたて: れきせんのゆうしゃザマゼンタへトリック・すりかえ等で渡すことを防ぐ。"""
    mon = ctx.target
    if mon is not None and mon.name == "ザマゼンタ(れきせん)":
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def くっつきバリ_damage_on_turn_end(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """くっつきバリ: ターン終了時に最大HPの1/8ダメージを受ける。"""
    mon = ctx.source
    assert mon is not None
    if battle.modify_hp(mon, r=-1/8):
        _announce_item_triggered(battle, mon)
    return HandlerReturn(value=value)


def くっつきバリ_transfer_on_contact(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """くっつきバリ: 接触攻撃者がアイテムを持っていない場合、攻撃者に転送する。

    ねんちゃくを持っていても発動条件を満たせば攻撃側に渡る仕様のため、
    source=mon（自分自身）を渡してねんちゃくによる阻止を回避する。
    """
    mon = ctx.defender
    assert mon is not None
    if (
        battle.query.is_contact(ctx) and
        not ctx.attacker.has_item()
    ):
        _announce_item_triggered(battle, mon)
        if battle.item_manager.remove_item(mon, source=mon):
            battle.item_manager.gain_item(ctx.attacker, "くっつきバリ")
    return HandlerReturn(value=value)


def クラボのみ_cure_paralysis(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _cure_ailment_berry(battle, ctx, value, "まひ")


def クラボのみ_cure_paralysis_on_apply(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """クラボのみ: まひ付与直後に治療して消費する。"""
    return _cure_ailment_berry_on_apply(battle, ctx, value, "まひ")


def クリアチャーム_block_stat_drop(battle: Battle, ctx: EventContext, value: dict) -> HandlerReturn:
    """クリアチャーム: 相手による能力ランク低下を無効化する。"""
    mon = ctx.target
    assert mon is not None
    blocked = value
    if ctx.source is not None and ctx.source != ctx.target:
        blocked = {s: v for s, v in value.items() if v >= 0}
    if blocked != value:
        _announce_item_triggered(battle, mon)
    return HandlerReturn(value=blocked)


def くろいてっきゅう_halve_speed(_battle: Battle, _ctx: EventContext, value: Any) -> HandlerReturn:
    return HandlerReturn(value=apply_fixed_modifier(value, 2048))


def くろいてっきゅう_negate_floating(_battle: Battle, _ctx: EventContext, _value: Any) -> HandlerReturn:
    return HandlerReturn(value=False, stop_event=True)


def くろいヘドロ_heal_or_damage(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    mon = ctx.source
    assert mon is not None
    r = 1/16 if mon.has_type("どく") else -1/8
    if battle.modify_hp(mon, r=r):
        _announce_item_triggered(battle, mon)
    return HandlerReturn(value=value)


def くろいメガネ_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="あく", modifier=4915)


def くろおび_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="かくとう", modifier=4915)


def グラスシード_boost_defense(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _terrain_seed_boost(battle, ctx, value, "グラスフィールド", "def", "グラスシード")


def グランドコート_resolve_field_count(_battle: Battle, _ctx: EventContext, value: Any) -> HandlerReturn:
    return _resolve_field_count(value, "エレキフィールド", "グラスフィールド", "ミストフィールド", "サイコフィールド", additonal_count=3)


def こうかくレンズ_modify_accuracy(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """こうかくレンズ: 命中率を1.1倍にする。

    value が None の場合は既に必中状態が確定しているため、補正をかけずそのまま返す。
    """
    if value is None:
        return HandlerReturn(value=value)
    return HandlerReturn(value=apply_fixed_modifier(value, 4506))


def こうこうのしっぽ_back_tier(_battle: Battle, _ctx: AttackContext, value: int) -> HandlerReturn:
    """こうこうのしっぽ: 行動順を1段階後ろにする。"""
    return HandlerReturn(value=value - 1)


def こうてつのプレート_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="はがね", modifier=4915)


def こころのしずく_modify_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """こころのしずく: ラティオス・ラティアス持ちのエスパー・ドラゴン技1.2倍。"""
    return _dedicated_item_modify_power(ctx, value, {"ラティオス", "ラティアス"}, ("エスパー", "ドラゴン"))


def こだわり_lock_move(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """こだわりアイテム: 使用した技でロックする。

    Event.ON_PP_CONSUMED（PP消費確定直後、run_move._consume_pp内で技実行の
    成否・ON_MOVE_CHARGEの結果に関わらず必ず発火する）と Event.ON_MOVE_END の
    両方に登録している。ON_PP_CONSUMEDが本来のロック発生点（実機は「技を選択して
    PPを消費した瞬間」にロックする）で、`has_volatile`チェックにより同一ターン内で
    二重に発火しても副作用がないため、そらをとぶ・ソーラービーム等の
    charge_into_volatile系2ターン技のためターン（Event.ON_MOVE_CHARGEがFalseを
    返しON_MOVE_ENDが発火しない）でも確実にロックできる。ON_MOVE_ENDへの登録は
    引き続き残しており、トリック・すりかえ自身の使用によってこだわり系アイテムを
    新たに入手した場合（アイテム交換はON_STATUS_HIT内で行われ、ON_PP_CONSUMED
    発火時点ではまだ新アイテムを保持していないため、そちらでは発火しない）に、
    ON_MOVE_ENDでロックされた直後 `すりかえ_release_choice_lock`
    （`data/moves/move_sa.py` `data/moves/move_ta.py` に登録）がより遅い優先度で
    ロックを解除する既存の仕組みを維持するため。

    ねごとのサブ実行中（sleep_talk_active）はロック対象としない。
    第五世代以降、こだわり系アイテムはねごとで選ばれた技ではなく「ねごと」自体で
    ロックされるため、サブ実行中に発火するこのハンドラでは何もせず、
    ねごと自身のON_PP_CONSUMED/ON_MOVE_ENDでロックする。
    """
    mon = ctx.attacker
    if mon.sleep_talk_active:
        return HandlerReturn(value=value)
    if not mon.has_volatile("こだわり"):
        battle.volatile_manager.apply(
            mon, "こだわり", source=mon, move_name=ctx.move.name
        )
    return HandlerReturn(value=value)


def こだわりスカーフ_boost_speed(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """こだわりスカーフ: 素早さを1.5倍にする。"""
    value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def こだわりハチマキ_boost_physical(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """こだわりハチマキ: 物理技の攻撃補正を1.5倍にする。

    こんらんの自傷ダメージ（"_こんらん"）には影響しない
    （Champions仕様＝第五世代以降の仕様に準拠）。
    """
    if ctx.move.category == "physical" and ctx.move.name != "_こんらん":
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def こだわりメガネ_boost_special(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """こだわりメガネ: 特殊技の攻撃補正を1.5倍にする。"""
    if ctx.move.category == "special":
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def こぶしのプレート_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="かくとう", modifier=4915)


def こわもてプレート_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="あく", modifier=4915)


def こんごうだま_modify_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """こんごうだま: ディアルガ持ちのドラゴン・はがね技1.2倍。"""
    return _dedicated_item_modify_power(ctx, value, frozenset({"ディアルガ", "ディアルガ(オリジン)"}), ("ドラゴン", "はがね"))


def ゴツゴツメット_chip_contact_attacker(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    mon = ctx.defender
    assert mon is not None
    if _apply_contact_item_chip(battle, ctx, ratio=1/6):
        _announce_item_triggered(battle, mon)
    return HandlerReturn(value=value)


def サイコシード_boost_spdef(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _terrain_seed_boost(battle, ctx, value, "サイコフィールド", "spd", "サイコシード")


def さらさらいわ_resolve_field_count(_battle: Battle, _ctx: EventContext, value: Any) -> HandlerReturn:
    return _resolve_field_count(value, "すなあらし", additonal_count=3)


def サンのみ_apply_focus_energy(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """サンのみ: HP1/4以下できゅうしょアップ状態になる。

    value >= mon.max_hp はほおばる等による強制発動（HP閾値チェックを無視する）。
    くいしんぼう所持時は1/2HP以下に緩和される。
    """
    mon = ctx.target
    assert mon is not None
    denominator = _gluttony_denominator(mon, 4)
    if mon.hp * denominator <= mon.max_hp or value >= mon.max_hp:
        if battle.volatile_manager.apply(mon, "きゅうしょアップ", count=2):
            _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)


def しずくプレート_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="みず", modifier=4915)


def しめったいわ_resolve_field_count(_battle: Battle, _ctx: EventContext, value: Any) -> HandlerReturn:
    return _resolve_field_count(value, "あめ", additonal_count=3)


def しめつけバンド_boost_bind_damage(_battle: Battle, _ctx: EventContext, _value: Any) -> HandlerReturn:
    """しめつけバンド: バインドのダメージを最大HPの1/6に増加する。"""
    return HandlerReturn(value=1/6)


def シュカのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="じめん", modifier=2048/4096)


def しらたま_modify_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """しらたま: パルキア持ちのドラゴン・みず技1.2倍。"""
    return _dedicated_item_modify_power(ctx, value, frozenset({"パルキア", "パルキア(オリジン)"}), ("ドラゴン", "みず"))


def シルクのスカーフ_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="ノーマル", modifier=4915)


def しろいハーブ_cancel_stat_drop(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """しろいハーブ: 能力ランクが下がった結果マイナスになったとき、下がった能力を全て0に戻す。

    2段階上がっている能力を2段階下げられた場合など、結果のランクが+0以上の場合は発動しない。
    発動時はこの変化以外で既にマイナスになっている能力もまとめてリセットする。
    """
    # value は actual_changes ({stat: 変化量})。今回の変化で負になったランクがあるか確認する。
    mon = ctx.target
    assert mon is not None
    triggered = any(v < 0 and mon.boosts[s] < 0 for s, v in value.items())
    if triggered and _reset_negative_ranks(battle, mon, reason="しろいハーブ"):
        _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)


def しろいハーブ_reset_if_already_lowered(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """しろいハーブ: 場に出た時・アイテムを入手した時点で既に能力がマイナスの場合、即座に発動する。

    バトンタッチで下がった能力を引き継いだ場合や、トリック等で入手した時点で
    既に能力が下がっている場合に対応する。
    """
    mon = ctx.source
    assert mon is not None
    if _reset_negative_ranks(battle, mon, reason="しろいハーブ"):
        _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)


def しんかのきせき_boost_defenses(_battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """しんかのきせき: 未進化ポケモンのぼうぎょ・とくぼうを1.5倍にする。

    メルタンは進化先（メルメタル）を持つが、通常と異なる進化手段のため例外的に効果が無い。
    """
    if (
        ctx.defender.name in _HAS_EVOLUTION
        and ctx.defender.name not in _EVIOLITE_NO_EFFECT
    ):
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def しんぴのしずく_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="みず", modifier=4915)


def じしゃく_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="でんき", modifier=4915)


def じゃくてんほけん_boost_on_super_effective(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """じゃくてんほけん: 効果抜群のダメージを受けたときA・Cを+2。

    ダメージ固定技（一撃必殺技を除く）はタイプ相性上は抜群でも発動しない。
    """
    mon = ctx.defender
    assert mon is not None
    if ctx.move.has_flag("fixed_damage"):
        return HandlerReturn(value=value)
    if battle.query.is_super_effective(ctx):
        changes = battle.modify_stats(mon, {"atk": +2, "spa": +2})
        if changes:  # ランク上限などで不発の場合は消費しない
            _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)


def ジャポのみ_retaliate_physical(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ジャポのみ: 物理技でダメージを受けたとき攻撃者に最大HPの1/8ダメージ。"""
    return _retaliate_on_category(battle, ctx, value, "physical")


def じゅうでんち_boost_atk_on_electric_hit(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """じゅうでんち: でんき技でダメージを受けたときこうげき+1。"""
    return _boost_stat_on_type_hit(battle, ctx, value, type_="でんき", stats={"atk": +1})


def スターのみ_random_boost(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """スターのみ: HP1/4以下でこうげき・ぼうぎょ・とくこう・とくぼう・すばやさの
    うちランダムな1つ（ランクが最大でないもの）+2。

    value >= mon.max_hp はほおばる等による強制発動（HP閾値チェックを無視する）。
    くいしんぼう所持時は1/2HP以下に緩和される。
    """
    mon = ctx.target
    assert mon is not None
    forced = value >= mon.max_hp
    denominator = _gluttony_denominator(mon, 4)
    if not forced:
        # こんらんの自傷ダメージでは発動しない（第五世代以降の仕様）
        if ctx.hp_change_reason == "self_attack":
            return HandlerReturn(value=value)
        if mon.hp * denominator > mon.max_hp:
            return HandlerReturn(value=value)
    # すでにランクが最大の能力は選ばれない（5箇所全て最大なら発動しない）
    candidates: list[Stat] = [s for s in ("atk", "def", "spa", "spd", "spe") if mon.boosts[s] < 6]
    if candidates:
        stat = battle.random.choice(candidates)
        if battle.modify_stats(mon, {stat: +2}):
            _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)


def するどいくちばし_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="ひこう", modifier=4915)


def するどいツメ_boost_critical_rank(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """するどいツメ: 急所ランクを+1する。"""
    return HandlerReturn(value=value + 1)


def ズアのみ_boost_spdef(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ズアのみ: HP1/4以下でとくぼう+1。"""
    return _boost_on_quarter_hp(battle, ctx, value, stat="spd", amount=+1)


def せいれいプレート_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="フェアリー", modifier=4915)


def せんせいのツメ_priority_boost(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """せんせいのツメ: 20%の確率で先制ティアを+1する。

    所有者の特性がきんしのちからで変化技を選んだ場合は発動しない。
    """
    if (
        ctx.attacker.ability.name == "きんしのちから"
        and not ctx.move.is_attack
    ):
        return HandlerReturn(value=value)
    if battle.random.random() < 0.2:
        return HandlerReturn(value=value + 1)
    return HandlerReturn(value=value)


def ソクノのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="でんき", modifier=2048/4096)


def たつじんのおび_boost_super_effective(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    if battle.query.is_super_effective(ctx):
        value = apply_fixed_modifier(value, 4915)
    return HandlerReturn(value=value)


def たべのこし_heal(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """たべのこし: ターン終了時HP回復"""
    mon = ctx.source
    if battle.modify_hp(mon, r=1/16):
        _announce_item_triggered(battle, mon)
    return HandlerReturn(value=value)


def たまむしのプレート_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="むし", modifier=4915)


def タラプのみ_boost_spdef(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """タラプのみ: 特殊技でダメージを受けたときとくぼう+1。"""
    return _boost_on_attack_category(battle, ctx, value, "special", "spd", +1)


def タンガのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="むし", modifier=2048/4096)


def だいこんごうだま_form_change(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """だいこんごうだま: ディアルガをオリジンフォルムにフォルムチェンジする。"""
    return _dedicated_item_form_change(battle, ctx, value, "ディアルガ", "ディアルガ(オリジン)")


def だいこんごうだま_modify_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """だいこんごうだま: ディアルガ(オリジン)持ちのドラゴン・はがね技1.2倍。"""
    return _dedicated_item_modify_power(ctx, value, frozenset({"ディアルガ(オリジン)"}), ("ドラゴン", "はがね"))


def だいこんごうだま_prevent_item_change(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """だいこんごうだま: ディアルガが持っている間はトリック・すりかえ・ほしがる・どろぼう・
    特性マジシャン・わるいてぐせ・ふしょくガス・はたきおとすによる奪取/交換/除去を防ぐ。
    ディアルガ以外が持っている場合は通常通り奪取/交換/除去できる。
    """
    return _dedicated_item_prevent_item_change(ctx, value, "ディアルガ")


def だいこんごうだま_prevent_transfer_to_base_form(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """だいこんごうだま: 通常の姿のディアルガへトリック・すりかえ等で渡すことを防ぐ。"""
    return _dedicated_item_prevent_transfer_to_base_form(ctx, value, "ディアルガ")


def だいしらたま_form_change(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """だいしらたま: パルキアをオリジンフォルムにフォルムチェンジする。"""
    return _dedicated_item_form_change(battle, ctx, value, "パルキア", "パルキア(オリジン)")


def だいしらたま_modify_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """だいしらたま: パルキア(オリジン)持ちのドラゴン・みず技1.2倍。"""
    return _dedicated_item_modify_power(ctx, value, frozenset({"パルキア(オリジン)"}), ("ドラゴン", "みず"))


def だいしらたま_prevent_item_change(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """だいしらたま: パルキアが持っている間はトリック・すりかえ・ほしがる・どろぼう・
    特性マジシャン・わるいてぐせ・ふしょくガス・はたきおとすによる奪取/交換/除去を防ぐ。
    パルキア以外が持っている場合は通常通り奪取/交換/除去できる。
    """
    return _dedicated_item_prevent_item_change(ctx, value, "パルキア")


def だいしらたま_prevent_transfer_to_base_form(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """だいしらたま: 通常の姿のパルキアへトリック・すりかえ等で渡すことを防ぐ。"""
    return _dedicated_item_prevent_transfer_to_base_form(ctx, value, "パルキア")


def だいちのプレート_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="じめん", modifier=4915)


def だいはっきんだま_form_change(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """だいはっきんだま: ギラティナ(アナザー)をオリジンフォルムにフォルムチェンジする。"""
    return _dedicated_item_form_change(battle, ctx, value, "ギラティナ(アナザー)", "ギラティナ(オリジン)")


def だいはっきんだま_modify_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """だいはっきんだま: ギラティナ(オリジン)持ちのドラゴン・ゴースト技1.2倍。"""
    return _dedicated_item_modify_power(ctx, value, frozenset({"ギラティナ(オリジン)"}), ("ドラゴン", "ゴースト"))


def だいはっきんだま_prevent_item_change(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """だいはっきんだま: ギラティナが持っている間はトリック・すりかえ・ほしがる・どろぼう・
    特性マジシャン・わるいてぐせ・ふしょくガス・はたきおとすによる奪取/交換/除去を防ぐ。
    ギラティナ以外が持っている場合は通常通り奪取/交換/除去できる。
    """
    return _dedicated_item_prevent_item_change(ctx, value, "ギラティナ")


def だいはっきんだま_prevent_transfer_to_base_form(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """だいはっきんだま: アナザーフォルムのギラティナへトリック・すりかえ等で渡すことを防ぐ。"""
    return _dedicated_item_prevent_transfer_to_base_form(ctx, value, "ギラティナ(アナザー)")


def だっしゅつパック_reserve_switch(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    # valueは{stat: change}の辞書
    # にげられない・バインド・ねをはる・フェアリーロックや特性かげふみ・ありじごく・
    # じりょくなどのとらわれ状態も無視して発動するため、can_switch ではなく
    # 交代先の有無のみを見る has_available_bench を使う。
    player = battle.get_player(ctx.target)
    if (
        any(v < 0 for v in value.values())
        and battle.query.has_available_bench(player)
    ):
        battle.player_states[player].interrupt = Interrupt.EJECTPACK_REQUESTED
    return HandlerReturn(value=value)


def だっしゅつボタン_reserve_switch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """だっしゅつボタン: 攻撃技を受けると控えのポケモンに交代する（自由選択）。

    実HPダメージが0でも（ばけのかわ/アイスフェイスの肩代わり、こらえる等で耐えた場合）
    発動するが、みがわりに阻まれた場合や特性ちからずくの効果が発動した技を受けた場合は
    発動しない。受けた攻撃でひんしになったときや、交代先の控えがいないときも発動しない。
    にげられない・バインド・ねをはる・フェアリーロックや特性かげふみ・ありじごく・
    じりょくなどのとらわれ状態も無視して発動するため、can_switch ではなく
    交代先の有無のみを見る has_available_bench を使う。
    """
    mon = ctx.defender
    if (
        mon.fainted
        or ctx.substitute_damage
        or (
            ctx.attacker.ability.name == "ちからずく"
            and ctx.move.has_flag("secondary_effect")
        )
    ):
        return HandlerReturn(value=value)
    player = battle.get_player(mon)
    if not battle.query.has_available_bench(player):
        return HandlerReturn(value=value)
    battle.player_states[player].interrupt = Interrupt.EJECTBUTTON
    return HandlerReturn(value=value)


def チイラのみ_boost_attack(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """チイラのみ: HP1/4以下でこうげき+1。"""
    return _boost_on_quarter_hp(battle, ctx, value, stat="atk", amount=+1)


def ちからのハチマキ_boost_physical(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """物理技1.1倍"""
    if ctx.move.category == "physical":
        value = apply_fixed_modifier(value, 4505)
    return HandlerReturn(value=value)


def チーゴのみ_cure_burn(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _cure_ailment_berry(battle, ctx, value, "やけど")


def チーゴのみ_cure_burn_on_apply(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """チーゴのみ: やけど付与直後に治療して消費する。"""
    return _cure_ailment_berry_on_apply(battle, ctx, value, "やけど")


def つめたいいわ_resolve_field_count(_battle: Battle, _ctx: EventContext, value: Any) -> HandlerReturn:
    return _resolve_field_count(value, "ゆき", additonal_count=3)


def つららのプレート_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="こおり", modifier=4915)


def でんきだま_boost_atk(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """でんきだま: ピカチュウ持ちの攻撃技こうげき・とくこう2倍。キョダイマックスするピカチュウも対象。

    こんらんの自傷ダメージ（"_こんらん"）には影響しない
    （Champions仕様＝第五世代以降の仕様に準拠）。
    """
    if (
        ctx.attacker.name in {"ピカチュウ", "ピカチュウ(キョダイ)"}
        and ctx.move.name != "_こんらん"
    ):
        value = apply_fixed_modifier(value, 8192)
    return HandlerReturn(value=value)


def とくせいガード_check_ability_disable(battle: Battle, ctx: EventContext, _value: Any) -> HandlerReturn:
    """とくせいガード: 特性の変更・無効化を防ぐ。"""
    _announce_item_triggered(battle, ctx.source)
    return HandlerReturn(value=True, stop_event=True)


def とけないこおり_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="こおり", modifier=4915)


def とつげきチョッキ_boost_spdef(_battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """とつげきチョッキ: 特殊技に対してとくぼうを1.5倍にする。"""
    if ctx.move.category == "special":
        value = apply_fixed_modifier(value, 6144)
    return HandlerReturn(value=value)


def とつげきチョッキ_modify_command_options(_battle: Battle, ctx: EventContext, value: list) -> HandlerReturn:
    """とつげきチョッキ: 変化技のコマンドを選択肢から除外する。"""
    mon = ctx.source
    return HandlerReturn(value=[
        cmd for cmd in value
        if not (cmd.is_move and mon.moves[cmd.index].category == "status")
    ])


def どくどくだま_apply_poison(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """どくどくだま: ターン終了時にもうどくを付与する。"""
    return _apply_ailment_from_item(battle, ctx, value, "もうどく")


def どくバリ_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="どく", modifier=4915)


def ナゾのみ_heal_on_super_effective(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ナゾのみ: 効果抜群のダメージを受けたときHPを最大HPの25%回復する。

    ダメージ固定技（一撃必殺技を除く）はタイプ相性上は抜群でも発動しない。
    """
    mon = ctx.defender
    assert mon is not None
    if ctx.move.has_flag("fixed_damage"):
        return HandlerReturn(value=value)
    # 相手のきんちょうかん・じんばいったいの影響下では発動しない
    if battle.query.is_nervous(mon):
        return HandlerReturn(value=value)
    if battle.query.is_super_effective(ctx):
        battle.modify_hp(mon, v=berry_heal_amount(mon, r=1/4))
        _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)


def ナナシのみ_cure_freeze(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _cure_ailment_berry(battle, ctx, value, "こおり")


def ナナシのみ_cure_freeze_on_apply(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ナナシのみ: こおり付与直後に治療して消費する。"""
    return _cure_ailment_berry_on_apply(battle, ctx, value, "こおり")


def ナモのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="あく", modifier=2048/4096)


def ねばりのかぎづめ_fix_bind_duration(_battle: Battle, _ctx: AttackContext, value: Any) -> HandlerReturn:
    """ねばりのかぎづめ: バインドの継続ターンを7ターンに固定する。"""
    if value[0] == "バインド":
        value[1] = 7
    return HandlerReturn(value=value)


def ねらいのまと_negate_immunity(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """ねらいのまと: タイプ相性による無効（0倍）を1倍に補正する。

    複数タイプを持つ相手の場合、無効化タイプ以外の相性補正（弱点・耐性）は
    そのまま活かすため、タイプごとに0倍のみを1倍に置き換えてから掛け合わせる。
    浮遊等によるじめん技無効化（フリーフォール）や特性による耐性には影響しない。
    """
    move_type = ctx.move.type
    if move_type == "ステラ" and ctx.defender.is_terastallized:
        # ステラ技のテラスタル相手への効果抜群は無効化ではないため対象外
        return HandlerReturn(value=value)

    type_chart = TYPE_MODIFIER.get(move_type, {})
    if move_type == "じめん":
        if battle.query.is_floating(ctx.defender):
            # 浮遊による無効化（フリーフォール）はねらいのまとの対象外
            return HandlerReturn(value=value)
        type_chart = type_chart.copy()
        type_chart["ひこう"] = 1.0

    base = 4096
    for def_type in ctx.defender.types:
        rate = type_chart.get(def_type, 1.0)
        if rate == 0.0:
            rate = 1.0
        base = int(base * rate)
    return HandlerReturn(value=base)


def のどスプレー_boost_spatk_on_sound(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """のどスプレー: 音技を使用した後にとくこう+1。

    技が外れたとき（move_missed）や、命中はしたが不発だったとき
    （いやしのすずの対象なし等でmove_success=Falseになった場合）は発動しない。
    また、ランクがすでに上限で実際に変化しなかった場合は消費しない。
    """
    mon = ctx.attacker
    executor = battle.move_executor
    if (
        ctx.move.has_flag("sound")
        and not executor.move_missed
        and executor.move_success is not False
    ):
        if battle.modify_stats(mon, {"spa": +1}):
            _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)


def のろいのおふだ_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="ゴースト", modifier=4915)


def ノーマルジュエル_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ノーマルジュエル: ノーマルタイプの攻撃技威力を1.3倍(5325/4096倍)にして消費する。"""
    if ctx.move.type == "ノーマル":
        value = apply_fixed_modifier(value, 5325)
        _announce_and_consume_item(battle, ctx.attacker)
    return HandlerReturn(value=value)


def はっきんだま_modify_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """はっきんだま: ギラティナ(アナザー/オリジン問わず)持ちのドラゴン・ゴースト技1.2倍。"""
    return _dedicated_item_modify_power(
        ctx, value, frozenset({"ギラティナ(アナザー)", "ギラティナ(オリジン)"}), ("ドラゴン", "ゴースト")
    )


def ハバンのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="ドラゴン", modifier=2048/4096)


def バコウのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="ひこう", modifier=2048/4096)


def バンジのみ_heal_on_quarter_hp(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """バンジのみ: HPが1/4以下になった瞬間に最大HPの1/3を回復するが、
    とくぼうが上がりにくい性格（やんちゃ・のうてんき・うっかりや・むじゃき）は
    にがい味を嫌うためこんらんする。
    """
    return _heal_berry(
        battle, ctx, value, denominator=4, heal_r=1/3,
        confuse_natures=("やんちゃ", "のうてんき", "うっかりや", "むじゃき"),
    )


def ばんのうがさ_weather_immune(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ばんのうがさ: はれ・あめ系の天候の影響を受けない。

    battle.weather_for() から ON_CHECK_WEATHER_IMMUNE 経由で参照される。
    """
    if battle.weather.name in ("はれ", "あめ", "おおひでり", "おおあめ"):
        return HandlerReturn(True)
    return HandlerReturn(value)


def パワフルハーブ_skip_charge(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """パワフルハーブ: 溜め技の溜めターンをスキップする。

    Event.ON_MOVE_CHARGE は全ての技実行のたびに発火する汎用イベントのため、
    ctx.move が実際に2ターン技（溜め技）かどうかをまず判定する。溜め技は
    自身の MoveData.handlers に Event.ON_MOVE_CHARGE のハンドラ
    （charge_into_volatile 等）を登録しているため、これが存在しない場合
    （くらいつく等の通常技や、ブラッドムーン/デカハンマーのような反動で
    動けなくなる系の技）は何もせず後続のハンドラへ処理を委ねる。

    溜めをスキップした結果、おおひでり下のダイビングのように技自体が
    天候によって無効化される場合（ON_TRY_MOVE_1 で判定）は、アイテムを消費しない。
    """
    if Event.ON_MOVE_CHARGE not in ctx.move.data.handlers:
        return HandlerReturn(value=value)

    mon = ctx.attacker
    weather_blocks_move = (
        (battle.weather.name == "おおひでり" and ctx.move.type == "みず")
        or (battle.weather.name == "おおあめ" and ctx.move.type == "ほのお")
    )
    if not weather_blocks_move:
        _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=True, stop_event=True)


def パンチグローブ_boost_punch_power(_battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """パンチグローブ: パンチ技の威力を1.1倍にする。"""
    if ctx.move.has_flag("punch"):
        value = apply_fixed_modifier(value, 4506)
    return HandlerReturn(value=value)


def パンチグローブ_negate_punch_contact(_battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """パンチグローブ: パンチ技の接触判定を無効化する。"""
    if ctx.move.has_flag("punch"):
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ひかりごけ_boost_spdef_on_water_hit(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ひかりごけ: みず技でダメージを受けたときとくぼう+1。"""
    return _boost_stat_on_type_hit(battle, ctx, value, type_="みず", stats={"spd": +1})


def ひかりのこな_reduce_accuracy(_battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ひかりのこな: 命中率を0.9倍にする（一撃必殺技を除く）。

    value が None の場合は既に必中状態が確定しているため、補正をかけずそのまま返す。
    """
    if value is not None and not ctx.move.has_flag("ohko"):
        value = apply_fixed_modifier(value, 3686)
    return HandlerReturn(value=value)


def ひかりのねんど_resolve_field_count(_battle: Battle, _ctx: EventContext, value: Any) -> HandlerReturn:
    return _resolve_field_count(value, "リフレクター", "ひかりのかべ", "オーロラベール", additonal_count=3)


def ひのたまプレート_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="ほのお", modifier=4915)


def himeri_pp_restore_cap(mon: Pokemon) -> int:
    """ヒメリのみ: 回復するPP量（じゅくせい所持時は2倍の20）。"""
    return 20 if is_ripen(mon) else 10

def himeri_select_move_to_restore(mon: Pokemon) -> Move | None:
    """ヒメリのみ: PPが0の技が複数ある場合に回復対象を選ぶ（なげつける・むしくい・
    ついばむ・ほおばる・おちゃかい等、使用中の技以外から発動する経路で使う）。

    最後にPPを消費した技（pp_consumed_move）がPP0であればそれを優先し、
    なければ技リストの先頭にあるPP0の技を対象にする
    （一次情報 .internal/spec/items/ヒメリのみ.md「第五世代以降」の優先順位）。
    """
    move = mon.pp_consumed_move
    if move is not None and move.pp == 0:
        return move
    return next((m for m in mon.moves if m.pp == 0), None)


def ヒメリのみ_restore_pp(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ヒメリのみ: 使用した技のPPが0になったときPPを回復する。"""
    mon = ctx.attacker
    if ctx.move.pp == 0:
        ctx.move.pp = min(himeri_pp_restore_cap(mon), ctx.move.data.pp)
        _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)


def ヒメリのみ_restore_pp_if_any_move_empty(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ヒメリのみ: PPが0の技があれば回復する。

    Event.ON_SWITCH_IN（場に出た直後にPPが0の技を持っていた場合）・
    Event.ON_ITEM_ENABLED（マジックルーム・ぶきよう等でアイテムが無効化されていた間に
    PPが0になり、無効化解除後もPPが0のままだった場合）・
    Event.ON_FORCE_BERRY_TRIGGER（むしくい・ついばむ・ほおばる・おちゃかいで
    強制発動する場合）から呼ばれる共通ロジック。
    """
    mon = ctx.source
    assert mon is not None
    move = himeri_select_move_to_restore(mon)
    if move is not None:
        move.pp = min(himeri_pp_restore_cap(mon), move.data.pp)
        _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)


def ビアーのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="どく", modifier=2048/4096)


def ビビリだま_boost_speed_on_intimidate(battle: Battle, ctx: EventContext, value: dict) -> HandlerReturn:
    """ビビリだま: いかくでこうげきが変化するはずだったときすばやさ+1。

    しろいきり・かいりきバサミ/クリアボディ/しろいけむり/メタルプロテクト/フラワーベール・
    きもったま/せいしんりょく/どんかん/マイペースでいかくの効果が無効化された場合でも発動する
    （ON_BEFORE_MODIFY_STAT の中で他の無効化ハンドラより先に判定するため）。
    あまのじゃく/ばんけん所持者はいかくで逆にこうげきが上昇するが、その場合も発動する。
    こうげきが既に最低ランク（あまのじゃく/ばんけん所持者は最大ランク）で
    いかくが不発だった場合や、みがわり状態（いかく自体が発動しないため本ハンドラも呼ばれない）
    では発動しない。
    ミラーアーマー所持者自身がいかくを跳ね返した時点では発動しない。
    すばやさが既に最大（あまのじゃく所持者ならすばやさが既に最小）で
    battle.modify_stats が不発だった場合は発動・消費しない。
    """
    mon = ctx.target
    assert mon is not None
    if (
        ctx.stat_change_reason != "いかく"
        or "atk" not in value
        or mon.ability.name == "ミラーアーマー"
    ):
        return HandlerReturn(value=value)
    reversed_direction = mon.ability.name in ("あまのじゃく", "ばんけん")
    at_limit = mon.boosts["atk"] >= 6 if reversed_direction else mon.boosts["atk"] <= -6
    if not at_limit and battle.modify_stats(mon, {"spe": +1}):
        _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)


def ピントレンズ_boost_critical_rank(battle: Battle, ctx: AttackContext, value: int) -> HandlerReturn:
    """ピントレンズ: 急所ランクを+1する。"""
    return HandlerReturn(value=value + 1)


def フィラのみ_heal_on_quarter_hp(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """フィラのみ: HPが1/4以下になった瞬間に最大HPの1/3を回復するが、
    こうげきが上がりにくい性格（ずぶとい・ひかえめ・おだやか・おくびょう）は
    からい味を嫌うためこんらんする。
    """
    return _heal_berry(
        battle, ctx, value, denominator=4, heal_r=1/3,
        confuse_natures=("ずぶとい", "ひかえめ", "おだやか", "おくびょう"),
    )


def ふうせん_check_floating(_battle: Battle, _ctx: EventContext, _value: Any) -> HandlerReturn:
    """ふうせん: 持たせたポケモンを地面にいない（浮いている）扱いにする。"""
    return HandlerReturn(value=True)


def ふうせん_pop_on_hit(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ふうせん: 攻撃技が有効だった場合に割れて消費される。

    ON_HITはダメージ量に関わらず（みがわりに肩代わりさせた場合やばけのかわ・
    アイスフェイスで肩代わりした場合、ダメージ量が補正で0になった場合を含む）
    攻撃技が無効化されずに命中した時点で発火するため、これらのケースでも
    正しくふうせんが割れる。

    割れたふうせんはものひろい・リサイクルの対象にならないため track_loss=False を指定する
    （なげつけるでふうせんを消費した場合は別経路で処理され、対象になる）。
    """
    mon = ctx.defender
    assert mon is not None
    _announce_and_consume_item(battle, mon, track_loss=False)
    return HandlerReturn(value=value)


def フォーカスレンズ_boost_accuracy_second(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """フォーカスレンズ: そのターンにすでに行動している相手に対して使う技の命中率を1.2倍にする。

    - 一撃必殺技には効果がない。
    - 交代してきたばかりで技を未使用の相手には効果がない（第五世代以降の仕様）。
    - value が None の場合は既に必中状態が確定しているため、補正をかけずそのまま返す。
    """
    if value is None or ctx.move.has_flag("ohko"):
        return HandlerReturn(value=value)

    defender = ctx.defender
    assert defender is not None
    defender_player = battle.get_player(defender)
    if battle.player_states[defender_player].has_switched:
        return HandlerReturn(value=value)

    attacker_player = battle.get_player(ctx.attacker)
    is_second = battle.query.is_second_actor(attacker_player)
    if is_second is None:
        is_second = defender.last_move is not None

    if is_second:
        value = apply_fixed_modifier(value, 4915)
    return HandlerReturn(value=value)


def ふしぎのプレート_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="エスパー", modifier=4915)


def ブーストエナジー_prevent_item_change(battle: Battle, ctx: EventContext, value: bool) -> HandlerReturn:
    """ブーストエナジー: こだいかっせい/クォークチャージ持ちが絡む奪取/交換を防ぐ。

    - 保持者自身がこだいかっせい/クォークチャージ持ちの場合、
      トリック・すりかえ・はたきおとす・どろぼう等による外部からの授受を防ぐ
      （渡す/奪われる双方）。ただし、ブースト発動に伴う自己消費（source が自分自身）は防がない。
      特性がかがくへんかガス等で無効化されているときでも、この効果は無効にならないため
      base_name（無効化状態に関わらない元の特性名）で判定する。
    - 保持者がそうでない場合でも、トリック・すりかえ・どろぼう等の交換相手
      （ctx.is_exchange が立つ swap_items 経由の判定における相手側）が
      こだいかっせい/クォークチャージ持ちなら、その相手にブーストエナジーが
      渡ることを防ぐ。
      はたきおとす等 is_exchange を立てない単純消失処理では相手側の判定を行わない。
    """
    mon = ctx.target
    if mon is None:
        return HandlerReturn(value=value)

    paradox_abilities = ("こだいかっせい", "クォークチャージ")
    if mon.ability.base_name in paradox_abilities and ctx.source is not mon:
        return HandlerReturn(value=False, stop_event=True)

    if ctx.is_exchange:
        foe = battle.foe(mon)
        if foe is not None and foe.ability.base_name in paradox_abilities:
            return HandlerReturn(value=False, stop_event=True)

    return HandlerReturn(value=value)


def ブーストエナジー_refresh_paradox_charge(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ブーストエナジー: アイテム有効化・取得時にパラドックスブーストを再判定する。"""
    return paradox.refresh_paradox_charge_state(battle, ctx, value)


def ホズのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ホズのみ: ノーマルタイプの技のダメージを1/2にして消費する（抜群不要）。"""
    return _modify_super_effective_damage(
        battle, ctx, value, type_="ノーマル", modifier=2048/4096, super_effective_only=False
    )


def ぼうごパット_block_contact_reaction(_battle: Battle, _ctx: AttackContext, _value: Any) -> HandlerReturn:
    """ぼうごパット: 相手が自分の接触を受けたことに反応する効果（ゴツゴツメット・さめはだ等）を防ぐ。

    Note:
        技自体は接触技のままであり、かたいツメ/どくしゅ/ふかしのこぶしのように
        自分の技が接触技であることに由来する効果や、もふもふ/わるいてぐせの効果は防がない。
    """
    return HandlerReturn(value=False, stop_event=True)


def ぼうじんゴーグル_block_powder_move(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ぼうじんゴーグル: 粉技を無効化する。"""
    if ctx.move.has_flag("powder"):
        _announce_item_triggered(battle, ctx.defender)
        return HandlerReturn(value=False, stop_event=True)
    return HandlerReturn(value=value)


def ぼうじんゴーグル_block_weather_damage(_battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ぼうじんゴーグル: 天候によるターン終了ダメージを無効化する。"""
    if ctx.hp_change_reason == "sandstorm":
        return HandlerReturn(value=0, stop_event=True)
    return HandlerReturn(value=value)


def まがったスプーン_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="エスパー", modifier=4915)


def マゴのみ_heal_on_quarter_hp(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """マゴのみ: HPが1/4以下になった瞬間に最大HPの1/3を回復するが、
    はやさが上がりにくい性格（ゆうかん・れいせい・のんき・なまいき）は
    あまい味を嫌うためこんらんする。
    """
    return _heal_berry(
        battle, ctx, value, denominator=4, heal_r=1/3,
        confuse_natures=("ゆうかん", "れいせい", "のんき", "なまいき"),
    )


def ミクルのみ_boost_accuracy(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ミクルのみ: 命中率フラグが立っているとき次の技の命中率を1.2倍にする。

    一撃必殺技は命中率が固定式（レベル差依存）のため倍率は適用されないが、
    効果自体は消費される。value が None の場合（既に必中状態が確定している場合）も
    同様に倍率は適用しないが、効果自体は消費される。
    """
    mon = ctx.attacker
    if mon.item.count == 1:
        battle.item_manager.consume_item(mon)
        if value is not None and not ctx.move.has_flag("ohko"):
            return HandlerReturn(value=apply_fixed_modifier(value, 4915))
    return HandlerReturn(value=value)


def ミクルのみ_clear_flag_after_move(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ミクルのみ: 命中判定のない技（命中率None）を使ったときなど、
    ON_MODIFY_ACCURACYで消費されなかった場合でも行動完了時に効果を消す。

    行動不能（状態異常・ひるみ等）や溜め技の溜めターンでは効果を維持する。
    """
    mon = ctx.attacker
    if mon.item.count != 1:
        return HandlerReturn(value=value)
    executor = battle.move_executor
    if executor.action_success is False:
        return HandlerReturn(value=value)
    if (
        executor.move_success is None
        and executor.move_applied is None
        and not executor.move_missed
    ):
        return HandlerReturn(value=value)
    battle.item_manager.consume_item(mon)
    return HandlerReturn(value=value)


def ミクルのみ_set_accuracy_flag(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ミクルのみ: HP1/4以下に下がった瞬間に命中率アップフラグを立てる。

    こんらんの自傷ダメージでは発動しない（第五世代以降の仕様）。
    くいしんぼう所持時は1/2HP以下に緩和される。
    """
    mon = ctx.target
    assert mon is not None
    if ctx.hp_change_reason == "self_attack":
        return HandlerReturn(value=value)
    denominator = _gluttony_denominator(mon, 4)
    hp_after = mon.hp
    hp_before = hp_after + value
    if hp_before * denominator > mon.max_hp and hp_after * denominator <= mon.max_hp:
        mon.item.count = 1
        _announce_item_triggered(battle, mon)
    return HandlerReturn(value=value)


def ミストシード_boost_spdef(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _terrain_seed_boost(battle, ctx, value, "ミストフィールド", "spd", "ミストシード")


def メタルコート_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="はがね", modifier=4915)


def メトロノーム_boost_power(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """メトロノーム: 同じ技を連続使用するたびに威力が上がる（最大2倍）。"""
    item = ctx.attacker.item
    if item.count > 0 and item.move_name == ctx.move.name:
        value = apply_fixed_modifier(value, 4096 + item.count * 819)
    return HandlerReturn(value=value)


def メトロノーム_update_count(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """メトロノーム: 技使用後に連続カウントを更新する。

    ON_END_MOVEは行動不能時（状態異常・ひるみなど）や溜め技の溜めターンも含めて
    必ず発火するため、以下のように場合分けする。
    - 技を出そうとすらしなかった場合（action_success is False）: カウントを維持
    - 溜め技の溜めターンなど、実際に攻撃を試みていない場合: カウントを維持
    - 技が無効化・失敗・ミスした場合: カウントを0にリセット
    - 技が成功した場合: 通常通りカウントを更新
    """
    executor = battle.move_executor
    item = ctx.attacker.item
    if executor.action_success is False:
        return HandlerReturn(value=value)
    if (
        executor.move_success is None
        and executor.move_applied is None
        and not executor.move_missed
    ):
        return HandlerReturn(value=value)
    if (
        executor.move_success is False
        or executor.move_applied is False
        or executor.move_missed
    ):
        item.count = 0
        return HandlerReturn(value=value)
    if item.move_name == ctx.move.name:
        item.count = min(item.count + 1, 5)
    else:
        item.move_name = ctx.move.name
        item.count = 1
    return HandlerReturn(value=value)


def メンタルハーブ_cure_mental_volatile(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """メンタルハーブ: 特定の揮発性状態が付与されたとき即解除する。"""
    mon = ctx.source
    assert mon is not None
    if value in {"メロメロ", "アンコール", "いちゃもん", "かなしばり", "ちょうはつ", "かいふくふうじ"}:
        battle.volatile_manager.remove(mon, value)
        _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)


def もうどくプレート_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="どく", modifier=4915)


def もくたん_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="ほのお", modifier=4915)


def ものしりメガネ_boost_special(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """特殊技1.1倍"""
    if ctx.move.category == "special":
        value = apply_fixed_modifier(value, 4505)
    return HandlerReturn(value=value)


def もののけプレート_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="ゴースト", modifier=4915)


def ものまねハーブ_copy_stat_boost(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ものまねハーブ: 相手のランク上昇を実際に上昇した分だけコピーする（1度きり）。

    相手のびんじょう・ものまねハーブによるコピーで上がった分は、再度のコピー対象にしない。
    また、コピーしても実際にランクが変化しなかった場合（自分のランクが既に最大等）は
    アイテムを消費しない。
    """
    if ctx.stat_change_reason in ("びんじょう", "ものまねハーブ"):
        return HandlerReturn(value=value)
    mon = battle.foe(ctx.target)
    boosts = {s: v for s, v in value.items() if v > 0}
    if not boosts:
        return HandlerReturn(value=value)
    changed = battle.modify_stats(mon, boosts, source=ctx.target, reason="ものまねハーブ")
    if changed:
        _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)


def モモンのみ_cure_poison(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    return _cure_ailment_berry(battle, ctx, value, "どく", "もうどく")


def モモンのみ_cure_poison_on_apply(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """モモンのみ: どく・もうどく付与直後に治療して消費する。"""
    return _cure_ailment_berry_on_apply(battle, ctx, value, "どく", "もうどく")


def もりのプレート_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="くさ", modifier=4915)


def ヤタピのみ_boost_spatk(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ヤタピのみ: HP1/4以下でとくこう+1。"""
    return _boost_on_quarter_hp(battle, ctx, value, stat="spa", amount=+1)


def ヤチェのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="こおり", modifier=2048/4096)


def やわらかいすな_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="じめん", modifier=4915)


def ゆきだま_boost_attack_on_ice_hit(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """ゆきだま: こおり技でダメージを受けたときこうげき+1。"""
    return _boost_stat_on_type_hit(battle, ctx, value, type_="こおり", stats={"atk": +1})


def ようせいのハネ_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="フェアリー", modifier=4915)


def ヨプのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="かくとう", modifier=2048/4096)


def ヨロギのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="いわ", modifier=2048/4096)


def ラムのみ_cure_ailment_and_confusion(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ラムのみ: 状態異常・こんらんのいずれかがあれば回復する（ターン終了時等の保険的チェック用）。"""
    mon = ctx.source
    assert mon is not None
    if _cure_ailment_and_confusion(battle, mon):
        _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)


def ラムのみ_cure_ailment_and_confusion_on_apply_ailment(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ラムのみ: 状態異常付与直後に、重複しているこんらんも含めて回復する。"""
    mon = ctx.target
    assert mon is not None
    if _cure_ailment_and_confusion(battle, mon):
        _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)


def ラムのみ_cure_ailment_and_confusion_on_confuse(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ラムのみ: こんらん付与直後に、重複している状態異常も含めて回復する。"""
    mon = ctx.source
    assert mon is not None
    if value != "こんらん":
        return HandlerReturn(value=value)
    if _cure_ailment_and_confusion(battle, mon):
        _announce_and_consume_item(battle, mon)
    return HandlerReturn(value=value)


def りゅうのキバ_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="ドラゴン", modifier=4915)


def りゅうのプレート_modify_power_by_type(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_power_by_type(ctx.move, value, type_="ドラゴン", modifier=4915)


def リュガのみ_boost_defense(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """リュガのみ: HP1/4以下でぼうぎょ+1。"""
    return _boost_on_quarter_hp(battle, ctx, value, stat="def", amount=+1)


def リリバのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="はがね", modifier=2048/4096)


def リンドのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="くさ", modifier=2048/4096)


def _ルームサービス_try_trigger(battle: Battle, mon: Pokemon) -> None:
    """ルームサービス: すばやさ-1を試み、実際にランクが変化した場合のみ発動を通知して消費する。

    source=mon を明示することで、所持者自身によるランク低下として扱い、
    まけんき・かちきなど「相手による低下」を条件とする効果を誤発動させない。
    """
    changes = battle.modify_stats(mon, {"spe": -1}, source=mon)
    if changes:  # すでにランクが下限（あまのじゃくの場合は上限）の場合は不発・消費しない
        _announce_and_consume_item(battle, mon)


def ルームサービス_drop_speed_on_switch_in(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ルームサービス: トリックルーム状態の場に繰り出したときすばやさ-1。"""
    mon = ctx.source
    assert mon is not None
    if battle.get_global_field("トリックルーム").is_active:
        _ルームサービス_try_trigger(battle, mon)
    return HandlerReturn(value=value)


def ルームサービス_drop_speed_on_trick_room(battle: Battle, ctx: EventContext, value: Any) -> HandlerReturn:
    """ルームサービス: トリックルーム発動時にすばやさ-1。"""
    mon = ctx.source
    assert mon is not None
    if value.name == "トリックルーム":
        _ルームサービス_try_trigger(battle, mon)
    return HandlerReturn(value=value)


def _レッドカード_should_trigger(ctx: AttackContext) -> bool:
    """レッドカード: 発動条件（持たせたポケモン・攻撃者側の状態）を判定する共通ロジック。"""
    mon = ctx.defender
    assert mon is not None
    return not (
        mon.fainted
        or ctx.substitute_damage
        or ctx.hit_index != ctx.hit_count
        or ctx.attacker.fainted
        or (
            ctx.attacker.ability.name == "ちからずく"
            and ctx.move.has_flag("secondary_effect")
        )
    )

def _レッドカード_try_force_switch(battle: Battle, ctx: AttackContext) -> None:
    """レッドカード: 攻撃者をランダムな控えポケモンと強制交代させる共通ロジック。

    にげられない・バインド・フェアリーロックや特性かげふみ・ありじごく・じりょくなどの
    とらわれ状態は無視して発動するため、can_switch は使わず控えの生存有無のみを見る。
    """
    mon = ctx.defender
    assert mon is not None
    foe = ctx.attacker
    opponent = battle.get_player(foe)
    state = battle.player_states[opponent]
    bench = state.bench
    commands = [
        Command.get_switch_command(i)
        for i, m in enumerate(state.team)
        if m in bench and m.alive
    ]
    if not commands:
        return

    _announce_and_consume_item(battle, mon)

    # ねをはる状態・特性きゅうばん/ばんけんの相手は交代させられないが、アイテムは消費される。
    if foe.has_volatile("ねをはる") or foe.ability.name in ("きゅうばん", "ばんけん"):
        return

    command = battle.random.choice(commands)
    battle.run_switch(opponent, state.team[command.index])


def レッドカード_force_switch(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """レッドカード: 実HPダメージ(>0)を受けたとき、攻撃者をランダムな控えポケモンと
    強制交代させる。

    みがわりに阻まれた場合・特性ちからずくの効果が発動した技を受けた場合は発動しない。
    連続攻撃技は最後のヒットでのみ判定する。持たせたポケモンが既にひんしの場合や、
    攻撃者が反動・自滅技によって既にひんしになっている場合は発動しない。
    実HPダメージが0の場合（ばけのかわ/アイスフェイスの肩代わり、こらえる等）は
    Event.ON_DAMAGE_HIT が発火しないため、レッドカード_force_switch_on_zero_damage
    （Event.ON_HIT）側で処理する。
    """
    if _レッドカード_should_trigger(ctx):
        _レッドカード_try_force_switch(battle, ctx)
    return HandlerReturn(value=value)


def レッドカード_force_switch_on_zero_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """レッドカード: 実HPダメージが0だった場合（ばけのかわ/アイスフェイスの肩代わり、
    こらえる等で耐えた場合）に発動する。

    Event.ON_DAMAGE_HIT は実HPダメージが0のとき発火しないため、常に発火する
    Event.ON_HIT 側でこのケース（value<=0）のみを処理する。実HPダメージが正の場合は
    レッドカード_force_switch（Event.ON_DAMAGE_HIT）側で処理するため、ここでは何もしない。
    """
    if value <= 0 and _レッドカード_should_trigger(ctx):
        _レッドカード_try_force_switch(battle, ctx)
    return HandlerReturn(value=value)


def レンブのみ_retaliate_special(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    """レンブのみ: 特殊技でダメージを受けたとき攻撃者に最大HPの1/8ダメージ。"""
    return _retaliate_on_category(battle, ctx, value, "special")


def ロゼルのみ_modify_super_effective_damage(battle: Battle, ctx: AttackContext, value: Any) -> HandlerReturn:
    return _modify_super_effective_damage(battle, ctx, value, type_="フェアリー", modifier=2048/4096)
