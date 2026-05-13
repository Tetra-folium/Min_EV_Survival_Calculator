# app.py

import streamlit as st

from models import (
    SurvivalRequest,
    DefenderConfig,
    AttackConfig,
    StatInvestment,
)

from calculator import (
    find_min_ev_survival,
    PHYSICAL_TYPES,
    TYPE_TO_BOOST_ITEMS,
    CONDITIONAL_ABILITIES,
)

from data_loader import load_data

if "selected_gen" not in st.session_state:
    st.session_state.selected_gen = 3

selected_gen = st.sidebar.selectbox(
    "Generation",
    options=[1,2,3],
    index=st.session_state.selected_gen - 1,
    format_func=lambda g: f"Gen {g}",
)
st.session_state.selected_gen = selected_gen
st.warning(
    f"Current version only works properly for Gen 3. "
    f"Some non Gen 3 situations and abilities may be selectable "
    "but are not necessarily accurate or functional at this time."
)

POKEMON_DB, MOVE_DB = load_data()

st.title(f"Gen 3 Min EV Survival Calculator")
# st.title(f"Gen {selected_gen} Min EV Survival Calculator")

pokemon_names = sorted(
    list(POKEMON_DB.keys())
)

move_names = sorted(
    list(MOVE_DB.keys())
)

physical_move_names = sorted([
    move.name
    for move in MOVE_DB.values()
    if (
        move.type in PHYSICAL_TYPES
        or move.base_power == 1
    )
])

special_move_names = sorted([
    move.name
    for move in MOVE_DB.values()
    if (
        move.type not in PHYSICAL_TYPES
        or move.base_power == 1
    )
])

# -------------------------
# Visual UI Elements
# -------------------------

def render_move_badge(move):
    badges = []

    # Primary category
    if move.base_power == 1:
        badges.append("⚪ Fixed Damage")
    elif move.type in PHYSICAL_TYPES:
        badges.append("🔴 Physical")
    else:
        badges.append("🔵 Special")

    # Secondary tags
    if move.hits:
        if move.hits.get("type") == "variable":
            min_h = move.hits.get("min")
            max_h = move.hits.get("max")
            badges.append(f"🟡 Multi-hit ({min_h}-{max_h})")
        elif move.hits.get("type") == "fixed":
            badges.append(f"🟡 Multi-hit ({move.hits['value']}x)")

    if move.name.startswith("Hidden Power"):
        badges.append("🟣 Hidden Power")

    return " | ".join(badges)


def get_hits_type(move):
    """Return 'variable', 'fixed', or 'single' for a move."""
    if move.hits is None:
        return "single"
    return move.hits.get("type", "single")


level = st.slider(
    "Level",
    min_value=1,
    max_value=100,
    value=100,
)


# -------------------------
# Defender
# -------------------------

st.header("Defender")

defender_name = st.selectbox(
    "Defender",
    pokemon_names,
)

defender_obj = POKEMON_DB[defender_name]

defender_ability = st.selectbox(
    "Defender Ability",
    defender_obj.abilities,
)

# Signature item: only show when it affects the defender
defender_item = None
if defender_name in ("Clamperl",):
    if st.checkbox("Seep Sea Scale", key="def_deep_sea_scale"):
        defender_item = "Deep Sea Scale"
elif defender_name == "Ditto":
    if st.checkbox("Metal Powder", key="def_metal_powder"):
        defender_item = "Metal Powder"
elif defender_name in ("Latios", "Latias"):
    if st.checkbox("Soul Dew", key="def_soul_dew"):
        defender_item = "Soul Dew"

defender_hp_iv  = 31
defender_def_iv = 31
defender_spd_iv = 31

if st.checkbox("Defender using Hidden Power?", key="def_hidden_power"):
    st.caption('''
        Hidden Power may impact HP, Def, or SpD IVs.  
        Adjust below. Default IVs are assumed to be 31.
        ''')
    col_hp, col_def, col_spd = st.columns(3)
    with col_hp:
        defender_hp_iv = st.number_input(
            "HP IV",
            min_value=0, max_value=31, value=31, step=1,
            key="def_hp_iv",
        )
    with col_def:
        defender_def_iv = st.number_input(
            "Def IV",
            min_value=0, max_value=31, value=31, step=1,
            key="def_def_iv",
        )
    with col_spd:
        defender_spd_iv = st.number_input(
            "SpD IV",
            min_value=0, max_value=31, value=31, step=1,
            key="def_spd_iv",
        )


if defender_item == None:
    leftovers = st.checkbox("Leftovers")

sandstorm = st.checkbox("Sandstorm")
st.markdown("### Entry Hazards")

spikes = st.slider(
    "Spikes Layers",
    min_value=0,
    max_value=3,
    value=0
)

spikes_mode = st.selectbox(
    "Spikes Timing",
    ["Switch", "Revenge"],
    help=( '''
        Switch = Switch -> Spikes damage -> Attack -> Sand, Leftovers, etc. -< Next Turn  
        Revenge = Switch -> Spikes damage -> Sand, Leftovers, etc. -> Next Turn
        ''')
)

# -------------------------
# Physical
# -------------------------

st.header("Physical Attack")

use_phys = st.checkbox(
    "Enable Physical Attack"
)

physical_config = None

if use_phys:

    phys_attacker = st.selectbox(
        "Physical Attacker",
        pokemon_names,
        key="phys_attacker",
    )

    phys_obj = POKEMON_DB[phys_attacker]

    phys_move = st.selectbox(
        "Physical Move",
        physical_move_names,
    )

    phys_move_obj = MOVE_DB[phys_move]
    st.info(render_move_badge(phys_move_obj))

    phys_hits_type = get_hits_type(phys_move_obj)

    if phys_hits_type == "variable":
        st.warning(
            f"{phys_move} is a multi-hit move. "
            f"({phys_move_obj.hits['min']}-{phys_move_obj.hits['max']} hits). "
            "Each hit is treated as a separate damage instance. "
            "(e.g. Rock Blast hits 3 times then 4 times = 7 hits total.)"
        )
    elif phys_hits_type == "fixed":
        fixed_hits = phys_move_obj.hits["value"]
        st.warning(
            f"{phys_move} always hits {fixed_hits} times. "
            f"Each attack used incorporates all {fixed_hits} hits."
        )

    phys_hidden_power_iv = None
    if phys_move.startswith("Hidden Power"):
        phys_hidden_power_iv = st.slider(
            "Atk IV (Hidden Power)",
            min_value=0,
            max_value=31,
            value=31,
        )

    phys_ability = st.selectbox(
        "Physical Ability",
        phys_obj.abilities,
    )

    phys_ability_active = False
    if phys_ability in CONDITIONAL_ABILITIES:
        cond = CONDITIONAL_ABILITIES[phys_ability]
        label = (
            f"{phys_ability} active "
            f"({'base power' if cond['target'] == 'base_power' else 'Atk'} "
            f"x{cond['multiplier']}"
            + (f", {cond['move_type']} moves only" if cond["move_type"] else "")
            + ")"
        )
        phys_ability_active = st.checkbox(label, key="phys_ability_active")

    # Items for physical attackers

    phys_item = None
    # Signature items
    if phys_attacker == "Marowak":
        if st.checkbox("Thick Club", key="phys_thick_club"):
            phys_item = "Thick Club"
    elif phys_attacker == "Clamperl":
        if st.checkbox("Deep Sea Tooth", key="phys_deep_sea_tooth"):
            phys_item = "Deep Sea Tooth"
    elif phys_attacker == "Pikachu":
        if st.checkbox("Light Ball", key="phys_light_ball"):
            phys_item = "Light Ball"
    elif phys_attacker in ("Latios", "Latias"):
        if st.checkbox("Soul Dew", key="phys_soul_dew"):
            phys_item = "Soul Dew"
    if phys_item is None:
        # Choice Band: available for physical attackers
        if st.checkbox("Choice Band", key="phys_choice_band"):
            phys_item = "Choice Band"
        # Type-boosting item: only shown if selected move's type has associated item
        if phys_item is None:
            for phys_type_item, phys_type_mult in TYPE_TO_BOOST_ITEMS.get(phys_move_obj.type, []):
                if st.checkbox(f"{phys_type_item} ({phys_move_obj.type} {phys_type_mult}x)", 
                    key="phys_type_item_{phys_type_item}"):
                        phys_item = phys_type_item
                        break


    phys_attacks_used = st.number_input(
        "Physical Attacks Used",
        min_value=1,
        max_value=10,
        value=1,
    )

    if phys_hits_type == "variable":
        # Variable multi-hit: show a hits-per-attack slider for each attack
        phys_hits_per_attack = []
        for i in range(phys_attacks_used):
            phys_hits_per_attack.append(
                st.slider(
                    f"Physical Mode - Attack {i+1} Hits",
                    min_value=1,
                    max_value=5,
                    value=1,
                    key=f"phys_hits_{i}"
                )
            )
    elif phys_hits_type == "fixed":
        # Fixed multi-hit: always hits `value` times, no sliders needed
        phys_hits_per_attack = [phys_move_obj.hits["value"]] * phys_attacks_used
    else:
        # Single-hit move: always 1 hit per attack, no sliders needed
        phys_hits_per_attack = [1] * phys_attacks_used

    phys_stage = st.slider(
        "Attack Stage",
        min_value=-6,
        max_value=6,
        value=0,
    )

    phys_ev = st.slider(
        "Atk EV",
        0,
        252,
        252,
        step=4,
    )

    phys_nature = st.selectbox(
        "Atk Nature",
        [1.1, 1.0, 0.9],
        format_func=lambda x: {
            1.1: "+",
            1.0: "Neutral",
            0.9: "-",
        }[x]
    )

    physical_config = AttackConfig(
        attacker_name=phys_attacker,
        move_name=phys_move,
        stage=phys_stage,
        ability=phys_ability,
        ability_active=phys_ability_active,
        investment=StatInvestment(
            ev=phys_ev,
            nature=phys_nature,
        ),
        hidden_power_iv=phys_hidden_power_iv,
        hits_per_attack=phys_hits_per_attack,
        item=phys_item,
    )

# -------------------------
# Special
# -------------------------

st.header("Special Attack")

use_spec = st.checkbox(
    "Enable Special Attack"
)

special_config = None

if use_spec:

    spec_attacker = st.selectbox(
        "Special Attacker",
        pokemon_names,
        key="spec_attacker",
    )

    spec_obj = POKEMON_DB[spec_attacker]

    spec_move = st.selectbox(
        "Special Move",
        special_move_names,
    )

    spec_move_obj = MOVE_DB[spec_move]
    st.info(render_move_badge(spec_move_obj))

    spec_hits_type = get_hits_type(spec_move_obj)

    if spec_hits_type == "variable":
        st.warning(
            f"{spec_move} is a multi-hit move. "
            f"({spec_move_obj.hits['min']}-{spec_move_obj.hits['max']} hits). "
            "Each hit is treated as a separate damage instance. "
            "e.g. Icicle Spear hits 3 times then 4 times = 7 hits total."
        )
    elif spec_hits_type == "fixed":
        fixed_hits = spec_move_obj.hits["value"]
        st.warning(
            f"{spec_move} always hits {fixed_hits} times. "
            f"Each attack used incorporates all {fixed_hits} hits."
        )

    spec_hidden_power_iv = None
    if spec_move.startswith("Hidden Power"):
        spec_hidden_power_iv = st.slider(
            "SpA IV (Hidden Power)",
            min_value=0,
            max_value=31,
            value=31,
        )

    spec_ability = st.selectbox(
        "Special Ability",
        spec_obj.abilities,
    )

    spec_ability_active = False
    if spec_ability in CONDITIONAL_ABILITIES:
        cond = CONDITIONAL_ABILITIES[spec_ability]
        label = (
            f"{spec_ability} active "
            f"({'base power' if cond['target'] == 'base_power' else 'SpA'} "
            f"x{cond['multiplier']}"
            + (f", {cond['move_type']} moves only" if cond["move_type"] else "")
            + ")"
        )
        spec_ability_active = st.checkbox(label, key="spec_ability_active")

    # Items for special attackers.

    spec_item = None
    # Signature items
    if spec_attacker == "Marowak":
        if st.checkbox("Thick Club", key="spec_thick_club"):
            spec_item = "Thick Club"
    elif spec_attacker == "Clamperl":
        if st.checkbox("Deep Sea Tooth", key="spec_deep_sea_tooth"):
            spec_item = "Deep Sea Tooth"
    elif spec_attacker == "Pikachu":
        if st.checkbox("Light Ball", key="spec_light_ball"):
            spec_item = "Light Ball"
    elif spec_attacker in ("Latios", "Latias"):
        if st.checkbox("Soul Dew", key="spec_soul_dew"):
            spec_item = "Soul Dew"
    if spec_item is None:
        # Type-boosting items
        for spec_type_item, spec_type_mult in TYPE_TO_BOOST_ITEMS.get(spec_move_obj.type, []):
            if st.checkbox(f"{spec_type_item} ({spec_move_obj.type} {spec_type_mult}x)",
                key=f"spec_type_item_{spec_type_item}"):
                    spec_item = spec_type_item
                    break

    spec_attacks_used = st.number_input(
        "Special Attacks Used",
        min_value=1,
        max_value=10,
        value=1,
    )

    if spec_hits_type == "variable":
        # Variable multi-hit: show a hits-per-attack slider for each attack
        spec_hits_per_attack = []
        for i in range(spec_attacks_used):
            spec_hits_per_attack.append(
                st.slider(
                    f"Special Mode - Attack {i+1} Hits",
                    min_value=1,
                    max_value=5,
                    value=1,
                    key=f"spec_hits_{i}"
                )
            )
    elif spec_hits_type == "fixed":
        # Fixed multi-hit: always hits `value` times, no sliders needed
        spec_hits_per_attack = [spec_move_obj.hits["value"]] * spec_attacks_used
    else:
        # Single-hit move: always 1 hit per attack, no sliders needed
        spec_hits_per_attack = [1] * spec_attacks_used

    spec_stage = st.slider(
        "SpA Stage",
        min_value=-6,
        max_value=6,
        value=0,
        key="spec_stage",
    )

    spec_ev = st.slider(
        "SpA EV",
        0,
        252,
        252,
        step=4,
        key="spec_ev",
    )

    spec_nature = st.selectbox(
        "SpA Nature",
        [1.1, 1.0, 0.9],
        format_func=lambda x: {
            1.1: "+",
            1.0: "Neutral",
            0.9: "-",
        }[x],
        key="spec_nature",
    )

    special_config = AttackConfig(
        attacker_name=spec_attacker,
        move_name=spec_move,
        stage=spec_stage,
        ability=spec_ability,
        ability_active=spec_ability_active,
        investment=StatInvestment(
            ev=spec_ev,
            nature=spec_nature,
        ),
        hidden_power_iv=spec_hidden_power_iv,
        hits_per_attack=spec_hits_per_attack,
        item=spec_item,
    )

# -------------------------
# Misc
# -------------------------

allow_nature = st.checkbox(
    "Allow Defensive Natures"
)

combine_mode = st.checkbox(
    "Combine Physical + Special",
    help=('''
        Finds the bulk to live Phys hits + Spec hits in sequence &mdash; not separately.  
        Most accurate for sequences where Leftovers and Sandstorm cancel out.  
        (e.g. sand-immune defender w/o Leftovers, sand-weak defender with Leftovers)
    '''),
)

# -------------------------
# Run
# -------------------------

if st.button("Calculate"):

    req = SurvivalRequest(
        defender=DefenderConfig(
            defender_name=defender_name,
            ability=defender_ability,
            sandstorm=sandstorm,
            leftovers=leftovers,
            spikes_layers=spikes,
            spikes_mode=spikes_mode,
            item=defender_item,
            hp_iv=defender_hp_iv,
            def_iv=defender_def_iv,
            spd_iv=defender_spd_iv,
        ),

        physical=physical_config,
        special=special_config,

        allow_nature=allow_nature,
        combine_mode=combine_mode,
        level=level,
    )

    spreads = find_min_ev_survival(req, POKEMON_DB, MOVE_DB)

    st.subheader("Results")

    if not spreads:
        st.error("No legal spread found.")

    else:

        for s in spreads:

            def_marker = "+" if s.nature == "+Def" else ""
            spd_marker = "+" if s.nature == "+SpD" else ""
            total = s.hp_ev + s.def_ev + s.spd_ev

            st.write(
                f"{s.hp_ev} HP / "
                f"{s.def_ev}{def_marker} Def / "
                f"{s.spd_ev}{spd_marker} SpD | "
                f"Total: {total} EVs"
            )
