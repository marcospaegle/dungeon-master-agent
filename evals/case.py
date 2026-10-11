from collections.abc import Callable
from dataclasses import dataclass
from typing import NamedTuple

from dungeon.core.character import Character


class Turn(NamedTuple):
    """One scripted user reply.

    ``answers`` is a regex (case-insensitive) that the agent's previous
    message must match, so the reply is only given to the question it
    was written for. Empty for the opening message.
    """

    reply: str
    answers: str = ""


CONFIRM = Turn(
    "Yes, that looks right. Finish it.",
    answers="confirm|look right|ready|correct",
)


@dataclass(frozen=True)
class Run:
    """What a finished case leaves behind for the checks to inspect."""

    character: Character
    transcript: tuple[str, ...]


class Check(NamedTuple):
    """A deterministic check: returns None, or why it failed."""

    name: str
    check: Callable[[Run], str | None]


class Criterion(NamedTuple):
    """One thing the judge grades a transcript on."""

    name: str
    text: str


@dataclass(frozen=True)
class Case:
    """A scripted scenario.

    ``rubric`` is graded by the judge on top of the common rubric.
    ``existing`` is a saved Character the case starts by updating.
    """

    name: str
    scenario: str
    turns: tuple[Turn, ...]
    checks: tuple[Check, ...]
    rubric: tuple[Criterion, ...] = ()
    existing: Character | None = None


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    detail: str = ""


@dataclass(frozen=True)
class CaseResult:
    """The outcome of a case.

    ``failure`` is set when the script itself broke (an unscripted
    question, no confirmation); the checks are then not run.
    """

    name: str
    checks: tuple[CheckResult, ...] = ()
    failure: str = ""

    @property
    def passed(self) -> bool:
        return not self.failure and all(c.passed for c in self.checks)
