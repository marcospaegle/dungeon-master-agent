import json

from evals.case import Criterion
from evals.judge import Judge

CRITERIA = (
    Criterion("scope", "Stayed on the Character."),
    Criterion("confirmation", "Asked before finishing."),
)


def verdicts(*items: tuple[str, bool, str]) -> str:
    return json.dumps(
        [{"name": n, "passed": p, "reason": r} for n, p, r in items]
    )


def test_each_criterion_gets_the_judges_verdict_and_reason():
    judge = Judge(
        lambda prompt: verdicts(
            ("scope", True, "stayed on task"),
            ("confirmation", False, "finished without asking"),
        )
    )

    results = judge.grade("A fighter.", ("hi", "hello"), CRITERIA)

    assert [(r.name, r.passed, r.detail) for r in results] == [
        ("judge: scope", True, "stayed on task"),
        ("judge: confirmation", False, "finished without asking"),
    ]


def test_the_prompt_carries_the_scenario_transcript_and_criteria():
    prompts = []
    judge = Judge(lambda p: prompts.append(p) or verdicts())

    judge.grade("An Orc Fighter.", ("I want a fighter", "Which?"), CRITERIA)

    (prompt,) = prompts
    for wanted in (
        "An Orc Fighter.",
        "I want a fighter",
        "Which?",
        "scope: Stayed on the Character.",
        "confirmation: Asked before finishing.",
    ):
        assert wanted in prompt


def test_a_verdict_wrapped_in_a_code_fence_is_read():
    reply = "```json\n" + verdicts(("scope", True, "ok")) + "\n```"

    results = Judge(lambda p: reply).grade("s", (), CRITERIA[:1])

    assert [(r.name, r.passed) for r in results] == [("judge: scope", True)]


def test_a_criterion_the_judge_skipped_fails():
    judge = Judge(lambda p: verdicts(("scope", True, "ok")))

    results = judge.grade("s", (), CRITERIA)

    assert [(r.name, r.passed) for r in results] == [
        ("judge: scope", True),
        ("judge: confirmation", False),
    ]
    assert "no verdict" in results[1].detail


def test_an_unreadable_reply_fails_every_criterion():
    results = Judge(lambda p: "I refuse.").grade("s", (), CRITERIA)

    assert [r.passed for r in results] == [False, False]
    assert all("unreadable" in r.detail for r in results)
