from typer.testing import CliRunner

from dungeon_cli import app
from dungeon_cli.chat.terminal import Terminal
from dungeon_core.agents.agent import AgentReply
from dungeon_core.chat.chat import Chat

runner = CliRunner()


def chat(*lines: str):
    return runner.invoke(app, ["chat"], input="\n".join(lines) + "\n")


def test_quit_ends_the_chat_cleanly():
    result = chat("/quit")

    assert result.exit_code == 0


def test_help_lists_the_commands():
    result = chat("/help", "/quit")

    assert "Commands:" in result.output


def test_text_goes_to_the_concierge():
    result = chat("hello there", "/quit")

    assert "The Concierge is not built yet." in result.output


def test_an_unknown_command_gets_a_clear_message():
    result = chat("/dance", "/quit")

    assert "Unknown Command: /dance" in result.output
    assert "Type /help to list the Commands." in result.output


def test_the_chat_ends_when_input_runs_out():
    result = runner.invoke(app, ["chat"], input="")

    assert result.exit_code == 0


def test_blank_lines_are_ignored():
    result = chat("", "/quit")

    assert "Concierge" not in result.output


def test_a_command_with_trailing_text_still_runs():
    result = chat("/help please", "/quit now")

    assert "Commands:" in result.output
    assert "Unknown Command" not in result.output


def test_agent_replies_render_as_markdown(monkeypatch):
    from dungeon_cli import chat as chat_module

    class Concierge:
        def send(self, text):
            return AgentReply("**Classes** and more")

    monkeypatch.setattr(chat_module, "PlaceholderConcierge", Concierge)
    result = chat("hi", "/quit")

    assert "Classes and more" in result.output
    assert "**" not in result.output


class EchoAgent:
    def send(self, text: str) -> AgentReply:
        return AgentReply(f"echo: {text}")

    def leave(self) -> str:
        return "echo off"


def drive(*lines: str) -> list[str]:
    inputs = iter(lines)
    output: list[str] = []

    def read() -> str:
        try:
            return next(inputs)
        except StopIteration:
            raise EOFError from None

    Terminal(Chat(EchoAgent()), read, output.append).run()
    return output


def test_the_terminal_writes_each_reply_until_quit():
    output = drive("hello", "/exit", "/quit", "never read")

    assert output == ["echo: hello", "Nothing to leave."]


def test_the_terminal_stops_when_input_runs_out():
    assert drive("hello") == ["echo: hello"]


def test_the_terminal_writes_nothing_for_an_empty_reply():
    assert drive("", "/quit") == []


def test_the_terminal_holds_busy_while_the_chat_works():
    from contextlib import contextmanager

    events: list[str] = []

    @contextmanager
    def busy():
        events.append("start")
        yield
        events.append("stop")

    inputs = iter(["hello", "/quit"])
    chat = Chat(EchoAgent())
    Terminal(chat, lambda: next(inputs), events.append, busy).run()

    assert events == ["start", "stop", "echo: hello", "start", "stop"]
