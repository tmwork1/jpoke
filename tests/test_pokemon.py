from jpoke.model import Pokemon


def test_reconstruct_from_log_restores_core_fields():
    data = {
        "name": "ピカチュウ",
        "gender": "オス",
        "level": 50,
        "nature": "おくびょう",
        "ability": "せいでんき",
        "item": "いのちのたま",
        "moves": ["たいあたり", "でんきショック", "なきごえ", "はねる"],
        "indiv": [31, 0, 31, 31, 31, 31],
        "effort": [0, 0, 0, 252, 4, 252],
        "terastal": "でんき",
    }

    mon = Pokemon.reconstruct_from_log(data)

    assert mon.name == data["name"]
    assert mon.gender == data["gender"]
    assert mon.level == data["level"]
    assert mon.nature == data["nature"]
    assert mon.ability.name == data["ability"]
    assert mon.item.name == data["item"]
    assert [move.name for move in mon.moves] == data["moves"]
    assert mon.indiv == data["indiv"]
    assert mon.effort == data["effort"]
    mon.terastallize()
    assert mon.terastal == data["terastal"]
