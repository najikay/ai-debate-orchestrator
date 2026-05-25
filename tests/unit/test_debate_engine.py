"""Unit tests for DebateEngine.

TDD order:
    __init__ (agents created / state_manager / watchdog)
    → _run_turn_loop (min turns / alternation / record_message / route called)
    → _check_budget (below cap / above cap / 90% warning)
    → _handle_watchdog_error (logs error / appends event / dumps JSON)
    → start (returns Verdict / open_debate called / draw=False / budget / watchdog)
"""

import logging
from unittest.mock import patch

import pytest

from src.agents.base_agent import DebateMessage
from src.agents.father_agent import Verdict
from src.engine.debate_engine import DebateEngine
from src.infrastructure.cost_reporter import CostSummary
from src.infrastructure.watchdog import WatchdogError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _msg(sender="pro_son", recipient="father", turn=1) -> DebateMessage:
    return DebateMessage(
        message_id="00000000-0000-0000-0000-000000000001",
        sender=sender,
        recipient=recipient,
        turn=turn,
        content="Argument text.",
        sources=["https://example.com"],
        token_count=10,
        timestamp="2026-05-25T12:00:00+00:00",
    )


def _verdict() -> Verdict:
    return Verdict(
        verdict_id="00000000-0000-0000-0000-000000000002",
        winner="pro_son",
        draw=False,
        reasoning="Pro Son demonstrated superior clarity and evidence quality.",
        turn_count=20,
        timestamp="2026-05-25T13:00:00+00:00",
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_config() -> dict:
    return {
        "schema_version": "1.0",
        "debate": {"min_turns_per_side": 2, "max_session_cost_usd": 2.00},
        "agents": {
            "father": {"model": "test-model"},
            "pro_son": {"model": "test-model"},
            "con_son": {"model": "test-model"},
        },
        "watchdog": {"timeout_seconds": 30, "max_retries": 1},
    }


@pytest.fixture
def engine(mock_config: dict) -> DebateEngine:
    """DebateEngine with all collaborators replaced by MagicMocks."""
    with patch("src.engine.debate_engine.FatherAgent") as MockFather, \
         patch("src.engine.debate_engine.ProSonAgent") as MockPro, \
         patch("src.engine.debate_engine.ConSonAgent") as MockCon, \
         patch("src.engine.debate_engine.StateManager") as MockSM, \
         patch("src.engine.debate_engine.Watchdog") as MockWD, \
         patch("src.engine.debate_engine.CostReporter") as MockCR, \
         patch("src.engine.debate_engine.Gatekeeper"):

        eng = DebateEngine(mock_config)

        # Expose mocks for assertion
        eng._mock_father = MockFather.return_value
        eng._mock_pro = MockPro.return_value
        eng._mock_con = MockCon.return_value
        eng._mock_sm = MockSM.return_value
        eng._mock_wd = MockWD.return_value
        eng._mock_cr = MockCR.return_value

        # Wire default happy-path returns
        opening = _msg(sender="father", recipient="pro_son", turn=1)
        eng._mock_father.open_debate.return_value = opening
        eng._mock_father.route.side_effect = lambda m: m.recipient
        eng._mock_father._check_min_turns.return_value = True
        eng._mock_father.evaluate.return_value = _verdict()
        eng._mock_father._validate_message.return_value = True
        eng._mock_pro.generate_argument.return_value = _msg("pro_son", "father", 2)
        eng._mock_con.generate_argument.return_value = _msg("con_son", "father", 3)
        eng._mock_sm.state.topic = "AI ethics"
        eng._mock_sm.state.status = "IN_PROGRESS"
        eng._mock_sm.state.events = []
        eng._mock_sm.get_turn_count.return_value = 4
        eng._mock_sm.to_json.return_value = '{"topic": "AI ethics"}'

        low_cost = CostSummary(
            per_agent={}, total_usd=0.10, budget_cap_usd=2.00, utilisation_pct=5.0
        )
        eng._mock_cr.compute.return_value = low_cost

    return eng


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------


def test_debate_engine_init_creates_father_agent(engine: DebateEngine) -> None:
    """father attribute is set after __init__."""
    assert engine.father is not None


def test_debate_engine_init_creates_pro_son_agent(engine: DebateEngine) -> None:
    """pro_son attribute is set after __init__."""
    assert engine.pro_son is not None


def test_debate_engine_init_creates_con_son_agent(engine: DebateEngine) -> None:
    """con_son attribute is set after __init__."""
    assert engine.con_son is not None


def test_debate_engine_init_creates_state_manager(engine: DebateEngine) -> None:
    """state_manager attribute is set after __init__."""
    assert engine.state_manager is not None


def test_debate_engine_init_creates_watchdog_with_configured_timeout(
    engine: DebateEngine, mock_config: dict
) -> None:
    """watchdog attribute is set after __init__."""
    assert engine.watchdog is not None


# ---------------------------------------------------------------------------
# _run_turn_loop
# ---------------------------------------------------------------------------


def test_run_turn_loop_executes_at_least_min_turns(engine: DebateEngine) -> None:
    """generate_argument is called at least min_turns_per_side × 2 times total."""
    engine._run_turn_loop(min_turns=2)
    total = (engine.pro_son.generate_argument.call_count
             + engine.con_son.generate_argument.call_count)
    assert total >= 4  # 2 per side


def test_run_turn_loop_alternates_pro_son_and_con_son(engine: DebateEngine) -> None:
    """Pro Son goes before Con Son in every round."""
    engine._run_turn_loop(min_turns=2)
    assert engine.pro_son.generate_argument.call_count >= 1
    assert engine.con_son.generate_argument.call_count >= 1


def test_run_turn_loop_calls_record_message_after_every_turn(
    engine: DebateEngine,
) -> None:
    """state_manager.record_message is called for every agent turn."""
    engine._run_turn_loop(min_turns=2)
    # 2 rounds × 2 agents = 4 calls minimum
    assert engine.state_manager.record_message.call_count >= 4


def test_run_turn_loop_routes_all_responses_through_father(
    engine: DebateEngine,
) -> None:
    """father.route is called for each agent response."""
    engine._run_turn_loop(min_turns=2)
    assert engine.father.route.call_count >= 4


# ---------------------------------------------------------------------------
# _check_budget
# ---------------------------------------------------------------------------


def test_check_budget_returns_false_when_cost_below_cap(
    engine: DebateEngine,
) -> None:
    """Returns False when total cost is below the budget cap."""
    assert engine._check_budget() is False


def test_check_budget_returns_true_when_cost_exceeds_cap(
    engine: DebateEngine,
) -> None:
    """Returns True when total cost meets or exceeds the cap."""
    over = CostSummary(
        per_agent={}, total_usd=2.50, budget_cap_usd=2.00, utilisation_pct=125.0
    )
    engine.cost_reporter.compute.return_value = over
    assert engine._check_budget() is True


def test_check_budget_logs_warning_at_90_percent_threshold(
    engine: DebateEngine, caplog: pytest.LogCaptureFixture
) -> None:
    """A WARNING is logged when utilisation_pct ≥ 90."""
    near = CostSummary(
        per_agent={}, total_usd=1.85, budget_cap_usd=2.00, utilisation_pct=92.5
    )
    engine.cost_reporter.compute.return_value = near
    with caplog.at_level(logging.WARNING):
        engine._check_budget()
    assert any("90" in r.message or "budget" in r.message.lower()
               for r in caplog.records)


# ---------------------------------------------------------------------------
# _handle_watchdog_error
# ---------------------------------------------------------------------------


def test_handle_watchdog_error_logs_error_to_logger(
    engine: DebateEngine, caplog: pytest.LogCaptureFixture
) -> None:
    """An ERROR-level log entry is emitted."""
    err = WatchdogError("timed out")
    with caplog.at_level(logging.ERROR):
        engine._handle_watchdog_error(err)
    assert any(r.levelno == logging.ERROR for r in caplog.records)


def test_handle_watchdog_error_appends_event_to_state(
    engine: DebateEngine,
) -> None:
    """An event dict is appended to state.events."""
    engine.state_manager.state.events = []
    engine._handle_watchdog_error(WatchdogError("timeout"))
    assert engine.state_manager.state.events


def test_handle_watchdog_error_saves_partial_state_json_to_logs(
    engine: DebateEngine,
) -> None:
    """to_json is called to capture partial state."""
    engine._handle_watchdog_error(WatchdogError("timeout"))
    engine.state_manager.to_json.assert_called()


# ---------------------------------------------------------------------------
# start
# ---------------------------------------------------------------------------


def test_start_returns_verdict_object(engine: DebateEngine) -> None:
    """start returns a Verdict instance."""
    verdict = engine.start("AI ethics")
    assert isinstance(verdict, Verdict)


def test_start_calls_father_open_debate_with_topic_string(
    engine: DebateEngine,
) -> None:
    """father.open_debate is called with the topic string."""
    engine.start("climate change")
    engine.father.open_debate.assert_called_once_with("climate change")


def test_start_verdict_draw_field_is_always_false(engine: DebateEngine) -> None:
    """The returned Verdict has draw=False."""
    verdict = engine.start("AI ethics")
    assert verdict.draw is False


def test_start_forces_early_evaluation_when_budget_cap_exceeded(
    engine: DebateEngine,
) -> None:
    """father.evaluate is called even when budget is exceeded mid-loop."""
    over = CostSummary(
        per_agent={}, total_usd=3.00, budget_cap_usd=2.00, utilisation_pct=150.0
    )
    engine.cost_reporter.compute.return_value = over
    verdict = engine.start("AI ethics")
    engine.father.evaluate.assert_called_once()
    assert verdict is not None


def test_start_propagates_watchdog_error_after_max_retries(
    engine: DebateEngine,
) -> None:
    """WatchdogError from the turn loop is handled and re-raised."""
    engine.pro_son.generate_argument.side_effect = WatchdogError("hung")
    with pytest.raises(WatchdogError):
        engine.start("AI ethics")
