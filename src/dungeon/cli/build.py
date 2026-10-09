import typer

app = typer.Typer()


@app.command()
def build():
    print("building knowledge base")
