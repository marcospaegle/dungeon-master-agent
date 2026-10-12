import pytest

from dungeon_core.agents.agent import AgentReply, AgentUnavailableError
from dungeon_core.chat.chat import HINT, Chat
from dungeon_core.chat.command import AgentCommand


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


def chat_with(agent=None, error=None) -> Chat:
    def start():
        if error:
            raise error
        return agent

    return Chat(
        [AgentCommand("/char", "Create a Character", "Welcome.", start)]
    )


def test_help_lists_the_builtins_and_the_commands():
    reply = Chat([AgentCommand("/char", "Create", "Hi", lambda: None)]).send(
        "/help"
    )

    assert "`/help`" in reply.text
    assert "`/quit`" in reply.text
    assert "`/char` Create" in reply.text


def test_text_outside_a_command_gets_a_hint_and_blank_nothing():
    chat = chat_with()

    assert chat.send("hello").text == HINT
    assert chat.send("   ").text == ""


def test_an_unknown_command_gets_a_clear_message():
    reply = chat_with().send("/dance")

    assert "Unknown Command: /dance" in reply.text
    assert HINT in reply.text


def test_a_command_starts_its_agent_and_is_then_active():
    reply = chat_with(ScriptedAgent()).send("/char")

    assert reply == ("Welcome.", True)


def test_text_goes_to_the_active_agent():
    agent = ScriptedAgent(AgentReply("Which class?"))
    chat = chat_with(agent)
    chat.send("/char")

    reply = chat.send("a fighter")

    assert agent.heard == ["a fighter"]
    assert reply == ("Which class?", True)


def test_blank_lines_are_not_sent_to_the_agent():
    agent = ScriptedAgent()
    chat = chat_with(agent)
    chat.send("/char")

    assert chat.send("").text == ""
    assert agent.heard == []


def test_a_finished_agent_ends_the_command():
    chat = chat_with(ScriptedAgent(AgentReply("Saved.", finished=True)))
    chat.send("/char")

    assert chat.send("y") == ("Saved.", False)
    assert chat.send("hello").text == HINT


def test_starting_again_while_active_is_refused():
    chat = chat_with(ScriptedAgent())
    chat.send("/char")

    assert "Already in /char" in chat.send("/char").text


def test_exit_leaves_and_tells_what_the_agent_says():
    chat = chat_with(ScriptedAgent(farewell="Discarded."))
    chat.send("/char")

    assert chat.send("/exit") == ("Discarded.", False)
    assert chat.send("/exit").text == "Not in a Command."


def test_an_unavailable_agent_is_told_to_the_user():
    chat = chat_with(error=AgentUnavailableError("Set the key."))

    assert chat.send("/char") == ("Set the key.", False)
    assert chat.send("hi").text == HINT


def test_an_agent_that_becomes_unavailable_ends_the_command():
    chat = chat_with(ScriptedAgent(AgentUnavailableError("Too long.")))
    chat.send("/char")

    assert chat.send("hi") == ("Too long.", False)
    assert chat.send("hi").text == HINT


@pytest.mark.parametrize("line", ["/quit", "/quit now"])
def test_quit_ends_the_chat(line):
    chat = chat_with()

    assert not chat.ended
    chat.send(line)

    assert chat.ended
