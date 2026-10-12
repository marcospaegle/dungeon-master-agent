import pytest
from builders import fighter

from dungeon_core.characters.character import Ability
from dungeon_core.characters.draft import (
    CharacterDraft,
    IncompleteCharacterError,
)
from dungeon_core.characters.serializer import CharacterSerializer


def test_an_empty_draft_is_not_a_character_yet():
    draft = CharacterDraft()

    with pytest.raises(IncompleteCharacterError):
        draft.build()
    assert draft.describe().startswith("Not a legal character yet")


def test_a_complete_draft_builds_and_reports_derived_numbers():
    draft = CharacterDraft()
    draft.update(CharacterSerializer.to_dict(fighter()))

    assert draft.build() == fighter()
    assert draft.describe().startswith("Legal so far.")
    assert "armor_class" in draft.describe()


def test_unknown_fields_are_reported_and_nothing_changes():
    draft = CharacterDraft()

    assert draft.update({"name": "Zed", "hat": "red"}) == ["hat"]
    assert '"name"' not in draft.describe()


def test_an_illegal_choice_is_reported_not_raised_by_describe():
    draft = CharacterDraft()
    draft.update(
        CharacterSerializer.to_dict(fighter())
        | {"base_scores": {Ability.STRENGTH.value: 99}}
    )

    assert draft.describe().startswith("Not a legal character yet")


def test_loading_a_character_remembers_what_is_being_edited():
    draft = CharacterDraft()

    draft.load(fighter(name="Thorin"))

    assert draft.editing == "Thorin"
    assert draft.build().name == "Thorin"
