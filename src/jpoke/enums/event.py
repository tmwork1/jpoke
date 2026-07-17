"""
イベントのEnum定義
イベントの処理順の詳細は .internal/spec/turn_flow.md を参照
"""

from enum import Enum, auto


class LethalEvent(Enum):
    """致死率計算専用の制御イベント。"""
    ON_BEFORE_MOVE = auto()
    ON_BEFORE_HIT = auto()
    ON_APPLY_DAMAGE = auto()  # ダメージ適用時、HP満タン枝にのみ発火する（がんじょう・きあいのタスキ等のHP1耐え）
    ON_HIT = auto()
    ON_TURN_END = auto()
    ON_EVERY_EVENT = auto()  # イベント発火後に発火するイベント (きのみによる回復など)


class DomainEvent(Enum):
    """行動順の決定に関与するイベント。

    通常の Event とは独立して処理され、ターン開始前に行動順を確定させる。
    """

    # 素早さ実数値を計算する際に発火。ability/itemハンドラがすばやさ実数値を増減
    ON_CALC_SPEED = auto()

    # 行動順を反転させるか確認する際に発火。トリックルーム等で順序を反転
    ON_CHECK_SPEED_REVERSE = auto()

    # 技の優先度を計算する際に発火。いたずらごころ等が優先度を加算・減算
    ON_MODIFY_MOVE_PRIORITY = auto()

    # 行動順決定時に発火。あとだし等が -1 を返して後攻ティアを付与
    # value=0 が標準。低い値ほど後攻（降順ソートのため）
    ON_CALC_BACK_TIER = auto()


class Event(Enum):
    """バトルイベントの種類。

    イベントは大きく5つのカテゴリに分類される：
    - 制御系: ON_BEGIN_MOVE, ON_ABILITY_ENABLED など
    - アクション系: ON_BEFORE_ACTION, ON_SWITCH_IN など
    - ターン終了系: ON_TURN_END など
    - 状態変化系: ON_BEFORE_APPLY_AILMENT, ON_BEFORE_MODIFY_STAT など
    - チェック系: ON_MODIFY_PP_CONSUMED, ON_CHECK_FLOATING など
    - 計算系: ON_MODIFY_ACCURACY など

    行動順に関与するものは DomainEvent に分離されている。
    各イベントの発火タイミングと代表的なハンドラ例は以下のコメントを参照。
    実装ファイルへの言及は変更・分割で容易に陳腐化するため意図的に含めていない。
    実際の emit/handle 箇所は `grep "Event\\.<イベント名>"` で確認すること。
    """

    # ------------------------------------------------------------------ #
    # 制御系イベント（能力/道具の有効化、特定状態フラグ）
    # ------------------------------------------------------------------ #

    # 発火: 技実行前・action_success=True のとき
    # 用例: かたやぶり系の能力無効化・メガソーラー等の攻撃開始時フック
    ON_BEGIN_MOVE = auto()

    # 発火: 技実行後・finally ブロックで常に発火
    # 用例: かたやぶり系の能力復元・メガソーラー等の攻撃終了時フック
    ON_END_MOVE = auto()

    # 発火: ふきとばし・ほえる等の強制交代を試行
    # 用例: きゅうばん・ねをはる等で無効化
    ON_TRY_BLOW = auto()

    # 発火: 特性効果が有効化された直後
    # 用例: 即時発動系特性の起動トリガー
    ON_ABILITY_ENABLED = auto()

    # 発火: 特性効果が無効化された直後
    # 用例: かがくへんかガス等の解除トリガー
    ON_ABILITY_DISABLED = auto()

    # 発火: 道具効果が有効化された直後
    # 用例: ぶきよう解除後などの再判定トリガー
    ON_ITEM_ENABLED = auto()

    # 発火: 道具効果が無効化された直後
    # 用例: ぶきよう発動時などの無効化トリガー
    ON_ITEM_DISABLED = auto()

    # 発火: 道具を新たに保持したとき
    # 用例: 保持時即時効果・状態同期
    ON_ITEM_GAINED = auto()

    # 発火: 道具を失ったとき
    # 用例: 喪失時の後処理・状態同期
    ON_ITEM_LOST = auto()

    # ------------------------------------------------------------------ #
    # アクション系イベント
    # ------------------------------------------------------------------ #

    # 発火: 登場時・バトル開始時
    # 用例: すなおこし・いかくなど登場時能力、エントリーハザード
    ON_SWITCH_IN = auto()

    # 発火: 天候・地形が変化した直後
    # 用例: こだいかっせい・クォークチャージの再判定など
    ON_FIELD_CHANGE = auto()

    # 発火: 場効果が発動した直後
    # 用例: マジックルーム適用時のアイテム再判定など
    ON_FIELD_ACTIVATE = auto()

    # 発火: 場効果が解除される直前
    # 用例: マジックルーム終了時のアイテム再判定など
    ON_FIELD_DEACTIVATE = auto()

    # 発火: 退場直前
    # 用例: バインド状態の解除など
    ON_SWITCH_OUT = auto()

    # 発火: コマンド選択肢を構築する直前
    # 用例: 強制技・交代禁止・こだわりロックなど選択肢を制限
    ON_MODIFY_COMMAND_OPTIONS = auto()

    # 発火: 未実装（各アクション実行直前に発火する予定）
    # 用例: 未実装（強制アクション許可チェック等を想定）
    ON_BEFORE_ACTION = auto()

    # 発火: テラスタル実行直後
    # 用例: ゼロフォーミング（テラスタル時に天候・フィールドを消去）
    ON_TERASTALLIZE = auto()

    # 発火: 行動順解決後・各技実行前。予約コマンドを技に解決して発火
    # 用例: くちばしキャノンの予備動作（加熱状態を付与）
    ON_BEFORE_MOVE = auto()

    # 発火: 技を実際に適用する前
    # 用例: アンコールによる技プロパティ上書き、メトロノームなど
    ON_MODIFY_MOVE = auto()

    # 発火: 連続技の最終ヒット数を決定
    # 用例: スキルリンク・おやこあい、いかさまダイス
    ON_MODIFY_HIT_COUNT = auto()

    # 発火: 連続技のヒット毎命中判定要否を決定。ヒットループ開始前に1回だけ発火
    # 用例: いかさまダイス・スキルリンク（トリプルキック等を初回のみの命中判定にする）
    ON_MODIFY_HIT_CHECK_EACH_TIME = auto()

    # 発火: 行動実行可否の判定
    # 用例: まひ・ねむり・こおり、こんらん・ひるみ・どろぼう状態等
    ON_TRY_ACTION = auto()

    # 発火: 溜め技の1ターン目検知
    # 用例: ソーラービーム・スカイアタック・かくれる等の溜め処理
    ON_MOVE_CHARGE = auto()

    # 発火: 技選択の最終確認
    # 用例: アンコール・かいふくふうじ・ちょうはつ等による使用禁止、
    #        こだわりアイテムによるロック、サイコフィールドによる優先度技ブロック
    ON_TRY_MOVE_1 = auto()

    # 発火: 技選択後の実行直前チェック
    # 用例: 成功可否の最終確認。まもる連打失敗等の判定を追加する拡張スロット
    ON_TRY_MOVE_2 = auto()

    # 発火: 技の無効化チェック
    # 用例: タイプ相性による無効、まもる等による無効
    ON_BEFORE_APPLY_MOVE = auto()

    # 発火: みがわりへの干渉確認
    # 用例: みがわり状態への技ヒット可否
    ON_CHECK_SUBSTITUTE = auto()

    # 発火: まもる系技の判定
    # 用例: まもる・みきり・たてこもる等
    ON_CHECK_PROTECT = auto()

    # 発火: 未実装（まもる成功時の追加処理用に予約）
    # 用例: 未実装（キングシールド等の反撃処理を想定）
    ON_PROTECT_SUCCESS = auto()

    # 発火: 反射確認
    # 用例: マジックコート、マジックミラー
    ON_CHECK_REFLECT = auto()

    # 発火: 変化技命中時
    # 用例: 状態異常・ランク変化などの変化技効果適用
    ON_STATUS_HIT = auto()

    # 発火: ダメージ技命中時
    # 用例: 追加効果発動、カウンター等
    ON_HIT = auto()

    # 発火: 技使用前のHP前払い
    # 用例: みちずれ・はらきり等の反動先払い
    ON_PAY_HP = auto()

    # 発火: 計算済みダメージの上書き
    # 用例: 固定ダメージ技・ふきとばし・0ダメ調整等、まもる状態によるダメージ無効化
    ON_MODIFY_MOVE_DAMAGE = auto()

    # 発火: HP減少適用直前
    # 用例: マジックガード・いしあたま等、ダメージ適用前に値を調整する特性
    #        hp_change_reason に基づいて砂嵐ダメージ・反動ダメージ等を識別
    ON_MODIFY_NON_MOVE_DAMAGE = auto()

    # 発火: reason="poison" のHP変化適用前
    # 用例: ポイズンヒール等、どく/もうどく由来のHP変化量を補正
    ON_MODIFY_POISON_DAMAGE = auto()

    # 発火: 追加効果の実効確率を計算する直前
    # 用例: ちからずく（確率→0）、てんのめぐみ（確率×2）等
    ON_MODIFY_SECONDARY_CHANCE = auto()

    # 発火: ダメージ適用後
    # 用例: 追加効果発動、いのちがけ・カウンター等の被ダメージトリガー処理
    ON_DAMAGE_HIT = auto()

    # 発火: 命中判定に失敗したとき
    # 用例: からぶりほけん（外れ時にすばやさ+2）
    ON_MISS = auto()

    # 発火: 技実行完了直後
    # 用例: もらいび等、技実行終了後の状態管理・撤去処理
    ON_MOVE_END = auto()

    # 発火: HP変化適用後
    # 用例: にげごし等、ダメージ要因をまたいでHP閾値を監視する特性
    ON_HP_CHANGED = auto()

    # 発火: force_trigger_berry（HP閾値チェックなしにきのみ効果を強制発動）
    # 用例: ほおばる・おちゃかい等できのみを強制消費するとき専用。
    #        subject_spec="source:self" を使う
    ON_FORCE_BERRY_TRIGGER = auto()

    # 発火: きのみ消費が確定した時点（ItemManagerを経由しない消費・被弾効果も含む）
    # 用例: はんすう（次のターン終了時に同じきのみを再度食べるカウントを開始する）
    #        subject_spec="source:self" を使う
    ON_BERRY_CONSUMED = auto()

    # 発火: 技によるひんし時
    # 用例: おんねん・みちづれ等のひんし時効果
    ON_MOVE_KO = auto()

    # 発火: TurnController._run_move_phase() で、1体の行動枠（技実行 +
    #        だっしゅつボタン/ききかいひ/交代技/だっしゅつパックの割り込み交代）が
    #        完全に終わった直後。今ターンに実際に技を実行した場合のみ発火する
    #        （交代のみの枠・既に割り込みで行動権を失った枠では発火しない）。
    # 用例: おどりこ（自分以外が踊り技を成功させた直後、同じ技を自分も使う）
    ON_AFTER_ACTION_RESOLVED = auto()

    # ------------------------------------------------------------------ #
    # ターン終了イベント
    # ------------------------------------------------------------------ #

    # 発火: ターン終了フェーズ開始時
    # 用例: ほろびのうた・わるあがき強制カウント等
    ON_TURN_END = auto()

    # 発火: 未実装（最終終端イベント用に予約）
    # 用例: 未実装（全体後処理フックを想定）
    ON_END = auto()

    # ------------------------------------------------------------------ #
    # 状態変化系イベント
    # ------------------------------------------------------------------ #

    # 発火: HP回復処理の直前
    # 用例: かいふくふうじ状態による回復ブロック
    ON_MODIFY_HEAL = auto()

    # 発火: 状態異常を付与する直前
    # 用例: シンクロ・みずのベール・かんそうはだ等、
    #        ミストフィールド・エレキフィールドによる無効化
    ON_BEFORE_APPLY_AILMENT = auto()

    # 発火: 状態異常を付与した直後
    # 用例: シンクロ（状態異常反射）
    ON_APPLY_AILMENT = auto()

    # 発火: 揮発性状態を付与する直前
    # 用例: サイコフィールド・ミストフィールド等 volatile 無効化、
    #        アイスフェイス等の状態ブロック
    ON_BEFORE_APPLY_VOLATILE = auto()

    # 発火: 揮発性状態を付与した直後
    # 用例: とくせいなし等、付与直後に同期が必要な後処理
    ON_VOLATILE_START = auto()

    # 発火: 揮発性状態が終了したとき
    # 用例: 状態終了時の後処理・ハンドラ解除を呼び出す内部イベント
    ON_VOLATILE_END = auto()

    # 発火: ランク変化を適用する直前
    # 用例: ミストフィールドのランク低下防止
    ON_BEFORE_MODIFY_STAT = auto()

    # 発火: ランク変化適用後
    # 用例: まけんき・かちき等の反応
    ON_MODIFY_STAT = auto()

    # 発火: PP消費後
    # 用例: ヒメリのみ（PP が 0 になったとき PP を回復）
    ON_PP_CONSUMED = auto()

    # ------------------------------------------------------------------ #
    # チェック系イベント
    # ------------------------------------------------------------------ #

    # 発火: PP消費量を問い合わせ
    # 用例: 通常は1消費。プレッシャー等で2消費にする
    ON_MODIFY_PP_CONSUMED = auto()

    # 発火: フィールド・場の状態の残りターンを確認（EventContext専用）
    # 用例: あついいわ・さらさらいわ・しめったいわ・つめたいいわ・
    #       グランドコート・ひかりのねんど等、天候・地形・壁の持続ターン延長ハンドラ
    ON_MODIFY_DURATION = auto()

    # 発火: バインド系技の継続ターン数を設定（AttackContext専用）
    # 用例: ねばりのかぎづめ（バインド継続ターンを7ターンに固定）
    # 注意: ON_MODIFY_DURATION とは異なるコンテキスト型（AttackContext）から
    #       発火するため、1イベント=1コンテキスト型の原則に従い別イベントとしている
    ON_MODIFY_BIND_DURATION = auto()

    # 発火: 天候効果が有効かどうかを判定
    # 用例: エアロック・ノーてんき で天候効果を無効化
    ON_CHECK_WEATHER_ENABLED = auto()

    # 発火: 対象ポケモン個体が天候の影響を受けないかを判定
    # 用例: ばんのうがさ（はれ・あめ系天候の影響を無効化）subject_spec="source:self"
    ON_CHECK_WEATHER_IMMUNE = auto()

    # 発火: 地面技の着地確認等
    # 用例: マグネットライズ・テレキネシス等で浮遊判定を返す、
    #        じゅうりょく発動中は全ポケモンを接地扱いにする
    ON_CHECK_FLOATING = auto()

    # 発火: エントリーハザード免疫チェック
    # 用例: あつぞこブーツ等 subject_spec="source:self"
    ON_CHECK_HAZARD_IMMUNE = auto()

    # 発火: 逃げ・交代可否
    # 用例: かげふみ・ありじごく等のトラップ能力、まきつく・くさむすび等バインド状態
    ON_CHECK_TRAPPED = auto()

    # 発火: いかく等の割り込み処理で怯え確認
    # 用例: マイペース・にげごし等で怯えを無効化
    ON_CHECK_NERVOUS = auto()

    # 発火: 特性を無効化する直前
    # 用例: とくせいガード（True を返して無効化をブロック）subject_spec="source:self"
    ON_CHECK_ABILITY_DISABLE = auto()

    # 発火: アイテムの交換・奪取・除去可否を判定
    # 用例: ねんちゃく
    ON_CHECK_ITEM_CHANGE = auto()

    # 発火: 技タイプを書き換える
    # 用例: ノーマルスキン・フェアリースキン等のタイプ変換能力、
    #        プレート・Zクリスタル等によるタイプ変換
    ON_MODIFY_MOVE_TYPE = auto()

    # 発火: 技分類を書き換える
    # 用例: フォトンゲイザー等の分類変換能力
    ON_MODIFY_MOVE_CATEGORY = auto()

    # 発火: みがわりへのヒット可否（音技・bypass_substituteフラグ技はこのイベントより前に
    #        move_executor 側で直接判定される）
    # 用例: すりぬけ等 subject_spec="attacker:self"
    ON_CHECK_HIT_SUBSTITUTE = auto()

    # 発火: 接触判定確認
    # 用例: ほのおのからだ・さめはだ等、接触技に反応する能力
    ON_CHECK_CONTACT = auto()

    # 発火: 相手の接触を受けたことに反応する効果の発動可否確認
    # 用例: ぼうごパット。攻撃者自身の接触に由来する効果には影響しない
    ON_CHECK_CONTACT_REACTION = auto()

    # ------------------------------------------------------------------ #
    # 計算系イベント
    # ------------------------------------------------------------------ #

    # 発火: 命中率を計算
    # 用例: にらみつける・かたくなる等の命中修正、ゆき・すなあらし等の天候命中補正
    ON_MODIFY_ACCURACY = auto()

    # 発火: 命中チェック中のACC/EVAランク補正値を問い合わせ
    # 用例: するどいめ等による回避ランク無視
    ON_GET_STAT_RANK = auto()

    # 発火: バインド付与時、AttackContextで倍率を確定する
    # 用例: しめつけバンドによるバインドダメージ増加
    ON_MODIFY_BIND_DAMAGE = auto()

    # 発火: 急所ランクを計算
    # 用例: きあいだめ・スコープレンズ等による急所ランク加算
    ON_CALC_CRITICAL_RANK = auto()

    # 発火: 急所確率を計算
    # 用例: きあいだめ・スコープレンズ等による急所確率加算
    ON_MODIFY_CRITICAL_RATE = auto()

    # 発火: 技の威力倍率を計算
    # 用例: てきおうりょく・ちからづく等、テラインブーストなど
    ON_CALC_POWER_MODIFIER = auto()

    # 発火: 攻撃側のランク補正値を計算
    # 用例: てんねん等による攻撃ランク無視
    ON_CALC_ATK_RANK_MODIFIER = auto()

    # 発火: 攻撃側の実数値＋ランク補正を計算
    # 用例: こだわりハチマキ等の攻撃倍率、各種強化アイテム
    ON_CALC_ATK_MODIFIER = auto()

    # 発火: 防御側の実数値＋ランク補正を計算
    # 用例: グラスフィールドでの物理防御上昇等
    ON_CALC_DEF_MODIFIER = auto()

    # 発火: 防御側のランク補正値を計算
    # 用例: てんねん等による防御ランク無視
    ON_CALC_DEF_RANK_MODIFIER = auto()

    # 発火: 攻撃側のタイプ一致・テラスタル補正を計算
    # 用例: てきおうりょく等によるSTAB 2倍化
    ON_CALC_ATK_TYPE_MODIFIER = auto()

    # 発火: 防御側のタイプ相性倍率を計算
    # 用例: フォレストカース等のタイプ追加
    ON_CALC_DEF_TYPE_MODIFIER = auto()

    # 発火: やけどによる物理ダメージ半減を計算
    # 用例: やけど状態の0.5倍適用、こんじょう等でやけど補正を無効化
    ON_CALC_BURN_MODIFIER = auto()

    # 発火: 汎用ダメージ倍率を計算
    # 用例: テライン・天候によるダメージ補正
    ON_CALC_DAMAGE_MODIFIER = auto()

    # 発火: まもる系の軽減率を計算
    # 用例: まもる形態ごとの防御倍率ハンドラ（0倍・0.25倍等）
    ON_CALC_PROTECT_MODIFIER = auto()

    # 発火: 未実装（最終ダメージ倍率を計算用に予約）
    # 用例: 未実装（いのちのたま・たつじんのおび等の最終倍率アイテム）
    ON_CALC_FINAL_DAMAGE_MODIFIER = auto()

    # 発火: リフレクター等の壁を貫通するか問い合わせ（AttackContext）
    # 用例: すりぬけ等 subject_spec="attacker:self"
    ON_CHECK_BYPASS_SCREEN = auto()

    # 発火: しんぴのまもり・しろいきり等の耐性を貫通するか問い合わせ（EventContext）
    # 用例: すりぬけ等 subject_spec="source:self"
    ON_CHECK_BYPASS_STATUS_GUARD = auto()

    # 発火: 吸収技の回収量、ちからをすいとるの回復量、
    #        アクアリング・ねをはる・やどりぎのタネの回復量
    # EventContext 専用イベント（AttackContext から発火する箇所は回復対象を
    # source に正規化して EventContext で発火する。#ON_CALC_DRAIN 参照）
    # 用例: おおきなねっこ subject_spec="source:self"
    ON_CALC_DRAIN = auto()
