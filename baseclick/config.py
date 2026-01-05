import json
import os
from dataclasses import dataclass, asdict
from typing import Literal

ConfigMode = Literal["hold", "toggle"]
# Trigger token format examples:
#   mouse:x1, mouse:x2, key:f6, key:a, key:esc
TriggerToken = str

CONFIG_DIR = os.path.join(os.getenv("APPDATA", os.getcwd()), "BaseClick")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

@dataclass
class AppConfig:
    cps: int = 15
    jitter_ratio: float = 0.25
    mode: ConfigMode = "hold"
    left_trigger: TriggerToken = "mouse:x2"
    right_trigger: TriggerToken = "mouse:x1"

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)

    @staticmethod
    def from_json(data: str) -> "AppConfig":
        obj = json.loads(data)
        # Migrate legacy values like "x1"/"x2" to token format
        def normalize(tok: str) -> str:
            if tok in ("x1", "x2"):
                return f"mouse:{tok}"
            if tok.startswith("mouse:") or tok.startswith("key:"):
                return tok
            return tok  # leave as-is; UI may correct

        return AppConfig(
            cps=int(obj.get("cps", 15)),
            jitter_ratio=float(obj.get("jitter_ratio", 0.25)),
            mode=obj.get("mode", "hold"),
            left_trigger=normalize(obj.get("left_trigger", "mouse:x2")),
            right_trigger=normalize(obj.get("right_trigger", "mouse:x1")),
        )


def load_config() -> AppConfig:
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return AppConfig.from_json(f.read())
    except Exception:
        pass
    return AppConfig()


def save_config(cfg: AppConfig) -> None:
    os.makedirs(CONFIG_DIR, exist_ok=True)
    tmp_path = CONFIG_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(cfg.to_json())
    os.replace(tmp_path, CONFIG_PATH)
