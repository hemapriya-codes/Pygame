"""The whole game simulation. It never draws anything and never reads the keyboard:
the UI feeds it an `inp` dict each frame and reads its state back to render."""
import math
import random

from .vec import Vec2
from . import config as C
from . import ai
from .entities import (Player, Bot, Mimic, Alien, Rock, HazardZone, Crate, Pickup,
                       Projectile, Structure, Companion)


class World:
    def __init__(self, mode, planet_index, profile, site=0, seed=None):
        self.rng = random.Random(seed)
        self.mode = mode                          # "combat" or "explore"
        self.planet_index = planet_index
        self.planet = C.PLANETS[planet_index]
        self.round_no = profile["round"]
        self.W, self.H = C.WORLD_W, C.WORLD_H
        self.time = 0.0
        self.state = "playing"                    # playing / won / lost
        self.result = None
        self.messages = []
        self.projectiles, self.pickups, self.crates = [], [], []
        self.aliens, self.structures, self.meteors = [], [], []
        self.fighters, self.rocks, self.zones = [], [], []
        self.resources = {"ore": 0, "crystal": 0}
        self.puzzle = None
        self.flashlight = False
        self.alien_timer = 6.0
        self.mimic_timer = 30.0
        self.mimics_pending = 0
        self.enemy_total = 0
        self.use_zone = (mode == "combat")
        self.zone_center = Vec2(self.W / 2 + self.rng.uniform(-350, 350),
                                self.H / 2 + self.rng.uniform(-350, 350))

        rk = profile["rocket"]
        body = C.ROCKET_BODIES[rk["body"]]
        self.speed_mult = body["speed"] * (1 + 0.06 * rk["engine"])
        self.bonus_armor = body["shield"] + 8 * rk["shield"]
        self.start_medkits = body["cargo"] + rk["cargo"]
        self.scan_range = 600 + 250 * rk["scanner"]

        sx, sy = C.LANDING_SITES[site][1], C.LANDING_SITES[site][2]
        self.player = Player(self.W * sx, self.H * sy)
        self.player.armor = float(self.bonus_armor)
        self.player.medkits = self.start_medkits
        self.fighters.append(self.player)

        self.companion = Companion(self.player.pos.x - 40, self.player.pos.y - 40) \
            if profile.get("companion") else None
        if self.companion:
            self.scan_range += 300

        self._make_terrain()
        if mode == "combat":
            self._spawn_bots()
        else:
            self._spawn_explore()
        self.msg(f"Landed on {self.planet['name']}. Hazard: {C.HAZARDS[self.planet['hazard']]['label']}")

    # ------------------------------------------------------------ set-up
    def _rand_pos(self, margin=200, away_from=None, min_dist=0):
        for _ in range(30):
            p = Vec2(self.rng.uniform(margin, self.W - margin), self.rng.uniform(margin, self.H - margin))
            if away_from is None or p.distance_to(away_from) >= min_dist:
                return p
        return p

    def _make_terrain(self):
        spawn = self.player.pos
        for _ in range(55):
            p = self._rand_pos(100)
            if p.distance_to(spawn) > 220:
                self.rocks.append(Rock(p.x, p.y, self.rng.uniform(25, 70)))
        kinds = [self.planet["hazard"], self.planet["hazard"]]
        others = [k for k in C.HAZARDS if k != self.planet["hazard"]]
        kinds += self.rng.sample(others, 2)
        for k in kinds:
            p = self._rand_pos(400, spawn, 500)
            self.zones.append(HazardZone(p.x, p.y, self.rng.uniform(220, 320), k))

    def _spawn_bots(self):
        n = C.bots_for_round(self.round_no)
        for i in range(n):
            p = self._rand_pos(150, self.player.pos, 650)
            b = Bot(p.x, p.y, f"Bot-{i + 1}", self.round_no)
            if self.rng.random() < 0.25:
                b.give_weapon(self.rng.choice(["Plasma Rifle", "Pulse Shotgun"]))
            self.fighters.append(b)
        self.mimics_pending = min(4, max(0, self.round_no - 1))
        self.enemy_total = n + self.mimics_pending
        for _ in range(35):
            p = self._rand_pos(150)
            self.crates.append(Crate(p.x, p.y))
        for _ in range(30):
            p = self._rand_pos(150)
            k, name = self._roll_loot()
            self.pickups.append(Pickup(p.x, p.y, k, name))

    def _spawn_explore(self):
        for _ in range(12):
            p = self._rand_pos(150)
            self.crates.append(Crate(p.x, p.y))
        for _ in range(3):                                   # abandoned labs / vaults
            p = self._rand_pos(300, self.player.pos, 600)
            code = [self.rng.choice("UDLR") for _ in range(4)]
            self.crates.append(Crate(p.x, p.y, "vault", code))
        for _ in range(45):                                  # resource nodes
            p = self._rand_pos(150)
            if self.rng.random() < 0.65:
                self.pickups.append(Pickup(p.x, p.y, "ore", amount=self.rng.randint(5, 10)))
            else:
                self.pickups.append(Pickup(p.x, p.y, "crystal", amount=self.rng.randint(3, 6)))
        for _ in range(10):
            p = self._rand_pos(150)
            k, name = self._roll_loot()
            self.pickups.append(Pickup(p.x, p.y, k, name))
        for _ in range(6):
            self._spawn_alien()
        self.msg("Explore the planet, open vaults (E), then build a colony (Z X C V).")

    # ------------------------------------------------------------ helpers
    def msg(self, text):
        self.messages.append([text, 5.0])
        self.messages = self.messages[-6:]

    @property
    def night(self):
        """0 = full day, 1 = full night."""
        return 0.5 - 0.5 * math.cos(2 * math.pi * self.time / C.DAY_LENGTH)

    def sight_range(self):
        return 520 - 260 * self.night

    def vision_radius(self):
        r = 950 - 710 * self.night
        return r + (170 if self.flashlight else 0)

    @property
    def zone_radius(self):
        if not self.use_zone:
            return 1e9
        return max(C.ZONE_MIN_RADIUS,
                   C.ZONE_START_RADIUS - max(0.0, self.time - C.ZONE_GRACE) * C.ZONE_SHRINK_PER_SEC)

    def hazards_at(self, pos):
        return [z for z in self.zones if pos.distance_to(z.pos) < z.radius]

    def enemies_left(self):
        return sum(1 for f in self.fighters if f is not self.player and f.alive) + self.mimics_pending

    def placement(self):
        p = self.player
        return 1 + sum(1 for f in self.fighters if f is not p and f.kills > p.kills)

    def colony_progress(self):
        return len({s.kind for s in self.structures}) / len(C.STRUCTURES)

    # ------------------------------------------------------------ loot
    def _roll_loot(self):
        r = self.rng.random()
        suits = ["Heat Suit", "Rad Suit", "Hazmat Suit", "Gravity Suit"]
        if r < 0.55:      # common
            return self.rng.choice([("medkit", None), ("oxygen", None), ("ammo", None), ("armor", None)])
        if r < 0.85:      # uncommon
            return self.rng.choice([("weapon", "Plasma Rifle"), ("weapon", "Pulse Shotgun"),
                                    ("suit", self.rng.choice(suits)), ("armor", None)])
        if r < 0.97:      # rare
            return self.rng.choice([("weapon", "Ion Sniper"), ("weapon", "Gravity Gun"),
                                    ("suit", self.rng.choice(suits))])
        return ("suit", "Shield Suit")  # epic

    def _drop(self, pos, kind, name=None, amount=0):
        off = Vec2(self.rng.uniform(-30, 30), self.rng.uniform(-30, 30))
        self.pickups.append(Pickup(pos.x + off.x, pos.y + off.y, kind, name, amount))

    def open_crate(self, crate, by):
        if crate.opened:
            return
        crate.opened = True
        if crate.kind == "vault":
            self._drop(crate.pos, *self.rng.choice([("weapon", "Ion Sniper"), ("suit", "Shield Suit")]))
            self._drop(crate.pos, "crystal", amount=self.rng.randint(10, 20))
            self._drop(crate.pos, "armor")
            if by is self.player:
                self.msg("Vault opened! Rare alien tech inside.")
        else:
            for _ in range(2):
                k, name = self._roll_loot()
                self._drop(crate.pos, k, name)
            if by is self.player:
                self.msg("Loot crate opened")

    def _apply_pickup(self, f, pk):
        k = pk.kind
        if k == "medkit":
            if f.is_player:
                if f.medkits >= 5:
                    return False
                f.medkits += 1
            elif f.hp >= f.max_hp:
                return False
            else:
                f.hp = min(f.max_hp, f.hp + 35)
        elif k == "oxygen":
            if f.oxygen >= f.max_oxygen - 1:
                return False
            f.oxygen = min(f.max_oxygen, f.oxygen + 35)
        elif k == "armor":
            if f.armor >= f.max_armor:
                return False
            f.armor = min(f.max_armor, f.armor + 30)
        elif k == "ammo":
            for w in f.weapons:
                if w:
                    f.add_ammo(w, (C.WEAPONS[w]["ammo"] or 0) // 2)
        elif k == "weapon":
            f.give_weapon(pk.name)
        elif k == "suit":
            f.wear(pk.name)
        elif k in ("ore", "crystal"):
            if not f.is_player:
                return False
            self.resources[k] += pk.amount
        if f.is_player:
            self.msg(f"Picked up {pk.label()}" + (f" x{pk.amount}" if pk.amount else ""))
        return True

    # ------------------------------------------------------------ player actions (called by the UI)
    def switch_weapon(self, idx):
        self.player.switch(idx)

    def toggle_flashlight(self):
        self.flashlight = not self.flashlight

    def use_medkit(self):
        p = self.player
        if p.alive and p.medkits > 0 and p.hp < p.max_hp:
            p.medkits -= 1
            p.hp = min(p.max_hp, p.hp + 35)
            self.msg("Medkit used (+35 HP)")

    def interact(self):
        if self.puzzle or not self.player.alive:
            return
        best, target = 80.0, None
        for c in self.crates:
            if not c.opened:
                d = self.player.pos.distance_to(c.pos)
                if d < best:
                    best, target = d, c
        if target is None:
            return
        if target.kind == "vault":
            self.puzzle = {"crate": target, "pos": 0, "fails": 0}
            self.msg("Vault terminal: enter the arrow code")
        else:
            self.open_crate(target, self.player)

    def puzzle_press(self, d):
        pz = self.puzzle
        if not pz:
            return
        if d == pz["crate"].code[pz["pos"]]:
            pz["pos"] += 1
            if pz["pos"] >= len(pz["crate"].code):
                self.open_crate(pz["crate"], self.player)
                self.puzzle = None
        else:
            pz["pos"] = 0
            pz["fails"] += 1
            self.msg("Wrong code!")

    def puzzle_cancel(self):
        self.puzzle = None

    def build(self, kind):
        if self.mode != "explore" or not self.player.alive:
            return
        s = C.STRUCTURES[kind]
        if any(st.kind == kind for st in self.structures):
            self.msg(f"{kind} already built")
            return
        if self.resources["ore"] < s["ore"] or self.resources["crystal"] < s["crystal"]:
            self.msg(f"{kind} needs {s['ore']} ore + {s['crystal']} crystal")
            return
        self.resources["ore"] -= s["ore"]
        self.resources["crystal"] -= s["crystal"]
        pos = self.player.pos + self.player.aim * 70
        self.structures.append(Structure(kind, pos.x, pos.y))
        self.msg(f"Built {kind}")
        if self.colony_progress() >= 1.0:
            self.msg("COLONY ESTABLISHED!")
            self._finish(True)

    # ------------------------------------------------------------ main update
    def update(self, dt, inp):
        if self.state != "playing":
            return
        dt = min(dt, 0.05)
        self.time += dt
        p = self.player

        self._update_player(dt, inp)
        for f in self.fighters:
            if f is p or not f.alive:
                continue
            ai.update_bot(f, self, dt)
            self._integrate(f, dt)
            for c in self.crates:
                if not c.opened and c.kind == "crate" and f.pos.distance_to(c.pos) < 40:
                    self.open_crate(c, f)
        for f in self.fighters:
            if f.alive:
                self._survival(f, dt)

        self._spawning(dt)
        self._update_aliens(dt)
        self._update_structures(dt)
        self._update_meteors(dt)
        self._update_projectiles(dt)
        self._update_pickups(dt)
        self._update_companion(dt)
        self._handle_deaths()

        for m in self.messages:
            m[1] -= dt
        self.messages = [m for m in self.messages if m[1] > 0]

        if self.state == "playing":
            if not p.alive:
                self._finish(False)
            elif self.mode == "combat" and self.enemies_left() == 0:
                self.msg("ALL ENEMIES ELIMINATED - LEVEL CLEARED!")
                self._finish(True)

    def _update_player(self, dt, inp):
        p = self.player
        if not p.alive:
            return
        move = inp.get("move") or Vec2()
        if self.puzzle:
            move = Vec2()
        slippery = any(z.kind == "lowgrav" for z in self.hazards_at(p.pos)) and not p.protected("lowgrav")
        k = 1.4 if slippery else 10.0
        p.vel = p.vel.lerp(move * (p.speed * self.speed_mult), min(1.0, k * dt))
        aim = inp.get("aim")
        if aim is not None:
            d = aim - p.pos
            if d.length() > 1:
                p.aim = d.normalize()
        if inp.get("shoot") and not self.puzzle:
            self.projectiles.extend(p.try_shoot(self.rng, 0.0))
        self._integrate(p, dt)

    def _integrate(self, e, dt):
        e.pos = e.pos + (e.vel + e.push) * dt
        e.push = e.push * (0.001 ** dt)
        self._collide(e)
        if hasattr(e, "cooldown"):
            e.cooldown = max(0.0, e.cooldown - dt)
        e.flash = max(0.0, e.flash - dt)

    def _collide(self, e):
        for r in self.rocks:
            d = e.pos - r.pos
            dist = d.length()
            mn = r.radius + e.radius
            if dist < mn:
                e.pos = r.pos + (d.normalize() if dist > 1e-6 else Vec2(1, 0)) * mn
        e.pos = Vec2(min(max(e.pos.x, e.radius), self.W - e.radius),
                     min(max(e.pos.y, e.radius), self.H - e.radius))

    def _env_damage(self, f, amount):
        f.hp -= amount
        if f.hp <= 0:
            f.hp = 0
            f.alive = False
            f.last_attacker = None

    def _survival(self, f, dt):
        f.oxygen -= C.OXYGEN_DRAIN * dt
        if f.oxygen <= 0:
            f.oxygen = 0
            self._env_damage(f, 5 * dt)
        if self.use_zone and f.pos.distance_to(self.zone_center) > self.zone_radius:
            self._env_damage(f, C.ZONE_DPS * dt)
        if not f.alive:
            return
        dome = any(s.kind == "Habitat Dome" and f.pos.distance_to(s.pos) < 220 for s in self.structures)
        for z in self.hazards_at(f.pos):
            dps = C.HAZARDS[z.kind]["dps"]
            if dps and not f.protected(z.kind) and not dome:
                self._env_damage(f, dps * dt)

    # ------------------------------------------------------------ spawning / aliens
    def _spawn_alien(self, near=None):
        pos = self._rand_pos(150)
        if near is not None:
            ang = self.rng.uniform(0, 6.283)
            pos = near + Vec2(math.cos(ang), math.sin(ang)) * self.rng.uniform(500, 800)
            pos = Vec2(min(max(pos.x, 100), self.W - 100), min(max(pos.y, 100), self.H - 100))
        kinds = ["Crawler", "Crawler"]
        if self.time > 40 or self.round_no >= 2 or self.mode == "explore":
            kinds += ["Spitter"]
        if (self.round_no >= 2 and self.time > 80) or self.mode == "explore":
            kinds += ["Brute"]
        self.aliens.append(Alien(pos.x, pos.y, self.rng.choice(kinds)))

    def _spawning(self, dt):
        self.alien_timer -= dt
        cap = 4 + self.round_no if self.mode == "combat" else 8
        if self.alien_timer <= 0:
            self.alien_timer = 12.0 if self.mode == "combat" else 8.0
            if len(self.aliens) < cap and self.player.alive:
                self._spawn_alien(self.player.pos)
        if self.mimics_pending > 0:
            self.mimic_timer -= dt
            if self.mimic_timer <= 0:
                self.mimic_timer = 8.0
                self.mimics_pending -= 1
                p = self._rand_pos(300, self.player.pos, 700)
                m = Mimic(p.x, p.y, self.player)
                self.fighters.append(m)
                self.msg("WARNING: a MIMIC copied your suit and gun!")

    def _update_aliens(self, dt):
        for a in self.aliens:
            if not a.alive:
                continue
            s = C.ALIENS[a.kind]
            a.cd -= dt
            tgt, best = None, 550.0
            for f in self.fighters:
                if f.alive:
                    d = a.pos.distance_to(f.pos)
                    if d < best:
                        best, tgt = d, f
            move = Vec2()
            if tgt is not None:
                to = tgt.pos - a.pos
                dist = to.length()
                dirn = to.normalize()
                if s["ranged"]:
                    move = dirn if dist > 300 else (-dirn if dist < 200 else Vec2())
                    if a.cd <= 0 and dist < 420:
                        a.cd = 1.6
                        self.projectiles.append(Projectile(a.pos.copy(), dirn * 380, s["dmg"], a,
                                                           "alien", 1.4, (220, 120, 255)))
                else:
                    move = dirn
                    if dist < a.radius + tgt.radius + 4 and a.cd <= 0:
                        a.cd = 0.9
                        tgt.damage(s["dmg"], None)
            else:
                a.wander_t -= dt
                if a.wander_t <= 0:
                    a.wander_t = self.rng.uniform(1, 3)
                    a.wander = Vec2(self.rng.uniform(-1, 1), self.rng.uniform(-1, 1)).normalize()
                move = a.wander * 0.4
            a.vel = move * a.speed
            self._integrate(a, dt)

    def _update_structures(self, dt):
        p = self.player
        for s in self.structures:
            s.cd -= dt
            d = p.pos.distance_to(s.pos)
            if s.kind == "Oxygen Generator" and d < 180 and p.alive:
                p.oxygen = min(p.max_oxygen, p.oxygen + 6 * dt)
            elif s.kind == "Habitat Dome" and d < 220 and p.alive:
                p.oxygen = min(p.max_oxygen, p.oxygen + 10 * dt)
            elif s.kind == "Lab" and d < 140 and p.alive:
                p.hp = min(p.max_hp, p.hp + 3 * dt)
            elif s.kind == "Turret" and s.cd <= 0:
                best, tgt = 450.0, None
                for a in self.aliens:
                    dd = s.pos.distance_to(a.pos)
                    if a.alive and dd < best:
                        best, tgt = dd, a
                if tgt is not None:
                    s.cd = 0.5
                    dirn = (tgt.pos - s.pos).normalize()
                    self.projectiles.append(Projectile(s.pos.copy(), dirn * 800, 12, s, "turret",
                                                       0.7, (255, 140, 100)))

    def _update_meteors(self, dt):
        mz = [z for z in self.zones if z.kind == "meteor"]
        if mz:
            self.meteor_timer = getattr(self, "meteor_timer", 0.0) - dt
            if self.meteor_timer <= 0:
                self.meteor_timer = 0.7
                z = self.rng.choice(mz)
                ang, r = self.rng.uniform(0, 6.283), self.rng.uniform(0, z.radius)
                self.meteors.append([z.pos + Vec2(math.cos(ang), math.sin(ang)) * r, 1.2])
        for m in self.meteors:
            m[1] -= dt
            if m[1] <= 0:
                for f in self.fighters:
                    if f.alive and f.pos.distance_to(m[0]) < 70 and not f.protected("meteor"):
                        f.damage(35, None)
                for a in self.aliens:
                    if a.alive and a.pos.distance_to(m[0]) < 70:
                        a.hp -= 35
                        a.alive = a.hp > 0
        self.meteors = [m for m in self.meteors if m[1] > 0]

    # ------------------------------------------------------------ projectiles / pickups / deaths
    def _update_projectiles(self, dt):
        for pr in self.projectiles:
            pr.pos = pr.pos + pr.vel * dt
            pr.life -= dt
            if pr.life <= 0 or not (0 <= pr.pos.x <= self.W and 0 <= pr.pos.y <= self.H):
                pr.dead = True
                continue
            for r in self.rocks:
                if pr.pos.distance_to(r.pos) < r.radius:
                    pr.dead = True
                    break
            if pr.dead:
                continue
            if pr.team in ("fighter", "alien"):
                for f in self.fighters:
                    if f.alive and f is not pr.owner and pr.pos.distance_to(f.pos) < f.radius + pr.radius:
                        f.damage(pr.dmg, pr.owner if pr.team == "fighter" else None)
                        if pr.knockback:
                            f.push = f.push + pr.vel.normalize() * pr.knockback
                        pr.dead = True
                        break
            if pr.dead:
                continue
            if pr.team in ("fighter", "turret"):
                for a in self.aliens:
                    if a.alive and pr.pos.distance_to(a.pos) < a.radius + pr.radius:
                        a.hp -= pr.dmg
                        a.flash = 0.15
                        if pr.knockback:
                            a.push = a.push + pr.vel.normalize() * pr.knockback
                        if a.hp <= 0:
                            a.alive = False
                            self._alien_died(a, pr.owner if pr.team == "fighter" else None)
                        pr.dead = True
                        break
        self.projectiles = [p for p in self.projectiles if not p.dead]
        self.aliens = [a for a in self.aliens if a.alive]

    def _alien_died(self, a, killer):
        if killer is not None:
            killer.kills += 1
            killer.alien_kills += 1
            killer.oxygen = min(killer.max_oxygen, killer.oxygen + C.OXYGEN_PER_ALIEN)
            if killer.is_player:
                self.msg(f"{a.kind} killed  +{C.OXYGEN_PER_ALIEN} O2")
        if self.rng.random() < 0.35:
            k = self.rng.choice(["oxygen", "ammo", "medkit"])
            self._drop(a.pos, k)
        if self.mode == "explore" and self.rng.random() < 0.5:
            self._drop(a.pos, "ore", amount=self.rng.randint(3, 6))

    def _update_pickups(self, dt):
        for pk in self.pickups:
            for f in self.fighters:
                if f.alive and f.pos.distance_to(pk.pos) < f.radius + 18:
                    if self._apply_pickup(f, pk):
                        pk.dead = True
                        break
        self.pickups = [p for p in self.pickups if not p.dead]

    def _update_companion(self, dt):
        c = self.companion
        if not c or not self.player.alive:
            return
        goal = self.player.pos + Vec2(-45, -45)
        c.vel = c.vel.lerp((goal - c.pos) * 4, min(1.0, 5 * dt))
        c.pos = c.pos + c.vel * dt
        for pk in self.pickups:                    # collects nearby loot for you
            if c.pos.distance_to(pk.pos) < 160 and self._apply_pickup(self.player, pk):
                pk.dead = True
        self.pickups = [p for p in self.pickups if not p.dead]
        c.repair_t += dt                           # repairs your armor slowly
        if c.repair_t >= 2.0:
            c.repair_t = 0.0
            self.player.armor = min(self.player.max_armor, self.player.armor + 2)

    def _handle_deaths(self):
        for f in self.fighters:
            if f.alive or f.dead_done:
                continue
            f.dead_done = True
            k = f.last_attacker
            if k is not None and k is not f:
                k.kills += 1
                k.oxygen = min(k.max_oxygen, k.oxygen + C.OXYGEN_PER_KILL)
                self.msg(f"{k.name} eliminated {f.name}" + ("  +25 O2" if k.is_player else ""))
            else:
                self.msg(("You were" if f.is_player else f"{f.name} was") + " lost to the void")
            if f.is_mimic:
                self._drop(f.pos, "suit", "Shield Suit")
                self._drop(f.pos, "weapon", "Ion Sniper")
            elif not f.is_player:
                if f.weapon != "Blaster Pistol":
                    self._drop(f.pos, "weapon", f.weapon)
                if self.rng.random() < 0.8:
                    self._drop(f.pos, "oxygen")
                if self.rng.random() < 0.5:
                    self._drop(f.pos, "armor")

    # ------------------------------------------------------------ end of level
    def _finish(self, won):
        self.state = "won" if won else "lost"
        p = self.player
        fk = p.kills - p.alien_kills
        pts = fk * 10 + p.alien_kills * 3 + int(self.time / 60 * 5)
        if won:
            pts += 50 if self.mode == "combat" else 80
        self.result = dict(won=won, mode=self.mode, kills=p.kills, fighter_kills=fk,
                           alien_kills=p.alien_kills, time=self.time, points=pts,
                           resources=dict(self.resources), planet=self.planet["name"],
                           planet_index=self.planet_index, placement=self.placement())
