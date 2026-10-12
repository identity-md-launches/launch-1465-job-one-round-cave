# Handoff Portability

Screen a verified HANDOFF v1 ZIP for filename hazards when a worker passes a
Linux-built deliverable to a Windows or macOS recipient. Python 3.8+ and only
the standard library are required. Run from the workspace root:

```sh
python3 -B line-2/tools/handoff-portability/portability.py demo
```

The demo checks the real inherited `line-2/handoff.zip`, reads no other payload
source files, writes nothing, and never extracts or executes archive content.

For your own archive:

```sh
python3 -B line-2/tools/handoff-portability/portability.py check line-2/handoff.zip
```

Optional `--sha256 HASH` compares an independently trusted archive digest.
Exit 0 means no hazards in this conservative profile; exit 2 emits a complete
JSON report of hazards in an integrity-valid archive; exit 1 refuses invalid
input with no partial report. Issues and paths are sorted deterministically.
Archive integrity is checked first with the unchanged bounded sibling
`line-2/tools/handoff-inspect/inspect_handoff.py`; retain that dependency at its
workspace-relative location when moving this piece.

The screen detects Windows forbidden punctuation, reserved device names
(including extensions and superscript device digits), trailing spaces/dots,
non-NFC Unicode, UTF-16 component lengths over 255 and relative path lengths
over 240. It compares every file and implicit directory after NFC normalization,
case folding and trimming trailing spaces/dots. It reports spelling collisions
and file/directory collisions, including collisions with the root HANDOFF.json
metadata. It never renames, removes, rewrites, installs or extracts anything.

This is intentionally conservative: Unicode case folding can flag names that
some filesystems distinguish. Conversely, filesystem versions, destination
prefixes, permissions, executable bits, platform-specific program behavior,
short-name aliases and OS extraction policies are outside this screen. A clean
report does not guarantee successful extraction or execution. Integrity does
not establish sender identity or code safety. No network, environment variables,
keys, wallets, signatures, transactions, payments or uploads are used.

Behavioral checks:

```sh
python3 -B line-2/tools/handoff-portability/test_portability.py
```

Trial results are recorded after local verification in `line-2/checks-26.json`.

When tried, the inherited archive verified its two files and had zero hazards.
All 17 behavioral tests passed, including real ZIP hazard reports, payload
corruption, trusted-digest mismatch, path refusal and exact CLI exit behavior.
All 19 inherited inspector tests also passed. The demo's self-computed hash
is an integrity identifier, not independent authentication.
