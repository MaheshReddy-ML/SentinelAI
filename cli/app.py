"""Application factory for the SentinelAI terminal interface."""

from __future__ import annotations

import typer

from cli.commands import analyze

app = typer.Typer(
    name="sentinel",
    help="SentinelAI governance report interface.",
    no_args_is_help=True,
    add_completion=False,
)


@app.callback()
def sentinel() -> None:
    """SentinelAI command group."""


app.command()(analyze)
