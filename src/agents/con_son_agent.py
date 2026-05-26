"""ConSonAgent — negative debater that argues AGAINST the debate topic.

Must maintain the con position at all times. Responses that express
support are rejected and retried up to twice before raising
:class:`~src.agents.base_agent.AgentFailureError`.
"""

import uuid
from datetime import datetime, timezone

from src.agents.base_agent import AgentFailureError, BaseAgent, DebateMessage
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

    # ------------------------------------------------------------------
    # BaseAgent abstract interface
    # ------------------------------------------------------------------

    def build_prompt(self, context: dict) -> str:
        """Build a con-position prompt embedding the debate topic.

        Args:
            context: Dict with ``topic`` (str) and ``message`` (DebateMessage).

        Returns:
            Prompt string instructing the agent to oppose the topic.
        """
        topic = context.get("topic", "")
        msg = context.get("message")
        prior = msg.content if msg else ""
        return (
            f"You are the CON debater. You must argue strongly AGAINST: '{topic}'.\n"
            f"You MUST oppose and argue against this position.\n"
            f"Previous message: {prior}\n"
            f"Respond with a compelling argument that opposes the topic."
        )

    def act(self, context: dict) -> DebateMessage:
        """Produce the next con-side argument."""
        msg = context.get("message")
        return self.generate_argument(msg)

    # ------------------------------------------------------------------
    # Public domain method
    # ------------------------------------------------------------------

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
            content = self.call_api(prompt_str)
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

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _enforce_position(self, content: str) -> str:
        """Verify *content* expresses a con stance; raise if it does not."""
        lower = content.lower()
        if any(signal in lower for signal in _PRO_SIGNALS):
            raise _PositionError("Content expresses a pro stance.")
        return content

    def _gather_sources(self, topic: str) -> list[str]:
        """Run the first available skill and collect its snippets as sources."""
        if not self.skills:
            return []
        result = self.skills[0].execute(topic)
        return result.snippets
