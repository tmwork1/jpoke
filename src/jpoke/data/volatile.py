"""揮発状態データ定義モジュール。

Note:
    このモジュール内の揮発状態定義はVOLATILES辞書内で五十音順に配置されています。
"""
from jpoke.enums import Event, LethalEvent
from jpoke.core.lethal import LethalHandler
from jpoke.handlers import volatile as h
from jpoke.handlers import lethal as l
from .models import VolatileData


def common_setup() -> None:
    """
    各VOLATILEのハンドラにログ用のテキスト（名前）を設定する。

    この関数は、VOLATILESディクショナリ内の全てのVolatileDataに対して、
    これにより、ハンドラ実行時のログ出力で状態名を表示できます。

    呼び出しタイミング: モジュール初期化時（ファイル末尾）
    """
    for name, data in VOLATILES.items():
        data.name = name


VOLATILES: dict[str, VolatileData] = {
    "": VolatileData(),
    "アクアリング": VolatileData(
        handlers={
            Event.ON_TURN_END: h.VolatileHandler(
                h.アクアリング_self_heal,
                subject_spec="source:self",
                priority=70,
            ),
        },
        lethal_handlers={
            LethalEvent.ON_TURN_END: LethalHandler(func=l.アクアリング_heal, subject="defender")
        }
    ),
    "あなをほる": VolatileData(
        forced=True,
        handlers={
            Event.ON_CHECK_TRAPPED: h.VolatileHandler(
                h.check_trapped_not_ghost,
                subject_spec="source:self",
            ),
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                h.force_command,
                subject_spec="source:self",
            ),
            Event.ON_CALC_POWER_MODIFIER: h.VolatileHandler(
                h.あなをほる_boost_power,
                subject_spec="defender:self",
            ),
            Event.ON_TRY_MOVE_1: h.VolatileHandler(
                h.あなをほる_can_hit_hidden_target,
                subject_spec="defender:self",
                priority=50,
            ),
            # 2ターン目の技実行完了時にため状態を解除する。命中・命中失敗に加えて
            # タイプ相性による無効化等（move_executor._check_hit_by_type等の早期return
            # 経路）でも確実に解除するため、経路を問わず必ず発火するON_MOVE_ENDへ登録する
            # （ON_HIT/ON_MISS個別登録では対応できない経路があり、解除されないまま
            # 永久に行動不能になる不具合があったため統一した）。
            Event.ON_MOVE_END: h.VolatileHandler(
                h.あなをほる_remove_volatile,
                subject_spec="attacker:self",
            ),
        }
    ),
    "あばれる": VolatileData(
        forced=True,
        handlers={
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                h.force_command,
                subject_spec="source:self",
            ),
            # ON_DAMAGE_HIT ではなく ON_HIT に登録する。ON_DAMAGE_HIT は
            # みがわり等で実ダメージが0になった場合に発火しないが、みがわりに
            # 被弾した場合も技自体は正常に命中・実行されたものとして扱われ、
            # あばれる状態のターンカウントは通常どおり進行するべきである
            # （.internal/spec/volatiles/あばれる.md の消滅条件3には該当しない）。
            # ON_HIT は「ダメージ発生後の処理（みがわりに被弾しても発動）」
            # (.internal/spec/turn.md) ため、この用途に適する。
            Event.ON_HIT: h.VolatileHandler(
                h.あばれる_tick,
                subject_spec="attacker:self",
                priority=180
            ),
        }
    ),
    "あめまみれ": VolatileData(
        handlers={
            Event.ON_TURN_END: h.VolatileHandler(
                h.あめまみれ_turn_end,
                subject_spec="source:self",
            ),
        }
    ),
    "アンコール": VolatileData(
        handlers={
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                h.アンコール_restrict_commands,
                subject_spec="source:self",
            ),
            Event.ON_MODIFY_MOVE: h.VolatileHandler(
                h.アンコール_modify_move,
                subject_spec="attacker:self",
                priority=20
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.アンコール_tick_volatile,
                subject_spec="source:self",
                priority=110
            ),
        }
    ),
    "いちゃもん": VolatileData(
        handlers={
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                h.いちゃもん_modify_command_options,
                subject_spec="source:self",
            )
        }
    ),
    "うちおとす": VolatileData(
        handlers={
            Event.ON_CHECK_FLOATING: h.VolatileHandler(
                h.うちおとす_check_floating,
                subject_spec="source:self",
            ),
        }
    ),
    "おんねん": VolatileData(
        handlers={
            Event.ON_TRY_ACTION: h.VolatileHandler(
                h.おんねん_remove_volatile,
                subject_spec="attacker:self",
                priority=10
            ),
            Event.ON_MOVE_KO: h.VolatileHandler(
                h.おんねん_deplete_attacking_move_pp,
                subject_spec="defender:self",
                priority=10,
                allow_fainted_subject=True,  # 自身が瀕死になった(ON_MOVE_KO)ことがこの効果の発動条件
            ),
        }
    ),
    "かいふくふうじ": VolatileData(
        handlers={
            Event.ON_MODIFY_HEAL: h.VolatileHandler(
                h.かいふくふうじ_block_heal,
                subject_spec="target:self",
            ),
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                h.かいふくふうじ_modify_command_options,
                subject_spec="source:self",
            ),
            Event.ON_TRY_ACTION: h.VolatileHandler(
                h.かいふくふうじ_try_action,
                subject_spec="attacker:self",
                priority=100
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.かいふくふうじ_tick_volatile,
                subject_spec="source:self",
                priority=110
            ),
        }
    ),
    "かなしばり": VolatileData(
        handlers={
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                h.かなしばり_modify_command_options,
                subject_spec="source:self",
            ),
            Event.ON_TRY_ACTION: h.VolatileHandler(
                h.かなしばり_try_action,
                subject_spec="attacker:self",
                priority=100
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.かなしばり_tick_volatile,
                subject_spec="source:self",
                priority=110
            ),
        }
    ),
    "きゅうしょアップ": VolatileData(
        handlers={
            Event.ON_CALC_CRITICAL_RANK: h.VolatileHandler(
                h.きゅうしょアップ_boost_critical_rank,
                subject_spec="attacker:self",
            ),
        }
    ),
    "きょけんとつげき": VolatileData(
        handlers={
            Event.ON_MODIFY_ACCURACY: h.VolatileHandler(
                h.きょけんとつげき_guaranteed_hit,
                subject_spec="defender:self",
            ),
            Event.ON_CALC_DAMAGE_MODIFIER: h.VolatileHandler(
                h.きょけんとつげき_double_damage,
                subject_spec="defender:self",
            ),
            Event.ON_TRY_ACTION: h.VolatileHandler(
                h.きょけんとつげき_remove,
                subject_spec="attacker:self",
                priority=10,
            ),
        }
    ),
    "くちばしキャノン": VolatileData(
        handlers={
            Event.ON_DAMAGE_HIT: h.VolatileHandler(
                h.くちばしキャノン_burn_on_contact,
                subject_spec="defender:self",
                allow_fainted_subject=True,  # 使用者が接触技でひんしになった場合でも攻撃者をやけどにする
            ),
            Event.ON_TRY_ACTION: h.VolatileHandler(
                h.くちばしキャノン_end_heating,
                subject_spec="attacker:self",
                priority=5,
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.くちばしキャノン_end_heating,
                subject_spec="source:self",
            ),
        }
    ),
    "こだわり": VolatileData(
        handlers={
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                h.こだわり_restrict_commands,
                subject_spec="source:self",
            )
        }
    ),
    "ころがる": VolatileData(
        forced=True,
        handlers={
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                h.force_command,
                subject_spec="source:self",
            ),
            Event.ON_CALC_POWER_MODIFIER: h.VolatileHandler(
                h.ころがる_boost_power,
                subject_spec="attacker:self",
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.ころがる_check_interrupt,
                subject_spec="source:self",
                priority=150,
            ),
        }
    ),
    "こらえる": VolatileData(
        handlers={
            # .internal/spec/turn.md の Event.ON_MODIFY_DAMAGE 表では60番と記載されているが、
            # 一撃必殺技の確定ダメージ算出（ohko_damage, priority=90。turn.md未掲載）より後に
            # 実行しないと、こらえるによる HP1 補正が ohko_damage の確定ダメージで
            # 上書きされてしまう。がんじょう/きあいのタスキ/きあいのハチマキ（100）より前、
            # ohko_damage（90）より後となる95を採用する
            # （.internal/plan/moves/こらえる.md「Priority根拠」参照）。
            Event.ON_MODIFY_MOVE_DAMAGE: h.VolatileHandler(
                h.こらえる_endure,
                subject_spec="defender:self",
                priority=95,
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.こらえる_remove_volatile,
                subject_spec="source:self",
            ),
        }
    ),
    "ごりむちゅう": VolatileData(
        # ロックした技名の保持のみ行う。実際の選択制限は特性側の
        # ON_MODIFY_COMMAND_OPTIONS ハンドラ（ごりむちゅう_restrict_commands）で行う。
        # かがくへんかガス等で特性が無効化されている間は選択制限を止める必要があるため、
        # 常に発動する VolatileHandler ではなく特性ハンドラ側に制限ロジックを持たせている。
        handlers={}
    ),
    "こんらん": VolatileData(
        handlers={
            Event.ON_TRY_ACTION: h.VolatileHandler(
                h.こんらん_try_action,
                subject_spec="attacker:self",
                priority=110
            ),
        }
    ),
    "コールドフレア": VolatileData(
        forced=True,
        handlers={
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                h.force_command,
                subject_spec="source:self",
            ),
            # 2ターン目の技実行完了時にため状態を解除する。命中・命中失敗に加えて
            # タイプ相性による無効化等（move_executor._check_hit_by_type等の早期return
            # 経路）でも確実に解除するため、経路を問わず必ず発火するON_MOVE_ENDへ登録する
            # （ON_HIT/ON_MISS個別登録では対応できない経路があり、解除されないまま
            # 永久に行動不能になる不具合があったため統一した）。
            Event.ON_MOVE_END: h.VolatileHandler(
                h.コールドフレア_remove_volatile,
                subject_spec="attacker:self",
            ),
        }
    ),
    "さわぐ": VolatileData(
        forced=True,
        handlers={
            Event.ON_VOLATILE_START: h.VolatileHandler(
                h.さわぐ_start,
                subject_spec="source:self",
            ),
            Event.ON_VOLATILE_END: h.VolatileHandler(
                h.さわぐ_remove_さわがしい,
                subject_spec="source:self",
            ),
            Event.ON_SWITCH_IN: h.VolatileHandler(
                h.さわぐ_apply_to_new_opponent,
                subject_spec="source:foe",
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.さわぐ_tick_volatile,
                subject_spec="source:self",
                priority=150
            ),
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                h.force_command,
                subject_spec="source:self",
            ),
            Event.ON_BEFORE_APPLY_AILMENT: h.VolatileHandler(
                h.さわぐ_prevent_sleep,
                subject_spec="target:self",
            ),
        }
    ),
    "さわがしい": VolatileData(
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.VolatileHandler(
                h.さわぐ_prevent_sleep,
                subject_spec="target:self",
            ),
        }
    ),
    "シャドーダイブ": VolatileData(
        forced=True,
        handlers={
            Event.ON_CHECK_TRAPPED: h.VolatileHandler(
                h.check_trapped_not_ghost,
                subject_spec="source:self",
            ),
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                h.force_command,
                subject_spec="source:self",
            ),
            Event.ON_TRY_MOVE_1: h.VolatileHandler(
                h.シャドーダイブ_can_hit_hidden_target,
                subject_spec="defender:self",
                priority=50,
            ),
            # 2ターン目の技実行完了時にため状態を解除する。命中・命中失敗に加えて
            # タイプ相性による無効化等（move_executor._check_hit_by_type等の早期return
            # 経路）でも確実に解除するため、経路を問わず必ず発火するON_MOVE_ENDへ登録する
            # （ON_HIT/ON_MISS個別登録では対応できない経路があり、解除されないまま
            # 永久に行動不能になる不具合があったため統一した）。
            Event.ON_MOVE_END: h.VolatileHandler(
                h.シャドーダイブ_remove_volatile,
                subject_spec="attacker:self",
            ),
        }
    ),
    "しおづけ": VolatileData(
        handlers={
            Event.ON_TURN_END: h.VolatileHandler(
                h.しおづけ_damage,
                subject_spec="source:self",
                priority=100,
            ),
        },
        lethal_handlers={
            LethalEvent.ON_TURN_END: LethalHandler(func=l.しおづけ_damage, subject="defender")
        }
    ),
    "じごくづき": VolatileData(
        handlers={
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                h.じごくづき_restrict_commands,
                subject_spec="source:self",
            ),
            Event.ON_TRY_ACTION: h.VolatileHandler(
                h.じごくづき_try_action,
                subject_spec="attacker:self",
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.じごくづき_tick_volatile,
                subject_spec="source:self",
                priority=110
            ),
        }
    ),
    "じゅうでん": VolatileData(
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.VolatileHandler(
                h.じゅうでん_boost_electric,
                subject_spec="attacker:self",
            ),
        }
    ),
    "そうでん": VolatileData(
        handlers={
            Event.ON_MODIFY_MOVE_TYPE: h.VolatileHandler(
                h.そうでん_move_type,
                subject_spec="attacker:self",
                # めざめるダンス等、使用者のタイプを参照して技タイプを決定する効果よりも
                # 後に評価し、でんきタイプへの変換を確実に優先させる。
                priority=110,
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.そうでん_turn_end,
                subject_spec="source:self",
                priority=110,
            ),
        }
    ),
    "そらをとぶ": VolatileData(
        forced=True,
        handlers={
            Event.ON_CHECK_TRAPPED: h.VolatileHandler(
                h.check_trapped_not_ghost,
                subject_spec="source:self",
            ),
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                h.force_command,
                subject_spec="source:self",
            ),
            Event.ON_CALC_POWER_MODIFIER: h.VolatileHandler(
                h.そらをとぶ_boost_power,
                subject_spec="defender:self",
            ),
            Event.ON_TRY_MOVE_1: h.VolatileHandler(
                h.そらをとぶ_can_hit_hidden_target,
                subject_spec="defender:self",
                priority=50,
            ),
            # 2ターン目の技実行完了時にため状態を解除する。命中・命中失敗に加えて
            # タイプ相性による無効化等（move_executor._check_hit_by_type等の早期return
            # 経路）でも確実に解除するため、経路を問わず必ず発火するON_MOVE_ENDへ登録する
            # （ON_HIT/ON_MISS個別登録では対応できない経路があり、解除されないまま
            # 永久に行動不能になる不具合があったため統一した）。
            Event.ON_MOVE_END: h.VolatileHandler(
                h.そらをとぶ_remove_volatile,
                subject_spec="attacker:self",
            ),
        }
    ),
    "ソーラービーム": VolatileData(
        forced=True,
        handlers={
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                h.force_command,
                subject_spec="source:self",
            ),
            # 2ターン目の技実行完了時にため状態を解除する。命中・命中失敗に加えて
            # タイプ相性による無効化等（move_executor._check_hit_by_type等の早期return
            # 経路）でも確実に解除するため、経路を問わず必ず発火するON_MOVE_ENDへ登録する
            # （ON_HIT/ON_MISS個別登録では対応できない経路があり、解除されないまま
            # 永久に行動不能になる不具合があったため統一した）。
            Event.ON_MOVE_END: h.VolatileHandler(
                h.ソーラービーム_remove_volatile,
                subject_spec="attacker:self",
            ),
        }
    ),
    "ソーラーブレード": VolatileData(
        forced=True,
        handlers={
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                h.force_command,
                subject_spec="source:self",
            ),
            # 2ターン目の技実行完了時にため状態を解除する。命中・命中失敗に加えて
            # タイプ相性による無効化等（move_executor._check_hit_by_type等の早期return
            # 経路）でも確実に解除するため、経路を問わず必ず発火するON_MOVE_ENDへ登録する
            # （ON_HIT/ON_MISS個別登録では対応できない経路があり、解除されないまま
            # 永久に行動不能になる不具合があったため統一した）。
            Event.ON_MOVE_END: h.VolatileHandler(
                h.ソーラーブレード_remove_volatile,
                subject_spec="attacker:self",
            ),
        }
    ),
    "ゴッドバード": VolatileData(
        forced=True,
        handlers={
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                h.force_command,
                subject_spec="source:self",
            ),
            # 2ターン目の技実行完了時にため状態を解除する。命中・命中失敗に加えて
            # タイプ相性による無効化等（move_executor._check_hit_by_type等の早期return
            # 経路）でも確実に解除するため、経路を問わず必ず発火するON_MOVE_ENDへ登録する
            # （ON_HIT/ON_MISS個別登録では対応できない経路があり、解除されないまま
            # 永久に行動不能になる不具合があったため統一した）。
            Event.ON_MOVE_END: h.VolatileHandler(
                h.ゴッドバード_remove_volatile,
                subject_spec="attacker:self",
            ),
        }
    ),
    "メテオビーム": VolatileData(
        forced=True,
        handlers={
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                h.force_command,
                subject_spec="source:self",
            ),
            # 2ターン目の技実行完了時にため状態を解除する。命中・命中失敗に加えて
            # タイプ相性による無効化等（move_executor._check_hit_by_type等の早期return
            # 経路）でも確実に解除するため、経路を問わず必ず発火するON_MOVE_ENDへ登録する
            # （ON_HIT/ON_MISS個別登録では対応できない経路があり、解除されないまま
            # 永久に行動不能になる不具合があったため統一した）。
            Event.ON_MOVE_END: h.VolatileHandler(
                h.メテオビーム_remove_volatile,
                subject_spec="attacker:self",
            ),
        }
    ),
    "エレクトロビーム": VolatileData(
        forced=True,
        handlers={
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                h.force_command,
                subject_spec="source:self",
            ),
            # 2ターン目の技実行完了時にため状態を解除する。命中・命中失敗に加えて
            # タイプ相性による無効化等（move_executor._check_hit_by_type等の早期return
            # 経路）でも確実に解除するため、経路を問わず必ず発火するON_MOVE_ENDへ登録する
            # （ON_HIT/ON_MISS個別登録では対応できない経路があり、解除されないまま
            # 永久に行動不能になる不具合があったため統一した）。
            Event.ON_MOVE_END: h.VolatileHandler(
                h.エレクトロビーム_remove_volatile,
                subject_spec="attacker:self",
            ),
        }
    ),
    "たくわえる": VolatileData(
        # Volatileではカウントの管理のみ行い、実際の効果は技のハンドラ側で処理
        handlers={}
    ),
    "タールショット": VolatileData(
        handlers={
            Event.ON_CALC_DEF_TYPE_MODIFIER: h.VolatileHandler(
                h.タールショット_boost_fire,
                subject_spec="defender:self",
            ),
        }
    ),
    "ダイビング": VolatileData(
        forced=True,
        handlers={
            Event.ON_CHECK_TRAPPED: h.VolatileHandler(
                h.check_trapped_not_ghost,
                subject_spec="source:self",
            ),
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                h.force_command,
                subject_spec="source:self",
            ),
            Event.ON_CALC_POWER_MODIFIER: h.VolatileHandler(
                h.ダイビング_boost_power,
                subject_spec="defender:self",
            ),
            Event.ON_TRY_MOVE_1: h.VolatileHandler(
                h.ダイビング_can_hit_hidden_target,
                subject_spec="defender:self",
                priority=50,
            ),
            # 2ターン目の技実行完了時にため状態を解除する。命中・命中失敗に加えて
            # タイプ相性による無効化等（move_executor._check_hit_by_type等の早期return
            # 経路）でも確実に解除するため、経路を問わず必ず発火するON_MOVE_ENDへ登録する
            # （ON_HIT/ON_MISS個別登録では対応できない経路があり、解除されないまま
            # 永久に行動不能になる不具合があったため統一した）。
            Event.ON_MOVE_END: h.VolatileHandler(
                h.ダイビング_remove_volatile,
                subject_spec="attacker:self",
            ),
        }
    ),
    "ちいさくなる": VolatileData(
        handlers={
            Event.ON_MODIFY_ACCURACY: h.VolatileHandler(
                h.ちいさくなる_guaranteed_hit,
                subject_spec="defender:self",
            ),
            Event.ON_CALC_POWER_MODIFIER: h.VolatileHandler(
                h.ちいさくなる_boost_power,
                subject_spec="defender:self",
            ),
        }
    ),
    "ちょうはつ": VolatileData(
        handlers={
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                h.ちょうはつ_modify_command_options,
                subject_spec="source:self",
            ),
            Event.ON_TRY_ACTION: h.VolatileHandler(
                h.ちょうはつ_try_action,
                subject_spec="attacker:self",
                priority=100
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.ちょうはつ_tick_volatile,
                subject_spec="source:self",
                priority=110
            ),
        }
    ),
    "でんじふゆう": VolatileData(
        handlers={
            Event.ON_CHECK_FLOATING: h.VolatileHandler(
                h.でんじふゆう_check_floating,
                subject_spec="source:self",
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.でんじふゆう_tick_volatile,
                subject_spec="source:self",
                priority=110
            ),
        }
    ),
    "デカハンマー": VolatileData(
        handlers={
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                h.デカハンマー_modify_command_options,
                subject_spec="source:self",
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.デカハンマー_tick_volatile,
                subject_spec="source:self",
            ),
        }
    ),
    "とくせいなし": VolatileData(
        handlers={
            Event.ON_VOLATILE_START: h.VolatileHandler(
                h.とくせいなし_disable_ability,
                subject_spec="source:self",
            ),
            Event.ON_VOLATILE_END: h.VolatileHandler(
                h.とくせいなし_enable_ability,
                subject_spec="source:self",
            ),
        }
    ),
    "にげられない": VolatileData(
        handlers={
            Event.ON_CHECK_TRAPPED: h.VolatileHandler(
                h.check_trapped_not_ghost,
                subject_spec="source:self",
            ),
            Event.ON_SWITCH_OUT: h.VolatileHandler(
                h.にげられない_remove_on_foe_switch,
                subject_spec="source:foe",
            ),
        }
    ),
    "ねむけ": VolatileData(
        handlers={
            Event.ON_TURN_END: h.VolatileHandler(
                h.ねむけ_tick_volatile,
                subject_spec="source:self",
                priority=110,
            ),
            Event.ON_VOLATILE_END: h.VolatileHandler(
                h.ねむけ_remove_and_apply_sleep,
                subject_spec="source:self",
            ),
        }
    ),
    "ねをはる": VolatileData(
        handlers={
            Event.ON_TURN_END: h.VolatileHandler(
                h.ねをはる_self_heal,
                subject_spec="source:self",
                priority=70
            ),
            Event.ON_CHECK_TRAPPED: h.VolatileHandler(
                h.check_trapped_not_ghost,
                subject_spec="source:self",
            ),
            Event.ON_CHECK_FLOATING: h.VolatileHandler(
                h.ねをはる_check_floating,
                subject_spec="source:self",
            ),
            Event.ON_TRY_BLOW: h.VolatileHandler(
                h.ねをはる_block_blow,
                subject_spec="defender:self",
            ),
        },
        lethal_handlers={
            LethalEvent.ON_TURN_END: LethalHandler(func=l.ねをはる_heal, subject="defender")
        }
    ),
    "のろい": VolatileData(
        handlers={
            Event.ON_TURN_END: h.VolatileHandler(
                h.のろい_damage,
                subject_spec="source:self",
                priority=100,
            ),
        },
        lethal_handlers={
            LethalEvent.ON_TURN_END: LethalHandler(func=l.のろい_damage, subject="defender")
        }
    ),
    "バインド": VolatileData(
        handlers={
            Event.ON_TURN_END: h.VolatileHandler(
                h.バインド_damage,
                subject_spec="source:self",
                priority=100
            ),
            Event.ON_CHECK_TRAPPED: h.VolatileHandler(
                h.check_trapped_not_ghost,
                subject_spec="source:self",
            ),
            Event.ON_SWITCH_OUT: h.VolatileHandler(
                h.バインド_remove,
                subject_spec="source:foe",
            ),
        },
        lethal_handlers={
            LethalEvent.ON_TURN_END: LethalHandler(func=l.バインド_damage, subject="defender")
        }
    ),
    "ひるみ": VolatileData(
        handlers={
            Event.ON_TRY_ACTION: h.VolatileHandler(
                h.ひるみ_block_action,
                subject_spec="attacker:self",
                priority=40,
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.ひるみ_remove_volatile,
                subject_spec="source:self",
            ),
        }
    ),
    "ふういん": VolatileData(
        handlers={
            Event.ON_TRY_ACTION: h.VolatileHandler(
                h.ふういん_try_action,
                subject_spec="defender:self",
                priority=100,
            ),
        }
    ),
    "フリーズボルト": VolatileData(
        forced=True,
        handlers={
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                h.force_command,
                subject_spec="source:self",
            ),
            # 2ターン目の技実行完了時にため状態を解除する。命中・命中失敗に加えて
            # タイプ相性による無効化等（move_executor._check_hit_by_type等の早期return
            # 経路）でも確実に解除するため、経路を問わず必ず発火するON_MOVE_ENDへ登録する
            # （ON_HIT/ON_MISS個別登録では対応できない経路があり、解除されないまま
            # 永久に行動不能になる不具合があったため統一した）。
            Event.ON_MOVE_END: h.VolatileHandler(
                h.フリーズボルト_remove_volatile,
                subject_spec="attacker:self",
            ),
        }
    ),
    "ブラッドムーン": VolatileData(
        handlers={
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                h.ブラッドムーン_modify_command_options,
                subject_spec="source:self",
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.ブラッドムーン_tick_volatile,
                subject_spec="source:self",
            ),
        }
    ),
    # へんしん状態であることを示すマーカー専用状態（ハンドラなし）。
    # 変身の実体（特性・技・実数値ステータス・タイプ・体重・性別のコピーと交代/瀕死時の復元）は
    # battle.transform()（core/battle.py）と Pokemon.reset_on_switch_out() が担い、
    # 本状態は「対象がへんしん状態か」を判定する各種失敗条件チェック専用。
    "へんしん": VolatileData(),
    "ほろびのうた": VolatileData(
        handlers={
            Event.ON_TURN_END: h.VolatileHandler(
                h.ほろびのうた_tick_volatile,
                subject_spec="source:self",
                priority=120
            ),
            Event.ON_VOLATILE_END: h.VolatileHandler(
                h.ほろびのうた_faint,
                subject_spec="source:self",
            )
        }
    ),
    "マジックコート": VolatileData(
        handlers={
            Event.ON_CHECK_REFLECT: h.VolatileHandler(
                h.マジックコート_reflect,
                subject_spec="defender:self",
                priority=200
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.マジックコート_turn_end,
                subject_spec="source:self",
            ),
        }
    ),
    "まるくなる": VolatileData(
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.VolatileHandler(
                h.まるくなる_boost_power,
                subject_spec="attacker:self",
            ),
        }
    ),
    "みがわり": VolatileData(
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.VolatileHandler(
                h.みがわり_immune,
                subject_spec="defender:self",
                priority=30,
            ),
            Event.ON_MODIFY_MOVE_DAMAGE: h.VolatileHandler(
                h.みがわり_block_damage,
                subject_spec="defender:self",
                priority=20,
            ),
        }
    ),
    "みちづれ": VolatileData(
        handlers={
            Event.ON_MOVE_KO: h.VolatileHandler(
                h.みちづれ_faint,
                subject_spec="defender:self",
                priority=30,
                allow_fainted_subject=True,  # 自身が瀕死になった(ON_MOVE_KO)ことがこの効果の発動条件
            ),
            Event.ON_TRY_ACTION: h.VolatileHandler(
                h.みちづれ_remove,
                subject_spec="attacker:self",
                priority=10,
            ),
        }
    ),
    "めいちゅうアップ": VolatileData(
        handlers={
            Event.ON_MODIFY_ACCURACY: h.VolatileHandler(
                h.めいちゅうアップ_boost_accuracy,
                subject_spec="attacker:self",
            ),
            Event.ON_END_MOVE: h.VolatileHandler(
                h.めいちゅうアップ_clear_after_move,
                subject_spec="attacker:self",
            ),
        }
    ),
    "メロメロ": VolatileData(
        handlers={
            Event.ON_TRY_ACTION: h.VolatileHandler(
                h.メロメロ_try_action,
                subject_spec="attacker:self",
                priority=130
            ),
        }
    ),
    "やどりぎのタネ": VolatileData(
        handlers={
            Event.ON_TURN_END: h.VolatileHandler(
                h.やどりぎのタネ_drain_hp,
                subject_spec="source:self",
                priority=80,
            ),
        },
        lethal_handlers={
            LethalEvent.ON_TURN_END: LethalHandler(func=l.やどりぎのタネ_damage, subject="defender")
        }
    ),
    "リチャージ": VolatileData(
        handlers={
            Event.ON_MODIFY_COMMAND_OPTIONS: h.VolatileHandler(
                h.force_command,
                subject_spec="source:self",
            ),
            Event.ON_TRY_ACTION: h.VolatileHandler(
                h.リチャージ_block_action,
                subject_spec="attacker:self",
                priority=10,
            ),
        }
    ),
    "れんぞくぎり": VolatileData(
        handlers={
            Event.ON_TURN_END: h.VolatileHandler(
                h.れんぞくぎり_reset_on_turn_end,
                subject_spec="source:self",
            ),
        }
    ),
    "ロックオン": VolatileData(
        handlers={
            Event.ON_MODIFY_ACCURACY: h.VolatileHandler(
                h.ロックオン_guarantee_hit,
                subject_spec="attacker:self",
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.ロックオン_tick_volatile,
                subject_spec="source:self",
            ),
            Event.ON_SWITCH_OUT: h.VolatileHandler(
                h.ロックオン_remove_volatile,
                subject_spec="source:foe",
            ),
        }
    ),
    "まもる": VolatileData(
        handlers={
            Event.ON_TRY_MOVE_1: h.VolatileHandler(
                h.まもる_protect,
                subject_spec="defender:self",
                priority=100,
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.まもる_remove_volatile,
                subject_spec="source:self",
            ),
        }
    ),
    "かえんのまもり": VolatileData(
        handlers={
            Event.ON_TRY_MOVE_1: h.VolatileHandler(
                h.かえんのまもり_protect,
                subject_spec="defender:self",
                priority=100,
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.かえんのまもり_remove_volatile,
                subject_spec="source:self",
            ),
        }
    ),
    "キングシールド": VolatileData(
        handlers={
            Event.ON_TRY_MOVE_1: h.VolatileHandler(
                h.キングシールド_protect,
                subject_spec="defender:self",
                priority=100,
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.キングシールド_remove_volatile,
                subject_spec="source:self",
            ),
        }
    ),
    "スレッドトラップ": VolatileData(
        handlers={
            Event.ON_TRY_MOVE_1: h.VolatileHandler(
                h.スレッドトラップ_protect,
                subject_spec="defender:self",
                priority=100,
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.スレッドトラップ_remove_volatile,
                subject_spec="source:self",
            ),
        }
    ),
    "トーチカ": VolatileData(
        handlers={
            Event.ON_TRY_MOVE_1: h.VolatileHandler(
                h.トーチカ_protect,
                subject_spec="defender:self",
                priority=100,
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.トーチカ_remove_volatile,
                subject_spec="source:self",
            ),
        }
    ),
    "ニードルガード": VolatileData(
        handlers={
            Event.ON_TRY_MOVE_1: h.VolatileHandler(
                h.ニードルガード_protect,
                subject_spec="defender:self",
                priority=100,
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.ニードルガード_remove_volatile,
                subject_spec="source:self",
            ),
        }
    ),
    "ファストガード": VolatileData(
        handlers={
            Event.ON_TRY_MOVE_1: h.VolatileHandler(
                h.ファストガード_protect,
                subject_spec="defender:self",
                priority=100,
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.ファストガード_remove_volatile,
                subject_spec="source:self",
            ),
        }
    ),
    "ワイドガード": VolatileData(
        # まもる・ファストガード等と同じprotect系の骨格。判定基準のみ異なる
        # （is_blocked_by_wide_guard: "spread"フラグを持つ技を防ぐ）。
        handlers={
            Event.ON_TRY_MOVE_1: h.VolatileHandler(
                h.ワイドガード_protect,
                subject_spec="defender:self",
                priority=100,
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.ワイドガード_remove_volatile,
                subject_spec="source:self",
            ),
        }
    ),
    "ハロウィン": VolatileData(
        handlers={
            Event.ON_VOLATILE_START: h.VolatileHandler(
                h.ハロウィン_add_type,
                subject_spec="source:self",
            ),
            Event.ON_VOLATILE_END: h.VolatileHandler(
                h.ハロウィン_remove_type,
                subject_spec="source:self",
            ),
        }
    ),
    "はねやすめ": VolatileData(
        handlers={
            Event.ON_VOLATILE_START: h.VolatileHandler(
                h.はねやすめ_remove_flying,
                subject_spec="source:self",
            ),
            Event.ON_TURN_END: h.VolatileHandler(
                h.はねやすめ_restore_flying,
                subject_spec="source:self",
                priority=120,
            ),
        }
    ),
    "まほうのこな": VolatileData(
        handlers={
            Event.ON_VOLATILE_START: h.VolatileHandler(
                h.まほうのこな_set_type,
                subject_spec="source:self",
            ),
            Event.ON_VOLATILE_END: h.VolatileHandler(
                h.まほうのこな_clear_type,
                subject_spec="source:self",
            ),
        }
    ),
    "みずびたし": VolatileData(
        handlers={
            Event.ON_VOLATILE_START: h.VolatileHandler(
                h.みずびたし_set_type,
                subject_spec="source:self",
            ),
            Event.ON_VOLATILE_END: h.VolatileHandler(
                h.みずびたし_clear_type,
                subject_spec="source:self",
            ),
        }
    ),
    "もりののろい": VolatileData(
        handlers={
            Event.ON_VOLATILE_START: h.VolatileHandler(
                h.もりののろい_add_type,
                subject_spec="source:self",
            ),
            Event.ON_VOLATILE_END: h.VolatileHandler(
                h.もりののろい_remove_type,
                subject_spec="source:self",
            ),
        }
    ),
}


common_setup()
