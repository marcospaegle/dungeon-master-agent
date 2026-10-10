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


def test_build_reads_pdfs_from_dungeon_books_by_default(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("dungeon.cli.build.load_dotenv", lambda: None)
    monkeypatch.setenv("GOOGLE_API_KEY", "key")
    monkeypatch.setenv("GOOGLE_EMBEDDING_MODEL", "model")

    result = runner.invoke(app, ["build"])

    assert isinstance(result.exception, FileNotFoundError)
    assert ".dungeon/books" in str(result.exception)
