"""DebateCLI — command-line entry point for the AI Debate System.

Usage::

    uv run debate --topic "AI will replace human workers"
    uv run debate --topic "..." --config config/ --dry-run

Returns exit code 0 on success, 1 on WatchdogError.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import colorama
from colorama import Fore, Style

from dotenv import load_dotenv

load_dotenv()

colorama.init(autoreset=True)

from src.agents.father_agent import Verdict
from src.engine.debate_engine import DebateEngine
from src.infrastructure.config_loader import ConfigLoader
from src.infrastructure.cost_reporter import CostSummary
from src.infrastructure.watchdog import WatchdogError


def _agent_colour(sender: str) -> str:
    if sender == "pro_son":
        return Fore.BLUE
    if sender == "con_son":
        return Fore.RED
    return Fore.YELLOW


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AI Debate System — multi-agent debate orchestrator."
    )
    parser.add_argument("--topic", required=True, help="Debate topic string.")
    parser.add_argument("--config", default="config/", help="Path to config directory.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--save", action="store_true",
                        help="Save transcript to debate_history/.")
    return parser.parse_args()


def _print_live_message(msg) -> None:
    colour = _agent_colour(msg.sender)
    label = msg.sender.upper().replace("_", " ")
    bar = "─" * 60
    print(colour + Style.BRIGHT + f"\n[{label}]  turn {msg.turn}")
    print(colour + bar)
    words = msg.content.split()
    line, width = [], 0
    for word in words:
        if width + len(word) + 1 > 80:
            print("  " + " ".join(line))
            line, width = [word], len(word)
        else:
            line.append(word)
            width += len(word) + 1
    if line:
        print("  " + " ".join(line))


def _print_verdict(verdict: Verdict) -> None:
    bar = "=" * 60
    print(Fore.GREEN + Style.BRIGHT + f"\n{bar}")
    print(Fore.GREEN + Style.BRIGHT + "[VERDICT]")
    print(f"  Winner    : " + Fore.GREEN + Style.BRIGHT + verdict.winner)
    print(f"  Turns     : {verdict.turn_count}")
    print(f"  Reasoning : {verdict.reasoning}")
    print(Fore.GREEN + Style.BRIGHT + bar)


def _print_cost_report(summary: CostSummary) -> None:
    print(Fore.WHITE + Style.DIM + "\n[COST REPORT]")
    print(
        Fore.WHITE + Style.DIM +
        f"  Total : ${summary.total_usd:.4f}"
        f" / ${summary.budget_cap_usd:.2f}"
        f"  ({summary.utilisation_pct:.1f}% of budget)"
    )
    for agent_id, usage in summary.per_agent.items():
        print(Fore.WHITE + Style.DIM + f"  {agent_id:<12}: ${usage.cost_usd:.4f}")


def _save_transcript(topic: str, engine: DebateEngine, verdict: Verdict) -> None:
    history_dir = Path("debate_history")
    history_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = topic[:40].replace(" ", "_").replace("?", "").replace('"', "")
    filename = history_dir / f"{timestamp}_{slug}.json"
    data = {
        "topic": topic,
        "timestamp": timestamp,
        "winner": verdict.winner,
        "turns": verdict.turn_count,
        "reasoning": verdict.reasoning,
        "transcript": [
            {
                "sender": m.sender,
                "turn": m.turn,
                "content": m.content,
                "sources": m.sources or [],
            }
            for m in engine.state_manager.state.transcript
        ],
    }
    with open(filename, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    print(Fore.WHITE + Style.DIM + f"\n[SAVED] Transcript saved to {filename}")


def run() -> int:
    args = parse_args()
    print(Fore.WHITE + Style.DIM + f"[INFO]  Loading config from '{args.config}' ...")
    loader = ConfigLoader(args.config)
    config = loader.load_setup()
    config["pricing"] = loader.load_pricing()
    print(Fore.WHITE + Style.DIM +
          f"[INFO]  Config loaded. Schema version: {config.get('schema_version')}")

    if args.dry_run:
        father = config.get("agents", {}).get("father", {}).get("model", "?")
        pro = config.get("agents", {}).get("pro_son", {}).get("model", "?")
        con = config.get("agents", {}).get("con_son", {}).get("model", "?")
        print(f"[INFO]  Agents — father: {father}  pro_son: {pro}  con_son: {con}")
        print("[INFO]  Dry run complete — no API calls made.")
        return 0

    try:
        engine = DebateEngine(config)
        engine.state_manager.on_message = _print_live_message
        print(Style.BRIGHT + f"\n[DEBATE STARTING] Topic: {args.topic}\n")
        verdict = engine.start(args.topic)
        summary = engine.cost_reporter.compute()
        _print_verdict(verdict)
        _print_cost_report(summary)
        if args.save:
            _save_transcript(args.topic, engine, verdict)
        return 0
    except WatchdogError as exc:
        print(f"[ERROR] WatchdogError: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(run())
