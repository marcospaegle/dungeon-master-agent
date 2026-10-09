import typer

app = typer.Typer()


@app.command()
def new():
    print("start a new chat")
