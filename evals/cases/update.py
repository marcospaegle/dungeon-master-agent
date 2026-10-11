"""The user adds a Shield to a saved Character and changes alignment.

The saved Character is a Fighter with Chain Mail and a Longsword, so
adding a Shield is legal. Armor Class goes from 16 to 18 and
everything else must stay as saved.
"""

from dungeon.core.character import (
    Ability,
    Armor,
    Character,
    CharacterClass,
    ScoreMethod,
    Skill,
)
from evals.case import CONFIRM, Case, Check, Criterion, Run, Turn
from evals.checks import BASIC_FIELDS, filled, is_equal, mentions

STR, DEX, CON, INT, WIS, CHA = Ability

SCORES = {STR: 15, DEX: 14, CON: 13, INT: 8, WIS: 10, CHA: 12}
INCREASES = {STR: 2, CON: 1}
SKILLS = frozenset(
    {
        Skill.ATHLETICS,
        Skill.INTIMIDATION,
        Skill.ACROBATICS,
        Skill.PERCEPTION,
    }
)
FEATURES = ("Second Wind", "Weapon Mastery", "Dueling")

EXISTING = Character(
    name="Brannoch",
    species="Orc",
    background="Soldier",
    character_class=CharacterClass.FIGHTER,
    score_method=ScoreMethod.STANDARD_ARRAY,
    base_scores=SCORES,
    background_increases=INCREASES,
    skill_proficiencies=SKILLS,
    armor=Armor.CHAIN_MAIL,
    equipment=("Chain Mail", "Longsword", "Backpack"),
    personality="A gruff veteran who trusts discipline over words.",
    alignment="Lawful Good",
    languages=("Common", "Orc"),
    class_features=FEATURES,
    species_traits=("Adrenaline Rush", "Darkvision", "Relentless Endurance"),
    feats=("Savage Attacker",),
    weapon_proficiencies=("Simple weapons", "Martial weapons"),
)


def _unchanged(run: Run) -> str | None:
    c = run.character
    return (
        is_equal("name", c.name, "Brannoch")
        or is_equal("class", c.character_class, CharacterClass.FIGHTER)
        or is_equal("base scores", dict(c.base_scores), SCORES)
        or is_equal("increases", dict(c.background_increases), INCREASES)
        or is_equal("skills", set(c.skill_proficiencies), set(SKILLS))
        or is_equal("armor", c.armor, Armor.CHAIN_MAIL)
        or mentions(c.class_features, FEATURES)
        or mentions(c.feats, ["Savage Attacker"])
    )


def _changed(run: Run) -> str | None:
    c = run.character
    return (
        is_equal("shield", c.shield, True)
        or mentions([c.alignment], ["Neutral Good"])
        or is_equal("armor class", c.armor_class, 18)
    )


UPDATE = Case(
    name="update",
    scenario=(
        "The user updates the saved Orc Fighter Brannoch (Chain Mail, "
        "Longsword): add a Shield and change alignment to Neutral "
        "Good. Nothing else changes."
    ),
    turns=(
        Turn(
            "I want to update Brannoch. Give him a Shield and change "
            "his alignment to Neutral Good. Nothing else changes."
        ),
        CONFIRM,
    ),
    checks=(
        Check("fields filled", filled(*BASIC_FIELDS)),
        Check("what the user did not touch is kept", _unchanged),
        Check("what the user asked for is changed", _changed),
    ),
    rubric=(
        Criterion(
            "worked from the saved Character",
            "The agent worked from the existing Character instead of "
            "asking the user to repeat it, changed only what the user "
            "asked for, and asked for confirmation before finishing.",
        ),
    ),
    existing=EXISTING,
)
