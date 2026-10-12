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

    def send(self, text: str) -> AgentReply:
        if self._session is None:
            self._session = self._build()
        # Drop a request left behind by a turn that failed.
        self._handoff.take()
        reply = self._session.send(text)
        return reply._replace(handoff=self._handoff.take())

    def leave(self) -> str:
        return ""
