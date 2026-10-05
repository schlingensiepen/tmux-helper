"""Host persistence to JSON file."""

import json
import os
from datetime import datetime
from pathlib import Path

from open_tmux_tabs.models import HostEntry

_DEFAULT_DIR = Path(os.environ.get("APPDATA", Path.home())) / "Open-TmuxTabs"
_DEFAULT_FILE = "hosts.json"


class HostStore:
    """Load and save host entries to a JSON file."""

    def __init__(self, path: Path | None = None):
        if path is None:
            path = _DEFAULT_DIR / _DEFAULT_FILE
        self.path = path

    def load(self) -> list[HostEntry]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                return []
            return [
                HostEntry(
                    ssh_target=entry["ssh_target"],
                    display_name=entry.get("display_name", entry["ssh_target"]),
                    last_used=entry.get("last_used", ""),
                    use_count=entry.get("use_count", 0),
                )
                for entry in data
                if isinstance(entry, dict) and "ssh_target" in entry
            ]
        except (json.JSONDecodeError, OSError, KeyError):
            return []

    def save(self, hosts: list[HostEntry]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = [
            {
                "ssh_target": h.ssh_target,
                "display_name": h.display_name,
                "last_used": h.last_used,
                "use_count": h.use_count,
            }
            for h in hosts
        ]
        self.path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def update_usage(self, hosts: list[HostEntry], ssh_target: str) -> None:
        for host in hosts:
            if host.ssh_target == ssh_target:
                host.last_used = datetime.now().isoformat()
                host.use_count += 1
                break
        self.save(hosts)
