"""Fast-track: sortable table of all sessions across all connected hosts."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, DataTable, Label

from open_tmux_tabs.i18n import _
from open_tmux_tabs.models import HostEntry, HostStatus

_MARK = "✓"
_EMPTY = " "


class ShowAllOpenSingleWT(Message):
    """Open selected sessions in one WT."""

    def __init__(self, sessions: list[tuple[str, str]]) -> None:
        super().__init__()
        self.sessions = sessions


class ShowAllOpenPerHost(Message):
    """Open selected sessions, one WT per host."""

    def __init__(self, sessions: list[tuple[str, str]]) -> None:
        super().__init__()
        self.sessions = sessions


class ShowAllJumpStart(Message):
    """Jump-start one session immediately."""

    def __init__(self, host: str, session: str) -> None:
        super().__init__()
        self.host = host
        self.session = session


class ShowAllView(Widget):
    """Sortable overview table of all sessions across connected hosts."""

    DEFAULT_CSS = """
    ShowAllView {
        width: 100%;
        height: 100%;
        padding: 1 2;
    }

    #show-all-table {
        height: 1fr;
    }

    #show-all-buttons {
        height: 3;
        margin-top: 1;
    }

    #show-all-buttons Button {
        width: 1fr;
        margin: 0 1;
    }
    """

    BINDINGS = [
        ("t", "toggle_row", _("Toggle")),
        ("a", "toggle_all", _("Toggle All")),
        ("i", "invert_selection", _("Invert")),
        ("j", "jump_start", _("Jump start")),
    ]

    def __init__(self, hosts: list[HostEntry]) -> None:
        super().__init__()
        self._hosts = hosts
        self._selected: set[tuple[str, str]] = set()  # (host, session)

    def compose(self) -> ComposeResult:
        yield DataTable(id="show-all-table", cursor_type="row")
        with Horizontal(id="show-all-buttons"):
            yield Button(
                _("One WT – Open selection"),
                variant="primary",
                id="show-all-single-btn",
                disabled=True,
            )
            yield Button(
                _("Per host – Open selection"),
                variant="primary",
                id="show-all-perhost-btn",
                disabled=True,
            )

    def on_mount(self) -> None:
        table = self.query_one("#show-all-table", DataTable)
        table.add_column("", key="mark", width=3)
        table.add_column(_("Host"), key="host")
        table.add_column(_("Session"), key="session")
        self.rebuild_table()

    def rebuild_table(self) -> None:
        table = self.query_one("#show-all-table", DataTable)
        table.clear()

        rows = self._get_all_sessions()
        if not rows:
            table.add_row(_EMPTY, _("Waiting for connections..."), "", key="waiting")
        else:
            for host, session in rows:
                mark = _MARK if (host, session) in self._selected else _EMPTY
                table.add_row(mark, host, session, key=f"{host}|{session}")

        table.sort("session")
        self._update_buttons()

    def _get_all_sessions(self) -> list[tuple[str, str]]:
        rows = []
        for host in self._hosts:
            if host.status == HostStatus.CONNECTED:
                for sess in host.sessions:
                    rows.append((host.ssh_target, sess))
        return rows

    def _get_row_key_at_cursor(self) -> tuple[str, str] | None:
        table = self.query_one("#show-all-table", DataTable)
        if table.row_count == 0:
            return None
        try:
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
            key_str = str(row_key.value)
            if "|" not in key_str:
                return None
            host, session = key_str.split("|", 1)
            return host, session
        except Exception:
            return None

    def _toggle_entry(self, host: str, session: str) -> None:
        key = (host, session)
        if key in self._selected:
            self._selected.discard(key)
        else:
            self._selected.add(key)
        self._update_mark(host, session)
        self._update_buttons()

    def _update_mark(self, host: str, session: str) -> None:
        table = self.query_one("#show-all-table", DataTable)
        row_key = f"{host}|{session}"
        mark = _MARK if (host, session) in self._selected else _EMPTY
        try:
            table.update_cell(row_key, "mark", mark)
        except Exception:
            pass

    def _update_buttons(self) -> None:
        has_selection = len(self._selected) > 0
        self.query_one("#show-all-single-btn", Button).disabled = not has_selection
        self.query_one("#show-all-perhost-btn", Button).disabled = not has_selection

    def _get_selected_list(self) -> list[tuple[str, str]]:
        return sorted(self._selected)

    # --- Actions ---

    def action_toggle_row(self) -> None:
        entry = self._get_row_key_at_cursor()
        if entry:
            self._toggle_entry(*entry)

    def action_toggle_all(self) -> None:
        rows = self._get_all_sessions()
        if len(self._selected) == len(rows):
            self._selected.clear()
        else:
            self._selected = set(rows)
        self._refresh_all_marks()

    def action_invert_selection(self) -> None:
        rows = set(self._get_all_sessions())
        self._selected = rows - self._selected
        self._refresh_all_marks()

    def action_jump_start(self) -> None:
        entry = self._get_row_key_at_cursor()
        if entry:
            self.post_message(ShowAllJumpStart(entry[0], entry[1]))

    def _refresh_all_marks(self) -> None:
        table = self.query_one("#show-all-table", DataTable)
        for host, session in self._get_all_sessions():
            mark = _MARK if (host, session) in self._selected else _EMPTY
            try:
                table.update_cell(f"{host}|{session}", "mark", mark)
            except Exception:
                pass
        self._update_buttons()

    # --- Sort on header click ---

    def on_data_table_header_selected(self, event: DataTable.HeaderSelected) -> None:
        table = self.query_one("#show-all-table", DataTable)
        table.sort(event.column_key)

    # --- Buttons ---

    def on_button_pressed(self, event: Button.Pressed) -> None:
        sessions = self._get_selected_list()
        if not sessions:
            return
        if event.button.id == "show-all-single-btn":
            self.post_message(ShowAllOpenSingleWT(sessions))
        elif event.button.id == "show-all-perhost-btn":
            self.post_message(ShowAllOpenPerHost(sessions))
