import pytest

from dungeon.core.adapters.gemini_embedder import GeminiEmbedder


class FakeClient:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def embed_documents(self, texts):
        self.calls.append(texts)
        return [[1.0, 2.0] for _ in texts]


@pytest.fixture
def client(monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr(
        "dungeon.core.adapters.gemini_embedder.GoogleGenerativeAIEmbeddings",
        lambda **kwargs: fake,
    )
    return fake


def test_embeds_texts_through_the_client(client):
    vectors = GeminiEmbedder("key", "model").embed(["a", "b"])

    assert client.calls == [["a", "b"]]
    assert vectors == [[1.0, 2.0], [1.0, 2.0]]


def test_no_texts_makes_no_call(client):
    assert GeminiEmbedder("key", "model").embed([]) == []
    assert client.calls == []
