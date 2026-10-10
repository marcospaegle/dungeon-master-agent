import logging
import warnings
from pathlib import Path

import pytest
from langchain_core.documents import Document
from typer.testing import CliRunner

from dungeon.cli import app
from dungeon.cli.build import _format_elapsed
from dungeon.core.adapters.recursive_splitter import RecursiveSplitter
from dungeon.core.indexing_service import IndexingService

runner = CliRunner()


def test_build_requires_the_api_key(tmp_path, monkeypatch):
    monkeypatch.setattr("dungeon.cli.build.load_dotenv", lambda: None)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_EMBEDDING_MODEL", "model")

    result = runner.invoke(app, ["build", "--source-folder", str(tmp_path)])

    assert result.exit_code != 0
    assert "GOOGLE_API_KEY" in result.output


def test_build_reads_pdfs_from_storage_books_by_default(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("dungeon.cli.build.load_dotenv", lambda: None)
    monkeypatch.setenv("GOOGLE_API_KEY", "key")
    monkeypatch.setenv("GOOGLE_EMBEDDING_MODEL", "model")

    result = runner.invoke(app, ["build"])

    assert isinstance(result.exception, FileNotFoundError)
    assert "storage/books" in str(result.exception)


def test_build_logs_errors_to_a_dated_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("dungeon.cli.build.load_dotenv", lambda: None)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_EMBEDDING_MODEL", "model")

    result = runner.invoke(app, ["build"])

    assert result.exit_code != 0
    (log,) = (tmp_path / "storage/logs").glob("build-*.log")
    assert "GOOGLE_API_KEY" in log.read_text()


def test_build_logs_warnings_and_still_shows_them(tmp_path, monkeypatch):
    class WarningLoader:
        def load(self):
            warnings.warn("page 1 has no text", UserWarning, stacklevel=1)
            return []

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("dungeon.cli.build.load_dotenv", lambda: None)
    patch_service(monkeypatch, WarningLoader(), FakeStore())
    monkeypatch.setenv("GOOGLE_API_KEY", "key")
    monkeypatch.setenv("GOOGLE_EMBEDDING_MODEL", "model")
    shown = []
    monkeypatch.setattr(
        warnings, "showwarning", lambda message, *a, **k: shown.append(message)
    )

    runner.invoke(app, ["build"])

    (log,) = (tmp_path / "storage/logs").glob("build-*.log")
    assert "page 1 has no text" in log.read_text()
    assert any("page 1 has no text" in str(m) for m in shown)


class FakeLoader:
    def load(self):
        return [
            Document(
                page_content="a rules page",
                metadata={"source": "a.pdf", "page": 1},
            )
        ]


class FakeStore:
    """Records what the command does to the store."""

    def __init__(self):
        self.stored: set[str] = set()
        self.cleared = False

    def add(self, chunks, ids):
        self.stored |= set(ids)

    def existing_ids(self):
        return set(self.stored)

    def clear(self):
        self.cleared = True


def patch_service(monkeypatch, loader, store):
    """Make the command index through fakes instead of real adapters."""

    monkeypatch.setattr(
        "dungeon.cli.build.create_indexing_service",
        lambda *args, **kwargs: IndexingService(
            loader, RecursiveSplitter(), store
        ),
    )


@pytest.fixture
def fake_build(tmp_path, monkeypatch):
    store = FakeStore()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("dungeon.cli.build.load_dotenv", lambda: None)
    patch_service(monkeypatch, FakeLoader(), store)
    monkeypatch.setenv("GOOGLE_API_KEY", "key")
    monkeypatch.setenv("GOOGLE_EMBEDDING_MODEL", "model")
    return tmp_path, store


def test_build_prints_a_summary_and_logs_progress(fake_build):
    tmp_path, _ = fake_build

    result = runner.invoke(app, ["build"])

    assert result.exit_code == 0
    assert "Added 1 of 1 chunks in " in result.output
    (log,) = (tmp_path / "storage/logs").glob("build-*.log")
    text = log.read_text()
    assert "1 chunks, 0 already stored, 1 to add" in text
    assert "Stored 1 of 1 chunks" in text
    assert "Added 1 of 1 chunks" in text


def test_build_does_not_clear_the_store_by_default(fake_build):
    _, store = fake_build

    runner.invoke(app, ["build"])

    assert not store.cleared


def test_build_rebuild_clears_the_store(fake_build):
    _, store = fake_build

    result = runner.invoke(app, ["build", "--rebuild"])

    assert result.exit_code == 0
    assert store.cleared


def test_build_logs_the_core_modules_too(fake_build, monkeypatch):
    tmp_path, _ = fake_build

    class Failing(FakeStore):
        def add(self, chunks, ids):
            logging.getLogger("dungeon.core.adapters.x").warning("retrying")

    patch_service(monkeypatch, FakeLoader(), Failing())

    runner.invoke(app, ["build"])

    (log,) = (tmp_path / "storage/logs").glob("build-*.log")
    assert "retrying" in log.read_text()


def test_build_passes_its_options_to_the_factory(tmp_path, monkeypatch):
    received = {}

    def factory(source_folder, store, embedding_model, api_key):
        received.update(
            source_folder=source_folder,
            store=store,
            embedding_model=embedding_model,
            api_key=api_key,
        )
        return IndexingService(FakeLoader(), RecursiveSplitter(), FakeStore())

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("dungeon.cli.build.load_dotenv", lambda: None)
    monkeypatch.setattr("dungeon.cli.build.create_indexing_service", factory)
    monkeypatch.setenv("GOOGLE_API_KEY", "key")
    monkeypatch.setenv("GOOGLE_EMBEDDING_MODEL", "model")

    runner.invoke(app, ["build", "--source-folder", "pdfs", "--store", "db"])

    assert received == {
        "source_folder": Path("pdfs"),
        "store": Path("db"),
        "embedding_model": "model",
        "api_key": "key",
    }


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [(0, "0s"), (59, "59s"), (60, "1m 0s"), (125.4, "2m 5s")],
)
def test_format_elapsed(seconds, expected):
    assert _format_elapsed(seconds) == expected
