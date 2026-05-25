"""StateManager — in-memory debate state with JSON serialisation round-trip.

Tracks transcript, turn count, verdict, and status through the four
lifecycle phases: INITIALIZATION → IN_PROGRESS → EVALUATION → TERMINATED.
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


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
    """Manages a :class:`DebateState` object through a debate session.

    Attributes:
        state: The live :class:`DebateState` instance.

    Example::

        sm = StateManager()
        sm.state.topic = "AI ethics"
        sm.record_message(msg)
        snapshot = sm.to_json()
    """

    def __init__(self) -> None:
        self.state: DebateState = DebateState()

    # ------------------------------------------------------------------
    # Mutation methods
    # ------------------------------------------------------------------

    def record_message(self, msg) -> None:
        """Append *msg* to the transcript and increment the turn counter.

        Args:
            msg: A DebateMessage (or compatible object) to record.
        """
        self.state.transcript.append(msg)
        self.state.turn_count += 1
        self.state.updated_at = _now()
        if self.state.status == "INITIALIZATION":
            self.state.status = "IN_PROGRESS"

    def record_verdict(self, v) -> None:
        """Store the debate Verdict and mark the session TERMINATED.

        Args:
            v: A :class:`~src.agents.father_agent.Verdict` object.

        Raises:
            ValueError: If a verdict has already been recorded.
        """
        if self.state.verdict is not None:
            raise ValueError("A verdict has already been recorded for this session.")
        self.state.verdict = v
        self.state.status = "TERMINATED"
        self.state.updated_at = _now()

    # ------------------------------------------------------------------
    # Query methods
    # ------------------------------------------------------------------

    def get_turn_count(self) -> int:
        """Return the current turn count."""
        return self.state.turn_count

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_json(self) -> str:
        """Serialise the current state to a JSON string.

        Returns:
            A JSON string representation of :attr:`state`.
        """
        def _serialise(obj):
            if hasattr(obj, "__dataclass_fields__"):
                return {
                    k: _serialise(getattr(obj, k))
                    for k in obj.__dataclass_fields__
                }
            if isinstance(obj, list):
                return [_serialise(i) for i in obj]
            return obj

        return json.dumps(_serialise(self.state))

    def from_json(self, data: str) -> DebateState:
        """Restore a :class:`DebateState` from a JSON string.

        Args:
            data: JSON string previously produced by :meth:`to_json`.

        Returns:
            A :class:`DebateState` populated with the deserialised fields.

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
