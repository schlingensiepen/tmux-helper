"""Open-TmuxTabs TUI application."""

import asyncio
import os
import sys
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.reactive import reactive
from textual.widgets import Footer, ListView

from open_tmux_tabs.config import Config
from open_tmux_tabs.display import compute_display_names
from open_tmux_tabs.host_resolver import resolve_ssh_target
from open_tmux_tabs.host_store import HostStore
from open_tmux_tabs.i18n import _, setup_i18n
from open_tmux_tabs.models import HostEntry, HostStatus
from open_tmux_tabs.ssh import ssh_connect, ssh_create_and_list
from open_tmux_tabs.widgets.app_header import AppHeader
from open_tmux_tabs.widgets.confirm_dialog import ConfirmDialog
from open_tmux_tabs.widgets.error_dialog import ErrorDialog
from open_tmux_tabs.widgets.host_detail import (
    HostDetailView,
    ReloadRequested,
    DeleteHostRequested as DetailDeleteRequested,
    SessionSelectionChanged,
    NewSessionTextChanged,
    JumpStartRequested,
)
from open_tmux_tabs.widgets.host_error import (
    HostErrorView,
    ReconnectRequested,
    SetupHostRequested,
    DeleteHostRequested as ErrorDeleteRequested,
)
from open_tmux_tabs.widgets.direct_session_view import (
    DirectSessionView,
    DirectSessionExecuteSingleWT,
    DirectSessionExecutePerHost,
)
from open_tmux_tabs.widgets.host_list import (
    HostListView,
    HostSelected,
    NEW_HOST,
    OPEN,
    DIRECT_SESSION,
    SHOW_ALL,
)
from open_tmux_tabs.widgets.language_dialog import LanguageDialog
from open_tmux_tabs.widgets.new_host import NewHostView, AddHostRequested
from open_tmux_tabs.widgets.open_view import (
    OpenView,
    OpenAllRequested,
    OpenSelectionSingleWT,
    OpenSelectionPerHost,
    _get_valid_new_sessions,
)
from open_tmux_tabs.widgets.show_all_view import (
    ShowAllView,
    ShowAllOpenSingleWT,
    ShowAllOpenPerHost,
    ShowAllJumpStart,
)
from open_tmux_tabs.wt_launcher import (
    launch_single_wt,
    launch_per_host,
    launch_all,
    launch_setup_host,
)


class OpenTmuxTabsApp(App):
    """Main TUI application for managing remote tmux sessions."""

    CSS_PATH = "app.tcss"
    TITLE = "Open-TmuxTabs"
    ENABLE_COMMAND_PALETTE = False

    BINDINGS = [
        ("q", "quit", _("Quit")),
        ("n", "new_host", _("New host")),
        ("o", "goto_open", _("Open")),
        ("x", "open_all", _("Open all")),
        ("plus_sign", "goto_direct_session", _("Direct session")),
        ("minus", "goto_show_all", _("Show all")),
        ("l", "change_language", _("Language")),
        ("delete", "delete_host", _("Delete host")),
    ]

    selected_index: reactive[int] = reactive(OPEN)

    def __init__(
        self,
        store: HostStore | None = None,
        config: Config | None = None,
        language: str = "en",
    ) -> None:
        super().__init__()
        self.store = store or HostStore()
        self.config = config or Config()
        self.language = language
        self.should_restart = False
        self.hosts: list[HostEntry] = []
        self._display_names: dict[str, str] = {}
        self._list_width: int = 0
        self._error_queue: asyncio.Queue[tuple[str, str]] = asyncio.Queue()
        self._error_consumer_running = False
        self._suppress_highlight = False

    def compose(self) -> ComposeResult:
        yield AppHeader(self.TITLE, self.language)
        yield HostListView(id="host-list-widget")
        yield Container(id="detail-area")
        yield Footer()

    async def on_mount(self) -> None:
        self.hosts = self.store.load()
        self._update_display_names()
        await self._rebuild_host_list()

        if not self.hosts:
            self.selected_index = NEW_HOST
            host_list = self.query_one(HostListView)
            listview = host_list.query_one("#host-listview", ListView)
            listview.index = 0  # "Neuer Host" is first item
        else:
            self.selected_index = OPEN

        self._show_detail(focus=False)

        # Start focus in the host list
        self.call_after_refresh(self._focus_host_list)

        # Connect to all hosts in the background (fire-and-forget)
        for i, host in enumerate(self.hosts):
            self._start_connect_worker(i)

    def _update_display_names(self) -> None:
        # Soft cap on list width; can grow beyond if minimum guarantee requires it
        self._display_names, self._list_width = compute_display_names(
            self.hosts, max_width=30
        )

    async def _rebuild_host_list(self) -> None:
        self._suppress_highlight = True
        host_list = self.query_one(HostListView)
        await host_list.rebuild(self.hosts, self._display_names, self._list_width)

        if self.selected_index == OPEN:
            host_list.select_open()
        self._suppress_highlight = False

    def _show_detail(self, focus: bool = False) -> None:
        detail = self.query_one("#detail-area")
        detail.remove_children()

        idx = self.selected_index
        if idx == NEW_HOST:
            detail.mount(NewHostView())
            if focus:
                self.call_after_refresh(self._focus_new_host_input)
        elif idx == OPEN:
            view = OpenView(self.hosts)
            detail.mount(view)
            if focus:
                self.call_after_refresh(self._focus_open_all)
        elif idx == DIRECT_SESSION:
            detail.mount(DirectSessionView(self.hosts))
        elif idx == SHOW_ALL:
            detail.mount(ShowAllView(self.hosts))
        elif 0 <= idx < len(self.hosts):
            host = self.hosts[idx]
            if host.status == HostStatus.FAILED:
                detail.mount(
                    HostErrorView(idx, host.display_name, host.error_message)
                )
            else:
                detail.mount(
                    HostDetailView(
                        idx,
                        host.display_name,
                        host.sessions,
                        host.selected_sessions,
                        host.new_session_text,
                    )
                )
                if focus:
                    self.call_after_refresh(self._focus_first_session)

    def _queue_error(self, title: str, message: str) -> None:
        """Queue an error for display. A single consumer shows them one by one."""
        self._error_queue.put_nowait((title, message))
        if not self._error_consumer_running:
            self._error_consumer_running = True
            self.run_worker(self._process_error_queue())

    async def _process_error_queue(self) -> None:
        """Show queued errors as modal dialogs, one at a time."""
        while not self._error_queue.empty():
            title, message = self._error_queue.get_nowait()
            await self.push_screen_wait(ErrorDialog(title, message))
        self._error_consumer_running = False

    def _focus_host_list(self) -> None:
        try:
            listview = self.query_one("#host-listview", ListView)
            self.set_focus(listview)
        except Exception:
            pass

    def _focus_new_host_input(self) -> None:
        try:
            self.query_one("#new-host-input").focus()
        except Exception:
            pass

    def _focus_first_session(self) -> None:
        try:
            sl = self.query_one("#session-list")
            sl.focus()
        except Exception:
            pass

    def _focus_open_all(self) -> None:
        try:
            btn = self.query_one("#open-all-btn")
            btn.focus()
        except Exception:
            pass

    def _start_connect_worker(self, index: int) -> None:
        host = self.hosts[index]
        host.status = HostStatus.PENDING

        async def _connect() -> None:
            # Show PENDING state immediately (blue)
            await self._rebuild_host_list()

            try:
                sessions, error = await ssh_connect(host.ssh_target)
            except Exception as exc:
                sessions, error = [], str(exc)

            if error:
                host.status = HostStatus.FAILED
                host.error_message = error
                host.sessions = []
            else:
                host.status = HostStatus.CONNECTED
                host.sessions = sessions
                host.error_message = ""
            await self._rebuild_host_list()
            if self.selected_index == index or self.selected_index == OPEN:
                self._show_detail()

        self.run_worker(_connect(), exclusive=False)

    # --- Event handlers ---

    def on_host_selected(self, event: HostSelected) -> None:
        if self._suppress_highlight and not event.focus:
            return
        self.selected_index = event.index
        self._show_detail(focus=event.focus)

    async def on_add_host_requested(self, event: AddHostRequested) -> None:
        target = event.ssh_target
        resolved = await resolve_ssh_target(target)

        host = HostEntry(ssh_target=target, display_name=resolved)
        self.hosts.append(host)
        self._update_display_names()
        await self._rebuild_host_list()
        self.store.save(self.hosts)

        index = len(self.hosts) - 1
        self.selected_index = index
        self._show_detail()
        self._start_connect_worker(index)

    def on_reload_requested(self, event: ReloadRequested) -> None:
        self._start_connect_worker(event.host_index)

    def on_jump_start_requested(self, event: JumpStartRequested) -> None:
        """Launch a single session immediately (no selection, no reset)."""
        if 0 <= event.host_index < len(self.hosts):
            host = self.hosts[event.host_index]
            try:
                launch_single_wt([(host.ssh_target, event.session)])
                self.store.update_usage(self.hosts, host.ssh_target)
            except Exception as exc:
                self._queue_error(
                    _("Error on {name}").format(name=host.display_name),
                    str(exc),
                )

    def on_reconnect_requested(self, event: ReconnectRequested) -> None:
        self._start_connect_worker(event.host_index)

    def on_setup_host_requested(self, event: SetupHostRequested) -> None:
        if 0 <= event.host_index < len(self.hosts):
            host = self.hosts[event.host_index]
            try:
                launch_setup_host(host.ssh_target)
            except Exception as exc:
                self._queue_error(
                    _("Error on {name}").format(name=host.display_name),
                    str(exc),
                )

    async def _delete_host(self, index: int) -> None:
        if 0 <= index < len(self.hosts):
            confirmed = await self.push_screen_wait(
                ConfirmDialog(
                    _("Delete host '{name}'?").format(
                        name=self.hosts[index].display_name
                    )
                )
            )
            if confirmed:
                self.hosts.pop(index)
                self._update_display_names()
                await self._rebuild_host_list()
                self.store.save(self.hosts)
                self.selected_index = OPEN
                self._show_detail()

    def on_delete_host_requested(self, event: DetailDeleteRequested | ErrorDeleteRequested) -> None:
        self.run_worker(self._delete_host(event.host_index))

    def on_session_selection_changed(self, event: SessionSelectionChanged) -> None:
        if 0 <= event.host_index < len(self.hosts):
            self.hosts[event.host_index].selected_sessions = event.selected

    def on_new_session_text_changed(self, event: NewSessionTextChanged) -> None:
        if 0 <= event.host_index < len(self.hosts):
            self.hosts[event.host_index].new_session_text = event.text

    async def _open_all(self) -> None:
        # Wait for any pending connections
        pending = [
            h for h in self.hosts if h.status == HostStatus.PENDING
        ]
        if pending:
            self.notify(_("Waiting for pending connections..."))
            # Poll until all done
            while any(h.status == HostStatus.PENDING for h in self.hosts):
                await asyncio.sleep(0.5)

        launch_all(self.hosts)
        self._update_usage_and_reset(
            [h for h in self.hosts if h.status == HostStatus.CONNECTED]
        )

    def on_open_all_requested(self, event: OpenAllRequested) -> None:
        self.run_worker(self._open_all())

    async def _open_selection(self, single_wt: bool) -> None:
        sessions_to_open: list[tuple[str, str]] = []
        sessions_by_host: dict[str, list[str]] = {}

        for host in self.hosts:
            existing = sorted(host.selected_sessions)
            new = _get_valid_new_sessions(host.new_session_text)
            all_selected = existing + new

            if not all_selected:
                continue

            if new:
                try:
                    _created, _all, error = await ssh_create_and_list(host.ssh_target, new)
                except Exception as exc:
                    error = str(exc)
                if error:
                    self._queue_error(
                        _("Error on {name}").format(name=host.display_name),
                        error,
                    )

            for sess in all_selected:
                sessions_to_open.append((host.ssh_target, sess))

            sessions_by_host[host.ssh_target] = all_selected

        if single_wt:
            launch_single_wt(sessions_to_open)
        else:
            launch_per_host(sessions_by_host)

        affected = [h for h in self.hosts if h.ssh_target in sessions_by_host]
        self._update_usage_and_reset(affected)

    def on_open_selection_single_wt(self, event: OpenSelectionSingleWT) -> None:
        self.run_worker(self._open_selection(single_wt=True))

    def on_open_selection_per_host(self, event: OpenSelectionPerHost) -> None:
        self.run_worker(self._open_selection(single_wt=False))

    def _update_usage_and_reset(self, affected_hosts: list[HostEntry]) -> None:
        for host in affected_hosts:
            self.store.update_usage(self.hosts, host.ssh_target)
            host.selected_sessions.clear()
            host.new_session_text = ""

        # Reload affected hosts
        for i, host in enumerate(self.hosts):
            if host in affected_hosts:
                self._start_connect_worker(i)

        self._show_detail()

    def action_delete_host(self) -> None:
        idx = self.selected_index
        if 0 <= idx < len(self.hosts):
            self.run_worker(self._delete_host(idx))

    def action_new_host(self) -> None:
        """Jump to the 'New host' entry and focus the input field."""
        self.selected_index = NEW_HOST
        host_list = self.query_one(HostListView)
        listview = host_list.query_one("#host-listview", ListView)
        self._suppress_highlight = True
        listview.index = 0
        self._suppress_highlight = False
        self._show_detail(focus=True)

    def action_goto_open(self) -> None:
        """Jump to the 'Open' entry."""
        self.selected_index = OPEN
        host_list = self.query_one(HostListView)
        host_list.select_open()
        self._show_detail(focus=True)

    def action_goto_direct_session(self) -> None:
        """Jump to the 'Direct session' entry."""
        self.selected_index = DIRECT_SESSION
        self._show_detail(focus=True)

    def action_goto_show_all(self) -> None:
        """Jump to the 'Show all' entry."""
        self.selected_index = SHOW_ALL
        self._show_detail(focus=True)

    def action_open_all(self) -> None:
        """Trigger 'Open all detected sessions' immediately."""
        self.run_worker(self._open_all())

    # --- Show All event handlers ---

    def on_show_all_open_single_wt(self, event: ShowAllOpenSingleWT) -> None:
        if event.sessions:
            try:
                launch_single_wt(event.sessions)
                for host, _sess in event.sessions:
                    self.store.update_usage(self.hosts, host)
            except Exception as exc:
                self._queue_error(_("Error on {name}").format(name="Show All"), str(exc))

    def on_show_all_open_per_host(self, event: ShowAllOpenPerHost) -> None:
        if event.sessions:
            by_host: dict[str, list[str]] = {}
            for host, sess in event.sessions:
                by_host.setdefault(host, []).append(sess)
            try:
                launch_per_host(by_host)
                for host in by_host:
                    self.store.update_usage(self.hosts, host)
            except Exception as exc:
                self._queue_error(_("Error on {name}").format(name="Show All"), str(exc))

    def on_show_all_jump_start(self, event: ShowAllJumpStart) -> None:
        try:
            launch_single_wt([(event.host, event.session)])
            self.store.update_usage(self.hosts, event.host)
        except Exception as exc:
            self._queue_error(
                _("Error on {name}").format(name=event.host), str(exc)
            )

    # --- Direct Session event handlers ---

    def on_direct_session_execute_single_wt(self, event: DirectSessionExecuteSingleWT) -> None:
        self.run_worker(self._execute_direct_session(event.targets, single_wt=True))

    def on_direct_session_execute_per_host(self, event: DirectSessionExecutePerHost) -> None:
        self.run_worker(self._execute_direct_session(event.targets, single_wt=False))

    async def _execute_direct_session(
        self, targets: list[tuple[str, str, bool]], single_wt: bool
    ) -> None:
        """Execute a direct session deployment.

        For each target (host, session, needs_create):
        - If the host is red (failed), attempt reconnect first.
        - If needs_create, create the session via SSH.
        - Open all sessions in WT.
        """
        # Group by host
        hosts_involved: dict[str, list[tuple[str, bool]]] = {}
        for host, session, needs_create in targets:
            hosts_involved.setdefault(host, []).append((session, needs_create))

        # Handle reconnect for red hosts
        for host_target in list(hosts_involved.keys()):
            host_entry = next((h for h in self.hosts if h.ssh_target == host_target), None)
            if host_entry and host_entry.status == HostStatus.FAILED:
                try:
                    sessions, error = await ssh_connect(host_target)
                except Exception as exc:
                    sessions, error = [], str(exc)
                if error:
                    self._queue_error(
                        _("Error on {name}").format(name=host_entry.display_name),
                        error,
                    )
                    del hosts_involved[host_target]
                    continue
                host_entry.status = HostStatus.CONNECTED
                host_entry.sessions = sessions
                host_entry.error_message = ""

        # Create missing sessions
        for host_target, session_list in hosts_involved.items():
            to_create = [name for name, needs in session_list if needs]
            if to_create:
                try:
                    _created, _all, error = await ssh_create_and_list(
                        host_target, to_create
                    )
                except Exception as exc:
                    error = str(exc)
                if error:
                    host_entry = next(
                        (h for h in self.hosts if h.ssh_target == host_target), None
                    )
                    self._queue_error(
                        _("Error on {name}").format(
                            name=host_entry.display_name if host_entry else host_target
                        ),
                        error,
                    )

        # Launch WT
        all_sessions = [
            (host, sess) for host, sl in hosts_involved.items() for sess, _ in sl
        ]
        if all_sessions:
            if single_wt:
                launch_single_wt(all_sessions)
            else:
                by_host = {}
                for host, sess in all_sessions:
                    by_host.setdefault(host, []).append(sess)
                launch_per_host(by_host)

        # Update usage + refresh host session lists (no reset)
        for host_target in hosts_involved:
            self.store.update_usage(self.hosts, host_target)
            # Refresh session lists so next click knows what exists
            host_entry = next((h for h in self.hosts if h.ssh_target == host_target), None)
            if host_entry:
                self._start_connect_worker(self.hosts.index(host_entry))

    def action_change_language(self) -> None:
        """Show the language selection dialog."""
        self.run_worker(self._show_language_dialog())

    async def _show_language_dialog(self) -> None:
        new_language = await self.push_screen_wait(
            LanguageDialog(current_language=self.language)
        )
        if not new_language or new_language == self.language:
            return

        self.config.language = new_language
        confirmed = await self.push_screen_wait(
            ConfirmDialog(
                _(
                    "Language changed to {name}. Restart now?"
                ).format(name=new_language)
            )
        )
        if confirmed:
            self.should_restart = True
            self.exit()


def main() -> None:
    config = Config()
    language = config.language or setup_i18n()
    if config.language:
        setup_i18n(config.language)

    while True:
        app = OpenTmuxTabsApp(config=config, language=language)
        app.run()
        if not app.should_restart:
            break
        # Reload language for next iteration
        config = Config()
        language = setup_i18n(config.language) if config.language else setup_i18n()


if __name__ == "__main__":
    main()
