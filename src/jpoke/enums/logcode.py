from enum import Enum, auto


class LogCode(Enum):
    # ルール関連
    GAME_STARTED = auto()  # ゲーム開始
    GAME_WON = auto()  # 勝利
    GAME_LOST = auto()  # 敗北

    # 交代関連
    SWITCHED_IN = auto()  # 交代出場
    SWITCHED_OUT = auto()  # 交代退場

    # 技関連
    ACTION_BLOCKED = auto()  # 行動不能（まひ・ねむり等）
    PP_CONSUMED = auto()  # PP消費
    MOVE_FAILED = auto()  # 発動失敗
    MOVE_REFLECTED = auto()  # 反射（マジックコート・リフレクター等）
    MOVE_MISSED = auto()  # 技が外れた
    MOVE_IMMUNED = auto()  # 技が無効化された
    MOVE_REVEALED = auto()  # 相手の技を公開（よちむ等）

    CRITICAL_HIT = auto()  # 急所に当たった

    # HP関連
    HP_CHANGED = auto()  # HP変化
    HEAL_BLOCKED = auto()  # 回復ブロック

    # 能力値関連
    STAT_CHANGED = auto()  # 能力値変化
    STAT_CHANGE_BLOCKED = auto()  # 能力値変化ブロック（まもる等）

    # 特性関連
    ABILITY_TRIGGERED = auto()  # 特性発動
    ABILITY_EFFECT_ENDED = auto()  # 特性の時限効果終了（スロースタート・こだいかっせい等）

    # アイテム関連
    ITEM_TRIGGERED = auto()  # アイテム発動
    ITEM_GAINED = auto()  # アイテム獲得
    ITEM_LOST = auto()  # アイテム喪失
    ITEM_REVEALED = auto()  # 相手の持ち物を公開（おみとおし等）

    # 状態異常関連
    AILMENT_APPLIED = auto()  # 状態異常付与
    AILMENT_REMOVED = auto()  # 状態異常回復
    AILMENT_PREVENTED = auto()  # 状態異常付与ブロック

    # 揮発状態関連
    VOLATILE_IMMUNE = auto()  # 揮発状態無効化
    VOLATILE_APPLIED = auto()  # 揮発状態付与
    VOLATILE_REMOVED = auto()  # 揮発状態解除
    VOLATILE_DISPLAY = auto()  # 揮発状態の宣言 (こんらんなど)
    VOLATILE_PREVENTED = auto()  # 揮発状態の付与ブロック

    PROTECT_SUCCEEDED = auto()  # まもる成功
    PROTECT_FAILED = auto()  # まもる失敗
    SUBSTITUTE_HIT = auto()  # みがわりにヒット

    # 場関連
    FIELD_STARTED = auto()  # 場の状態開始
    FIELD_STACKED = auto()  # 場の状態の層数増加（まきびし・どくびし等の重ね掛け）
    FIELD_ENDED = auto()  # 場の状態終了

    # その他
    TERASALLIZED = auto()  # テラスタル化
    MEGA_EVOLVED = auto()  # メガシンカ
