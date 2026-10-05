"""Tests for SSH alias resolution."""

import subprocess
from unittest.mock import patch

import pytest

from open_tmux_tabs.host_resolver import resolve_ssh_target


class TestResolveSSHTarget:
    @pytest.fixture(autouse=True)
    def _no_real_ssh(self, monkeypatch):
        """Prevent accidental real SSH calls."""
        monkeypatch.delenv("SSH_AUTH_SOCK", raising=False)

    async def test_user_at_host_returned_unchanged(self):
        result = await resolve_ssh_target("root@server.example.com")
        assert result == "root@server.example.com"

    async def test_alias_resolved(self):
        fake_output = "hostname dev-server.example.com\nuser root\nport 22\n"
        with patch("open_tmux_tabs.host_resolver.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout=fake_output, stderr=""
            )
            result = await resolve_ssh_target("devbox")
        assert result == "root@devbox"

    async def test_alias_no_user_falls_back_to_current(self):
        fake_output = "hostname dev-server.example.com\nport 22\n"
        with patch("open_tmux_tabs.host_resolver.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout=fake_output, stderr=""
            )
            with patch("open_tmux_tabs.host_resolver.getpass") as mock_getpass:
                mock_getpass.getuser.return_value = "testuser"
                result = await resolve_ssh_target("devbox")
        assert result == "testuser@devbox"

    async def test_ssh_not_found(self):
        with patch(
            "open_tmux_tabs.host_resolver.subprocess.run",
            side_effect=FileNotFoundError,
        ):
            result = await resolve_ssh_target("devbox")
        assert result == "devbox"

    async def test_ssh_timeout(self):
        with patch(
            "open_tmux_tabs.host_resolver.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="ssh", timeout=10),
        ):
            result = await resolve_ssh_target("devbox")
        assert result == "devbox"

    async def test_ssh_nonzero_exit(self):
        with patch("open_tmux_tabs.host_resolver.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=255, stdout="", stderr="error"
            )
            result = await resolve_ssh_target("devbox")
        assert result == "devbox"

    async def test_ssh_no_hostname_in_output(self):
        with patch("open_tmux_tabs.host_resolver.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="port 22\n", stderr=""
            )
            result = await resolve_ssh_target("devbox")
        assert result == "devbox"
