import pytest
from characters import fighter
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, ToolMessage

from dungeon_core.adapters.langchain_agent import LangchainAgent
from dungeon_core.character import Ability
from dungeon_core.character_json import character_to_dict
from dungeon_core.ports.agent import AgentUnavailableError
from dungeon_core.ports.retriever import IndexNotBuiltError


def call(name: str, **args) -> AIMessage:
    return AIMessage(
        content="",
        tool_calls=[{"name": name, "args": args, "id": f"id-{name}"}],
    )


class ScriptedModel:
    """Stands in for a chat model: replies in order, records calls."""

    def __init__(self, *replies: AIMessage) -> None:
        self._replies = iter(replies)
        self.tool_names: list[str] = []
        self.seen: list[list] = []

    def bind_tools(self, tools):
        self.tool_names = [tool.name for tool in tools]
        return self

    def invoke(self, messages):
        self.seen.append(list(messages))
        return next(self._replies)

    def tool_results(self) -> list[str]:
        return [
            message.content
            for message in self.seen[-1]
            if isinstance(message, ToolMessage)
        ]


class FakeRetriever:
    def __init__(self, hits=(), error=None) -> None:
        self._hits = list(hits)
        self._error = error

    def check(self) -> None:
        pass

    def search(self, query: str, k: int):
        if self._error:
            raise self._error
        return self._hits


def agent(model, retriever=None, draft=None) -> LangchainAgent:
    return LangchainAgent(model, retriever or FakeRetriever(), draft)


def test_the_agent_has_the_character_tools_search_and_finish_only():
    model = ScriptedModel(AIMessage("Hello"))

    agent(model).reply("hi")

    assert sorted(model.tool_names) == [
        "finish",
        "get_character",
        "search_rules",
        "set_fields",
    ]


def test_a_plain_answer_is_the_reply():
    reply = agent(ScriptedModel(AIMessage("Pick a class."))).reply("hi")

    assert reply.text == "Pick a class."
    assert reply.finished is None


def test_finish_returns_the_character_the_fields_describe():
    model = ScriptedModel(
        call("set_fields", fields=character_to_dict(fighter())),
        call("finish"),
        AIMessage("All done."),
    )

    reply = agent(model).reply("that is all")

    assert reply.text == "All done."
    assert reply.finished == fighter()


def test_finish_refuses_an_incomplete_character():
    model = ScriptedModel(
        call("set_fields", fields={"name": "Brannoch"}),
        call("finish"),
        AIMessage("Which class?"),
    )

    reply = agent(model).reply("done")

    assert reply.finished is None
    assert "character_class" in model.tool_results()[-1]


def test_an_illegal_choice_is_pushed_back_to_the_model():
    illegal = character_to_dict(fighter()) | {
        "base_scores": {a.value: 18 for a in Ability}
    }
    model = ScriptedModel(
        call("set_fields", fields=illegal), AIMessage("That is illegal.")
    )

    agent(model).reply("all 18s")

    assert "standard array" in model.tool_results()[-1]


def test_a_legal_character_reports_the_numbers_code_derived():
    model = ScriptedModel(
        call("set_fields", fields=character_to_dict(fighter())),
        AIMessage("ok"),
    )

    agent(model).reply("go")

    assert '"armor_class": 12' in model.tool_results()[-1]
    assert '"hit_points": 12' in model.tool_results()[-1]


def test_a_draft_starts_the_agent_from_a_saved_character():
    model = ScriptedModel(call("get_character"), AIMessage("ok"))

    agent(model, draft=fighter()).reply("change my name")

    assert "Brannoch" in model.tool_results()[-1]


def test_search_results_carry_their_source_and_page():
    hit = Document(
        page_content="Fighters wear any armor.",
        metadata={"source": "phb.pdf", "page": 94},
    )
    model = ScriptedModel(
        call("search_rules", query="fighter armor"), AIMessage("ok")
    )

    agent(model, FakeRetriever([hit])).reply("armor?")

    result = model.tool_results()[-1]
    assert "phb.pdf" in result
    assert "94" in result
    assert "Fighters wear any armor." in result


def test_a_missing_index_makes_the_agent_unavailable():
    model = ScriptedModel(call("search_rules", query="x"))
    retriever = FakeRetriever(error=IndexNotBuiltError("Run `dungeon build`"))

    with pytest.raises(AgentUnavailableError, match="dungeon build"):
        agent(model, retriever).reply("armor?")


def test_the_conversation_carries_over_between_replies():
    model = ScriptedModel(AIMessage("one"), AIMessage("two"))
    talker = agent(model)

    talker.reply("first")
    talker.reply("second")

    texts = [getattr(m, "content", "") for m in model.seen[-1]]
    assert "first" in texts
    assert "one" in texts


def test_a_model_that_never_stops_calling_tools_is_cut_off():
    model = ScriptedModel(*[call("get_character")] * 50)

    with pytest.raises(AgentUnavailableError, match="tool"):
        agent(model).reply("loop")


def test_an_unknown_field_is_refused_without_changing_anything():
    model = ScriptedModel(
        call("set_fields", fields={"hit_points": 99}), AIMessage("ok")
    )

    agent(model).reply("give me 99 hp")

    assert "Unknown fields" in model.tool_results()[-1]
