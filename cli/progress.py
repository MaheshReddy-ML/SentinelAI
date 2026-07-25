"""Live progress presentation for the analysis lifecycle."""

from __future__ import annotations

from rich.console import Console
from collections.abc import Callable
from time import sleep

from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from schemas.request import FinancialRequest

STEPS = (
    "Validating request",
    "Loading governance rules",
    "Routing experts",
    "Running Policy Expert",
    "Running Fraud Expert",
    "Running Risk Expert",
    "Running Compliance Expert",
    "Running Spend Expert",
    "Running Audit Expert",
    "Aggregating results",
    "Generating explanation",
)


def run_analysis_with_progress(
    console: Console,
    request: FinancialRequest,
    analyze: Callable[[FinancialRequest, Callable[[str], None]], object],
) -> object:
    """Advance one live indicator as each real engine stage completes."""
    with Progress(
        SpinnerColumn(style="brand"),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("[heading]Preparing governance analysis", total=None)

        def update(step: str) -> None:
            progress.update(task, description=f"[brand]●[/brand] {step}")
            progress.refresh()
            sleep(0.10)

        return analyze(request, update)
