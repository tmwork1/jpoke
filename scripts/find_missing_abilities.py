
from jpoke.data import POKEDEX, ABILITIES


def main():
    abilities_in_pokedex = set()
    for data in POKEDEX.values():
        for ability in data.abilities:
            abilities_in_pokedex.add(ability)

    implemented_abilities = set(ABILITIES.keys())

    unimplemented_abilities = abilities_in_pokedex - implemented_abilities
    print("Unimplemented abilities:")
    for ability in sorted(unimplemented_abilities):
        print(ability)


if __name__ == "__main__":
    main()
