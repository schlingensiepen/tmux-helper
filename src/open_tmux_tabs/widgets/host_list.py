"""Left panel: Host list with two-zone structure and separators."""

from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import ListView, ListItem, Label, Rule

from open_tmux_tabs.i18n import _
from open_tmux_tabs.models import HostEntry, HostStatus

_STATUS_CLASS = {
    HostStatus.PENDING: "host-pending",
    HostStatus.CONNECTED: "host-connected",
    HostStatus.FAILED: "host-failed",
}

# Selection index constants
NEW_HOST = -1
OPEN = -2
DIRECT_SESSION = -3
SHOW_ALL = -4
SEPARATOR = -99  # not selectable


class HostSelected(Message):
    """Posted when a host list entry is highlighted or selected."""

    def __init__(self, index: int, focus: bool = False) -> None:
        super().__init__()
        self.index = index
        self.focus = focus


class HostListView(Widget):
    """Two-zone host list with separators.

    Upper zone (classic workflow):
      + New host
      ─────────
      <hosts>
      >> Open

    Lower zone (fast-track):
      ─────────
      Direct session
      Show all
    """

    DEFAULT_CSS = """
    HostListView {
        width: auto;
        border-right: solid $accent;
    }

    HostListView ListView {
        height: 100%;
        width: auto;
    }

    .host-pending {
        background: $primary-darken-2;
    }

    .host-connected {
        background: $success-darken-2;
    }

    .host-failed {
        background: $error-darken-2;
    }

    .list-action {
        text-style: bold;
    }

    .list-separator {
        height: 1;
        color: $text-muted;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._host_count = 0
        self._index_map: list[int] = []  # maps listview index -> selection index

    def compose(self) -> ComposeResult:
        yield ListView(id="host-listview")

    def _build_index_map(self, host_count: int) -> list[int]:
        """Build mapping from listview item index to selection index.

        Layout:
          0: + New host       -> NEW_HOST
          1: separator        -> SEPARATOR
          2..n+1: hosts       -> 0..n-1
          n+2: >> Open        -> OPEN
          n+3: separator      -> SEPARATOR
          n+4: Direct session -> DIRECT_SESSION
          n+5: Show all       -> SHOW_ALL
        """
        m = [NEW_HOST, SEPARATOR]
        for i in range(host_count):
            m.append(i)
        m.append(OPEN)
        m.append(SEPARATOR)
        m.append(DIRECT_SESSION)
        m.append(SHOW_ALL)
        return m

    async def rebuild(
        self,
        hosts: list[HostEntry],
        display_names: dict[str, str],
        list_width: int,
    ) -> None:
        """Rebuild the list from current host data."""
        self._host_count = len(hosts)
        self._index_map = self._build_index_map(self._host_count)

        listview = self.query_one("#host-listview", ListView)

        new_host_label = _("+ New host")
        open_label = _(">> Open")
        direct_session_label = _("Direct session")
        show_all_label = _("Show all")
        sep = "─" * 18

        # Set explicit width
        labels = [new_host_label, open_label, direct_session_label, show_all_label] + [
            display_names.get(h.ssh_target, h.display_name) for h in hosts
        ]
        max_label_len = max(len(label) for label in labels) if labels else 20
        target_width = max(max_label_len, list_width) + 4
        self.styles.width = target_width
        listview.styles.width = target_width

        await listview.clear()

        # Upper zone
        await listview.append(ListItem(Label(new_host_label, classes="list-action")))
        await listview.append(ListItem(Label(sep, classes="list-separator")))

        for host in hosts:
            name = display_names.get(host.ssh_target, host.display_name)
            item = ListItem(Label(name))
            css_class = _STATUS_CLASS.get(host.status, "")
            if css_class:
                item.add_class(css_class)
            await listview.append(item)

        await listview.append(ListItem(Label(open_label, classes="list-action")))

        # Lower zone
        await listview.append(ListItem(Label(sep, classes="list-separator")))
        await listview.append(ListItem(Label(direct_session_label, classes="list-action")))
        await listview.append(ListItem(Label(show_all_label, classes="list-action")))

    def _listview_index_to_selection(self, idx: int) -> int:
        if 0 <= idx < len(self._index_map):
            return self._index_map[idx]
        return SEPARATOR

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.item is None:
            return
        listview = self.query_one("#host-listview", ListView)
        try:
            idx = list(listview.children).index(event.item)
        except ValueError:
            return
        sel = self._listview_index_to_selection(idx)
        if sel == SEPARATOR:
            # Skip separators: move to next non-separator item
            return
        self.post_message(HostSelected(sel, focus=False))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.item is None:
            return
        listview = self.query_one("#host-listview", ListView)
        try:
            idx = list(listview.children).index(event.item)
        except ValueError:
            return
        sel = self._listview_index_to_selection(idx)
        if sel == SEPARATOR:
            return
        self.post_message(HostSelected(sel, focus=True))

    def select_open(self) -> None:
        """Programmatically select the Open entry."""
        listview = self.query_one("#host-listview", ListView)
        for i, sel in enumerate(self._index_map):
            if sel == OPEN:
                listview.index = i
                break
