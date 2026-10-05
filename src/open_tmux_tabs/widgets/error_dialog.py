"""Modal error dialog (message box)."""

from textual.app import ComposeResult
from textual.containers import Container, ScrollableContainer
from textual.screen import ModalScreen
from textual.widgets import Label, Button

from open_tmux_tabs.i18n import _


class ErrorDialog(ModalScreen[None]):
    """Modal message box for error display."""

    DEFAULT_CSS = """
    ErrorDialog {
        align: center middle;
    }

    #error-dialog {
        width: auto;
        min-width: 50;
        max-width: 80%;
        height: auto;
        max-height: 80%;
        border: thick $error;
        background: $surface;
        padding: 1 2;
    }

    #error-dialog-title {
        text-style: bold;
        color: $error;
        width: 100%;
        margin-bottom: 1;
    }

    #error-dialog-body {
        height: auto;
        max-height: 20;
        margin-bottom: 1;
    }

    #error-dialog-ok {
        width: 100%;
    }
    """

    def __init__(self, title: str, message: str) -> None:
        super().__init__()
        self._title = title
        self._message = message

    def compose(self) -> ComposeResult:
        with Container(id="error-dialog"):
            yield Label(self._title, id="error-dialog-title")
            with ScrollableContainer(id="error-dialog-body"):
                yield Label(self._message, id="error-dialog-message")
            yield Button(_("OK"), variant="primary", id="error-dialog-ok")

    def on_mount(self) -> None:
        self.query_one("#error-dialog-ok").focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)

    def on_key(self, event) -> None:
        if event.key in ("escape", "enter"):
            self.dismiss(None)
