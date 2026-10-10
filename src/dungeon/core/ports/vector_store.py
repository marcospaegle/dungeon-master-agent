from typing import Protocol

from langchain_core.documents import Document


class VectorStore(Protocol):
    """Embeds chunks and persists them under the IDs they are given."""

    def add(self, chunks: list[Document], ids: list[str]) -> None: ...

    def existing_ids(self) -> set[str]: ...

    def clear(self) -> None: ...
