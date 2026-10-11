import json
import re
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from dungeon.core.character import Character
from dungeon.core.character_store import CharacterStore
from dungeon.core.ports.agent import Agent
from evals.case import Case, CaseResult, CheckResult, Run


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


def run_case(case: Case, agent: Agent, store: CharacterStore) -> CaseResult:
    """Play a case against the agent, then apply its checks.

    Finishing stands for the user's final yes: the Character is saved
    through the real store and the checks see it as read back from
    disk.
    """
    try:
        finished, transcript = _play(case, agent)
    except ScriptError as error:
        return CaseResult(case.name, failure=str(error))
    if finished is None:
        return CaseResult(
            case.name,
            failure="the agent never reached the confirmation",
        )
    store.save(finished)
    saved = next(c for c in store.saved() if c.name == finished.name)
    run = Run(saved, tuple(transcript))
    results = []
    for check in case.checks:
        detail = check.check(run)
        results.append(CheckResult(check.name, detail is None, detail or ""))
    return CaseResult(case.name, tuple(results))


def write_results(results: list[CaseResult], folder: Path, model: str) -> Path:
    """Write one JSON file for the whole run; return its path."""
    now = datetime.now(UTC)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{now:%Y%m%dT%H%M%S}.json"
    path.write_text(
        json.dumps(
            {
                "time": now.isoformat(),
                "model": model,
                "passed": all(r.passed for r in results),
                "cases": [{**asdict(r), "passed": r.passed} for r in results],
            },
            indent=2,
        )
        + "\n"
    )
    return path
