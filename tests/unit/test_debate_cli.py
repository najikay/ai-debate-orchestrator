"""Unit tests for DebateCLI.

TDD order:
    parse_args (missing topic / topic present / --config / --dry-run)
    → run (returns 0 / calls engine / prints verdict / prints cost report /
           dry-run / WatchdogError → 1)
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

from src.agents.father_agent import Verdict
from src.infrastructure.cost_reporter import CostSummary
from src.infrastructure.watchdog import WatchdogError
from src.ui.debate_cli import parse_args, run

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_verdict() -> Verdict:
    return Verdict(
        verdict_id="00000000-0000-0000-0000-000000000001",
        winner="pro_son",
        draw=False,
        reasoning="Pro Son demonstrated superior clarity and evidence quality.",
        turn_count=20,
        timestamp="2026-05-25T13:00:00+00:00",
    )


@pytest.fixture
def mock_summary() -> CostSummary:
    return CostSummary(
        per_agent={},
        total_usd=0.45,
        budget_cap_usd=2.00,
        utilisation_pct=22.5,
    )


# ---------------------------------------------------------------------------
# parse_args
# ---------------------------------------------------------------------------


def test_parse_args_exits_with_code_2_when_topic_is_missing() -> None:
    with patch.object(sys, "argv", ["debate"]):
        with pytest.raises(SystemExit) as exc:
            parse_args()
    assert exc.value.code == 2


def test_parse_args_returns_namespace_with_topic_string() -> None:
    with patch.object(sys, "argv", ["debate", "--topic", "AI ethics"]):
        args = parse_args()
    assert args.topic == "AI ethics"


def test_parse_args_accepts_optional_config_flag() -> None:
    with patch.object(sys, "argv", ["debate", "--topic", "x", "--config", "my/"]):
        args = parse_args()
    assert args.config == "my/"


def test_parse_args_accepts_optional_dry_run_flag() -> None:
    with patch.object(sys, "argv", ["debate", "--topic", "x", "--dry-run"]):
        args = parse_args()
    assert args.dry_run is True


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------


def _run_with_args(*argv, engine_mock=None, config_mock=None):
    """Helper: patch sys.argv + collaborators, call run(), return exit code."""
    with patch.object(sys, "argv", ["debate", *argv]), \
         patch("src.ui.debate_cli.DebateEngine", engine_mock or MagicMock()), \
         patch("src.ui.debate_cli.ConfigLoader", MagicMock()):
        return run()


def test_run_returns_0_on_successful_debate(mock_verdict, mock_summary) -> None:
    eng = MagicMock()
    eng.return_value.start.return_value = mock_verdict
    eng.return_value.cost_reporter.compute.return_value = mock_summary
    code = _run_with_args("--topic", "AI ethics", engine_mock=eng)
    assert code == 0


def test_run_calls_debate_engine_start_with_topic_string(
    mock_verdict, mock_summary
) -> None:
    eng = MagicMock()
    eng.return_value.start.return_value = mock_verdict
    eng.return_value.cost_reporter.compute.return_value = mock_summary
    _run_with_args("--topic", "AI ethics", engine_mock=eng)
    eng.return_value.start.assert_called_once_with("AI ethics")


def test_run_prints_verdict_output_to_stdout(
    mock_verdict, mock_summary, capsys
) -> None:
    eng = MagicMock()
    eng.return_value.start.return_value = mock_verdict
    eng.return_value.cost_reporter.compute.return_value = mock_summary
    _run_with_args("--topic", "AI ethics", engine_mock=eng)
    assert "VERDICT" in capsys.readouterr().out


def test_run_prints_cost_report_to_stdout(
    mock_verdict, mock_summary, capsys
) -> None:
    eng = MagicMock()
    eng.return_value.start.return_value = mock_verdict
    eng.return_value.cost_reporter.compute.return_value = mock_summary
    _run_with_args("--topic", "AI ethics", engine_mock=eng)
    assert "COST" in capsys.readouterr().out


def test_run_dry_run_validates_config_without_calling_llm_api(capsys) -> None:
    eng = MagicMock()
    _run_with_args("--topic", "AI ethics", "--dry-run", engine_mock=eng)
    eng.return_value.start.assert_not_called()


def test_run_dry_run_prints_config_loaded_message(capsys) -> None:
    _run_with_args("--topic", "AI ethics", "--dry-run")
    assert "config" in capsys.readouterr().out.lower()


def test_run_returns_1_on_watchdog_error(mock_summary) -> None:
    eng = MagicMock()
    eng.return_value.start.side_effect = WatchdogError("hung")
    code = _run_with_args("--topic", "AI ethics", engine_mock=eng)
    assert code == 1
