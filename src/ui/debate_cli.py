"""DebateCLI — command-line entry point for the AI Debate System.

Usage::

    uv run debate --topic "AI will replace human workers"
    uv run debate --topic "..." --rounds 5
    uv run debate --topic "..." --pro-model claude-sonnet-4-6 --con-model claude-haiku-4-5
    uv run debate --topic "..." --dry-run --save

Returns exit code 0 on success, 1 on WatchdogError.
"""

import argparse
import sys

from colorama import Style
from dotenv import load_dotenv

load_dotenv()

from src.engine.debate_engine import DebateEngine
from src.infrastructure.config_loader import ConfigLoader
from src.infrastructure.watchdog import WatchdogError
from src.ui.cli_output import (
    print_cost_report,
    print_live_message,
    print_verdict,
    save_transcript,
)

try:
    import colorama
    colorama.init(autoreset=True)
except ImportError:
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AI Debate System — multi-agent debate orchestrator."
    )
    parser.add_argument("--topic", required=True, help="Debate topic string.")
    parser.add_argument("--config", default="config/", help="Path to config directory.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--save", action="store_true",
                        help="Save transcript to debate_history/.")
    parser.add_argument("--rounds", type=int, default=None,
                        help="Number of debate rounds per side (overrides config).")
    parser.add_argument("--pro-model", default=None,
                        help="Claude model for the Pro agent.")
    parser.add_argument("--con-model", default=None,
                        help="Claude model for the Con agent.")
    return parser.parse_args()


def _apply_overrides(config: dict, args: argparse.Namespace) -> None:
    """Apply CLI flag overrides onto the loaded config dict."""
    if args.rounds is not None:
        config.setdefault("debate", {})["min_turns_per_side"] = args.rounds
        print(f"[INFO]  Rounds overridden to {args.rounds} per side.")
    if args.pro_model is not None:
        config.setdefault("agents", {}).setdefault("pro_son", {})["model"] = args.pro_model
        print(f"[INFO]  Pro model overridden to '{args.pro_model}'.")
    if args.con_model is not None:
        config.setdefault("agents", {}).setdefault("con_son", {})["model"] = args.con_model
        print(f"[INFO]  Con model overridden to '{args.con_model}'.")


def run() -> int:
    args = parse_args()
    print(f"[INFO]  Loading config from '{args.config}' ...")
    loader = ConfigLoader(args.config)
    config = loader.load_setup()
    config["pricing"] = loader.load_pricing()
    _apply_overrides(config, args)
    print(f"[INFO]  Config loaded. Schema version: {config.get('schema_version')}")

    if args.dry_run:
        agents = config.get("agents", {})
        father = agents.get("father", {}).get("model", "?")
        pro    = agents.get("pro_son", {}).get("model", "?")
        con    = agents.get("con_son", {}).get("model", "?")
        rounds = config.get("debate", {}).get("min_turns_per_side", "?")
        print(f"[INFO]  Agents — father: {father}  pro_son: {pro}  con_son: {con}")
        print(f"[INFO]  Rounds — {rounds} per side")
        print("[INFO]  Dry run complete — no API calls made.")
        return 0

    try:
        engine = DebateEngine(config)
        engine.state_manager.on_message = print_live_message
        print(Style.BRIGHT + f"\n[DEBATE STARTING] Topic: {args.topic}\n")
        verdict = engine.start(args.topic)
        summary = engine.cost_reporter.compute()
        print_verdict(verdict)
        print_cost_report(summary)
        if args.save:
            save_transcript(args.topic, engine, verdict)
        return 0
    except WatchdogError as exc:
        print(f"[ERROR] WatchdogError: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(run())
