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


class FakeStore:
    def __init__(self) -> None:
        self.chunks: list[Document] = []

    def add(self, chunks: list[Document]) -> None:
        self.chunks = chunks


def build_service(documents: list[Document]):
    splitter, store = FakeSplitter(), FakeStore()
    service = IndexingService(FakeLoader(documents), splitter, store)
    return service, splitter, store


def test_index_runs_each_stage_on_the_previous_output():
    loaded = [Document(page_content="ab\ncde")]
    service, splitter, store = build_service(loaded)

    service.index()

    assert splitter.received == loaded
    assert store.chunks == [
        Document(page_content="ab"),
        Document(page_content="cde"),
    ]


def test_index_returns_the_number_of_chunks_stored():
    service, *_ = build_service([Document(page_content="a\nb\nc")])

    assert service.index() == 3


def test_index_with_no_documents_stores_nothing():
    service, _, store = build_service([])

    assert service.index() == 0
    assert store.chunks == []
