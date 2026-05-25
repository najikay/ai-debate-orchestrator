"""CostReporter — per-agent USD cost breakdown and budget utilisation.

Reads token rates from ``pricing.json`` and converts accumulated token
counts into dollar amounts.  Prints a human-readable session summary.
"""

from dataclasses import dataclass, field


@dataclass
class AgentUsage:
    """Per-agent token totals and computed cost.

    Attributes:
        prompt_tokens: Total input tokens consumed.
        completion_tokens: Total output tokens consumed.
        model: Model name used to look up pricing.
        cost_usd: Computed USD cost (set by :meth:`CostReporter.compute`).
    """

    prompt_tokens: int
    completion_tokens: int
    model: str
    cost_usd: float = field(default=0.0)


@dataclass
class CostSummary:
    """Session-level cost summary.

    Attributes:
        per_agent: Mapping of agent_id → :class:`AgentUsage` with cost filled in.
        total_usd: Sum of all per-agent costs.
        budget_cap_usd: The configured session budget ceiling.
        utilisation_pct: ``total_usd / budget_cap_usd * 100``.
    """

    per_agent: dict[str, AgentUsage]
    total_usd: float
    budget_cap_usd: float
    utilisation_pct: float


class CostReporter:
    """Tracks token usage and reports USD costs against a budget cap.

    Args:
        pricing: Parsed ``pricing.json`` dict with per-model input/output rates.
        budget_cap_usd: Maximum allowed session spend in USD.

    Attributes:
        budget_cap_usd: The session budget ceiling.

    Example::

        reporter = CostReporter(pricing, budget_cap_usd=2.00)
        reporter.record_usage("father", "claude-sonnet-4-6", 500, 200)
        summary = reporter.compute()
        reporter.print_report(summary)
    """

    def __init__(self, pricing: dict, budget_cap_usd: float) -> None:
        self._pricing: dict = pricing
        self.budget_cap_usd: float = budget_cap_usd
        self._records: dict[str, AgentUsage] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record_usage(
        self,
        agent_id: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> None:
        """Accumulate token usage for *agent_id*.

        Args:
            agent_id: Identifier for the calling agent.
            model: Model name used to look up pricing.
            prompt_tokens: Input tokens for this call.
            completion_tokens: Output tokens for this call.
        """
        if agent_id not in self._records:
            self._records[agent_id] = AgentUsage(0, 0, model)
        rec = self._records[agent_id]
        rec.prompt_tokens += prompt_tokens
        rec.completion_tokens += completion_tokens

    def compute(self) -> CostSummary:
        """Calculate per-agent and total USD cost.

        Returns:
            A :class:`CostSummary` with all cost fields populated.
        """
        total = 0.0
        per_agent: dict[str, AgentUsage] = {}
        for agent_id, rec in self._records.items():
            rates = self._pricing["models"][rec.model]
            cost = (
                rec.prompt_tokens * rates["input_per_1k"]
                + rec.completion_tokens * rates["output_per_1k"]
            ) / 1000
            rec.cost_usd = cost
            total += cost
            per_agent[agent_id] = rec
        util = (total / self.budget_cap_usd * 100) if self.budget_cap_usd else 0.0
        return CostSummary(per_agent, total, self.budget_cap_usd, util)

    def print_report(self, summary: CostSummary) -> None:
        """Print a human-readable cost report to stdout.

        Args:
            summary: The :class:`CostSummary` returned by :meth:`compute`.
        """
        print("=" * 52)
        print("  Session Cost Report")
        print("=" * 52)
        for agent_id, usage in summary.per_agent.items():
            print(
                f"  {agent_id:<20} "
                f"p={usage.prompt_tokens:>6}  "
                f"c={usage.completion_tokens:>6}  "
                f"${usage.cost_usd:.6f}"
            )
        print("-" * 52)
        print(f"  Total:                          ${summary.total_usd:.6f}")
        print(
            f"  Budget cap: ${summary.budget_cap_usd:.2f}   "
            f"Utilisation: {summary.utilisation_pct:.2f}%"
        )
        print("=" * 52)
