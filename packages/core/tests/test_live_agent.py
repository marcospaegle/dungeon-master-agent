import os
from pathlib import Path

import pytest
from dotenv import dotenv_values

from dungeon_core.agents.character_builder.factory import create_agent_factory

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


def test_the_live_agent_answers_a_character_question():
    agent = create_agent_factory(INDEX, ENVIRON)(None)

    reply = agent.reply("Which armor can a Fighter wear at level 1?")

    assert reply.text
    assert reply.finished is None
