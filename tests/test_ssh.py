"""Tests for SSH communication."""

import subprocess
from unittest.mock import patch

import pytest

from open_tmux_tabs.ssh import ssh_connect, ssh_create_and_list, _parse_output


class TestParseOutput:
    def test_sessions_only(self):
        sessions, created, status = _parse_output("dev\nbuild\nsync")
        assert sessions == ["dev", "build", "sync"]
        assert created == []

    def test_config_and_sessions(self):
        sessions, created, status = _parse_output("CFG_OK\ndev\nbuild")
        assert sessions == ["dev", "build"]
        assert "CFG_OK" in status

    def test_created_sessions(self):
        sessions, created, status = _parse_output(
            "CFG_OK\nCREATED:new1\nEXISTS:old1\ndev\nnew1\nold1"
        )
        assert created == ["new1"]
        assert sessions == ["dev", "new1", "old1"]

    def test_no_sessions(self):
        sessions, created, status = _parse_output("CFG_OK\nNO_SESSIONS")
        assert sessions == []
        assert "NO_SESSIONS" in status

    def test_empty_output(self):
        sessions, created, status = _parse_output("")
        assert sessions == []
        assert created == []

    def test_config_deployed(self):
        sessions, _, status = _parse_output("CFG_DEPLOYED_RELOADED\ndev")
        assert sessions == ["dev"]
        assert "CFG_DEPLOYED_RELOADED" in status

    def test_blank_lines_ignored(self):
        sessions, _, _ = _parse_output("\n  \ndev\n\nbuild\n")
        assert sessions == ["dev", "build"]


class TestSSHConnect:
    async def test_successful_connection(self):
        with patch("open_tmux_tabs.ssh._run_ssh") as mock:
            mock.return_value = (0, "CFG_OK\ndev\nbuild\nsync", "")
            sessions, error = await ssh_connect("root@server")
        assert sessions == ["dev", "build", "sync"]
        assert error is None

    async def test_timeout(self):
        with patch(
            "open_tmux_tabs.ssh._run_ssh",
            side_effect=subprocess.TimeoutExpired(cmd="ssh", timeout=120),
        ):
            sessions, error = await ssh_connect("root@server")
        assert sessions == []
        assert "timed out" in error

    async def test_ssh_not_found(self):
        with patch(
            "open_tmux_tabs.ssh._run_ssh", side_effect=FileNotFoundError
        ):
            sessions, error = await ssh_connect("root@server")
        assert sessions == []
        assert "not found" in error

    async def test_connection_failed(self):
        with patch("open_tmux_tabs.ssh._run_ssh") as mock:
            mock.return_value = (255, "", "Connection refused")
            sessions, error = await ssh_connect("root@server")
        assert sessions == []
        assert "failed" in error

    async def test_nonzero_with_output(self):
        with patch("open_tmux_tabs.ssh._run_ssh") as mock:
            mock.return_value = (1, "CFG_OK\ndev", "")
            sessions, error = await ssh_connect("root@server")
        assert sessions == ["dev"]
        assert error is None


class TestSSHCreateAndList:
    async def test_create_sessions(self):
        with patch("open_tmux_tabs.ssh._run_ssh") as mock:
            mock.return_value = (
                0,
                "CFG_OK\nCREATED:new1\nCREATED:new2\ndev\nnew1\nnew2",
                "",
            )
            created, all_sessions, error = await ssh_create_and_list(
                "root@server", ["new1", "new2"]
            )
        assert created == ["new1", "new2"]
        assert all_sessions == ["dev", "new1", "new2"]
        assert error is None

    async def test_existing_session(self):
        with patch("open_tmux_tabs.ssh._run_ssh") as mock:
            mock.return_value = (0, "CFG_OK\nEXISTS:dev\ndev", "")
            created, all_sessions, error = await ssh_create_and_list(
                "root@server", ["dev"]
            )
        assert created == []
        assert all_sessions == ["dev"]
        assert error is None
