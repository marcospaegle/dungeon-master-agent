from langchain_core.documents import Document
from langchain_core.embeddings import DeterministicFakeEmbedding

from dungeon.core.indexing_factory import create_indexing_service


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
        "dungeon.core.indexing_factory.PdfFolderLoader", FakeLoader
    )
    monkeypatch.setattr(
        "dungeon.core.indexing_factory.GoogleGenerativeAIEmbeddings",
        fake_google,
    )

    service = create_indexing_service(
        source_folder=tmp_path / "books",
        store=tmp_path / "chroma",
        embedding_model="model-x",
        api_key="key-y",
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
