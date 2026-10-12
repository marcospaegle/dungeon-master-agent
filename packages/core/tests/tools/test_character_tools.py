from pathlib import Path

import pytest
from builders import fighter

from dungeon_core.characters.adapters.json_repository import (
    JsonCharacterRepository,
)
from dungeon_core.characters.draft import CharacterDraft
from dungeon_core.characters.serializer import CharacterSerializer
from dungeon_core.characters.service import CharacterService
from dungeon_core.tools.character_tools import CharacterTools


class RecordingSheetWriter:
    def write(self, character, destination: Path) -> None:
        destination.write_text(character.name)


@pytest.fixture
def service(tmp_path):
    return CharacterService(
        JsonCharacterRepository(tmp_path),
        RecordingSheetWriter(),
        tmp_path,
    )


def tools(service, draft=None) -> CharacterTools:
    return CharacterTools(draft or CharacterDraft(), service)


def test_the_tools_are_offered_by_name(service):
    names = {t.name for t in tools(service).tools()}

    assert names == {
        "set_fields",
        "get_character",
        "list_characters",
        "load_character",
        "save_character",
    }


def test_set_fields_rejects_unknown_fields(service):
    result = tools(service).set_fields({"hat": "red"})

    assert "Unknown fields" in result
    assert "hat" in result


def test_set_fields_reports_derived_numbers_once_legal(service):
    result = tools(service).set_fields(CharacterSerializer.to_dict(fighter()))

    assert result.startswith("Legal so far.")


def test_list_and_load_saved_characters(service):
    assert tools(service).list_characters() == "No saved characters."
    service.save(fighter(name="Thorin"))
    draft = CharacterDraft()

    assert tools(service, draft).list_characters() == "Thorin"
    assert "Legal so far." in tools(service, draft).load_character("thorin")
    assert draft.editing == "Thorin"
    assert "No saved character" in tools(service).load_character("Zed")


def test_save_refuses_an_illegal_draft_without_asking(service):
    result = tools(service).save_character()

    assert result.startswith("Cannot save")
