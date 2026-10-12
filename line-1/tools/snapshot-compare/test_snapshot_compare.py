#!/usr/bin/env python3
"""Offline tests for hash-pinned evidence comparison."""
import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import snapshot_compare as tool


EXAMPLE = tool.hash_snapshot.load_json(
    (Path(__file__).resolve().parents[1] / 'hash-snapshot' / 'example-mainnet.json').read_bytes())


class Tests(unittest.TestCase):
    def pair(self, left=EXAMPLE, right=EXAMPLE):
        return {'left': left, 'right': right}

    def test_real_retained_snapshot_compares_offline(self):
        with patch.object(tool.hash_snapshot, 'public_read') as network:
            result = tool.compare(EXAMPLE, EXAMPLE)
            self.assertTrue(result['same_block_hash'])
            self.assertEqual({row['status'] for row in result['calls']}, {'unchanged'})
            network.assert_not_called()

    def test_known_supply_change_has_exact_delta(self):
        right = copy.deepcopy(EXAMPLE)
        row = next(row for row in right['observations'] if row['label'] == 'ZTO-supply')
        row['response']['result'] = '0x' + format(10**27 + 9, '064x')
        result = tool.compare(EXAMPLE, right)
        changed = next(row for row in result['calls'] if row['label'] == 'ZTO-supply')
        self.assertEqual(changed['status'], 'result-changed')
        self.assertEqual(changed['decoded_uint256_delta'], '9')

    def test_generic_change_does_not_invent_delta(self):
        left, right = copy.deepcopy(EXAMPLE), copy.deepcopy(EXAMPLE)
        for bundle in (left, right):
            bundle['observations'] = [bundle['observations'][0]]
            bundle['observations'][0]['params'][0]['data'] = '0x'
        right['observations'][0]['response']['result'] = '0x1234'
        changed = tool.compare(left, right)['calls'][0]
        self.assertEqual(changed['status'], 'result-changed')
        self.assertNotIn('decoded_uint256_delta', changed)

    def test_changed_request_is_not_mislabeled_as_value_change(self):
        right = copy.deepcopy(EXAMPLE)
        right['observations'][0]['params'][0]['data'] = '0x313ce567'
        right['observations'][0]['response']['result'] = '0x' + format(18, '064x')
        changed = next(row for row in tool.compare(EXAMPLE, right)['calls'] if row['label'] == 'ZTO-supply')
        self.assertEqual(changed['status'], 'request-changed')

    def test_added_and_removed_labels_are_explicit(self):
        left, right = copy.deepcopy(EXAMPLE), copy.deepcopy(EXAMPLE)
        left['observations'] = left['observations'][:1]
        right['observations'] = right['observations'][1:2]
        statuses = {row['label']: row['status'] for row in tool.compare(left, right)['calls']}
        self.assertEqual(statuses, {'IMD-supply': 'added', 'ZTO-supply': 'removed'})

    def test_invalid_child_evidence_fails_before_output(self):
        bad = copy.deepcopy(EXAMPLE)
        bad['observations'][0]['params'][1]['requireCanonical'] = False
        with self.assertRaises(ValueError):
            tool.compare(EXAMPLE, bad)

    def test_duplicate_pair_json_and_wrong_shape_rejected(self):
        raw = json.dumps(self.pair()).encode()
        self.assertEqual(tool.load_pair(raw)['left']['schema'], tool.hash_snapshot.SCHEMA)
        for raw in (b'{"left":{},"left":{}}', b'[]', b'{"left":{}}', b'NaN'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                tool.load_pair(raw)

    def test_input_bound_rejected(self):
        with self.assertRaises(ValueError):
            tool.load_pair(b' ' * (tool.MAX_INPUT + 1))

    def test_deterministic_label_order(self):
        right = copy.deepcopy(EXAMPLE)
        right['observations'].reverse()
        labels = [row['label'] for row in tool.compare(EXAMPLE, right)['calls']]
        self.assertEqual(labels, sorted(labels))

    def test_cli_compare_never_calls_network(self):
        raw = json.dumps(self.pair()).encode()
        out, err = io.StringIO(), io.StringIO()
        with patch.object(sys, 'argv', ['snapshot-compare', 'compare']), \
             patch.object(sys, 'stdin', io.TextIOWrapper(io.BytesIO(raw))), \
             patch.object(tool.hash_snapshot, 'public_read') as network, \
             contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.assertEqual(tool.main(), 0)
            self.assertIn('ethereum-snapshot-compare/1', out.getvalue())
            self.assertEqual(err.getvalue(), '')
            network.assert_not_called()

    def test_cli_rejects_without_partial_json(self):
        out, err = io.StringIO(), io.StringIO()
        with patch.object(sys, 'argv', ['snapshot-compare', 'compare']), \
             patch.object(sys, 'stdin', io.TextIOWrapper(io.BytesIO(b'null'))), \
             contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.assertEqual(tool.main(), 1)
            self.assertEqual(out.getvalue(), '')
            self.assertNotIn('Traceback', err.getvalue())


if __name__ == '__main__':
    unittest.main(verbosity=2)
