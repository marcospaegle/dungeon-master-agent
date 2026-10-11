"""Building blocks for the deterministic checks of the cases."""

from collections.abc import Callable

from evals.case import Run


def is_equal(label: str, actual, expected) -> str | None:
    if actual == expected:
        return None
    return f"{label}: expected {expected!r}, got {actual!r}"


BASIC_FIELDS = (
    "name",
    "species",
    "background",
    "equipment",
    "personality",
    "class_features",
    "languages",
)


def filled(*names: str) -> Callable[[Run], str | None]:
    """A check that the named Character fields are not empty."""

    def check(run: Run) -> str | None:
        empty = [n for n in names if not getattr(run.character, n)]
        return f"empty fields: {', '.join(empty)}" if empty else None

    return check


def mentions(texts, wanted: list[str]) -> str | None:
    text = " ".join(texts).casefold()
    missing = [w for w in wanted if w.casefold() not in text]
    return f"missing: {', '.join(missing)}" if missing else None


def lacks(texts, unwanted: list[str]) -> str | None:
    text = " ".join(texts).casefold()
    found = [w for w in unwanted if w.casefold() in text]
    return f"should not have: {', '.join(found)}" if found else None
