"""Typer commands for the SentinelAI presentation layer."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console

from cli.display import render_report, show_banner
from cli.mock_engine import analyze_transaction
from cli.progress import show_analysis_progress
from cli.prompts import collect_request, load_request
from cli.theme import THEME

console = Console(theme=THEME)


def analyze(
    sample: Annotated[Optional[Path], typer.Argument(help="Optional JSON request file.")] = None,
) -> None:
    """Collect or load a transaction, then render a governance report."""
    show_banner(console)
    request = load_request(sample) if sample else collect_request()
    show_analysis_progress(console)
    result = analyze_transaction(request)
    render_report(console, request, result)
