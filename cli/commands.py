"""Typer commands for the SentinelAI presentation layer."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console

from cli.display import render_ai_understanding, render_batch_report, render_directory_summary, render_report, show_banner
from cli.mock_engine import analyze_transaction
from cli.progress import run_analysis_with_progress
from cli.prompts import load_batch, load_requests
from cli.theme import THEME
from models.llm.local_provider import LocalMLXProvider
from models.llm.parser import RequestValidationError
from schemas.enums import ActionType
from schemas.request import FinancialRequest

console = Console(theme=THEME)
BATCH_CHUNK_SIZE = 100


def analyze(
    sample: Annotated[Optional[Path], typer.Argument(help="Optional JSON request file.")] = None,
    prompt: Annotated[Optional[str], typer.Option("--prompt", "-p", help="Natural-language financial request.")] = None,
    directory: Annotated[Optional[Path], typer.Option("--directory", "-d", help="Analyze every JSON file in a folder.")] = None,
) -> None:
    """Collect or load a transaction, then render a governance report."""
    show_banner(console)
    if sum(value is not None for value in (sample, prompt, directory)) > 1:
        raise typer.BadParameter("Provide one of: a JSON sample, --prompt, or --directory.")
    if directory:
        _analyze_directory(directory)
        return
    if sample:
        batch = load_batch(sample)
        requests = batch.requests
        if not requests:
            raise typer.BadParameter("; ".join(batch.errors))
        if len(requests) > 1:
            _analyze_batch(requests, sample, batch.errors)
            return
        request = requests[0]
    else:
        natural_prompt = prompt or typer.prompt("Enter request")
        try:
            with console.status("[heading]Extracting a validated financial request locally...", spinner="dots"):
                request = LocalMLXProvider().generate_request(natural_prompt)
        except RequestValidationError as error:
            console.print(f"[danger]Request extraction failed:[/danger] {error}")
            raise typer.Exit(code=2) from error
        _collect_governance_clarifications(request)
    render_ai_understanding(console, request)
    result = run_analysis_with_progress(console, request, analyze_transaction)
    render_report(console, request, result)


def _analyze_batch(requests: list[FinancialRequest], source: Path, skipped: list[str]) -> None:
    """Keep multi-request files readable with a single decision dashboard."""
    with console.status(f"[heading]Analyzing {len(requests)} requests from {source.name}...", spinner="dots"):
        results, chunks = _run_batch_in_chunks(requests)
    render_batch_report(console, requests, results, source.name, skipped, chunks)


def _run_batch_in_chunks(requests: list[FinancialRequest]) -> tuple[list, int]:
    """Bound memory and progress state; rule evaluation never shares LLM context."""
    results = []
    for offset in range(0, len(requests), BATCH_CHUNK_SIZE):
        results.extend(analyze_transaction(request) for request in requests[offset : offset + BATCH_CHUNK_SIZE])
    return results, max(1, (len(requests) + BATCH_CHUNK_SIZE - 1) // BATCH_CHUNK_SIZE)


def _analyze_directory(directory: Path) -> None:
    """Analyze every JSON file independently and retain usable work on failures."""
    if not directory.is_dir():
        raise typer.BadParameter(f"Directory not found: {directory}")
    files = sorted(directory.glob("*.json"))
    if not files:
        raise typer.BadParameter("Directory contains no .json files.")
    aggregate: list[tuple[str, int, int, int, int]] = []
    for path in files:
        batch = load_batch(path)
        if not batch.requests:
            render_batch_report(console, [], [], path.name, batch.errors, 0)
            aggregate.append((path.name, 0, 0, 0, 0))
            continue
        with console.status(f"[heading]Analyzing {len(batch.requests)} requests from {path.name}...", spinner="dots"):
            results, chunks = _run_batch_in_chunks(batch.requests)
        render_batch_report(console, batch.requests, results, path.name, batch.errors, chunks)
        aggregate.append((path.name, len(results), sum(result.final_decision == "APPROVE" for result in results), sum(result.final_decision == "REVIEW" for result in results), sum(result.final_decision == "BLOCK" for result in results)))
    render_directory_summary(console, aggregate)


def _collect_governance_clarifications(request: FinancialRequest) -> None:
    """Ask only for facts required to apply the selected governance rules."""
    needs_amount = request.action in {
        ActionType.TRAVEL_BOOKING,
        ActionType.MERCHANT_PAYMENT,
        ActionType.CREDIT_LIMIT_INCREASE,
        ActionType.REFUND,
    }
    if needs_amount and request.transaction.amount is None:
        console.print("[warning]Amount was not received.[/warning] In zsh, quote dollar amounts with single quotes or escape `$`.")
        raw_amount = typer.prompt("Amount (required for automated approval; blank keeps manual review)", default="")
        if raw_amount.strip():
            try:
                amount = float(raw_amount.replace(",", ""))
            except ValueError:
                console.print("[danger]Invalid amount; leaving it unavailable for governance rules.[/danger]")
            else:
                if amount > 0:
                    request.transaction.amount = amount
                    raw_currency = typer.prompt("Currency (for example USD, INR; blank is not assumed)", default="")
                    request.transaction.currency = raw_currency.upper() or None
                    request.metadata.setdefault("_clarified_fields", []).append("amount")
                else:
                    console.print("[danger]Amount must be greater than zero.[/danger]")
