"""特性データ定義モジュール。

Note:
    このモジュール内の特性定義はABILITIES辞書内で五十音順に配置されています。
"""

from jpoke.enums import DomainEvent, Event
from jpoke.handlers import common, ability as h, ability_paradox as paradox
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
            ),
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.アイスフェイス_restore_on_switch_in,
                subject_spec="source:self",
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
    "あくしゅう": AbilityData(),
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
                subject_spec="attacker:self",
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
                "source:self",
            ),
            Event.ON_ABILITY_ENABLED: h.AbilityHandler(
                h.あめふらし_activate_weather,
                "source:self",
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
                "target:self",
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
    "いかりのこうら": AbilityData(),
    "いかりのつぼ": AbilityData(),
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
                subject_spec="source:self",
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
    "うるおいボイス": AbilityData(),
    "うるおいボディ": AbilityData(),
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
    "えんかく": AbilityData(),
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
        ]
    ),
    "おどりこ": AbilityData(),
    "おみとおし": AbilityData(),
    "おもかげやどし": AbilityData(
        flags=[
            "uncopyable",
            "protected"
        ]
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
    "カーリーヘアー": AbilityData(),
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
        ]
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
            Event.ON_ACTIVATE_MOLD_BREAKER: h.AbilityHandler(
                h.かたやぶり_disable_foe_ability,
                subject_spec="attacker:self",
            ),
            Event.ON_DEACTIVATE_MOLD_BREAKER: h.AbilityHandler(
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
                subject_spec="target:self",
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
    "かんつうドリル": AbilityData(),
    "かんろなミツ": AbilityData(
        flags=[
            "per_battle_once"
        ]
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
    "きけんよち": AbilityData(),
    "ぎたい": AbilityData(),
    "きみょうなくすり": AbilityData(),
    "きもったま": AbilityData(),
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
    "ぎょぐん": AbilityData(),
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
    "きんしのちから": AbilityData(),
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
    "クイックドロウ": AbilityData(),
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
    "くだけるよろい": AbilityData(),
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
    "こぼれダネ": AbilityData(),
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
    "サーフテール": AbilityData(),
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
    "さまようたましい": AbilityData(),
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
    "じきゅうりょく": AbilityData(),
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
    "じょうききかん": AbilityData(),
    "しょうりのほし": AbilityData(),
    "じょおうのいげん": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
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
        ]
    ),
    "シンクロ": AbilityData(),
    "じんばいったい": AbilityData(
        flags=[
            "uncopyable",
            "protected"
        ]
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
                    h.すいほう_modify_boost_water,
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
                subject_spec="source:self",
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
    "すてみ": AbilityData(),
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
    "すなはき": AbilityData(),
    "すりぬけ": AbilityData(
        handlers={
            Event.ON_CHECK_HIT_SUBSTITUTE: h.AbilityHandler(
                h.すりぬけ_bypass_substitute,
                subject_spec="attacker:self",
            ),
            Event.ON_CHECK_BYPASS_SCREEN: h.AbilityHandler(
                h.すりぬけ_bypass_screen,
                subject_spec="attacker:self",
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
        ]
    ),
    "せいぎのこころ": AbilityData(),
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
    ),
    "ゼロフォーミング": AbilityData(
        flags=[
            "uncopyable"
        ]
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
    "そうだいしょう": AbilityData(),
    "ソウルハート": AbilityData(),
    "ダークオーラ": AbilityData(
        flags=[
            "mold_breaker_ignorable",
        ]
    ),
    "ターボブレイズ": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.announce_ability_triggered,
                subject_spec="source:self",
            ),
            Event.ON_ACTIVATE_MOLD_BREAKER: h.AbilityHandler(
                h.かたやぶり_disable_foe_ability,
                subject_spec="attacker:self",
            ),
            Event.ON_DEACTIVATE_MOLD_BREAKER: h.AbilityHandler(
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
    "ダルマモード": AbilityData(),
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
        ]
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
        ]
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
        ]
    ),
    "テラボルテージ": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.announce_ability_triggered,
                subject_spec="source:self",
            ),
            Event.ON_ACTIVATE_MOLD_BREAKER: h.AbilityHandler(
                h.かたやぶり_disable_foe_ability,
                subject_spec="attacker:self",
            ),
            Event.ON_DEACTIVATE_MOLD_BREAKER: h.AbilityHandler(
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
    "でんきにかえる": AbilityData(),
    "てんきや": AbilityData(
        flags=[
            "uncopyable"
        ]
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
    "とうそうしん": AbilityData(),
    "どくくぐつ": AbilityData(
        flags=[
            "uncopyable"
        ]
    ),
    "どくげしょう": AbilityData(),
    "どくしゅ": AbilityData(
        handlers={
            Event.ON_DAMAGE_HIT: h.AbilityHandler(
                h.どくしゅ_on_damage,
                subject_spec="attacker:self",
            )
        }
    ),
    "どくのくさり": AbilityData(),
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
    "とびだすなかみ": AbilityData(),
    "とびだすハバネロ": AbilityData(),
    "ドラゴンスキン": AbilityData(),
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
    "とれないにおい": AbilityData(),
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
    "ナイトメア": AbilityData(),
    "なまけ": AbilityData(),
    "にげあし": AbilityData(),
    "にげごし": AbilityData(
        handlers={
            Event.ON_HP_CHANGED: h.AbilityHandler(
                h.ききかいひ_on_hp_change,
                subject_spec="target:self",
            )
        }
    ),
    "ぬめぬめ": AbilityData(),
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
                subject_spec="source:self",
            ),
            Event.ON_CALC_POWER_MODIFIER: h.AbilityHandler(
                h.ノーマルスキン_boost_power,
                subject_spec="attacker:self",
            ),
        }
    ),
    "のろわれボディ": AbilityData(),
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
        ]
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
    "はやおき": AbilityData(),
    "はやてのつばさ": AbilityData(),
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
    "バリアフリー": AbilityData(),
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
        ]
    ),
    "はんすう": AbilityData(),
    "ビーストブースト": AbilityData(),
    "ヒーリングシフト": AbilityData(),
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
        ]
    ),
    "びびり": AbilityData(),
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
    "びんじょう": AbilityData(),
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
    "ふうりょくでんき": AbilityData(),
    "フェアリーオーラ": AbilityData(
        flags=[
            "mold_breaker_ignorable",
        ]
    ),
    "フェアリースキン": AbilityData(
        handlers={
            Event.ON_MODIFY_MOVE_TYPE: h.AbilityHandler(
                h.フェアリースキン_modify_move_type,
                subject_spec="source:self",
            ),
            Event.ON_CALC_POWER_MODIFIER: h.AbilityHandler(
                h.フェアリースキン_modify_power,
                subject_spec="attacker:self",
            ),
        }
    ),
    "ふかしのこぶし": AbilityData(),
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
    "ふくつのこころ": AbilityData(),
    "ふくつのたて": AbilityData(
        flags=[
            "per_battle_once"
        ]
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
    "ふしぎなまもり": AbilityData(),
    "ふしょく": AbilityData(),
    "ふとうのけん": AbilityData(
        flags=[
            "per_battle_once"
        ]
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
        ]
    ),
    "フラワーベール": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "フリーズスキン": AbilityData(
        handlers={
            Event.ON_MODIFY_MOVE_TYPE: h.AbilityHandler(
                h.フリーズスキン_modify_move_type,
                subject_spec="source:self",
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
    "プレッシャー": AbilityData(),
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
    "ヘドロえき": AbilityData(),
    "へんげんじざい": AbilityData(
        handlers={
            Event.ON_MOVE_CHARGE: h.AbilityHandler(
                h.へんげんじざい_change_type,
                subject_spec="source:self",
                priority=100,
            )
        }
    ),
    "へんしょく": AbilityData(),
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
    "ほうし": AbilityData(),
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
    "ほろびのボディ": AbilityData(),
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
    "まけんき": AbilityData(),
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
                subject_spec="target:self",
            ),
        }
    ),
    "ミイラ": AbilityData(),
    "みずがため": AbilityData(),
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
        ]
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
    "メガソーラー": AbilityData(),
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
    "メロメロボディ": AbilityData(),
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
    "ものひろい": AbilityData(),
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
                h.もらいび_arm_fire_boost,
                subject_spec="source:self",
            ),
            Event.ON_MOVE_END: h.AbilityHandler(
                h.もらいび_on_move_end,
                subject_spec="source:self",
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
    "ゆうばく": AbilityData(),
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
    "よちむ": AbilityData(),
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
                subject_spec="source:self",
                priority=100,
            )
        }
    ),
    "リミットシールド": AbilityData(
        flags=[
            "uncopyable",
            "protected",
            "gas_proof",
        ]
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
    "わたげ": AbilityData(),
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
