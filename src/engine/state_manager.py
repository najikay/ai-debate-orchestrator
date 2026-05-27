"""StateManager — in-memory debate state with JSON serialisation round-trip."""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


@dataclass
class DebateState:
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
    def __init__(self) -> None:
        self.state: DebateState = DebateState()
        self.on_message = None  # callback for live printing

    def record_message(self, msg) -> None:
        self.state.transcript.append(msg)
        self.state.turn_count += 1
        self.state.updated_at = _now()
        if self.state.status == "INITIALIZATION":
            self.state.status = "IN_PROGRESS"
        if self.on_message is not None:
            self.on_message(msg)

    def record_verdict(self, v) -> None:
        if self.state.verdict is not None:
            raise ValueError("A verdict has already been recorded for this session.")
        self.state.verdict = v
        self.state.status = "TERMINATED"
        self.state.updated_at = _now()

    def get_turn_count(self) -> int:
        return self.state.turn_count

    def to_json(self) -> str:
        def _serialise(obj):
            if hasattr(obj, "__dataclass_fields__"):
                fields = obj.__dataclass_fields__
                return {k: _serialise(getattr(obj, k)) for k in fields}
            if isinstance(obj, list):
                return [_serialise(i) for i in obj]
            return obj
        return json.dumps(_serialise(self.state))

    def from_json(self, data: str) -> DebateState:
        try:
            raw = json.loads(data)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON: {exc}") from exc
        state = DebateState()
        for key, val in raw.items():
            if hasattr(state, key):
                setattr(state, key, val)
        return state
