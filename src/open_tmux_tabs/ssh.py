"""SSH communication with remote hosts."""

import asyncio
import subprocess

from open_tmux_tabs.i18n import _

# On Windows, prevent ssh.exe from inheriting the parent console.
# Without this, SSH writes prompts (passwords, host key fingerprints)
# directly to the terminal, bypassing our stdin/stderr redirection
# and corrupting the TUI.
_CREATION_FLAGS = getattr(subprocess, "CREATE_NO_WINDOW", 0)

_TMUX_CONFIG_BLOCK = (
    "if ! grep -q 'Open-TmuxTabs managed settings' ~/.tmux.conf 2>/dev/null; then\n"
    "  cat >> ~/.tmux.conf << 'TMUXCFGEOF'\n"
    "\n"
    "# --- Open-TmuxTabs managed settings (do not remove this line) ---\n"
    "set -g mouse on\n"
    "set -g history-limit 10000\n"
    "# --- end Open-TmuxTabs ---\n"
    "TMUXCFGEOF\n"
    "  tmux source-file ~/.tmux.conf 2>/dev/null && echo 'CFG_DEPLOYED_RELOADED' || echo 'CFG_DEPLOYED_PENDING'\n"
    "else\n"
    "  echo 'CFG_OK'\n"
    "fi"
)

_LIST_SESSIONS = "tmux list-sessions -F '#{session_name}' 2>/dev/null || echo 'NO_SESSIONS'"


def _build_connect_script() -> str:
    return f"{_TMUX_CONFIG_BLOCK}\n{_LIST_SESSIONS}"


def _build_create_script(new_sessions: list[str]) -> str:
    parts = [_TMUX_CONFIG_BLOCK]
    for name in new_sessions:
        parts.append(
            f"tmux new-session -d -s '{name}' 2>/dev/null "
            f"&& echo 'CREATED:{name}' || echo 'EXISTS:{name}'"
        )
    parts.append(_LIST_SESSIONS)
    return "\n".join(parts)


def _run_ssh(host: str, script: str) -> tuple[int, str, str]:
    result = subprocess.run(
        ["ssh", "-o", "ConnectTimeout=10", host, script],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=120,
        creationflags=_CREATION_FLAGS,
    )
    return result.returncode, (result.stdout or "").strip(), (result.stderr or "").strip()


def _parse_output(output: str) -> tuple[list[str], list[str], list[str]]:
    """Parse SSH output into (sessions, created, status_lines)."""
    sessions = []
    created = []
    status_lines = []

    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        if line in ("CFG_DEPLOYED_RELOADED", "CFG_DEPLOYED_PENDING", "CFG_OK"):
            status_lines.append(line)
        elif line.startswith("CREATED:"):
            created.append(line[8:])
        elif line.startswith("EXISTS:"):
            status_lines.append(line)
        elif line == "NO_SESSIONS":
            status_lines.append(line)
        else:
            sessions.append(line)

    return sessions, created, status_lines


async def ssh_connect(host: str) -> tuple[list[str], str | None]:
    """Connect to host, deploy tmux config, list sessions.

    Returns (session_names, error_or_none).
    """
    loop = asyncio.get_running_loop()
    script = _build_connect_script()

    try:
        rc, output, stderr = await loop.run_in_executor(None, _run_ssh, host, script)
    except subprocess.TimeoutExpired:
        return [], _("SSH connection timed out")
    except FileNotFoundError:
        return [], _("ssh executable not found")
    except OSError as e:
        return [], _("SSH error: {error}").format(error=e)

    if rc != 0 and not output:
        err_msg = _("SSH connection failed")
        if stderr:
            err_msg += f"\n{stderr}"
        return [], err_msg

    sessions, _created, _status = _parse_output(output)
    return sessions, None


async def ssh_create_and_list(
    host: str, new_sessions: list[str]
) -> tuple[list[str], list[str], str | None]:
    """Create new sessions and list all sessions.

    Returns (created_names, all_session_names, error_or_none).
    """
    loop = asyncio.get_running_loop()
    script = _build_create_script(new_sessions)

    try:
        rc, output, stderr = await loop.run_in_executor(None, _run_ssh, host, script)
    except subprocess.TimeoutExpired:
        return [], [], _("SSH connection timed out")
    except FileNotFoundError:
        return [], [], _("ssh executable not found")
    except OSError as e:
        return [], [], _("SSH error: {error}").format(error=e)

    if rc != 0 and not output:
        err_msg = _("SSH connection failed")
        if stderr:
            err_msg += f"\n{stderr}"
        return [], [], err_msg

    sessions, created, _ = _parse_output(output)
    return created, sessions, None
