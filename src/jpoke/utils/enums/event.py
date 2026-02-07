"""
イベントのEnum定義
イベントの処理順の詳細は docs/spec/turn_flow.md を参照
"""

from enum import Enum, auto


class Event(Enum):
    """バトルイベントの種類

    イベントは大きく3つのカテゴリに分類される：
    - アクション系: ON_BEFORE_ACTION, ON_SWITCH_IN など
    - チェック系: ON_CHECK_PP_CONSUMED, ON_CHECK_FLOATING など
    - 計算系: ON_CALC_SPEED, ON_CALC_ACCURACY など
    """
    # アクション系イベント（emit/handlerの主な参照先）
    ON_BEFORE_ACTION = auto()  # emit: core/turn_controller.py; handlers: data/ailment.py,data/volatile.py
    ON_SWITCH_IN = auto()  # emit: core/switch_manager.py; handlers: data/ability.py,data/field.py
    ON_SWITCH_OUT = auto()  # emit: core/switch_manager.py
    ON_BEFORE_MOVE = auto()  # emit: core/turn_controller.py; handlers: data/volatile.py
    ON_TRY_ACTION = auto()  # emit: core/move_executor.py | spec: turn_flow.md ON_TRY_ACTION
    ON_CONSUME_PP = auto()  # emit: core/move_executor.py | spec: turn_flow.md ON_CONSUME_PP
    ON_TRY_MOVE = auto()  # emit: core/move_executor.py | spec: turn_flow.md ON_TRY_MOVE
    ON_TRY_IMMUNE = auto()  # emit: core/move_executor.py | spec: turn_flow.md ON_TRY_IMMUNE
    ON_CHECK_SUBSTITUTE = auto()  # emit: core/move_executor.py | spec: turn_flow.md ON_TRY_IMMUNE Priority 30
    ON_CHECK_PROTECT = auto()  # emit: core/move_executor.py | spec: turn_flow.md ON_TRY_MOVE Priority 100
    ON_CHECK_INVULNERABLE = auto()  # emit: core/move_executor.py | spec: turn_flow.md ON_TRY_MOVE Priority 100
    ON_CHECK_REFLECT = auto()  # emit: core/move_executor.py | spec: turn_flow.md ON_TRY_MOVE Priority 100
    ON_HIT = auto()  # emit: core/move_executor.py | spec: turn_flow.md ON_HIT
    ON_PAY_HP = auto()  # emit: core/move_executor.py | spec: turn_flow.md ON_PAY_HP
    ON_MODIFY_DAMAGE = auto()  # emit: core/move_executor.py | spec: turn_flow.md ON_MODIFY_DAMAGE
    ON_BEFORE_DAMAGE_APPLY = auto()  # emit: core/move_executor.py | spec: turn_flow.md ON_BEFORE_DAMAGE_APPLY
    ON_FAINT = auto()  # emit: core/move_executor.py | spec: turn_flow.md ON_FAINT
    ON_MOVE_SECONDARY = auto()  # 未使用
    ON_DAMAGE_1 = auto()  # emit: core/move_executor.py; handlers: data/item.py
    ON_DAMAGE_2 = auto()  # emit: core/move_executor.py
    ON_AFTER_PIVOT = auto()  # 未使用

    # ターン終了イベント
    ON_TURN_END_1 = auto()  # emit: core/turn_controller.py; handlers: data/field.py,data/ailment.py,data/volatile.py
    ON_TURN_END_2 = auto()  # emit: core/turn_controller.py; handlers: data/field.py,data/volatile.py
    ON_TURN_END_3 = auto()  # emit: core/turn_controller.py; handlers: data/ailment.py,data/volatile.py
    ON_TURN_END_4 = auto()  # emit: core/turn_controller.py; handlers: data/ailment.py,data/volatile.py
    ON_TURN_END_5 = auto()  # emit: core/turn_controller.py; handlers: data/volatile.py
    ON_TURN_END_6 = auto()  # emit: core/turn_controller.py

    ON_MODIFY_STAT = auto()  # emit: core/battle.py modify_stats; handlers: data/ability.py
    ON_END = auto()  # 未使用

    # 状態異常・能力変化前イベント
    ON_BEFORE_APPLY_AILMENT = auto()  # emit: model/pokemon.py apply_ailment; handlers: data/ability.py,data/field.py
    ON_BEFORE_APPLY_VOLATILE = auto()  # emit: model/pokemon.py apply_volatile; handlers: data/field.py
    ON_BEFORE_MODIFY_STAT = auto()  # 未使用

    # チェック系イベント
    ON_CHECK_PP_CONSUMED = auto()  # emit: handlers/move.py consume_pp
    ON_CHECK_DURATION = auto()  # emit: core/field_manager.py; handlers: data/item.py
    ON_CHECK_FLOATING = auto()  # emit: model/pokemon.py is_floating; handlers: data/field.py
    ON_CHECK_TRAPPED = auto()  # emit: model/pokemon.py is_trapped; handlers: data/ability.py,data/volatile.py,data/item.py
    ON_CHECK_NERVOUS = auto()  # emit: model/pokemon.py is_nervous; handlers: data/ability.py
    ON_CHECK_MOVE_TYPE = auto()  # emit: model/pokemon.py effective_move_type
    ON_CHECK_MOVE_CATEGORY = auto()  # emit: model/pokemon.py effective_move_category
    ON_CHECK_PRIORITY_VALID = auto()  # emit: core/move_executor.py; handlers: data/field.py

    # 計算系イベント
    ON_CALC_SPEED = auto()  # emit: core/speed_calculator.py; handlers: data/ability.py,data/ailment.py,data/field.py
    ON_CALC_ACTION_SPEED = auto()  # emit: core/speed_calculator.py; handlers: data/field.py
    ON_CALC_ACCURACY = auto()  # emit: core/move_executor.py; handlers: data/field.py
    ON_CALC_CRITICAL = auto()  # emit: core/damage.py; handlers: data/ability.py,data/item.py
    ON_CALC_POWER_MODIFIER = auto()  # emit: core/damage.py; handlers: data/field.py
    ON_CALC_ATK_MODIFIER = auto()  # emit: core/damage.py
    ON_CALC_DEF_MODIFIER = auto()  # emit: core/damage.py; handlers: data/field.py
    ON_CALC_ATK_TYPE_MODIFIER = auto()  # emit: core/damage.py
    ON_CALC_DEF_TYPE_MODIFIER = auto()  # emit: core/damage.py
    ON_CALC_BURN_MODIFIER = auto()  # emit: core/damage.py; handlers: data/ailment.py
    ON_CALC_DAMAGE_MODIFIER = auto()  # emit: core/damage.py; handlers: data/field.py
    ON_CALC_PROTECT_MODIFIER = auto()  # emit: core/damage.py
    ON_CALC_FINAL_DAMAGE_MODIFIER = auto()  # 未使用
    ON_CHECK_DEF_ABILITY = auto()  # emit: core/damage.py
    ON_CALC_DRAIN = auto()  # 未使用
