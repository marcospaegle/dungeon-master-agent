import json
from pathlib import Path

from characters import fighter
from pypdf import PdfReader

from dungeon.cli.chat.chat import Chat
from dungeon.core.adapters.pypdf_sheet_writer import PypdfSheetWriter
from dungeon.core.character_store import CharacterStore
from dungeon.core.ports.agent import AgentReply

TEMPLATE = (
    Path(__file__).parents[2] / "storage" / "assets" / "character_sheet.pdf"
)


class ScriptedAgent:
    """Replies in order; the last reply finishes with the Character."""

    def __init__(self, *replies: AgentReply) -> None:
        self._replies = iter(replies)

    def reply(self, text: str) -> AgentReply:
        return next(self._replies)


def run(tmp_path: Path, agent: ScriptedAgent, *lines: str) -> str:
    inputs = iter([*lines, "/quit"])
    output: list[str] = []
    Chat(
        read=lambda: next(inputs),
        write=output.append,
        agent_factory=lambda: agent,
        store=CharacterStore(tmp_path, PypdfSheetWriter(TEMPLATE)),
    ).run()
    return "\n".join(output)


def finishing_agent() -> ScriptedAgent:
    return ScriptedAgent(
        AgentReply("What is your name?"),
        AgentReply("All done.", finished=fighter()),
    )


def test_char_routes_text_to_the_agent(tmp_path):
    output = run(tmp_path, finishing_agent(), "/char", "hi", "/exit")

    assert "What is your name?" in output


def test_text_after_exit_gets_the_hint_again(tmp_path):
    output = run(tmp_path, finishing_agent(), "/char", "/exit", "hello")

    assert "Type /help to list the Commands." in output


def test_exit_on_an_unfinished_character_warns_and_saves_nothing(tmp_path):
    output = run(tmp_path, finishing_agent(), "/char", "hi", "/exit")

    assert "Unfinished Character discarded." in output
    assert not list(tmp_path.iterdir())


def test_exit_before_saying_anything_discards_silently(tmp_path):
    output = run(tmp_path, finishing_agent(), "/char", "/exit")

    assert "discarded" not in output


def test_declining_the_confirmation_writes_nothing(tmp_path):
    output = run(tmp_path, finishing_agent(), "/char", "hi", "done", "n")

    assert "Not saved." in output
    assert not list(tmp_path.iterdir())


def test_confirming_writes_the_json_and_the_pdf_and_prints_the_path(
    tmp_path,
):
    output = run(tmp_path, finishing_agent(), "/char", "hi", "done", "y")

    pdf = tmp_path / "brannoch.pdf"
    assert str(pdf) in output
    assert json.loads((tmp_path / "brannoch.json").read_text())["name"] == (
        "Brannoch"
    )
    assert PdfReader(pdf).get_fields()


def test_the_pdf_is_rendered_from_the_json_on_disk(tmp_path):
    run(tmp_path, finishing_agent(), "/char", "hi", "done", "y")

    reader = PdfReader(tmp_path / "brannoch.pdf")
    values = {
        field.get("/V") for field in (reader.get_fields() or {}).values()
    }
    assert "Brannoch" in values


def test_char_without_an_agent_says_it_is_unavailable():
    output: list[str] = []
    inputs = iter(["/char", "/quit"])
    Chat(read=lambda: next(inputs), write=output.append).run()

    assert "not available" in "\n".join(output)
