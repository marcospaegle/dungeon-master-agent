import json
from pathlib import Path

from characters import fighter

from dungeon.core.adapters.pypdf_sheet_writer import PypdfSheetWriter
from dungeon.core.character_store import CharacterStore
from dungeon.core.ports.agent import AgentReply
from evals.case import Case, Check, Turn
from evals.runner import run_case, write_results

TEMPLATE = Path("storage/assets/character_sheet.pdf")


class ScriptedAgent:
    """Says its lines in order, finishing with the last one."""

    def __init__(self, *lines: str, finishes: bool = True) -> None:
        self._lines = iter(lines)
        self._remaining = len(lines)
        self._finishes = finishes

    def reply(self, text: str) -> AgentReply:
        self._remaining -= 1
        finished = (
            fighter() if self._finishes and not self._remaining else None
        )
        return AgentReply(next(self._lines), finished)


def store(tmp_path) -> CharacterStore:
    return CharacterStore(tmp_path / "characters", PypdfSheetWriter(TEMPLATE))


def case(*checks: Check) -> Case:
    return Case(
        name="demo",
        scenario="A demo.",
        turns=(
            Turn("I want a fighter."),
            Turn("Standard array.", answers="abilit"),
            Turn("Yes, finish.", answers="confirm"),
        ),
        checks=checks,
    )


def named_fighter(run) -> str | None:
    return None if run.character.name == "Brannoch" else "wrong name"


def test_a_case_that_reaches_confirmation_reports_each_check(tmp_path):
    agent = ScriptedAgent("Which abilities?", "Please confirm.", "Done.")

    result = run_case(
        case(Check("name", named_fighter), Check("bad", lambda run: "no")),
        agent,
        store(tmp_path),
    )

    assert not result.passed
    assert [(c.name, c.passed) for c in result.checks] == [
        ("name", True),
        ("bad", False),
    ]
    assert result.checks[1].detail == "no"


def test_the_saved_character_is_what_the_checks_see(tmp_path):
    agent = ScriptedAgent("Which abilities?", "Please confirm.", "Done.")

    result = run_case(
        case(Check("name", named_fighter)), agent, store(tmp_path)
    )

    assert result.passed
    assert (tmp_path / "characters" / "brannoch.json").exists()


def test_an_unscripted_question_fails_the_case(tmp_path):
    agent = ScriptedAgent("What is your favourite colour?", "Done.")

    result = run_case(
        case(Check("name", named_fighter)), agent, store(tmp_path)
    )

    assert not result.passed
    assert "unscripted" in result.failure
    assert "favourite colour" in result.failure
    assert result.checks == ()


def test_never_reaching_confirmation_fails_the_case(tmp_path):
    agent = ScriptedAgent(
        "Which abilities?",
        "Please confirm.",
        "Anything else?",
        finishes=False,
    )

    result = run_case(
        case(Check("name", named_fighter)), agent, store(tmp_path)
    )

    assert not result.passed
    assert "confirmation" in result.failure


def test_a_run_writes_one_json_result_file(tmp_path):
    agent = ScriptedAgent("Which abilities?", "Please confirm.", "Done.")
    result = run_case(
        case(Check("name", named_fighter)), agent, store(tmp_path)
    )

    path = write_results([result], tmp_path / "results", model="test-model")

    written = json.loads(path.read_text())
    assert list(path.parent.iterdir()) == [path]
    assert written["model"] == "test-model"
    assert written["cases"][0]["name"] == "demo"
    assert written["cases"][0]["checks"][0] == {
        "name": "name",
        "passed": True,
        "detail": "",
    }
