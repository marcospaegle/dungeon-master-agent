import pytest

from dungeon.core.character import (
    Ability,
    Armor,
    Character,
    CharacterClass,
    InvalidCharacterError,
    ScoreMethod,
    Skill,
)

STR, DEX, CON, INT, WIS, CHA = Ability


def fighter(**overrides) -> Character:
    """A level 1 Soldier Fighter on the standard array.

    Base scores are 15/14/13/8/10/12 for Str/Dex/Con/Int/Wis/Cha, and
    the background adds +2 Str and +1 Con, so the final scores are
    17/14/14/8/10/12.
    """
    fields = dict(
        name="Brannoch",
        species="Human",
        background="Soldier",
        character_class=CharacterClass.FIGHTER,
        score_method=ScoreMethod.STANDARD_ARRAY,
        base_scores={
            STR: 15,
            DEX: 14,
            CON: 13,
            INT: 8,
            WIS: 10,
            CHA: 12,
        },
        background_increases={STR: 2, CON: 1},
        skill_proficiencies={
            Skill.ATHLETICS,
            Skill.INTIMIDATION,
            Skill.ACROBATICS,
            Skill.PERCEPTION,
        },
    )
    fields.update(overrides)
    return Character(**fields)


def agile_fighter(**overrides) -> Character:
    """The same Fighter with Dex 17 (+3) instead of Str 17."""
    return fighter(
        base_scores={STR: 14, DEX: 15, CON: 13, INT: 8, WIS: 10, CHA: 12},
        background_increases={DEX: 2, CON: 1},
        **overrides,
    )


def test_ability_scores_include_the_background_increases():
    character = fighter()

    assert dict(character.ability_scores) == {
        STR: 17,
        DEX: 14,
        CON: 14,
        INT: 8,
        WIS: 10,
        CHA: 12,
    }


def test_ability_modifiers_follow_the_modifiers_table():
    character = fighter()

    assert dict(character.ability_modifiers) == {
        STR: 3,
        DEX: 2,
        CON: 2,
        INT: -1,
        WIS: 0,
        CHA: 1,
    }


def test_proficiency_bonus_is_plus_two_at_level_1():
    assert fighter().proficiency_bonus == 2


def test_saving_throws_add_proficiency_for_the_class_abilities():
    # A Fighter is proficient in Strength and Constitution saves.
    assert dict(fighter().saving_throws) == {
        STR: 5,
        DEX: 2,
        CON: 4,
        INT: -1,
        WIS: 0,
        CHA: 1,
    }


def test_skill_bonuses_use_the_skills_ability():
    bonuses = fighter().skill_bonuses

    assert bonuses[Skill.ATHLETICS] == 5  # Str +3, proficient
    assert bonuses[Skill.INTIMIDATION] == 3  # Cha +1, proficient
    assert bonuses[Skill.ACROBATICS] == 4  # Dex +2, proficient
    assert bonuses[Skill.STEALTH] == 2  # Dex +2
    assert bonuses[Skill.HISTORY] == -1  # Int -1
    assert bonuses[Skill.SURVIVAL] == 0  # Wis 0
    assert len(bonuses) == 18


def test_passive_perception_is_10_plus_the_perception_bonus():
    # Wis 0, proficient in Perception: 10 + 2.
    assert fighter().passive_perception == 12


def test_passive_perception_without_proficiency():
    character = fighter(
        skill_proficiencies={Skill.ATHLETICS, Skill.INTIMIDATION}
    )

    assert character.passive_perception == 10


def test_initiative_is_the_dexterity_modifier():
    assert fighter().initiative == 2


@pytest.mark.parametrize(
    ("character_class", "hit_die"),
    [
        (CharacterClass.BARBARIAN, 12),
        (CharacterClass.FIGHTER, 10),
        (CharacterClass.PALADIN, 10),
        (CharacterClass.RANGER, 10),
        (CharacterClass.BARD, 8),
        (CharacterClass.CLERIC, 8),
        (CharacterClass.DRUID, 8),
        (CharacterClass.MONK, 8),
        (CharacterClass.ROGUE, 8),
        (CharacterClass.WARLOCK, 8),
        (CharacterClass.SORCERER, 6),
        (CharacterClass.WIZARD, 6),
    ],
)
def test_hit_points_are_the_hit_die_plus_constitution(
    character_class, hit_die
):
    character = fighter(character_class=character_class)

    assert character.hit_points == hit_die + 2  # Con 14 is +2


def test_unarmored_armor_class_is_10_plus_dexterity():
    assert fighter().armor_class == 12  # Dex 14 is +2


def test_light_armor_adds_the_full_dexterity_modifier():
    # Studded Leather is 12 + Dex; Dex 17 is +3.
    character = agile_fighter(armor=Armor.STUDDED_LEATHER)

    assert character.armor_class == 15


def test_medium_armor_caps_the_dexterity_modifier_at_2():
    # Chain Shirt is 13 + Dex (max 2); Dex 17 is +3.
    character = agile_fighter(armor=Armor.CHAIN_SHIRT)

    assert character.armor_class == 15


def test_heavy_armor_ignores_dexterity():
    assert fighter(armor=Armor.CHAIN_MAIL).armor_class == 16


def test_a_shield_adds_2():
    character = fighter(armor=Armor.CHAIN_MAIL, shield=True)

    assert character.armor_class == 18


def test_a_barbarian_without_armor_adds_constitution():
    # Unarmored Defense: 10 + Dex +2 + Con +2.
    barbarian = fighter(character_class=CharacterClass.BARBARIAN)

    assert barbarian.armor_class == 14


def test_a_barbarian_keeps_unarmored_defense_with_a_shield():
    barbarian = fighter(character_class=CharacterClass.BARBARIAN, shield=True)

    assert barbarian.armor_class == 16


def test_a_barbarian_in_armor_uses_the_armor():
    # Chain Shirt is 13 + Dex (max 2); no Unarmored Defense.
    barbarian = fighter(
        character_class=CharacterClass.BARBARIAN, armor=Armor.CHAIN_SHIRT
    )

    assert barbarian.armor_class == 15


def monk(**overrides) -> Character:
    """A Monk on the Monk row of the Standard Array by Class table.

    Dex 15 and Wis 14 plus the background's +1 and +2 make both +3.
    """
    return fighter(
        character_class=CharacterClass.MONK,
        base_scores={STR: 12, DEX: 15, CON: 13, INT: 10, WIS: 14, CHA: 8},
        background_increases={WIS: 2, DEX: 1},
        **overrides,
    )


def test_a_monk_without_armor_or_shield_adds_wisdom():
    # Unarmored Defense: 10 + Dex +3 + Wis +3.
    assert monk().armor_class == 16


def test_heavy_armor_is_not_lowered_by_a_negative_dexterity():
    # Chain Mail is a flat 16; Dex 8 is -1.
    clumsy = fighter(
        base_scores={STR: 15, DEX: 8, CON: 14, INT: 12, WIS: 10, CHA: 13},
        armor=Armor.CHAIN_MAIL,
    )

    assert clumsy.armor_class == 16


def test_armor_the_class_is_not_trained_with_is_rejected():
    # Wizards have no armor training.
    with pytest.raises(InvalidCharacterError, match="Chain Mail"):
        fighter(character_class=CharacterClass.WIZARD, armor=Armor.CHAIN_MAIL)


def test_a_barbarian_cannot_wear_heavy_armor():
    with pytest.raises(InvalidCharacterError, match="Chain Mail"):
        fighter(
            character_class=CharacterClass.BARBARIAN,
            armor=Armor.CHAIN_MAIL,
        )


def test_a_shield_the_class_is_not_trained_with_is_rejected():
    # Bards have only Light armor training.
    with pytest.raises(InvalidCharacterError, match="Shield"):
        fighter(character_class=CharacterClass.BARD, shield=True)


def rogue(**overrides) -> Character:
    """A Rogue on the Rogue row of the Standard Array by Class table.

    The background adds +2 Dex and +1 Int: Dex 17 (+3), Wis 10 (0).
    """
    fields = dict(
        character_class=CharacterClass.ROGUE,
        base_scores={STR: 12, DEX: 15, CON: 13, INT: 14, WIS: 10, CHA: 8},
        background_increases={DEX: 2, INT: 1},
        skill_proficiencies={
            Skill.STEALTH,
            Skill.PERCEPTION,
            Skill.SLEIGHT_OF_HAND,
            Skill.INSIGHT,
        },
        expertise={Skill.STEALTH, Skill.PERCEPTION},
    )
    fields.update(overrides)
    return fighter(**fields)


def test_expertise_doubles_the_proficiency_bonus():
    bonuses = rogue().skill_bonuses

    assert bonuses[Skill.STEALTH] == 7  # Dex +3, proficiency 2 x 2
    assert bonuses[Skill.SLEIGHT_OF_HAND] == 5  # Dex +3, proficient


def test_passive_perception_counts_expertise():
    assert rogue().passive_perception == 14  # 10 + Wis 0 + 2 x 2


def test_expertise_in_a_skill_without_proficiency_is_rejected():
    with pytest.raises(InvalidCharacterError, match="Arcana"):
        rogue(expertise={Skill.ARCANA})


def test_only_a_rogue_has_expertise_at_level_1():
    with pytest.raises(InvalidCharacterError, match="Expertise"):
        fighter(expertise={Skill.ATHLETICS})


def test_a_rogue_has_expertise_in_at_most_two_skills():
    with pytest.raises(InvalidCharacterError, match="two"):
        rogue(expertise={Skill.STEALTH, Skill.PERCEPTION, Skill.INSIGHT})


def scores(*values: int) -> dict[Ability, int]:
    return dict(zip(Ability, values, strict=True))


def test_all_six_abilities_are_required():
    with pytest.raises(InvalidCharacterError, match="six abilities"):
        fighter(base_scores={STR: 15, DEX: 14, CON: 13})


def test_the_standard_array_must_be_assigned_as_is():
    with pytest.raises(InvalidCharacterError, match="standard array"):
        fighter(base_scores=scores(16, 14, 13, 8, 10, 12))


def test_a_point_buy_may_spend_all_27_points():
    # 15 costs 9, 8 costs 0.
    character = fighter(
        score_method=ScoreMethod.POINT_BUY,
        base_scores=scores(15, 15, 15, 8, 8, 8),
    )

    assert character.ability_scores[STR] == 17


def test_a_point_buy_may_leave_points_unspent():
    fighter(
        score_method=ScoreMethod.POINT_BUY,
        base_scores=scores(13, 13, 13, 8, 8, 8),  # 15 points
    )


def test_a_point_buy_over_27_points_is_rejected():
    # 14 costs 7 and 13 costs 5: 7 + 7 + 7 + 5 + 5 + 0 = 31.
    with pytest.raises(InvalidCharacterError, match="27"):
        fighter(
            score_method=ScoreMethod.POINT_BUY,
            base_scores=scores(14, 14, 14, 13, 13, 8),
        )


@pytest.mark.parametrize("score", [7, 16])
def test_a_point_buy_score_must_be_from_8_to_15(score):
    with pytest.raises(InvalidCharacterError, match="8 to 15"):
        fighter(
            score_method=ScoreMethod.POINT_BUY,
            base_scores=scores(score, 8, 8, 8, 8, 8),
        )


def test_rolled_scores_may_be_anything_a_roll_can_give():
    # Four d6, drop the lowest: from 3 to 18.
    character = fighter(
        score_method=ScoreMethod.ROLLED,
        base_scores=scores(18, 3, 11, 9, 14, 7),
    )

    assert character.ability_modifiers[DEX] == -4


@pytest.mark.parametrize("score", [2, 19])
def test_a_rolled_score_outside_3_to_18_is_rejected(score):
    with pytest.raises(InvalidCharacterError, match="3 to 18"):
        fighter(
            score_method=ScoreMethod.ROLLED,
            base_scores=scores(score, 10, 10, 10, 10, 10),
        )


def test_a_background_may_add_1_to_three_abilities():
    character = fighter(background_increases={STR: 1, DEX: 1, CON: 1})

    assert character.ability_scores[STR] == 16
    assert character.ability_scores[DEX] == 15
    assert character.ability_scores[CON] == 14


@pytest.mark.parametrize(
    "increases",
    [
        {STR: 2},
        {STR: 3},
        {STR: 1, DEX: 1},
        {STR: 2, DEX: 2},
        {STR: 2, DEX: 1, CON: 1},
        {STR: 1, DEX: 1, CON: 1, INT: 1},
        {},
    ],
)
def test_other_background_increases_are_rejected(increases):
    with pytest.raises(InvalidCharacterError, match="background"):
        fighter(background_increases=increases)


def test_a_character_is_not_changed_by_its_inputs_afterwards():
    base = scores(15, 14, 13, 8, 10, 12)
    increases = {STR: 2, CON: 1}
    character = fighter(base_scores=base, background_increases=increases)

    base[STR] = 8
    increases[DEX] = 5

    assert character.ability_scores[STR] == 17
    assert character.ability_scores[DEX] == 14


@pytest.mark.parametrize(
    ("character_class", "proficient"),
    [
        (CharacterClass.BARBARIAN, {STR, CON}),
        (CharacterClass.BARD, {DEX, CHA}),
        (CharacterClass.CLERIC, {WIS, CHA}),
        (CharacterClass.DRUID, {INT, WIS}),
        (CharacterClass.FIGHTER, {STR, CON}),
        (CharacterClass.MONK, {STR, DEX}),
        (CharacterClass.PALADIN, {WIS, CHA}),
        (CharacterClass.RANGER, {STR, DEX}),
        (CharacterClass.ROGUE, {DEX, INT}),
        (CharacterClass.SORCERER, {CON, CHA}),
        (CharacterClass.WARLOCK, {WIS, CHA}),
        (CharacterClass.WIZARD, {INT, WIS}),
    ],
)
def test_each_class_is_proficient_in_two_saving_throws(
    character_class, proficient
):
    # The fixture's modifiers are Str +3, Dex +2, Con +2, Int -1,
    # Wis 0, Cha +1: a proficient save is 2 higher than the modifier.
    modifiers = fighter().ability_modifiers
    character = fighter(character_class=character_class)

    assert dict(character.saving_throws) == {
        ability: modifiers[ability] + (2 if ability in proficient else 0)
        for ability in Ability
    }


def test_a_character_keeps_its_equipment_and_story():
    equipment = ["Greatsword", "Explorer's Pack"]
    character = fighter(
        equipment=equipment,
        personality="Blunt and loyal",
        backstory="Left the legion after the siege of Karth.",
    )
    equipment.append("Dagger")

    assert character.equipment == ("Greatsword", "Explorer's Pack")
    assert character.personality == "Blunt and loyal"
    assert character.backstory.startswith("Left the legion")
