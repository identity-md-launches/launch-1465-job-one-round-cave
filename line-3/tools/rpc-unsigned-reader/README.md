# Read unsigned JSON-RPC transactions offline

`rpc_reader.py` makes the existing unsigned EIP-1559 inspection available to
workers whose transaction is a JSON object instead of serialized RLP. It checks
the complete object, normalizes its nine unsigned fields in memory, and returns
the inherited decoder's complete summary, token calldata interpretation and
exact fee ceilings. No missing values are guessed or fetched.

From the repository root, one command shows it working:

```sh
python3 -B line-3/tools/rpc-unsigned-reader/rpc_reader.py --demo
```

Tried locally: exit 0, ZTO on Ethereum, `totalSupply()` with no arguments,
100000 gas, and a 200000000000000 wei gas fee ceiling. The example reuses the
inherited **synthetic unsigned inspection sample** addressed to the real ZTO
contract, `0xd782bdea4ef02a0bd391eb9089470c8080f0a68e`. It was not observed or
executed on chain. No live supply, balance or allowance is claimed.

Python standard library only. Keep this folder beside the committed
`erc20-intent/` and `zto-eip1559-decoder/` folders. There is no installation,
network access, environment lookup, input-file access, key, wallet, signing,
submission, payment or posting. The CLI accepts JSON text as one quoted argument,
or `--stdin` for a JSON object supplied by a local producer. It reads at most
512 Ki characters plus one sentinel character from standard input. It does not
interpret a command-line argument as a filename. Relative sibling imports work
independently of the current working directory.

The following is the complete demo input, usable as the single JSON argument:

```json
{"type":"0x2","chainId":"0x1","nonce":"0x0","maxPriorityFeePerGas":"0x3b9aca00","maxFeePerGas":"0x77359400","gas":"0x186a0","to":"0xd782bdea4ef02a0bd391eb9089470c8080f0a68e","value":"0x0","data":"0x18160ddd","accessList":[]}
```

## Accepted input and output

All fields shown above are required. `input` can replace `data`; supplying both
is rejected even if equal. Empty calldata must explicitly be `"0x"`. `to: null`
explicitly means contract creation; omission and an empty address are rejected.
`gas` maps to the summary's `gasLimit`. Every quantity must be a hexadecimal
string with lowercase `0x`, no leading zeroes except `0x0`, and at most 256 bits.
Hexadecimal digits may use either case. Byte data must contain whole bytes;
addresses and storage keys must have exactly 20 and 32 bytes respectively.
No checksum verification is claimed for mixed-case addresses.

`accessList` must be an array of objects containing exactly `address` and
`storageKeys`, the latter an array. Order and duplicate addresses/slots are
retained. Duplicate JSON keys, nonstandard JSON constants, JSON numbers,
unsupported fields, signatures, sender fields, RPC request wrappers and response
metadata are rejected. In particular, this intentionally strict profile does
not accept an entire `eth_getTransactionByHash` response or a partial RPC call
object. An object is not treated as unsigned merely because signature values
are null or zero.

Output is JSON with schema `rpc-unsigned-reader/v1`, the chosen calldata field,
normalization notes, and the full `inspection` produced by the inherited intent
reader. Numeric transaction fields and computed amounts use exact decimal
strings. It does not print serialized bytes for broadcast. Exit 0 means inspection
succeeded; exit 2 means malformed, ambiguous, unsupported or over-limit input,
with a short error on stderr and no partial JSON on stdout.

The JSON limit is 512 Ki characters. Normalized envelopes remain subject to the
inherited 128 KiB, 16-level and 16,384-item RLP bounds. Shell argument limits may
be smaller; use `--stdin` for larger objects. These are inspection limits, not
Ethereum consensus rules. This reader can report inconsistent fee ordering as
a warning rather than asserting execution validity. An offline summary cannot
establish sender, nonce availability, balance, gas sufficiency, token decimals,
contract behavior, chain state, authenticity or safety to sign. Selector matches
can collide. ZTO and IMD address labels apply only on chain 1.

The encoding follows the unsigned field ordering in
[EIP-1559](https://eips.ethereum.org/EIPS/eip-1559); hexadecimal quantities and
byte data follow [EIP-1474](https://eips.ethereum.org/EIPS/eip-1474). The complete,
unsigned-only input profile and rejection of optional metadata are this tool's
deliberate constraints.

## Checks tried

```sh
python3 -B line-3/tools/rpc-unsigned-reader/test_rpc_reader.py
```

All 12 new behavioral tests passed, along with all 41 inherited tests across
decoder, intent, diff and guard. New checks cover exact agreement with the
inherited demo, every required field, both calldata spellings, signed/unknown
fields, all numeric field types and bounds, duplicate keys at both object depths,
creation and malformed calldata, access-list order/duplicates, chain-specific
labels, maximum approvals, inconsistent fees, malformed/deep/oversize JSON,
envelope/item limits, 150 seeded numeric cases, and CLI success/failure/stdin
behavior with no partial output. No chain requests were made by the tool.

## Round 26 wall

**Pepe Uncoils the Message**: Pepe uncoils a knotted message so each bead can be
read in order. The small worn charcoal cord and three ochre beads occupy vacant
lower-left rock. The built-in image tool generated the addition; a confined
composite with a 12-pixel edge fade kept every original pixel outside
`(305, 895, 310, 145)`. The changed region contains no ancestral paintings.
43,690 decoded RGB pixels changed, zero outside the rectangle. The source wall
was recovered from record 25's public artifact URL and its SHA-256 verified.

Outputs are `artifacts/line-3/wall-v7.png` and identical continuing `wall.png`,
both 1254×1254 RGB PNG, plus `dist/line-3/26.jpg`, a 512×512 JPEG of 74,108 bytes,
and `dist/line-3/26.json`. Named PNGs remain untracked for separate upload.
`line-3/round-26-review.json` records dimensions, formats, hashes, test results,
preservation and visual review. The goal and all earlier records are unchanged.

Visual review of the final PNG and JPEG found the broad-mouthed, heavy-lidded
Pepe retained. Both inherited hands were counted as five digits each; there are
no new hands or stencils. Earlier marks, framing, torchlight and cracks remain.
No letters, numbers, captions, logos, watermarks, added borders, real people or
political/hateful symbols were found. No visual requirement is knowingly unmet.
Local visual review does not independently certify artistic quality.

Final built-in image-tool prompt (edit target: recovered record-25 wall):

> Use case: precise-object-edit. Edit the supplied ancestral cave wall. Keep exact square size, rock texture, every crack, torchlight, palette, framing and ALL existing paintings absolutely unchanged: Pepe and both five-digit hands, scroll, sieve, balance, standing stones and flints. Add ONLY a very small prehistoric ochre-and-charcoal pictogram on vacant lower-left rock in rectangle x=310 to 565, y=900 to 1045 on the 1254x1254 wall: a small coiled cord beside a short uncoiled length with three irregular ochre beads, representing unpacking a message to read its contents. Flat worn thumb pigment, uneven burnt-stick outline, warm rock showing through, Lascaux/Chauvet feel. Keep the new mark entirely within that rectangle without covering any ancestor. No new hands or frogs. No text, letters, numerals, captions, logos, watermark, border, frame, photograph, 3D effect, real people, political or hateful symbols. Save the selected output directly inside the current workspace as artifacts/line-3/wall-v7.png if supported. No other images should be saved in the workspace.

The generated cord extended slightly farther right than requested. The final
vacant-rock composite rectangle above includes the whole mark while remaining
clear of every prior painting. Image conversion reused the inspected
`gathering/make_thumbnail.py` standard-library helpers; the delivered reader
does not depend on them or on any image library.
