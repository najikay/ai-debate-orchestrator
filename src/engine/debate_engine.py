"""DebateEngine — orchestrates the full debate loop from start to Verdict.

Wires Father, ProSon, ConSon, StateManager, Watchdog, and CostReporter
into a single coherent session.  The :meth:`start` method is the only
public entry point for callers.
"""

import logging

from src.agents.con_son_agent import ConSonAgent
from src.agents.father_agent import FatherAgent, Verdict
from src.agents.pro_son_agent import ProSonAgent
from src.engine.state_manager import StateManager
from src.infrastructure.cost_reporter import CostReporter
from src.infrastructure.gatekeeper import Gatekeeper
from src.infrastructure.watchdog import Watchdog, WatchdogError

_logger = logging.getLogger(__name__)
_WARN_THRESHOLD: float = 90.0


class DebateEngine:
    """Orchestrates a full AI debate from topic to Verdict.

    Args:
        config: Parsed ``setup.json`` dict containing agent models,
            turn limits, budget cap, and watchdog settings.

    Attributes:
        father: The moderator and judge agent.
        pro_son: The affirmative debater.
        con_son: The negative debater.
        state_manager: Tracks the live :class:`~src.engine.state_manager.DebateState`.
        watchdog: Enforces per-call timeouts.
        cost_reporter: Accumulates and reports token costs.
    """

    def __init__(self, config: dict) -> None:
        self._config = config
        self._budget_cap: float = (
            config.get("debate", {}).get("max_session_cost_usd", 2.00)
        )
        wd_cfg = config.get("watchdog", {})
        gk = Gatekeeper({"models": {m: {"rpm": 50, "tpm": 40000}
                                     for m in ("test-model",
                                               "claude-sonnet-4-6",
                                               "claude-haiku-4-5")},
                          "web_search": {"rpm": 30}})
        pricing = config.get("pricing", {"models": {}})
        agents_cfg = config.get("agents", {})
        father_model = agents_cfg.get("father", {}).get("model", "claude-sonnet-4-6")
        pro_model = agents_cfg.get("pro_son", {}).get("model", "claude-haiku-4-5")
        con_model = agents_cfg.get("con_son", {}).get("model", "claude-haiku-4-5")
        self.gatekeeper = gk
        self.father = FatherAgent(
            gatekeeper=gk, config=config, model=father_model,
        )
        self.pro_son = ProSonAgent(
            gatekeeper=gk, config=config, skills=[], model=pro_model,
        )
        self.con_son = ConSonAgent(
            gatekeeper=gk, config=config, skills=[], model=con_model,
        )
        self.state_manager = StateManager()
        self.watchdog = Watchdog(
            timeout_seconds=wd_cfg.get("timeout_seconds", 30),
            max_retries=wd_cfg.get("max_retries", 1),
        )
        self.cost_reporter = CostReporter(pricing, self._budget_cap)

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def start(self, topic: str) -> Verdict:
        """Run the full debate and return the Father's Verdict.

        Args:
            topic: The debate topic supplied by the user.

        Returns:
            A :class:`~src.agents.father_agent.Verdict` with ``draw=False``.

        Raises:
            WatchdogError: If an agent hangs past the retry limit.
        """
        self.state_manager.state.topic = topic
        opening = self.father.open_debate(topic)
        self.state_manager.record_message(opening)
        min_turns = self._config.get("debate", {}).get("min_turns_per_side", 10)
        try:
            self._run_turn_loop(min_turns=min_turns)
        except WatchdogError as exc:
            self._handle_watchdog_error(exc)
            raise
        verdict = self.father.evaluate(self.state_manager.state)
        self.state_manager.record_verdict(verdict)
        self._sync_costs()
        return verdict

    def _run_turn_loop(self, min_turns: int) -> None:
        """Execute debate rounds until min_turns per side are complete."""
        topic = self.state_manager.state.topic
        for _ in range(min_turns):
            if self._check_budget():
                break
            pro_msg = self.pro_son.generate_argument(
                self.state_manager.state.transcript[-1], topic=topic
            )
            self.state_manager.record_message(pro_msg)
            self.father.route(pro_msg)
            if self._check_budget():
                break
            con_msg = self.con_son.generate_argument(
                self.state_manager.state.transcript[-1], topic=topic
            )
            self.state_manager.record_message(con_msg)
            self.father.route(con_msg)

    def _sync_costs(self) -> None:
        """Replace cost records with current Gatekeeper usage totals."""
        cr = self.cost_reporter
        cr._records.clear()
        for aid in ("father", "pro_son", "con_son"):
            s = self.gatekeeper.get_usage(aid)
            if s.total_tokens:
                m = getattr(self, aid).model
                cr.record_usage(aid, m, s.prompt_tokens, s.completion_tokens)

    def _check_budget(self) -> bool:
        """Return True if session cost has reached or exceeded the cap."""
        self._sync_costs()
        summary = self.cost_reporter.compute()
        if summary.utilisation_pct >= _WARN_THRESHOLD:
            _logger.warning(
                "Budget utilisation at %.1f%% (cap $%.2f).",
                summary.utilisation_pct,
                self._budget_cap,
            )
        return summary.total_usd >= self._budget_cap

    def _handle_watchdog_error(self, error: WatchdogError) -> None:
        """Log the error, record an event, and snapshot the state."""
        _logger.error("WatchdogError: %s", error)
        self.state_manager.state.events.append(
            {"event_type": "WATCHDOG_TIMEOUT", "detail": str(error)}
        )
        self.state_manager.to_json()
