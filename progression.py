"""Saved player progress: rank, rocket, planets, resources."""
import copy
import json
import os

from . import config as C

SAVE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "savegame.json")

DEFAULT = dict(
    rank_points=0, total_kills=0, matches=0, wins=0, round=1, companion=False,
    ore=0, crystal=0,
    discovered=["Kepler-7"], cleared=[], colonies=[],
    rocket=dict(body="Scout", color=0, engine=0, shield=0, cargo=0, scanner=0),
)


class Profile(dict):
    @classmethod
    def load(cls):
        data = copy.deepcopy(DEFAULT)
        try:
            with open(SAVE_FILE) as fh:
                saved = json.load(fh)
            for k, v in saved.items():
                if isinstance(v, dict) and isinstance(data.get(k), dict):
                    data[k].update(v)
                else:
                    data[k] = v
        except (OSError, ValueError):
            pass
        return cls(data)

    def save(self):
        try:
            with open(SAVE_FILE, "w") as fh:
                json.dump(self, fh, indent=2)
        except OSError:
            pass

    def rank(self):
        """Returns (rank_name, points_into_rank, points_needed_for_next or None)."""
        pts, name, base, nxt = self["rank_points"], C.RANKS[0][0], 0, None
        for i, (n, need) in enumerate(C.RANKS):
            if pts >= need:
                name, base = n, need
                nxt = C.RANKS[i + 1][1] if i + 1 < len(C.RANKS) else None
        return name, pts - base, (nxt - base) if nxt is not None else None

    def apply_result(self, res):
        old = self.rank()[0]
        self["rank_points"] += res["points"]
        self["total_kills"] += res["kills"]
        self["matches"] += 1
        self["ore"] += res["resources"]["ore"]
        self["crystal"] += res["resources"]["crystal"]
        if res["won"]:
            self["wins"] += 1
            name = res["planet"]
            if res["mode"] == "combat":
                self["round"] += 1
                self["companion"] = True              # robot companion unlocked
                if name not in self["cleared"]:
                    self["cleared"].append(name)
                nxt = res["planet_index"] + 1
                if nxt < len(C.PLANETS) and C.PLANETS[nxt]["name"] not in self["discovered"]:
                    self["discovered"].append(C.PLANETS[nxt]["name"])
            elif name not in self["colonies"]:
                self["colonies"].append(name)
        self.save()
        return self.rank()[0] != old

    def buy_upgrade(self, key):
        lvl = self["rocket"][key]
        if lvl >= C.MAX_UPGRADE:
            return False
        ore, crys = C.upgrade_cost(lvl)
        if self["ore"] < ore or self["crystal"] < crys:
            return False
        self["ore"] -= ore
        self["crystal"] -= crys
        self["rocket"][key] = lvl + 1
        self.save()
        return True
