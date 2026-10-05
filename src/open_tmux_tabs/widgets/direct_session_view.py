"""Fast-track: Deploy sessions to multiple hosts at once."""

import re

from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Label, SelectionList, TextArea

from open_tmux_tabs.i18n import _
from open_tmux_tabs.models import HostEntry, HostStatus

_VALID_SESSION_RE = re.compile(r"^[a-zA-Z0-9_-]+$")

_STATUS_LABEL = {
    HostStatus.PENDING: "[BLUE]",
    HostStatus.CONNECTED: "[GREEN]",
    HostStatus.FAILED: "[RED]",
}


class DirectSessionExecuteSingleWT(Message):
    """Execute: open all in one WT."""

    def __init__(
        self, targets: list[tuple[str, str, bool]]
    ) -> None:
        """targets: [(host, session, needs_create), ...]"""
        super().__init__()
        self.targets = targets


class DirectSessionExecutePerHost(Message):
    """Execute: one WT per host."""

    def __init__(
        self, targets: list[tuple[str, str, bool]]
    ) -> None:
        super().__init__()
        self.targets = targets


def _get_valid_names(text: str) -> list[str]:
    names = []
    for line in text.splitlines():
        name = line.strip()
        if name and _VALID_SESSION_RE.match(name):
            names.append(name)
    return names


class DirectSessionView(Widget):
    """Deploy sessions to multiple hosts."""

    DEFAULT_CSS = """
    DirectSessionView {
        width: 100%;
        height: 100%;
        padding: 1 2;
    }

    #ds-host-label {
        margin-bottom: 1;
    }

    #ds-host-list {
        height: auto;
        max-height: 40%;
        border: solid $primary;
    }

    #ds-session-label {
        margin-top: 1;
    }

    #ds-session-input {
        height: auto;
        min-height: 4;
        max-height: 30%;
        border: solid $accent;
    }

    #ds-validation {
        color: $error;
        height: auto;
    }

    #ds-summary-container {
        height: 1fr;
        border: solid $accent;
        padding: 1;
        margin: 1 0;
    }

    #ds-buttons {
        height: 3;
    }

    #ds-buttons Button {
        width: 1fr;
        margin: 0 1;
    }
    """

    BINDINGS = [
        ("t", "toggle_host", _("Toggle")),
        ("a", "toggle_all_hosts", _("Toggle All")),
        ("i", "invert_hosts", _("Invert")),
        ("j", "execute_single", _("Execute")),
    ]

    def __init__(self, hosts: list[HostEntry]) -> None:
        super().__init__()
        self._hosts = hosts
        self._selected_hosts: set[str] = set()
        self._session_text: str = ""

    def compose(self) -> ComposeResult:
        yield Label(_("Target hosts:"), id="ds-host-label")
        yield SelectionList[str](
            *[
                (
                    f"{h.display_name} {_STATUS_LABEL.get(h.status, '')}",
                    h.ssh_target,
                    h.ssh_target in self._selected_hosts,
                )
                for h in self._hosts
            ],
            id="ds-host-list",
        )

        yield Label(_("Session names (one per line):"), id="ds-session-label")
        yield TextArea(self._session_text, id="ds-session-input")
        yield Label("", id="ds-validation")

        summary = ScrollableContainer(id="ds-summary-container")
        summary.can_focus = False
        with summary:
            yield Label("", id="ds-summary-text")
        yield Label("", id="ds-summary-total")

        with Horizontal(id="ds-buttons"):
            yield Button(
                _("One WT – Execute"),
                variant="primary",
                id="ds-single-btn",
                disabled=True,
            )
            yield Button(
                _("Per host – Execute"),
                variant="primary",
                id="ds-perhost-btn",
                disabled=True,
            )

    def on_selection_list_selected_changed(
        self, event: SelectionList.SelectedChanged
    ) -> None:
        self._selected_hosts = set(event.selection_list.selected)
        self._refresh_summary()

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        self._session_text = event.text_area.text
        self._validate_and_refresh()

    def _validate_and_refresh(self) -> None:
        warnings = []
        for line in self._session_text.splitlines():
            name = line.strip()
            if not name:
                continue
            if not _VALID_SESSION_RE.match(name):
                warnings.append(_("Invalid name: '{name}'").format(name=name))

        self.query_one("#ds-validation", Label).update("\n".join(warnings))
        self._refresh_summary()

    def _refresh_summary(self) -> None:
        names = _get_valid_names(self._session_text)
        selected_hosts = [
            h for h in self._hosts if h.ssh_target in self._selected_hosts
        ]

        existing_marker = _("(existing)")
        new_marker = _("(new)")

        lines = []
        total = 0
        for host in selected_hosts:
            for name in names:
                if name in host.sessions:
                    lines.append(f"  {name} → {host.display_name} {existing_marker}")
                else:
                    lines.append(f"  {name} → {host.display_name} {new_marker}")
                total += 1

        summary_label = self.query_one("#ds-summary-text", Label)
        if lines:
            summary_label.update("\n".join(lines))
        else:
            summary_label.update(_("(no selection)"))

        total_label = self.query_one("#ds-summary-total", Label)
        if total > 0:
            total_label.update(
                _("Total: {total} session(s) on {hosts} host(s)").format(
                    total=total, hosts=len(selected_hosts)
                )
            )
        else:
            total_label.update("")

        has_work = total > 0
        self.query_one("#ds-single-btn", Button).disabled = not has_work
        self.query_one("#ds-perhost-btn", Button).disabled = not has_work

    def _build_targets(self) -> list[tuple[str, str, bool]]:
        """Build list of (host, session, needs_create) tuples."""
        names = _get_valid_names(self._session_text)
        selected_hosts = [
            h for h in self._hosts if h.ssh_target in self._selected_hosts
        ]
        targets = []
        for host in selected_hosts:
            for name in names:
                needs_create = name not in host.sessions
                targets.append((host.ssh_target, name, needs_create))
        return targets

    # --- Actions ---

    def action_toggle_host(self) -> None:
        sl = self.query_one("#ds-host-list", SelectionList)
        highlighted = sl.highlighted
        if highlighted is not None and 0 <= highlighted < len(self._hosts):
            sl.toggle(self._hosts[highlighted].ssh_target)

    def action_toggle_all_hosts(self) -> None:
        sl = self.query_one("#ds-host-list", SelectionList)
        if len(sl.selected) == len(self._hosts):
            sl.deselect_all()
        else:
            sl.select_all()

    def action_invert_hosts(self) -> None:
        sl = self.query_one("#ds-host-list", SelectionList)
        for h in self._hosts:
            sl.toggle(h.ssh_target)

    def action_execute_single(self) -> None:
        targets = self._build_targets()
        if targets:
            self.post_message(DirectSessionExecuteSingleWT(targets))

    # --- Buttons ---

    def on_button_pressed(self, event: Button.Pressed) -> None:
        targets = self._build_targets()
        if not targets:
            return
        if event.button.id == "ds-single-btn":
            self.post_message(DirectSessionExecuteSingleWT(targets))
        elif event.button.id == "ds-perhost-btn":
            self.post_message(DirectSessionExecutePerHost(targets))
