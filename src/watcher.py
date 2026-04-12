"""Watch health-log.md for changes and regenerate wallpaper."""

import time
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class HealthLogHandler(FileSystemEventHandler):
    def __init__(self, target_file: str, callback):
        self.target = Path(target_file).name
        self.callback = callback
        self._last_trigger = 0

    def on_modified(self, event):
        if event.is_directory:
            return
        if Path(event.src_path).name == self.target:
            # Debounce: ignore events within 2 seconds of each other
            now = time.time()
            if now - self._last_trigger < 2:
                return
            self._last_trigger = now
            print(f"[watcher] {self.target} changed, regenerating...")
            self.callback()


def watch_health_log(health_log_path: str, callback):
    """Block and watch the health log file for changes, calling callback on each."""
    path = Path(health_log_path)
    handler = HealthLogHandler(str(path), callback)
    observer = Observer()
    observer.schedule(handler, str(path.parent), recursive=False)
    observer.start()
    print(f"[watcher] Watching {path} for changes. Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
