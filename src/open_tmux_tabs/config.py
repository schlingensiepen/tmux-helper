"""User configuration persistence."""

import json
import os
from pathlib import Path

_DEFAULT_DIR = Path(os.environ.get("APPDATA", Path.home())) / "Open-TmuxTabs"
_DEFAULT_FILE = "config.json"


class Config:
    """Application configuration stored as JSON."""

    def __init__(self, path: Path | None = None):
        if path is None:
            path = _DEFAULT_DIR / _DEFAULT_FILE
        self.path = path
        self._data: dict = {}
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            self._data = {}
            return
        try:
            self._data = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(self._data, dict):
                self._data = {}
        except (json.JSONDecodeError, OSError):
            self._data = {}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self._data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    @property
    def language(self) -> str | None:
        value = self._data.get("language")
        return value if isinstance(value, str) and value else None

    @language.setter
    def language(self, value: str | None) -> None:
        if value:
            self._data["language"] = value
        else:
            self._data.pop("language", None)
        self.save()
