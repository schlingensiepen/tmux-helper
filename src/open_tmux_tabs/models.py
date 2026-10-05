"""Data models for Open-TmuxTabs."""

from dataclasses import dataclass, field
from enum import Enum


class HostStatus(Enum):
    """Connection status of a remote host."""

    PENDING = "pending"
    CONNECTED = "connected"
    FAILED = "failed"


@dataclass
class HostEntry:
    """A remote host with its runtime state.

    Fields ssh_target, display_name, last_used, and use_count are persisted
    to hosts.json. All other fields are transient runtime state.
    """

    ssh_target: str
    display_name: str
    status: HostStatus = HostStatus.PENDING
    sessions: list[str] = field(default_factory=list)
    selected_sessions: set[str] = field(default_factory=set)
    new_session_text: str = ""
    last_used: str = ""
    use_count: int = 0
    error_message: str = ""
