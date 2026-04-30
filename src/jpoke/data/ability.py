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
        ]
    ),
    "あくしゅう": AbilityData(),
    "あついしぼう": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "あとだし": AbilityData(),
    "あまのじゃく": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "あめうけざら": AbilityData(),
    "あめふらし": AbilityData(),
    "ありじごく": AbilityData(
        handlers={
            Event.ON_CHECK_TRAPPED: h.AbilityHandler(
                h.ありじごく,
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
    "いしあたま": AbilityData(),
    "いたずらごころ": AbilityData(),
    "いやしのこころ": AbilityData(),
    "いろめがね": AbilityData(),
    "いわはこび": AbilityData(),
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
                h.おうごんのからだ,
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
        ]
    ),
    "かいりきバサミ": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
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
                h.かげふみ,
                subject_spec="source:foe",
            )
        }
    ),
    "かぜのり": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "かそく": AbilityData(),
    "かたいツメ": AbilityData(),
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
                h.かちき,
                subject_spec="target:self",
            )
        }
    ),
    "かるわざ": AbilityData(),
    "かわりもの": AbilityData(
        flags=[
            "uncopyable"
        ]
    ),
    "かんそうはだ": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
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
    "がんじょうあご": AbilityData(),
    "ききかいひ": AbilityData(
        flags=[
            "undeniable"
        ],
        handlers={
            Event.ON_HP_CHANGED: h.AbilityHandler(
                h.ききかいひ,
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
        ]
    ),
    "きょううん": AbilityData(),
    "きょうえん": AbilityData(),
    "きょうせい": AbilityData(),
    "きよめのしお": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "きれあじ": AbilityData(),
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
                h.ぎゃくじょう,
                subject_spec="defender:self",
            )
        }
    ),
    "くいしんぼう": AbilityData(),
    "くさのけがわ": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "くだけるよろい": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "くろのいななき": AbilityData(),
    "げきりゅう": AbilityData(),
    "こおりのりんぷん": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
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
    "こんじょう": AbilityData(),
    "ごりむちゅう": AbilityData(),
    "さいせいりょく": AbilityData(),
    "さまようたましい": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "さめはだ": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "しぜんかいふく": AbilityData(),
    "しめりけ": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
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
        ]
    ),
    "しろのいななき": AbilityData(),
    "しんがん": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "しんりょく": AbilityData(),
    "じきゅうりょく": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "じしんかじょう": AbilityData(),
    "じゅうなん": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.じゅうなん,
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
                h.じりょく,
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
    "すいすい": AbilityData(),
    "すいほう": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "すじがねいり": AbilityData(),
    "すてみ": AbilityData(),
    "すなおこし": AbilityData(),
    "すなかき": AbilityData(
        handlers={
            DomainEvent.ON_CALC_SPEED: h.AbilityHandler(
                h.すなかき,
                subject_spec="source:self",
            )
        }
    ),
    "すながくれ": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "すなのちから": AbilityData(),
    "すなはき": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "すりぬけ": AbilityData(),
    "するどいめ": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "せいぎのこころ": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "せいしんりょく": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "せいでんき": AbilityData(),
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
        ]
    ),
    "そうだいしょう": AbilityData(),
    "たいねつ": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "たまひろい": AbilityData(),
    "たんじゅん": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "だっぴ": AbilityData(),
    "ちからずく": AbilityData(),
    "ちからもち": AbilityData(),
    "ちくでん": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "ちどりあし": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "ちょすい": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "てきおうりょく": AbilityData(),
    "てつのこぶし": AbilityData(
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.AbilityHandler(
                h.てつのこぶし,
                subject_spec="attacker:self",
            )
        }
    ),
    "てつのトゲ": AbilityData(
        flags=[
            "undeniable"
        ]
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
    "てんのめぐみ": AbilityData(),
    "でんきにかえる": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "でんきエンジン": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
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
    "どくしゅ": AbilityData(),
    "どくのくさり": AbilityData(),
    "どくのトゲ": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "どくぼうそう": AbilityData(),
    "どしょく": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
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
                h.ききかいひ,
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
        ]
    ),
    "ねつぼうそう": AbilityData(),
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
    "はがねつかい": AbilityData(),
    "はがねのせいしん": AbilityData(),
    "はじまりのうみ": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "はっこう": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "はとむね": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "はやあし": AbilityData(),
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
    "はりきり": AbilityData(),
    "はりこみ": AbilityData(),
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
    "ひでり": AbilityData(),
    "ひとでなし": AbilityData(),
    "ひひいろのこどう": AbilityData(),
    "ひらいしん": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
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
    "ふくがん": AbilityData(),
    "ふくつのこころ": AbilityData(),
    "ふくつのたて": AbilityData(
        flags=[
            "per_battle_once"
        ]
    ),
    "ふしぎなうろこ": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
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
                h.ふみん,
                subject_spec="target:self",
            )
        }
    ),
    "ふゆう": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
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
        ]
    ),
    "ほろびのボディ": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "ぼうおん": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "ぼうじん": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "ぼうだん": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
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
                h.みずのベール,
                subject_spec="target:self",
            )
        }
    ),
    "みつあつめ": AbilityData(),
    "むしのしらせ": AbilityData(),
    "めんえき": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.めんえき,
                subject_spec="target:self",
            )
        }
    ),
    "もうか": AbilityData(),
    "ものひろい": AbilityData(),
    "もふもふ": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "もらいび": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "やるき": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ],
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.やるき,
                subject_spec="target:self",
            )
        }
    ),
    "ゆうばく": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "ゆきかき": AbilityData(),
    "ゆきがくれ": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "ゆきふらし": AbilityData(),
    "ようりょくそ": AbilityData(),
    "よちむ": AbilityData(),
    "よびみず": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "よわき": AbilityData(),
    "りゅうのあぎと": AbilityData(),
    "りんぷん": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "わざわいのうつわ": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "わざわいのおふだ": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "わざわいのたま": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "わざわいのつるぎ": AbilityData(),
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
    "アイスボディ": AbilityData(),
    "アナライズ": AbilityData(),
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
        ]
    ),
    "エレキメイカー": AbilityData(),
    "オーラブレイク": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "カブトアーマー": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
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
        ]
    ),
    "グラスメイカー": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                partial(common.activate_terrain, terrain="グラスフィールド", source_spec="source:self"),
                subject_spec="source:self",
            )
        }
    ),
    "サイコメイカー": AbilityData(),
    "サンパワー": AbilityData(),
    "サーフテール": AbilityData(),
    "シェルアーマー": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
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
    "スカイスキン": AbilityData(),
    "スキルリンク": AbilityData(
        handlers={
            Event.ON_MODIFY_HIT_COUNT: h.AbilityHandler(
                h.スキルリンク_modify_hit_count,
                subject_spec="attacker:self",
            )
        }
    ),
    "スナイパー": AbilityData(),
    "スロースタート": AbilityData(),
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
    "ダウンロード": AbilityData(),
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
    "テクニシャン": AbilityData(),
    "テラスシェル": AbilityData(
        flags=[
            "uncopyable",
            "mold_breaker_ignorable",
        ]
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
        ]
    ),
    "トランジスタ": AbilityData(),
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
        ]
    ),
    "ノーガード": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "ノーマルスキン": AbilityData(),
    "ハドロンエンジン": AbilityData(),
    "ハードロック": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
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
        ]
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
            "undeniable"
        ]
    ),
    "ファーコート": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "フィルター": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "フェアリーオーラ": AbilityData(
        flags=[
            "undeniable",
            "mold_breaker_ignorable",
        ]
    ),
    "フェアリースキン": AbilityData(),
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
    "フリーズスキン": AbilityData(),
    "フレンドガード": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "ブレインフォース": AbilityData(),
    "プラス": AbilityData(),
    "プリズムアーマー": AbilityData(
        flags=[
            "undeniable"
        ]
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
    "ポイズンヒール": AbilityData(),
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
                h.マイペース,
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
                h.マグマのよろい,
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
                h.マジックガード,
                subject_spec="target:self",
            )
        }
    ),
    "マジックミラー": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "マルチスケイル": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "マルチタイプ": AbilityData(
        flags=[
            "uncopyable",
            "protected"
        ]
    ),
    "ミイラ": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "ミストメイカー": AbilityData(),
    "ミラクルスキン": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "ミラーアーマー": AbilityData(
        flags=[
            "mold_breaker_ignorable"
        ]
    ),
    "ムラっけ": AbilityData(),
    "メガランチャー": AbilityData(),
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
    "ヨガパワー": AbilityData(),
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
        ]
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
