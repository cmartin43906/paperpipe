import typer
from pathlib import Path

'''
defines a CLI application with two commands
hello: proves system runs
inspect: accepts a file path and reports info
'''

app = typer.Typer()

@app.command()
def hello():
    '''
    verify the tool runs
    '''
    typer.echo("paperpipe is alive")

@app.command()
def inspect(file: Path):
    '''
    simple test command: show info about a file
    '''
    if not file.exists():
        typer.echo(f"File not found: {file}")
        raise typer.Exit(code=1)
    
    typer.echo(f"Inspecting: {file}")
    typer.echo(f"Size: {file.stat().st_size} bytes")

if __name__ == "__main__":
    app()