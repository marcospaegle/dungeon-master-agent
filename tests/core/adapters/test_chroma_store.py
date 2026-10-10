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
    ChromaStore(tmp_path, EMBEDDINGS).add([chunk("x")], ["a#1#0"])

    assert stored(tmp_path) == ["x"]


def test_adding_an_existing_id_replaces_it(tmp_path):
    store = ChromaStore(tmp_path, EMBEDDINGS)
    store.add([chunk("one"), chunk("two")], ["a#1#0", "a#1#1"])

    store.add([chunk("one edited")], ["a#1#0"])

    assert stored(tmp_path) == ["one edited", "two"]


def test_existing_ids_lists_what_is_stored(tmp_path):
    store = ChromaStore(tmp_path, EMBEDDINGS)

    assert store.existing_ids() == set()

    store.add([chunk("one"), chunk("two")], ["a#1#0", "a#1#1"])

    assert ChromaStore(tmp_path, EMBEDDINGS).existing_ids() == {
        "a#1#0",
        "a#1#1",
    }


def test_clear_removes_everything_and_stays_usable(tmp_path):
    store = ChromaStore(tmp_path, EMBEDDINGS)
    store.add([chunk("one")], ["a#1#0"])

    store.clear()

    assert stored(tmp_path) == []

    store.add([chunk("two")], ["a#1#0"])

    assert stored(tmp_path) == ["two"]
