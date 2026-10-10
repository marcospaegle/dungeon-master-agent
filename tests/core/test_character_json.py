from characters import fighter

from dungeon.core.character import Armor, Attack, CharacterClass, Skill
from dungeon.core.character_json import (
    character_from_dict,
    character_to_dict,
)


def test_a_character_survives_the_json_round_trip():
    character = fighter(
        armor=Armor.CHAIN_MAIL,
        shield=True,
        equipment=("Backpack",),
        attacks=(Attack("Longsword", "+5", "1d8+3 Slashing", "Versatile"),),
        languages=("Common",),
    )

    assert character_from_dict(character_to_dict(character)) == character


def test_a_rogues_expertise_survives_the_json_round_trip():
    character = fighter(
        character_class=CharacterClass.ROGUE,
        expertise={Skill.ATHLETICS},
    )

    assert character_from_dict(character_to_dict(character)) == character
