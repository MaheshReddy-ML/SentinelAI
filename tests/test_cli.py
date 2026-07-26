from pathlib import Path
from types import SimpleNamespace
import json

from rich.console import Console
from typer.testing import CliRunner

from cli.app import app
from cli.display import _rule_frequency, render_batch_report
from cli.mock_engine import analyze_transaction
from cli.prompts import load_request, load_requests
from cli.theme import THEME


def test_analyze_json_batch_renders_compact_governance_dashboard() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["analyze", "simulations/sample.json"], color=False)

    assert result.exit_code == 0, result.output
    assert "Batch Governance Report" in result.output
    assert "Batch Decision Overview" in result.output
    assert "Request Decisions" in result.output
    assert "Approved" in result.output
    assert "Governance Runtime" in result.output
    assert "Decision-Triggering Rule Frequency" in result.output
    assert "Processed requests" in result.output
    assert "Skipped requests" in result.output
    assert "Governance completed successfully" in result.output
    assert "Processing chunks" not in result.output
    assert "Chunks Processed" not in result.output
    assert "Total runtime" not in result.output
    assert "AUD-001" not in result.output


def test_batch_report_groups_validation_failures_and_shows_rule_names(tmp_path: Path) -> None:
    payload = [
        {"request_id": "req-1", "user_id": "operator-1", "amount": 120000, "action": "merchant_payment"},
        {"request_id": "bad-row", "user_id": "operator-2", "amount": "not-a-number"},
        {"request_id": "req-2", "user_id": "operator-3", "amount": 250, "action": "merchant_payment"},
    ]
    source = tmp_path / "mixed.json"
    source.write_text(json.dumps(payload), encoding="utf-8")

    result = CliRunner().invoke(app, ["analyze", str(source)], color=False)

    assert result.exit_code == 0, result.output
    assert "Request" in result.output
    assert "User ID" in result.output
    assert "req-1" in result.output
    assert "operato" in result.output
    assert "POL-013" in result.output
    assert "High-Value" in result.output
    assert "Skipped Requests" in result.output
    assert "Row 2" in result.output
    assert "could not convert" in result.output
    assert "Skipped requests    1" in result.output


def test_rule_frequency_excludes_baseline_rules() -> None:
    results = [analyze_transaction(request) for request in load_requests(Path("simulations/sample.json"))]

    rule_ids = {rule_id for rule_id, _ in _rule_frequency(results)}

    assert all(not rule_id.endswith("-000") for rule_id in rule_ids)
    assert all(not rule_id.startswith("AUD-") for rule_id in rule_ids)


def test_batch_report_shows_chunk_progress_only_for_multiple_chunks() -> None:
    request = load_requests(Path("simulations/sample.json"))[0]
    result = analyze_transaction(request)
    console = Console(record=True, theme=THEME, width=160)

    render_batch_report(console, [request, request], [result, result], "large.json", [], chunks=2)

    output = console.export_text()
    assert "Chunks Processed" in output
    assert "2/2" in output


def test_sample_batch_is_mapped_to_existing_request_contracts() -> None:
    requests = load_requests(Path("simulations/sample.json"))
    request = requests[0]

    assert len(requests) == 88
    assert request.transaction.amount == 19000
    assert request.metadata["category"] == "travel_booking"
    assert request.context.location == "IN"


def test_engine_adapter_returns_render_ready_result() -> None:
    result = analyze_transaction(load_requests(Path("simulations/sample.json"))[0])

    assert result.final_decision == "APPROVE"
    assert len(result.expert_results) == 6


def test_natural_language_option_uses_provider_then_rule_pipeline(monkeypatch) -> None:
    request = load_requests(Path("simulations/sample.json"))[0]
    monkeypatch.setattr(
        "cli.commands.LocalMLXProvider",
        lambda: SimpleNamespace(generate_request=lambda _: request),
    )
    runner = CliRunner()

    result = runner.invoke(app, ["analyze", "--prompt", "Pay $1250 to Northstar Travel"], color=False)

    assert result.exit_code == 0, result.output
    assert "SentinelAI Governance Report" in result.output
    assert "Policy Expert" in result.output
    assert "Decision Evidence" in result.output
    assert "Audit Actions" in result.output


def test_directory_mode_renders_each_file_and_an_overall_summary() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["analyze", "--directory", "simulations"], color=False)

    assert result.exit_code == 0, result.output
    assert "Batch Governance Report · sample.json" in result.output
    assert "Directory Governance Summary" in result.output
