# Snapshot compare

Compare two `hash-snapshot` EIP-1898 evidence bundles without any network access. It validates both bundles with the ancestor's strict hash-pinned inspector, then reports deterministic per-label states: unchanged, result changed, request changed, added, or removed. Known ZTO-first and IMD token uint256 observations receive an exact signed decimal delta only when the call's meaning matches; generic bytes are never guessed.

One command from the repository root demonstrates it with the retained real ZTO/IMD observation and never opens a network connection:

```sh
python3 -B line-1/tools/snapshot-compare/snapshot_compare.py demo
```

It reports block `26177975`, its recorded hash, and four `unchanged` calls because the demo compares that retained snapshot to itself. The underlying provider observation was captured on 2026-10-12 and is not a claim about current chain state, a price, or provider honesty.

To compare two snapshots, send one JSON object on standard input, rather than giving filesystem paths:

```sh
python3 -B line-1/tools/snapshot-compare/snapshot_compare.py compare < two-snapshots.json
```

The input must be exactly `{"left": <snapshot>, "right": <snapshot>}` and is capped at 2 MiB. Both children must satisfy the sibling `hash-snapshot` schema: Ethereum mainnet, an unchanged before/after anchor, and every call pinned to the anchor hash with `requireCanonical: true`. This tool makes no requests, imports no dependencies, reads no environment settings, signs nothing, and does not submit transactions. It intentionally does not compare provider identity, authenticate data, prove finality, or explain the cause of a difference.

Eleven offline tests passed, covering retained-data replay, exact ZTO decimal deltas, generic return bytes, changed call requests, added/removed labels, malicious evidence, duplicate JSON keys, size limits, deterministic ordering, and controlled CLI failure:

```sh
python3 -B line-1/tools/snapshot-compare/test_snapshot_compare.py
```
