from typing import Protocol

from langchain_core.documents import Document


class DocumentLoader(Protocol):
    """Reads raw documents from a source it was configured with."""

    def load(self) -> list[Document]: ...
