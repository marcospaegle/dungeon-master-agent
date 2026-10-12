from typing import NamedTuple, Protocol


class AgentUnavailableError(Exception):
    """The agent cannot run; the message says what the user must fix."""


class Handoff(NamedTuple):
    """A request to give the conversation to a Specialist.

    ``brief`` tells the Specialist what the user wants.
    """

    specialist: str
    brief: str


class AgentReply(NamedTuple):
    """What an Agent says back, as Markdown.

    ``finished`` says the Agent's task is done, so the conversation
    with it ends. ``handoff`` asks the Chat to start a Specialist.
    """

    text: str
    finished: bool = False
    handoff: Handoff | None = None


class Agent(Protocol):
    """A worker that does one task, one conversation at a time."""

    def send(self, text: str) -> AgentReply:
        """Take what the user said and answer it."""
        ...

    def leave(self) -> str:
        """Called when the user leaves; return what to tell them."""
        ...
