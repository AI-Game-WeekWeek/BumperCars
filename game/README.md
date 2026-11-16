# BumperCars game

`dist/BumperCars.html` is the whole game in one file (about 2.7 MB, works offline except the Google Fonts link).
Double-click it, or put it in OBS / TikTok LIVE Studio as a browser source.

| URL | What you see |
|---|---|
| `BumperCars.html` | the 9:16 stage on the left and the test panel (fake viewers, gift buttons) on the right |
| `BumperCars.html?stage=1` | the 9:16 stage only, scaled to the window: use this one on stream |

## Rebuild after changing pictures or code

```bash
pip install pillow numpy scipy
python3 tools/build_game.py        # reads game/game.src.html and assets/, writes dist/BumperCars.html
```

`game/game.src.html` is the readable source (HTML, CSS and JavaScript). `tools/build_game.py` shrinks every picture in
`assets/` to the size the game draws, finds the profile-picture hole in each car, the inner radius of each rim and the
text area of each banner, and embeds all of it. Text is always placed inside those measured areas.

Screen layout (1080×1920): HUD plates at the top, arena centred at (510, 800) with a 880 px diameter, gift banner or
how-to strip at the bottom. Keep the very top and bottom clear of important things: the app covers them.
