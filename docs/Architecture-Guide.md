# Architecture Guide -- Open-TmuxTabs

**Purpose of this document:** Entry point for developers, AI agents, or contributors who want to understand the application, its architecture, design decisions, and where to find everything. Start here.

**Last updated:** 2026-10-05 (version 2.0.0)

---

## 1. What is Open-TmuxTabs?

Open-TmuxTabs is a persistent TUI (Terminal User Interface) for Windows that manages remote tmux sessions across multiple Linux servers. It is built with [Textual](https://textual.textualize.io/) and Python 3.10+.

**The problem it solves:** Developers and DevOps specialists who work with many tmux sessions on many servers must manually open SSH connections, attach to sessions one by one, and repeat this every time they reconnect. With 10 sessions on 3 hosts, that is 30 manual steps -- every time.

**The solution:** Open-TmuxTabs provides a single consolidated view of all hosts and their sessions. The user selects what to open, and the app launches the correct SSH+tmux commands as tabs in Windows Terminal. The app stays open for the next round.

**Primary use case:** Managing persistent environments for AI agents (e.g. Claude Code in tmux), long-running builds, monitoring, and database maintenance.

For the full user-facing specification, see [`User-Specification.md`](User-Specification.md) (German, detailed, all views and shortcuts). For the technical internals, see [`Technical-Specification.md`](Technical-Specification.md) (German, modules, design decisions). For the user manual, see [`Benutzerhandbuch.md`](Benutzerhandbuch.md) (German, 5 parts, 22 chapters).

**How to get it:** every GitHub release ships a standalone `open-tmux-tabs.exe` (no Python needed) and a Python wheel. See the [README](../README.md).

---

## 2. Technology Stack

| Component | Technology | Notes |
|---|---|---|
| Language | Python 3.10+ | Type hints, dataclasses, asyncio |
| TUI framework | Textual >= 0.86 | TCSS styling, reactive state, async workers |
| I18n | `gettext` (stdlib) | No external dependency |
| SSH | `subprocess` -> OpenSSH | `CREATE_NO_WINDOW` on Windows |
| Terminal | Windows Terminal (`wt.exe`) | Tab commands via `subprocess.Popen` |
| Tests | pytest + pytest-asyncio | 60 unit tests |
| Packaging | setuptools wheel, PyInstaller | Wheel + standalone Windows `.exe` per release |
| TUI devtools | textual-dev | Snapshot tests (planned) |

**No other runtime dependencies.** Only `textual` is installed via pip. Everything else is stdlib or system tools.

---

## 3. Project Structure

```
tmux-helper/                          # Repository root
├── src/open_tmux_tabs/               # Application package (pip-installable)
│   ├── __main__.py                   # `python -m open_tmux_tabs`
│   ├── app.py                        # Main Textual App class, main() with restart loop
│   ├── app.tcss                      # Global stylesheet (minimal -- 2 rules)
│   ├── config.py                     # User settings persistence (config.json)
│   ├── display.py                    # Host name truncation algorithm
│   ├── host_resolver.py              # SSH alias resolution (ssh -G)
│   ├── host_store.py                 # Host list persistence (hosts.json)
│   ├── i18n.py                       # gettext setup, language discovery
│   ├── models.py                     # Data models (HostEntry, HostStatus)
│   ├── ssh.py                        # SSH communication (connect, create, parse)
│   ├── wt_launcher.py                # Windows Terminal launcher
│   ├── locales/                      # messages.pot, <lang>.po, <lang>/LC_MESSAGES/*.mo
│   └── widgets/                      # All TUI widgets (11 modules)
├── scripts/compile_po.py             # Portable .po -> .mo compiler (no external gettext)
├── packaging/                        # PyInstaller spec + entry script for the .exe
├── deploy/samba/                     # start.cmd + SSH config example for a network share
├── tests/                            # 60 unit tests
├── docs/                             # Documentation (see Document Map below)
├── .github/workflows/                # ci.yml (tests), release.yml (wheel + .exe draft release)
├── pyproject.toml                    # Package definition, deps, entry point
├── LICENSE, NOTICE                   # Apache-2.0
└── README.md                         # Quick start, features, development
```

## 4. Application Architecture

### 4.1 Startup and Restart Loop

The entry point is `main()` in `app.py`. It implements a restart loop for language changes:

```
main()
  ├── Config() -- load config.json (language setting)
  ├── setup_i18n() -- install gettext _() globally
  └── while True:
        ├── OpenTmuxTabsApp().run()
        ├── if not app.should_restart: break
        └── reload Config + i18n for next iteration
```

When the user changes the language, a ConfirmDialog asks "Restart now?". On Yes, `app.should_restart = True` and `app.exit()` are called, and the while-loop creates a fresh App instance.

### 4.2 Widget Tree

```
Screen
├── AppHeader                    # Custom: title left, "[de] Deutsch" right
├── HostListView                 # Left panel: two-zone ListView
│   └── ListView #host-listview  # Items: New Host, separator, hosts, Open, separator, Direct, ShowAll
├── Container #detail-area       # Right panel: children swapped dynamically
│   └── (one of 6 views)         # NewHostView / HostDetailView / HostErrorView /
│                                # OpenView / DirectSessionView / ShowAllView
└── Footer                       # Context-sensitive shortcut display
```

There is **no ContentSwitcher**. The detail area is a plain `Container`. On view change, `_show_detail()` calls `detail.remove_children()` and then `detail.mount(<new_view>)`.

### 4.3 Host List: Two-Zone Structure

```
+ New host         -> NEW_HOST (-1)
────────────       -> SEPARATOR (-99)
root@dev-server    -> 0
jsp@build.corp     -> 1
admin@ci.lo        -> 2
>> Open            -> OPEN (-2)
────────────       -> SEPARATOR (-99)
Direct session     -> DIRECT_SESSION (-3)
Show all           -> SHOW_ALL (-4)
```

The HostListView maintains an `_index_map` that translates ListView item indices to selection constants. Separators are skipped on highlight. Navigation with arrow keys fires `HostSelected(index, focus=False)` (detail updates but focus stays in list). Enter fires `HostSelected(index, focus=True)` (focus moves to detail area).

### 4.4 The Six Views

| Selection | View Class | Purpose | BINDINGS |
|---|---|---|---|
| `NEW_HOST` | `NewHostView` | Input form for SSH target | -- |
| Host (connected) | `HostDetailView` | Session checkboxes + new session textarea | t/a/i/j/r |
| Host (failed) | `HostErrorView` | Reconnect / Setup / Delete | r/s |
| `OPEN` | `OpenView` | Quick-start + summary + 2 launch buttons | -- |
| `DIRECT_SESSION` | `DirectSessionView` | Multi-host session deployment | t/a/i/j |
| `SHOW_ALL` | `ShowAllView` | Sortable DataTable of all sessions | t/a/i/j |

All views are instantiated fresh on each view switch (except that HostEntry data persists in `app.hosts`). The user's session selections and new-session text are stored on the `HostEntry` dataclass and survive view switches.

### 4.5 State Management

The app's state is centralized in the `OpenTmuxTabsApp` instance:

- `hosts: list[HostEntry]` -- all hosts with runtime state (plain list, NOT reactive)
- `selected_index: reactive[int]` -- which list entry is highlighted (uses constants from host_list.py)
- `_display_names: dict[str, str]` -- truncated host names for the list
- `_list_width: int` -- computed width for uniform padding
- `_error_queue: asyncio.Queue` -- serial display of parallel SSH errors
- `_suppress_highlight: bool` -- prevents event storms during list rebuild

There is no `watch_hosts` watcher. UI updates are triggered explicitly by calling `_rebuild_host_list()` (rebuilds the left panel) and `_show_detail()` (rebuilds the right panel).

### 4.6 Background Workers (SSH Connections)

On startup and on reload, a worker is started for each host:

1. `_start_connect_worker(index)` is **synchronous** (fire-and-forget). It sets the host to PENDING and calls `self.run_worker(_connect(), exclusive=False)`.
2. The inner `_connect()` is an **async coroutine** that calls `ssh_connect()`.
3. `ssh_connect()` internally uses `loop.run_in_executor()` to run `subprocess.run()` in a thread.
4. After completion, `_connect()` updates the host status and calls `_rebuild_host_list()` to update the UI.

This means: SSH runs in threads, but UI updates happen in the async main loop. The `_suppress_highlight` flag prevents ListView from firing spurious Highlighted events during rebuild (each `append()` triggers one).

### 4.7 Error Handling

- SSH errors are queued in `_error_queue` (asyncio.Queue).
- A single consumer (`_process_error_queue`) shows them as modal ErrorDialogs, one at a time.
- This prevents dialog stacking when multiple hosts fail in parallel.

### 4.8 Open Flow

**Quick-start ("Open all detected sessions"):**
1. Check for PENDING hosts (still connecting). If any, wait with polling.
2. Collect all sessions from all CONNECTED hosts.
3. `launch_all()` -- one WT window per host.
4. Update usage stats, reset selections, reload hosts.

**Selection buttons ("One WT" / "Per host"):**
1. For each host with selections/new sessions: create new sessions via SSH.
2. Launch via `launch_single_wt()` or `launch_per_host()`.
3. Update usage, clear selections, reload.

**Direct Session execution:**
1. For red hosts: attempt reconnect first.
2. Create missing sessions on selected hosts.
3. Launch all sessions in WT.
4. NO reset -- selections persist for repeat execution.

---

## 5. Data Models

### 5.1 HostEntry (dataclass)

```python
@dataclass
class HostEntry:
    ssh_target: str           # Original input ("root@server" or "devbox")
    display_name: str         # Resolved: "root@devbox" or full FQDN
    status: HostStatus        # PENDING / CONNECTED / FAILED
    sessions: list[str]       # Running tmux sessions (from SSH)
    selected_sessions: set    # User's checkbox selections (runtime only)
    new_session_text: str     # Content of new-session textarea (runtime only)
    last_used: str            # ISO timestamp (persisted)
    use_count: int            # Usage counter (persisted)
    error_message: str        # Last error message (runtime only)
```

### 5.2 Persistence

Two JSON files in `%APPDATA%\Open-TmuxTabs\`:
- `hosts.json` -- only `ssh_target`, `display_name`, `last_used`, `use_count` (runtime fields are NOT saved)
- `config.json` -- only `language` (e.g. `"de"`)

---

## 6. SSH Communication

All SSH is in `ssh.py`. Key design:

- **One batched SSH call per host** -- deploys tmux config, creates requested sessions, lists all sessions, in one `subprocess.run()`.
- **Line protocol parsing:** `CFG_OK`, `CREATED:<name>`, `EXISTS:<name>`, `NO_SESSIONS`, other lines = session names.
- **`CREATE_NO_WINDOW`** on Windows (`getattr(subprocess, "CREATE_NO_WINDOW", 0)`) -- prevents SSH fingerprint prompts from corrupting the TUI by detaching the child process from the parent console.
- **stderr is captured** (`stderr=subprocess.PIPE`), not inherited.
- **Async via `run_in_executor`** -- `subprocess.run()` is blocking, so it runs in a thread pool.

Public API:
```python
async def ssh_connect(host: str) -> tuple[list[str], str | None]
async def ssh_create_and_list(host: str, new_sessions: list[str]) -> tuple[list[str], list[str], str | None]
```

---

## 7. Windows Terminal Launcher

All WT launching is in `wt_launcher.py`. Key design:

- Tab command: `new-tab --title "session@host" cmd.exe /c "ssh -t host \"tmux attach-session -t session\""`
- Tabs joined with ` ; ` in one `wt.exe` invocation.
- **Auto-splitting at 30,000 chars** (Windows `CreateProcessW` limit is ~32,767).
- `subprocess.Popen(f"wt.exe {args}")` -- string arg, no `shell=True`.

Functions:
- `launch_single_wt(sessions)` -- all sessions in one WT window
- `launch_per_host(sessions_by_host)` -- one WT window per host
- `launch_all(hosts)` -- all connected hosts, one WT each
- `launch_setup_host(host)` -- interactive WT for SSH key deployment

---

## 8. Host Display Name Truncation

In `display.py`. The algorithm ensures that even with very long hostnames, the user can always distinguish hosts:

- Split each hostname at the first dot after `@`: `user@hostname` + `.domain.com`
- Find the longest `user@hostname` prefix.
- **5-character domain minimum guarantee:** The list is wide enough that the longest entry shows at least 5 chars of its domain.
- If a `max_width` cap is set (default: 30), entries are truncated, but the minimum guarantee can grow the list beyond `max_width`.
- Returns `(dict[ssh_target -> truncated_name], list_width)`.

---

## 9. Internationalization (i18n)

- **Source language:** English (msgids in code).
- **7 available languages:** en (source), de, fr, es, eo, tlh, ur.
- **Translation files:** `src/open_tmux_tabs/locales/<lang>.po` (human-editable) -> `src/open_tmux_tabs/locales/<lang>/LC_MESSAGES/open_tmux_tabs.mo` (compiled binary). They ship as package data inside the wheel and the `.exe`.
- **Portable compiler:** `scripts/compile_po.py` compiles `.po` to `.mo` without external `gettext`/`msgfmt`. Entries with an empty `msgstr` are skipped (runtime falls back to English); plural forms are not supported.
- **Discovery:** `i18n.find_locales_dir()` looks inside the package first; `i18n.get_available_languages()` scans `*/LC_MESSAGES/*.mo` there.
- **Default language:** without a saved choice the language is detected from `LANG`/`LC_ALL` or the system locale (fallback: English).
- **Language switch:** Global shortcut `l` opens LanguageDialog (RadioSet). After selection, ConfirmDialog asks "Restart now?". On Yes, `should_restart=True` triggers the restart loop in `main()`.
- **Shortcut constancy:** Key bindings are hardcoded (`"t"`, `"a"`, etc.). Only the footer description is translated via `_()`. Keys never change with language.
- **`LANGUAGE_NAMES` dict:** Contains 13 entries (native names for UI display), but only 7 have `.po` files. The extra entries are placeholders for future translations.

---

## 10. Keyboard Shortcuts

### Global (always active)

| Key | Action | Description |
|---|---|---|
| `q` | `action_quit` | Quit |
| `n` | `action_new_host` | Jump to New Host, focus input |
| `o` | `action_goto_open` | Jump to Open |
| `x` | `action_open_all` | Open all sessions immediately |
| `+` | `action_goto_direct_session` | Jump to Direct Session |
| `-` | `action_goto_show_all` | Jump to Show All |
| `l` | `action_change_language` | Language dialog |
| `Delete` | `action_delete_host` | Delete selected host |

### Context-specific

| Key | View | Action |
|---|---|---|
| `t` | HostDetailView, DirectSessionView, ShowAllView | Toggle current item |
| `a` | HostDetailView, DirectSessionView, ShowAllView | Toggle all |
| `i` | HostDetailView, DirectSessionView, ShowAllView | Invert selection |
| `j` | HostDetailView, ShowAllView | Jump start (open immediately) |
| `j` | DirectSessionView | Execute (one WT) |
| `r` | HostDetailView | Reload session list |
| `r` | HostErrorView | Reconnect |
| `s` | HostErrorView | Set up host (deploy SSH key) |

---

## 11. Key Design Decisions

Design decisions with rationales are listed in [`Technical-Specification.md`](Technical-Specification.md), Section 11. The most important ones:

| Decision | Rationale |
|---|---|
| **`CREATE_NO_WINDOW` for all subprocesses** | SSH fingerprint prompts write directly to the inherited console, corrupting the TUI. `BatchMode=yes` was rejected ("hiding problems"). `CREATE_NO_WINDOW` detaches SSH from the parent console entirely. |
| **No ContentSwitcher** | Detail views are swapped via `remove_children()`/`mount()`. Simpler than ContentSwitcher, avoids ID conflicts. |
| **`_suppress_highlight` flag** | ListView fires Highlighted for each `append()` during rebuild, which would overwrite `selected_index`. The flag blocks these spurious events. |
| **All DOM operations `await`ed** | `ListView.clear()` and `append()` are async in Textual. Without `await`, the old DOM persists and causes `DuplicateIds` crashes. |
| **Disjoint selection pools** | HostDetailView, DirectSessionView, and ShowAllView each have their own selection state. Changes in one don't affect the others. |
| **No reset in fast-track views** | Open view resets after launch (collect -> submit -> done). Fast-track views don't reset (direct access -> maybe press again). Different usage philosophy. |
| **Button labels: differentiator first** | "Ein WT -- ..." / "Pro Host -- ..." puts the distinguishing part at the beginning so truncation from the right (CSS `text-overflow: ellipsis`) doesn't lose the difference. |
| **Error dialog queue** | Parallel SSH failures produce errors simultaneously. An `asyncio.Queue` with a single consumer shows them serially. |
| **Session list as SelectionList** | Arrow-key navigation instead of tabbing between separate checkbox widgets. |
| **Views re-created on every switch** | No ContentSwitcher; runtime state (selection, typed names) lives on `HostEntry`, so it survives view changes. |
| **Standalone .exe next to the wheel** | Users without Python get a single file (PyInstaller); the wheel remains for pipx and network shares. |
| **Portable .po compiler** | `scripts/compile_po.py` compiles translations without external `gettext`/`msgfmt`, making the project self-contained. |

---

## 12. Testing

**Framework:** pytest + pytest-asyncio. 60 unit tests, all green.

| Test file | Covers |
|---|---|
| `test_models.py` | HostEntry, HostStatus enum |
| `test_display.py` | Truncation algorithm, edge cases |
| `test_host_store.py` | JSON load/save, corrupt file handling |
| `test_host_resolver.py` | SSH alias resolution |
| `test_ssh.py` | SSH subprocess calls, protocol parsing |
| `test_wt_launcher.py` | WT command construction, auto-splitting |

**Not yet implemented:** integration tests (`test_app.py` with the Textual Pilot API) and snapshot tests (visual regression via `textual-dev`).

CI (`.github/workflows/ci.yml`) runs the unit tests on Linux and Windows for every push and pull request.

Run tests:
```bash
pip install -e ".[dev]"
pytest
```

---

## 13. Status

Version 2.0.0 is feature-complete: 6 views, 7 languages, all shortcuts. It is released as a wheel and as a standalone Windows executable. Planned next: manual test on Windows (75 test cases in [`Testplan.md`](Testplan.md)), screenshots for the user manual (generated with a demo mode and the Textual Pilot API), and integration/snapshot tests.

---

## 14. Document Map

| Document | Language | What it contains | When to read it |
|---|---|---|---|
| **This file** | EN | Architecture overview, entry point for all other docs | First |
| [`User-Specification.md`](User-Specification.md) | DE | All 6 views, all shortcuts, button conventions, design rationales | When you need to understand WHAT the app does and WHY |
| [`Technical-Specification.md`](Technical-Specification.md) | DE | Modules, widget tree, design decisions, packaging | When you need to understand HOW the app is built |
| [`Benutzerhandbuch.md`](Benutzerhandbuch.md) | DE | Full user manual (5 parts, 22 chapters, appendix, cheatsheet) | When you need to understand the USER EXPERIENCE |
| [`LIESMICH.md`](LIESMICH.md) | DE | Quick guide for the clawbook-lehre container (network share) | When you set it up for students |
| [`Testplan.md`](Testplan.md) | DE | 75 manual test cases in 12 categories | When you need to TEST the app |
| [`../README.md`](../README.md) | EN | Quick start, features, shortcuts, development | Quick orientation + installation |

**Convention:** Documentation is in German, code and comments are in English, gettext source strings are in English.
