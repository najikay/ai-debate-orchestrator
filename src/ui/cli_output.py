"""CLI output helpers — printing, colouring, and saving debate results."""

import json
from datetime import datetime
from pathlib import Path

import colorama
from colorama import Fore, Style

from src.agents.father_agent import Verdict
from src.infrastructure.cost_reporter import CostSummary

colorama.init(autoreset=True)


def agent_colour(sender: str) -> str:
    if sender == "pro_son":
        return Fore.BLUE
    if sender == "con_son":
        return Fore.RED
    return Fore.YELLOW


def print_live_message(msg) -> None:
    colour = agent_colour(msg.sender)
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


def print_verdict(verdict: Verdict) -> None:
    bar = "=" * 60
    colour = Fore.YELLOW if verdict.draw else Fore.GREEN
    winner_label = "DRAW" if verdict.draw else verdict.winner
    print(colour + Style.BRIGHT + f"\n{bar}")
    print(colour + Style.BRIGHT + "[VERDICT]")
    print(f"  Winner    : " + colour + Style.BRIGHT + winner_label)
    print(f"  Turns     : {verdict.turn_count}")
    print(f"  Reasoning : {verdict.reasoning}")
    scores = verdict.scores or {}
    if scores.get("pro_son") and scores.get("con_son"):
        ps, cs = scores["pro_son"], scores["con_son"]
        print(Fore.BLUE + f"\n  PRO SON  — Logic: {ps.get('logic','?')}  "
              f"Clarity: {ps.get('clarity','?')}  "
              f"Evidence: {ps.get('evidence','?')}  Total: {ps.get('total','?')}/30")
        print(Fore.RED + f"  CON SON  — Logic: {cs.get('logic','?')}  "
              f"Clarity: {cs.get('clarity','?')}  "
              f"Evidence: {cs.get('evidence','?')}  Total: {cs.get('total','?')}/30")
    print(colour + Style.BRIGHT + bar)


def print_cost_report(summary: CostSummary) -> None:
    print(Fore.WHITE + Style.DIM + "\n[COST REPORT]")
    print(Fore.WHITE + Style.DIM +
          f"  Total : ${summary.total_usd:.4f}"
          f" / ${summary.budget_cap_usd:.2f}"
          f"  ({summary.utilisation_pct:.1f}% of budget)")
    for agent_id, usage in summary.per_agent.items():
        print(Fore.WHITE + Style.DIM + f"  {agent_id:<12}: ${usage.cost_usd:.4f}")


def save_transcript(topic: str, engine, verdict: Verdict) -> None:
    history_dir = Path("debate_history")
    history_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = topic[:40].replace(" ", "_").replace("?", "").replace('"', "")
    filename = history_dir / f"{timestamp}_{slug}.json"
    data = {
        "topic": topic,
        "timestamp": timestamp,
        "winner": verdict.winner,
        "draw": verdict.draw,
        "turns": verdict.turn_count,
        "reasoning": verdict.reasoning,
        "scores": verdict.scores,
        "transcript": [
            {"sender": m.sender, "turn": m.turn,
             "content": m.content, "sources": m.sources or []}
            for m in engine.state_manager.state.transcript
        ],
    }
    with open(filename, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    print(Fore.WHITE + Style.DIM + f"\n[SAVED] Transcript saved to {filename}")
