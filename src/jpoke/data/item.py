"""アイテムデータ定義モジュール。

Note:
    このモジュール内のアイテム定義はITEMS辞書内で五十音順に配置されています。
"""
from jpoke.enums import Event, DomainEvent
from jpoke.core.lethal import LethalHandler
from jpoke.handlers import item as h

from .models import ItemData
from .megaevol import MEGA_STONES
from . import lethal_func as l


def common_setup():
    """共通のセットアップ処理"""
    _add_mega_stones(ITEMS)

    for name, data in ITEMS.items():
        ITEMS[name].name = name


def _add_mega_stones(items: dict[str, ItemData]):
    """メガストーンをITEMS辞書に追加する。"""
    for name, forms in MEGA_STONES.items():
        items[name] = ItemData(
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
        fling_power=10,
        handlers={
            Event.ON_VOLATILE_START: h.ItemHandler(
                h.あかいいと_infatuate_foe,
                subject_spec="source:self",
            )
        }
    ),
    "あついいわ": ItemData(
        fling_power=60,
        handlers={
            Event.ON_MODIFY_DURATION: h.ItemHandler(
                h.あついいわ_resolve_field_count,
                subject_spec="source:self",
            )
        }
    ),
    "あつぞこブーツ": ItemData(
        fling_power=80,
        handlers={
            Event.ON_CHECK_HAZARD_IMMUNE: h.ItemHandler(
                h.あつぞこブーツ_check_hazard_immune,
                subject_spec="source:self",
            )
        }
    ),
    "いかさまダイス": ItemData(
        fling_power=30,
        handlers={
            Event.ON_MODIFY_HIT_COUNT: h.ItemHandler(
                h.いかさまダイス_modify_hit_count,
                subject_spec="attacker:self",
            )
        }
    ),
    "いしずえのめん": ItemData(
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
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.ItemHandler(
                h.いのちのたま_boost_atk,
                subject_spec="attacker:self",
            ),
            Event.ON_HIT: h.ItemHandler(
                h.いのちのたま_recoil,
                subject_spec="attacker:self",
            )
        }
    ),
    "エレキシード": ItemData(
        fling_power=10,
        handlers={
            Event.ON_SWITCH_IN: h.ItemHandler(
                h.エレキシード_boost_defense,
                subject_spec="source:self",
            ),
            Event.ON_FIELD_CHANGE: h.ItemHandler(
                h.エレキシード_boost_defense,
                subject_spec="source:self",
            ),
            Event.ON_ITEM_ENABLED: h.ItemHandler(
                h.エレキシード_boost_defense,
                subject_spec="source:self",
            ),
        }
    ),
    "おうじゃのしるし": ItemData(
        fling_power=30,
        handlers={
            Event.ON_DAMAGE_HIT: h.ItemHandler(
                h.flinch_on_hit_10pct,
                subject_spec="attacker:self",
            )
        }
    ),
    "おおきなねっこ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_CALC_DRAIN: h.ItemHandler(
                h.おおきなねっこ_boost_drain,
                subject_spec="attacker:self",
            )
        }
    ),
    "おんみつマント": ItemData(
        fling_power=30,
        handlers={
            Event.ON_MODIFY_SECONDARY_CHANCE: h.ItemHandler(
                h.おんみつマント_negate_secondary,
                subject_spec="defender:self",
            )
        }
    ),
    "かいがらのすず": ItemData(
        fling_power=30,
        handlers={
            Event.ON_DAMAGE_HIT: h.ItemHandler(
                h.かいがらのすず_drain_on_hit,
                subject_spec="attacker:self",
            )
        }
    ),
    "かえんだま": ItemData(
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
        fling_power=100,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.かたいいし_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "かまどのめん": ItemData(
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
        fling_power=80,
        handlers={
            Event.ON_MISS: h.ItemHandler(
                h.からぶりほけん_boost_speed_on_miss,
                subject_spec="attacker:self",
            )
        }
    ),
    "かるいし": ItemData(
        fling_power=30,
    ),
    "きあいのタスキ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_MODIFY_MOVE_DAMAGE: h.ItemHandler(
                h.きあいのタスキ_survive_ohko,
                subject_spec="defender:self",
            )
        }
    ),
    "きあいのハチマキ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_MODIFY_MOVE_DAMAGE: h.ItemHandler(
                h.きあいのハチマキ_survive_by_chance,
                subject_spec="defender:self",
            )
        }
    ),
    "きせきのたね": ItemData(
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.きせきのたね_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "きゅうこん": ItemData(
        fling_power=30,
        handlers={
            Event.ON_DAMAGE_HIT: h.ItemHandler(
                h.きゅうこん_boost_spatk_on_water_hit,
                subject_spec="defender:self",
            )
        }
    ),
    "きれいなぬけがら": ItemData(
        fling_power=10,
        handlers={
            Event.ON_CHECK_TRAPPED: h.ItemHandler(
                h.きれいなぬけがら_check_trapped,
                subject_spec="source:self",
                priority=-100,
            )
        }
    ),
    "ぎんのこな": ItemData(
        fling_power=10,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.ぎんのこな_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "くっつきバリ": ItemData(
        fling_power=80,
        handlers={
            Event.ON_TURN_END: h.ItemHandler(
                h.くっつきバリ_damage_on_turn_end,
                subject_spec="source:self",
                priority=150,
            ),
            Event.ON_DAMAGE_HIT: h.ItemHandler(
                h.くっつきバリ_transfer_on_contact,
                subject_spec="defender:self",
            ),
        }
    ),
    "グラスシード": ItemData(
        fling_power=10,
        handlers={
            Event.ON_SWITCH_IN: h.ItemHandler(
                h.グラスシード_boost_defense,
                subject_spec="source:self",
            ),
            Event.ON_FIELD_CHANGE: h.ItemHandler(
                h.グラスシード_boost_defense,
                subject_spec="source:self",
            ),
            Event.ON_ITEM_ENABLED: h.ItemHandler(
                h.グラスシード_boost_defense,
                subject_spec="source:self",
            ),
        }
    ),
    "グランドコート": ItemData(
        fling_power=60,
        handlers={
            Event.ON_MODIFY_DURATION: h.ItemHandler(
                h.グランドコート_resolve_field_count,
                subject_spec="source:self",
            ),
        }
    ),
    "クリアチャーム": ItemData(
        fling_power=30,
        handlers={
            Event.ON_BEFORE_MODIFY_STAT: h.ItemHandler(
                h.クリアチャーム_block_stat_drop,
                subject_spec="target:self",
            )
        }
    ),
    "くろいてっきゅう": ItemData(
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
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.くろいメガネ_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "くろおび": ItemData(
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.くろおび_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "こうかくレンズ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_MODIFY_ACCURACY: h.ItemHandler(
                h.こうかくレンズ_modify_accuracy,
                subject_spec="attacker:self",
            )
        }
    ),
    "こうこうのしっぽ": ItemData(
        fling_power=10,
        handlers={
            DomainEvent.ON_CALC_BACK_TIER: h.ItemHandler(
                h.こうこうのしっぽ_back_tier,
                subject_spec="attacker:self",
            )
        }
    ),
    "こころのしずく": ItemData(
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.こころのしずく_modify_power,
                subject_spec="attacker:self",
            )
        }
    ),
    "こだわりスカーフ": ItemData(
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
        fling_power=60,
        handlers={
            Event.ON_DAMAGE_HIT: h.ItemHandler(
                h.ゴツゴツメット_chip_contact_attacker,
                subject_spec="defender:self",
            )
        }
    ),
    "サイコシード": ItemData(
        fling_power=10,
        handlers={
            Event.ON_SWITCH_IN: h.ItemHandler(
                h.サイコシード_boost_spdef,
                subject_spec="source:self",
            ),
            Event.ON_FIELD_CHANGE: h.ItemHandler(
                h.サイコシード_boost_spdef,
                subject_spec="source:self",
            ),
            Event.ON_ITEM_ENABLED: h.ItemHandler(
                h.サイコシード_boost_spdef,
                subject_spec="source:self",
            ),
        }
    ),
    "さらさらいわ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_MODIFY_DURATION: h.ItemHandler(
                h.さらさらいわ_resolve_field_count,
                subject_spec="source:self",
            )
        }
    ),
    "じしゃく": ItemData(
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.じしゃく_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "しめつけバンド": ItemData(
        fling_power=30,
        handlers={
            Event.ON_MODIFY_BIND_DAMAGE: h.ItemHandler(
                h.しめつけバンド_boost_bind_damage,
                subject_spec="source:foe",
            )
        }
    ),
    "しめったいわ": ItemData(
        fling_power=60,
        handlers={
            Event.ON_MODIFY_DURATION: h.ItemHandler(
                h.しめったいわ_resolve_field_count,
                subject_spec="source:self",
            )
        }
    ),
    "じゃくてんほけん": ItemData(
        fling_power=80,
        handlers={
            Event.ON_DAMAGE_HIT: h.ItemHandler(
                h.じゃくてんほけん_boost_on_super_effective,
                subject_spec="defender:self",
            )
        }
    ),
    "じゅうでんち": ItemData(
        fling_power=30,
        handlers={
            Event.ON_DAMAGE_HIT: h.ItemHandler(
                h.じゅうでんち_boost_atk_on_electric_hit,
                subject_spec="defender:self",
            )
        }
    ),
    "シルクのスカーフ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.シルクのスカーフ_modify_power_by_type,
                subject_spec="attacker:self",
            )
        },
    ),
    "しろいハーブ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_MODIFY_STAT: h.ItemHandler(
                h.しろいハーブ_cancel_stat_drop,
                subject_spec="target:self",
            ),
        }
    ),
    "しんかのきせき": ItemData(
        fling_power=40,
        handlers={
            Event.ON_CALC_DEF_MODIFIER: h.ItemHandler(
                h.しんかのきせき_boost_defenses,
                subject_spec="defender:self",
            ),
        }
    ),
    "しんぴのしずく": ItemData(
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.しんぴのしずく_modify_power_by_type,
                subject_spec="attacker:self",
            )
        },
    ),
    "するどいキバ": ItemData(
        fling_power=30,
        handlers={
            Event.ON_DAMAGE_HIT: h.ItemHandler(
                h.flinch_on_hit_10pct,
                subject_spec="attacker:self",
            )
        }
    ),
    "するどいくちばし": ItemData(
        fling_power=50,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.するどいくちばし_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "するどいツメ": ItemData(
        fling_power=80,
        handlers={
            Event.ON_CALC_CRITICAL_RANK: h.ItemHandler(
                h.するどいツメ_boost_critical_rank,
                subject_spec="attacker:self",
            )
        }
    ),
    "せいれいプレート": ItemData(
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.せいれいプレート_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "フェアリーメモリ": ItemData(
        fling_power=50,
    ),
    "せんせいのツメ": ItemData(
        fling_power=80,
        handlers={
            DomainEvent.ON_CALC_BACK_TIER: h.ItemHandler(
                h.せんせいのツメ_priority_boost,
                subject_spec="attacker:self",
            )
        }
    ),
    "だっしゅつパック": ItemData(
        fling_power=50,
        handlers={
            Event.ON_MODIFY_STAT: h.ItemHandler(
                h.だっしゅつパック_reserve_switch,
                subject_spec="target:self",
            )
        }
    ),
    "だっしゅつボタン": ItemData(
        fling_power=30,
        handlers={
            Event.ON_DAMAGE_HIT: h.ItemHandler(
                h.だっしゅつボタン_reserve_switch,
                subject_spec="defender:self",
            )
        }
    ),
    "たつじんのおび": ItemData(
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
            ),
        },
        lethal_handler=LethalHandler(
            func=l.たべのこし_heal_hp,
            target="defender",
            priority=60
        )
    ),
    "ちからのハチマキ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.ちからのハチマキ_boost_physical,
                subject_spec="attacker:self",
            )
        }
    ),
    "つめたいいわ": ItemData(
        fling_power=40,
        handlers={
            Event.ON_MODIFY_DURATION: h.ItemHandler(
                h.つめたいいわ_resolve_field_count,
                subject_spec="source:self",
            )
        }
    ),
    "でかいきんのたま": ItemData(
        fling_power=130,
        handlers={}  # 効果なし
    ),
    "でんきだま": ItemData(
        fling_power=30,
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.ItemHandler(
                h.でんきだま_boost_atk,
                subject_spec="attacker:self",
            )
        }
    ),
    "とくせいガード": ItemData(
        fling_power=30,
        handlers={
            Event.ON_CHECK_ABILITY_DISABLE: h.ItemHandler(
                h.とくせいガード_check_ability_disable,
                subject_spec="source:self",
                priority=200,
            ),
        }
    ),
    "どくどくだま": ItemData(
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
        fling_power=70,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.どくバリ_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "とけないこおり": ItemData(
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.とけないこおり_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "とつげきチョッキ": ItemData(
        fling_power=80,
        handlers={
            Event.ON_MODIFY_COMMAND_OPTIONS: h.ItemHandler(
                h.とつげきチョッキ_modify_command_options,
                subject_spec="source:self",
            ),
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
        fling_power=90,
        handlers={
            Event.ON_MODIFY_DURATION: h.ItemHandler(
                h.ねばりのかぎづめ_fix_bind_duration,
                subject_spec="attacker:self",
            )
        }
    ),
    "ねらいのまと": ItemData(
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
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.ノーマルジュエル_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "のどスプレー": ItemData(
        fling_power=30,
        handlers={
            Event.ON_MOVE_END: h.ItemHandler(
                h.のどスプレー_boost_spatk_on_sound,
                subject_spec="attacker:self",
            )
        }
    ),
    "のろいのおふだ": ItemData(
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.のろいのおふだ_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "パワフルハーブ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_MOVE_CHARGE: h.ItemHandler(
                h.パワフルハーブ_skip_charge,
                subject_spec="attacker:self",
            )
        }
    ),
    "パンチグローブ": ItemData(
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
        fling_power=60
        # 効果: 持たせたポケモンはにほんばれ・あめ状態の影響を受けなくなる。
        # 実装方法: battle.weather_for(mon) を用いて各ハンドラ内で個別判定する。
        # 未実装技のばんのうがさ対応: ウェザーボール・エレクトロビーム・ハイドロスチーム
    ),
    "ひかりごけ": ItemData(
        fling_power=30,
        handlers={
            Event.ON_DAMAGE_HIT: h.ItemHandler(
                h.ひかりごけ_boost_spdef_on_water_hit,
                subject_spec="defender:self",
            )
        }
    ),
    "ひかりのこな": ItemData(
        fling_power=10,
        handlers={
            Event.ON_MODIFY_ACCURACY: h.ItemHandler(
                h.ひかりのこな_reduce_accuracy,
                subject_spec="defender:self",
            )
        }
    ),
    "ひかりのねんど": ItemData(
        fling_power=30,
        handlers={
            Event.ON_MODIFY_DURATION: h.ItemHandler(
                h.ひかりのねんど_resolve_field_count,
                subject_spec="source:self",
            ),
        }
    ),
    "ビビリだま": ItemData(
        fling_power=30,
        handlers={
            Event.ON_MODIFY_STAT: h.ItemHandler(
                h.ビビリだま_boost_speed_on_intimidate,
                subject_spec="target:self",
            )
        }
    ),
    "ピントレンズ": ItemData(
        fling_power=30,
        handlers={
            Event.ON_CALC_CRITICAL_RANK: h.ItemHandler(
                h.ピントレンズ_boost_critical_rank,
                subject_spec="attacker:self",
            )
        }
    ),
    "ブーストエナジー": ItemData(
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
        fling_power=10,
        handlers={
            Event.ON_MODIFY_ACCURACY: h.ItemHandler(
                h.フォーカスレンズ_boost_accuracy_second,
                subject_spec="attacker:self",
            )
        }
    ),
    "ぼうごパット": ItemData(
        fling_power=30,
        handlers={
            Event.ON_CHECK_CONTACT: h.ItemHandler(
                h.ぼうごパット_negate_contact,
                subject_spec="attacker:self",
            )
        }
    ),
    "ぼうじんゴーグル": ItemData(
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
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.まがったスプーン_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "ミストシード": ItemData(
        fling_power=10,
        handlers={
            Event.ON_SWITCH_IN: h.ItemHandler(
                h.ミストシード_boost_spdef,
                subject_spec="source:self",
            ),
            Event.ON_FIELD_CHANGE: h.ItemHandler(
                h.ミストシード_boost_spdef,
                subject_spec="source:self",
            ),
            Event.ON_ITEM_ENABLED: h.ItemHandler(
                h.ミストシード_boost_spdef,
                subject_spec="source:self",
            ),
        }
    ),
    "メタルコート": ItemData(
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.メタルコート_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "メトロノーム": ItemData(
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
        fling_power=10,
        handlers={
            Event.ON_VOLATILE_START: h.ItemHandler(
                h.メンタルハーブ_cure_mental_volatile,
                subject_spec="source:self",
            )
        }
    ),
    "もくたん": ItemData(
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.もくたん_modify_power_by_type,
                subject_spec="attacker:self",
            )
        },
    ),
    "ものしりメガネ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.ものしりメガネ_boost_special,
                subject_spec="attacker:self",
            )
        }
    ),
    "ものまねハーブ": ItemData(
        fling_power=30,
        handlers={
            Event.ON_MODIFY_STAT: h.ItemHandler(
                h.ものまねハーブ_copy_stat_boost,
                subject_spec="target:foe",
            )
        }
    ),
    "やわらかいすな": ItemData(
        fling_power=10,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.やわらかいすな_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "ゆきだま": ItemData(
        fling_power=30,
        handlers={
            Event.ON_DAMAGE_HIT: h.ItemHandler(
                h.ゆきだま_boost_defense_on_ice_hit,
                subject_spec="defender:self",
            )
        }
    ),
    "ようせいのハネ": ItemData(
        fling_power=20,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.ようせいのハネ_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "りゅうのキバ": ItemData(
        fling_power=70,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.りゅうのキバ_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "ルームサービス": ItemData(
        fling_power=100,
        handlers={
            Event.ON_FIELD_ACTIVATE: h.ItemHandler(
                h.ルームサービス_drop_speed_on_trick_room,
                subject_spec="source:self",
            )
        }
    ),
    "レッドカード": ItemData(
        fling_power=10,
        handlers={
            Event.ON_DAMAGE_HIT: h.ItemHandler(
                h.レッドカード_force_switch,
                subject_spec="defender:self",
            )
        }
    ),
    "くちたけん": ItemData(
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
        fling_power=10,
        handlers={
            Event.ON_HP_CHANGED: h.ItemHandler(
                h.オボンのみ_heal_on_half_hp,
                subject_spec="target:self",
            ),
        }
    ),
    "ラムのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_TURN_END: h.ItemHandler(
                h.ラムのみ_cure_ailment,
                subject_spec="source:self",
                priority=50,
            ),
            Event.ON_APPLY_AILMENT: h.ItemHandler(
                h.ラムのみ_cure_ailment_on_apply,
                subject_spec="target:self",
                priority=50,
            ),
            Event.ON_ITEM_ENABLED: h.ItemHandler(
                h.ラムのみ_cure_ailment,
                subject_spec="source:self",
                priority=50,
            ),
            Event.ON_FORCE_BERRY_TRIGGER: h.ItemHandler(
                h.ラムのみ_cure_ailment,
                subject_spec="source:self",
                priority=50,
            ),
        }
    ),
    "クラボのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_TURN_END: h.ItemHandler(
                h.クラボのみ_cure_paralysis,
                subject_spec="source:self",
                priority=50,
            ),
            Event.ON_APPLY_AILMENT: h.ItemHandler(
                h.クラボのみ_cure_paralysis_on_apply,
                subject_spec="target:self",
                priority=50,
            ),
            Event.ON_ITEM_ENABLED: h.ItemHandler(
                h.クラボのみ_cure_paralysis,
                subject_spec="source:self",
                priority=50,
            ),
            Event.ON_FORCE_BERRY_TRIGGER: h.ItemHandler(
                h.クラボのみ_cure_paralysis,
                subject_spec="source:self",
                priority=50,
            ),
        }
    ),
    "カゴのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_TURN_END: h.ItemHandler(
                h.カゴのみ_cure_sleep,
                subject_spec="source:self",
                priority=50,
            ),
            Event.ON_APPLY_AILMENT: h.ItemHandler(
                h.カゴのみ_cure_sleep_on_apply,
                subject_spec="target:self",
                priority=50,
            ),
            Event.ON_ITEM_ENABLED: h.ItemHandler(
                h.カゴのみ_cure_sleep,
                subject_spec="source:self",
                priority=50,
            ),
            Event.ON_FORCE_BERRY_TRIGGER: h.ItemHandler(
                h.カゴのみ_cure_sleep,
                subject_spec="source:self",
                priority=50,
            ),
        }
    ),
    "モモンのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_TURN_END: h.ItemHandler(
                h.モモンのみ_cure_poison,
                subject_spec="source:self",
                priority=50,
            ),
            Event.ON_APPLY_AILMENT: h.ItemHandler(
                h.モモンのみ_cure_poison_on_apply,
                subject_spec="target:self",
                priority=50,
            ),
            Event.ON_ITEM_ENABLED: h.ItemHandler(
                h.モモンのみ_cure_poison,
                subject_spec="source:self",
                priority=50,
            ),
            Event.ON_FORCE_BERRY_TRIGGER: h.ItemHandler(
                h.モモンのみ_cure_poison,
                subject_spec="source:self",
                priority=50,
            ),
        }
    ),
    "チーゴのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_TURN_END: h.ItemHandler(
                h.チーゴのみ_cure_burn,
                subject_spec="source:self",
                priority=50,
            ),
            Event.ON_APPLY_AILMENT: h.ItemHandler(
                h.チーゴのみ_cure_burn_on_apply,
                subject_spec="target:self",
                priority=50,
            ),
            Event.ON_ITEM_ENABLED: h.ItemHandler(
                h.チーゴのみ_cure_burn,
                subject_spec="source:self",
                priority=50,
            ),
            Event.ON_FORCE_BERRY_TRIGGER: h.ItemHandler(
                h.チーゴのみ_cure_burn,
                subject_spec="source:self",
                priority=50,
            ),
        }
    ),
    "ナナシのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_TURN_END: h.ItemHandler(
                h.ナナシのみ_cure_freeze,
                subject_spec="source:self",
                priority=50,
            ),
            Event.ON_APPLY_AILMENT: h.ItemHandler(
                h.ナナシのみ_cure_freeze_on_apply,
                subject_spec="target:self",
                priority=50,
            ),
            Event.ON_ITEM_ENABLED: h.ItemHandler(
                h.ナナシのみ_cure_freeze,
                subject_spec="source:self",
                priority=50,
            ),
            Event.ON_FORCE_BERRY_TRIGGER: h.ItemHandler(
                h.ナナシのみ_cure_freeze,
                subject_spec="source:self",
                priority=50,
            ),
        }
    ),
    "キーのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_TURN_END: h.ItemHandler(
                h.キーのみ_cure_confusion,
                subject_spec="source:self",
                priority=50,
            ),
            Event.ON_FORCE_BERRY_TRIGGER: h.ItemHandler(
                h.キーのみ_cure_confusion,
                subject_spec="source:self",
                priority=50,
            ),
        }
    ),
    "ヒメリのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_PP_CONSUMED: h.ItemHandler(
                h.ヒメリのみ_restore_pp,
                subject_spec="attacker:self",
            )
        }
    ),
    "オレンのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_HP_CHANGED: h.ItemHandler(
                h.オレンのみ_heal_on_half_hp,
                subject_spec="target:self",
            ),
        }
    ),
    "フィラのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_HP_CHANGED: h.ItemHandler(
                h.heal_on_quarter_hp,
                subject_spec="target:self",
            )
        }
    ),
    "ウイのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_HP_CHANGED: h.ItemHandler(
                h.heal_on_quarter_hp,
                subject_spec="target:self",
            )
        }
    ),
    "マゴのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_HP_CHANGED: h.ItemHandler(
                h.heal_on_quarter_hp,
                subject_spec="target:self",
            )
        }
    ),
    "バンジのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_HP_CHANGED: h.ItemHandler(
                h.heal_on_quarter_hp,
                subject_spec="target:self",
            )
        }
    ),
    "イアのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_HP_CHANGED: h.ItemHandler(
                h.heal_on_quarter_hp,
                subject_spec="target:self",
            )
        }
    ),
    "チイラのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_HP_CHANGED: h.ItemHandler(
                h.チイラのみ_boost_attack,
                subject_spec="target:self",
            )
        }
    ),
    "リュガのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_HP_CHANGED: h.ItemHandler(
                h.リュガのみ_boost_defense,
                subject_spec="target:self",
            )
        }
    ),
    "ヤタピのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_HP_CHANGED: h.ItemHandler(
                h.ヤタピのみ_boost_spatk,
                subject_spec="target:self",
            )
        }
    ),
    "ズアのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_HP_CHANGED: h.ItemHandler(
                h.ズアのみ_boost_spdef,
                subject_spec="target:self",
            )
        }
    ),
    "カムラのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_HP_CHANGED: h.ItemHandler(
                h.カムラのみ_boost_speed,
                subject_spec="target:self",
            )
        }
    ),
    "スターのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_HP_CHANGED: h.ItemHandler(
                h.スターのみ_random_boost,
                subject_spec="target:self",
            )
        }
    ),
    "サンのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_HP_CHANGED: h.ItemHandler(
                h.サンのみ_apply_focus_energy,
                subject_spec="target:self",
            )
        }
    ),
    "ホズのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.ホズのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "リンドのみ": ItemData(
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
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.オッカのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "イトケのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.イトケのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "ソクノのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.ソクノのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "カシブのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.カシブのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "ヨロギのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.ヨロギのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "タンガのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.タンガのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "ウタンのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.ウタンのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "バコウのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.バコウのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "シュカのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.シュカのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "ビアーのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.ビアーのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "ヨプのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.ヨプのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "ヤチェのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.ヤチェのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "リリバのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.リリバのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "ナモのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.ナモのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "ハバンのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.ハバンのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "ロゼルのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.ロゼルのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        }
    ),
    "アッキのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_DAMAGE_HIT: h.ItemHandler(
                h.アッキのみ_boost_defense_on_physical_hit,
                subject_spec="defender:self",
            )
        }
    ),
    "タラプのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_DAMAGE_HIT: h.ItemHandler(
                h.タラプのみ_boost_spdef,
                subject_spec="defender:self",
            )
        }
    ),
    "イバンのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_HP_CHANGED: h.ItemHandler(
                h.イバンのみ_set_priority_flag,
                subject_spec="target:self",
            ),
            DomainEvent.ON_CALC_BACK_TIER: h.ItemHandler(
                h.イバンのみ_boost_priority,
                subject_spec="attacker:self",
            ),
        }
    ),
    "ジャポのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_DAMAGE_HIT: h.ItemHandler(
                h.ジャポのみ_retaliate_physical,
                subject_spec="defender:self",
            )
        }
    ),
    "レンブのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_DAMAGE_HIT: h.ItemHandler(
                h.レンブのみ_retaliate_special,
                subject_spec="defender:self",
            )
        }
    ),
    "ナゾのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_DAMAGE_HIT: h.ItemHandler(
                h.ナゾのみ_heal_on_super_effective,
                subject_spec="defender:self",
            )
        }
    ),
    "ミクルのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_HP_CHANGED: h.ItemHandler(
                h.ミクルのみ_set_accuracy_flag,
                subject_spec="target:self",
                priority=100,
            ),
            Event.ON_MODIFY_ACCURACY: h.ItemHandler(
                h.ミクルのみ_boost_accuracy,
                subject_spec="attacker:self",
                priority=100,
            ),
        }
    ),
}

common_setup()
