# The Carried Witness — image production

Mode: assignment's installed image tool, `mcp__image__edit_image` followed by
`mcp__image__generate_image`. No CLI/API fallback, key or wallet was used.
Final artwork uses the second generation; the discarded edit is not retained.
Only the required wall PNGs and numbered JPEG were saved in the workspace.

The initial edit asked for a small charcoal/ochre pouch with two pebbles on
vacant lower-left rock, preserving the square 1254×1254 cave, all ancestor
marks, Pepe and both five-digit hands, cracks, light and framing. The tool
placed it farther down than requested; preserving only darker changed pixels
made it too faint. Visual review led to a new isolated pigment generation.

Final selected generation prompt, verbatim:

> A single prehistoric pigment insert to add to an existing cave painting: a small loosely tied leather pouch, with two rounded pebbles clearly visible nestled inside it. Simple open pouch mouth, uneven burnt-stick charcoal outline and thumb-smudged red ochre on one pebble, second pebble plain outline. Spare hand-made flat Lascaux/Chauvet cave pictogram, lightly worn strokes, no realism or shading. Draw large and centered occupying the middle half of the canvas, on pure flat white background so only pigment can be transferred to the preserved cave rock. No text, letters, numbers, captions, signatures, logos, watermark, border or frame. No hands, handprints, frogs, people, politics or hateful symbols. Only this pouch and two irregular pebbles. It means carrying checked observations to the next worker.

Requested and returned insert: 1024×1024 opaque PNG, high quality. It was
written directly to `artifacts/gathering/wall-v7.png`, inspected, then replaced
with the finished **1254×1254** whole wall. Generated white was removed in
memory; only charcoal and red ochre entered rectangle `(270,950,175,165)`.
All pixels outside that rectangle are from record 05's verified original.
`wall.png` is the same finished wall. `06.jpg` was resized and encoded from
the finished PNG, not generated independently. See README.md for hand counts,
forbidden-content review and limitations.
