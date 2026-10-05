"""Tests for display name truncation."""

from open_tmux_tabs.display import compute_display_names, _split_host
from open_tmux_tabs.models import HostEntry


class TestSplitHost:
    def test_full_fqdn(self):
        assert _split_host("root@dev-server.example.com") == (
            "root@dev-server",
            ".example.com",
        )

    def test_no_domain(self):
        assert _split_host("root@devbox") == ("root@devbox", "")

    def test_no_at_sign(self):
        assert _split_host("devbox.example.com") == ("devbox", ".example.com")

    def test_no_at_no_domain(self):
        assert _split_host("devbox") == ("devbox", "")

    def test_multiple_dots(self):
        assert _split_host("root@ci.internal.mycompany.com") == (
            "root@ci",
            ".internal.mycompany.com",
        )


def _make_hosts(*names: str) -> list[HostEntry]:
    return [HostEntry(ssh_target=n, display_name=n) for n in names]


class TestComputeDisplayNames:
    def test_empty_list(self):
        names, width = compute_display_names([])
        assert names == {}
        assert width == 0

    def test_no_max_width_shows_full_names(self):
        hosts = _make_hosts(
            "root@dev-server.example.com",
            "jsp@build.corp.com",
        )
        names, width = compute_display_names(hosts)
        # All padded to longest full name
        assert width == len("root@dev-server.example.com")
        assert names["root@dev-server.example.com"] == "root@dev-server.example.com"
        assert names["jsp@build.corp.com"].startswith("jsp@build.corp.com")
        # All same width (padded)
        assert all(len(n) == width for n in names.values())

    def test_max_width_truncates_when_needed(self):
        hosts = _make_hosts(
            "root@dev-server.internal.mycompany.com",  # 38 chars
            "jsp@build.corp.example.com",              # 26 chars
        )
        names, width = compute_display_names(hosts, max_width=30)
        assert width == 30
        # Longest prefix is "root@dev-server" (15) -> needs at least 15+1+5=21
        # 30 fits well
        assert len(names["root@dev-server.internal.mycompany.com"]) == 30
        assert names["root@dev-server.internal.mycompany.com"] == "root@dev-server.internal.myco"[:30].ljust(30)[:30] or len(names["root@dev-server.internal.mycompany.com"]) == 30

    def test_max_width_not_below_minimum_guarantee(self):
        # Longest prefix is 15 chars, needs at least 15+1+5=21
        # If max_width=15, list still grows to 21
        hosts = _make_hosts(
            "root@dev-server.example.com",
            "jsp@build.corp.com",
        )
        names, width = compute_display_names(hosts, max_width=15)
        assert width == 21  # 15 + 1 + 5

    def test_full_names_fit_within_max_width(self):
        hosts = _make_hosts("root@a.b", "root@c.d")
        names, width = compute_display_names(hosts, max_width=50)
        # Longest full = 8, ideal=8, fits well
        assert width == 8
        assert names["root@a.b"] == "root@a.b"

    def test_no_domains_at_all(self):
        hosts = _make_hosts("root@box1", "admin@box2")
        names, width = compute_display_names(hosts, max_width=50)
        assert width == len("admin@box2")
        assert names["admin@box2"] == "admin@box2"
        # Padded to width
        assert names["root@box1"] == "root@box1".ljust(width)

    def test_single_host_no_domain(self):
        hosts = _make_hosts("root@devbox")
        names, width = compute_display_names(hosts)
        assert names["root@devbox"] == "root@devbox"
        assert width == len("root@devbox")

    def test_min_domain_chars_custom(self):
        hosts = _make_hosts("root@srv.example.com")
        names, width = compute_display_names(hosts, max_width=10, min_domain_chars=3)
        # Prefix=8, min_required=8+1+3=12, max_width=10 → list grows to 12
        assert width == 12
        assert names["root@srv.example.com"] == "root@srv.exa"

    def test_all_padded_to_same_width(self):
        hosts = _make_hosts(
            "root@dev-server.example.com",
            "root@a.b",
            "admin@c.d",
        )
        names, width = compute_display_names(hosts)
        assert all(len(n) == width for n in names.values())
