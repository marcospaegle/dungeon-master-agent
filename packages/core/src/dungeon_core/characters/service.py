from pathlib import Path

from dungeon_core.characters.character import Character
from dungeon_core.characters.ports.repository import CharacterRepository
from dungeon_core.characters.ports.sheet_writer import SheetWriter


class CharacterService:
    """Saves Characters, each with its Character sheet PDF.

    The sheet is rendered from the Character as read back from the
    repository, so what is saved is the single source for the sheet.
    """

    def __init__(
        self,
        repository: CharacterRepository,
        sheet_writer: SheetWriter,
        sheets: Path,
    ) -> None:
        self._repository = repository
        self._sheet_writer = sheet_writer
        self._sheets = sheets

    def saved(self) -> list[Character]:
        return self._repository.saved()

    def exists(self, character: Character) -> bool:
        return self._repository.exists(character)

    def save(self, character: Character) -> Path:
        """Save the Character and its sheet; return the PDF's path."""
        stored = self._repository.save(character)
        self._sheets.mkdir(parents=True, exist_ok=True)
        pdf = self._sheets / f"{stored.slug}.pdf"
        self._sheet_writer.write(stored, pdf)
        return pdf
