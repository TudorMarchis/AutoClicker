from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGroupBox,
    QComboBox, QSlider, QPushButton, QCheckBox
)
from baseclick.config import AppConfig, save_config
from baseclick.triggers import pretty_token

MODE_OPTIONS = [
    ("Hold", "hold"),
    ("Toggle", "toggle"),
]

class MainWindow(QMainWindow):
    settings_changed = Signal(AppConfig)
    request_bind = Signal(str)  # "left" or "right"
    bound_token_captured = Signal(str, str)  # side, token

    def __init__(self, cfg: AppConfig):
        super().__init__()
        self.setWindowTitle("BaseClick")
        self.setMinimumSize(520, 380)
        self._cfg = cfg

        self._root = QWidget()
        self.setCentralWidget(self._root)
        self._root.setStyleSheet(self._style())

        layout = QVBoxLayout(self._root)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(14)

        title = QLabel("BaseClick")
        title.setObjectName("appTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        layout.addWidget(self._build_mode_group())
        layout.addWidget(self._build_rate_group())
        layout.addWidget(self._build_triggers_group())

        layout.addStretch(1)

        save_btn = QPushButton("Save Settings")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self._on_save)
        layout.addWidget(save_btn)

        self._apply_cfg(self._cfg)
        # Route cross-thread capture updates to UI thread
        self.bound_token_captured.connect(self.set_bound_token)

    def _style(self) -> str:
        accent = "#3DAEE9"
        hover = "#5BC4FF"
        return (
            f"""
            * {{ background: #0f0f10; color: #dcdcdc; font-family: Segoe UI, Arial; }}
            QLabel#appTitle {{
                font-size: 22px; font-weight: 700; letter-spacing: 0.6px; margin: 0 0 8px 0;
                padding: 16px 18px; color: #0b0f12; border: none; border-radius: 10px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3DAEE9, stop:1 #E56B9F);
            }}

            /* Panels */
            QGroupBox {{ background: transparent; border: 1px solid #28323b; border-radius: 10px; margin-top: 14px; }}
            QGroupBox::title {{
                subcontrol-origin: margin; left: 12px; padding: 2px 6px;
                color: {accent}; font-weight: 600; letter-spacing: 0.4px;
            }}

            /* Primary button */
            QPushButton#primaryButton {{
                background: {accent}; color: #0b0f12; border: none; padding: 9px 14px; border-radius: 6px;
            }}
            QPushButton#primaryButton:hover {{ background: {hover}; }}
            QPushButton#primaryButton:pressed {{ background: #2898cf; }}

            /* Neutral buttons */
            QPushButton {{ background: transparent; color: #c8c8c8; border: 1px solid #3a3a3a; padding: 7px 12px; border-radius: 6px; }}
            QPushButton:hover {{ border-color: {accent}; color: #e6e6e6; }}
            QPushButton:pressed {{ background: #161a1e; }}

            /* Dropdown */
            QComboBox {{ background: transparent; border: 1px solid #2a2e33; border-radius: 6px; padding: 6px 8px; color: #d4d4d4; }}
            QComboBox:hover {{ border-color: {accent}; }}
            QComboBox:focus {{ border-color: {accent}; }}
            QComboBox QAbstractItemView {{
                background: #101215; outline: none; selection-background-color: {accent}; selection-color: #0b0f12;
            }}

            /* Sliders */
            QSlider::groove:horizontal {{ height: 6px; background: #171a1e; border-radius: 3px; }}
            QSlider::sub-page:horizontal {{ background: {accent}; border-radius: 3px; }}
            QSlider::add-page:horizontal {{ background: #171a1e; border-radius: 3px; }}
            QSlider::handle:horizontal {{ background: {accent}; width: 14px; height: 14px; border-radius: 7px; margin: -6px 0; }}
            QSlider::handle:horizontal:hover {{ background: {hover}; }}

            /* Checkboxes */
            QCheckBox {{ color: #bfbfbf; }}
            QCheckBox::indicator {{ width: 18px; height: 18px; border: 1px solid #2f2f2f; background: #141619; border-radius: 3px; }}
            QCheckBox::indicator:checked {{ background: {accent}; border-color: {accent}; }}
            QCheckBox::indicator:unchecked:hover {{ border-color: {accent}; }}
            """
        )

    def _build_mode_group(self) -> QGroupBox:
        g = QGroupBox("Mode")
        h = QHBoxLayout(g)

        self.mode_combo = QComboBox()
        for label, value in MODE_OPTIONS:
            self.mode_combo.addItem(label, userData=value)
        h.addWidget(QLabel("Activation:"))
        h.addWidget(self.mode_combo, 1)

        self.master_enable = QCheckBox("Enable triggers")
        self.master_enable.setChecked(True)
        h.addWidget(self.master_enable)

        return g

    def _build_rate_group(self) -> QGroupBox:
        g = QGroupBox("Timing")
        v = QVBoxLayout(g)
        v.setContentsMargins(12, 10, 12, 12)
        v.setSpacing(10)

        # CPS slider (1-100)
        cps_row = QHBoxLayout()
        cps_row.setSpacing(8)
        cps_row.addWidget(QLabel("Speed"))
        self.cps_value = QLabel("15 cps")
        self.cps_value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        cps_row.addWidget(self.cps_value, 1)
        v.addLayout(cps_row)

        self.cps_slider = QSlider(Qt.Horizontal)
        self.cps_slider.setRange(1, 100)
        self.cps_slider.setValue(self._cfg.cps)
        v.addWidget(self.cps_slider)

        # Jitter slider (0-90 mapped to 0.0-0.9)
        jitter_row = QHBoxLayout()
        jitter_row.setSpacing(8)
        jitter_row.addWidget(QLabel("Randomness"))
        self.jitter_value = QLabel("0.25")
        self.jitter_value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        jitter_row.addWidget(self.jitter_value, 1)
        v.addLayout(jitter_row)

        self.jitter_slider = QSlider(Qt.Horizontal)
        self.jitter_slider.setRange(0, 90)
        self.jitter_slider.setValue(int(self._cfg.jitter_ratio * 100))
        v.addWidget(self.jitter_slider)

        return g

    def _build_triggers_group(self) -> QGroupBox:
        g = QGroupBox("Triggers")
        v = QVBoxLayout(g)
        v.setContentsMargins(12, 10, 12, 12)
        v.setSpacing(10)

        # Left bind
        lrow = QHBoxLayout()
        lrow.setSpacing(8)
        self.left_label = QLabel("Not bound")
        self.left_bind_btn = QPushButton("Bind…")
        self.left_bind_btn.clicked.connect(lambda: self._on_bind("left"))
        left_name = QLabel("Left Auto-Click Trigger:")
        left_name.setMinimumWidth(190)
        lrow.addWidget(left_name)
        lrow.addWidget(self.left_label, 1)
        lrow.addWidget(self.left_bind_btn)
        v.addLayout(lrow)

        # Right bind
        rrow = QHBoxLayout()
        rrow.setSpacing(8)
        self.right_label = QLabel("Not bound")
        self.right_bind_btn = QPushButton("Bind…")
        self.right_bind_btn.clicked.connect(lambda: self._on_bind("right"))
        right_name = QLabel("Right Auto-Click Trigger:")
        right_name.setMinimumWidth(190)
        rrow.addWidget(right_name)
        rrow.addWidget(self.right_label, 1)
        rrow.addWidget(self.right_bind_btn)
        v.addLayout(rrow)

        return g

    def _apply_cfg(self, cfg: AppConfig) -> None:
        # Mode
        idx = self.mode_combo.findData(cfg.mode)
        if idx >= 0:
            self.mode_combo.setCurrentIndex(idx)
        # Rate
        self.cps_slider.setValue(cfg.cps)
        self._update_cps_label(cfg.cps)
        self.jitter_slider.setValue(int(cfg.jitter_ratio * 100))
        self._update_jitter_label(cfg.jitter_ratio)
        # Triggers
        self._set_left_token(cfg.left_trigger)
        self._set_right_token(cfg.right_trigger)

        # Wire value changes
        self.mode_combo.currentIndexChanged.connect(self._emit_settings)
        self.cps_slider.valueChanged.connect(self._on_cps_changed)
        self.jitter_slider.valueChanged.connect(self._on_jitter_changed)
        self.master_enable.stateChanged.connect(self._emit_settings)

    def _collect_cfg(self) -> AppConfig:
        return AppConfig(
            cps=self.cps_slider.value(),
            jitter_ratio=self.jitter_slider.value() / 100.0,
            mode=self.mode_combo.currentData(),
            left_trigger=self.left_token,
            right_trigger=self.right_token,
        )

    # Helpers
    def _update_cps_label(self, cps: int):
        self.cps_value.setText(f"{cps} cps")

    def _on_cps_changed(self, value: int):
        self._update_cps_label(value)
        self._emit_settings()

    def _update_jitter_label(self, jitter: float):
        self.jitter_value.setText(f"{jitter:.2f}")

    def _on_jitter_changed(self, value: int):
        self._update_jitter_label(value / 100.0)
        self._emit_settings()
    def _emit_settings(self):
        cfg = self._collect_cfg()
        self.settings_changed.emit(cfg)

    def _on_save(self):
        cfg = self._collect_cfg()
        save_config(cfg)

    # Binding utilities
    def _on_bind(self, side: str):
        # Let controller start capture via signal
        # Update button text to guide user
        if side == "left":
            self.left_bind_btn.setText("Press side button or key…")
            self.left_bind_btn.setEnabled(False)
        else:
            self.right_bind_btn.setText("Press side button or key…")
            self.right_bind_btn.setEnabled(False)
        self.request_bind.emit(side)

    def set_bound_token(self, side: str, token: str):
        if side == "left":
            self._set_left_token(token)
            self.left_bind_btn.setText("Bind…")
            self.left_bind_btn.setEnabled(True)
        else:
            self._set_right_token(token)
            self.right_bind_btn.setText("Bind…")
            self.right_bind_btn.setEnabled(True)
        self._emit_settings()

    def _set_left_token(self, token: str):
        self.left_token = token
        self.left_label.setText(pretty_token(token))

    def _set_right_token(self, token: str):
        self.right_token = token
        self.right_label.setText(pretty_token(token))
