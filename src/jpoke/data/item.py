from functools import partial

from jpoke.utils.enums import Event, EventControl
from jpoke.core.event import HandlerReturn
from jpoke.handlers import common, item as h
from .models import ItemData


ITEMS: dict[str, ItemData] = {
    "": ItemData(name=""),
    "あかいいと": ItemData(
        consumable=False,
        throw_power=10
    ),
    "あついいわ": ItemData(
        consumable=False,
        throw_power=60
    ),
    "あつぞこブーツ": ItemData(
        consumable=False,
        throw_power=80
    ),
    "いかさまダイス": ItemData(
        consumable=False,
        throw_power=30
    ),
    "いしずえのめん": ItemData(
        consumable=False,
        throw_power=60
    ),
    "いどのめん": ItemData(
        consumable=False,
        throw_power=60
    ),
    "いのちのたま": ItemData(
        throw_power=30,
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
        throw_power=10
    ),
    "おうじゃのしるし": ItemData(
        consumable=False,
        throw_power=30
    ),
    "おおきなねっこ": ItemData(
        consumable=False,
        throw_power=10
    ),
    "おんみつマント": ItemData(
        consumable=False,
        throw_power=30
    ),
    "かいがらのすず": ItemData(
        consumable=False,
        throw_power=30
    ),
    "かえんだま": ItemData(
        consumable=False,
        throw_power=30
    ),
    "かたいいし": ItemData(
        consumable=False,
        throw_power=100
    ),
    "かまどのめん": ItemData(
        consumable=False,
        throw_power=60
    ),
    "からぶりほけん": ItemData(
        consumable=True,
        throw_power=80
    ),
    "かるいし": ItemData(
        consumable=False,
        throw_power=30
    ),
    "きあいのタスキ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "きあいのハチマキ": ItemData(
        consumable=False,
        throw_power=10
    ),
    "きせきのたね": ItemData(
        consumable=False,
        throw_power=30
    ),
    "きゅうこん": ItemData(
        consumable=True,
        throw_power=30
    ),
    "きれいなぬけがら": ItemData(
        consumable=False,
        throw_power=10,
        handlers={
            Event.ON_CHECK_TRAPPED: h.ItemHandler(
                lambda *args: HandlerReturn(True, False, EventControl.STOP_EVENT),
                subject_spec="source:self",
                log="never",
                priority=-100,
            )
        }
    ),
    "ぎんのこな": ItemData(
        consumable=False,
        throw_power=10
    ),
    "くっつきバリ": ItemData(
        consumable=False,
        throw_power=80
    ),
    "グラスシード": ItemData(
        consumable=True,
        throw_power=10
    ),
    "グランドコート": ItemData(
        consumable=False,
        throw_power=60
    ),
    "クリアチャーム": ItemData(
        consumable=False,
        throw_power=30
    ),
    "くろいてっきゅう": ItemData(
        consumable=False,
        throw_power=130
    ),
    "くろいヘドロ": ItemData(
        consumable=False,
        throw_power=30
    ),
    "くろいメガネ": ItemData(
        consumable=False,
        throw_power=30
    ),
    "くろおび": ItemData(
        consumable=False,
        throw_power=30
    ),
    "こうかくレンズ": ItemData(
        consumable=False,
        throw_power=10
    ),
    "こうこうのしっぽ": ItemData(
        consumable=False,
        throw_power=10
    ),
    "こころのしずく": ItemData(
        consumable=False,
        throw_power=30
    ),
    "こだわりスカーフ": ItemData(
        consumable=False,
        throw_power=10
    ),
    "こだわりハチマキ": ItemData(
        consumable=False,
        throw_power=10
    ),
    "こだわりメガネ": ItemData(
        consumable=False,
        throw_power=10
    ),
    "ゴツゴツメット": ItemData(
        consumable=False,
        throw_power=60
    ),
    "サイコシード": ItemData(
        consumable=True,
        throw_power=10
    ),
    "さらさらいわ": ItemData(
        consumable=False,
        throw_power=10,
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
        throw_power=30
    ),
    "しめつけバンド": ItemData(
        consumable=False,
        throw_power=30
    ),
    "しめったいわ": ItemData(
        consumable=False,
        throw_power=60
    ),
    "じゃくてんほけん": ItemData(
        consumable=True,
        throw_power=80
    ),
    "じゅうでんち": ItemData(
        consumable=True,
        throw_power=30
    ),
    "シルクのスカーフ": ItemData(
        consumable=False,
        throw_power=10
    ),
    "しろいハーブ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "しんかのきせき": ItemData(
        consumable=False,
        throw_power=40
    ),
    "しんぴのしずく": ItemData(
        consumable=False,
        throw_power=30
    ),
    "するどいキバ": ItemData(
        consumable=False,
        throw_power=30
    ),
    "するどいくちばし": ItemData(
        consumable=False,
        throw_power=50
    ),
    "するどいツメ": ItemData(
        consumable=False,
        throw_power=80
    ),
    "せいれいプレート": ItemData(
        consumable=False,
        throw_power=30
    ),
    "せんせいのツメ": ItemData(
        consumable=False,
        throw_power=80
    ),
    "だっしゅつパック": ItemData(
        consumable=True,
        throw_power=50,
        handlers={
            Event.ON_MODIFY_STAT: h.ItemHandler(
                h.だっしゅつパック,
                subject_spec="target:self",
            )
        }
    ),
    "だっしゅつボタン": ItemData(
        consumable=True,
        throw_power=30,
        handlers={
            Event.ON_DAMAGE_1: h.ItemHandler(
                h.だっしゅつボタン,
                subject_spec="defender:self",
            )
        }
    ),
    "たつじんのおび": ItemData(
        consumable=False,
        throw_power=10
    ),
    "たべのこし": ItemData(
        throw_power=10,
        handlers={
            Event.ON_TURN_END_2: h.ItemHandler(
                partial(
                    common.modify_hp, target_spec="source:self", r=1/16
                ),
                subject_spec="source:self",
            )
        }
    ),
    "ちからのハチマキ": ItemData(
        consumable=False,
        throw_power=10
    ),
    "つめたいいわ": ItemData(
        consumable=False,
        throw_power=40
    ),
    "でかいきんのたま": ItemData(
        consumable=False,
        throw_power=130
    ),
    "でんきだま": ItemData(
        consumable=False,
        throw_power=30
    ),
    "とくせいガード": ItemData(
        consumable=False,
        throw_power=30
    ),
    "どくどくだま": ItemData(
        consumable=False,
        throw_power=30
    ),
    "どくバリ": ItemData(
        consumable=False,
        throw_power=70
    ),
    "とけないこおり": ItemData(
        consumable=False,
        throw_power=30
    ),
    "とつげきチョッキ": ItemData(
        consumable=False,
        throw_power=80
    ),
    "ねばりのかぎづめ": ItemData(
        consumable=False,
        throw_power=90
    ),
    "ねらいのまと": ItemData(
        consumable=False,
        throw_power=10
    ),
    "ノーマルジュエル": ItemData(
        consumable=True,
        throw_power=30
    ),
    "のどスプレー": ItemData(
        consumable=True,
        throw_power=30
    ),
    "のろいのおふだ": ItemData(
        consumable=False,
        throw_power=30
    ),
    "パワフルハーブ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "パンチグローブ": ItemData(
        consumable=False,
        throw_power=30
    ),
    "ばんのうがさ": ItemData(
        consumable=False,
        throw_power=60
    ),
    "ひかりごけ": ItemData(
        consumable=True,
        throw_power=30
    ),
    "ひかりのこな": ItemData(
        consumable=False,
        throw_power=10
    ),
    "ひかりのねんど": ItemData(
        consumable=False,
        throw_power=30
    ),
    "ビビリだま": ItemData(
        consumable=True,
        throw_power=30
    ),
    "ピントレンズ": ItemData(
        consumable=False,
        throw_power=30
    ),
    "ブーストエナジー": ItemData(
        consumable=True,
        throw_power=30
    ),
    "ふうせん": ItemData(
        consumable=False,
        throw_power=10
    ),
    "フォーカスレンズ": ItemData(
        consumable=False,
        throw_power=10
    ),
    "ぼうごパット": ItemData(
        consumable=False,
        throw_power=30
    ),
    "ぼうじんゴーグル": ItemData(
        consumable=False,
        throw_power=80
    ),
    "まがったスプーン": ItemData(
        consumable=False,
        throw_power=30
    ),
    "ミストシード": ItemData(
        consumable=True,
        throw_power=10
    ),
    "メタルコート": ItemData(
        consumable=False,
        throw_power=30
    ),
    "メトロノーム": ItemData(
        consumable=False,
        throw_power=30
    ),
    "メンタルハーブ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "もくたん": ItemData(
        consumable=False,
        throw_power=30
    ),
    "ものしりメガネ": ItemData(
        consumable=False,
        throw_power=10
    ),
    "ものまねハーブ": ItemData(
        consumable=True,
        throw_power=30
    ),
    "やわらかいすな": ItemData(
        consumable=False,
        throw_power=10
    ),
    "ゆきだま": ItemData(
        consumable=True,
        throw_power=30
    ),
    "ようせいのハネ": ItemData(
        consumable=False,
        throw_power=20
    ),
    "りゅうのキバ": ItemData(
        consumable=False,
        throw_power=70
    ),
    "ルームサービス": ItemData(
        consumable=True,
        throw_power=100
    ),
    "レッドカード": ItemData(
        consumable=True,
        throw_power=10
    ),
    "くちたけん": ItemData(
        consumable=False,
        throw_power=0
    ),
    "くちたたて": ItemData(
        consumable=False,
        throw_power=0
    ),
    "こんごうだま": ItemData(
        consumable=False,
        throw_power=0
    ),
    "しらたま": ItemData(
        consumable=False,
        throw_power=0
    ),
    "だいこんごうだま": ItemData(
        consumable=False,
        throw_power=0
    ),
    "だいしらたま": ItemData(
        consumable=False,
        throw_power=0
    ),
    "だいはっきんだま": ItemData(
        consumable=False,
        throw_power=0
    ),
    "はっきんだま": ItemData(
        consumable=False,
        throw_power=0
    ),
    "オボンのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "ラムのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "クラボのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "カゴのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "モモンのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "チーゴのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "ナナシのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "キーのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "ヒメリのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "オレンのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "フィラのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "ウイのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "マゴのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "バンジのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "イアのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "チイラのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "リュガのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "ヤタピのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "ズアのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "カムラのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "スターのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "サンのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "ホズのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "リンドのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "オッカのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "イトケのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "ソクノのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "カシブのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "ヨロギのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "タンガのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "ウタンのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "バコウのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "シュカのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "ビアーのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "ヨプのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "ヤチェのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "リリバのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "ナモのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "ハバンのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "ロゼルのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "アッキのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "タラプのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "イバンのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "ジャポのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "レンブのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "ナゾのみ": ItemData(
        consumable=True,
        throw_power=10
    ),
    "ミクルのみ": ItemData(
        consumable=True,
        throw_power=10
    )
}
