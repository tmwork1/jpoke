"""特性データ定義モジュール。

Note:
    このモジュール内の特性定義はABILITIES辞書内で五十音順に配置されています。
"""

from functools import partial

from jpoke.enums import DomainEvent, Event
from jpoke.core import HandlerReturn
from jpoke.handlers import common, ability as h, ability_paradox as hp
from .models import AbilityData


def common_setup():
    """共通のセットアップ処理"""
    for name in ABILITIES:
        ABILITIES[name].name = name

    # undeniable フラグ持ちは共通で特性有効化保護ハンドラを持つ。
    for data in ABILITIES.values():
        if "undeniable" in data.flags and \
                Event.ON_CHECK_ABILITY_ENABLED not in data.handlers:
            data.handlers[Event.ON_CHECK_ABILITY_ENABLED] = h.AbilityHandler(
                h.undeniable_check_enabled,
                subject_spec="source:self",
                priority=20,
            )


ABILITIES: dict[str, AbilityData] = {
    "": AbilityData(name=""),
    "ARシステム": AbilityData(
        flags=[
            "uncopyable",
            "protected"
        ],
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.ARシステム_on_switch_in,
                subject_spec="source:self",
            ),
            Event.ON_CHECK_ITEM_CHANGE: h.AbilityHandler(
                h.ARシステム_prevent_item_change,
                subject_spec="target:self",
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
                h.あついしぼう_modify_atk,
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
    "あまのじゃく": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_BEFORE_MODIFY_STAT: h.AbilityHandler(
                h.あまのじゃく_modify_stat,
                subject_spec="target:self",
            )
        }
    ),
    "あめうけざら": AbilityData(
        handlers={
            Event.ON_TURN_END_3: h.AbilityHandler(
                h.あめうけざら_on_turn_end,
                subject_spec="source:self",
            ),
        }
    ),
    "あめふらし": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                partial(common.activate_weather, weather="あめ", source_spec="source:self"),
                subject_spec="source:self",
            )
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
    "いかく": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                partial(common.modify_stat, stat="A", v=-1, target_spec="source:foe", source_spec="source:self"),
                subject_spec="source:self",
            )
        },
    ),
    "いかりのこうら": AbilityData(),
    "いかりのつぼ": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "いしあたま": AbilityData(
        handlers={
            Event.ON_BEFORE_DAMAGE_APPLY: h.AbilityHandler(
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
            Event.ON_CHECK_IMMUNE: h.AbilityHandler(
                h.いたずらごころ_block_dark_target,
                subject_spec="attacker:self",
            ),
        }
    ),
    "いやしのこころ": AbilityData(),
    "いろめがね": AbilityData(
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.AbilityHandler(
                h.いろめがね_modify_damage,
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
            "undeniable"
        ]
    ),
    "うるおいボイス": AbilityData(),
    "うるおいボディ": AbilityData(),
    "えんかく": AbilityData(),
    "おうごんのからだ": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_CHECK_IMMUNE: h.AbilityHandler(
                h.おうごんのからだ_block_status_move,
                subject_spec="target:self",
            )
        }
    ),
    "おどりこ": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "おみとおし": AbilityData(),
    "おもてなし": AbilityData(),
    "おやこあい": AbilityData(
        handlers={
            Event.ON_MODIFY_HIT_COUNT: h.AbilityHandler(
                h.おやこあい_modify_hit_count,
                subject_spec="attacker:self",
            ),
            Event.ON_MODIFY_DAMAGE: h.AbilityHandler(
                h.おやこあい_modify_damage,
                subject_spec="attacker:self",
            )
        }
    ),
    "おわりのだいち": AbilityData(
        flags=[
            "undeniable"
        ],
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                partial(common.activate_weather, weather="おおひでり", source_spec="source:self"),
                subject_spec="source:self",
            ),
            Event.ON_SWITCH_OUT: h.AbilityHandler(
                partial(common.deactivate_weather, weather="おおひでり"),
                subject_spec="source:self",
            ),
        },
    ),
    "かいりきバサミ": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_MODIFY_STAT: h.AbilityHandler(
                h.かいりきバサミ_modify_stat,
                subject_spec="target:self",
            )
        }
    ),
    "かがくへんかガス": AbilityData(
        flags=[
            "uncopyable"
        ],
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.かがくへんかガス_switch_in,
                subject_spec="source:self",
                priority=0,
            ),
            Event.ON_CHECK_ABILITY_ENABLED: h.AbilityHandler(
                h.かがくへんかガス_check_enabled,
                subject_spec="source:foe",
                priority=10,
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
            Event.ON_TURN_END_5: h.AbilityHandler(
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
                h.announce_ability_on_switch_in,
                subject_spec="source:self",
            ),
            Event.ON_CHECK_DEF_ABILITY_ENABLED: h.AbilityHandler(
                h.かたやぶり_check_def_ability_enabled,
                subject_spec="attacker:self",
                priority=100,
            ),
        }
    ),
    "かちき": AbilityData(
        flags=["undeniable"],
        handlers={
            Event.ON_MODIFY_STAT: h.AbilityHandler(
                h.かちき_on_stat_down,
                subject_spec="target:self",
            )
        }
    ),
    "かるわざ": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.かるわざ_on_switch_in,
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
    "かんそうはだ": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_CHECK_IMMUNE: h.AbilityHandler(
                h.かんそうはだ_check_water_immune,
                subject_spec="target:self",
            ),
            Event.ON_CALC_DAMAGE_MODIFIER: h.AbilityHandler(
                h.かんそうはだ_modify_fire_damage,
                subject_spec="defender:self",
            ),
            Event.ON_TURN_END_3: h.AbilityHandler(
                h.かんそうはだ_on_turn_end,
                subject_spec="source:self",
            ),
        }
    ),
    "かんろなミツ": AbilityData(
        flags=[
            "per_battle_once"
        ]
    ),
    "がんじょう": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
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
        flags=[
            "undeniable"
        ],
        handlers={
            Event.ON_HP_CHANGED: h.AbilityHandler(
                h.ききかいひ_on_hp_change,
                subject_spec="target:self",
            )
        }
    ),
    "きけんよち": AbilityData(),
    "きみょうなくすり": AbilityData(),
    "きもったま": AbilityData(),
    "きゅうばん": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_HIT: h.AbilityHandler(
                h.きゅうばん_check_blow,
                subject_spec="defender:self",
                priority=200,
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
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.きよめのしお_modify_atk,
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
                lambda *args: HandlerReturn(),
                subject_spec="source:self",
            ),
            Event.ON_CHECK_NERVOUS: h.AbilityHandler(
                lambda *args: HandlerReturn(value=True),
                subject_spec="source:foe",
            ),
        }
    ),
    "ぎたい": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "ぎゃくじょう": AbilityData(
        handlers={
            Event.ON_DAMAGE: h.AbilityHandler(
                h.ぎゃくじょう_on_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "くいしんぼう": AbilityData(),
    "くさのけがわ": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_CALC_DEF_MODIFIER: h.AbilityHandler(
                h.くさのけがわ_modify_def,
                subject_spec="defender:self",
            )
        }
    ),
    "くだけるよろい": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "くろのいななき": AbilityData(),
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
                h.こおりのりんぷん_modify_damage,
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
                hp.パラドックスチャージ_refresh,
                subject_spec="source:self",
                priority=200,
            ),
            Event.ON_FIELD_CHANGE: h.AbilityHandler(
                hp.パラドックスチャージ_refresh,
                subject_spec="source:self",
                priority=200,
            ),
            Event.ON_REFRESH_PARADOX_BOOST: h.AbilityHandler(
                hp.パラドックスチャージ_refresh,
                subject_spec="source:self",
                priority=200,
            ),
            DomainEvent.ON_CALC_SPEED: h.AbilityHandler(
                hp.パラドックスチャージ_on_calc_speed,
                subject_spec="source:self",
            ),
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                hp.パラドックスチャージ_on_calc_atk_modifier,
                subject_spec="attacker:self",
            ),
            Event.ON_CALC_DEF_MODIFIER: h.AbilityHandler(
                hp.パラドックスチャージ_on_calc_def_modifier,
                subject_spec="defender:self",
            ),
        }
    ),
    "こぼれダネ": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "こんがりボディ": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "がんじょう": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_CHECK_IMMUNE: h.AbilityHandler(
                h.がんじょう_block_ohko,
                subject_spec="target:self",
            ),
            Event.ON_BEFORE_DAMAGE_APPLY: h.AbilityHandler(
                h.がんじょう_survive_lethal,
                subject_spec="target:self",
            ),
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
        flags=[
            "undeniable"
        ]
    ),
    "さめはだ": AbilityData(
        flags=[
            "undeniable"
        ],
        handlers={
            Event.ON_DAMAGE: h.AbilityHandler(
                h.さめはだ_on_damage,
                subject_spec="defender:self",
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
            Event.ON_CHECK_MOVE: [
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
            Event.ON_TURN_END_5: h.AbilityHandler(
                h.しゅうかく_on_turn_end,
                subject_spec="source:self",
            ),
        }
    ),
    "しょうりのほし": AbilityData(
        flags=[
            "undeniable"
        ]
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
            Event.ON_MODIFY_STAT: h.AbilityHandler(
                h.クリアボディ_modify_stat,
                subject_spec="target:self",
            )
        }
    ),
    "しろのいななき": AbilityData(),
    "しんがん": AbilityData(
        flags=[
            "mold_breaker_ignorable"
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
    "じきゅうりょく": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "じしんかじょう": AbilityData(
        handlers={
            Event.ON_DAMAGE: h.AbilityHandler(
                h.じしんかじょう_on_damage,
                subject_spec="attacker:self",
            )
        }
    ),
    "じゅうなん": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.じゅうなん_prevent_paralysis,
                subject_spec="target:self",
            )
        }
    ),
    "じゅくせい": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "じょうききかん": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
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
    "じんばいったい": AbilityData(
        flags=[
            "uncopyable",
            "protected"
        ]
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
                    h.すいほう_modify_atk,
                    subject_spec="attacker:self",
                ),
                h.AbilityHandler(
                    h.すいほう_modify_atk,
                    subject_spec="defender:self",
                ),
            ]
        }
    ),
    "すじがねいり": AbilityData(),
    "すてみ": AbilityData(),
    "すなおこし": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                partial(common.activate_weather, weather="すなあらし", source_spec="source:self"),
                subject_spec="source:self",
            )
        }
    ),
    "すなかき": AbilityData(
        handlers={
            DomainEvent.ON_CALC_SPEED: h.AbilityHandler(
                h.すなかき_modify_speed,
                subject_spec="source:self",
            ),
            Event.ON_BEFORE_DAMAGE_APPLY: h.AbilityHandler(
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
            Event.ON_BEFORE_DAMAGE_APPLY: h.AbilityHandler(
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
            Event.ON_BEFORE_DAMAGE_APPLY: h.AbilityHandler(
                h.すなのちから_ignore_sandstorm_damage,
                subject_spec="target:self",
            ),
        }
    ),
    "すなはき": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "すりぬけ": AbilityData(),
    "するどいめ": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_MODIFY_STAT: h.AbilityHandler(
                h.するどいめ_modify_stat,
                subject_spec="target:self",
            )
        }
    ),
    "せいぎのこころ": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "せいしんりょく": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_BEFORE_APPLY_VOLATILE: h.AbilityHandler(
                h.せいしんりょく_prevent_flinch,
                subject_spec="target:self",
            ),
            Event.ON_BEFORE_MODIFY_STAT: h.AbilityHandler(
                h.せいしんりょく_block_intimidate,
                subject_spec="target:self",
            ),
        }
    ),
    "せいでんき": AbilityData(
        handlers={
            Event.ON_DAMAGE: h.AbilityHandler(
                h.せいでんき_on_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "ぜったいねむり": AbilityData(
        flags=[
            "uncopyable",
            "protected",
            "undeniable"
        ],
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                partial(common.apply_ailment, ailment="ねむり", target_spec="source:self", source_spec="source:self"),
                subject_spec="source:self",
            )
        }
    ),
    "そうしょく": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_CHECK_IMMUNE: h.AbilityHandler(
                h.そうしょく_check_immune,
                subject_spec="defender:self",
            )
        }
    ),
    "そうだいしょう": AbilityData(),
    "たいねつ": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.たいねつ_modify_atk,
                subject_spec="defender:self",
            )
        }
    ),
    "たまひろい": AbilityData(),
    "たんじゅん": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_BEFORE_MODIFY_STAT: h.AbilityHandler(
                h.たんじゅん_modify_stat,
                subject_spec="target:self",
            )
        }
    ),
    "だっぴ": AbilityData(
        handlers={
            Event.ON_TURN_END_2: h.AbilityHandler(
                h.だっぴ_on_turn_end,
                subject_spec="source:self",
                priority=90,
            ),
        }
    ),
    "ちからずく": AbilityData(
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.AbilityHandler(
                h.ちからずく_modify_power,
                subject_spec="attacker:self",
            ),
            Event.ON_MODIFY_SECONDARY_CHANCE: h.AbilityHandler(
                h.ちからずく_on_modify_secondary_chance,
                subject_spec="attacker:self",
            ),
        }
    ),
    "ちからもち": AbilityData(
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.ちからもちヨガパワー_on_calc_atk_modifier,
                subject_spec="attacker:self",
            )
        }
    ),
    "ちくでん": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_CHECK_IMMUNE: h.AbilityHandler(
                h.ちくでん_check_immune,
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
            Event.ON_CHECK_IMMUNE: h.AbilityHandler(
                h.ちょすい_check_immune,
                subject_spec="defender:self",
            )
        },
    ),
    "てきおうりょく": AbilityData(
        handlers={
            Event.ON_CALC_ATK_TYPE_MODIFIER: h.AbilityHandler(
                h.てきおうりょく_modify_stab,
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
        flags=[
            "undeniable"
        ],
        handlers={
            Event.ON_DAMAGE: h.AbilityHandler(
                h.てつのトゲ_on_damage,
                subject_spec="defender:self",
            )
        }
    ),
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
                h.てんねん_on_calc_atk_rank_modifier,
                subject_spec="defender:self",
            ),
            Event.ON_CALC_DEF_RANK_MODIFIER: h.AbilityHandler(
                h.てんねん_on_calc_def_rank_modifier,
                subject_spec="attacker:self",
            ),
        }
    ),
    "てんのめぐみ": AbilityData(
        handlers={
            Event.ON_MODIFY_SECONDARY_CHANCE: h.AbilityHandler(
                h.てんのめぐみ_on_modify_secondary_chance,
                subject_spec="attacker:self",
            ),
        }
    ),
    "でんきにかえる": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "でんきエンジン": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_CHECK_IMMUNE: h.AbilityHandler(
                h.でんきエンジン_check_immune,
                subject_spec="defender:self",
            )
        }
    ),
    "とうそうしん": AbilityData(),
    "とれないにおい": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "どくくぐつ": AbilityData(
        flags=[
            "uncopyable"
        ]
    ),
    "どくげしょう": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "どくしゅ": AbilityData(
        handlers={
            Event.ON_DAMAGE: h.AbilityHandler(
                h.どくしゅ_on_damage,
                subject_spec="attacker:self",
            )
        }
    ),
    "どくのくさり": AbilityData(),
    "どくのトゲ": AbilityData(
        flags=[
            "undeniable"
        ],
        handlers={
            Event.ON_DAMAGE: h.AbilityHandler(
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
            Event.ON_CHECK_IMMUNE: h.AbilityHandler(
                h.どしょく_check_immune,
                subject_spec="defender:self",
            )
        },
    ),
    "どんかん": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.どんかん_prevent_volatile,
                subject_spec="target:self",
            )
        }
    ),
    "なまけ": AbilityData(),
    "にげあし": AbilityData(),
    "にげごし": AbilityData(
        flags=[
            "undeniable"
        ],
        handlers={
            Event.ON_HP_CHANGED: h.AbilityHandler(
                h.ききかいひ_on_hp_change,
                subject_spec="target:self",
            )
        }
    ),
    "ぬめぬめ": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "ねつこうかん": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.ねつこうかん_prevent_burn,
                subject_spec="target:self",
            ),
            Event.ON_DAMAGE: h.AbilityHandler(
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
    "のろわれボディ": AbilityData(
        flags=[
            "undeniable"
        ]
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
        flags=[
            "undeniable"
        ],
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.AbilityHandler(
                h.はがねのせいしん_modify_power,
                subject_spec="attacker:self",
            )
        }
    ),
    "はじまりのうみ": AbilityData(
        flags=[
            "undeniable"
        ],
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                partial(common.activate_weather, weather="おおあめ", source_spec="source:self"),
                subject_spec="source:self",
            ),
            Event.ON_SWITCH_OUT: h.AbilityHandler(
                partial(common.deactivate_weather, weather="おおあめ"),
                subject_spec="source:self",
            ),
        },
    ),
    "はっこう": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "はとむね": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_MODIFY_STAT: h.AbilityHandler(
                h.はとむね_modify_stat,
                subject_spec="target:self",
            )
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
            Event.ON_TURN_END_5: h.AbilityHandler(
                h.はらぺこスイッチ_on_turn_end,
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
    "はんすう": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "ばけのかわ": AbilityData(
        flags=[
            "uncopyable",
            "protected",
            "per_battle_once",
            "mold_breaker_ignorable",
            "undeniable",
        ],
        handlers={
            Event.ON_MODIFY_DAMAGE: h.AbilityHandler(
                h.ばけのかわ_modify_damage,
                subject_spec="defender:self",
                priority=10,
            )
        }
    ),
    "ばんけん": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "ひでり": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                partial(common.activate_weather, weather="はれ", source_spec="source:self"),
                subject_spec="source:self",
            )
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
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.ひひいろのこどう_modify_atk,
                subject_spec="attacker:self",
            )
        }
    ),
    "ひらいしん": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_CHECK_IMMUNE: h.AbilityHandler(
                h.ひらいしん_check_immune,
                subject_spec="defender:self",
            )
        },
    ),
    "びびり": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "びんじょう": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "ふうりょくでんき": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "ふかしのこぶし": AbilityData(),
    "ふくがん": AbilityData(
        handlers={
            Event.ON_MODIFY_ACCURACY: h.AbilityHandler(
                h.ふくがん_modify_accuracy,
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
                h.ふしぎなうろこ_modify_def,
                subject_spec="defender:self",
            )
        }
    ),
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
                h.ふみん_prevent_sleep,
                subject_spec="target:self",
            )
        }
    ),
    "ふゆう": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_CHECK_FLOATING: h.AbilityHandler(
                lambda *args: HandlerReturn(value=True),
                subject_spec="source:self",
            )
        }
    ),
    "ぶきよう": AbilityData(
        handlers={
            Event.ON_CHECK_ITEM_ENABLED: h.AbilityHandler(
                h.ぶきよう_check_item_enabled,
                subject_spec="source:self",
            )
        }
    ),
    "へんげんじざい": AbilityData(
        handlers={
            Event.ON_MOVE_CHARGE: h.AbilityHandler(
                h.へんげんじざいリベロ_on_move_charge,
                subject_spec="source:self",
                priority=100,
            )
        }
    ),
    "へんしょく": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "ほうし": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "ほおぶくろ": AbilityData(),
    "ほのおのからだ": AbilityData(
        flags=[
            "undeniable"
        ],
        handlers={
            Event.ON_DAMAGE: h.AbilityHandler(
                h.ほのおのからだ_on_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "ほろびのボディ": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "ぼうおん": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_CHECK_IMMUNE: h.AbilityHandler(
                h.ぼうおん_check_immune,
                subject_spec="defender:self",
            ),
        }
    ),
    "ぼうじん": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_CHECK_IMMUNE: h.AbilityHandler(
                h.ぼうじん_check_immune,
                subject_spec="defender:self",
            ),
            Event.ON_BEFORE_DAMAGE_APPLY: h.AbilityHandler(
                h.ぼうじん_ignore_sandstorm_damage,
                subject_spec="target:self",
            ),
        }
    ),
    "ぼうだん": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_CHECK_IMMUNE: h.AbilityHandler(
                h.ぼうだん_check_immune,
                subject_spec="defender:self",
            ),
        }
    ),
    "まけんき": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "みずがため": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "みずのベール": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.みずのベール_prevent_burn,
                subject_spec="target:self",
            )
        }
    ),
    "みつあつめ": AbilityData(),
    "むしのしらせ": AbilityData(
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.しんりょくもうかげきりゅうむしのしらせ_modify_atk,
                subject_spec="attacker:self",
            )
        }
    ),
    "めんえき": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.めんえき_prevent_poison,
                subject_spec="target:self",
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
            Event.ON_CHECK_IMMUNE: h.AbilityHandler(
                h.もらいび_check_immune,
                subject_spec="defender:self",
            ),
            Event.ON_MOVE_CHARGE: h.AbilityHandler(
                h.もらいび_on_move_charge,
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
                h.やるき_prevent_sleep,
                subject_spec="target:self",
            )
        }
    ),
    "ゆうばく": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "ゆきかき": AbilityData(
        handlers={
            DomainEvent.ON_CALC_SPEED: h.AbilityHandler(
                h.ゆきかき_modify_speed,
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
                h.ゆきがくれ_modify_accuracy,
                subject_spec="defender:self",
            ),
        }
    ),
    "ゆきふらし": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                partial(common.activate_weather, weather="ゆき", source_spec="source:self"),
                subject_spec="source:self",
            )
        }
    ),
    "ようりょくそ": AbilityData(
        handlers={
            DomainEvent.ON_CALC_SPEED: h.AbilityHandler(
                h.ようりょくそ_modify_speed,
                subject_spec="source:self",
            )
        }
    ),
    "よちむ": AbilityData(),
    "よびみず": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_CHECK_IMMUNE: h.AbilityHandler(
                h.よびみず_check_immune,
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
                h.りんぷん_modify_secondary_chance,
                subject_spec="defender:self",
            ),
        }
    ),
    "わざわいのうつわ": AbilityData(
        flags=[
            "undeniable"
        ],
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.わざわいのうつわ_modify_atk,
                subject_spec="defender:self",
            )
        }
    ),
    "わざわいのおふだ": AbilityData(
        flags=[
            "undeniable"
        ],
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.わざわいのおふだ_modify_atk,
                subject_spec="defender:self",
            )
        }
    ),
    "わざわいのたま": AbilityData(
        flags=[
            "undeniable"
        ],
        handlers={
            Event.ON_CALC_DEF_MODIFIER: h.AbilityHandler(
                h.わざわいのたま_modify_def,
                subject_spec="attacker:self",
            )
        }
    ),
    "わざわいのつるぎ": AbilityData(
        handlers={
            Event.ON_CALC_DEF_MODIFIER: h.AbilityHandler(
                h.わざわいのつるぎ_modify_def,
                subject_spec="attacker:self",
            )
        }
    ),
    "わたげ": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "わるいてぐせ": AbilityData(
        flags=[
            "undeniable"
        ],
        handlers={
            Event.ON_DAMAGE: h.AbilityHandler(
                h.わるいてぐせ_steal_item,
                subject_spec="defender:self",
                priority=180,
            )
        }
    ),
    "アイスフェイス": AbilityData(
        flags=[
            "uncopyable",
            "protected",
            "mold_breaker_ignorable",
        ]
    ),
    "アイスボディ": AbilityData(
        handlers={
            Event.ON_TURN_END_3: h.AbilityHandler(
                h.アイスボディ_on_turn_end,
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
    "アロマベール": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "イリュージョン": AbilityData(
        flags=[
            "uncopyable"
        ]
    ),
    "エアロック": AbilityData(
        flags=[
            "undeniable"
        ],
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
                partial(common.activate_terrain, terrain="エレキフィールド", source_spec="source:self"),
                subject_spec="source:self",
            )
        }
    ),
    "オーラブレイク": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "カブトアーマー": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_CALC_CRITICAL_RANK: h.AbilityHandler(
                h.カブトアーマー_on_calc_critical_rank,
                subject_spec="defender:self",
            )
        }
    ),
    "カーリーヘアー": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "クイックドロウ": AbilityData(),
    "クォークチャージ": AbilityData(
        flags=[
            "uncopyable",
        ],
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                hp.パラドックスチャージ_refresh,
                subject_spec="source:self",
                priority=200,
            ),
            Event.ON_FIELD_CHANGE: h.AbilityHandler(
                hp.パラドックスチャージ_refresh,
                subject_spec="source:self",
                priority=200,
            ),
            Event.ON_REFRESH_PARADOX_BOOST: h.AbilityHandler(
                hp.パラドックスチャージ_refresh,
                subject_spec="source:self",
                priority=200,
            ),
            DomainEvent.ON_CALC_SPEED: h.AbilityHandler(
                hp.パラドックスチャージ_on_calc_speed,
                subject_spec="source:self",
            ),
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                hp.パラドックスチャージ_on_calc_atk_modifier,
                subject_spec="attacker:self",
            ),
            Event.ON_CALC_DEF_MODIFIER: h.AbilityHandler(
                hp.パラドックスチャージ_on_calc_def_modifier,
                subject_spec="defender:self",
            ),
        }
    ),
    "クリアボディ": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_MODIFY_STAT: h.AbilityHandler(
                h.クリアボディ_modify_stat,
                subject_spec="target:self",
            )
        }
    ),
    "グラスメイカー": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                partial(common.activate_terrain, terrain="グラスフィールド", source_spec="source:self"),
                subject_spec="source:self",
            )
        }
    ),
    "サイコメイカー": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                partial(common.activate_terrain, terrain="サイコフィールド", source_spec="source:self"),
                subject_spec="source:self",
            )
        }
    ),
    "サンパワー": AbilityData(
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.サンパワー_modify_atk,
                subject_spec="attacker:self",
            ),
            Event.ON_TURN_END_3: h.AbilityHandler(
                h.サンパワー_on_turn_end,
                subject_spec="source:self",
            ),
        }
    ),
    "サーフテール": AbilityData(),
    "シェルアーマー": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_CALC_CRITICAL_RANK: h.AbilityHandler(
                h.カブトアーマー_on_calc_critical_rank,
                subject_spec="defender:self",
            )
        }
    ),
    "シンクロ": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "スイートベール": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
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
    "スナイパー": AbilityData(
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.AbilityHandler(
                h.スナイパー_modify_damage,
                subject_spec="attacker:self",
            )
        }
    ),
    "スロースタート": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.スロースタート_on_switch_in,
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
            "protected"
        ]
    ),
    "ゼロフォーミング": AbilityData(
        flags=[
            "uncopyable"
        ]
    ),
    "ソウルハート": AbilityData(),
    "ターボブレイズ": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.announce_ability_on_switch_in,
                subject_spec="source:self",
            ),
            Event.ON_CHECK_DEF_ABILITY_ENABLED: h.AbilityHandler(
                h.かたやぶり_check_def_ability_enabled,
                subject_spec="attacker:self",
                priority=100,
            ),
        }
    ),
    "ダウンロード": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.ダウンロード_on_switch_in,
                subject_spec="source:self",
            ),
        }
    ),
    "ダークオーラ": AbilityData(
        flags=[
            "undeniable",
            "mold_breaker_ignorable",
        ]
    ),
    "テイルアーマー": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "テクニシャン": AbilityData(
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.AbilityHandler(
                h.テクニシャン_on_calc_power_modifier,
                subject_spec="attacker:self",
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
                h.テラスシェル_modify_def_type_modifier,
                subject_spec="defender:self",
            )
        }
    ),
    "テラスチェンジ": AbilityData(
        flags=[
            "uncopyable",
            "protected"
        ]
    ),
    "テラボルテージ": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.announce_ability_on_switch_in,
                subject_spec="source:self",
            ),
            Event.ON_CHECK_DEF_ABILITY_ENABLED: h.AbilityHandler(
                h.かたやぶり_check_def_ability_enabled,
                subject_spec="attacker:self",
                priority=100,
            ),
        }
    ),
    "テレパシー": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "デルタストリーム": AbilityData(
        flags=[
            "undeniable"
        ],
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                partial(common.activate_weather, weather="らんきりゅう", source_spec="source:self"),
                subject_spec="source:self",
            ),
            Event.ON_SWITCH_OUT: h.AbilityHandler(
                partial(common.deactivate_weather, weather="らんきりゅう"),
                subject_spec="source:self",
            ),
        },
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
                h.トレース_on_switch_in,
                subject_spec="source:self",
            ),
            Event.ON_SWITCH_OUT: h.AbilityHandler(
                h.トレース_on_switch_out,
                subject_spec="source:self",
            ),
        },
    ),
    "ナイトメア": AbilityData(),
    "ノーてんき": AbilityData(
        flags=[
            "undeniable"
        ],
        handlers={
            Event.ON_CHECK_WEATHER_ENABLED: h.AbilityHandler(
                h.ノーてんき_check_weather_enabled,
                subject_spec="source:self",
            ),
        },
    ),
    "ノーガード": AbilityData(
        flags=[
            "undeniable"
        ],
        handlers={
            Event.ON_MODIFY_ACCURACY: [
                h.AbilityHandler(
                    h.ノーガード_modify_accuracy,
                    subject_spec="attacker:self",
                ),
                h.AbilityHandler(
                    h.ノーガード_modify_accuracy,
                    subject_spec="defender:self",
                ),
            ]
        }
    ),
    "ノーマルスキン": AbilityData(
        handlers={
            Event.ON_MODIFY_MOVE_TYPE: h.AbilityHandler(
                h.ノーマルスキン_modify_move_type,
                subject_spec="source:self",
            ),
            Event.ON_CALC_POWER_MODIFIER: h.AbilityHandler(
                h.ノーマルスキン_modify_power,
                subject_spec="attacker:self",
            ),
        }
    ),
    "ハドロンエンジン": AbilityData(
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.ハドロンエンジン_modify_atk,
                subject_spec="attacker:self",
            )
        }
    ),
    "ハードロック": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.AbilityHandler(
                h.フィルターハードロックプリズムアーマー_modify_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "バッテリー": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "バトルスイッチ": AbilityData(
        flags=[
            "uncopyable",
            "protected"
        ],
        handlers={
            Event.ON_CHECK_ACTION: h.AbilityHandler(
                h.バトルスイッチ_check_action,
                subject_spec="attacker:self",
                priority=200,
            ),
            Event.ON_SWITCH_OUT: h.AbilityHandler(
                h.バトルスイッチ_on_switch_out,
                subject_spec="source:self",
            ),
        },
    ),
    "バリアフリー": AbilityData(),
    "パステルベール": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "パワースポット": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
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
    "ヒーリングシフト": AbilityData(),
    "ビビッドボディ": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "ビーストブースト": AbilityData(),
    "ファントムガード": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.AbilityHandler(
                h.マルチスケイルファントムガード_modify_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "ファーコート": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_CALC_DEF_MODIFIER: h.AbilityHandler(
                h.ファーコート_modify_def,
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
                h.フィルターハードロックプリズムアーマー_modify_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "フェアリーオーラ": AbilityData(
        flags=[
            "undeniable",
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
    "フレンドガード": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "ブレインフォース": AbilityData(
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.AbilityHandler(
                h.ブレインフォース_modify_damage,
                subject_spec="attacker:self",
            )
        }
    ),
    "プラス": AbilityData(),
    "プリズムアーマー": AbilityData(
        flags=[
            "undeniable"
        ],
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.AbilityHandler(
                h.フィルターハードロックプリズムアーマー_modify_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "プレッシャー": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "ヘドロえき": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "ヘヴィメタル": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "ポイズンヒール": AbilityData(
        handlers={
            Event.ON_MODIFY_POISON_DAMAGE: h.AbilityHandler(
                h.ポイズンヒール_modify_poison_damage,
                subject_spec="target:self",
            )
        }
    ),
    "マイティチェンジ": AbilityData(
        flags=[
            "uncopyable",
            "protected"
        ],
        handlers={
            Event.ON_SWITCH_OUT: h.AbilityHandler(
                h.マイティチェンジ_on_switch_out,
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
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.マイペース_prevent_confusion,
                subject_spec="target:self",
            )
        }
    ),
    "マグマのよろい": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.マグマのよろい_prevent_freeze,
                subject_spec="target:self",
            )
        }
    ),
    "マジシャン": AbilityData(
        handlers={
            Event.ON_DAMAGE: h.AbilityHandler(
                h.マジシャン_steal_item,
                subject_spec="attacker:self",
            )
        }
    ),
    "マジックガード": AbilityData(
        flags=[
            "undeniable"
        ],
        handlers={
            Event.ON_BEFORE_DAMAGE_APPLY: h.AbilityHandler(
                h.マジックガード_reduce_damage,
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
                h.マルチスケイルファントムガード_modify_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "マルチタイプ": AbilityData(
        flags=[
            "uncopyable",
            "protected"
        ],
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                h.マルチタイプ_on_switch_in,
                subject_spec="source:self",
            ),
            Event.ON_CHECK_ITEM_CHANGE: h.AbilityHandler(
                h.マルチタイプ_prevent_item_change,
                subject_spec="target:self",
            ),
        }
    ),
    "ミイラ": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "ミストメイカー": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                partial(common.activate_terrain, terrain="ミストフィールド", source_spec="source:self"),
                subject_spec="source:self",
            )
        }
    ),
    "ミラクルスキン": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
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
    "ムラっけ": AbilityData(
        handlers={
            Event.ON_TURN_END_3: h.AbilityHandler(
                h.ムラっけ_on_turn_end,
                subject_spec="source:self",
            )
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
        flags=[
            "undeniable"
        ]
    ),
    "メロメロボディ": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "ヨガパワー": AbilityData(
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.AbilityHandler(
                h.ちからもちヨガパワー_on_calc_atk_modifier,
                subject_spec="attacker:self",
            )
        }
    ),
    "ライトメタル": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "リベロ": AbilityData(
        handlers={
            Event.ON_MOVE_CHARGE: h.AbilityHandler(
                h.へんげんじざいリベロ_on_move_charge,
                subject_spec="source:self",
                priority=100,
            )
        }
    ),
    "リミットシールド": AbilityData(
        flags=[
            "uncopyable",
            "protected",
            "undeniable"
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
    "レシーバー": AbilityData(
        flags=[
            "uncopyable"
        ]
    ),
    "ＡＲシステム": AbilityData(),
    "おもかげやどし": AbilityData(
        flags=[
            "uncopyable",
            "protected"
        ]
    )
}


common_setup()
