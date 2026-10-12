from collections.abc import Sequence
from typing import NamedTuple

from dungeon_core.agents.agent import (
    Agent,
    AgentReply,
    AgentUnavailableError,
    Handoff,
)
from dungeon_core.chat.specialist import Specialist

HINT = "Type /help to list the Commands."


class Reply(NamedTuple):
    """What the Chat says back, as Markdown; empty says nothing."""

    text: str
    active: bool = False


class Chat:
    """One conversation, whatever the Frontend that shows it.

    It takes what the user types and returns a Reply. Text that is not
    a Command goes to the Active Agent: the Concierge, or a Specialist
    after the Concierge hands the conversation to it. A Specialist has
    it until it finishes or the user leaves with /exit. The Chat owns
    /help, /exit and /quit. A Frontend keeps one Chat per conversation.
    """

    def __init__(
        self, concierge: Agent, specialists: Sequence[Specialist] = ()
    ) -> None:
        self._concierge = concierge
        self._specialists = {s.name: s for s in specialists}
        self._specialist: Agent | None = None
        self._ended = False
        self._builtins = {
            "/help": ("List the Commands", self._help),
            "/exit": ("Leave the Specialist", self._exit),
            "/quit": ("End the Chat", self._quit),
        }

    @property
    def ended(self) -> bool:
        """Whether the user ended the Chat with /quit."""
        return self._ended

    def send(self, text: str) -> Reply:
        text = text.strip()
        if not text:
            return Reply("", active=self._specialist is not None)
        if not text.startswith("/"):
            return self._turn(text)

        name = text.split()[0]
        if name in self._builtins:
            return self._builtins[name][1]()
        return Reply(f"Unknown Command: {name}\n\n{HINT}")

    @property
    def _agent(self) -> Agent:
        return self._specialist or self._concierge

    def _turn(self, text: str) -> Reply:
        try:
            reply = self._agent.send(text)
            if reply.handoff is not None:
                return self._hand_off(reply.handoff, text)
        except AgentUnavailableError as error:
            self._specialist = None
            return Reply(str(error))
        return self._answer(reply)

    def _answer(self, reply: AgentReply) -> Reply:
        if reply.finished:
            self._specialist = None
        return Reply(reply.text, active=self._specialist is not None)

    def _hand_off(self, handoff: Handoff, text: str) -> Reply:
        specialist = self._specialists.get(handoff.specialist)
        if specialist is None:
            return Reply(f"Unknown Specialist: {handoff.specialist}")
        self._specialist = specialist.start()
        reply = self._specialist.send(f"{text}\n\n{handoff.brief}")
        return self._answer(reply)

    def _help(self) -> Reply:
        lines = [
            f"- `{name}` {text}" for name, (text, _) in self._builtins.items()
        ]
        return Reply("\n".join(["Commands:", "", *lines]))

    def _exit(self) -> Reply:
        if self._specialist is None:
            return Reply("Nothing to leave.")
        specialist = self._specialist
        self._specialist = None
        return Reply(specialist.leave())

    def _quit(self) -> Reply:
        self._ended = True
        return Reply("")
