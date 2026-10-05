"""Modal dialog for selecting the application language."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Label, Button, RadioSet, RadioButton

from open_tmux_tabs.i18n import _, get_available_languages, get_native_name


class LanguageDialog(ModalScreen[str | None]):
    """Modal that lets the user pick a language. Returns the chosen
    language code, or None if cancelled."""

    DEFAULT_CSS = """
    LanguageDialog {
        align: center middle;
    }

    #language-dialog {
        width: auto;
        min-width: 40;
        height: auto;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }

    #language-dialog-title {
        text-style: bold;
        margin-bottom: 1;
    }

    #language-radioset {
        height: auto;
        margin-bottom: 1;
    }

    #language-buttons {
        align: center middle;
        height: 3;
    }

    #language-buttons Button {
        margin: 0 2;
    }
    """

    def __init__(self, current_language: str) -> None:
        super().__init__()
        self._current = current_language
        self._available = get_available_languages()
        self._selected = current_language

    def compose(self) -> ComposeResult:
        with Container(id="language-dialog"):
            yield Label(_("Select language:"), id="language-dialog-title")
            with RadioSet(id="language-radioset"):
                for code in self._available:
                    yield RadioButton(
                        f"{get_native_name(code)} ({code})",
                        value=(code == self._current),
                        id=f"lang-{code}",
                    )
            with Horizontal(id="language-buttons"):
                yield Button(_("OK"), variant="primary", id="lang-ok")
                yield Button(_("Cancel"), variant="default", id="lang-cancel")

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        if event.pressed and event.pressed.id:
            self._selected = event.pressed.id.removeprefix("lang-")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "lang-ok":
            self.dismiss(self._selected)
        else:
            self.dismiss(None)
