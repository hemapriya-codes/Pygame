# Moon Royale (Space theme)

Top-down astronaut battle royale built with Python + Pygame.

## Run it

```bash
# 1. go into the project folder
cd moon-royale

# 2. (recommended) create a virtual environment
python -m venv venv
#   Windows:      venv\Scripts\activate
#   Mac / Linux:  source venv/bin/activate

# 3. install Pygame
pip install -r requirements.txt

# 4. start the game
python main.py
```
(On Mac/Linux use `python3` / `pip3` if `python` is not found.)

## Controls
| Key | Action |
|---|---|
| W A S D / arrows | move |
| Mouse / left click | aim / shoot |
| E | open crate / vault terminal |
| 1, 2 | switch weapon |
| H | use medkit |
| F | flashlight (bigger vision at night) |
| Z X C V | build Oxygen Generator / Turret / Lab / Habitat Dome (explore level) |
| Arrow keys | enter the vault code (puzzle) |
| ESC | pause / leave puzzle |

## Project layout
```
main.py              entry point (window + main loop)
core/                BACKEND (no drawing, no keyboard)
  config.py          all numbers: guns, suits, hazards, planets, ranks
  vec.py             small 2D vector class
  entities.py        Player, Bot, Mimic, Alien, Projectile, Crate, Pickup...
  ai.py              bot / mimic behaviour
  world.py           the simulation: combat, zone, hazards, loot, levels
  progression.py     save file: rank, rocket, planets, resources
ui/                  FRONTEND (Pygame)
  theme.py           fonts, colours, Button, bars
  render.py          world, rockets, minimap, night overlay, HUD
  screens.py         menu, dashboard, rocket builder, planets, game, result
```

## Push to GitHub
```bash
git init
git add .
git commit -m "Moon Royale space game"
git branch -M main
git remote add origin https://github.com/<your-user>/<your-repo>.git
git push -u origin main
```
