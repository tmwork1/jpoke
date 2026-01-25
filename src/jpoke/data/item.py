from jpoke.core.event import Event, Handler, HandlerResult
from .models import ItemData

from jpoke.handlers import common, item as hdl


ITEMS: dict[str, ItemData] = {
    "": ItemData(name=""),
    "あかいいと": {
        "consumable": False,
        "throw_power": 10
    },
    "あついいわ": {
        "consumable": False,
        "throw_power": 60
    },
    "あつぞこブーツ": {
        "consumable": False,
        "throw_power": 80
    },
    "いかさまダイス": {
        "consumable": False,
        "throw_power": 30
    },
    "いしずえのめん": {
        "consumable": False,
        "throw_power": 60
    },
    "いどのめん": {
        "consumable": False,
        "throw_power": 60
    },
    "いのちのたま": ItemData(
        throw_power=30,
        consumable=False,
        handlers={Event.ON_HIT: Handler(hdl.いのちのたま, role="attacker")},
    ),
    "エレキシード": {
        "consumable": True,
        "throw_power": 10
    },
    "おうじゃのしるし": {
        "consumable": False,
        "throw_power": 30
    },
    "おおきなねっこ": {
        "consumable": False,
        "throw_power": 10
    },
    "おんみつマント": {
        "consumable": False,
        "throw_power": 30
    },
    "かいがらのすず": {
        "consumable": False,
        "throw_power": 30
    },
    "かえんだま": {
        "consumable": False,
        "throw_power": 30
    },
    "かたいいし": {
        "consumable": False,
        "throw_power": 100
    },
    "かまどのめん": {
        "consumable": False,
        "throw_power": 60
    },
    "からぶりほけん": {
        "consumable": True,
        "throw_power": 80
    },
    "かるいし": {
        "consumable": False,
        "throw_power": 30
    },
    "きあいのタスキ": {
        "consumable": True,
        "throw_power": 10
    },
    "きあいのハチマキ": {
        "consumable": False,
        "throw_power": 10
    },
    "きせきのたね": {
        "consumable": False,
        "throw_power": 30
    },
    "きゅうこん": {
        "consumable": True,
        "throw_power": 30
    },
    "きれいなぬけがら": ItemData(
        consumable=False,
        throw_power=10,
        handlers={Event.ON_CHECK_TRAPPED: Handler(
            lambda btl, ctx, v: (False, HandlerResult.STOP_EVENT), priority=-100)}
    ),
    "ぎんのこな": {
        "consumable": False,
        "throw_power": 10
    },
    "くっつきバリ": {
        "consumable": False,
        "throw_power": 80
    },
    "グラスシード": {
        "consumable": True,
        "throw_power": 10
    },
    "グランドコート": {
        "consumable": False,
        "throw_power": 60
    },
    "クリアチャーム": {
        "consumable": False,
        "throw_power": 30
    },
    "くろいてっきゅう": {
        "consumable": False,
        "throw_power": 130
    },
    "くろいヘドロ": {
        "consumable": False,
        "throw_power": 30
    },
    "くろいメガネ": {
        "consumable": False,
        "throw_power": 30
    },
    "くろおび": {
        "consumable": False,
        "throw_power": 30
    },
    "こうかくレンズ": {
        "consumable": False,
        "throw_power": 10
    },
    "こうこうのしっぽ": {
        "consumable": False,
        "throw_power": 10
    },
    "こころのしずく": {
        "consumable": False,
        "throw_power": 30
    },
    "こだわりスカーフ": {
        "consumable": False,
        "throw_power": 10
    },
    "こだわりハチマキ": {
        "consumable": False,
        "throw_power": 10
    },
    "こだわりメガネ": {
        "consumable": False,
        "throw_power": 10
    },
    "ゴツゴツメット": {
        "consumable": False,
        "throw_power": 60
    },
    "サイコシード": {
        "consumable": True,
        "throw_power": 10
    },
    "さらさらいわ": ItemData(
        consumable=False,
        throw_power=10,
    ),
    "じしゃく": {
        "consumable": False,
        "throw_power": 30
    },
    "しめつけバンド": {
        "consumable": False,
        "throw_power": 30
    },
    "しめったいわ": {
        "consumable": False,
        "throw_power": 60
    },
    "じゃくてんほけん": {
        "consumable": True,
        "throw_power": 80
    },
    "じゅうでんち": {
        "consumable": True,
        "throw_power": 30
    },
    "シルクのスカーフ": {
        "consumable": False,
        "throw_power": 10
    },
    "しろいハーブ": {
        "consumable": True,
        "throw_power": 10
    },
    "しんかのきせき": {
        "consumable": False,
        "throw_power": 40
    },
    "しんぴのしずく": {
        "consumable": False,
        "throw_power": 30
    },
    "するどいキバ": {
        "consumable": False,
        "throw_power": 30
    },
    "するどいくちばし": {
        "consumable": False,
        "throw_power": 50
    },
    "するどいツメ": {
        "consumable": False,
        "throw_power": 80
    },
    "せいれいプレート": {
        "consumable": False,
        "throw_power": 30
    },
    "せんせいのツメ": {
        "consumable": False,
        "throw_power": 80
    },
    "だっしゅつパック": ItemData(
        consumable=True,
        throw_power=50,
        handlers={Event.ON_MODIFY_STAT: Handler(hdl.だっしゅつパック)}
    ),
    "だっしゅつボタン": ItemData(
        consumable=True,
        throw_power=30,
        handlers={Event.ON_DAMAGE: Handler(hdl.だっしゅつボタン, role="defender")}
    ),
    "たつじんのおび": {
        "consumable": False,
        "throw_power": 10
    },
    "たべのこし": ItemData(
        throw_power=10,
        handlers={Event.ON_TURN_END_2: Handler(
            lambda btl, ctx, v: common.modify_hp(btl, ctx.target, r=1/16) and hdl.reveal_item(btl, ctx.target))}
    ),
    "ちからのハチマキ": {
        "consumable": False,
        "throw_power": 10
    },
    "つめたいいわ": {
        "consumable": False,
        "throw_power": 40
    },
    "でかいきんのたま": {
        "consumable": False,
        "throw_power": 130
    },
    "でんきだま": {
        "consumable": False,
        "throw_power": 30
    },
    "とくせいガード": {
        "consumable": False,
        "throw_power": 30
    },
    "どくどくだま": {
        "consumable": False,
        "throw_power": 30
    },
    "どくバリ": {
        "consumable": False,
        "throw_power": 70
    },
    "とけないこおり": {
        "consumable": False,
        "throw_power": 30
    },
    "とつげきチョッキ": {
        "consumable": False,
        "throw_power": 80
    },
    "ねばりのかぎづめ": {
        "consumable": False,
        "throw_power": 90
    },
    "ねらいのまと": {
        "consumable": False,
        "throw_power": 10
    },
    "ノーマルジュエル": {
        "consumable": True,
        "throw_power": 30
    },
    "のどスプレー": {
        "consumable": True,
        "throw_power": 30
    },
    "のろいのおふだ": {
        "consumable": False,
        "throw_power": 30
    },
    "パワフルハーブ": {
        "consumable": True,
        "throw_power": 10
    },
    "パンチグローブ": {
        "consumable": False,
        "throw_power": 30
    },
    "ばんのうがさ": {
        "consumable": False,
        "throw_power": 60
    },
    "ひかりごけ": {
        "consumable": True,
        "throw_power": 30
    },
    "ひかりのこな": {
        "consumable": False,
        "throw_power": 10
    },
    "ひかりのねんど": {
        "consumable": False,
        "throw_power": 30
    },
    "ビビリだま": {
        "consumable": True,
        "throw_power": 30
    },
    "ピントレンズ": {
        "consumable": False,
        "throw_power": 30
    },
    "ブーストエナジー": {
        "consumable": True,
        "throw_power": 30
    },
    "ふうせん": {
        "consumable": False,
        "throw_power": 10
    },
    "フォーカスレンズ": {
        "consumable": False,
        "throw_power": 10
    },
    "ぼうごパット": {
        "consumable": False,
        "throw_power": 30
    },
    "ぼうじんゴーグル": {
        "consumable": False,
        "throw_power": 80
    },
    "まがったスプーン": {
        "consumable": False,
        "throw_power": 30
    },
    "ミストシード": {
        "consumable": True,
        "throw_power": 10
    },
    "メタルコート": {
        "consumable": False,
        "throw_power": 30
    },
    "メトロノーム": {
        "consumable": False,
        "throw_power": 30
    },
    "メンタルハーブ": {
        "consumable": True,
        "throw_power": 10
    },
    "もくたん": {
        "consumable": False,
        "throw_power": 30
    },
    "ものしりメガネ": {
        "consumable": False,
        "throw_power": 10
    },
    "ものまねハーブ": {
        "consumable": True,
        "throw_power": 30
    },
    "やわらかいすな": {
        "consumable": False,
        "throw_power": 10
    },
    "ゆきだま": {
        "consumable": True,
        "throw_power": 30
    },
    "ようせいのハネ": {
        "consumable": False,
        "throw_power": 20
    },
    "りゅうのキバ": {
        "consumable": False,
        "throw_power": 70
    },
    "ルームサービス": {
        "consumable": True,
        "throw_power": 100
    },
    "レッドカード": {
        "consumable": True,
        "throw_power": 10
    },
    "くちたけん": {
        "consumable": False,
        "throw_power": 0
    },
    "くちたたて": {
        "consumable": False,
        "throw_power": 0
    },
    "こんごうだま": {
        "consumable": False,
        "throw_power": 0
    },
    "しらたま": {
        "consumable": False,
        "throw_power": 0
    },
    "だいこんごうだま": {
        "consumable": False,
        "throw_power": 0
    },
    "だいしらたま": {
        "consumable": False,
        "throw_power": 0
    },
    "だいはっきんだま": {
        "consumable": False,
        "throw_power": 0
    },
    "はっきんだま": {
        "consumable": False,
        "throw_power": 0
    },
    "オボンのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "ラムのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "クラボのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "カゴのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "モモンのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "チーゴのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "ナナシのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "キーのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "ヒメリのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "オレンのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "フィラのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "ウイのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "マゴのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "バンジのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "イアのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "チイラのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "リュガのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "ヤタピのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "ズアのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "カムラのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "スターのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "サンのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "ホズのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "リンドのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "オッカのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "イトケのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "ソクノのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "カシブのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "ヨロギのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "タンガのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "ウタンのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "バコウのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "シュカのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "ビアーのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "ヨプのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "ヤチェのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "リリバのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "ナモのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "ハバンのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "ロゼルのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "アッキのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "タラプのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "イバンのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "ジャポのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "レンブのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "ナゾのみ": {
        "consumable": True,
        "throw_power": 10
    },
    "ミクルのみ": {
        "consumable": True,
        "throw_power": 10
    }
}
