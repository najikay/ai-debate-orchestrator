"""AgentSkill — abstract base class for all agent tools.

Every tool (e.g. WebSearchTool) must subclass :class:`AgentSkill` and
implement :meth:`execute`.  Results are returned as :class:`SkillResult`
dataclasses so callers always receive a uniform structure.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


class SkillError(Exception):
    """Raised when a skill cannot complete its operation.

    Examples: HTTP errors, missing API keys, empty result sets.
    """


@dataclass
class SkillResult:
    """Structured output from a skill invocation.

    Attributes:
        query: The original query string passed to :meth:`AgentSkill.execute`.
        snippets: List of text excerpts extracted from the response.
        raw_response: The full, unprocessed API response dict.
    """

    query: str
    snippets: list[str]
    raw_response: dict = field(default_factory=dict)


class AgentSkill(ABC):
    """Abstract base for all agent tools.

    Subclasses must:
    - Set the class attribute :attr:`skill_name` to a non-empty string.
    - Override :meth:`execute` to perform the tool's operation.

    Attributes:
        skill_name: Short identifier for the skill (e.g. ``"web_search"``).

    Example::

        class MySkill(AgentSkill):
            skill_name = "my_skill"

            def execute(self, query: str) -> SkillResult:
                return SkillResult(query=query, snippets=["result"], raw_response={})
    """

    skill_name: str = ""

    @abstractmethod
    def execute(self, query: str) -> SkillResult:
        """Run the skill for *query* and return structured results.

        Args:
            query: The search or action string to process.

        Returns:
            A populated :class:`SkillResult`.

        Raises:
            SkillError: If the skill cannot produce a result.
        """
