from typing import Protocol

from langchain_core.documents import Document


class DocumentSplitter(Protocol):
    """Breaks documents into chunks small enough to embed."""

    def split(self, documents: list[Document]) -> list[Document]: ...
