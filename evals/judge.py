import json
from collections.abc import Callable, Sequence

from langchain_core.language_models import BaseChatModel

from evals.case import CheckResult, Criterion

# Graded on every case. Cases add their own on top.
COMMON_RUBRIC = (
    Criterion(
        "scope",
        "The agent stayed on creating or updating the Character and "
        "politely declined or redirected anything unrelated.",
    ),
    Criterion(
        "rules explained",
        "Every rule the agent stated is correct under the D&D 5.5e "
        "(2024) rules, never the 2014 rules.",
    ),
    Criterion(
        "cites a Page",
        "Whenever the agent stated a rule it named a Source and a Page "
        "for it, and the citation is plausible. Pass if it stated no "
        "rule.",
    ),
    Criterion(
        "asks before finishing",
        "Before the final message the agent summarised the Character "
        "and asked the user to confirm it.",
    ),
)

PROMPT = """\
You grade a conversation between a user and an assistant that helps \
create a D&D 5.5e (2024) player character. Judge only what is in the \
transcript.

Scenario the user was playing:
{scenario}

Transcript:
{transcript}

Criteria:
{criteria}

Reply with only a JSON array with one object per criterion: \
{{"name": <the criterion name>, "passed": true or false, \
"reason": <one short sentence>}}.
"""


class Judge:
    """Grades a transcript against criteria with a language model.

    ``ask`` sends a prompt to the judge model and returns its text, so
    the judge knows nothing of any provider.
    """

    def __init__(self, ask: Callable[[str], str]) -> None:
        self._ask = ask

    def grade(
        self,
        scenario: str,
        transcript: Sequence[str],
        criteria: Sequence[Criterion],
    ) -> tuple[CheckResult, ...]:
        # The transcript alternates, starting with the user.
        lines = (
            f"{'User' if i % 2 == 0 else 'Agent'}: {text}"
            for i, text in enumerate(transcript)
        )
        prompt = PROMPT.format(
            scenario=scenario,
            transcript="\n".join(lines),
            criteria="\n".join(f"- {c.name}: {c.text}" for c in criteria),
        )
        verdicts = _parse(self._ask(prompt))
        if verdicts is None:
            return tuple(
                CheckResult(f"judge: {c.name}", False, "unreadable verdict")
                for c in criteria
            )
        return tuple(_result(c, verdicts.get(c.name)) for c in criteria)


def chat_judge(model: BaseChatModel) -> Judge:
    return Judge(lambda prompt: model.invoke(prompt).text)


def _result(criterion: Criterion, verdict: dict | None) -> CheckResult:
    name = f"judge: {criterion.name}"
    if verdict is None:
        return CheckResult(name, False, "no verdict")
    return CheckResult(
        name, verdict.get("passed") is True, str(verdict.get("reason", ""))
    )


def _parse(text: str) -> dict[str, dict] | None:
    """The verdicts keyed by criterion name, or None if unreadable."""
    start, end = text.find("["), text.rfind("]")
    if start < 0 or end < start:
        return None
    try:
        items = json.loads(text[start : end + 1])
        return {item["name"]: item for item in items}
    except ValueError, KeyError, TypeError:
        return None
