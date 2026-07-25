"""Progress presentation for the analysis lifecycle."""

from __future__ import annotations

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

STEPS = (
    "Validating request",
    "Loading governance rules",
    "Routing experts",
    "Running Policy Expert",
    "Running Fraud Expert",
    "Running Risk Expert",
    "Running Compliance Expert",
    "Running Spend Expert",
    "Aggregating results",
    "Generating explanation",
)


def show_analysis_progress(console: Console) -> None:
    """Render the presentation-only analysis lifecycle."""
    with Progress(
        SpinnerColumn(style="brand"),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=False,
    ) as progress:
        for step in STEPS:
            task = progress.add_task(f"[heading]{step}", total=None)
            progress.update(task, description=f"[success]✓[/success] {step}", completed=1)
