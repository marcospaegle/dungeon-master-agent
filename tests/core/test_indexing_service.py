from langchain_core.documents import Document

from dungeon.core.indexing_service import (
    BATCH_SIZE,
    IndexingService,
    IndexResult,
)

META = {"source": "a.pdf", "page": 1}


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
            Document(page_content=line, metadata=document.metadata)
            for document in documents
            for line in document.page_content.splitlines()
        ]


class FakeStore:
    def __init__(self, stored: set[str] | None = None) -> None:
        self.stored = set(stored or ())
        self.batches: list[tuple[list[Document], list[str]]] = []
        self.cleared = False

    @property
    def chunks(self) -> list[Document]:
        return [c for chunks, _ in self.batches for c in chunks]

    @property
    def ids(self) -> list[str]:
        return [i for _, ids in self.batches for i in ids]

    def add(self, chunks: list[Document], ids: list[str]) -> None:
        self.batches.append((chunks, ids))
        self.stored |= set(ids)

    def existing_ids(self) -> set[str]:
        return set(self.stored)

    def clear(self) -> None:
        self.cleared = True
        self.stored = set()


def build_service(documents: list[Document], store: FakeStore | None = None):
    splitter, store = FakeSplitter(), store or FakeStore()
    service = IndexingService(FakeLoader(documents), splitter, store)
    return service, splitter, store


def test_index_runs_each_stage_on_the_previous_output():
    loaded = [Document(page_content="ab\ncde", metadata=META)]
    service, splitter, store = build_service(loaded)

    service.index()

    assert splitter.received == loaded
    assert store.chunks == [
        Document(page_content="ab", metadata=META),
        Document(page_content="cde", metadata=META),
    ]
    assert store.ids == ["a.pdf#1#0", "a.pdf#1#1"]


def test_index_returns_total_and_added_chunks():
    service, *_ = build_service(
        [Document(page_content="a\nb\nc", metadata=META)]
    )

    assert service.index() == IndexResult(total=3, added=3)


def test_index_with_no_documents_stores_nothing():
    service, _, store = build_service([])

    assert service.index() == IndexResult(total=0, added=0)
    assert store.batches == []


def lines(count: int) -> list[Document]:
    text = "\n".join(f"line {n}" for n in range(count))
    return [Document(page_content=text, metadata=META)]


def test_index_stores_in_batches_and_reports_progress():
    count = BATCH_SIZE * 2 + 1
    service, _, store = build_service(lines(count))
    progress = []

    service.index(on_progress=lambda done, todo: progress.append((done, todo)))

    assert [len(chunks) for chunks, _ in store.batches] == [
        BATCH_SIZE,
        BATCH_SIZE,
        1,
    ]
    assert len(set(store.ids)) == count
    assert progress == [
        (BATCH_SIZE, count),
        (BATCH_SIZE * 2, count),
        (count, count),
    ]


def test_index_skips_chunks_already_stored():
    store = FakeStore({"a.pdf#1#0", "a.pdf#1#1"})
    service, _, store = build_service(lines(4), store)

    result = service.index()

    assert result == IndexResult(total=4, added=2)
    assert store.ids == ["a.pdf#1#2", "a.pdf#1#3"]
    assert not store.cleared


def test_index_rebuild_clears_the_store_and_adds_everything():
    store = FakeStore({"a.pdf#1#0", "a.pdf#1#1"})
    service, _, store = build_service(lines(3), store)

    result = service.index(rebuild=True)

    assert store.cleared
    assert result == IndexResult(total=3, added=3)
    assert store.ids == ["a.pdf#1#0", "a.pdf#1#1", "a.pdf#1#2"]


def test_index_with_no_chunks_does_not_clear_on_rebuild():
    service, _, store = build_service([])

    service.index(rebuild=True)

    assert not store.cleared
