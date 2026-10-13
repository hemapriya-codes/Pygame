"""Bot, mimic AI. Every bot thinks a few times per second, then acts every frame."""
from .vec import Vec2
from . import config as C


def _weapon_score(name):
    w = C.WEAPONS[name]
    return w["dmg"] * w["pellets"] / w["cooldown"]


def _choose_weapon(bot):
    best, best_i = -1, bot.slot
    for i, wn in enumerate(bot.weapons):
        if wn and (bot.ammo.get(wn) is None or bot.ammo[wn] > 0):
            s = _weapon_score(wn)
            if s > best:
                best, best_i = s, i
    bot.slot = best_i


def _nearest_loot(bot, world, want_oxygen):
    best, goal = 700.0, None
    for pk in world.pickups:
        if want_oxygen and pk.kind != "oxygen":
            continue
        if pk.kind in ("ore", "crystal"):
            continue
        d = bot.pos.distance_to(pk.pos)
        if d < best:
            best, goal = d, pk.pos
    if not want_oxygen:
        for c in world.crates:
            if c.opened or c.kind != "crate":
                continue
            d = bot.pos.distance_to(c.pos)
            if d < best:
                best, goal = d, c.pos
    return goal


def _decide(bot, world):
    rng = world.rng
    sight = world.sight_range()
    p = world.player

    # ---- choose a target
    target = None
    if bot.is_mimic:
        if p.alive:
            target = p
    else:
        best = sight
        for f in world.fighters:
            if f is bot or not f.alive:
                continue
            d = bot.pos.distance_to(f.pos)
            if d < best:
                best, target = d, f
        for a in world.aliens:
            d = bot.pos.distance_to(a.pos)
            if d < min(best, 300):
                best, target = d, a
    if target is not bot.target:
        bot.react = bot.reaction
    bot.target = target
    _choose_weapon(bot)

    # ---- choose movement (priority list)
    move = Vec2()
    to_center = world.zone_center - bot.pos
    bad = [z for z in world.hazards_at(bot.pos) if not bot.protected(z.kind)]
    if world.use_zone and to_center.length() > world.zone_radius - 140:
        move = to_center.normalize()                       # 1. run into the safe zone
    elif bad:
        move = (bot.pos - bad[0].pos).normalize()          # 2. leave hazard areas
    elif target is not None and not (bot.oxygen < 25 and _nearest_loot(bot, world, True)):
        to = target.pos - bot.pos
        dist = to.length()
        dirn = to.normalize()
        pref = C.WEAPONS[bot.weapon]["range"] * 0.55
        perp = Vec2(-dirn.y, dirn.x) * bot.strafe_dir
        if rng.random() < 0.15:
            bot.strafe_dir *= -1
        if bot.is_mimic or dist > pref + 60:
            move = (dirn + perp * 0.3).normalize()          # 3. close in
        elif dist < pref - 120:
            move = (-dirn + perp * 0.3).normalize()         #    back off
        else:
            move = perp                                     #    strafe
    else:
        goal = _nearest_loot(bot, world, bot.oxygen < 30)   # 4. loot
        if goal is None and bot.oxygen < 30:
            goal = _nearest_loot(bot, world, False)
        if goal is not None:
            move = (goal - bot.pos).normalize()
        else:                                               # 5. wander toward the middle
            bot.wander_t -= 0.3
            if bot.wander_t <= 0:
                bot.wander_t = rng.uniform(1, 3)
                bot.wander = (Vec2(rng.uniform(-1, 1), rng.uniform(-1, 1)) * 0.6
                              + to_center.normalize() * 0.4).normalize()
            move = bot.wander
    bot.move = move


def update_bot(bot, world, dt):
    bot.think -= dt
    if bot.think <= 0:
        bot.think = world.rng.uniform(0.15, 0.4)
        _decide(bot, world)

    bot.vel = bot.vel.lerp(bot.move * bot.speed, min(1.0, 7 * dt))

    t = bot.target
    if t is not None and t.alive:
        to = t.pos - bot.pos
        dist = to.length()
        if dist > 1:
            bot.aim = to.normalize()
        bot.react -= dt
        if dist < C.WEAPONS[bot.weapon]["range"] * 0.9 and bot.react <= 0:
            world.projectiles.extend(bot.try_shoot(world.rng, bot.aim_error))
