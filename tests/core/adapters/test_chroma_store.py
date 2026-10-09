from langchain_core.documents import Document

from dungeon.core.adapters.chroma_store import ChromaStore


def chunk(text: str, source: str = "a.pdf", page: int = 1) -> Document:
    return Document(
        page_content=text, metadata={"source": source, "page": page}
    )


def test_persists_across_instances(tmp_path):
    ChromaStore(tmp_path).add([chunk("x")], [[1.0, 0.0]])

    assert ChromaStore(tmp_path).count() == 1


def test_readding_a_source_replaces_its_chunks(tmp_path):
    store = ChromaStore(tmp_path)
    store.add(
        [chunk("one"), chunk("two"), chunk("other", "b.pdf")],
        [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]],
    )

    store.add([chunk("one edited")], [[1.0, 0.5]])

    assert store.count() == 2


def test_rerunning_the_same_batch_does_not_duplicate(tmp_path):
    store = ChromaStore(tmp_path)
    batch = [chunk("one"), chunk("two", page=2)]
    vectors = [[1.0, 0.0], [0.0, 1.0]]

    store.add(batch, vectors)
    store.add(batch, vectors)

    assert store.count() == 2


def test_adding_nothing_is_a_noop(tmp_path):
    store = ChromaStore(tmp_path)

    store.add([], [])

    assert store.count() == 0
