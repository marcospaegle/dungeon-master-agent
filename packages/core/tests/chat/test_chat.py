import pytest

from dungeon_core.agents.agent import (
    AgentReply,
    AgentUnavailableError,
    Handoff,
)
from dungeon_core.chat.chat import HINT, Chat
from dungeon_core.chat.specialist import Specialist


class ScriptedAgent:
    """Replies in order; leave returns the given farewell."""

    def __init__(self, *replies: AgentReply, farewell: str = "") -> None:
        self._replies = iter(replies)
        self._farewell = farewell
        self.heard: list[str] = []

    def send(self, text: str) -> AgentReply:
        self.heard.append(text)
        reply = next(self._replies)
        if isinstance(reply, Exception):
            raise reply
        return reply

    def leave(self) -> str:
        return self._farewell


def hand_off(specialist: str, brief: str = "") -> AgentReply:
    return AgentReply("", handoff=Handoff(specialist, brief))


def chat_with(concierge=None, specialist=None, error=None) -> Chat:
    def start():
        if error:
            raise error
        return specialist

    return Chat(
        concierge or ScriptedAgent(),
        [Specialist("builder", "Create a Character", start)],
    )


def test_a_handoff_starts_the_specialist_which_answers_the_user():
    builder = ScriptedAgent(AgentReply("Which class?"))
    chat = chat_with(
        ScriptedAgent(hand_off("builder", "wants a half-orc barbarian")),
        builder,
    )

    reply = chat.send("help me create a new char")

    assert reply == ("Which class?", True)
    assert "help me create a new char" in builder.heard[0]
    assert "wants a half-orc barbarian" in builder.heard[0]


def test_later_text_goes_to_the_specialist_not_the_concierge():
    concierge = ScriptedAgent(hand_off("builder"))
    builder = ScriptedAgent(AgentReply("Which class?"), AgentReply("Nice."))
    chat = chat_with(concierge, builder)
    chat.send("make a character")

    reply = chat.send("a fighter")

    assert builder.heard[-1] == "a fighter"
    assert concierge.heard == ["make a character"]
    assert reply == ("Nice.", True)


def test_an_unknown_specialist_is_reported_and_the_concierge_stays():
    concierge = ScriptedAgent(hand_off("bard"), AgentReply("Hello."))
    chat = chat_with(concierge)

    reply = chat.send("sing me a song")

    assert "Unknown Specialist: bard" in reply.text
    assert reply.active is False
    assert chat.send("hi") == ("Hello.", False)


def test_a_finished_specialist_gives_the_chat_back_to_the_concierge():
    concierge = ScriptedAgent(hand_off("builder"), AgentReply("Welcome."))
    builder = ScriptedAgent(AgentReply("Saved.", finished=True))
    chat = chat_with(concierge, builder)

    assert chat.send("make a character") == ("Saved.", False)
    assert chat.send("thanks") == ("Welcome.", False)


def test_exit_leaves_the_specialist_and_tells_what_it_says():
    concierge = ScriptedAgent(hand_off("builder"), AgentReply("Welcome."))
    chat = chat_with(
        concierge, ScriptedAgent(AgentReply("Hi."), farewell="Discarded.")
    )
    chat.send("make a character")

    assert chat.send("/exit") == ("Discarded.", False)
    assert chat.send("hello") == ("Welcome.", False)


def test_exit_without_a_specialist_has_nothing_to_leave():
    assert chat_with().send("/exit").text == "Nothing to leave."


def test_a_specialist_that_cannot_start_is_told_and_concierge_stays():
    concierge = ScriptedAgent(hand_off("builder"), AgentReply("Hello."))
    chat = chat_with(concierge, error=AgentUnavailableError("Set the key."))

    assert chat.send("make a character") == ("Set the key.", False)
    assert chat.send("hi") == ("Hello.", False)


def test_a_specialist_that_becomes_unavailable_is_left():
    concierge = ScriptedAgent(hand_off("builder"), AgentReply("Hello."))
    builder = ScriptedAgent(
        AgentReply("Hi."), AgentUnavailableError("Too long.")
    )
    chat = chat_with(concierge, builder)
    chat.send("make a character")

    assert chat.send("a fighter") == ("Too long.", False)
    assert chat.send("hi") == ("Hello.", False)


def test_an_unavailable_concierge_is_told_to_the_user():
    chat = chat_with(ScriptedAgent(AgentUnavailableError("Set the key.")))

    assert chat.send("hi") == ("Set the key.", False)


def test_help_lists_only_the_builtins():
    reply = chat_with().send("/help")

    assert "`/help`" in reply.text
    assert "`/exit`" in reply.text
    assert "`/quit`" in reply.text
    assert "builder" not in reply.text


def test_a_specialist_name_is_not_a_command():
    reply = chat_with().send("/builder")

    assert "Unknown Command: /builder" in reply.text
    assert HINT in reply.text


def test_blank_lines_are_not_sent_to_any_agent():
    concierge = ScriptedAgent()

    assert chat_with(concierge).send("   ") == ("", False)
    assert concierge.heard == []


@pytest.mark.parametrize("line", ["/quit", "/quit now"])
def test_quit_ends_the_chat(line):
    chat = chat_with()

    assert not chat.ended
    chat.send(line)

    assert chat.ended


def test_only_the_concierge_can_hand_the_conversation_over():
    concierge = ScriptedAgent(hand_off("builder"))
    builder = ScriptedAgent(
        AgentReply("Which class?"),
        hand_off("builder"),
        AgentReply("A fighter, then."),
    )
    chat = chat_with(concierge, builder)
    chat.send("make a character")

    assert chat.send("hmm") == ("", True)
    assert chat.send("a fighter") == ("A fighter, then.", True)
    assert concierge.heard == ["make a character"]
