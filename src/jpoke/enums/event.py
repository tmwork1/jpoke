"""
イベントのEnum定義
イベントの処理順の詳細は docs/spec/turn_flow.md を参照
"""

from enum import Enum, auto


class DomainEvent(Enum):
    """行動順の決定に関与するイベント（core/speed.py で使用）。

    通常の Event とは独立して処理され、ターン開始前に行動順を確定させる。
    """

    # emit: core/speed.py  handle: ability/item handlers がすばやさ実数値を増減
    ON_CALC_SPEED = auto()

    # emit: core/speed.py  handle: data/field.py トリックルームで順序を反転
    ON_CHECK_SPEED_REVERSE = auto()

    # emit: core/speed.py  handle: DomainEvent として優先度を加算・減算（いたずらごころ等）
    ON_MODIFY_MOVE_PRIORITY = auto()

    # emit: core/speed.py（行動順決定時）  handle: あとだし等が -1 を返して後攻ティアを付与
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
    各イベントの emit 箇所と代表的な handle 箇所は以下のコメントを参照。
    """

    # ------------------------------------------------------------------ #
    # 制御系イベント（能力/道具の有効化、特定状態フラグ）
    # ------------------------------------------------------------------ #

    # emit: core/move_executor.py（技実行前・action_success=True のとき）
    # handle: ability.py（かたやぶり系の能力無効化・メガソーラー等の攻撃開始時フック）
    ON_BEGIN_MOVE = auto()

    # emit: core/move_executor.py（技実行後・finally ブロックで常に発火）
    # handle: ability.py（かたやぶり系の能力復元・メガソーラー等の攻撃終了時フック）
    ON_END_MOVE = auto()

    # emit: core/move_executor.py（ふきとばし・ほえる等の強制交代を試行）
    # handle: ability.py / volatile.py（きゅうばん・ねをはる等で無効化）
    ON_TRY_BLOW = auto()

    # emit: core/battle.py（特性効果が有効化された直後）
    # handle: ability.py（即時発動系特性の起動トリガー）
    ON_ABILITY_ENABLED = auto()

    # emit: core/battle.py（特性効果が無効化された直後）
    # handle: ability.py（かがくへんかガス等の解除トリガー）
    ON_ABILITY_DISABLED = auto()

    # emit: core/battle.py（道具効果が有効化された直後）
    # handle: item.py / ability.py（ぶきよう解除後などの再判定トリガー）
    ON_ITEM_ENABLED = auto()

    # emit: core/battle.py（道具効果が無効化された直後）
    # handle: item.py / ability.py（ぶきよう発動時などの無効化トリガー）
    ON_ITEM_DISABLED = auto()

    # emit: core/battle.py（道具を新たに保持したとき）
    # handle: item.py（保持時即時効果・状態同期）
    ON_ITEM_GAINED = auto()

    # emit: core/battle.py（道具を失ったとき）
    # handle: item.py（喪失時の後処理・状態同期）
    ON_ITEM_LOST = auto()

    # ------------------------------------------------------------------ #
    # アクション系イベント
    # ------------------------------------------------------------------ #

    # emit: core/switch.py（登場時・バトル開始時）
    # handle: ability.py（すなおこし・いかくなど登場時能力）, field.py（エントリーハザード）
    ON_SWITCH_IN = auto()

    # emit: core/field_manager.py（天候・地形が変化した直後）
    # handle: ability.py（こだいかっせい・クォークチャージの再判定）など
    ON_FIELD_CHANGE = auto()

    # emit: core/field_manager.py（場効果が発動した直後）
    # handle: data/field.py（マジックルーム適用時のアイテム再判定など）
    ON_FIELD_ACTIVATE = auto()

    # emit: core/field_manager.py（場効果が解除される直前）
    # handle: data/field.py（マジックルーム終了時のアイテム再判定など）
    ON_FIELD_DEACTIVATE = auto()

    # emit: core/battle.py（特性有効状態変化後の再判定要求）
    # handle: ability.py（こだいかっせい・クォークチャージの再判定）
    ON_REFRESH_PARADOX_BOOST = auto()

    # emit: core/switch.py（退場直前）
    # handle: volatile.py（バインド状態の解除など）
    ON_SWITCH_OUT = auto()

    # emit: core/battle.py（コマンド選択肢を構築する直前）
    # handle: volatile.py（強制技・交代禁止・こだわりロックなど選択肢を制限）
    ON_MODIFY_COMMAND_OPTIONS = auto()

    # emit: 未実装（各アクション実行直前に発火する予定）
    # handle: 未実装（強制アクション許可チェック等を想定）
    ON_BEFORE_ACTION = auto()

    # emit: core/turn_controller.py（テラスタル実行直後）
    # handle: ability.py（ゼロフォーミング: テラスタル時に天候・フィールドを消去）
    ON_TERASTALLIZE = auto()

    # emit: core/turn_controller.py（技フェーズ開始直前・ターン内に1回）
    # handle: 現時点でハンドラ登録なし（将来の拡張用スロット）
    ON_BEFORE_MOVE = auto()

    # emit: core/move_executor.py（技を実際に適用する前）
    # handle: volatile.py（アンコールによる技プロパティ上書き、メトロノームなど）
    ON_MODIFY_MOVE = auto()

    # emit: core/move_executor.py（連続技の最終ヒット数を決定）
    # handle: ability.py（スキルリンク・おやこあい）/ item.py（いかさまダイス）
    ON_MODIFY_HIT_COUNT = auto()

    # emit: core/move_executor.py（行動実行可否の判定）
    # handle: ailment.py（まひ・ねむり・こおり）, volatile.py（こんらん・ひるみ・どろぼう状態等）
    ON_TRY_ACTION = auto()

    # emit: core/move_executor.py（溜め技の1ターン目検知）
    # handle: data/move.py（ソーラービーム・スカイアタック・かくれる等の溜め処理）
    ON_MOVE_CHARGE = auto()

    # emit: core/move_executor.py（技選択の最終確認）
    # handle: volatile.py（アンコール・かいふくふうじ・ちょうはつ等による使用禁止）
    #          data/move.py（こだわりアイテムによるロック）
    #          data/field.py（サイコフィールドによる優先度技ブロック）
    ON_TRY_MOVE_1 = auto()

    # emit: core/move_executor.py（技選択後の実行直前チェック）
    # handle: volatile.py（成功可否の最終確認。まもる連打失敗等の判定を追加する拡張スロット）
    ON_TRY_MOVE_2 = auto()

    # emit: core/move_executor.py（技の無効化チェック）
    # handle: data/move.py（タイプ相性による無効）, volatile.py（まもる等による無効）
    ON_BEFORE_APPLY_MOVE = auto()

    # emit: core/move_executor.py（みがわりへの干渉確認）
    # handle: volatile.py（みがわり状態への技ヒット可否）
    ON_CHECK_SUBSTITUTE = auto()

    # emit: core/move_executor.py（まもる系技の判定）
    # handle: handlers/volatile.py（まもる・みきり・たてこもる等）
    ON_CHECK_PROTECT = auto()

    # emit: 未実装（まもる成功時の追加処理用に予約）
    # handle: 未実装（キングシールド等の反撃処理を想定）
    ON_PROTECT_SUCCESS = auto()

    # emit: core/move_executor.py（反射確認）
    # handle: volatile.py（マジックコート）, ability.py（マジックミラー）
    ON_CHECK_REFLECT = auto()

    # emit: core/move_executor.py（変化技命中時）
    # handle: data/move.py（状態異常・ランク変化などの変化技効果適用）
    ON_STATUS_HIT = auto()

    # emit: core/move_executor.py（ダメージ技命中時）
    # handle: data/move.py（追加効果発動）, volatile.py（カウンター等）
    ON_HIT = auto()

    # emit: core/move_executor.py（技使用前のHP前払い）
    # handle: data/move.py（みちずれ・はらきり等の反動先払い）
    ON_PAY_HP = auto()

    # emit: core/move_executor.py（計算済みダメージの上書き）
    # handle: data/move.py（固定ダメージ技・ふきとばし・0ダメ調整等）
    #          volatile.py（まもる状態によるダメージ無効化）
    ON_MODIFY_MOVE_DAMAGE = auto()

    # emit: core/pokemon_state.py（HP減少適用直前）
    # handle: ability.py（マジックガード・いしあたま等、ダメージ適用前に値を調整する特性）
    #         hp_change_reason に基づいて砂嵐ダメージ・反動ダメージ等を識別
    ON_MODIFY_NON_MOVE_DAMAGE = auto()

    # emit: core/pokemon_state.py（reason="poison" のHP変化適用前）
    # handle: ability.py（ポイズンヒール等、どく/もうどく由来のHP変化量を補正）
    ON_MODIFY_POISON_DAMAGE = auto()

    # emit: handlers/common.py（追加効果の実効確率を計算する直前）
    # handle: ability.py（ちからずく: 確率→0, てんのめぐみ: 確率×2 等）
    ON_MODIFY_SECONDARY_CHANCE = auto()

    # emit: core/move_executor.py（ダメージ適用後）
    # handle: volatile.py（いのちがけ・カウンター等、被ダメージトリガー処理）
    ON_DAMAGE_HIT = auto()

    # emit: core/move_executor.py（命中判定に失敗したとき）
    # handle: item.py（からぶりほけん: 外れ時にすばやさ+2）
    ON_MISS = auto()

    # emit: core/move_executor.py（技実行完了直後）
    # handle: ability.py（もらいび等、技実行終了後の状態管理・撤去処理）
    ON_MOVE_END = auto()

    # emit: core/pokemon_state.py（HP変化適用後）
    # handle: ability.py（にげごし等、ダメージ要因をまたいでHP閾値を監視する特性）
    ON_HP_CHANGED = auto()

    # emit: core/battle.py（force_trigger_berry）
    # handle: item.py（HP閾値チェックなしにきのみ効果を強制発動。
    #         ほおばる・おちゃかい等できのみを強制消費するとき専用）
    #         subject_spec="source:self" を使う
    ON_FORCE_BERRY_TRIGGER = auto()

    # emit: core/move_executor.py（技によるひんし時）
    # handle: volatile.py（おんねん・みちづれ等のひんし時効果）
    ON_MOVE_KO = auto()

    # ------------------------------------------------------------------ #
    # ターン終了イベント
    # ------------------------------------------------------------------ #

    # emit: core/turn_controller.py（ターン終了フェーズ開始時）
    # handle: volatile.py（ほろびのうた・わるあがき強制カウント等）
    ON_TURN_END = auto()

    # emit: 未実装（最終終端イベント用に予約）
    # handle: 未実装（全体後処理フックを想定）
    ON_END = auto()

    # ------------------------------------------------------------------ #
    # 状態変化系イベント
    # ------------------------------------------------------------------ #

    # emit: core/battle.py（HP回復処理の直前）
    # handle: volatile.py（かいふくふうじ状態による回復ブロック）
    ON_MODIFY_HEAL = auto()

    # emit: core/pokemon_state.py（状態異常を付与する直前）
    # handle: ability.py（シンクロ・みずのベール・かんそうはだ等）
    #          data/field.py（ミストフィールド・エレキフィールドによる無効化）
    ON_BEFORE_APPLY_AILMENT = auto()

    # emit: core/ailment_manager.py（状態異常を付与した直後）
    # handle: ability.py（シンクロ: 状態異常反射）
    ON_APPLY_AILMENT = auto()

    # emit: core/pokemon_state.py（揮発性状態を付与する直前）
    # handle: data/field.py（サイコフィールド・ミストフィールド等 volatile 無効化）
    #          volatile.py（アイスフェイス等の状態ブロック）
    ON_BEFORE_APPLY_VOLATILE = auto()

    # emit: core/pokemon_state.py（揮発性状態を付与した直後）
    # handle: volatile.py（とくせいなし等、付与直後に同期が必要な後処理）
    ON_VOLATILE_START = auto()

    # emit: core/pokemon_state.py（揮発性状態が終了したとき）
    # handle: volatile.py（状態終了時の後処理・ハンドラ解除を呼び出す内部イベント）
    ON_VOLATILE_END = auto()

    # emit: core/battle.py（ランク変化を適用する直前）
    # handle: data/field.py（ミストフィールドのランク低下防止）
    ON_BEFORE_MODIFY_STAT = auto()

    # emit: core/status_manager.py（ランク変化適用後）
    # handle: ability.py（まけんき・かちき等の反応）
    ON_MODIFY_STAT = auto()

    # emit: core/move_executor.py（PP消費後）
    # handle: item.py（ヒメリのみ: PP が 0 になったとき PP を回復）
    ON_PP_CONSUMED = auto()

    # ------------------------------------------------------------------ #
    # チェック系イベント
    # ------------------------------------------------------------------ #

    # emit: handlers/move.py（PP消費量を問い合わせ）
    # handle: data/move.py（通常は1消費。プレッシャー等で2消費にする）
    ON_MODIFY_PP_CONSUMED = auto()

    # emit: core/field_manager.py（フィールド・場の状態の残りターンを確認）
    #        handlers/move_attack.py（バインド系技の継続ターン数を設定）
    # handle: 各フィールド・バインドの持続ターン管理ハンドラ
    ON_MODIFY_DURATION = auto()

    # emit: core/battle.py（天候効果が有効かどうかを判定）
    # handle: ability.py（エアロック・ノーてんき で天候効果を無効化）
    ON_CHECK_WEATHER_ENABLED = auto()

    # emit: core/pokemon_state.py（地面技の着地確認等）
    # handle: volatile.py（マグネットライズ・テレキネシス等で浮遊判定を返す）
    #          data/field.py（じゅうりょく発動中は全ポケモンを接地扱いにする）
    ON_CHECK_FLOATING = auto()

    # emit: core/pokemon_query.py（エントリーハザード免疫チェック）
    # handle: item.py（あつぞこブーツ等）subject_spec="source:self"
    ON_CHECK_HAZARD_IMMUNE = auto()

    # emit: core/pokemon_state.py（逃げ・交代可否）
    # handle: ability.py（かげふみ・ありじごく等のトラップ能力）
    #          volatile.py（まきつく・くさむすび等バインド状態）
    ON_CHECK_TRAPPED = auto()

    # emit: core/pokemon_state.py（いかく等の割り込み処理で怯え確認）
    # handle: ability.py（マイペース・にげごし等で怯えを無効化）
    ON_CHECK_NERVOUS = auto()

    # emit: core/ability_manager.py（特性を無効化する直前）
    # handle: item.py（とくせいガード: True を返して無効化をブロック）subject_spec="source:self"
    ON_CHECK_ABILITY_DISABLE = auto()

    # emit: core/battle.py（アイテムの交換・奪取・除去可否を判定）
    # handle: ability.py（ねんちゃく）
    ON_CHECK_ITEM_CHANGE = auto()

    # emit: core/move_executor.py（技タイプを書き換える）
    # handle: ability.py（ノーマルスキン・フェアリースキン等のタイプ変換能力）
    #          data/item.py（プレート・Zクリスタル等によるタイプ変換）
    ON_MODIFY_MOVE_TYPE = auto()

    # emit: core/move_executor.py（技分類を書き換える）
    # handle: ability.py（フォトンゲイザー等の分類変換能力）
    ON_MODIFY_MOVE_CATEGORY = auto()

    # emit: core/move_executor.py（みがわりへのヒット可否）
    # handle: 音技・パンチ系など代替物を貫通する技のハンドラ
    ON_CHECK_HIT_SUBSTITUTE = auto()

    # emit: core/pokemon_state.py（接触判定確認）
    # handle: ability.py（ほのおのからだ・さめはだ等、接触技に反応する能力）
    ON_CHECK_CONTACT = auto()

    # ------------------------------------------------------------------ #
    # 計算系イベント
    # ------------------------------------------------------------------ #

    # emit: core/move_executor.py（命中率を計算）
    # handle: volatile.py（にらみつける・かたくなる等の命中修正）
    #          data/field.py（ゆき・すなあらし等の天候命中補正）
    ON_MODIFY_ACCURACY = auto()

    # emit: core/move_executor.py（命中チェック中のACC/EVAランク補正値を問い合わせ）
    # handle: data/ability.py（するどいめ等による回避ランク無視）
    ON_GET_STAT_RANK = auto()

    # emit: 未実装（バインドダメージの倍率調整用に予約）
    # handle: 未実装（しめつけバンド等によるダメージ増加を想定）
    ON_MODIFY_BIND_DAMAGE = auto()

    # emit: core/move_executor.py（急所ランクを計算）
    # handle: volatile.py（きあいだめ・スコープレンズ等による急所ランク加算）
    ON_CALC_CRITICAL_RANK = auto()

    # emit: core/move_executor.py（急所確率を計算）
    # handle: volatile.py（きあいだめ・スコープレンズ等による急所確率加算）
    ON_MODIFY_CRITICAL_RATE = auto()

    # emit: core/damage.py（技の威力倍率を計算）
    # handle: ability.py（てきおうりょく・ちからづく等）
    #          data/field.py・volatile.py（テラインブーストなど）
    ON_CALC_POWER_MODIFIER = auto()

    # emit: core/damage.py（攻撃側のランク補正値を計算）
    # handle: ability.py（てんねん等による攻撃ランク無視）
    ON_CALC_ATK_RANK_MODIFIER = auto()

    # emit: core/damage.py（攻撃側の実数値＋ランク補正を計算）
    # handle: ability.py（こだわりハチマキ等の攻撃倍率）
    #          data/item.py（各種強化アイテム）
    ON_CALC_ATK_MODIFIER = auto()

    # emit: core/damage.py（防御側の実数値＋ランク補正を計算）
    # handle: data/field.py（グラスフィールドでの物理防御上昇等）
    ON_CALC_DEF_MODIFIER = auto()

    # emit: core/damage.py（防御側のランク補正値を計算）
    # handle: ability.py（てんねん等による防御ランク無視）
    ON_CALC_DEF_RANK_MODIFIER = auto()

    # emit: core/damage.py（攻撃側のタイプ一致・テラスタル補正を計算）
    # handle: ability.py（てきおうりょく等によるSTAB 2倍化）
    ON_CALC_ATK_TYPE_MODIFIER = auto()

    # emit: core/damage.py（防御側のタイプ相性倍率を計算）
    # handle: volatile.py（フォレストカース等のタイプ追加）
    ON_CALC_DEF_TYPE_MODIFIER = auto()

    # emit: core/damage.py（やけどによる物理ダメージ半減を計算）
    # handle: ailment.py（やけど状態の0.5倍適用）
    #          ability.py（こんじょう等でやけど補正を無効化）
    ON_CALC_BURN_MODIFIER = auto()

    # emit: core/damage.py（汎用ダメージ倍率を計算）
    # handle: data/field.py（テライン・天候によるダメージ補正）
    ON_CALC_DAMAGE_MODIFIER = auto()

    # emit: core/damage.py（まもる系の軽減率を計算）
    # handle: まもる形態ごとの防御倍率ハンドラ（0倍・0.25倍等）
    ON_CALC_PROTECT_MODIFIER = auto()

    # emit: 未実装（最終ダメージ倍率を計算用に予約）
    # handle: 未実装（いのちのたま・たつじんのおび等の最終倍率アイテム）
    ON_CALC_FINAL_DAMAGE_MODIFIER = auto()

    # emit: AttackContext（リフレクター等の壁を貫通するか問い合わせ）
    # handle: ability.py（すりぬけ等）subject_spec="attacker:self"
    ON_CHECK_BYPASS_SCREEN = auto()

    # emit: EventContext（しんぴのまもり・しろいきり等の耐性を貫通するか問い合わせ）
    # handle: ability.py（すりぬけ等）subject_spec="source:self"
    ON_CHECK_BYPASS_STATUS_GUARD = auto()

    # emit: 未実装（吸収技のHP回収量計算用に予約）
    # handle: 未実装（おおきなねっこ等による回収量増加を想定）
    ON_CALC_DRAIN = auto()
