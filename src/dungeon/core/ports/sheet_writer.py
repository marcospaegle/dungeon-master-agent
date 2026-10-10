from pathlib import Path
from typing import Protocol

from dungeon.core.character import Character


class SheetTemplateError(Exception):
    """The Character sheet template is not what the writer expects."""


class SheetWriter(Protocol):
    """Writes a Character onto the Character sheet and saves it."""

    def write(self, character: Character, destination: Path) -> None: ...
