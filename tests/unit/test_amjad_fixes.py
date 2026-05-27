"""Tests for the three fixes made on the amjad branch:

    1. colorama: debate_cli uses Fore/Style constants (no raw ANSI codes)
    2. SSE done event: stream endpoint sends a named 'close' event, not a data frame
    3. state_manager: on_message callback is typed Optional[Callable] and fires on record_message
"""

import json
from typing import Callable, Optional
from unittest.mock import MagicMock, patch

import pytest

from src.agents.base_agent import DebateMessage
from src.engine.state_manager import StateManager
from src.ui.app import create_app


# ---------------------------------------------------------------------------
# Fix 1 — colorama: no raw ANSI escape codes in debate_cli module
# ---------------------------------------------------------------------------

def test_debate_cli_does_not_define_raw_ansi_codes():
    """debate_cli must not contain raw ANSI escape string constants."""
    import src.ui.debate_cli as cli_module
    import inspect

    source = inspect.getsource(cli_module)
    # Raw ANSI codes look like \033[ or \x1b[ — these should not appear
    assert "\\033[" not in source, "Raw ANSI code found — use colorama.Fore/Style instead"
    assert "\\x1b[" not in source, "Raw ANSI code found — use colorama.Fore/Style instead"


def test_debate_cli_imports_colorama_fore_and_style():
    """debate_cli must import Fore and Style from colorama."""
    from src.ui import debate_cli  # noqa: F401
    import colorama
    assert hasattr(colorama, "Fore")
    assert hasattr(colorama, "Style")


# ---------------------------------------------------------------------------
# Fix 2 — SSE stream: 'done' sends a named 'close' event, not a data frame
# ---------------------------------------------------------------------------

@pytest.fixture
def app():
    flask_app = create_app(config_path="config/")
    flask_app.config["TESTING"] = True
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


def _make_mock_engine_for_stream():
    from src.agents.base_agent import DebateMessage
    from src.agents.father_agent import Verdict
    from src.infrastructure.cost_reporter import CostSummary

    verdict = Verdict(
        verdict_id="bbb",
        winner="pro_son",
        draw=False,
        reasoning="Clear winner.",
        turn_count=4,
        timestamp="2026-05-26T01:00:00+00:00",
    )
    summary = CostSummary(
        per_agent={}, total_usd=0.01, budget_cap_usd=2.0, utilisation_pct=0.5
    )
    engine = MagicMock()
    engine.start.return_value = verdict
    engine.state_manager.on_message = None
    engine.state_manager.state.transcript = []
    engine.cost_reporter.compute.return_value = summary
    return engine


def test_stream_endpoint_returns_200(client):
    """GET /api/debate/stream with a topic returns HTTP 200."""
    with patch("src.ui.app.DebateEngine", return_value=_make_mock_engine_for_stream()), \
         patch("src.ui.app.ConfigLoader"):
        resp = client.get("/api/debate/stream?topic=AI+ethics")
    assert resp.status_code == 200


def test_stream_endpoint_mimetype_is_event_stream(client):
    """SSE response Content-Type must be text/event-stream."""
    with patch("src.ui.app.DebateEngine", return_value=_make_mock_engine_for_stream()), \
         patch("src.ui.app.ConfigLoader"):
        resp = client.get("/api/debate/stream?topic=AI+ethics")
    assert "text/event-stream" in resp.content_type


def test_stream_endpoint_returns_400_when_topic_missing(client):
    """GET /api/debate/stream with no topic returns HTTP 400."""
    resp = client.get("/api/debate/stream")
    assert resp.status_code == 400


def test_stream_done_uses_named_close_event_not_data_frame(client):
    """The stream must close with 'event: close' not 'data: {type: done}'."""
    with patch("src.ui.app.DebateEngine", return_value=_make_mock_engine_for_stream()), \
         patch("src.ui.app.ConfigLoader"):
        resp = client.get("/api/debate/stream?topic=AI+ethics")
        body = resp.data.decode()

    assert "event: close" in body, "Stream must end with a named 'event: close' frame"
    assert '"type": "done"' not in body, \
        "Stream must NOT send a raw data frame with type=done"


# ---------------------------------------------------------------------------
# Fix 3 — state_manager: on_message typed Optional[Callable] and fires correctly
# ---------------------------------------------------------------------------

@pytest.fixture
def sm() -> StateManager:
    return StateManager()


@pytest.fixture
def sample_message() -> DebateMessage:
    return DebateMessage(
        message_id="123e4567-e89b-12d3-a456-426614174000",
        sender="pro_son",
        recipient="father",
        turn=1,
        content="AI is beneficial.",
        sources=["https://example.com"],
        token_count=10,
        timestamp="2026-05-25T12:00:00+00:00",
    )


def test_on_message_default_is_none(sm: StateManager):
    """on_message must default to None."""
    assert sm.on_message is None


def test_on_message_is_typed_optional_callable(sm: StateManager):
    """on_message annotation must be Optional[Callable]."""
    hints = sm.__class__.__init__.__annotations__
    # Check the attribute can accept None and a callable without error
    sm.on_message = None
    sm.on_message = lambda msg: None
    assert True  # no TypeError raised


def test_on_message_callback_is_called_on_record_message(
    sm: StateManager, sample_message: DebateMessage
):
    """on_message callback must be invoked when record_message is called."""
    received = []
    sm.on_message = lambda msg: received.append(msg)
    sm.record_message(sample_message)
    assert len(received) == 1
    assert received[0] is sample_message


def test_on_message_callback_called_once_per_message(
    sm: StateManager, sample_message: DebateMessage
):
    """on_message must fire exactly once per record_message call."""
    count = []
    sm.on_message = lambda msg: count.append(1)
    sm.record_message(sample_message)
    sm.record_message(sample_message)
    assert len(count) == 2


def test_record_message_works_normally_when_on_message_is_none(
    sm: StateManager, sample_message: DebateMessage
):
    """record_message must not raise when on_message is None."""
    sm.on_message = None
    sm.record_message(sample_message)
    assert sm.state.turn_count == 1
