"""持ち物データ定義モジュール。

Note:
    このモジュール内の持ち物定義はITEMS辞書内で五十音順に配置されています。
"""
from functools import partial

from jpoke.enums import Event
from jpoke.core import HandlerReturn
from jpoke.handlers import common, item as h
from .models import ItemData


def common_setup():
    """共通のセットアップ処理"""
    for name, data in ITEMS.items():
        ITEMS[name].name = name


ITEMS: dict[str, ItemData] = {
    "": ItemData(name=""),
    "あかいいと": ItemData(
        consumable=False,
        fling_power=10
    ),
    "あついいわ": ItemData(
        consumable=False,
        fling_power=60
    ),
    "あつぞこブーツ": ItemData(
        consumable=False,
        fling_power=80
    ),
    "いかさまダイス": ItemData(
        consumable=False,
        fling_power=30
    ),
    "いしずえのめん": ItemData(
        consumable=False,
        fling_power=60
    ),
    "いどのめん": ItemData(
        consumable=False,
        fling_power=60
    ),
    "いのちのたま": ItemData(
        fling_power=30,
        consumable=False,
        handlers={
            Event.ON_HIT: h.ItemHandler(
                h.いのちのたま,
                subject_spec="attacker:self",
            )
        }
    ),
    "エレキシード": ItemData(
        consumable=True,
        fling_power=10
    ),
    "おうじゃのしるし": ItemData(
        consumable=False,
        fling_power=30
    ),
    "おおきなねっこ": ItemData(
        consumable=False,
        fling_power=10
    ),
    "おんみつマント": ItemData(
        consumable=False,
        fling_power=30
    ),
    "かいがらのすず": ItemData(
        consumable=False,
        fling_power=30
    ),
    "かえんだま": ItemData(
        consumable=False,
        fling_power=30
    ),
    "かたいいし": ItemData(
        consumable=False,
        fling_power=100,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                partial(h.modify_power_by_type, type_="いわ", modifier=4915/4096),
                subject_spec="attacker:self",
                log="never",
            )
        }
    ),
    "かまどのめん": ItemData(
        consumable=False,
        fling_power=60
    ),
    "からぶりほけん": ItemData(
        consumable=True,
        fling_power=80
    ),
    "かるいし": ItemData(
        consumable=False,
        fling_power=30
    ),
    "きあいのタスキ": ItemData(
        consumable=True,
        fling_power=10
    ),
    "きあいのハチマキ": ItemData(
        consumable=False,
        fling_power=10
    ),
    "きせきのたね": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                partial(h.modify_power_by_type, type_="くさ", modifier=4915/4096),
                subject_spec="attacker:self",
                log="never",
            )
        }
    ),
    "きゅうこん": ItemData(
        consumable=True,
        fling_power=30,
        handlers={
            Event.ON_BEFORE_ACTION: h.ItemHandler(
                h.きゅうこん,
                subject_spec="source:self",
                priority=75,
            )
        }
    ),
    "きれいなぬけがら": ItemData(
        consumable=False,
        fling_power=10,
        handlers={
            Event.ON_CHECK_TRAPPED: h.ItemHandler(
                lambda *args: HandlerReturn(True, False, stop_event=True),
                subject_spec="source:self",
                log="never",
                priority=-100,
            )
        }
    ),
    "ぎんのこな": ItemData(
        consumable=False,
        fling_power=10,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                partial(h.modify_power_by_type, type_="むし", modifier=4915/4096),
                subject_spec="attacker:self",
                log="never",
            )
        }
    ),
    "くっつきバリ": ItemData(
        consumable=False,
        fling_power=80
    ),
    "グラスシード": ItemData(
        consumable=True,
        fling_power=10
    ),
    "グランドコート": ItemData(
        consumable=False,
        fling_power=60
    ),
    "クリアチャーム": ItemData(
        consumable=False,
        fling_power=30
    ),
    "くろいてっきゅう": ItemData(
        consumable=False,
        fling_power=130
    ),
    "くろいヘドロ": ItemData(
        consumable=False,
        fling_power=30
    ),
    "くろいメガネ": ItemData(
        consumable=False,
        fling_power=30
    ),
    "くろおび": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                partial(h.modify_power_by_type, type_="あく", modifier=4915/4096),
                subject_spec="attacker:self",
                log="never",
            )
        }
    ),
    "こうかくレンズ": ItemData(
        consumable=False,
        fling_power=10
    ),
    "こうこうのしっぽ": ItemData(
        consumable=False,
        fling_power=10
    ),
    "こころのしずく": ItemData(
        consumable=False,
        fling_power=30
    ),
    "こだわりスカーフ": ItemData(
        consumable=False,
        fling_power=10
    ),
    "こだわりハチマキ": ItemData(
        consumable=False,
        fling_power=10
    ),
    "こだわりメガネ": ItemData(
        consumable=False,
        fling_power=10
    ),
    "ゴツゴツメット": ItemData(
        consumable=False,
        fling_power=60
    ),
    "サイコシード": ItemData(
        consumable=True,
        fling_power=10
    ),
    "さらさらいわ": ItemData(
        consumable=False,
        fling_power=10,
        handlers={
            Event.ON_CHECK_DURATION: h.ItemHandler(
                partial(common.resolve_field_count, field="すなあらし", additonal_count=3),
                subject_spec="source:self",
                log="never",
            )
        }
    ),
    "じしゃく": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                partial(h.modify_power_by_type, type_="でんき", modifier=4915/4096),
                subject_spec="attacker:self",
                log="never",
            )
        }
    ),
    "しめつけバンド": ItemData(
        consumable=False,
        fling_power=30
    ),
    "しめったいわ": ItemData(
        consumable=False,
        fling_power=60
    ),
    "じゃくてんほけん": ItemData(
        consumable=True,
        fling_power=80
    ),
    "じゅうでんち": ItemData(
        consumable=True,
        fling_power=30
    ),
    "シルクのスカーフ": ItemData(
        consumable=False,
        fling_power=10,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                partial(h.modify_power_by_type, type_="ノーマル", modifier=4915/4096),
                subject_spec="attacker:self",
                log="never",
            )
        },
    ),
    "しろいハーブ": ItemData(
        consumable=True,
        fling_power=10
    ),
    "しんかのきせき": ItemData(
        consumable=False,
        fling_power=40
    ),
    "しんぴのしずく": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                partial(h.modify_power_by_type, type_="みず", modifier=4915/4096),
                subject_spec="attacker:self",
                log="never",
            )
        },
    ),
    "するどいキバ": ItemData(
        consumable=False,
        fling_power=30
    ),
    "するどいくちばし": ItemData(
        consumable=False,
        fling_power=50,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                partial(h.modify_power_by_type, type_="ひこう", modifier=4915/4096),
                subject_spec="attacker:self",
                log="never",
            )
        }
    ),
    "するどいツメ": ItemData(
        consumable=False,
        fling_power=80
    ),
    "せいれいプレート": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                partial(h.modify_power_by_type, type_="フェアリー", modifier=4915/4096),
                subject_spec="attacker:self",
                log="never",
            )
        }
    ),
    "せんせいのツメ": ItemData(
        consumable=False,
        fling_power=80
    ),
    "だっしゅつパック": ItemData(
        consumable=True,
        fling_power=50,
        handlers={
            Event.ON_MODIFY_STAT: h.ItemHandler(
                h.だっしゅつパック,
                subject_spec="target:self",
            )
        }
    ),
    "だっしゅつボタン": ItemData(
        consumable=True,
        fling_power=30,
        handlers={
            Event.ON_DAMAGE_1: h.ItemHandler(
                h.だっしゅつボタン,
                subject_spec="defender:self",
            )
        }
    ),
    "たつじんのおび": ItemData(
        consumable=False,
        fling_power=10
    ),
    "たべのこし": ItemData(
        fling_power=10,
        handlers={
            Event.ON_TURN_END_2: h.ItemHandler(
                partial(common.modify_hp, target_spec="source:self", r=1/16),
                subject_spec="source:self",
            )
        }
    ),
    "ちからのハチマキ": ItemData(
        consumable=False,
        fling_power=10,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.ちからのハチマキ,
                subject_spec="attacker:self",
                log="never",
            )
        }
    ),
    "つめたいいわ": ItemData(
        consumable=False,
        fling_power=40,
    ),
    "でかいきんのたま": ItemData(
        consumable=False,
        fling_power=130
    ),
    "でんきだま": ItemData(
        consumable=False,
        fling_power=30
    ),
    "とくせいガード": ItemData(
        consumable=False,
        fling_power=30
    ),
    "どくどくだま": ItemData(
        consumable=False,
        fling_power=30
    ),
    "どくバリ": ItemData(
        consumable=False,
        fling_power=70,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                partial(h.modify_power_by_type, type_="どく", modifier=4915/4096),
                subject_spec="attacker:self",
                log="never",
            )
        }
    ),
    "とけないこおり": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                partial(h.modify_power_by_type, type_="こおり", modifier=4915/4096),
                subject_spec="attacker:self",
                log="never",
            )
        }
    ),
    "とつげきチョッキ": ItemData(
        consumable=False,
        fling_power=80
    ),
    "ねばりのかぎづめ": ItemData(
        consumable=False,
        fling_power=90
    ),
    "ねらいのまと": ItemData(
        consumable=False,
        fling_power=10
    ),
    "ノーマルジュエル": ItemData(
        consumable=True,
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                partial(h.modify_power_by_type, type_="ノーマル", modifier=6144/4096),
                subject_spec="attacker:self",
                log="never",
            )
        }
    ),
    "のどスプレー": ItemData(
        consumable=True,
        fling_power=30
    ),
    "のろいのおふだ": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                partial(h.modify_power_by_type, type_="ゴースト", modifier=4915/4096),
                subject_spec="attacker:self",
                log="never",
            )
        }
    ),
    "パワフルハーブ": ItemData(
        consumable=True,
        fling_power=10
    ),
    "パンチグローブ": ItemData(
        consumable=False,
        fling_power=30
    ),
    "ばんのうがさ": ItemData(
        consumable=False,
        fling_power=60
    ),
    "ひかりごけ": ItemData(
        consumable=True,
        fling_power=30,
        handlers={
            Event.ON_BEFORE_ACTION: h.ItemHandler(
                h.ひかりごけ,
                subject_spec="source:self",
                priority=75,
            )
        }
    ),
    "ひかりのこな": ItemData(
        consumable=False,
        fling_power=10
    ),
    "ひかりのねんど": ItemData(
        consumable=False,
        fling_power=30
    ),
    "ビビリだま": ItemData(
        consumable=True,
        fling_power=30
    ),
    "ピントレンズ": ItemData(
        consumable=False,
        fling_power=30
    ),
    "ブーストエナジー": ItemData(
        consumable=True,
        fling_power=30
    ),
    "ふうせん": ItemData(
        consumable=False,
        fling_power=10
    ),
    "フォーカスレンズ": ItemData(
        consumable=False,
        fling_power=10
    ),
    "ぼうごパット": ItemData(
        consumable=False,
        fling_power=30
    ),
    "ぼうじんゴーグル": ItemData(
        consumable=False,
        fling_power=80
    ),
    "まがったスプーン": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                partial(h.modify_power_by_type, type_="エスパー", modifier=4915/4096),
                subject_spec="attacker:self",
                log="never",
            )
        }
    ),
    "ミストシード": ItemData(
        consumable=True,
        fling_power=10
    ),
    "メタルコート": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                partial(h.modify_power_by_type, type_="はがね", modifier=4915/4096),
                subject_spec="attacker:self",
                log="never",
            )
        }
    ),
    "メトロノーム": ItemData(
        consumable=False,
        fling_power=30
    ),
    "メンタルハーブ": ItemData(
        consumable=True,
        fling_power=10
    ),
    "もくたん": ItemData(
        consumable=False,
        fling_power=30,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                partial(h.modify_power_by_type, type_="ほのお", modifier=4915/4096),
                subject_spec="attacker:self",
                log="never",
            )
        },
    ),
    "ものしりメガネ": ItemData(
        consumable=False,
        fling_power=10,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                h.ものしりメガネ,
                subject_spec="attacker:self",
                log="never",
            )
        }
    ),
    "ものまねハーブ": ItemData(
        consumable=True,
        fling_power=30
    ),
    "やわらかいすな": ItemData(
        consumable=False,
        fling_power=10,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                partial(h.modify_power_by_type, type_="じめん", modifier=4915/4096),
                subject_spec="attacker:self",
                log="never",
            )
        }
    ),
    "ゆきだま": ItemData(
        consumable=True,
        fling_power=30
    ),
    "ようせいのハネ": ItemData(
        consumable=False,
        fling_power=20,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                partial(h.modify_power_by_type, type_="フェアリー", modifier=4915/4096),
                subject_spec="attacker:self",
                log="never",
            )
        }
    ),
    "りゅうのキバ": ItemData(
        consumable=False,
        fling_power=70,
        handlers={
            Event.ON_CALC_POWER_MODIFIER: h.ItemHandler(
                partial(h.modify_power_by_type, type_="ドラゴン", modifier=4915/4096),
                subject_spec="attacker:self",
                log="never",
            )
        }
    ),
    "ルームサービス": ItemData(
        consumable=True,
        fling_power=100
    ),
    "レッドカード": ItemData(
        consumable=True,
        fling_power=10
    ),
    "くちたけん": ItemData(
        consumable=False,
        fling_power=0
    ),
    "くちたたて": ItemData(
        consumable=False,
        fling_power=0
    ),
    "こんごうだま": ItemData(
        consumable=False,
        fling_power=0
    ),
    "しらたま": ItemData(
        consumable=False,
        fling_power=0
    ),
    "だいこんごうだま": ItemData(
        consumable=False,
        fling_power=0
    ),
    "だいしらたま": ItemData(
        consumable=False,
        fling_power=0
    ),
    "だいはっきんだま": ItemData(
        consumable=False,
        fling_power=0
    ),
    "はっきんだま": ItemData(
        consumable=False,
        fling_power=0
    ),
    "オボンのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_BEFORE_ACTION: h.ItemHandler(
                h.オボンのみ,
                subject_spec="source:self",
                priority=75,
            )
        }
    ),
    "ラムのみ": ItemData(
        consumable=True,
        fling_power=10
    ),
    "クラボのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_BEFORE_ACTION: h.ItemHandler(
                h.クラボのみ,
                subject_spec="source:self",
                priority=75,
            )
        }
    ),
    "カゴのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_BEFORE_ACTION: h.ItemHandler(
                h.カゴのみ,
                subject_spec="source:self",
                priority=75,
            )
        }
    ),
    "モモンのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_BEFORE_ACTION: h.ItemHandler(
                h.モモンのみ,
                subject_spec="source:self",
                priority=75,
            )
        }
    ),
    "チーゴのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_BEFORE_ACTION: h.ItemHandler(
                h.チーゴのみ,
                subject_spec="source:self",
                priority=75,
            )
        }
    ),
    "ナナシのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_BEFORE_ACTION: h.ItemHandler(
                h.ナナシのみ,
                subject_spec="source:self",
                priority=75,
            )
        }
    ),
    "キーのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_BEFORE_ACTION: h.ItemHandler(
                h.キーのみ,
                subject_spec="source:self",
                priority=75,
            )
        }
    ),
    "ヒメリのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_BEFORE_ACTION: h.ItemHandler(
                h.ヒメリのみ,
                subject_spec="source:self",
                priority=75,
            )
        }
    ),
    "オレンのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_BEFORE_ACTION: h.ItemHandler(
                h.オレンのみ,
                subject_spec="source:self",
                priority=75,
            )
        }
    ),
    "フィラのみ": ItemData(
        consumable=True,
        fling_power=10
    ),
    "ウイのみ": ItemData(
        consumable=True,
        fling_power=10
    ),
    "マゴのみ": ItemData(
        consumable=True,
        fling_power=10
    ),
    "バンジのみ": ItemData(
        consumable=True,
        fling_power=10
    ),
    "イアのみ": ItemData(
        consumable=True,
        fling_power=10
    ),
    "チイラのみ": ItemData(
        consumable=True,
        fling_power=10
    ),
    "リュガのみ": ItemData(
        consumable=True,
        fling_power=10
    ),
    "ヤタピのみ": ItemData(
        consumable=True,
        fling_power=10
    ),
    "ズアのみ": ItemData(
        consumable=True,
        fling_power=10
    ),
    "カムラのみ": ItemData(
        consumable=True,
        fling_power=10
    ),
    "スターのみ": ItemData(
        consumable=True,
        fling_power=10
    ),
    "サンのみ": ItemData(
        consumable=True,
        fling_power=10
    ),
    "ホズのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                partial(h.modify_super_effective_damage, type_="ノーマル", modifier=2048/4096),
                subject_spec="defender:self",
                log="never",
            )
        }
    ),
    "リンドのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                partial(h.modify_super_effective_damage, type_="くさ", modifier=2048/4096),
                subject_spec="defender:self",
                log="never",
            )
        }
        # handlers=_type_damage_handler("くさ", 2048/4096)
    ),
    "オッカのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                partial(h.modify_super_effective_damage, type_="ほのお", modifier=2048/4096),
                subject_spec="defender:self",
                log="never",
            )
        }
    ),
    "イトケのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                partial(h.modify_super_effective_damage, type_="みず", modifier=2048/4096),
                subject_spec="defender:self",
                log="never",
            )
        }
    ),
    "ソクノのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                partial(h.modify_super_effective_damage, type_="でんき", modifier=2048/4096),
                subject_spec="defender:self",
                log="never",
            )
        }
    ),
    "カシブのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                partial(h.modify_super_effective_damage, type_="ゴースト", modifier=2048/4096),
                subject_spec="defender:self",
                log="never",
            )
        }
    ),
    "ヨロギのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                partial(h.modify_super_effective_damage, type_="いわ", modifier=2048/4096),
                subject_spec="defender:self",
                log="never",
            )
        }
    ),
    "タンガのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                partial(h.modify_super_effective_damage, type_="むし", modifier=2048/4096),
                subject_spec="defender:self",
                log="never",
            )
        }
    ),
    "ウタンのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                partial(h.modify_super_effective_damage, type_="エスパー", modifier=2048/4096),
                subject_spec="defender:self",
                log="never",
            )
        }
    ),
    "バコウのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                partial(h.modify_super_effective_damage, type_="ひこう", modifier=2048/4096),
                subject_spec="defender:self",
                log="never",
            )
        }
    ),
    "シュカのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                partial(h.modify_super_effective_damage, type_="じめん", modifier=2048/4096),
                subject_spec="defender:self",
                log="never",
            )
        }
    ),
    "ビアーのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                partial(h.modify_super_effective_damage, type_="どく", modifier=2048/4096),
                subject_spec="defender:self",
                log="never",
            )
        }
    ),
    "ヨプのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                partial(h.modify_super_effective_damage, type_="かくとう", modifier=2048/4096),
                subject_spec="defender:self",
                log="never",
            )
        }
    ),
    "ヤチェのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                partial(h.modify_super_effective_damage, type_="こおり", modifier=2048/4096),
                subject_spec="defender:self",
                log="never",
            )
        }
    ),
    "リリバのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                partial(h.modify_super_effective_damage, type_="はがね", modifier=2048/4096),
                subject_spec="defender:self",
                log="never",
            )
        }
    ),
    "ナモのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                partial(h.modify_super_effective_damage, type_="あく", modifier=2048/4096),
                subject_spec="defender:self",
                log="never",
            )
        }
    ),
    "ハバンのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                partial(h.modify_super_effective_damage, type_="ドラゴン", modifier=2048/4096),
                subject_spec="defender:self",
                log="never",
            )
        }
    ),
    "ロゼルのみ": ItemData(
        consumable=True,
        fling_power=10,
        handlers={
            Event.ON_CALC_DAMAGE_MODIFIER: h.ItemHandler(
                partial(h.modify_super_effective_damage, type_="フェアリー", modifier=2048/4096),
                subject_spec="defender:self",
                log="never",
            )
        }
    ),
    "アッキのみ": ItemData(
        consumable=True,
        fling_power=10
    ),
    "タラプのみ": ItemData(
        consumable=True,
        fling_power=10
    ),
    "イバンのみ": ItemData(
        consumable=True,
        fling_power=10
    ),
    "ジャポのみ": ItemData(
        consumable=True,
        fling_power=10
    ),
    "レンブのみ": ItemData(
        consumable=True,
        fling_power=10
    ),
    "ナゾのみ": ItemData(
        consumable=True,
        fling_power=10
    ),
    "ミクルのみ": ItemData(
        consumable=True,
        fling_power=10
    )


}

common_setup()
