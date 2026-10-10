from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


class RecursiveSplitter:
    """Splits Documents into Chunks, keeping their metadata."""

    def __init__(self) -> None:
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
        )

    def split(self, documents: list[Document]) -> list[Document]:
        return self._splitter.split_documents(documents)
