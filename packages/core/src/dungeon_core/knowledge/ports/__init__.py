"""Interfaces the core depends on.

Each step of the indexing pipeline, and the retriever that reads the
index, is a ``Protocol``, so implementations (LangChain's or ours, see
``knowledge.adapters``) satisfy it structurally and can be swapped
without touching their callers.
"""

from dungeon_core.knowledge.ports.loader import DocumentLoader
from dungeon_core.knowledge.ports.retriever import (
    IndexNotBuiltError,
    Retriever,
)
from dungeon_core.knowledge.ports.splitter import DocumentSplitter
from dungeon_core.knowledge.ports.vector_store import VectorStore

__all__ = [
    "DocumentLoader",
    "DocumentSplitter",
    "IndexNotBuiltError",
    "Retriever",
    "VectorStore",
]
