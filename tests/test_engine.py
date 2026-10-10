"""Unit tests for the story graph and engine."""

import json
import tempfile
import unittest
from pathlib import Path

from adventure import count_endings
from game_engine import (
    GameState,
    choice_is_available,
    load_state,
    load_story,
    new_game,
    parse_input,
    resolve_choice,
    save_state,
)


class EngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.story_path = Path(__file__).parents[1] / "story.json"
        cls.story = load_story(cls.story_path)

    def test_every_next_points_to_existing_scene(self):
        for scene in self.story.values():
            for choice in scene.choices:
                self.assertIn(choice.next, self.story)

    def reachable_states(self, story=None):
        story = story or self.story
        seen = set()
        pending = [("entrance", frozenset())]
        while pending:
            scene_id, inventory = pending.pop()
            state_key = (scene_id, inventory)
            if state_key in seen:
                continue
            seen.add(state_key)
            scene = story[scene_id]
            for choice in scene.choices:
                if choice.requires_item and choice.requires_item not in inventory:
                    continue
                next_inventory = set(inventory)
                if choice.gives_item:
                    next_inventory.add(choice.gives_item)
                pending.append((choice.next, frozenset(next_inventory)))
        return seen

    def test_every_ending_is_reachable_with_inventory_rules(self):
        reachable = {scene_id for scene_id, _ in self.reachable_states()}
        endings = {scene.id for scene in self.story.values() if scene.ending}
        self.assertTrue(endings)
        self.assertTrue(endings.issubset(reachable))

    def test_story_has_four_endings_and_required_types(self):
        endings = [scene.ending for scene in self.story.values() if scene.ending]
        self.assertGreaterEqual(len(endings), 4)
        ending_types = {ending["type"] for ending in endings}
        self.assertTrue({"good", "bad", "secret"}.issubset(ending_types))

    def test_secret_ending_needs_collectible_item(self):
        secret = next(scene for scene in self.story.values()
                      if scene.ending and scene.ending["type"] == "secret")
        required = {
            choice.requires_item
            for scene in self.story.values()
            for choice in scene.choices
            if choice.next == secret.id and choice.requires_item
        }
        self.assertTrue(required)
        stripped = json.loads(self.story_path.read_text(encoding="utf-8"))
        for scene in stripped["scenes"]:
            for choice in scene.get("choices", []):
                if choice.get("gives_item") in required:
                    choice.pop("gives_item")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "stripped.json"
            path.write_text(json.dumps(stripped), encoding="utf-8")
            stripped_story = load_story(path)
        reachable = {scene_id for scene_id, _ in self.reachable_states(stripped_story)}
        self.assertNotIn(secret.id, reachable)

    def test_every_required_item_is_granted_somewhere(self):
        granted = {
            choice.gives_item
            for scene in self.story.values()
            for choice in scene.choices
            if choice.gives_item
        }
        required = {
            choice.requires_item
            for scene in self.story.values()
            for choice in scene.choices
            if choice.requires_item
        }
        self.assertTrue(required.issubset(granted))

    def test_inventory_add_and_require_logic(self):
        state = new_game()
        self.assertFalse(choice_is_available(self.story["graveyard"].choices[0], state))
        resolve_choice(self.story["terminal"], 1, state)
        self.assertIn("lantern", state.inventory)
        self.assertTrue(choice_is_available(self.story["graveyard"].choices[0], state))

    def test_save_and_load_round_trip(self):
        state = GameState("workshop", ["lantern", "key"], ["entrance", "terminal", "workshop"])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "savegame.json"
            save_state(state, path)
            self.assertEqual(load_state(path), state)

    def test_ending_total_comes_from_story(self):
        self.assertEqual(count_endings(self.story), sum(
            scene.ending is not None for scene in self.story.values()
        ))

    def test_input_parsing(self):
        self.assertEqual(parse_input(" 2 ", 3), ("choice", 2))
        self.assertEqual(parse_input("I", 3), ("i", None))
        self.assertEqual(parse_input("q", 3), ("q", None))
        with self.assertRaises(ValueError):
            parse_input("4", 3)
        with self.assertRaises(ValueError):
            parse_input("banana", 3)


if __name__ == "__main__":
    unittest.main()
