from typing import Protocol


class Embedder(Protocol):
    """Turns text into vectors."""

    def embed(self, texts: list[str]) -> list[list[float]]: ...
