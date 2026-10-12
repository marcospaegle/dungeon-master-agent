from typing import NamedTuple, Protocol

from dungeon_core.characters.character import Character


class AgentUnavailableError(Exception):
    """The agent cannot run; the message says what the user must fix."""


class AgentReply(NamedTuple):
    """What the agent says back.

    The Character is set only when the agent calls it finished; the
    user still has to confirm it before anything is saved.
    """

    text: str
    finished: Character | None = None


class Agent(Protocol):
    """Guides the user through one Character creation."""

    def reply(self, text: str) -> AgentReply: ...
