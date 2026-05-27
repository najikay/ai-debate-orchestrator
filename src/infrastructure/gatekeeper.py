"""Gatekeeper — token-bucket rate limiting and FIFO request queuing.
Enforces per-model RPM limits using a 60-second rolling window.
Queues requests when the bucket is full (max depth: 50).
Tracks cumulative token usage per agent, thread-safely.
Unknown models fall back to the ``default`` entry or 60 RPM.
"""

import threading
import time
from collections import deque
from dataclasses import dataclass

from .llm_provider import LLMProvider, build_provider

MAX_QUEUE_DEPTH: int = 50
_WINDOW: float = 60.0
_DEFAULT_RPM: int = 60


class QueueFullError(Exception):
    """Raised when _enqueue is called on a full queue (depth == 50)."""


@dataclass
class APIRequest:
    """Attributes: agent_id, model, payload."""

    agent_id: str
    model: str
    payload: dict


@dataclass
class APIResponse:
    """Attributes: content, prompt_tokens, completion_tokens."""

    content: str
    prompt_tokens: int
    completion_tokens: int


@dataclass
class UsageStats:
    """Cumulative token usage for a single agent."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class Gatekeeper:
    """Rate-limits API calls and tracks per-agent token usage.

    Args:
        rate_limits: Parsed ``rate_limits.json``.  Unknown models fall back to
            the ``"default"`` key, or 60 RPM when that key is absent too.
        provider: Optional :class:`~src.infrastructure.llm_provider.LLMProvider`.
            Auto-detected from environment variables when *None*.

    Attributes:
        queue: FIFO deque of pending :class:`APIRequest` objects.
    """

    def __init__(
        self, rate_limits: dict, provider: LLMProvider | None = None
    ) -> None:
        self._rl: dict = rate_limits
        self.queue: deque[APIRequest] = deque()
        self._usage: dict[str, dict[str, int]] = {}
        self._times: dict[str, list[float]] = {}
        self._lock: threading.Lock = threading.Lock()
        self._provider: LLMProvider | None = provider

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def dispatch(self, request: APIRequest) -> APIResponse:
        """Rate-limit, optionally enqueue, then call the API."""
        limited = self._is_limited(request.model)
        if limited:
            self._enqueue(request)
        self._enforce_limits(request.model)
        if limited:
            self._dequeue()
        response = self._make_api_call(request)
        with self._lock:
            acc = self._usage.setdefault(request.agent_id, {"p": 0, "c": 0})
            acc["p"] += response.prompt_tokens
            acc["c"] += response.completion_tokens
        return response

    def get_usage(self, agent_id: str) -> UsageStats:
        """Return cumulative usage; zeros for unknown agents."""
        with self._lock:
            acc = self._usage.get(agent_id)
        if acc is None:
            return UsageStats(0, 0, 0)
        return UsageStats(acc["p"], acc["c"], acc["p"] + acc["c"])

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _rpm(self, model: str) -> int:
        """Look up RPM for *model*; fall back to default entry or 60."""
        cfg = self._rl["models"].get(model) or self._rl.get("default", {})
        return cfg.get("rpm", _DEFAULT_RPM)

    def _is_limited(self, model: str) -> bool:
        rpm = self._rpm(model)
        with self._lock:
            now = time.monotonic()
            window = [t for t in self._times.get(model, []) if now - t < _WINDOW]
            return len(window) >= rpm

    def _enforce_limits(self, model: str) -> None:
        """Sleep until the RPM bucket has a free slot, then record the call."""
        rpm = self._rpm(model)
        with self._lock:
            now = time.monotonic()
            window = [t for t in self._times.get(model, []) if now - t < _WINDOW]
            wait = (_WINDOW - (now - window[0])) if len(window) >= rpm else 0.0
        if wait > 0:
            time.sleep(wait)
        with self._lock:
            now = time.monotonic()
            window = [t for t in self._times.get(model, []) if now - t < _WINDOW]
            window.append(now)
            self._times[model] = window

    def _enqueue(self, request: APIRequest) -> None:
        if len(self.queue) >= MAX_QUEUE_DEPTH:
            raise QueueFullError(f"Queue full (max {MAX_QUEUE_DEPTH}).")
        self.queue.append(request)

    def _dequeue(self) -> APIRequest:
        if not self.queue:
            raise IndexError("Cannot dequeue from an empty queue.")
        return self.queue.popleft()

    def _make_api_call(self, request: APIRequest) -> APIResponse:  # pragma: no cover
        if self._provider is None:
            self._provider = build_provider()
        resp = self._provider.complete(
            model=request.model,
            prompt=request.payload["prompt"],
        )
        return APIResponse(
            content=resp.content,
            prompt_tokens=resp.prompt_tokens,
            completion_tokens=resp.completion_tokens,
        )
