"""Custom header with language indicator on the right."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label

from open_tmux_tabs.i18n import get_native_name


class AppHeader(Widget):
    """Header bar showing the app title on the left and the active
    language code + native name on the right."""

    DEFAULT_CSS = """
    AppHeader {
        dock: top;
        height: 1;
        background: $primary-darken-1;
        color: $text;
    }

    AppHeader Horizontal {
        height: 1;
    }

    #header-title {
        width: 1fr;
        padding: 0 1;
        text-style: bold;
    }

    #header-language {
        width: auto;
        padding: 0 1;
        text-style: bold;
    }
    """

    title: reactive[str] = reactive("")
    language: reactive[str] = reactive("en")

    def __init__(self, title: str, language: str) -> None:
        super().__init__()
        self.title = title
        self.language = language

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label(self.title, id="header-title")
            yield Label(self._format_language(), id="header-language")

    def _format_language(self) -> str:
        return f"[{self.language}] {get_native_name(self.language)}"

    def watch_language(self, new_value: str) -> None:
        try:
            label = self.query_one("#header-language", Label)
            label.update(self._format_language())
        except Exception:
            pass
