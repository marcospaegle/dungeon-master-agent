from collections.abc import Callable

from dungeon_core.agents.agent import AgentReply
from dungeon_core.agents.session import AgentSession
from dungeon_core.tools.handoff_tool import HandoffTool


class Concierge:
    """The Agent the user talks to by default.

    It builds its Agent on the first message, so a missing key only
    matters once someone talks to it. When it calls ``hand_off``, its
    reply carries the Handoff for the Chat to act on.
    """

    def __init__(
        self, build: Callable[[], AgentSession], handoff: HandoffTool
    ) -> None:
        self._build = build
        self._handoff = handoff
        self._session: AgentSession | None = None
        self._notes: list[str] = []

    def note(self, text: str) -> None:
        """Keep something to tell the Agent with the next message."""
        self._notes.append(text)

    def send(self, text: str) -> AgentReply:
        if self._session is None:
            self._session = self._build()
        # Drop a request left behind by a turn that failed.
        self._handoff.take()
        notes = [f"(Note: {note})" for note in self._notes]
        reply = self._session.send("\n".join([*notes, text]))
        self._notes.clear()
        return reply._replace(handoff=self._handoff.take())

    def leave(self) -> str:
        return ""
