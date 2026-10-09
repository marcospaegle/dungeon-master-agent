from langchain_core.documents import Document

from dungeon.core.adapters.recursive_splitter import RecursiveSplitter


def test_chunks_inherit_metadata():
    doc = Document(
        page_content="word " * 100, metadata={"source": "a", "page": 3}
    )

    chunks = RecursiveSplitter(chunk_size=100, chunk_overlap=10).split([doc])

    assert len(chunks) > 1
    assert all(c.metadata == doc.metadata for c in chunks)
    assert all(len(c.page_content) <= 100 for c in chunks)
