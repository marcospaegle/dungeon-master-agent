from typing import Protocol

from langchain_core.documents import Document


class IndexNotBuiltError(Exception):
    """There is no indexed Chunk to retrieve from."""


class Retriever(Protocol):
    """Finds the Chunks closest in meaning to a query.

    Each Chunk carries the Source and Page it came from.
    """

    def search(self, query: str, k: int) -> list[Document]: ...
