import os
from pathlib import Path
from typing import Annotated

import typer
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from dungeon.core.adapters.chroma_store import ChromaStore
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
    source_folder: Annotated[
        Path, typer.Option(help="Folder with the PDFs to index.")
    ] = Path(".dungeon/books"),
    store: Annotated[
        Path, typer.Option(help="Where the Chroma store lives.")
    ] = Path(".dungeon/chroma"),
):
    """Index the PDFs of a source folder into the vector store."""

    load_dotenv()

    embeddings = GoogleGenerativeAIEmbeddings(
        model=_require_env("GOOGLE_EMBEDDING_MODEL"),
        google_api_key=_require_env("GOOGLE_API_KEY"),
        task_type="RETRIEVAL_DOCUMENT",
    )

    service = IndexingService(
        PdfFolderLoader(source_folder),
        RecursiveSplitter(),
        ChromaStore(store, embeddings),
    )

    print(f"Indexed {service.index()} chunks.")
