from fakes import ScriptedChatModel, call, say
from langgraph.checkpoint.memory import InMemorySaver

from dungeon_core.agents.character_builder.factory import (
    CharacterBuilderFactory,
)
from dungeon_core.agents.concierge.factory import ConciergeFactory
from dungeon_core.characters.adapters.json_repository import (
    JsonCharacterRepository,
)
from dungeon_core.characters.service import CharacterService
from dungeon_core.chat.chat import Chat
from dungeon_core.knowledge.ports.retriever import IndexNotBuiltError


class Models:
    def __init__(self, model) -> None:
        self._model = model

    def create(self):
        return self._model


class MissingIndex:
    def check(self) -> None:
        raise IndexNotBuiltError("Build the index first.")


class Knowledge:
    def retriever(self, store):
        return MissingIndex()


class NoSheets:
    def write(self, character, destination) -> None:
        raise AssertionError("no sheet should be written")


def test_a_missing_index_is_shown_and_the_concierge_knows_it_failed(
    tmp_path,
):
    concierge_model = ScriptedChatModel(
        replies=[
            call(
                "hand_off",
                specialist="character-builder",
                brief="a new character",
            ),
            say("On it."),
            say("The index is not built; build it first."),
        ]
    )
    saver = InMemorySaver()
    builder = CharacterBuilderFactory(
        Models(ScriptedChatModel(replies=[])),
        Knowledge(),
        tmp_path / "chroma",
        CharacterService(
            JsonCharacterRepository(tmp_path), NoSheets(), tmp_path
        ),
        saver,
    )
    specialists = [builder.specialist()]
    chat = Chat(
        ConciergeFactory(
            Models(concierge_model),
            specialists,
            Knowledge(),
            tmp_path / "chroma",
            saver,
        ).create(),
        specialists,
    )

    shown = chat.send("create a character")
    chat.send("why did that not work?")

    assert shown.text == "Build the index first."
    assert not shown.active
    heard = concierge_model.seen_messages[-1].content
    assert "character-builder could not start: Build the index first." in heard
    assert heard.endswith("why did that not work?")
