import typer
from pathlib import Path

from paperpipe.ingest import intake

'''
defines a CLI application with two commands
hello: proves system runs
inspect: accepts a file path and reports info
'''

app = typer.Typer() # app container

@app.command() # expose this function as a CLI command
def hello():
    '''
    verify the tool runs
    '''
    typer.echo("paperpipe is alive")

@app.command()
def inspect(file: Path): # user must pass a filesystem path, convert to Path object
    '''
    simple test command: show info about a file
    '''
    if not file.exists():
        typer.echo(f"File not found: {file}")
        raise typer.Exit(code=1) # fail
    
    typer.echo(f"Inspecting: {file}")
    typer.echo(f"Size: {file.stat().st_size} bytes")
    # .stat() is defined on Path, returns metadata structure
    # .st_size is an attribute on the object, size in bytes

@app.command("intake")
# typer.Option defines a flag option instead of a positional arg, first arg of Option is default
# will see docstring if you run python -m paperpipe.cli ingest --help
# thin wrapper
def intake_cmd(path: Path, move: bool = typer.Option(False, help="Move instead of copy")):
    """
    Ingest a PDF file or a directory of files into the library.
    """
    result = intake(path, move=move)
    typer.echo(
        f"Done. copied={result.copied} moved={result.moved} "
        f"skipped_duplicate={result.skipped_duplicate} rejected_non_pdf={result.rejected_non_pdf} failed={result.failed}"
    )

if __name__ == "__main__":
    app()