from evals.case import Case
from evals.cases.changed_mind import CHANGED_MIND
from evals.cases.fighter import FIGHTER
from evals.cases.invalid_choice import INVALID_CHOICE
from evals.cases.off_topic import OFF_TOPIC
from evals.cases.spellcaster import SPELLCASTER
from evals.cases.update import UPDATE

CASES: dict[str, Case] = {
    case.name: case
    for case in (
        FIGHTER,
        SPELLCASTER,
        CHANGED_MIND,
        INVALID_CHOICE,
        OFF_TOPIC,
        UPDATE,
    )
}
