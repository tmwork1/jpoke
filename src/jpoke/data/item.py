"""アイテムデータ定義モジュール。

Note:
    このモジュール内のアイテム定義はITEMS辞書内で五十音順に配置されています。
"""
import csv
from importlib import resources

from jpoke.enums import Event, DomainEvent, LethalEvent
from jpoke.core.lethal import LethalHandler
from jpoke.handlers import item as h, lethal as l
from jpoke.data.models import ItemData
from jpoke.types import ItemName, Regulation

from .megaevol import MEGA_STONES


def _load_item_regulations() -> dict[ItemName, set[Regulation]]:
    """regulation/item.csv からアイテムごとの使用可能レギュレーションを読み込む。"""
    regulation_path = resources.files("jpoke").joinpath("data", "regulation", "item.csv")
    regulations_by_item = {}

    with regulation_path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames is not None, "regulation/item.csv のヘッダが読み取れません"
        regulation_names = [
            name
            for name in reader.fieldnames
            if name not in {"name", "implemented"}
        ]

        for row in reader:
            if row["implemented"] != "1":
                continue

            regulations_by_item[row["name"]] = {
                regulation
                for regulation in regulation_names
                if row[regulation] == "1"
            }

    return regulations_by_item


def common_setup():
    """共通のセットアップ処理"""
    _add_mega_stones(ITEMS)
    item_regulations = _load_item_regulations()

    for name in item_regulations:
        assert name in ITEMS, f"regulation/item.csv に未定義のアイテム名があります: {name}"

    for name in ITEMS:
        ITEMS[name].name = name
        ITEMS[name].regulations = set(item_regulations.get(name, set()))


def _add_mega_stones(items: dict[ItemName, ItemData]):
    """メガストーンをITEMS辞書に追加する。"""
    for name, forms in MEGA_STONES.items():
        items[name] = ItemData(
            removable=False,
            fling_power=80,
            mega_evolve=forms,
            handlers={
                Event.ON_MODIFY_COMMAND_OPTIONS: h.ItemHandler(
                    h.mega_modify_command_options,
                    subject_spec="source:self"
                ),
                Event.ON_CHECK_ITEM_CHANGE: h.ItemHandler(
                    h.mega_prevent_item_change,
                    subject_spec="target:self",
                ),
            }
        )


ITEMS: dict[ItemName, ItemData] = {
    "": ItemData(name=""),
    "アイスメモリ": ItemData(
        fling_power=50,
    ),
    "あおぞらプレート": ItemData(
        fling_power=90,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.あおぞらプレート_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "あかいいと": ItemData(
        fling_power=10,
        handlers={
            Event.ON_VOLATILE_START: h.ItemHandler(
                h.あかいいと_infatuate_foe,
                subject_spec="source:self",
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
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(
                func=l.アッキのみ_boost_def,
                subject="defender",
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
    "イアのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_HP_CHANGED: h.ItemHandler(
                h.イアのみ_heal_on_quarter_hp,
                subject_spec="target:self",
            )
        },
        lethal_handlers={
            LethalEvent.ON_EVERY_EVENT: LethalHandler(
                func=l.イアのみ_heal,
                subject="defender",
            )
        }
    ),
    "いかさまダイス": ItemData(
        fling_power=30,
        handlers={
            Event.ON_MODIFY_HIT_COUNT: h.ItemHandler(
                h.いかさまダイス_modify_hit_count,
                subject_spec="attacker:self",
                priority=90,  # スキルリンク等の特性側ハンドラ(priority=100)より先に発動し、後勝ちの上書きで特性側を優先させる
            ),
            Event.ON_MODIFY_HIT_CHECK_EACH_TIME: h.ItemHandler(
                h.いかさまダイス_modify_hit_check_each_time,
                subject_spec="attacker:self",
            ),
        }
    ),
    "いかずちプレート": ItemData(
        fling_power=90,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.いかずちプレート_modify_power_by_type,
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
            ),
            Event.ON_CHECK_ITEM_CHANGE: h.ItemHandler(
                h.オーガポンのめん_prevent_item_change,
                subject_spec="target:self",
            ),
        }
    ),
    "イトケのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.イトケのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        },
        lethal_handlers={
            LethalEvent.ON_BEFORE_HIT: LethalHandler(
                func=l.イトケのみ_resist_water,
                subject="defender",
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
            ),
            Event.ON_CHECK_ITEM_CHANGE: h.ItemHandler(
                h.オーガポンのめん_prevent_item_change,
                subject_spec="target:self",
            ),
        }
    ),
    "いのちのたま": ItemData(
        fling_power=30,
        handlers={
            Event.ON_CALC_ATK_MODIFIER: h.ItemHandler(
                h.いのちのたま_boost_atk,
                subject_spec="attacker:self",
            ),
            # turn.md では「いのちのたまの反動」は priority=160 で Event.ON_DAMAGE
            # （実装上の Event.ON_DAMAGE_HIT に相当）に掲載されているが、
            # ON_DAMAGE_HIT は actual_damage<=0 のとき発火しないため採用しない。
            # 0ダメージ時（HP1相手へのみねうち等）も反動が発生する仕様
            # （.internal/spec/items/いのちのたま.md 詳細な仕様）を満たすため、
            # 常に発火する Event.ON_HIT を使用し、priority のみ turn.md の値に合わせる。
            Event.ON_HIT: h.ItemHandler(
                h.いのちのたま_recoil,
                subject_spec="attacker:self",
                priority=160,
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
    "ウイのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_HP_CHANGED: h.ItemHandler(
                h.ウイのみ_heal_on_quarter_hp,
                subject_spec="target:self",
            )
        },
        lethal_handlers={
            LethalEvent.ON_EVERY_EVENT: LethalHandler(
                func=l.ウイのみ_heal,
                subject="defender",
            )
        }
    ),
    "ウォーターメモリ": ItemData(
        fling_power=50,
    ),
    "ウタンのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.ウタンのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        },
        lethal_handlers={
            LethalEvent.ON_BEFORE_HIT: LethalHandler(
                func=l.ウタンのみ_resist_psychic,
                subject="defender",
            )
        }
    ),
    "エレキシード": ItemData(
        fling_power=10,
        handlers={
            Event.ON_SWITCH_IN: h.ItemHandler(
                h.エレキシード_boost_defense,
                subject_spec="source:self",
                priority=120,  # .internal/spec/turn.md ON_SWITCH_IN: 「120 エレキシードの発動」
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
    "エレクトロメモリ": ItemData(
        fling_power=50,
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
                subject_spec="source:self",
            ),
        }
    ),
    "オッカのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.オッカのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        },
        lethal_handlers={
            LethalEvent.ON_BEFORE_HIT: LethalHandler(
                func=l.オッカのみ_resist_fire,
                subject="defender",
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
        },
        lethal_handlers={
            LethalEvent.ON_EVERY_EVENT: LethalHandler(
                func=l.オボンのみ_heal,
                subject="defender",
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
        },
        lethal_handlers={
            LethalEvent.ON_EVERY_EVENT: LethalHandler(
                func=l.オレンのみ_heal,
                subject="defender",
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
            # turn.md では「かいがらのすずの回復」は priority=160 で Event.ON_DAMAGE
            # （実装上の Event.ON_DAMAGE_HIT に相当）に掲載されているが、
            # ON_DAMAGE_HIT はみがわりに阻まれた場合（実HPダメージ0）に発火しないため採用しない。
            # 第五世代以降はみがわりへの与ダメージでも回復する仕様
            # （.internal/spec/items/かいがらのすず.md 詳細な仕様）を満たすため、
            # 常に発火する Event.ON_HIT を使用し、priority のみ turn.md の値に合わせる。
            Event.ON_HIT: h.ItemHandler(
                h.かいがらのすず_drain_on_hit,
                subject_spec="attacker:self",
                priority=160,
            )
        }
    ),
    "かえんだま": ItemData(
        fling_power=30,
        handlers={
            Event.ON_TURN_END: h.ItemHandler(
                h.かえんだま_apply_burn,
                subject_spec="source:self",
                priority=150,
            )
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
    "カシブのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.カシブのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        },
        lethal_handlers={
            LethalEvent.ON_BEFORE_HIT: LethalHandler(
                func=l.カシブのみ_resist_ghost,
                subject="defender",
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
            ),
            Event.ON_CHECK_ITEM_CHANGE: h.ItemHandler(
                h.オーガポンのめん_prevent_item_change,
                subject_spec="target:self",
            ),
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
    "がんせきプレート": ItemData(
        fling_power=90,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.がんせきプレート_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "きあいのタスキ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_MODIFY_MOVE_DAMAGE: h.ItemHandler(
                h.きあいのタスキ_survive_ohko,
                subject_spec="defender:self",
            )
        },
        lethal_handlers={
            LethalEvent.ON_APPLY_DAMAGE: LethalHandler(
                l.きあいのタスキ_survive_ohko,
                subject="defender",
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
    "きせきのタネ": ItemData(
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.きせきのタネ_modify_power_by_type,
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
                # .internal/spec/abilities/マジシャン.md: 「じゅうでんち/ゆきだま/きゅうこん/ひかりごけ等の
                # 効果が発動する場合、マジシャンで奪う前に発動する」。マジシャン特性ハンドラ(priority=100)
                # より確実に先に発動させるため、素早さに依存しないpriority=90を指定する。
                priority=90,
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
    "キーのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_TURN_END: h.ItemHandler(
                h.キーのみ_cure_confusion,
                subject_spec="source:self",
                priority=50,
            ),
            Event.ON_VOLATILE_START: h.ItemHandler(
                h.キーのみ_cure_confusion,
                subject_spec="source:self",
            ),
            Event.ON_ITEM_ENABLED: h.ItemHandler(
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
    "ぎんのこな": ItemData(
        fling_power=10,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.ぎんのこな_modify_power_by_type,
                subject_spec="attacker:self",
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
            Event.ON_CHECK_ITEM_CHANGE: [
                h.ItemHandler(
                    h.くちたけん_prevent_item_change,
                    subject_spec="target:self",
                ),
                h.ItemHandler(
                    h.くちたけん_prevent_transfer_to_hero,
                    subject_spec="target:foe",
                ),
            ],
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
            Event.ON_CHECK_ITEM_CHANGE: [
                h.ItemHandler(
                    h.くちたたて_prevent_item_change,
                    subject_spec="target:self",
                ),
                h.ItemHandler(
                    h.くちたたて_prevent_transfer_to_hero,
                    subject_spec="target:foe",
                ),
            ],
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
                priority=30,  # .internal/spec/turn.md ON_DAMAGE: 「30 くっつきバリが攻撃側に渡る」
                # 所持者がひんしになった場合も攻撃した相手にくっつく仕様
                # （.internal/spec/items/くっつきバリ.md）のため、瀕死主体でも発動を許可する。
                allow_fainted_subject=True,
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
                priority=60,
            )
        },
        lethal_handlers={
            LethalEvent.ON_TURN_END: LethalHandler(
                func=l.くろいヘドロ_recover_or_damage,
                subject="defender",
                priority=60,
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
    "グラウンドメモリ": ItemData(
        fling_power=50,
    ),
    "グラスシード": ItemData(
        fling_power=10,
        handlers={
            Event.ON_SWITCH_IN: h.ItemHandler(
                h.グラスシード_boost_defense,
                subject_spec="source:self",
                priority=120,  # .internal/spec/turn.md ON_SWITCH_IN: 「120 グラスシードの発動」
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
    "グラスメモリ": ItemData(
        fling_power=50,
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
    "こうてつのプレート": ItemData(
        fling_power=90,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.こうてつのプレート_modify_power_by_type,
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
            Event.ON_PP_CONSUMED: h.ItemHandler(
                h.こだわり_lock_move,
                subject_spec="attacker:self",
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
            Event.ON_PP_CONSUMED: h.ItemHandler(
                h.こだわり_lock_move,
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
            Event.ON_PP_CONSUMED: h.ItemHandler(
                h.こだわり_lock_move,
                subject_spec="attacker:self",
            ),
            Event.ON_MOVE_END: h.ItemHandler(
                h.こだわり_lock_move,
                subject_spec="attacker:self",
            ),
        }
    ),
    "こぶしのプレート": ItemData(
        fling_power=90,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.こぶしのプレート_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "こわもてプレート": ItemData(
        fling_power=90,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.こわもてプレート_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "こんごうだま": ItemData(
        fling_power=60,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.こんごうだま_modify_power,
                subject_spec="attacker:self",
            )
        }
    ),
    "ゴツゴツメット": ItemData(
        fling_power=60,
        handlers={
            Event.ON_DAMAGE_HIT: h.ItemHandler(
                h.ゴツゴツメット_chip_contact_attacker,
                subject_spec="defender:self",
                # .internal/spec/abilities/マジシャン.md: 「きあいのハチマキ/きあいのタスキ/ゴツゴツメット/
                # じゃくてんほけん/じゅうでんち/ゆきだま/きゅうこん/ひかりごけ/ふうせんの効果が発動する場合、
                # マジシャンで奪う前に発動する」。マジシャン特性ハンドラ(priority=100)より確実に先に
                # 発動させるため、素早さに依存しないpriority=90を指定する。
                priority=90,
                # ゴツゴツメットを持つポケモンがひんしになったときも発動する仕様
                # （.internal/spec/items/ゴツゴツメット.md）のため、瀕死主体でも発動を許可する。
                allow_fainted_subject=True,
            )
        }
    ),
    "ゴーストメモリ": ItemData(
        fling_power=50,
    ),
    "サイキックメモリ": ItemData(
        fling_power=50,
    ),
    "サイコシード": ItemData(
        fling_power=10,
        handlers={
            Event.ON_SWITCH_IN: h.ItemHandler(
                h.サイコシード_boost_spdef,
                subject_spec="source:self",
                priority=120,  # .internal/spec/turn.md ON_SWITCH_IN: 「120 サイコシードの発動」
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
    "サンのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_HP_CHANGED: h.ItemHandler(
                h.サンのみ_apply_focus_energy,
                subject_spec="target:self",
            )
        }
    ),
    "しずくプレート": ItemData(
        fling_power=90,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.しずくプレート_modify_power_by_type,
                subject_spec="attacker:self",
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
    "しめつけバンド": ItemData(
        fling_power=30,
        handlers={
            Event.ON_MODIFY_BIND_DAMAGE: h.ItemHandler(
                h.しめつけバンド_boost_bind_damage,
                subject_spec="attacker:self",
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
        },
        lethal_handlers={
            LethalEvent.ON_BEFORE_HIT: LethalHandler(
                func=l.シュカのみ_resist_ground,
                subject="defender",
            )
        }
    ),
    "しらたま": ItemData(
        fling_power=60,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.しらたま_modify_power,
                subject_spec="attacker:self",
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
            Event.ON_SWITCH_IN: h.ItemHandler(
                h.しろいハーブ_reset_if_already_lowered,
                subject_spec="source:self",
                priority=160,  # .internal/spec/turn.md ON_SWITCH_IN: 「160 しろいハーブの発動」
            ),
            Event.ON_ITEM_GAINED: h.ItemHandler(
                h.しろいハーブ_reset_if_already_lowered,
                subject_spec="source:self",
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
    "じしゃく": ItemData(
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.じしゃく_modify_power_by_type,
                subject_spec="attacker:self",
            )
        },
    ),
    "じゃくてんほけん": ItemData(
        fling_power=80,
        handlers={
            Event.ON_DAMAGE_HIT: h.ItemHandler(
                h.じゃくてんほけん_boost_on_super_effective,
                subject_spec="defender:self",
                # .internal/spec/abilities/マジシャン.md: 「きあいのハチマキ/きあいのタスキ/ゴツゴツメット/
                # じゃくてんほけん/じゅうでんち/ゆきだま/きゅうこん/ひかりごけ/ふうせんの効果が発動する場合、
                # マジシャンで奪う前に発動する」。マジシャン特性ハンドラ(priority=100)より確実に先に
                # 発動させるため、素早さに依存しないpriority=90を指定する。
                priority=90,
            )
        }
    ),
    "ジャポのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_DAMAGE_HIT: h.ItemHandler(
                h.ジャポのみ_retaliate_physical,
                subject_spec="defender:self",
                # .internal/spec/abilities/マジシャン.md: 「弱点半減のきのみ/ナゾのみ/ジャポのみ/
                # レンブのみはマジシャンより先に発動する」。マジシャン特性ハンドラ(priority=100)
                # より確実に先に発動させるため、素早さに依存しないpriority=90を指定する。
                priority=90,
                # 所持者がひんしになったときでも発動する仕様
                # （.internal/spec/items/ジャポのみ.md）のため、瀕死主体でも発動を許可する。
                allow_fainted_subject=True,
            )
        }
    ),
    "じゅうでんち": ItemData(
        fling_power=30,
        handlers={
            Event.ON_DAMAGE_HIT: h.ItemHandler(
                h.じゅうでんち_boost_atk_on_electric_hit,
                subject_spec="defender:self",
                # .internal/spec/abilities/マジシャン.md: 「きあいのハチマキ/きあいのタスキ/ゴツゴツメット/
                # じゃくてんほけん/じゅうでんち/ゆきだま/きゅうこん/ひかりごけ/ふうせんの効果が発動する場合、
                # マジシャンで奪う前に発動する」。マジシャン特性ハンドラ(priority=100)より確実に先に
                # 発動させるため、素早さに依存しないpriority=90を指定する。
                priority=90,
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
    "スチールメモリ": ItemData(
        fling_power=50,
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
    "ズアのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_HP_CHANGED: h.ItemHandler(
                h.ズアのみ_boost_spdef,
                subject_spec="target:self",
            )
        }
    ),
    "せいれいプレート": ItemData(
        fling_power=90,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.せいれいプレート_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
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
    "ソクノのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.ソクノのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        },
        lethal_handlers={
            LethalEvent.ON_BEFORE_HIT: LethalHandler(
                func=l.ソクノのみ_resist_electric,
                subject="defender",
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
                h.たべのこし_heal,
                subject_spec="source:self",
                priority=60,
            ),
        },
        lethal_handlers={
            LethalEvent.ON_TURN_END: LethalHandler(
                func=l.たべのこし_heal,
                subject="defender",
                priority=60,
            )
        }
    ),
    "たまむしのプレート": ItemData(
        fling_power=90,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.たまむしのプレート_modify_power_by_type,
                subject_spec="attacker:self",
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
        },
        lethal_handlers={
            LethalEvent.ON_HIT: LethalHandler(
                func=l.タラプのみ_boost_spd,
                subject="defender",
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
        },
        lethal_handlers={
            LethalEvent.ON_BEFORE_HIT: LethalHandler(
                func=l.タンガのみ_resist_bug,
                subject="defender",
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
            Event.ON_CHECK_ITEM_CHANGE: [
                h.ItemHandler(
                    h.だいこんごうだま_prevent_item_change,
                    subject_spec="target:self",
                ),
                h.ItemHandler(
                    h.だいこんごうだま_prevent_transfer_to_base_form,
                    subject_spec="target:foe",
                ),
            ],
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
            Event.ON_CHECK_ITEM_CHANGE: [
                h.ItemHandler(
                    h.だいしらたま_prevent_item_change,
                    subject_spec="target:self",
                ),
                h.ItemHandler(
                    h.だいしらたま_prevent_transfer_to_base_form,
                    subject_spec="target:foe",
                ),
            ],
        }
    ),
    "だいちのプレート": ItemData(
        fling_power=90,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.だいちのプレート_modify_power_by_type,
                subject_spec="attacker:self",
            )
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
            Event.ON_CHECK_ITEM_CHANGE: [
                h.ItemHandler(
                    h.だいはっきんだま_prevent_item_change,
                    subject_spec="target:self",
                ),
                h.ItemHandler(
                    h.だいはっきんだま_prevent_transfer_to_base_form,
                    subject_spec="target:foe",
                ),
            ],
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
            # turn.md には「だっしゅつボタン」自体の priority 行はなく、Interrupt注記
            # （ON_DAMAGE 節の末尾）としてのみ言及されている。ON_DAMAGE_HIT は
            # actual_damage<=0 のとき発火しないため採用しない。ばけのかわ/アイスフェイスの
            # 肩代わりやこらえるでHP1のまま耐えたとき（実HPダメージ0）も発動する仕様
            # （.internal/spec/items/だっしゅつボタン.md 詳細な仕様）を満たすため、いのちのたま
            # と同様に常に発火する Event.ON_HIT を使用する（priority は既定値のまま）。
            Event.ON_HIT: h.ItemHandler(
                h.だっしゅつボタン_reserve_switch,
                subject_spec="defender:self",
            )
        }
    ),
    "ダークメモリ": ItemData(
        fling_power=50,
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
    "ちからのハチマキ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.ちからのハチマキ_boost_physical,
                subject_spec="attacker:self",
            )
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
    "つめたいいわ": ItemData(
        fling_power=40,
        handlers={
            Event.ON_MODIFY_DURATION: h.ItemHandler(
                h.つめたいいわ_resolve_field_count,
                subject_spec="source:self",
            )
        }
    ),
    "つららのプレート": ItemData(
        fling_power=90,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.つららのプレート_modify_power_by_type,
                subject_spec="attacker:self",
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
                # 所持者の特性がぶきようであっても道具の効果は発動する
                ignored_disable_reasons=frozenset({"ぶきよう"}),
            ),
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
            Event.ON_CALC_DEF_MODIFIER: h.ItemHandler(
                h.とつげきチョッキ_boost_spdef,
                subject_spec="defender:self",
            ),
        }
    ),
    "どくどくだま": ItemData(
        fling_power=30,
        handlers={
            Event.ON_TURN_END: h.ItemHandler(
                h.どくどくだま_apply_poison,
                subject_spec="source:self",
                priority=150,
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
    "ドラゴンメモリ": ItemData(
        fling_power=50,
    ),
    "ナゾのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_DAMAGE_HIT: h.ItemHandler(
                h.ナゾのみ_heal_on_super_effective,
                subject_spec="defender:self",
                # .internal/spec/abilities/マジシャン.md: 「弱点半減のきのみ/ナゾのみ/ジャポのみ/
                # レンブのみはマジシャンより先に発動する」。マジシャン特性ハンドラ(priority=100)
                # より確実に先に発動させるため、素早さに依存しないpriority=90を指定する。
                priority=90,
            )
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
    "ナモのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.ナモのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        },
        lethal_handlers={
            LethalEvent.ON_BEFORE_HIT: LethalHandler(
                func=l.ナモのみ_resist_dark,
                subject="defender",
            )
        }
    ),
    "ねばりのかぎづめ": ItemData(
        fling_power=90,
        handlers={
            Event.ON_MODIFY_BIND_DURATION: h.ItemHandler(
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
    "ノーマルジュエル": ItemData(
        fling_power=30,
        no_fling=True,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.ノーマルジュエル_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "はっきんだま": ItemData(
        fling_power=60,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.はっきんだま_modify_power,
                subject_spec="attacker:self",
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
        },
        lethal_handlers={
            LethalEvent.ON_BEFORE_HIT: LethalHandler(
                func=l.ハバンのみ_resist_dragon,
                subject="defender",
            )
        }
    ),
    "バグメモリ": ItemData(
        fling_power=50,
    ),
    "バコウのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.バコウのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        },
        lethal_handlers={
            LethalEvent.ON_BEFORE_HIT: LethalHandler(
                func=l.バコウのみ_resist_flying,
                subject="defender",
            )
        }
    ),
    "バンジのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_HP_CHANGED: h.ItemHandler(
                h.バンジのみ_heal_on_quarter_hp,
                subject_spec="target:self",
            )
        },
        lethal_handlers={
            LethalEvent.ON_EVERY_EVENT: LethalHandler(
                func=l.バンジのみ_heal,
                subject="defender",
            )
        }
    ),
    "ばんのうがさ": ItemData(
        fling_power=60,
        # 効果: 持たせたポケモンはにほんばれ・あめ状態の影響を受けなくなる。
        # 実装方法: battle.weather_for(mon) が ON_CHECK_WEATHER_IMMUNE を発火する。
        #           天候参照側は weather_for(mon) を使うことで自動的に反映される。
        # ウェザーボール・エレクトロビーム・ハイドロスチームも weather_for 経由で対応済み。
        handlers={
            Event.ON_CHECK_WEATHER_IMMUNE: h.ItemHandler(
                h.ばんのうがさ_weather_immune,
                subject_spec="source:self",
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
    "ひかりごけ": ItemData(
        fling_power=30,
        handlers={
            Event.ON_DAMAGE_HIT: h.ItemHandler(
                h.ひかりごけ_boost_spdef_on_water_hit,
                subject_spec="defender:self",
                # .internal/spec/abilities/マジシャン.md: 「きあいのハチマキ/きあいのタスキ/ゴツゴツメット/
                # じゃくてんほけん/じゅうでんち/ゆきだま/きゅうこん/ひかりごけ/ふうせんの効果が発動する場合、
                # マジシャンで奪う前に発動する」。マジシャン特性ハンドラ(priority=100)より確実に先に
                # 発動させるため、素早さに依存しないpriority=90を指定する。
                priority=90,
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
    "ひのたまプレート": ItemData(
        fling_power=90,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.ひのたまプレート_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "ヒメリのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_PP_CONSUMED: h.ItemHandler(
                h.ヒメリのみ_restore_pp,
                subject_spec="attacker:self",
                allow_fainted_subject=True,  # ぶきみなじゅもん等でPPが0になった際に自身が瀕死でも発動する
            ),
            Event.ON_SWITCH_IN: h.ItemHandler(
                h.ヒメリのみ_restore_pp_if_any_move_empty,
                subject_spec="source:self",
            ),
            Event.ON_ITEM_ENABLED: h.ItemHandler(
                h.ヒメリのみ_restore_pp_if_any_move_empty,
                subject_spec="source:self",
                priority=50,
            ),
            Event.ON_FORCE_BERRY_TRIGGER: h.ItemHandler(
                h.ヒメリのみ_restore_pp_if_any_move_empty,
                subject_spec="source:self",
                priority=50,
            ),
        }
    ),
    "ビアーのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.ビアーのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        },
        lethal_handlers={
            LethalEvent.ON_BEFORE_HIT: LethalHandler(
                func=l.ビアーのみ_resist_poison,
                subject="defender",
            )
        }
    ),
    "ビビリだま": ItemData(
        fling_power=30,
        handlers={
            # priority=50: しろいきり(130)やクリアボディ等の無効化ハンドラ(既定100)より先に
            # 判定し、いかくが無効化された場合でも発動するようにする（一次情報:
            # .internal/wiki/abilities/いかく.html 特性の仕様#ランク低下効果 の発動順一覧 3.）。
            Event.ON_BEFORE_MODIFY_STAT: h.ItemHandler(
                h.ビビリだま_boost_speed_on_intimidate,
                subject_spec="target:self",
                priority=50,
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
    "ファイアーメモリ": ItemData(
        fling_power=50,
    ),
    "ファイトメモリ": ItemData(
        fling_power=50,
    ),
    "フィラのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_HP_CHANGED: h.ItemHandler(
                h.フィラのみ_heal_on_quarter_hp,
                subject_spec="target:self",
            )
        },
        lethal_handlers={
            LethalEvent.ON_EVERY_EVENT: LethalHandler(
                func=l.フィラのみ_heal,
                subject="defender",
            )
        }
    ),
    "ふうせん": ItemData(
        fling_power=10,
        handlers={
            Event.ON_CHECK_FLOATING: h.ItemHandler(
                h.ふうせん_check_floating,
                subject_spec="source:self",
            ),
            # ON_HITはみがわり肩代わり・ばけのかわ/アイスフェイス肩代わり・
            # ダメージ0補正のケースでも発火するため、これらでも正しく割れる
            # （.internal/spec/turn.md の Event.ON_HIT 参照）
            Event.ON_HIT: h.ItemHandler(
                h.ふうせん_pop_on_hit,
                subject_spec="defender:self",
                # 攻撃技でひんしになったときもふうせんが割れる仕様
                # （.internal/spec/items/ふうせん.md）のため、瀕死主体でも発動を許可する。
                allow_fainted_subject=True,
            ),
        }
    ),
    "フェアリーメモリ": ItemData(
        fling_power=50,
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
    "ふしぎのプレート": ItemData(
        fling_power=90,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.ふしぎのプレート_modify_power_by_type,
                subject_spec="attacker:self",
            )
        }
    ),
    "フライングメモリ": ItemData(
        fling_power=50,
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
            Event.ON_CHECK_ITEM_CHANGE: h.ItemHandler(
                h.ブーストエナジー_prevent_item_change,
                subject_spec="target:self",
            ),
        }
    ),
    "ホズのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.ホズのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        },
        lethal_handlers={
            LethalEvent.ON_BEFORE_HIT: LethalHandler(
                func=l.ホズのみ_resist_normal,
                subject="defender",
            )
        }
    ),
    "ぼうごパット": ItemData(
        fling_power=30,
        handlers={
            Event.ON_CHECK_CONTACT_REACTION: h.ItemHandler(
                h.ぼうごパット_block_contact_reaction,
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
    "ポイズンメモリ": ItemData(
        fling_power=50,
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
    "マゴのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_HP_CHANGED: h.ItemHandler(
                h.マゴのみ_heal_on_quarter_hp,
                subject_spec="target:self",
            )
        },
        lethal_handlers={
            LethalEvent.ON_EVERY_EVENT: LethalHandler(
                func=l.マゴのみ_heal,
                subject="defender",
            )
        }
    ),
    "ミクルのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_HP_CHANGED: h.ItemHandler(
                h.ミクルのみ_set_accuracy_flag,
                subject_spec="target:self",
            ),
            Event.ON_MODIFY_ACCURACY: h.ItemHandler(
                h.ミクルのみ_boost_accuracy,
                subject_spec="attacker:self",
            ),
            Event.ON_END_MOVE: h.ItemHandler(
                h.ミクルのみ_clear_flag_after_move,
                subject_spec="attacker:self",
            ),
        }
    ),
    "ミストシード": ItemData(
        fling_power=10,
        handlers={
            Event.ON_SWITCH_IN: h.ItemHandler(
                h.ミストシード_boost_spdef,
                subject_spec="source:self",
                priority=120,  # .internal/spec/turn.md ON_SWITCH_IN: 「120 ミストシードの発動」
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
            Event.ON_END_MOVE: h.ItemHandler(
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
    "もうどくプレート": ItemData(
        fling_power=90,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.もうどくプレート_modify_power_by_type,
                subject_spec="attacker:self",
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
    "もののけプレート": ItemData(
        fling_power=90,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.もののけプレート_modify_power_by_type,
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
    "もりのプレート": ItemData(
        fling_power=90,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.もりのプレート_modify_power_by_type,
                subject_spec="attacker:self",
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
    "ヤチェのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.ヤチェのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        },
        lethal_handlers={
            LethalEvent.ON_BEFORE_HIT: LethalHandler(
                func=l.ヤチェのみ_resist_ice,
                subject="defender",
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
                h.ゆきだま_boost_attack_on_ice_hit,
                subject_spec="defender:self",
                # .internal/spec/abilities/マジシャン.md: 「きあいのハチマキ/きあいのタスキ/ゴツゴツメット/
                # じゃくてんほけん/じゅうでんち/ゆきだま/きゅうこん/ひかりごけ/ふうせんの効果が発動する場合、
                # マジシャンで奪う前に発動する」。マジシャン特性ハンドラ(priority=100)より確実に先に
                # 発動させるため、素早さに依存しないpriority=90を指定する。
                priority=90,
            )
        }
    ),
    "ようせいのハネ": ItemData(
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.ようせいのハネ_modify_power_by_type,
                subject_spec="attacker:self",
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
        },
        lethal_handlers={
            LethalEvent.ON_BEFORE_HIT: LethalHandler(
                func=l.ヨプのみ_resist_fighting,
                subject="defender",
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
        },
        lethal_handlers={
            LethalEvent.ON_BEFORE_HIT: LethalHandler(
                func=l.ヨロギのみ_resist_rock,
                subject="defender",
            )
        }
    ),
    "ラムのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_TURN_END: h.ItemHandler(
                h.ラムのみ_cure_ailment_and_confusion,
                subject_spec="source:self",
                priority=50,
            ),
            Event.ON_APPLY_AILMENT: h.ItemHandler(
                h.ラムのみ_cure_ailment_and_confusion_on_apply_ailment,
                subject_spec="target:self",
                priority=50,
            ),
            Event.ON_VOLATILE_START: h.ItemHandler(
                h.ラムのみ_cure_ailment_and_confusion_on_confuse,
                subject_spec="source:self",
            ),
            Event.ON_ITEM_ENABLED: h.ItemHandler(
                h.ラムのみ_cure_ailment_and_confusion,
                subject_spec="source:self",
                priority=50,
            ),
            Event.ON_FORCE_BERRY_TRIGGER: h.ItemHandler(
                h.ラムのみ_cure_ailment_and_confusion,
                subject_spec="source:self",
                priority=50,
            ),
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
    "りゅうのプレート": ItemData(
        fling_power=90,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.りゅうのプレート_modify_power_by_type,
                subject_spec="attacker:self",
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
    "リリバのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                h.リリバのみ_modify_super_effective_damage,
                subject_spec="defender:self",
            )
        },
        lethal_handlers={
            LethalEvent.ON_BEFORE_HIT: LethalHandler(
                func=l.リリバのみ_resist_steel,
                subject="defender",
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
        },
        lethal_handlers={
            LethalEvent.ON_BEFORE_HIT: LethalHandler(
                func=l.リンドのみ_resist_grass,
                subject="defender",
            )
        }
    ),
    "ルームサービス": ItemData(
        fling_power=100,
        handlers={
            Event.ON_FIELD_ACTIVATE: h.ItemHandler(
                h.ルームサービス_drop_speed_on_trick_room,
                subject_spec="source:self",
            ),
            Event.ON_SWITCH_IN: h.ItemHandler(
                h.ルームサービス_drop_speed_on_switch_in,
                subject_spec="source:self",
                priority=120,  # .internal/spec/turn.md ON_SWITCH_IN: 「120 ルームサービスの発動」
            ),
        }
    ),
    "レッドカード": ItemData(
        fling_power=10,
        handlers={
            # 実HPダメージ(>0)を受けたときの通常ケース。ゴツゴツメット等の反動処理より後、
            # いのちのたまの反動より先に発動させるため、.internal/spec/turn.md ON_DAMAGE:
            # 「150 レッドカードの発動・交代」に合わせて priority=150 を指定する。
            Event.ON_DAMAGE_HIT: h.ItemHandler(
                h.レッドカード_force_switch,
                subject_spec="defender:self",
                priority=150,
            ),
            # ON_DAMAGE_HIT は actual_damage<=0 のとき発火しないため、ばけのかわ/
            # アイスフェイスの肩代わりやこらえるでHP1のまま耐えたとき（実HPダメージ0）も
            # 発動する仕様（.internal/spec/items/レッドカード.md 詳細な仕様）を満たすため、
            # いのちのたま・だっしゅつボタンと同様に常に発火する Event.ON_HIT でも
            # 実HPダメージ0のケースのみを処理する（handlers/item.py 参照）。
            Event.ON_HIT: h.ItemHandler(
                h.レッドカード_force_switch_on_zero_damage,
                subject_spec="defender:self",
                priority=150,
            )
        }
    ),
    "レンブのみ": ItemData(
        fling_power=10,
        handlers={
            Event.ON_DAMAGE_HIT: h.ItemHandler(
                h.レンブのみ_retaliate_special,
                subject_spec="defender:self",
                # .internal/spec/abilities/マジシャン.md: 「弱点半減のきのみ/ナゾのみ/ジャポのみ/
                # レンブのみはマジシャンより先に発動する」。マジシャン特性ハンドラ(priority=100)
                # より確実に先に発動させるため、素早さに依存しないpriority=90を指定する。
                priority=90,
                # 所持者がひんしになったときでも発動する仕様
                # （.internal/spec/items/レンブのみ.md）のため、瀕死主体でも発動を許可する。
                allow_fainted_subject=True,
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
        },
        lethal_handlers={
            LethalEvent.ON_BEFORE_HIT: LethalHandler(
                func=l.ロゼルのみ_resist_fairy,
                subject="defender",
            )
        }
    ),
    "ロックメモリ": ItemData(
        fling_power=50,
    ),
}

common_setup()


def get_items_by_regulation(regulation: Regulation) -> list[ItemName]:
    """指定レギュレーションで使用可能なアイテム名の一覧を返す（五十音順）。"""
    return sorted(name for name, data in ITEMS.items() if regulation in data.regulations)
