import logging
import os
import time
import warnings
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Annotated

import typer
from dotenv import load_dotenv
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
)

from dungeon.core.indexing_factory import create_indexing_service

app = typer.Typer()

LOG_FOLDER = Path("storage/logs")

logger = logging.getLogger("dungeon")


@contextmanager
def _log_to_file():
    """Write the run's INFO and above to today's log file."""

    LOG_FOLDER.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(
        LOG_FOLDER / f"build-{date.today():%Y-%m-%d}.log"
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    )
    level = logger.level
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    try:
        yield
    finally:
        logger.removeHandler(handler)
        logger.setLevel(level)
        handler.close()


@contextmanager
def _log_warnings():
    """Also write warnings to the log, keeping the console output."""

    console_showwarning = warnings.showwarning

    def showwarning(message, category, filename, lineno, *args, **kwargs):
        logger.warning("%s: %s", category.__name__, message)
        console_showwarning(
            message, category, filename, lineno, *args, **kwargs
        )

    warnings.showwarning = showwarning
    try:
        yield
    finally:
        warnings.showwarning = console_showwarning


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise typer.BadParameter(f"{name} is not set (environment or .env).")
    return value


def _format_elapsed(seconds: float) -> str:
    minutes, seconds = divmod(round(seconds), 60)
    return f"{minutes}m {seconds}s" if minutes else f"{seconds}s"


@app.command()
def build(
    source_folder: Annotated[
        Path, typer.Option(help="Folder with the PDFs to index.")
    ] = Path("storage/books"),
    store: Annotated[
        Path, typer.Option(help="Where the Chroma store lives.")
    ] = Path("storage/chroma"),
    rebuild: Annotated[
        bool,
        typer.Option(
            help="Empty the store and index everything again. Needed "
            "after changing the PDFs, the chunking or the embedding "
            "model; without it, only chunks not yet stored are added."
        ),
    ] = False,
):
    """Index the PDFs of a source folder into the vector store.

    An interrupted run can be resumed by running the command again.
    """

    with _log_to_file():
        try:
            with _log_warnings():
                load_dotenv()

                service = create_indexing_service(
                    source_folder,
                    store,
                    embedding_model=_require_env("GOOGLE_EMBEDDING_MODEL"),
                    api_key=_require_env("GOOGLE_API_KEY"),
                )

                started = time.monotonic()
                with Progress(
                    TextColumn("Indexing"),
                    BarColumn(),
                    MofNCompleteColumn(),
                    TimeRemainingColumn(),
                    transient=True,
                ) as progress:
                    task = progress.add_task("", total=None)

                    def on_progress(done: int, todo: int) -> None:
                        progress.update(task, completed=done, total=todo)

                    result = service.index(rebuild, on_progress)

                summary = (
                    f"Added {result.added} of {result.total} chunks "
                    f"in {_format_elapsed(time.monotonic() - started)}."
                )
                logger.info(summary)
                print(summary)
        except Exception:
            logger.exception("dungeon build failed")
            raise
