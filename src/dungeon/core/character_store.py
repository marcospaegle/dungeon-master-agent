import json
import re
from pathlib import Path

from dungeon.core.character import Character
from dungeon.core.character_json import (
    character_from_dict,
    character_to_dict,
)
from dungeon.core.ports.sheet_writer import SheetWriter


def _slug(name: str) -> str:
    """The file name stem for a Character name."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "character"


class CharacterStore:
    """Saves Characters as JSON, each with its Character sheet PDF.

    The PDF is rendered from the JSON read back from disk, so the
    saved file is the single source for the sheet.
    """

    def __init__(self, folder: Path, sheet_writer: SheetWriter) -> None:
        self._folder = folder
        self._sheet_writer = sheet_writer

    def saved(self) -> list[Character]:
        """The saved Characters, sorted by name."""
        return sorted(
            (
                character_from_dict(json.loads(source.read_text()))
                for source in self._folder.glob("*.json")
            ),
            key=lambda character: character.name.casefold(),
        )

    def exists(self, character: Character) -> bool:
        return (self._folder / f"{_slug(character.name)}.json").exists()

    def save(self, character: Character) -> Path:
        """Write the JSON and the PDF; return the PDF's path."""
        self._folder.mkdir(parents=True, exist_ok=True)
        stem = _slug(character.name)
        source = self._folder / f"{stem}.json"
        source.write_text(
            json.dumps(character_to_dict(character), indent=2) + "\n"
        )
        pdf = self._folder / f"{stem}.pdf"
        self._sheet_writer.write(
            character_from_dict(json.loads(source.read_text())), pdf
        )
        return pdf
