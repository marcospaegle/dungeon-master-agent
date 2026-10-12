from deepagents import create_deep_agent
from fakes import ScriptedChatModel, call, say
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt

from dungeon_core.agents.allowlist import ToolAllowlistMiddleware
from dungeon_core.agents.session import AgentSession


@tool
def ask() -> str:
    """Ask the user to confirm."""
    return "confirmed" if interrupt("Sure? [y/N]") else "declined"


def session(model, done=lambda: False) -> AgentSession:
    graph = create_deep_agent(
        model=model,
        tools=[ask],
        middleware=[ToolAllowlistMiddleware(["ask"])],
        checkpointer=InMemorySaver(),
    )
    return AgentSession(graph, done)


def test_a_reply_without_tools_is_the_models_text():
    chat = session(ScriptedChatModel(replies=[say("Hello!")]))

    reply = chat.send("hi")

    assert reply.text == "Hello!"
    assert not reply.finished
    assert not chat.asked


def test_only_the_allowed_tools_reach_the_model():
    model = ScriptedChatModel(replies=[say("ok")])

    session(model).send("hi")

    assert model.tool_names == ["ask"]


def test_a_tool_question_is_the_reply_and_the_next_message_answers_it():
    model = ScriptedChatModel(
        replies=[call("ask"), say("Done, it was confirmed.")]
    )
    chat = session(model)

    asked = chat.send("go")
    answered = chat.send("Yes")

    assert asked.text == "Sure? [y/N]"
    assert chat.asked is False
    assert answered.text == "Done, it was confirmed."


def test_anything_but_yes_declines():
    model = ScriptedChatModel(replies=[call("ask"), say("Fine, declined.")])
    chat = session(model)

    chat.send("go")
    chat.send("nope")

    tool_results = [m.content for m in model.seen_messages if m.type == "tool"]
    assert tool_results == ["declined"]


def test_the_reply_is_finished_once_the_task_is_done():
    chat = session(ScriptedChatModel(replies=[say("Bye")]), lambda: True)

    assert chat.send("hi").finished
