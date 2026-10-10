import os
from pathlib import Path

import pytest
from dotenv import dotenv_values

from dungeon.core.agent_factory import create_agent_factory

ENVIRON = {**dotenv_values(), **os.environ}
INDEX = Path("storage/chroma")

# Opt-in: needs real keys and a built index, and costs a few cents.
pytestmark = pytest.mark.skipif(
    not (
        ENVIRON.get("ANTHROPIC_API_KEY")
        and ENVIRON.get("GOOGLE_API_KEY")
        and INDEX.is_dir()
    ),
    reason="needs ANTHROPIC_API_KEY, GOOGLE_API_KEY and a built index",
)


def test_the_live_agent_answers_a_character_question():
    agent = create_agent_factory(INDEX, ENVIRON)(None)

    reply = agent.reply("Which armor can a Fighter wear at level 1?")

    assert reply.text
    assert reply.finished is None
