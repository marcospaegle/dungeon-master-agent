from pathlib import Path

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from dungeon.core.adapters.chroma_store import ChromaStore
from dungeon.core.adapters.pdf_folder_loader import PdfFolderLoader
from dungeon.core.adapters.recursive_splitter import RecursiveSplitter
from dungeon.core.adapters.retrying_embeddings import RetryingEmbeddings
from dungeon.core.indexing_service import IndexingService


def create_indexing_service(
    source_folder: Path,
    store: Path,
    embedding_model: str,
    api_key: str,
) -> IndexingService:
    """Assemble the indexing pipeline with its real adapters.

    The embedding model is a Rebuild trigger, so it is chosen here,
    once, for documents (the task type is specific to indexing).
    """

    embeddings = RetryingEmbeddings(
        GoogleGenerativeAIEmbeddings(
            model=embedding_model,
            google_api_key=api_key,
            task_type="RETRIEVAL_DOCUMENT",
        )
    )
    return IndexingService(
        PdfFolderLoader(source_folder),
        RecursiveSplitter(),
        ChromaStore(store, embeddings),
    )
