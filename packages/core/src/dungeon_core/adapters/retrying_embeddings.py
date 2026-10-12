import logging
import random
import time
from collections.abc import Callable

import httpx
from google.genai.errors import APIError
from langchain_core.embeddings import Embeddings

logger = logging.getLogger(__name__)

ATTEMPTS = 5
BASE_DELAY = 4.0
TRANSIENT_CODES = {429, 503}


def _is_transient(error: BaseException | None) -> bool:
    """Whether the error, or a cause of it, is worth retrying.

    LangChain wraps the Google client's errors, so the chain of
    causes is walked.
    """
    while error is not None:
        if isinstance(error, APIError) and error.code in TRANSIENT_CODES:
            return True
        if isinstance(error, TimeoutError | httpx.TimeoutException):
            return True
        error = error.__cause__

    return False


class RetryingEmbeddings(Embeddings):
    """Retries another Embeddings on transient API errors.

    Rate limits (429), unavailability (503) and timeouts are retried
    with exponential backoff and jitter. Any other error, such as a
    bad API key, is raised at once, as is the last transient one.
    """

    def __init__(
        self,
        embeddings: Embeddings,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._embeddings = embeddings
        self._sleep = sleep

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._retry(self._embeddings.embed_documents, texts)

    def embed_query(self, text: str) -> list[float]:
        return self._retry(self._embeddings.embed_query, text)

    def _retry(self, embed, argument):
        for attempt in range(1, ATTEMPTS + 1):
            try:
                return embed(argument)
            except Exception as error:
                if attempt == ATTEMPTS or not _is_transient(error):
                    raise

                delay = BASE_DELAY * 2 ** (attempt - 1)
                delay = delay / 2 + random.uniform(0, delay / 2)
                logger.warning(
                    "Embedding failed (attempt %d of %d), retrying in "
                    "%.0fs: %s",
                    attempt,
                    ATTEMPTS,
                    delay,
                    error,
                )
                self._sleep(delay)
