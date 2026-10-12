from collections.abc import Sequence
from typing import NamedTuple

from dungeon_core.agents.agent import Agent, AgentUnavailableError
from dungeon_core.chat.command import AgentCommand

HINT = "Type /help to list the Commands."


class Reply(NamedTuple):
    """What the Chat says back, as Markdown; empty says nothing."""

    text: str
    active: bool = False


class Chat:
    """One conversation, whatever the Frontend that shows it.

    It takes what the user types and returns a Reply. A Command starts
    an Agent; until that Agent finishes or the user leaves with /exit,
    text that is not a Command goes to it. The Chat owns /help, /exit
    and /quit; everything else is a Command. A Frontend keeps one Chat
    per conversation.
    """

    def __init__(self, commands: Sequence[AgentCommand] = ()) -> None:
        self._commands = {command.name: command for command in commands}
        self._active: AgentCommand | None = None
        self._agent: Agent | None = None
        self._ended = False
        self._builtins = {
            "/help": ("List the Commands", self._help),
            "/exit": ("Leave the active Command", self._exit),
            "/quit": ("End the Chat", self._quit),
        }

    @property
    def ended(self) -> bool:
        """Whether the user ended the Chat with /quit."""
        return self._ended

    def send(self, text: str) -> Reply:
        text = text.strip()
        if not text:
            return Reply("", active=self._agent is not None)
        if not text.startswith("/"):
            if self._agent is not None:
                return self._turn(text)
            return Reply(HINT)

        name = text.split()[0]
        if name in self._builtins:
            return self._builtins[name][1]()
        if name not in self._commands:
            return Reply(f"Unknown Command: {name}\n\n{HINT}")
        if self._active is not None:
            return Reply(f"Already in {self._active.name}. /exit leaves.")
        return self._start(self._commands[name])

    def _start(self, command: AgentCommand) -> Reply:
        try:
            self._agent = command.start()
        except AgentUnavailableError as error:
            return Reply(str(error))
        self._active = command
        return Reply(command.intro, active=True)

    def _turn(self, text: str) -> Reply:
        try:
            reply = self._agent.send(text)
        except AgentUnavailableError as error:
            self._finish()
            return Reply(str(error))
        if reply.finished:
            self._finish()
        return Reply(reply.text, active=not reply.finished)

    def _finish(self) -> None:
        self._active = self._agent = None

    def _help(self) -> Reply:
        described = [
            (name, text) for name, (text, _) in self._builtins.items()
        ] + [(c.name, c.description) for c in self._commands.values()]
        lines = [f"- `{name}` {text}" for name, text in described]
        return Reply("\n".join(["Commands:", "", *lines]))

    def _exit(self) -> Reply:
        if self._agent is None:
            return Reply("Not in a Command.")
        agent = self._agent
        self._finish()
        return Reply(agent.leave())

    def _quit(self) -> Reply:
        self._ended = True
        return Reply("")
