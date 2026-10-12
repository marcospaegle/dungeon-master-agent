from typing import Protocol

from dungeon_core.characters.character import Character


class CharacterRepository(Protocol):
    """Keeps the saved Characters."""

    def saved(self) -> list[Character]:
        """The saved Characters, sorted by name."""
        ...

    def exists(self, character: Character) -> bool: ...

    def save(self, character: Character) -> Character:
        """Save a Character; return it as read back from storage.

        The stored form is the single source for the Character sheet,
        so the sheet is rendered from what this returns.
        """
        ...
