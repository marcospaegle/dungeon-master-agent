import logging
import warnings

import pytest
from langchain_core.documents import Document
from typer.testing import CliRunner

from dungeon.cli import app

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
        def __init__(self, folder):
            pass

        def load(self):
            warnings.warn("page 1 has no text", UserWarning, stacklevel=1)
            return []

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("dungeon.cli.build.load_dotenv", lambda: None)
    monkeypatch.setattr("dungeon.cli.build.PdfFolderLoader", WarningLoader)
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
    def __init__(self, folder):
        pass

    def load(self):
        return [
            Document(
                page_content="a rules page",
                metadata={"source": "a.pdf", "page": 1},
            )
        ]


class FakeStore:
    """Records what the command does to the store."""

    instances: list["FakeStore"] = []

    def __init__(self, path, embeddings):
        self.stored: set[str] = set()
        self.cleared = False
        FakeStore.instances.append(self)

    def add(self, chunks, ids):
        self.stored |= set(ids)

    def existing_ids(self):
        return set(self.stored)

    def clear(self):
        self.cleared = True


@pytest.fixture
def fake_build(tmp_path, monkeypatch):
    FakeStore.instances = []
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("dungeon.cli.build.load_dotenv", lambda: None)
    monkeypatch.setattr("dungeon.cli.build.PdfFolderLoader", FakeLoader)
    monkeypatch.setattr("dungeon.cli.build.ChromaStore", FakeStore)
    monkeypatch.setenv("GOOGLE_API_KEY", "key")
    monkeypatch.setenv("GOOGLE_EMBEDDING_MODEL", "model")
    return tmp_path


def test_build_prints_a_summary_and_logs_progress(fake_build):
    result = runner.invoke(app, ["build"])

    assert result.exit_code == 0
    assert "Added 1 of 1 chunks in " in result.output
    (log,) = (fake_build / "storage/logs").glob("build-*.log")
    text = log.read_text()
    assert "1 chunks, 0 already stored, 1 to add" in text
    assert "Stored 1 of 1 chunks" in text
    assert "Added 1 of 1 chunks" in text


def test_build_does_not_clear_the_store_by_default(fake_build):
    runner.invoke(app, ["build"])

    assert not FakeStore.instances[0].cleared


def test_build_rebuild_clears_the_store(fake_build):
    result = runner.invoke(app, ["build", "--rebuild"])

    assert result.exit_code == 0
    assert FakeStore.instances[0].cleared


def test_build_logs_the_core_modules_too(fake_build, monkeypatch):
    class Failing(FakeStore):
        def add(self, chunks, ids):
            logging.getLogger("dungeon.core.adapters.x").warning("retrying")

    monkeypatch.setattr("dungeon.cli.build.ChromaStore", Failing)

    runner.invoke(app, ["build"])

    (log,) = (fake_build / "storage/logs").glob("build-*.log")
    assert "retrying" in log.read_text()
