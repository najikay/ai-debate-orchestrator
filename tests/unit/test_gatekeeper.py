"""Unit tests for Gatekeeper.

TDD order:
    __init__ → dispatch (happy / usage / queues)
    → _enforce_limits (allows / blocks)
    → _enqueue (add / full)
    → _dequeue (fifo / empty)
    → get_usage (known / unknown / thread-safe)
"""

import threading
import time
from unittest.mock import patch

import pytest

from src.infrastructure.gatekeeper import (
    APIRequest,
    APIResponse,
    Gatekeeper,
    QueueFullError,
    UsageStats,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_rate_limits() -> dict:
    """Rate-limits with rpm=2 so rate-limiting is easy to trigger in tests."""
    return {
        "schema_version": "1.0",
        "models": {"test-model": {"rpm": 2, "tpm": 1000}},
        "web_search": {"rpm": 5},
    }


@pytest.fixture
def gatekeeper(mock_rate_limits: dict) -> Gatekeeper:
    return Gatekeeper(mock_rate_limits)


@pytest.fixture
def sample_request() -> APIRequest:
    return APIRequest(agent_id="agent-1", model="test-model", payload={})


@pytest.fixture
def mock_response() -> APIResponse:
    return APIResponse(content="hello", prompt_tokens=10, completion_tokens=5)


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------


def test_gatekeeper_init_creates_empty_queue(gatekeeper: Gatekeeper) -> None:
    """queue is an empty deque after construction."""
    assert len(gatekeeper.queue) == 0


def test_gatekeeper_init_stores_rate_limits(
    gatekeeper: Gatekeeper, mock_rate_limits: dict
) -> None:
    """Rate limits dict is retained internally."""
    assert gatekeeper._rl == mock_rate_limits


# ---------------------------------------------------------------------------
# dispatch — happy path
# ---------------------------------------------------------------------------


def test_dispatch_returns_api_response(
    gatekeeper: Gatekeeper, sample_request: APIRequest, mock_response: APIResponse
) -> None:
    """dispatch returns the APIResponse produced by _make_api_call."""
    with patch.object(gatekeeper, "_make_api_call", return_value=mock_response):
        result = gatekeeper.dispatch(sample_request)
    assert result == mock_response


def test_dispatch_records_token_usage_for_agent(
    gatekeeper: Gatekeeper, sample_request: APIRequest, mock_response: APIResponse
) -> None:
    """Token counts from the response are accumulated for the agent."""
    with patch.object(gatekeeper, "_make_api_call", return_value=mock_response):
        gatekeeper.dispatch(sample_request)
    stats = gatekeeper.get_usage("agent-1")
    assert stats.prompt_tokens == 10
    assert stats.completion_tokens == 5
    assert stats.total_tokens == 15


def test_dispatch_queues_request_when_rate_limit_enforced(
    gatekeeper: Gatekeeper, sample_request: APIRequest, mock_response: APIResponse
) -> None:
    """When the RPM bucket is full, dispatch enqueues the request before processing."""
    now = time.monotonic()
    gatekeeper._times["test-model"] = [now, now]  # rpm=2 → bucket full

    with patch.object(gatekeeper, "_make_api_call", return_value=mock_response):
        # Prevent the actual sleep so the test runs instantly.
        with patch.object(gatekeeper, "_enforce_limits"):
            with patch.object(gatekeeper, "_enqueue", wraps=gatekeeper._enqueue) as spy:
                gatekeeper.dispatch(sample_request)

    spy.assert_called_once_with(sample_request)


# ---------------------------------------------------------------------------
# _enforce_limits
# ---------------------------------------------------------------------------


def test_enforce_limits_allows_call_within_rpm(gatekeeper: Gatekeeper) -> None:
    """No sleep when the RPM bucket has capacity."""
    with patch("src.infrastructure.gatekeeper.time.sleep") as mock_sleep:
        gatekeeper._enforce_limits("test-model")  # fresh bucket
    mock_sleep.assert_not_called()


def test_enforce_limits_blocks_when_rpm_bucket_depleted(
    gatekeeper: Gatekeeper,
) -> None:
    """time.sleep is called with a positive value when the bucket is exhausted."""
    now = time.monotonic()
    gatekeeper._times["test-model"] = [now, now]  # rpm=2 → full
    with patch("src.infrastructure.gatekeeper.time.sleep") as mock_sleep:
        gatekeeper._enforce_limits("test-model")
    mock_sleep.assert_called_once()
    assert mock_sleep.call_args[0][0] > 0


# ---------------------------------------------------------------------------
# _enqueue
# ---------------------------------------------------------------------------


def test_enqueue_adds_request_to_deque(
    gatekeeper: Gatekeeper, sample_request: APIRequest
) -> None:
    """_enqueue appends the request and increases queue length by one."""
    gatekeeper._enqueue(sample_request)
    assert len(gatekeeper.queue) == 1
    assert gatekeeper.queue[0] == sample_request


def test_enqueue_raises_queue_full_error_when_depth_exceeds_50(
    gatekeeper: Gatekeeper, sample_request: APIRequest
) -> None:
    """QueueFullError raised when the queue already holds 50 items."""
    for _ in range(50):
        gatekeeper.queue.append(sample_request)
    with pytest.raises(QueueFullError):
        gatekeeper._enqueue(sample_request)


# ---------------------------------------------------------------------------
# _dequeue
# ---------------------------------------------------------------------------


def test_dequeue_returns_oldest_request_fifo(
    gatekeeper: Gatekeeper, sample_request: APIRequest
) -> None:
    """_dequeue returns requests in FIFO order."""
    req_a = APIRequest("a", "test-model", {})
    req_b = APIRequest("b", "test-model", {})
    gatekeeper._enqueue(req_a)
    gatekeeper._enqueue(req_b)
    assert gatekeeper._dequeue() == req_a
    assert gatekeeper._dequeue() == req_b


def test_dequeue_raises_when_queue_is_empty(gatekeeper: Gatekeeper) -> None:
    """IndexError raised when dequeuing from an empty queue."""
    with pytest.raises(IndexError):
        gatekeeper._dequeue()


# ---------------------------------------------------------------------------
# get_usage
# ---------------------------------------------------------------------------


def test_get_usage_returns_correct_stats_for_known_agent(
    gatekeeper: Gatekeeper, sample_request: APIRequest, mock_response: APIResponse
) -> None:
    """Usage stats match the accumulated tokens for a dispatched agent."""
    with patch.object(gatekeeper, "_make_api_call", return_value=mock_response):
        gatekeeper.dispatch(sample_request)
        gatekeeper.dispatch(sample_request)
    stats = gatekeeper.get_usage("agent-1")
    assert stats.prompt_tokens == 20
    assert stats.completion_tokens == 10
    assert stats.total_tokens == 30


def test_get_usage_returns_zero_stats_for_unknown_agent(
    gatekeeper: Gatekeeper,
) -> None:
    """UsageStats with all-zero fields returned for agents with no history."""
    stats = gatekeeper.get_usage("never-dispatched")
    assert stats == UsageStats(0, 0, 0)


# ---------------------------------------------------------------------------
# Thread safety
# ---------------------------------------------------------------------------


def test_gatekeeper_is_thread_safe(
    gatekeeper: Gatekeeper, mock_response: APIResponse
) -> None:
    """Concurrent dispatches do not corrupt cumulative usage totals."""
    n_threads = 20

    def do_dispatch() -> None:
        req = APIRequest("agent-ts", "test-model", {})
        with patch.object(gatekeeper, "_make_api_call", return_value=mock_response):
            with patch.object(gatekeeper, "_enforce_limits"):
                gatekeeper.dispatch(req)

    threads = [threading.Thread(target=do_dispatch) for _ in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    stats = gatekeeper.get_usage("agent-ts")
    assert stats.prompt_tokens == n_threads * 10
    assert stats.completion_tokens == n_threads * 5
    assert stats.total_tokens == n_threads * 15
