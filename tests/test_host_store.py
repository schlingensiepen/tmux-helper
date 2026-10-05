"""Tests for host persistence."""

import json

from open_tmux_tabs.host_store import HostStore
from open_tmux_tabs.models import HostEntry, HostStatus


class TestHostStore:
    def test_load_empty_when_no_file(self, tmp_path):
        store = HostStore(tmp_path / "hosts.json")
        assert store.load() == []

    def test_save_and_load(self, tmp_path):
        store = HostStore(tmp_path / "hosts.json")
        hosts = [
            HostEntry(
                ssh_target="root@server",
                display_name="root@server",
                last_used="2026-04-06T14:00:00",
                use_count=3,
            )
        ]
        store.save(hosts)
        loaded = store.load()
        assert len(loaded) == 1
        assert loaded[0].ssh_target == "root@server"
        assert loaded[0].display_name == "root@server"
        assert loaded[0].last_used == "2026-04-06T14:00:00"
        assert loaded[0].use_count == 3

    def test_load_ignores_transient_fields(self, tmp_path):
        store = HostStore(tmp_path / "hosts.json")
        hosts = [
            HostEntry(
                ssh_target="root@server",
                display_name="root@server",
                status=HostStatus.CONNECTED,
                sessions=["dev", "build"],
                selected_sessions={"dev"},
                new_session_text="new-sess",
                error_message="some error",
            )
        ]
        store.save(hosts)
        loaded = store.load()
        assert loaded[0].status == HostStatus.PENDING
        assert loaded[0].sessions == []
        assert loaded[0].selected_sessions == set()
        assert loaded[0].new_session_text == ""
        assert loaded[0].error_message == ""

    def test_load_corrupt_json(self, tmp_path):
        f = tmp_path / "hosts.json"
        f.write_text("not valid json", encoding="utf-8")
        store = HostStore(f)
        assert store.load() == []

    def test_load_wrong_type(self, tmp_path):
        f = tmp_path / "hosts.json"
        f.write_text('"just a string"', encoding="utf-8")
        store = HostStore(f)
        assert store.load() == []

    def test_load_skips_invalid_entries(self, tmp_path):
        f = tmp_path / "hosts.json"
        data = [
            {"ssh_target": "root@a", "display_name": "root@a"},
            {"no_target": True},
            "not a dict",
            {"ssh_target": "root@b"},
        ]
        f.write_text(json.dumps(data), encoding="utf-8")
        store = HostStore(f)
        loaded = store.load()
        assert len(loaded) == 2
        assert loaded[0].ssh_target == "root@a"
        assert loaded[1].ssh_target == "root@b"

    def test_save_creates_parent_dirs(self, tmp_path):
        store = HostStore(tmp_path / "sub" / "dir" / "hosts.json")
        store.save([HostEntry(ssh_target="root@x", display_name="root@x")])
        assert store.path.exists()

    def test_update_usage(self, tmp_path):
        store = HostStore(tmp_path / "hosts.json")
        hosts = [
            HostEntry(ssh_target="root@a", display_name="root@a", use_count=0),
            HostEntry(ssh_target="root@b", display_name="root@b", use_count=5),
        ]
        store.update_usage(hosts, "root@b")
        assert hosts[1].use_count == 6
        assert hosts[1].last_used != ""
        # Verify it was persisted
        loaded = store.load()
        assert loaded[1].use_count == 6

    def test_update_usage_unknown_target(self, tmp_path):
        store = HostStore(tmp_path / "hosts.json")
        hosts = [HostEntry(ssh_target="root@a", display_name="root@a")]
        store.update_usage(hosts, "root@unknown")
        assert hosts[0].use_count == 0
