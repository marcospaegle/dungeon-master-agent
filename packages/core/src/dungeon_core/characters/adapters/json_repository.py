import json
from pathlib import Path

from dungeon_core.characters.character import Character
from dungeon_core.characters.serializer import CharacterSerializer


class JsonCharacterRepository:
    """Keeps each Character as a JSON file in one folder."""

    def __init__(self, folder: Path) -> None:
        self._folder = folder

    def saved(self) -> list[Character]:
        """The saved Characters, sorted by name.

        A JSON file that is not a Character is skipped, so one stray
        file cannot lock the user out of the others.
        """
        characters = []
        for source in self._folder.glob("*.json"):
            try:
                characters.append(self._read(source))
            except ValueError, KeyError, TypeError, AttributeError:
                continue
        return sorted(characters, key=lambda c: c.name.casefold())

    def exists(self, character: Character) -> bool:
        return self._path(character).exists()

    def save(self, character: Character) -> Character:
        self._folder.mkdir(parents=True, exist_ok=True)
        source = self._path(character)
        source.write_text(
            json.dumps(CharacterSerializer.to_dict(character), indent=2) + "\n"
        )
        return self._read(source)

    def _path(self, character: Character) -> Path:
        return self._folder / f"{character.slug}.json"

    @staticmethod
    def _read(source: Path) -> Character:
        return CharacterSerializer.from_dict(json.loads(source.read_text()))
