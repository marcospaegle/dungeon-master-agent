from builders import fighter

from dungeon_core.characters.character import (
    Armor,
    Attack,
    CharacterClass,
    Skill,
)
from dungeon_core.characters.serializer import CharacterSerializer


def test_a_character_survives_the_json_round_trip():
    character = fighter(
        armor=Armor.CHAIN_MAIL,
        shield=True,
        equipment=("Backpack",),
        attacks=(Attack("Longsword", "+5", "1d8+3 Slashing", "Versatile"),),
        languages=("Common",),
    )

    assert (
        CharacterSerializer.from_dict(CharacterSerializer.to_dict(character))
        == character
    )


def test_a_rogues_expertise_survives_the_json_round_trip():
    character = fighter(
        character_class=CharacterClass.ROGUE,
        expertise={Skill.ATHLETICS},
    )

    assert (
        CharacterSerializer.from_dict(CharacterSerializer.to_dict(character))
        == character
    )
