from dungeon.core.ports import (
    DocumentLoader,
    DocumentSplitter,
    VectorStore,
)


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

    def index(self) -> int:
        """Run the pipeline and return the number of chunks stored."""

        chunks = self._splitter.split(self._loader.load())

        if not chunks:
            return 0

        self._store.add(chunks)

        return len(chunks)
