import pytest
from builders import fighter
from fakes import ScriptedChatModel, call, say
from langgraph.checkpoint.memory import InMemorySaver

from dungeon_core.agents.agent import AgentUnavailableError
from dungeon_core.agents.character_builder.factory import (
    CharacterBuilderFactory,
)
from dungeon_core.characters.adapters.json_repository import (
    JsonCharacterRepository,
)
from dungeon_core.characters.serializer import CharacterSerializer
from dungeon_core.characters.service import CharacterService
from dungeon_core.knowledge.ports.retriever import IndexNotBuiltError


class RecordingSheetWriter:
    def write(self, character, destination) -> None:
        destination.write_text(character.name)


class FakeRetriever:
    def __init__(self, error=None) -> None:
        self._error = error

    def check(self) -> None:
        if self._error:
            raise self._error

    def search(self, query, k):
        return []


class FakeModels:
    def __init__(self, model=None, error=None) -> None:
        self._model = model
        self._error = error

    def create(self):
        if self._error:
            raise self._error
        return self._model


class FakeKnowledge:
    def __init__(self, retriever) -> None:
        self._retriever = retriever

    def retriever(self, store):
        return self._retriever


def factory(tmp_path, model, retriever=None, models=None):
    return CharacterBuilderFactory(
        models or FakeModels(model),
        FakeKnowledge(retriever or FakeRetriever()),
        tmp_path / "chroma",
        CharacterService(
            JsonCharacterRepository(tmp_path), RecordingSheetWriter(), tmp_path
        ),
        InMemorySaver(),
    )


def fill():
    return call("set_fields", fields=CharacterSerializer.to_dict(fighter()))


def test_the_command_starts_a_builder(tmp_path):
    command = factory(tmp_path, ScriptedChatModel(replies=[])).command()

    assert command.name == "/char"
    assert command.start() is not None


def test_only_the_character_tools_reach_the_model(tmp_path):
    model = ScriptedChatModel(replies=[say("Hi")])

    factory(tmp_path, model).create().send("hello")

    assert set(model.tool_names) == {
        "search_rules",
        "set_fields",
        "get_character",
        "list_characters",
        "load_character",
        "save_character",
    }


def test_saving_asks_first_and_saves_on_yes(tmp_path):
    model = ScriptedChatModel(
        replies=[fill(), call("save_character"), say("All saved.")]
    )
    builder = factory(tmp_path, model).create()

    asked = builder.send("make me a fighter")
    done = builder.send("y")

    assert asked.text == f"Save {fighter().name}? [y/N]"
    assert not asked.finished
    assert done.text == "All saved."
    assert done.finished
    assert (tmp_path / f"{fighter().slug}.pdf").exists()
    assert builder.leave() == ""


def test_declining_saves_nothing_and_the_talk_goes_on(tmp_path):
    model = ScriptedChatModel(
        replies=[fill(), call("save_character"), say("Not saved then.")]
    )
    builder = factory(tmp_path, model).create()

    builder.send("make me a fighter")
    reply = builder.send("n")

    assert not reply.finished
    assert not (tmp_path / f"{fighter().slug}.json").exists()
    assert builder.leave() == "Unfinished Character discarded."


def test_leaving_at_the_question_says_not_saved(tmp_path):
    model = ScriptedChatModel(replies=[fill(), call("save_character")])
    builder = factory(tmp_path, model).create()

    builder.send("make me a fighter")

    assert builder.leave() == "Not saved."


def test_leaving_before_talking_says_nothing(tmp_path):
    builder = factory(tmp_path, ScriptedChatModel(replies=[])).create()

    assert builder.leave() == ""


def test_an_existing_name_asks_to_overwrite(tmp_path):
    JsonCharacterRepository(tmp_path).save(fighter())
    model = ScriptedChatModel(replies=[fill(), call("save_character")])
    builder = factory(tmp_path, model).create()

    asked = builder.send("make me a fighter")

    assert asked.text == f"{fighter().name} already exists. Overwrite? [y/N]"


def test_editing_a_saved_character_does_not_ask_to_overwrite(tmp_path):
    JsonCharacterRepository(tmp_path).save(fighter())
    model = ScriptedChatModel(
        replies=[
            call("load_character", name=fighter().name),
            call("save_character"),
        ]
    )
    builder = factory(tmp_path, model).create()

    asked = builder.send("edit it")

    assert asked.text == f"Save {fighter().name}? [y/N]"


def test_an_unbuilt_index_makes_the_agent_unavailable(tmp_path):
    retriever = FakeRetriever(IndexNotBuiltError("Run `dungeon build`."))

    with pytest.raises(AgentUnavailableError, match="dungeon build"):
        factory(tmp_path, ScriptedChatModel(replies=[]), retriever).create()


def test_a_model_that_cannot_be_built_makes_the_agent_unavailable(tmp_path):
    models = FakeModels(error=AgentUnavailableError("no key"))

    with pytest.raises(AgentUnavailableError, match="no key"):
        factory(tmp_path, None, models=models).create()
