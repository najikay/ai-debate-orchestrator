"""Unit tests for Watchdog.

TDD order:
    __init__ (timeout / retries)
    → run (happy / retry / double-timeout)
    → _kill_and_retry (cancels future / emits warning log)
"""

import logging
import time

import pytest

from src.infrastructure.watchdog import Watchdog, WatchdogError

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def wd() -> Watchdog:
    """Watchdog with a very short timeout so tests run fast."""
    return Watchdog(timeout_seconds=0.05, max_retries=1)


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------


def test_watchdog_init_sets_timeout_seconds(wd: Watchdog) -> None:
    """timeout_seconds is stored as an attribute."""
    assert wd.timeout_seconds == 0.05


def test_watchdog_init_sets_max_retries(wd: Watchdog) -> None:
    """max_retries is stored as an attribute."""
    assert wd.max_retries == 1


# ---------------------------------------------------------------------------
# run — happy path
# ---------------------------------------------------------------------------


def test_run_returns_result_when_function_completes_within_timeout(
    wd: Watchdog,
) -> None:
    """run returns the callable's return value when it finishes on time."""
    result = wd.run(lambda args: 42, {})
    assert result == 42


def test_run_passes_args_to_function(wd: Watchdog) -> None:
    """The args dict is forwarded to the callable."""
    result = wd.run(lambda args: args["x"] * 2, {"x": 7})
    assert result == 14


# ---------------------------------------------------------------------------
# run — retry
# ---------------------------------------------------------------------------


def test_run_retries_once_on_first_timeout(wd: Watchdog) -> None:
    """run retries after the first timeout and returns the second call's result."""
    calls = []

    def flaky(args):
        calls.append(1)
        if len(calls) == 1:
            time.sleep(0.2)  # will time out
        return "ok"

    result = wd.run(flaky, {})
    assert result == "ok"
    assert len(calls) == 2


# ---------------------------------------------------------------------------
# run — double timeout → WatchdogError
# ---------------------------------------------------------------------------


def test_run_raises_watchdog_error_on_two_consecutive_timeouts(
    wd: Watchdog,
) -> None:
    """WatchdogError is raised when every attempt times out."""

    def always_slow(args):
        time.sleep(0.2)

    with pytest.raises(WatchdogError):
        wd.run(always_slow, {})


# ---------------------------------------------------------------------------
# _kill_and_retry — warning log
# ---------------------------------------------------------------------------


def test_kill_and_retry_emits_warning_log_on_timeout(
    wd: Watchdog, caplog: pytest.LogCaptureFixture
) -> None:
    """A WARNING-level message is logged each time a timeout occurs."""

    def always_slow(args):
        time.sleep(0.2)

    with caplog.at_level(logging.WARNING, logger="src.infrastructure.watchdog"):
        with pytest.raises(WatchdogError):
            wd.run(always_slow, {})

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) >= 1
