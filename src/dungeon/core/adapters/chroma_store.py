from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

COLLECTION = "dungeon"


def open_chroma(path: Path, embeddings: Embeddings) -> Chroma:
    """The Chroma collection indexing writes and retrieval reads."""

    return Chroma(
        collection_name=COLLECTION,
        persist_directory=str(path),
        embedding_function=embeddings,
    )


class ChromaStore:
    """Embeds Chunks and persists them in a local Chroma store.

    Chunks are stored under the IDs they are given, so adding an ID
    that is already stored replaces it.
    """

    def __init__(self, path: Path, embeddings: Embeddings) -> None:
        self._chroma = open_chroma(path, embeddings)

    def add(self, chunks: list[Document], ids: list[str]) -> None:
        self._chroma.add_documents(chunks, ids=ids)

    def existing_ids(self) -> set[str]:
        return set(self._chroma.get(include=[])["ids"])

    def clear(self) -> None:
        self._chroma.reset_collection()
