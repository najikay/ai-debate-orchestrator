"""LogicAnalyzerTool — offline, network-free argument structure analyzer.

Counts premise and conclusion indicator keywords, word count, sentence count,
and average sentence length.  Returns a rubric summary in :class:`SkillResult`
with no external I/O of any kind.
"""

import re

from src.skills.base_skill import AgentSkill, SkillResult

_PREMISE_KEYWORDS: list[str] = [
    "because",
    "since",
    "given that",
    "as",
    "if",
]

_CONCLUSION_KEYWORDS: list[str] = [
    "therefore",
    "thus",
    "hence",
    "so",
    "consequently",
]


class LogicAnalyzerTool(AgentSkill):
    """Purely local argument-structure analyzer.

    Inspects a text query for logical-indicator keywords and basic
    readability metrics.  Makes **no** network calls.

    Attributes:
        skill_name: Always ``"logic_analyzer"``.

    Example::

        tool = LogicAnalyzerTool()
        result = tool.execute("Because birds fly, they must have wings.")
        print(result.snippets[0])
    """

    skill_name: str = "logic_analyzer"

    def execute(self, query: str) -> SkillResult:
        """Analyse *query* locally and return a rubric :class:`SkillResult`.

        Args:
            query: The argument text to inspect.

        Returns:
            A :class:`SkillResult` whose ``raw_response`` contains the
            integer counts and whose ``snippets`` list holds a human-readable
            summary line.
        """
        text = query.strip()
        premise_count = self._count_keywords(text, _PREMISE_KEYWORDS)
        conclusion_count = self._count_keywords(text, _CONCLUSION_KEYWORDS)
        words = text.split() if text else []
        word_count = len(words)
        sentence_count = self._sentence_count(text)
        avg_len = round(word_count / sentence_count, 2) if sentence_count else 0.0

        rubric = {
            "premise_keywords": premise_count,
            "conclusion_keywords": conclusion_count,
            "word_count": word_count,
            "sentence_count": sentence_count,
            "avg_sentence_length": avg_len,
        }

        snippet = (
            f"premises={premise_count} conclusions={conclusion_count} "
            f"words={word_count} sentences={sentence_count} "
            f"avg_len={avg_len}"
        )

        return SkillResult(query=query, snippets=[snippet], raw_response=rubric)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _count_keywords(self, text: str, keywords: list[str]) -> int:
        """Return the total occurrences of *keywords* in *text* (case-insensitive)."""
        lower = text.lower()
        return sum(lower.count(kw) for kw in keywords)

    def _sentence_count(self, text: str) -> int:
        """Count sentence-ending punctuation marks (.  !  ?) in *text*."""
        return len(re.findall(r"[.!?]", text))
