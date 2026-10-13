"""All drawing code: world, rockets, astronauts, minimap, night overlay, HUD."""
import math
import pygame

from core import config as C
from . import theme as T

_overlay = None      # re-used full-screen alpha surfaces
_night = None


def _surf(kind):
    global _overlay, _night
    if kind == "zone":
        if _overlay is None:
            _overlay = pygame.Surface((C.SCREEN_W, C.SCREEN_H), pygame.SRCALPHA)
        return _overlay
    if _night is None:
        _night = pygame.Surface((C.SCREEN_W, C.SCREEN_H), pygame.SRCALPHA)
    return _night


class Camera:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0

    def follow(self, pos):
        self.x = min(max(pos.x - C.SCREEN_W / 2, 0), C.WORLD_W - C.SCREEN_W)
        self.y = min(max(pos.y - C.SCREEN_H / 2, 0), C.WORLD_H - C.SCREEN_H)

    def to_screen(self, pos):
        return int(pos.x - self.x), int(pos.y - self.y)

    def to_world(self, sx, sy):
        from core.vec import Vec2
        return Vec2(sx + self.x, sy + self.y)

    def visible(self, pos, margin=80):
        return (-margin < pos.x - self.x < C.SCREEN_W + margin and
                -margin < pos.y - self.y < C.SCREEN_H + margin)


# ------------------------------------------------------------------ rocket
def draw_rocket(surf, cx, cy, body="Scout", color_idx=0, scale=1.0, flame=True):
    col = C.ROCKET_COLORS[color_idx % len(C.ROCKET_COLORS)]
    dark = tuple(max(0, c - 70) for c in col)
    s = scale

    def P(pts):
        return [(cx + x * s, cy + y * s) for x, y in pts]

    if flame:
        pygame.draw.polygon(surf, (255, 190, 60), P([(-10, 55), (10, 55), (0, 95)]))
        pygame.draw.polygon(surf, (255, 90, 40), P([(-5, 55), (5, 55), (0, 78)]))
    if body == "Scout":
        pygame.draw.polygon(surf, dark, P([(-16, 20), (-38, 58), (-14, 50)]))
        pygame.draw.polygon(surf, dark, P([(16, 20), (38, 58), (14, 50)]))
        pygame.draw.rect(surf, col, (cx - 15 * s, cy - 40 * s, 30 * s, 100 * s), border_radius=int(14 * s))
        pygame.draw.polygon(surf, (240, 240, 250), P([(-15, -34), (15, -34), (0, -78)]))
    elif body == "Hauler":
        pygame.draw.rect(surf, dark, (cx - 36 * s, cy - 10 * s, 18 * s, 60 * s), border_radius=int(6 * s))
        pygame.draw.rect(surf, dark, (cx + 18 * s, cy - 10 * s, 18 * s, 60 * s), border_radius=int(6 * s))
        pygame.draw.rect(surf, col, (cx - 20 * s, cy - 45 * s, 40 * s, 105 * s), border_radius=int(10 * s))
        pygame.draw.polygon(surf, (240, 240, 250), P([(-20, -40), (20, -40), (0, -75)]))
    else:   # Tank
        pygame.draw.rect(surf, dark, (cx - 30 * s, cy - 20 * s, 60 * s, 80 * s), border_radius=int(8 * s))
        pygame.draw.rect(surf, col, (cx - 24 * s, cy - 42 * s, 48 * s, 100 * s), border_radius=int(10 * s))
        pygame.draw.polygon(surf, (200, 200, 210), P([(-24, -38), (24, -38), (0, -66)]))
        pygame.draw.line(surf, dark, (cx - 24 * s, cy), (cx + 24 * s, cy), max(1, int(4 * s)))
    pygame.draw.circle(surf, (150, 220, 255), (int(cx), int(cy - 15 * s)), max(3, int(8 * s)))
    pygame.draw.circle(surf, (255, 255, 255), (int(cx), int(cy - 15 * s)), max(3, int(8 * s)), 2)


# --------------------------------------------------------------- astronaut
def draw_fighter(surf, cam, f, show_name=True):
    x, y = cam.to_screen(f.pos)
    r = int(f.radius)
    col = f.color
    if f.flash > 0:
        col = (255, 255, 255)
    pygame.draw.circle(surf, (0, 0, 0), (x + 3, y + 4), r)                       # shadow
    gx, gy = x + f.aim.x * (r + 10), y + f.aim.y * (r + 10)
    gun_col = C.WEAPONS[f.weapon]["color"]
    pygame.draw.line(surf, (50, 50, 60), (x, y), (gx, gy), 7)
    pygame.draw.line(surf, gun_col, (x, y), (gx, gy), 3)
    pygame.draw.circle(surf, col, (x, y), r)
    pygame.draw.circle(surf, (40, 50, 80), (x, y), r, 3)
    vx, vy = x + f.aim.x * 6, y + f.aim.y * 6                                     # visor
    pygame.draw.circle(surf, (30, 60, 110), (int(vx), int(vy)), 7)
    pygame.draw.circle(surf, (120, 190, 255), (int(vx - 2), int(vy - 2)), 2)
    if f.is_mimic:
        pygame.draw.circle(surf, T.RED, (x, y), r + 5, 3)
    if not f.is_player:
        T.bar(surf, (x - 20, y - r - 14, 40, 6), f.hp / f.max_hp, T.RED)
        if show_name:
            T.text(surf, f.name, (x, y - r - 22), "s", T.RED if f.is_mimic else T.GREY, center=True)


def draw_alien(surf, cam, a):
    x, y = cam.to_screen(a.pos)
    col = C.ALIENS[a.kind]["color"]
    if a.flash > 0:
        col = (255, 255, 255)
    r = int(a.radius)
    pygame.draw.circle(surf, (0, 0, 0), (x + 3, y + 4), r)
    pygame.draw.circle(surf, col, (x, y), r)
    pygame.draw.circle(surf, (20, 20, 30), (x, y), r, 2)
    pygame.draw.circle(surf, (255, 255, 255), (x - r // 3, y - r // 4), max(2, r // 4))
    pygame.draw.circle(surf, (255, 255, 255), (x + r // 3, y - r // 4), max(2, r // 4))
    pygame.draw.circle(surf, (0, 0, 0), (x - r // 3, y - r // 4), max(1, r // 8))
    pygame.draw.circle(surf, (0, 0, 0), (x + r // 3, y - r // 4), max(1, r // 8))
    if a.hp < a.max_hp:
        T.bar(surf, (x - 16, y - r - 10, 32, 5), a.hp / a.max_hp, T.GREEN)


# ------------------------------------------------------------------- world
PICK_COL = {"medkit": (255, 90, 110), "oxygen": (90, 230, 240), "armor": (110, 150, 255),
            "ammo": (255, 210, 80), "weapon": (150, 255, 150), "suit": (255, 160, 255),
            "ore": (170, 170, 180), "crystal": (190, 120, 255)}
PICK_LETTER = {"medkit": "+", "oxygen": "O", "armor": "A", "ammo": "B", "weapon": "W",
               "suit": "S", "ore": "o", "crystal": "c"}


def draw_world(surf, world, cam, t):
    surf.fill(world.planet["color"])
    # grid (gives a sense of movement)
    step = 200
    gx = -int(cam.x) % step
    gy = -int(cam.y) % step
    gcol = tuple(min(255, c + 14) for c in world.planet["color"])
    for x in range(gx, C.SCREEN_W, step):
        pygame.draw.line(surf, gcol, (x, 0), (x, C.SCREEN_H))
    for y in range(gy, C.SCREEN_H, step):
        pygame.draw.line(surf, gcol, (0, y), (C.SCREEN_W, y))
    # world border
    pygame.draw.rect(surf, (200, 60, 60), (-int(cam.x), -int(cam.y), C.WORLD_W, C.WORLD_H), 4)

    # hazard zones
    ov = _surf("zone")
    ov.fill((0, 0, 0, 0))
    for z in world.zones:
        if cam.visible(z.pos, z.radius):
            sx, sy = cam.to_screen(z.pos)
            col = C.HAZARDS[z.kind]["color"]
            pygame.draw.circle(ov, col + (60,), (sx, sy), int(z.radius))
            pygame.draw.circle(ov, col + (160,), (sx, sy), int(z.radius), 3)
    surf.blit(ov, (0, 0))
    for z in world.zones:
        if cam.visible(z.pos, z.radius):
            sx, sy = cam.to_screen(z.pos)
            T.text(surf, C.HAZARDS[z.kind]["label"], (sx, sy), "m", C.HAZARDS[z.kind]["color"], center=True)

    # rocks
    for r in world.rocks:
        if cam.visible(r.pos, r.radius):
            sx, sy = cam.to_screen(r.pos)
            pygame.draw.circle(surf, (90, 90, 100), (sx, sy), int(r.radius))
            pygame.draw.circle(surf, (60, 60, 70), (sx, sy), int(r.radius), 4)
            pygame.draw.circle(surf, (120, 120, 130), (sx - int(r.radius * .3), sy - int(r.radius * .3)),
                               int(r.radius * .3))

    # crates / vaults
    for c in world.crates:
        if c.opened or not cam.visible(c.pos):
            continue
        sx, sy = cam.to_screen(c.pos)
        if c.kind == "vault":
            pygame.draw.rect(surf, (110, 60, 160), (sx - 22, sy - 22, 44, 44), border_radius=6)
            pygame.draw.rect(surf, (230, 180, 255), (sx - 22, sy - 22, 44, 44), 3, border_radius=6)
            T.text(surf, "VAULT", (sx, sy), "s", T.WHITE, center=True)
        else:
            pygame.draw.rect(surf, (200, 150, 60), (sx - 16, sy - 16, 32, 32), border_radius=4)
            pygame.draw.rect(surf, (255, 220, 120), (sx - 16, sy - 16, 32, 32), 3, border_radius=4)
            T.text(surf, "?", (sx, sy), "m", (60, 40, 10), center=True)

    # pickups
    for pk in world.pickups:
        if cam.visible(pk.pos):
            sx, sy = cam.to_screen(pk.pos)
            bob = int(math.sin(t * 4 + pk.pos.x) * 3)
            col = PICK_COL[pk.kind]
            pygame.draw.circle(surf, col, (sx, sy + bob), 11)
            pygame.draw.circle(surf, (255, 255, 255), (sx, sy + bob), 11, 2)
            T.text(surf, PICK_LETTER[pk.kind], (sx, sy + bob), "s", (20, 20, 30), center=True)

    # structures
    for s in world.structures:
        sx, sy = cam.to_screen(s.pos)
        col = C.STRUCTURES[s.kind]["color"]
        pygame.draw.rect(surf, col, (sx - 22, sy - 22, 44, 44), border_radius=8)
        pygame.draw.rect(surf, (255, 255, 255), (sx - 22, sy - 22, 44, 44), 2, border_radius=8)
        T.text(surf, s.kind.split()[0], (sx, sy), "s", (20, 20, 30), center=True)

    # meteor warnings
    for pos, left in world.meteors:
        sx, sy = cam.to_screen(pos)
        pr = max(0.0, left / 1.2)
        pygame.draw.circle(surf, (255, 80, 60), (sx, sy), 70, 2)
        pygame.draw.circle(surf, (255, 140, 60), (sx, sy), int(70 * (1 - pr)) + 4)
        pygame.draw.circle(surf, (255, 200, 120), (sx, int(sy - 400 * pr)), 8)

    # aliens, fighters, companion, projectiles
    for a in world.aliens:
        if cam.visible(a.pos):
            draw_alien(surf, cam, a)
    for f in world.fighters:
        if f.alive and cam.visible(f.pos):
            draw_fighter(surf, cam, f)
    if world.companion:
        sx, sy = cam.to_screen(world.companion.pos)
        pygame.draw.circle(surf, (120, 200, 255), (sx, sy), 10)
        pygame.draw.circle(surf, (255, 255, 255), (sx, sy), 10, 2)
        pygame.draw.circle(surf, (255, 80, 80), (sx, sy), 3)
    for pr in world.projectiles:
        if cam.visible(pr.pos):
            sx, sy = cam.to_screen(pr.pos)
            pygame.draw.circle(surf, pr.color, (sx, sy), 4)
            pygame.draw.circle(surf, (255, 255, 255), (sx, sy), 2)

    # shrinking safe zone: red outside, ring at the edge
    if world.use_zone:
        ov.fill((200, 20, 20, 70))
        cx, cy = cam.to_screen(world.zone_center)
        pygame.draw.circle(ov, (0, 0, 0, 0), (cx, cy), int(world.zone_radius))
        surf.blit(ov, (0, 0))
        pygame.draw.circle(surf, (255, 255, 255), (cx, cy), int(world.zone_radius), 3)


def draw_night(surf, world, cam):
    n = world.night
    if n < 0.05:
        return
    A = int(238 * n)
    ov = _surf("night")
    ov.fill((0, 0, 12, A))
    cx, cy = cam.to_screen(world.player.pos)
    r = world.vision_radius()
    for frac, a in ((1.0, 0.75), (0.82, 0.55), (0.64, 0.35), (0.46, 0.15), (0.30, 0.0)):
        pygame.draw.circle(ov, (0, 0, 12, int(A * a)), (cx, cy), int(r * frac))
    surf.blit(ov, (0, 0))


# ----------------------------------------------------------------- minimap
def draw_minimap(surf, world, rect):
    x, y, w, h = rect
    sc = w / C.WORLD_W
    mm = pygame.Surface((w, h), pygame.SRCALPHA)
    mm.fill((8, 10, 22, 215))
    for z in world.zones:
        pygame.draw.circle(mm, C.HAZARDS[z.kind]["color"] + (110,), (int(z.pos.x * sc), int(z.pos.y * sc)),
                           max(2, int(z.radius * sc)))
    if world.use_zone:
        pygame.draw.circle(mm, (255, 255, 255, 230), (int(world.zone_center.x * sc), int(world.zone_center.y * sc)),
                           max(2, int(world.zone_radius * sc)), 2)
    p = world.player
    for c in world.crates:
        if not c.opened and p.pos.distance_to(c.pos) < world.scan_range:
            pygame.draw.rect(mm, (255, 215, 90) if c.kind == "crate" else (220, 130, 255),
                             (int(c.pos.x * sc) - 2, int(c.pos.y * sc) - 2, 4, 4))
    for s in world.structures:
        pygame.draw.rect(mm, (120, 255, 170), (int(s.pos.x * sc) - 3, int(s.pos.y * sc) - 3, 6, 6))
    for a in world.aliens:
        if p.pos.distance_to(a.pos) < world.scan_range:
            pygame.draw.circle(mm, (200, 90, 240), (int(a.pos.x * sc), int(a.pos.y * sc)), 2)
    for f in world.fighters:
        if f.alive and not f.is_player and p.pos.distance_to(f.pos) < world.scan_range:
            pygame.draw.circle(mm, (255, 70, 70), (int(f.pos.x * sc), int(f.pos.y * sc)), 3)
    pygame.draw.circle(mm, (255, 255, 255), (int(p.pos.x * sc), int(p.pos.y * sc)), 4)
    pygame.draw.circle(mm, (80, 200, 255), (int(p.pos.x * sc), int(p.pos.y * sc)), 7, 1)
    surf.blit(mm, (x, y))
    pygame.draw.rect(surf, (150, 170, 220), rect, 2)
    T.text(surf, "MAP", (x + 6, y + 4), "s", T.GREY)


# --------------------------------------------------------------------- HUD
def draw_hud(surf, world, profile, phase_text=None):
    p = world.player
    # --- left panel: health / armor / oxygen
    pygame.draw.rect(surf, (10, 12, 26, 200), (10, 10, 300, 118), border_radius=8)
    pygame.draw.rect(surf, T.ACCENT, (10, 10, 300, 118), 2, border_radius=8)
    T.bar(surf, (20, 18, 280, 22), p.hp / p.max_hp, T.RED, f"HEALTH {int(p.hp)}")
    T.bar(surf, (20, 46, 280, 22), p.armor / p.max_armor, T.BLUE, f"ARMOR {int(p.armor)}")
    low = p.oxygen < 25 and int(world.time * 4) % 2 == 0
    T.bar(surf, (20, 74, 280, 22), p.oxygen / p.max_oxygen, T.RED if low else T.CYAN, f"OXYGEN {int(p.oxygen)}")
    T.text(surf, f"{p.suit}   Medkits: {p.medkits} (H)", (20, 102), "s", T.WHITE)

    # --- top centre: objective, kills, rank
    rank, into, need = profile.rank()
    cx = C.SCREEN_W // 2
    if world.mode == "combat":
        T.text(surf, f"ENEMIES LEFT: {world.enemies_left()}", (cx, 22), "l", T.YELLOW, center=True)
        T.text(surf, f"Kill {world.enemies_left()} more to unlock the planet-exploration level",
               (cx, 54), "s", T.GREY, center=True)
    else:
        T.text(surf, f"COLONY {int(world.colony_progress() * 100)}%", (cx, 22), "l", T.GREEN, center=True)
        T.text(surf, "Build all 4: Z oxygen  X turret  C lab  V dome", (cx, 54), "s", T.GREY, center=True)
    T.text(surf, f"Kills: {p.kills}   Match rank: #{world.placement()}   Rank: {rank}",
           (cx, 76), "m", T.WHITE, center=True)
    mins, secs = divmod(int(world.time), 60)
    day = "NIGHT" if world.night > 0.5 else "DAY"
    T.text(surf, f"{world.planet['name']}   {mins:02d}:{secs:02d}   {day}", (cx, 100), "s", T.GREY, center=True)

    # --- minimap + hazard warning
    draw_minimap(surf, world, (C.SCREEN_W - 210, 10, 200, 200))
    for z in world.hazards_at(p.pos):
        h = C.HAZARDS[z.kind]
        if not p.protected(z.kind):
            T.text(surf, f"{h['label']}! Wear {h['suit']}", (C.SCREEN_W - 210, 218), "s", h["color"])
            break
    else:
        if world.use_zone and p.pos.distance_to(world.zone_center) > world.zone_radius:
            T.text(surf, "OUTSIDE SAFE ZONE!", (C.SCREEN_W - 210, 218), "s", T.RED)
    if world.use_zone:
        T.text(surf, f"Alive: {sum(1 for f in world.fighters if f.alive)}/{len(world.fighters)}",
               (C.SCREEN_W - 210, 238), "s", T.WHITE)

    # --- bottom centre: weapons
    for i, wn in enumerate(p.weapons):
        bx = cx - 130 + i * 140
        sel = (i == p.slot)
        pygame.draw.rect(surf, (10, 12, 26), (bx, C.SCREEN_H - 62, 128, 50), border_radius=8)
        pygame.draw.rect(surf, T.YELLOW if sel else T.GREY, (bx, C.SCREEN_H - 62, 128, 50), 2, border_radius=8)
        if wn:
            ammo = p.ammo.get(wn)
            T.text(surf, f"{i + 1}  {wn}", (bx + 6, C.SCREEN_H - 56), "s", C.WEAPONS[wn]["color"])
            T.text(surf, "ammo: inf" if ammo is None else f"ammo: {ammo}", (bx + 6, C.SCREEN_H - 34), "s", T.WHITE)
        else:
            T.text(surf, f"{i + 1}  empty", (bx + 6, C.SCREEN_H - 45), "s", T.GREY)

    # --- explore resources
    if world.mode == "explore":
        T.text(surf, f"Ore: {world.resources['ore']}   Crystal: {world.resources['crystal']}",
               (20, C.SCREEN_H - 100), "m", T.YELLOW)
    if world.companion:
        T.text(surf, "Robot companion: ONLINE", (20, C.SCREEN_H - 130), "s", T.CYAN)

    # --- message feed
    for i, (m, ttl) in enumerate(world.messages):
        T.text(surf, m, (20, 140 + i * 22), "s", T.WHITE)
    if phase_text:
        T.text(surf, phase_text, (cx, C.SCREEN_H // 2 - 150), "l", T.WHITE, center=True)
