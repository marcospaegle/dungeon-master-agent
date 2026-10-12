import pytest
from fakes import ScriptedChatModel, call, say
from langgraph.checkpoint.memory import InMemorySaver

from dungeon_core.agents.agent import AgentUnavailableError, Handoff
from dungeon_core.agents.concierge.factory import ConciergeFactory
from dungeon_core.chat.specialist import Specialist

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


def factory(model=None, models=None, specialists=(BUILDER,)):
    return ConciergeFactory(
        models or FakeModels(model), specialists, InMemorySaver()
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


def test_only_hand_off_reaches_the_model():
    model = ScriptedChatModel(replies=[say("Hello.")])

    factory(model).create().send("hi")

    assert model.tool_names == ["hand_off"]


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
