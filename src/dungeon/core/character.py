"""A level 1 Character under the D&D 5.5e (2024) rules.

The Character holds only the choices that define it; every number that
follows from them is derived here, in code, never by the model.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import NamedTuple


class Ability(StrEnum):
    STRENGTH = "Strength"
    DEXTERITY = "Dexterity"
    CONSTITUTION = "Constitution"
    INTELLIGENCE = "Intelligence"
    WISDOM = "Wisdom"
    CHARISMA = "Charisma"


class Skill(StrEnum):
    ACROBATICS = "Acrobatics"
    ANIMAL_HANDLING = "Animal Handling"
    ARCANA = "Arcana"
    ATHLETICS = "Athletics"
    DECEPTION = "Deception"
    HISTORY = "History"
    INSIGHT = "Insight"
    INTIMIDATION = "Intimidation"
    INVESTIGATION = "Investigation"
    MEDICINE = "Medicine"
    NATURE = "Nature"
    PERCEPTION = "Perception"
    PERFORMANCE = "Performance"
    PERSUASION = "Persuasion"
    RELIGION = "Religion"
    SLEIGHT_OF_HAND = "Sleight of Hand"
    STEALTH = "Stealth"
    SURVIVAL = "Survival"


class CharacterClass(StrEnum):
    BARBARIAN = "Barbarian"
    BARD = "Bard"
    CLERIC = "Cleric"
    DRUID = "Druid"
    FIGHTER = "Fighter"
    MONK = "Monk"
    PALADIN = "Paladin"
    RANGER = "Ranger"
    ROGUE = "Rogue"
    SORCERER = "Sorcerer"
    WARLOCK = "Warlock"
    WIZARD = "Wizard"


class Armor(StrEnum):
    PADDED = "Padded Armor"
    LEATHER = "Leather Armor"
    STUDDED_LEATHER = "Studded Leather Armor"
    HIDE = "Hide Armor"
    CHAIN_SHIRT = "Chain Shirt"
    SCALE_MAIL = "Scale Mail"
    BREASTPLATE = "Breastplate"
    HALF_PLATE = "Half Plate Armor"
    RING_MAIL = "Ring Mail"
    CHAIN_MAIL = "Chain Mail"
    SPLINT = "Splint Armor"
    PLATE = "Plate Armor"


class ArmorCategory(StrEnum):
    LIGHT = "Light"
    MEDIUM = "Medium"
    HEAVY = "Heavy"


class ScoreMethod(StrEnum):
    STANDARD_ARRAY = "standard array"
    POINT_BUY = "point buy"
    ROLLED = "rolled"


STR, DEX, CON, INT, WIS, CHA = Ability

PROFICIENCY_BONUS = 2  # at level 1

# Step 3: Determine Ability Scores, Player's Handbook (2024), chapter 2.
STANDARD_ARRAY = (15, 14, 13, 12, 10, 8)
POINT_BUY_BUDGET = 27
POINT_BUY_COSTS = {8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9}
ROLLED_SCORES = range(3, 19)  # four d6, dropping the lowest
BACKGROUND_INCREASES = ([2, 1], [1, 1, 1])

# Core traits tables, Player's Handbook (2024), chapter 3.
SAVING_THROW_PROFICIENCIES = {
    CharacterClass.BARBARIAN: frozenset({STR, CON}),
    CharacterClass.BARD: frozenset({DEX, CHA}),
    CharacterClass.CLERIC: frozenset({WIS, CHA}),
    CharacterClass.DRUID: frozenset({INT, WIS}),
    CharacterClass.FIGHTER: frozenset({STR, CON}),
    CharacterClass.MONK: frozenset({STR, DEX}),
    CharacterClass.PALADIN: frozenset({WIS, CHA}),
    CharacterClass.RANGER: frozenset({STR, DEX}),
    CharacterClass.ROGUE: frozenset({DEX, INT}),
    CharacterClass.SORCERER: frozenset({CON, CHA}),
    CharacterClass.WARLOCK: frozenset({WIS, CHA}),
    CharacterClass.WIZARD: frozenset({INT, WIS}),
}


# The Skills table, Player's Handbook (2024), chapter 1.
SKILL_ABILITIES = {
    Skill.ACROBATICS: DEX,
    Skill.ANIMAL_HANDLING: WIS,
    Skill.ARCANA: INT,
    Skill.ATHLETICS: STR,
    Skill.DECEPTION: CHA,
    Skill.HISTORY: INT,
    Skill.INSIGHT: WIS,
    Skill.INTIMIDATION: CHA,
    Skill.INVESTIGATION: INT,
    Skill.MEDICINE: WIS,
    Skill.NATURE: INT,
    Skill.PERCEPTION: WIS,
    Skill.PERFORMANCE: CHA,
    Skill.PERSUASION: CHA,
    Skill.RELIGION: INT,
    Skill.SLEIGHT_OF_HAND: DEX,
    Skill.STEALTH: DEX,
    Skill.SURVIVAL: WIS,
}


HIT_DIE = {
    CharacterClass.BARBARIAN: 12,
    CharacterClass.FIGHTER: 10,
    CharacterClass.PALADIN: 10,
    CharacterClass.RANGER: 10,
    CharacterClass.BARD: 8,
    CharacterClass.CLERIC: 8,
    CharacterClass.DRUID: 8,
    CharacterClass.MONK: 8,
    CharacterClass.ROGUE: 8,
    CharacterClass.WARLOCK: 8,
    CharacterClass.SORCERER: 6,
    CharacterClass.WIZARD: 6,
}


class ArmorStats(NamedTuple):
    category: ArmorCategory
    base_armor_class: int


class ArmorTraining(NamedTuple):
    categories: frozenset[ArmorCategory]
    shields: bool


LIGHT, MEDIUM, HEAVY = ArmorCategory

# The Armor table, Player's Handbook (2024), chapter 6.
ARMOR = {
    Armor.PADDED: ArmorStats(LIGHT, 11),
    Armor.LEATHER: ArmorStats(LIGHT, 11),
    Armor.STUDDED_LEATHER: ArmorStats(LIGHT, 12),
    Armor.HIDE: ArmorStats(MEDIUM, 12),
    Armor.CHAIN_SHIRT: ArmorStats(MEDIUM, 13),
    Armor.SCALE_MAIL: ArmorStats(MEDIUM, 14),
    Armor.BREASTPLATE: ArmorStats(MEDIUM, 14),
    Armor.HALF_PLATE: ArmorStats(MEDIUM, 15),
    Armor.RING_MAIL: ArmorStats(HEAVY, 14),
    Armor.CHAIN_MAIL: ArmorStats(HEAVY, 16),
    Armor.SPLINT: ArmorStats(HEAVY, 17),
    Armor.PLATE: ArmorStats(HEAVY, 18),
}
MEDIUM_ARMOR_MAX_DEXTERITY = 2

# Armor Training in each class's Core traits table.
ARMOR_TRAINING = {
    CharacterClass.BARBARIAN: ArmorTraining(
        frozenset({LIGHT, MEDIUM}), shields=True
    ),
    CharacterClass.BARD: ArmorTraining(frozenset({LIGHT}), shields=False),
    CharacterClass.CLERIC: ArmorTraining(
        frozenset({LIGHT, MEDIUM}), shields=True
    ),
    CharacterClass.DRUID: ArmorTraining(frozenset({LIGHT}), shields=True),
    CharacterClass.FIGHTER: ArmorTraining(
        frozenset({LIGHT, MEDIUM, HEAVY}), shields=True
    ),
    CharacterClass.MONK: ArmorTraining(frozenset(), shields=False),
    CharacterClass.PALADIN: ArmorTraining(
        frozenset({LIGHT, MEDIUM, HEAVY}), shields=True
    ),
    CharacterClass.RANGER: ArmorTraining(
        frozenset({LIGHT, MEDIUM}), shields=True
    ),
    CharacterClass.ROGUE: ArmorTraining(frozenset({LIGHT}), shields=False),
    CharacterClass.SORCERER: ArmorTraining(frozenset(), shields=False),
    CharacterClass.WARLOCK: ArmorTraining(frozenset({LIGHT}), shields=False),
    CharacterClass.WIZARD: ArmorTraining(frozenset(), shields=False),
}
SHIELD_ARMOR_CLASS = 2
ROGUE_EXPERTISE_SKILLS = 2  # skills; the other pick can be a tool


def modifier(score: int) -> int:
    return (score - 10) // 2


class InvalidCharacterError(ValueError):
    """The choices do not make a legal Character."""


@dataclass(frozen=True)
class Character:
    name: str
    species: str
    background: str
    character_class: CharacterClass
    score_method: ScoreMethod
    base_scores: Mapping[Ability, int]
    background_increases: Mapping[Ability, int]
    skill_proficiencies: frozenset[Skill]
    expertise: frozenset[Skill] = frozenset()
    armor: Armor | None = None
    shield: bool = False
    equipment: tuple[str, ...] = ()
    personality: str = ""
    backstory: str = ""

    def __post_init__(self):
        # Copy what the caller may still hold, then validate the copy.
        for field, copy in (
            ("base_scores", lambda v: MappingProxyType(dict(v))),
            ("background_increases", lambda v: MappingProxyType(dict(v))),
            ("skill_proficiencies", frozenset),
            ("expertise", frozenset),
            ("equipment", tuple),
        ):
            object.__setattr__(self, field, copy(getattr(self, field)))
        self._check_ability_scores()
        self._check_expertise()
        self._check_armor_training()

    @property
    def ability_scores(self) -> Mapping[Ability, int]:
        return {
            ability: score + self.background_increases.get(ability, 0)
            for ability, score in self.base_scores.items()
        }

    @property
    def ability_modifiers(self) -> Mapping[Ability, int]:
        return {
            ability: modifier(score)
            for ability, score in self.ability_scores.items()
        }

    @property
    def proficiency_bonus(self) -> int:
        return PROFICIENCY_BONUS

    @property
    def saving_throws(self) -> Mapping[Ability, int]:
        proficient = SAVING_THROW_PROFICIENCIES[self.character_class]
        return {
            ability: bonus
            + (self.proficiency_bonus if ability in proficient else 0)
            for ability, bonus in self.ability_modifiers.items()
        }

    @property
    def skill_bonuses(self) -> Mapping[Skill, int]:
        modifiers = self.ability_modifiers
        return {
            skill: modifiers[ability] + self._proficiency_in(skill)
            for skill, ability in SKILL_ABILITIES.items()
        }

    def _proficiency_in(self, skill: Skill) -> int:
        if skill in self.expertise:
            return 2 * self.proficiency_bonus
        if skill in self.skill_proficiencies:
            return self.proficiency_bonus
        return 0

    @property
    def passive_perception(self) -> int:
        return 10 + self.skill_bonuses[Skill.PERCEPTION]

    @property
    def initiative(self) -> int:
        return self.ability_modifiers[DEX]

    @property
    def hit_points(self) -> int:
        """Level 1: the hit die at its maximum plus Constitution."""
        return HIT_DIE[self.character_class] + self.ability_modifiers[CON]

    def _check_ability_scores(self):
        if set(self.base_scores) != set(Ability):
            raise InvalidCharacterError(
                "Scores are needed for all six abilities"
            )
        scores = sorted(self.base_scores.values(), reverse=True)
        match self.score_method:
            case ScoreMethod.STANDARD_ARRAY:
                if scores != list(STANDARD_ARRAY):
                    raise InvalidCharacterError(
                        "The standard array is 15, 14, 13, 12, 10 and "
                        "8, each assigned to one ability"
                    )
            case ScoreMethod.POINT_BUY:
                if not set(scores) <= POINT_BUY_COSTS.keys():
                    raise InvalidCharacterError(
                        "A point buy score is from 8 to 15"
                    )
                cost = sum(POINT_BUY_COSTS[score] for score in scores)
                if cost > POINT_BUY_BUDGET:
                    raise InvalidCharacterError(
                        f"A point buy has {POINT_BUY_BUDGET} points to spend"
                    )
            case ScoreMethod.ROLLED:
                if not set(scores) <= set(ROLLED_SCORES):
                    raise InvalidCharacterError(
                        "A rolled score is from 3 to 18"
                    )
        if sorted(self.background_increases.values(), reverse=True) not in (
            BACKGROUND_INCREASES
        ):
            raise InvalidCharacterError(
                "The background increases one ability by 2 and another "
                "by 1, or three abilities by 1"
            )

    def _check_expertise(self):
        if not self.expertise:
            return
        if self.character_class is not CharacterClass.ROGUE:
            raise InvalidCharacterError(
                f"A {self.character_class} has no Expertise at level 1"
            )
        if len(self.expertise) > ROGUE_EXPERTISE_SKILLS:
            raise InvalidCharacterError(
                "A Rogue has Expertise in at most two skills"
            )
        untrained = self.expertise - self.skill_proficiencies
        if untrained:
            names = ", ".join(sorted(untrained))
            raise InvalidCharacterError(
                f"Expertise needs proficiency first, missing: {names}"
            )

    def _check_armor_training(self):
        training = ARMOR_TRAINING[self.character_class]
        if (
            self.armor is not None
            and ARMOR[self.armor].category not in training.categories
        ):
            raise InvalidCharacterError(
                f"A {self.character_class} has no training with {self.armor}"
            )
        if self.shield and not training.shields:
            raise InvalidCharacterError(
                f"A {self.character_class} has no training with Shields"
            )

    @property
    def armor_class(self) -> int:
        modifiers = self.ability_modifiers
        shield = SHIELD_ARMOR_CLASS if self.shield else 0

        if self.armor is None:
            base = 10 + modifiers[DEX]
            match self.character_class:
                case CharacterClass.BARBARIAN:
                    base += modifiers[CON]
                case CharacterClass.MONK:
                    base += modifiers[WIS]
            return base + shield

        category, base = ARMOR[self.armor]
        match category:
            case ArmorCategory.LIGHT:
                base += modifiers[DEX]
            case ArmorCategory.MEDIUM:
                base += min(modifiers[DEX], MEDIUM_ARMOR_MAX_DEXTERITY)
        return base + shield
