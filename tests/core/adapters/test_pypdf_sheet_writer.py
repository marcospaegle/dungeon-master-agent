import json
from importlib import resources
from pathlib import Path

import pytest
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, TextStringObject

from dungeon.core.adapters.pypdf_sheet_writer import PypdfSheetWriter
from dungeon.core.character import (
    Ability,
    Armor,
    Attack,
    Character,
    CharacterClass,
    ScoreMethod,
    Skill,
)
from dungeon.core.ports.sheet_writer import SheetTemplateError

STR, DEX, CON, INT, WIS, CHA = Ability

TEMPLATE = (
    Path(__file__).parents[3] / "storage" / "assets" / "character_sheet.pdf"
)

# The template lives in the gitignored storage folder, so a fresh clone
# does not have it.
pytestmark = pytest.mark.skipif(
    not TEMPLATE.exists(), reason=f"no Character sheet at {TEMPLATE}"
)


def brannoch(**overrides) -> Character:
    """A level 1 Soldier Fighter on the standard array.

    Final scores are 17/14/14/8/10/12 for Str/Dex/Con/Int/Wis/Cha.
    """
    fields = dict(
        name="Brannoch",
        species="Human",
        background="Soldier",
        character_class=CharacterClass.FIGHTER,
        score_method=ScoreMethod.STANDARD_ARRAY,
        base_scores={STR: 15, DEX: 14, CON: 13, INT: 8, WIS: 10, CHA: 12},
        background_increases={STR: 2, CON: 1},
        skill_proficiencies={
            Skill.ATHLETICS,
            Skill.INTIMIDATION,
            Skill.PERCEPTION,
            Skill.SURVIVAL,
        },
        armor=Armor.CHAIN_MAIL,
        shield=True,
    )
    return Character(**{**fields, **overrides})


def filled(tmp_path: Path, character: Character) -> dict[str, str]:
    """Write the Character and read every field value back."""
    destination = tmp_path / "sheet.pdf"
    PypdfSheetWriter(TEMPLATE).write(character, destination)
    fields = PdfReader(destination).get_fields()
    return {name: field.get("/V") for name, field in fields.items()}


def lines(value: str) -> list[str]:
    return value.replace("\r\n", "\n").replace("\r", "\n").split("\n")


def widgets(reader: PdfReader) -> dict:
    """Each field's widget annotation, by field name."""
    found = {}
    for page in reader.pages:
        for annotation in page["/Annots"]:
            widget = annotation.get_object()
            field = widget.get("/Parent", widget).get_object()
            found[field["/T"]] = widget
    return found


def ticked(values: dict, name: str) -> bool:
    return values[name] == "/Yes"


def test_writes_who_the_character_is(tmp_path):
    values = filled(tmp_path, brannoch())

    assert values["Text1"] == "Brannoch"
    assert values["Text6"] == "Soldier"
    assert values["Text7"] == "Fighter"
    assert values["Text8"] == "Human"
    assert values["Text11"] == "1"


def test_writes_ability_scores_modifiers_and_saving_throws(tmp_path):
    values = filled(tmp_path, brannoch())

    assert values["Text19"] == "+2"
    # (score field, modifier field, saving throw field, proficient box)
    abilities = {
        STR: ("Text64", "Text21", "Text91", "Check Box37"),
        DEX: ("Text66", "Text22", "Text87", "Check Box33"),
        CON: ("Text67", "Text24", "Text86", "Check Box32"),
        INT: ("Text63", "Text20", "Text69", "Check Box4"),
        WIS: ("Text65", "Text23", "Text75", "Check Box21"),
        CHA: ("Text68", "Text25", "Text81", "Check Box26"),
    }
    # score, modifier, saving throw, proficient (Fighter: Str and Con)
    expected = {
        STR: ("17", "+3", "+5", True),
        DEX: ("14", "+2", "+2", False),
        CON: ("14", "+2", "+4", True),
        INT: ("8", "-1", "-1", False),
        WIS: ("10", "+0", "+0", False),
        CHA: ("12", "+1", "+1", False),
    }
    for ability, (score, mod, save, box) in abilities.items():
        want_score, want_mod, want_save, proficient = expected[ability]
        assert values[score] == want_score, ability
        assert values[mod] == want_mod, ability
        assert values[save] == want_save, ability
        assert ticked(values, box) is proficient, ability


def test_writes_every_skill_bonus_and_proficiency(tmp_path):
    values = filled(tmp_path, brannoch())

    # skill: (bonus field, proficient box, bonus, proficient)
    skills = {
        Skill.ACROBATICS: ("Text88", "Check Box34", "+2", False),
        Skill.ANIMAL_HANDLING: ("Text76", "Check Box22", "+0", False),
        Skill.ARCANA: ("Text70", "Check Box16", "-1", False),
        Skill.ATHLETICS: ("Text92", "Check Box38", "+5", True),
        Skill.DECEPTION: ("Text82", "Check Box27", "+1", False),
        Skill.HISTORY: ("Text71", "Check Box17", "-1", False),
        Skill.INSIGHT: ("Text77", "Check Box23", "+0", False),
        Skill.INTIMIDATION: ("Text83", "Check Box28", "+3", True),
        Skill.INVESTIGATION: ("Text72", "Check Box19", "-1", False),
        Skill.MEDICINE: ("Text78", "Check Box25", "+0", False),
        Skill.NATURE: ("Text73", "Check Box20", "-1", False),
        Skill.PERCEPTION: ("Text79", "Check Box31", "+2", True),
        Skill.PERFORMANCE: ("Text84", "Check Box30", "+1", False),
        Skill.PERSUASION: ("Text85", "Check Box29", "+1", False),
        Skill.RELIGION: ("Text74", "Check Box18", "-1", False),
        Skill.SLEIGHT_OF_HAND: ("Text89", "Check Box35", "+2", False),
        Skill.STEALTH: ("Text90", "Check Box36", "+2", False),
        Skill.SURVIVAL: ("Text80", "Check Box24", "+2", True),
    }
    assert set(skills) == set(Skill)
    for skill, (bonus, box, want_bonus, proficient) in skills.items():
        assert values[bonus] == want_bonus, skill
        assert ticked(values, box) is proficient, skill


def test_writes_the_combat_numbers(tmp_path):
    values = filled(tmp_path, brannoch(speed="30 ft.", size="Medium"))

    assert values["Text13"] == "18"  # chain mail 16 + shield 2
    assert ticked(values, "Check Box3")  # shield
    assert values["Text14"] == "12"  # current: d10 + Con +2, at full
    assert values["Text16"] == "12"  # max
    assert values["Text17"] == "1d10"  # hit dice
    assert values["Text26"] == "+2"  # initiative
    assert values["Text27"] == "30 ft."  # speed
    assert values["Text28"] == "Medium"  # size
    assert values["Text29"] == "12"  # passive Perception: 10 + 2


def test_ticks_the_armor_training_of_the_class(tmp_path):
    fighter = filled(tmp_path, brannoch())
    wizard = filled(
        tmp_path,
        brannoch(
            character_class=CharacterClass.WIZARD, armor=None, shield=False
        ),
    )

    # light, medium, heavy armor and shields
    boxes = ("Check Box13", "Check Box14", "Check Box15", "Check Box12")
    assert [ticked(fighter, box) for box in boxes] == [True] * 4
    assert [ticked(wizard, box) for box in boxes] == [False] * 4
    assert not ticked(wizard, "Check Box3")  # no shield


def test_writes_the_text_blocks_on_both_pages(tmp_path):
    character = brannoch(
        attacks=(Attack("Longsword", "+5", "1d8+3 Slashing", "Versatile"),),
        class_features=("Fighting Style: Defense", "Second Wind"),
        species_traits=("Resourceful", "Skillful"),
        feats=("Savage Attacker",),
        weapon_proficiencies=("Simple", "Martial"),
        tool_proficiencies=("Dice set",),
        equipment=("Chain Mail", "Shield", "Longsword"),
        languages=("Common", "Dwarvish"),
        alignment="Lawful Good",
        appearance="Scarred, grey-eyed, with a braided beard.",
        personality="Blunt but loyal.",
        backstory="A sergeant who left the legion.",
    )

    values = filled(tmp_path, character)

    # first attack row: name, bonus, damage and type, notes
    assert [values[f"Text{n}"] for n in (30, 31, 32, 33)] == [
        "Longsword",
        "+5",
        "1d8+3 Slashing",
        "Versatile",
    ]
    assert values["Text34"] in (None, "")  # the second row stays empty
    assert lines(values["Text54"]) == [
        "Fighting Style: Defense",
        "Second Wind",
    ]
    assert lines(values["Text57"]) == ["Resourceful", "Skillful"]
    assert lines(values["Text58"]) == ["Savage Attacker"]
    assert values["Text59"] == "Simple, Martial"
    assert values["Text60"] == "Dice set"
    # page 2
    assert lines(values["Text99"]) == ["Chain Mail", "Shield", "Longsword"]
    assert values["Text98"] == "Common, Dwarvish"
    assert values["Text100"] == "Lawful Good"
    assert values["Text96"] == "Scarred, grey-eyed, with a braided beard."
    assert lines(values["Text97"]) == [
        "Blunt but loyal.",
        "",
        "A sergeant who left the legion.",
    ]


def test_refuses_more_attacks_than_the_sheet_has_rows(tmp_path):
    attacks = tuple(Attack(f"Dagger {n}", "+4", "1d4+2", "") for n in range(7))

    with pytest.raises(ValueError, match="6 attacks"):
        filled(tmp_path, brannoch(attacks=attacks))


def test_refuses_a_template_that_lost_a_mapped_field(tmp_path):
    changed = tmp_path / "changed.pdf"
    writer = PdfWriter(clone_from=TEMPLATE)
    for annotation in writer.pages[0]["/Annots"]:
        widget = annotation.get_object()
        field = widget if "/T" in widget else widget["/Parent"].get_object()
        if field["/T"] == "Text1":  # the character name
            field[NameObject("/T")] = TextStringObject("Renamed")
    writer.write(changed)

    with pytest.raises(SheetTemplateError, match="Text1"):
        PypdfSheetWriter(changed)


def test_refuses_a_pdf_that_has_no_form(tmp_path):
    blank = tmp_path / "blank.pdf"
    writer = PdfWriter()
    writer.add_blank_page(612, 792)
    writer.write(blank)

    with pytest.raises(SheetTemplateError):
        PypdfSheetWriter(blank)


def test_saved_sheet_shows_its_values_in_a_viewer(tmp_path):
    destination = tmp_path / "sheet.pdf"
    PypdfSheetWriter(TEMPLATE).write(brannoch(), destination)

    reader = PdfReader(destination)

    form = reader.trailer["/Root"]["/AcroForm"]
    assert form["/NeedAppearances"].value is True  # viewers redraw
    by_name = widgets(reader)
    name_drawing = by_name["Text1"]["/AP"]["/N"].get_object().get_data()
    assert b"Brannoch" in name_drawing  # drawn for viewers that skip it
    assert by_name["Check Box3"]["/AS"] == "/Yes"  # shield shown ticked


def test_single_line_fields_shrink_long_text_to_fit(tmp_path):
    destination = tmp_path / "sheet.pdf"
    PypdfSheetWriter(TEMPLATE).write(brannoch(), destination)

    fields = widgets(PdfReader(destination))

    # The template fixes Size at 18 pt and damage at 12 pt, which clips
    # "Medium" and "1d8+3 Slashing"; size 0 lets the viewer fit them.
    assert " 0 Tf" in fields["Text28"]["/DA"]  # size
    assert " 0 Tf" in fields["Text32"]["/DA"]  # damage and type
    assert " 10 Tf" in fields["Text54"]["/DA"]  # multiline block unchanged


def mapped_field_names() -> set[str]:
    data = resources.files("dungeon.core.adapters")
    fields = json.loads((data / "character_sheet_fields.json").read_text())

    def names(node) -> set[str]:
        if isinstance(node, str):
            return {node}
        children = node.values() if isinstance(node, dict) else node
        return set().union(*(names(child) for child in children))

    return names(fields)


def test_every_mapped_text_field_is_written(tmp_path):
    character = brannoch(
        speed="30 ft.",
        size="Medium",
        alignment="Lawful Good",
        appearance="Scarred.",
        personality="Blunt.",
        backstory="A sergeant.",
        languages=("Common",),
        attacks=tuple(
            Attack(f"Dagger {n}", "+4", "1d4+2", "") for n in range(6)
        ),
        class_features=("Second Wind",),
        species_traits=("Resourceful",),
        feats=("Savage Attacker",),
        weapon_proficiencies=("Martial",),
        tool_proficiencies=("Dice set",),
        equipment=("Longsword",),
    )

    values = filled(tmp_path, character)

    kinds = {
        name: field.get("/FT")
        for name, field in PdfReader(TEMPLATE).get_fields().items()
    }
    text_fields = {n for n in mapped_field_names() if kinds[n] == "/Tx"}
    blank = {n for n in text_fields if not values.get(n)}
    # an attack's notes are legitimately empty in this sample
    assert blank == {
        "Text33",
        "Text37",
        "Text41",
        "Text45",
        "Text49",
        "Text53",
    }
