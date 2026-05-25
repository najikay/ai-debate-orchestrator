"""DebateCLI — command-line entry point for the AI Debate System.

Usage::

    uv run debate --topic "AI will replace human workers"
    uv run debate --topic "..." --config config/ --dry-run

Returns exit code 0 on success, 1 on WatchdogError.
"""

import argparse
import sys

from src.agents.father_agent import Verdict
from src.engine.debate_engine import DebateEngine
from src.infrastructure.config_loader import ConfigLoader
from src.infrastructure.cost_reporter import CostSummary
from src.infrastructure.watchdog import WatchdogError


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Namespace with ``topic`` (str), ``config`` (str), ``dry_run`` (bool).
    """
    parser = argparse.ArgumentParser(
        description="AI Debate System — multi-agent debate orchestrator."
    )
    parser.add_argument("--topic", required=True, help="Debate topic string.")
    parser.add_argument(
        "--config", default="config/", help="Path to config directory."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate config and exit without calling the LLM API.",
    )
    return parser.parse_args()


def _print_verdict(verdict: Verdict) -> None:
    """Print the debate verdict to stdout."""
    bar = "=" * 60
    print(f"\n{bar}")
    print("[VERDICT]")
    print(f"  Winner    : {verdict.winner}")
    print(f"  Turns     : {verdict.turn_count}")
    print(f"  Reasoning : {verdict.reasoning}")
    print(bar)


def _print_cost_report(summary: CostSummary) -> None:
    """Print the session cost summary to stdout."""
    print("\n[COST REPORT]")
    print(
        f"  Total : ${summary.total_usd:.4f}"
        f" / ${summary.budget_cap_usd:.2f}"
        f"  ({summary.utilisation_pct:.1f}% of budget)"
    )
    for agent_id, usage in summary.per_agent.items():
        print(f"  {agent_id:<12}: ${usage:.4f}")


def run() -> int:
    """Run the debate CLI.

    Returns:
        ``0`` on success, ``1`` on :class:`~src.infrastructure.watchdog.WatchdogError`.
    """
    args = parse_args()
    print(f"[INFO]  Loading config from '{args.config}' ...")
    config = ConfigLoader(args.config).load_setup()
    print(f"[INFO]  Config loaded. Schema version: {config.get('schema_version')}")

    if args.dry_run:
        father = config.get("agents", {}).get("father", {}).get("model", "?")
        pro = config.get("agents", {}).get("pro_son", {}).get("model", "?")
        con = config.get("agents", {}).get("con_son", {}).get("model", "?")
        print(f"[INFO]  Agents — father: {father}  pro_son: {pro}  con_son: {con}")
        print("[INFO]  Dry run complete — no API calls made.")
        return 0

    try:
        engine = DebateEngine(config)
        print(f"\n[DEBATE STARTING] Topic: {args.topic}\n")
        verdict = engine.start(args.topic)
        summary = engine.cost_reporter.compute()
        _print_verdict(verdict)
        _print_cost_report(summary)
        return 0
    except WatchdogError as exc:
        print(f"[ERROR] WatchdogError: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(run())
