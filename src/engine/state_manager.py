"""StateManager — in-memory debate state with JSON serialisation round-trip.

Lifecycle phases: INITIALIZATION → IN_PROGRESS → EVALUATION → TERMINATED.
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


@dataclass
class DebateState:
    """Full in-memory representation of a single debate session.

    Attributes:
        state_id: UUID string uniquely identifying this session.
        status: Lifecycle phase string.
        topic: The user-supplied debate topic.
        turn_count: Number of agent turns recorded.
        transcript: Ordered list of DebateMessage objects.
        verdict: Final Verdict object, or None until evaluation.
        events: List of event dicts appended during the session.
        cost_summary: CostSummary or None until session end.
        created_at: ISO-8601 timestamp of state creation.
        updated_at: ISO-8601 timestamp of the last mutation.
    """

    state_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "INITIALIZATION"
    topic: str = ""
    turn_count: int = 0
    transcript: list = field(default_factory=list)
    verdict: Any = None
    events: list = field(default_factory=list)
    cost_summary: Any = None
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)


class StateManager:
    """Manages a :class:`DebateState` through a debate session.

    Attributes:
        state: The live :class:`DebateState` instance.
        on_message: Optional callback fired on each new message.
            Useful for live printing (CLI) or SSE streaming (web).
    """

    def __init__(self) -> None:
        self.state: DebateState = DebateState()
        self.on_message: Optional[Callable] = None

    def record_message(self, msg) -> None:
        """Append *msg* to the transcript and increment the turn counter."""
        self.state.transcript.append(msg)
        self.state.turn_count += 1
        self.state.updated_at = _now()
        if self.state.status == "INITIALIZATION":
            self.state.status = "IN_PROGRESS"
        if self.on_message is not None:
            self.on_message(msg)

    def record_verdict(self, v) -> None:
        """Store the Verdict and mark the session TERMINATED.

        Raises:
            ValueError: If a verdict has already been recorded.
        """
        if self.state.verdict is not None:
            raise ValueError("A verdict has already been recorded for this session.")
        self.state.verdict = v
        self.state.status = "TERMINATED"
        self.state.updated_at = _now()

    def get_turn_count(self) -> int:
        """Return the current turn count."""
        return self.state.turn_count

    def to_json(self) -> str:
        """Serialise the current state to a JSON string."""
        def _serialise(obj):
            if hasattr(obj, "__dataclass_fields__"):
                return {k: _serialise(getattr(obj, k)) for k in obj.__dataclass_fields__}
            if isinstance(obj, list):
                return [_serialise(i) for i in obj]
            return obj
        return json.dumps(_serialise(self.state))

    def from_json(self, data: str) -> DebateState:
        """Restore a :class:`DebateState` from a JSON string.

        Raises:
            ValueError: If *data* is not valid JSON.
        """
        try:
            raw = json.loads(data)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON: {exc}") from exc
        state = DebateState()
        for key, val in raw.items():
            if hasattr(state, key):
                setattr(state, key, val)
        return state
