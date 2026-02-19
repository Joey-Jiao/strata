import threading
import time
from pathlib import Path
from typing import Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent


class DebouncedHandler(FileSystemEventHandler):
    def __init__(self, callback: Callable[[], None], debounce_seconds: float = 2.0):
        self._callback = callback
        self._debounce = debounce_seconds
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()

    def _trigger(self):
        with self._lock:
            self._timer = None
        self._callback()

    def on_modified(self, event):
        if event.is_directory:
            return
        if not event.src_path.endswith(".sqlite"):
            return
        with self._lock:
            if self._timer:
                self._timer.cancel()
            self._timer = threading.Timer(self._debounce, self._trigger)
            self._timer.start()

    def cancel(self):
        with self._lock:
            if self._timer:
                self._timer.cancel()
                self._timer = None


class ZoteroWatcher:
    def __init__(
        self,
        db_path: Path | str,
        on_change: Callable[[], None],
        debounce_seconds: float = 2.0,
    ):
        self._db_path = Path(db_path).expanduser()
        self._watch_dir = self._db_path.parent
        self._on_change = on_change
        self._debounce = debounce_seconds
        self._observer: Observer | None = None
        self._handler: DebouncedHandler | None = None

    def start(self):
        if self._observer:
            return
        self._handler = DebouncedHandler(self._on_change, self._debounce)
        self._observer = Observer()
        self._observer.schedule(self._handler, str(self._watch_dir), recursive=False)
        self._observer.start()

    def stop(self):
        if self._handler:
            self._handler.cancel()
            self._handler = None
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None

    def is_running(self) -> bool:
        return self._observer is not None and self._observer.is_alive()

    def __enter__(self) -> "ZoteroWatcher":
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return False
