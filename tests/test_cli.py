from pathlib import Path
from types import SimpleNamespace

from typer.testing import CliRunner

from cli.app import app
from cli.mock_engine import analyze_transaction
from cli.prompts import load_request


def test_analyze_sample_renders_governance_report() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["analyze", "simulations/sample.json"], color=False)

    assert result.exit_code == 0, result.output
    assert "SentinelAI Governance Report" in result.output
    assert "Policy Expert" in result.output
    assert "Final Decision" in result.output
    assert "Performance Metrics" in result.output


def test_sample_is_mapped_to_existing_request_contract() -> None:
    request = load_request(Path("simulations/sample.json"))

    assert request.transaction.amount == 1250.75
    assert request.metadata["category"] == "travel"
    assert request.context.location == "US"


def test_engine_adapter_returns_render_ready_result() -> None:
    result = analyze_transaction(load_request(Path("simulations/sample.json")))

    assert result.final_decision == "APPROVE"
    assert len(result.expert_results) == 6


def test_natural_language_option_uses_provider_then_rule_pipeline(monkeypatch) -> None:
    request = load_request(Path("simulations/sample.json"))
    monkeypatch.setattr(
        "cli.commands.LocalMLXProvider",
        lambda: SimpleNamespace(generate_request=lambda _: request),
    )
    runner = CliRunner()

    result = runner.invoke(app, ["analyze", "--prompt", "Pay $1250 to Northstar Travel"], color=False)

    assert result.exit_code == 0, result.output
    assert "SentinelAI Governance Report" in result.output
    assert "Policy Expert" in result.output
