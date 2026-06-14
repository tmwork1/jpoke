"""アイテムデータ定義モジュール。

Note:
    このモジュール内のアイテム定義はITEMS辞書内で五十音順に配置されています。
"""
from jpoke.enums import Event, DomainEvent
from jpoke.core import HandlerReturn
from jpoke.handlers import item as h
from .models import ItemData
from .megaevol import MEGA_STONES


def common_setup():
    """共通のセットアップ処理"""
    _add_mega_stones(ITEMS)

    for name, data in ITEMS.items():
        ITEMS[name].name = name


def _add_mega_stones(items: dict[str, ItemData]):
    """メガストーンをITEMS辞書に追加する。"""
    for name, forms in MEGA_STONES.items():
        items[name] = ItemData(
            consumable=False,
            removable=False,
            fling_power=80,
            mega_evol=forms,
            handlers={
                Event.ON_MODIFY_COMMAND_OPTIONS: h.ItemHandler(
                    h.mega_modify_command_options,
                    subject_spec="source:self"
                ),
            }
        )


ITEMS: dict[str, ItemData] = {
    "": ItemData(name=""),
    "あかいいと": ItemData(
        consumable=False,
        fling_power=10,
        handlers={
            Event.ON_VOLATILE_START: h.ItemHandler(
                h.あかいいと_infatuate_foe,
                subject_spec="source:self",
            )
        }
    ),
    "あついいわ": ItemData(
        consumable=False,
        fling_power=60,
        handlers={
            Event.ON_MODIFY_DURATION: h.ItemHandler(
                h.あついいわ_resolve_field_count,
                subject_spec="source:self",
            )
        }
    ),
    "あつぞこブーツ": ItemData(
        consumable=False,
        fling_power=80,
        handlers={
            Event.ON_CHECK_HAZARD_IMMUNE: h.ItemHandler(
                h.あつぞこブーツ_check_hazard_immune,
                subject_spec="source:self",
            )
        }
    ),
    "いかさまダイス": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            Event.ON_MODIFY_HIT_COUNT: h.ItemHandler(
                h.いかさまダイス_modify_hit_count,
                subject_spec="attacker:self",
            )
        }
    ),
    "いしずえのめん": ItemData(
        consumable=False,
        removable=False,
        fling_power=60,
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.ItemHandler(
                h.オーガポンのめん_boost_atk,
                subject_spec="attacker:self",
            )
        }
    ),
    "いどのめん": ItemData(
        consumable=False,
        removable=False,
        fling_power=60,
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.ItemHandler(
                h.オーガポンのめん_boost_atk,
                subject_spec="attacker:self",
            )
        }
    ),
    "いのちのたま": ItemData(
        fling_power=30,
        consumable=False,
        handlers={
            Event.ON_HIT: h.ItemHandler(
                h.いのちのたま_recoil,
                subject_spec="attacker:self",
            )
        }
    ),
    "エレキシード": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_SWITCH_IN: h.ItemHandler(
                h.エレキシード_boost_defense,
                subject_spec="source:self",
                once=True,
            ),
            Event.ON_FIELD_CHANGE: h.ItemHandler(
                h.エレキシード_boost_defense,
                subject_spec="source:self",
                once=True,
            ),
        }
    ),
    "おうじゃのしるし": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            Event.ON_HIT: h.ItemHandler(
                h.flinch_on_hit_10pct,
                subject_spec="attacker:self",
            )
        }
    ),
    "おおきなねっこ": ItemData(
        consumable=False,
        fling_power=10,
        handlers={
            Event.ON_CALC_DRAIN: h.ItemHandler(
                h.おおきなねっこ_boost_drain,
                subject_spec="attacker:self",
            )
        }
    ),
    "おんみつマント": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            Event.ON_MODIFY_SECONDARY_CHANCE: h.ItemHandler(
                h.おんみつマント_negate_secondary,
                subject_spec="defender:self",
            )
        }
    ),
    "かいがらのすず": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            Event.ON_HIT: h.ItemHandler(
                h.かいがらのすず_heal_on_hit,
                subject_spec="attacker:self",
            )
        }
    ),
    "かえんだま": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            Event.ON_TURN_END: h.ItemHandler(
                h.かえんだま_apply_burn,
                subject_spec="source:self",
                priority=90,
            )
        }
    ),
    "かたいいし": ItemData(
        consumable=False,
        fling_power=100,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.かたいいし_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "かまどのめん": ItemData(
        consumable=False,
        removable=False,
        fling_power=60,
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.ItemHandler(
                h.オーガポンのめん_boost_atk,
                subject_spec="attacker:self",
            )
        }
    ),
    "からぶりほけん": ItemData(
        consumable=True,
        fling_power=80,
        handlers={
            Event.ON_MISS: h.ItemHandler(
                h.からぶりほけん_boost_speed_on_miss,
                subject_spec="attacker:self",
                once=True,
            )
        }
    ),
    "かるいし": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            DomainEvent.ON_CALC_SPEED: h.ItemHandler(
                h.かるいし_boost_speed,
                subject_spec="source:self",
            )
        }
    ),
    "きあいのタスキ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_MODIFY_MOVE_DAMAGE: h.ItemHandler(
                h.きあいのタスキ_survive_ohko,
                subject_spec="defender:self",
                once=True,
            )
        }
    ),
    "きあいのハチマキ": ItemData(
        consumable=False,
        fling_power=10,
        handlers={
            Event.ON_MODIFY_MOVE_DAMAGE: h.ItemHandler(
                h.きあいのハチマキ_survive_by_chance,
                subject_spec="defender:self",
            )
        }
    ),
    "きせきのたね": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.きせきのたね_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "きゅうこん": ItemData(
        consumable=True,
        fling_power=30,
        handlers={
        }
    ),
    "きれいなぬけがら": ItemData(
        consumable=False,
        fling_power=10,
        handlers={
            Event.ON_CHECK_TRAPPED: h.ItemHandler(
                lambda *args: HandlerReturn(value=False, stop_event=True),
                subject_spec="source:self",
                priority=-100,
            )
        }
    ),
    "ぎんのこな": ItemData(
        consumable=False,
        fling_power=10,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.ぎんのこな_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "くっつきバリ": ItemData(
        consumable=False,
        fling_power=80
    ),
    "グラスシード": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_SWITCH_IN: h.ItemHandler(
                h.グラスシード_boost_defense,
                subject_spec="source:self",
                once=True,
            ),
            Event.ON_FIELD_CHANGE: h.ItemHandler(
                h.グラスシード_boost_defense,
                subject_spec="source:self",
                once=True,
            ),
        }
    ),
    "グランドコート": ItemData(
        consumable=False,
        fling_power=60,
        handlers={
            Event.ON_MODIFY_DURATION: h.ItemHandler(
                h.グランドコート_resolve_field_count,
                subject_spec="source:self",
            ),
        }
    ),
    "クリアチャーム": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            Event.ON_BEFORE_MODIFY_STAT: h.ItemHandler(
                h.クリアチャーム_block_stat_drop,
                subject_spec="target:self",
            )
        }
    ),
    "くろいてっきゅう": ItemData(
        consumable=False,
        fling_power=130,
        handlers={
            DomainEvent.ON_CALC_SPEED: h.ItemHandler(
                h.くろいてっきゅう_halve_speed,
                subject_spec="source:self",
            ),
            Event.ON_CHECK_FLOATING: h.ItemHandler(
                h.くろいてっきゅう_negate_floating,
                subject_spec="source:self",
            ),
        }
    ),
    "くろいヘドロ": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            Event.ON_TURN_END: h.ItemHandler(
                h.くろいヘドロ_heal_or_damage,
                subject_spec="source:self",
                priority=50,
            )
        }
    ),
    "くろいメガネ": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.くろいメガネ_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "くろおび": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.くろおび_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "こうかくレンズ": ItemData(
        consumable=False,
        fling_power=10,
        handlers={
            Event.ON_MODIFY_ACCURACY: h.ItemHandler(
                h.こうかくレンズ_modify_accuracy,
                subject_spec="attacker:self",
            )
        }
    ),
    "こうこうのしっぽ": ItemData(
        consumable=False,
        fling_power=10,
        handlers={
            DomainEvent.ON_CALC_BACK_TIER: h.ItemHandler(
                h.こうこうのしっぽ_back_tier,
                subject_spec="attacker:self",
            )
        }
    ),
    "こころのしずく": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.こころのしずく_modify_power,
                subject_spec="attacker:self",
            )
        }
    ),
    "こだわりスカーフ": ItemData(
        consumable=False,
        fling_power=10,
        handlers={
            DomainEvent.ON_CALC_SPEED: h.ItemHandler(
                h.こだわりスカーフ_boost_speed,
                subject_spec="source:self",
            ),
            Event.ON_MOVE_END: h.ItemHandler(
                h.こだわり_lock_move,
                subject_spec="attacker:self",
            ),
        }
    ),
    "こだわりハチマキ": ItemData(
        consumable=False,
        fling_power=10,
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.ItemHandler(
                h.こだわりハチマキ_boost_physical,
                subject_spec="attacker:self",
            ),
            Event.ON_MOVE_END: h.ItemHandler(
                h.こだわり_lock_move,
                subject_spec="attacker:self",
            ),
        }
    ),
    "こだわりメガネ": ItemData(
        consumable=False,
        fling_power=10,
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.ItemHandler(
                h.こだわりメガネ_boost_special,
                subject_spec="attacker:self",
            ),
            Event.ON_MOVE_END: h.ItemHandler(
                h.こだわり_lock_move,
                subject_spec="attacker:self",
            ),
        }
    ),
    "ゴツゴツメット": ItemData(
        consumable=False,
        fling_power=60,
        handlers={
            Event.ON_DAMAGE_HIT: h.ItemHandler(
                h.ゴツゴツメット_chip_contact_attacker,
                subject_spec="defender:self",
            )
        }
    ),
    "サイコシード": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_SWITCH_IN: h.ItemHandler(
                h.サイコシード_boost_spdef,
                subject_spec="source:self",
                once=True,
            ),
            Event.ON_FIELD_CHANGE: h.ItemHandler(
                h.サイコシード_boost_spdef,
                subject_spec="source:self",
                once=True,
            ),
        }
    ),
    "さらさらいわ": ItemData(
        consumable=False,
        fling_power=10,
        handlers={
            Event.ON_MODIFY_DURATION: h.ItemHandler(
                h.さらさらいわ_resolve_field_count,
                subject_spec="source:self",
            )
        }
    ),
    "じしゃく": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.じしゃく_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "しめつけバンド": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            Event.ON_MODIFY_BIND_DAMAGE: h.ItemHandler(
                h.しめつけバンド_boost_bind_damage,
                subject_spec="source:foe",
            )
        }
    ),
    "しめったいわ": ItemData(
        consumable=False,
        fling_power=60,
        handlers={
            Event.ON_MODIFY_DURATION: h.ItemHandler(
                h.しめったいわ_resolve_field_count,
                subject_spec="source:self",
            )
        }
    ),
    "じゃくてんほけん": ItemData(
        consumable=True,
        fling_power=80,
        handlers={
            Event.ON_DAMAGE_HIT: h.ItemHandler(
                h.じゃくてんほけん_boost_on_super_effective,
                subject_spec="defender:self",
                once=True,
            )
        }
    ),
    "じゅうでんち": ItemData(
        consumable=True,
        fling_power=30,
        handlers={
            Event.ON_DAMAGE_HIT: h.ItemHandler(
                h.じゅうでんち_boost_atk_on_electric_hit,
                subject_spec="defender:self",
                once=True,
            )
        }
    ),
    "シルクのスカーフ": ItemData(
        consumable=False,
        fling_power=10,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.シルクのスカーフ_modify_power_by_type,
                subject_spec="attacker:self",
            )
        },
    ),
    "しろいハーブ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_BEFORE_MODIFY_STAT: h.ItemHandler(
                h.しろいハーブ_cancel_stat_drop,
                subject_spec="target:self",
                once=True,
            ),
        }
    ),
    "しんかのきせき": ItemData(
        consumable=False,
        fling_power=40,
        handlers={
            Event.ON_CALC_DEF_MODIFIER: h.ItemHandler(
                h.しんかのきせき_boost_defenses,
                subject_spec="defender:self",
            ),
        }
    ),
    "しんぴのしずく": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.しんぴのしずく_modify_power_by_type,
                subject_spec="attacker:self",
            )
        },
    ),
    "するどいキバ": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            Event.ON_HIT: h.ItemHandler(
                h.flinch_on_hit_10pct,
                subject_spec="attacker:self",
            )
        }
    ),
    "するどいくちばし": ItemData(
        consumable=False,
        fling_power=50,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.するどいくちばし_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "するどいツメ": ItemData(
        consumable=False,
        fling_power=80,
        handlers={
            Event.ON_CALC_CRITICAL_RANK: h.ItemHandler(
                h.するどいツメ_boost_critical_rank,
                subject_spec="attacker:self",
            )
        }
    ),
    "せいれいプレート": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.せいれいプレート_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "フェアリーメモリ": ItemData(
        consumable=False,
        fling_power=50,
    ),
    "せんせいのツメ": ItemData(
        consumable=False,
        fling_power=80,
        handlers={
            DomainEvent.ON_CALC_BACK_TIER: h.ItemHandler(
                h.せんせいのツメ_priority_boost,
                subject_spec="attacker:self",
            )
        }
    ),
    "だっしゅつパック": ItemData(
        consumable=True,
        fling_power=50,
        handlers={
            Event.ON_MODIFY_STAT: h.ItemHandler(
                h.だっしゅつパック_reserve_switch,
                subject_spec="target:self",
            )
        }
    ),
    "だっしゅつボタン": ItemData(
        consumable=True,
        fling_power=30,
        handlers={
            Event.ON_DAMAGE_HIT: h.ItemHandler(
                h.だっしゅつボタン_reserve_switch,
                subject_spec="defender:self",
            )
        }
    ),
    "たつじんのおび": ItemData(
        consumable=False,
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.たつじんのおび_boost_super_effective,
                subject_spec="attacker:self",
            )
        }
    ),
    "たべのこし": ItemData(
        fling_power=10,
        handlers={
            Event.ON_TURN_END: h.ItemHandler(
                h.たべのこし_heal_hp,
                subject_spec="source:self",
                priority=60,
            )
        }
    ),
    "ちからのハチマキ": ItemData(
        consumable=False,
        fling_power=10,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.ちからのハチマキ_boost_physical,
                subject_spec="attacker:self",
            )
        }
    ),
    "つめたいいわ": ItemData(
        consumable=False,
        fling_power=40,
        handlers={
            Event.ON_MODIFY_DURATION: h.ItemHandler(
                h.つめたいいわ_resolve_field_count,
                subject_spec="source:self",
            )
        }
    ),
    "でかいきんのたま": ItemData(
        consumable=False,
        fling_power=130,
        handlers={}  # 効果なし
    ),
    "でんきだま": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.ItemHandler(
                h.でんきだま_boost_atk,
                subject_spec="attacker:self",
            )
        }
    ),
    "とくせいガード": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            Event.ON_CHECK_ABILITY_DISABLE: h.ItemHandler(
                lambda *args: HandlerReturn(value=True, stop_event=True),
                subject_spec="source:self",
                priority=200,
            ),
        }
    ),
    "どくどくだま": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            Event.ON_TURN_END: h.ItemHandler(
                h.どくどくだま_apply_poison,
                subject_spec="source:self",
                priority=90,
            )
        }
    ),
    "どくバリ": ItemData(
        consumable=False,
        fling_power=70,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.どくバリ_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "とけないこおり": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.とけないこおり_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "とつげきチョッキ": ItemData(
        consumable=False,
        fling_power=80,
        handlers={
            Event.ON_TRY_MOVE_1: h.ItemHandler(
                h.とつげきチョッキ_block_status_move,
                subject_spec="attacker:self",
            ),
            Event.ON_CALC_DEF_MODIFIER: h.ItemHandler(
                h.とつげきチョッキ_boost_spdef,
                subject_spec="defender:self",
            ),
        }
    ),
    "ねばりのかぎづめ": ItemData(
        consumable=False,
        fling_power=90,
        handlers={
            Event.ON_MODIFY_DURATION: h.ItemHandler(
                h.ねばりのかぎづめ_fix_bind_duration,
                subject_spec="attacker:self",
            )
        }
    ),
    "ねらいのまと": ItemData(
        consumable=False,
        fling_power=10,
        handlers={
            Event.ON_CALC_DEF_TYPE_MODIFIER: h.ItemHandler(
                h.ねらいのまと_negate_immunity,
                subject_spec="defender:self",
                priority=-100,
            )
        }
    ),
    "ノーマルジュエル": ItemData(
        consumable=True,
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.ノーマルジュエル_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "のどスプレー": ItemData(
        consumable=True,
        fling_power=30,
        handlers={
            Event.ON_MOVE_END: h.ItemHandler(
                h.のどスプレー_boost_spatk_on_sound,
                subject_spec="attacker:self",
                once=True,
            )
        }
    ),
    "のろいのおふだ": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.のろいのおふだ_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "パワフルハーブ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_MOVE_CHARGE: h.ItemHandler(
                h.パワフルハーブ_skip_charge,
                subject_spec="attacker:self",
                once=True,
            )
        }
    ),
    "パンチグローブ": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.パンチグローブ_boost_punch_power,
                subject_spec="attacker:self",
            ),
            Event.ON_CHECK_CONTACT: h.ItemHandler(
                h.パンチグローブ_negate_punch_contact,
                subject_spec="attacker:self",
            ),
        }
    ),
    "ばんのうがさ": ItemData(
        consumable=False,
        fling_power=60
    ),
    "ひかりごけ": ItemData(
        consumable=True,
        fling_power=30,
        handlers={
            Event.ON_DAMAGE_HIT: h.ItemHandler(
                h.ひかりごけ_boost_spdef_on_water_hit,
                subject_spec="defender:self",
                once=True,
            )
        }
    ),
    "ひかりのこな": ItemData(
        consumable=False,
        fling_power=10,
        handlers={
            Event.ON_MODIFY_ACCURACY: h.ItemHandler(
                h.ひかりのこな_reduce_accuracy,
                subject_spec="defender:self",
            )
        }
    ),
    "ひかりのねんど": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            Event.ON_MODIFY_DURATION: h.ItemHandler(
                h.ひかりのねんど_resolve_field_count,
                subject_spec="source:self",
            ),
        }
    ),
    "ビビリだま": ItemData(
        consumable=True,
        fling_power=30,
        handlers={
            Event.ON_MODIFY_STAT: h.ItemHandler(
                h.ビビリだま_boost_speed_on_intimidate,
                subject_spec="target:self",
                once=True,
            )
        }
    ),
    "ピントレンズ": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            Event.ON_CALC_CRITICAL_RANK: h.ItemHandler(
                h.ピントレンズ_boost_critical_rank,
                subject_spec="attacker:self",
            )
        }
    ),
    "ブーストエナジー": ItemData(
        consumable=True,
        removable=False,
        fling_power=30,
        handlers={
            Event.ON_ITEM_ENABLED: h.ItemHandler(
                h.ブーストエナジー_refresh_paradox_charge,
                subject_spec="source:self",
            ),
            Event.ON_ITEM_GAINED: h.ItemHandler(
                h.ブーストエナジー_refresh_paradox_charge,
                subject_spec="source:self",
            ),
        }
    ),
    "ふうせん": ItemData(
        consumable=False,
        fling_power=10,
        handlers={
            Event.ON_CHECK_FLOATING: h.ItemHandler(
                h.ふうせん_check_floating,
                subject_spec="source:self",
            ),
            Event.ON_DAMAGE_HIT: h.ItemHandler(
                h.ふうせん_pop_on_hit,
                subject_spec="defender:self",
            ),
        }
    ),
    "フォーカスレンズ": ItemData(
        consumable=False,
        fling_power=10,
        handlers={
            Event.ON_MODIFY_ACCURACY: h.ItemHandler(
                h.フォーカスレンズ_boost_accuracy_second,
                subject_spec="attacker:self",
            )
        }
    ),
    "ぼうごパット": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            Event.ON_CHECK_CONTACT: h.ItemHandler(
                h.ぼうごパット_negate_contact,
                subject_spec="attacker:self",
            )
        }
    ),
    "ぼうじんゴーグル": ItemData(
        consumable=False,
        fling_power=80,
        handlers={
            Event.ON_BEFORE_APPLY_MOVE: h.ItemHandler(
                h.ぼうじんゴーグル_block_powder_move,
                subject_spec="defender:self",
            ),
            Event.ON_MODIFY_NON_MOVE_DAMAGE: h.ItemHandler(
                h.ぼうじんゴーグル_block_weather_damage,
                subject_spec="target:self",
            ),
        }
    ),
    "まがったスプーン": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.まがったスプーン_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "ミストシード": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_SWITCH_IN: h.ItemHandler(
                h.ミストシード_boost_spdef,
                subject_spec="source:self",
                once=True,
            ),
            Event.ON_FIELD_CHANGE: h.ItemHandler(
                h.ミストシード_boost_spdef,
                subject_spec="source:self",
                once=True,
            ),
        }
    ),
    "メタルコート": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.メタルコート_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "メトロノーム": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.メトロノーム_boost_power,
                subject_spec="attacker:self",
            ),
            Event.ON_MOVE_END: h.ItemHandler(
                h.メトロノーム_update_count,
                subject_spec="attacker:self",
            ),
        }
    ),
    "メンタルハーブ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_VOLATILE_START: h.ItemHandler(
                h.メンタルハーブ_cure_mental_volatile,
                subject_spec="source:self",
                once=True,
            )
        }
    ),
    "もくたん": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.もくたん_modify_power_by_type,
                subject_spec="attacker:self",
            )
        },
    ),
    "ものしりメガネ": ItemData(
        consumable=False,
        fling_power=10,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.ものしりメガネ_boost_special,
                subject_spec="attacker:self",
            )
        }
    ),
    "ものまねハーブ": ItemData(
        consumable=True,
        fling_power=30,
        handlers={
            Event.ON_MODIFY_STAT: h.ItemHandler(
                h.ものまねハーブ_copy_stat_boost,
                subject_spec="target:foe",
                once=True,
            )
        }
    ),
    "やわらかいすな": ItemData(
        consumable=False,
        fling_power=10,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.やわらかいすな_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "ゆきだま": ItemData(
        consumable=True,
        fling_power=30,
        handlers={
            Event.ON_DAMAGE_HIT: h.ItemHandler(
                h.ゆきだま_boost_defense_on_ice_hit,
                subject_spec="defender:self",
                once=True,
            )
        }
    ),
    "ようせいのハネ": ItemData(
        consumable=False,
        fling_power=20,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.ようせいのハネ_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "りゅうのキバ": ItemData(
        consumable=False,
        fling_power=70,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.りゅうのキバ_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "ルームサービス": ItemData(
        consumable=True,
        fling_power=100,
        handlers={
            Event.ON_FIELD_ACTIVATE: h.ItemHandler(
                h.ルームサービス_drop_speed_on_trick_room,
                subject_spec="source:self",
                once=True,
            )
        }
    ),
    "レッドカード": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_DAMAGE_HIT: h.ItemHandler(
                h.レッドカード_force_switch,
                subject_spec="defender:self",
                once=True,
            )
        }
    ),
    "くちたけん": ItemData(
        consumable=False,
        removable=False,
        fling_power=0,
        handlers={
            Event.ON_SWITCH_IN: h.ItemHandler(
                h.くちたけん_form_change,
                subject_spec="source:self",
            ),
            Event.ON_ITEM_GAINED: h.ItemHandler(
                h.くちたけん_form_change,
                subject_spec="source:self",
            ),
        }
    ),
    "くちたたて": ItemData(
        consumable=False,
        removable=False,
        fling_power=0,
        handlers={
            Event.ON_SWITCH_IN: h.ItemHandler(
                h.くちたたて_form_change,
                subject_spec="source:self",
            ),
            Event.ON_ITEM_GAINED: h.ItemHandler(
                h.くちたたて_form_change,
                subject_spec="source:self",
            ),
        }
    ),
    "こんごうだま": ItemData(
        consumable=False,
        removable=False,
        fling_power=0,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.こんごうだま_modify_power,
                subject_spec="attacker:self",
            )
        }
    ),
    "しらたま": ItemData(
        consumable=False,
        removable=False,
        fling_power=0,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.しらたま_modify_power,
                subject_spec="attacker:self",
            )
        }
    ),
    "だいこんごうだま": ItemData(
        consumable=False,
        removable=False,
        fling_power=0,
        handlers={
            Event.ON_SWITCH_IN: h.ItemHandler(
                h.だいこんごうだま_form_change,
                subject_spec="source:self",
            ),
            Event.ON_ITEM_GAINED: h.ItemHandler(
                h.だいこんごうだま_form_change,
                subject_spec="source:self",
            ),
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.だいこんごうだま_modify_power,
                subject_spec="attacker:self",
            ),
        }
    ),
    "だいしらたま": ItemData(
        consumable=False,
        removable=False,
        fling_power=0,
        handlers={
            Event.ON_SWITCH_IN: h.ItemHandler(
                h.だいしらたま_form_change,
                subject_spec="source:self",
            ),
            Event.ON_ITEM_GAINED: h.ItemHandler(
                h.だいしらたま_form_change,
                subject_spec="source:self",
            ),
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.だいしらたま_modify_power,
                subject_spec="attacker:self",
            ),
        }
    ),
    "だいはっきんだま": ItemData(
        consumable=False,
        removable=False,
        fling_power=0,
        handlers={
            Event.ON_SWITCH_IN: h.ItemHandler(
                h.だいはっきんだま_form_change,
                subject_spec="source:self",
            ),
            Event.ON_ITEM_GAINED: h.ItemHandler(
                h.だいはっきんだま_form_change,
                subject_spec="source:self",
            ),
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.だいはっきんだま_modify_power,
                subject_spec="attacker:self",
            ),
        }
    ),
    "はっきんだま": ItemData(
        consumable=False,
        removable=False,
        fling_power=0,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.はっきんだま_modify_power,
                subject_spec="attacker:self",
            )
        }
    ),
    "オボンのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_HP_CHANGED: h.ItemHandler(
                h.オボンのみ_heal_on_half_hp,
                subject_spec="target:self",
                once=True,
            ),
        }
    ),
    "ラムのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_TURN_END: h.ItemHandler(
                h.ラムのみ_cure_ailment,
                subject_spec="source:self",
                priority=50,
                once=True,
            )
        }
    ),
    "クラボのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_TURN_END: h.ItemHandler(
                h.クラボのみ_cure_paralysis,
                subject_spec="source:self",
                priority=50,
                once=True,
            )
        }
    ),
    "カゴのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_TURN_END: h.ItemHandler(
                h.カゴのみ_cure_sleep,
                subject_spec="source:self",
                priority=50,
                once=True,
            )
        }
    ),
    "モモンのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_TURN_END: h.ItemHandler(
                h.モモンのみ_cure_poison,
                subject_spec="source:self",
                priority=50,
                once=True,
            )
        }
    ),
    "チーゴのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_TURN_END: h.ItemHandler(
                h.チーゴのみ_cure_burn,
                subject_spec="source:self",
                priority=50,
                once=True,
            )
        }
    ),
    "ナナシのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_TURN_END: h.ItemHandler(
                h.ナナシのみ_cure_freeze,
                subject_spec="source:self",
                priority=50,
                once=True,
            )
        }
    ),
    "キーのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_TURN_END: h.ItemHandler(
                h.キーのみ_cure_confusion,
                subject_spec="source:self",
                priority=50,
                once=True,
            )
        }
    ),
    "ヒメリのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_PP_CONSUMED: h.ItemHandler(
                h.ヒメリのみ_restore_pp,
                subject_spec="attacker:self",
            )
        }
    ),
    "オレンのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_HP_CHANGED: h.ItemHandler(
                h.オレンのみ_heal_on_half_hp,
                subject_spec="target:self",
                once=True,
            ),
        }
    ),
    "フィラのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_HP_CHANGED: h.ItemHandler(
                h.heal_on_quarter_hp,
                subject_spec="target:self",
                once=True,
            )
        }
    ),
    "ウイのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_HP_CHANGED: h.ItemHandler(
                h.heal_on_quarter_hp,
                subject_spec="target:self",
                once=True,
            )
        }
    ),
    "マゴのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_HP_CHANGED: h.ItemHandler(
                h.heal_on_quarter_hp,
                subject_spec="target:self",
                once=True,
            )
        }
    ),
    "バンジのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_HP_CHANGED: h.ItemHandler(
                h.heal_on_quarter_hp,
                subject_spec="target:self",
                once=True,
            )
        }
    ),
    "イアのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_HP_CHANGED: h.ItemHandler(
                h.heal_on_quarter_hp,
                subject_spec="target:self",
                once=True,
            )
        }
    ),
    "チイラのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_HP_CHANGED: h.ItemHandler(
                h.チイラのみ_boost_attack,
                subject_spec="target:self",
                once=True,
            )
        }
    ),
    "リュガのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_HP_CHANGED: h.ItemHandler(
                h.リュガのみ_boost_defense,
                subject_spec="target:self",
                once=True,
            )
        }
    ),
    "ヤタピのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_HP_CHANGED: h.ItemHandler(
                h.ヤタピのみ_boost_spatk,
                subject_spec="target:self",
                once=True,
            )
        }
    ),
    "ズアのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_HP_CHANGED: h.ItemHandler(
                h.ズアのみ_boost_spdef,
                subject_spec="target:self",
                once=True,
            )
        }
    ),
    "カムラのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_HP_CHANGED: h.ItemHandler(
                h.カムラのみ_boost_speed,
                subject_spec="target:self",
                once=True,
            )
        }
    ),
    "スターのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_HP_CHANGED: h.ItemHandler(
                h.スターのみ_random_boost,
                subject_spec="target:self",
                once=True,
            )
        }
    ),
    "サンのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_HP_CHANGED: h.ItemHandler(
                h.サンのみ_apply_focus_energy,
                subject_spec="target:self",
                once=True,
            )
        }
    ),
    "ホズのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.ホズのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "リンドのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.リンドのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        }
        # handlers=_type_damage_handler("くさ", 2048/4096)
    ),
    "オッカのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.オッカのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "イトケのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.イトケのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "ソクノのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.ソクノのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "カシブのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.カシブのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "ヨロギのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.ヨロギのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "タンガのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.タンガのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "ウタンのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.ウタンのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "バコウのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.バコウのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "シュカのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.シュカのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "ビアーのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.ビアーのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "ヨプのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.ヨプのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "ヤチェのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.ヤチェのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "リリバのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.リリバのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "ナモのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.ナモのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "ハバンのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.ハバンのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "ロゼルのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.ロゼルのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "アッキのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_DAMAGE_HIT: h.ItemHandler(
                h.アッキのみ_boost_defense_on_physical_hit,
                subject_spec="defender:self",
                once=True,
            )
        }
    ),
    "タラプのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_DAMAGE_HIT: h.ItemHandler(
                h.タラプのみ_boost_spdef,
                subject_spec="defender:self",
                once=True,
            )
        }
    ),
    "イバンのみ": ItemData(
        consumable=True,
        fling_power=10
    ),
    "ジャポのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_DAMAGE_HIT: h.ItemHandler(
                h.ジャポのみ_retaliate_physical,
                subject_spec="defender:self",
                once=True,
            )
        }
    ),
    "レンブのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_DAMAGE_HIT: h.ItemHandler(
                h.レンブのみ_retaliate_special,
                subject_spec="defender:self",
                once=True,
            )
        }
    ),
    "ナゾのみ": ItemData(
        consumable=True,
        fling_power=10
    ),
    "ミクルのみ": ItemData(
        consumable=True,
        fling_power=10
    ),
}

common_setup()
