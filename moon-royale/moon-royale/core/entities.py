"""Game objects. No drawing code here, only data and small behaviours."""
import random
from .vec import Vec2
from . import config as C


class Entity:
    def __init__(self, x, y, radius, hp):
        self.pos = Vec2(x, y)
        self.vel = Vec2()
        self.push = Vec2()          # knockback impulse (decays quickly)
        self.radius = radius
        self.hp = float(hp)
        self.max_hp = float(hp)
        self.alive = True
        self.flash = 0.0            # hit-flash timer (used by the renderer)


class Projectile:
    def __init__(self, pos, vel, dmg, owner, team, life, color, knockback=0.0):
        self.pos, self.vel, self.dmg = pos, vel, dmg
        self.owner, self.team = owner, team       # team: fighter / alien / turret
        self.life, self.color, self.knockback = life, color, knockback
        self.radius = 4
        self.dead = False


class Fighter(Entity):
    """Anything that carries a gun and a suit: the player, bots and mimics."""

    def __init__(self, x, y, name, suit="Basic Suit"):
        super().__init__(x, y, 16, 100)
        self.name = name
        self.suit = suit
        self.armor = float(C.SUITS[suit]["armor"])
        self.max_armor = 100.0
        self.oxygen = 100.0
        self.max_oxygen = 100.0
        self.weapons = ["Blaster Pistol", None]
        self.ammo = {"Blaster Pistol": None}          # None = infinite
        self.slot = 0
        self.cooldown = 0.0
        self.aim = Vec2(1, 0)
        self.kills = 0
        self.alien_kills = 0
        self.speed = 230.0
        self.medkits = 0
        self.is_player = False
        self.is_mimic = False
        self.last_attacker = None
        self.dead_done = False

    # ---- suit
    @property
    def color(self):
        return C.SUITS[self.suit]["color"]

    def protected(self, hazard):
        return hazard in C.SUITS[self.suit]["protects"]

    def wear(self, suit):
        self.suit = suit
        self.armor = max(self.armor, float(C.SUITS[suit]["armor"]))

    # ---- weapons
    @property
    def weapon(self):
        return self.weapons[self.slot] or "Blaster Pistol"

    def give_weapon(self, name):
        if name in self.weapons:
            self.add_ammo(name, C.WEAPONS[name]["ammo"] or 0)
            self.slot = self.weapons.index(name)
            return
        idx = self.weapons.index(None) if None in self.weapons else self.slot
        old = self.weapons[idx]
        if old:
            self.ammo.pop(old, None)
        self.weapons[idx] = name
        self.ammo[name] = C.WEAPONS[name]["ammo"]
        self.slot = idx

    def add_ammo(self, name, n):
        cur = self.ammo.get(name)
        if name not in self.ammo or cur is None:
            return
        self.ammo[name] = min(C.WEAPONS[name]["ammo"] * 2, cur + n)

    def switch(self, idx):
        if 0 <= idx < len(self.weapons) and self.weapons[idx]:
            self.slot = idx

    def _auto_switch(self):
        for i, wn in enumerate(self.weapons):
            if wn and (self.ammo.get(wn) is None or self.ammo[wn] > 0):
                self.slot = i
                return

    def try_shoot(self, rng, extra_spread=0.0):
        if self.cooldown > 0 or not self.alive:
            return []
        name = self.weapon
        w = C.WEAPONS[name]
        ammo = self.ammo.get(name)
        if ammo is not None:
            if ammo <= 0:
                self._auto_switch()
                return []
            self.ammo[name] = ammo - 1
        self.cooldown = w["cooldown"]
        out = []
        for _ in range(w["pellets"]):
            ang = rng.uniform(-1, 1) * (w["spread"] + extra_spread)
            d = self.aim.rotate(ang)
            out.append(Projectile(self.pos + d * (self.radius + 6), d * w["speed"], w["dmg"],
                                  self, "fighter", w["range"] / w["speed"], w["color"],
                                  w.get("knockback", 0.0)))
        return out

    # ---- health
    def damage(self, amount, source=None):
        if not self.alive:
            return
        absorbed = min(self.armor, amount * 0.6)     # armor soaks 60% of the hit
        self.armor -= absorbed
        self.hp -= amount - absorbed
        self.flash = 0.15
        self.last_attacker = source
        if self.hp <= 0:
            self.hp = 0
            self.alive = False


class Player(Fighter):
    def __init__(self, x, y):
        super().__init__(x, y, "You")
        self.is_player = True


class Bot(Fighter):
    def __init__(self, x, y, name, difficulty=1):
        super().__init__(x, y, name)
        self.difficulty = difficulty
        self.speed = min(250.0, 185.0 + 8 * difficulty)
        self.reaction = max(0.12, 0.6 - 0.07 * difficulty)
        self.aim_error = max(0.02, 0.24 - 0.035 * difficulty)
        self.think = random.random() * 0.3
        self.move = Vec2()
        self.target = None
        self.react = 0.0
        self.strafe_dir = random.choice([-1, 1])
        self.wander = Vec2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize()
        self.wander_t = 0.0


class Mimic(Bot):
    """A copycat astronaut: copies your suit and gun and hunts only you."""

    def __init__(self, x, y, player):
        super().__init__(x, y, "MIMIC", difficulty=4)
        self.is_mimic = True
        self.suit = player.suit
        self.armor = float(C.SUITS[player.suit]["armor"]) + 20
        self.max_hp = self.hp = 120.0
        w = player.weapon
        self.weapons = [w, None]
        self.ammo = {w: C.WEAPONS[w]["ammo"]}
        self.speed = player.speed * 1.05
        self.oxygen = 500.0


class Alien(Entity):
    def __init__(self, x, y, kind):
        s = C.ALIENS[kind]
        super().__init__(x, y, s["radius"], s["hp"])
        self.kind = kind
        self.speed = s["speed"]
        self.cd = random.random()
        self.wander = Vec2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize()
        self.wander_t = 0.0


class Rock:
    def __init__(self, x, y, r):
        self.pos = Vec2(x, y)
        self.radius = r


class HazardZone:
    def __init__(self, x, y, r, kind):
        self.pos = Vec2(x, y)
        self.radius = r
        self.kind = kind


class Crate:
    def __init__(self, x, y, kind="crate", code=None):
        self.pos = Vec2(x, y)
        self.kind = kind            # crate or vault
        self.opened = False
        self.code = code or []      # vault puzzle: list of "U","D","L","R"


class Pickup:
    def __init__(self, x, y, kind, name=None, amount=0):
        self.pos = Vec2(x, y)
        self.kind = kind            # medkit oxygen armor ammo weapon suit ore crystal
        self.name = name
        self.amount = amount
        self.dead = False

    def label(self):
        names = {"medkit": "Medkit", "oxygen": "Oxygen Tank", "armor": "Armor Plate",
                 "ammo": "Ammo Pack", "ore": "Ore", "crystal": "Crystal"}
        return names.get(self.kind, self.name or self.kind)


class Structure:
    def __init__(self, kind, x, y):
        self.kind = kind
        self.pos = Vec2(x, y)
        self.radius = 22
        self.cd = 0.0


class Companion:
    def __init__(self, x, y):
        self.pos = Vec2(x, y)
        self.vel = Vec2()
        self.radius = 10
        self.repair_t = 0.0
