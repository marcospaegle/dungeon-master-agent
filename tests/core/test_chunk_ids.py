from langchain_core.documents import Document

from dungeon.core.chunk_ids import chunk_ids


def chunk(source: str, page: int) -> Document:
    return Document(
        page_content="x", metadata={"source": source, "page": page}
    )


def test_index_restarts_for_each_page_of_each_source():
    chunks = [
        chunk("a.pdf", 1),
        chunk("a.pdf", 1),
        chunk("a.pdf", 2),
        chunk("b.pdf", 1),
    ]

    assert chunk_ids(chunks) == [
        "a.pdf#1#0",
        "a.pdf#1#1",
        "a.pdf#2#0",
        "b.pdf#1#0",
    ]


def test_same_chunks_get_the_same_ids():
    chunks = [chunk("a.pdf", 1), chunk("a.pdf", 1)]

    assert chunk_ids(chunks) == chunk_ids(chunks)
