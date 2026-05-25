"""BaseAgent — abstract base for all debate agents.

Provides JSON parsing, schema validation against ``debate_message.json``,
and a ``call_api`` method that routes every LLM call through the
:class:`~src.infrastructure.gatekeeper.Gatekeeper`.
"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

import jsonschema

from src.infrastructure.gatekeeper import APIRequest, Gatekeeper

_SCHEMA_PATH: Path = (
    Path(__file__).parent.parent / "schemas" / "debate_message.json"
)


def _load_schema() -> dict:
    with open(_SCHEMA_PATH) as fh:
        return json.load(fh)


_SCHEMA: dict = _load_schema()


class MessageParseError(Exception):
    """Raised when a raw LLM response cannot be parsed into a DebateMessage."""


class AgentFailureError(Exception):
    """Raised when an agent fails to produce a valid response after retries."""


@dataclass
class DebateMessage:
    """All eight fields from the ``debate_message.json`` schema."""

    message_id: str
    sender: str
    recipient: str
    turn: int
    content: str
    sources: list[str]
    token_count: int
    timestamp: str


class BaseAgent(ABC):
    """Abstract base for Father, ProSon, and ConSon agents.

    Args:
        agent_id: Unique identifier for this agent instance.
        role: Semantic role string (e.g. ``"pro"``, ``"con"``, ``"father"``).
        gatekeeper: Shared :class:`~src.infrastructure.gatekeeper.Gatekeeper`.
        config: Full parsed ``setup.json`` dict.
        model: Claude model string to use for API calls.

    Attributes:
        agent_id: Unique agent identifier.
        role: Semantic role string.
        gatekeeper: Reference to the shared Gatekeeper.
        config: Parsed setup configuration.
        model: Model name used in every :class:`APIRequest`.
    """

    def __init__(
        self,
        agent_id: str,
        role: str,
        gatekeeper: Gatekeeper,
        config: dict,
        model: str,
    ) -> None:
        self.agent_id: str = agent_id
        self.role: str = role
        self.gatekeeper: Gatekeeper = gatekeeper
        self.config: dict = config
        self.model: str = model

    @abstractmethod
    def build_prompt(self, context: dict) -> str:
        """Build the prompt string for a given debate context."""

    @abstractmethod
    def act(self, context: dict) -> DebateMessage:
        """Produce the agent's next DebateMessage for the given context."""

    def parse_response(self, raw: str) -> DebateMessage:
        """Parse and validate *raw* JSON into a :class:`DebateMessage`.

        Args:
            raw: JSON string returned by the LLM.

        Returns:
            A validated :class:`DebateMessage` dataclass.

        Raises:
            MessageParseError: On JSON decode failure or schema violation.
        """
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise MessageParseError(f"Invalid JSON: {exc}") from exc
        if not self._validate_schema(data):
            raise MessageParseError(
                "Response does not conform to DebateMessage schema."
            )
        return DebateMessage(**{k: data[k] for k in DebateMessage.__dataclass_fields__})

    def _validate_schema(self, msg: dict) -> bool:
        """Return True if *msg* conforms to the DebateMessage JSON schema."""
        try:
            jsonschema.validate(instance=msg, schema=_SCHEMA)
            return True
        except jsonschema.ValidationError:
            return False

    def call_api(self, prompt: str) -> str:
        """Dispatch *prompt* through the Gatekeeper and return the reply text.

        Args:
            prompt: The full prompt string to send to the LLM.

        Returns:
            The ``content`` field of the :class:`APIResponse`.
        """
        request = APIRequest(
            agent_id=self.agent_id,
            model=self.model,
            payload={"prompt": prompt},
        )
        response = self.gatekeeper.dispatch(request)
        return response.content
