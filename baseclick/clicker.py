import threading
import time
import random
from typing import Optional
from pynput.mouse import Button, Controller

class AutoClicker:
    def __init__(self, click_button: Button, cps: int = 15, jitter_ratio: float = 0.25) -> None:
        self._controller = Controller()
        self._button = click_button
        self._cps = cps
        self._jitter = jitter_ratio
        self._running = threading.Event()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def set_rate(self, cps: int) -> None:
        self._cps = max(1, int(cps))

    def set_jitter(self, jitter_ratio: float) -> None:
        self._jitter = max(0.0, float(jitter_ratio))

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            self._running.set()
            return
        self._running.set()
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running.clear()

    def shutdown(self) -> None:
        self._running.clear()
        self._stop.set()

    def is_active(self) -> bool:
        return self._running.is_set()

    def _run(self) -> None:
        while not self._stop.is_set():
            if not self._running.is_set():
                time.sleep(0.01)
                continue
            base = 1.0 / max(1, self._cps)
            if self._jitter > 0:
                low = max(0.0, base * (1 - self._jitter))
                high = base * (1 + self._jitter)
                delay = random.uniform(low, high)
            else:
                delay = base
            self._controller.click(self._button)
            time.sleep(delay)
