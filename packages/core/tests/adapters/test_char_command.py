import json
from pathlib import Path

from characters import fighter
from pypdf import PdfReader

from dungeon_core.adapters.char_command import CharCommand
from dungeon_core.adapters.pypdf_sheet_writer import PypdfSheetWriter
from dungeon_core.character import Character
from dungeon_core.character_store import CharacterStore
from dungeon_core.ports.agent import AgentReply, AgentUnavailableError
from dungeon_core.ports.command import Reply

TEMPLATE = (
    Path(__file__).parents[4] / "storage" / "assets" / "character_sheet.pdf"
)


class ScriptedAgent:
    """Replies in order; the last reply finishes with the Character."""

    def __init__(self, *replies: AgentReply) -> None:
        self._replies = iter(replies)

    def reply(self, text: str) -> AgentReply:
        return next(self._replies)


def converse(command: CharCommand, *lines: str) -> list[Reply]:
    """Start the Command and feed it lines while it stays active.

    "/exit" leaves it, as the Chat would.
    """
    replies = [command.start()]
    for line in lines:
        if not replies[-1].active:
            break
        replies.append(
            command.leave() if line == "/exit" else command.handle(line)
        )
    return replies


def run(
    tmp_path: Path,
    agent: ScriptedAgent,
    *lines: str,
    drafts: list[Character | None] | None = None,
) -> str:
    """Drive /char; `drafts` collects what each start began from."""

    def agent_factory(draft: Character | None) -> ScriptedAgent:
        if drafts is not None:
            drafts.append(draft)
        return agent

    command = CharCommand(
        agent_factory, CharacterStore(tmp_path, PypdfSheetWriter(TEMPLATE))
    )
    return "\n".join(r.text for r in converse(command, *lines))


def finishing_agent() -> ScriptedAgent:
    return ScriptedAgent(
        AgentReply("What is your name?"),
        AgentReply("All done.", finished=fighter()),
    )


def test_char_routes_text_to_the_agent(tmp_path):
    output = run(tmp_path, finishing_agent(), "hi", "/exit")

    assert "What is your name?" in output


def test_exit_on_an_unfinished_character_warns_and_saves_nothing(tmp_path):
    output = run(tmp_path, finishing_agent(), "hi", "/exit")

    assert "Unfinished Character discarded." in output
    assert not list(tmp_path.iterdir())


def test_exit_before_saying_anything_discards_silently(tmp_path):
    output = run(tmp_path, finishing_agent(), "/exit")

    assert "discarded" not in output


def test_declining_the_confirmation_writes_nothing(tmp_path):
    output = run(tmp_path, finishing_agent(), "hi", "done", "n")

    assert "Not saved." in output
    assert not list(tmp_path.iterdir())


def test_confirming_writes_the_json_and_the_pdf_and_prints_the_path(
    tmp_path,
):
    output = run(tmp_path, finishing_agent(), "hi", "done", "y")

    pdf = tmp_path / "brannoch.pdf"
    assert str(pdf) in output
    assert json.loads((tmp_path / "brannoch.json").read_text())["name"] == (
        "Brannoch"
    )
    assert PdfReader(pdf).get_fields()


def test_the_pdf_is_rendered_from_the_json_on_disk(tmp_path):
    run(tmp_path, finishing_agent(), "hi", "done", "y")

    reader = PdfReader(tmp_path / "brannoch.pdf")
    values = {
        field.get("/V") for field in (reader.get_fields() or {}).values()
    }
    assert "Brannoch" in values


def save_brannoch(folder: Path, **overrides) -> None:
    CharacterStore(folder, PypdfSheetWriter(TEMPLATE)).save(
        fighter(**overrides)
    )


def test_char_lists_the_saved_characters_with_a_start_new_option(tmp_path):
    save_brannoch(tmp_path)
    save_brannoch(tmp_path, name="Aelar")

    output = run(tmp_path, finishing_agent(), "")

    assert "1. Aelar" in output
    assert "2. Brannoch" in output
    assert "Enter" in output


def test_char_without_saved_characters_does_not_ask_to_pick(tmp_path):
    drafts: list[Character | None] = []

    output = run(tmp_path, finishing_agent(), drafts=drafts)

    assert "1." not in output
    assert drafts == [None]


def test_starting_new_gives_the_agent_no_draft(tmp_path):
    save_brannoch(tmp_path)
    drafts: list[Character | None] = []

    run(tmp_path, finishing_agent(), "", drafts=drafts)

    assert drafts == [None]


def test_a_picked_character_is_loaded_into_the_agents_draft(tmp_path):
    save_brannoch(tmp_path)
    drafts: list[Character | None] = []

    run(tmp_path, finishing_agent(), "1", drafts=drafts)

    assert drafts == [fighter()]


def test_a_pick_that_is_not_listed_starts_nothing(tmp_path):
    save_brannoch(tmp_path)
    drafts: list[Character | None] = []

    output = run(tmp_path, finishing_agent(), "7", drafts=drafts)

    assert "Not a choice" in output
    assert drafts == []


def test_saving_over_an_existing_name_asks_before_overwriting(tmp_path):
    save_brannoch(tmp_path)

    output = run(tmp_path, finishing_agent(), "", "hi", "done", "y")

    assert "Brannoch already exists. Overwrite? [y/N]" in output


def test_declining_the_overwrite_leaves_both_files_unchanged(tmp_path):
    save_brannoch(tmp_path, personality="Gruff")
    before = {path.name: path.read_bytes() for path in tmp_path.iterdir()}

    output = run(tmp_path, finishing_agent(), "", "hi", "done", "n")

    assert "Not saved." in output
    assert {
        path.name: path.read_bytes() for path in tmp_path.iterdir()
    } == before


def test_confirming_an_edit_updates_the_json_and_the_pdf(tmp_path):
    save_brannoch(tmp_path, personality="Gruff")
    pdf_before = (tmp_path / "brannoch.pdf").read_bytes()

    run(tmp_path, finishing_agent(), "1", "hi", "done", "y")

    saved = json.loads((tmp_path / "brannoch.json").read_text())
    assert saved["personality"] == ""
    assert (tmp_path / "brannoch.pdf").read_bytes() != pdf_before


class UnavailableAgent:
    def reply(self, text: str) -> AgentReply:
        raise AgentUnavailableError("Run `dungeon build` first.")


def test_an_agent_that_cannot_run_ends_creation_with_its_message(tmp_path):
    command = CharCommand(
        lambda draft: UnavailableAgent(),
        CharacterStore(tmp_path, PypdfSheetWriter(TEMPLATE)),
    )

    replies = converse(command, "hi")

    assert replies[-1] == Reply("Run `dungeon build` first.")


def test_a_factory_that_cannot_build_the_agent_says_why(tmp_path):
    def agent_factory(draft):
        raise AgentUnavailableError("ANTHROPIC_API_KEY is not set.")

    command = CharCommand(
        agent_factory, CharacterStore(tmp_path, PypdfSheetWriter(TEMPLATE))
    )

    assert command.start() == Reply("ANTHROPIC_API_KEY is not set.")


def test_leaving_at_the_confirmation_saves_nothing(tmp_path):
    output = run(tmp_path, finishing_agent(), "hi", "done", "/exit")

    assert "Not saved." in output
    assert not list(tmp_path.iterdir())


def test_the_command_stays_active_until_it_is_done(tmp_path):
    command = CharCommand(
        lambda draft: finishing_agent(),
        CharacterStore(tmp_path, PypdfSheetWriter(TEMPLATE)),
    )

    replies = converse(command, "hi", "done", "y")

    assert [r.active for r in replies] == [True, True, True, False]


def test_a_stray_json_file_does_not_break_the_list(tmp_path):
    save_brannoch(tmp_path)
    (tmp_path / "notes.json").write_text("not json")
    (tmp_path / "other.json").write_text('{"a": 1}')

    output = run(tmp_path, finishing_agent(), "")

    assert "1. Brannoch" in output
    assert "2." not in output


def test_saving_an_edit_under_the_same_name_does_not_ask_to_overwrite(
    tmp_path,
):
    save_brannoch(tmp_path, personality="Gruff")

    output = run(tmp_path, finishing_agent(), "1", "hi", "done", "y")

    assert "Save Brannoch? [y/N]" in output
    assert "already exists" not in output


def test_renaming_an_edit_onto_another_character_asks_to_overwrite(tmp_path):
    save_brannoch(tmp_path)
    save_brannoch(tmp_path, name="Aelar")
    agent = ScriptedAgent(
        AgentReply("Renamed.", finished=fighter(name="Aelar"))
    )

    output = run(tmp_path, agent, "2", "rename", "n")

    assert "Aelar already exists. Overwrite? [y/N]" in output
