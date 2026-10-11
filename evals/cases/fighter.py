"""The straightforward Fighter: standard array, Soldier, Chain Mail.

The expected numbers are worked by hand from the scripted choices
(final scores 17/14/14/8/10/12), not computed by the code under test.
The species is Orc because the 2024 Human adds a skill and a feat
choice that would change the counts below.
"""

from dungeon.core.character import (
    Ability,
    Armor,
    CharacterClass,
    ScoreMethod,
    Skill,
)
from evals.case import CONFIRM, Case, Check, Run, Turn
from evals.checks import BASIC_FIELDS, filled, is_equal, mentions

STR, DEX, CON, INT, WIS, CHA = Ability

SCORES = {STR: 15, DEX: 14, CON: 13, INT: 8, WIS: 10, CHA: 12}
INCREASES = {STR: 2, CON: 1}


def _class_and_choices(run: Run) -> str | None:
    c = run.character
    return (
        is_equal("class", c.character_class, CharacterClass.FIGHTER)
        or is_equal("score method", c.score_method, ScoreMethod.STANDARD_ARRAY)
        or is_equal("base scores", dict(c.base_scores), SCORES)
        or is_equal("increases", dict(c.background_increases), INCREASES)
        or is_equal("armor", c.armor, Armor.CHAIN_MAIL)
        or is_equal("shield", c.shield, False)
    )


def _skills(run: Run) -> str | None:
    skills = run.character.skill_proficiencies
    # Soldier grants Athletics and Intimidation; the Fighter picks two.
    wanted = {Skill.ATHLETICS, Skill.INTIMIDATION}
    return is_equal("skills", len(skills) == 4 and wanted <= skills, True)


def _derived(run: Run) -> str | None:
    c = run.character
    return (
        is_equal("hit points", c.hit_points, 12)
        or is_equal("armor class", c.armor_class, 16)
        or is_equal("initiative", c.initiative, 2)
        or is_equal("passive Perception", c.passive_perception, 12)
        or is_equal("Athletics", c.skill_bonuses[Skill.ATHLETICS], 5)
        or is_equal("Strength save", c.saving_throws[STR], 5)
        or is_equal("Wisdom save", c.saving_throws[WIS], 0)
    )


FIGHTER = Case(
    name="fighter",
    scenario=(
        "An Orc Fighter called Brannoch, Soldier background, standard "
        "array, Chain Mail and a Greatsword, no spells."
    ),
    turns=(
        Turn(
            "I want to make an Orc Fighter called Brannoch with the "
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
            "Lawful Good, tall and scarred. He speaks Common and Orc.",
            answers="personality|backstory|alignment|trait",
        ),
        CONFIRM,
    ),
    checks=(
        Check("fields filled", filled(*BASIC_FIELDS, "weapon_proficiencies")),
        Check("class and choices", _class_and_choices),
        Check("skills", _skills),
        Check(
            "Fighter features match the 2024 PHB",
            lambda run: mentions(
                run.character.class_features,
                ["Second Wind", "Weapon Mastery"],
            ),
        ),
        Check(
            "chosen style and Soldier feat",
            lambda run: mentions(
                (*run.character.class_features, *run.character.feats),
                ["Great Weapon Fighting", "Savage Attacker"],
            ),
        ),
        Check("derived numbers", _derived),
    ),
)
