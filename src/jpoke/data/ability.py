"""特性データ定義モジュール。

Note:
    このモジュール内の特性定義はABILITIES辞書内で五十音順に配置されています。
"""

from jpoke.enums import DomainEvent, Event, LethalEvent
from jpoke.core.lethal import LethalHandler
from jpoke.handlers import ability as h
from jpoke.handlers import ability_paradox as paradox
from jpoke.handlers import lethal as l
from jpoke.types import AbilityName

from .models import AbilityData


def common_setup():
    """共通のセットアップ処理"""
    for name in ABILITIES:
        ABILITIES[name].name = name


ABILITIES: dict[AbilityName, AbilityData] = {
    "": AbilityData(name=""),
    "ARシステム": AbilityData(
        flags={
            "uncopyable",
            "protected",
            "gas_proof",
        },
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.ARシステム_apply_type,
                subject_spec="source:self",
            ),
            Event.ON_CHECK_ITEM_CHANGE: h.AbilityHandler(
                h.ARシステム_prevent_item_change,
                subject_spec="target:self",
            ),
        }
    ),
    "アイスフェイス": AbilityData(
        flags={
            "uncopyable",
            "protected",
            "mold_breaker_ignorable",
            "gas_proof",
        },
        handlers={
            Event.ON_MODIFY_MOVE_DAMAGE: h.AbilityHandler(
                h.アイスフェイス_block_physical,
                subject_spec="defender:self",
                priority=40,
            ),
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.アイスフェイス_restore_on_switch_in,
                subject_spec="source:self",
                priority=140,
            ),
            Event.ON_FIELD_CHANGE: h.AbilityHandler(
                h.アイスフェイス_restore_on_snow,
                subject_spec="source:self",
            ),
        }
    ),
    "アイスボディ": AbilityData(
        handlers={
            Event.ON_TURN_END: h.AbilityHandler(
                h.アイスボディ_heal,
                subject_spec="source:self",
                priority=30,
            ),
        },
        lethal_handlers={
            LethalEvent.ON_TURN_END: LethalHandler(
                func=l.アイスボディ_heal,
                subject="defender",
            )
        }
    ),
    "あくしゅう": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.あくしゅう_maybe_flinch,
                subject_spec="attacker:self",
            )
        }
    ),
    "あついしぼう": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.あついしぼう_reduce_fire_ice,
                subject_spec="defender:self",
            )
        }
    ),
    "あとだし": AbilityData(
        handlers={
            DomainEvent.ON_CALC_BACK_TIER: h.AbilityHandler(
                h.あとだし_delay_move_order,
                subject_spec="attacker:self",
            ),
        }
    ),
    "アナライズ": AbilityData(
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.AbilityHandler(
                h.アナライズ_boost_power,
                subject_spec="attacker:self",
            )
        }
    ),
    "あまのじゃく": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_BEFORE_MODIFY_STAT: h.AbilityHandler(
                h.あまのじゃく_reverse_stat,
                subject_spec="target:self",
            )
        }
    ),
    "あめうけざら": AbilityData(
        handlers={
            Event.ON_TURN_END: h.AbilityHandler(
                h.あめうけざら_heal,
                subject_spec="source:self",
                priority=30,
            ),
        },
        lethal_handlers={
            LethalEvent.ON_TURN_END: LethalHandler(
                func=l.あめうけざら_heal,
                subject="defender",
            )
        }
    ),
    "あめふらし": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.あめふらし_activate_weather,
                subject_spec="source:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.あめふらし_activate_weather,
                subject_spec="source:self",
            ),
        }
    ),
    "ありじごく": AbilityData(
        handlers={
            Event.ON_CHECK_TRAPPED: h.AbilityHandler(
                h.ありじごく_check_trapped,
                subject_spec="source:foe",
            )
        }
    ),
    "アロマベール": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_BEFORE_APPLY_VOLATILE: h.AbilityHandler(
                h.アロマベール_prevent_volatile,
                subject_spec="target:self",
            )
        }
    ),
    "いかく": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.いかく_lower_foe_atk,
                subject_spec="source:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.いかく_lower_foe_atk,
                subject_spec="source:self",
            ),
        },
    ),
    "いかりのこうら": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.いかりのこうら_boost_on_half_hp,
                subject_spec="defender:self",
            )
        }
    ),
    "いかりのつぼ": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.いかりのつぼ_max_atk_on_crit,
                subject_spec="defender:self",
                priority=20,
            )
        }
    ),
    "いしあたま": AbilityData(
        handlers={
            Event.ON_MODIFY_NON_MOVE_DAMAGE: h.AbilityHandler(
                h.いしあたま_ignore_recoil,
                subject_spec="target:self",
            ),
        }
    ),
    "いたずらごころ": AbilityData(
        handlers={
            DomainEvent.ON_MODIFY_MOVE_PRIORITY: h.AbilityHandler(
                h.いたずらごころ_modify_move_priority,
                subject_spec="attacker:self",
            ),
            Event.ON_BEFORE_APPLY_MOVE: h.AbilityHandler(
                h.いたずらごころ_blocked_by_dark,
                subject_spec="attacker:self",
            ),
        }
    ),
    "いやしのこころ": AbilityData(),
    "イリュージョン": AbilityData(
        flags={
            "uncopyable"
        }
    ),
    "いろめがね": AbilityData(
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.AbilityHandler(
                h.いろめがね_boost_ineffective,
                subject_spec="attacker:self",
            )
        }
    ),
    "いわはこび": AbilityData(
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.いわはこび_modify_atk,
                subject_spec="attacker:self",
            )
        }
    ),
    "うなぎのぼり": AbilityData(
        flags={
            "mold_breaker_ignorable",
        },
        handlers={
            Event.ON_CHECK_FLOATING: h.AbilityHandler(
                h.ふゆう_float,
                subject_spec="source:self",
                allow_fainted_subject=True,  # 技のダメージ計算中に使用者が瀕死になっても浮遊判定は維持する
            ),
            Event.ON_MOVE_KO: h.AbilityHandler(
                h.ビーストブースト_boost_best_stat_on_ko,
                subject_spec="attacker:self",
                allow_fainted_subject=True,  # HPコスト技等で自身が瀕死になっても、撃破時(ON_MOVE_KO)の効果は発動する
            ),
        }
    ),
    "うのミサイル": AbilityData(
        flags={
            "protected",
            "gas_proof",
        },
        handlers={
            Event.ON_MOVE_CHARGE: h.AbilityHandler(
                h.うのミサイル_load_prey_on_charge,
                subject_spec="attacker:self",
                priority=90,
            ),
            Event.ON_MOVE_END: h.AbilityHandler(
                h.うのミサイル_load_prey,
                subject_spec="attacker:self",
            ),
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.うのミサイル_spit_out_prey,
                subject_spec="defender:self",
                # 攻撃を受けてウッウがひんしになったときも獲物を吐き出してダメージと効果を
                # 与える仕様（.internal/spec/abilities/うのミサイル.md）のため、瀕死主体でも
                # 発動を許可する。
                allow_fainted_subject=True,
            ),
            Event.ON_SWITCH_OUT: h.AbilityHandler(
                h.うのミサイル_revert_form,
                subject_spec="source:self",
                allow_fainted_subject=True,  # 瀕死交代(ON_SWITCH_OUT)でも発動する
            ),
        }
    ),
    "うるおいボイス": AbilityData(
        handlers={
            Event.ON_MODIFY_MOVE_TYPE: h.AbilityHandler(
                h.うるおいボイス_modify_move_type,
                subject_spec="attacker:self",
            ),
        }
    ),
    "うるおいボディ": AbilityData(
        handlers={
            Event.ON_TURN_END: h.AbilityHandler(
                h.うるおいボディ_cure_ailment_in_rain,
                subject_spec="source:self",
                priority=60,
            )
        }
    ),
    "エアロック": AbilityData(
        handlers={
            Event.ON_CHECK_WEATHER_ENABLED: h.AbilityHandler(
                h.エアロック_check_weather_enabled,
                subject_spec="source:self",
            ),
        },
    ),
    "エレキメイカー": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.エレキメイカー_activate_terrain,
                "source:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.エレキメイカー_activate_terrain,
                "source:self",
            ),
        }
    ),
    "えんかく": AbilityData(
        handlers={
            Event.ON_CHECK_CONTACT: h.AbilityHandler(
                h.えんかく_nullify_contact,
                subject_spec="attacker:self",
            )
        }
    ),
    "おうごんのからだ": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.AbilityHandler(
                h.おうごんのからだ_block_status_move,
                subject_spec="defender:self",
            )
        }
    ),
    "おどりこ": AbilityData(
        handlers={
            Event.ON_AFTER_ACTION_RESOLVED: h.AbilityHandler(
                h.おどりこ_copy_dance_move,
                subject_spec="source:foe",
            ),
        },
    ),
    "おみとおし": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.おみとおし_reveal_foe_item,
                subject_spec="source:self",
            ),
        }
    ),
    "おもかげやどし": AbilityData(
        flags={
            "uncopyable",
            "protected"
        },
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.おもかげやどし_boost_stat,
                subject_spec="source:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.おもかげやどし_boost_stat,
                subject_spec="source:self",
            ),
            Event.ON_TERASTALLIZE: h.AbilityHandler(
                h.おもかげやどし_boost_stat,
                subject_spec="source:self",
            ),
        }
    ),
    "おもてなし": AbilityData(),
    "おやこあい": AbilityData(
        handlers={
            Event.ON_MODIFY_HIT_COUNT: h.AbilityHandler(
                h.おやこあい_modify_hit_count,
                subject_spec="attacker:self",
            ),
            Event.ON_MODIFY_MOVE_DAMAGE: h.AbilityHandler(
                h.おやこあい_reduce_second_damage,
                subject_spec="attacker:self",
            )
        },
        lethal_handlers={
            LethalEvent.ON_BEFORE_HIT: LethalHandler(l.おやこあい_boost_damage, subject="attacker")
        }
    ),
    "おわりのだいち": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.おわりのだいち_activate_weather,
                "source:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.おわりのだいち_activate_weather,
                "source:self",
            ),
            Event.ON_SWITCH_OUT: h.AbilityHandler(
                h.おわりのだいち_deactivate_strong_weather,
                "source:self",
                allow_fainted_subject=True,  # 瀕死交代(ON_SWITCH_OUT)でも強制天候を解除する
            ),
            Event.ON_ABILITY_DISABLED: h.AbilityHandler(
                h.おわりのだいち_deactivate_strong_weather,
                "source:self",
                allow_fainted_subject=True,  # 瀕死交代(ON_SWITCH_OUT)でも強制天候を解除する
                ignored_disable_reasons=frozenset({"とくせいなし"}),  # 自身がとくせいなしで無効化された結果として発火するため、その理由は無視する
            ),
        },
    ),
    "オーラブレイク": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.announce_ability_triggered,
                subject_spec="source:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.announce_ability_triggered,
                subject_spec="source:self",
            ),
        }
    ),
    "かいりきバサミ": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_BEFORE_MODIFY_STAT: h.AbilityHandler(
                h.かいりきバサミ_block_A_drop,
                subject_spec="target:self",
            )
        }
    ),
    "かがくへんかガス": AbilityData(
        flags={
            "uncopyable",
            "gas_proof",
        },
        handlers={
            Event.ON_SWITCH_IN: [
                h.AbilityHandler(
                    h.かがくへんかガス_disable_foe_ability,
                    subject_spec="source:self",
                    priority=20,
                ),
                h.AbilityHandler(
                    h.かがくへんかガス_disable_new_foe,
                    subject_spec="source:foe",
                    priority=20,
                ),
            ],
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.かがくへんかガス_disable_foe_ability,
                subject_spec="source:self",
            ),
            Event.ON_SWITCH_OUT: h.AbilityHandler(
                h.かがくへんかガス_gas_deactivate,
                subject_spec="source:self",
                allow_fainted_subject=True,  # 瀕死交代(ON_SWITCH_OUT)でも発動する
            ),
            Event.ON_ABILITY_DISABLED: h.AbilityHandler(
                h.かがくへんかガス_gas_deactivate,
                subject_spec="source:self",
                # とくせいなし状態になった直後にガスの解除処理自身が
                # 無効化理由の判定でスキップされないようにする
                # （このハンドラの主体自身が「とくせいなし」で無効化された結果として
                # 発火するため、その理由だけは無視して発動させる必要がある）
                ignored_disable_reasons=frozenset({"とくせいなし"}),
            )
        }
    ),
    "かげふみ": AbilityData(
        handlers={
            Event.ON_CHECK_TRAPPED: h.AbilityHandler(
                h.かげふみ_check_trapped,
                subject_spec="source:foe",
            )
        }
    ),
    "かぜのり": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.AbilityHandler(
                h.かぜのり_absorb_wind,
                subject_spec="defender:self",
            ),
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.かぜのり_boost_atk_in_tailwind,
                subject_spec="source:self",
            ),
            Event.ON_FIELD_ACTIVATE: h.AbilityHandler(
                h.かぜのり_boost_atk_on_tailwind_start,
                subject_spec="source:self",
            ),
        }
    ),
    "かそく": AbilityData(
        handlers={
            Event.ON_TURN_END: h.AbilityHandler(
                h.かそく_boost_speed,
                subject_spec="source:self",
                priority=150,
            ),
        }
    ),
    "かたいツメ": AbilityData(
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.AbilityHandler(
                h.かたいツメ_modify_power,
                subject_spec="attacker:self",
            )
        }
    ),
    "かたやぶり": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.announce_ability_triggered,
                subject_spec="source:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.announce_ability_triggered,
                subject_spec="source:self",
            ),
            Event.ON_BEGIN_MOVE: h.AbilityHandler(
                h.かたやぶり_disable_foe_ability,
                subject_spec="attacker:self",
            ),
            Event.ON_END_MOVE: h.AbilityHandler(
                h.かたやぶり_restore_foe_ability,
                subject_spec="attacker:self",
            ),
        }
    ),
    "かちき": AbilityData(
        flags=set(),
        handlers={
            Event.ON_MODIFY_STAT: h.AbilityHandler(
                h.かちき_boost_spa_on_stat_drop,
                subject_spec="target:self",
            )
        }
    ),
    "カブトアーマー": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_MODIFY_CRITICAL_RATE: h.AbilityHandler(
                h.カブトアーマー_block_crit,
                subject_spec="defender:self",
            )
        }
    ),
    "かるわざ": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.かるわざ_init_state,
                subject_spec="source:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.かるわざ_init_state,
                subject_spec="source:self",
            ),
            Event.ON_ITEM_LOST: h.AbilityHandler(
                h.かるわざ_activate_on_item_lost,
                subject_spec="source:self",
            ),
            DomainEvent.ON_CALC_SPEED: h.AbilityHandler(
                h.かるわざ_modify_speed,
                subject_spec="source:self",
            ),
        }
    ),
    "かわりもの": AbilityData(
        flags={
            "uncopyable"
        },
        handlers={
            # ON_ABILITY_ENABLEDには登録しない: 他の「場に出た時に発動する特性」
            # （いかく等）とは異なり、かわりものはスキルスワップ/さまようたましいで
            # 得た場合や、へんしん/かわりもの自身の変身先の特性としてこの特性を得た
            # 場合には効果が発動しない（.internal/spec/abilities/かわりもの.md）。
            # 特にへんしん/かわりものの変身先がかわりもの持ちだった場合、
            # ON_ABILITY_ENABLEDに登録すると battle.transform() を再帰的に呼び出し
            # 無限再帰を起こすため、クラッシュ防止の意味でも必須。
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.かわりもの_transform_to_opponent,
                subject_spec="source:self",
            ),
        },
    ),
    "かんそうはだ": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.AbilityHandler(
                h.かんそうはだ_absorb_water,
                subject_spec="defender:self",
            ),
            Event.ON_CALC_DAMAGE_MODIFIER: h.AbilityHandler(
                h.かんそうはだ_modify_fire_damage,
                subject_spec="defender:self",
            ),
            Event.ON_TURN_END: h.AbilityHandler(
                h.かんそうはだ_change_hp_by_weather,
                subject_spec="source:self",
                priority=30,
            ),
        },
        lethal_handlers={
            LethalEvent.ON_TURN_END: LethalHandler(l.かんそうはだ_weather_hp, subject="defender")
        }
    ),
    "かんつうドリル": AbilityData(
        handlers={
            Event.ON_CHECK_PROTECT: h.AbilityHandler(
                h.ふかしのこぶし_bypass_protect,
                subject_spec="attacker:self",
            ),
            Event.ON_CALC_PROTECT_MODIFIER: h.AbilityHandler(
                h.ふかしのこぶし_reduce_damage,
                subject_spec="attacker:self",
            ),
        }
    ),
    "かんろなミツ": AbilityData(
        flags={
            "per_battle_once"
        },
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.かんろなミツ_lower_foe_evasion,
                subject_spec="source:self",
            )
        }
    ),
    "カーリーヘアー": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.カーリーヘアー_lower_spd_on_contact,
                subject_spec="defender:self",
                # ぬめぬめと同じ効果（.internal/spec/abilities/カーリーヘアー.md）のため、
                # ぬめぬめと同様に瀕死主体でも発動を許可する。
                allow_fainted_subject=True,
            )
        }
    ),
    "がんじょう": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_MODIFY_MOVE_DAMAGE: h.AbilityHandler(
                h.がんじょう_survive_lethal,
                subject_spec="defender:self",
            ),
            # こんらんの自傷ダメージは技扱いではないため ON_MODIFY_NON_MOVE_DAMAGE で別途判定する
            Event.ON_MODIFY_NON_MOVE_DAMAGE: h.AbilityHandler(
                h.がんじょう_survive_confusion_damage,
                subject_spec="target:self",
            ),
            # 命中判定(Interrupt)より前に無効化するため ON_TRY_MOVE_2 で判定する
            # (.internal/spec/turn.md の ON_TRY_MOVE_2 priority=140 を参照)
            Event.ON_TRY_MOVE_2: h.AbilityHandler(
                h.がんじょう_block_ohko,
                subject_spec="defender:self",
                priority=140,
            ),
        },
        lethal_handlers={
            LethalEvent.ON_APPLY_DAMAGE: LethalHandler(
                l.がんじょう_survive_lethal,
                subject="defender",
            )
        }
    ),
    "がんじょうあご": AbilityData(
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.AbilityHandler(
                h.がんじょうあご_modify_power,
                subject_spec="attacker:self",
            )
        }
    ),
    "ききかいひ": AbilityData(
        flags=set(),
        handlers={
            Event.ON_HP_CHANGED: h.AbilityHandler(
                h.ききかいひ_switch_on_half_hp,
                subject_spec="target:self",
            )
        }
    ),
    "きけんよち": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.きけんよち_warn_threat,
                subject_spec="source:self",
            ),
        }
    ),
    "きみょうなくすり": AbilityData(),
    "きもったま": AbilityData(
        handlers={
            Event.ON_CALC_DEF_TYPE_MODIFIER: h.AbilityHandler(
                h.きもったま_ghost_immune_bypass,
                subject_spec="attacker:self",
            ),
            Event.ON_BEFORE_MODIFY_STAT: h.AbilityHandler(
                h.きもったま_block_intimidate,
                subject_spec="target:self",
            ),
        }
    ),
    "きゅうばん": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_TRY_BLOW: h.AbilityHandler(
                h.きゅうばん_block_blow,
                subject_spec="defender:self",
            ),
        },
    ),
    "きょううん": AbilityData(
        handlers={
            Event.ON_CALC_CRITICAL_RANK: h.AbilityHandler(
                h.きょううん_modify_critical_rank,
                subject_spec="attacker:self",
            ),
        }
    ),
    "きょうえん": AbilityData(),
    "きょうせい": AbilityData(),
    "きよめのしお": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.きよめのしお_prevent_ailment,
                subject_spec="target:self",
            ),
            Event.ON_BEFORE_APPLY_VOLATILE: h.AbilityHandler(
                h.きよめのしお_prevent_volatile,
                subject_spec="target:self",
            ),
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.きよめのしお_reduce_ghost,
                subject_spec="defender:self",
            )
        }
    ),
    "きれあじ": AbilityData(
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.AbilityHandler(
                h.きれあじ_modify_power,
                subject_spec="attacker:self",
            ),
        }
    ),
    "きんしのちから": AbilityData(
        handlers={
            DomainEvent.ON_CALC_BACK_TIER: h.AbilityHandler(
                h.きんしのちから_delay_status_move,
                subject_spec="attacker:self",
            ),
            Event.ON_BEGIN_MOVE: h.AbilityHandler(
                h.きんしのちから_disable_foe_ability,
                subject_spec="attacker:self",
            ),
            Event.ON_END_MOVE: h.AbilityHandler(
                h.きんしのちから_restore_foe_ability,
                subject_spec="attacker:self",
            ),
        }
    ),
    "きんちょうかん": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.announce_ability_triggered,
                subject_spec="source:self",
                priority=30,
            ),
            Event.ON_CHECK_NERVOUS: h.AbilityHandler(
                h.きんちょうかん_check_nervous,
                subject_spec="source:foe",
            ),
        }
    ),
    "ぎたい": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.ぎたい_change_type,
                subject_spec="source:self",
                priority=120,
            ),
            Event.ON_FIELD_CHANGE: h.AbilityHandler(
                h.ぎたい_change_type,
                subject_spec="source:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.ぎたい_change_type,
                subject_spec="source:self",
            ),
        }
    ),
    "ぎゃくじょう": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.ぎゃくじょう_boost_spa_on_half_hp,
                subject_spec="defender:self",
            )
        }
    ),
    "ぎょぐん": AbilityData(
        flags={
            "uncopyable",
            "protected",
            "gas_proof",
        },
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.ぎょぐん_enter_school_form,
                subject_spec="source:self",
                priority=120,
            ),
            Event.ON_TURN_END: h.AbilityHandler(
                h.ぎょぐん_update_form,
                subject_spec="source:self",
                priority=160,
            ),
        }
    ),
    "くいしんぼう": AbilityData(),
    "クイックドロウ": AbilityData(
        handlers={
            DomainEvent.ON_CALC_BACK_TIER: h.AbilityHandler(
                h.クイックドロウ_maybe_fast_attack,
                subject_spec="attacker:self",
            ),
        }
    ),
    "クォークチャージ": AbilityData(
        flags={
            "uncopyable",
        },
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                paradox.refresh_paradox_charge_state,
                subject_spec="source:self",
                priority=140,  # .internal/spec/turn.md ON_SWITCH_IN: 「140 クォークチャージ（特性）」
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                paradox.refresh_paradox_charge_state,
                subject_spec="source:self",
                priority=200,
            ),
            Event.ON_FIELD_CHANGE: h.AbilityHandler(
                paradox.refresh_paradox_charge_state,
                subject_spec="source:self",
                priority=200,
            ),
            DomainEvent.ON_CALC_SPEED: h.AbilityHandler(
                paradox.modify_speed,
                subject_spec="source:self",
            ),
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                paradox.apply_atk_modifier,
                subject_spec="attacker:self",
            ),
            Event.ON_CALC_DEF_MODIFIER: h.AbilityHandler(
                paradox.apply_def_modifier,
                subject_spec="defender:self",
            ),
        }
    ),
    "くさのけがわ": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_CALC_DEF_MODIFIER: h.AbilityHandler(
                h.くさのけがわ_boost_B,
                subject_spec="defender:self",
            )
        }
    ),
    "くだけるよろい": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.くだけるよろい_drop_B_boost_S,
                subject_spec="defender:self",
                priority=20,
            )
        }
    ),
    "クリアボディ": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_BEFORE_MODIFY_STAT: h.AbilityHandler(
                h.クリアボディ_block_stat_drop,
                subject_spec="target:self",
            )
        }
    ),
    "くろのいななき": AbilityData(
        handlers={
            Event.ON_MOVE_KO: h.AbilityHandler(
                h.くろのいななき_boost,
                subject_spec="attacker:self",
                allow_fainted_subject=True,  # HPコスト技等で自身が瀕死になっても、撃破時(ON_MOVE_KO)の効果は発動する
            )
        }
    ),
    "グラスメイカー": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.グラスメイカー_activate_terrain,
                "source:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.グラスメイカー_activate_terrain,
                "source:self",
            ),
        }
    ),
    "げきりゅう": AbilityData(
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.しんりょくもうかげきりゅうむしのしらせ_modify_atk,
                subject_spec="attacker:self",
            )
        }
    ),
    "こおりのりんぷん": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.AbilityHandler(
                h.こおりのりんぷん_reduce_special_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "こだいかっせい": AbilityData(
        flags={
            "uncopyable",
        },
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                paradox.refresh_paradox_charge_state,
                subject_spec="source:self",
                priority=140,  # .internal/spec/turn.md ON_SWITCH_IN: 「140 こだいかっせい（特性）」
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                paradox.refresh_paradox_charge_state,
                subject_spec="source:self",
                priority=200,
            ),
            Event.ON_FIELD_CHANGE: h.AbilityHandler(
                paradox.refresh_paradox_charge_state,
                subject_spec="source:self",
                priority=200,
            ),
            DomainEvent.ON_CALC_SPEED: h.AbilityHandler(
                paradox.modify_speed,
                subject_spec="source:self",
            ),
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                paradox.apply_atk_modifier,
                subject_spec="attacker:self",
            ),
            Event.ON_CALC_DEF_MODIFIER: h.AbilityHandler(
                paradox.apply_def_modifier,
                subject_spec="defender:self",
            ),
        }
    ),
    "こぼれダネ": AbilityData(
        handlers={
            # ON_DAMAGE_HIT は actual_damage<=0 のとき発火しないため採用しない。こらえるで
            # HP1のまま耐えたときやみねうちを受けたとき（実HPダメージ0）も発動する仕様
            # （.internal/spec/abilities/こぼれダネ.md）を満たすため、常に発火する Event.ON_HIT
            # を使用する（みがわりに阻まれた場合はハンドラ内で ctx.substitute_damage を見て除外する）。
            Event.ON_HIT: h.AbilityHandler(
                h.こぼれダネ_set_grassy_terrain,
                subject_spec="defender:self",
                # 攻撃技でHPが0になったときも特性を発動させてからひんしになる仕様
                # （.internal/spec/abilities/こぼれダネ.md）のため、瀕死主体でも発動を許可する。
                allow_fainted_subject=True,
            )
        }
    ),
    "こんがりボディ": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.AbilityHandler(
                h.こんがりボディ_absorb_fire,
                subject_spec="defender:self",
            )
        }
    ),
    "こんじょう": AbilityData(
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.こんじょう_modify_atk,
                subject_spec="attacker:self",
            ),
            Event.ON_CALC_BURN_MODIFIER: h.AbilityHandler(
                h.こんじょう_ignore_burn_penalty,
                subject_spec="attacker:self",
                priority=200,
            ),
        }
    ),
    "ごりむちゅう": AbilityData(
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.ごりむちゅう_modify_atk,
                subject_spec="attacker:self",
            ),
            Event.ON_PP_CONSUMED: h.AbilityHandler(
                h.ごりむちゅう_lock_move,
                subject_spec="attacker:self",
            ),
            Event.ON_MOVE_END: h.AbilityHandler(
                h.ごりむちゅう_lock_move,
                subject_spec="attacker:self",
            ),
            Event.ON_MODIFY_COMMAND_OPTIONS: h.AbilityHandler(
                h.ごりむちゅう_restrict_commands,
                subject_spec="source:self",
            ),
        }
    ),
    "サイコメイカー": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.サイコメイカー_activate_terrain,
                "source:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.サイコメイカー_activate_terrain,
                "source:self",
            ),
        }
    ),
    "さいせいりょく": AbilityData(
        handlers={
            Event.ON_SWITCH_OUT: h.AbilityHandler(
                h.さいせいりょく_heal_on_withdraw,
                subject_spec="source:self",
            ),
        }
    ),
    "さまようたましい": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.さまようたましい_swap_ability_on_contact,
                subject_spec="defender:self",
                priority=20,
                allow_fainted_subject=True,  # 自身が直接攻撃でひんしになった場合でも発動する
            ),
        }
    ),
    "さめはだ": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.さめはだ_chip_contact_attacker,
                subject_spec="defender:self",
                allow_fainted_subject=True,  # 自身が直接攻撃でひんしになった場合でも発動する
            )
        }
    ),
    "サンパワー": AbilityData(
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.サンパワー_modify_atk,
                subject_spec="attacker:self",
            ),
            Event.ON_TURN_END: h.AbilityHandler(
                h.サンパワー_take_sun_damage,
                subject_spec="source:self",
                priority=30,
            ),
        },
        lethal_handlers={
            LethalEvent.ON_TURN_END: LethalHandler(
                func=l.サンパワー_take_sun_damage,
                subject="defender",
            )
        }
    ),
    "サーフテール": AbilityData(
        handlers={
            DomainEvent.ON_CALC_SPEED: h.AbilityHandler(
                h.サーフテール_modify_speed,
                subject_spec="source:self",
            )
        }
    ),
    "シェルアーマー": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_MODIFY_CRITICAL_RATE: h.AbilityHandler(
                h.カブトアーマー_block_crit,
                subject_spec="defender:self",
            )
        }
    ),
    "しぜんかいふく": AbilityData(
        handlers={
            Event.ON_SWITCH_OUT: h.AbilityHandler(
                h.しぜんかいふく_cure_ailment,
                subject_spec="source:self",
            ),
        }
    ),
    "しめりけ": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_TRY_MOVE_1: [
                h.AbilityHandler(
                    h.しめりけ_block_explosion_self,
                    subject_spec="attacker:self",
                ),
                h.AbilityHandler(
                    h.しめりけ_block_explosion_foe,
                    subject_spec="defender:self",
                ),
            ]
        }
    ),
    "しゅうかく": AbilityData(
        handlers={
            Event.ON_TURN_END: h.AbilityHandler(
                h.しゅうかく_restore_berry,
                subject_spec="source:self",
                priority=150,  # .internal/spec/turn.md ON_TURN_END: 「150 しゅうかく」
            ),
        }
    ),
    "しょうりのほし": AbilityData(
        handlers={
            Event.ON_MODIFY_ACCURACY: h.AbilityHandler(
                h.しょうりのほし_modify_accuracy,
                subject_spec="attacker:self",
            )
        }
    ),
    "しれいとう": AbilityData(
        flags={
            "uncopyable"
        }
    ),
    "しろいけむり": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_BEFORE_MODIFY_STAT: h.AbilityHandler(
                h.クリアボディ_block_stat_drop,
                subject_spec="target:self",
            )
        }
    ),
    "しろのいななき": AbilityData(
        handlers={
            Event.ON_MOVE_KO: h.AbilityHandler(
                h.しろのいななき_boost,
                subject_spec="attacker:self",
                allow_fainted_subject=True,  # HPコスト技等で自身が瀕死になっても、撃破時(ON_MOVE_KO)の効果は発動する
            )
        }
    ),
    "しんがん": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_CALC_DEF_TYPE_MODIFIER: h.AbilityHandler(
                h.しんがん_ghost_immune_bypass,
                subject_spec="attacker:self",
            ),
            Event.ON_BEFORE_MODIFY_STAT: h.AbilityHandler(
                h.するどいめ_block_ACC_drop,
                subject_spec="target:self",
            ),
            Event.ON_GET_STAT_RANK: h.AbilityHandler(
                h.するどいめ_ignore_evasion,
                subject_spec="attacker:self",
            ),
        }
    ),
    "シンクロ": AbilityData(
        handlers={
            Event.ON_APPLY_AILMENT: h.AbilityHandler(
                h.シンクロ_return_ailment,
                subject_spec="target:self",
            ),
        }
    ),
    "シンプル": AbilityData(
        handlers={
            Event.ON_BEFORE_MODIFY_STAT: h.AbilityHandler(
                h.シンプル_modify_stat_delta,
                subject_spec="target:self",
            ),
        }
    ),
    "しんりょく": AbilityData(
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.しんりょくもうかげきりゅうむしのしらせ_modify_atk,
                subject_spec="attacker:self",
            )
        }
    ),
    "じきゅうりょく": AbilityData(
        handlers={
            # 通常のダメージ（実HPダメージ>0）はEvent.ON_DAMAGE_HITで処理する。
            # クリアスモッグのランクリセット（priority=10）より後に発火させることで、
            # 「クリアスモッグを受けた場合、ランクがリセットされた後にじきゅうりょくが発動する」
            # （.internal/spec/abilities/じきゅうりょく.md）という仕様どおりの順序にする。
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.じきゅうりょく_boost_B_on_damage_hit,
                subject_spec="defender:self",
            ),
            # ON_DAMAGE_HIT は actual_damage<=0 のとき発火しないため、こらえるでHP1のまま
            # 耐えたときなど（実HPダメージ0）も発動する仕様（.internal/spec/abilities/
            # じきゅうりょく.md）を満たすため、常に発火する Event.ON_HIT も併用する
            # （実HPダメージ>0の通常ケースはON_DAMAGE_HIT側で処理済みのためハンドラ内で除外し、
            # みがわりに阻まれた場合はctx.substitute_damageを見て除外する）。
            Event.ON_HIT: h.AbilityHandler(
                h.じきゅうりょく_boost_B_on_hit,
                subject_spec="defender:self",
            ),
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(
                func=l.じきゅうりょく_boost_def,
                subject="defender",
            )
        }
    ),
    "じしんかじょう": AbilityData(
        handlers={
            Event.ON_MOVE_KO: h.AbilityHandler(
                h.しろのいななき_boost,
                subject_spec="attacker:self",
                allow_fainted_subject=True,  # HPコスト技等で自身が瀕死になっても、撃破時(ON_MOVE_KO)の効果は発動する
            )
        }
    ),
    "じゅうなん": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.prevent_paralysis_ailment,
                "target:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.じゅうなん_cure_paralysis_on_enable,
                subject_spec="source:self",
            ),
        }
    ),
    "じゅくせい": AbilityData(),
    "じょうききかん": AbilityData(
        handlers={
            # 技側の ON_DAMAGE_HIT ハンドラ（h.MoveHandler、デフォルト priority=100）より
            # 大きい値を指定し、バブルこうせん等の追加効果（S-1）の後にじょうききかん
            # （S+6）が発動する仕様（.internal/spec/abilities/じょうききかん.md）を満たす。
            # priority を指定しない場合、(priority, -speed) のタイブレークで攻撃側・
            # 防御側どちらが速いかによって発動順が変わってしまうため明示する。
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.じょうききかん_max_boost_speed,
                subject_spec="defender:self",
                priority=110,
            )
        }
    ),
    "じょおうのいげん": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_TRY_MOVE_1: h.AbilityHandler(
                h.じょおうのいげん_block_priority,
                subject_spec="defender:self",
                priority=40,
            ),
        }
    ),
    "じりょく": AbilityData(
        handlers={
            Event.ON_CHECK_TRAPPED: h.AbilityHandler(
                h.じりょく_check_trapped,
                subject_spec="source:foe",
            )
        }
    ),
    "じんばいったい": AbilityData(
        flags={
            "uncopyable",
            "protected",
            "gas_proof",
        },
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.announce_ability_triggered,
                subject_spec="source:self",
                priority=30,
            ),
            Event.ON_CHECK_NERVOUS: h.AbilityHandler(
                h.きんちょうかん_check_nervous,
                subject_spec="source:foe",
            ),
            Event.ON_MOVE_KO: h.AbilityHandler(
                h.じんばいったい_boost,
                subject_spec="attacker:self",
                allow_fainted_subject=True,  # HPコスト技等で自身が瀕死になっても、撃破時(ON_MOVE_KO)の効果は発動する
            ),
        }
    ),
    "すいすい": AbilityData(
        handlers={
            DomainEvent.ON_CALC_SPEED: h.AbilityHandler(
                h.すいすい_modify_speed,
                subject_spec="source:self",
            )
        }
    ),
    "すいほう": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_CALC_ATK_MODIFIER: [
                h.AbilityHandler(
                    h.すいほう_boost_water,
                    subject_spec="attacker:self",
                ),
                h.AbilityHandler(
                    h.すいほう_reduce_fire,
                    subject_spec="defender:self",
                ),
            ],
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.prevent_burn_ailment,
                "target:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.すいほう_cure_burn_on_enable,
                subject_spec="source:self",
            ),
        }
    ),
    "スイートベール": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.prevent_sleep_ailment,
                "target:self",
            ),
            Event.ON_BEFORE_APPLY_VOLATILE: h.AbilityHandler(
                h.スイートベール_prevent_volatile,
                "target:self",
            )
        }
    ),
    "スカイスキン": AbilityData(
        handlers={
            Event.ON_MODIFY_MOVE_TYPE: h.AbilityHandler(
                h.スカイスキン_modify_move_type,
                subject_spec="attacker:self",
            ),
            Event.ON_CALC_POWER_MODIFIER: h.AbilityHandler(
                h.スカイスキン_modify_power,
                subject_spec="attacker:self",
            ),
        }
    ),
    "スキルリンク": AbilityData(
        handlers={
            Event.ON_MODIFY_HIT_COUNT: h.AbilityHandler(
                h.スキルリンク_modify_hit_count,
                subject_spec="attacker:self",
            ),
            Event.ON_MODIFY_HIT_CHECK_EACH_TIME: h.AbilityHandler(
                h.スキルリンク_modify_hit_check_each_time,
                subject_spec="attacker:self",
            ),
        }
    ),
    "スクリューおびれ": AbilityData(),
    "すじがねいり": AbilityData(),
    "すてみ": AbilityData(
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.AbilityHandler(
                h.すてみ_boost_power,
                subject_spec="attacker:self",
            )
        }
    ),
    "スナイパー": AbilityData(
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.AbilityHandler(
                h.スナイパー_boost_critical,
                subject_spec="attacker:self",
            )
        }
    ),
    "すなおこし": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.すなおこし_activate_weather,
                "source:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.すなおこし_activate_weather,
                "source:self",
            ),
        }
    ),
    "すなかき": AbilityData(
        handlers={
            DomainEvent.ON_CALC_SPEED: h.AbilityHandler(
                h.すなかき_modify_speed,
                subject_spec="source:self",
            ),
            Event.ON_MODIFY_NON_MOVE_DAMAGE: h.AbilityHandler(
                h.すなかき_ignore_sandstorm_damage,
                subject_spec="target:self",
            ),
        }
    ),
    "すながくれ": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_MODIFY_ACCURACY: h.AbilityHandler(
                h.すながくれ_reduce_accuracy,
                subject_spec="defender:self",
            ),
            Event.ON_MODIFY_NON_MOVE_DAMAGE: h.AbilityHandler(
                h.すながくれ_ignore_sandstorm_damage,
                subject_spec="target:self",
            ),
        }
    ),
    "すなのちから": AbilityData(
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.AbilityHandler(
                h.すなのちから_modify_power,
                subject_spec="attacker:self",
            ),
            Event.ON_MODIFY_NON_MOVE_DAMAGE: h.AbilityHandler(
                h.すなのちから_ignore_sandstorm_damage,
                subject_spec="target:self",
            ),
        }
    ),
    "すなはき": AbilityData(
        handlers={
            # ON_DAMAGE_HIT は actual_damage<=0 のとき発火しないため採用しない。こらえるで
            # HP1のまま耐えたときやみねうちを受けたとき（実HPダメージ0）も発動する仕様
            # （.internal/spec/abilities/すなはき.md）を満たすため、常に発火する Event.ON_HIT
            # を使用する（みがわりに阻まれた場合はハンドラ内で ctx.substitute_damage を見て除外する）。
            Event.ON_HIT: h.AbilityHandler(
                h.すなはき_set_sandstorm,
                subject_spec="defender:self",
                # 攻撃技でHPが0になったときも特性を発動させてからひんしになる仕様
                # （.internal/spec/abilities/すなはき.md）のため、瀕死主体でも発動を許可する。
                allow_fainted_subject=True,
            )
        }
    ),
    "すりぬけ": AbilityData(
        handlers={
            Event.ON_CHECK_HIT_SUBSTITUTE: h.AbilityHandler(
                h.すりぬけ_bypass_substitute,
                subject_spec="attacker:self",
            ),
            Event.ON_CHECK_BYPASS_SCREEN: h.AbilityHandler(
                h.すりぬけ_bypass_screen,
                subject_spec="attacker:self",
            ),
            Event.ON_CHECK_BYPASS_STATUS_GUARD: h.AbilityHandler(
                h.すりぬけ_bypass_status_guard,
                subject_spec="source:self",
            )
        }
    ),
    "するどいめ": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_BEFORE_MODIFY_STAT: h.AbilityHandler(
                h.するどいめ_block_ACC_drop,
                subject_spec="target:self",
            ),
            Event.ON_GET_STAT_RANK: h.AbilityHandler(
                h.するどいめ_ignore_evasion,
                subject_spec="attacker:self",
            )
        }
    ),
    "スロースタート": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.スロースタート_start,
                subject_spec="source:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.スロースタート_start,
                subject_spec="source:self",
            ),
            DomainEvent.ON_CALC_SPEED: h.AbilityHandler(
                h.スロースタート_modify_speed,
                subject_spec="source:self",
            ),
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.スロースタート_modify_atk,
                subject_spec="attacker:self",
            ),
            Event.ON_TURN_END: h.AbilityHandler(
                h.スロースタート_tick,
                subject_spec="source:self",
                priority=150,
            ),
        }
    ),
    "スワームチェンジ": AbilityData(
        flags={
            "uncopyable",
            "protected",
            "gas_proof",
        },
        handlers={
            Event.ON_TURN_END: h.AbilityHandler(
                h.スワームチェンジ_form_change_on_low_hp,
                subject_spec="source:self",
                priority=160,
            ),
            Event.ON_HP_CHANGED: h.AbilityHandler(
                h.スワームチェンジ_revert_form_on_faint,
                subject_spec="target:self",
                allow_fainted_subject=True,  # 瀕死になったこと自体がパーフェクトフォルム解除の発動条件
            ),
        }
    ),
    "せいぎのこころ": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.せいぎのこころ_boost_atk_on_dark,
                subject_spec="defender:self",
            )
        }
    ),
    "せいしんりょく": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_BEFORE_APPLY_VOLATILE: h.AbilityHandler(
                h.せいしんりょく_prevent_volatile,
                "target:self",
            ),
            Event.ON_BEFORE_MODIFY_STAT: h.AbilityHandler(
                h.せいしんりょく_block_intimidate,
                subject_spec="target:self",
            ),
        }
    ),
    "せいでんき": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.せいでんき_maybe_paralyze_attacker,
                subject_spec="defender:self",
                # 攻撃技でひんしになったときも発動する仕様
                # （.internal/spec/abilities/せいでんき.md）のため、瀕死主体でも発動を許可する。
                allow_fainted_subject=True,
            )
        }
    ),
    "ぜったいねむり": AbilityData(
        flags={
            "uncopyable",
            "protected",
            "gas_proof",
        },
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.ぜったいねむり_switch_in,
                subject_spec="source:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.ぜったいねむり_switch_in,
                subject_spec="source:self",
            ),
        },
    ),
    "ゼロフォーミング": AbilityData(
        flags={
            "uncopyable"
        },
        handlers={
            Event.ON_TERASTALLIZE: h.AbilityHandler(
                h.ゼロフォーミング_clear_field,
                subject_spec="source:self",
            ),
        }
    ),
    "そうしょく": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.AbilityHandler(
                h.そうしょく_absorb_grass,
                subject_spec="defender:self",
            )
        }
    ),
    "そうだいしょう": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.そうだいしょう_announce_on_entry,
                subject_spec="source:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.そうだいしょう_announce_on_entry,
                subject_spec="source:self",
            ),
            Event.ON_CALC_POWER_MODIFIER: h.AbilityHandler(
                h.そうだいしょう_modify_power,
                subject_spec="attacker:self",
            ),
        }
    ),
    "ソウルハート": AbilityData(
        handlers={
            Event.ON_MOVE_KO: h.AbilityHandler(
                h.ソウルハート_boost_spa_on_ko,
                subject_spec="attacker:self",
                allow_fainted_subject=True,  # HPコスト技等で自身が瀕死になっても、撃破時(ON_MOVE_KO)の効果は発動する
            ),
            Event.ON_HP_CHANGED: h.AbilityHandler(
                h.ソウルハート_boost_spa_on_faint,
                subject_spec="target:foe",
            ),
        }
    ),
    "たいねつ": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.たいねつ_reduce_fire,
                subject_spec="defender:self",
            ),
            Event.ON_MODIFY_NON_MOVE_DAMAGE: h.AbilityHandler(
                h.たいねつ_reduce_burn_damage,
                subject_spec="target:self",
            ),
        }
    ),
    "たまひろい": AbilityData(),
    "たんじゅん": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_BEFORE_MODIFY_STAT: h.AbilityHandler(
                h.たんじゅん_double_stat,
                subject_spec="target:self",
            )
        }
    ),
    "ターボブレイズ": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.announce_ability_triggered,
                subject_spec="source:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.announce_ability_triggered,
                subject_spec="source:self",
            ),
            Event.ON_BEGIN_MOVE: h.AbilityHandler(
                h.かたやぶり_disable_foe_ability,
                subject_spec="attacker:self",
            ),
            Event.ON_END_MOVE: h.AbilityHandler(
                h.かたやぶり_restore_foe_ability,
                subject_spec="attacker:self",
            ),
        }
    ),
    "ダウンロード": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.ダウンロード_raise_stat,
                subject_spec="source:self",
            ),
        }
    ),
    "だっぴ": AbilityData(
        handlers={
            Event.ON_TURN_END: h.AbilityHandler(
                h.だっぴ_cure_ailment,
                subject_spec="source:self",
                priority=60,
            ),
        }
    ),
    "ダルマモード": AbilityData(
        flags={
            "uncopyable",
            "protected",
            "gas_proof",
        },
        handlers={
            Event.ON_TURN_END: h.AbilityHandler(
                h.ダルマモード_update_form,
                subject_spec="source:self",
                priority=160,
            ),
            Event.ON_SWITCH_OUT: h.AbilityHandler(
                h.ダルマモード_revert_form,
                subject_spec="source:self",
                allow_fainted_subject=True,  # 瀕死交代(ON_SWITCH_OUT)でも発動する
            ),
        }
    ),
    "ダークオーラ": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.announce_ability_triggered,
                subject_spec="source:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.announce_ability_triggered,
                subject_spec="source:self",
            ),
            Event.ON_CALC_POWER_MODIFIER: [
                h.AbilityHandler(
                    h.ダークオーラ_boost_power,
                    subject_spec="attacker:self",
                ),
                h.AbilityHandler(
                    h.ダークオーラ_boost_power,
                    subject_spec="defender:self",
                ),
            ],
        }
    ),
    "ちからずく": AbilityData(
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.AbilityHandler(
                h.ちからずく_boost,
                subject_spec="attacker:self",
            ),
            Event.ON_MODIFY_SECONDARY_CHANCE: h.AbilityHandler(
                h.ちからずく_disable_secondary_effect,
                subject_spec="attacker:self",
            ),
        }
    ),
    "ちからもち": AbilityData(
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.ちからもち_boost_physical,
                subject_spec="attacker:self",
            )
        }
    ),
    "ちくでん": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.AbilityHandler(
                h.ちくでん_absorb_electric,
                subject_spec="defender:self",
            )
        }
    ),
    "ちどりあし": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_MODIFY_ACCURACY: h.AbilityHandler(
                h.ちどりあし_reduce_accuracy,
                subject_spec="defender:self",
            )
        }
    ),
    "ちょすい": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.AbilityHandler(
                h.ちょすい_absorb_water,
                subject_spec="defender:self",
            )
        },
    ),
    "テイルアーマー": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_TRY_MOVE_1: h.AbilityHandler(
                h.じょおうのいげん_block_priority,
                subject_spec="defender:self",
                priority=40,
            ),
        }
    ),
    "てきおうりょく": AbilityData(
        handlers={
            Event.ON_CALC_ATK_TYPE_MODIFIER: h.AbilityHandler(
                h.てきおうりょく_modify_stab,
                subject_spec="attacker:self",
            )
        }
    ),
    "テクニシャン": AbilityData(
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.AbilityHandler(
                h.テクニシャン_boost_power,
                subject_spec="attacker:self",
            )
        }
    ),
    "てつのこぶし": AbilityData(
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.AbilityHandler(
                h.てつのこぶし_modify_power,
                subject_spec="attacker:self",
            )
        }
    ),
    "てつのトゲ": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.さめはだ_chip_contact_attacker,
                subject_spec="defender:self",
                # さめはだと同じ効果（.internal/spec/abilities/てつのトゲ.md「さめはだ#特性の
                # 仕様を参照」）のため、さめはだと同様に瀕死主体でも発動を許可する。
                allow_fainted_subject=True,
            )
        }
    ),
    "テラスシェル": AbilityData(
        flags={
            "uncopyable",
            "mold_breaker_ignorable",
            "full_hp_damage_modifier",
        },
        handlers={
            Event.ON_CALC_DEF_TYPE_MODIFIER: h.AbilityHandler(
                h.テラスシェル_overwrite_type_modifier,
                subject_spec="defender:self",
            )
        }
    ),
    "テラスチェンジ": AbilityData(
        flags={
            "uncopyable",
            "protected",
            "gas_proof",
        },
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.テラスチェンジ_form_change_on_entry,
                subject_spec="source:self",
                priority=10,
            ),
        }
    ),
    "テラボルテージ": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.announce_ability_triggered,
                subject_spec="source:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.announce_ability_triggered,
                subject_spec="source:self",
            ),
            Event.ON_BEGIN_MOVE: h.AbilityHandler(
                h.かたやぶり_disable_foe_ability,
                subject_spec="attacker:self",
            ),
            Event.ON_END_MOVE: h.AbilityHandler(
                h.かたやぶり_restore_foe_ability,
                subject_spec="attacker:self",
            ),
        }
    ),
    "テレパシー": AbilityData(
        flags={
            "mold_breaker_ignorable"
        }
    ),
    "てんきや": AbilityData(
        flags={
            "uncopyable"
        },
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.てんきや_sync_form,
                subject_spec="source:self",
                priority=140,
            ),
            Event.ON_FIELD_CHANGE: h.AbilityHandler(
                h.てんきや_sync_form,
                subject_spec="source:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.てんきや_sync_form,
                subject_spec="source:self",
            ),
        }
    ),
    "てんねん": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_CALC_ATK_RANK_MODIFIER: h.AbilityHandler(
                h.てんねん_ignore_rank,
                subject_spec="defender:self",
            ),
            Event.ON_CALC_DEF_RANK_MODIFIER: h.AbilityHandler(
                h.てんねん_ignore_rank,
                subject_spec="attacker:self",
            ),
            Event.ON_GET_STAT_RANK: [
                h.AbilityHandler(
                    h.てんねん_ignore_accuracy,
                    subject_spec="defender:self",
                ),
                h.AbilityHandler(
                    h.てんねん_ignore_evasion,
                    subject_spec="attacker:self",
                ),
            ],
        }
    ),
    "てんのめぐみ": AbilityData(
        handlers={
            Event.ON_MODIFY_SECONDARY_CHANCE: h.AbilityHandler(
                h.てんのめぐみ_boost_secondary_chance,
                subject_spec="attacker:self",
            ),
        }
    ),
    "デルタストリーム": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.デルタストリーム_activate_weather,
                "source:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.デルタストリーム_activate_weather,
                "source:self",
            ),
            Event.ON_SWITCH_OUT: h.AbilityHandler(
                h.デルタストリーム_deactivate_strong_weather,
                "source:self",
                allow_fainted_subject=True,  # 瀕死交代(ON_SWITCH_OUT)でも強制天候を解除する
            ),
            Event.ON_ABILITY_DISABLED: h.AbilityHandler(
                h.デルタストリーム_deactivate_strong_weather,
                "source:self",
                allow_fainted_subject=True,  # 瀕死交代(ON_SWITCH_OUT)でも強制天候を解除する
                ignored_disable_reasons=frozenset({"とくせいなし"}),  # 自身がとくせいなしで無効化された結果として発火するため、その理由は無視する
            ),
        },
    ),
    "でんきエンジン": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.AbilityHandler(
                h.でんきエンジン_absorb_electric,
                subject_spec="defender:self",
            )
        }
    ),
    "でんきにかえる": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.でんきにかえる_charge_on_hit,
                subject_spec="defender:self",
            ),
            Event.ON_HIT: h.AbilityHandler(
                h.でんきにかえる_charge_on_zero_damage,
                subject_spec="defender:self",
            ),
        }
    ),
    "とうそうしん": AbilityData(
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.AbilityHandler(
                h.とうそうしん_modify_power,
                subject_spec="attacker:self",
            )
        }
    ),
    "とびだすなかみ": AbilityData(
        handlers={
            Event.ON_BEGIN_MOVE: h.AbilityHandler(
                h.とびだすなかみ_save_hp,
                subject_spec="defender:self",
            ),
            Event.ON_MOVE_KO: h.AbilityHandler(
                h.とびだすなかみ_retaliate_on_ko,
                subject_spec="defender:self",
                allow_fainted_subject=True,  # 自身が瀕死になった(ON_MOVE_KO)ことがこの効果の発動条件
            ),
        }
    ),
    "とびだすハバネロ": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.とびだすハバネロ_burn_attacker,
                subject_spec="defender:self",
                # 攻撃技でひんしになったときも発動する仕様
                # （.internal/spec/abilities/とびだすハバネロ.md）のため、瀕死主体でも発動を許可する。
                allow_fainted_subject=True,
            ),
        }
    ),
    "トランジスタ": AbilityData(
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.トランジスタ_modify_atk,
                subject_spec="attacker:self",
            )
        }
    ),
    "とれないにおい": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.とれないにおい_overwrite_attacker_ability,
                subject_spec="defender:self",
                priority=20,
                allow_fainted_subject=True,  # 自身が直接攻撃でひんしになった場合でも発動する（ミイラ等と同種の効果）
            ),
        }
    ),
    "トレース": AbilityData(
        flags={
            "uncopyable"
        },
        handlers={
            Event.ON_SWITCH_IN: [
                h.AbilityHandler(
                    h.トレース_copy_ability,
                    subject_spec="source:self",
                ),
                h.AbilityHandler(
                    h.トレース_copy_ability_on_foe_change,
                    subject_spec="source:foe",
                ),
            ],
            Event.ON_ABILITY_ENABLED: [
                h.AbilityHandler(
                    h.トレース_copy_ability,
                    subject_spec="source:self",
                ),
                h.AbilityHandler(
                    h.トレース_copy_ability_on_foe_change,
                    subject_spec="source:foe",
                ),
            ],
        },
    ),
    "どくくぐつ": AbilityData(
        flags={
            "uncopyable"
        },
        handlers={
            Event.ON_APPLY_AILMENT: h.AbilityHandler(
                h.どくくぐつ_confuse_on_poison,
                subject_spec="source:self",
            ),
        }
    ),
    "どくげしょう": AbilityData(
        handlers={
            # ON_DAMAGE_HIT は actual_damage<=0 のとき発火しないため採用しない。こらえるで
            # HP1のまま耐えたときやみねうちを受けたとき（実HPダメージ0）も発動する仕様
            # （.internal/spec/abilities/どくげしょう.md）を満たすため、常に発火する Event.ON_HIT
            # を使用する（みがわりに阻まれた場合はハンドラ内で ctx.substitute_damage を見て除外する）。
            Event.ON_HIT: h.AbilityHandler(
                h.どくげしょう_set_toxic_spikes,
                subject_spec="defender:self",
                # 物理技でHPが0になったときも特性を発動させてからひんしになる仕様
                # （.internal/spec/abilities/どくげしょう.md）のため、瀕死主体でも発動を許可する。
                allow_fainted_subject=True,
            )
        }
    ),
    "どくしゅ": AbilityData(
        handlers={
            # .internal/spec/turn.md の Event.ON_DAMAGE（実装上の Event.ON_DAMAGE_HIT に相当）に
            # 「10 | 攻撃側のどくしゅによるどく」と明記されているため priority=10 を指定する。
            # ミイラ/さまようたましい/とれないにおい（同イベントpriority=20）や
            # はたきおとす等のアイテム効果（同100）より先に発動する必要がある
            # （.internal/spec/abilities/どくしゅ.md）ため、デフォルト(100)のままでは順序が壊れる。
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.どくしゅ_maybe_poison_on_contact,
                subject_spec="attacker:self",
                priority=10,
            )
        }
    ),
    "どくのくさり": AbilityData(
        handlers={
            # ON_DAMAGE_HIT は actual_damage<=0 のとき発火しないため採用しない。こらえるで
            # HP1のまま耐えたときやみねうちを受けたとき（実HPダメージ0）も発動する仕様
            # （.internal/spec/abilities/どくのくさり.md）を満たすため、常に発火する Event.ON_HIT
            # を使用する（みがわりに阻まれた場合はハンドラ内で ctx.substitute_damage を見て除外する）。
            Event.ON_HIT: h.AbilityHandler(
                h.どくのくさり_maybe_badly_poison,
                subject_spec="attacker:self",
            )
        }
    ),
    "どくのトゲ": AbilityData(
        handlers={
            # ON_DAMAGE_HIT は actual_damage<=0 のとき発火しないため採用しない。こらえるで
            # HP1のまま耐えたときやみねうちを受けたとき（実HPダメージ0）も発動する仕様
            # （どくげしょう・どくのくさり等の同種特性と同じ挙動）を満たすため、常に発火する
            # Event.ON_HIT を使用する（みがわりに阻まれた場合はハンドラ内で
            # ctx.substitute_damage を見て除外する）。
            Event.ON_HIT: h.AbilityHandler(
                h.どくのトゲ_maybe_poison_attacker,
                subject_spec="defender:self",
                # 攻撃技でひんしになったときも発動する仕様
                # （.internal/spec/abilities/どくのトゲ.md）のため、瀕死主体でも発動を許可する。
                allow_fainted_subject=True,
            )
        }
    ),
    "どくぼうそう": AbilityData(
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.AbilityHandler(
                h.どくぼうそう_modify_power,
                subject_spec="attacker:self",
            )
        }
    ),
    "どしょく": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.AbilityHandler(
                h.どしょく_absorb_ground,
                subject_spec="defender:self",
            )
        },
    ),
    "ドラゴンスキン": AbilityData(
        handlers={
            Event.ON_MODIFY_MOVE_TYPE: h.AbilityHandler(
                h.ドラゴンスキン_modify_move_type,
                subject_spec="attacker:self",
            ),
            Event.ON_CALC_POWER_MODIFIER: h.AbilityHandler(
                h.ドラゴンスキン_modify_power,
                subject_spec="attacker:self",
            ),
        }
    ),
    "どんかん": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_BEFORE_APPLY_VOLATILE: h.AbilityHandler(
                h.どんかん_prevent_volatile,
                subject_spec="target:self",
            ),
            Event.ON_BEFORE_MODIFY_STAT: h.AbilityHandler(
                h.どんかん_block_intimidate,
                subject_spec="target:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.どんかん_cure_volatile_on_enable,
                subject_spec="source:self",
            ),
        }
    ),
    "ナイトメア": AbilityData(
        handlers={
            Event.ON_TURN_END: h.AbilityHandler(
                h.ナイトメア_damage_sleeping_foe,
                subject_spec="source:self",
                priority=150,
            )
        }
    ),
    "なまけ": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.なまけ_init,
                subject_spec="source:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.なまけ_init,
                subject_spec="source:self",
            ),
            Event.ON_TRY_ACTION: h.AbilityHandler(
                h.なまけ_try_action,
                subject_spec="attacker:self",
                # 一次情報:「なまけているメッセージが現れるタイミングはねむり/こおり
                # 判定の後」。ねむり_check_action/こおり_action は同じ priority=10 で
                # stop_event するため、tie-break で先に実行されると眠り・氷結で
                # 動けないターンにXが誤って消費されてしまう。ねむり/こおり(10)より
                # 後、PPが残っていない(20)より前になるよう priority=15 とする。
                priority=15,
            ),
        }
    ),
    "にげあし": AbilityData(),
    "にげごし": AbilityData(
        handlers={
            Event.ON_HP_CHANGED: h.AbilityHandler(
                h.ききかいひ_switch_on_half_hp,
                subject_spec="target:self",
            )
        }
    ),
    "ぬめぬめ": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.ぬめぬめ_lower_spd_on_contact,
                subject_spec="defender:self",
                allow_fainted_subject=True,  # 自身が直接攻撃でひんしになった場合でも発動する
            )
        }
    ),
    "ねつこうかん": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.prevent_burn_ailment,
                "target:self",
            ),
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.ねつこうかん_boost_atk_on_fire,
                subject_spec="defender:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.ねつこうかん_cure_burn_on_enable,
                subject_spec="source:self",
            ),
        }
    ),
    "ねつぼうそう": AbilityData(
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.AbilityHandler(
                h.ねつぼうそう_modify_power,
                subject_spec="attacker:self",
            )
        }
    ),
    "ねんちゃく": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_CHECK_ITEM_CHANGE: h.AbilityHandler(
                h.ねんちゃく_prevent_item_change,
                subject_spec="target:self",
            )
        }
    ),
    "のろわれボディ": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.のろわれボディ_maybe_disable_move,
                subject_spec="defender:self",
                priority=20,
                # その攻撃で自身がひんしになったときでも発動する仕様
                # （.internal/spec/abilities/のろわれボディ.md）のため、瀕死主体でも発動を許可する。
                allow_fainted_subject=True,
            )
        }
    ),
    "ノーガード": AbilityData(
        handlers={
            Event.ON_MODIFY_ACCURACY: [
                h.AbilityHandler(
                    h.ノーガード_guarantee_hit,
                    subject_spec="attacker:self",
                ),
                h.AbilityHandler(
                    h.ノーガード_guarantee_hit,
                    subject_spec="defender:self",
                ),
            ]
        }
    ),
    "ノーてんき": AbilityData(
        handlers={
            Event.ON_CHECK_WEATHER_ENABLED: h.AbilityHandler(
                h.エアロック_check_weather_enabled,
                subject_spec="source:self",
            ),
        },
    ),
    "ノーマルスキン": AbilityData(
        handlers={
            Event.ON_MODIFY_MOVE_TYPE: h.AbilityHandler(
                h.ノーマルスキン_modify_move_type,
                subject_spec="attacker:self",
            ),
            Event.ON_CALC_POWER_MODIFIER: h.AbilityHandler(
                h.ノーマルスキン_boost_power,
                subject_spec="attacker:self",
            ),
        }
    ),
    "はがねつかい": AbilityData(
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.はがねつかい_modify_atk,
                subject_spec="attacker:self",
            )
        }
    ),
    "はがねのせいしん": AbilityData(
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.AbilityHandler(
                h.はがねのせいしん_modify_power,
                subject_spec="attacker:self",
            )
        }
    ),
    "はじまりのうみ": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.はじまりのうみ_activate_weather,
                "source:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.はじまりのうみ_activate_weather,
                "source:self",
            ),
            Event.ON_SWITCH_OUT: h.AbilityHandler(
                h.はじまりのうみ_deactivate_strong_weather,
                "source:self",
                allow_fainted_subject=True,  # 瀕死交代(ON_SWITCH_OUT)でも強制天候を解除する
            ),
            Event.ON_ABILITY_DISABLED: h.AbilityHandler(
                h.はじまりのうみ_deactivate_strong_weather,
                "source:self",
                allow_fainted_subject=True,  # 瀕死交代(ON_SWITCH_OUT)でも強制天候を解除する
                ignored_disable_reasons=frozenset({"とくせいなし"}),  # 自身がとくせいなしで無効化された結果として発火するため、その理由は無視する
            ),
        },
    ),
    "はっこう": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_BEFORE_MODIFY_STAT: h.AbilityHandler(
                h.はっこう_block_acc_drop,
                subject_spec="target:self",
            ),
            Event.ON_GET_STAT_RANK: h.AbilityHandler(
                h.はっこう_ignore_evasion,
                subject_spec="attacker:self",
            )
        }
    ),
    "はとむね": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_BEFORE_MODIFY_STAT: h.AbilityHandler(
                h.はとむね_block_B_drop,
                subject_spec="target:self",
            )
        }
    ),
    "ハドロンエンジン": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.ハドロンエンジン_activate_terrain,
                "source:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.ハドロンエンジン_activate_terrain,
                "source:self",
            ),
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.ハドロンエンジン_modify_atk,
                subject_spec="attacker:self",
            ),
        }
    ),
    "はやあし": AbilityData(
        handlers={
            DomainEvent.ON_CALC_SPEED: h.AbilityHandler(
                h.はやあし_modify_speed,
                subject_spec="source:self",
            ),
        }
    ),
    "はやおき": AbilityData(
        handlers={
            Event.ON_TRY_ACTION: h.AbilityHandler(
                h.はやおき_extra_decrement,
                subject_spec="attacker:self",
                priority=9,  # ねむりカウント消費 (priority=10) の直前
            ),
        }
    ),
    "はやてのつばさ": AbilityData(
        handlers={
            DomainEvent.ON_MODIFY_MOVE_PRIORITY: h.AbilityHandler(
                h.はやてのつばさ_modify_priority,
                subject_spec="attacker:self",
            ),
        }
    ),
    "はらぺこスイッチ": AbilityData(
        flags={
            "uncopyable"
        },
        handlers={
            Event.ON_SWITCH_OUT: h.AbilityHandler(
                h.はらぺこスイッチ_on_switch_out,
                subject_spec="source:self",
                allow_fainted_subject=True,  # 瀕死交代でON_SWITCH_OUTが発火した場合もフォルム状態更新が必要
            ),
            Event.ON_TURN_END: h.AbilityHandler(
                h.はらぺこスイッチ_on_turn_end,
                subject_spec="source:self",
                # .internal/spec/turn.md ON_TURN_END: 「160 ダルマモード/リミットシールド/
                # スワームチェンジ/ぎょぐんによるフォルムチェンジ」と同じ160だと
                # _sort_handlers の (priority, -speed) tie-break ですばやさ次第で
                # 順序が入れ替わってしまう。一次情報で「すばやさに関係なくはらぺこ
                # スイッチが後に発動する」と明記されているため、161にして必ず後に回す。
                priority=161,
            ),
        }
    ),
    "はりきり": AbilityData(
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.はりきり_modify_atk,
                subject_spec="attacker:self",
            ),
            Event.ON_MODIFY_ACCURACY: h.AbilityHandler(
                h.はりきり_modify_accuracy,
                subject_spec="attacker:self",
            ),
        }
    ),
    "はりこみ": AbilityData(
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.はりこみ_modify_atk,
                subject_spec="attacker:self",
            )
        }
    ),
    "はんすう": AbilityData(
        handlers={
            Event.ON_BERRY_CONSUMED: h.AbilityHandler(
                h.はんすう_start_counter,
                subject_spec="source:self",
            ),
            Event.ON_TURN_END: h.AbilityHandler(
                h.はんすう_on_turn_end,
                subject_spec="source:self",
                priority=150,  # .internal/spec/turn.md ON_TURN_END: 「150 はんすう」
            ),
        }
    ),
    "ハードロック": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.AbilityHandler(
                h.ハードロック_reduce_effective,
                subject_spec="defender:self",
            )
        }
    ),
    "ばけのかわ": AbilityData(
        flags={
            "uncopyable",
            "protected",
            "per_battle_once",
            "mold_breaker_ignorable",
            "gas_proof",
        },
        handlers={
            # .internal/spec/turn.md Event.ON_MODIFY_DAMAGE: 40番（ばけのかわに被弾）。
            # アイスフェイス（同じ40）と同一の優先度。ちきゅうなげ/ナイトヘッド等の
            # level_fixed_damage（priority=15）より後に実行し、確定した攻撃側の
            # ダメージ値を0へ上書きする必要がある。がんじょう/きあいのタスキ/
            # きあいのハチマキ（いずれもデフォルト優先度100）より先に完全ブロックする
            # 必要があるため、40であればこの両条件を同時に満たす。
            Event.ON_MODIFY_MOVE_DAMAGE: h.AbilityHandler(
                h.ばけのかわ_block_damage,
                subject_spec="defender:self",
                priority=40,
            ),
            # こんらんの自傷ダメージは技扱いではないため ON_MODIFY_NON_MOVE_DAMAGE で別途判定する
            Event.ON_MODIFY_NON_MOVE_DAMAGE: h.AbilityHandler(
                h.ばけのかわ_block_confusion_damage,
                subject_spec="target:self",
            ),
        },
        lethal_handlers={
            LethalEvent.ON_BEFORE_HIT: LethalHandler(
                func=l.ばけのかわ_block_damage,
                subject="defender",
            )
        },
    ),
    "バッテリー": AbilityData(),
    "バトルスイッチ": AbilityData(
        flags={
            "uncopyable",
            "protected",
            "gas_proof",
        },
        handlers={
            Event.ON_TRY_ACTION: h.AbilityHandler(
                h.バトルスイッチ_change_form,
                subject_spec="attacker:self",
                priority=200,
            ),
            Event.ON_SWITCH_OUT: h.AbilityHandler(
                h.バトルスイッチ_revert_form,
                subject_spec="source:self",
                allow_fainted_subject=True,  # 瀕死交代(ON_SWITCH_OUT)でも発動する
            ),
        },
    ),
    "バリアフリー": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.バリアフリー_remove_screens,
                subject_spec="source:self",
            ),
        }
    ),
    "ばんけん": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_BEFORE_MODIFY_STAT: h.AbilityHandler(
                h.ばんけん_boost_atk_on_intimidate,
                subject_spec="target:self",
            ),
            Event.ON_TRY_BLOW: h.AbilityHandler(
                h.ばんけん_block_blow,
                subject_spec="defender:self",
            ),
        }
    ),
    "パステルベール": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.prevent_poison_ailment,
                "target:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.パステルベール_cure_poison_on_enable,
                subject_spec="source:self",
            ),
        }
    ),
    "パワースポット": AbilityData(),
    "パンクロック": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.AbilityHandler(
                h.パンクロック_modify_power,
                subject_spec="attacker:self",
            ),
            Event.ON_CALC_DAMAGE_MODIFIER: h.AbilityHandler(
                h.パンクロック_reduce_damage,
                subject_spec="defender:self",
            ),
        }
    ),
    "ひでり": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.ひでり_activate_weather,
                "source:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.ひでり_activate_weather,
                "source:self",
            ),
        }
    ),
    "ひとでなし": AbilityData(
        handlers={
            Event.ON_CALC_CRITICAL_RANK: h.AbilityHandler(
                h.ひとでなし_modify_critical_rank,
                subject_spec="attacker:self",
            )
        }
    ),
    "ひひいろのこどう": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.ひひいろのこどう_activate_weather,
                "source:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.ひひいろのこどう_activate_weather,
                "source:self",
            ),
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.ひひいろのこどう_modify_atk,
                subject_spec="attacker:self",
            ),
        }
    ),
    "ひらいしん": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.AbilityHandler(
                h.ひらいしん_absorb_electric,
                subject_spec="defender:self",
            )
        },
    ),
    "ヒーリングシフト": AbilityData(
        handlers={
            DomainEvent.ON_MODIFY_MOVE_PRIORITY: h.AbilityHandler(
                h.ヒーリングシフト_modify_priority,
                subject_spec="attacker:self",
            ),
        }
    ),
    "ビビッドボディ": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_TRY_MOVE_1: h.AbilityHandler(
                h.じょおうのいげん_block_priority,
                subject_spec="defender:self",
                priority=40,
            ),
        }
    ),
    "びびり": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.びびり_boost_spd_on_fear_move,
                subject_spec="defender:self",
            ),
            # priority=140: しろいきり(130)やクリアボディ等の無効化ハンドラ(既定100)より後に
            # 判定し、いかくの効果が実際に無効化された場合は発動しないようにする
            # （一次情報: .internal/wiki/abilities/びびり.html 特性の仕様#第八世代以降）。
            Event.ON_BEFORE_MODIFY_STAT: h.AbilityHandler(
                h.びびり_boost_spd_on_intimidate,
                subject_spec="target:self",
                priority=140,
            ),
        }
    ),
    "びんじょう": AbilityData(
        handlers={
            Event.ON_MODIFY_STAT: h.AbilityHandler(
                h.びんじょう_copy_stat_rise,
                subject_spec="target:foe",
            ),
        }
    ),
    "ビーストブースト": AbilityData(
        handlers={
            Event.ON_MOVE_KO: h.AbilityHandler(
                h.ビーストブースト_boost_best_stat_on_ko,
                subject_spec="attacker:self",
                allow_fainted_subject=True,  # HPコスト技等で自身が瀕死になっても、撃破時(ON_MOVE_KO)の効果は発動する
            )
        }
    ),
    "ファントムガード": AbilityData(
        flags={
            "full_hp_damage_modifier",
        },
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.AbilityHandler(
                h.マルチスケイル_reduce_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "ファーコート": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_CALC_DEF_MODIFIER: h.AbilityHandler(
                h.ファーコート_boost_B,
                subject_spec="defender:self",
            )
        }
    ),
    "フィルター": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.AbilityHandler(
                h.ハードロック_reduce_effective,
                subject_spec="defender:self",
            )
        }
    ),
    "ふうりょくでんき": AbilityData(
        handlers={
            # ON_DAMAGE_HIT は actual_damage<=0 のとき発火しないため採用しない。こらえるで
            # HP1のまま耐えたときなど（実HPダメージ0）も発動する仕様
            # （.internal/spec/abilities/ふうりょくでんき.md）を満たすため、常に発火する Event.ON_HIT
            # を使用する（みがわりに阻まれた場合はハンドラ内で ctx.substitute_damage を見て除外する）。
            Event.ON_HIT: h.AbilityHandler(
                h.ふうりょくでんき_on_damage,
                subject_spec="defender:self",
                # 風の技でHPが0になったときも特性が発動してからひんしになる仕様
                # （.internal/spec/abilities/ふうりょくでんき.md）のため、瀕死主体でも発動を許可する。
                allow_fainted_subject=True,
            ),
            Event.ON_FIELD_ACTIVATE: h.AbilityHandler(
                h.ふうりょくでんき_on_field_activate,
                subject_spec="source:self",
            ),
        }
    ),
    "フェアリーオーラ": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.announce_ability_triggered,
                subject_spec="source:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.announce_ability_triggered,
                subject_spec="source:self",
            ),
            Event.ON_CALC_POWER_MODIFIER: [
                h.AbilityHandler(
                    h.フェアリーオーラ_boost_power,
                    subject_spec="attacker:self",
                ),
                h.AbilityHandler(
                    h.フェアリーオーラ_boost_power,
                    subject_spec="defender:self",
                ),
            ],
        }
    ),
    "フェアリースキン": AbilityData(
        handlers={
            Event.ON_MODIFY_MOVE_TYPE: h.AbilityHandler(
                h.フェアリースキン_modify_move_type,
                subject_spec="attacker:self",
            ),
            Event.ON_CALC_POWER_MODIFIER: h.AbilityHandler(
                h.フェアリースキン_modify_power,
                subject_spec="attacker:self",
            ),
        }
    ),
    "ふかしのこぶし": AbilityData(
        handlers={
            Event.ON_CHECK_PROTECT: h.AbilityHandler(
                h.ふかしのこぶし_bypass_protect,
                subject_spec="attacker:self",
            ),
            Event.ON_CALC_PROTECT_MODIFIER: h.AbilityHandler(
                h.ふかしのこぶし_reduce_damage,
                subject_spec="attacker:self",
            ),
        }
    ),
    "ふくがん": AbilityData(
        handlers={
            Event.ON_MODIFY_ACCURACY: h.AbilityHandler(
                h.ふくがん_boost_accuracy,
                subject_spec="attacker:self",
            ),
        }
    ),
    "ふくつのこころ": AbilityData(
        handlers={
            Event.ON_VOLATILE_START: h.AbilityHandler(
                h.ふくつのこころ_boost_spd_on_flinch,
                subject_spec="source:self",
            )
        }
    ),
    "ふくつのたて": AbilityData(
        flags={
            "per_battle_once"
        },
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.ふくつのたて_boost_B,
                subject_spec="source:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.ふくつのたて_boost_B,
                subject_spec="source:self",
            ),
        }
    ),
    "ふしぎなうろこ": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_CALC_DEF_MODIFIER: h.AbilityHandler(
                h.ふしぎなうろこ_boost_B,
                subject_spec="defender:self",
            )
        }
    ),
    "ふしぎなまもり": AbilityData(
        flags={"mold_breaker_ignorable"},
        handlers={
            Event.ON_TRY_MOVE_1: h.AbilityHandler(
                h.ふしぎなまもり_block_non_effective,
                subject_spec="defender:self",
                priority=110,
            ),
        }
    ),
    "ふしょく": AbilityData(),
    "ふとうのけん": AbilityData(
        flags={
            "per_battle_once"
        },
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.ふとうのけん_boost_A,
                subject_spec="source:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.ふとうのけん_boost_A,
                subject_spec="source:self",
            ),
        }
    ),
    "ふみん": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.prevent_sleep_ailment,
                "target:self",
            ),
            Event.ON_BEFORE_APPLY_VOLATILE: h.AbilityHandler(
                h.ふみん_prevent_volatile,
                "target:self",
            ),
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.ふみん_cure_sleep_on_enable,
                subject_spec="source:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.ふみん_cure_sleep_on_enable,
                subject_spec="source:self",
            ),
        }
    ),
    "ふゆう": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_CHECK_FLOATING: h.AbilityHandler(
                h.ふゆう_float,
                subject_spec="source:self",
                allow_fainted_subject=True,  # 技のダメージ計算中に使用者が瀕死になっても浮遊判定は維持する
            )
        }
    ),
    "フラワーギフト": AbilityData(
        flags={
            "uncopyable",
            "mold_breaker_ignorable",
        },
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.フラワーギフト_modify_atk,
                subject_spec="attacker:self",
            ),
            Event.ON_CALC_DEF_MODIFIER: h.AbilityHandler(
                h.フラワーギフト_modify_def,
                subject_spec="defender:self",
            ),
        }
    ),
    "フラワーベール": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.フラワーベール_prevent_ailment,
                subject_spec="target:self",
            ),
            Event.ON_BEFORE_MODIFY_STAT: h.AbilityHandler(
                h.フラワーベール_prevent_stat_drop,
                subject_spec="target:self",
            ),
            Event.ON_BEFORE_APPLY_VOLATILE: h.AbilityHandler(
                h.フラワーベール_prevent_volatile,
                subject_spec="target:self",
            ),
        }
    ),
    "フリーズスキン": AbilityData(
        handlers={
            Event.ON_MODIFY_MOVE_TYPE: h.AbilityHandler(
                h.フリーズスキン_modify_move_type,
                subject_spec="attacker:self",
            ),
            Event.ON_CALC_POWER_MODIFIER: h.AbilityHandler(
                h.フリーズスキン_modify_power,
                subject_spec="attacker:self",
            ),
        }
    ),
    "フレンドガード": AbilityData(
        flags={
            "mold_breaker_ignorable"
        }
    ),
    "ぶきよう": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.ぶきよう_disable_item,
                subject_spec="source:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.ぶきよう_disable_item,
                subject_spec="source:self",
            ),
            Event.ON_ABILITY_DISABLED: h.AbilityHandler(
                h.ぶきよう_enable_item,
                subject_spec="source:self",
                ignored_disable_reasons=frozenset({"とくせいなし"}),  # 自身がとくせいなしで無効化された結果として発火するため、その理由は無視する
            ),
        }
    ),
    "ブレインフォース": AbilityData(
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.AbilityHandler(
                h.ブレインフォース_boost_effective,
                subject_spec="attacker:self",
            )
        }
    ),
    "プラス": AbilityData(),
    "プリズムアーマー": AbilityData(
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.AbilityHandler(
                h.ハードロック_reduce_effective,
                subject_spec="defender:self",
            )
        }
    ),
    "プレッシャー": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.プレッシャー_announce,
                subject_spec="source:self",
            ),
            Event.ON_MODIFY_PP_CONSUMED: h.AbilityHandler(
                h.プレッシャー_extra_pp,
                subject_spec="defender:self",
            ),
        }
    ),
    "ヘドロえき": AbilityData(
        handlers={
            Event.ON_MODIFY_HEAL: h.AbilityHandler(
                h.ヘドロえき_reverse_drain,
                subject_spec="target:foe",
                # かいふくふうじの回復ブロック（優先度100）より先に処理し、
                # 回復量をダメージへ変換したうえで通過させる必要があるため優先度を上げる。
                priority=90,
                # ヘドロえきのポケモンがひんしになったときも発動する仕様
                # （.internal/spec/abilities/ヘドロえき.md）のため、瀕死主体でも発動を許可する。
                allow_fainted_subject=True,
            ),
        }
    ),
    "へんげんじざい": AbilityData(
        handlers={
            Event.ON_MOVE_CHARGE: h.AbilityHandler(
                h.へんげんじざい_change_type,
                subject_spec="attacker:self",
                priority=100,
            )
        }
    ),
    "へんしょく": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.へんしょく_copy_move_type,
                subject_spec="defender:self",
            ),
        }
    ),
    "ヘヴィメタル": AbilityData(
        flags={
            "mold_breaker_ignorable"
        }
    ),
    "ほうし": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.ほうし_maybe_inflict_ailment_on_contact,
                subject_spec="defender:self",
                # その攻撃で特性所有者がひんし状態になったときも発動する仕様
                # （.internal/spec/abilities/ほうし.md）のため、瀕死主体でも発動を許可する。
                allow_fainted_subject=True,
            )
        }
    ),
    "ほおぶくろ": AbilityData(
        handlers={
            Event.ON_BERRY_CONSUMED: h.AbilityHandler(
                h.ほおぶくろ_heal_on_berry_consumed,
                subject_spec="source:self",
            )
        }
    ),
    "ほのおのからだ": AbilityData(
        handlers={
            # ON_DAMAGE_HIT は actual_damage<=0 のとき発火しないため採用しない。こらえるで
            # HP1のまま耐えたときやみねうちを受けたとき（実HPダメージ0）も発動する仕様
            # （どくげしょう・どくのくさり等の同種特性と同じ挙動）を満たすため、常に発火する
            # Event.ON_HIT を使用する（みがわりに阻まれた場合はハンドラ内で
            # ctx.substitute_damage を見て除外する）。
            Event.ON_HIT: h.AbilityHandler(
                h.ほのおのからだ_maybe_burn_attacker,
                subject_spec="defender:self",
                # 攻撃技でひんしになったときも発動する仕様
                # （.internal/spec/abilities/ほのおのからだ.md）のため、瀕死主体でも発動を許可する。
                allow_fainted_subject=True,
            )
        }
    ),
    "ほのおのたてがみ": AbilityData(
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.ほのおのたてがみ_modify_atk,
                subject_spec="attacker:self",
            )
        }
    ),
    "ほろびのボディ": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.ほろびのボディ_apply_perish_song_on_contact,
                subject_spec="defender:self",
                priority=20,
                allow_fainted_subject=True,  # 自身が接触技でひんしになった場合でも発動する
            )
        }
    ),
    "ぼうおん": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.AbilityHandler(
                h.ぼうおん_block_sound,
                subject_spec="defender:self",
            ),
        }
    ),
    "ぼうじん": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.AbilityHandler(
                h.ぼうじん_block_powder,
                subject_spec="defender:self",
            ),
            Event.ON_MODIFY_NON_MOVE_DAMAGE: h.AbilityHandler(
                h.ぼうじん_block_sandstorm_damage,
                subject_spec="target:self",
            ),
        }
    ),
    "ぼうだん": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.AbilityHandler(
                h.ぼうだん_block_bullet,
                subject_spec="defender:self",
            ),
        }
    ),
    "ポイズンヒール": AbilityData(
        handlers={
            Event.ON_MODIFY_POISON_DAMAGE: h.AbilityHandler(
                h.ポイズンヒール_modify_poison_damage,
                subject_spec="target:self",
            )
        },
        lethal_handlers={
            LethalEvent.ON_TURN_END: LethalHandler(
                func=l.ポイズンヒール_heal,
                subject="defender",
            )
        }
    ),
    "マイティチェンジ": AbilityData(
        flags={
            "uncopyable",
            "protected",
            "gas_proof",
        },
        handlers={
            Event.ON_SWITCH_OUT: h.AbilityHandler(
                h.マイティチェンジ_change_form,
                subject_spec="source:self",
            ),
        },
    ),
    "マイナス": AbilityData(),
    "マイペース": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_BEFORE_APPLY_VOLATILE: h.AbilityHandler(
                h.マイペース_prevent_volatile,
                "target:self",
            ),
            Event.ON_BEFORE_MODIFY_STAT: h.AbilityHandler(
                h.マイペース_block_intimidate,
                subject_spec="target:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.マイペース_cure_confusion_on_enable,
                subject_spec="source:self",
            ),
        }
    ),
    "マグマのよろい": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.prevent_freeze_ailment,
                "target:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.マグマのよろい_cure_freeze_on_enable,
                subject_spec="source:self",
            ),
        }
    ),
    "まけんき": AbilityData(
        handlers={
            Event.ON_MODIFY_STAT: h.AbilityHandler(
                h.まけんき_boost_atk_on_stat_drop,
                subject_spec="target:self",
            )
        }
    ),
    "マジシャン": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.マジシャン_steal_item,
                subject_spec="attacker:self",
            )
        }
    ),
    "マジックガード": AbilityData(
        handlers={
            Event.ON_MODIFY_NON_MOVE_DAMAGE: h.AbilityHandler(
                h.マジックガード_ignore_damage,
                subject_spec="target:self",
            )
        }
    ),
    "マジックミラー": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_CHECK_REFLECT: h.AbilityHandler(
                h.マジックミラー_reflect,
                subject_spec="defender:self",
                priority=200,
            )
        }
    ),
    "マルチスケイル": AbilityData(
        flags={
            "mold_breaker_ignorable",
            "full_hp_damage_modifier",
        },
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.AbilityHandler(
                h.マルチスケイル_reduce_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "マルチタイプ": AbilityData(
        flags={
            "uncopyable",
            "protected",
            "gas_proof",
        },
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.マルチタイプ_apply_type,
                subject_spec="source:self",
            ),
            Event.ON_CHECK_ITEM_CHANGE: h.AbilityHandler(
                h.マルチタイプ_block_item_change,
                subject_spec="target:self",
            ),
        }
    ),
    "ミイラ": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.ミイラ_overwrite_attacker_ability,
                subject_spec="defender:self",
                priority=20,
                allow_fainted_subject=True,  # 自身が直接攻撃でひんしになった場合でも発動する
            ),
        }
    ),
    "ミストメイカー": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.ミストメイカー_activate_terrain,
                "source:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.ミストメイカー_activate_terrain,
                "source:self",
            ),
        }
    ),
    "みずがため": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.みずがため_boost_B_on_water,
                subject_spec="defender:self",
                priority=20,
            )
        }
    ),
    "みずのベール": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.prevent_burn_ailment,
                "target:self",
            ),
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.みずのベール_cure_burn_on_enable,
                subject_spec="source:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.みずのベール_cure_burn_on_enable,
                subject_spec="source:self",
            ),
        }
    ),
    "みつあつめ": AbilityData(),
    "ミラクルスキン": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_MODIFY_ACCURACY: h.AbilityHandler(
                h.ミラクルスキン_reduce_accuracy,
                subject_spec="defender:self",
            )
        }
    ),
    "ミラーアーマー": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            # priority=140: クリアチャーム(既定100)やしろいきり(130)の無効化ハンドラより
            # 後に判定し、それらで既にランク低下が無効化されている場合は反射しないようにする
            # （一次情報: .internal/wiki/abilities/ミラーアーマー.html 特性の仕様）。
            Event.ON_BEFORE_MODIFY_STAT: h.AbilityHandler(
                h.ミラーアーマー_reflect_stat_drop,
                subject_spec="target:self",
                priority=140,
            )
        }
    ),
    "むしのしらせ": AbilityData(
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.しんりょくもうかげきりゅうむしのしらせ_modify_atk,
                subject_spec="attacker:self",
            )
        }
    ),
    "ムラっけ": AbilityData(
        handlers={
            Event.ON_TURN_END: h.AbilityHandler(
                h.ムラっけ_boost_stats,
                subject_spec="source:self",
                priority=150,
            )
        }
    ),
    "メガソーラー": AbilityData(
        handlers={
            Event.ON_BEGIN_MOVE: h.AbilityHandler(
                h.メガソーラー_activate,
                subject_spec="attacker:self",
            ),
            Event.ON_END_MOVE: h.AbilityHandler(
                h.メガソーラー_deactivate,
                subject_spec="attacker:self",
            ),
            Event.ON_CHECK_WEATHER_ENABLED: h.AbilityHandler(
                h.メガソーラー_force_weather_enabled,
                subject_spec="source:self",
                priority=1,
            ),
        }
    ),
    "メガランチャー": AbilityData(
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.AbilityHandler(
                h.メガランチャー_modify_power,
                subject_spec="attacker:self",
            )
        }
    ),
    "メタルプロテクト": AbilityData(
        handlers={
            Event.ON_BEFORE_MODIFY_STAT: h.AbilityHandler(
                h.クリアボディ_block_stat_drop,
                subject_spec="target:self",
            )
        }
    ),
    "メロメロボディ": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.メロメロボディ_maybe_infatuate_attacker,
                subject_spec="defender:self",
                # 攻撃技でひんしになったときもメロメロボディは発動する（即座に効果は消える）
                # 仕様（.internal/spec/abilities/メロメロボディ.md）のため、瀕死主体でも
                # 発動を許可する。
                allow_fainted_subject=True,
            )
        }
    ),
    "めんえき": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.prevent_poison_ailment,
                "target:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.めんえき_cure_poison_on_enable,
                subject_spec="source:self",
            ),
        }
    ),
    "もうか": AbilityData(
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.しんりょくもうかげきりゅうむしのしらせ_modify_atk,
                subject_spec="attacker:self",
            )
        }
    ),
    "ものひろい": AbilityData(
        handlers={
            Event.ON_TURN_END: h.AbilityHandler(
                h.ものひろい_pickup_foe_item,
                subject_spec="source:self",
                priority=150,
            ),
        }
    ),
    "もふもふ": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.AbilityHandler(
                h.もふもふ_modify_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "もらいび": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.もらいび_init_state,
                subject_spec="source:self",
            ),
            Event.ON_BEFORE_APPLY_MOVE: h.AbilityHandler(
                h.もらいび_block_fire,
                subject_spec="defender:self",
            ),
            Event.ON_MOVE_CHARGE: h.AbilityHandler(
                h.もらいび_reserve_fire_boost,
                subject_spec="attacker:self",
            ),
            Event.ON_MOVE_END: h.AbilityHandler(
                h.もらいび_consume_fire_boost,
                subject_spec="attacker:self",
            ),
            Event.ON_CALC_POWER_MODIFIER: h.AbilityHandler(
                h.もらいび_modify_power,
                subject_spec="attacker:self",
            ),
        },
    ),
    "やるき": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.prevent_sleep_ailment,
                "target:self",
            ),
            Event.ON_BEFORE_APPLY_VOLATILE: h.AbilityHandler(
                h.やるき_prevent_volatile,
                "target:self",
            ),
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.やるき_cure_sleep_on_enable,
                subject_spec="source:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.やるき_cure_sleep_on_enable,
                subject_spec="source:self",
            ),
        }
    ),
    "ゆうばく": AbilityData(
        handlers={
            Event.ON_MOVE_KO: h.AbilityHandler(
                h.ゆうばく_damage_attacker_on_ko,
                subject_spec="defender:self",
                allow_fainted_subject=True,  # 自身が瀕死になった(ON_MOVE_KO)ことがこの効果の発動条件
            )
        }
    ),
    "ゆきかき": AbilityData(
        handlers={
            DomainEvent.ON_CALC_SPEED: h.AbilityHandler(
                h.ゆきかき_boost_speed,
                subject_spec="source:self",
            ),
        }
    ),
    "ゆきがくれ": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_MODIFY_ACCURACY: h.AbilityHandler(
                h.ゆきがくれ_reduce_accuracy,
                subject_spec="defender:self",
            ),
        }
    ),
    "ゆきふらし": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.ゆきふらし_activate_weather,
                "source:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.ゆきふらし_activate_weather,
                "source:self",
            ),
        }
    ),
    "ようりょくそ": AbilityData(
        handlers={
            DomainEvent.ON_CALC_SPEED: h.AbilityHandler(
                h.ようりょくそ_boost_speed,
                subject_spec="source:self",
            )
        }
    ),
    "ヨガパワー": AbilityData(
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.ちからもち_boost_physical,
                subject_spec="attacker:self",
            )
        }
    ),
    "よちむ": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.よちむ_reveal_strongest_move,
                subject_spec="source:self",
            ),
        }
    ),
    "よびみず": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.AbilityHandler(
                h.よびみず_absorb_water,
                subject_spec="defender:self",
            )
        },
    ),
    "よわき": AbilityData(
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.よわき_modify_atk,
                subject_spec="attacker:self",
            )
        }
    ),
    "ライトメタル": AbilityData(
        flags={
            "mold_breaker_ignorable"
        }
    ),
    "リベロ": AbilityData(
        handlers={
            Event.ON_MOVE_CHARGE: h.AbilityHandler(
                h.へんげんじざい_change_type,
                subject_spec="attacker:self",
                priority=100,
            )
        }
    ),
    "リミットシールド": AbilityData(
        flags={
            "uncopyable",
            "protected",
            "gas_proof",
        },
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.リミットシールド_enter_meteor_form,
                subject_spec="source:self",
                priority=120,
            ),
            Event.ON_TURN_END: h.AbilityHandler(
                h.リミットシールド_update_form,
                subject_spec="source:self",
                priority=160,
            ),
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.リミットシールド_prevent_ailment,
                subject_spec="target:self",
            ),
            Event.ON_BEFORE_APPLY_VOLATILE: h.AbilityHandler(
                h.リミットシールド_prevent_drowsy,
                subject_spec="target:self",
            ),
            Event.ON_SWITCH_OUT: h.AbilityHandler(
                h.リミットシールド_revert_form,
                subject_spec="source:self",
                allow_fainted_subject=True,  # 瀕死交代(ON_SWITCH_OUT)でも発動する
            ),
        }
    ),
    "りゅうのあぎと": AbilityData(
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.りゅうのあぎと_modify_atk,
                subject_spec="attacker:self",
            )
        }
    ),
    "りんぷん": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_MODIFY_SECONDARY_CHANCE: h.AbilityHandler(
                h.りんぷん_block_secondary_chance,
                subject_spec="defender:self",
            ),
        }
    ),
    "リーフガード": AbilityData(
        flags={
            "mold_breaker_ignorable"
        },
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.リーフガード_prevent_ailment,
                subject_spec="target:self",
            ),
        }
    ),
    "レシーバー": AbilityData(
        flags={
            "uncopyable"
        }
    ),
    "わざわいのうつわ": AbilityData(
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.わざわいのうつわ_reduce_C,
                subject_spec="defender:self",
            )
        }
    ),
    "わざわいのおふだ": AbilityData(
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.わざわいのおふだ_reduce_A,
                subject_spec="defender:self",
            )
        }
    ),
    "わざわいのたま": AbilityData(
        handlers={
            Event.ON_CALC_DEF_MODIFIER: h.AbilityHandler(
                h.わざわいのたま_reduce_D,
                subject_spec="attacker:self",
            )
        }
    ),
    "わざわいのつるぎ": AbilityData(
        handlers={
            Event.ON_CALC_DEF_MODIFIER: h.AbilityHandler(
                h.わざわいのつるぎ_reduce_B,
                subject_spec="attacker:self",
            )
        }
    ),
    "わたげ": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.わたげ_lower_spd_on_hit,
                subject_spec="defender:self",
                allow_fainted_subject=True,  # 自身が直接攻撃でひんしになった場合でも発動する
            )
        }
    ),
    "わるいてぐせ": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.わるいてぐせ_steal_item,
                subject_spec="defender:self",
                priority=180,
            )
        }
    ),
}


common_setup()
