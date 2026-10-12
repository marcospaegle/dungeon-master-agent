from collections.abc import Collection

from langchain_core.tools import BaseTool, StructuredTool

from dungeon_core.agents.agent import Handoff


class HandoffTool:
    """Lets the Concierge ask for a Specialist to take over.

    It does not start anything: it records the request, which the
    Concierge puts on its reply and the Chat acts on.
    """

    def __init__(self, specialists: Collection[str]) -> None:
        self._specialists = sorted(specialists)
        self._requested: Handoff | None = None

    def tools(self) -> list[BaseTool]:
        return [StructuredTool.from_function(self.hand_off)]

    def take(self) -> Handoff | None:
        """The request made since the last call, if any."""
        requested, self._requested = self._requested, None
        return requested

    def hand_off(self, specialist: str, brief: str) -> str:
        """Hand the conversation to a Specialist.

        ``brief`` tells it what the user wants, in a sentence or two.
        """
        if specialist not in self._specialists:
            return (
                f"No Specialist named {specialist!r}; "
                f"known: {', '.join(self._specialists)}."
            )
        self._requested = Handoff(specialist, brief)
        return f"Handing the conversation to {specialist}."
