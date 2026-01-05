import threading
from typing import Callable, Dict, Optional, Set
from pynput.mouse import Listener as MouseListener, Button
from pynput import keyboard

TriggerCallback = Callable[[bool], None]

def normalize_key(k: keyboard.Key | keyboard.KeyCode) -> Optional[str]:
    if isinstance(k, keyboard.Key):
        name = str(k).split('.')[-1]
        return name.lower()
    if isinstance(k, keyboard.KeyCode) and k.char:
        return k.char.lower()
    return None

def pretty_token(token: str) -> str:
    if token.startswith("mouse:"):
        t = token.split(":", 1)[1]
        return "Side 1" if t == "x1" else ("Side 2" if t == "x2" else token)
    if token.startswith("key:"):
        t = token.split(":", 1)[1]
        return t.upper()
    return token

class TriggerManager:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._callbacks: Dict[str, TriggerCallback] = {}
        self._mouse_listener: Optional[MouseListener] = None
        self._key_listener: Optional[keyboard.Listener] = None
        self._capture_cb: Optional[Callable[[str], None]] = None
        self._capture_allow: Set[str] = {"mouse", "key"}

    def set_trigger(self, token: str, callback: TriggerCallback) -> None:
        # Remove any previous token that mapped to this callback
        with self._lock:
            for t, cb in list(self._callbacks.items()):
                if cb is callback:
                    self._callbacks.pop(t, None)
            self._callbacks[token] = callback

    def clear_trigger(self, token: str) -> None:
        with self._lock:
            self._callbacks.pop(token, None)

    def start(self) -> None:
        if self._mouse_listener or self._key_listener:
            return
        self._mouse_listener = MouseListener(on_click=self._on_mouse_click)
        self._mouse_listener.start()
        self._key_listener = keyboard.Listener(on_press=self._on_key_press, on_release=self._on_key_release)
        self._key_listener.start()

    def _maybe_capture(self, token: str) -> bool:
        cb = None
        with self._lock:
            cb = self._capture_cb
            if cb:
                self._capture_cb = None
        if cb:
            try:
                cb(token)
            except Exception:
                pass
            return True
        return False

    def _on_mouse_click(self, x, y, button, pressed):
        if button not in (Button.x1, Button.x2):
            return
        token = f"mouse:{'x1' if button == Button.x1 else 'x2'}"

        # Capture mode takes precedence
        with self._lock:
            if self._capture_cb and 'mouse' in self._capture_allow and pressed:
                pass
            else:
                callback = self._callbacks.get(token)
                if callback is None:
                    return
                try:
                    callback(pressed)
                except Exception:
                    return

        if pressed and 'mouse' in self._capture_allow:
            self._maybe_capture(token)

    def _on_key_press(self, key):
        code = normalize_key(key)
        if not code:
            return
        token = f"key:{code}"
        with self._lock:
            if self._capture_cb and 'key' in self._capture_allow:
                pass
            else:
                callback = self._callbacks.get(token)
                if callback is None:
                    return
                try:
                    callback(True)
                except Exception:
                    return
        if 'key' in self._capture_allow:
            self._maybe_capture(token)

    def _on_key_release(self, key):
        code = normalize_key(key)
        if not code:
            return
        token = f"key:{code}"
        with self._lock:
            callback = self._callbacks.get(token)
        if callback is None:
            return
        try:
            callback(False)
        except Exception:
            return

    def capture_once(self, on_captured: Callable[[str], None], allow: Set[str] | None = None) -> None:
        # allow: {"mouse", "key"}
        with self._lock:
            self._capture_cb = on_captured
            self._capture_allow = allow or {"mouse", "key"}

    def stop(self) -> None:
        if self._mouse_listener:
            self._mouse_listener.stop()
            self._mouse_listener = None
        if self._key_listener:
            self._key_listener.stop()
            self._key_listener = None
