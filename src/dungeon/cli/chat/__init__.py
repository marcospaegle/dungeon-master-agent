import os
from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown

from dungeon.core.adapters.char_command import CharCommand
from dungeon.core.adapters.pypdf_sheet_writer import PypdfSheetWriter
from dungeon.core.agent_factory import create_agent_factory
from dungeon.core.character_store import CharacterStore

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
                CharacterStore(
                    STORAGE / "characters",
                    PypdfSheetWriter(
                        STORAGE / "assets" / "character_sheet.pdf"
                    ),
                ),
            )
        ],
    ).run()
