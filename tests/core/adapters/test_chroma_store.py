from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import DeterministicFakeEmbedding

from dungeon.core.adapters.chroma_store import COLLECTION, ChromaStore

EMBEDDINGS = DeterministicFakeEmbedding(size=4)


def chunk(text: str, source: str = "a.pdf", page: int = 1) -> Document:
    return Document(
        page_content=text, metadata={"source": source, "page": page}
    )


def stored(path) -> list[str]:
    """Texts persisted at ``path``, read through a fresh Chroma."""
    chroma = Chroma(
        collection_name=COLLECTION,
        persist_directory=str(path),
        embedding_function=EMBEDDINGS,
    )
    return sorted(chroma.get()["documents"])


def test_persists_across_instances(tmp_path):
    ChromaStore(tmp_path, EMBEDDINGS).add([chunk("x")])

    assert stored(tmp_path) == ["x"]


def test_readding_a_source_replaces_its_chunks(tmp_path):
    store = ChromaStore(tmp_path, EMBEDDINGS)
    store.add([chunk("one"), chunk("two"), chunk("other", "b.pdf")])

    store.add([chunk("one edited")])

    assert stored(tmp_path) == ["one edited", "other"]


def test_rerunning_the_same_batch_does_not_duplicate(tmp_path):
    store = ChromaStore(tmp_path, EMBEDDINGS)
    batch = [chunk("one"), chunk("two", page=2)]

    store.add(batch)
    store.add(batch)

    assert stored(tmp_path) == ["one", "two"]
