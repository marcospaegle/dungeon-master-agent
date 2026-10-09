"""Interfaces the indexing pipeline depends on.

Each step of the pipeline is a ``Protocol``, so implementations
(LangChain's or ours) satisfy it structurally and can be swapped
without touching ``IndexingService``.
"""

from typing import Protocol

from langchain_core.documents import Document


class DocumentLoader(Protocol):
    """Reads raw documents from a source it was configured with."""

    def load(self) -> list[Document]: ...


class DocumentSplitter(Protocol):
    """Breaks documents into chunks small enough to embed."""

    def split(self, documents: list[Document]) -> list[Document]: ...


class Embedder(Protocol):
    """Turns text into vectors."""

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class VectorStore(Protocol):
    """Persists documents together with their embeddings."""

    def add(
        self,
        documents: list[Document],
        embeddings: list[list[float]],
    ) -> None: ...
