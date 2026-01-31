from jpoke import Battle, Player, Pokemon
from jpoke.utils.type_defs import VolatileName, Weather, Terrain
from jpoke.utils.enums import Command


class CustomPlayer(Player):
    def choose_selection_commands(self, battle: Battle) -> list[Command]:
        return battle.get_available_selection_commands(self)

    def choose_action_command(self, battle: Battle) -> Command:
        return battle.get_available_action_commands(self)[0]


def start_battle(ally: list[Pokemon] | None = None,
                 foe: list[Pokemon] | None = None,
                 turn: int = 0,
                 weather: Weather | None = None,
                 terrain: Terrain | None = None,
                 ally_volatile: dict[VolatileName, int] | None = None,
                 foe_volatile: dict[VolatileName, int] | None = None,
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

        if battle.turn == 1 and (ally_volatile or foe_volatile):
            volatiles = [ally_volatile, foe_volatile]
            for idx, mon in enumerate(battle.actives):
                if volatiles[idx]:
                    for name, count in volatiles[idx].items():
                        mon.apply_volatile(battle.events, name, count=count)

        battle.print_logs()
        if battle.winner() or battle.turn == turn:
            return battle


def can_switch(battle: Battle, idx: int) -> bool:
    """交代可能ならTrueを返す"""
    commands = battle.get_available_action_commands(battle.players[idx])
    return any(c.is_switch() for c in commands)
