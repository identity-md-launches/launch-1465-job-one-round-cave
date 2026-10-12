#!/usr/bin/env python3
"""Compare two validated hash-pinned Ethereum snapshots entirely offline."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parents[1] / 'hash-snapshot' / 'hash_snapshot.py'
SPEC = importlib.util.spec_from_file_location('snapshot_compare_hash', SOURCE)
hash_snapshot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(hash_snapshot)

SCHEMA = 'ethereum-snapshot-compare/1'
MAX_INPUT = hash_snapshot.MAX_INPUT * 2


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError('non-finite JSON value')


def load_pair(raw):
    if len(raw) > MAX_INPUT:
        raise ValueError('comparison input exceeds 2 MiB')
    pair = json.loads(raw, object_pairs_hook=unique_object, parse_constant=reject_constant)
    if not isinstance(pair, dict) or set(pair) != {'left', 'right'}:
        raise ValueError('expected exactly left and right snapshots')
    return pair


def anchor(summary):
    return {key: summary[key] for key in ('block_number', 'block_hash', 'captured_at')}


def call_index(summary):
    return {row['label']: row for row in summary['calls']}


def comparable(row):
    return {key: row[key] for key in ('to', 'data')}


def value_delta(left, right):
    if (left.get('meaning') == right.get('meaning')
            and 'decoded_uint256' in left and 'decoded_uint256' in right):
        return str(int(right['decoded_uint256']) - int(left['decoded_uint256']))
    return None


def compare(left_bundle, right_bundle):
    """Validate two evidence bundles and return a bounded deterministic comparison."""
    left = hash_snapshot.inspect(left_bundle)
    right = hash_snapshot.inspect(right_bundle)
    left_calls, right_calls = call_index(left), call_index(right)
    rows = []
    for label in sorted(set(left_calls) | set(right_calls)):
        before, after = left_calls.get(label), right_calls.get(label)
        if before is None:
            rows.append({'label': label, 'status': 'added', 'right': after})
        elif after is None:
            rows.append({'label': label, 'status': 'removed', 'left': before})
        elif comparable(before) != comparable(after):
            rows.append({'label': label, 'status': 'request-changed',
                         'left': before, 'right': after})
        elif before['result'] != after['result']:
            row = {'label': label, 'status': 'result-changed',
                   'request': comparable(before),
                   'left_result': before['result'], 'right_result': after['result']}
            delta = value_delta(before, after)
            if delta is not None:
                row['decoded_uint256_delta'] = delta
            rows.append(row)
        else:
            rows.append({'label': label, 'status': 'unchanged',
                         'request': comparable(before), 'result': before['result']})
    return {
        'schema': SCHEMA,
        'left_anchor': anchor(left),
        'right_anchor': anchor(right),
        'same_block_hash': left['block_hash'] == right['block_hash'],
        'calls': rows,
        'evidence_limits': ('Offline structural comparison only. It validates each provider bundle but '
                            'does not authenticate either provider, prove finality, or prove why a value changed.')
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('compare', 'demo'))
    args = parser.parse_args()
    try:
        if args.command == 'demo':
            raw = (Path(__file__).resolve().parents[1] / 'hash-snapshot' /
                   'example-mainnet.json').read_bytes()
            one = hash_snapshot.load_json(raw)
            output = compare(one, one)
        else:
            pair = load_pair(sys.stdin.buffer.read(MAX_INPUT + 1))
            output = compare(pair['left'], pair['right'])
        print(json.dumps(output, indent=2, sort_keys=True))
        return 0
    except (ValueError, TypeError, KeyError, RuntimeError, OSError, RecursionError, json.JSONDecodeError):
        print('snapshot-compare: invalid or inconsistent offline evidence; no comparison emitted', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
