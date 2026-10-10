from langchain_core.documents import Document
from langchain_core.embeddings import DeterministicFakeEmbedding

from dungeon.core.adapters.chroma_store import ChromaStore
from dungeon.core.retrieval_factory import create_retriever


def test_wires_the_store_and_the_query_embedding_model(tmp_path, monkeypatch):
    google_args = {}
    embeddings = DeterministicFakeEmbedding(size=8)

    def fake_google(**kwargs):
        google_args.update(kwargs)
        return embeddings

    monkeypatch.setattr(
        "dungeon.core.retrieval_factory.GoogleGenerativeAIEmbeddings",
        fake_google,
    )
    ChromaStore(tmp_path, embeddings).add(
        [
            Document(
                page_content="a rules page",
                metadata={"source": "a.pdf", "page": 1},
            )
        ],
        ["a#1#0"],
    )

    retriever = create_retriever(
        store=tmp_path,
        embedding_model="model-x",
        api_key="key-y",
    )
    [hit] = retriever.search("a rules page", k=1)

    assert hit.metadata["page"] == 1
    assert google_args == {
        "model": "model-x",
        "google_api_key": "key-y",
        "task_type": "RETRIEVAL_QUERY",
    }
