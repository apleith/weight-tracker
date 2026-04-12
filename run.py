#!/usr/bin/env python3
"""Weight Tracker CLI entry point.

Usage:
    python run.py wallpaper     Generate dashboard PNG and set as wallpaper
    python run.py serve         Start localhost dashboard server
    python run.py watch         Watch health-log.md, auto-regenerate wallpaper
    python run.py json          Export weight data as JSON to output/
    python run.py all           Wallpaper + serve + watch (background threads)
    python run.py remind        Check if today is logged; if not, ping your phone
    python run.py recalibrate   Analyze actual data and propose updated model breakpoints
"""

import json
import sys
import threading
from pathlib import Path

import yaml

from src.parser import parse_health_log, entries_to_json_serializable
from src.model import compute_stats, generate_curve

CONFIG_PATH = Path(__file__).parent / "config.yaml"


def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        config = yaml.safe_load(f)
    # Parse model breakpoints into tuples
    if "model_breakpoints" in config:
        config["breakpoints"] = [tuple(bp) for bp in config["model_breakpoints"]]
    return config


def do_wallpaper(config: dict, silent: bool = False):
    from src.wallpaper import generate_wallpaper, set_wallpaper

    entries = parse_health_log(config["health_log_path"])
    stats = compute_stats(entries, config.get("breakpoints"))

    wp = config.get("wallpaper", {})
    output = Path(config["output_dir"]) / "wallpaper.png"

    generate_wallpaper(
        entries,
        output,
        width=wp.get("width", 2560),
        height=wp.get("height", 1440),
        dpi=wp.get("dpi", 150),
        breakpoints=config.get("breakpoints"),
    )

    set_wallpaper(output)
    if not silent:
        print(f"[wallpaper] Generated {output}")
        print(f"[wallpaper] Current: {stats['current_weight']} lbs | "
              f"Lost: {stats['total_lost']} lbs | "
              f"Day {stats['day_number']}")


def do_json(config: dict):
    entries = parse_health_log(config["health_log_path"])
    stats = compute_stats(entries, config.get("breakpoints"))
    curve = generate_curve(config.get("breakpoints"))

    output_dir = Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    data = {
        "stats": stats,
        "entries": entries_to_json_serializable(entries),
        "curve": curve,
    }

    out_path = output_dir / "weight-data.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"[json] Exported to {out_path}")


def do_serve(config: dict):
    from src.server import run_server
    print(f"[server] Starting at http://{config.get('server', {}).get('host', '127.0.0.1')}:"
          f"{config.get('server', {}).get('port', 8080)}")
    run_server(config)


def do_watch(config: dict):
    from src.watcher import watch_health_log
    # Generate once immediately
    do_wallpaper(config, silent=False)
    do_json(config)
    # Then watch for changes
    def on_change():
        do_wallpaper(config, silent=False)
        do_json(config)
    watch_health_log(config["health_log_path"], on_change)


def do_all(config: dict):
    # Generate immediately
    do_wallpaper(config, silent=False)
    do_json(config)

    # Start server in background thread
    server_thread = threading.Thread(target=do_serve, args=(config,), daemon=True)
    server_thread.start()

    # Watch in foreground (blocks)
    from src.watcher import watch_health_log
    def on_change():
        do_wallpaper(config, silent=False)
        do_json(config)
    watch_health_log(config["health_log_path"], on_change)


def do_remind(config: dict):
    from src.notify import remind_if_missing
    remind_if_missing(config)


def do_recalibrate(config: dict):
    from src.recalibrate import recalibrate, format_report
    entries = parse_health_log(config["health_log_path"])
    result = recalibrate(entries, config.get("breakpoints"))
    print(format_report(result))


COMMANDS = {
    "wallpaper": do_wallpaper,
    "serve": do_serve,
    "watch": do_watch,
    "json": do_json,
    "all": do_all,
    "remind": do_remind,
    "recalibrate": do_recalibrate,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        print(f"Available commands: {', '.join(COMMANDS)}")
        sys.exit(1)

    config = load_config()
    COMMANDS[sys.argv[1]](config)


if __name__ == "__main__":
    main()
