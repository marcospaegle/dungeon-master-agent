from collections import defaultdict

from langchain_core.documents import Document

from dungeon.core.metadata import PAGE, SOURCE


def chunk_ids(chunks: list[Document]) -> list[str]:
    """IDs of the form ``<source>#<page>#<chunk-index>``.

    Deterministic for the same chunks, so a rerun maps each chunk to
    the ID it had before. Compute them over all chunks at once: the
    index restarts for each page.
    """
    counts: defaultdict[tuple, int] = defaultdict(int)
    ids = []

    for chunk in chunks:
        key = (chunk.metadata[SOURCE], chunk.metadata[PAGE])
        ids.append(f"{key[0]}#{key[1]}#{counts[key]}")
        counts[key] += 1

    return ids
