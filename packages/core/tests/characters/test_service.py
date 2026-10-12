from pathlib import Path

from builders import fighter

from dungeon_core.characters.adapters.json_repository import (
    JsonCharacterRepository,
)
from dungeon_core.characters.service import CharacterService


class RecordingSheetWriter:
    def __init__(self) -> None:
        self.written = []

    def write(self, character, destination: Path) -> None:
        self.written.append((character, destination))


def test_save_stores_the_character_and_renders_its_sheet(tmp_path):
    writer = RecordingSheetWriter()
    service = CharacterService(
        JsonCharacterRepository(tmp_path / "data"), writer, tmp_path / "pdf"
    )
    character = fighter(name="Thorin Oakenshield")

    pdf = service.save(character)

    assert pdf == tmp_path / "pdf" / "thorin-oakenshield.pdf"
    assert writer.written == [(character, pdf)]
    assert service.saved() == [character]
    assert service.exists(character)
