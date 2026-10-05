# Open-TmuxTabs

Persistent TUI for Windows that manages tmux sessions on remote Linux hosts and opens them as tabs in Windows Terminal. Built with [Textual](https://textual.textualize.io/).

## Quick start (Windows, no Python needed)

Open PowerShell and run:

```powershell
irm https://github.com/schlingensiepen/tmux-helper/releases/latest/download/open-tmux-tabs.exe -OutFile "$env:TEMP\open-tmux-tabs.exe"; Start-Process "$env:TEMP\open-tmux-tabs.exe" -Wait
```

This downloads the standalone executable from the latest release and starts it. To keep it, save `open-tmux-tabs.exe` anywhere you like and start it from there.

**You also need:**

- **Windows Terminal**, which is pre-installed on Windows 11. Otherwise install it from the [Microsoft Store](https://aka.ms/terminal).
- **OpenSSH client**, which ships with Windows 10/11 (Settings > Apps > Optional Features > OpenSSH Client). Check it with `ssh -V`.
- **tmux on the remote hosts**: `sudo apt install tmux` (Debian/Ubuntu) or `sudo dnf install tmux` (Fedora/RHEL).
- Key-based SSH access to your hosts. If a host has no key yet, use **Set up host** in the app.

### First steps

The app starts on the **Open** view. Press `n` to add your first SSH host, e.g. `root@myserver` or an alias from `~/.ssh/config`. The app connects and lists the running tmux sessions. Press Enter on **Open all detected sessions** to open them all as Windows Terminal tabs.

## Alternative: Python wheel

If Python 3.10+ and [pipx](https://pipx.pypa.io/) are available, download the wheel from the [releases page](https://github.com/schlingensiepen/tmux-helper/releases) and either run it once or install it:

```bash
pipx run --spec open_tmux_tabs-<version>-py3-none-any.whl open-tmux-tabs
pipx install open_tmux_tabs-<version>-py3-none-any.whl
```

The wheel is also the right choice for starting from a network share. pipx creates the environment locally, not on the share. See `deploy/samba/`.

## What it does

Open-TmuxTabs is a control centre for developers and DevOps specialists who keep many tmux sessions running on several servers: AI agents such as Claude Code, long builds, database migrations, monitoring. Take 10 sessions on 3 hosts: that is 30 manual SSH-and-attach steps every time you reconnect. Here it is one keystroke. The app stays open for the next round.

## Features

- **Host management**: unlimited SSH hosts with automatic reachability check and colour status (blue = connecting, green = ready, red = failed). SSH config aliases are resolved via `ssh -G`.
- **Session overview and selection**: lists the running tmux sessions per host. Pick sessions with `t` (toggle), `a` (toggle all) and `i` (invert).
- **Session creation**: define new session names per host, validated in real time (`[a-zA-Z0-9_-]+`).
- **Quick start**: open every running session on every reachable host, one Windows Terminal window per host, with a single Enter.
- **Batch launch**: open the selection in one Windows Terminal window, or one window per host.
- **Jump start**: open the highlighted session immediately with `j`.
- **Direct session**: distribute a list of session names to several hosts at once. Existing sessions are attached, missing ones are created.
- **Show all**: sortable table of all sessions on all reachable hosts, with its own selection.
- **Set up host**: deploy your SSH public key to a host from an interactive terminal window.
- **7 languages**: English, German, French, Spanish, Esperanto, Klingon and Urdu, switchable at runtime with `l`. Without a saved choice the app follows the system language.

## Layout

```
+--------------------------------------------------------------------+
| Open-TmuxTabs                                    [de] Deutsch      |  Header
+--------------------+-----------------------------------------------+
| + New host         |                                               |
| ────────────       |        DETAIL AREA                            |
| root@dev-se...     |                                               |
| jsp@build.c...     |   switches based on left-panel selection:     |
| admin@ci.lo        |   - New host form                             |
| >> Open            |   - Session list (host connected)             |
| ────────────       |   - Error view (host failed)                  |
| Direct session     |   - Open view (summary + launch buttons)      |
| Show all           |   - Direct session (multi-host deployment)    |
|                    |   - Show all (sortable session table)         |
+--------------------+-----------------------------------------------+
| q Quit  n New  o Open  x All  + Direct  - ShowAll  l Lang  Del     |  Footer
+--------------------------------------------------------------------+
```

The upper zone of the host list is the classic workflow (New host → hosts → Open). The lower zone holds the host-independent fast-track views (Direct session, Show all).

## Keyboard shortcuts

| Key | Action |
|---|---|
| `q` | Quit |
| `n` | Jump to New host |
| `o` | Jump to Open |
| `x` | Open all detected sessions |
| `+` / `-` | Jump to Direct session / Show all |
| `l` | Language |
| `Delete` | Delete selected host (with confirmation) |
| `t` / `a` / `i` | Toggle / toggle all / invert (session lists, Direct session, Show all) |
| `j` | Jump start (Direct session: execute in one window) |
| `r` | Reload sessions (connected host) / reconnect (failed host) |
| `s` | Set up host (failed host) |

Keys are the same in every language. Only the footer labels are translated.

## Data

Hosts are stored in `%APPDATA%\Open-TmuxTabs\hosts.json` and settings (language) in `config.json` in the same folder. Selections and typed session names are not stored.

## Documentation

| Document | Content |
|---|---|
| [`docs/Architecture-Guide.md`](docs/Architecture-Guide.md) | Entry point for developers: architecture, data flow, design decisions |
| [`docs/Benutzerhandbuch.md`](docs/Benutzerhandbuch.md) | User manual (German) |
| [`docs/LIESMICH.md`](docs/LIESMICH.md) | Quick guide for the clawbook-lehre container (German) |
| [`docs/User-Specification.md`](docs/User-Specification.md) | User specification (German) |
| [`docs/Technical-Specification.md`](docs/Technical-Specification.md) | Technical specification (German) |
| [`docs/Testplan.md`](docs/Testplan.md) | Manual test plan (German) |

## Development

```bash
git clone https://github.com/schlingensiepen/tmux-helper.git
cd tmux-helper
pip install -e ".[dev]"
pytest                                        # unit tests
textual run --dev src/open_tmux_tabs/app.py   # run with hot reload
python scripts/compile_po.py                  # compile .po translations to .mo
```

Build the release artefacts:

```bash
pip install ".[build]"
python -m build --wheel                       # dist/open_tmux_tabs-<version>-py3-none-any.whl
pyinstaller packaging/open-tmux-tabs.spec     # dist/open-tmux-tabs.exe (on Windows)
```

Pushing a tag `v*` runs `.github/workflows/release.yml`. It runs the tests, builds the wheel and the Windows executable, and creates a draft release.

## License

Apache License 2.0. See [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).
