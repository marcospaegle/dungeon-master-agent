import os
from pathlib import Path

import pytest
from dotenv import dotenv_values
from langgraph.checkpoint.memory import InMemorySaver

from dungeon_core.agents.character_builder.factory import (
    CharacterBuilderFactory,
)
from dungeon_core.agents.model_factory import ModelFactory
from dungeon_core.characters.adapters.json_repository import (
    JsonCharacterRepository,
)
from dungeon_core.characters.adapters.pypdf_sheet_writer import (
    PypdfSheetWriter,
)
from dungeon_core.characters.service import CharacterService
from dungeon_core.config.settings import Settings
from dungeon_core.knowledge.factory import KnowledgeFactory

ENVIRON = {**dotenv_values(), **os.environ}
INDEX = Path("storage/chroma")

# Opt-in with DUNGEON_LIVE=1: needs real keys and a built index, and
# costs a few cents.
pytestmark = pytest.mark.skipif(
    not (
        ENVIRON.get("DUNGEON_LIVE") == "1"
        and ENVIRON.get("ANTHROPIC_API_KEY")
        and ENVIRON.get("GOOGLE_API_KEY")
        and INDEX.is_dir()
    ),
    reason="set DUNGEON_LIVE=1, both API keys and build the index",
)


def test_the_live_agent_answers_a_character_question(tmp_path):
    settings = Settings(ENVIRON)
    characters = CharacterService(
        JsonCharacterRepository(tmp_path),
        PypdfSheetWriter(Path("storage/assets/character_sheet.pdf")),
        tmp_path,
    )
    builder = CharacterBuilderFactory(
        ModelFactory(settings),
        KnowledgeFactory(settings),
        INDEX,
        characters,
        InMemorySaver(),
    ).create()

    reply = builder.send("Which armor can a Fighter wear at level 1?")

    assert reply.text
