import json
from pathlib import Path

from characters import fighter
from pypdf import PdfReader

from dungeon.cli.chat.chat import Chat
from dungeon.core.adapters.pypdf_sheet_writer import PypdfSheetWriter
from dungeon.core.character import Character
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


def run(
    tmp_path: Path,
    agent: ScriptedAgent,
    *lines: str,
    drafts: list[Character | None] | None = None,
) -> str:
    """Drive a Chat; `drafts` collects what each /char started from."""
    inputs = iter([*lines, "/quit"])
    output: list[str] = []

    def agent_factory(draft: Character | None) -> ScriptedAgent:
        if drafts is not None:
            drafts.append(draft)
        return agent

    Chat(
        read=lambda: next(inputs),
        write=output.append,
        agent_factory=agent_factory,
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


def save_brannoch(folder: Path, **overrides) -> None:
    CharacterStore(folder, PypdfSheetWriter(TEMPLATE)).save(
        fighter(**overrides)
    )


def test_char_lists_the_saved_characters_with_a_start_new_option(tmp_path):
    save_brannoch(tmp_path)
    save_brannoch(tmp_path, name="Aelar")

    output = run(tmp_path, finishing_agent(), "/char", "")

    assert "1. Aelar" in output
    assert "2. Brannoch" in output
    assert "Enter" in output


def test_char_without_saved_characters_does_not_ask_to_pick(tmp_path):
    drafts: list[Character | None] = []

    output = run(tmp_path, finishing_agent(), "/char", drafts=drafts)

    assert "1." not in output
    assert drafts == [None]


def test_starting_new_gives_the_agent_no_draft(tmp_path):
    save_brannoch(tmp_path)
    drafts: list[Character | None] = []

    run(tmp_path, finishing_agent(), "/char", "", drafts=drafts)

    assert drafts == [None]


def test_a_picked_character_is_loaded_into_the_agents_draft(tmp_path):
    save_brannoch(tmp_path)
    drafts: list[Character | None] = []

    run(tmp_path, finishing_agent(), "/char", "1", drafts=drafts)

    assert drafts == [fighter()]


def test_a_pick_that_is_not_listed_starts_nothing(tmp_path):
    save_brannoch(tmp_path)
    drafts: list[Character | None] = []

    output = run(tmp_path, finishing_agent(), "/char", "7", drafts=drafts)

    assert "Not a choice" in output
    assert drafts == []


def test_saving_over_an_existing_name_asks_before_overwriting(tmp_path):
    save_brannoch(tmp_path)

    output = run(tmp_path, finishing_agent(), "/char", "", "hi", "done", "y")

    assert "Brannoch already exists. Overwrite? [y/N]" in output


def test_declining_the_overwrite_leaves_both_files_unchanged(tmp_path):
    save_brannoch(tmp_path, personality="Gruff")
    before = {path.name: path.read_bytes() for path in tmp_path.iterdir()}

    output = run(tmp_path, finishing_agent(), "/char", "", "hi", "done", "n")

    assert "Not saved." in output
    assert {
        path.name: path.read_bytes() for path in tmp_path.iterdir()
    } == before


def test_confirming_an_edit_updates_the_json_and_the_pdf(tmp_path):
    save_brannoch(tmp_path, personality="Gruff")
    pdf_before = (tmp_path / "brannoch.pdf").read_bytes()

    run(tmp_path, finishing_agent(), "/char", "1", "hi", "done", "y")

    saved = json.loads((tmp_path / "brannoch.json").read_text())
    assert saved["personality"] == ""
    assert (tmp_path / "brannoch.pdf").read_bytes() != pdf_before
