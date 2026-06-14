mod_list = "mods.ini"

mod_list_header = """; Ruka KMM Mod List Configuration
;
; Categories are wrapped in `[]`
; Use `_desc` key to describe a category
; Comments get stripped on every sync, so please do not write your own comments
;
"""

category_intros = [
    (
        "UI, Graphics, Performance",
        "Visual and performance tweaks (textures, weather, clutter, maps, UI).",
    ),
    ("Animations", "Character and combat animation overhauls."),
    ("New Races & Race Edits", "Race unlocks, new races, cosmetics, and stat edits."),
    (
        "Animals",
        "New animals, animal backpacks, armor, and recruit mechanics for animals.",
    ),
    ("Game Starts", "Game start scenarios and initial state mods."),
    (
        "Faction Edits & Additions",
        "Minor faction changes (spawns, bounties) or tiny new factions.",
    ),
    ("Buildings", "Buildings, furniture, and building mechanic edits."),
    (
        "Armor & Weapons",
        "Standalone or packs of weapons/armor, faction-specific gear, and overhauls.",
    ),
    (
        "Overhauls & World Changes",
        "Major world, faction, or mechanic overhauls (check compatibility).",
    ),
    ("Patches", "Compatibility patches between mods."),
    ("Economy", "Merchant behavior, shopping, and economy tweaks."),
    (
        "Uncategorized",
        "Mods to be sorted.",
    ),
]
