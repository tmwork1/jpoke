"""特性データ定義モジュール。

Note:
    このモジュール内の特性定義はABILITIES辞書内で五十音順に配置されています。
"""

from jpoke.enums import DomainEvent, Event
from jpoke.handlers import ability as h, ability_paradox as paradox
from .models import AbilityData


def common_setup():
    """共通のセットアップ処理"""
    for name in ABILITIES:
        ABILITIES[name].name = name


ABILITIES: dict[str, AbilityData] = {
    "": AbilityData(name=""),
    "ARシステム": AbilityData(
        flags=[
            "uncopyable",
            "protected",
            "gas_proof",
        ],
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
        flags=[
            "uncopyable",
            "protected",
            "mold_breaker_ignorable",
            "gas_proof",
        ],
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
                h.アイスボディ_on_turn_end,
                subject_spec="source:self",
                priority=30,
            ),
        }
    ),
    "あくしゅう": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.あくしゅう_on_damage,
                subject_spec="attacker:self",
            )
        }
    ),
    "あついしぼう": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
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
                h.あとだし_on_calc_back_tier,
                subject_spec="source:self",
            ),
        }
    ),
    "アナライズ": AbilityData(
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.AbilityHandler(
                h.アナライズ_modify_power,
                subject_spec="attacker:self",
            )
        }
    ),
    "あまのじゃく": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
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
        flags=[
            "mold_breaker_ignorable"
        ],
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
                h.いかりのこうら_on_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "いかりのつぼ": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.いかりのつぼ_on_damage,
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
        flags=[
            "uncopyable"
        ]
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
    "うのミサイル": AbilityData(
        flags=[
            "uncopyable",
            "protected",
            "gas_proof",
        ],
        handlers={
            Event.ON_MOVE_END: h.AbilityHandler(
                h.うのミサイル_on_move_end,
                subject_spec="attacker:self",
            ),
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.うのミサイル_on_damage_hit,
                subject_spec="defender:self",
            ),
            Event.ON_SWITCH_OUT: h.AbilityHandler(
                h.うのミサイル_on_switch_out,
                subject_spec="source:self",
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
                h.うるおいボディ_on_turn_end,
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
            )
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
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.AbilityHandler(
                h.おうごんのからだ_block_status_move,
                subject_spec="defender:self",
            )
        }
    ),
    "オーラブレイク": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
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
    "おどりこ": AbilityData(),
    "おみとおし": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.おみとおし_on_switch_in,
                subject_spec="source:self",
            ),
        }
    ),
    "おもかげやどし": AbilityData(
        flags=[
            "uncopyable",
            "protected"
        ],
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
            ),
            Event.ON_ABILITY_DISABLED: h.AbilityHandler(
                h.おわりのだいち_deactivate_strong_weather,
                "source:self",
            ),
        },
    ),
    "カーリーヘアー": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.カーリーヘアー_on_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "かいりきバサミ": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_BEFORE_MODIFY_STAT: h.AbilityHandler(
                h.かいりきバサミ_block_A_drop,
                subject_spec="target:self",
            )
        }
    ),
    "かがくへんかガス": AbilityData(
        flags=[
            "uncopyable",
            "gas_proof",
        ],
        handlers={
            Event.ON_SWITCH_IN: [
                h.AbilityHandler(
                    h.かがくへんかガス_on_switch_in,
                    subject_spec="source:self",
                    priority=20,
                ),
                h.AbilityHandler(
                    h.かがくへんかガス_foe_switch_in,
                    subject_spec="source:foe",
                    priority=20,
                ),
            ],
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.かがくへんかガス_on_switch_in,
                subject_spec="source:self",
            ),
            Event.ON_SWITCH_OUT: h.AbilityHandler(
                h.かがくへんかガス_gas_deactivate,
                subject_spec="source:self",
            ),
            Event.ON_ABILITY_DISABLED: h.AbilityHandler(
                h.かがくへんかガス_gas_deactivate,
                subject_spec="source:self",
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
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.AbilityHandler(
                h.かぜのり_absorb_wind,
                subject_spec="defender:self",
            ),
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.かぜのり_on_switch_in,
                subject_spec="source:self",
            ),
            Event.ON_FIELD_ACTIVATE: h.AbilityHandler(
                h.かぜのり_on_field_activate,
                subject_spec="source:self",
            ),
        }
    ),
    "かそく": AbilityData(
        handlers={
            Event.ON_TURN_END: h.AbilityHandler(
                h.かそく_on_turn_end,
                subject_spec="source:self",
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
        flags=[],
        handlers={
            Event.ON_MODIFY_STAT: h.AbilityHandler(
                h.かちき_on_stat_down,
                subject_spec="target:self",
            )
        }
    ),
    "カブトアーマー": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
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
            Event.ON_ABILITY_DISABLED: h.AbilityHandler(
                h.かるわざ_reset_state,
                subject_spec="source:self",
            ),
            DomainEvent.ON_CALC_SPEED: h.AbilityHandler(
                h.かるわざ_modify_speed,
                subject_spec="source:self",
            ),
        }
    ),
    "かわりもの": AbilityData(
        flags=[
            "uncopyable"
        ]
    ),
    "がんじょう": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_MODIFY_MOVE_DAMAGE: h.AbilityHandler(
                h.がんじょう_survive_lethal,
                subject_spec="defender:self",
            ),
            Event.ON_BEFORE_APPLY_MOVE: h.AbilityHandler(
                h.がんじょう_block_ohko,
                subject_spec="defender:self",
            ),
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
    "かんそうはだ": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
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
                h.かんそうはだ_on_turn_end,
                subject_spec="source:self",
                priority=30,
            ),
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
        flags=[
            "per_battle_once"
        ],
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.かんろなミツ_on_switch_in,
                subject_spec="source:self",
            )
        }
    ),
    "ききかいひ": AbilityData(
        flags=[

        ],
        handlers={
            Event.ON_HP_CHANGED: h.AbilityHandler(
                h.ききかいひ_on_hp_change,
                subject_spec="target:self",
            )
        }
    ),
    "きけんよち": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.きけんよち_on_switch_in,
                subject_spec="source:self",
            ),
        }
    ),
    "ぎたい": AbilityData(),
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
    "ぎゃくじょう": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.ぎゃくじょう_on_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "きゅうばん": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
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
    "ぎょぐん": AbilityData(
        flags=[
            "uncopyable",
            "protected",
            "gas_proof",
        ],
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.ぎょぐん_on_switch_in,
                subject_spec="source:self",
                priority=120,
            ),
            Event.ON_TURN_END: h.AbilityHandler(
                h.ぎょぐん_on_turn_end,
                subject_spec="source:self",
                priority=160,
            ),
        }
    ),
    "きよめのしお": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.きよめのしお_prevent_ailment,
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
                h.きんしのちから_on_calc_back_tier,
                subject_spec="source:self",
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
            ),
            Event.ON_CHECK_NERVOUS: h.AbilityHandler(
                h.きんちょうかん_check_nervous,
                subject_spec="source:foe",
            ),
        }
    ),
    "くいしんぼう": AbilityData(),
    "クイックドロウ": AbilityData(
        handlers={
            DomainEvent.ON_CALC_BACK_TIER: h.AbilityHandler(
                h.クイックドロウ_on_calc_back_tier,
                subject_spec="source:self",
            ),
        }
    ),
    "クォークチャージ": AbilityData(
        flags=[
            "uncopyable",
        ],
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                paradox.refresh_paradox_charge_state,
                subject_spec="source:self",
                priority=200,
            ),
            Event.ON_FIELD_CHANGE: h.AbilityHandler(
                paradox.refresh_paradox_charge_state,
                subject_spec="source:self",
                priority=200,
            ),
            Event.ON_REFRESH_PARADOX_BOOST: h.AbilityHandler(
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
        flags=[
            "mold_breaker_ignorable"
        ],
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
                h.くだけるよろい_on_damage,
                subject_spec="defender:self",
                priority=20,
            )
        }
    ),
    "グラスメイカー": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.グラスメイカー_activate_terrain,
                "source:self",
            )
        }
    ),
    "クリアボディ": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
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
            )
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
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.AbilityHandler(
                h.こおりのりんぷん_reduce_special_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "こだいかっせい": AbilityData(
        flags=[
            "uncopyable",
        ],
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                paradox.refresh_paradox_charge_state,
                subject_spec="source:self",
                priority=200,
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
            Event.ON_REFRESH_PARADOX_BOOST: h.AbilityHandler(
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
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.こぼれダネ_on_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "ごりむちゅう": AbilityData(
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.ごりむちゅう_modify_atk,
                subject_spec="attacker:self",
            )
        }
    ),
    "こんがりボディ": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
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
    "サーフテール": AbilityData(
        handlers={
            DomainEvent.ON_CALC_SPEED: h.AbilityHandler(
                h.サーフテール_modify_speed,
                subject_spec="source:self",
            )
        }
    ),
    "サイコメイカー": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.サイコメイカー_activate_terrain,
                "source:self",
            )
        }
    ),
    "さいせいりょく": AbilityData(
        handlers={
            Event.ON_SWITCH_OUT: h.AbilityHandler(
                h.さいせいりょく_on_switch_out,
                subject_spec="source:self",
            ),
        }
    ),
    "さまようたましい": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.さまようたましい_on_damage,
                subject_spec="defender:self",
            ),
        }
    ),
    "さめはだ": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.さめはだ_on_damage,
                subject_spec="defender:self",
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
                h.サンパワー_on_turn_end,
                subject_spec="source:self",
                priority=30,
            ),
        }
    ),
    "シェルアーマー": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_MODIFY_CRITICAL_RATE: h.AbilityHandler(
                h.カブトアーマー_block_crit,
                subject_spec="defender:self",
            )
        }
    ),
    "じきゅうりょく": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.じきゅうりょく_on_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "じしんかじょう": AbilityData(
        handlers={
            Event.ON_MOVE_KO: h.AbilityHandler(
                h.しろのいななき_boost,
                subject_spec="attacker:self",
            )
        }
    ),
    "しぜんかいふく": AbilityData(
        handlers={
            Event.ON_SWITCH_OUT: h.AbilityHandler(
                h.しぜんかいふく_on_switch_out,
                subject_spec="source:self",
            ),
        }
    ),
    "しめりけ": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
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
            ),
        }
    ),
    "じゅうなん": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.prevent_paralysis_ailment,
                "target:self",
            )
        }
    ),
    "じゅくせい": AbilityData(),
    "じょうきっかん": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.じょうきっかん_on_damage,
                subject_spec="defender:self",
            )
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
    "じょおうのいげん": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
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
    "しれいとう": AbilityData(
        flags=[
            "uncopyable"
        ]
    ),
    "しろいけむり": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
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
            )
        }
    ),
    "しんがん": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
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
    "じんばいったい": AbilityData(
        flags=[
            "uncopyable",
            "protected"
        ],
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.announce_ability_triggered,
                subject_spec="source:self",
            ),
            Event.ON_CHECK_NERVOUS: h.AbilityHandler(
                h.きんちょうかん_check_nervous,
                subject_spec="source:foe",
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
    "スイートベール": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
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
    "すいすい": AbilityData(
        handlers={
            DomainEvent.ON_CALC_SPEED: h.AbilityHandler(
                h.すいすい_modify_speed,
                subject_spec="source:self",
            )
        }
    ),
    "すいほう": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
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
            ]
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
            )
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
        flags=[
            "mold_breaker_ignorable"
        ],
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
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.すなはき_on_damage,
                subject_spec="defender:self",
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
                subject_spec="source:self",
            )
        }
    ),
    "するどいめ": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
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
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.スロースタート_modify_atk,
                subject_spec="attacker:self",
            ),
        }
    ),
    "スワームチェンジ": AbilityData(
        flags=[
            "uncopyable",
            "protected",
            "gas_proof",
        ],
        handlers={
            Event.ON_TURN_END: h.AbilityHandler(
                h.スワームチェンジ_on_turn_end,
                subject_spec="source:self",
                priority=160,
            ),
        }
    ),
    "せいぎのこころ": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.せいぎのこころ_on_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "せいしんりょく": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
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
                h.せいでんき_on_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "ぜったいねむり": AbilityData(
        flags=[
            "uncopyable",
            "protected",
            "gas_proof",
        ],
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.ぜったいねむり_switch_in,
                subject_spec="source:self",
            ),
        },
    ),
    "ゼロフォーミング": AbilityData(
        flags=[
            "uncopyable"
        ],
        handlers={
            Event.ON_TERASTALLIZE: h.AbilityHandler(
                h.ゼロフォーミング_on_terastallize,
                subject_spec="source:self",
            ),
        }
    ),
    "そうしょく": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
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
                h.そうだいしょう_on_switch_in,
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
                h.ソウルハート_on_ko,
                subject_spec="attacker:self",
            )
        }
    ),
    "ダークオーラ": AbilityData(
        flags=[
            "mold_breaker_ignorable",
        ],
        handlers={
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
    "ターボブレイズ": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
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
    "たいねつ": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.たいねつ_reduce_fire,
                subject_spec="defender:self",
            )
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
    "たまひろい": AbilityData(),
    "ダルマモード": AbilityData(
        flags=[
            "uncopyable",
            "protected",
            "gas_proof",
        ],
        handlers={
            Event.ON_TURN_END: h.AbilityHandler(
                h.ダルマモード_on_turn_end,
                subject_spec="source:self",
                priority=160,
            ),
            Event.ON_SWITCH_OUT: h.AbilityHandler(
                h.ダルマモード_on_switch_out,
                subject_spec="source:self",
            ),
        }
    ),
    "たんじゅん": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_BEFORE_MODIFY_STAT: h.AbilityHandler(
                h.たんじゅん_double_stat,
                subject_spec="target:self",
            )
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
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.AbilityHandler(
                h.ちくでん_absorb_electric,
                subject_spec="defender:self",
            )
        }
    ),
    "ちどりあし": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_MODIFY_ACCURACY: h.AbilityHandler(
                h.ちどりあし_reduce_accuracy,
                subject_spec="defender:self",
            )
        }
    ),
    "ちょすい": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.AbilityHandler(
                h.ちょすい_absorb_water,
                subject_spec="defender:self",
            )
        },
    ),
    "テイルアーマー": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
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
                h.さめはだ_on_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "テラスシェル": AbilityData(
        flags=[
            "uncopyable",
            "mold_breaker_ignorable",
        ],
        handlers={
            Event.ON_CALC_DEF_TYPE_MODIFIER: h.AbilityHandler(
                h.テラスシェル_overwrite_type_modifier,
                subject_spec="defender:self",
            )
        }
    ),
    "テラスチェンジ": AbilityData(
        flags=[
            "uncopyable",
            "protected",
            "gas_proof",
        ],
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.テラスチェンジ_on_switch_in,
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
            ),
            Event.ON_ABILITY_DISABLED: h.AbilityHandler(
                h.デルタストリーム_deactivate_strong_weather,
                "source:self",
            ),
        },
    ),
    "テレパシー": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "でんきエンジン": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
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
                h.でんきにかえる_on_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "てんきや": AbilityData(
        flags=[
            "uncopyable"
        ],
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
        }
    ),
    "てんねん": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_CALC_ATK_RANK_MODIFIER: h.AbilityHandler(
                h.てんねん_ignore_rank,
                subject_spec="defender:self",
            ),
            Event.ON_CALC_DEF_RANK_MODIFIER: h.AbilityHandler(
                h.てんねん_ignore_rank,
                subject_spec="attacker:self",
            ),
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
    "とうそうしん": AbilityData(
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.とうそうしん_modify_atk,
                subject_spec="attacker:self",
            )
        }
    ),
    "どくくぐつ": AbilityData(
        flags=[
            "uncopyable"
        ],
        handlers={
            Event.ON_APPLY_AILMENT: h.AbilityHandler(
                h.どくくぐつ_on_apply_ailment,
                subject_spec="source:self",
            ),
        }
    ),
    "どくげしょう": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.どくげしょう_on_damage,
                subject_spec="defender:self",
                priority=20,
            )
        }
    ),
    "どくしゅ": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.どくしゅ_on_damage,
                subject_spec="attacker:self",
            )
        }
    ),
    "どくのくさり": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.どくのくさり_on_damage,
                subject_spec="attacker:self",
            )
        }
    ),
    "どくのトゲ": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.どくのトゲ_on_damage,
                subject_spec="defender:self",
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
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.AbilityHandler(
                h.どしょく_absorb_ground,
                subject_spec="defender:self",
            )
        },
    ),
    "とびだすなかみ": AbilityData(
        handlers={
            Event.ON_BEGIN_MOVE: h.AbilityHandler(
                h.とびだすなかみ_save_hp,
                subject_spec="defender:self",
            ),
            Event.ON_MOVE_KO: h.AbilityHandler(
                h.とびだすなかみ_on_ko,
                subject_spec="defender:self",
            ),
        }
    ),
    "とびだすハバネロ": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.とびだすハバネロ_on_damage,
                subject_spec="defender:self",
            ),
        }
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
    "トランジスタ": AbilityData(
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.トランジスタ_modify_atk,
                subject_spec="attacker:self",
            )
        }
    ),
    "トレース": AbilityData(
        flags=[
            "uncopyable"
        ],
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.トレース_copy_ability,
                subject_spec="source:self",
            ),
        },
    ),
    "とれないにおい": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.とれないにおい_on_damage,
                subject_spec="defender:self",
            ),
        }
    ),
    "どんかん": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_BEFORE_APPLY_VOLATILE: h.AbilityHandler(
                h.どんかん_prevent_volatile,
                "target:self",
            )
        }
    ),
    "ナイトメア": AbilityData(
        handlers={
            Event.ON_TURN_END: h.AbilityHandler(
                h.ナイトメア_on_turn_end,
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
                priority=10,
            ),
        }
    ),
    "にげあし": AbilityData(),
    "にげごし": AbilityData(
        handlers={
            Event.ON_HP_CHANGED: h.AbilityHandler(
                h.ききかいひ_on_hp_change,
                subject_spec="target:self",
            )
        }
    ),
    "ぬめぬめ": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.ぬめぬめ_on_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "ねつこうかん": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.prevent_burn_ailment,
                "target:self",
            ),
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.ねつこうかん_on_damage,
                subject_spec="defender:self",
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
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_CHECK_ITEM_CHANGE: h.AbilityHandler(
                h.ねんちゃく_prevent_item_change,
                subject_spec="target:self",
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
    "のろわれボディ": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.のろわれボディ_on_damage,
                subject_spec="defender:self",
                priority=20,
            )
        }
    ),
    "ハードロック": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.AbilityHandler(
                h.ハードロック_reduce_effective,
                subject_spec="defender:self",
            )
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
    "ばけのかわ": AbilityData(
        flags=[
            "uncopyable",
            "protected",
            "per_battle_once",
            "mold_breaker_ignorable",
            "gas_proof",
        ],
        handlers={
            Event.ON_MODIFY_MOVE_DAMAGE: h.AbilityHandler(
                h.ばけのかわ_block_damage,
                subject_spec="defender:self",
                priority=10,
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
            ),
            Event.ON_ABILITY_DISABLED: h.AbilityHandler(
                h.はじまりのうみ_deactivate_strong_weather,
                "source:self",
            ),
        },
    ),
    "パステルベール": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.prevent_poison_ailment,
                "target:self",
            )
        }
    ),
    "はっこう": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_BEFORE_MODIFY_STAT: h.AbilityHandler(
                h.はっこう_block_acc_drop,
                subject_spec="target:self",
            )
        }
    ),
    "バッテリー": AbilityData(),
    "はとむね": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_BEFORE_MODIFY_STAT: h.AbilityHandler(
                h.はとむね_block_B_drop,
                subject_spec="target:self",
            )
        }
    ),
    "バトルスイッチ": AbilityData(
        flags=[
            "uncopyable",
            "protected",
            "gas_proof",
        ],
        handlers={
            Event.ON_TRY_ACTION: h.AbilityHandler(
                h.バトルスイッチ_change_form,
                subject_spec="attacker:self",
                priority=200,
            ),
            Event.ON_SWITCH_OUT: h.AbilityHandler(
                h.バトルスイッチ_revert_form,
                subject_spec="source:self",
            ),
        },
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
                priority=200,
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
        flags=[
            "uncopyable"
        ],
        handlers={
            Event.ON_SWITCH_OUT: h.AbilityHandler(
                h.はらぺこスイッチ_on_switch_out,
                subject_spec="source:self",
            ),
            Event.ON_TURN_END: h.AbilityHandler(
                h.はらぺこスイッチ_on_turn_end,
                subject_spec="source:self",
            ),
        }
    ),
    "バリアフリー": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.バリアフリー_on_switch_in,
                subject_spec="source:self",
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
    "パワースポット": AbilityData(),
    "パンクロック": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
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
    "ばんけん": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_BEFORE_MODIFY_STAT: h.AbilityHandler(
                h.ばんけん_on_intimidate,
                subject_spec="target:self",
            ),
            Event.ON_TRY_BLOW: h.AbilityHandler(
                h.きゅうばん_block_blow,
                subject_spec="defender:self",
            ),
        }
    ),
    "はんすう": AbilityData(),
    "ビーストブースト": AbilityData(
        handlers={
            Event.ON_MOVE_KO: h.AbilityHandler(
                h.ビーストブースト_on_ko,
                subject_spec="attacker:self",
            )
        }
    ),
    "ヒーリングシフト": AbilityData(
        handlers={
            DomainEvent.ON_MODIFY_MOVE_PRIORITY: h.AbilityHandler(
                h.ヒーリングシフト_modify_priority,
                subject_spec="attacker:self",
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
    "ビビッドボディ": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
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
                h.びびり_on_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "ひらいしん": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.AbilityHandler(
                h.ひらいしん_absorb_electric,
                subject_spec="defender:self",
            )
        },
    ),
    "びんじょう": AbilityData(
        handlers={
            Event.ON_MODIFY_STAT: h.AbilityHandler(
                h.びんじょう_copy_stat_rise,
                subject_spec="target:foe",
            ),
        }
    ),
    "ファーコート": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_CALC_DEF_MODIFIER: h.AbilityHandler(
                h.ファーコート_boost_B,
                subject_spec="defender:self",
            )
        }
    ),
    "ファントムガード": AbilityData(
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.AbilityHandler(
                h.マルチスケイル_reduce_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "フィルター": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.AbilityHandler(
                h.ハードロック_reduce_effective,
                subject_spec="defender:self",
            )
        }
    ),
    "ふうりょくでんき": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.ふうりょくでんき_on_damage,
                subject_spec="defender:self",
                priority=20,
            ),
            Event.ON_FIELD_ACTIVATE: h.AbilityHandler(
                h.ふうりょくでんき_on_field_activate,
                subject_spec="source:self",
            ),
        }
    ),
    "フェアリーオーラ": AbilityData(
        flags=[
            "mold_breaker_ignorable",
        ],
        handlers={
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
                h.ふくつのこころ_on_flinch,
                subject_spec="source:self",
            )
        }
    ),
    "ふくつのたて": AbilityData(
        flags=[
            "per_battle_once"
        ],
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
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_CALC_DEF_MODIFIER: h.AbilityHandler(
                h.ふしぎなうろこ_boost_B,
                subject_spec="defender:self",
            )
        }
    ),
    "ふしぎなまもり": AbilityData(
        flags=["mold_breaker_ignorable"],
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
        flags=[
            "per_battle_once"
        ],
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
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.prevent_sleep_ailment,
                "target:self",
            ),
            Event.ON_BEFORE_APPLY_VOLATILE: h.AbilityHandler(
                h.ふみん_prevent_volatile,
                "target:self",
            ),
        }
    ),
    "ふゆう": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_CHECK_FLOATING: h.AbilityHandler(
                h.ふゆう_float,
                subject_spec="source:self",
            )
        }
    ),
    "プラス": AbilityData(),
    "フラワーギフト": AbilityData(
        flags=[
            "uncopyable",
            "mold_breaker_ignorable",
        ],
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.フラワーギフト_modify_atk,
                subject_spec="attacker:self",
            ),
            Event.ON_CALC_DEF_MODIFIER: h.AbilityHandler(
                h.フラワーギフト_modify_atk,
                subject_spec="defender:self",
            ),
        }
    ),
    "フラワーベール": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.フラワーベール_prevent_ailment,
                subject_spec="target:self",
            ),
            Event.ON_BEFORE_MODIFY_STAT: h.AbilityHandler(
                h.フラワーベール_prevent_stat_drop,
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
    "プリズムアーマー": AbilityData(
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.AbilityHandler(
                h.ハードロック_reduce_effective,
                subject_spec="defender:self",
            )
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
    "プレッシャー": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.プレッシャー_on_switch_in,
                subject_spec="source:self",
            ),
            Event.ON_MODIFY_PP_CONSUMED: h.AbilityHandler(
                h.プレッシャー_extra_pp,
                subject_spec="defender:self",
            ),
        }
    ),
    "フレンドガード": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "ヘヴィメタル": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "ヘドロえき": AbilityData(
        handlers={
            Event.ON_MODIFY_HEAL: h.AbilityHandler(
                h.ヘドロえき_reverse_drain,
                subject_spec="target:foe",
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
                h.へんしょく_on_damage,
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
        }
    ),
    "ぼうおん": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.AbilityHandler(
                h.ぼうおん_block_sound,
                subject_spec="defender:self",
            ),
        }
    ),
    "ほうし": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.ほうし_on_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "ぼうじん": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
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
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.AbilityHandler(
                h.ぼうだん_block_bullet,
                subject_spec="defender:self",
            ),
        }
    ),
    "ほおぶくろ": AbilityData(),
    "ほのおのからだ": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.ほのおのからだ_on_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "ほろびのボディ": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.ほろびのボディ_on_damage,
                subject_spec="defender:self",
                priority=20,
            )
        }
    ),
    "マイティチェンジ": AbilityData(
        flags=[
            "uncopyable",
            "protected",
            "gas_proof",
        ],
        handlers={
            Event.ON_SWITCH_OUT: h.AbilityHandler(
                h.マイティチェンジ_change_form,
                subject_spec="source:self",
            ),
        },
    ),
    "マイナス": AbilityData(),
    "マイペース": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_BEFORE_APPLY_VOLATILE: h.AbilityHandler(
                h.マイペース_prevent_volatile,
                "target:self",
            )
        }
    ),
    "マグマのよろい": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.prevent_freeze_ailment,
                "target:self",
            )
        }
    ),
    "まけんき": AbilityData(
        handlers={
            Event.ON_MODIFY_STAT: h.AbilityHandler(
                h.まけんき_on_stat_down,
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
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_CHECK_REFLECT: h.AbilityHandler(
                h.マジックミラー_reflect,
                subject_spec="defender:self",
                priority=200,
            )
        }
    ),
    "マルチスケイル": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.AbilityHandler(
                h.マルチスケイル_reduce_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "マルチタイプ": AbilityData(
        flags=[
            "uncopyable",
            "protected",
            "gas_proof",
        ],
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.マルチタイプ_apply_type,
                subject_spec="source:self",
            ),
            Event.ON_CHECK_ITEM_CHANGE: h.AbilityHandler(
                h.マルチタイプ_block_item_change,
                subject_spec="defender:self",
            ),
        }
    ),
    "ミイラ": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.ミイラ_on_damage,
                subject_spec="defender:self",
            ),
        }
    ),
    "みずがため": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.みずがため_on_damage,
                subject_spec="defender:self",
                priority=20,
            )
        }
    ),
    "ミストメイカー": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.ミストメイカー_activate_terrain,
                "source:self",
            )
        }
    ),
    "みずのベール": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.prevent_burn_ailment,
                "target:self",
            )
        }
    ),
    "みつあつめ": AbilityData(),
    "ミラーアーマー": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_BEFORE_MODIFY_STAT: h.AbilityHandler(
                h.ミラーアーマー_reflect_stat_drop,
                subject_spec="target:self",
            )
        }
    ),
    "ミラクルスキン": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_MODIFY_ACCURACY: h.AbilityHandler(
                h.ミラクルスキン_reduce_accuracy,
                subject_spec="defender:self",
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
                h.メロメロボディ_on_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "めんえき": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.prevent_poison_ailment,
                "target:self",
            )
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
                h.ものひろい_on_turn_end,
                subject_spec="source:self",
                priority=30,
            ),
        }
    ),
    "もふもふ": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.AbilityHandler(
                h.もふもふ_modify_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "もらいび": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.もらいび_on_switch_in,
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
                h.もらいび_on_move_end,
                subject_spec="attacker:self",
            ),
            Event.ON_CALC_POWER_MODIFIER: h.AbilityHandler(
                h.もらいび_modify_power,
                subject_spec="attacker:self",
            ),
        },
    ),
    "やるき": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.prevent_sleep_ailment,
                "target:self",
            ),
            Event.ON_BEFORE_APPLY_VOLATILE: h.AbilityHandler(
                h.やるき_prevent_volatile,
                "target:self",
            )
        }
    ),
    "ゆうばく": AbilityData(
        handlers={
            Event.ON_MOVE_KO: h.AbilityHandler(
                h.ゆうばく_on_ko,
                subject_spec="defender:self",
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
        flags=[
            "mold_breaker_ignorable"
        ],
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
                h.よちむ_on_switch_in,
                subject_spec="source:self",
            ),
        }
    ),
    "よびみず": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
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
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "リーフガード": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.リーフガード_prevent_ailment,
                subject_spec="target:self",
            ),
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
        flags=[
            "uncopyable",
            "protected",
            "gas_proof",
        ],
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.リミットシールド_on_switch_in,
                subject_spec="source:self",
                priority=120,
            ),
            Event.ON_TURN_END: h.AbilityHandler(
                h.リミットシールド_on_turn_end,
                subject_spec="source:self",
                priority=160,
            ),
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.リミットシールド_prevent_ailment,
                subject_spec="target:self",
            ),
            Event.ON_SWITCH_OUT: h.AbilityHandler(
                h.リミットシールド_on_switch_out,
                subject_spec="source:self",
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
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_MODIFY_SECONDARY_CHANCE: h.AbilityHandler(
                h.りんぷん_block_secondary_chance,
                subject_spec="defender:self",
            ),
        }
    ),
    "レシーバー": AbilityData(
        flags=[
            "uncopyable"
        ]
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
                h.わたげ_on_damage,
                subject_spec="defender:self",
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
