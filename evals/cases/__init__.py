from evals.case import Case
from evals.cases.fighter import FIGHTER

CASES: dict[str, Case] = {case.name: case for case in (FIGHTER,)}
