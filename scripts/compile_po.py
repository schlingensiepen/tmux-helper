#!/usr/bin/env python3
"""Compile all .po files in src/open_tmux_tabs/locales/ to .mo files using msgfmt.py from
Python's Tools (no external gettext required)."""

import sys
from pathlib import Path

# msgfmt.py is shipped with Python in Tools/i18n on most installs.
# Bundled here for portability:
import struct
import re


def make(filename: str, outfile: str) -> None:
    """Compile a .po file to a .mo file."""
    messages: dict = {}

    with open(filename, "rb") as f:
        lines = f.readlines()

    msgid = msgstr = ""
    section = None
    fuzzy = False

    def add(msgid_b: bytes, msgstr_b: bytes) -> None:
        if msgid_b or msgstr_b:
            messages[msgid_b] = msgstr_b

    encoding = "utf-8"
    for lineno, line in enumerate(lines, 1):
        line = line.decode(encoding).strip()
        if not line:
            if section is not None:
                add(msgid.encode(encoding), msgstr.encode(encoding))
                msgid = msgstr = ""
                section = None
                fuzzy = False
            continue
        if line.startswith("#,") and "fuzzy" in line:
            fuzzy = True
            continue
        if line.startswith("#"):
            continue
        if line.startswith("msgid"):
            if section is not None:
                add(msgid.encode(encoding), msgstr.encode(encoding))
                msgstr = ""
            section = "msgid"
            line = line[5:].strip()
            msgid = ""
        elif line.startswith("msgstr"):
            section = "msgstr"
            line = line[6:].strip()
            msgstr = ""

        # quoted string
        if line and line[0] == '"' and line[-1] == '"':
            content = line[1:-1].encode("raw_unicode_escape").decode("unicode_escape")
            if section == "msgid":
                msgid += content
            elif section == "msgstr":
                msgstr += content

    if section is not None:
        add(msgid.encode(encoding), msgstr.encode(encoding))

    # Filter empty translations and the metadata header
    output = {}
    for k, v in messages.items():
        if k == b"":
            output[k] = v  # keep header even if msgstr is metadata
        elif v:
            output[k] = v

    keys = sorted(output.keys())
    offsets = []
    ids = b""
    strs = b""
    for key in keys:
        value = output[key]
        offsets.append((len(ids), len(key), len(strs), len(value)))
        ids += key + b"\0"
        strs += value + b"\0"

    keystart = 7 * 4 + 16 * len(keys)
    valuestart = keystart + len(ids)
    koffsets = []
    voffsets = []
    for o1, l1, o2, l2 in offsets:
        koffsets += [l1, o1 + keystart]
        voffsets += [l2, o2 + valuestart]
    offsets = koffsets + voffsets

    output_bytes = struct.pack(
        "Iiiiiii",
        0x950412DE,
        0,
        len(keys),
        7 * 4,
        7 * 4 + len(keys) * 8,
        0, 0,
    )
    output_bytes += struct.pack("i" * len(offsets), *offsets)
    output_bytes += ids
    output_bytes += strs

    with open(outfile, "wb") as f:
        f.write(output_bytes)


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    locales_dir = project_root / "src" / "open_tmux_tabs" / "locales"

    for po_file in locales_dir.glob("*.po"):
        lang = po_file.stem
        mo_dir = locales_dir / lang / "LC_MESSAGES"
        mo_dir.mkdir(parents=True, exist_ok=True)
        mo_file = mo_dir / "open_tmux_tabs.mo"
        print(f"Compiling {po_file.name} -> {mo_file.relative_to(project_root)}")
        make(str(po_file), str(mo_file))


if __name__ == "__main__":
    main()
