from collections import defaultdict
from pathlib import Path

import chromadb
from langchain_core.documents import Document

COLLECTION = "dungeon"


class ChromaStore:
    """Persists Chunks and their embeddings in a local Chroma store.

    Adding replaces: everything already stored for a Source in the
    batch is deleted first, then the batch is upserted under IDs of
    the form ``<source>#<page>#<chunk-index>``.
    """

    def __init__(self, path: Path) -> None:
        client = chromadb.PersistentClient(path=str(path))
        self._collection = client.get_or_create_collection(COLLECTION)

    def add(
        self,
        documents: list[Document],
        embeddings: list[list[float]],
    ) -> None:
        if not documents:
            return

        for source in {doc.metadata["source"] for doc in documents}:
            self._collection.delete(where={"source": source})

        counts: defaultdict[tuple, int] = defaultdict(int)
        ids = []

        for doc in documents:
            key = (doc.metadata["source"], doc.metadata["page"])
            ids.append(f"{key[0]}#{key[1]}#{counts[key]}")
            counts[key] += 1

        self._collection.upsert(
            ids=ids,
            documents=[doc.page_content for doc in documents],
            embeddings=embeddings,
            metadatas=[doc.metadata for doc in documents],
        )

    def count(self) -> int:
        return self._collection.count()
