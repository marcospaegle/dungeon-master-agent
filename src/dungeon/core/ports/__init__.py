"""Interfaces the indexing pipeline depends on.

Each step of the pipeline is a ``Protocol``, so implementations
(LangChain's or ours, see ``core.adapters``) satisfy it structurally
and can be swapped without touching ``IndexingService``.
"""

from dungeon.core.ports.loader import DocumentLoader
from dungeon.core.ports.splitter import DocumentSplitter
from dungeon.core.ports.vector_store import VectorStore

__all__ = ["DocumentLoader", "DocumentSplitter", "VectorStore"]
