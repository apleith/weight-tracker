"""Flask micro-server for the browser new-tab dashboard."""

import json
from pathlib import Path

from flask import Flask, jsonify, send_from_directory

from .parser import parse_health_log, entries_to_json_serializable
from .model import compute_stats, generate_curve, START_DATE, START_WEIGHT, GOAL_WEIGHT

app = Flask(__name__, static_folder=None)

# Set at startup by run.py
_config = {}


def configure(config: dict):
    global _config
    _config = config


@app.route("/")
def index():
    static_dir = Path(__file__).parent.parent / "static"
    return send_from_directory(str(static_dir), "dashboard.html")


@app.route("/api/data")
def api_data():
    entries = parse_health_log(_config["health_log_path"])
    stats = compute_stats(entries, _config.get("breakpoints"))
    curve = generate_curve(_config.get("breakpoints"))

    return jsonify({
        "stats": stats,
        "entries": entries_to_json_serializable(entries),
        "curve": curve,
        "start_date": START_DATE.isoformat(),
        "start_weight": START_WEIGHT,
        "goal_weight": GOAL_WEIGHT,
    })


@app.route("/static/<path:filename>")
def static_files(filename):
    static_dir = Path(__file__).parent.parent / "static"
    return send_from_directory(str(static_dir), filename)


def run_server(config: dict):
    configure(config)
    host = config.get("server", {}).get("host", "127.0.0.1")
    port = config.get("server", {}).get("port", 8080)
    app.run(host=host, port=port, debug=False)
