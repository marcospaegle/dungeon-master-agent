from typing import Any

from langchain_core.tools import BaseTool, StructuredTool
from langgraph.types import interrupt

from dungeon_core.characters.draft import (
    CharacterDraft,
    IncompleteCharacterError,
)
from dungeon_core.characters.service import CharacterService


class CharacterTools:
    """Lets an Agent work on a Character draft and save it.

    ``save_character`` pauses the Agent with a question for the user
    and only saves once the answer is yes, so the user always has the
    last word.
    """

    def __init__(
        self, draft: CharacterDraft, service: CharacterService
    ) -> None:
        self._draft = draft
        self._service = service

    def tools(self) -> list[BaseTool]:
        return [
            StructuredTool.from_function(function)
            for function in (
                self.set_fields,
                self.get_character,
                self.list_characters,
                self.load_character,
                self.save_character,
            )
        ]

    def set_fields(self, fields: dict[str, Any]) -> str:
        """Set or change fields of the character.

        Pass only the fields to change; the rest are kept. Returns the
        problem if the character is not legal yet, or the numbers
        derived by code if it is.
        """
        unknown = self._draft.update(fields)
        if unknown:
            return f"Unknown fields, nothing changed: {unknown}"
        return self._draft.describe()

    def get_character(self) -> str:
        """Show the character so far, with its derived numbers."""
        return self._draft.describe()

    def list_characters(self) -> str:
        """List the names of the saved characters."""
        names = [character.name for character in self._service.saved()]
        return "\n".join(names) if names else "No saved characters."

    def load_character(self, name: str) -> str:
        """Start editing a saved character, replacing the draft."""
        for character in self._service.saved():
            if character.name.casefold() == name.strip().casefold():
                self._draft.load(character)
                return self._draft.describe()
        return f"No saved character named {name!r}."

    def save_character(self) -> str:
        """Save the character and render its sheet.

        Call it only after the user agreed to the finished character
        in conversation. The user is then asked for a final yes.
        """
        try:
            character = self._draft.build()
        except IncompleteCharacterError as error:
            return f"Cannot save, the character is not legal: {error}"
        overwrites = (
            self._service.exists(character)
            and character.name != self._draft.editing
        )
        if overwrites:
            question = f"{character.name} already exists. Overwrite? [y/N]"
        else:
            question = f"Save {character.name}? [y/N]"
        if not interrupt(question):
            return "The user declined, nothing was saved."
        pdf = self._service.save(character)
        self._draft.mark_saved()
        return f"Saved {character.name}: `{pdf}`"
