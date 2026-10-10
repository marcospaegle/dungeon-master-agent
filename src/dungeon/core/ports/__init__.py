"""Interfaces the core depends on.

Each step of the indexing pipeline, and the retriever that reads the
index, is a ``Protocol``, so implementations (LangChain's or ours, see
``core.adapters``) satisfy it structurally and can be swapped without
touching their callers.
"""

from dungeon.core.ports.loader import DocumentLoader
from dungeon.core.ports.retriever import IndexNotBuiltError, Retriever
from dungeon.core.ports.splitter import DocumentSplitter
from dungeon.core.ports.vector_store import VectorStore

__all__ = [
    "DocumentLoader",
    "DocumentSplitter",
    "IndexNotBuiltError",
    "Retriever",
    "VectorStore",
]
