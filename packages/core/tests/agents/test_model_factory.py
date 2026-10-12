import pytest

from dungeon_core.agents import model_factory
from dungeon_core.agents.agent import AgentUnavailableError
from dungeon_core.agents.model_factory import ModelFactory
from dungeon_core.config.settings import Settings


@pytest.fixture
def built(monkeypatch):
    calls = {}

    def fake_chat_anthropic(**kwargs):
        calls.update(kwargs)
        return object()

    monkeypatch.setattr(model_factory, "ChatAnthropic", fake_chat_anthropic)
    return calls


def test_the_model_defaults_to_anthropic_claude_sonnet(built):
    ModelFactory(Settings({"ANTHROPIC_API_KEY": "k"})).create()

    assert built == {"model": "claude-sonnet-5-5", "api_key": "k"}


def test_the_model_is_chosen_by_environment(built):
    ModelFactory(
        Settings({"ANTHROPIC_API_KEY": "k", "DUNGEON_MODEL": "other"})
    ).create()

    assert built["model"] == "other"


def test_a_missing_key_says_which(built):
    with pytest.raises(AgentUnavailableError, match="ANTHROPIC_API_KEY"):
        ModelFactory(Settings({})).create()


def test_an_unknown_provider_lists_the_known_ones(built):
    with pytest.raises(AgentUnavailableError, match="anthropic"):
        ModelFactory(Settings({"DUNGEON_PROVIDER": "nope"})).create()
