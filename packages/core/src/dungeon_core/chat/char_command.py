from collections.abc import Callable

from dungeon_core.agents.character_builder.agent import (
    Agent,
    AgentUnavailableError,
)
from dungeon_core.characters.character import Character
from dungeon_core.characters.service import CharacterService
from dungeon_core.chat.command import Reply


class CharCommand:
    """/char: Character creation.

    The conversation moves through up to three steps, each answered
    by the next message: picking a saved Character to edit (only if
    there are any), talking to the agent, and confirming the save.
    The agent factory gets the Character to edit, or None for a new
    one.
    """

    name = "/char"
    description = "Create a Character"

    def __init__(
        self,
        agent_factory: Callable[[Character | None], Agent],
        store: CharacterService,
    ) -> None:
        self._agent_factory = agent_factory
        self._store = store
        self._reset()

    def _reset(self) -> None:
        self._picking: list[Character] | None = None
        self._agent: Agent | None = None
        self._finished: Character | None = None
        self._talked = False
        self._editing: str | None = None

    def start(self) -> Reply:
        saved = self._store.saved()
        if not saved:
            return self._begin(None)
        self._picking = saved
        lines = [f"{n}. {c.name}" for n, c in enumerate(saved, 1)]
        return Reply(
            "\n".join(
                [
                    "Saved Characters:",
                    "",
                    *lines,
                    "",
                    "Pick a number to edit one, or press Enter to "
                    "start a new Character.",
                ]
            ),
            active=True,
        )

    def handle(self, text: str) -> Reply:
        if self._picking is not None:
            return self._pick(text.strip())
        if self._finished is not None:
            return self._confirm(text)
        return self._talk(text)

    def leave(self) -> Reply:
        if self._finished is not None:
            text = "Not saved."
        elif self._talked:
            text = "Unfinished Character discarded."
        else:
            text = ""
        self._reset()
        return Reply(text)

    def _pick(self, pick: str) -> Reply:
        saved = self._picking
        self._reset()
        if not pick:
            return self._begin(None)
        if not (pick.isdigit() and 1 <= int(pick) <= len(saved)):
            return Reply(f"Not a choice: {pick}")
        return self._begin(saved[int(pick) - 1])

    def _begin(self, draft: Character | None) -> Reply:
        try:
            self._agent = self._agent_factory(draft)
        except AgentUnavailableError as error:
            return Reply(str(error))
        self._editing = draft.name if draft else None
        return Reply("Character creation. Type /exit to leave.", active=True)

    def _talk(self, text: str) -> Reply:
        self._talked = True
        try:
            reply = self._agent.reply(text)
        except AgentUnavailableError as error:
            self._reset()
            return Reply(str(error))
        if reply.finished is None:
            return Reply(reply.text, active=True)
        character = reply.finished
        self._agent = None
        self._finished = character
        if self._store.exists(character) and character.name != self._editing:
            question = f"{character.name} already exists. Overwrite? [y/N]"
        else:
            question = f"Save {character.name}? [y/N]"
        return Reply(f"{reply.text}\n\n{question}", active=True)

    def _confirm(self, answer: str) -> Reply:
        character = self._finished
        self._reset()
        if answer.strip().lower() not in ("y", "yes"):
            return Reply("Not saved.")
        pdf = self._store.save(character)
        return Reply(f"Saved {character.name}: `{pdf}`")
