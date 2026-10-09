import typer

from .build import app as build_app
from .chat import app as chat_app
from .version import app as version_app

app = typer.Typer()

app.add_typer(version_app)
app.add_typer(chat_app, name="chat")
app.add_typer(build_app)


if __name__ == "__main__":
    app()
