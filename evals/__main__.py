"""Run Evals: ``uv run python -m evals [case ...]``."""

import os
import sys
import tempfile
from pathlib import Path

from dotenv import dotenv_values

from dungeon.core.adapters.pypdf_sheet_writer import PypdfSheetWriter
from dungeon.core.agent_factory import (
    DEFAULT_MODEL,
    create_agent_factory,
)
from dungeon.core.character_store import CharacterStore
from dungeon.core.ports.agent import AgentUnavailableError
from evals.cases import CASES
from evals.runner import run_case, write_results

STORAGE = Path("storage")
RESULTS = Path("evals/results")


def main(names: list[str]) -> int:
    unknown = [name for name in names if name not in CASES]
    if unknown:
        print(f"Unknown case: {', '.join(unknown)}; known: {', '.join(CASES)}")
        return 2
    environ = {**dotenv_values(), **os.environ}
    create_agent = create_agent_factory(STORAGE / "chroma", environ)
    results = []
    for case in (CASES[n] for n in names or CASES):
        try:
            agent = create_agent(None)
        except AgentUnavailableError as error:
            print(error)
            return 2
        with tempfile.TemporaryDirectory() as folder:
            store = CharacterStore(
                Path(folder),
                PypdfSheetWriter(STORAGE / "assets" / "character_sheet.pdf"),
            )
            result = run_case(case, agent, store)
        results.append(result)
        print(f"{'PASS' if result.passed else 'FAIL'} {result.name}")
        if result.failure:
            print(f"  {result.failure}")
        for check in result.checks:
            print(f"  {'ok  ' if check.passed else 'FAIL'} {check.name}")
            if check.detail:
                print(f"       {check.detail}")
    model = environ.get("DUNGEON_MODEL") or DEFAULT_MODEL
    path = write_results(results, RESULTS, model)
    print(f"Results: {path}")
    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
