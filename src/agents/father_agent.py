"""FatherAgent — moderator, router, and judge of the debate."""

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from src.agents.base_agent import BaseAgent, DebateMessage

_MIN_TURNS: int = 20
_VALID_SENDERS: frozenset[str] = frozenset({"father", "pro_son", "con_son"})
_VALID_RECIPIENTS: frozenset[str] = frozenset({"pro_son", "con_son"})

_RUBRIC_TEMPLATE = (
    "You are the debate judge. Score each debater on:\n"
    "1. Clarity (1-10): How clearly were arguments expressed?\n"
    "2. Evidence Quality (1-10): How well were claims supported by cited sources?\n"
    "3. Logical Consistency (1-10): Were arguments internally consistent"
    " across all turns?\n"
    "\nTranscript:\n{transcript}\n\n"
    "Return ONLY valid JSON matching this schema:\n"
    '{{\n  "scores": {{\n'
    '    "pro_son": {{"clarity": N, "evidence": N, "logic": N, "total": N}},\n'
    '    "con_son":  {{"clarity": N, "evidence": N, "logic": N, "total": N}}\n'
    "  }},\n"
    '  "winner": "pro_son" | "con_son",\n'
    '  "draw": false,\n'
    '  "reasoning": "<min 50 chars>"\n}}'
)


class NotEnoughTurnsError(Exception):
    """Raised when evaluate() is called before 20 turns have elapsed."""


@dataclass
class Verdict:
    """Final debate outcome with winner, reasoning, and turn count."""

    verdict_id: str
    winner: str
    draw: bool
    reasoning: str
    turn_count: int
    timestamp: str


class FatherAgent(BaseAgent):
    """Moderator agent: routes messages and issues the final Verdict.

    Args:
        gatekeeper: Shared Gatekeeper for all API calls.
        config: Parsed ``setup.json`` dict.
        model: Claude model string.
    """

    def __init__(self, gatekeeper, config: dict, model: str) -> None:
        super().__init__(
            agent_id="father",
            role="father",
            gatekeeper=gatekeeper,
            config=config,
            model=model,
        )

    def build_prompt(self, context: dict) -> str:
        return context.get("prompt", "")

    def act(self, context: dict) -> DebateMessage:
        return self.open_debate(context.get("topic", ""))

    def open_debate(self, topic: str) -> DebateMessage:
        """Return the opening DebateMessage addressed to pro_son."""
        return DebateMessage(
            message_id=str(uuid.uuid4()),
            sender="father",
            recipient="pro_son",
            turn=1,
            content=f"Debate topic: {topic}. Pro Son, please open the argument.",
            sources=[],
            token_count=0,
            timestamp=datetime.now(tz=timezone.utc).isoformat(),
        )

    def _validate_message(self, msg: DebateMessage) -> bool:
        """Return True if *msg* passes Father-level constraints."""
        if not msg.content:
            return False
        if msg.sender not in _VALID_SENDERS:
            return False
        if msg.turn % 3 == 0 and not msg.sources:
            return False
        return True

    def route(self, msg: DebateMessage) -> str:
        """Return the target agent identifier for *msg*."""
        if msg.recipient not in _VALID_RECIPIENTS:
            raise ValueError(f"Invalid recipient: {msg.recipient!r}")
        return msg.recipient

    def _check_min_turns(self, state) -> bool:
        return len(state.transcript) >= _MIN_TURNS

    def _score_persuasiveness(self, transcript: list) -> dict:
        """Ask the LLM to score both debaters; return parsed scores dict."""
        excerpt = " | ".join(m.content for m in transcript)
        raw = self.call_api(_RUBRIC_TEMPLATE.format(transcript=excerpt))
        return json.loads(raw)["scores"]

    def evaluate(self, state) -> Verdict:
        """Score the debate and declare a winner (never a draw).

        Raises:
            NotEnoughTurnsError: If fewer than 20 turns have elapsed.
        """
        if not self._check_min_turns(state):
            raise NotEnoughTurnsError(
                f"Need {_MIN_TURNS} turns; only {len(state.transcript)} so far."
            )
        scores = self._score_persuasiveness(state.transcript)
        pro_t = scores["pro_son"]["total"]
        con_t = scores["con_son"]["total"]
        winner = (
            self._tiebreak(state.transcript)
            if pro_t == con_t
            else ("pro_son" if pro_t > con_t else "con_son")
        )
        reasoning = (
            f"pro_son scored {pro_t}/30, con_son scored {con_t}/30. "
            f"Winner: {winner} based on cumulative rubric evaluation."
        )
        return Verdict(
            verdict_id=str(uuid.uuid4()),
            winner=winner,
            draw=False,
            reasoning=reasoning,
            turn_count=len(state.transcript),
            timestamp=datetime.now(tz=timezone.utc).isoformat(),
        )

    def _tiebreak(self, transcript: list) -> str:
        """Break a scoring tie using persuasive momentum in the last 4 turns."""
        last = transcript[-4:] if len(transcript) >= 4 else transcript
        pro = sum(len(m.content) for m in last if m.sender == "pro_son")
        con = sum(len(m.content) for m in last if m.sender == "con_son")
        return "pro_son" if pro >= con else "con_son"
