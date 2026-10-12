#!/usr/bin/env python3
"""Behavioral checks for portable receipts; fixtures remain in test/scratch."""
import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import window_handoff as tool


EXAMPLE = (tool.HERE / 'examples/zto-window.json').read_bytes()


class Tests(unittest.TestCase):
    def modified(self):
        return json.loads(EXAMPLE)

    def test_real_retained_capture_roundtrip_exact_bytes_and_determinism(self):
        data = tool.build(EXAMPLE)
        self.assertEqual(data, tool.build(EXAMPLE))
        report = tool.inspect_bytes(data)
        self.assertEqual(report['window_receipt']['transfer_count'], 3)
        self.assertEqual(report['window_receipt']['token'], 'ZTO')
        self.assertTrue(report['portable_filenames'])
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            self.assertEqual(archive.read(tool.CAPTURE), EXAMPLE)

    def test_native_schema3_capture_with_address_summary(self):
        # Exercise the current producer, with retained public reads replayed
        # by a fake transport. Minimal headers are explicit test scaffolding.
        source = self.modified()
        def replay(endpoint, method, params):
            if method == 'eth_chainId': return '0x1'
            if method == 'eth_blockNumber': return hex(source['head_at_capture'])
            if method == 'eth_call': return '0x' + format(source['decimals'], '064x')
            if method == 'eth_getLogs': return source['raw_logs']
            if method == 'eth_getBlockByNumber':
                anchor = source['from_block_anchor'] if int(params[0], 16) == source['from_block'] else source['to_block_anchor']
                return {'number': hex(anchor['number']), 'hash': anchor['hash']}
            raise AssertionError('unexpected RPC method')
        output = io.StringIO()
        selected = source['transfers'][0]['to']
        with patch.object(tool.window, 'rpc', replay), contextlib.redirect_stdout(output):
            tool.window.main(['--from-block', str(source['from_block']), '--to-block',
                              str(source['to_block']), '--address', selected])
        report = tool.inspect_bytes(tool.build(output.getvalue().encode()))
        self.assertEqual(report['capture_schema_version'], 3)
        self.assertTrue(report['address_summary_recomputed'])

    def test_invalid_schema_wrong_chain_and_false_summary_rejected(self):
        for key, value in [('schema_version', True), ('schema_version', 4),
                           ('chain_id', True), ('chain_id', 2), ('transfer_count', 0),
                           ('decimals_block', 1), ('raw_logs', None)]:
            capture = self.modified()
            capture[key] = value
            with self.subTest(key=key, value=value), self.assertRaises((ValueError, RuntimeError)):
                tool.build(tool.canonical(capture))

    def test_removed_log_rejected_even_with_original_receipt(self):
        capture = self.modified()
        capture['raw_logs'][0]['removed'] = True
        with self.assertRaises(RuntimeError):
            tool.build(tool.canonical(capture))

    def test_address_summary_recomputed_and_boolean_count_refused(self):
        capture = self.modified()
        capture['schema_version'] = 3
        summary = tool.window.address_summary(capture['transfers'],
                                              capture['transfers'][0]['to'], capture['decimals'])
        capture['address_window_summary'] = summary
        for field, value in [('net_raw', '123'), ('incoming_transfer_count', True), ('address', 'invalid')]:
            altered = copy.deepcopy(capture)
            altered['address_window_summary'][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                tool.build(tool.canonical(altered))
        capture['schema_version'] = 2
        with self.assertRaises(ValueError):
            tool.build(tool.canonical(capture))

    def test_semantic_digest_ignores_duplicate_delivery_full_capture_changes(self):
        capture = self.modified()
        capture['raw_logs'] = list(reversed(capture['raw_logs'])) + [capture['raw_logs'][0]]
        events, duplicates = tool.window.validate_logs(capture['raw_logs'], capture['decimals'],
            capture['token_address'], capture['from_block'], capture['to_block'])
        capture.update(transfers=events, transfer_count=len(events), duplicate_count=duplicates)
        left = tool.checked_receipt(self.modified())
        right = tool.checked_receipt(capture)
        self.assertEqual(left['window_sha256'], right['window_sha256'])
        self.assertNotEqual(left['capture_sha256'], right['capture_sha256'])

    def test_rehashed_false_receipt_rejected_after_archive_integrity(self):
        receipt = tool.checked_receipt(self.modified())
        receipt['transfer_count'] = 0
        forged = tool.handoff.build({tool.CAPTURE: EXAMPLE, tool.RECEIPT: tool.canonical(receipt)})
        with self.assertRaisesRegex(ValueError, 'saved receipt'):
            tool.inspect_bytes(forged)

    def test_payload_tampering_with_repaired_crc_rejected(self):
        good = tool.build(EXAMPLE)
        result = io.BytesIO()
        with zipfile.ZipFile(io.BytesIO(good)) as archive, zipfile.ZipFile(result, 'w') as altered:
            for entry in archive.infolist():
                raw = archive.read(entry.filename)
                if entry.filename == tool.CAPTURE:
                    raw = raw.replace(b'ZTO', b'IMD')
                altered.writestr(entry, raw)
        with self.assertRaises(ValueError):
            tool.inspect_bytes(result.getvalue())

    def test_independent_digest_match_and_mismatch(self):
        data = tool.build(EXAMPLE)
        digest = hashlib.sha256(data).hexdigest()
        self.assertTrue(tool.inspect_bytes(data, digest)['trusted_digest_matched'])
        with self.assertRaises(ValueError):
            tool.inspect_bytes(data, 'f' * 64)

    def test_unknown_payload_and_path_hazards_refused(self):
        good = tool.build(EXAMPLE)
        with zipfile.ZipFile(io.BytesIO(good)) as archive:
            files = {name: archive.read(name) for name in (tool.CAPTURE, tool.RECEIPT)}
        files['README'] = b'not a window payload'
        with self.assertRaises(ValueError):
            tool.inspect_bytes(tool.handoff.build(files))
        self.assertTrue(tool.portability.analyze(['CON.txt', 'README', 'readme']))

    def test_strict_json_duplicate_nonfinite_and_size_limits(self):
        for raw in [b'{"a":1,"a":2}', b'{"a":NaN}', b'[]', b' '*(tool.MAX_BYTES+1)]:
            with self.subTest(raw=raw[:20]), self.assertRaises((ValueError, RuntimeError)):
                tool.build(raw)
        capture = self.modified()
        capture['padding'] = 'x' * 95000
        with self.assertRaises(ValueError):
            tool.build(tool.canonical(capture))

    def test_cli_roundtrip_overwrite_and_no_partial_output(self):
        scratch = Path('test/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as directory:
            root = Path(directory).relative_to(Path.cwd())
            source = root / 'capture.json'
            target = root / 'bundle.zip'
            source.write_bytes(EXAMPLE)
            for args in [['pack', str(source), str(target)], ['inspect', str(target)]]:
                with contextlib.redirect_stdout(io.StringIO()) as output:
                    self.assertEqual(tool.main(args), 0)
                self.assertTrue(json.loads(output.getvalue())['verified'])
            for args in [['pack', str(source), str(target)], ['inspect', '../outside.zip']]:
                with contextlib.redirect_stdout(io.StringIO()) as output, contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(tool.main(args), 1)
                self.assertEqual(output.getvalue(), '')


if __name__ == '__main__':
    unittest.main(verbosity=2)
