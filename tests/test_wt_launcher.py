"""Tests for Windows Terminal launcher."""

from unittest.mock import patch, call

from open_tmux_tabs.wt_launcher import (
    _build_tab_cmd,
    _split_into_batches,
    launch_single_wt,
    launch_per_host,
    launch_all,
)
from open_tmux_tabs.models import HostEntry, HostStatus


class TestBuildTabCmd:
    def test_basic(self):
        cmd = _build_tab_cmd("root@server", "dev")
        assert 'new-tab --title "dev@root@server"' in cmd
        assert "ssh -t root@server" in cmd
        assert "tmux attach-session -t dev" in cmd


class TestSplitIntoBatches:
    def test_single_batch(self):
        parts = ["a" * 100, "b" * 100]
        batches = _split_into_batches(parts)
        assert len(batches) == 1
        assert batches[0] == parts

    def test_splits_on_limit(self):
        # Each part is ~14000 chars + 3 for separator = ~14003
        # Two parts = ~28006 < 30000 (fits in one batch)
        # Three parts = ~42009 > 30000 (needs split)
        # First batch gets 2 parts, second gets 1
        parts = ["x" * 14000, "y" * 14000, "z" * 14000]
        batches = _split_into_batches(parts)
        assert len(batches) == 2
        assert len(batches[0]) == 2
        assert len(batches[1]) == 1

    def test_empty_list(self):
        assert _split_into_batches([]) == []


class TestLaunchSingleWT:
    def test_launches_wt(self):
        with patch("open_tmux_tabs.wt_launcher.subprocess.Popen") as mock:
            launch_single_wt([("root@server", "dev"), ("root@server", "build")])
        mock.assert_called_once()
        cmd = mock.call_args[0][0]
        assert "wt.exe" in cmd
        assert "dev" in cmd
        assert "build" in cmd

    def test_empty_list(self):
        with patch("open_tmux_tabs.wt_launcher.subprocess.Popen") as mock:
            launch_single_wt([])
        mock.assert_not_called()


class TestLaunchPerHost:
    def test_one_wt_per_host(self):
        with patch("open_tmux_tabs.wt_launcher.subprocess.Popen") as mock:
            launch_per_host({
                "root@a": ["dev", "build"],
                "root@b": ["sync"],
            })
        assert mock.call_count == 2

    def test_skips_empty_sessions(self):
        with patch("open_tmux_tabs.wt_launcher.subprocess.Popen") as mock:
            launch_per_host({"root@a": [], "root@b": ["sync"]})
        assert mock.call_count == 1


class TestLaunchAll:
    def test_launches_connected_hosts(self):
        hosts = [
            HostEntry(
                ssh_target="root@a",
                display_name="root@a",
                status=HostStatus.CONNECTED,
                sessions=["dev"],
            ),
            HostEntry(
                ssh_target="root@b",
                display_name="root@b",
                status=HostStatus.FAILED,
                sessions=["build"],
            ),
            HostEntry(
                ssh_target="root@c",
                display_name="root@c",
                status=HostStatus.CONNECTED,
                sessions=["sync", "test"],
            ),
        ]
        with patch("open_tmux_tabs.wt_launcher.subprocess.Popen") as mock:
            launch_all(hosts)
        # Only root@a and root@c should be launched
        assert mock.call_count == 2

    def test_skips_connected_without_sessions(self):
        hosts = [
            HostEntry(
                ssh_target="root@a",
                display_name="root@a",
                status=HostStatus.CONNECTED,
                sessions=[],
            ),
        ]
        with patch("open_tmux_tabs.wt_launcher.subprocess.Popen") as mock:
            launch_all(hosts)
        mock.assert_not_called()
