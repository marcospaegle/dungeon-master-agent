import pytest

from dungeon.core import agent_factory
from dungeon.core.ports.agent import AgentUnavailableError

KEYS = {
    "ANTHROPIC_API_KEY": "anthropic-key",
    "GOOGLE_API_KEY": "google-key",
    "GOOGLE_EMBEDDING_MODEL": "embedding-model",
}


def create(tmp_path, environ):
    return agent_factory.create_agent_factory(tmp_path, environ)(None)


@pytest.fixture(autouse=True)
def fakes(monkeypatch):
    built = {}

    def fake_chat_anthropic(**kwargs):
        built["model"] = kwargs
        return object()

    monkeypatch.setattr(agent_factory, "ChatAnthropic", fake_chat_anthropic)
    monkeypatch.setattr(
        agent_factory, "create_retriever", lambda *args, **kwargs: object()
    )
    monkeypatch.setattr(
        agent_factory, "LangchainAgent", lambda *args: built.update(agent=args)
    )
    return built


def test_the_model_defaults_to_anthropic_claude_sonnet(tmp_path, fakes):
    create(tmp_path, KEYS)

    assert fakes["model"]["model"] == "claude-sonnet-5-5"
    assert fakes["model"]["api_key"] == "anthropic-key"


def test_the_model_is_chosen_by_environment(tmp_path, fakes):
    create(tmp_path, KEYS | {"DUNGEON_MODEL": "claude-haiku-4-5-20251001"})

    assert fakes["model"]["model"] == "claude-haiku-4-5-20251001"


@pytest.mark.parametrize(
    "missing",
    ["ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "GOOGLE_EMBEDDING_MODEL"],
)
def test_a_missing_variable_is_named(tmp_path, missing):
    environ = {k: v for k, v in KEYS.items() if k != missing}

    with pytest.raises(AgentUnavailableError, match=missing):
        create(tmp_path, environ)


def test_an_unknown_provider_lists_the_known_ones(tmp_path):
    with pytest.raises(AgentUnavailableError, match="anthropic"):
        create(tmp_path, KEYS | {"DUNGEON_PROVIDER": "nope"})
