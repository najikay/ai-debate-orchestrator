"""Flask web application for the AI Debate System.

Provides:
    GET  /               — main chat interface (Bootstrap 5 + jQuery)
    POST /api/debate     — run a full debate and return JSON results

Usage::

    uv run debate-web
    # then open http://localhost:5000
"""

import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from src.engine.debate_engine import DebateEngine
from src.infrastructure.config_loader import ConfigLoader

_TEMPLATE_DIR = Path(__file__).parent.parent.parent / "templates"


def create_app(config_path: str = "config/") -> Flask:
    """Create and configure the Flask application.

    Args:
        config_path: Path to the ``config/`` directory.

    Returns:
        Configured :class:`flask.Flask` instance.
    """
    app = Flask(__name__, template_folder=str(_TEMPLATE_DIR))
    app.config["CONFIG_PATH"] = config_path

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/debate", methods=["POST"])
    def run_debate():
        data = request.get_json(force=True) or {}
        topic = (data.get("topic") or "").strip()
        if not topic:
            return jsonify({"error": "Topic is required."}), 400
        try:
            _loader = ConfigLoader(app.config["CONFIG_PATH"])
            cfg = {**_loader.load_setup(), "pricing": _loader.load_pricing()}
            engine = DebateEngine(cfg)
            verdict = engine.start(topic)
            summary = engine.cost_reporter.compute()
            transcript = [
                {
                    "sender": m.sender,
                    "content": m.content,
                    "turn": m.turn,
                    "sources": m.sources,
                }
                for m in engine.state_manager.state.transcript
            ]
            return jsonify(
                {
                    "transcript": transcript,
                    "verdict": {
                        "winner": verdict.winner,
                        "reasoning": verdict.reasoning,
                        "turn_count": verdict.turn_count,
                        "scores": verdict.scores,
                    },
                    "cost": {
                        "total_usd": round(summary.total_usd, 4),
                        "utilisation_pct": round(summary.utilisation_pct, 1),
                    },
                }
            )
        except Exception as exc:  # noqa: BLE001
            return jsonify({"error": str(exc)}), 500

    return app


def main() -> None:
    """Entry point for ``uv run debate-web``."""
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
