import typer

from .chat import Chat

app = typer.Typer()


def _read() -> str:
    try:
        return typer.prompt(
            ">", prompt_suffix=" ", default="", show_default=False
        )
    except typer.Abort:
        raise EOFError from None


@app.callback(invoke_without_command=True)
def chat():
    """Open a Chat."""

    Chat(read=_read, write=typer.echo).run()
