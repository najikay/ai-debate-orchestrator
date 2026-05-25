"""Unit tests for CostReporter.

TDD order:
    __init__ (stores pricing / budget_cap)
    → record_usage (new entry / accumulate)
    → compute (total_usd / per-agent / zero / utilisation_pct)
    → print_report (non-empty / agent names / total line / utilisation)
"""

import pytest

from src.infrastructure.cost_reporter import CostReporter

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_pricing() -> dict:
    """Pricing with round numbers for easy mental arithmetic."""
    return {
        "schema_version": "1.0",
        "models": {
            "test-model": {"input_per_1k": 0.001, "output_per_1k": 0.002},
        },
    }


@pytest.fixture
def reporter(mock_pricing: dict) -> CostReporter:
    return CostReporter(mock_pricing, budget_cap_usd=2.00)


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------


def test_cost_reporter_init_stores_pricing(
    reporter: CostReporter, mock_pricing: dict
) -> None:
    """The pricing dict is retained internally."""
    assert reporter._pricing == mock_pricing


def test_cost_reporter_init_stores_budget_cap(reporter: CostReporter) -> None:
    """budget_cap_usd is stored as an attribute."""
    assert reporter.budget_cap_usd == 2.00


# ---------------------------------------------------------------------------
# record_usage
# ---------------------------------------------------------------------------


def test_record_usage_creates_new_entry_for_first_call(
    reporter: CostReporter,
) -> None:
    """record_usage creates a fresh record for a previously unseen agent."""
    reporter.record_usage("agent-x", "test-model", 100, 50)
    assert "agent-x" in reporter._records


def test_record_usage_accumulates_prompt_tokens_for_agent(
    reporter: CostReporter,
) -> None:
    """Repeated calls accumulate prompt_tokens for the same agent."""
    reporter.record_usage("agent-x", "test-model", 100, 0)
    reporter.record_usage("agent-x", "test-model", 200, 0)
    assert reporter._records["agent-x"].prompt_tokens == 300


def test_record_usage_accumulates_completion_tokens_for_agent(
    reporter: CostReporter,
) -> None:
    """Repeated calls accumulate completion_tokens for the same agent."""
    reporter.record_usage("agent-x", "test-model", 0, 40)
    reporter.record_usage("agent-x", "test-model", 0, 60)
    assert reporter._records["agent-x"].completion_tokens == 100


def test_record_usage_accumulates_tokens_across_multiple_calls(
    reporter: CostReporter,
) -> None:
    """Token tallies after three calls match the running sum."""
    reporter.record_usage("agent-x", "test-model", 100, 50)
    reporter.record_usage("agent-x", "test-model", 200, 100)
    reporter.record_usage("agent-x", "test-model", 300, 150)
    assert reporter._records["agent-x"].prompt_tokens == 600
    assert reporter._records["agent-x"].completion_tokens == 300


# ---------------------------------------------------------------------------
# compute
# ---------------------------------------------------------------------------


def test_compute_returns_correct_total_usd(reporter: CostReporter) -> None:
    """total_usd matches manual calculation: (1000*0.001 + 2000*0.002)/1000."""
    # 1000 prompt tokens → $0.001, 2000 completion tokens → $0.004 → $0.005
    reporter.record_usage("a1", "test-model", 1000, 2000)
    summary = reporter.compute()
    assert abs(summary.total_usd - 0.005) < 1e-9


def test_compute_per_agent_costs_sum_to_session_total(
    reporter: CostReporter,
) -> None:
    """Sum of per-agent USD equals CostSummary.total_usd."""
    reporter.record_usage("a1", "test-model", 1000, 500)
    reporter.record_usage("a2", "test-model", 500, 250)
    summary = reporter.compute()
    per_agent_sum = sum(u.cost_usd for u in summary.per_agent.values())
    assert abs(per_agent_sum - summary.total_usd) < 1e-9


def test_compute_returns_zero_summary_when_no_usage_recorded(
    reporter: CostReporter,
) -> None:
    """compute on a fresh reporter returns zero totals."""
    summary = reporter.compute()
    assert summary.total_usd == 0.0
    assert summary.utilisation_pct == 0.0


def test_compute_calculates_utilisation_pct_correctly(
    reporter: CostReporter,
) -> None:
    """utilisation_pct == total_usd / budget_cap_usd * 100."""
    # $0.005 cost, $2.00 cap → 0.25 %
    reporter.record_usage("a1", "test-model", 1000, 2000)
    summary = reporter.compute()
    expected_pct = (summary.total_usd / 2.00) * 100
    assert abs(summary.utilisation_pct - expected_pct) < 1e-9


# ---------------------------------------------------------------------------
# print_report
# ---------------------------------------------------------------------------


def test_print_report_writes_non_empty_output(
    reporter: CostReporter, capsys: pytest.CaptureFixture
) -> None:
    """print_report outputs at least one non-blank line."""
    reporter.record_usage("a1", "test-model", 1000, 500)
    reporter.print_report(reporter.compute())
    out = capsys.readouterr().out
    assert out.strip()


def test_print_report_output_contains_each_agent_name(
    reporter: CostReporter, capsys: pytest.CaptureFixture
) -> None:
    """Each agent_id appears at least once in the printed output."""
    reporter.record_usage("agent-alpha", "test-model", 100, 50)
    reporter.record_usage("agent-beta", "test-model", 200, 100)
    reporter.print_report(reporter.compute())
    out = capsys.readouterr().out
    assert "agent-alpha" in out
    assert "agent-beta" in out


def test_print_report_output_contains_total_usd_line(
    reporter: CostReporter, capsys: pytest.CaptureFixture
) -> None:
    """The word 'total' (case-insensitive) appears in the printed output."""
    reporter.record_usage("a1", "test-model", 1000, 500)
    reporter.print_report(reporter.compute())
    out = capsys.readouterr().out
    assert "total" in out.lower()


def test_print_report_output_contains_budget_utilisation_percentage(
    reporter: CostReporter, capsys: pytest.CaptureFixture
) -> None:
    """The printed output includes a '%' character for utilisation."""
    reporter.record_usage("a1", "test-model", 1000, 500)
    reporter.print_report(reporter.compute())
    out = capsys.readouterr().out
    assert "%" in out
