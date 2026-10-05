"""Right panel: New host form."""

from textual.app import ComposeResult
from textual.containers import Container
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Input, Button, Label

from open_tmux_tabs.i18n import _


class AddHostRequested(Message):
    """Posted when user wants to add a new host."""

    def __init__(self, ssh_target: str) -> None:
        super().__init__()
        self.ssh_target = ssh_target


class NewHostView(Widget):
    """Form for adding a new SSH host."""

    DEFAULT_CSS = """
    NewHostView {
        width: 100%;
        height: 100%;
        padding: 2 4;
    }

    #new-host-label {
        margin-bottom: 1;
    }

    #new-host-input {
        margin-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label(_("SSH target (user@host or alias):"), id="new-host-label")
        yield Input(placeholder=_("root@server or ssh-alias"), id="new-host-input")
        yield Button(_("Add host"), variant="primary", id="new-host-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "new-host-btn":
            self._submit()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._submit()

    def _submit(self) -> None:
        inp = self.query_one("#new-host-input", Input)
        target = inp.value.strip()
        if target:
            self.post_message(AddHostRequested(target))
            inp.value = ""
