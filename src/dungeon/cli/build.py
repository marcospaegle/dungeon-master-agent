import os
from pathlib import Path
from typing import Annotated

import typer

from dungeon.core.adapters.chroma_store import ChromaStore
from dungeon.core.adapters.gemini_embedder import GeminiEmbedder
from dungeon.core.adapters.pdf_folder_loader import PdfFolderLoader
from dungeon.core.adapters.recursive_splitter import RecursiveSplitter
from dungeon.core.indexing_service import IndexingService

app = typer.Typer()


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise typer.BadParameter(f"{name} is not set (environment or .env).")
    return value


@app.command()
def build(
    source: Annotated[
        Path, typer.Option(help="Folder with the PDFs to index.")
    ],
    store: Annotated[
        Path, typer.Option(help="Where the Chroma store lives.")
    ] = Path(".dungeon/chroma"),
):
    """Index the PDFs of a source folder into the vector store."""

    api_key = _require_env("GOOGLE_API_KEY")
    model = _require_env("GOOGLE_EMBEDDING_MODEL")

    service = IndexingService(
        PdfFolderLoader(source),
        RecursiveSplitter(),
        GeminiEmbedder(api_key, model),
        ChromaStore(store),
    )

    print(f"Indexed {service.index()} chunks.")
