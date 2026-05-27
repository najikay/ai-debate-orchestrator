"""Flask web application for the AI Debate System.

Provides:
    GET  /                    — main chat interface (Bootstrap 5 + jQuery)
    POST /api/debate          — run a full debate and return JSON results
    GET  /api/debate/stream   — SSE stream: yields messages live as they arrive

Usage::

    uv run debate-web
    # then open http://localhost:5000
"""

import json
import os
import queue
import threading
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, render_template, request

from src.engine.debate_engine import DebateEngine
from src.infrastructure.config_loader import ConfigLoader

load_dotenv()

_TEMPLATE_DIR = Path(__file__).parent.parent.parent / "templates"


def _load_engine(app) -> DebateEngine:
    """Load config and return a fresh DebateEngine."""
    loader = ConfigLoader(app.config["CONFIG_PATH"])
    cfg = loader.load_setup()
    cfg["pricing"] = loader.load_pricing()
    return DebateEngine(cfg)


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
            engine = _load_engine(app)
            verdict = engine.start(topic)
            summary = engine.cost_reporter.compute()
            transcript = [
                {"sender": m.sender, "content": m.content,
                 "turn": m.turn, "sources": m.sources or []}
                for m in engine.state_manager.state.transcript
            ]
            return jsonify({
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
            })
        except Exception as exc:  # noqa: BLE001
            return jsonify({"error": str(exc)}), 500

    @app.route("/api/debate/stream")
    def stream_debate():
        topic = request.args.get("topic", "").strip()
        if not topic:
            return jsonify({"error": "Topic is required."}), 400

        msg_queue: queue.Queue = queue.Queue()

        def run_engine() -> None:
            try:
                engine = _load_engine(app)
                engine.state_manager.on_message = lambda msg: msg_queue.put(("message", {
                    "sender": msg.sender, "content": msg.content,
                    "turn": msg.turn, "sources": msg.sources or [],
                }))
                verdict = engine.start(topic)
                summary = engine.cost_reporter.compute()
                msg_queue.put(("verdict", {
                    "winner": verdict.winner, "reasoning": verdict.reasoning,
                    "turn_count": verdict.turn_count, "scores": verdict.scores,
                    "cost": {"total_usd": round(summary.total_usd, 4),
                             "utilisation_pct": round(summary.utilisation_pct, 1)},
                }))
            except Exception as exc:  # noqa: BLE001
                msg_queue.put(("error", str(exc)))
            finally:
                msg_queue.put(("done", None))

        threading.Thread(target=run_engine, daemon=True).start()

        def generate():
            while True:
                kind, payload = msg_queue.get()
                if kind == "done":
                    yield "event: close\ndata: {}\n\n"
                    break
                yield f"data: {json.dumps({'type': kind, 'data': payload})}\n\n"
                if kind == "error":
                    break

        return Response(generate(), mimetype="text/event-stream",
                        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    return app


def main() -> None:
    """Entry point for ``uv run debate-web``."""
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
