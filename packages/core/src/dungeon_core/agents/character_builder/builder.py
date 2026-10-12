from dungeon_core.agents.agent import AgentReply
from dungeon_core.agents.session import AgentSession
from dungeon_core.characters.draft import CharacterDraft
from dungeon_core.tools.return_tool import ReturnTool


class CharacterBuilder:
    """The Agent that guides the user through Character creation.

    The conversation is finished once the Character is saved, or when
    the user asks for something else and the Builder gives the
    conversation back to the Concierge.
    """

    def __init__(
        self,
        session: AgentSession,
        draft: CharacterDraft,
        returning: ReturnTool,
    ) -> None:
        self._session = session
        self._draft = draft
        self._returning = returning
        self._talked = False

    def send(self, text: str) -> AgentReply:
        self._talked = True
        # Drop an outcome left behind by a turn that failed.
        self._returning.take()
        reply = self._session.send(text)
        outcome = self._returning.take()
        if outcome:
            return reply._replace(finished=True, outcome=outcome, reroute=True)
        if reply.finished:
            return reply._replace(outcome=f"Saved {self._draft.build().name}.")
        return reply

    def leave(self) -> str:
        if self._session.asked:
            return "Not saved."
        if self._talked and not self._draft.saved:
            return "Unfinished Character discarded."
        return ""
