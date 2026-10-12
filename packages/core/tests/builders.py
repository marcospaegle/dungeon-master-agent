from dungeon_core.characters.character import (
    Ability,
    Character,
    CharacterClass,
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
