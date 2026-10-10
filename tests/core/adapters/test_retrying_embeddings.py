import logging

import httpx
import pytest
from google.genai.errors import ClientError, ServerError
from langchain_core.embeddings import Embeddings
from langchain_google_genai._common import GoogleGenerativeAIError

from dungeon.core.adapters.retrying_embeddings import (
    ATTEMPTS,
    RetryingEmbeddings,
)


class FlakyEmbeddings(Embeddings):
    """Raises the given errors in turn, then embeds."""

    def __init__(self, errors: list[Exception]) -> None:
        self.errors = list(errors)
        self.calls = 0

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.calls += 1
        if self.errors:
            raise self.errors.pop(0)
        return [[1.0] for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        return [1.0]


def wrapped(error: Exception) -> GoogleGenerativeAIError:
    """The error as LangChain raises it, with the original as cause."""
    wrapper = GoogleGenerativeAIError("Error embedding content")
    wrapper.__cause__ = error
    return wrapper


def unavailable() -> GoogleGenerativeAIError:
    return wrapped(ServerError(503, {"error": {"status": "UNAVAILABLE"}}))


def build(errors: list[Exception]):
    inner, sleeps = FlakyEmbeddings(errors), []
    return RetryingEmbeddings(inner, sleeps.append), inner, sleeps


def test_retries_a_503_until_it_succeeds():
    embeddings, inner, sleeps = build([unavailable(), unavailable()])

    assert embeddings.embed_documents(["a", "b"]) == [[1.0], [1.0]]
    assert inner.calls == 3
    assert len(sleeps) == 2


def test_retries_rate_limits_and_timeouts():
    rate_limit = wrapped(ClientError(429, {"error": {"status": "EXHAUSTED"}}))
    timeout = wrapped(httpx.ReadTimeout("slow"))
    embeddings, inner, _ = build([rate_limit, timeout])

    embeddings.embed_documents(["a"])

    assert inner.calls == 3


def test_backoff_grows_between_attempts():
    embeddings, _, sleeps = build([unavailable()] * 3)

    embeddings.embed_documents(["a"])

    assert sleeps[0] < sleeps[1] < sleeps[2]


def test_gives_up_after_the_last_attempt():
    embeddings, inner, sleeps = build([unavailable()] * ATTEMPTS)

    with pytest.raises(GoogleGenerativeAIError):
        embeddings.embed_documents(["a"])

    assert inner.calls == ATTEMPTS
    assert len(sleeps) == ATTEMPTS - 1


def test_other_errors_are_raised_at_once():
    bad_key = wrapped(ClientError(403, {"error": {"status": "DENIED"}}))
    embeddings, inner, sleeps = build([bad_key])

    with pytest.raises(GoogleGenerativeAIError):
        embeddings.embed_documents(["a"])

    assert inner.calls == 1
    assert sleeps == []


def test_logs_each_retry(caplog):
    embeddings, *_ = build([unavailable()])

    with caplog.at_level(logging.WARNING):
        embeddings.embed_documents(["a"])

    assert "attempt 1 of" in caplog.text
