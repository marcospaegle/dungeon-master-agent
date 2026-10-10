from collections import defaultdict
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from dungeon.core.metadata import PAGE, SOURCE

COLLECTION = "dungeon"


def _chunk_ids(chunks: list[Document]) -> list[str]:
    """IDs of the form ``<source>#<page>#<chunk-index>``."""
    counts: defaultdict[tuple, int] = defaultdict(int)
    ids = []

    for chunk in chunks:
        key = (chunk.metadata[SOURCE], chunk.metadata[PAGE])
        ids.append(f"{key[0]}#{key[1]}#{counts[key]}")
        counts[key] += 1

    return ids


class ChromaStore:
    """Embeds Chunks and persists them in a local Chroma store.

    Adding replaces: everything already stored for a Source in the
    batch is deleted first, then the batch is upserted.
    """

    def __init__(self, path: Path, embeddings: Embeddings) -> None:
        self._chroma = Chroma(
            collection_name=COLLECTION,
            persist_directory=str(path),
            embedding_function=embeddings,
        )

    def add(self, chunks: list[Document]) -> None:
        for source in {chunk.metadata[SOURCE] for chunk in chunks}:
            self._chroma.delete(where={SOURCE: source})

        self._chroma.add_documents(chunks, ids=_chunk_ids(chunks))
