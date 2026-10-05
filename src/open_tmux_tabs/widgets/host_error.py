"""Right panel: Failed host view with reconnect/setup/delete buttons."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Label, Button

from open_tmux_tabs.i18n import _


class ReconnectRequested(Message):
    def __init__(self, host_index: int) -> None:
        super().__init__()
        self.host_index = host_index


class SetupHostRequested(Message):
    def __init__(self, host_index: int) -> None:
        super().__init__()
        self.host_index = host_index


class DeleteHostRequested(Message):
    def __init__(self, host_index: int) -> None:
        super().__init__()
        self.host_index = host_index


class HostErrorView(Widget):
    """View for a host that failed to connect."""

    BINDINGS = [
        ("s", "setup_host", _("Set up host")),
        ("r", "reconnect", _("Reconnect")),
    ]

    DEFAULT_CSS = """
    HostErrorView {
        width: 100%;
        height: 100%;
        padding: 2 4;
    }

    #error-host-name {
        text-style: bold;
        margin-bottom: 1;
    }

    #error-status {
        color: $error;
        margin-bottom: 2;
    }

    #error-buttons {
        height: 3;
    }

    #error-buttons Button {
        margin-right: 2;
    }
    """

    def __init__(self, host_index: int, display_name: str, error_message: str) -> None:
        super().__init__()
        self._host_index = host_index
        self._display_name = display_name
        self._error_message = error_message

    def compose(self) -> ComposeResult:
        yield Label(self._display_name, id="error-host-name")
        status_text = _("Status: connection failed")
        if self._error_message:
            status_text += f" ({self._error_message})"
        yield Label(status_text, id="error-status")
        with Horizontal(id="error-buttons"):
            yield Button(_("Reconnect"), variant="primary", id="reconnect-btn")
            yield Button(_("Set up host"), variant="warning", id="setup-btn")
            yield Button(_("Delete"), variant="error", id="delete-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "reconnect-btn":
            self.post_message(ReconnectRequested(self._host_index))
        elif event.button.id == "setup-btn":
            self.post_message(SetupHostRequested(self._host_index))
        elif event.button.id == "delete-btn":
            self.post_message(DeleteHostRequested(self._host_index))

    def action_reconnect(self) -> None:
        self.post_message(ReconnectRequested(self._host_index))

    def action_setup_host(self) -> None:
        self.post_message(SetupHostRequested(self._host_index))
