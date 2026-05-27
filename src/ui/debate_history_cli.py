"""debate-history — CLI viewer for saved debate transcripts.

Usage::

    uv run debate-history          # list all saved debates
    uv run debate-history --replay # pick a debate to replay in terminal
    uv run debate-history --last   # replay the most recent debate

Returns exit code 0 on success, 1 on error.
"""

import json
import sys
import time
from pathlib import Path

import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

HISTORY_DIR = Path("debate_history")


def _load_all() -> list[Path]:
    """Return all saved debate JSON files sorted newest first."""
    if not HISTORY_DIR.exists():
        return []
    return sorted(HISTORY_DIR.glob("*.json"), reverse=True)


def _print_list(files: list[Path]) -> None:
    if not files:
        print(Fore.YELLOW + "No saved debates found in debate_history/")
        return
    print(Fore.WHITE + Style.BRIGHT + f"\n{'#':<4} {'Date':<18} {'Winner':<12} Topic")
    print("─" * 70)
    for i, f in enumerate(files, 1):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            winner = data.get("winner", "?")
            topic = data.get("topic", "?")[:45]
            ts = data.get("timestamp", f.stem)[:16].replace("_", " ")
            colour = Fore.BLUE if winner == "pro_son" else (
                Fore.RED if winner == "con_son" else Fore.YELLOW)
            print(f"{i:<4} {ts:<18} {colour}{winner:<12}{Style.RESET_ALL} {topic}")
        except Exception:
            print(f"{i:<4} {f.name}")


def _replay(path: Path) -> None:
    """Print a saved debate transcript with colours and pacing."""
    data = json.loads(path.read_text(encoding="utf-8"))
    topic = data.get("topic", "?")
    winner = data.get("winner", "?")
    print(Fore.WHITE + Style.BRIGHT + f"\n[REPLAY] {topic}")
    print("─" * 60)

    for msg in data.get("transcript", []):
        sender = msg.get("sender", "?")
        if sender == "pro_son":
            colour = Fore.BLUE
        elif sender == "con_son":
            colour = Fore.RED
        else:
            colour = Fore.YELLOW
        label = sender.upper().replace("_", " ")
        print(colour + Style.BRIGHT + f"\n[{label}]  turn {msg.get('turn', '?')}")
        print(colour + "─" * 60)
        print("  " + msg.get("content", ""))
        time.sleep(0.3)

    scores = data.get("scores", {})
    print(Fore.GREEN + Style.BRIGHT + "\n[VERDICT]")
    print(f"  Winner    : {Fore.GREEN + Style.BRIGHT + winner}")
    print(f"  Reasoning : {data.get('reasoning', '')}")
    if scores.get("pro_son") and scores.get("con_son"):
        ps, cs = scores["pro_son"], scores["con_son"]
        print(Fore.BLUE + f"  PRO SON — Total: {ps.get('total','?')}/30")
        print(Fore.RED  + f"  CON SON — Total: {cs.get('total','?')}/30")


def run() -> int:
    import argparse
    parser = argparse.ArgumentParser(
        description="View and replay saved AI debates."
    )
    parser.add_argument("--replay", action="store_true",
                        help="Pick a debate to replay interactively.")
    parser.add_argument("--last", action="store_true",
                        help="Replay the most recent saved debate.")
    args = parser.parse_args()

    files = _load_all()

    if args.last:
        if not files:
            print(Fore.YELLOW + "No saved debates found.")
            return 1
        _replay(files[0])
        return 0

    if args.replay:
        if not files:
            print(Fore.YELLOW + "No saved debates found.")
            return 1
        _print_list(files)
        try:
            choice = int(input(Fore.WHITE + "\nEnter debate number to replay: "))
            if 1 <= choice <= len(files):
                _replay(files[choice - 1])
            else:
                print(Fore.RED + "Invalid choice.")
                return 1
        except (ValueError, KeyboardInterrupt):
            print()
            return 1
        return 0

    _print_list(files)
    return 0


if __name__ == "__main__":
    sys.exit(run())
