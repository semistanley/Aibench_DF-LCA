from __future__ import annotations

import click

from cli.benchmark import benchmark


@click.group()
def cli():
    """AI Bench DF-LCA CLI."""


@cli.command("serve")
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=8000, show_default=True, type=int)
def serve(host: str, port: int) -> None:
    """Run the FastAPI server."""
    import uvicorn

    uvicorn.run("api.main:app", host=host, port=port, reload=True)


cli.add_command(benchmark)

if __name__ == "__main__":
    cli()

