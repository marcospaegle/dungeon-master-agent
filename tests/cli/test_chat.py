from typer.testing import CliRunner

from dungeon.cli import app

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
