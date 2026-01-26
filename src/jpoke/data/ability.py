from functools import partial
from jpoke.core.event import Event, Handler
from .models import AbilityData
from jpoke.handlers import common, ability as h


ABILITIES: dict[str, AbilityData] = {
    "": AbilityData(name=""),
    "ARシステム": {
        "flags": [
            "unreproducible",
            "protected"
        ]
    },
    "あくしゅう": {},
    "あついしぼう": {},
    "あとだし": {},
    "あまのじゃく": {},
    "あめうけざら": {},
    "あめふらし": {},
    "ありじごく": AbilityData(
        handlers={
            Event.ON_CHECK_TRAPPED: Handler(
                lambda btl, ctx, v: not ctx.source.floating(btl.events),
                role="source", side="foe",
            )
        }
    ),
    "いかく": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: Handler(
                lambda btl, ctx, v: h.reveal_ability(btl, ctx.source) and common.modify_stat(btl, btl.foe(ctx.source), "A", -1),
                role="source",
            )
        },
    ),
    "いかりのこうら": {},
    "いかりのつぼ": {
        "flags": [
            "undeniable"
        ]
    },
    "いしあたま": {},
    "いたずらごころ": {},
    "いやしのこころ": {},
    "いろめがね": {},
    "いわはこび": {},
    "うのミサイル": {
        "flags": [
            "unreproducible",
            "protected",
            "undeniable"
        ]
    },
    "うるおいボイス": {},
    "うるおいボディ": {},
    "えんかく": {},
    "おうごんのからだ": {},
    "おどりこ": {
        "flags": [
            "undeniable"
        ]
    },
    "おみとおし": {},
    "おもてなし": {},
    "おやこあい": {},
    "おわりのだいち": {
        "flags": [
            "undeniable"
        ]
    },
    "かいりきバサミ": {},
    "かがくへんかガス": {
        "flags": [
            "unreproducible"
        ]
    },
    "かげふみ": AbilityData(
        handlers={
            Event.ON_CHECK_TRAPPED: Handler(
                lambda btl, ctx, v: ctx.source.ability != "かげふみ",
                role="source", side="foe",
            )
        }
    ),
    "かぜのり": {},
    "かそく": {},
    "かたいツメ": {},
    "かたやぶり": {},
    "かちき": AbilityData(
        flags=["undeniable"],
        handlers={
            Event.ON_MODIFY_STAT: Handler(h.かちき, role="target")
        }
    ),
    "かるわざ": {},
    "かわりもの": {
        "flags": [
            "unreproducible"
        ]
    },
    "かんそうはだ": {},
    "かんろなミツ": {
        "flags": [
            "one_time"
        ]
    },
    "がんじょう": {},
    "がんじょうあご": {},
    "ききかいひ": {
        "flags": [
            "undeniable"
        ]
    },
    "きけんよち": {},
    "きみょうなくすり": {},
    "きもったま": {},
    "きゅうばん": {},
    "きょううん": {},
    "きょうえん": {},
    "きょうせい": {},
    "きよめのしお": {},
    "きれあじ": {},
    "きんしのちから": {},
    "きんちょうかん": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: Handler(
                lambda btl, ctx, v: h.reveal_ability(btl, ctx.source),
                role="source",
            ),
            Event.ON_CHECK_NERVOUS: Handler(
                lambda btl, ctx, v: True,
                role="source", side="foe"
            ),
        }
    ),
    "ぎたい": {
        "flags": [
            "undeniable"
        ]
    },
    "ぎゃくじょう": {
        "flags": [
            "undeniable"
        ]
    },
    "ぎょぐん": {
        "flags": [
            "unreproducible",
            "protected"
        ]
    },
    "くいしんぼう": {},
    "くさのけがわ": {},
    "くだけるよろい": {
        "flags": [
            "undeniable"
        ]
    },
    "くろのいななき": {},
    "げきりゅう": {},
    "こおりのりんぷん": {},
    "こだいかっせい": {
        "flags": [
            "unreproducible",
            "undeniable"
        ]
    },
    "こぼれダネ": {
        "flags": [
            "undeniable"
        ]
    },
    "こんがりボディ": {},
    "こんじょう": {},
    "ごりむちゅう": {},
    "さいせいりょく": {},
    "さまようたましい": {
        "flags": [
            "undeniable"
        ]
    },
    "さめはだ": {
        "flags": [
            "undeniable"
        ]
    },
    "しぜんかいふく": {},
    "しめりけ": {},
    "しゅうかく": {},
    "しょうりのほし": {
        "flags": [
            "undeniable"
        ]
    },
    "しれいとう": {
        "flags": [
            "unreproducible"
        ]
    },
    "しろいけむり": {},
    "しろのいななき": {},
    "しんがん": {},
    "しんりょく": {},
    "じきゅうりょく": {
        "flags": [
            "undeniable"
        ]
    },
    "じしんかじょう": {},
    "じゅうなん": {},
    "じゅくせい": {
        "flags": [
            "undeniable"
        ]
    },
    "じょうききかん": {
        "flags": [
            "undeniable"
        ]
    },
    "じょおうのいげん": {},
    "じりょく": AbilityData(
        handlers={Event.ON_CHECK_TRAPPED: Handler(
            lambda btl, ctx, v: "はがね" in ctx.source.types,
            role="source", side="foe"
        )}
    ),
    "じんばいったい": {
        "flags": [
            "unreproducible",
            "protected"
        ]
    },
    "すいすい": {},
    "すいほう": {},
    "すじがねいり": {},
    "すてみ": {},
    "すなおこし": {},
    "すなかき": AbilityData(
        handlers={
            Event.ON_CALC_SPEED: Handler(
                lambda btl, ctx, v: v * 2 if btl.weather == "すなあらし" else v,
                role="source",
            )
        }
    ),
    "すながくれ": {},
    "すなのちから": {},
    "すなはき": {
        "flags": [
            "undeniable"
        ]
    },
    "すりぬけ": {},
    "するどいめ": {},
    "せいぎのこころ": {
        "flags": [
            "undeniable"
        ]
    },
    "せいしんりょく": {},
    "せいでんき": {},
    "ぜったいねむり": AbilityData(
        flags=[
            "unreproducible",
            "protected",
            "undeniable"
        ],
        handlers={
            Event.ON_SWITCH_IN: Handler(
                lambda btl, ctx, v: h.reveal_ability(btl, ctx.source) and common.apply_ailment(btl, ctx.source, "ねむり"),
                role="source",
            )
        }
    ),
    "そうしょく": {},
    "そうだいしょう": {},
    "たいねつ": {},
    "たまひろい": {},
    "たんじゅん": {},
    "だっぴ": {},
    "ちからずく": {},
    "ちからもち": {},
    "ちくでん": {},
    "ちどりあし": {},
    "ちょすい": {},
    "てきおうりょく": {},
    "てつのこぶし": {},
    "てつのトゲ": {
        "flags": [
            "undeniable"
        ]
    },
    "てんきや": {
        "flags": [
            "unreproducible"
        ]
    },
    "てんねん": {},
    "てんのめぐみ": {},
    "でんきにかえる": {
        "flags": [
            "undeniable"
        ]
    },
    "でんきエンジン": {},
    "とうそうしん": {},
    "とびだすなかみ": {
        "flags": [
            "undeniable"
        ]
    },
    "とれないにおい": {
        "flags": [
            "undeniable"
        ]
    },
    "どくくぐつ": {
        "flags": [
            "unreproducible"
        ]
    },
    "どくげしょう": {
        "flags": [
            "undeniable"
        ]
    },
    "どくしゅ": {},
    "どくのくさり": {},
    "どくのトゲ": {
        "flags": [
            "undeniable"
        ]
    },
    "どくぼうそう": {},
    "どしょく": {},
    "どんかん": {},
    "なまけ": {},
    "にげあし": AbilityData(),
    "にげごし": {
        "flags": [
            "undeniable"
        ]
    },
    "ぬめぬめ": {
        "flags": [
            "undeniable"
        ]
    },
    "ねつこうかん": {},
    "ねつぼうそう": {},
    "ねんちゃく": {},
    "のろわれボディ": {
        "flags": [
            "undeniable"
        ]
    },
    "はがねつかい": {},
    "はがねのせいしん": {},
    "はじまりのうみ": {
        "flags": [
            "undeniable"
        ]
    },
    "はっこう": {},
    "はとむね": {},
    "はやあし": {},
    "はやおき": {},
    "はやてのつばさ": {},
    "はらぺこスイッチ": {
        "flags": [
            "unreproducible"
        ]
    },
    "はりきり": {},
    "はりこみ": {},
    "はんすう": {
        "flags": [
            "undeniable"
        ]
    },
    "ばけのかわ": {
        "flags": [
            "unreproducible",
            "protected",
            "one_time"
        ]
    },
    "ばんけん": {},
    "ひでり": {},
    "ひとでなし": {},
    "ひひいろのこどう": {},
    "ひらいしん": {},
    "びびり": {
        "flags": [
            "undeniable"
        ]
    },
    "びんじょう": {
        "flags": [
            "undeniable"
        ]
    },
    "ふうりょくでんき": {
        "flags": [
            "undeniable"
        ]
    },
    "ふかしのこぶし": {},
    "ふくがん": {},
    "ふくつのこころ": {},
    "ふくつのたて": {
        "flags": [
            "one_time"
        ]
    },
    "ふしぎなうろこ": {},
    "ふしぎなまもり": {},
    "ふしょく": {},
    "ふとうのけん": {
        "flags": [
            "one_time"
        ]
    },
    "ふみん": {},
    "ふゆう": {},
    "ぶきよう": {},
    "へんげんじざい": {},
    "へんしょく": {
        "flags": [
            "undeniable"
        ]
    },
    "ほうし": {
        "flags": [
            "undeniable"
        ]
    },
    "ほおぶくろ": {},
    "ほのおのからだ": {
        "flags": [
            "undeniable"
        ]
    },
    "ほろびのボディ": {
        "flags": [
            "undeniable"
        ]
    },
    "ぼうおん": {},
    "ぼうじん": {},
    "ぼうだん": {},
    "まけんき": {
        "flags": [
            "undeniable"
        ]
    },
    "みずがため": {
        "flags": [
            "undeniable"
        ]
    },
    "みずのベール": {},
    "みつあつめ": {},
    "むしのしらせ": {},
    "めんえき": {},
    "もうか": {},
    "ものひろい": {},
    "もふもふ": {},
    "もらいび": {},
    "やるき": {},
    "ゆうばく": {
        "flags": [
            "undeniable"
        ]
    },
    "ゆきかき": {},
    "ゆきがくれ": {},
    "ゆきふらし": {},
    "ようりょくそ": {},
    "よちむ": {},
    "よびみず": {},
    "よわき": {},
    "りゅうのあぎと": {},
    "りんぷん": {},
    "わざわいのうつわ": {
        "flags": [
            "undeniable"
        ]
    },
    "わざわいのおふだ": {
        "flags": [
            "undeniable"
        ]
    },
    "わざわいのたま": {
        "flags": [
            "undeniable"
        ]
    },
    "わざわいのつるぎ": {},
    "わたげ": {
        "flags": [
            "undeniable"
        ]
    },
    "わるいてぐせ": {
        "flags": [
            "undeniable"
        ]
    },
    "アイスフェイス": {
        "flags": [
            "unreproducible",
            "protected"
        ]
    },
    "アイスボディ": {},
    "アナライズ": {},
    "アロマベール": {},
    "イリュージョン": {
        "flags": [
            "unreproducible"
        ]
    },
    "エアロック": {
        "flags": [
            "undeniable"
        ]
    },
    "エレキメイカー": {},
    "オーラブレイク": {},
    "カブトアーマー": {},
    "カーリーヘアー": {
        "flags": [
            "undeniable"
        ]
    },
    "クイックドロウ": {},
    "クォークチャージ": {
        "flags": [
            "unreproducible",
            "undeniable"
        ]
    },
    "クリアボディ": {},
    "グラスメイカー": AbilityData(
        handlers={
            Event.ON_SWITCH_IN: Handler(
                partial(
                    common.activate_terrain,
                    terrain="グラスフィールド",
                    count=5,
                ),
                role="source",
            )
        }
    ),
    "サイコメイカー": {},
    "サンパワー": {},
    "サーフテール": {},
    "シェルアーマー": {},
    "シンクロ": {
        "flags": [
            "undeniable"
        ]
    },
    "スイートベール": {},
    "スカイスキン": {},
    "スキルリンク": {},
    "スクリューおびれ": {},
    "スナイパー": {},
    "スロースタート": {},
    "スワームチェンジ": {
        "flags": [
            "unreproducible",
            "protected"
        ]
    },
    "ゼロフォーミング": {
        "flags": [
            "unreproducible"
        ]
    },
    "ソウルハート": {},
    "ターボブレイズ": {},
    "ダウンロード": {},
    "ダルマモード": {
        "flags": [
            "unreproducible",
            "protected"
        ]
    },
    "ダークオーラ": {
        "flags": [
            "undeniable"
        ]
    },
    "テイルアーマー": {},
    "テクニシャン": {},
    "テラスシェル": {
        "flags": [
            "unreproducible"
        ]
    },
    "テラスチェンジ": {
        "flags": [
            "unreproducible",
            "protected"
        ]
    },
    "テラボルテージ": {},
    "テレパシー": {},
    "デルタストリーム": {
        "flags": [
            "undeniable"
        ]
    },
    "トランジスタ": {},
    "トレース": {
        "flags": [
            "unreproducible"
        ]
    },
    "ナイトメア": {},
    "ノーてんき": {
        "flags": [
            "undeniable"
        ]
    },
    "ノーガード": {
        "flags": [
            "undeniable"
        ]
    },
    "ノーマルスキン": {},
    "ハドロンエンジン": {},
    "ハードロック": {},
    "バッテリー": {
        "flags": [
            "undeniable"
        ]
    },
    "バトルスイッチ": {
        "flags": [
            "unreproducible",
            "protected"
        ]
    },
    "バリアフリー": {},
    "パステルベール": {},
    "パワースポット": {
        "flags": [
            "undeniable"
        ]
    },
    "パンクロック": {},
    "ヒーリングシフト": {},
    "ビビッドボディ": {},
    "ビーストブースト": {},
    "ファントムガード": {
        "flags": [
            "undeniable"
        ]
    },
    "ファーコート": {},
    "フィルター": {},
    "フェアリーオーラ": {
        "flags": [
            "undeniable"
        ]
    },
    "フェアリースキン": {},
    "フラワーギフト": {
        "flags": [
            "unreproducible"
        ]
    },
    "フラワーベール": {},
    "フリーズスキン": {},
    "フレンドガード": {},
    "ブレインフォース": {},
    "プラス": {},
    "プリズムアーマー": {
        "flags": [
            "undeniable"
        ]
    },
    "プレッシャー": {
        "flags": [
            "undeniable"
        ]
    },
    "ヘドロえき": {
        "flags": [
            "undeniable"
        ]
    },
    "ヘヴィメタル": {},
    "ポイズンヒール": {},
    "マイティチェンジ": {
        "flags": [
            "unreproducible",
            "protected"
        ]
    },
    "マイナス": {},
    "マイペース": {},
    "マグマのよろい": {},
    "マジシャン": {},
    "マジックガード": {
        "flags": [
            "undeniable"
        ]
    },
    "マジックミラー": {},
    "マルチスケイル": {},
    "マルチタイプ": {
        "flags": [
            "unreproducible",
            "protected"
        ]
    },
    "ミイラ": {
        "flags": [
            "undeniable"
        ]
    },
    "ミストメイカー": {},
    "ミラクルスキン": {},
    "ミラーアーマー": {},
    "ムラっけ": {},
    "メガランチャー": {},
    "メタルプロテクト": {
        "flags": [
            "undeniable"
        ]
    },
    "メロメロボディ": {
        "flags": [
            "undeniable"
        ]
    },
    "ヨガパワー": {},
    "ライトメタル": {},
    "リベロ": {},
    "リミットシールド": {
        "flags": [
            "unreproducible",
            "protected",
            "undeniable"
        ]
    },
    "リーフガード": {},
    "レシーバー": {
        "flags": [
            "unreproducible"
        ]
    },
    "ＡＲシステム": {},
    "おもかげやどし": {
        "flags": [
            "unreproducible",
            "protected"
        ]
    }
}
