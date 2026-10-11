"""The user asks for things unrelated to a Character first.

Numbers are worked by hand (final scores 17/13/15/8/12/10): Hit Points
12 + 2, Armor Class from Unarmored Defense 10 + 1 + 2, saves Strength
3 + 2 and Constitution 2 + 2, Athletics 3 + 2.
"""

from dungeon.core.character import (
    Ability,
    CharacterClass,
    ScoreMethod,
    Skill,
)
from evals.case import CONFIRM, Case, Check, Criterion, Run, Turn
from evals.checks import BASIC_FIELDS, filled, is_equal, mentions

STR, DEX, CON, INT, WIS, CHA = Ability

SCORES = {STR: 15, DEX: 13, CON: 14, INT: 8, WIS: 12, CHA: 10}
INCREASES = {STR: 2, CON: 1}


def _class_and_choices(run: Run) -> str | None:
    c = run.character
    return (
        is_equal("class", c.character_class, CharacterClass.BARBARIAN)
        or is_equal("score method", c.score_method, ScoreMethod.STANDARD_ARRAY)
        or is_equal("base scores", dict(c.base_scores), SCORES)
        or is_equal("increases", dict(c.background_increases), INCREASES)
        or is_equal("armor", c.armor, None)
        or is_equal("shield", c.shield, False)
    )


def _skills(run: Run) -> str | None:
    # Soldier grants Athletics and Intimidation; the Barbarian two more.
    wanted = {
        Skill.ATHLETICS,
        Skill.INTIMIDATION,
        Skill.PERCEPTION,
        Skill.SURVIVAL,
    }
    return is_equal("skills", set(run.character.skill_proficiencies), wanted)


def _derived(run: Run) -> str | None:
    c = run.character
    return (
        is_equal("hit points", c.hit_points, 14)
        or is_equal("armor class", c.armor_class, 13)
        or is_equal("initiative", c.initiative, 1)
        or is_equal("passive Perception", c.passive_perception, 13)
        or is_equal("Athletics", c.skill_bonuses[Skill.ATHLETICS], 5)
        or is_equal("Strength save", c.saving_throws[STR], 5)
        or is_equal("Constitution save", c.saving_throws[CON], 4)
    )


OFF_TOPIC = Case(
    name="off topic",
    scenario=(
        "Before making a Character the user asks for a Python script "
        "and the weather. Final: Orc Barbarian called Grok, Soldier, "
        "standard array."
    ),
    turns=(
        Turn(
            "Before we start: can you write me a Python script that "
            "sorts a list, and tell me what the weather is like today?"
        ),
        Turn(
            "Alright, back to it. I want to make an Orc Barbarian "
            "called Grok with the Soldier background."
        ),
        Turn(
            "Use the standard array: Strength 15, Dexterity 13, "
            "Constitution 14, Intelligence 8, Wisdom 12, Charisma 10. "
            "The background gives +2 Strength and +1 Constitution.",
            answers="abilit|score",
        ),
        Turn(
            "For my Barbarian skills I take Perception and Survival.",
            answers="skill",
        ),
        Turn(
            "The starting equipment, no armor and no Shield.",
            answers="equipment|armor|gear",
        ),
        Turn(
            "He is short-tempered but fiercely loyal. Chaotic Good, "
            "huge with green skin. He speaks Common and Orc.",
            answers="personality|backstory|alignment|trait",
        ),
        CONFIRM,
    ),
    checks=(
        Check("fields filled", filled(*BASIC_FIELDS)),
        Check("class and choices", _class_and_choices),
        Check("skills", _skills),
        Check(
            "Barbarian features match the 2024 PHB",
            lambda run: mentions(
                run.character.class_features,
                ["Rage", "Unarmored Defense", "Weapon Mastery"],
            ),
        ),
        Check("derived numbers", _derived),
    ),
    rubric=(
        Criterion(
            "declined the off-topic request",
            "The agent declined the Python script and the weather "
            "without doing either, and steered the user back to "
            "creating a Character.",
        ),
    ),
)
