from collections.abc import Sequence
from typing import NamedTuple

from dungeon_core.agents.agent import (
    Agent,
    AgentReply,
    AgentUnavailableError,
    ConciergeAgent,
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
        self, concierge: ConciergeAgent, specialists: Sequence[Specialist] = ()
    ) -> None:
        self._concierge = concierge
        self._specialists = {item.name: item for item in specialists}
        self._handed_to: Agent | None = None
        self._handed_name = ""
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
            return Reply("", active=self._handed_to is not None)
        if not text.startswith("/"):
            return self._turn(text)

        name = text.split()[0]
        if name in self._builtins:
            return self._builtins[name][1]()
        return Reply(f"Unknown Command: {name}\n\n{HINT}")

    @property
    def _active_agent(self) -> Agent:
        return self._handed_to or self._concierge

    def _turn(self, text: str) -> Reply:
        try:
            reply = self._active_agent.send(text)
            if reply.handoff is not None and self._handed_to is None:
                return self._hand_off(reply.handoff, text)
        except AgentUnavailableError as error:
            if self._handed_to is not None:
                self._concierge.note(f"{self._handed_name} stopped: {error}")
            self._leave()
            return Reply(str(error))
        return self._answer(reply, text)

    def _answer(self, reply: AgentReply, replay: str | None = None) -> Reply:
        """Show a reply; ``replay`` is what a reroute sends back."""
        if reply.finished:
            self._leave()
            if reply.outcome:
                self._concierge.note(reply.outcome)
            if reply.reroute and replay is not None:
                return self._turn(replay)
        return Reply(reply.text, active=self._handed_to is not None)

    def _hand_off(self, handoff: Handoff, text: str) -> Reply:
        specialist = self._specialists.get(handoff.specialist)
        if specialist is None:
            return Reply(f"Unknown Specialist: {handoff.specialist}")
        try:
            self._handed_to = specialist.start()
        except AgentUnavailableError as error:
            self._concierge.note(f"{specialist.name} could not start: {error}")
            return Reply(str(error))
        self._handed_name = specialist.name
        reply = self._handed_to.send(f"{text}\n\n{handoff.brief}")
        return self._answer(reply)

    def _help(self) -> Reply:
        lines = [
            f"- `{name}` {text}" for name, (text, _) in self._builtins.items()
        ]
        return Reply("\n".join(["Commands:", "", *lines]))

    def _exit(self) -> Reply:
        if self._handed_to is None:
            return Reply("Nothing to leave.")
        specialist = self._handed_to
        self._leave()
        self._concierge.note("The user left without finishing.")
        return Reply(specialist.leave())

    def _leave(self) -> None:
        self._handed_to = None

    def _quit(self) -> Reply:
        self._ended = True
        return Reply("")
