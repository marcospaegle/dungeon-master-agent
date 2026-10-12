from collections.abc import Callable

from dungeon.core.character import Character
from dungeon.core.character_store import CharacterStore
from dungeon.core.ports.agent import Agent, AgentUnavailableError

HINT = "Type /help to list the Commands."


class Chat:
    """A Chat: reads lines until a Command ends it.

    Input and output are injected so the Chat can be driven without a
    terminal. The read callable raises EOFError when input runs out.

    /char needs an agent factory, which gets the saved Character to
    edit (or None for a new one), and a Character store; without them
    it says Character creation is unavailable.

    The agent's replies go to ``write_reply`` (Markdown), which
    defaults to ``write``.
    """

    def __init__(
        self,
        read: Callable[[], str],
        write: Callable[[str], None],
        agent_factory: Callable[[Character | None], Agent] | None = None,
        store: CharacterStore | None = None,
        write_reply: Callable[[str], None] | None = None,
    ) -> None:
        self._read = read
        self._write = write
        self._write_reply = write_reply or write
        self._agent_factory = agent_factory
        self._store = store
        self._agent: Agent | None = None
        self._talked = False
        self._editing: str | None = None
        self._running = False
        self._commands = {
            "/help": ("List the Commands", self._help),
            "/char": ("Create a Character", self._char),
            "/exit": ("Leave Character creation", self._exit),
            "/quit": ("End the Chat", self._quit),
        }

    def run(self) -> None:
        self._running = True
        while self._running:
            try:
                line = self._read().strip()
            except EOFError:
                return
            self._handle(line)

    def _handle(self, line: str) -> None:
        if not line:
            return
        if not line.startswith("/"):
            if self._agent is None:
                self._write(HINT)
            else:
                self._talk(line)
            return
        name = line.split()[0]
        if name not in self._commands:
            self._write(f"Unknown Command: {name}\n{HINT}")
            return
        _, handler = self._commands[name]
        handler()

    def _help(self) -> None:
        lines = [
            f"  {name}  {text}" for name, (text, _) in self._commands.items()
        ]
        self._write("\n".join(["Commands:", *lines]))

    def _quit(self) -> None:
        self._running = False

    def _char(self) -> None:
        if self._agent_factory is None or self._store is None:
            self._write("Character creation is not available yet.")
        elif self._agent is not None:
            self._write("Already creating a Character. /exit leaves.")
        else:
            self._start_creation()

    def _start_creation(self) -> None:
        draft = None
        saved = self._store.saved()
        if saved:
            lines = [f"  {n}. {c.name}" for n, c in enumerate(saved, 1)]
            self._write(
                "\n".join(
                    [
                        "Saved Characters:",
                        *lines,
                        "Pick a number to edit one, or press Enter to "
                        "start a new Character.",
                    ]
                )
            )
            pick = self._read().strip()
            if pick:
                if not (pick.isdigit() and 1 <= int(pick) <= len(saved)):
                    self._write(f"Not a choice: {pick}")
                    return
                draft = saved[int(pick) - 1]
        try:
            self._agent = self._agent_factory(draft)
        except AgentUnavailableError as error:
            self._write(str(error))
            return
        self._talked = False
        self._editing = draft.name if draft else None
        self._write("Character creation. Type /exit to leave.")

    def _exit(self) -> None:
        if self._agent is None:
            self._write("Not in Character creation.")
            return
        if self._talked:
            self._write("Unfinished Character discarded.")
        self._agent = None

    def _talk(self, text: str) -> None:
        self._talked = True
        try:
            reply = self._agent.reply(text)
        except AgentUnavailableError as error:
            self._agent = None
            self._write(str(error))
            return
        self._write_reply(reply.text)
        if reply.finished is None:
            return
        character = reply.finished
        self._agent = None
        if self._store.exists(character) and character.name != self._editing:
            question = f"{character.name} already exists. Overwrite? [y/N]"
        else:
            question = f"Save {character.name}? [y/N]"
        if self._confirm(question):
            pdf = self._store.save(character)
            self._write(f"Saved {character.name}: {pdf}")
        else:
            self._write("Not saved.")

    def _confirm(self, question: str) -> bool:
        self._write(question)
        try:
            return self._read().strip().lower() in ("y", "yes")
        except EOFError:
            return False
