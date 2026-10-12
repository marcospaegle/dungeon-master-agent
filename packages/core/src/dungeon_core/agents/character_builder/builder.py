from dungeon_core.agents.agent import AgentReply
from dungeon_core.agents.session import AgentSession
from dungeon_core.characters.draft import CharacterDraft


class CharacterBuilder:
    """The Agent that guides the user through Character creation.

    The conversation is finished once the Character is saved.
    """

    def __init__(self, session: AgentSession, draft: CharacterDraft) -> None:
        self._session = session
        self._draft = draft
        self._talked = False

    def send(self, text: str) -> AgentReply:
        self._talked = True
        return self._session.send(text)

    def leave(self) -> str:
        if self._session.asked:
            return "Not saved."
        if self._talked and not self._draft.saved:
            return "Unfinished Character discarded."
        return ""
