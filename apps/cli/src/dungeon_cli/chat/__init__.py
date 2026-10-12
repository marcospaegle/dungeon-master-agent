import os
from pathlib import Path

import typer
from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver
from rich.console import Console
from rich.markdown import Markdown
from rich.rule import Rule

from dungeon_core.agents.agent import AgentReply
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
from dungeon_core.chat.chat import Chat
from dungeon_core.config.settings import Settings
from dungeon_core.knowledge.factory import KnowledgeFactory

from .terminal import Terminal

app = typer.Typer()

STORAGE = Path("storage")
LABEL = "Dungeon Master"
PROMPT = typer.style("You ›", fg=typer.colors.CYAN, bold=True)

console = Console()


class PlaceholderConcierge:
    """Stands in for the Concierge until it is built."""

    def send(self, text: str) -> AgentReply:
        return AgentReply("The Concierge is not built yet.")

    def leave(self) -> str:
        return ""


def _write(text: str) -> None:
    console.print(Rule(LABEL, style="dim", align="left"))
    console.print(Markdown(text))
    console.print()


def _busy():
    return console.status("Thinking…")


def _read() -> str:
    try:
        return typer.prompt(
            PROMPT, prompt_suffix=" ", default="", show_default=False
        )
    except typer.Abort:
        raise EOFError from None


@app.callback(invoke_without_command=True)
def chat():
    """Open a Chat."""

    load_dotenv()
    settings = Settings(os.environ)
    characters = CharacterService(
        JsonCharacterRepository(STORAGE / "characters"),
        PypdfSheetWriter(STORAGE / "assets" / "character_sheet.pdf"),
        STORAGE / "characters",
    )
    builder = CharacterBuilderFactory(
        ModelFactory(settings),
        KnowledgeFactory(settings),
        STORAGE / "chroma",
        characters,
        InMemorySaver(),
    )
    conversation = Chat(PlaceholderConcierge(), [builder.specialist()])
    Terminal(conversation, _read, _write, _busy).run()
