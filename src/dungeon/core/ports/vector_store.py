from typing import Protocol

from langchain_core.documents import Document


class VectorStore(Protocol):
    """Embeds chunks and persists them."""

    def add(self, chunks: list[Document]) -> None: ...
