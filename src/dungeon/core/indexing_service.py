from dungeon.core.ports import (
    DocumentLoader,
    DocumentSplitter,
    Embedder,
    VectorStore,
)


class IndexingService:
    """Builds the RAG index: load, split, embed, store."""

    def __init__(
        self,
        loader: DocumentLoader,
        splitter: DocumentSplitter,
        embedder: Embedder,
        store: VectorStore,
    ) -> None:
        self._loader = loader
        self._splitter = splitter
        self._embedder = embedder
        self._store = store

    def index(self) -> int:
        """Run the pipeline and return the number of chunks stored."""
        documents = self._loader.load()
        chunks = self._splitter.split(documents)
        embeddings = self._embedder.embed(
            [chunk.page_content for chunk in chunks]
        )
        self._store.add(chunks, embeddings)
        return len(chunks)
