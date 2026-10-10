from collections.abc import Callable

from dungeon.core.character_store import CharacterStore
from dungeon.core.ports.agent import Agent

HINT = "Type /help to list the Commands."


class Chat:
    """A Chat: reads lines until a Command ends it.

    Input and output are injected so the Chat can be driven without a
    terminal. The read callable raises EOFError when input runs out.

    /char needs an agent factory and a Character store; without them
    it says Character creation is unavailable.
    """

    def __init__(
        self,
        read: Callable[[], str],
        write: Callable[[str], None],
        agent_factory: Callable[[], Agent] | None = None,
        store: CharacterStore | None = None,
    ) -> None:
        self._read = read
        self._write = write
        self._agent_factory = agent_factory
        self._store = store
        self._agent: Agent | None = None
        self._talked = False
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
            self._agent = self._agent_factory()
            self._talked = False
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
        reply = self._agent.reply(text)
        self._write(reply.text)
        if reply.finished is None:
            return
        character = reply.finished
        self._agent = None
        if self._confirm(f"Save {character.name}? [y/N]"):
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
