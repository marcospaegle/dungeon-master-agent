import pytest
from langchain_core.documents import Document
from langchain_core.embeddings import DeterministicFakeEmbedding

from dungeon.core.adapters.chroma_retriever import ChromaRetriever
from dungeon.core.adapters.chroma_store import ChromaStore
from dungeon.core.ports.retriever import IndexNotBuiltError

EMBEDDINGS = DeterministicFakeEmbedding(size=8)


def chunk(text: str, source: str = "a.pdf", page: int = 1) -> Document:
    return Document(
        page_content=text, metadata={"source": source, "page": page}
    )


def index(path, *chunks: Document) -> None:
    ids = [f"{c.metadata['source']}#{i}" for i, c in enumerate(chunks)]
    ChromaStore(path, EMBEDDINGS).add(list(chunks), ids)


def test_returns_the_closest_chunk_with_its_source_and_page(tmp_path):
    index(
        tmp_path,
        chunk("Fighters get Second Wind", "phb.pdf", 72),
        chunk("Wizards cast spells", "phb.pdf", 90),
    )

    [hit] = ChromaRetriever(tmp_path, EMBEDDINGS).search(
        "Wizards cast spells", k=1
    )

    assert hit.page_content == "Wizards cast spells"
    assert hit.metadata["source"] == "phb.pdf"
    assert hit.metadata["page"] == 90


def test_returns_at_most_k_chunks_closest_first(tmp_path):
    index(
        tmp_path,
        chunk("one", page=1),
        chunk("two", page=2),
        chunk("three", page=3),
    )

    hits = ChromaRetriever(tmp_path, EMBEDDINGS).search("two", k=2)

    assert len(hits) == 2
    assert hits[0].page_content == "two"


def test_a_missing_store_says_to_run_dungeon_build(tmp_path):
    missing = tmp_path / "chroma"

    with pytest.raises(IndexNotBuiltError, match="dungeon build"):
        ChromaRetriever(missing, EMBEDDINGS).search("anything", k=1)

    assert not missing.exists()


def test_an_empty_index_says_to_run_dungeon_build(tmp_path):
    store = ChromaStore(tmp_path, EMBEDDINGS)
    store.add([chunk("x")], ["a#1#0"])
    store.clear()

    with pytest.raises(IndexNotBuiltError, match="dungeon build"):
        ChromaRetriever(tmp_path, EMBEDDINGS).search("anything", k=1)
