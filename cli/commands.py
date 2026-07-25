"""Typer commands for the SentinelAI presentation layer."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console

from cli.display import render_ai_understanding, render_report, show_banner
from cli.mock_engine import analyze_transaction
from cli.progress import run_analysis_with_progress
from cli.prompts import load_request
from cli.theme import THEME
from models.llm.local_provider import LocalMLXProvider
from models.llm.parser import RequestValidationError
from schemas.enums import ActionType
from schemas.request import FinancialRequest

console = Console(theme=THEME)


def analyze(
    sample: Annotated[Optional[Path], typer.Argument(help="Optional JSON request file.")] = None,
    prompt: Annotated[Optional[str], typer.Option("--prompt", "-p", help="Natural-language financial request.")] = None,
) -> None:
    """Collect or load a transaction, then render a governance report."""
    show_banner(console)
    if sample and prompt:
        raise typer.BadParameter("Provide either a JSON sample or --prompt, not both.")
    if sample:
        request = load_request(sample)
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
