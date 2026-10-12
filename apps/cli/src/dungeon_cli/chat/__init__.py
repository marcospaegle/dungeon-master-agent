import os
from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown

from dungeon_core.agents.character_builder.factory import create_agent_factory
from dungeon_core.characters.adapters.json_repository import (
    JsonCharacterRepository,
)
from dungeon_core.characters.adapters.pypdf_sheet_writer import (
    PypdfSheetWriter,
)
from dungeon_core.characters.service import CharacterService
from dungeon_core.chat.char_command import CharCommand

from .chat import Chat

app = typer.Typer()

STORAGE = Path("storage")


def _write(text: str) -> None:
    Console().print(Markdown(text))


def _read() -> str:
    try:
        return typer.prompt(
            ">", prompt_suffix=" ", default="", show_default=False
        )
    except typer.Abort:
        raise EOFError from None


@app.callback(invoke_without_command=True)
def chat():
    """Open a Chat."""

    load_dotenv()
    Chat(
        read=_read,
        write=_write,
        commands=[
            CharCommand(
                create_agent_factory(STORAGE / "chroma", os.environ),
                CharacterService(
                    JsonCharacterRepository(STORAGE / "characters"),
                    PypdfSheetWriter(
                        STORAGE / "assets" / "character_sheet.pdf"
                    ),
                    STORAGE / "characters",
                ),
            )
        ],
    ).run()
