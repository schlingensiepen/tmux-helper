"""Tests for data models."""

from open_tmux_tabs.models import HostEntry, HostStatus


class TestHostStatus:
    def test_enum_values(self):
        assert HostStatus.PENDING.value == "pending"
        assert HostStatus.CONNECTED.value == "connected"
        assert HostStatus.FAILED.value == "failed"

    def test_enum_members(self):
        assert len(HostStatus) == 3


class TestHostEntry:
    def test_defaults(self):
        host = HostEntry(ssh_target="root@server", display_name="root@server")
        assert host.status == HostStatus.PENDING
        assert host.sessions == []
        assert host.selected_sessions == set()
        assert host.new_session_text == ""
        assert host.last_used == ""
        assert host.use_count == 0
        assert host.error_message == ""

    def test_sessions_are_independent(self):
        h1 = HostEntry(ssh_target="a", display_name="a")
        h2 = HostEntry(ssh_target="b", display_name="b")
        h1.sessions.append("x")
        assert h2.sessions == []

    def test_selected_sessions_are_independent(self):
        h1 = HostEntry(ssh_target="a", display_name="a")
        h2 = HostEntry(ssh_target="b", display_name="b")
        h1.selected_sessions.add("x")
        assert h2.selected_sessions == set()

    def test_explicit_values(self):
        host = HostEntry(
            ssh_target="root@box.example.com",
            display_name="root@box",
            status=HostStatus.CONNECTED,
            sessions=["dev", "build"],
            selected_sessions={"dev"},
            new_session_text="test-session",
            last_used="2026-04-06T14:00:00",
            use_count=5,
            error_message="",
        )
        assert host.ssh_target == "root@box.example.com"
        assert host.display_name == "root@box"
        assert host.status == HostStatus.CONNECTED
        assert host.sessions == ["dev", "build"]
        assert host.selected_sessions == {"dev"}
        assert host.new_session_text == "test-session"
        assert host.use_count == 5
