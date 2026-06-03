# file_watcher.py
# /// script
# requires-python = ">=3.13"
# dependencies = ["watchdog", "narwhals"]
# ///
"""
Standalone file watcher. Run this to see what Flask/Werkzeug might be triggering on (and thus causing hot-reloading).
"""
from datetime import datetime
import fnmatch
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging
import time
import sys

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

class WatchHandler(FileSystemEventHandler):
    exclude_patterns = [os.path.join("*",".git","*"), "*.git*", os.path.join("*",".venv","*"), "*.venv*"]#, "*\\.git\\*"]

    def on_any_event(self, event):
        matched = 0 #
        for pattern in self.exclude_patterns:
            matched += 1 if len(fnmatch.filter([event.src_path], pattern)) != 0 else 0
        logger.info(f"{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} Detected file change: {event.src_path} -- {event.event_type} -- {matched}")

if __name__ == "__main__":
    path = "."  # Monitor your project root 
    observer = Observer()
    observer.schedule(WatchHandler(), path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
