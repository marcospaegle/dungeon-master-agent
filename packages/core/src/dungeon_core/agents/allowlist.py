from collections.abc import Awaitable, Callable, Collection
from typing import Any

from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import ToolMessage


def _name(tool: Any) -> str:
    return tool["name"] if isinstance(tool, dict) else tool.name


class ToolAllowlistMiddleware(AgentMiddleware):
    """Limits an Agent to the Tools it is given.

    Deep Agents adds filesystem, shell and sub-agent tools to every
    agent. An Agent here does one task, so only the named tools reach
    the model, and a call to any other is refused. Place it last in
    the middleware list, after whatever injects tools.
    """

    def __init__(self, allowed: Collection[str]) -> None:
        self._allowed = frozenset(allowed)

    def wrap_model_call(self, request, handler):
        return handler(self._restrict(request))

    async def awrap_model_call(self, request, handler):
        return await handler(self._restrict(request))

    def wrap_tool_call(self, request, handler):
        return self._refusal(request) or handler(request)

    async def awrap_tool_call(
        self,
        request,
        handler: Callable[..., Awaitable[Any]],
    ):
        return self._refusal(request) or await handler(request)

    def _restrict(self, request):
        return request.override(
            tools=[t for t in request.tools if _name(t) in self._allowed]
        )

    def _refusal(self, request) -> ToolMessage | None:
        name = request.tool_call["name"]
        if name in self._allowed:
            return None
        return ToolMessage(
            content=f"Error: {name} is not available.",
            tool_call_id=request.tool_call["id"] or "",
            name=name,
            status="error",
        )
