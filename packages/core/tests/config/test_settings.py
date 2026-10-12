import pytest

from dungeon_core.config.settings import MissingSettingError, Settings


def test_reads_a_setting_from_the_environment():
    settings = Settings(
        {"GOOGLE_API_KEY": "key", "GOOGLE_EMBEDDING_MODEL": "model"}
    )

    assert settings.google_api_key == "key"
    assert settings.embedding_model == "model"


@pytest.mark.parametrize("value", [None, ""])
def test_a_missing_setting_only_fails_when_it_is_read(value):
    environ = {} if value is None else {"GOOGLE_API_KEY": value}
    settings = Settings(environ)

    with pytest.raises(MissingSettingError, match="GOOGLE_API_KEY"):
        settings.google_api_key


def test_provider_and_model_have_defaults_the_environment_overrides():
    assert Settings({}).provider == "anthropic"
    assert Settings({}).model == "claude-sonnet-5-5"
    overridden = Settings({"DUNGEON_PROVIDER": "p", "DUNGEON_MODEL": "m"})
    assert (overridden.provider, overridden.model) == ("p", "m")
