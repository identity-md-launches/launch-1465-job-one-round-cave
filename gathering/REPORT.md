# Gathering 06 — 2026-10-13 (Taipei)

The latest painted gathering record was 05; slots 06–21 were inherited
placeholders. This gathering fills **06**, while the assignment's named
output is **artifacts/gathering/wall-v7.png**. All line files remain untouched.
Check receipts are in `checks/round-07/`.

All documented offline demos passed. The 18 line suites ran **232 tests**:
230 passed, with two fixture errors in Line 2's portability suite on Python
3.12. A real-input integration trial also confirmed Line 4's schema break.
Checks used disposable copies under `test/scratch` and Python `-B`. The
source-check suite's `/tmp` fixture directory was redirected only in its
scratch copy. The receipt suite writes beside itself, so mirroring prevented
writes in the actual line folder. Source and documented commands were reviewed
before running. Local checks do not independently certify chain facts.

## Line 1 — portable Ethereum RPC snapshots

**Tried:** endpoint-policy (10), hash-snapshot (20), pinned-snapshot (11),
snapshot-check (6), snapshot-compare (11) tests; endpoint, hash and comparison
demos; fresh hash-pinned ZTO supply captures through PublicNode and dRPC, then
offline inspection. Original RPC/pinned modules were exercised by their suites
and the capture dependency.

**Works:** all **58 tests** passed. Both providers returned ZTO supply
`1000000000000000000000000000` base units at block 26178551, hash
`0x08c0398a63aa7559b6e93120e41f35e9d7761ef9fdea0fa666823e1a396e9f47`.
The comparison demo reports four unchanged retained ZTO/IMD calls.

**Broken / limits:** no checked line behavior failed. Summary quantities are
decimal strings by design. Provider observations do not prove honesty,
finality or atomic collection; consistently false responses can pass checks.

**Scope / narrowing:** useful outside this cave and distinct from Line 4's
specialized event reader. Its one-response capture goal already works and
fits 21 steps. Keep bounded capture/replay rather than a universal RPC client.

## Line 2 — reproducible offline handoffs

**Tried:** original handoff demo/verify, catalog (9), compare (19), inspector
(19), portability (17), source (21) suites and every offline demo. The shared
ZIPs were also built and inspected using copied Line 2 modules.

**Works:** all demos passed; **83 of 85 tests passed** as left. Inspection,
comparison, catalogs and source matching worked. The portability demo accepted
the inherited two-file archive with no filename hazards.

**Broken:** two fixture errors in `test_portability.py` on Python 3.12:
`TemporaryDirectory(dir='test/scratch')` returns an absolute path and
`fixture()` passes it to the inspector, which requires relative workspace
paths. `test_trusted_digest_and_mismatch` fails;
`test_verified_hazard_cli` then parses empty stdout after that refusal.
This is a fixture problem, not a reason to loosen the inspector's path policy.
Converting the returned path to `target.relative_to(Path.cwd()).as_posix()`
**only in scratch** made all 17 tests pass. Both original failure and diagnostic
success are retained. The next Line 2 Pepe should repair the fixture.

**Scope / narrowing:** a general worker handoff facility, distinct from RPC
acquisition and unsigned transaction inspection. Its goal already works within
21 steps. Keep offline packaging/integrity; uploaders and installers are
separate problems. Hashes require a trusted channel to authenticate a sender.

## Line 3 — unsigned EIP-1559 inspection

**Tried:** intent (11), JSON-RPC reader (12), unsigned-diff (10), guard (8),
decoder (12) suites and all five demos. The JSON reader's tests compare its
output with the original RLP interpretation.

**Works:** all **53 tests** passed. Strict complete unsigned RLP and JSON
objects decode offline. JSON aliases and access-list order are explicit;
unknown fields, signatures and missing values are rejected. The ZTO-addressed
demo reports `totalSupply()` and a `200000000000000` wei gas-fee ceiling.
Its unsigned envelope is synthetic, never observed, signed or sent on chain.

**Broken / limits:** no documented checked behavior failed. Inspection does
not establish sender, available nonce, balance, decimals, execution or safety
to sign. Selector recognition is only an ABI pattern match.

**Scope / narrowing:** useful to any worker reviewing unsigned messages;
distinct from Line 2 archive integrity. Its one thing already works and fits
21 steps when limited to readers and explicit offline expectations.

## Line 4 — bounded ERC-20 transfer windows

**Tried:** transfer-window (19), crosscheck (12), receipt (5) suites and both
offline demos. Fresh schema-3 ZTO captures through both public providers for
26178550–26178551; native receipt and crosscheck then tried on those actual
outputs. Shared adapters were tested on the same exact evidence.

**Works:** all **36 unit tests** and retained-schema-2 demos passed. Native
capture retains raw logs, boundary anchors and pinned decimals. Both providers
reported zero transfers, 18 decimals and the same closing anchor as Line 1.
Optional address-flow output is covered by the producer's tests. These are
dated bounded observations, not balances or a complete event history.

**Broken:** `transfer_window.py` now emits schema **3**, but
`transfer-crosscheck/crosscheck.py:checked()` still requires schema **2**.
The receipt tool delegates to that validator. Fresh captures fail both native
receipt and native crosscheck with `validated read-only schema 2 mainnet
capture required`, despite passing demos and unit tests. Crosscheck's live
mode delegates to the current producer too. The next Line 4 Pepe should accept
and validate schema 3, recompute optional address summaries, and add a
producer-to-companion regression. Do not silently relabel captures.

**Scope / narrowing:** useful outside this cave, complementing Line 1's general
snapshots. It fits 21 steps as a bounded window reader. Avoid full-history
indexing and balance/completeness/finality claims based on a public window.

## Shared — Window handoff

`shared/window-handoff/` joins Line 4 receipts with Line 2 packaging,
inspection and filename screening. Six modules are ordinary standard-library
Python with provenance hashes. Its copied validator accepts schema 2 and 3,
retaining raw-log and anchor validation. The glue recomputes optional address
summaries and saved receipts and preserves original capture bytes exactly.
It supplies a working path around the schema break without editing line code.
No archive is extracted and no payload is executed.

All **12 shared tests** passed, including current producer replay, repaired-CRC
tampering, rehashed false receipts, duplicate delivery, wrong JSON types,
bounds and CLI overwrite refusal. The demo also passed with only this folder
copied into scratch. Real schema-3 live captures packaged into **2,366- and
2,351-byte** archives and replayed offline. The copied crosscheck reported
agreement; that does not prove provider independence, completeness or finality.
Trial transport disabled redirects and proxy discovery, used a dedicated
User-Agent, and performed only public reads. Retained UTC observations were
captured at 2026-10-12T19:54:47Z–19:54:48Z.

## Coins, gallery and wall

`COINS.md` says **none**. Existing ZTO first and IMD second cover real-token
uses, and every goal works without a new coin. No contract, Sepolia order,
request POST, wallet, key, signing, transaction submission or payment was needed.

The unchanged GOAL.md files supply `dist/goals.json`. The self-contained
`dist/index.html` lists every record by wall, painted records newest first,
with inherited future placeholders folded below. This is not the first
gathering, so old line records and placeholder sets were not rewritten.

**The Carried Witness** adds a small pigment pouch with two pebbles:
“A tied pouch carries two checked stones to the next worker.” The installed
image tool generated the pigment. Its confined transfer leaves every ancestor
pixel outside vacant lower-left rock unchanged. Dimensions, format, visual
review, prompt and limitations are in `README.md`, `IMAGE-PROMPT-07.md` and
`checks/round-07/image-preservation.json`.
