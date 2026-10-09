from langchain_core.documents import Document

from dungeon.core.indexing_service import IndexingService


class FakeLoader:
    def __init__(self, documents: list[Document]) -> None:
        self._documents = documents

    def load(self) -> list[Document]:
        return self._documents


class FakeSplitter:
    """Splits each document's text on newlines into one chunk each."""

    def __init__(self) -> None:
        self.received: list[Document] = []

    def split(self, documents: list[Document]) -> list[Document]:
        self.received = documents
        return [
            Document(page_content=line)
            for document in documents
            for line in document.page_content.splitlines()
        ]


class FakeEmbedder:
    def __init__(self) -> None:
        self.received: list[str] = []

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.received = texts
        return [[float(len(text))] for text in texts]


class FakeStore:
    def __init__(self) -> None:
        self.documents: list[Document] = []
        self.embeddings: list[list[float]] = []

    def add(
        self,
        documents: list[Document],
        embeddings: list[list[float]],
    ) -> None:
        self.documents = documents
        self.embeddings = embeddings


def build_service(documents: list[Document]):
    splitter, embedder, store = FakeSplitter(), FakeEmbedder(), FakeStore()
    service = IndexingService(FakeLoader(documents), splitter, embedder, store)
    return service, splitter, embedder, store


def test_index_runs_each_stage_on_the_previous_output():
    loaded = [Document(page_content="ab\ncde")]
    service, splitter, embedder, store = build_service(loaded)

    service.index()

    assert splitter.received == loaded
    assert embedder.received == ["ab", "cde"]
    assert store.documents == [
        Document(page_content="ab"),
        Document(page_content="cde"),
    ]
    assert store.embeddings == [[2.0], [3.0]]


def test_index_returns_the_number_of_chunks_stored():
    service, *_ = build_service([Document(page_content="a\nb\nc")])

    assert service.index() == 3


def test_index_with_no_documents_stores_nothing():
    service, _, embedder, store = build_service([])

    assert service.index() == 0
    assert embedder.received == []
    assert store.documents == []
