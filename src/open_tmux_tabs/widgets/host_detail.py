"""Right panel: Connected host with session list and new session input."""

import re

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Label, Button, SelectionList, TextArea

from open_tmux_tabs.i18n import _

_VALID_SESSION_RE = re.compile(r"^[a-zA-Z0-9_-]+$")


class ReloadRequested(Message):
    def __init__(self, host_index: int) -> None:
        super().__init__()
        self.host_index = host_index


class DeleteHostRequested(Message):
    def __init__(self, host_index: int) -> None:
        super().__init__()
        self.host_index = host_index


class SessionSelectionChanged(Message):
    def __init__(self, host_index: int, selected: set[str]) -> None:
        super().__init__()
        self.host_index = host_index
        self.selected = selected


class NewSessionTextChanged(Message):
    def __init__(self, host_index: int, text: str) -> None:
        super().__init__()
        self.host_index = host_index
        self.text = text


class JumpStartRequested(Message):
    """Launch the currently highlighted session immediately in a new WT tab."""

    def __init__(self, host_index: int, session: str) -> None:
        super().__init__()
        self.host_index = host_index
        self.session = session


class HostDetailView(Widget):
    """Detail view for a connected host."""

    DEFAULT_CSS = """
    HostDetailView {
        width: 100%;
        height: 100%;
        padding: 1 2;
    }

    #detail-header {
        height: 3;
        margin-bottom: 1;
    }

    #detail-host-name {
        text-style: bold;
    }

    #detail-buttons {
        height: 3;
        align: right top;
    }

    #detail-buttons Button {
        margin-left: 1;
    }

    #session-list {
        height: 1fr;
        border: solid $primary;
    }

    #shortcuts-label {
        height: 1;
        margin: 1 0;
        color: $text-muted;
    }

    #new-session-label {
        margin-top: 1;
    }

    #new-session-input {
        height: 1fr;
        min-height: 6;
        border: solid $accent;
    }

    #validation-warning {
        color: $error;
        height: auto;
    }
    """

    BINDINGS = [
        ("t", "toggle_session", _("Toggle")),
        ("a", "toggle_all", _("Toggle All")),
        ("i", "invert_selection", _("Invert")),
        ("j", "jump_start", _("Jump start")),
        ("r", "reload", _("Reload")),
    ]

    def __init__(
        self,
        host_index: int,
        display_name: str,
        sessions: list[str],
        selected: set[str],
        new_session_text: str,
    ) -> None:
        super().__init__()
        self._host_index = host_index
        self._display_name = display_name
        self._sessions = sessions
        self._selected = set(selected)
        self._new_session_text = new_session_text

    def compose(self) -> ComposeResult:
        with Horizontal(id="detail-header"):
            yield Label(self._display_name, id="detail-host-name")
            with Horizontal(id="detail-buttons"):
                yield Button(_("Reload"), variant="primary", id="reload-btn")
                yield Button(_("Delete"), variant="error", id="detail-delete-btn")

        yield Label(_("Running sessions:"), id="sessions-label")
        yield SelectionList[str](
            *[
                (sess, sess, sess in self._selected)
                for sess in self._sessions
            ],
            id="session-list",
        )

        yield Label(
            _("Toggle: [t]   All: [a]   Invert: [i]"),
            id="shortcuts-label",
        )

        yield Label(_("New sessions (one name per line):"), id="new-session-label")
        yield TextArea(self._new_session_text, id="new-session-input")
        yield Label("", id="validation-warning")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "reload-btn":
            self.post_message(ReloadRequested(self._host_index))
        elif event.button.id == "detail-delete-btn":
            self.post_message(DeleteHostRequested(self._host_index))

    def on_selection_list_selected_changed(self, event: SelectionList.SelectedChanged) -> None:
        self._selected = set(event.selection_list.selected)
        self.post_message(
            SessionSelectionChanged(self._host_index, set(self._selected))
        )

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        text = event.text_area.text
        self._new_session_text = text
        self.post_message(NewSessionTextChanged(self._host_index, text))
        self._validate_new_sessions(text)

    def _validate_new_sessions(self, text: str) -> None:
        warnings = []
        for line in text.splitlines():
            name = line.strip()
            if not name:
                continue
            if not _VALID_SESSION_RE.match(name):
                warnings.append(_("Invalid name: '{name}'").format(name=name))
            elif name in self._sessions:
                warnings.append(
                    _("A session named '{name}' already exists.").format(name=name)
                )

        label = self.query_one("#validation-warning", Label)
        label.update("\n".join(warnings))

    def action_toggle_session(self) -> None:
        sl = self.query_one("#session-list", SelectionList)
        highlighted = sl.highlighted
        if highlighted is not None:
            sl.toggle(self._sessions[highlighted])

    def action_toggle_all(self) -> None:
        sl = self.query_one("#session-list", SelectionList)
        if len(sl.selected) == len(self._sessions):
            sl.deselect_all()
        else:
            sl.select_all()

    def action_invert_selection(self) -> None:
        sl = self.query_one("#session-list", SelectionList)
        for sess in self._sessions:
            sl.toggle(sess)

    def action_reload(self) -> None:
        self.post_message(ReloadRequested(self._host_index))

    def action_jump_start(self) -> None:
        """Launch the currently highlighted session immediately."""
        sl = self.query_one("#session-list", SelectionList)
        highlighted = sl.highlighted
        if highlighted is not None and 0 <= highlighted < len(self._sessions):
            session_name = self._sessions[highlighted]
            self.post_message(
                JumpStartRequested(self._host_index, session_name)
            )
