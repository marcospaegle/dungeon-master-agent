import logging
from collections.abc import Callable
from dataclasses import dataclass

from dungeon.core.chunk_ids import chunk_ids
from dungeon.core.ports import (
    DocumentLoader,
    DocumentSplitter,
    VectorStore,
)

logger = logging.getLogger(__name__)

BATCH_SIZE = 100


@dataclass(frozen=True)
class IndexResult:
    """What a run did: chunks the Sources have, and chunks it added."""

    total: int
    added: int


class IndexingService:
    """Builds the RAG index: load, split, store (embedding included)."""

    def __init__(
        self,
        loader: DocumentLoader,
        splitter: DocumentSplitter,
        store: VectorStore,
    ) -> None:
        self._loader = loader
        self._splitter = splitter
        self._store = store

    def index(
        self,
        rebuild: bool = False,
        on_progress: Callable[[int, int], None] | None = None,
    ) -> IndexResult:
        """Run the pipeline, storing the chunks in batches.

        Chunks already stored are skipped, so rerunning after an
        interruption only adds what is missing. A rebuild empties the
        store first and adds everything. ``on_progress(done, todo)``
        is called after each batch is stored.
        """

        chunks = self._splitter.split(self._loader.load())

        if not chunks:
            return IndexResult(total=0, added=0)

        if rebuild:
            self._store.clear()

        ids = chunk_ids(chunks)
        stored = self._store.existing_ids()
        todo = [
            (chunk, id_)
            for chunk, id_ in zip(chunks, ids, strict=True)
            if id_ not in stored
        ]

        logger.info(
            "%d chunks, %d already stored, %d to add",
            len(chunks),
            len(chunks) - len(todo),
            len(todo),
        )

        for start in range(0, len(todo), BATCH_SIZE):
            batch = todo[start : start + BATCH_SIZE]
            self._store.add([c for c, _ in batch], [i for _, i in batch])

            logger.info(
                "Stored %d of %d chunks", start + len(batch), len(todo)
            )

            if on_progress:
                on_progress(start + len(batch), len(todo))

        return IndexResult(total=len(chunks), added=len(todo))
