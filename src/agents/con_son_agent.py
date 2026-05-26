"""ConSonAgent — negative debater that argues AGAINST the debate topic."""

import json
import uuid
from datetime import datetime, timezone

from src.agents.base_agent import (
    AgentFailureError,
    BaseAgent,
    DebateMessage,
    _extract_json,
)
from src.skills.base_skill import AgentSkill

_MAX_RETRIES: int = 2

# Keywords that indicate the agent has drifted to a pro stance.
_PRO_SIGNALS: tuple[str, ...] = (
    "support",
    "advocate",
    "i agree",
    "wonderful",
    "greatly benefits",
)
_COT_SCHEMA: str = (
    '{"opponent_analysis":"core claim of opponent",'
    '"debate_strategy":"how you will refute it with logic and facts",'
    '"argument":"your rebuttal — max 3 paragraphs, sharp and factual"}'
)


class _PositionError(Exception):
    """Internal signal: content violates the assigned position."""


class ConSonAgent(BaseAgent):
    """Negative son agent — always argues AGAINST the debate topic.

    Args:
        gatekeeper: Shared Gatekeeper for all API calls.
        config: Parsed ``setup.json`` dict.
        skills: List of :class:`~src.skills.base_skill.AgentSkill` instances.
        model: Claude model string for API calls.

    Attributes:
        position: Always ``"con"``.
        skills: Tool instances available to this agent.
    """

    def __init__(
        self,
        gatekeeper,
        config: dict,
        skills: list[AgentSkill],
        model: str,
    ) -> None:
        super().__init__(
            agent_id="con_son",
            role="con",
            gatekeeper=gatekeeper,
            config=config,
            model=model,
        )
        self.position: str = "con"
        self.skills: list[AgentSkill] = skills

    def build_prompt(self, context: dict) -> str:
        """Return a CoT prompt with No-Surrender clause and JSON output schema."""
        topic = context.get("topic", "")
        msg = context.get("message")
        prior = msg.content if msg else ""
        return (
            f"You are the CON debater. You must argue strongly AGAINST: '{topic}'.\n"
            "NO SURRENDER: Never concede, agree with the opponent, or be neutral. "
            "Directly counter their points using sound logic and verified facts.\n"
            f"Opponent's last argument:\n{prior}\n\n"
            "Respond ONLY with valid JSON (no markdown fences):\n" + _COT_SCHEMA
        )

    def act(self, context: dict) -> DebateMessage:
        """Produce the next con-side argument."""
        msg = context.get("message")
        return self.generate_argument(msg)

    def generate_argument(
        self, prompt: DebateMessage, topic: str = ""
    ) -> DebateMessage:
        """Generate a con-position argument, retrying on position drift.

        Args:
            prompt: Incoming :class:`DebateMessage` from the Father.

        Returns:
            A new :class:`DebateMessage` with con-position content and sources.

        Raises:
            AgentFailureError: If position is violated on all attempts.
        """
        topic = topic or prompt.content
        sources = self._gather_sources(topic)
        prompt_str = self.build_prompt({"topic": topic, "message": prompt})

        for attempt in range(_MAX_RETRIES + 1):
            raw = self.call_api(prompt_str)
            content = self._extract_argument(raw)
            try:
                content = self._enforce_position(content)
                break
            except _PositionError:
                if attempt == _MAX_RETRIES:
                    raise AgentFailureError(
                        "ConSonAgent failed to maintain con position "
                        f"after {_MAX_RETRIES} retries."
                    )

        return DebateMessage(
            message_id=str(uuid.uuid4()),
            sender="con_son",
            recipient="father",
            turn=prompt.turn + 1,
            content=content,
            sources=sources,
            token_count=len(content.split()),
            timestamp=datetime.now(tz=timezone.utc).isoformat(),
        )

    def _enforce_position(self, content: str) -> str:
        """Verify *content* expresses a con stance; raise if it does not."""
        lower = content.lower()
        if any(signal in lower for signal in _PRO_SIGNALS):
            raise _PositionError("Content expresses a pro stance.")
        return content

    def _extract_argument(self, raw: str) -> str:
        """Extract ``argument`` field from CoT JSON; fall back to raw text."""
        try:
            data = json.loads(_extract_json(raw))
            return data.get("argument", raw) if isinstance(data, dict) else raw
        except json.JSONDecodeError:
            return raw

    def _gather_sources(self, topic: str) -> list[str]:
        """Run the first available skill and collect its snippets as sources."""
        if not self.skills:
            return []
        result = self.skills[0].execute(topic)
        return result.snippets
