"""Modal confirmation dialog."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Container
from textual.screen import ModalScreen
from textual.widgets import Label, Button

from open_tmux_tabs.i18n import _


class ConfirmDialog(ModalScreen[bool]):
    """Modal dialog that returns True (confirmed) or False (cancelled)."""

    DEFAULT_CSS = """
    ConfirmDialog {
        align: center middle;
    }

    #confirm-dialog {
        width: auto;
        max-width: 80;
        height: auto;
        min-width: 40;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }

    #confirm-message {
        width: auto;
        height: auto;
        margin-bottom: 1;
    }

    #confirm-buttons {
        align: center middle;
        height: 3;
        width: 100%;
    }

    #confirm-buttons Button {
        margin: 0 2;
    }
    """

    def __init__(self, message: str) -> None:
        super().__init__()
        self._message = message

    def compose(self) -> ComposeResult:
        with Container(id="confirm-dialog"):
            yield Label(self._message, id="confirm-message")
            with Horizontal(id="confirm-buttons"):
                yield Button(_("Yes"), variant="error", id="confirm-yes")
                yield Button(_("No"), variant="primary", id="confirm-no")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm-yes")
