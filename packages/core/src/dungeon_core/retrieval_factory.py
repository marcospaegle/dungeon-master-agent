from pathlib import Path

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from dungeon_core.adapters.chroma_retriever import ChromaRetriever
from dungeon_core.adapters.retrying_embeddings import RetryingEmbeddings
from dungeon_core.ports.retriever import Retriever


def create_retriever(
    store: Path,
    embedding_model: str,
    api_key: str,
) -> Retriever:
    """Assemble the retriever with its real adapters.

    The embedding model must be the one the index was built with (see
    ``create_indexing_service``); only the task type differs, being
    specific to queries.
    """

    embeddings = RetryingEmbeddings(
        GoogleGenerativeAIEmbeddings(
            model=embedding_model,
            google_api_key=api_key,
            task_type="RETRIEVAL_QUERY",
        )
    )
    return ChromaRetriever(store, embeddings)
