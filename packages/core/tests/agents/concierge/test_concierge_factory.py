from pathlib import Path

import pytest
from fakes import ScriptedChatModel, call, say
from langchain_core.documents import Document
from langgraph.checkpoint.memory import InMemorySaver

from dungeon_core.agents.agent import AgentUnavailableError, Handoff
from dungeon_core.agents.concierge.factory import ConciergeFactory
from dungeon_core.chat.specialist import Specialist
from dungeon_core.config.settings import MissingSettingError
from dungeon_core.knowledge.ports.retriever import IndexNotBuiltError

BUILDER = Specialist(
    "character-builder", "Create or edit a Character", lambda: None
)


class FakeModels:
    def __init__(self, model=None, error=None) -> None:
        self._model = model
        self._error = error

    def create(self):
        if self._error:
            raise self._error
        return self._model


class FakeRetriever:
    def __init__(self, hits=(), error=None) -> None:
        self._hits = list(hits)
        self._error = error

    def search(self, query: str, k: int):
        if self._error:
            raise self._error
        return self._hits


class FakeKnowledge:
    def __init__(self, retriever=None, error=None) -> None:
        self._retriever = retriever or FakeRetriever()
        self._error = error

    def retriever(self, store):
        if self._error:
            raise self._error
        return self._retriever


def factory(model=None, models=None, specialists=(BUILDER,), knowledge=None):
    return ConciergeFactory(
        models or FakeModels(model),
        specialists,
        knowledge or FakeKnowledge(),
        Path("chroma"),
        InMemorySaver(),
    )


def test_a_hand_off_call_becomes_a_handoff_on_the_reply():
    model = ScriptedChatModel(
        replies=[
            call(
                "hand_off",
                specialist="character-builder",
                brief="a half-orc barbarian",
            ),
            say("On it."),
        ]
    )

    reply = factory(model).create().send("help me create a new char")

    assert reply.handoff == Handoff(
        "character-builder", "a half-orc barbarian"
    )


def test_an_unknown_specialist_gives_no_handoff_and_tells_the_model():
    model = ScriptedChatModel(
        replies=[call("hand_off", specialist="bard", brief="x"), say("Hm.")]
    )

    reply = factory(model).create().send("sing")

    assert reply.handoff is None
    assert "No Specialist named 'bard'" in model.seen_messages[-1].content


def test_a_handoff_is_given_once():
    model = ScriptedChatModel(
        replies=[
            call("hand_off", specialist="character-builder", brief="x"),
            say("On it."),
            say("Anything else?"),
        ]
    )
    concierge = factory(model).create()
    concierge.send("make a character")

    assert concierge.send("thanks").handoff is None


def test_only_hand_off_and_search_rules_reach_the_model():
    model = ScriptedChatModel(replies=[say("Hello.")])

    factory(model).create().send("hi")

    assert sorted(model.tool_names) == ["hand_off", "search_rules"]


def test_a_rules_question_is_answered_from_the_sources():
    hit = Document(
        page_content="A Fighter wears any armor.",
        metadata={"source": "phb.pdf", "page": 94},
    )
    model = ScriptedChatModel(
        replies=[
            call("search_rules", query="fighter armor"),
            say("Any armor."),
        ]
    )
    knowledge = FakeKnowledge(FakeRetriever([hit]))

    reply = factory(model, knowledge=knowledge).create().send("armor?")

    assert reply.text == "Any armor."
    assert "[phb.pdf, page 94]" in model.seen_messages[-1].content


def test_a_missing_index_is_told_to_the_model_not_raised():
    model = ScriptedChatModel(
        replies=[call("search_rules", query="x"), say("Build it.")]
    )
    knowledge = FakeKnowledge(
        FakeRetriever(error=IndexNotBuiltError("Build the index first."))
    )

    factory(model, knowledge=knowledge).create().send("armor?")

    assert "Build the index first." in model.seen_messages[-1].content


def test_a_missing_key_makes_the_concierge_unavailable():
    knowledge = FakeKnowledge(error=MissingSettingError("Set the key."))
    concierge = factory(knowledge=knowledge).create()

    with pytest.raises(AgentUnavailableError, match="Set the key."):
        concierge.send("hi")


def test_the_prompt_limits_the_concierge_to_dnd_5_5e_questions():
    model = ScriptedChatModel(replies=[say("Hello.")])

    factory(model).create().send("hi")

    system = model.seen_messages[0].content
    assert "search_rules" in system
    assert "Decline" in system


def test_the_prompt_lists_the_specialists_with_what_they_do():
    model = ScriptedChatModel(replies=[say("Hello.")])

    factory(model).create().send("hi")

    system = model.seen_messages[0].content
    assert "character-builder: Create or edit a Character" in system


def test_nothing_is_read_until_the_first_message():
    models = FakeModels(error=AgentUnavailableError("Set the key."))
    concierge = factory(models=models).create()

    with pytest.raises(AgentUnavailableError, match="Set the key."):
        concierge.send("hi")


def test_a_handoff_from_a_failed_turn_does_not_leak_into_the_next():
    # The scripted model runs out after the call, so the turn fails.
    model = ScriptedChatModel(
        replies=[call("hand_off", specialist="character-builder", brief="x")]
    )
    concierge = factory(model).create()
    with pytest.raises(IndexError):
        concierge.send("make a character")
    model.replies.append(say("Hello."))

    assert concierge.send("hi").handoff is None


def test_a_note_is_heard_before_the_next_message_and_only_once():
    model = ScriptedChatModel(replies=[say("Nice."), say("Sure.")])
    concierge = factory(model).create()
    concierge.note("Saved Mira.")

    concierge.send("thanks")
    first = model.seen_messages[-1].content
    concierge.send("what else?")
    second = model.seen_messages[-1].content

    assert "Saved Mira." in first
    assert first.endswith("thanks")
    assert "Saved Mira." not in second


def test_the_prompt_says_notes_come_from_the_program():
    model = ScriptedChatModel(replies=[say("Hello.")])

    factory(model).create().send("hi")

    assert "(Note:" in model.seen_messages[0].content


def test_a_note_survives_a_failed_turn():
    model = ScriptedChatModel(replies=[])
    concierge = factory(model).create()
    concierge.note("Saved Mira.")
    with pytest.raises(IndexError):
        concierge.send("thanks")
    model.replies.append(say("Nice."))

    concierge.send("thanks again")

    assert "Saved Mira." in model.seen_messages[-1].content
