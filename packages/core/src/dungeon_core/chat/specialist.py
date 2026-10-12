from collections.abc import Callable
from dataclasses import dataclass

from dungeon_core.agents.agent import Agent


@dataclass(frozen=True)
class Specialist:
    """An Agent the Concierge can hand the conversation to.

    ``description`` tells the Concierge what the Specialist is for.
    ``start`` may raise ``AgentUnavailableError`` when the Agent cannot
    run.
    """

    name: str
    description: str
    start: Callable[[], Agent]
