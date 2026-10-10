"""Command-line interface for Lost in the Repository."""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import time
from pathlib import Path

from game_engine import (
    GameState,
    Scene,
    choice_is_available,
    load_state,
    load_story,
    new_game,
    parse_input,
    resolve_choice,
    save_state,
)

BASE_DIR = Path(__file__).resolve().parent


class Display:
    """Terminal output with optional color and typewriter effects."""

    COLORS = {"cyan": "\033[96m", "yellow": "\033[93m", "green": "\033[92m",
              "red": "\033[91m", "dim": "\033[2m", "reset": "\033[0m"}

    def __init__(self, fast: bool = False, no_color: bool = False) -> None:
        self.fast = fast
        self.no_color = no_color
        self._enable_windows_ansi()

    def _enable_windows_ansi(self) -> None:
        if os.name == "nt":
            try:
                kernel32 = ctypes.windll.kernel32
                handle = kernel32.GetStdHandle(-11)
                mode = ctypes.c_uint()
                if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                    kernel32.SetConsoleMode(handle, mode.value | 0x0004)
            except (AttributeError, OSError):
                pass

    def color(self, text: str, name: str) -> str:
        if self.no_color:
            return text
        return f"{self.COLORS[name]}{text}{self.COLORS['reset']}"

    def say(self, text: str = "", color: str | None = None) -> None:
        output = self.color(text, color) if color else text
        if self.fast:
            print(output)
            return
        for character in output:
            print(character, end="", flush=True)
            time.sleep(0.008)
        print()


TITLE = r"""
+--------------------------------------------------------------------------+
|                         LOST IN THE                                      |
|                           REPOSITORY                                     |
+--------------------------------------------------------------------------+
"""


def show_scene(display: Display, scene: Scene, state: GameState) -> None:
    """Render a scene and its available or locked choices."""
    display.say(f"\n{scene.title}", "cyan")
    display.say(scene.text)
    for number, choice in enumerate(scene.choices, 1):
        if choice_is_available(choice, state):
            display.say(f"  {number}. {choice.text}", "yellow")
        else:
            needed = choice.requires_item
            display.say(f"  {number}. {choice.text} [needs {needed}]", "dim")


def ending_count(path: Path, ending_name: str, total: int | None = None) -> tuple[int, int]:
    """Record an ending and return discovered and total counts."""
    if total is None:
        total = count_endings(load_story(BASE_DIR / "story.json"))
    discovered: set[str] = set()
    if path.exists():
        try:
            discovered = set(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            discovered = set()
    discovered.add(ending_name)
    path.write_text(json.dumps(sorted(discovered), indent=2), encoding="utf-8")
    return len(discovered), total


def count_endings(story: dict[str, Scene]) -> int:
    """Return the number of ending scenes in a loaded story."""
    return sum(scene.ending is not None for scene in story.values())


def run_game(args: argparse.Namespace) -> None:
    """Run the main game loop."""
    display = Display(args.fast, args.no_color)
    story = load_story(BASE_DIR / "story.json")
    print(display.color(TITLE, "cyan"))
    try:
        state = load_state(BASE_DIR / "savegame.json") if args.load else new_game()
        if state.current_scene not in story:
            raise KeyError(state.current_scene)
    except (OSError, KeyError, json.JSONDecodeError):
        display.say("No usable save found, so a fresh adventure begins.", "yellow")
        state = new_game()

    while True:
        scene = story[state.current_scene]
        if scene.ending:
            display.say(f"\n{scene.ending['name']}", "green" if scene.ending["type"] != "bad" else "red")
            display.say(scene.text)
            found, total = ending_count(
                BASE_DIR / "endings.json", scene.ending["name"], count_endings(story)
            )
            display.say(f"Endings discovered: {found}/{total}", "cyan")
            try:
                answer = input("\nPlay again? (y/n): ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                display.say("\nGoodbye!", "yellow")
                return
            if answer.startswith("y"):
                state = new_game()
                continue
            return

        show_scene(display, scene, state)
        try:
            command, number = parse_input(input("\n> "), len(scene.choices))
        except (EOFError, KeyboardInterrupt):
            display.say("\nGoodbye!", "yellow")
            return
        except ValueError as error:
            display.say(str(error), "red")
            continue
        if command == "i":
            display.say("Inventory: " + (", ".join(state.inventory) or "empty"), "cyan")
        elif command == "s":
            save_state(state, BASE_DIR / "savegame.json")
            display.say("Progress saved to savegame.json.", "green")
        elif command == "h":
            display.say("Enter a choice number. i = inventory, s = save, h = help, q = quit.", "cyan")
        elif command == "q":
            display.say("The repository will remember your branch. Goodbye!", "yellow")
            return
        else:
            try:
                resolve_choice(scene, number or 0, state)
            except ValueError as error:
                display.say(str(error), "red")


def main() -> None:
    """Parse command-line flags and start the game."""
    parser = argparse.ArgumentParser(description="Lost in the Repository")
    parser.add_argument("--fast", action="store_true", help="disable typewriter effect")
    parser.add_argument("--no-color", action="store_true", help="disable ANSI colors")
    parser.add_argument("--load", action="store_true", help="resume savegame.json")
    run_game(parser.parse_args())


if __name__ == "__main__":
    main()
