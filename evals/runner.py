import json
import re
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from dungeon.core.character import Character
from dungeon.core.character_store import CharacterStore
from dungeon.core.ports.agent import Agent
from evals.case import Case, CaseResult, CheckResult, Run
from evals.judge import COMMON_RUBRIC, Judge


def _play(case: Case, agent: Agent) -> tuple[Character | None, list[str]]:
    """Give the scripted replies; stop when the agent finishes.

    Raises ScriptError if the agent asks what the script has no
    answer for.
    """
    transcript: list[str] = []
    previous = ""
    for turn in case.turns:
        if turn.answers and not re.search(
            turn.answers, previous, re.IGNORECASE
        ):
            raise ScriptError(
                f"unscripted question, expected /{turn.answers}/ but the "
                f"agent said: {previous!r}"
            )
        transcript.append(turn.reply)
        reply = agent.reply(turn.reply)
        transcript.append(reply.text)
        previous = reply.text
        if reply.finished is not None:
            if turn is not case.turns[-1]:
                raise ScriptError(
                    "the agent finished before the confirmation turn"
                )
            return reply.finished, transcript
    return None, transcript


class ScriptError(Exception):
    """The agent went somewhere the script cannot follow."""


def run_case(
    case: Case,
    agent: Agent,
    store: CharacterStore,
    judge: Judge | None = None,
) -> CaseResult:
    """Play a case against the agent, then apply its checks.

    With a judge, the transcript is also graded against the common
    rubric and the case's own; its verdicts join the checks. A case
    with an existing Character saves it first, so the run overwrites
    it as the update flow does.

    Finishing stands for the user's final yes: the Character is saved
    through the real store and the checks see it as read back from
    disk.
    """
    if case.existing is not None:
        store.save(case.existing)
    try:
        finished, transcript = _play(case, agent)
    except ScriptError as error:
        return _broken(case, str(error), judge)
    if finished is None:
        return _broken(case, "the agent never reached the confirmation", judge)
    store.save(finished)
    saved = next(c for c in store.saved() if c.name == finished.name)
    run = Run(saved, tuple(transcript))
    results = []
    for check in case.checks:
        detail = check.check(run)
        results.append(CheckResult(check.name, detail is None, detail or ""))
    if judge is not None:
        results.extend(
            judge.grade(
                case.scenario, transcript, (*COMMON_RUBRIC, *case.rubric)
            )
        )
    return CaseResult(case.name, tuple(results))


def _broken(case: Case, failure: str, judge: Judge | None) -> CaseResult:
    """A case whose script broke fails all its checks, so the pass
    rates do not hide it."""
    names = [check.name for check in case.checks]
    if judge is not None:
        names += [f"judge: {c.name}" for c in (*COMMON_RUBRIC, *case.rubric)]
    checks = tuple(CheckResult(n, False, "not run") for n in names)
    return CaseResult(case.name, checks, failure)


def pass_rates(results: list[CaseResult]) -> dict[str, tuple[int, int]]:
    """For each check, how many cases passed it and how many ran it."""
    rates: dict[str, tuple[int, int]] = {}
    for result in results:
        for check in result.checks:
            passed, total = rates.get(check.name, (0, 0))
            rates[check.name] = (passed + check.passed, total + 1)
    return rates


def write_results(
    results: list[CaseResult], folder: Path, model: str, judge_model: str = ""
) -> Path:
    """Write one JSON file for the whole run; return its path."""
    now = datetime.now(UTC)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{now:%Y%m%dT%H%M%S}.json"
    path.write_text(
        json.dumps(
            {
                "time": now.isoformat(),
                "model": model,
                "judge_model": judge_model,
                "passed": all(r.passed for r in results),
                "pass_rates": {
                    name: {
                        "passed": passed,
                        "total": total,
                        "rate": passed / total,
                    }
                    for name, (passed, total) in pass_rates(results).items()
                },
                "cases": [{**asdict(r), "passed": r.passed} for r in results],
            },
            indent=2,
        )
        + "\n"
    )
    return path
