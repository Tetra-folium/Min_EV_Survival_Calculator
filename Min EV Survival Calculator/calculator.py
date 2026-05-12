# calculator.py

import math

from models import (
    SurvivalRequest,
    EVSpread,
    Pokemon,
    Move,
)

IV = 31

PHYSICAL_TYPES = {
    "Normal", "Fighting", "Flying", "Poison",
    "Ground", "Rock", "Bug", "Ghost", "Steel"
}


# ------------------------
# Type Chart (Gen 3)
# ------------------------
type_chart = {
    "Normal": {"Rock": 0.5, "Ghost": 0, "Steel": 0.5},
    "Fire": {"Fire": 0.5, "Water": 0.5, "Grass": 2, "Ice": 2, "Bug": 2, "Rock": 0.5, "Dragon": 0.5, "Steel": 2},
    "Water": {"Fire": 2, "Water": 0.5, "Grass": 0.5, "Ground": 2, "Rock": 2, "Dragon": 0.5},
    "Electric": {"Water": 2, "Electric": 0.5, "Grass": 0.5, "Ground": 0, "Flying": 2, "Dragon": 0.5},
    "Grass": {"Fire": 0.5, "Water": 2, "Grass": 0.5, "Poison": 0.5, "Ground": 2, "Flying": 0.5, "Bug": 0.5, "Rock": 2, "Dragon": 0.5, "Steel": 0.5},
    "Ice": {"Fire": 0.5, "Water": 0.5, "Grass": 2, "Ice": 0.5, "Ground": 2, "Flying": 2, "Dragon": 2, "Steel": 0.5},
    "Fighting": {"Normal": 2, "Ice": 2, "Rock": 2, "Dark": 2, "Steel": 2, "Poison": 0.5, "Flying": 0.5, "Psychic": 0.5, "Bug": 0.5, "Ghost": 0},
    "Poison": {"Grass": 2, "Poison": 0.5, "Ground": 0.5, "Rock": 0.5, "Ghost": 0.5, "Steel": 0},
    "Ground": {"Fire": 2, "Electric": 2, "Grass": 0.5, "Poison": 2, "Flying": 0, "Bug": 0.5, "Rock": 2, "Steel": 2},
    "Flying": {"Electric": 0.5, "Grass": 2, "Fighting": 2, "Bug": 2, "Rock": 0.5, "Steel": 0.5},
    "Psychic": {"Fighting": 2, "Poison": 2, "Psychic": 0.5, "Dark": 0, "Steel": 0.5},
    "Bug": {"Fire": 0.5, "Grass": 2, "Fighting": 0.5, "Poison": 0.5, "Flying": 0.5, "Psychic": 2, "Ghost": 0.5, "Dark": 2, "Steel": 0.5},
    "Rock": {"Fire": 2, "Ice": 2, "Fighting": 0.5, "Ground": 0.5, "Flying": 2, "Bug": 2, "Steel": 0.5},
    "Ghost": {"Normal": 0, "Psychic": 2, "Ghost": 2, "Dark": 0.5},
    "Dragon": {"Dragon": 2, "Steel": 0.5},
    "Dark": {"Fighting": 0.5, "Psychic": 2, "Ghost": 2, "Dark": 0.5, "Steel": 0.5},
    "Steel": {"Fire": 0.5, "Water": 0.5, "Electric": 0.5, "Ice": 2, "Rock": 2, "Steel": 0.5},
}


# ------------------------
# Core Mechanics
# ------------------------

def get_types(mon):
   return [mon.type_1] + ([mon.type_2] if mon.type_2 else [])


def get_type_effectiveness(move_type, target_types):
    eff = 1.0
    for t in target_types:
        eff *= type_chart.get(move_type, {}).get(t, 1)
    return eff


def has_stab(types, move_type):
    return move_type in types


def stat_hp(base, ev, level: int = 100, iv: int = 31):
    return math.floor((2 * base + IV + (ev // 4)) * level / 100) + level + 10


def stat_non_hp(base: int, ev: int, nature: float = 1.0, level: int = 100, iv: int = 31) -> int:
    return int(
        math.floor(
            (math.floor((2 * base + IV + (ev // 4)) * level / 100) + 5) * nature
        )
    )


def apply_stat_stage(stat, stage):
    if stage >= 0:
        return int(stat * ((2 + stage) / 2))
    return int(stat * (2 / (2 - stage)))


def apply_attacker_ability_modifiers(
    atk_stat: int,
    move_type: str,
    ability: str | None,
    is_physical: bool,
    defender_ability: str | None = None,
) -> int:
    
    if ability:
        if ability in {"Huge Power", "Pure Power"} and is_physical:
            atk_stat *= 2

        if ability == "Blaze" and move_type == "Fire":
            atk_stat = int(atk_stat * 1.5)

        if ability == "Torrent" and move_type == "Water":
            atk_stat = int(atk_stat * 1.5)

        if ability == "Overgrow" and move_type == "Grass":
            atk_stat = int(atk_stat * 1.5)

    if defender_ability == "Thick Fat" and move_type in {"Fire", "Ice"}:
        atk_stat //=2

    return atk_stat


def apply_defender_ability_modifiers(
    damage: int,
    move_type: str,
    defender_ability: str | None,
) -> int:

    if not defender_ability:
        return damage

    if defender_ability == "Levitate" and move_type == "Ground":
        return 0

    if defender_ability == "Water Absorb" and move_type == "Water":
        return 0

    if defender_ability == "Volt Absorb" and move_type == "Electric":
        return 0

    return damage


# ------------------------
# Item Modifiers
# ------------------------

SIGNATURE_ITEMS: dict[str, dict[str, callable]] = {
    "Marowak":  {"Thick Club":     lambda s, phys: s * 2 if phys else s},
    "Clamperl": {"Deep Sea Tooth": lambda s, phys: s * 2 if not phys else s},
    "Pikachu":  {"Light Ball":     lambda s, phys: s * 2 if not phys else s},
    "Ditto":    {"Metal Powder":   lambda s, phys: s},
    "Latios":   {"Soul Dew":       lambda s, phys: int(s * 1.5) if not phys else s},
    "Latias":   {"Soul Dew":       lambda s, phys: int(s * 1.5) if not phys else s},
}


FLAT_ATK_ITEMS: dict[str, callable] = {
    "Choice Band": lambda s, phys: int(s * 1.5) if phys else s,
}

TYPE_BOOST_ITEMS: dict[str, dict] = {
    "Black Belt":     {"type": "Fighting", "multiplier": 1.1},
    "Black Glasses":  {"type": "Dark",     "multiplier": 1.1},
    "Charcoal":       {"type": "Fire",     "multiplier": 1.1},
    "Dragon Fang":    {"type": "Dragon",   "multiplier": 1.1},
    "Hard Stone":     {"type": "Rock",     "multiplier": 1.1},
    "Magnet":         {"type": "Electric", "multiplier": 1.1},
    "Metal Coat":     {"type": "Steel",    "multiplier": 1.1},
    "Miracle Seed":   {"type": "Grass",    "multiplier": 1.1},
    "Mystic Water":   {"type": "Water",    "multiplier": 1.1},
    "Never-Melt Ice": {"type": "Ice",      "multiplier": 1.1},
    "Poison Barb":    {"type": "Poison",   "multiplier": 1.1},
    "Sea Incense":    {"type": "Water",    "multiplier": 1.05},
    "Sharp Beak":     {"type": "Flying",   "multiplier": 1.1},
    "Silk Scarf":     {"type": "Normal",   "multiplier": 1.1},
    "Silver Powder":  {"type": "Bug",      "multiplier": 1.1},
    "Soft Sand":      {"type": "Ground",   "multiplier": 1.1},
    "Spell Tag":      {"type": "Ghost",    "multiplier": 1.1},
    "Twisted Spoon":  {"type": "Psychic",  "multiplier": 1.1},
}    


TYPE_TO_BOOST_ITEMS: dict[str, list[tuple[str, float]]] = {}
for _item_name, _item_data in TYPE_BOOST_ITEMS.items():
    _t = _item_data.get("type")
    _m = _item_data.get("multiplier")
    if _t and _m:
        TYPE_TO_BOOST_ITEMS.setdefault(_t, []).append((_item_name, _m))


def apply_attacker_item_modifiers(
    atk_stat: int,
    attacker_name: str,
    item: str | None,
    is_physical: bool,
    move_type: str = "",
) -> int:
    if not item:
        return atk_stat

    sig = SIGNATURE_ITEMS.get(attacker_name, {}).get(item)
    if sig:
        atk_stat = sig(atk_stat, is_physical)

    flat = FLAT_ATK_ITEMS.get(item)
    if flat:
        atk_stat = flat(atk_stat, is_physical)

    return atk_stat


def apply_attacker_item_damage_multiplier(
    damage: int,
    item: str | None,
    move_type: str,
) -> int:
    if not item:
        return damage
    boost = TYPE_BOOST_ITEMS.get(item)
    if boost and move_type == boost.get(type):
        damage = int(damage * boost.get(multiplier))
    return damage


DEFENDER_STAT_ITEMS: dict[str, callable] = {
    "Deep Sea Scale": lambda d, s: (d * 2, s),
    "Metal Powder":   lambda d, s: (d * 2, s),
    "Soul Dew":       lambda d, s: (d, int(s * 1.5)),
}


# ------------------------
# Computation
# ------------------------

def compute_damage(
    attacker: Pokemon,
    move: Move,
    stage: int,
    defender: Pokemon,
    defender_ability: str | None = None,
    attacker_ability: str | None = None,
    atk_ev: int = 252,
    spa_ev: int = 252,
    atk_nature: float = 1.1,
    spa_nature: float = 1.1,
    hidden_power_iv: int | None = None,
    attacker_item: str | None = None,
    Def: int = 0,
    SpD: int = 0,
    level: int = 100,
) -> int:

    defender_types = get_types(defender)
    attacker_types = get_types(attacker)

    is_physical = move.type in PHYSICAL_TYPES

    if move.base_power == 1:
        return level

    if is_physical:
        atk_stat = apply_stat_stage(
            stat_non_hp(attacker.base_atk, atk_ev, atk_nature, level),
            stage,
        )
        defense_stat = Def
    else:
        atk_stat = apply_stat_stage(
            stat_non_hp(attacker.base_spa, spa_ev, spa_nature, level),
            stage,
        )
        defense_stat = SpD

    atk_stat = apply_attacker_ability_modifiers(
        atk_stat,
        move.type,
        attacker_ability,
        is_physical,
        defender_ability,
    )

    atk_stat = apply_attacker_item_modifiers(
        atk_stat,
        attacker.name,
        attacker_item,
        is_physical,
        move.type,
    )

    if (
        move.name.startswith("Hidden Power")
        and hidden_power_iv is not None
    ):
        atk_stat = atk_stat - IV + hidden_power_iv

    effective_base_power = apply_attacker_item_damage_multiplier(
        move.base_power,
        attacker_item,
        move.type,
    )

    base_damage = (
        ((2 * level) // 5 + 2)
        * effective_base_power
        * atk_stat
    )

    base_damage = base_damage // defense_stat
    base_damage = base_damage // 50 + 2

    if has_stab(attacker_types, move.type):
        base_damage = (base_damage * 3) // 2

    base_damage = int(
        base_damage * get_type_effectiveness(move.type, defender_types)
    )

    return apply_defender_ability_modifiers(
        base_damage,
        move.type,
        defender_ability,
    )

def build_damage_sequence(
    attacker: Pokemon,
    move: Move,
    plan: list[int],
    defender: Pokemon,
    compute_damage_fn,
    atk_stage: int = 0, spa_stage: int = 0,
    atk_ev: int = 252, spa_ev: int = 252,
    atk_nature: float = 1.1, spa_nature: float = 1.1,
    hidden_power_iv: int | None = None,
    attacker_item: str | None = None,
    Def: int = 0,
    SpD: int = 0,
    level: int = 100,
) -> list[list[int]]:

    is_physical = move.type in PHYSICAL_TYPES
    sequence: list[list[int]] = []

    for hits in plan:
        dmg = compute_damage_fn(
            attacker=attacker,
            move=move,
            stage=atk_stage if is_physical else spa_stage,
            defender=defender,
            defender_ability=None,
            attacker_ability=None,
            atk_ev=atk_ev, spa_ev=spa_ev,
            atk_nature=atk_nature, spa_nature=spa_nature,
            hidden_power_iv=hidden_power_iv,
            attacker_item=attacker_item,
            Def=Def,
            SpD=SpD,
            level=level,
        )
        sequence.append([dmg] * hits)
    return sequence


def simulate_sequence(
    max_hp: int,
    damage_sequence: list[list[int]],
    defender_types: list[str],
    sandstorm: bool = False,
    leftovers: bool = False,
    spikes_layers: int = 0,
    spikes_mode: str = "switch",
    defender_abilities: list[str] | None = None,
) -> bool:

    current_hp = max_hp

    # ----------------------
    # Spikes
    # ----------------------

    if spikes_layers > 0:
        grounded = True
        if "Flying" in defender_types:
            grounded = False
        if "Levitate" in (defender_abilities or []):
            grounded = False
        if grounded:
            if spikes_layers == 1:
                current_hp -= max_hp // 8
            elif spikes_layers == 2:
                current_hp -= max_hp // 6
            elif spikes_layers == 3:
                current_hp -= max_hp // 4

        if current_hp <= 0:
            return False

    if spikes_mode == "revenge" and leftovers:
        current_hp = min(max_hp, current_hp + max_hp // 16)

    # ----------------------
    # Main Simulation Loop
    # ----------------------

    for attack in damage_sequence:
        for dmg in attack:
            current_hp -= dmg
            if current_hp <= 0:
                return False

        if (
            sandstorm and not any(
                t in {"Rock", "Steel", "Ground"}
                for t in defender_types
            )
        ):
            current_hp -= max_hp // 16
            if current_hp <= 0:
                return False

        if leftovers:
            current_hp = min(max_hp, current_hp + max_hp // 16)

    return True


def find_min_ev_survival(req, POKEMON_DB, MOVE_DB):

    level: int = req.level

    defender: Pokemon = POKEMON_DB[req.defender.defender_name]

    def_hp_iv  = req.defender.hp_iv
    def_def_iv = req.defender.def_iv
    def_spd_iv = req.defender.spd_iv

    defender_types = [defender.type_1]
    if defender.type_2:
        defender_types.append(defender.type_2)

    best_total = float("inf")
    best_spreads = []

    phys = req.physical
    spec = req.special

    phys_plan = phys.hits_per_attack if phys else None
    spec_plan = spec.hits_per_attack if spec else None

    # -------------------------
    # Set Nature
    # -------------------------
    if req.allow_nature:
        nature_candidates = [
            ("+Def", 1.1, 1.0),
            ("+SpD", 1.0, 1.1),
            ("Neutral", 1.0, 1.0),
        ]
    else:
        nature_candidates = [
            ("Neutral", 1.0, 1.0),
        ]
 
    for nature_label, def_nature, spd_nature in nature_candidates:
 
        for def_ev in range(0, 253, 4):
            for spd_ev in range(0, 253, 4):
 
                Def = stat_non_hp(defender.base_def, def_ev, def_nature, level, def_def_iv)
                SpD = stat_non_hp(defender.base_spd, spd_ev, spd_nature, level, def_spd_iv)
 
                defender_item = req.defender.item if req.defender.item else None
                if defender_item:
                    item_mod = DEFENDER_STAT_ITEMS.get(defender_item)
                    if item_mod:
                        Def, SpD = item_mod(Def, SpD)

                for hp_ev in range(0, 253, 4):
 
                    max_hp = stat_hp(defender.base_hp, hp_ev, level, def_hp_iv)
 
                    sequences = []

                    # -------------------------
                    # Physical
                    # -------------------------
                    if phys and phys_plan:
                        move = MOVE_DB[phys.move_name]
                        attacker = POKEMON_DB[phys.attacker_name]

                        seq = build_damage_sequence(
                            attacker, move, phys_plan, defender,
                            compute_damage,
                            atk_stage=phys.stage,
                            atk_ev=phys.investment.ev,
                            atk_nature=phys.investment.nature,
                            hidden_power_iv=phys.hidden_power_iv,
                            attacker_item=phys.item,
                            Def=Def,
                            SpD=SpD,
                            level=level,
                        )

                        sequences.append(seq)
    
                    # -------------------------
                    # Special
                    # -------------------------
                    if spec and spec_plan:
                        move = MOVE_DB[spec.move_name]
                        attacker = POKEMON_DB[spec.attacker_name]

                        seq = build_damage_sequence(
                            attacker, move, spec_plan, defender,
                            compute_damage,
                            spa_stage=spec.stage,
                            spa_ev=spec.investment.ev,
                            spa_nature=spec.investment.nature,
                            hidden_power_iv=spec.hidden_power_iv,
                            attacker_item=spec.item,
                            Def=Def,
                            SpD=SpD,
                            level=level,
                        )

                        sequences.append(seq)

                    if not sequences:
                        continue
    
                    if req.combine_mode:
                        merged = []
                        for s in sequences:
                            merged += s
                        sequences = [merged]

                    survives = all(
                        simulate_sequence(
                            max_hp,
                            seq,
                            defender_types,
                            sandstorm=req.defender.sandstorm,
                            leftovers=req.defender.leftovers,
                            spikes_layers=req.defender.spikes_layers,
                            spikes_mode=req.defender.spikes_mode,
                            defender_abilities=[req.defender.ability],
                        )
                        for seq in sequences
                    )

                    if not survives:
                        continue

                    total_ev = hp_ev + def_ev + spd_ev

                    if total_ev < best_total:
                        best_total = total_ev
                        best_spreads = []

                    if total_ev == best_total:
                        existing_idx = next(
                            (i for i, s in enumerate(best_spreads)
                             if s.hp_ev == hp_ev
                             and s.def_ev == def_ev
                             and s.spd_ev == spd_ev),
                            None,
                        )
                        if existing_idx is None:
                            best_spreads.append(EVSpread(
                                hp_ev=hp_ev,
                                def_ev=def_ev,
                                spd_ev=spd_ev,
                                nature=nature_label,
                                total_ev=total_ev,
                            ))
                        elif nature_label == "Neutral":
                            best_spreads[existing_idx] = EVSpread(
                                hp_ev=hp_ev,
                                def_ev=def_ev,
                                spd_ev=spd_ev,
                                nature="Neutral",
                                total_ev=total_ev,
                            )
 
    return best_spreads