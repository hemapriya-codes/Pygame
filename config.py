"""All game data in one place. Tweak numbers here to balance the game."""

SCREEN_W, SCREEN_H = 1100, 700
WORLD_W, WORLD_H = 3200, 3200
FPS = 60

OXYGEN_DRAIN = 1.2          # per second
OXYGEN_PER_KILL = 25        # refill when you kill a player/bot/mimic
OXYGEN_PER_ALIEN = 10       # refill when you kill an alien
ZONE_START_RADIUS = 1700
ZONE_MIN_RADIUS = 220
ZONE_SHRINK_PER_SEC = 8
ZONE_GRACE = 20             # seconds before the zone starts shrinking
ZONE_DPS = 5
DAY_LENGTH = 240            # seconds for a full day/night cycle

# ----------------------------------------------------------------- weapons
WEAPONS = {
    "Blaster Pistol": dict(dmg=12, cooldown=0.30, speed=700, range=650, spread=0.03,
                           pellets=1, ammo=None, color=(120, 220, 255)),
    "Plasma Rifle":   dict(dmg=10, cooldown=0.15, speed=850, range=800, spread=0.05,
                           pellets=1, ammo=120, color=(120, 255, 160)),
    "Pulse Shotgun":  dict(dmg=8, cooldown=0.90, speed=700, range=380, spread=0.28,
                           pellets=6, ammo=24, color=(255, 200, 90)),
    "Ion Sniper":     dict(dmg=70, cooldown=1.30, speed=1500, range=1400, spread=0.0,
                           pellets=1, ammo=12, color=(200, 140, 255)),
    "Gravity Gun":    dict(dmg=5, cooldown=0.50, speed=600, range=420, spread=0.02,
                           pellets=1, ammo=30, color=(90, 120, 255), knockback=900),
}

# ------------------------------------------------------------------- suits
SUITS = {
    "Basic Suit":   dict(armor=0,  protects=set(),          color=(235, 235, 235)),
    "Heat Suit":    dict(armor=20, protects={"heat"},       color=(255, 150, 60)),
    "Rad Suit":     dict(armor=25, protects={"radiation"},  color=(240, 230, 70)),
    "Hazmat Suit":  dict(armor=25, protects={"toxic"},      color=(90, 220, 90)),
    "Gravity Suit": dict(armor=30, protects={"lowgrav"},    color=(90, 150, 255)),
    "Shield Suit":  dict(armor=50, color=(190, 200, 215),
                         protects={"heat", "radiation", "toxic", "lowgrav", "meteor"}),
}

HAZARDS = {
    "heat":      dict(dps=6, color=(255, 90, 40),  label="Extreme Heat",  suit="Heat Suit"),
    "radiation": dict(dps=5, color=(220, 230, 40), label="Radiation",     suit="Rad Suit"),
    "toxic":     dict(dps=5, color=(60, 220, 80),  label="Toxic Storm",   suit="Hazmat Suit"),
    "lowgrav":   dict(dps=0, color=(90, 140, 255), label="Low Gravity",   suit="Gravity Suit"),
    "meteor":    dict(dps=0, color=(200, 120, 90), label="Meteor Shower", suit="Shield Suit"),
}

# ------------------------------------------------------------------ aliens
ALIENS = {
    "Crawler": dict(hp=30,  speed=150, dmg=8,  radius=12, ranged=False, color=(120, 220, 90)),
    "Spitter": dict(hp=45,  speed=90,  dmg=10, radius=14, ranged=True,  color=(200, 90, 220)),
    "Brute":   dict(hp=160, speed=80,  dmg=25, radius=24, ranged=False, color=(220, 80, 80)),
}

# ------------------------------------------------------------------- ranks
RANKS = [("Cadet", 0), ("Pilot", 100), ("Commander", 300), ("Captain", 700), ("Admiral", 1500)]

# ----------------------------------------------------------------- rockets
ROCKET_BODIES = {
    "Scout":  dict(speed=1.10, cargo=0, shield=0,  desc="Fast and light"),
    "Hauler": dict(speed=0.95, cargo=2, shield=0,  desc="Carries 2 extra medkits"),
    "Tank":   dict(speed=0.90, cargo=0, shield=20, desc="+20 starting armor"),
}
ROCKET_COLORS = [(220, 60, 60), (70, 130, 230), (240, 190, 50), (90, 200, 120), (200, 200, 210)]
UPGRADES = ["engine", "shield", "cargo", "scanner"]
UPGRADE_INFO = {
    "engine":  "Engine: +6% move speed per level",
    "shield":  "Shield: +8 starting armor per level",
    "cargo":   "Cargo: +1 starting medkit per level",
    "scanner": "Scanner: bigger minimap range",
}
MAX_UPGRADE = 3


def upgrade_cost(level):
    return 20 * (level + 1), 5 * level      # (ore, crystal)


# ----------------------------------------------------------------- planets
PLANETS = [
    dict(name="Kepler-7",   hazard="heat",      color=(70, 45, 35),  gravity="1.0 g", temp="+48 C"),
    dict(name="Nyx",        hazard="radiation", color=(45, 50, 35),  gravity="0.8 g", temp="-10 C"),
    dict(name="Verdant-3",  hazard="toxic",     color=(30, 55, 40),  gravity="1.1 g", temp="+22 C"),
    dict(name="Luna-Prime", hazard="lowgrav",   color=(50, 55, 70),  gravity="0.2 g", temp="-60 C"),
    dict(name="Meteora",    hazard="meteor",    color=(60, 40, 60),  gravity="0.9 g", temp="+5 C"),
]
LANDING_SITES = [("Crater Rim", 0.25, 0.25), ("Dust Plains", 0.75, 0.25),
                 ("Ridge Camp", 0.25, 0.75), ("Coast Dunes", 0.75, 0.75)]

# -------------------------------------------------------- colony buildings
STRUCTURES = {
    "Oxygen Generator": dict(key="Z", ore=25, crystal=0,  color=(90, 220, 255), info="Refills oxygen nearby"),
    "Turret":           dict(key="X", ore=30, crystal=5,  color=(255, 120, 90), info="Shoots aliens"),
    "Lab":              dict(key="C", ore=0,  crystal=20, color=(190, 120, 255), info="Heals nearby"),
    "Habitat Dome":     dict(key="V", ore=40, crystal=10, color=(120, 255, 170), info="Safe oxygen zone"),
}


def bots_for_round(r):
    table = [5, 10, 20, 30]
    return table[r - 1] if r <= 4 else min(40, 30 + (r - 4) * 5)
