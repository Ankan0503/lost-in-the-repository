"""Unit tests for the story graph and engine."""

import unittest
from pathlib import Path

from game_engine import (
    choice_is_available,
    load_story,
    new_game,
    parse_input,
    resolve_choice,
)


class EngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.story = load_story(Path(__file__).parents[1] / "story.json")

    def test_every_next_points_to_existing_scene(self):
        for scene in self.story.values():
            for choice in scene.choices:
                self.assertIn(choice.next, self.story)

    def test_every_ending_is_reachable(self):
        seen = set()
        pending = ["entrance"]
        while pending:
            scene_id = pending.pop()
            if scene_id in seen:
                continue
            seen.add(scene_id)
            pending.extend(choice.next for choice in self.story[scene_id].choices)
        endings = [scene.id for scene in self.story.values() if scene.ending]
        self.assertTrue(endings)
        self.assertTrue(set(endings).issubset(seen))

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
