"""The straightforward Fighter: standard array, Soldier, Chain Mail.

The expected numbers are worked by hand from the scripted choices
(final scores 17/14/14/8/10/12), not computed by the code under test.
"""

from dungeon.core.character import (
    Ability,
    Armor,
    CharacterClass,
    ScoreMethod,
    Skill,
)
from evals.case import Case, Check, Run, Turn

STR, DEX, CON, INT, WIS, CHA = Ability

SCORES = {STR: 15, DEX: 14, CON: 13, INT: 8, WIS: 10, CHA: 12}
INCREASES = {STR: 2, CON: 1}


def _is(label: str, actual, expected) -> str | None:
    if actual == expected:
        return None
    return f"{label}: expected {expected!r}, got {actual!r}"


def _filled(run: Run) -> str | None:
    c = run.character
    empty = [
        name
        for name, value in (
            ("name", c.name),
            ("species", c.species),
            ("background", c.background),
            ("equipment", c.equipment),
            ("personality", c.personality),
            ("class_features", c.class_features),
            ("languages", c.languages),
            ("weapon_proficiencies", c.weapon_proficiencies),
        )
        if not value
    ]
    return f"empty fields: {', '.join(empty)}" if empty else None


def _mentions(texts, wanted: list[str]) -> str | None:
    text = " ".join(texts).casefold()
    missing = [w for w in wanted if w.casefold() not in text]
    return f"missing: {', '.join(missing)}" if missing else None


def _class_and_choices(run: Run) -> str | None:
    c = run.character
    return (
        _is("class", c.character_class, CharacterClass.FIGHTER)
        or _is("score method", c.score_method, ScoreMethod.STANDARD_ARRAY)
        or _is("base scores", dict(c.base_scores), SCORES)
        or _is("increases", dict(c.background_increases), INCREASES)
        or _is("armor", c.armor, Armor.CHAIN_MAIL)
        or _is("shield", c.shield, False)
    )


def _skills(run: Run) -> str | None:
    skills = run.character.skill_proficiencies
    # Soldier grants Athletics and Intimidation; the Fighter picks two.
    wanted = {Skill.ATHLETICS, Skill.INTIMIDATION}
    return _is("skills", len(skills) == 4 and wanted <= skills, True)


def _derived(run: Run) -> str | None:
    c = run.character
    return (
        _is("hit points", c.hit_points, 12)
        or _is("armor class", c.armor_class, 16)
        or _is("initiative", c.initiative, 2)
        or _is("passive Perception", c.passive_perception, 12)
        or _is("Athletics", c.skill_bonuses[Skill.ATHLETICS], 5)
        or _is("Strength save", c.saving_throws[STR], 5)
        or _is("Wisdom save", c.saving_throws[WIS], 0)
    )


FIGHTER = Case(
    name="fighter",
    scenario=(
        "A Human Fighter called Brannoch, Soldier background, standard "
        "array, Chain Mail and a Greatsword, no spells."
    ),
    turns=(
        Turn(
            "I want to make a Human Fighter called Brannoch with the "
            "Soldier background, taking the Great Weapon Fighting style."
        ),
        Turn(
            "Use the standard array: Strength 15, Dexterity 14, "
            "Constitution 13, Intelligence 8, Wisdom 10, Charisma 12. "
            "The background gives +2 Strength and +1 Constitution.",
            answers="abilit|score",
        ),
        Turn(
            "For my Fighter skills I take Acrobatics and Perception.",
            answers="skill",
        ),
        Turn(
            "I take the starting equipment with Chain Mail and the "
            "Greatsword, and no Shield.",
            answers="equipment|armor|gear",
        ),
        Turn(
            "He is a gruff veteran who trusts discipline over words. "
            "Lawful Good, tall and scarred. He speaks Common.",
            answers="personality|backstory|alignment|trait",
        ),
        Turn(
            "Yes, that looks right. Finish it.",
            answers="confirm|look right|ready|correct",
        ),
    ),
    checks=(
        Check("fields filled", _filled),
        Check("class and choices", _class_and_choices),
        Check("skills", _skills),
        Check(
            "Fighter features match the PHB",
            lambda run: _mentions(
                run.character.class_features,
                ["Second Wind", "Weapon Mastery"],
            ),
        ),
        Check(
            "chosen style and Soldier feat",
            lambda run: _mentions(
                (*run.character.class_features, *run.character.feats),
                ["Great Weapon Fighting", "Savage Attacker"],
            ),
        ),
        Check("derived numbers", _derived),
    ),
)
