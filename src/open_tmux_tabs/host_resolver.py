"""SSH alias resolution via ssh -G."""

import asyncio
import getpass
import subprocess

_CREATION_FLAGS = getattr(subprocess, "CREATE_NO_WINDOW", 0)


async def resolve_ssh_target(target: str) -> str:
    """Resolve an SSH target to 'user@hostname' via 'ssh -G'.

    For targets already in 'user@host' format, returns them unchanged.
    For SSH config aliases, resolves the actual user and hostname.
    Returns the original target if resolution fails.
    """
    if "@" in target:
        return target

    loop = asyncio.get_running_loop()
    try:
        result = await loop.run_in_executor(
            None,
            lambda: subprocess.run(
                ["ssh", "-G", target],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
                creationflags=_CREATION_FLAGS,
            ),
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return target

    if result.returncode != 0:
        return target

    hostname = ""
    user = ""
    for line in result.stdout.splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) != 2:
            continue
        key, value = parts[0].lower(), parts[1]
        if key == "hostname":
            hostname = value
        elif key == "user":
            user = value

    if not hostname:
        return target

    if not user:
        user = getpass.getuser()

    return f"{user}@{target}"
