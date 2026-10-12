from builders import fighter

from dungeon_core.characters.adapters.json_repository import (
    JsonCharacterRepository,
)


def test_saves_and_lists_characters_sorted_by_name(tmp_path):
    repository = JsonCharacterRepository(tmp_path / "characters")
    repository.save(fighter(name="Zed"))
    repository.save(fighter(name="alma"))

    assert [c.name for c in repository.saved()] == ["alma", "Zed"]


def test_save_returns_the_character_as_read_back(tmp_path):
    repository = JsonCharacterRepository(tmp_path)
    character = fighter()

    assert repository.save(character) == character


def test_exists_matches_the_file_name_of_the_character(tmp_path):
    repository = JsonCharacterRepository(tmp_path)
    repository.save(fighter(name="Thorin Oakenshield"))

    assert repository.exists(fighter(name="thorin  oakenshield!"))
    assert not repository.exists(fighter(name="Balin"))


def test_a_file_that_is_not_a_character_is_skipped(tmp_path):
    repository = JsonCharacterRepository(tmp_path)
    repository.save(fighter())
    (tmp_path / "stray.json").write_text('{"hello": 1}')

    assert [c.name for c in repository.saved()] == [fighter().name]
