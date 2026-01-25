from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from jpoke.core import Battle, EventContext
    from jpoke.model import Pokemon


def reveal_ability(battle: Battle, target: Pokemon) -> bool:
    target.ability.revealed = True
    battle.add_turn_log(target, target.ability.name)
    return True


def かちき(battle: Battle, ctx: EventContext, value: Any):
    # ON_MODIFY_STAT ハンドラ
    if value < 0 and ctx.source != ctx.target:
        reveal_ability(battle, ctx.target)
        battle.modify_stat(ctx.target, "C", +2, source=ctx.source)
