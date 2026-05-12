# data_loader.py

import json
import os

from models import Pokemon, Move


def load_data(config_path=None):

    if config_path is None:

        current_dir = os.path.dirname(
            os.path.abspath(__file__)
        )

        config_path = os.path.join(
            current_dir,
            "pokemon_data.json"
        )

    if not os.path.exists(config_path):

        raise FileNotFoundError(
            f"Could not find pokemon_data.json at:\n{config_path}"
        )

    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    pokemon_db = {
        name: Pokemon(
            name=name,
            type_1=p["type_1"],
            type_2=p["type_2"],
            base_hp=p["base_hp"],
            base_atk=p["base_atk"],
            base_def=p["base_def"],
            base_spa=p["base_spa"],
            base_spd=p["base_spd"],
            abilities=p["abilities"],
        )
        for name, p in data["Pokemon"].items()
    }

    move_db = {
        name: Move(
            name=name,
            type=m["type"],
            base_power=m["base_power"],
            accuracy=m.get("accuracy"),
            hits=m.get("hits"),
        )
        for name, m in data["Moves"].items()
    }

    return pokemon_db, move_db