import sys
from PySide6.QtWidgets import QApplication
from pynput.mouse import Button

from baseclick.config import load_config, save_config
from baseclick.clicker import AutoClicker
from baseclick.triggers import TriggerManager
from baseclick.ui.main_window import MainWindow


class AppController:
    def __init__(self) -> None:
        self.cfg = load_config()
        self.left_clicker = AutoClicker(Button.left, cps=self.cfg.cps, jitter_ratio=self.cfg.jitter_ratio)
        self.right_clicker = AutoClicker(Button.right, cps=self.cfg.cps, jitter_ratio=self.cfg.jitter_ratio)
        self.triggers = TriggerManager()

        self._mode = self.cfg.mode  # 'hold' or 'toggle'
        self._left_toggled = False
        self._right_toggled = False

        self._wire_triggers()
        self.triggers.start()

    def _wire_triggers(self):
        self.triggers.set_trigger(self.cfg.left_trigger, self._on_left_trigger)
        self.triggers.set_trigger(self.cfg.right_trigger, self._on_right_trigger)

    def _on_left_trigger(self, pressed: bool):
        if self._mode == "hold":
            if pressed:
                self.left_clicker.start()
            else:
                self.left_clicker.stop()
        else:
            if pressed:
                self._left_toggled = not self._left_toggled
                if self._left_toggled:
                    self.left_clicker.start()
                else:
                    self.left_clicker.stop()

    def _on_right_trigger(self, pressed: bool):
        if self._mode == "hold":
            if pressed:
                self.right_clicker.start()
            else:
                self.right_clicker.stop()
        else:
            if pressed:
                self._right_toggled = not self._right_toggled
                if self._right_toggled:
                    self.right_clicker.start()
                else:
                    self.right_clicker.stop()

    def apply_settings(self, new_cfg):
        self._mode = new_cfg.mode
        self.left_clicker.set_rate(new_cfg.cps)
        self.right_clicker.set_rate(new_cfg.cps)
        self.left_clicker.set_jitter(new_cfg.jitter_ratio)
        self.right_clicker.set_jitter(new_cfg.jitter_ratio)

        # Rebind triggers if changed
        if new_cfg.left_trigger != self.cfg.left_trigger:
            self.triggers.set_trigger(new_cfg.left_trigger, self._on_left_trigger)
        if new_cfg.right_trigger != self.cfg.right_trigger:
            self.triggers.set_trigger(new_cfg.right_trigger, self._on_right_trigger)

        self.cfg = new_cfg
        save_config(self.cfg)

    def shutdown(self):
        self.left_clicker.shutdown()
        self.right_clicker.shutdown()
        self.triggers.stop()


def main():
    app = QApplication(sys.argv)
    controller = AppController()
    win = MainWindow(controller.cfg)

    def on_settings_changed(cfg):
        controller.apply_settings(cfg)

    def on_request_bind(side: str):
        # Start capture: accept mouse side buttons and any key
        def _captured(token: str):
            # Update config and UI on capture
            if side == 'left':
                controller.cfg.left_trigger = token
                controller.triggers.set_trigger(token, controller._on_left_trigger)
                win.bound_token_captured.emit('left', token)
            else:
                controller.cfg.right_trigger = token
                controller.triggers.set_trigger(token, controller._on_right_trigger)
                win.bound_token_captured.emit('right', token)
            save_config(controller.cfg)

        controller.triggers.capture_once(_captured, allow={"mouse", "key"})

    win.settings_changed.connect(on_settings_changed)
    win.request_bind.connect(on_request_bind)
    win.show()

    rc = app.exec()
    controller.shutdown()
    sys.exit(rc)


if __name__ == "__main__":
    main()
