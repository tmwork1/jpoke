from jpoke import Battle, Player, Pokemon
from jpoke.utils.enums import Command


class CustomPlayer(Player):
    def choose_selection_commands(self, battle: Battle) -> list[Command]:
        return battle.get_available_selection_commands(self)

    def choose_action_command(self, battle: Battle) -> Command:
        return battle.get_available_action_commands(self)[0]


PRINT_LOG = True


def generate_battle(ally: list[Pokemon] | None = None,
                    foe: list[Pokemon] | None = None,
                    turn: int = 0,
                    accuracy: int | None = 100) -> Battle:
    if not ally:
        ally = [Pokemon("ピカチュウ")]
    if not foe:
        foe = [Pokemon("ピカチュウ")]
    players = [CustomPlayer() for _ in range(2)]
    for player, mons in zip(players, [ally, foe]):
        for mon in mons:
            player.team.append(mon)

    battle = Battle(players)  # type: ignore

    if accuracy is not None:
        battle.test_option.accuracy = accuracy

    while True:
        battle.advance_turn(print_log=PRINT_LOG)
        if battle.winner() or battle.turn == turn:
            return battle


def check_switch(battle, idx=1) -> bool:
    """交代可能ならTrueを返す"""
    commands = battle.get_available_action_commands(battle.players[idx])
    return any(c.is_switch() for c in commands)
