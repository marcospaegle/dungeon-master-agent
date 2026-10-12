from collections.abc import Callable
from dataclasses import dataclass

from dungeon_core.agents.agent import Agent


@dataclass(frozen=True)
class AgentCommand:
    """A Command that only starts an Agent.

    ``intro`` is what the user is told when it starts. ``start`` may
    raise ``AgentUnavailableError`` when the Agent cannot run.
    """

    name: str
    description: str
    intro: str
    start: Callable[[], Agent]
