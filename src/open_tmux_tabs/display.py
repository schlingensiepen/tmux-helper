"""Host display name truncation for the host list."""

from open_tmux_tabs.models import HostEntry

MIN_DOMAIN_CHARS = 5


def _split_host(display_name: str) -> tuple[str, str]:
    """Split 'user@host.domain.com' into ('user@host', '.domain.com').

    If there is no dot after the hostname part, returns (display_name, '').
    For names without '@', treats the first dot as the split point.
    """
    at_pos = display_name.find("@")
    if at_pos == -1:
        dot_pos = display_name.find(".")
    else:
        dot_pos = display_name.find(".", at_pos + 1)

    if dot_pos == -1:
        return display_name, ""

    return display_name[:dot_pos], display_name[dot_pos:]


def compute_display_names(
    hosts: list[HostEntry],
    max_width: int | None = None,
    min_domain_chars: int = MIN_DOMAIN_CHARS,
) -> tuple[dict[str, str], int]:
    """Compute display names for the host list.

    Rules:
    - All entries are padded to the same width.
    - If all full names fit within max_width, show them in full.
    - Otherwise, truncate to max_width.
    - The minimum guarantee: each entry shows at least min_domain_chars
      of its domain. If max_width is too small for that guarantee on
      the longest entry, the list grows beyond max_width to honor it.

    Args:
        hosts: List of hosts.
        max_width: Soft upper bound for the list width. If None, no limit.
        min_domain_chars: Minimum number of domain characters that must
            remain visible (after the dot) for the entry with the longest
            user@host prefix.

    Returns:
        (display_names_dict, list_width) where list_width is the actual
        width every entry is padded to.
    """
    if not hosts:
        return {}, 0

    parts: dict[str, tuple[str, str]] = {}
    max_prefix_len = 0
    max_full_len = 0

    for host in hosts:
        prefix, domain = _split_host(host.display_name)
        parts[host.ssh_target] = (prefix, domain)
        if len(prefix) > max_prefix_len:
            max_prefix_len = len(prefix)
        full_len = len(prefix + domain)
        if full_len > max_full_len:
            max_full_len = full_len

    has_domains = any(domain for _, domain in parts.values())

    # Minimum required width: longest prefix must show at least
    # `min_domain_chars` of its domain (if it has one).
    if has_domains:
        min_required = max_prefix_len + 1 + min_domain_chars
    else:
        min_required = max_prefix_len

    # Ideal: show all full names without truncation.
    ideal = max_full_len

    if max_width is None:
        # No limit -- show full names
        list_width = ideal
    elif ideal <= max_width:
        # Everything fits without truncation
        list_width = ideal
    else:
        # Truncation needed: stay at max_width unless that would
        # violate the minimum guarantee
        list_width = max(min_required, max_width)

    result = {}
    for ssh_target, (prefix, domain) in parts.items():
        full = prefix + domain
        if len(full) <= list_width:
            # Pad to uniform width
            result[ssh_target] = full.ljust(list_width)
        else:
            result[ssh_target] = full[:list_width]

    return result, list_width
