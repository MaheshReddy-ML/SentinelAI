"""Rich rendering for engine result objects."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from functools import lru_cache
from utils.rule_loader import RuleLoader

from cli.mock_engine import AnalysisResult
from schemas.request import FinancialRequest

BATCH_PREVIEW_LIMIT = 25
BASELINE_RULE_SUFFIX = "-000"


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
    _render_audit_actions(console, result)
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


def render_batch_report(
    console: Console,
    requests: list[FinancialRequest],
    results: list[AnalysisResult],
    source_name: str,
    skipped: list[str],
    chunks: int,
) -> None:
    """Render a compact governance dashboard for a JSON request batch."""
    console.rule(f"[heading]Batch Governance Report · {source_name}[/heading]")
    processed = len(results)
    decisions = {name: sum(result.final_decision == name for result in results) for name in ("APPROVE", "REVIEW", "BLOCK")}
    summary = Table.grid(padding=(0, 2))
    summary.add_column(style="muted")
    summary.add_column(style="heading")
    summary.add_row("Processed Requests", str(processed))
    if chunks > 1:
        summary.add_row("Chunks Processed", f"{chunks}/{chunks}")
    summary.add_row("Approved", _count_with_percentage(decisions["APPROVE"], processed))
    summary.add_row("Review", _count_with_percentage(decisions["REVIEW"], processed))
    summary.add_row("Blocked", _count_with_percentage(decisions["BLOCK"], processed))
    summary.add_row("Governance Runtime", f"{sum(result.total_runtime_ms for result in results):.1f} ms")
    console.print(Panel(summary, title="[heading]Batch Decision Overview[/heading]", border_style="brand"))
    table = Table(title="Request Decisions", border_style="muted", header_style="heading")
    table.add_column("#", justify="right", style="muted")
    table.add_column("Request ID / User ID", overflow="fold")
    table.add_column("Amount", justify="right")
    table.add_column("Decision")
    table.add_column("Confidence", justify="right")
    table.add_column("Decision rule", overflow="fold")
    table.add_column("Risk")
    table.add_column("Runtime", justify="right")
    for index, (request, result) in enumerate(zip(requests[:BATCH_PREVIEW_LIMIT], results[:BATCH_PREVIEW_LIMIT]), start=1):
        style = {"APPROVE": "success", "REVIEW": "warning", "BLOCK": "danger"}.get(result.final_decision, "heading")
        decisive = _decision_triggering_rules(result)
        risk = next((item.risk_level for item in result.expert_results if item.risk_level), "LOW")
        user = request.user_id if request.user_id not in {"", "Unknown", "anonymous"} else "—"
        table.add_row(str(index), f"{request.request_id}\n{user}", _format_amount(request), f"[{style}]{result.final_decision}[/{style}]", _confidence(result.confidence), _rule_label(decisive[:2]) if decisive else "Baseline / no triggering rule", risk.upper(), f"{result.total_runtime_ms:.1f} ms")
    console.print(table)
    if processed > BATCH_PREVIEW_LIMIT:
        console.print(f"[success]Processed all {processed} valid requests.[/success] [muted]Showing the first {BATCH_PREVIEW_LIMIT} rows only; totals and rule frequency include the complete batch.[/muted]")
    frequencies = _rule_frequency(results)
    if frequencies:
        frequency_table = Table(title="Decision-Triggering Rule Frequency", border_style="muted", header_style="heading")
        frequency_table.add_column("Rule ID")
        frequency_table.add_column("Rule Name")
        frequency_table.add_column("Occurrences", justify="right")
        catalog = _rule_catalog()
        for rule_id, count in frequencies:
            frequency_table.add_row(rule_id, catalog.get(rule_id, "Unknown rule"), str(count))
        console.print(frequency_table)
    if skipped:
        skipped_table = Table(title="Skipped Requests", border_style="warning", header_style="heading")
        skipped_table.add_column("Row", justify="right", style="muted")
        skipped_table.add_column("Validation Reason")
        for error in skipped:
            row, reason = _split_skipped_error(error)
            skipped_table.add_row(row, reason)
        console.print(skipped_table)
    footer = Table.grid(padding=(0, 2))
    footer.add_column(style="muted")
    footer.add_column(style="heading")
    footer.add_row("Processed requests", str(processed))
    footer.add_row("Skipped requests", str(len(skipped)))
    footer.add_row("Status", "[success]Governance completed successfully[/success]")
    console.print(Panel(footer, border_style="success"))
    console.print("[muted]Tip: supply one object to view the full AI Understanding and expert evidence report.[/muted]")


def render_directory_summary(console: Console, rows: list[tuple[str, int, int, int, int]]) -> None:
    """Show the operational roll-up after each source file has its own report."""
    table = Table(title="Directory Governance Summary", border_style="brand", header_style="heading")
    table.add_column("File")
    table.add_column("Requests", justify="right")
    table.add_column("Approve", justify="right", style="success")
    table.add_column("Review", justify="right", style="warning")
    table.add_column("Block", justify="right", style="danger")
    for name, total, approved, review, blocked in rows:
        table.add_row(name, str(total), str(approved), str(review), str(blocked))
    console.print(table)


def _rule_frequency(results: list[AnalysisResult]) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for result in results:
        for rule in _decision_triggering_rules(result):
            counts[rule] = counts.get(rule, 0) + 1
    return sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))


def _decision_triggering_rules(result: AnalysisResult) -> list[str]:
    """Return unique non-audit rules from experts supporting the final decision."""
    return sorted(
        {
            rule
            for item in result.expert_results
            if item.decision == result.final_decision
            for rule in _matched_rule_ids(item)
            if not rule.endswith(BASELINE_RULE_SUFFIX) and not rule.startswith("AUD-")
        }
    )


def _matched_rule_ids(item: object) -> list[str]:
    metadata = getattr(item, "metadata", {})
    rule_ids = metadata.get("matched_rule_ids") or metadata.get("rule_ids") or [metadata.get("rule_id")]
    if isinstance(rule_ids, str):
        rule_ids = [rule_ids]
    elif not isinstance(rule_ids, (list, tuple, set)):
        return []
    return [rule_id for rule_id in rule_ids if isinstance(rule_id, str) and rule_id]


def _count_with_percentage(count: int, total: int) -> str:
    return f"{count} ({count / total:.1%})" if total else "0 (0.0%)"


def _split_skipped_error(error: str) -> tuple[str, str]:
    """Keep loader validation messages readable even for file-level failures."""
    if error.startswith("Row ") and ":" in error:
        row, reason = error.split(":", 1)
        return row, reason.strip()
    return "—", error


def _rule_label(rule_ids: list[str]) -> str:
    catalog = _rule_catalog()
    return ", ".join(f"{rule_id} ({catalog.get(rule_id, 'Unknown rule')})" for rule_id in rule_ids)


@lru_cache(maxsize=1)
def _rule_catalog() -> dict[str, str]:
    """Load rule labels once per process, even for thousand-row batch reports."""
    catalog: dict[str, str] = {}
    for name in RuleLoader.available_rules():
        for rule in RuleLoader.load_rules(name)["rules"]:
            catalog[rule.rule_id] = rule.name
    return catalog


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
    table = Table(title="Decision Evidence", border_style="muted", header_style="heading")
    table.add_column("Expert")
    table.add_column("Matched Rule")
    table.add_column("Decision")
    table.add_column("Confidence", justify="right")
    table.add_column("Execution Time", justify="right")
    for item in result.expert_results:
        if _is_audit_action(item):
            continue
        style = {"APPROVE": "success", "REVIEW": "warning", "BLOCK": "danger"}.get(item.decision, "heading")
        rule = _rule_label(_matched_rule_ids(item)) or "Undefined"
        table.add_row(item.expert, rule, f"[{style}]{item.decision}[/{style}]", _confidence(item.confidence), f"{item.execution_time_ms:.1f} ms")
    console.print(table)
    console.print()


def _render_audit_actions(console: Console, result: AnalysisResult) -> None:
    """Render audit trace data separately from governance decision evidence."""
    audit_items = [item for item in result.expert_results if _is_audit_action(item)]
    if not audit_items:
        return
    table = Table(title="Audit Actions", border_style="muted", header_style="heading")
    table.add_column("Action")
    table.add_column("Recorded Rule")
    table.add_column("Execution Time", justify="right")
    for item in audit_items:
        table.add_row(item.expert, _rule_label(_matched_rule_ids(item)) or "Recorded", f"{item.execution_time_ms:.1f} ms")
    console.print(table)
    console.print()


def _is_audit_action(item: object) -> bool:
    """Audit output is traceability evidence and never governs the final decision."""
    return getattr(item, "expert", "").casefold().startswith("audit") or any(
        rule_id.startswith("AUD-") for rule_id in _matched_rule_ids(item)
    )


def _format_amount(request: FinancialRequest) -> str:
    if request.transaction.amount is None:
        return "—"
    return f"{request.transaction.currency or ''} {request.transaction.amount:,.2f}".strip()


def _confidence(value: float | None) -> str:
    return f"{value:.0%}" if value is not None else "N/A"
