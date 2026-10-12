from collections.abc import Callable
from typing import Any
from uuid import uuid4

from langgraph.errors import GraphRecursionError
from langgraph.types import Command

from dungeon_core.agents.agent import AgentReply, AgentUnavailableError

YES = ("y", "yes")


class AgentSession:
    """One conversation with a Deep Agents graph.

    The graph's checkpointer keeps the history under this session's
    thread. When a Tool pauses the graph to ask the user something,
    the question is the reply and the next message answers it.
    ``done`` says when the Agent's task is complete.
    """

    def __init__(
        self,
        graph: Any,
        done: Callable[[], bool] = lambda: False,
    ) -> None:
        self._graph = graph
        self._done = done
        self._config = {"configurable": {"thread_id": str(uuid4())}}
        self._asked = False

    @property
    def asked(self) -> bool:
        """Whether a question is waiting for the user's answer."""
        return self._asked

    def send(self, text: str) -> AgentReply:
        if self._asked:
            message = Command(resume=text.strip().lower() in YES)
        else:
            message = {"messages": [{"role": "user", "content": text}]}
        try:
            result = self._graph.invoke(message, self._config)
        except GraphRecursionError as error:
            raise AgentUnavailableError(
                "The agent kept calling tools without answering; try again."
            ) from error
        answer = result["messages"][-1].text
        interrupts = result.get("__interrupt__")
        self._asked = bool(interrupts)
        if interrupts:
            return AgentReply(
                "\n\n".join(filter(None, [answer, interrupts[0].value]))
            )
        return AgentReply(answer, finished=self._done())
