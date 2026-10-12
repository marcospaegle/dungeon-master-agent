"""The JSON form of a Character, the single source for its sheet."""

from dungeon_core.characters.character import (
    Ability,
    Armor,
    Attack,
    Character,
    CharacterClass,
    ScoreMethod,
    Skill,
)


class CharacterSerializer:
    """Converts a Character to and from its JSON-ready dict."""

    @staticmethod
    def to_dict(character: Character) -> dict:
        return {
            "name": character.name,
            "species": character.species,
            "background": character.background,
            "character_class": character.character_class.value,
            "score_method": character.score_method.value,
            "base_scores": {
                a.value: n for a, n in character.base_scores.items()
            },
            "background_increases": {
                a.value: n for a, n in character.background_increases.items()
            },
            "skill_proficiencies": sorted(character.skill_proficiencies),
            "expertise": sorted(character.expertise),
            "armor": character.armor.value if character.armor else None,
            "shield": character.shield,
            "equipment": list(character.equipment),
            "personality": character.personality,
            "backstory": character.backstory,
            "speed": character.speed,
            "size": character.size,
            "alignment": character.alignment,
            "appearance": character.appearance,
            "languages": list(character.languages),
            "attacks": [attack._asdict() for attack in character.attacks],
            "class_features": list(character.class_features),
            "species_traits": list(character.species_traits),
            "feats": list(character.feats),
            "weapon_proficiencies": list(character.weapon_proficiencies),
            "tool_proficiencies": list(character.tool_proficiencies),
        }

    @staticmethod
    def from_dict(data: dict) -> Character:
        data = dict(data)
        data["character_class"] = CharacterClass(data["character_class"])
        data["score_method"] = ScoreMethod(data["score_method"])
        for field in ("base_scores", "background_increases"):
            data[field] = {Ability(a): n for a, n in data[field].items()}
        for field in ("skill_proficiencies", "expertise"):
            data[field] = {Skill(s) for s in data.get(field, ())}
        if data.get("armor") is not None:
            data["armor"] = Armor(data["armor"])
        data["attacks"] = [Attack(**a) for a in data.get("attacks", ())]
        return Character(**data)
