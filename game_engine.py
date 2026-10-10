"""Core story loading, state, inventory, and choice logic."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Choice:
    """A selectable edge in the story graph."""

    text: str
    next: str
    requires_item: str | None = None
    gives_item: str | None = None


@dataclass
class Scene:
    """A story scene and its outgoing choices."""

    id: str
    title: str
    text: str
    choices: list[Choice] = field(default_factory=list)
    ending: dict[str, str] | None = None


@dataclass
class GameState:
    """Mutable progress that can be saved and restored."""

    current_scene: str
    inventory: list[str] = field(default_factory=list)
    visited_scenes: list[str] = field(default_factory=list)


def load_story(path: str | Path = "story.json") -> dict[str, Scene]:
    """Load and validate story scenes from JSON."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    scenes: dict[str, Scene] = {}
    for item in raw["scenes"]:
        choices = [Choice(**choice) for choice in item.get("choices", [])]
        scenes[item["id"]] = Scene(
            id=item["id"],
            title=item["title"],
            text=item["text"],
            choices=choices,
            ending=item.get("ending"),
        )
    return scenes


def new_game(start_scene: str = "entrance") -> GameState:
    """Return a fresh game state."""
    return GameState(current_scene=start_scene, visited_scenes=[start_scene])


def choice_is_available(choice: Choice, state: GameState) -> bool:
    """Return whether the player owns the choice's required item."""
    return not choice.requires_item or choice.requires_item in state.inventory


def resolve_choice(scene: Scene, choice_number: int, state: GameState) -> Choice:
    """Apply a numbered choice and return the selected choice."""
    if choice_number < 1 or choice_number > len(scene.choices):
        raise ValueError("That choice number is out of range.")
    choice = scene.choices[choice_number - 1]
    if not choice_is_available(choice, state):
        raise ValueError("You do not have the item needed for that choice.")
    if choice.gives_item and choice.gives_item not in state.inventory:
        state.inventory.append(choice.gives_item)
    state.current_scene = choice.next
    if choice.next not in state.visited_scenes:
        state.visited_scenes.append(choice.next)
    return choice


def save_state(state: GameState, path: str | Path = "savegame.json") -> None:
    """Write progress to disk."""
    payload = {
        "current_scene": state.current_scene,
        "inventory": state.inventory,
        "visited_scenes": state.visited_scenes,
    }
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_state(path: str | Path = "savegame.json") -> GameState:
    """Read progress from disk."""
    payload: dict[str, Any] = json.loads(Path(path).read_text(encoding="utf-8"))
    return GameState(
        current_scene=payload["current_scene"],
        inventory=list(payload.get("inventory", [])),
        visited_scenes=list(payload.get("visited_scenes", [])),
    )


def parse_input(value: str, choice_count: int) -> tuple[str, int | None]:
    """Parse a command or a valid choice number."""
    command = value.strip().lower()
    if command in {"i", "s", "h", "q"}:
        return command, None
    if command.isdigit():
        number = int(command)
        if 1 <= number <= choice_count:
            return "choice", number
    raise ValueError("Please enter a listed number, or i, s, h, or q.")
