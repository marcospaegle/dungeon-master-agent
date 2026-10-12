from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.utils.function_calling import convert_to_openai_tool
from pydantic import PrivateAttr


def say(text: str) -> AIMessage:
    return AIMessage(content=text)


def call(tool: str, /, **args) -> AIMessage:
    return AIMessage(
        content="",
        tool_calls=[{"name": tool, "args": args, "id": f"id-{tool}"}],
    )


class ScriptedChatModel(BaseChatModel):
    """A chat model that replies in order and records what it saw."""

    replies: list[AIMessage]
    _tool_names: list[str] = PrivateAttr(default_factory=list)
    _seen: list = PrivateAttr(default_factory=list)

    @property
    def tool_names(self) -> list[str]:
        return self._tool_names

    @property
    def seen_messages(self) -> list:
        """The messages of the latest call to the model."""
        return self._seen

    @property
    def _llm_type(self) -> str:
        return "scripted"

    def bind_tools(self, tools, **kwargs):
        self._tool_names = [
            convert_to_openai_tool(tool)["function"]["name"] for tool in tools
        ]
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        self._seen = list(messages)
        return ChatResult(
            generations=[ChatGeneration(message=self.replies.pop(0))]
        )
