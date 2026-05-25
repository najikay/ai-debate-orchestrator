"""Watchdog — thread-pool timeout and retry wrapper for agent callables.

Runs a callable in a :class:`~concurrent.futures.ThreadPoolExecutor`
with a fixed timeout.  On timeout it logs a WARNING and retries up to
*max_retries* times.  If every attempt exceeds the timeout it raises
:class:`WatchdogError`.
"""

import concurrent.futures
import logging

_logger = logging.getLogger(__name__)


class WatchdogError(Exception):
    """Raised when every attempt of a callable exceeds the timeout."""


class Watchdog:
    """Enforces per-call timeouts with configurable retries.

    Args:
        timeout_seconds: Maximum seconds a single call may run.
        max_retries: Number of additional attempts after the first timeout.
            With ``max_retries=1`` the callable is tried at most twice.

    Attributes:
        timeout_seconds: Per-call timeout limit.
        max_retries: Maximum number of retries after the first timeout.

    Example::

        wd = Watchdog(timeout_seconds=30, max_retries=1)
        result = wd.run(my_fn, {"prompt": "hello"})
    """

    def __init__(self, timeout_seconds: float, max_retries: int) -> None:
        self.timeout_seconds: float = timeout_seconds
        self.max_retries: int = max_retries

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, fn, args: dict):
        """Execute *fn(args)* with timeout enforcement and retries.

        Args:
            fn: Callable that accepts a single ``args`` dict.
            args: Argument dict forwarded to *fn*.

        Returns:
            Whatever *fn* returns on a successful call.

        Raises:
            WatchdogError: If every attempt times out.
        """
        attempts = 1 + self.max_retries
        for attempt in range(attempts):
            result = self._attempt(fn, args)
            if result is not _TIMEOUT:
                return result
            _logger.warning(
                "Watchdog: attempt %d/%d timed out after %.3fs",
                attempt + 1,
                attempts,
                self.timeout_seconds,
            )
        raise WatchdogError(
            f"Callable exceeded timeout ({self.timeout_seconds}s) "
            f"on all {attempts} attempt(s)."
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _attempt(self, fn, args: dict):
        """Run *fn(args)* in a thread; return sentinel on timeout."""
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(fn, args)
            try:
                return future.result(timeout=self.timeout_seconds)
            except concurrent.futures.TimeoutError:
                future.cancel()
                return _TIMEOUT


class _TimeoutSentinel:
    """Private sentinel object — returned by _attempt on timeout."""


_TIMEOUT = _TimeoutSentinel()
