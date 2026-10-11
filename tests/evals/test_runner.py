import json
from pathlib import Path

from characters import fighter

from dungeon.core.adapters.pypdf_sheet_writer import PypdfSheetWriter
from dungeon.core.character_store import CharacterStore
from dungeon.core.ports.agent import AgentReply
from evals.case import Case, Check, CheckResult, Criterion, Turn
from evals.runner import pass_rates, run_case, write_results

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


def case(*checks: Check, **fields) -> Case:
    return Case(
        name="demo",
        scenario="A demo.",
        turns=(
            Turn("I want a fighter."),
            Turn("Standard array.", answers="abilit"),
            Turn("Yes, finish.", answers="confirm"),
        ),
        checks=checks,
        **fields,
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
    assert [(c.name, c.passed) for c in result.checks] == [("name", False)]


def test_finishing_before_the_confirmation_fails_the_case(tmp_path):
    agent = ScriptedAgent("Done already.")

    result = run_case(
        case(Check("name", named_fighter)), agent, store(tmp_path)
    )

    assert not result.passed
    assert "before the confirmation" in result.failure


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


class StubJudge:
    """Records what it was asked and fails every criterion it gets."""

    def __init__(self) -> None:
        self.asked = []

    def grade(self, scenario, transcript, criteria):
        self.asked.append((scenario, tuple(transcript), tuple(criteria)))
        return tuple(
            CheckResult(f"judge: {c.name}", False, "nope") for c in criteria
        )


def test_the_judge_grades_the_transcript_on_the_common_and_case_rubric(
    tmp_path,
):
    agent = ScriptedAgent("Which abilities?", "Please confirm.", "Done.")
    judge = StubJudge()
    own = Criterion("flavour", "Used the user's flavour.")

    result = run_case(
        case(Check("name", named_fighter), rubric=(own,)),
        agent,
        store(tmp_path),
        judge,
    )

    ((scenario, transcript, criteria),) = judge.asked
    assert scenario == "A demo."
    assert transcript[0] == "I want a fighter."
    assert transcript[1] == "Which abilities?"
    assert criteria[-1] == own
    assert len(criteria) > 1
    assert [c.name for c in result.checks][0] == "name"
    assert result.checks[-1] == CheckResult("judge: flavour", False, "nope")
    assert not result.passed


def test_no_judge_means_only_the_deterministic_checks_run(tmp_path):
    agent = ScriptedAgent("Which abilities?", "Please confirm.", "Done.")

    result = run_case(
        case(Check("name", named_fighter)), agent, store(tmp_path)
    )

    assert [c.name for c in result.checks] == ["name"]


def test_an_update_case_starts_from_the_saved_character(tmp_path):
    saved = store(tmp_path)
    agent = ScriptedAgent("Which abilities?", "Please confirm.", "Done.")
    seen = []

    def was_saved_first(run) -> str | None:
        seen.append(saved.saved())
        return None

    run_case(
        case(Check("any", was_saved_first), existing=fighter(name="Old")),
        agent,
        saved,
    )

    assert [c.name for c in seen[0]] == ["Brannoch", "Old"]


def test_pass_rates_count_each_check_across_cases(tmp_path):
    results = []
    for passes in (True, False, True):
        agent = ScriptedAgent("Which abilities?", "Please confirm.", "Done.")
        results.append(
            run_case(
                case(Check("a", lambda run, ok=passes: None if ok else "x")),
                agent,
                store(tmp_path),
            )
        )

    assert pass_rates(results) == {"a": (2, 3)}


def test_the_result_file_reports_pass_rates(tmp_path):
    agent = ScriptedAgent("Which abilities?", "Please confirm.", "Done.")
    result = run_case(
        case(Check("name", named_fighter)), agent, store(tmp_path)
    )

    path = write_results([result], tmp_path / "results", model="m")

    assert json.loads(path.read_text())["pass_rates"] == {
        "name": {"passed": 1, "total": 1, "rate": 1.0}
    }
