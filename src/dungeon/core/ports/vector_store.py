from typing import Protocol

from langchain_core.documents import Document


class VectorStore(Protocol):
    """Persists documents together with their embeddings."""

    def add(
        self,
        documents: list[Document],
        embeddings: list[list[float]],
    ) -> None: ...
