from pynput.mouse import Listener, Button, Controller
import threading
import time
import random

# CONFIG
CPS = 15
CLICK_INTERVAL = 1.0 / CPS

# Randomness
JITTER_RATIO = 0.25

mouse = Controller()

right_event = threading.Event()   # Activated by side button 1 (x1)
left_event = threading.Event()    # Activated by side button 2 (x2)

def auto_click_loop(event: threading.Event, click_button: Button):

    while True:
        event.wait()  # Block until activated
        while event.is_set():
            mouse.click(click_button)
            if JITTER_RATIO > 0:
                low = max(0.0, CLICK_INTERVAL * (1 - JITTER_RATIO))
                high = CLICK_INTERVAL * (1 + JITTER_RATIO)
                delay = random.uniform(low, high)
            else:
                delay = CLICK_INTERVAL
            time.sleep(delay)

def on_click(x, y, button, pressed):
    # Map side buttons: x1 -> right-click auto; x2 -> left-click auto
    if button == Button.x1:
        if pressed:
            right_event.set()
            print("Auto right-click: ON")
        else:
            right_event.clear()
            print("Auto right-click: OFF")
    elif button == Button.x2:
        if pressed:
            left_event.set()
            print("Auto left-click: ON")
        else:
            left_event.clear()
            print("Auto left-click: OFF")

threading.Thread(target=auto_click_loop, args=(right_event, Button.right), daemon=True).start()
threading.Thread(target=auto_click_loop, args=(left_event, Button.left), daemon=True).start()

with Listener(on_click=on_click) as listener:
    listener.join()
