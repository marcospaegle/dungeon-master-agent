from pathlib import Path

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from dungeon.core.adapters.chroma_store import open_chroma
from dungeon.core.ports.retriever import IndexNotBuiltError

NOT_BUILT = "Nothing is indexed yet. Run `dungeon build` first."


class ChromaRetriever:
    """Finds Chunks in the local Chroma store that indexing filled.

    The embeddings must be the model the index was built with.
    """

    def __init__(self, path: Path, embeddings: Embeddings) -> None:
        self._path = path
        self._embeddings = embeddings

    def search(self, query: str, k: int) -> list[Document]:
        # Opening Chroma creates the folder, so check before that.
        if not self._path.is_dir():
            raise IndexNotBuiltError(NOT_BUILT)

        chroma = open_chroma(self._path, self._embeddings)
        if not chroma.get(limit=1)["ids"]:
            raise IndexNotBuiltError(NOT_BUILT)

        return chroma.similarity_search(query, k=k)
