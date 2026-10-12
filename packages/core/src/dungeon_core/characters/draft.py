import json
from collections.abc import Mapping
from dataclasses import fields as dataclass_fields
from typing import Any

from dungeon_core.characters.character import Character
from dungeon_core.characters.serializer import CharacterSerializer

_FIELD_NAMES = {field.name for field in dataclass_fields(Character)}


class IncompleteCharacterError(Exception):
    """The draft is not a legal Character yet; the message says why."""


class CharacterDraft:
    """A Character being built, held as its JSON fields until legal.

    ``editing`` is the name of the saved Character the draft started
    from, if any, so saving it under that name is not an overwrite of
    someone else's.
    """

    def __init__(self) -> None:
        self._fields: dict[str, Any] = {}
        self._editing: str | None = None
        self._saved = False

    @property
    def editing(self) -> str | None:
        return self._editing

    @property
    def saved(self) -> bool:
        return self._saved

    def mark_saved(self) -> None:
        self._saved = True

    def load(self, character: Character) -> None:
        """Start from a saved Character, replacing the fields."""
        self._fields = CharacterSerializer.to_dict(character)
        self._editing = character.name

    def update(self, fields: Mapping[str, Any]) -> list[str]:
        """Set fields; return the unknown names, changing nothing."""
        unknown = sorted(fields.keys() - _FIELD_NAMES)
        if not unknown:
            self._fields.update(fields)
        return unknown

    def build(self) -> Character:
        try:
            return CharacterSerializer.from_dict(self._fields)
        except (KeyError, TypeError, ValueError) as error:
            raise IncompleteCharacterError(repr(error)) from error

    def describe(self) -> str:
        """The fields so far and the numbers code derives from them."""
        shown = json.dumps(self._fields, indent=2)
        try:
            character = self.build()
        except IncompleteCharacterError as error:
            return f"Not a legal character yet: {error}\n{shown}"
        derived = json.dumps(self._derived_numbers(character), indent=2)
        return f"Legal so far.\n{shown}\nDerived by code:\n{derived}"

    @staticmethod
    def _derived_numbers(character: Character) -> dict:
        return {
            "ability_scores": dict(character.ability_scores),
            "ability_modifiers": dict(character.ability_modifiers),
            "proficiency_bonus": character.proficiency_bonus,
            "saving_throws": dict(character.saving_throws),
            "skill_bonuses": dict(character.skill_bonuses),
            "armor_class": character.armor_class,
            "hit_points": character.hit_points,
            "hit_dice": character.hit_dice,
            "initiative": character.initiative,
            "passive_perception": character.passive_perception,
        }
