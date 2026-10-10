# Lost in the Repository

**Lost in the Repository** is a spooky, silly command-line choose-your-own-adventure game. You are a first-time open source contributor trapped in a haunted GitHub repository. Find your way through merge-conflict monsters, a stale-branch graveyard, and a grumpy maintainer ghost to get your first pull request merged before Hacktoberfest ends.

## Features

- JSON graph keeps story content separate from the Python engine.
- Inventory items unlock routes and secret content.
- Four endings: one good, two bad, and one secret ending.
- Typewriter text, ANSI colors, ASCII title art, and Windows terminal support.
- Save/resume progress and persistent ending discovery.
- Standard library only, with `unittest` coverage for graph links, inventory-aware
ending reachability, ending types, secret-item gating, save/load round trips,
ending totals, inventory logic, and input parsing.

## Run

```text
python adventure.py
```

The game resolves `story.json`, `savegame.json`, and `endings.json` beside
`adventure.py`, so it can also be launched from another folder with a path
such as `python path/to/adventure.py`.

Flags:

- `--fast` disables the typewriter effect.
- `--no-color` disables ANSI colors.
- `--load` resumes from the save beside `adventure.py`; an invalid or missing
  save starts a fresh game.

## How to play

Choose a numbered option. Locked options are dimmed and show the required item. During play, use `i` for inventory, `s` to save, `h` for help, and `q` to quit. When you reach an ending, the game records it in `endings.json` and offers a replay.

## Tests

```text
python -m unittest discover -s tests -v
```

## Project structure

```text
adventure.py       Terminal UI and game loop
game_engine.py     Story loading, state, inventory, and choice logic
story.json         Scene graph and ending data
tests/test_engine.py
README.md          This documentation
.gitignore         Python and generated-save exclusions
```
