"""Rich rendering for engine result objects."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from cli.mock_engine import AnalysisResult
from schemas.request import FinancialRequest


def show_banner(console: Console) -> None:
    """Show a compact enterprise-style command header."""
    console.print("[brand]SENTINELAI[/brand] [muted]// Adaptive Governance Platform[/muted]")


def render_ai_understanding(console: Console, request: FinancialRequest) -> None:
    """Show only facts that were actually extracted before rules run."""
    fields = {
        "Amount": request.transaction.amount,
        "Merchant": request.transaction.merchant,
        "Category": request.metadata.get("category"),
        "Payment Method": request.metadata.get("payment_method"),
        "Country": request.context.location,
        "Destination": request.metadata.get("destination"),
        "Travel Date": request.metadata.get("travel_date"),
        "Purpose": request.metadata.get("purpose"),
    }
    extraction = request.metadata.get("_extraction", {})
    extracted = extraction.get("explicit", [name for name, value in fields.items() if value not in (None, "", "Unknown")])
    inferred = extraction.get("inferred", [])
    metrics = request.metadata.get("_extraction_metrics", {})
    table = Table(title="AI Understanding", border_style="brand", show_header=False)
    table.add_column(style="muted")
    table.add_column()
    table.add_row("Intent", request.intent.value.replace("_", " ").title())
    table.add_row("Model", "Local Qwen3 MLX")
    table.add_row("Extraction Confidence", f"{len(extracted)}/{len(fields)} explicit fields")
    if metrics:
        table.add_row("LLM extraction", f"{metrics.get('llm_ms', 0):.1f} ms")
        table.add_row("Validation", f"{metrics.get('validation_ms', 0):.1f} ms")
    table.add_row("[heading]Extracted[/heading]", "")
    for name in extracted:
        table.add_row("✓ " + name.replace("_", " ").title(), str(fields.get(name.replace("_", " ").title(), request.metadata.get(name, request.transaction.amount if name == "amount" else request.transaction.currency if name == "currency" else "—"))))
    missing = [name for name, value in fields.items() if value in (None, "", "Unknown")]
    if missing:
        table.add_row("[muted]Missing[/muted]", "• " + " · ".join(missing))
    if inferred:
        table.add_row("[warning]Inferred[/warning]", "• " + " · ".join(inferred))
    console.print(table)
    console.print()


def render_report(console: Console, request: FinancialRequest, result: AnalysisResult) -> None:
    """Render a result object without making governance decisions."""
    console.rule("[heading]SentinelAI Governance Report")
    _render_request_summary(console, request)
    _render_expert_results(console, result)
    decision_style = {"APPROVE": "success", "REVIEW": "warning", "BLOCK": "danger"}.get(
        result.final_decision, "heading"
    )
    console.print(
        Panel(
            Text(f"{result.final_decision}  ·  {_confidence(result.confidence)} confidence", style=decision_style),
            title="[heading]Final Decision[/heading]",
            border_style=decision_style,
            padding=(1, 2),
        )
    )
    console.print("[heading]Explanation[/heading]")
    for point in result.explanation:
        console.print(f"  [brand]•[/brand] {point}")
    console.print()
    metrics = Table(title="Performance Metrics", border_style="muted", show_header=False, box=None)
    metrics.add_column(style="muted")
    metrics.add_column(justify="right", style="heading")
    confidences = [item.confidence for item in result.expert_results if item.confidence is not None]
    average = sum(confidences) / len(confidences) if confidences else None
    metrics.add_row("Total Runtime", f"{result.total_runtime_ms:.1f} ms")
    metrics.add_row("Experts Executed", str(len(result.expert_results)))
    metrics.add_row("Average Confidence", _confidence(average))
    console.print(metrics)


def _render_request_summary(console: Console, request: FinancialRequest) -> None:
    table = Table(title="Request Summary", border_style="muted", header_style="heading")
    table.add_column("Field", style="muted")
    table.add_column("Value")
    table.add_row("Request ID", request.request_id)
    table.add_row("Amount", _format_amount(request))
    table.add_row("Merchant", request.transaction.merchant or "—")
    table.add_row("Category", str(request.metadata.get("category", "—")))
    table.add_row("Country", request.context.location or "—")
    table.add_row("Payment Method", str(request.metadata.get("payment_method", "—")))
    table.add_row("Timestamp", request.timestamp.isoformat())
    table.add_row("User ID", request.user_id)
    console.print(table)
    console.print()


def _render_expert_results(console: Console, result: AnalysisResult) -> None:
    table = Table(title="Expert Results", border_style="muted", header_style="heading")
    table.add_column("Expert")
    table.add_column("Matched Rule")
    table.add_column("Decision")
    table.add_column("Confidence", justify="right")
    table.add_column("Execution Time", justify="right")
    for item in result.expert_results:
        style = {"APPROVE": "success", "REVIEW": "warning", "BLOCK": "danger"}.get(item.decision, "heading")
        rule_ids = item.metadata.get("matched_rule_ids") or item.metadata.get("rule_ids") or []
        rule = ", ".join(rule_ids) or item.metadata.get("rule_id") or "Undefined"
        table.add_row(item.expert, rule, f"[{style}]{item.decision}[/{style}]", _confidence(item.confidence), f"{item.execution_time_ms:.1f} ms")
    console.print(table)
    console.print()


def _format_amount(request: FinancialRequest) -> str:
    if request.transaction.amount is None:
        return "—"
    return f"{request.transaction.currency or ''} {request.transaction.amount:,.2f}".strip()


def _confidence(value: float | None) -> str:
    return f"{value:.0%}" if value is not None else "N/A"
