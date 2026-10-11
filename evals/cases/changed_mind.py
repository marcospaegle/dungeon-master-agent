"""The user switches from a Barbarian to a Cleric mid-conversation.

Numbers are worked by hand (final scores 10/12/13/8/17/15): Hit Points
8 + 1, Armor Class Chain Shirt 13 + Dexterity 1 + Shield 2, saves
Wisdom 3 + 2 and Charisma 2 + 2, Medicine 3 + 2.
"""

from dungeon.core.character import (
    Ability,
    Armor,
    CharacterClass,
    ScoreMethod,
    Skill,
)
from evals.case import CONFIRM, Case, Check, Criterion, Run, Turn
from evals.checks import BASIC_FIELDS, filled, is_equal, lacks, mentions

STR, DEX, CON, INT, WIS, CHA = Ability

SCORES = {STR: 10, DEX: 12, CON: 13, INT: 8, WIS: 15, CHA: 14}
INCREASES = {WIS: 2, CHA: 1}


def _class_and_choices(run: Run) -> str | None:
    c = run.character
    return (
        is_equal("class", c.character_class, CharacterClass.CLERIC)
        or is_equal("score method", c.score_method, ScoreMethod.STANDARD_ARRAY)
        or is_equal("base scores", dict(c.base_scores), SCORES)
        or is_equal("increases", dict(c.background_increases), INCREASES)
        or is_equal("armor", c.armor, Armor.CHAIN_SHIRT)
        or is_equal("shield", c.shield, True)
    )


def _skills(run: Run) -> str | None:
    # Acolyte grants Insight and Religion; the Cleric picks two more.
    wanted = {
        Skill.INSIGHT,
        Skill.RELIGION,
        Skill.MEDICINE,
        Skill.PERSUASION,
    }
    return is_equal("skills", set(run.character.skill_proficiencies), wanted)


def _derived(run: Run) -> str | None:
    c = run.character
    return (
        is_equal("hit points", c.hit_points, 9)
        or is_equal("armor class", c.armor_class, 16)
        or is_equal("initiative", c.initiative, 1)
        or is_equal("passive Perception", c.passive_perception, 13)
        or is_equal("Medicine", c.skill_bonuses[Skill.MEDICINE], 5)
        or is_equal("Wisdom save", c.saving_throws[WIS], 5)
        or is_equal("Charisma save", c.saving_throws[CHA], 4)
    )


CHANGED_MIND = Case(
    name="changed mind",
    scenario=(
        "The user starts an Orc Barbarian called Dagna (Acolyte), then "
        "changes to a Cleric before any scores are chosen. Final: Orc "
        "Cleric, standard array, Chain Shirt and Shield."
    ),
    turns=(
        Turn(
            "I want to make an Orc Barbarian called Dagna with the "
            "Acolyte background."
        ),
        Turn(
            "Wait, change of plans: I would rather play a Cleric than a "
            "Barbarian. Same name, species and background."
        ),
        Turn(
            "Use the standard array: Strength 10, Dexterity 12, "
            "Constitution 13, Intelligence 8, Wisdom 15, Charisma 14. "
            "The background gives +2 Wisdom and +1 Charisma.",
            answers="abilit|score",
        ),
        Turn(
            "For my Cleric skills I take Medicine and Persuasion.",
            answers="skill",
        ),
        Turn(
            "Take a Chain Shirt and a Shield.",
            answers="equipment|armor|gear",
        ),
        Turn(
            "She is a patient healer who forgives too easily. Lawful "
            "Good, broad-shouldered with a shaved head. She speaks "
            "Common and Orc.",
            answers="personality|backstory|alignment|trait",
        ),
        CONFIRM,
    ),
    checks=(
        Check("fields filled", filled(*BASIC_FIELDS)),
        Check("class and choices", _class_and_choices),
        Check("skills", _skills),
        Check(
            "Cleric features match the 2024 PHB",
            lambda run: mentions(
                run.character.class_features, ["Spellcasting"]
            ),
        ),
        Check(
            "nothing left of the Barbarian",
            lambda run: lacks(
                run.character.class_features, ["Rage", "Unarmored Defense"]
            ),
        ),
        Check("derived numbers", _derived),
    ),
    rubric=(
        Criterion(
            "accepted the change",
            "The agent accepted the switch to Cleric without "
            "complaint or confusion and carried on with the Cleric, "
            "keeping the name, species and background.",
        ),
    ),
)
