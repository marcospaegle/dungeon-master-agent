import json
import re
from importlib import resources
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, TextStringObject

from dungeon.core.character import (
    HIT_DIE,
    SAVING_THROW_PROFICIENCIES,
    Character,
)
from dungeon.core.ports.sheet_writer import SheetTemplateError

_TICKED = "/Yes"
_MULTILINE = 1 << 12  # the multiline bit of a text field's flags


def _signed(number: int) -> str:
    return f"{number:+d}"


def _autosize_single_line_fields(writer: PdfWriter) -> None:
    """Let viewers shrink long text to fit its box.

    The template fixes some fonts (Size at 18 pt, damage at 12 pt),
    which clips "Medium" and "1d8+3 Slashing". Font size 0 is "auto".
    """
    for page in writer.pages:
        for annotation in page.get("/Annots", []):
            widget = annotation.get_object()
            field = widget.get("/Parent", widget).get_object()
            if (
                field.get("/FT") != "/Tx"
                or field.get("/Ff", 0) & _MULTILINE
                or "/DA" not in field
            ):
                continue
            font = re.sub(r"(/\S+) [\d.]+ Tf", r"\1 0 Tf", field["/DA"])
            for target in (widget, field):
                target[NameObject("/DA")] = TextStringObject(font)


def _load_field_map() -> dict:
    data = resources.files(__package__) / "character_sheet_fields.json"
    return json.loads(data.read_text())


def _field_names(node) -> set[str]:
    """Every template field name the field map mentions."""
    if isinstance(node, str):
        return {node}
    children = node.values() if isinstance(node, dict) else node
    return set().union(*(_field_names(child) for child in children))


class PypdfSheetWriter:
    """Fills the AcroForm fields of a Character sheet template.

    The template's fields have opaque names, so a field map (a data
    file next to this module) says which field shows which value.
    """

    def __init__(self, template: Path):
        self._template = template
        self._fields = _load_field_map()
        self._check_template()

    def _check_template(self) -> None:
        present = PdfReader(self._template).get_fields() or {}
        missing = _field_names(self._fields) - present.keys()
        if missing:
            raise SheetTemplateError(
                f"{self._template} lacks the fields {sorted(missing)}; "
                "the field map no longer matches the template"
            )

    def write(self, character: Character, destination: Path) -> None:
        values = self._values(character)
        writer = PdfWriter(clone_from=self._template)
        _autosize_single_line_fields(writer)
        for page in writer.pages:
            writer.update_page_form_field_values(page, values)
        writer.write(destination)

    def _values(self, character: Character) -> dict[str, str]:
        fields = self._fields
        identity = fields["identity"]
        values = {
            identity["name"]: character.name,
            identity["background"]: character.background,
            identity["class"]: str(character.character_class),
            identity["species"]: character.species,
            identity["level"]: str(character.level),
            fields["proficiency_bonus"]: _signed(character.proficiency_bonus),
        }
        saves = character.saving_throws
        proficient = SAVING_THROW_PROFICIENCIES[character.character_class]
        for ability, score in character.ability_scores.items():
            field = fields["abilities"][ability]
            values[field["score"]] = str(score)
            values[field["modifier"]] = _signed(
                character.ability_modifiers[ability]
            )
            values[field["save"]] = _signed(saves[ability])
            if ability in proficient:
                values[field["save_proficient"]] = _TICKED
        trained = character.skill_proficiencies | character.expertise
        for skill, bonus in character.skill_bonuses.items():
            field = fields["skills"][skill]
            values[field["bonus"]] = _signed(bonus)
            if skill in trained:
                values[field["proficient"]] = _TICKED
        values.update(self._combat(character))
        values.update(self._attacks(character))
        values.update(self._text_blocks(character))
        return values

    def _attacks(self, character: Character) -> dict[str, str]:
        rows = self._fields["attacks"]
        if len(character.attacks) > len(rows):
            raise ValueError(
                f"The Character sheet has room for {len(rows)} attacks"
            )
        return {
            row[column]: text
            for row, attack in zip(rows, character.attacks)
            for column, text in attack._asdict().items()
        }

    def _text_blocks(self, character: Character) -> dict[str, str]:
        fields = self._fields["text_blocks"]
        story = "\n\n".join(
            part
            for part in (character.personality, character.backstory)
            if part
        )
        blocks = {
            "class_features": "\n".join(character.class_features),
            "species_traits": "\n".join(character.species_traits),
            "feats": "\n".join(character.feats),
            "weapon_proficiencies": ", ".join(character.weapon_proficiencies),
            "tool_proficiencies": ", ".join(character.tool_proficiencies),
            "appearance": character.appearance,
            "backstory_and_personality": story,
            "languages": ", ".join(character.languages),
            "equipment": "\n".join(character.equipment),
            "alignment": character.alignment,
        }
        return {fields[block]: text for block, text in blocks.items()}

    def _combat(self, character: Character) -> dict[str, str]:
        fields = self._fields["combat"]
        hit_die = HIT_DIE[character.character_class]
        values = {
            fields["armor_class"]: str(character.armor_class),
            fields["hp_current"]: str(character.hit_points),
            fields["hp_max"]: str(character.hit_points),
            fields["hit_dice_max"]: f"{character.level}d{hit_die}",
            fields["initiative"]: _signed(character.initiative),
            fields["speed"]: character.speed,
            fields["size"]: character.size,
            fields["passive_perception"]: str(character.passive_perception),
        }
        if character.shield:
            values[fields["shield"]] = _TICKED
        training = character.armor_training
        boxes = self._fields["armor_training"]
        for category in training.categories:
            values[boxes[category]] = _TICKED
        if training.shields:
            values[boxes["Shields"]] = _TICKED
        return values
