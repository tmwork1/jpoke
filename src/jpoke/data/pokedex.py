import json
from datetime import datetime, timedelta, timezone

from jpoke import config
from jpoke.utils import file_io as fileut
from jpoke.data.models import PokemonData


pokedex: dict[str, PokemonData] = {}


def get_season(start_year=2022, start_month=12) -> int:
    dt_now = datetime.now(timezone(timedelta(hours=+9), 'JST'))
    y, m, d = dt_now.year, dt_now.month, dt_now.day
    season = 12*(y-start_year) + m - start_month + 1 - (d == 1)
    return max(season, 1)


def init():
    file = str(fileut.resource_path('data', "zukan.json"))

    if False and fileut.needs_update(file):
        fileut.download(config.URL_ZUKAN, file)
        fileut.save_last_update(file)

    with open(file, encoding='utf-8') as f:
        data = json.load(f)

    global pokedex
    for d in data.values():
        pokedex[d["name"]] = PokemonData(d)


init()
