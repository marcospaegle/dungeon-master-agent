from langchain_core.documents import Document
from langchain_core.embeddings import DeterministicFakeEmbedding

from dungeon_core.config.settings import Settings
from dungeon_core.knowledge.adapters.chroma_store import ChromaStore
from dungeon_core.knowledge.factory import KnowledgeFactory

SETTINGS = Settings(
    {"GOOGLE_EMBEDDING_MODEL": "model-x", "GOOGLE_API_KEY": "key-y"}
)


class FakeLoader:
    folders: list = []

    def __init__(self, folder):
        FakeLoader.folders.append(folder)

    def load(self):
        return [
            Document(
                page_content="a rules page",
                metadata={"source": "a.pdf", "page": 1},
            )
        ]


def test_wires_the_folder_store_and_embedding_model(tmp_path, monkeypatch):
    FakeLoader.folders = []
    google_args = {}

    def fake_google(**kwargs):
        google_args.update(kwargs)
        return DeterministicFakeEmbedding(size=8)

    monkeypatch.setattr(
        "dungeon_core.knowledge.factory.PdfFolderLoader", FakeLoader
    )
    monkeypatch.setattr(
        "dungeon_core.knowledge.factory.GoogleGenerativeAIEmbeddings",
        fake_google,
    )

    service = KnowledgeFactory(SETTINGS).indexing_service(
        source_folder=tmp_path / "books", store=tmp_path / "chroma"
    )
    result = service.index()

    assert result.added == 1
    assert FakeLoader.folders == [tmp_path / "books"]
    assert (tmp_path / "chroma").is_dir()
    assert google_args == {
        "model": "model-x",
        "google_api_key": "key-y",
        "task_type": "RETRIEVAL_DOCUMENT",
    }


def test_wires_the_store_and_the_query_embedding_model(tmp_path, monkeypatch):
    google_args = {}
    embeddings = DeterministicFakeEmbedding(size=8)

    def fake_google(**kwargs):
        google_args.update(kwargs)
        return embeddings

    monkeypatch.setattr(
        "dungeon_core.knowledge.factory.GoogleGenerativeAIEmbeddings",
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

    retriever = KnowledgeFactory(SETTINGS).retriever(store=tmp_path)
    [hit] = retriever.search("a rules page", k=1)

    assert hit.metadata["page"] == 1
    assert google_args == {
        "model": "model-x",
        "google_api_key": "key-y",
        "task_type": "RETRIEVAL_QUERY",
    }
