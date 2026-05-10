# 特性実装進捗

更新日: 2026-05-05（不適切なかたやぶりテスト削除・進捗表整合）

## 実装状況サマリ（進捗管理基準）

| 項目           | 件数 | 根拠                                                                             |
| -------------- | ---: | -------------------------------------------------------------------------------- |
| 特性総数       |  300 | `len(ABILITIES)`                                                                 |
| 実装済み       |  213 | handlers 199 件（実装対象外との重複 1 件除く 198 件）+ 実装対象外 15 件           |
| 未実装         |   87 | 300 - 213                                                                        |
| コード実装済み |  199 | `src/jpoke/data/ability.py` で `AbilityData(handlers={...})` を明示した特性      |
| 実装対象外     |   15 | ダブル専用 12 件 + 対戦に影響なし 3 件                                           |
| 仕様書あり     |  291 | `spec/ability/` にファイルあり                                                   |
| 仕様具体化済み |  291 | `spec/ability/` 内で `要確認` を含まない仕様書ファイル数                         |
| 要確認残件     |    0 | `spec/ability/` 内の `要確認` ヒット件数                                         |
| テスト実装済み |  187 | `tests/test_ability.py` に専用テストあり（かたやぶり相互作用テスト含む）          |


## 特性一覧（実装状況付き）

- 実装対象総数: 282件（x 190件 / - 92件）
- 列
    実装 : 効果処理ハンドラの実装状況
    型破適用 : 特性かたやぶりにより無効化されるか
    ガス適用 : かがくへんかガスに無効化されるか
    型破テスト : かたやぶりによる無効化テストの実施状況
    ガステスト : かがくへんかガスによる無効化テストの実施状況
- 凡例
    x = 実装済み/テスト済み
    - = 未実装/未テスト
    y = Yes
    n = No
    n/a = 適用外 (不要)


特性	仕様書	実装	テスト	型破テスト	ガステスト	型破適用	ガス適用

ARシステム	x	x	x	n/a	-	n	n
アイスフェイス	x	-	-	-	-	y	n
アイスボディ	x	x	x	n/a	n/a	n	y
あくしゅう	x	-	-	-	n/a	y	y
あついしぼう	x	x	x	x	n/a	y	y
あとだし	x	x	x	n/a	n/a	n	y
アナライズ	x	x	-	n/a	n/a	n	y
あまのじゃく	x	x	-	x	n/a	y	y
あめうけざら	x	x	x	n/a	n/a	n	y
あめふらし	x	x	x	n/a	n/a	n	y
ありじごく	x	x	x	n/a	n/a	n	y
アロマベール	x	-	-	-	n/a	y	y
いかく	x	x	x	n/a	n/a	n	y
いかりのこうら	x	-	-	-	n/a	y	y
いかりのつぼ	x	-	-	n/a	n/a	n	y
いしあたま	x	x	x	n/a	n/a	n	y
いたずらごころ	x	x	x	n/a	n/a	n	y
いろめがね	x	x	x	n/a	n/a	n	y
いわはこび	x	x	x	n/a	n/a	n	y
うのミサイル	x	-	-	n/a	-	n	n
うるおいボイス	x	-	-	-	n/a	y	y
うるおいボディ	x	-	-	-	n/a	y	y
エアロック	x	x	x	n/a	n/a	n	y
エレキメイカー	x	x	x	n/a	n/a	n	y
えんかく	x	-	-	-	n/a	y	y
おうごんのからだ	x	x	x	x	n/a	y	y
オーラブレイク	x	-	-	-	n/a	y	y
おどりこ	x	保留	-	n/a	n/a	n	y
おみとおし	x	-	-	-	n/a	y	y
おもかげやどし	x	-	-	-	n/a	y	y
おやこあい	x	x	x	n/a	n/a	n	y
おわりのだいち	x	x	x	n/a	n/a	n	y
カーリーヘアー	x	-	-	n/a	n/a	n	y
かいりきバサミ	x	x	x	x	n/a	y	y
かがくへんかガス	x	x	x	n/a	n/a	n	y
かげふみ	x	x	x	n/a	n/a	n	y
かぜのり	x	-	-	-	n/a	y	y
かそく	x	x	x	n/a	n/a	n	y
かたいツメ	x	x	x	n/a	n/a	n	y
かたやぶり	x	x	x	n/a	n/a	n	y
かちき	x	x	x	n/a	n/a	n	y
カブトアーマー	x	x	x	x	n/a	y	y
かるわざ	x	x	x	n/a	n/a	n	y
がんじょう	x	x	x		n/a	-	-
がんじょうあご	x	x	x	n/a	n/a	n	y
かんそうはだ	x	-	-	x	n/a	y	y
かんろなミツ	x	-	-	-	n/a	y	y
ききかいひ	x	x	x	n/a	n/a	n	y
きけんよち	x	-	-	-	n/a	y	y
ぎたい	x	-	-	n/a	n/a	n	y
きもったま	x	-	-	-	n/a	y	y
ぎゃくじょう	x	x	x	n/a	n/a	n	y
きゅうばん	x	x	-		n/a	-	x
きょううん	x	x	x	n/a	n/a	n	y
きよめのしお	x	x	x	x	n/a	y	y
きれあじ	x	x	x	n/a	n/a	n	y
きんしのちから	x	-	-	-	n/a	y	y
きんちょうかん	x	x	x	n/a	n/a	n	y
くいしんぼう	x	-	-	-	n/a	y	y
クイックドロウ	x	-	-	-	n/a	y	y
クォークチャージ	x	x	x	n/a	n/a	n	y
くさのけがわ	x	x	x	x	n/a	y	y
くだけるよろい	x	x	x	n/a	n/a	n	y
グラスメイカー	x	x	x	n/a	n/a	n	y
クリアボディ	x	x	x	x	n/a	y	y
くろのいななき	x	-	-	-	n/a	y	y
げきりゅう	x	x	x	n/a	n/a	n	y
こおりのりんぷん	x	x	x	x	n/a	y	y
こだいかっせい	x	x	x	n/a	n/a	n	y
こぼれダネ	x	x	x	n/a	n/a	n	y
ごりむちゅう	x	x	x	n/a	n/a	n	y
こんがりボディ	x	-	-	-	n/a	y	y
こんじょう	x	x	x	n/a	n/a	n	y
サーフテール	x	-	-	-	n/a	y	y
サイコメイカー	x	x	x	n/a	n/a	n	y
さいせいりょく	x	x	x	n/a	n/a	n	y
さまようたましい	x	x	x	n/a	n/a	n	y
さめはだ	x	x	x		n/a	-	x
サンパワー	x	x	x	x	n/a	y	y
シェルアーマー	x	-	-	-	n/a	y	y
じきゅうりょく	x	x	x	n/a	n/a	n	y
じしんかじょう	x	x	x	n/a	n/a	n	y
しぜんかいふく	x	x	x	n/a	n/a	n	y
しめりけ	x	x	x	x	n/a	y	y
しゅうかく	x	x	-	n/a	n/a	n	y
じゅうなん	x	x	x	x	n/a	y	y
じゅくせい	x	-	x	n/a	n/a	n	y
じょうききかん	x	-	x	n/a	n/a	n	y
しょうりのほし	x	-	x	n/a	n/a	n	y
じょおうのいげん	x	-	-	-	n/a	y	y
じりょく	x	x	x	n/a	n/a	n	y
しろいけむり	x	x	x	x	n/a	y	y
しろのいななき	x	-	-	-	n/a	y	y
しんがん	x	-	-	-	n/a	y	y
シンクロ	x	-	-	n/a	n/a	n	y
じんばいったい	x	-	-	n/a	-	n	n
しんりょく	x	x	x	n/a	n/a	n	y
スイートベール	x	-	-	-	n/a	y	y
すいすい	x	x	x	n/a	n/a	n	y
すいほう	x	x	x	x	n/a	y	y
スカイスキン	x	x	x	n/a	n/a	n	y
スキルリンク	x	x	-	n/a	n/a	n	y
すじがねいり	x	n/a	-	-	n/a	y	y
すてみ	x	-	-	-	n/a	y	y
スナイパー	x	x	x	n/a	n/a	n	y
すなおこし	x	x	x	n/a	n/a	n	y
すなかき	x	x	x	n/a	n/a	n	y
すながくれ	x	-	-	-	n/a	y	y
すなのちから	x	x	-	n/a	n/a	n	y
すなはき	x	-	-	n/a	n/a	n	y
すりぬけ	x	x	x	n/a	n/a	n	y
するどいめ	x	x	x	x	n/a	y	y
スロースタート	x	x	x	n/a	n/a	n	y
スワームチェンジ	x	-	-	n/a	-	n	n
せいぎのこころ	x	-	-	n/a	n/a	n	y
せいしんりょく	x	x	x	x	n/a	y	y
せいでんき	x	x	x	n/a	n/a	n	y
ぜったいねむり	x	-	-	n/a	-	n	n
ゼロフォーミング	x	-	-	-	n/a	y	y
そうしょく	x	x	x		n/a	-	x
そうだいしょう	x	-	-	-	n/a	y	y
ソウルハート	x	-	-	-	n/a	y	y
ダークオーラ	x	-	-	-	n/a	y	y
ターボブレイズ	x	x	x	n/a	n/a	n	y
たいねつ	x	x	x	x	n/a	y	y
ダウンロード	x	x	x	n/a	n/a	n	y
だっぴ	x	x	x	n/a	n/a	n	y
たんじゅん	x	x	x	x	n/a	y	y
ちからずく	x	x	x	n/a	n/a	n	y
ちからもち	x	x	x	n/a	n/a	n	y
ちくでん	x	x	x	x	n/a	y	y
ちどりあし	x	-	-	-	n/a	y	y
ちょすい	x	x	x	x	n/a	y	y
テイルアーマー	x	-	-	-	n/a	y	y
てきおうりょく	x	x	x	n/a	n/a	n	y
テクニシャン	x	x	x	n/a	n/a	n	y
てつのこぶし	x	x	x	n/a	n/a	n	y
てつのトゲ	x	x	x	n/a	n/a	n	y
テラスシェル	x	x	x	x	n/a	y	y
テラスチェンジ	x	-	-	n/a	-	n	n
テラボルテージ	x	x	x	n/a	n/a	n	y
デルタストリーム	x	x	x	n/a	n/a	n	y
でんきエンジン	x	x	x	x	n/a	y	y
でんきにかえる	x	-	-	n/a	n/a	n	y
てんきや	x	-	-	-	n/a	y	y
てんねん	x	x	x	x	n/a	y	y
てんのめぐみ	x	x	x	n/a	n/a	n	y
とうそうしん	x	-	-	-	n/a	y	y
どくくぐつ	x	-	-	-	n/a	y	y
どくげしょう	x	-	-	n/a	n/a	n	y
どくしゅ	x	x	x	n/a	n/a	n	y
どくのくさり	x	-	-	-	n/a	y	y
どくのトゲ	x	x	x	n/a	n/a	n	y
どくぼうそう	x	-	-	n/a	n/a	n	y
どしょく	x	x	x	x	n/a	y	y
トランジスタ	x	x	x	n/a	n/a	n	y
トレース	x	x	x	n/a	n/a	n	y
とれないにおい	x	-	-	n/a	n/a	n	y
どんかん	x	x	x	x	n/a	y	y
ナイトメア	x	-	-	-	n/a	y	y
なまけ	x	-	-	-	n/a	y	y
にげごし	x	x	x	n/a	n/a	n	y
ぬめぬめ	x	-	-	n/a	n/a	n	y
ねつこうかん	x	x	x	x	n/a	y	y
ねつぼうそう	x	-	-	n/a	n/a	n	y
ねんちゃく	x	x	x	x	n/a	y	y
ノーガード	x	x	x	n/a	n/a	n	y
ノーてんき	x	x	x	n/a	n/a	n	y
ノーマルスキン	x	x	x	n/a	n/a	n	y
のろわれボディ	x	-	-	n/a	n/a	n	y
ハードロック	x	x	x	x	n/a	y	y
はがねつかい	x	x	x	n/a	n/a	n	y
はがねのせいしん	x	x	x	n/a	n/a	n	y
ばけのかわ	x	x	x	x	-	y	n
はじまりのうみ	x	x	x	n/a	n/a	n	y
パステルベール	x	-	-	-	n/a	y	y
はっこう	x	-	-	-	n/a	y	y
はとむね	x	x	x	x	n/a	y	y
バトルスイッチ	x	x	x	n/a	-	n	n
ハドロンエンジン	x	x	-	n/a	n/a	n	y
はやあし	x	x	x	n/a	n/a	n	y
はやおき	x	-	-	-	n/a	y	y
はやてのつばさ	x	-	-	-	n/a	y	y
はらぺこスイッチ	x	x	x	n/a	n/a	n	y
バリアフリー	x	-	-	-	n/a	y	y
はりきり	x	x	x	n/a	n/a	n	y
はりこみ	x	x	-	n/a	n/a	n	y
パワースポット	x	n/a	x	n/a	n/a	n	y
パンクロック	x	x	x	x	n/a	y	y
ばんけん	x	-	-	-	n/a	y	y
はんすう	x	-	-	n/a	n/a	n	y
ビーストブースト	x	-	-	-	n/a	y	y
ヒーリングシフト	x	-	-	-	n/a	y	y
ひでり	x	x	x	n/a	n/a	n	y
ひとでなし	x	x	x	n/a	n/a	n	y
ひひいろのこどう	x	x	-	n/a	n/a	n	y
ビビッドボディ	x	-	-	-	n/a	y	y
びびり	x	-	-	n/a	n/a	n	y
ひらいしん	x	x	x	x	n/a	y	y
びんじょう	x	-	-	n/a	n/a	n	y
ファーコート	x	x	x	x	n/a	y	y
ファントムガード	x	x	x		n/a	x	x
フィルター	x	x	x	x	n/a	y	y
ふうりょくでんき	x	-	-	n/a	n/a	n	y
フェアリーオーラ	x	-	-	-	n/a	y	y
フェアリースキン	x	x	x	n/a	n/a	n	y
ふかしのこぶし	x	-	-	-	n/a	y	y
ぶきよう	x	x	x	n/a	n/a	n	y
ふくがん	x	x	x	n/a	n/a	n	y
ふくつのこころ	x	-	-	-	n/a	y	y
ふくつのたて	x	-	-	-	n/a	y	y
ふしぎなうろこ	x	x	x	x	n/a	y	y
ふしょく	x	x	x	n/a	n/a	n	y
ふとうのけん	x	-	-	-	n/a	y	y
ふみん	x	x	x	x	n/a	y	y
ふゆう	x	x	x	x	n/a	y	y
フラワーギフト	x	-	-	-	n/a	y	y
フラワーベール	x	-	-	-	n/a	y	y
フリーズスキン	x	x	x	n/a	n/a	n	y
プリズムアーマー	x	x	x	n/a	n/a	n	y
ブレインフォース	x	x	x	n/a	n/a	n	y
プレッシャー	x	-	-	n/a	n/a	n	y
フレンドガード	x	n/a	-	-	n/a	y	y
ヘヴィメタル	x	-	-	-	n/a	y	y
ヘドロえき	x	-	-	n/a	n/a	n	y
へんげんじざい	x	x	x	n/a	n/a	n	y
へんしょく	x	x	x	n/a	n/a	n	y
ポイズンヒール	x	x	x	n/a	n/a	n	y
ぼうおん	x	x	x	x	n/a	y	y
ほうし	x	-	-	n/a	n/a	n	y
ぼうじん	x	x	x	x	n/a	y	y
ぼうだん	x	x	x	x	n/a	y	y
ほおぶくろ	x	-	-	-	n/a	y	y
ほのおのからだ	x	x	x	n/a	n/a	n	y
ほろびのボディ	x	-	-	n/a	n/a	n	y
マイティチェンジ	x	x	x	n/a	-	n	n
マイペース	x	x	x	x	n/a	y	y
マグマのよろい	x	x	x	x	n/a	y	y
まけんき	x	x	x	n/a	n/a	n	y
マジシャン	x	x	-	n/a	n/a	n	y
マジックガード	x	x	x	n/a	n/a	n	y
マジックミラー	x	x	x	x	n/a	y	y
マルチスケイル	x	x	x	x	n/a	y	y
マルチタイプ	x	x	x	n/a	-	n	n
ミイラ	x	-	-	n/a	n/a	n	y
みずがため	x	-	-	n/a	n/a	n	y
ミストメイカー	x	x	x	n/a	n/a	n	y
みずのベール	x	x	x	x	n/a	y	y
ミラーアーマー	x	x	x	x	n/a	y	y
ミラクルスキン	x	-	-	-	n/a	y	y
むしのしらせ	x	x	x	n/a	n/a	n	y
ムラっけ	x	x	x	n/a	n/a	n	y
メガランチャー	x	x	x	n/a	n/a	n	y
メタルプロテクト	x	x	x	n/a	n/a	n	y
メロメロボディ	x	-	-	n/a	n/a	n	y
めんえき	x	x	x	x	n/a	y	y
もうか	x	x	x	n/a	n/a	n	y
ものひろい	x	-	-	-	n/a	y	y
もふもふ	x	x	x	x	n/a	y	y
もらいび	x	x	x	x	n/a	y	y
やるき	x	x	x	x	n/a	y	y
ゆうばく	x	-	-	n/a	n/a	n	y
ゆきかき	x	x	x	n/a	n/a	n	y
ゆきがくれ	x	x	x	x	n/a	y	y
ゆきふらし	x	x	x	n/a	n/a	n	y
ようりょくそ	x	x	x	n/a	n/a	n	y
ヨガパワー	x	x	x	n/a	n/a	n	y
よちむ	x	-	-	-	n/a	y	y
よびみず	x	x	x	x	n/a	y	y
よわき	x	x	x	n/a	n/a	n	y
ライトメタル	x	-	-	-	n/a	y	y
リーフガード	x	x	x	x	n/a	y	y
リベロ	x	x	x	n/a	n/a	n	y
リミットシールド	x	-	-	n/a	-	n	n
りゅうのあぎと	x	x	x	n/a	n/a	n	y
りんぷん	x	x	x	x	n/a	y	y
わざわいのうつわ	x	x	x	n/a	n/a	n	y
わざわいのおふだ	x	x	x	n/a	n/a	n	y
わざわいのたま	x	x	x	n/a	n/a	n	y
わざわいのつるぎ	x	x	x	n/a	n/a	n	y
わたげ	x	-	-	n/a	n/a	n	y
わるいてぐせ	x	x	-	n/a	n/a	n	y

## 実装保留（2件）

| 特性           | 理由           |
| イリュージョン  | 処理が複雑     |
| かわりもの      | 処理が複雑     |

## リファクタリング（2026-05-01）

### コード品質改善: ハンドラモジュール統廃合

◆ **実施内容**
- 重複するユーティリティ関数を集約: `src/jpoke/handlers/common.py`
  - `is_berry_item()` - アイテム名から木の実判定 (ability.py, move.py から統一)
  - `apply_modifier()` - 4096基準の補正値計算 (ability.py で15+ 呼び出し統一)
  - `crossed_half_hp()` - HP 50% 閾値踏破判定 (ability.py で2箇所統一)

◆ **修正対象**
- `src/jpoke/handlers/move.py`
  - `_is_berry()` 削除 → `common.is_berry_item()` に統一
  - 2 呼び出し箇所更新 (ついばむ, やきつくす)

- `src/jpoke/handlers/ability.py`
  - `_is_berry_item()`, `_apply_modifier()`, `_crossed_half_hp()` 削除
  - 45 呼び出し箇所を `common.xxx` に統一
  - 特に `_apply_modifier()` は28箇所、`_crossed_half_hp()` は2箇所、`_is_berry_item()` は1箇所

◆ **テスト検証**
- x `tests/test_ability.py`: 192/192 テスト合格
- x リグレッション: なし

◆ **将来の最適化候補**
- item.py の `modify_power_by_type()`, `modify_super_effective_damage()` の common.py 整理検討
  - 現在: item.py 内で 30+ 呼び出し (partial でデータの定義で使用)
  - 複数モジュール再利用の可能性あり（優先度: 低）

## 実装対象外特性（15件）

| 特性             | 理由           |
| ---------------- | -------------- |
| いやしのこころ　| ダブル専用     |
| おもてなし　　　| ダブル専用     |
| きみょうなくすり| ダブル専用     |
| きょうえん　　　| ダブル専用     |
| きょうせい　　　| ダブル専用     |
| しれいとう　　　| ダブル専用     |
| スクリューおびれ| ダブル専用     |
| たまひろい　　　| 対戦に影響なし |
| にげあし　　　　| 対戦に影響なし |
| みつあつめ　　　| 対戦に影響なし |
| テレパシー　　　| ダブル専用     |
| バッテリー　　　| ダブル専用     |
| プラス　　　　　| ダブル専用     |
| マイナス　　　　| ダブル専用     |
| レシーバー　　　| ダブル専用     |
