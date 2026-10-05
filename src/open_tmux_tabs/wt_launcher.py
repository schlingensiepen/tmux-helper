"""Windows Terminal launcher."""

import subprocess

from open_tmux_tabs.i18n import _
from open_tmux_tabs.models import HostEntry, HostStatus

MAX_CMD_LEN = 30000


def _build_tab_cmd(host: str, session: str) -> str:
    title = f"{session}@{host}"
    ssh_cmd = f'cmd.exe /c "ssh -t {host} \\"tmux attach-session -t {session}\\""'
    return f'new-tab --title "{title}" {ssh_cmd}'


def _split_into_batches(tab_parts: list[str]) -> list[list[str]]:
    batches: list[list[str]] = []
    current_batch: list[str] = []
    current_len = len("wt.exe ")

    for part in tab_parts:
        part_len = len(part) + 3  # " ; " separator
        if current_batch and current_len + part_len > MAX_CMD_LEN:
            batches.append(current_batch)
            current_batch = []
            current_len = len("wt.exe ")
        current_batch.append(part)
        current_len += part_len

    if current_batch:
        batches.append(current_batch)

    return batches


def _launch_wt(tab_parts: list[str]) -> None:
    for batch in _split_into_batches(tab_parts):
        wt_args = " ; ".join(batch)
        subprocess.Popen(f"wt.exe {wt_args}")


def launch_single_wt(sessions: list[tuple[str, str]]) -> None:
    """Launch one WT window with all sessions as tabs.

    sessions: list of (host, session_name) tuples.
    """
    if not sessions:
        return
    tab_parts = [_build_tab_cmd(host, sess) for host, sess in sessions]
    _launch_wt(tab_parts)


def launch_per_host(sessions_by_host: dict[str, list[str]]) -> None:
    """Launch one WT window per host."""
    for host, session_names in sessions_by_host.items():
        if not session_names:
            continue
        tab_parts = [_build_tab_cmd(host, sess) for sess in session_names]
        _launch_wt(tab_parts)


def launch_all(hosts: list[HostEntry]) -> None:
    """Launch all sessions on all connected hosts (one WT per host)."""
    sessions_by_host = {
        h.ssh_target: h.sessions
        for h in hosts
        if h.status == HostStatus.CONNECTED and h.sessions
    }
    launch_per_host(sessions_by_host)


def launch_setup_host(host: str) -> None:
    """Open a Windows Terminal tab that deploys the user's SSH public key
    to the remote host. The session is interactive so SSH can prompt for
    the password (key auth is not yet set up at this point).

    Looks for an existing public key in %USERPROFILE%\\.ssh\\id_*.pub.
    If multiple keys exist, the first one alphabetically is used.
    """
    # Localized user-facing strings injected into the PowerShell script.
    # Single quotes are doubled for PowerShell escaping.
    msg_no_key = _(
        "No SSH key found in %USERPROFILE%\\.ssh\\."
    ).replace("'", "''")
    msg_create_hint = _(
        "Create one first with: ssh-keygen -t ed25519"
    ).replace("'", "''")
    msg_press_enter = _("Press Enter to close").replace("'", "''")
    msg_deploying = _("Deploying {key} to {host}...").format(
        key="$($pk.Name)", host=host
    ).replace("'", "''")
    msg_deployed = _("Key deployed.").replace("'", "''")
    title = _("Setup: {host}").format(host=host)

    ps_script = (
        "$ErrorActionPreference='Stop'; "
        "$pk = Get-ChildItem $env:USERPROFILE\\.ssh\\id_*.pub "
        "-ErrorAction SilentlyContinue | Select-Object -First 1; "
        "if (-not $pk) { "
        f"Write-Host '{msg_no_key}'; "
        f"Write-Host '{msg_create_hint}'; "
        f"Read-Host '{msg_press_enter}'; exit 1 }} ; "
        f"Write-Host \"{msg_deploying}\"; "
        f"Get-Content $pk.FullName | ssh {host} "
        f"'mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && "
        f"chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys && "
        f"echo {msg_deployed}'; "
        f"Read-Host '{msg_press_enter}'"
    )

    wt_args = (
        f'new-tab --title "{title}" '
        f'powershell.exe -NoProfile -Command "{ps_script}"'
    )
    subprocess.Popen(f"wt.exe {wt_args}")
