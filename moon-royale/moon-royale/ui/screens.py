"""Every screen of the game: menu, dashboard, rocket builder, planet select, play, result."""
import math
import random
import sys

import pygame

from core import config as C
from core.vec import Vec2
from core.world import World
from . import theme as T
from . import render as R


class Screen:
    def __init__(self, app):
        self.app = app
        self.buttons = []

    def handle(self, e):
        for b in self.buttons:
            if b.handle(e):
                return

    def update(self, dt):
        pass

    def draw(self, surf):
        pass

    def draw_buttons(self, surf):
        for b in self.buttons:
            b.draw(surf)


def starfield(n=120):
    return [(random.randint(0, C.SCREEN_W), random.randint(0, C.SCREEN_H),
             random.choice([1, 1, 2, 3]), random.random() * 6) for _ in range(n)]


def draw_stars(surf, stars, t):
    surf.fill(T.DARK)
    for x, y, r, ph in stars:
        v = 150 + int(100 * math.sin(t * 2 + ph))
        pygame.draw.circle(surf, (v, v, v), (x, y), r)


# =========================================================================== MENU
class MenuScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.stars, self.t = starfield(), 0.0
        cx = C.SCREEN_W // 2
        self.buttons = [
            T.Button((cx - 150, 300, 300, 52), "PLAY", lambda: app.go(PlanetScreen(app))),
            T.Button((cx - 150, 366, 300, 52), "ROCKET BUILDER", lambda: app.go(RocketScreen(app))),
            T.Button((cx - 150, 432, 300, 52), "DASHBOARD", lambda: app.go(DashboardScreen(app))),
            T.Button((cx - 150, 498, 300, 52), "QUIT", app.quit),
        ]

    def update(self, dt):
        self.t += dt

    def draw(self, surf):
        draw_stars(surf, self.stars, self.t)
        cx = C.SCREEN_W // 2
        R.draw_rocket(surf, cx, 150 + int(math.sin(self.t * 2) * 6), self.app.profile["rocket"]["body"],
                      self.app.profile["rocket"]["color"], 0.9)
        T.text(surf, "MOON ROYALE", (cx, 255), "xl", T.WHITE, center=True)
        rank = self.app.profile.rank()[0]
        T.text(surf, f"Rank: {rank}   Round: {self.app.profile['round']}", (cx, 575), "m", T.GREY, center=True)
        T.text(surf, "WASD move | Mouse aim+shoot | E interact | 1/2 weapon | H medkit | F flashlight",
               (cx, C.SCREEN_H - 30), "s", T.GREY, center=True)
        self.draw_buttons(surf)


# ===================================================================== DASHBOARD
class DashboardScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.stars = starfield(60)
        self.buttons = [T.Button((30, C.SCREEN_H - 70, 160, 46), "BACK", lambda: app.go(MenuScreen(app)))]

    def draw(self, surf):
        draw_stars(surf, self.stars, 0)
        p = self.app.profile
        rank, into, need = p.rank()
        T.text(surf, "DASHBOARD", (C.SCREEN_W // 2, 50), "l", T.WHITE, center=True)
        T.text(surf, f"Rank: {rank}", (80, 110), "l", T.YELLOW)
        if need:
            T.bar(surf, (80, 160, 500, 24), into / need, T.ACCENT, f"{into}/{need} to next rank")
        else:
            T.text(surf, "MAX RANK", (80, 160), "m", T.GREEN)
        rows = [("Total kills", p["total_kills"]), ("Matches played", p["matches"]), ("Victories", p["wins"]),
                ("Current round (bots)", f"{p['round']}  ->  {C.bots_for_round(p['round'])} bots"),
                ("Ore", p["ore"]), ("Crystal", p["crystal"]),
                ("Robot companion", "UNLOCKED" if p["companion"] else "locked (clear a level)")]
        for i, (k, v) in enumerate(rows):
            T.text(surf, k, (80, 220 + i * 36), "m", T.GREY)
            T.text(surf, v, (380, 220 + i * 36), "m", T.WHITE)
        T.text(surf, "Discovered planets", (700, 110), "m", T.YELLOW)
        for i, pl in enumerate(C.PLANETS):
            known = pl["name"] in p["discovered"]
            col = T.WHITE if known else (80, 80, 95)
            pygame.draw.circle(surf, pl["color"] if known else (50, 50, 60), (720, 160 + i * 50), 16)
            T.text(surf, pl["name"] if known else "???", (750, 150 + i * 50), "m", col)
            if pl["name"] in p["colonies"]:
                T.text(surf, "COLONY", (930, 150 + i * 50), "s", T.GREEN)
            elif pl["name"] in p["cleared"]:
                T.text(surf, "cleared", (930, 150 + i * 50), "s", T.ACCENT)
        self.draw_buttons(surf)


# ================================================================== ROCKET BUILDER
class RocketScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.stars, self.t = starfield(60), 0.0
        self.build()

    def build(self):
        a, p = self.app, self.app.profile
        self.buttons = [T.Button((30, C.SCREEN_H - 70, 160, 46), "BACK", lambda: a.go(MenuScreen(a)))]
        for i, body in enumerate(C.ROCKET_BODIES):
            self.buttons.append(T.Button((470 + i * 200, 120, 190, 44), body, lambda b=body: self.set_body(b)))
        for i in range(len(C.ROCKET_COLORS)):
            self.buttons.append(T.Button((470 + i * 62, 210, 54, 40), str(i + 1), lambda c=i: self.set_color(c)))
        for i, key in enumerate(C.UPGRADES):
            lvl = p["rocket"][key]
            ore, cr = C.upgrade_cost(lvl)
            label = "MAX" if lvl >= C.MAX_UPGRADE else f"BUY {ore}o {cr}c"
            ok = lvl < C.MAX_UPGRADE and p["ore"] >= ore and p["crystal"] >= cr
            self.buttons.append(T.Button((900, 300 + i * 70, 170, 44), label, lambda k=key: self.buy(k), ok))

    def set_body(self, b):
        self.app.profile["rocket"]["body"] = b
        self.app.profile.save()

    def set_color(self, c):
        self.app.profile["rocket"]["color"] = c
        self.app.profile.save()

    def buy(self, key):
        self.app.profile.buy_upgrade(key)
        self.build()

    def update(self, dt):
        self.t += dt

    def draw(self, surf):
        draw_stars(surf, self.stars, self.t)
        p = self.app.profile
        rk = p["rocket"]
        T.text(surf, "ROCKET BUILDER", (C.SCREEN_W // 2, 40), "l", T.WHITE, center=True)
        pygame.draw.rect(surf, T.PANEL, (60, 90, 340, 480), border_radius=12)
        R.draw_rocket(surf, 230, 300 + int(math.sin(self.t * 3) * 5), rk["body"], rk["color"], 2.0)
        T.text(surf, f"{rk['body']}: {C.ROCKET_BODIES[rk['body']]['desc']}", (230, 540), "s", T.GREY, center=True)
        T.text(surf, "Body", (470, 96), "m", T.YELLOW)
        T.text(surf, "Colour", (470, 186), "m", T.YELLOW)
        for i, c in enumerate(C.ROCKET_COLORS):
            pygame.draw.rect(surf, c, (470 + i * 62, 258, 54, 10), border_radius=3)
        T.text(surf, "Upgrades", (470, 280), "m", T.YELLOW)
        T.text(surf, f"Ore: {p['ore']}   Crystal: {p['crystal']}  (collect on explore levels)",
               (470, 566), "s", T.WHITE)
        for i, key in enumerate(C.UPGRADES):
            y = 300 + i * 70
            T.text(surf, C.UPGRADE_INFO[key], (470, y), "s", T.WHITE)
            T.bar(surf, (470, y + 24, 400, 16), rk[key] / C.MAX_UPGRADE, T.ACCENT, f"Lv {rk[key]}/{C.MAX_UPGRADE}")
        self.draw_buttons(surf)


# ===================================================================== PLANET SELECT
class PlanetScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.stars = starfield(60)
        self.sel, self.site, self.mode = 0, 0, "combat"
        self.build()

    def build(self):
        a, p = self.app, self.app.profile
        self.buttons = [T.Button((30, C.SCREEN_H - 70, 160, 46), "BACK", lambda: a.go(MenuScreen(a)))]
        for i, pl in enumerate(C.PLANETS):
            known = pl["name"] in p["discovered"]
            self.buttons.append(T.Button((40, 110 + i * 72, 320, 60), pl["name"] if known else "???",
                                         lambda i=i: self.pick(i), known))
        cleared = C.PLANETS[self.sel]["name"] in p["cleared"]
        self.buttons.append(T.Button((420, 520, 220, 50), "COMBAT", lambda: self.set_mode("combat")))
        self.buttons.append(T.Button((650, 520, 220, 50), "EXPLORE / BUILD", lambda: self.set_mode("explore"), cleared))
        self.buttons.append(T.Button((880, 520, 190, 50), "LAUNCH", self.launch))

    def pick(self, i):
        self.sel = i
        if C.PLANETS[i]["name"] not in self.app.profile["cleared"]:
            self.mode = "combat"
        self.build()

    def set_mode(self, m):
        self.mode = m

    def launch(self):
        self.app.go(GameScreen(self.app, self.mode, self.sel, self.site))

    def handle(self, e):
        super().handle(e)
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:       # choose a landing site on the map
            for i, (n, fx, fy) in enumerate(C.LANDING_SITES):
                sx, sy = 440 + int(fx * 260), 250 + int(fy * 260)
                if (e.pos[0] - sx) ** 2 + (e.pos[1] - sy) ** 2 < 18 ** 2:
                    self.site = i

    def draw(self, surf):
        draw_stars(surf, self.stars, 0)
        T.text(surf, "CHOOSE DESTINATION", (C.SCREEN_W // 2, 40), "l", T.WHITE, center=True)
        pl = C.PLANETS[self.sel]
        haz = C.HAZARDS[pl["hazard"]]
        pygame.draw.circle(surf, pl["color"], (890, 200), 110)
        pygame.draw.circle(surf, haz["color"], (890, 200), 110, 4)
        T.text(surf, pl["name"], (420, 100), "l", T.YELLOW)
        T.text(surf, f"Gravity {pl['gravity']}    Temperature {pl['temp']}", (420, 150), "m", T.WHITE)
        T.text(surf, f"Hazard: {haz['label']}  ->  equip {haz['suit']}", (420, 185), "m", haz["color"])
        T.text(surf, "Landing site (click a dot):", (420, 222), "s", T.GREY)
        pygame.draw.rect(surf, (20, 24, 44), (440, 250, 260, 260))
        pygame.draw.rect(surf, T.GREY, (440, 250, 260, 260), 2)
        for i, (n, fx, fy) in enumerate(C.LANDING_SITES):
            sx, sy = 440 + int(fx * 260), 250 + int(fy * 260)
            pygame.draw.circle(surf, T.GREEN if i == self.site else T.GREY, (sx, sy), 12)
        T.text(surf, C.LANDING_SITES[self.site][0], (720, 260), "m", T.GREEN)
        p = self.app.profile
        T.text(surf, f"Combat: {C.bots_for_round(p['round'])} bots  (round {p['round']})", (720, 300), "s", T.WHITE)
        T.text(surf, "Clear a planet in combat to unlock Explore", (720, 324), "s", T.GREY)
        T.text(surf, f"Mode: {self.mode.upper()}", (420, 585), "m", T.ACCENT)
        self.draw_buttons(surf)


# ============================================================================= GAME
class GameScreen(Screen):
    LAND_TIME = 3.0

    def __init__(self, app, mode, planet, site):
        super().__init__(app)
        self.world = World(mode, planet, app.profile, site)
        self.cam = R.Camera()
        self.cam.follow(self.world.player.pos)
        self.t = 0.0
        self.phase = "landing"            # landing -> play -> takeoff
        self.phase_t = 0.0
        self.paused = False

    def handle(self, e):
        w = self.world
        if e.type != pygame.KEYDOWN or self.phase != "play":
            return
        if e.key == pygame.K_ESCAPE:
            if w.puzzle:
                w.puzzle_cancel()
            else:
                self.paused = not self.paused
            return
        if self.paused:
            if e.key == pygame.K_q:
                self.app.go(MenuScreen(self.app))
            return
        if w.puzzle:
            keys = {pygame.K_UP: "U", pygame.K_DOWN: "D", pygame.K_LEFT: "L", pygame.K_RIGHT: "R"}
            if e.key in keys:
                w.puzzle_press(keys[e.key])
            return
        if e.key == pygame.K_e:
            w.interact()
        elif e.key == pygame.K_1:
            w.switch_weapon(0)
        elif e.key == pygame.K_2:
            w.switch_weapon(1)
        elif e.key == pygame.K_h:
            w.use_medkit()
        elif e.key == pygame.K_f:
            w.toggle_flashlight()
        else:
            for name, s in C.STRUCTURES.items():
                if e.key == getattr(pygame, "K_" + s["key"].lower()):
                    w.build(name)

    def update(self, dt):
        self.t += dt
        w = self.world
        if self.phase == "landing":
            self.phase_t += dt
            if self.phase_t >= self.LAND_TIME:
                self.phase, self.phase_t = "play", 0.0
        elif self.phase == "play":
            if self.paused:
                return
            keys = pygame.key.get_pressed()
            mv = Vec2((keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT]),
                      (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP]))
            mx, my = pygame.mouse.get_pos()
            inp = dict(move=mv.normalize(), aim=self.cam.to_world(mx, my),
                       shoot=pygame.mouse.get_pressed()[0])
            w.update(dt, inp)
            self.cam.follow(w.player.pos)
            if w.state != "playing":
                self.phase, self.phase_t = "takeoff", 0.0
        elif self.phase == "takeoff":
            self.phase_t += dt
            w.update(0, {})
            if self.phase_t >= 2.2:
                self.app.go(ResultScreen(self.app, w.result))

    def draw(self, surf):
        w = self.world
        R.draw_world(surf, w, self.cam, self.t)
        px, py = self.cam.to_screen(w.player.pos)
        if self.phase == "landing":
            k = self.phase_t / self.LAND_TIME
            drop = (1 - k) * (1 - k) * 700
            pygame.draw.circle(surf, (0, 0, 0), (px, py + 40), int(10 + 40 * k))      # growing shadow
            if k < 0.85:
                R.draw_rocket(surf, px, int(py - 40 - drop), self.app.profile["rocket"]["body"],
                              self.app.profile["rocket"]["color"], 1.0)
            else:
                R.draw_fighter(surf, self.cam, w.player)
            R.draw_night(surf, w, self.cam)
            T.text(surf, "LANDING...", (C.SCREEN_W // 2, 140), "l", T.WHITE, center=True)
            T.text(surf, f"Planet {w.planet['name']}  -  drop starts in {max(0, self.LAND_TIME - self.phase_t):.0f}s",
                   (C.SCREEN_W // 2, 180), "m", T.GREY, center=True)
            return
        R.draw_night(surf, w, self.cam)
        if self.phase == "takeoff":
            k = self.phase_t / 2.2
            R.draw_rocket(surf, px, int(py - 40 - k * k * 900), self.app.profile["rocket"]["body"],
                          self.app.profile["rocket"]["color"], 1.0)
            R.draw_hud(surf, w, self.app.profile, "LEVEL CLEARED - TAKING OFF" if w.state == "won" else "YOU DIED")
            return
        R.draw_hud(surf, w, self.app.profile)
        if w.puzzle:
            self.draw_puzzle(surf, w.puzzle)
        if self.paused:
            pygame.draw.rect(surf, (0, 0, 0), (0, 0, C.SCREEN_W, C.SCREEN_H))
            T.text(surf, "PAUSED", (C.SCREEN_W // 2, 300), "xl", T.WHITE, center=True)
            T.text(surf, "ESC = resume     Q = quit to menu", (C.SCREEN_W // 2, 380), "m", T.GREY, center=True)

    def draw_puzzle(self, surf, pz):
        box = pygame.Rect(0, 0, 520, 260)
        box.center = (C.SCREEN_W // 2, C.SCREEN_H // 2)
        pygame.draw.rect(surf, (20, 14, 40), box, border_radius=12)
        pygame.draw.rect(surf, (230, 180, 255), box, 3, border_radius=12)
        T.text(surf, "ALIEN VAULT TERMINAL", (box.centerx, box.y + 30), "m", T.WHITE, center=True)
        T.text(surf, "Repeat the code with the arrow keys  (ESC to leave)", (box.centerx, box.y + 62),
               "s", T.GREY, center=True)
        arrows = {"U": "^", "D": "v", "L": "<", "R": ">"}
        for i, d in enumerate(pz["crate"].code):
            r = pygame.Rect(box.x + 50 + i * 110, box.y + 100, 90, 90)
            done = i < pz["pos"]
            pygame.draw.rect(surf, (60, 150, 90) if done else (40, 30, 70), r, border_radius=10)
            pygame.draw.rect(surf, T.WHITE, r, 2, border_radius=10)
            T.text(surf, arrows[d], r.center, "xl", T.WHITE, center=True)
        T.text(surf, f"Wrong attempts: {pz['fails']}", (box.centerx, box.bottom - 25), "s", T.RED, center=True)


# =========================================================================== RESULT
class ResultScreen(Screen):
    def __init__(self, app, res):
        super().__init__(app)
        self.res = res
        self.stars = starfield(80)
        self.ranked_up = app.profile.apply_result(res)
        cx = C.SCREEN_W // 2
        if res["won"] and res["mode"] == "combat":
            first = ("PLAY AGAIN (next round)", lambda: app.go(PlanetScreen(app)))
        else:
            first = ("TRY AGAIN", lambda: app.go(PlanetScreen(app)))
        self.buttons = [T.Button((cx - 260, 560, 250, 50), first[0], first[1]),
                        T.Button((cx + 10, 560, 250, 50), "MAIN MENU", lambda: app.go(MenuScreen(app)))]

    def draw(self, surf):
        draw_stars(surf, self.stars, 0)
        r, cx = self.res, C.SCREEN_W // 2
        title = ("LEVEL CLEARED" if r["mode"] == "combat" else "COLONY ESTABLISHED") if r["won"] else "MISSION FAILED"
        T.text(surf, title, (cx, 90), "xl", T.GREEN if r["won"] else T.RED, center=True)
        rows = [("Planet", r["planet"]), ("Total kills", r["kills"]),
                ("  players/bots/mimics", r["fighter_kills"]), ("  aliens", r["alien_kills"]),
                ("Match placement", f"#{r['placement']}"), ("Time survived", f"{int(r['time'])} s"),
                ("Rank points earned", f"+{r['points']}"),
                ("Ore / Crystal collected", f"{r['resources']['ore']} / {r['resources']['crystal']}")]
        for i, (k, v) in enumerate(rows):
            T.text(surf, k, (cx - 260, 170 + i * 38), "m", T.GREY)
            T.text(surf, v, (cx + 120, 170 + i * 38), "m", T.WHITE)
        rank, into, need = self.app.profile.rank()
        T.text(surf, f"Rank: {rank}" + ("   RANK UP!" if self.ranked_up else ""), (cx, 500), "l",
               T.YELLOW, center=True)
        if r["won"] and r["mode"] == "combat":
            T.text(surf, "Explore mode unlocked on this planet - build a colony!", (cx, 535), "s", T.CYAN, center=True)
        self.draw_buttons(surf)
