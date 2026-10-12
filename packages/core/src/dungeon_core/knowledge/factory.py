from pathlib import Path

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from dungeon_core.config.settings import Settings
from dungeon_core.knowledge.adapters.chroma_retriever import ChromaRetriever
from dungeon_core.knowledge.adapters.chroma_store import ChromaStore
from dungeon_core.knowledge.adapters.pdf_folder_loader import PdfFolderLoader
from dungeon_core.knowledge.adapters.recursive_splitter import (
    RecursiveSplitter,
)
from dungeon_core.knowledge.adapters.retrying_embeddings import (
    RetryingEmbeddings,
)
from dungeon_core.knowledge.indexing_service import IndexingService
from dungeon_core.knowledge.ports.retriever import Retriever


class KnowledgeFactory:
    """Assembles indexing and retrieval with their real adapters.

    Both use the same embedding model, which is a Rebuild trigger;
    only the task type differs, being specific to documents when
    indexing and to queries when retrieving.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def indexing_service(
        self, source_folder: Path, store: Path
    ) -> IndexingService:
        return IndexingService(
            PdfFolderLoader(source_folder),
            RecursiveSplitter(),
            ChromaStore(store, self._embeddings("RETRIEVAL_DOCUMENT")),
        )

    def retriever(self, store: Path) -> Retriever:
        return ChromaRetriever(store, self._embeddings("RETRIEVAL_QUERY"))

    def _embeddings(self, task_type: str) -> RetryingEmbeddings:
        return RetryingEmbeddings(
            GoogleGenerativeAIEmbeddings(
                model=self._settings.embedding_model,
                google_api_key=self._settings.google_api_key,
                task_type=task_type,
            )
        )
