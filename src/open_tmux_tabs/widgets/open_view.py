"""Right panel: Open view with summary and launch buttons."""

import re

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Label, Button, Rule

from open_tmux_tabs.i18n import _
from open_tmux_tabs.models import HostEntry, HostStatus

_VALID_SESSION_RE = re.compile(r"^[a-zA-Z0-9_-]+$")


class OpenAllRequested(Message):
    """Open all sessions on all connected hosts."""
    pass


class OpenSelectionSingleWT(Message):
    """Open selected sessions in one WT window."""
    pass


class OpenSelectionPerHost(Message):
    """Open selected sessions, one WT per host."""
    pass


def _get_valid_new_sessions(text: str) -> list[str]:
    """Extract valid session names from multi-line text."""
    names = []
    for line in text.splitlines():
        name = line.strip()
        if name and _VALID_SESSION_RE.match(name):
            names.append(name)
    return names


def _build_summary(hosts: list[HostEntry]) -> tuple[list[tuple[str, list[str], list[str]]], int, int]:
    """Build summary of selected sessions.

    Returns (entries, total_sessions, total_hosts) where entries is
    [(display_name, existing_sessions, new_sessions), ...].
    """
    entries = []
    total = 0
    for host in hosts:
        existing = sorted(host.selected_sessions)
        new = _get_valid_new_sessions(host.new_session_text)
        if existing or new:
            entries.append((host.display_name, existing, new))
            total += len(existing) + len(new)
    return entries, total, len(entries)


class OpenView(Widget):
    """Summary and launch view."""

    DEFAULT_CSS = """
    OpenView {
        width: 100%;
        height: 100%;
        padding: 2 4;
    }

    #open-all-btn {
        width: 100%;
        margin-bottom: 1;
    }

    #summary-container {
        height: 1fr;
        border: solid $accent;
        padding: 1;
        margin: 1 0;
    }

    #summary-container {
        scrollbar-size: 1 1;
    }

    #selection-buttons {
        height: 3;
    }

    #selection-buttons Button {
        width: 1fr;
        margin: 0 1;
    }
    """

    def __init__(self, hosts: list[HostEntry]) -> None:
        super().__init__()
        self._hosts = hosts

    def compose(self) -> ComposeResult:
        yield Button(
            _("Open all detected sessions"),
            variant="success",
            id="open-all-btn",
        )

        yield Rule()

        yield Label(_("Selection summary:"), id="summary-title")
        summary = ScrollableContainer(id="summary-container")
        summary.can_focus = False
        with summary:
            yield Label("", id="summary-text")

        yield Label("", id="summary-total")

        with Horizontal(id="selection-buttons"):
            yield Button(
                _("One WT – Open selection"),
                variant="primary",
                id="open-selection-single-btn",
                disabled=True,
            )
            yield Button(
                _("Per host – Open selection"),
                variant="primary",
                id="open-selection-perhost-btn",
                disabled=True,
            )

    def on_mount(self) -> None:
        self.refresh_summary()

    def refresh_summary(self) -> None:
        entries, total, host_count = _build_summary(self._hosts)

        existing_marker = _("(existing)")
        new_marker = _("(new)")

        lines = []
        for display_name, existing, new in entries:
            lines.append(f"[bold]{display_name}:[/]")
            for s in existing:
                lines.append(f"  - {s} {existing_marker}")
            for s in new:
                lines.append(f"  - {s} {new_marker}")

        summary_label = self.query_one("#summary-text", Label)
        summary_label.update("\n".join(lines) if lines else _("(no selection)"))

        total_label = self.query_one("#summary-total", Label)
        if total > 0:
            total_label.update(
                _("Total: {total} session(s) on {hosts} host(s)").format(
                    total=total, hosts=host_count
                )
            )
        else:
            total_label.update("")

        has_selection = total > 0
        self.query_one("#open-selection-single-btn", Button).disabled = not has_selection
        self.query_one("#open-selection-perhost-btn", Button).disabled = not has_selection

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "open-all-btn":
            self.post_message(OpenAllRequested())
        elif event.button.id == "open-selection-single-btn":
            self.post_message(OpenSelectionSingleWT())
        elif event.button.id == "open-selection-perhost-btn":
            self.post_message(OpenSelectionPerHost())
