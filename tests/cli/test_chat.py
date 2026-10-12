import shutil

from typer.testing import CliRunner

from dungeon.cli import app
from dungeon.cli.chat.chat import Chat
from dungeon.core.ports.command import Reply

runner = CliRunner()


def chat(*lines: str):
    return runner.invoke(app, ["chat"], input="\n".join(lines) + "\n")


def test_quit_ends_the_chat_cleanly():
    result = chat("/quit")

    assert result.exit_code == 0


def test_help_lists_the_commands():
    result = chat("/help", "/quit")

    assert "Commands:" in result.output


def test_text_outside_a_command_gets_a_hint():
    result = chat("hello there", "/quit")

    assert "Type /help to list the Commands." in result.output


def test_an_unknown_command_gets_a_clear_message():
    result = chat("/dance", "/quit")

    assert "Unknown Command: /dance" in result.output
    assert "Type /help to list the Commands." in result.output


def test_the_chat_ends_when_input_runs_out():
    result = runner.invoke(app, ["chat"], input="")

    assert result.exit_code == 0


def test_blank_lines_are_ignored():
    result = chat("", "/quit")

    assert "Type /help" not in result.output


def test_a_command_with_trailing_text_still_runs():
    result = chat("/help please", "/quit now")

    assert "Commands:" in result.output
    assert "Unknown Command" not in result.output


def test_agent_replies_render_as_markdown(monkeypatch, tmp_path):
    from dungeon.cli import chat as chat_module
    from dungeon.core.ports.agent import AgentReply

    class Agent:
        def reply(self, text):
            return AgentReply("**Classes** and more")

    (tmp_path / "assets").mkdir()
    shutil.copy(
        chat_module.STORAGE / "assets" / "character_sheet.pdf",
        tmp_path / "assets",
    )
    monkeypatch.setattr(chat_module, "STORAGE", tmp_path)
    monkeypatch.setattr(
        chat_module, "create_agent_factory", lambda *a: lambda draft: Agent()
    )
    result = chat("/char", "hi", "/quit")

    assert "Classes and more" in result.output
    assert "**" not in result.output


class EchoCommand:
    """Stays active and echoes what it is told."""

    name = "/echo"
    description = "Repeat things"

    def __init__(self) -> None:
        self.left = False

    def start(self) -> Reply:
        return Reply("echo on", active=True)

    def handle(self, text: str) -> Reply:
        return Reply(f"echo: {text}", active=True)

    def leave(self) -> Reply:
        self.left = True
        return Reply("echo off")


def drive(*lines: str, commands=None) -> tuple[str, EchoCommand]:
    echo = EchoCommand()
    inputs = iter([*lines, "/quit"])
    output: list[str] = []
    Chat(
        read=lambda: next(inputs),
        write=output.append,
        commands=[echo] if commands is None else commands,
    ).run()
    return "\n".join(output), echo


def test_help_lists_registered_commands_with_their_descriptions():
    output, _ = drive("/help")

    assert "`/echo` Repeat things" in output


def test_text_goes_to_the_active_command():
    output, _ = drive("/echo", "hello")

    assert "echo: hello" in output


def test_blank_lines_reach_the_active_command():
    output, _ = drive("/echo", "")

    assert "echo: \n" in output + "\n"


def test_exit_leaves_the_active_command_and_stops_routing():
    output, echo = drive("/echo", "/exit", "hello")

    assert echo.left
    assert "echo off" in output
    assert "echo: hello" not in output
    assert "Type /help to list the Commands." in output


def test_exit_outside_a_command_says_so():
    output, _ = drive("/exit")

    assert "Not in a Command." in output


def test_a_command_cannot_be_started_while_one_is_active():
    output, _ = drive("/echo", "/echo")

    assert output.count("echo on") == 1
    assert "Already in /echo. /exit leaves." in output
