"""特性データ定義モジュール。

Note:
    このモジュール内の特性定義はABILITIES辞書内で五十音順に配置されています。
"""
from functools import partial

from jpoke.enums import DomainEvent, Event
from jpoke.core import HandlerReturn
from jpoke.handlers import common, ability as h
from .models import AbilityData


def common_setup():
    """共通のセットアップ処理"""
    for name in ABILITIES:
        ABILITIES[name].name = name


ABILITIES: dict[str, AbilityData] = {
    "": AbilityData(name=""),
    "ARシステム": AbilityData(
        flags=[
            "unreproducible",
            "protected"
        ]
    ),
    "あくしゅう": AbilityData(),
    "あついしぼう": AbilityData(),
    "あとだし": AbilityData(),
    "あまのじゃく": AbilityData(),
    "あめうけざら": AbilityData(),
    "あめふらし": AbilityData(),
    "ありじごく": AbilityData(
        handlers={
            Event.ON_CHECK_TRAPPED: h.AbilityHandler(
                h.ありじごく,
                subject_spec="source:foe",
                log="never",
            )
        }
    ),
    "いかく": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                partial(common.modify_stat, stat="A", v=-1, target_spec="source:foe", source_spec="source:self"),
                subject_spec="source:self",
                log="always",
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
            "unreproducible",
            "protected",
            "undeniable"
        ]
    ),
    "うるおいボイス": AbilityData(),
    "うるおいボディ": AbilityData(),
    "えんかく": AbilityData(),
    "おうごんのからだ": AbilityData(),
    "おどりこ": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "おみとおし": AbilityData(),
    "おもてなし": AbilityData(),
    "おやこあい": AbilityData(),
    "おわりのだいち": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "かいりきバサミ": AbilityData(),
    "かがくへんかガス": AbilityData(
        flags=[
            "unreproducible"
        ]
    ),
    "かげふみ": AbilityData(
        handlers={
            Event.ON_CHECK_TRAPPED: h.AbilityHandler(
                h.かげふみ,
                subject_spec="source:foe",
                log="never",
            )
        }
    ),
    "かぜのり": AbilityData(),
    "かそく": AbilityData(),
    "かたいツメ": AbilityData(),
    "かたやぶり": AbilityData(),
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
            "unreproducible"
        ]
    ),
    "かんそうはだ": AbilityData(),
    "かんろなミツ": AbilityData(
        flags=[
            "one_time"
        ]
    ),
    "がんじょう": AbilityData(),
    "がんじょうあご": AbilityData(),
    "ききかいひ": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "きけんよち": AbilityData(),
    "きみょうなくすり": AbilityData(),
    "きもったま": AbilityData(),
    "きゅうばん": AbilityData(),
    "きょううん": AbilityData(),
    "きょうえん": AbilityData(),
    "きょうせい": AbilityData(),
    "きよめのしお": AbilityData(),
    "きれあじ": AbilityData(),
    "きんしのちから": AbilityData(),
    "きんちょうかん": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                lambda *args: HandlerReturn(True),
                subject_spec="source:self",
                log="always",
            ),
            Event.ON_CHECK_NERVOUS: h.AbilityHandler(
                lambda *args: HandlerReturn(True, True),
                subject_spec="source:foe",
                log="never",
            ),
        }
    ),
    "ぎたい": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "ぎゃくじょう": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "ぎょぐん": AbilityData(
        flags=[
            "unreproducible",
            "protected"
        ]
    ),
    "くいしんぼう": AbilityData(),
    "くさのけがわ": AbilityData(),
    "くだけるよろい": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "くろのいななき": AbilityData(),
    "げきりゅう": AbilityData(),
    "こおりのりんぷん": AbilityData(),
    "こだいかっせい": AbilityData(
        flags=[
            "unreproducible",
            "undeniable"
        ]
    ),
    "こぼれダネ": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "こんがりボディ": AbilityData(),
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
    "しめりけ": AbilityData(),
    "しゅうかく": AbilityData(),
    "しょうりのほし": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "しれいとう": AbilityData(
        flags=[
            "unreproducible"
        ]
    ),
    "しろいけむり": AbilityData(),
    "しろのいななき": AbilityData(),
    "しんがん": AbilityData(),
    "しんりょく": AbilityData(),
    "じきゅうりょく": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "じしんかじょう": AbilityData(),
    "じゅうなん": AbilityData(
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.じゅうなん,
                subject_spec="target:self",
                log="on_fail",
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
    "じょおうのいげん": AbilityData(),
    "じりょく": AbilityData(
        handlers={
            Event.ON_CHECK_TRAPPED: h.AbilityHandler(
                h.じりょく,
                subject_spec="source:foe",
                log="never",
            )
        }
    ),
    "じんばいったい": AbilityData(
        flags=[
            "unreproducible",
            "protected"
        ]
    ),
    "すいすい": AbilityData(),
    "すいほう": AbilityData(),
    "すじがねいり": AbilityData(),
    "すてみ": AbilityData(),
    "すなおこし": AbilityData(),
    "すなかき": AbilityData(
        handlers={
            DomainEvent.ON_CALC_SPEED: h.AbilityHandler(
                h.すなかき,
                subject_spec="source:self",
                log="never",
            )
        }
    ),
    "すながくれ": AbilityData(),
    "すなのちから": AbilityData(),
    "すなはき": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "すりぬけ": AbilityData(),
    "するどいめ": AbilityData(),
    "せいぎのこころ": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "せいしんりょく": AbilityData(),
    "せいでんき": AbilityData(),
    "ぜったいねむり": AbilityData(
        flags=[
            "unreproducible",
            "protected",
            "undeniable"
        ],
        handlers={
            Event.ON_SWITCH_IN: h.AbilityHandler(
                partial(common.apply_ailment, ailment="ねむり", target_spec="source:self", source_spec="source:self"),
                subject_spec="source:self",
                log="always",
            )
        }
    ),
    "そうしょく": AbilityData(),
    "そうだいしょう": AbilityData(),
    "たいねつ": AbilityData(),
    "たまひろい": AbilityData(),
    "たんじゅん": AbilityData(),
    "だっぴ": AbilityData(),
    "ちからずく": AbilityData(),
    "ちからもち": AbilityData(),
    "ちくでん": AbilityData(),
    "ちどりあし": AbilityData(),
    "ちょすい": AbilityData(),
    "てきおうりょく": AbilityData(),
    "てつのこぶし": AbilityData(),
    "てつのトゲ": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "てんきや": AbilityData(
        flags=[
            "unreproducible"
        ]
    ),
    "てんねん": AbilityData(),
    "てんのめぐみ": AbilityData(),
    "でんきにかえる": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "でんきエンジン": AbilityData(),
    "とうそうしん": AbilityData(),
    "とびだすなかみ": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "とれないにおい": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "どくくぐつ": AbilityData(
        flags=[
            "unreproducible"
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
    "どしょく": AbilityData(),
    "どんかん": AbilityData(
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.どんかん,
                subject_spec="target:self",
                log="on_fail",
            )
        }
    ),
    "なまけ": AbilityData(),
    "にげあし": AbilityData(),
    "にげごし": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "ぬめぬめ": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "ねつこうかん": AbilityData(),
    "ねつぼうそう": AbilityData(),
    "ねんちゃく": AbilityData(),
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
    "はっこう": AbilityData(),
    "はとむね": AbilityData(),
    "はやあし": AbilityData(),
    "はやおき": AbilityData(),
    "はやてのつばさ": AbilityData(),
    "はらぺこスイッチ": AbilityData(
        flags=[
            "unreproducible"
        ]
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
            "unreproducible",
            "protected",
            "one_time"
        ]
    ),
    "ばんけん": AbilityData(),
    "ひでり": AbilityData(),
    "ひとでなし": AbilityData(),
    "ひひいろのこどう": AbilityData(),
    "ひらいしん": AbilityData(),
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
            "one_time"
        ]
    ),
    "ふしぎなうろこ": AbilityData(),
    "ふしぎなまもり": AbilityData(),
    "ふしょく": AbilityData(),
    "ふとうのけん": AbilityData(
        flags=[
            "one_time"
        ]
    ),
    "ふみん": AbilityData(
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.ふみん,
                subject_spec="target:self",
                log="on_fail",
            )
        }
    ),
    "ふゆう": AbilityData(),
    "ぶきよう": AbilityData(),
    "へんげんじざい": AbilityData(),
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
    "ぼうおん": AbilityData(),
    "ぼうじん": AbilityData(),
    "ぼうだん": AbilityData(),
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
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.みずのベール,
                subject_spec="target:self",
                log="on_fail",
            )
        }
    ),
    "みつあつめ": AbilityData(),
    "むしのしらせ": AbilityData(),
    "めんえき": AbilityData(
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.めんえき,
                subject_spec="target:self",
                log="on_fail",
            )
        }
    ),
    "もうか": AbilityData(),
    "ものひろい": AbilityData(),
    "もふもふ": AbilityData(),
    "もらいび": AbilityData(),
    "やるき": AbilityData(
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.やるき,
                subject_spec="target:self",
                log="on_fail",
            )
        }
    ),
    "ゆうばく": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "ゆきかき": AbilityData(),
    "ゆきがくれ": AbilityData(),
    "ゆきふらし": AbilityData(),
    "ようりょくそ": AbilityData(),
    "よちむ": AbilityData(),
    "よびみず": AbilityData(),
    "よわき": AbilityData(),
    "りゅうのあぎと": AbilityData(),
    "りんぷん": AbilityData(),
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
        ]
    ),
    "アイスフェイス": AbilityData(
        flags=[
            "unreproducible",
            "protected"
        ]
    ),
    "アイスボディ": AbilityData(),
    "アナライズ": AbilityData(),
    "アロマベール": AbilityData(),
    "イリュージョン": AbilityData(
        flags=[
            "unreproducible"
        ]
    ),
    "エアロック": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "エレキメイカー": AbilityData(),
    "オーラブレイク": AbilityData(),
    "カブトアーマー": AbilityData(),
    "カーリーヘアー": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "クイックドロウ": AbilityData(),
    "クォークチャージ": AbilityData(
        flags=[
            "unreproducible",
            "undeniable"
        ]
    ),
    "クリアボディ": AbilityData(),
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
    "シェルアーマー": AbilityData(),
    "シンクロ": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "スイートベール": AbilityData(),
    "スカイスキン": AbilityData(),
    "スキルリンク": AbilityData(),
    "スクリューおびれ": AbilityData(),
    "スナイパー": AbilityData(),
    "スロースタート": AbilityData(),
    "スワームチェンジ": AbilityData(
        flags=[
            "unreproducible",
            "protected"
        ]
    ),
    "ゼロフォーミング": AbilityData(
        flags=[
            "unreproducible"
        ]
    ),
    "ソウルハート": AbilityData(),
    "ターボブレイズ": AbilityData(),
    "ダウンロード": AbilityData(),
    "ダルマモード": AbilityData(
        flags=[
            "unreproducible",
            "protected"
        ]
    ),
    "ダークオーラ": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "テイルアーマー": AbilityData(),
    "テクニシャン": AbilityData(),
    "テラスシェル": AbilityData(
        flags=[
            "unreproducible"
        ]
    ),
    "テラスチェンジ": AbilityData(
        flags=[
            "unreproducible",
            "protected"
        ]
    ),
    "テラボルテージ": AbilityData(),
    "テレパシー": AbilityData(),
    "デルタストリーム": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "トランジスタ": AbilityData(),
    "トレース": AbilityData(
        flags=[
            "unreproducible"
        ]
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
    "ハードロック": AbilityData(),
    "バッテリー": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "バトルスイッチ": AbilityData(
        flags=[
            "unreproducible",
            "protected"
        ]
    ),
    "バリアフリー": AbilityData(),
    "パステルベール": AbilityData(),
    "パワースポット": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "パンクロック": AbilityData(),
    "ヒーリングシフト": AbilityData(),
    "ビビッドボディ": AbilityData(),
    "ビーストブースト": AbilityData(),
    "ファントムガード": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "ファーコート": AbilityData(),
    "フィルター": AbilityData(),
    "フェアリーオーラ": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "フェアリースキン": AbilityData(),
    "フラワーギフト": AbilityData(
        flags=[
            "unreproducible"
        ]
    ),
    "フラワーベール": AbilityData(),
    "フリーズスキン": AbilityData(),
    "フレンドガード": AbilityData(),
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
    "ヘヴィメタル": AbilityData(),
    "ポイズンヒール": AbilityData(),
    "マイティチェンジ": AbilityData(
        flags=[
            "unreproducible",
            "protected"
        ]
    ),
    "マイナス": AbilityData(),
    "マイペース": AbilityData(
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.マイペース,
                subject_spec="target:self",
                log="on_fail",
            )
        }
    ),
    "マグマのよろい": AbilityData(
        handlers={
            Event.ON_BEFORE_APPLY_AILMENT: h.AbilityHandler(
                h.マグマのよろい,
                subject_spec="target:self",
                log="on_fail",
            )
        }
    ),
    "マジシャン": AbilityData(),
    "マジックガード": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "マジックミラー": AbilityData(),
    "マルチスケイル": AbilityData(),
    "マルチタイプ": AbilityData(
        flags=[
            "unreproducible",
            "protected"
        ]
    ),
    "ミイラ": AbilityData(
        flags=[
            "undeniable"
        ]
    ),
    "ミストメイカー": AbilityData(),
    "ミラクルスキン": AbilityData(),
    "ミラーアーマー": AbilityData(),
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
    "ライトメタル": AbilityData(),
    "リベロ": AbilityData(),
    "リミットシールド": AbilityData(
        flags=[
            "unreproducible",
            "protected",
            "undeniable"
        ]
    ),
    "リーフガード": AbilityData(),
    "レシーバー": AbilityData(
        flags=[
            "unreproducible"
        ]
    ),
    "ＡＲシステム": AbilityData(),
    "おもかげやどし": AbilityData(
        flags=[
            "unreproducible",
            "protected"
        ]
    )
}


common_setup()
