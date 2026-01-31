from jpoke import Battle, Player, Pokemon
from jpoke.utils.type_defs import Weather, Terrain
from jpoke.utils.enums import Command


class CustomPlayer(Player):
    def choose_selection_commands(self, battle: Battle) -> list[Command]:
        return battle.get_available_selection_commands(self)

    def choose_action_command(self, battle: Battle) -> Command:
        return battle.get_available_action_commands(self)[0]


def start_battle(ally: list[Pokemon] | None = None,
                 foe: list[Pokemon] | None = None,
                 weather: Weather | None = None,
                 terrain: Terrain | None = None,
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

    battle = Battle(players)
    if weather:
        battle.weather_mgr.activate(weather, 999)
    if terrain:
        battle.terrain_mgr.activate(terrain, 999)

    if accuracy is not None:
        battle.test_option.accuracy = accuracy

    while True:
        battle.advance_turn()
        battle.print_logs()
        if battle.winner() or battle.turn == turn:
            return battle


def can_switch(battle: Battle, idx: int) -> bool:
    """交代可能ならTrueを返す"""
    commands = battle.get_available_action_commands(battle.players[idx])
    return any(c.is_switch() for c in commands)
