from langchain_core.tools import BaseTool, StructuredTool


class ReturnTool:
    """Lets a Specialist give the conversation back to the Concierge.

    It records the outcome, which the Specialist puts on its reply for
    the Chat to act on.
    """

    def __init__(self) -> None:
        self._outcome = ""

    def tools(self) -> list[BaseTool]:
        return [StructuredTool.from_function(self.return_to_concierge)]

    def take(self) -> str:
        """The outcome recorded since the last call, if any."""
        outcome, self._outcome = self._outcome, ""
        return outcome

    def return_to_concierge(self, outcome: str) -> str:
        """Give the conversation back to the Concierge.

        Use it when the user asks for something outside your task.
        ``outcome`` is one line on what happened and what the user
        wants now.
        """
        self._outcome = outcome
        return "Returning the conversation to the Concierge."
