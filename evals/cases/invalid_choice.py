"""The user asks for things the rules do not allow.

A Sorcerer has no armor training and 18 is not on the standard array.
Numbers are worked by hand (final scores 8/13/15/10/12/17): Hit Points
6 + 2, Armor Class 10 + 1, saves Charisma 3 + 2 and Constitution
2 + 2, Persuasion 3 + 2.
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

SCORES = {STR: 8, DEX: 13, CON: 14, INT: 10, WIS: 12, CHA: 15}
INCREASES = {CHA: 2, CON: 1}


def _class_and_choices(run: Run) -> str | None:
    c = run.character
    return (
        is_equal("class", c.character_class, CharacterClass.SORCERER)
        or is_equal("score method", c.score_method, ScoreMethod.STANDARD_ARRAY)
        or is_equal("base scores", dict(c.base_scores), SCORES)
        or is_equal("increases", dict(c.background_increases), INCREASES)
        or is_equal("armor", c.armor, None)
        or is_equal("shield", c.shield, False)
    )


def _skills(run: Run) -> str | None:
    # Hermit grants Medicine and Religion; the Sorcerer picks two more.
    wanted = {
        Skill.MEDICINE,
        Skill.RELIGION,
        Skill.DECEPTION,
        Skill.PERSUASION,
    }
    return is_equal("skills", set(run.character.skill_proficiencies), wanted)


def _derived(run: Run) -> str | None:
    c = run.character
    return (
        is_equal("hit points", c.hit_points, 8)
        or is_equal("armor class", c.armor_class, 11)
        or is_equal("initiative", c.initiative, 1)
        or is_equal("passive Perception", c.passive_perception, 11)
        or is_equal("Persuasion", c.skill_bonuses[Skill.PERSUASION], 5)
        or is_equal("Charisma save", c.saving_throws[CHA], 5)
        or is_equal("Constitution save", c.saving_throws[CON], 4)
    )


INVALID_CHOICE = Case(
    name="invalid choice",
    scenario=(
        "The user asks a Sorcerer to wear Plate Armor and carry a "
        "Shield, then asks for an 18 on the standard array. Final: Orc "
        "Sorcerer, no armor."
    ),
    turns=(
        Turn(
            "I want to make an Orc Sorcerer called Zara with the Hermit "
            "background. She wears Plate Armor and carries a Shield."
        ),
        Turn(
            "Fine, no armor then. Use the standard array and put 18 in "
            "Charisma, then Constitution 14, Dexterity 13, Wisdom 12, "
            "Intelligence 10 and Strength 8. The background gives +2 "
            "Charisma and +1 Constitution."
        ),
        Turn(
            "Okay, then Charisma 15 instead, and the rest as I said.",
            answers="array|standard|15|legal|allow|18",
        ),
        Turn(
            "For my Sorcerer skills I take Deception and Persuasion.",
            answers="skill",
        ),
        Turn(
            "Just the starting equipment.",
            answers="equipment|armor|gear",
        ),
        Turn(
            "She is a charming, fast-talking exile. Chaotic Neutral, "
            "short with copper hair. She speaks Common and Orc.",
            answers="personality|backstory|alignment|trait",
        ),
        CONFIRM,
    ),
    checks=(
        Check("fields filled", filled(*BASIC_FIELDS)),
        Check("class and choices", _class_and_choices),
        Check("skills", _skills),
        Check(
            "Sorcerer features match the 2024 PHB",
            lambda run: mentions(
                run.character.class_features,
                ["Spellcasting", "Innate Sorcery"],
            ),
        ),
        Check("derived numbers", _derived),
    ),
    rubric=(
        Criterion(
            "refused the illegal choices",
            "The agent refused Plate Armor and a Shield for a "
            "Sorcerer, and refused an 18 on the standard array, "
            "explained why under the 2024 rules and offered a legal "
            "alternative instead of quietly accepting or silently "
            "changing them.",
        ),
    ),
)
